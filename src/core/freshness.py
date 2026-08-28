"""
Motor de Frescura y Decaimiento Temporal de Métricas (FreshnessEngine v11.1 - M-6).
Calcula el decaimiento exponencial continuo por fuente: freshness = 0.5 ** (días / half_life_fuente).
"""

import math
from datetime import datetime, timezone
from typing import Tuple, Optional
from config.settings import HALF_LIVES_BY_SOURCE


class FreshnessEngine:
    """Calcula la vigencia y factor de decaimiento continuo de las mediciones de benchmarks por fuente."""

    def __init__(self, half_life_days: float = 30.0):
        self.default_half_life = half_life_days

    def get_half_life(self, source: Optional[str] = None) -> float:
        if not source:
            return self.default_half_life
        s_clean = source.lower().replace(" ", "").replace("-", "_")
        return HALF_LIVES_BY_SOURCE.get(s_clean, self.default_half_life)

    def evaluate_freshness(
        self,
        timestamp: Optional[datetime | str],
        source: Optional[str] = None
    ) -> Tuple[float, float, str]:
        """
        Calcula (días_antigüedad, factor_frescura_0_a_1, estado_semántico).
        Aplica decaimiento continuo: freshness = 0.5 ** (días / half_life_fuente).
        """
        if not timestamp:
            return 999.0, 0.05, "⚫ HISTORICAL"

        if isinstance(timestamp, str):
            try:
                clean_ts = timestamp.replace("T", " ").split(".")[0]
                dt = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                try:
                    dt = datetime.strptime(timestamp[:10], "%Y-%m-%d")
                except Exception:
                    return 999.0, 0.05, "⚫ HISTORICAL"
        else:
            dt = timestamp

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        delta = now - dt
        days = max(0.0, delta.total_seconds() / 86400.0)

        half_life = self.get_half_life(source)
        # M-6: Decaimiento continuo 0.5 ** (dias / half_life)
        decay_factor = 0.5 ** (days / max(half_life, 1.0))
        decay_factor = max(0.05, min(1.0, decay_factor))

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

