"""
Escáner y Descubridor de Credenciales Locales de IA.
Inspecciona variables de entorno y archivos seguros (.secrets/antigravity.env / OpenCode)
sin exponer valores en texto plano (Fix V-10).
"""

import os
from typing import Dict, Any, List
from config.settings import GEMINI_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, HF_TOKEN


def scan_configured_providers() -> Dict[str, Dict[str, Any]]:
    """
    Identifica qué proveedores de IA están configurados y disponibles en el entorno.
    Retorna un diccionario de proveedores con su estado y clave enmascarada (nunca en claro).
    """
    providers = {}

    # 1. Google AI Studio
    has_google = bool(GEMINI_API_KEY)
    providers["Google_AI_Studio"] = {
        "configured": has_google,
        "key_preview": f"...{GEMINI_API_KEY[-4:]}" if has_google else None,
        "default_models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]
    }

    # 2. OpenRouter
    has_openrouter = bool(OPENROUTER_API_KEY)
    providers["OpenRouter"] = {
        "configured": has_openrouter,
        "key_preview": f"...{OPENROUTER_API_KEY[-4:]}" if has_openrouter else None,
        "default_models": ["qwen/qwen-2.5-coder-32b-instruct:free", "meta-llama/llama-3.3-70b-instruct:free", "deepseek/deepseek-r1:free"]
    }

    # 3. DeepSeek
    has_deepseek = bool(DEEPSEEK_API_KEY)
    providers["DeepSeek"] = {
        "configured": has_deepseek,
        "key_preview": f"...{DEEPSEEK_API_KEY[-4:]}" if has_deepseek else None,
        "default_models": ["deepseek-chat", "deepseek-reasoner"]
    }

    # 4. Hermes / OpenAI-compatibles
    hermes_url = os.getenv("S17_VPS_HERMES_URL") or os.getenv("HERMES_API_URL")
    providers["Hermes_Local"] = {
        "configured": bool(hermes_url),
        "base_url": hermes_url,
        "default_models": ["nous-hermes-3-70b"]
    }

    return providers
