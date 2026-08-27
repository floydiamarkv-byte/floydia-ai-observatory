"""
Motor de Cálculo de Índices Sintéticos, Scoring Multidimensional y Metadatos de Modelo v9.0.
Calcula métricas desacopladas con transparencia de fuentes, asigna badges locales
y enriquece con casos de uso y comparativas.

Fuentes integradas (8):
  - OpenRouter (catálogo, precios)
  - Hugging Face (MMLU-Pro, GPQA, MATH, IFEval)
  - Artificial Analysis (velocidad, latencia, quality index)
  - LMSYS / Arena.ai (Elo de preferencia humana, Elo coding)
  - LiveBench (razonamiento anti-contaminación)
  - Epoch AI (ciencia)
  - SWE-bench (resolución de issues de GitHub)
  - Aider (coding polyglot multi-lenguaje)
"""

from typing import Dict, Any, List, Optional
from src.core.db import get_db_connection, get_latest_local_verified_models


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
    }
}


def calculate_multidimensional_rankings() -> List[Dict[str, Any]]:
    """
    Agrega todas las evaluaciones registradas, calcula los 4 índices sintéticos,
    asigna badges de disponibilidad local y enriquece con perfiles detallados.
    Incluye transparencia de fuentes (qué benchmarks contribuyeron a cada score).
    """
    local_verified = get_latest_local_verified_models()
    local_active_ids = {
        m["canonical_id"]: m for m in local_verified if m["is_functional"] and m["canonical_id"]
    }
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models")
        models = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("""
            SELECT model_id, benchmark_name, AVG(score) as avg_score, MAX(recorded_at) as last_date,
                   GROUP_CONCAT(DISTINCT source) as sources_list
            FROM evaluations
            GROUP BY model_id, benchmark_name
        """)
        evals_raw = cursor.fetchall()
    
    model_evals: Dict[str, Dict[str, float]] = {}
    model_sources: Dict[str, set] = {}
    
    for r in evals_raw:
        m_id = r["model_id"]
        if m_id not in model_evals:
            model_evals[m_id] = {}
            model_sources[m_id] = set()
        model_evals[m_id][r["benchmark_name"]] = float(r["avg_score"])
        if r["sources_list"]:
            for s in r["sources_list"].split(","):
                model_sources[m_id].add(s.strip())
    
    scored_models = []
    
    for m in models:
        m_id = m["id"]
        evals = model_evals.get(m_id, {})
        detected_sources = list(model_sources.get(m_id, []))
        
        # === User Preference Score (Arena.ai / LMSYS) ===
        arena_elo = evals.get("arena_elo", evals.get("chatbot_arena", 1150.0))
        preference_score = max(0.0, min(100.0, (arena_elo - 1000.0) / 4.0))
        
        # Track which benchmarks contributed
        intel_used = []
        coding_used = []
        
        # === Frontier Intelligence Score ===
        intel_metrics = []
        for k in ["mmlu_pro", "gpqa", "livebench", "math_500", "epoch_science", "aa_quality_index"]:
            if k in evals:
                intel_metrics.append(evals[k])
                intel_used.append(k)
        
        if intel_metrics:
            intelligence_score = sum(intel_metrics) / len(intel_metrics)
        else:
            tier_fallbacks = {"frontier": 88.0, "workhorse": 74.0, "coding": 76.0, 
                            "reasoning": 85.0, "agentic": 82.0, "multimodal": 78.0,
                            "long_context": 80.0, "uncensored": 72.0, "realtime": 70.0, 
                            "edge": 62.0}
            intelligence_score = tier_fallbacks.get(m["tier"], 65.0)

        # === Coding & Agentic Score (ahora con SWE-bench + Aider) ===
        coding_metrics = []
        for k in ["humaneval", "swe_bench", "aider_polyglot", "livecodebench", "arena_coding_elo"]:
            if k in evals:
                if k == "arena_coding_elo":
                    coding_metrics.append(max(0.0, min(100.0, (evals[k] - 1000.0) / 4.0)))
                else:
                    coding_metrics.append(evals[k])
                coding_used.append(k)
        
        if coding_metrics:
            coding_score = sum(coding_metrics) / len(coding_metrics)
        else:
            coding_score = intelligence_score * (1.1 if m["tier"] == "coding" else 0.95)
            coding_score = min(100.0, coding_score)

        # === Detección de Free Tier ===
        is_free = bool(m["is_free_tier"]) or (m["input_cost_per_m"] == 0.0 and m["output_cost_per_m"] == 0.0) or (":free" in m_id.lower())

        # === Workhorse Efficiency Score (con factor de velocidad real) ===
        cost_total = (m["input_cost_per_m"] + m["output_cost_per_m"]) or 0.10
        if is_free:
            cost_factor = 1.0
        else:
            cost_factor = max(0.2, 1.0 / (1.0 + (cost_total / 2.0)))
        
        # Incorporar velocidad real de Artificial Analysis si disponible
        speed = evals.get("speed_tokens_sec", 0)
        if speed > 0:
            speed_factor = min(1.0, speed / 150.0)  # Normalizar: 150 tok/s = factor 1.0
            workhorse_score = round(intelligence_score * 0.5 + (cost_factor * 100.0) * 0.3 + (speed_factor * 100.0) * 0.2, 1)
        else:
            workhorse_score = round(intelligence_score * 0.6 + (cost_factor * 100.0) * 0.4, 1)

        # === Local Readiness ===
        is_local_active = m_id in local_active_ids
        local_info = local_active_ids.get(m_id)

        # === Metadatos de perfil (Pop-up) ===
        profile = MODEL_PROFILES.get(m_id, {
            "description": f"Modelo de lenguaje de {m['provider']} clasificado en la categoría {m['tier'].upper()}.",
            "use_cases": [
                f"Procesamiento de texto general y tareas en la categoría {m['tier']}.",
                "Integración mediante APIs compatibles con OpenAI/OpenRouter."
            ],
            "comparison": f"Evaluado en la categoría {m['tier']} con score de inteligencia {round(intelligence_score, 1)}/100.",
            "sources": detected_sources or ["OpenRouter Datasets", "Benchmarks Agregados"]
        })

        all_sources = list(set(profile.get("sources", []) + detected_sources))
        if not all_sources:
            all_sources = ["OpenRouter Catalog", "Arena.ai"]

        scored_models.append({
            "id": m_id,
            "canonical_name": m["canonical_name"],
            "tier": m["tier"],
            "provider": m["provider"],
            "context_window": m["context_window"],
            "max_output": m["max_output"],
            "is_free_tier": is_free,
            "input_cost_per_m": m["input_cost_per_m"],
            "output_cost_per_m": m["output_cost_per_m"],
            "supports_tools": bool(m["supports_tools"]),
            "supports_vision": bool(m["supports_vision"]),
            "supports_reasoning": bool(m["supports_reasoning"]),
            # Índices
            "intelligence_score": round(intelligence_score, 1),
            "preference_score": round(preference_score, 1),
            "workhorse_score": round(workhorse_score, 1),
            "coding_score": round(coding_score, 1),
            # Transparencia de fuentes
            "intel_benchmarks": intel_used,
            "coding_benchmarks": coding_used,
            # Estado Local
            "is_local_active": is_local_active,
            "local_badge": "🟢 LOCAL ACTIVO" if is_local_active else "⚪ EXTERNO",
            "local_latency_ms": local_info["latency_ms"] if local_info else None,
            "local_status_msg": local_info["status_message"] if local_info else None,
            "local_detected_context": local_info["detected_context_window"] if local_info else m["context_window"],
            # Perfil para Pop-up
            "description": profile.get("description", ""),
            "use_cases": profile.get("use_cases", []),
            "comparison": profile.get("comparison", ""),
            "sources": all_sources
        })

    scored_models.sort(key=lambda x: x["intelligence_score"], reverse=True)
    
    for idx, sm in enumerate(scored_models, start=1):
        sm["global_rank"] = idx
        
    return scored_models
