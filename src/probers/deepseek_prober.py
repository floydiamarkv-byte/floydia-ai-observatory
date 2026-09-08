"""
Sonda y Verificador Multi-Cuenta de DeepSeek API.
Comprueba endpoints y la salud de todas las cuentas configuradas (C1 a C7).
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import DEEPSEEK_ACCOUNTS, DEEPSEEK_API_BASE
from src.core.normalizer import normalizer
from src.core.key_pool import key_pool


def probe_deepseek() -> List[Dict[str, Any]]:
    """Comprueba el estado y balance de todas las cuentas de DeepSeek."""
    results = []
    if not DEEPSEEK_ACCOUNTS:
        return results

    models_to_test = [
        {"model": "deepseek-chat", "context": 131072, "in_cost": 0.14, "out_cost": 0.28, "reasoning": False},
        {"model": "deepseek-reasoner", "context": 65536, "in_cost": 0.55, "out_cost": 2.19, "reasoning": True},
        {"model": "deepseek-v4-flash", "context": 262144, "in_cost": 0.10, "out_cost": 0.20, "reasoning": False},
        {"model": "deepseek-v4-pro", "context": 262144, "in_cost": 0.20, "out_cost": 0.40, "reasoning": False}
    ]

    chat_url = f"{DEEPSEEK_API_BASE}/chat/completions"
    
    # 1. Auditar cada cuenta con una solicitud ligera de 1 token para verificar saldo real
    account_statuses = {}
    working_account = None

    for acc in DEEPSEEK_ACCOUNTS:
        acc_name = acc["name"]
        headers = {"Authorization": f"Bearer {acc['key']}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}
        
        try:
            t0 = time.perf_counter()
            resp = requests.post(chat_url, headers=headers, json=payload, timeout=6)
            lat = round((time.perf_counter() - t0) * 1000, 1)
            
            if resp.status_code == 200:
                is_ok = True
                status_msg = "🟢 Operativa (200 OK)"
                key_pool.record_latency(acc_name, lat)
                if working_account is None:
                    working_account = (acc, lat, status_msg)
            elif resp.status_code == 402:
                is_ok = False
                status_msg = "⚠️ Sin Saldo (HTTP 402)"
            elif resp.status_code in (401, 403):
                is_ok = False
                status_msg = f"❌ Error Autenticación ({resp.status_code})"
                key_pool.mark_auth_failed(acc_name)
            else:
                is_ok = False
                status_msg = f"HTTP {resp.status_code}: {resp.text[:50]}"
        except Exception as e:
            is_ok = False
            lat = 0.0
            status_msg = f"Error de red: {e}"

        account_statuses[acc_name] = {
            "is_functional": is_ok,
            "latency_ms": lat,
            "status_message": status_msg
        }

        # Registrar entrada para la cuenta específica
        results.append({
            "provider_name": f"DeepSeek [{acc_name}]",
            "model_identifier": "deepseek-chat",
            "canonical_id": "deepseek-chat",
            "is_functional": is_ok,
            "status_code": 200 if is_ok else (402 if "402" in status_msg else 500),
            "status_message": status_msg,
            "latency_ms": lat,
            "detected_context_window": 131072,
            "supports_tools": True,
            "supports_vision": False,
            "is_free_tier": False,
            "cost_input_m": 0.14,
            "cost_output_m": 0.28
        })

    # 2. Registrar los modelos del catálogo con la cuenta activa encontrada
    if working_account is not None:
        active_acc, active_lat, active_msg = working_account
        cat_functional = True
        cat_latency = active_lat
        cat_msg = active_msg
    else:
        first_acc_name = DEEPSEEK_ACCOUNTS[0]["name"]
        cat_functional = False
        cat_latency = 0.0
        cat_msg = account_statuses.get(first_acc_name, {}).get("status_message", "⚠️ Sin saldo en el pool")

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="DeepSeek")
        results.append({
            "provider_name": "DeepSeek Direct",
            "model_identifier": raw_name,
            "canonical_id": can_id,
            "is_functional": cat_functional,
            "status_code": 200 if cat_functional else 402,
            "status_message": cat_msg,
            "latency_ms": cat_latency,
            "detected_context_window": item["context"],
            "supports_tools": not item["reasoning"],
            "supports_vision": False,
            "is_free_tier": False,
            "cost_input_m": item["in_cost"],
            "cost_output_m": item["out_cost"]
        })

    return results
