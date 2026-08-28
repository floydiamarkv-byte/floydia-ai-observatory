"""
Motor de Detección de Deriva (Drift) y Deprecación de Modelos y APIs (FloydIA Protocol).
Monitorea continuamente:
1. Variaciones de precios ($/1M tokens).
2. Degradación de latencias frente al baseline histórico (rolling median / p95).
3. Modificaciones en ventanas de contexto declaradas o detectadas.
4. Candidatos a deprecación por errores 404/410 reiterados.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from src.core.db import get_db_connection, record_drift_event, get_recent_drift_events


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DriftDetector:
    """Detecta y registra anomalías y cambios en el catálogo y rendimiento de APIs."""

    def __init__(self, latency_threshold_multiplier: float = 1.5, min_samples_for_latency: int = 3):
        self.latency_threshold = latency_threshold_multiplier
        self.min_samples = min_samples_for_latency

    def detect_catalog_drift(self, previous_models: List[Dict[str, Any]], current_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compara el catálogo de modelos previo con el actual para detectar cambios de precio y contexto.
        """
        events = []
        prev_map = {m["id"]: m for m in previous_models}

        for cur in current_models:
            m_id = cur.get("id")
            if not m_id or m_id not in prev_map:
                continue

            prev = prev_map[m_id]
            provider = cur.get("provider", "Unknown")

            # 1. Variación de Precio de Entrada
            prev_in = prev.get("input_cost_per_m")
            cur_in = cur.get("input_cost_per_m")
            if prev_in is not None and cur_in is not None and abs(prev_in - cur_in) > 0.0001:
                severity = "critical" if cur_in > prev_in * 1.2 else "warning"
                evt = {
                    "model_id": m_id,
                    "provider": provider,
                    "event_type": "price_change",
                    "metric_name": "input_cost_per_m",
                    "old_value": str(prev_in),
                    "new_value": str(cur_in),
                    "severity": severity,
                    "details": {"diff": round(cur_in - prev_in, 4), "percentage": round((cur_in - prev_in) / (prev_in or 1) * 100, 1)}
                }
                events.append(evt)
                record_drift_event(m_id, provider, "price_change", "input_cost_per_m", str(prev_in), str(cur_in), severity, evt["details"])

            # 2. Variación de Precio de Salida
            prev_out = prev.get("output_cost_per_m")
            cur_out = cur.get("output_cost_per_m")
            if prev_out is not None and cur_out is not None and abs(prev_out - cur_out) > 0.0001:
                severity = "critical" if cur_out > prev_out * 1.2 else "warning"
                evt = {
                    "model_id": m_id,
                    "provider": provider,
                    "event_type": "price_change",
                    "metric_name": "output_cost_per_m",
                    "old_value": str(prev_out),
                    "new_value": str(cur_out),
                    "severity": severity,
                    "details": {"diff": round(cur_out - prev_out, 4), "percentage": round((cur_out - prev_out) / (prev_out or 1) * 100, 1)}
                }
                events.append(evt)
                record_drift_event(m_id, provider, "price_change", "output_cost_per_m", str(prev_out), str(cur_out), severity, evt["details"])

            # 3. Cambio de Ventana de Contexto
            prev_ctx = prev.get("context_window")
            cur_ctx = cur.get("context_window")
            if prev_ctx and cur_ctx and prev_ctx != cur_ctx:
                severity = "critical" if cur_ctx < prev_ctx else "info"
                evt = {
                    "model_id": m_id,
                    "provider": provider,
                    "event_type": "context_window_change",
                    "metric_name": "context_window",
                    "old_value": str(prev_ctx),
                    "new_value": str(cur_ctx),
                    "severity": severity,
                    "details": {"diff_tokens": cur_ctx - prev_ctx}
                }
                events.append(evt)
                record_drift_event(m_id, provider, "context_window_change", "context_window", str(prev_ctx), str(cur_ctx), severity, evt["details"])

        return events

    def detect_latency_drift(self, model_id: str, provider: str, current_latency_ms: float) -> Optional[Dict[str, Any]]:
        """
        Compara la latencia actual contra el histórico de mediciones en base de datos.
        """
        if current_latency_ms is None or current_latency_ms <= 0:
            return None

        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT latency_ms FROM local_api_checks
                    WHERE (canonical_id = ? OR model_identifier LIKE ?)
                    AND is_functional = 1 AND latency_ms > 0
                    ORDER BY verified_at DESC LIMIT 15
                """, (model_id, f"%{model_id}%"))
                rows = [r[0] for r in c.fetchall() if r[0] is not None]

            if len(rows) < self.min_samples:
                return None

            # Calcular mediana histórica
            sorted_lat = sorted(rows)
            median_lat = sorted_lat[len(sorted_lat) // 2]

            if median_lat > 0 and current_latency_ms > (median_lat * self.latency_threshold):
                ratio = round(current_latency_ms / median_lat, 2)
                severity = "critical" if ratio >= 2.5 else "warning"
                evt = {
                    "model_id": model_id,
                    "provider": provider,
                    "event_type": "latency_degradation",
                    "metric_name": "latency_ms",
                    "old_value": f"{median_lat:.1f}ms (median)",
                    "new_value": f"{current_latency_ms:.1f}ms",
                    "severity": severity,
                    "details": {"ratio": ratio, "samples_evaluated": len(rows)}
                }
                record_drift_event(model_id, provider, "latency_degradation", "latency_ms", f"{median_lat:.1f}", f"{current_latency_ms:.1f}", severity, evt["details"])
                return evt
        except Exception as e:
            print(f"⚠️ [DriftDetector] Error analizando latencia para {model_id}: {e}")

        return None

    def detect_deprecation_candidate(self, model_id: str, provider: str, consecutive_404_count: int) -> Optional[Dict[str, Any]]:
        """
        Registra advertencia de posible deprecación de un endpoint tras múltiples fallos 404/410.
        """
        if consecutive_404_count >= 3:
            evt = {
                "model_id": model_id,
                "provider": provider,
                "event_type": "deprecation_candidate",
                "metric_name": "http_status",
                "old_value": "200 (OK)",
                "new_value": "404 (Not Found)",
                "severity": "critical",
                "details": {"consecutive_failures": consecutive_404_count}
            }
            record_drift_event(model_id, provider, "deprecation_candidate", "http_status", "200", "404", "critical", evt["details"])
            return evt
        return None


# Instancia global Singleton
drift_detector = DriftDetector()
