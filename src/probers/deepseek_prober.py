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
    """Comprueba el estado de las cuentas de DeepSeek."""
    results = []
    if not DEEPSEEK_ACCOUNTS:
        return results

    models_to_test = [
        {"model": "deepseek-v4-flash", "context": 262144, "in_cost": 0.10, "out_cost": 0.20, "reasoning": False},
        {"model": "deepseek-v4-pro", "context": 262144, "in_cost": 0.20, "out_cost": 0.40, "reasoning": False},
        {"model": "deepseek-chat", "context": 65536, "in_cost": 0.14, "out_cost": 0.28, "reasoning": False},
        {"model": "deepseek-reasoner", "context": 65536, "in_cost": 0.55, "out_cost": 2.19, "reasoning": True}
    ]

    # 1. Probar modelos con la cuenta principal
    primary_acc = DEEPSEEK_ACCOUNTS[0]
    models_url = f"{DEEPSEEK_API_BASE}/models"
    headers_primary = {"Authorization": f"Bearer {primary_acc['key']}"}

    try:
        t0 = time.perf_counter()
        resp = requests.get(models_url, headers=headers_primary, timeout=8)
        latency = round((time.perf_counter() - t0) * 1000, 1)
        is_ok = (resp.status_code == 200)
        status_msg = "🟢 Operativa (200 OK)" if is_ok else f"HTTP {resp.status_code}: {resp.text[:60]}"
        if is_ok:
            key_pool.record_latency(primary_acc["name"], latency)
    except Exception as e:
        is_ok = False
        latency = 0.0
        status_msg = f"Error de red: {e}"

    for item in models_to_test:
        raw_name = item["model"]
        can_id, _ = normalizer.resolve(raw_name, provider_hint="DeepSeek")
        results.append({
            "provider_name": "DeepSeek",
            "model_identifier": raw_name,
            "canonical_id": can_id,
            "is_functional": is_ok,
            "status_code": 200 if is_ok else 500,
            "status_message": status_msg,
            "latency_ms": latency,
            "detected_context_window": item["context"],
            "supports_tools": not item["reasoning"],
            "supports_vision": False,
            "is_free_tier": False,
            "cost_input_m": item["in_cost"],
            "cost_output_m": item["out_cost"]
        })

    # 2. Sondear cuentas adicionales de DeepSeek para verificar disponibilidad
    if len(DEEPSEEK_ACCOUNTS) > 1:
        for acc in DEEPSEEK_ACCOUNTS[1:]:
            acc_name = acc["name"]
            headers_acc = {"Authorization": f"Bearer {acc['key']}"}
            is_acc_ok = False
            acc_latency = 0.0
            acc_status = "No verificado"
            
            try:
                t0 = time.perf_counter()
                resp = requests.get(models_url, headers=headers_acc, timeout=6)
                acc_latency = round((time.perf_counter() - t0) * 1000, 1)
                is_acc_ok = (resp.status_code == 200)
                acc_status = "🟢 Operativa (200 OK)" if is_acc_ok else f"HTTP {resp.status_code}"
                if is_acc_ok:
                    key_pool.record_latency(acc_name, acc_latency)
            except Exception as e:
                acc_status = f"Error: {e}"

            results.append({
                "provider_name": f"DeepSeek [{acc_name}]",
                "model_identifier": "deepseek-chat",
                "canonical_id": "deepseek-chat",
                "is_functional": is_acc_ok,
                "status_code": 200 if is_acc_ok else 500,
                "status_message": acc_status,
                "latency_ms": acc_latency,
                "detected_context_window": 65536,
                "supports_tools": True,
                "supports_vision": False,
                "is_free_tier": False,
                "cost_input_m": 0.14,
                "cost_output_m": 0.28
            })

    return results
