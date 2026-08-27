"""
Motor de Calidad y Validación de Datos de Benchmarks (DataQualityEngine).
Rechaza anomalías duras (precios negativos, scores fuera de rango) y detecta valores sintéticos/constantes.
"""

from typing import List, Dict, Any, Tuple
from src.core.contracts import MetricObservation, QualityStatus, ObservationType


class DataQualityEngine:
    """Validador y detector de anomalías para métricas de modelos de IA."""

    def __init__(self, constant_threshold: int = 8):
        self.constant_threshold = constant_threshold

    def validate_metric(self, metric_name: str, value: float) -> Tuple[QualityStatus, str]:
        """
        Valida que una métrica cumpla límites plausibles.
        Retorna (QualityStatus, motivo).
        """
        if value is None:
            return QualityStatus.REJECTED, "NULL_VALUE"

        # Precios: jamás negativos
        if "cost" in metric_name or "price" in metric_name:
            if value < 0.0:
                return QualityStatus.REJECTED, "NEGATIVE_PRICE"

        # Latencias: no negativas
        if "latency" in metric_name or "ttft" in metric_name:
            if value < 0.0:
                return QualityStatus.REJECTED, "NEGATIVE_LATENCY"

        # Scores porcentuales estándar (0 a 100)
        if metric_name in ["mmlu_pro", "gpqa", "math_500", "humaneval", "swe_bench", "aider_polyglot", "livebench", "aa_quality_index"]:
            if value < 0.0 or value > 100.0:
                return QualityStatus.REJECTED, "SCORE_OUT_OF_BOUNDS_0_100"

        # Elo ratings (Arena)
        if "elo" in metric_name or "arena" in metric_name:
            if value < 400.0 or value > 2500.0:
                return QualityStatus.REJECTED, "ELO_OUT_OF_BOUNDS"

        return QualityStatus.VALID, "PASS"

    def detect_constant_values(self, observations: List[MetricObservation]) -> List[MetricObservation]:
        """
        Detecta si un valor se repite sospechosamente en una misma fuente (ej. latencia de 352.1 ms masiva).
        Si ocurre, lo reclasifica como ObservationType.DEFAULT y QualityStatus.SUSPICIOUS.
        """
        value_counts: Dict[Tuple[str, str, float], int] = {}
        for obs in observations:
            key = (obs.source, obs.metric, obs.value)
            value_counts[key] = value_counts.get(key, 0) + 1

        for obs in observations:
            key = (obs.source, obs.metric, obs.value)
            # Solo aplica a latencias y velocidades continuas, no a scores discretos o booleanos
            if ("latency" in obs.metric or "speed" in obs.metric) and value_counts[key] >= self.constant_threshold:
                obs.observation_type = ObservationType.DEFAULT
                obs.quality_status = QualityStatus.SUSPICIOUS
                obs.confidence *= 0.6  # Penalizar confianza de valores sintéticos

        return observations

    def filter_and_sanitize(self, observations: List[MetricObservation]) -> List[MetricObservation]:
        """Aplica la puerta de calidad completa sobre un conjunto de observaciones."""
        valid_obs = []
        for obs in observations:
            status, reason = self.validate_metric(obs.metric, obs.value)
            if status == QualityStatus.REJECTED:
                print(f"⚠️ [QualityGate] Rechazada métrica {obs.metric}={obs.value} de {obs.model_id} ({obs.source}): {reason}")
                continue
            obs.quality_status = status
            valid_obs.append(obs)

        return self.detect_constant_values(valid_obs)


# Instancia global
quality_engine = DataQualityEngine()
