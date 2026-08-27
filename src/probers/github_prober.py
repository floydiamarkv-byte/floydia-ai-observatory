"""
Sonda y Verificador de GitHub Models API (models.github.ai).
Comprueba endpoints de GPT-4o, o3-mini, Phi-4, DeepSeek-R1.
Detecta y documenta el estado de mantenimiento / brownout temporal.
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import GITHUB_TOKEN
from src.core.normalizer import normalizer


def probe_github_models() -> List[Dict[str, Any]]:
    """Comprueba el estado de los modelos en GitHub Models."""
    results = []
    if not GITHUB_TOKEN:
        return results

    models_to_test = [
        {"model": "gpt-4o", "context": 128000, "badge": "GPT-4o (GitHub Models)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "o3-mini", "context": 200000, "badge": "o3-mini (GitHub Models)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "Phi-4", "context": 16384, "badge": "Microsoft Phi-4 (GitHub)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0}
    ]

    check_url = "https://models.github.ai/inference/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="GitHub")

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
            elif resp.status_code == 410:
                status_msg = "🟡 410 GitHub Models en brownout / migración temporal"
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 6000.0
            status_msg = "🔴 Timeout (>6s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "GitHub Models",
            "model_identifier": raw_name,
            "canonical_id": can_id,
            "is_functional": is_ok,
            "status_code": status_code,
            "status_message": status_msg,
            "latency_ms": latency,
            "detected_context_window": item["context"],
            "supports_tools": True,
            "supports_vision": "4o" in raw_name,
            "is_free_tier": item["is_free"],
            "cost_input_m": item["in_cost"],
            "cost_output_m": item["out_cost"]
        })

    return results
