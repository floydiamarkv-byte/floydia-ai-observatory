"""
Sonda y Verificador Multi-Cuenta de Zhipu AI / Z.AI (GLM API).
Comprueba el estado de las cuentas C1 a C6 y los modelos GLM (5.3, 5.2, 5-turbo, 5.3-flash).
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import Z_AI_ACCOUNTS, Z_AI_API_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_z_ai() -> List[Dict[str, Any]]:
    """Comprueba el estado de las cuentas y modelos de Zhipu AI (GLM)."""
    results = []
    if not Z_AI_ACCOUNTS:
        return results

    models_to_test = [
        {"model": "glm-5.3", "context": 262144, "badge": "GLM 5.3 (Frontier)", "is_free": False, "in_cost": 0.15, "out_cost": 0.30},
        {"model": "glm-5.2", "context": 262144, "badge": "GLM 5.2 (Workhorse)", "is_free": False, "in_cost": 0.10, "out_cost": 0.20},
        {"model": "glm-5-turbo", "context": 131072, "badge": "GLM 5 Turbo (Speed)", "is_free": False, "in_cost": 0.05, "out_cost": 0.10},
        {"model": "glm-5.3-flash", "context": 131072, "badge": "GLM 5.3 Flash (Instant)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0}
    ]

    primary_acc = Z_AI_ACCOUNTS[0]
    check_url = f"{Z_AI_API_BASE}/chat/completions"
    headers_primary = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {primary_acc['key']}"
    }

    # 1. Probar modelos con la cuenta principal
    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="Zhipu AI")

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
                timeout=4.0
            )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            status_code = resp.status_code
            if resp.status_code == 200:
                is_ok = True
                status_msg = "🟢 Operativa (200 OK)"
                key_pool.record_latency(primary_acc["name"], latency)
            elif resp.status_code == 429:
                status_msg = "🟡 429 Rate Limit (Cuota llena)"
                key_pool.mark_rate_limited(primary_acc["name"], cooldown_seconds=60)
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 4000.0
            status_msg = "🔴 Timeout (>4s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "Z.AI (Zhipu)",
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

    # 2. Sondear cuentas secundarias del pool (C2..CN)
    if len(Z_AI_ACCOUNTS) > 1:
        for acc in Z_AI_ACCOUNTS[1:]:
            acc_name = acc["name"]
            headers_acc = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {acc['key']}"
            }
            is_acc_ok = False
            acc_latency = 0.0
            acc_status = "No verificado"
            acc_code = 500

            try:
                t0 = time.perf_counter()
                resp = requests.post(
                    check_url,
                    headers=headers_acc,
                    json={
                        "model": "glm-5.3-flash",
                        "messages": [{"role": "user", "content": "1"}],
                        "max_tokens": 2
                    },
                    timeout=3.0
                )
                acc_latency = round((time.perf_counter() - t0) * 1000, 1)
                acc_code = resp.status_code
                if resp.status_code == 200:
                    is_acc_ok = True
                    acc_status = "🟢 Operativa (200 OK)"
                    key_pool.record_latency(acc_name, acc_latency)
                elif resp.status_code == 429:
                    acc_status = "🟡 429 Rate Limit"
                    key_pool.mark_rate_limited(acc_name, cooldown_seconds=60)
                else:
                    acc_status = f"HTTP {resp.status_code}"
            except Exception as e:
                acc_status = f"Error: {e}"

            results.append({
                "provider_name": f"Z.AI [{acc_name}]",
                "model_identifier": "glm-5.3-flash",
                "canonical_id": "glm-5.3-flash",
                "is_functional": is_acc_ok,
                "status_code": acc_code,
                "status_message": acc_status,
                "latency_ms": acc_latency,
                "detected_context_window": 131072,
                "supports_tools": True,
                "supports_vision": False,
                "supports_reasoning": False,
                "is_free_tier": True,
                "cost_input_m": 0.0,
                "cost_output_m": 0.0
            })

    return results
