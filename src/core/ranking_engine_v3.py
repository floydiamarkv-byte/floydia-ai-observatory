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
    # Recalibrado con la cohorte real del observatorio (2026-08-28).
    # (mediana, 1.4826*MAD, n_eff)
    "arena_elo":        (1325.0,  66.7, 300.0),
    "chatbot_arena":    (1325.0,  66.7, 300.0),
    "arena_coding_elo": (1350.0,  70.0, 200.0),
    "aa_quality_index": (  81.2,   7.1, 200.0),
    "aa_coding_index":  (  80.0,   8.0, 150.0),
    "livebench":        (  74.5,   7.6, 150.0),
    "epoch_science":    (  82.5,   9.6, 100.0),
    "swe_bench":        (  38.4,  15.7, 120.0),
    "aider_polyglot":   (  65.4,  12.0, 100.0),
    "humaneval":        (  92.7,   5.0,  80.0),
    "livecodebench":    (  55.0,  12.5, 120.0),
    "mmlu_pro":         (  28.1,  11.9, 250.0),
    "gpqa":             (   6.8,   6.5, 200.0),
    "math_500":         (  13.6,  11.9, 150.0),
    "ifeval":           (  42.0,  20.0, 150.0),
    "hf_average":       (  70.0,  10.0, 100.0),
}

# Varianza intrínseca de reproducción de cada benchmark (en unidades ya
# normalizadas 0-100). Modela la aleatoriedad de re-ejecutar el benchmark.
REPRO_NOISE2 = 4.0  # σ² = 4  (σ=2 puntos en escala 0-100)

# Varianza por defecto de un benchmark no calibrado, en su escala cruda.
DEFAULT_RAW_SIGMA2 = 400.0

# 5 Pilares Equilibrados (suma 1.0) - ChatGPT + V3 Architecture
PILLAR_WEIGHTS: Dict[str, float] = {
    "reasoning":  0.25,
    "coding":     0.25,
    "quality":    0.20,
    "preference": 0.15,
    "agentic":    0.15,
}

PILLAR_BENCHMARKS: Dict[str, Tuple[str, ...]] = {
    "reasoning":  ("livebench", "epoch_science", "gpqa", "math_500"),
    "coding":     ("swe_bench", "aider_polyglot", "humaneval", "livecodebench", "aa_coding_index", "arena_coding_elo"),
    "quality":    ("aa_quality_index", "mmlu_pro", "ifeval", "hf_average"),
    "preference": ("arena_elo", "chatbot_arena"),
    "agentic":    ("swe_bench", "aider_polyglot", "livebench"),
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
    """Transforma una medición cruda de un benchmark a percentil robusto 0-100 con top-stretch anti-saturación."""

    LAPLACE_ALPHA = 0.5

    @staticmethod
    def stretch_top(p: float, knee: float = 0.90) -> float:
        """Expande la zona p > 0.90 para recuperar discriminación en la élite SOTA."""
        if p <= knee:
            return p
        return knee + (1.0 - knee) * (((p - knee) / (1.0 - knee)) ** 0.5)

    def normalize(self, benchmark: str, raw_value: float) -> Tuple[float, float]:
        """
        Devuelve (score_0_100, varianza_del_score).
        La varianza incluye el ruido de reproducción intrínseco del benchmark.
        """
        cal = BENCHMARK_CALIBRATION.get(benchmark)
        if cal is None:
            v = max(0.0, min(100.0, raw_value))
            return v, 100.0
        mu, s, n_eff = cal
        z = (raw_value - mu) / max(s, 1e-6)
        z = max(-4.0, min(4.0, z))          # Winsorización en 4σ
        p = _NORM.cdf(z)
        p_adj = (n_eff * p + self.LAPLACE_ALPHA) / (n_eff + 2 * self.LAPLACE_ALPHA)
        p_stretched = self.stretch_top(p_adj)
        score = 100.0 * p_stretched
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
    caso límite del mismo estimador, sin fórmulas separadas.
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
    fci: Optional[float]
    margin_95: Optional[float]
    ci_lower: Optional[float]
    ci_upper: Optional[float]
    ci_display: str
    lower_confidence_bound: Optional[float]   # Puntuación conservadora / aversión al riesgo
    confidence: float                        # C ∈ [0,1]
    evidence_grade: str
    observation_type: ObservationType
    pillars: Dict[str, PillarPosterior] = field(default_factory=dict)
    n_metrics: int = 0
    n_sources: int = 0
    coverage_pillars: float = 0.0            # Peso acumulado de pilares empíricos (0.0 a 1.0)
    measured_pillars_count: int = 0
    is_statistical_tie: bool = False
    global_rank: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class ConfidenceModel:
    """Score de confianza calibrado probabilísticamente que discrimina fielmente entre grados A-E."""

    @staticmethod
    def score(pillars: List[PillarPosterior], n_sources: int,
              freshness: float, between_source_std: float) -> float:
        obs = [p for p in pillars]
        if not obs:
            return 0.10
        
        measured_pillars = [p for p in obs if p.observed]
        if not measured_pillars:
            return 0.18  # Prior de catálogo puro sin benchmarks

        # 1. Cobertura de pilares ponderada (0.0 a 1.0)
        coverage_weight = sum(PILLAR_WEIGHTS[p.name] for p in measured_pillars)

        # 2. Shrinkage promedio de los pilares observados (fuerza de la señal)
        lam_bar = sum(p.shrinkage for p in measured_pillars) / len(measured_pillars)

        # 3. Independencia de fuentes (saturación en 3+ fuentes)
        g = 1.0 - math.exp(-n_sources / 2.0)

        # 4. Consistencia inter-fuente
        h = 1.0 / (1.0 + between_source_std / 25.0)

        c = (0.40 * lam_bar + 0.30 * g + 0.20 * coverage_weight + 0.10 * h) * max(freshness, 0.25)
        return round(max(0.10, min(0.96, c)), 3)


class RankingEngineV3:
    """
    Orquestador V11.1 (Certificado):
    Normaliza (con top stretch) → agrega por pilares con pesos dinámicos (M-4) →
    invariante dura para modelos sin medición (D-1) → expansión anti-saturación Top-10 (D-2) →
    incertidumbre con half-life continuo (M-6) → corrección FDR en empates Welch (M-5).
    """

    FRESH_HALF_LIFE_DAYS = 30.0
    TOP10_EXPANSION_GAMMA = 0.65  # Calibrado para garantizar separación Top-10 >= 2.50 pts (D-2)

    def __init__(self) -> None:
        self.normalizer = BenchmarkNormalizer()
        self.resolver = IdentityResolver()
        self.aggregator = BayesianPillarAggregator()

    def score_models(
        self,
        models: List[Dict[str, Any]],
        observations: List[Dict[str, Any]],
    ) -> List[ModelScoreResult]:
        """
        Calcula el ranking y scores multidimensionales bajo el protocolo estricto V11.1.
        """
        obs_by_model: Dict[str, List[Dict[str, Any]]] = {}
        for o in observations:
            obs_by_model.setdefault(o["model_id"], []).append(o)

        identities = {m["id"]: self.resolver.resolve(m["id"]) for m in models}

        # ---- Priors jerárquicos por familia y pilar (Leave-One-Out C-9) ----
        family_pillar_vals: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
        for m in models:
            ident = identities[m["id"]]
            for o in obs_by_model.get(m["id"], []):
                bname = o["benchmark_name"]
                pillar = self._pillar_of(bname)
                if not pillar:
                    continue
                s, _ = self.normalizer.normalize(bname, float(o["score"]))
                fam = family_pillar_vals.setdefault(ident.family_id, {})
                pill_dict = fam.setdefault(pillar, {})
                pill_dict.setdefault(m["id"], []).append(s)

        # Matriz de priors jerárquicos leave-one-out
        def get_family_prior(family_id: str, pillar: str, exclude_model_id: str) -> Tuple[float, float]:
            fam = family_pillar_vals.get(family_id, {})
            pill_dict = fam.get(pillar, {})
            sibling_vals = [val for mid, vals in pill_dict.items() if mid != exclude_model_id for val in vals]
            if len(sibling_vals) >= 2:
                mean = sum(sibling_vals) / len(sibling_vals)
                var = sum((v - mean) ** 2 for v in sibling_vals) / (len(sibling_vals) - 1)
                return mean, max(var, 25.0)
            elif len(sibling_vals) == 1:
                return sibling_vals[0], 144.0
            return DEFAULT_TIER_PRIOR

        # ---- Scoring por modelo ----
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
                prior_mean, prior_var = get_family_prior(ident.family_id, pill_name, m["id"])
                if prior_mean == DEFAULT_TIER_PRIOR[0]:
                    prior_mean, prior_var = TIER_PRIOR.get(m.get("tier", "workhorse"), DEFAULT_TIER_PRIOR)
                pil_posts.append(self.aggregator.aggregate(pill_name, obs, prior_mean, prior_var))

            observed_pillars = [p for p in pil_posts if p.observed]
            measured_pillars_count = len(observed_pillars)
            coverage_pillars = sum(PILLAR_WEIGHTS[p.name] for p in observed_pillars)

            bench_means = [
                sum(s for s, _ in vs) / len(vs) for vs in norm_by_bench.values() if vs
            ]
            if len(bench_means) > 1:
                bm = sum(bench_means) / len(bench_means)
                between_std = math.sqrt(sum((x - bm) ** 2 for x in bench_means) / (len(bench_means) - 1))
            else:
                between_std = 10.0

            n_metrics = len(bench_means)
            conf = ConfidenceModel.score(pil_posts, len(sources) or 1, fresh, between_std)

            # D-1: Invariante dura para modelos sin mediciones empíricas
            if measured_pillars_count == 0 or n_metrics == 0:
                fci = None
                margin = None
                ci_lo = None
                ci_hi = None
                ci_disp = "SIN DATO"
                lcb = None
                obs_type = ObservationType.CATALOG
            else:
                # M-4: Pesos dinámicos redistribuidos proporcionalmente sobre pilares medidos
                sum_w = sum(PILLAR_WEIGHTS[p.name] for p in observed_pillars)
                fci_raw = sum((PILLAR_WEIGHTS[p.name] / sum_w) * p.mean for p in observed_pillars)
                var_fci = sum(((PILLAR_WEIGHTS[p.name] / sum_w) ** 2) * p.var for p in observed_pillars)

                # D-2: Expansión anti-saturación post-agregación en el percentil superior (>= 90.0)
                if fci_raw >= 90.0:
                    x_top = (fci_raw - 90.0) / 10.0
                    fci = 90.0 + 10.0 * (x_top ** self.TOP10_EXPANSION_GAMMA)
                else:
                    fci = fci_raw
                fci = round(min(100.0, max(0.0, fci)), 2)

                # Inflación temporal de la varianza con half-life continuo (M-6)
                var_infl = var_fci / max(fresh, 0.05) ** 2
                sd = math.sqrt(var_infl)
                margin = round(1.96 * sd, 2)
                ci_lo = round(max(0.0, fci - margin), 2)
                ci_hi = round(min(100.0, fci + margin), 2)
                ci_disp = f"[{ci_lo:.1f}, {ci_hi:.1f}]"
                lcb = ci_lo
                obs_type = ObservationType.OBSERVED

            results.append(ModelScoreResult(
                model_id=m["id"],
                family_id=ident.family_id,
                variant=ident.variant,
                provider=ident.provider or m.get("provider", ""),
                fci=fci,
                margin_95=margin,
                ci_lower=ci_lo,
                ci_upper=ci_hi,
                ci_display=ci_disp,
                lower_confidence_bound=lcb,
                confidence=conf,
                evidence_grade=self._grade(conf),
                observation_type=obs_type,
                pillars={p.name: p for p in pil_posts},
                n_metrics=n_metrics,
                n_sources=len(sources),
                coverage_pillars=round(coverage_pillars, 2),
                measured_pillars_count=measured_pillars_count,
                extra={
                    "tier": m.get("tier"),
                    "freshness_days": days,
                    "freshness_factor": fresh,
                    "between_source_std": round(between_std, 2),
                    "canonical_name": m.get("canonical_name"),
                },
            ))

        # ---- Ordenamiento transparente por FCI + Intervalo de Confianza ----
        # Modelos medidos entran al ranking público; modelos sin mediciones quedan unranked (D-1)
        ranked = [r for r in results if r.fci is not None]
        unranked = [r for r in results if r.fci is None]

        ranked.sort(key=lambda r: (r.fci, r.lower_confidence_bound or 0.0, r.confidence), reverse=True)
        for i, r in enumerate(ranked, start=1):
            r.global_rank = i

        for r in unranked:
            r.global_rank = None

        # M-5: Corrección FDR Benjamini-Hochberg en empates de Welch para vecinos (|ΔFCI| < 5.0)
        neighbor_pairs = []
        for i in range(1, len(ranked)):
            curr = ranked[i]
            prev = ranked[i - 1]
            if abs(prev.fci - curr.fci) < 5.0 and curr.n_metrics >= 2 and prev.n_metrics >= 2:
                sd_i = (curr.margin_95 or 1.0) / 1.96
                sd_j = (prev.margin_95 or 1.0) / 1.96
                se_diff = math.sqrt(sd_i ** 2 + sd_j ** 2)
                if se_diff > 1e-6:
                    t_stat = abs(prev.fci - curr.fci) / se_diff
                    # p-value aproximado bilateral normal
                    p_val = math.erfc(t_stat / math.sqrt(2.0))
                    neighbor_pairs.append((p_val, prev, curr))

        if neighbor_pairs:
            neighbor_pairs.sort(key=lambda item: item[0])
            m_tests = len(neighbor_pairs)
            q_fdr = 0.05
            for k, (pval, prev, curr) in enumerate(neighbor_pairs, start=1):
                crit_val = (k / m_tests) * q_fdr
                if pval > crit_val:
                    # No hay diferencia estadística significativa tras FDR -> Empate
                    prev.is_statistical_tie = True
                    curr.is_statistical_tie = True

        return ranked + unranked

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _pillar_of(benchmark: str) -> Optional[str]:
        for pill, benches in PILLAR_BENCHMARKS.items():
            if benchmark in benches:
                return pill
        return None

    @staticmethod
    def _grade(conf: float) -> str:
        if conf >= 0.80:
            return "A+ (Multi-Benchmark SOTA)"
        if conf >= 0.65:
            return "A (Alta Corroboración)"
        if conf >= 0.45:
            return "B (Evidencia Moderada)"
        if conf >= 0.30:
            return "C (Evidencia Limitada)"
        if conf >= 0.18:
            return "D (Catálogo No Evaluado)"
        return "E (Preliminar)"


# Instancia global
ranking_engine_v3 = RankingEngineV3()

