"""
Sonda y Verificador de Fireworks AI API.
Comprueba endpoints de DeepSeek R1 y Llama 3.3 en api.fireworks.ai.
Detecta y documenta límites de cuenta y estados 412.
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import FIREWORKS_API_KEY, FIREWORKS_API_BASE
from src.core.normalizer import normalizer


def probe_fireworks() -> List[Dict[str, Any]]:
    """Comprueba el estado de los modelos en Fireworks AI."""
    results = []
    if not FIREWORKS_API_KEY:
        return results

    models_to_test = [
        {"model": "accounts/fireworks/models/deepseek-r1", "context": 160000, "badge": "DeepSeek R1 (Fireworks)", "is_free": False, "in_cost": 0.55, "out_cost": 2.19},
        {"model": "accounts/fireworks/models/llama-v3p3-70b-instruct", "context": 131072, "badge": "Llama 3.3 70B (Fireworks)", "is_free": False, "in_cost": 0.90, "out_cost": 0.90}
    ]

    check_url = f"{FIREWORKS_API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIREWORKS_API_KEY}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="Fireworks")

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
                timeout=6
            )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            status_code = resp.status_code
            if resp.status_code == 200:
                is_ok = True
                status_msg = "🟢 Operativa (200 OK)"
            elif resp.status_code == 412:
                status_msg = "🟡 412 Cuenta suspendida por límite de gasto mensual"
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 6000.0
            status_msg = "🔴 Timeout (>6s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "Fireworks AI",
            "model_identifier": raw_name,
            "canonical_id": can_id,
            "is_functional": is_ok,
            "status_code": status_code,
            "status_message": status_msg,
            "latency_ms": latency,
            "detected_context_window": item["context"],
            "supports_tools": True,
            "supports_vision": False,
            "is_free_tier": item["is_free"],
            "cost_input_m": item["in_cost"],
            "cost_output_m": item["out_cost"]
        })

    return results
