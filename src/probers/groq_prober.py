"""
Sonda y Verificador de Groq Cloud API.
Comprueba endpoints de Llama 3.3 70B, DeepSeek R1 Distill, Qwen 2.5 Coder 32B en api.groq.com.
Detecta y documenta 403 Forbidden / Claves a renovar.
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import GROQ_API_KEY, GROQ_API_BASE
from src.core.normalizer import normalizer


def probe_groq() -> List[Dict[str, Any]]:
    """Comprueba el estado de los modelos alojados en Groq Cloud."""
    results = []
    if not GROQ_API_KEY:
        return results

    models_to_test = [
        {"model": "llama-3.3-70b-versatile", "context": 131072, "badge": "Llama 3.3 70B (Groq LPU)", "is_free": True, "in_cost": 0.05, "out_cost": 0.08},
        {"model": "deepseek-r1-distill-llama-70b", "context": 131072, "badge": "DeepSeek R1 70B (Groq LPU)", "is_free": True, "in_cost": 0.07, "out_cost": 0.10},
        {"model": "qwen-2.5-coder-32b", "context": 32768, "badge": "Qwen 2.5 Coder 32B (Groq)", "is_free": True, "in_cost": 0.04, "out_cost": 0.06},
        {"model": "llama-3.1-8b-instant", "context": 131072, "badge": "Llama 3.1 8B Instant (Groq)", "is_free": True, "in_cost": 0.02, "out_cost": 0.03}
    ]

    check_url = f"{GROQ_API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="Groq")

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
            elif resp.status_code == 403:
                status_msg = "🔴 403 Forbidden (Clave de Groq requiere renovación en console.groq.com)"
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 6000.0
            status_msg = "🔴 Timeout (>6s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "Groq LPU",
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
