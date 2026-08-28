"""
Motor de Confianza y Calibración Probabilística de Rankings (ConfidenceEngine v2).
Calcula la fiabilidad metodológica real de cada score a partir de la dispersión empírica,
cobertura de benchmarks, independencia de fuentes, decaimiento temporal y margen de error (CI 95%).
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from src.core.contracts import ObservationType

# Matriz de fiabilidad de la fuente (independencia e integridad metodológica)
SOURCE_POLICY: Dict[str, float] = {
    "artificial_analysis": 0.96,
    "artificialanalysis": 0.96,
    "livebench": 0.95,
    "livebenchepoch": 0.95,
    "epoch_ai": 0.95,
    "epochai": 0.95,
    "swebench": 0.94,
    "aider": 0.94,
    "lmsys": 0.92,
    "lmsysarena": 0.92,
    "arena_ai": 0.92,
    "arenaai": 0.92,
    "huggingface": 0.90,
    "openrouter": 0.82,
    "google_ai_studio": 0.90,
    "deepseek_api": 0.90,
    "default": 0.70
}

# Cobertura objetivo de pilares para máxima certeza
TARGET_BENCHMARK_COUNT = 6.0
TARGET_INDEPENDENT_SOURCES = 4.0


class ConfidenceEngine:
    """Calcula la certeza estadística, el margen de error y la concordancia inter-fuentes."""

    def evaluate_statistical_confidence(
        self,
        sources: List[str],
        freshness_decay: float,
        metric_values: List[float],
        metrics_count: int,
        has_local_verification: bool = False,
        observation_type: ObservationType = ObservationType.OBSERVED
    ) -> Dict[str, Any]:
        """
        Calcula un modelo de confianza probabilístico riguroso con intervalo de incertidumbre.
        Retorna dict con confidence_score, margin_error, ci_lower, ci_upper, grade y alertas.
        """
        unique_sources = list(set(sources)) if sources else []
        n_sources = len(unique_sources)
        n_metrics = max(len(metric_values), metrics_count)

        # 1. Caso sin mediciones empíricas (Catálogo o Estimado puro)
        if observation_type != ObservationType.OBSERVED or n_metrics == 0 or not metric_values:
            base_conf = 0.45 if observation_type == ObservationType.ESTIMATED else 0.30
            if has_local_verification:
                base_conf += 0.05
            return {
                "confidence_score": round(base_conf, 2),
                "uncertainty_margin": 4.8,
                "variance": 0.0,
                "has_disagreement": False,
                "disagreement_message": "",
                "evidence_grade": "D (Catálogo No Evaluado)",
                "badge": "🟠 ESTIMACIÓN TEÓRICA",
                "sample_size": n_metrics,
                "source_count": n_sources
            }

        # 2. Análisis de Dispersión / Varianza entre Métricas Observadas
        mean_val = sum(metric_values) / len(metric_values)
        if len(metric_values) > 1:
            variance = sum((x - mean_val) ** 2 for x in metric_values) / (len(metric_values) - 1)
            std_dev = math.sqrt(variance)
        else:
            variance = 16.0  # Varianza imputada para muestra única
            std_dev = 4.0

        # 3. Detección de Discrepancia entre Fuentes
        has_disagreement = std_dev > 9.0
        disagreement_msg = "⚠️ Alta discrepancia entre fuentes de benchmark" if has_disagreement else ""

        # 4. Margen de Error Estadístico (CI 95% = 1.96 * SE)
        se = std_dev / math.sqrt(max(1, len(metric_values)))
        # Margen acotado entre ±0.9 y ±4.5 puntos
        margin = round(max(0.9, min(4.5, 1.96 * se)), 1)

        # 5. Cálculo Probabilístico de Confianza (0.0 a 1.0)
        # Factor A: Cobertura de métricas (0.0 a 0.35)
        coverage_factor = min(1.0, n_metrics / TARGET_BENCHMARK_COUNT) * 0.35

        # Factor B: Independencia y calidad de fuentes (0.0 a 0.30)
        rel_scores = [SOURCE_POLICY.get(s.lower().replace(" ", "_").replace(".", ""), 0.75) for s in unique_sources]
        avg_rel = (sum(rel_scores) / len(rel_scores)) if rel_scores else 0.70
        source_factor = (min(1.0, n_sources / TARGET_INDEPENDENT_SOURCES) * 0.15) + (avg_rel * 0.15)

        # Factor C: Frescura temporal de los datos (0.0 a 0.20)
        freshness_factor = freshness_decay * 0.20

        # Factor D: Consistencia (penalización si alta varianza) (0.0 a 0.15)
        consistency_penalty = min(0.12, (std_dev / 25.0) * 0.12)
        consistency_factor = max(0.02, 0.15 - consistency_penalty)

        raw_conf = coverage_factor + source_factor + freshness_factor + consistency_factor
        if has_local_verification:
            raw_conf += 0.03

        # Acotar entre 0.40 y 0.96 (el 100% de certeza absoluta no existe en inferencia estocástica)
        confidence_score = round(max(0.40, min(0.96, raw_conf)), 2)

        # 6. Grado de Evidencia Científica (FloydIA Protocol V11)
        if confidence_score >= 0.80 and n_sources >= 3 and not has_disagreement:
            evidence_grade = "A+ (Multi-Benchmark SOTA)"
            badge = "🟢 SOTA VERIFICADO"
        elif confidence_score >= 0.65:
            evidence_grade = "A (Alta Corroboración)"
            badge = "🟢 ALTA CERTEZA"
        elif confidence_score >= 0.45:
            evidence_grade = "B (Evidencia Moderada)"
            badge = "🟡 EVIDENCIA MODERADA"
        elif confidence_score >= 0.30:
            evidence_grade = "C (Evidencia Limitada)"
            badge = "🟠 EVIDENCIA LIMITADA"
        elif confidence_score >= 0.18:
            evidence_grade = "D (Catálogo No Evaluado)"
            badge = "⚪ CATÁLOGO NO EVALUADO"
        else:
            evidence_grade = "E (Preliminar)"
            badge = "⚪ PRELIMINAR"

        return {
            "confidence_score": confidence_score,
            "uncertainty_margin": margin,
            "variance": round(variance, 2),
            "has_disagreement": has_disagreement,
            "disagreement_message": disagreement_msg,
            "evidence_grade": evidence_grade,
            "badge": badge,
            "sample_size": n_metrics,
            "source_count": n_sources
        }

    def calculate_confidence(
        self,
        sources: List[str],
        freshness_decay: float,
        metrics_count: int,
        has_local_verification: bool = False,
        observation_type: ObservationType = ObservationType.OBSERVED,
        metric_values: Optional[List[float]] = None
    ) -> float:
        """Calcula el score escalar de confianza (0.0 a 1.0) para compatibilidad."""
        res = self.evaluate_statistical_confidence(
            sources=sources,
            freshness_decay=freshness_decay,
            metric_values=metric_values or ([80.0] * max(1, metrics_count) if metrics_count else []),
            metrics_count=metrics_count,
            has_local_verification=has_local_verification,
            observation_type=observation_type
        )
        return res["confidence_score"]

    def get_badge(self, confidence_score: float) -> str:
        """Retorna el badge visual simplificado."""
        if confidence_score >= 0.85:
            return "🟢 HIGH CONFIDENCE"
        elif confidence_score >= 0.70:
            return "🟡 MODERATE EVIDENCE"
        else:
            return "🟠 LIMITED EVIDENCE"


# Instancia global
confidence_engine = ConfidenceEngine()


