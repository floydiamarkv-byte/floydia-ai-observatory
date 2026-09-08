"""
Sonda y Verificador Multi-Cuenta de NVIDIA NIM API.
Comprueba endpoints de DeepSeek V4, Nemotron 3 Nano, Kimi K3 en integrate.api.nvidia.com para todas las cuentas.
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import NVIDIA_ACCOUNTS, NVIDIA_API_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_nvidia_nim() -> List[Dict[str, Any]]:
    """Comprueba el estado de todas las cuentas y modelos de NVIDIA NIM."""
    results = []
    if not NVIDIA_ACCOUNTS:
        return results

    models_to_test = [
        {"model": "moonshotai/kimi-k3", "context": 262144, "badge": "Kimi K3 (NIM)", "is_free": False, "in_cost": 0.15, "out_cost": 0.30},
        {"model": "deepseek-ai/deepseek-v4-flash-0731", "context": 262144, "badge": "DeepSeek V4 (NIM)", "is_free": False, "in_cost": 0.10, "out_cost": 0.20},
        {"model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "context": 256000, "badge": "Nemotron 3 Nano (NIM)", "is_free": False, "in_cost": 0.05, "out_cost": 0.10}
    ]

    check_url = f"{NVIDIA_API_BASE}/chat/completions"
    
    # 1. Probar cada cuenta de NVIDIA con un ping ligero a Kimi K3
    working_account = None

    for acc in NVIDIA_ACCOUNTS:
        acc_name = acc["name"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {acc['key']}"
        }
        
        is_acc_ok = False
        acc_lat = 0.0
        acc_status = "No verificado"
        
        try:
            t0 = time.perf_counter()
            resp = requests.post(
                check_url,
                headers=headers,
                json={"model": "moonshotai/kimi-k3", "messages": [{"role": "user", "content": "1"}], "max_tokens": 1},
                timeout=6
            )
            acc_lat = round((time.perf_counter() - t0) * 1000, 1)
            
            if resp.status_code == 200:
                is_acc_ok = True
                acc_status = "🟢 Operativa (200 OK)"
                key_pool.record_latency(acc_name, acc_lat)
                if working_account is None:
                    working_account = (acc, acc_lat)
            elif resp.status_code == 429:
                acc_status = "🟡 Rate Limit (429)"
                key_pool.mark_rate_limited(acc_name, 60.0)
            elif resp.status_code in (401, 403):
                acc_status = f"❌ Error Autenticación ({resp.status_code})"
                key_pool.mark_auth_failed(acc_name)
            elif resp.status_code == 402 or "limit" in resp.text.lower():
                acc_status = "⚠️ Cuota Agotada"
            else:
                acc_status = f"HTTP {resp.status_code}"
        except requests.exceptions.Timeout:
            acc_status = "🔴 Timeout (>6s)"
        except Exception as e:
            acc_status = f"Error: {e}"

        results.append({
            "provider_name": f"NVIDIA NIM [{acc_name}]",
            "model_identifier": "moonshotai/kimi-k3",
            "canonical_id": "moonshotai/kimi-k3",
            "is_functional": is_acc_ok,
            "status_code": 200 if is_acc_ok else 500,
            "status_message": acc_status,
            "latency_ms": acc_lat,
            "detected_context_window": 262144,
            "supports_tools": True,
            "supports_vision": False,
            "is_free_tier": False,
            "cost_input_m": 0.15,
            "cost_output_m": 0.30
        })

    # 2. Probar los modelos del catálogo con la cuenta activa
    active_key = working_account[0]["key"] if working_account else NVIDIA_ACCOUNTS[0]["key"]
    active_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {active_key}"}

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
                headers=active_headers,
                json={"model": raw_name, "messages": [{"role": "user", "content": "1"}], "max_tokens": 1},
                timeout=6
            )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            status_code = resp.status_code
            if resp.status_code == 200:
                is_ok = True
                status_msg = "🟢 Operativa (200 OK)"
            else:
                status_msg = f"HTTP {resp.status_code}: {resp.text[:60]}"
        except requests.exceptions.Timeout:
            status_code = 408
            latency = 6000.0
            status_msg = "🔴 Timeout (>6s)"
        except Exception as e:
            status_msg = f"Error: {e}"

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

