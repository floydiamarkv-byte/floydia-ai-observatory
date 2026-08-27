"""
Sonda y Verificador Multi-Cuenta de Mistral AI API.
Comprueba endpoints y la salud de todas las cuentas configuradas (C1 a C6).
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import MISTRAL_ACCOUNTS, MISTRAL_API_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_mistral() -> List[Dict[str, Any]]:
    """Comprueba el estado de las cuentas de Mistral AI."""
    results = []
    if not MISTRAL_ACCOUNTS:
        return results

    models_to_test = [
        {"model": "codestral-latest", "context": 256000, "badge": "Codestral (Mistral)", "is_free": False, "in_cost": 0.20, "out_cost": 0.60}
    ]

    check_url = f"{MISTRAL_API_BASE}/chat/completions"

    # 1. Probar modelos con la cuenta principal
    primary_acc = MISTRAL_ACCOUNTS[0]
    headers_primary = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {primary_acc['key']}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="Mistral")

        is_ok = False
        latency = 0.0
        status_msg = "No verificado"
        status_code = 500

        try:
            t0 = time.perf_counter()
            resp = requests.post(
                check_url,
                headers=headers_primary,
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
                key_pool.record_latency(primary_acc["name"], latency)
            elif resp.status_code == 429:
                status_msg = "🟡 429 Rate Limit"
                key_pool.mark_rate_limited(primary_acc["name"], 60)
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 8000.0
            status_msg = "🔴 Timeout (>8s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "Mistral AI",
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

    # 2. Sondear cuentas adicionales de Mistral
    if len(MISTRAL_ACCOUNTS) > 1:
        for acc in MISTRAL_ACCOUNTS[1:]:
            acc_name = acc["name"]
            headers_acc = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {acc['key']}"
            }
            is_acc_ok = False
            acc_latency = 0.0
            acc_status = "No verificado"

            try:
                t0 = time.perf_counter()
                resp = requests.post(
                    check_url,
                    headers=headers_acc,
                    json={
                        "model": "codestral-latest",
                        "messages": [{"role": "user", "content": "1"}],
                        "max_tokens": 2
                    },
                    timeout=6
                )
                acc_latency = round((time.perf_counter() - t0) * 1000, 1)
                is_acc_ok = (resp.status_code == 200)
                acc_status = "🟢 Operativa (200 OK)" if is_acc_ok else f"HTTP {resp.status_code}"
                if is_acc_ok:
                    key_pool.record_latency(acc_name, acc_latency)
            except Exception as e:
                acc_status = f"Error: {e}"

            results.append({
                "provider_name": f"Mistral AI [{acc_name}]",
                "model_identifier": "codestral-latest",
                "canonical_id": "codestral-latest",
                "is_functional": is_acc_ok,
                "status_code": 200 if is_acc_ok else 500,
                "status_message": acc_status,
                "latency_ms": acc_latency,
                "detected_context_window": 256000,
                "supports_tools": True,
                "supports_vision": False,
                "is_free_tier": False,
                "cost_input_m": 0.20,
                "cost_output_m": 0.60
            })

    return results
