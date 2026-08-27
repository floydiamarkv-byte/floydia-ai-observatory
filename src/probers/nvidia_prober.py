"""
Sonda y Verificador de NVIDIA NIM API.
Comprueba endpoints de DeepSeek V4, Nemotron 3 Nano, Kimi K3 en integrate.api.nvidia.com.
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import NVIDIA_API_KEY, NVIDIA_API_BASE
from src.core.normalizer import normalizer


def probe_nvidia_nim() -> List[Dict[str, Any]]:
    """Comprueba el estado de los modelos de NVIDIA NIM."""
    results = []
    if not NVIDIA_API_KEY:
        return results

    models_to_test = [
        {"model": "deepseek-ai/deepseek-v4-flash-0731", "context": 262144, "badge": "DeepSeek V4 (NIM)", "is_free": False, "in_cost": 0.10, "out_cost": 0.20},
        {"model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "context": 256000, "badge": "Nemotron 3 Nano (NIM)", "is_free": False, "in_cost": 0.05, "out_cost": 0.10},
        {"model": "moonshotai/kimi-k3", "context": 262144, "badge": "Kimi K3 (NIM)", "is_free": False, "in_cost": 0.15, "out_cost": 0.30}
    ]

    check_url = f"{NVIDIA_API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NVIDIA_API_KEY}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="NVIDIA")

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
                timeout=8
            )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            status_code = resp.status_code
            if resp.status_code == 200:
                is_ok = True
                status_msg = "🟢 Operativa (200 OK)"
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:80]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 8000.0
            status_msg = "🔴 Timeout (>8s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "NVIDIA NIM",
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
