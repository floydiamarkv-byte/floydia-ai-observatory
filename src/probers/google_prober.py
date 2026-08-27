"""
Sonda y Verificador Multi-Cuenta de Google AI Studio (OpenAI-compatible endpoint).
Evalúa todas las cuentas configuradas (C1 a C6) para auditoría de salud y rotación.
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import GOOGLE_ACCOUNTS, GOOGLE_OPENAI_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_google_ai_studio() -> List[Dict[str, Any]]:
    """Prueba todas las cuentas de Google AI Studio configuradas y sus modelos."""
    results = []
    if not GOOGLE_ACCOUNTS:
        return results

    models_to_test = [
        {"model": "gemini-3.6-flash", "context": 1048576, "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "gemini-3.5-flash", "context": 1048576, "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
        {"model": "gemini-3.7-flash", "context": 1048576, "is_free": False, "in_cost": 0.075, "out_cost": 0.30},
        {"model": "gemma-4-31b-it", "context": 262144, "is_free": True, "in_cost": 0.0, "out_cost": 0.0}
    ]

    check_url = f"{GOOGLE_OPENAI_BASE}/chat/completions"

    # 1. Evaluar la flota completa de modelos en la cuenta principal
    primary_acc = GOOGLE_ACCOUNTS[0]
    headers_primary = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {primary_acc['key']}"
    }

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="Google")
        
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
                status_msg = "🟡 429 Rate Limit (Cuota temporalmente llena)"
                key_pool.mark_rate_limited(primary_acc["name"], cooldown_seconds=60)
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 8000.0
            status_msg = "🔴 Timeout (>8s)"
        except Exception as e:
            status_msg = f"Error de red: {e}"

        results.append({
            "provider_name": "Google AI Studio",
            "model_identifier": raw_name,
            "canonical_id": can_id,
            "is_functional": is_ok,
            "status_code": status_code,
            "status_message": status_msg,
            "latency_ms": latency,
            "detected_context_window": item["context"],
            "supports_tools": True,
            "supports_vision": True,
            "is_free_tier": item["is_free"],
            "cost_input_m": item["in_cost"],
            "cost_output_m": item["out_cost"]
        })

    # 2. Sondear cada cuenta adicional (C2 a CN) para verificar la salud del pool
    if len(GOOGLE_ACCOUNTS) > 1:
        for acc in GOOGLE_ACCOUNTS[1:]:
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
                        "model": "gemini-3.6-flash",
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
                    key_pool.record_latency(acc_name, latency)
                elif resp.status_code == 429:
                    status_msg = "🟡 429 Rate Limit (Cuota temporalmente llena)"
                    key_pool.mark_rate_limited(acc_name, cooldown_seconds=60)
                else:
                    status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
            except requests.exceptions.Timeout:
                status_code = 408
                latency = 8000.0
                status_msg = "🔴 Timeout (>8s)"
            except Exception as e:
                status_msg = f"Error de red: {e}"

            results.append({
                "provider_name": f"Google AI Studio [{acc_name}]",
                "model_identifier": "gemini-3.6-flash",
                "canonical_id": "gemini-3.6-flash",
                "is_functional": is_ok,
                "status_code": status_code,
                "status_message": status_msg,
                "latency_ms": latency,
                "detected_context_window": 1048576,
                "supports_tools": True,
                "supports_vision": True,
                "is_free_tier": True,
                "cost_input_m": 0.0,
                "cost_output_m": 0.0
            })

    return results
