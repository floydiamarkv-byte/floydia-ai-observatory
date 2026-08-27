"""
Sonda y Verificador de OpenRouter API y Modelos Activos Completos.
Recupera todos los modelos activos de OpenRouter filtrando modelos obsoletos o legacy.
"""

import time
from typing import Dict, Any, List
import requests
from config.settings import OPENROUTER_API_KEY, OPENROUTER_API_BASE
from src.core.normalizer import normalizer


LEGACY_KEYWORDS = ["deprecated", "legacy", "old", "0301", "0613", "instruct-v0.1", "chatglm", "dall-e", "whisper", "davinci"]


def probe_openrouter() -> List[Dict[str, Any]]:
    """Comprueba la API de OpenRouter y recupera el catálogo completo de modelos activos."""
    results = []
    if not OPENROUTER_API_KEY:
        return results

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://floydia.com",
        "X-Title": "FloydIA Observatory"
    }

    # 1. Comprobación de autenticación
    auth_check_url = f"{OPENROUTER_API_BASE}/auth/key"
    try:
        t0 = time.perf_counter()
        resp = requests.get(auth_check_url, headers=headers, timeout=10)
        latency = round((time.perf_counter() - t0) * 1000, 1)
        is_ok = (resp.status_code == 200)
        status_msg = "🟢 Operativa" if is_ok else f"HTTP {resp.status_code}"
    except Exception as e:
        is_ok = False
        latency = 0.0
        status_msg = f"Error de red: {e}"

    # 2. Descubrimiento de modelos completos desde /api/v1/models
    models_url = f"{OPENROUTER_API_BASE}/models"
    discovered_models = []
    try:
        m_resp = requests.get(models_url, headers=headers, timeout=12)
        if m_resp.status_code == 200:
            m_data = m_resp.json().get("data", [])
            for item in m_data:
                m_id = item.get("id", "")
                m_name = item.get("name", m_id)
                # Filtrar modelos obsoletos / legacy
                if any(leg in m_id.lower() for leg in LEGACY_KEYWORDS):
                    continue
                
                pricing = item.get("pricing", {})
                p_in = float(pricing.get("prompt", 0.0)) * 1_000_000
                p_out = float(pricing.get("completion", 0.0)) * 1_000_000
                is_free = (p_in == 0.0 and p_out == 0.0) or ":free" in m_id

                discovered_models.append({
                    "id": m_id,
                    "name": m_name,
                    "context": item.get("context_length", 128000),
                    "is_free": is_free,
                    "in_cost": round(p_in, 4),
                    "out_cost": round(p_out, 4)
                })
    except Exception as e:
        print(f"⚠️ [OpenRouter Prober] Error listando modelos: {e}")

    # Si por alguna razón la lista falla, tener los modelos principales de respaldo
    if not discovered_models:
        discovered_models = [
            {"id": "qwen/qwen-2.5-coder-32b-instruct:free", "name": "Qwen 2.5 Coder 32B (Free)", "context": 131072, "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)", "context": 131072, "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
            {"id": "deepseek/deepseek-r1:free", "name": "DeepSeek R1 (Free)", "context": 65536, "is_free": True, "in_cost": 0.0, "out_cost": 0.0},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek V3", "context": 65536, "is_free": False, "in_cost": 0.14, "out_cost": 0.28},
            {"id": "anthropic/claude-3.7-sonnet", "name": "Claude 3.7 Sonnet", "context": 200000, "is_free": False, "in_cost": 3.0, "out_cost": 15.0},
            {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash", "context": 1048576, "is_free": False, "in_cost": 0.075, "out_cost": 0.30},
            {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro", "context": 2097152, "is_free": False, "in_cost": 1.25, "out_cost": 5.00}
        ]

    for item in discovered_models:
        can_id, _ = normalizer.resolve(item["id"], provider_hint="OpenRouter")
        results.append({
            "provider_name": "OpenRouter",
            "model_identifier": item["id"],
            "canonical_id": can_id,
            "is_functional": is_ok,
            "status_code": 200 if is_ok else 500,
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
