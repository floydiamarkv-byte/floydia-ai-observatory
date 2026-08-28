"""
Sonda y Verificador de Alibaba Cloud DashScope (Qwen Direct API).
Comprueba el estado de los modelos insignia de la serie Qwen (3.8-max, 3.8-flash, 3.8-27b, 3.8-2.4t).
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import DASHSCOPE_API_KEY, DASHSCOPE_API_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_dashscope() -> List[Dict[str, Any]]:
    """Comprueba el estado de los modelos de Alibaba Cloud DashScope / Qwen."""
    results = []
    if not DASHSCOPE_API_KEY:
        return results

    models_to_test = [
        {"model": "qwen3.8-max", "context": 262144, "badge": "Qwen 3.8 Max (Frontier)", "is_free": False, "in_cost": 0.20, "out_cost": 0.60},
        {"model": "qwen3.8-flash", "context": 131072, "badge": "Qwen 3.8 Flash (Speed)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "qwen3.8-27b", "context": 131072, "badge": "Qwen 3.8 27B (Dense)", "is_free": False, "in_cost": 0.08, "out_cost": 0.16},
        {"model": "qwen3.7-flash", "context": 131072, "badge": "Qwen 3.7 Flash", "is_free": True, "in_cost": 0.0, "out_cost": 0.0}
    ]

    check_url = f"{DASHSCOPE_API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="Alibaba")

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
                key_pool.record_latency("DASHSCOPE_API_KEY", latency)
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
            "provider_name": "Alibaba DashScope",
            "model_identifier": raw_name,
            "canonical_id": can_id,
            "is_functional": is_ok,
            "status_code": status_code,
            "status_message": status_msg,
            "latency_ms": latency,
            "detected_context_window": item["context"],
            "supports_tools": True,
            "supports_vision": False,
            "supports_reasoning": True,
            "is_free_tier": item["is_free"],
            "cost_input_m": item["in_cost"],
            "cost_output_m": item["out_cost"]
        })

    return results
