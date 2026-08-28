"""
Sonda y Verificador de Grokified (xAI Grok API).
Comprueba el estado de los modelos Grok (4.6, 4.5, 4.20-multi-agent, build-0.1).
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import GROKIFIED_API_KEY, GROKIFIED_API_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_grokified() -> List[Dict[str, Any]]:
    """Comprueba el estado de los modelos de xAI Grokified."""
    results = []
    if not GROKIFIED_API_KEY:
        return results

    models_to_test = [
        {"model": "grok-4.6", "context": 262144, "badge": "Grok 4.6 (Frontier)", "is_free": False, "in_cost": 0.20, "out_cost": 0.50},
        {"model": "grok-4.5", "context": 131072, "badge": "Grok 4.5 (Workhorse)", "is_free": False, "in_cost": 0.15, "out_cost": 0.30},
        {"model": "grok-4.20-multi-agent-0309", "context": 262144, "badge": "Grok 4.20 Multi-Agent", "is_free": False, "in_cost": 0.25, "out_cost": 0.60},
        {"model": "grok-build-0.1", "context": 131072, "badge": "Grok Build 0.1 (Code)", "is_free": False, "in_cost": 0.10, "out_cost": 0.20}
    ]

    check_url = f"{GROKIFIED_API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROKIFIED_API_KEY}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="xAI")

        is_ok = False
        latency = 0.0
        status_msg = "No verificado"
        status_code = 500

        try:
            t0 = time.perf_counter()
            resp = requests.post(
                check_url,
                headers=headers,
                json={
                    "model": raw_name,
                    "messages": [{"role": "user", "content": "1"}],
                    "max_tokens": 2
                },
                timeout=4.0
            )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            status_code = resp.status_code
            if resp.status_code == 200:
                is_ok = True
                status_msg = "🟢 Operativa (200 OK)"
                key_pool.record_latency("GROKIFIED_API_KEY", latency)
            elif resp.status_code == 429:
                status_msg = "🟡 429 Rate Limit"
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 4000.0
            status_msg = "🔴 Timeout (>4s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "Grokified (xAI)",
            "model_identifier": raw_name,
            "canonical_id": can_id,
            "is_functional": is_ok,
            "status_code": status_code,
            "status_message": status_msg,
            "latency_ms": latency,
            "detected_context_window": item["context"],
            "supports_tools": True,
            "supports_vision": True,
            "supports_reasoning": True,
            "is_free_tier": item["is_free"],
            "cost_input_m": item["in_cost"],
            "cost_output_m": item["out_cost"]
        })

    return results
