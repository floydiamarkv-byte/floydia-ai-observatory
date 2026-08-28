"""
RankingEngineV3 — Motor de scoring estadístico con Probit Rank Normalization,
shrinkage bayesiano jerárquico e incertidumbre posterior.

Reemplaza la lógica de scoring de `src/core/scoring.py` y `src/core/confidence.py`.
Documentación matemática: docs/SPEC_FCI_V3.md

Principios:
1. Ninguna escala cruda se mezcla: cada benchmark se transforma por un probit
   (z-score robusto -> CDF normal) calibrado con constantes históricas por benchmark,
   nunca por el cohorte actual (estabilidad temporal del ranking).
2. La imputación es el caso límite del shrinkage (lambda=0): el prior jerárquico
   es la MEDIA DE LA FAMILIA (familias con variantes hermanas medidas), nunca un
   valor global plano. Con esto los modelos con pocos datos no colapsan a un único
   valor ni lideran por ruido.
3. El margen de error se calcula desde la varianza posterior inflada por el
   decaimiento temporal de frescura. Sin cortes arbitrarios.
4. El orden público usa Lower Confidence Bound (FCI - Margen): el riesgo penaliza.
5. Empate estadístico = test de Welch: |Δ| < 1.96 * sqrt(σ_i² + σ_j²).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Any, Dict, List, Optional, Tuple

from src.core.contracts import ObservationType
from src.core.freshness import freshness_engine

_NORM = NormalDist()

# ---------------------------------------------------------------------------
# 1. Calibración histórica de benchmarks (no derivada del cohorte actual)
# ---------------------------------------------------------------------------
# (mu, s, n_eff) con s = 1.4826 * MAD histórico. Versione esta tabla al recalibrar
# con scripts/calibrate_benchmarks.py — nunca la derive en caliente del ranking.
BENCHMARK_CALIBRATION: Dict[str, Tuple[float, float, float]] = {
    # Recalibrado con la cohorte real del observatorio (2026-08-20).
    # (mediana, 1.4826*MAD, n_eff) — representan la población histórica de cada
    # benchmark, no un ideal externo. Recalcular con scripts/calibrate_benchmarks.py
    # cada vez que se actualicen los snapshots crudos.
    "arena_elo":       (1325.0,  66.7, 300.0),
    "chatbot_arena":   (1325.0,  66.7, 300.0),
    "aa_quality_index":(  81.2,   7.1, 200.0),
    "livebench":       (  74.5,   7.6, 150.0),
    "epoch_science":   (  82.5,   9.6, 100.0),
    "swe_bench":       (  38.4,  15.7, 120.0),
    "aider_polyglot":  (  65.4,  12.0, 100.0),
    "humaneval":       (  92.7,   5.0,  80.0),
    "livecodebench":   (  40.0,  10.0, 100.0),  # estimada
    "mmlu_pro":        (  28.1,  11.9, 250.0),
    "gpqa":            (   6.8,   6.5, 200.0),  # escala baja propia del dataset
    "math_500":        (  13.6,  11.9, 150.0),
    "ifeval":          (  42.0,  20.0, 150.0),
}

# Varianza intrínseca de reproducción de cada benchmark (en unidades ya
# normalizadas 0-100). Modela la aleatoriedad de re-ejecutar el benchmark.
REPRO_NOISE2 = 4.0  # σ² = 4  (σ=2 puntos en escala 0-100)

# Varianza por defecto de un benchmark no calibrado, en su escala cruda.
DEFAULT_RAW_SIGMA2 = 400.0

# Pesos de pilares (suma 1.0). Parte de la API pública del observatorio.
PILLAR_WEIGHTS: Dict[str, float] = {
    "reasoning":  0.35,
    "coding":     0.30,
    "quality":    0.20,
    "preference": 0.15,
}

PILLAR_BENCHMARKS: Dict[str, Tuple[str, ...]] = {
    "reasoning":  ("livebench", "epoch_science", "gpqa", "math_500", "mmlu_pro"),
    "coding":     ("swe_bench", "aider_polyglot", "humaneval", "livecodebench"),
    "quality":    ("aa_quality_index",),
    "preference": ("arena_elo", "chatbot_arena"),
}

# Prior de tier cuando la familia carece de información: media y varianza de la
# población de ese tier (en escala normalizada 0-100). Vaga pero no plana.
TIER_PRIOR: Dict[str, Tuple[float, float]] = {
    "frontier":     (68.0, 121.0),
    "reasoning":    (62.0, 121.0),
    "coding":       (60.0, 144.0),
    "agentic":      (63.0, 144.0),
    "long_context": (58.0, 144.0),
    "workhorse":    (52.0, 169.0),
    "multimodal":   (55.0, 169.0),
    "edge":         (40.0, 196.0),
}
DEFAULT_TIER_PRIOR = (50.0, 196.0)

# ---------------------------------------------------------------------------
# 2. Normalizador de benchmarks (Probit Rank Normalization)
# ---------------------------------------------------------------------------

class BenchmarkNormalizer:
    """Transforma una medición cruda de un benchmark a percentil robusto 0-100."""

    LAPLACE_ALPHA = 0.5

    def normalize(self, benchmark: str, raw_value: float) -> Tuple[float, float]:
        """
        Devuelve (score_0_100, varianza_del_score).
        La varianza incluye el ruido de reproducción intrínseco del benchmark.
        """
        cal = BENCHMARK_CALIBRATION.get(benchmark)
        if cal is None:
            # Sin calibración: Min-Max conservador sobre dominio declarado 0-100,
            # con alta varianza (el shrinkage lo relegará automáticamente).
            v = max(0.0, min(100.0, raw_value))
            return v, 100.0
        mu, s, n_eff = cal
        z = (raw_value - mu) / max(s, 1e-6)
        z = max(-4.0, min(4.0, z))          # Winsorización en 4σ
        p = _NORM.cdf(z)
        p_adj = (n_eff * p + self.LAPLACE_ALPHA) / (n_eff + 2 * self.LAPLACE_ALPHA)
        score = 100.0 * p_adj
        # Varianza del estimador de un percentil con n_eff observaciones:
        var_p = p * (1.0 - p) / max(n_eff, 1.0)
        var_score = (100.0 ** 2) * var_p + REPRO_NOISE2
        return score, var_score


# ---------------------------------------------------------------------------
# 3. Resolución canónica de identidades (Familia → Variante → Proveedor)
# ---------------------------------------------------------------------------

_VARIANT_SUFFIX = re.compile(
    r"-?(max|high|fast|turbo|flash|mini|nano|pro|standard|thinking(?:-\d+k?)?|reasoning|instruct|chat|base)$"
)

_KNOWN_PROVIDER_PREFIXES = (
    "anthropic", "google", "openai", "deepseek", "alibaba", "dashscope",
    "zhipu", "z-ai", "xai", "grokified", "meta", "mistral", "groq",
    "fireworks", "openrouter", "stepfun", "qwen", "nous",
)


@dataclass
class ResolvedIdentity:
    family_id: str
    variant: str            # "standard" si no hay sufijo reconocido
    provider: str           # proveedor del endpoint, si venía prefijado
    raw_id: str


class IdentityResolver:
    """
    Normaliza IDs crudos en (family, variant, provider). Determinista y
    fail-open: nunca descarta información, en el peor caso family = slug.
    """

    def resolve(self, raw_id: str) -> ResolvedIdentity:
        rid = raw_id.strip().lower()
        rid = rid.lstrip("~").strip()
        provider = ""
        slug = rid
        # Formato "proveedor/slug" (OpenRouter, catálogos agregados)
        if "/" in rid:
            head, tail = rid.split("/", 1)
            if head in _KNOWN_PROVIDER_PREFIXES:
                provider = head
                slug = tail
        else:
            # Formato "proveedor-modelo" (ej. "anthropic-claude-fable-5")
            for pref in _KNOWN_PROVIDER_PREFIXES:
                sep = pref + "-"
                if rid.startswith(sep):
                    provider = pref
                    slug = rid[len(sep):]
                    break
        # Sufijo de variante
        variant = "standard"
        m = _VARIANT_SUFFIX.search(slug)
        if m:
            variant = m.group(1)
            family = slug[: m.start()].strip("-") or slug
        else:
            family = slug
        family = re.sub(r"-{2,}", "-", family).strip("-")
        return ResolvedIdentity(
            family_id=family or slug,
            variant=variant,
            provider=provider,
            raw_id=raw_id,
        )


# ---------------------------------------------------------------------------
# 4. Agregación bayesiana de pilares
# ---------------------------------------------------------------------------

@dataclass
class PillarPosterior:
    name: str
    mean: float                 # Ŝ_p posterior
    var: float                  # Var(S_p) posterior
    shrinkage: float            # λ_p
    n_obs: int                  # número de observaciones realmente medidas
    observed: bool


class BayesianPillarAggregator:
    """
    Fusiona observaciones del pilar con un prior jerárquico:
      - BLUE por mínima varianza entre observaciones del pilar.
      - Shrinkage: Ŝ = λ·μ_obs + (1−λ)·θ_prior ;  λ = τ²/(τ² + Var(μ_obs)).
    Con n_obs = 0, λ = 0 automáticamente y Ŝ = θ_prior: la imputación es el
    caso límite del mismo estimador, sin fórmulas separadas (elimina el
    Defecto C por construcción).
    """

    def aggregate(
        self,
        pillar_name: str,
        observations: List[Tuple[float, float]],  # (score, var)
        prior_mean: float,
        prior_var: float,
    ) -> PillarPosterior:
        if observations:
            weights = [1.0 / max(v, 1e-6) for _, v in observations]
            w_sum = sum(weights)
            mu_obs = sum(w * s for w, (s, _) in zip(weights, observations)) / w_sum
            var_mu = 1.0 / w_sum
        else:
            mu_obs, var_mu = 0.0, math.inf

        tau2 = max(prior_var, 1e-6)
        lam = tau2 / (tau2 + var_mu) if math.isfinite(var_mu) else 0.0
        post_mean = lam * mu_obs + (1.0 - lam) * prior_mean
        post_var = lam * var_mu if math.isfinite(var_mu) else tau2
        return PillarPosterior(
            name=pillar_name,
            mean=post_mean,
            var=post_var,
            shrinkage=lam,
            n_obs=len(observations),
            observed=bool(observations),
        )


# ---------------------------------------------------------------------------
# 5. Motor principal
# ---------------------------------------------------------------------------

@dataclass
class ModelScoreResult:
    model_id: str
    family_id: str
    variant: str
    provider: str
    fci: float
    margin_95: float
    ci_lower: float
    ci_upper: float
    lower_confidence_bound: float   # criterio de ordenamiento público
    confidence: float               # C ∈ [0,1]
    evidence_grade: str
    observation_type: ObservationType
    pillars: Dict[str, PillarPosterior] = field(default_factory=dict)
    n_metrics: int = 0
    n_sources: int = 0
    is_statistical_tie: bool = False
    global_rank: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


class ConfidenceModel:
    """Score de confianza continuo (sin acotados tipo clamp artificial)."""

    @staticmethod
    def score(pillars: List[PillarPosterior], n_sources: int,
              freshness: float, between_source_std: float) -> float:
        obs = [p for p in pillars]
        if not obs:
            return 0.15
        lam_bar = sum(PILLAR_WEIGHTS[p.name] * p.shrinkage for p in obs) / 1.0
        g = 1.0 - math.exp(-n_sources / 3.0)              # independencia de fuentes
        h = 1.0 / (1.0 + between_source_std / 20.0)       # discordancia inter-fuente
        c = lam_bar * g * h * freshness
        return round(max(0.05, min(0.97, c)), 3)


class RankingEngineV3:
    """
    Orquestador: normaliza → agrega por pilares con shrinkage familiar → FCI →
    incertidumbre con inflación temporal → ordenamiento LCB → empates Welch.
    """

    FRESH_HALF_LIFE_DAYS = 30.0

    def __init__(self) -> None:
        self.normalizer = BenchmarkNormalizer()
        self.resolver = IdentityResolver()
        self.aggregator = BayesianPillarAggregator()

    # -- Entrada -----------------------------------------------------------

    def score_models(
        self,
        models: List[Dict[str, Any]],
        observations: List[Dict[str, Any]],
    ) -> List[ModelScoreResult]:
        """
        models: filas de `models` (id, tier, provider, canonical_name, ...).
        observations: filas de `evaluations`
              {model_id, benchmark_name, score, source, recorded_at}.
        """
        # Índice observación → modelo/variante
        obs_by_model: Dict[str, List[Dict[str, Any]]] = {}
        for o in observations:
            obs_by_model.setdefault(o["model_id"], []).append(o)

        identities = {m["id"]: self.resolver.resolve(m["id"]) for m in models}

        # ---- Priors jerárquicos por familia y pilar ----
        # Primera pasada: juntar medias normalizadas por (family, pilar) con
        # todas las variantes observadas de la familia.
        family_pillar_vals: Dict[str, Dict[str, List[float]]] = {}
        for m in models:
            ident = identities[m["id"]]
            for o in obs_by_model.get(m["id"], []):
                bname = o["benchmark_name"]
                pillar = self._pillar_of(bname)
                if not pillar:
                    continue
                s, _ = self.normalizer.normalize(bname, float(o["score"]))
                fam = family_pillar_vals.setdefault(ident.family_id, {})
                fam.setdefault(pillar, []).append(s)

        family_prior: Dict[str, Dict[str, Tuple[float, float]]] = {}
        for fam, pillars in family_pillar_vals.items():
            fp: Dict[str, Tuple[float, float]] = {}
            for pill, vals in pillars.items():
                if len(vals) >= 2:
                    mean = sum(vals) / len(vals)
                    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
                    fp[pill] = (mean, max(var, 25.0))       # varianza mínima 5²
                else:
                    fp[pill] = (vals[0], 144.0)             # una sola: media con var vaga
            family_prior[fam] = fp

        # ---- Segunda pasada: scoring por modelo ----
        results: List[ModelScoreResult] = []
        for m in models:
            ident = identities[m["id"]]
            model_obs = obs_by_model.get(m["id"], [])
            norm_by_bench: Dict[str, List[Tuple[float, float]]] = {}
            sources: set = set()
            latest_ts: Optional[str] = None
            for o in model_obs:
                bname = o["benchmark_name"]
                s, v = self.normalizer.normalize(bname, float(o["score"]))
                norm_by_bench.setdefault(bname, []).append((s, v))
                if o.get("source"):
                    sources.add(o["source"])
                ts = o.get("recorded_at")
                if ts and (latest_ts is None or str(ts) > latest_ts):
                    latest_ts = str(ts)

            days, fresh, _ = freshness_engine.evaluate_freshness(latest_ts)

            pil_posts: List[PillarPosterior] = []
            for pill_name, benches in PILLAR_BENCHMARKS.items():
                obs: List[Tuple[float, float]] = []
                for b in benches:
                    obs.extend(norm_by_bench.get(b, []))
                prior_mean, prior_var = self._prior_for(
                    ident.family_id, pill_name, m.get("tier", "workhorse"), family_prior
                )
                pil_posts.append(self.aggregator.aggregate(pill_name, obs, prior_mean, prior_var))

            # FCI y varianza
            fci = sum(PILLAR_WEIGHTS[p.name] * p.mean for p in pil_posts)
            var_fci = sum((PILLAR_WEIGHTS[p.name] ** 2) * p.var for p in pil_posts)
            # Inflación temporal de la varianza
            # El piso de frescura en 0.2 acota la inflación a 25x la varianza:
            # datos con >120 días degradan el margen pero sin explosión no informativa.
            var_infl = var_fci / max(fresh, 0.2) ** 2
            sd = math.sqrt(var_infl)
            margin = 1.96 * sd
            ci_lo = max(0.0, fci - margin)
            ci_hi = min(100.0, fci + margin)

            # Discrepancia inter-fuente (std de medias normalizadas de benchmarks)
            bench_means = [
                sum(s for s, _ in vs) / len(vs) for vs in norm_by_bench.values() if vs
            ]
            if len(bench_means) > 1:
                bm = sum(bench_means) / len(bench_means)
                between_std = math.sqrt(sum((x - bm) ** 2 for x in bench_means) / (len(bench_means) - 1))
            else:
                between_std = 10.0   # desconocida -> anticipación moderada

            n_metrics = len(bench_means)
            conf = ConfidenceModel.score(pil_posts, len(sources) or 1, fresh, between_std)

            obs_type = (ObservationType.OBSERVED if n_metrics >= 1 else ObservationType.ESTIMATED)
            results.append(ModelScoreResult(
                model_id=m["id"],
                family_id=ident.family_id,
                variant=ident.variant,
                provider=ident.provider or m.get("provider", ""),
                fci=round(fci, 2),
                margin_95=round(margin, 2),
                ci_lower=round(ci_lo, 2),
                ci_upper=round(ci_hi, 2),
                lower_confidence_bound=round(ci_lo, 2),
                confidence=conf,
                evidence_grade=self._grade(conf),
                observation_type=obs_type,
                pillars={p.name: p for p in pil_posts},
                n_metrics=n_metrics,
                n_sources=len(sources),
                extra={
                    "tier": m.get("tier"),
                    "freshness_days": days,
                    "freshness_factor": fresh,
                    "between_source_std": round(between_std, 2),
                    "canonical_name": m.get("canonical_name"),
                },
            ))

        # ---- Ordenamiento por Lower Confidence Bound + empates de Welch ----
        results.sort(key=lambda r: (r.lower_confidence_bound, r.confidence), reverse=True)
        # Umbral mínimo de evidencia para que el flag de empate sea informativo:
        # un modelo con n=1 tiene un IC enorme y empata con todo; reportar eso
        # como "empate" con un modelo de 14 benchmarks no dice nada útil.
        # Definimos el flag de empate solo entre modelos con ≥MIN_N_FOR_TIE
        # benchmarks observados Y la condición de Welch se cumple.
        MIN_N_FOR_TIE = 3
        for i, r in enumerate(results, start=1):
            r.global_rank = i
            if i > 1:
                prev = results[i - 2]
                sd_i = r.margin_95 / 1.96
                sd_j = prev.margin_95 / 1.96
                u = 1.96 * math.sqrt(sd_i ** 2 + sd_j ** 2)
                welch_overlap = abs(prev.fci - r.fci) < u
                both_evidence = (r.n_metrics >= MIN_N_FOR_TIE
                                  and prev.n_metrics >= MIN_N_FOR_TIE)
                tie = welch_overlap and both_evidence
                if tie:
                    r.is_statistical_tie = True
                    prev.is_statistical_tie = True
        return results

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _pillar_of(benchmark: str) -> Optional[str]:
        for pill, benches in PILLAR_BENCHMARKS.items():
            if benchmark in benches:
                return pill
        return None

    @staticmethod
    def _prior_for(family_id: str, pillar: str, tier: str,
                   family_prior: Dict[str, Dict[str, Tuple[float, float]]]) -> Tuple[float, float]:
        fp = family_prior.get(family_id, {})
        if pillar in fp:
            return fp[pillar]
        return TIER_PRIOR.get(tier, DEFAULT_TIER_PRIOR)

    @staticmethod
    def _grade(conf: float) -> str:
        if conf >= 0.85:
            return "A (Multi-Fuente Verificada)"
        if conf >= 0.70:
            return "B (Alta Corroboración)"
        if conf >= 0.50:
            return "C (Evidencia Moderada)"
        return "D (Evidencia Limitada)"


# Instancia global con la misma convención que confidence_engine / freshness_engine
ranking_engine_v3 = RankingEngineV3()
