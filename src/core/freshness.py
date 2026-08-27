"""
Motor de Frescura y Decaimiento Temporal de Métricas (FreshnessEngine).
Asigna ponderaciones decrecientes a datos antiguos y clasifica en estados semánticos.
"""

import math
from datetime import datetime
from typing import Tuple, Optional


class FreshnessEngine:
    """Calcula la vigencia y factor de decaimiento de las mediciones de benchmarks."""

    def __init__(self, half_life_days: float = 30.0):
        # Tiempo de vida media: tras 30 días, el peso decae al 50%
        self.half_life_days = half_life_days
        self.decay_constant = math.log(2) / half_life_days

    def evaluate_freshness(self, timestamp: Optional[datetime | str]) -> Tuple[float, float, str]:
        """
        Calcula (días_antigüedad, factor_frescura_0_a_1, estado_semántico).
        """
        if not timestamp:
            return 999.0, 0.2, "⚫ HISTORICAL"

        if isinstance(timestamp, str):
            try:
                # Intentar formato ISO o estándar SQLite
                clean_ts = timestamp.replace("T", " ").split(".")[0]
                dt = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                try:
                    dt = datetime.strptime(timestamp[:10], "%Y-%m-%d")
                except Exception:
                    return 999.0, 0.2, "⚫ HISTORICAL"
        else:
            dt = timestamp

        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        delta = now - dt
        days = max(0.0, delta.total_seconds() / 86400.0)

        # Factor de decaimiento exponencial e^(-lambda * t)
        decay_factor = math.exp(-self.decay_constant * days)

        # Estados semánticos de frescura
        if days <= 3.0:
            status = "🟢 FRESH"
        elif days <= 14.0:
            status = "🟡 RECENT"
        elif days <= 30.0:
            status = "🟠 AGING"
        elif days <= 90.0:
            status = "🔴 STALE"
        else:
            status = "⚫ HISTORICAL"

        return round(days, 1), round(decay_factor, 3), status


# Instancia global
freshness_engine = FreshnessEngine()
