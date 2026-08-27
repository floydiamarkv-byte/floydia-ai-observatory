"""
Motor de Confianza y Calibración Probabilística de Rankings (ConfidenceEngine).
Calcula la fiabilidad de cada score a partir de la fuente, frescura y corroboración cruzada.
"""

from typing import List, Dict, Any, Set
from src.core.contracts import ObservationType

# Matriz de fiabilidad base por fuente
SOURCE_POLICY: Dict[str, float] = {
    "lmsys": 0.95,
    "arena_ai": 0.95,
    "arenaai": 0.95,
    "artificial_analysis": 0.94,
    "artificialanalysis": 0.94,
    "livebench": 0.93,
    "livebenchepoch": 0.93,
    "swebench": 0.92,
    "aider": 0.92,
    "epoch_ai": 0.90,
    "huggingface": 0.90,
    "openrouter": 0.88,
    "google_ai_studio": 0.93,
    "deepseek_api": 0.93,
    "local_probe": 0.98,
    "default": 0.70
}

OBSERVATION_WEIGHTS: Dict[ObservationType, float] = {
    ObservationType.OBSERVED: 1.0,
    ObservationType.ESTIMATED: 0.85,
    ObservationType.IMPUTED: 0.70,
    ObservationType.DEFAULT: 0.50,
    ObservationType.HISTORICAL: 0.60,
    ObservationType.UNKNOWN: 0.50
}


class ConfidenceEngine:
    """Calcula el índice de certeza y solidez metodológica de un modelo."""

    def calculate_confidence(
        self,
        sources: List[str],
        freshness_decay: float,
        metrics_count: int,
        has_local_verification: bool = False,
        observation_type: ObservationType = ObservationType.OBSERVED
    ) -> float:
        """
        Calcula un score de confianza entre 0.0 y 1.0.
        """
        if not sources or metrics_count == 0:
            return 0.50  # Confianza mínima para modelos sin benchmarks externos

        # 1. Promedio de fiabilidad de las fuentes que aportaron datos
        rel_scores = []
        for s in sources:
            clean_s = s.lower().replace(" ", "_").replace(".", "")
            rel = SOURCE_POLICY.get(clean_s, SOURCE_POLICY.get("default", 0.70))
            rel_scores.append(rel)
        avg_source_rel = sum(rel_scores) / len(rel_scores) if rel_scores else 0.70

        # 2. Factor de corroboración cruzada (más fuentes = mayor confianza)
        source_count_bonus = min(0.15, (len(set(sources)) - 1) * 0.04)

        # 3. Factor de completitud de métricas (evaluado en múltiples dimensiones)
        metrics_bonus = min(0.10, (metrics_count - 1) * 0.02)

        # 4. Peso de tipo de observación
        obs_weight = OBSERVATION_WEIGHTS.get(observation_type, 0.80)

        # 5. Bonus por verificación directa en hardware local
        local_bonus = 0.05 if has_local_verification else 0.0

        # Ponderación combinada
        base_confidence = (
            (avg_source_rel * 0.45) +
            (freshness_decay * 0.25) +
            (obs_weight * 0.15) +
            source_count_bonus +
            metrics_bonus +
            local_bonus
        )

        return round(max(0.20, min(0.99, base_confidence)), 2)

    def get_badge(self, confidence_score: float) -> str:
        """Devuelve el badge visual de confianza para reportes y dashboard."""
        if confidence_score >= 0.85:
            return "🟢 HIGH CONFIDENCE"
        elif confidence_score >= 0.70:
            return "🟡 MODERATE CONFIDENCE"
        else:
            return "🟠 LIMITED EVIDENCE"


# Instancia global
confidence_engine = ConfidenceEngine()
