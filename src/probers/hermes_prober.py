"""
Sonda y Verificador de Endpoints Hermes / OpenAI-compatibles locales o VPS.
"""

import os
import time
from typing import Dict, Any, List
import requests
from src.core.normalizer import normalizer


def probe_hermes_endpoint() -> List[Dict[str, Any]]:
    """Comprueba el estado del endpoint de Hermes o servidor compatible."""
    results = []
    hermes_url = os.getenv("S17_VPS_HERMES_URL") or os.getenv("HERMES_API_URL")
    if not hermes_url:
        return results

    models_url = f"{hermes_url.rstrip('/')}/v1/models"
    try:
        t0 = time.perf_counter()
        resp = requests.get(models_url, timeout=4)
        latency = round((time.perf_counter() - t0) * 1000, 1)
        is_ok = (resp.status_code == 200)
        status_msg = "🟢 Operativa (Hermes VPS)" if is_ok else f"HTTP {resp.status_code}"
    except Exception as e:
        is_ok = False
        latency = 0.0
        status_msg = f"Inalcanzable ({e})"

    can_id, _ = normalizer.resolve("nous-hermes-3-70b", provider_hint="Hermes")
    results.append({
        "provider_name": "Hermes (Self-Hosted)",
        "model_identifier": "nous-hermes-3-70b",
        "canonical_id": can_id,
        "is_functional": is_ok,
        "status_code": 200 if is_ok else 500,
        "status_message": status_msg,
        "latency_ms": latency,
        "detected_context_window": 131072,
        "supports_tools": True,
        "supports_vision": False,
        "is_free_tier": True,
        "cost_input_m": 0.0,
        "cost_output_m": 0.0
    })
    return results
