"""
Motor de Enrutamiento Dinámico e Inteligente de LLMs (Cascading Router).
Permite a herramientas cliente (OpenCode, Hermes Agent, DeepSeek Harness, scripts)
consultar en tiempo real cuál es el modelo óptimo disponible en el clúster local
basándose en restricciones duras y ranking multicriterio (FCI, Latencia real, Coste, Evidencia).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from src.core.scoring import calculate_multidimensional_rankings
from src.core.db import get_latest_local_verified_models


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LLMRouter:
    """Orquestador de enrutamiento dinámico con restricciones duras y cascading fallbacks."""

    def __init__(self):
        self._cached_rankings: Optional[List[Dict[str, Any]]] = None
        self._cache_time: float = 0.0

    def recommend(
        self,
        task: str = "general",
        budget: str = "any",  # "free", "economy", "frontier", "any"
        max_latency_ms: Optional[float] = None,
        context_required: int = 4000,
        requires_tools: bool = False,
        requires_vision: bool = False,
        requires_reasoning: bool = False,
        requires_coding: bool = False,
        prefer_local_only: bool = True
    ) -> Dict[str, Any]:
        """
        Selecciona dinámicamente el modelo óptimo y una cascada ordenada de alternativas.
        """
        rankings = calculate_multidimensional_rankings()
        local_functional = [m for m in rankings if m.get("is_local_active")]

        candidate_pool = local_functional if prefer_local_only and local_functional else rankings
        
        # 1. Filtrado por Hard Constraints
        eligible: List[Dict[str, Any]] = []
        for m in candidate_pool:
            # Ventana de contexto suficiente
            ctx = m.get("context_window") or 128000
            if ctx < context_required:
                continue

            # Restricción de Presupuesto
            is_free = m.get("is_free_tier", False) or (m.get("input_cost_per_m", 0.0) == 0.0 and m.get("output_cost_per_m", 0.0) == 0.0)
            in_cost = m.get("input_cost_per_m", 0.0) or 0.0
            
            if budget == "free" and not is_free:
                continue
            elif budget == "economy" and in_cost > 1.5 and not is_free:
                continue

            # Restricciones de Capacidades
            tier = (m.get("tier") or "workhorse").lower()
            if requires_tools and not (m.get("supports_tools") or tier in ("coding", "agentic", "frontier")):
                continue
            if requires_vision and not (m.get("supports_vision") or tier in ("multimodal", "frontier")):
                continue
            if requires_reasoning and not (m.get("supports_reasoning") or tier in ("reasoning", "frontier")):
                continue
            if requires_coding and tier not in ("coding", "agentic", "frontier", "workhorse"):
                continue

            # Restricción dura de latencia si se especificó y el modelo tiene latencia medida
            lat = m.get("local_latency_ms")
            if max_latency_ms is not None and lat is not None and lat > max_latency_ms:
                continue

            eligible.append(m)

        # Si no hay elegibles estrictos, relajar latencia y capacidades no esenciales
        if not eligible:
            eligible = candidate_pool.copy()

        # 2. Ponderación Multicriterio
        task_lower = task.lower()
        scored_candidates = []

        for m in eligible:
            fci = m.get("intelligence_score") or 50.0
            conf = m.get("confidence") or 0.5
            lat = m.get("local_latency_ms") or 1200.0
            in_cost = m.get("input_cost_per_m") or 0.0
            out_cost = m.get("output_cost_per_m") or 0.0
            tier = (m.get("tier") or "workhorse").lower()
            supports_reas = m.get("supports_reasoning") or tier in ("reasoning", "frontier")
            supports_code = m.get("supports_tools") or tier in ("coding", "agentic", "frontier", "workhorse")

            # Puntuación base por pilar según tarea
            if task_lower in ("coding", "programming", "code"):
                base_val = m.get("coding_index") or fci
                core_score = base_val * 1.4 if supports_code else base_val * 0.7
            elif task_lower in ("reasoning", "math", "logic", "science"):
                base_val = m.get("reasoning_score") or fci
                core_score = base_val * 1.5 if supports_reas else base_val * 0.6
            elif task_lower in ("fast", "speed", "realtime"):
                core_score = fci * 0.9 + (max(0, 1500 - lat) / 100.0)
            else:
                core_score = fci

            # Bonificación por evidencia y telemetría local
            evidence_bonus = 10.0 if m.get("is_local_active") else 0.0
            if "A" in str(m.get("evidence_grade", "")):
                evidence_bonus += 5.0

            # Penalización por latencia suave
            lat_penalty = min(12.0, (lat / 250.0))
            if task_lower in ("fast", "speed", "realtime"):
                lat_penalty = (lat / 100.0)

            # Penalización por coste
            if budget == "frontier":
                cost_penalty = 0.0
            elif budget == "economy":
                cost_penalty = min(6.0, in_cost * 1.5)
            else:
                cost_penalty = min(15.0, (in_cost + out_cost) * 1.5)

            final_utility = (core_score * 0.7) + (conf * 15.0) + evidence_bonus - lat_penalty - cost_penalty
            scored_candidates.append((final_utility, m))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        if not scored_candidates:
            # Fallback de emergencia garantizado
            return {
                "status": "fallback_empty",
                "recommended_model": {
                    "id": "gemini-2.0-flash",
                    "canonical_name": "Google Gemini 2.0 Flash (Emergency Fallback)",
                    "provider": "Google",
                    "tier": "realtime",
                    "is_free_tier": True,
                    "local_latency_ms": 474.0,
                    "intelligence_score": 73.67,
                    "evidence_grade": "A",
                    "reason": "Modelo de emergencia asignado por falta de candidatos específicos"
                },
                "cascading_fallbacks": [],
                "constraints_applied": {"task": task, "budget": budget, "context_required": context_required},
                "generated_at": _now_iso()
            }

        primary = scored_candidates[0][1]
        primary_utility = scored_candidates[0][0]

        # Construir explicación transparente
        lat_txt = f"{primary.get('local_latency_ms')}ms" if primary.get('local_latency_ms') is not None else "Catálogo"
        cost_txt = "Gratuito" if primary.get("is_free_tier") else f"${primary.get('input_cost_per_m')}/1M"
        reason = f"Seleccionado para tarea '{task}' (Presupuesto: {budget}). Score FCI: {primary.get('intelligence_score')}/100, Latencia real: {lat_txt}, Coste: {cost_txt}, Grado Evidencia: {primary.get('evidence_grade', 'B')}."

        def _format_model_res(m_dict: Dict[str, Any], r_note: str) -> Dict[str, Any]:
            return {
                "id": m_dict.get("id"),
                "canonical_name": m_dict.get("canonical_name"),
                "provider": m_dict.get("provider"),
                "tier": m_dict.get("tier"),
                "context_window": m_dict.get("context_window"),
                "is_free_tier": m_dict.get("is_free_tier", False),
                "input_cost_per_m": m_dict.get("input_cost_per_m"),
                "output_cost_per_m": m_dict.get("output_cost_per_m"),
                "local_latency_ms": m_dict.get("local_latency_ms"),
                "intelligence_score": m_dict.get("intelligence_score"),
                "evidence_grade": m_dict.get("evidence_grade"),
                "supports_tools": m_dict.get("supports_tools", False),
                "supports_vision": m_dict.get("supports_vision", False),
                "supports_reasoning": m_dict.get("supports_reasoning", False),
                "local_verified": m_dict.get("is_local_active", False),
                "reason": r_note
            }

        fallbacks = []
        for i, (_, alt) in enumerate(scored_candidates[1:4]):
            role = ["Secondary", "Tertiary", "Emergency"][i]
            fallbacks.append(_format_model_res(alt, f"Alternativa {role}"))

        return {
            "status": "success",
            "recommended_model": _format_model_res(primary, reason),
            "cascading_fallbacks": fallbacks,
            "constraints_applied": {
                "task": task,
                "budget": budget,
                "max_latency_ms": max_latency_ms,
                "context_required": context_required,
                "requires_tools": requires_tools,
                "requires_vision": requires_vision,
                "requires_reasoning": requires_reasoning,
                "requires_coding": requires_coding
            },
            "routing_score": round(primary_utility, 2),
            "generated_at": _now_iso()
        }


# Instancia global Singleton
llm_router = LLMRouter()


def recommend_model(
    task: str = "general",
    budget: str = "any",
    max_latency_ms: Optional[float] = None,
    context_required: int = 4000,
    **kwargs
) -> Dict[str, Any]:
    """Helper global para invocar el Router dinámico de FloydIA."""
    return llm_router.recommend(
        task=task,
        budget=budget,
        max_latency_ms=max_latency_ms,
        context_required=context_required,
        **kwargs
    )
