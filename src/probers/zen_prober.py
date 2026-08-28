"""
Sonda y Verificador Multi-Cuenta de OpenCode Zen (OpenCode Gateway).
Evalúa la salud de las cuentas C1 a C7 y el estado de los modelos de OpenCode Zen
con llamadas reales de 1 token (latencia y funcionalidad medidas en vivo).
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import ZEN_ACCOUNTS, ZEN_API_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_opencode_zen() -> List[Dict[str, Any]]:
    """Comprueba el estado de las cuentas y modelos de OpenCode Zen con llamadas reales."""
    results = []
    if not ZEN_ACCOUNTS:
        return results

    models_to_test = [
        {"model": "opencode/nemotron-3-ultra-free", "context": 262144, "badge": "Nemotron 3 Ultra 550B (Zen Free)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "opencode/nemotron-3.5-lightning-free", "context": 262144, "badge": "Nemotron 3.5 Lightning (Zen Free)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "opencode/mimo-v2.5-free", "context": 262144, "badge": "MiMo V2.5 (Zen Free)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "opencode/hy3-free", "context": 262144, "badge": "Hy3 (Zen Free)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "opencode/big-pickle", "context": 131072, "badge": "Big Pickle (Zen)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "opencode/muse-spark-1.2-contributor-free", "context": 262144, "badge": "Muse Spark 1.2 (Zen Free)", "is_free": True, "in_cost": 0.0, "out_cost": 0.0}
    ]

    check_url = f"{ZEN_API_BASE}/chat/completions"

    # 1. Probar modelos de OpenCode Zen en la cuenta principal con llamada real
    primary_acc = ZEN_ACCOUNTS[0]
    headers_primary = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {primary_acc['key']}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="OpenCode")

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
                timeout=6.0
            )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            status_code = resp.status_code
            if resp.status_code == 200:
                is_ok = True
                status_msg = "🟢 Operativa (200 OK)"
                key_pool.record_latency(primary_acc["name"], latency)
            elif resp.status_code == 429:
                status_msg = "🟡 429 Rate Limit (Cuota temporalmente llena)"
                key_pool.mark_rate_limited(primary_acc["name"], cooldown_seconds=60)
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 8000.0
            status_msg = "🔴 Timeout (>6s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "OpenCode Zen",
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

    # 2. Sondear cada cuenta adicional (C2 a CN) con llamada real de 1 token
    if len(ZEN_ACCOUNTS) > 1:
        for acc in ZEN_ACCOUNTS[1:]:
            acc_name = acc["name"]
            headers_acc = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {acc['key']}"
            }
            is_ok = False
            latency = 0.0
            status_msg = "No verificado"
            status_code = 500

            try:
                t0 = time.perf_counter()
                resp = requests.post(
                    check_url,
                    headers=headers_acc,
                    json={
                        "model": "opencode/nemotron-3.5-lightning-free",
                        "messages": [{"role": "user", "content": "1"}],
                        "max_tokens": 2
                    },
                    timeout=6.0
                )
                latency = round((time.perf_counter() - t0) * 1000, 1)
                status_code = resp.status_code
                if resp.status_code == 200:
                    is_ok = True
                    status_msg = "🟢 Operativa (200 OK)"
                    key_pool.record_latency(acc_name, latency)
                elif resp.status_code == 429:
                    status_msg = "🟡 429 Rate Limit (Cuota temporalmente llena)"
                    key_pool.mark_rate_limited(acc_name, cooldown_seconds=60)
                else:
                    status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
            except requests.exceptions.Timeout:
                status_code = 408
                latency = 8000.0
                status_msg = "🔴 Timeout (>6s)"
            except Exception as e:
                status_msg = f"Error de red: {e}"

            results.append({
                "provider_name": f"OpenCode Zen [{acc_name}]",
                "model_identifier": "opencode/nemotron-3.5-lightning-free",
                "canonical_id": "opencode-nemotron-3.5-lightning-free",
                "is_functional": is_ok,
                "status_code": status_code,
                "status_message": status_msg,
                "latency_ms": latency,
                "detected_context_window": 262144,
                "supports_tools": True,
                "supports_vision": False,
                "is_free_tier": True,
                "cost_input_m": 0.0,
                "cost_output_m": 0.0
            })

    return results
