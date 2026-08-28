"""
Motor de Cálculo de Índices Sintéticos, Scoring Multidimensional y Metadatos de Modelo v10 (RankingEngineV3).

Versión 10 (2026-08-20): Reemplaza la lógica de mezcla de escalas y la imputación plana
por Probit Rank Calibration + Shrinkage bayesiano jerárquico. La función pública
`calculate_multidimensional_rankings()` mantiene exactamente la misma firma y shape
de salida que las versiones anteriores (todos los consumidores —web, cli, gui, analyst—
no requieren cambios). La matemática interna delega en `RankingEngineV3`; la
estética, metadatos de perfil y workhorse se conservan aquí.

Documentación matemática: docs/SPEC_FCI_V3.md.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.core.db import get_db_connection, get_latest_local_verified_models, get_local_functional_model_keys
from src.core.contracts import ObservationType, QualityStatus
from src.core.quality import quality_engine
from src.core.freshness import freshness_engine
from src.core.ranking_engine_v3 import ranking_engine_v3, ModelScoreResult


MODEL_PROFILES = {
    "gemini-2.5-flash": {
        "description": "Modelo insignia multimodal de ultra-alta velocidad y contexto masivo de 1M de tokens con latencia sub-segundo.",
        "use_cases": [
            "Ingesta y análisis masivo de documentos largos, PDFs y repositorios de código.",
            "Flujos de agentes autónomos y llamadas a herramientas (Tool Calling) en tiempo real.",
            "Procesamiento multimodal directo de audio, video e imágenes a coste cero en Free Tier."
        ],
        "comparison": "Supera a GPT-4o-mini y Claude 3.5 Haiku en velocidad y longitud de contexto, con coste $0.0 en Google AI Studio Free Tier.",
        "sources": ["Google AI Studio", "LMSYS Arena", "Artificial Analysis"]
    },
    "gemini-2.0-flash": {
        "description": "Caballo de batalla de Google optimizado para inferencia instantánea y procesamiento multimodal.",
        "use_cases": [
            "Microservicios de clasificación, extracción y traducción rápida.",
            "Chatbots de atención interactiva con streaming de baja latencia."
        ],
        "comparison": "Ligeramente más rápido que Gemini 2.5 Flash, ideal para flujos donde cada milisegundo de latencia cuenta.",
        "sources": ["Google AI Studio", "LMSYS Arena", "Artificial Analysis"]
    },
    "gemini-2.5-pro": {
        "description": "Modelo de razonamiento de frontera de Google con la mayor ventana de contexto del mercado (2 Millones de tokens).",
        "use_cases": [
            "Auditoría profunda de arquitecturas de software complejas y libros enteros.",
            "Razonamiento científico y análisis multimodal de alta fidelidad."
        ],
        "comparison": "Compite directamente con Claude 3.7 Sonnet y GPT-4o, ofreciendo el doble de ventana de contexto que cualquier rival.",
        "sources": ["Google AI Studio", "Arena.ai", "LiveBench", "SWE-bench", "Epoch AI"]
    },
    "deepseek-reasoner": {
        "description": "Modelo de razonamiento puro con cadena de pensamiento nativa (Reinforcement Learning a gran escala).",
        "use_cases": [
            "Resolución de problemas matemáticos avanzados y teoremas lógicos.",
            "Algoritmia competitiva y depuración de código crítico."
        ],
        "comparison": "Rendimiento similar a OpenAI o1/o3-mini en benchmarks matemáticos a una fracción del precio comercial.",
        "sources": ["DeepSeek API", "Arena.ai", "LiveBench", "Hugging Face", "Aider"]
    },
    "deepseek-chat": {
        "description": "Arquitectura Mixture-of-Experts (MoE) de 671B parámetros (37B activos) para tareas de producción general.",
        "use_cases": [
            "Redacción técnica, resúmenes, traducción y asistentes conversacionales.",
            "Backend económico para scraping, extracción estructurada JSON y etiquetado masivo."
        ],
        "comparison": "Ofrece calidad de clase GPT-4o a menos del 10% del coste por token.",
        "sources": ["DeepSeek API", "Arena.ai", "Artificial Analysis", "SWE-bench"]
    },
    "claude-3-7-sonnet": {
        "description": "Modelo de razonamiento híbrido de Anthropic con control continuo sobre el tiempo de pensamiento (Thinking Budget).",
        "use_cases": [
            "Desarrollo de software completo, refactorizaciones estructurales y creación de tests.",
            "Análisis estratégico de negocio y redacción editorial sofisticada."
        ],
        "comparison": "Líder en SWE-bench Verified (70.3%), Aider Polyglot (84.2%) y LMSYS Coding Arena.",
        "sources": ["Anthropic", "Arena.ai", "SWE-bench", "Aider", "Artificial Analysis", "LiveBench"]
    },
    "claude-3-5-haiku": {
        "description": "Modelo compacto de Anthropic con alta inteligencia y velocidad superior para flujos de producción.",
        "use_cases": [
            "Procesamiento rápido de tickets, clasificación y moderación.",
            "Agentes ligeros que requieren precisión de instrucción sin coste de Sonnet."
        ],
        "comparison": "Supera al Claude 3 Opus original en velocidad y tareas de programación ligera.",
        "sources": ["Anthropic", "Arena.ai", "Artificial Analysis", "Aider"]
    },
    "gpt-4o": {
        "description": "Modelo omni insignia de OpenAI con soporte nativo de texto, visión y herramientas.",
        "use_cases": [
            "Flujos multimodales empresariales y análisis de imágenes.",
            "Asistente general de propósito múltiple con ecosistema maduro de herramientas."
        ],
        "comparison": "Estándar industrial de compatibilidad, equilibrado en todas las dimensiones.",
        "sources": ["OpenAI", "Arena.ai", "SWE-bench", "Aider", "Artificial Analysis", "Hugging Face"]
    },
    "o3-mini": {
        "description": "Modelo de razonamiento ligero de OpenAI optimizado para ciencias, matemáticas y programación (STEM).",
        "use_cases": [
            "Competiciones de programación, scripts complejos y análisis cuantitativo.",
            "Validación estricta de lógica y generación de pruebas de software."
        ],
        "comparison": "Mayor velocidad y menor coste que o1 completo, con capacidades de razonamiento profundo.",
        "sources": ["OpenAI", "Arena.ai", "SWE-bench", "Aider", "LiveBench", "Epoch AI"]
    },
    "qwen-2.5-coder-32b": {
        "description": "Especialista líder en código de pesos abiertos entrenado con más de 5.5 billones de tokens de software.",
        "use_cases": [
            "Autocompletado y copiloto de programación local o auto-hospedado.",
            "Generación y depuración en más de 90 lenguajes de programación."
        ],
        "comparison": "El mejor modelo de código en su categoría de 32B parámetros, superando a muchos modelos comerciales 70B+.",
        "sources": ["Alibaba Cloud", "Hugging Face", "SWE-bench", "Aider", "LiveBench", "OpenRouter"]
    },
    "llama-3.3-70b": {
        "description": "Modelo insignia de pesos abiertos de Meta con 70B de parámetros y ventana de 128k tokens.",
        "use_cases": [
            "Despliegues corporativos soberanos en servidores locales o nubes privadas.",
            "Base para fine-tuning especializado en dominios empresariales."
        ],
        "comparison": "Ofrece rendimiento comparable a Llama 3.1 405B en la mayoría de tareas prácticas a un coste de inferencia mucho menor.",
        "sources": ["Meta AI", "Arena.ai", "Hugging Face", "Aider", "OpenRouter"]
    },
    "nous-hermes-3-70b": {
        "description": "Modelo centrado en la soberanía del usuario, seguimiento de instrucciones sin censura corporativa y razonamiento agentico.",
        "use_cases": [
            "Agentes autónomos complejos, creación de mundos y generación de roles.",
            "Llamadas a funciones estructuradas avanzadas y JSON generation."
        ],
        "comparison": "Alta adaptabilidad para flujos de investigación sin filtros artificiales.",
        "sources": ["Nous Research", "OpenRouter", "Hermes Endpoint"]
    },
    "anthropic-claude-fable-5": {
        "description": "Modelo insignia de frontera agéntica de Anthropic con capacidades avanzadas de autonomía y razonamiento largo.",
        "use_cases": [
            "Orquestación de flujos agénticos autónomos complejos y multi-herramienta.",
            "Ingeniería de software, síntesis y arquitectura de sistemas."
        ],
        "comparison": "Diseñado para tareas agénticas de vanguardia de Anthropic con alta coherencia.",
        "sources": ["Anthropic", "OpenRouter Catalog"]
    },
    "qwen3.8-max": {
        "description": "Modelo insignia de frontera de Alibaba Cloud para razonamiento multilingüe y resolución de problemas complejos.",
        "use_cases": [
            "Razonamiento matemático y técnico profundo.",
            "Traducción y desarrollo de software multilingüe a gran escala."
        ],
        "comparison": "El modelo más potente de Alibaba Cloud, compitiendo en la categoría de frontera.",
        "sources": ["Alibaba Cloud", "OpenRouter Catalog", "DashScope"]
    },
    "grok-4.6": {
        "description": "Modelo de razonamiento de frontera de xAI con comprensión profunda y amplias capacidades de análisis de datos.",
        "use_cases": [
            "Razonamiento lógico formal, análisis en tiempo real y codificación.",
            "Flujos de trabajo multi-agente complejos."
        ],
        "comparison": "Modelo de máxima capacidad de la familia Grok de xAI.",
        "sources": ["xAI", "Grokified"]
    },
    "glm-5.3": {
        "description": "Modelo insignia de frontera de Zhipu AI con ventana de contexto de 262k y alta precisión en razonamiento.",
        "use_cases": [
            "Comprensión de documentos complejos y generación estructurada.",
            "Tareas de programación y agentes de flujo continuo."
        ],
        "comparison": "Frontier de Zhipu AI para alto rendimiento y despliegue rápido.",
        "sources": ["Zhipu AI", "Z.AI Platform"]
    }
}


# ---------------------------------------------------------------------------
# Heurísticas de metadatos (perfil, dueño, variante, capacidades)
# Conservadas desde v9.5. No forman parte del cálculo matemático del FCI.
# ---------------------------------------------------------------------------

_OWNER_KEYWORDS = (
    ("anthropic", "claude"), ("google", "gemini", "gemma"),
    ("openai", "gpt", "o1", "o3"), ("deepseek",),
    ("qwen", "alibaba", "dashscope"), ("mistral", "codestral"),
    ("zhipu", "glm", "z-ai"), ("grok", "xai", "x-ai"),
    ("meta", "llama"),
)


def _infer_owner(model_id: str, provider_default: str) -> str:
    cid = model_id.lower()
    for group in _OWNER_KEYWORDS:
        for kw in group[1:] if len(group) > 1 else group:
            if kw in cid:
                return group[0].title() if group[0] not in ("xai",) else "xAI"
    return provider_default


def _infer_variant(model_id: str) -> str:
    cid = model_id.lower()
    if ":batch" in cid:
        return "Batch Processing"
    if any(t in cid for t in ("fast", "flash", "turbo")):
        return "Fast / Turbo"
    if any(t in cid for t in ("pro", "max")):
        return "High Reasoning (Pro/Max)"
    if any(t in cid for t in ("r1", "o3", "o1", "reasoner", "thinking")):
        return "Reasoning CoT"
    return "Standard"


def _infer_capabilities(model: Dict[str, Any], family_id: str, variant: str) -> List[str]:
    cid = model["id"].lower()
    caps = []
    if model.get("tier") == "frontier" or any(k in cid for k in ("fable", "opus", "gpt-5")):
        caps.append("FRONTIER")
    if model.get("supports_reasoning") or any(k in cid for k in ("reason", "r1", "o1", "o3", "thinking")):
        caps.append("REASONING")
    if model.get("supports_tools") or "agent" in cid:
        caps.append("AGENTIC")
    if model.get("tier") == "coding" or any(k in cid for k in ("code", "coder", "dev", "sonnet")):
        caps.append("CODING")
    ctx = int(model.get("context_window") or 0)
    if ctx >= 1_000_000:
        caps.append("1M+ CONTEXT")
    elif ctx >= 200_000:
        caps.append("LONG CONTEXT")
    if model.get("supports_vision"):
        caps.append("VISION")
    if not caps:
        caps.append((model.get("tier") or "workhorse").upper())
    return caps


# ---------------------------------------------------------------------------
# Fachada V3: delega en RankingEngineV3, conserva el dict-shape del contrato
# ---------------------------------------------------------------------------

# Benchmarks con observación y que el QualityGate acepta
_CORE_BENCHMARKS = (
    "arena_elo", "chatbot_arena", "aa_quality_index",
    "livebench", "epoch_science", "swe_bench", "aider_polyglot",
    "humaneval", "livecodebench", "mmlu_pro", "gpqa", "math_500",
    "ifeval", "hf_average", "arena_coding_elo", "aider_edit_format",
    "speed_tokens_sec", "ttft_seconds",
)


def _enrich_workhorse(fci: Optional[float], model: Dict[str, Any], raw_benchmarks: Dict[str, float]) -> Optional[float]:
    """Cálculo del Workhorse Efficiency preservado de v9.5."""
    if fci is None:
        return None
    input_cost = max(0.0, float(model.get("input_cost_per_m") or 0.0))
    output_cost = max(0.0, float(model.get("output_cost_per_m") or 0.0))
    is_free = bool(model.get("is_free_tier")) or (input_cost == 0.0 and output_cost == 0.0) or ":free" in model["id"].lower()
    cost_total = (input_cost + output_cost) or 0.10
    cost_factor = 1.0 if is_free else max(0.2, 1.0 / (1.0 + (cost_total / 2.0)))
    speed = max(0.0, raw_benchmarks.get("speed_tokens_sec", 0.0))
    speed_factor = min(1.0, speed / 150.0) if speed > 0 else 0.5
    return round(fci * 0.5 + (cost_factor * 100.0) * 0.3 + (speed_factor * 100.0) * 0.2, 1)



def _evidence_badge(conf: float, n_sources: int, has_disagreement: bool) -> tuple:
    if conf >= 0.80 and n_sources >= 3 and not has_disagreement:
        return "🟢 SOTA VERIFICADO", "A+ (Multi-Benchmark SOTA)"
    if conf >= 0.65:
        return "🟢 ALTA CERTEZA", "A (Alta Corroboración)"
    if conf >= 0.45:
        return "🟡 EVIDENCIA MODERADA", "B (Evidencia Moderada)"
    if conf >= 0.30:
        return "🟠 EVIDENCIA LIMITADA", "C (Evidencia Limitada)"
    if conf >= 0.18:
        return "⚪ CATÁLOGO NO EVALUADO", "D (Catálogo No Evaluado)"
    return "⚪ PRELIMINAR", "E (Preliminar)"


def calculate_multidimensional_rankings() -> List[Dict[str, Any]]:
    """
    Fachada de compatibilidad sobre RankingEngineV3 (FloydIA Protocol V11).
    Mantiene la firma y estructura esperada por los consumidores (web, cli, gui, analyst).
      - Probit Rank Normalization con top-stretch anti-saturación.
      - Agregación bayesiana con procedencia estricta por campo (Measurement).
      - Intervalo de Confianza 95% transparente [ci_lower, ci_upper].
      - Grados de evidencia A-E calibrados empíricamente.
    """
    local_verified = get_latest_local_verified_models()
    local_functional_keys = get_local_functional_model_keys()
    local_active_ids = {
        m["canonical_id"]: m for m in local_verified
        if m["is_functional"] and m.get("canonical_id")
        and not m.get("is_synthetic") and m.get("latency_ms") is not None
    }

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models")
        models = [dict(r) for r in cursor.fetchall()]

        # Evaluaciones crudas + calidad (solo mediciones empíricas: excluye fallbacks estáticos)
        cursor.execute("""
            SELECT model_id, benchmark_name, AVG(score) as avg_score, MAX(recorded_at) as last_date,
                   GROUP_CONCAT(DISTINCT source) as sources_list
            FROM evaluations
            WHERE provenance != 'fallback'
            GROUP BY model_id, benchmark_name
        """)
        evals_raw = cursor.fetchall()

    # Índice de observaciones (filtradas por QualityGate) en formato V3
    observations: List[Dict[str, Any]] = []
    for r in evals_raw:
        bname = r["benchmark_name"]
        score_val = float(r["avg_score"])
        q_status, _ = quality_engine.validate_metric(bname, score_val)
        if q_status == QualityStatus.REJECTED:
            continue
        sources = [s.strip() for s in (r["sources_list"] or "").split(",") if s.strip()]
        if not sources:
            sources = ["unknown"]
        for src in sources:
            observations.append({
                "model_id": r["model_id"],
                "benchmark_name": bname,
                "score": score_val,
                "source": src,
                "recorded_at": r["last_date"],
            })

    # Motor V3: produce ranking ordenado con IC y empates de Welch
    v3_results = ranking_engine_v3.score_models(models, observations)

    scored_models: List[Dict[str, Any]] = []
    by_id = {m["id"]: m for m in models}

    for r in v3_results:
        m = by_id.get(r.model_id, {})
        raw_name = m.get("canonical_name") or r.model_id
        cleaned_id = r.model_id.lower()
        owner = _infer_owner(r.model_id, m.get("provider", "Unknown"))
        variant = _infer_variant(r.model_id)
        capabilities = _infer_capabilities(m, r.family_id, variant)

        # Benchmarks crudos observados
        raw_benchmarks = {
            row["benchmark_name"]: float(row["avg_score"])
            for row in evals_raw
            if row["model_id"] == r.model_id
            and quality_engine.validate_metric(row["benchmark_name"], float(row["avg_score"]))[0] != QualityStatus.REJECTED
        }
        sources_list = sorted({o["source"] for o in observations if o["model_id"] == r.model_id})

        freshness_days = r.extra.get("freshness_days", 0.0)
        _, _, freshness_status = freshness_engine.evaluate_freshness(
            max((o["recorded_at"] for o in observations if o["model_id"] == r.model_id), default=None)
        )

        # Costes y Workhorse
        input_cost = max(0.0, float(m.get("input_cost_per_m") or 0.0))
        output_cost = max(0.0, float(m.get("output_cost_per_m") or 0.0))
        is_free = bool(m.get("is_free_tier")) or (input_cost == 0.0 and output_cost == 0.0) or ":free" in cleaned_id
        workhorse = _enrich_workhorse(r.fci, m, raw_benchmarks)

        # Discrepancia inter-fuente
        between_std = r.extra.get("between_source_std", 0.0)
        has_disagreement = between_std > 9.0
        disagreement_msg = "⚠️ Alta discrepancia entre fuentes de benchmark" if has_disagreement else ""

        badge, grade = _evidence_badge(r.confidence, r.n_sources, has_disagreement)

        profile = MODEL_PROFILES.get(r.model_id, {
            "description": f"Modelo de lenguaje de {owner} evaluado en la categoría {(m.get('tier') or 'workhorse').upper()}.",
            "use_cases": [
                f"Procesamiento y generación de texto en la categoría {m.get('tier')}.",
                f"Inferencia mediante {m.get('provider')}."
            ],
            "comparison": f"Evaluado con FCI {r.fci}/100 y grado de evidencia {grade}.",
            "sources": sources_list or ["Catálogo FloydIA"]
        })
        all_sources = list(set(profile.get("sources", []) + sources_list))

        # Local probe info (Dual-key matching: canonical_id OR model_identifier OR aliases)
        local_info = local_active_ids.get(r.model_id) or local_functional_keys.get(r.model_id) or local_functional_keys.get(m.get("id"))
        if not local_info and m.get("aliases_json"):
            try:
                aliases = json.loads(m.get("aliases_json") or "[]")
                for al in aliases:
                    if al in local_functional_keys or al.lower() in local_functional_keys:
                        local_info = local_functional_keys.get(al) or local_functional_keys.get(al.lower())
                        break
            except Exception:
                pass
        has_empirical = (r.n_metrics > 0 and r.fci is not None)

        scored_models.append({
            # Identidad
            "id": r.model_id,
            "canonical_name": raw_name,
            "model_owner": owner,
            "api_provider": m.get("provider", ""),
            "variant": variant,
            "capabilities": capabilities,
            "tier": m.get("tier"),
            "provider": m.get("provider"),
            "context_window": m.get("context_window"),
            "max_output": m.get("max_output"),
            "is_free_tier": is_free,
            "input_cost_per_m": input_cost,
            "output_cost_per_m": output_cost,
            "supports_tools": bool(m.get("supports_tools")),
            "supports_vision": bool(m.get("supports_vision")),
            "supports_reasoning": bool(m.get("supports_reasoning")),
            "family_id": r.family_id,
            "canonical_variant": r.variant,
            # FCI e Incertidumbre Transparente (V11)
            "intelligence_score": r.fci,
            "fci_score": r.fci,
            "fci_display": f"{r.fci} ± {r.margin_95}" if r.fci is not None else "SIN DATO",
            "uncertainty_margin": r.margin_95,
            "ci_lower": r.ci_lower,
            "ci_upper": r.ci_upper,
            "ci_display": r.ci_display,
            "lower_confidence_bound": r.lower_confidence_bound,
            "effective_score": round(r.fci * (0.85 + 0.15 * r.confidence), 1) if r.fci is not None else None,
            "confidence_score": r.confidence,
            "confidence_badge": badge,
            "evidence_grade": grade,
            "has_disagreement": has_disagreement,
            "disagreement_message": disagreement_msg,
            "sample_size": r.n_metrics,
            "n_metrics": r.n_metrics,
            "n_sources": r.n_sources,
            "coverage_pillars": r.coverage_pillars,
            "measured_pillars_count": r.measured_pillars_count,
            "is_empirically_measured": has_empirical,
            "variance": between_std ** 2,
            # Pilares observados (None si no tienen observación empírica real)
            "pillar_reasoning": round(r.pillars["reasoning"].mean, 1) if ("reasoning" in r.pillars and r.pillars["reasoning"].observed) else None,
            "pillar_coding": round(r.pillars["coding"].mean, 1) if ("coding" in r.pillars and r.pillars["coding"].observed) else None,
            "pillar_quality": round(r.pillars["quality"].mean, 1) if ("quality" in r.pillars and r.pillars["quality"].observed) else None,
            "pillar_preference": round(r.pillars["preference"].mean, 1) if ("preference" in r.pillars and r.pillars["preference"].observed) else None,
            "pillar_agentic": round(r.pillars["agentic"].mean, 1) if ("agentic" in r.pillars and r.pillars["agentic"].observed) else None,
            "pillar_shrinkage": {
                p: round(r.pillars[p].shrinkage, 3) for p in r.pillars
            },
            # Scores por dimensión (Estricta procedencia: None si no medido)
            "workhorse_score": workhorse if r.fci is not None else "SIN DATO",
            "coding_score": round(r.pillars["coding"].mean, 1) if ("coding" in r.pillars and r.pillars["coding"].observed) else None,
            "preference_score": round(r.pillars["preference"].mean, 1) if ("preference" in r.pillars and r.pillars["preference"].observed) else None,
            "quality_score": round(r.pillars["quality"].mean, 1) if ("quality" in r.pillars and r.pillars["quality"].observed) else None,
            "reasoning_score": round(r.pillars["reasoning"].mean, 1) if ("reasoning" in r.pillars and r.pillars["reasoning"].observed) else None,
            "agentic_score": round(r.pillars["agentic"].mean, 1) if ("agentic" in r.pillars and r.pillars["agentic"].observed) else None,
            # Trazabilidad y Benchmarks Crudos
            "raw_benchmarks": {k: round(v, 2) for k, v in raw_benchmarks.items()},
            "intel_benchmarks": {k: round(v, 2) for k, v in raw_benchmarks.items()},
            "coding_benchmarks": {k: round(v, 2) for k, v in raw_benchmarks.items() if any(c in k for c in ["swe", "code", "coder", "aider", "human"])},
            "freshness_days": freshness_days,
            "freshness_status": freshness_status,
            "observation_type": r.observation_type.value,
            "global_rank": r.global_rank,
            "is_statistical_tie": r.is_statistical_tie,
            # Estado local
            "is_local_active": bool(local_info),
            "local_badge": "🟢 LOCAL ACTIVO" if local_info else "⚪ EXTERNO",
            "local_latency_ms": local_info["latency_ms"] if local_info else None,
            "local_status_msg": local_info["status_message"] if local_info else None,
            "account_email": local_info.get("account_email", "—") if local_info else "—",
            "account_key": local_info.get("account_key", "") if local_info else "",
            "local_detected_context": local_info["detected_context_window"] if local_info else m.get("context_window"),
            # Perfil
            "description": profile.get("description", ""),
            "use_cases": profile.get("use_cases", []),
            "comparison": profile.get("comparison", ""),
            "sources": all_sources,
        })

    # Persistir tablas relacionales certificadas (model_measurements, model_grades, rankings)
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM rankings")
            c.execute("DELETE FROM model_measurements")
            c.execute("DELETE FROM model_grades")

            for r in v3_results:
                # 1. model_grades
                c.execute("""
                    INSERT OR REPLACE INTO model_grades (canonical_id, fci, confidence, grade, measured_pillars_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (r.model_id, r.fci, r.confidence, r.evidence_grade, r.measured_pillars_count))

                # 2. rankings (solo si está medido con fci y rank público)
                if r.fci is not None and r.global_rank is not None:
                    c.execute("""
                        INSERT OR REPLACE INTO rankings (canonical_id, global_rank, fci, ci_lower, ci_upper, confidence, evidence_grade)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (r.model_id, r.global_rank, r.fci, r.ci_lower, r.ci_upper, r.confidence, r.evidence_grade))

                # 3. model_measurements por pilar
                for pill_name, p in r.pillars.items():
                    m_sources = [o["source"] for o in observations if o["model_id"] == r.model_id]
                    src_tag = m_sources[0] if (p.observed and m_sources) else (None if not p.observed else "BenchmarkSuite")
                    c.execute("""
                        INSERT INTO model_measurements (canonical_id, pillar, measured, n_obs, score, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (r.model_id, pill_name, 1 if p.observed else 0, p.n_obs, round(p.mean, 2) if p.observed else None, src_tag))

                # 4. Inserción de pilar 'intelligence' general
                if r.fci is not None and r.n_metrics > 0:
                    m_sources = [o["source"] for o in observations if o["model_id"] == r.model_id]
                    # Desglose de fuente primaria de inteligencia
                    aa_present = any("artificial" in s.lower() for s in m_sources)
                    hf_present = any("hugging" in s.lower() or "mmlu" in s.lower() for s in m_sources)
                    arena_present = any("arena" in s.lower() for s in m_sources)
                    live_present = any("live" in s.lower() or "epoch" in s.lower() for s in m_sources)
                    
                    intel_src = "ArtificialAnalysis" if aa_present else ("HuggingFace" if hf_present else ("ArenaAI" if arena_present else ("LiveBench" if live_present else (m_sources[0] if m_sources else "BenchmarkSuite"))))
                    c.execute("""
                        INSERT INTO model_measurements (canonical_id, pillar, measured, n_obs, score, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (r.model_id, "intelligence", 1, r.n_metrics, r.fci, intel_src))
    except Exception as e:
        print(f"⚠️ [Scoring] Error persistiendo tablas relacionales: {e}")

    return scored_models


def build_input_data_payload(
    rankings_data: List[Dict[str, Any]],
    local_apis_data: List[Dict[str, Any]],
    profile_categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    ETAPA A (Grounded Reporting Contract V11):
    Construye el payload JSON canónico INPUT_DATA estrictamente fundamentado en datos reales.
    Cualquier valor numérico no observado empíricamente se serializa explícitamente como `None` (null en JSON).
    """
    if profile_categories is None:
        profile_categories = ["frontier", "workhorse", "reasoning", "coding", "agentic"]

    models_payload = []
    for m in rankings_data:
        raw_b = m.get("raw_benchmarks", {})
        sources = m.get("sources", [])
        is_empirical = m.get("is_empirically_measured", False) or bool(raw_b)

        # Fuentes por métrica
        intel_src = "artificial_analysis" if "aa_quality_index" in raw_b else ("livebench" if "livebench" in raw_b else ("huggingface" if "mmlu_pro" in raw_b else (sources[0].lower() if (sources and is_empirical) else None)))
        coding_src = "livecodebench" if "livecodebench" in raw_b else ("swebench" if "swe_bench" in raw_b else ("aider" if "aider_polyglot" in raw_b else ("arena_coding" if "arena_coding_elo" in raw_b else None)))
        elo_src = "arena_ai" if "arena_elo" in raw_b else ("lmsys" if "chatbot_arena" in raw_b else None)
        pricing_src = "openrouter" if m.get("input_cost_per_m") is not None else None
        latency_src = "local_probe" if m.get("local_latency_ms") is not None else None

        elo_val = raw_b.get("arena_elo") or raw_b.get("chatbot_arena")

        # Procedencia estricta: si no está medido empíricamente, el redactor ve null (Regla 1)
        intel_val = m.get("intelligence_score") if is_empirical else None

        models_payload.append({
            "id": m["id"],
            "display_name": m["canonical_name"],
            "provider": m.get("provider", "Unknown"),
            "category": m.get("tier", "workhorse"),
            "is_local": bool(m.get("is_local_active")),
            "is_measured": is_empirical,
            "context_window": m.get("context_window"),
            "pricing_in_per_1m": m.get("input_cost_per_m"),
            "pricing_out_per_1m": m.get("output_cost_per_m"),
            "pricing_source": pricing_src,
            "latency_ms": m.get("local_latency_ms"),
            "latency_source": latency_src,
            "intelligence_index": intel_val,
            "intelligence_source": intel_src if intel_val is not None else None,
            "ci_95": m.get("ci_display"),
            "lower_confidence_bound": m.get("lower_confidence_bound"),
            "coding_index": m.get("coding_score"),
            "coding_source": coding_src if m.get("coding_score") is not None else None,
            "preference_index": m.get("preference_score"),
            "elo_lmsys": elo_val,
            "elo_source": elo_src,
            "confidence_score": m.get("confidence_score"),
            "evidence_grade": m.get("evidence_grade"),
            "raw_benchmarks": raw_b,
        })

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "profile_categories": profile_categories,
        "models": models_payload
    }


