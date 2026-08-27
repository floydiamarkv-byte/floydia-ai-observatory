"""
Contratos Canónicos y Taxonomía Unificada de Modelos y Métricas de IA (Kimi Protocol).
Garantiza inmutabilidad, trazabilidad de procedencia, tipo de observación y estado de ciclo de vida.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Set


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ModelStatus(str, Enum):
    """Ciclo de vida y estado de disponibilidad del modelo."""
    DISCOVERED = "discovered"      # La fuente externa menciona su existencia
    AVAILABLE = "available"        # El endpoint público existe
    CONFIGURED = "configured"      # FloydIA tiene credenciales/acceso configurado
    VERIFIED = "verified"          # Sonda FloydIA recibió respuesta 200 en vivo
    BENCHMARKED = "benchmarked"    # Posee evaluaciones cuantitativas válidas
    DEPRECATED = "deprecated"      # Retirado o reemplazado por versión más reciente
    FAILED = "failed"              # Endpoint inaccesible o error recurrente


class ObservationType(str, Enum):
    """Calidad y naturaleza del dato observado."""
    OBSERVED = "OBSERVED"          # Medición real observada en vivo
    ESTIMATED = "ESTIMATED"        # Interpolado con evidencia cuantitativa
    IMPUTED = "IMPUTED"            # Completado por modelo estadístico
    DEFAULT = "DEFAULT"            # Valor por defecto / sintético detectado
    HISTORICAL = "HISTORICAL"      # Snapshot histórico no reciente
    UNKNOWN = "UNKNOWN"            # Fuente no especificada


class QualityStatus(str, Enum):
    """Estado de validación por la puerta de calidad."""
    VALID = "VALID"                # Pasa todos los límites y reglas
    SUSPICIOUS = "SUSPICIOUS"      # Valor constante o fuera de distribución típica
    REJECTED = "REJECTED"          # Violación dura (precio negativo, score fuera de rango)
    PASS = "PASS"                  # Conjunto validado


class RankingDomain(str, Enum):
    """Dominios de evaluación desacoplados."""
    GENERAL = "general"
    REASONING = "reasoning"
    CODING = "coding"
    AGENTIC = "agentic"
    LONG_CONTEXT = "long_context"
    MULTIMODAL = "multimodal"
    SPEED = "speed"
    COST_EFFICIENCY = "cost_efficiency"
    EDGE = "edge"


@dataclass
class ModelIdentity:
    """Entidad canónica de un modelo de IA."""
    canonical_id: str
    display_name: str
    provider: str
    tier: str = "workhorse"
    status: ModelStatus = ModelStatus.DISCOVERED
    context_window: int = 128000
    max_output: int = 8192
    is_free_tier: bool = False
    input_cost_per_m: float = 0.0
    output_cost_per_m: float = 0.0
    supports_tools: bool = False
    supports_vision: bool = False
    supports_reasoning: bool = False
    aliases: List[str] = field(default_factory=list)
    source_ids: Dict[str, str] = field(default_factory=dict)
    release_date: Optional[str] = None
    deprecation_date: Optional[str] = None


@dataclass
class MetricObservation:
    """Registro individual de una observación o benchmark."""
    model_id: str
    metric: str
    value: float
    unit: str = "points"
    source: str = "unknown"
    observation_type: ObservationType = ObservationType.OBSERVED
    observed_at: datetime = field(default_factory=_now_utc)
    metric_timestamp: Optional[datetime] = None
    source_record_id: Optional[str] = None
    confidence: float = 1.0
    quality_status: QualityStatus = QualityStatus.VALID
    raw_value: Optional[Any] = None
