"""
src/probers/deep_probe_scanner.py — Escáner Profundo y Diagnóstico de Modelos IA.
Ejecuta consultas cortas de prueba ("¡hola di si!") con pool concurrente acotado,
timeouts estrictos de 5s y clasificación determinista en 6 estados:
  1. RESPUESTA_OK (🟢 Funciona 100%)
  2. SIN_SALDO (💳 402 / Créditos agotados)
  3. FREE_TIER_AGOTADO (⏳ 429 / Rate limit)
  4. NO_AUTORIZADO (🔒 401/403 / Clave inválida)
  5. SIN_RESPUESTA (⏱️ Timeout / Red / Body vacío)
  6. ERROR (⚠️ 5xx / 404 / Error de esquema)

Persiste telemetría y provee modelos filtrados para inyección en OpenCode, Hermes y DSH.
"""

import time
import json
import asyncio
from typing import Dict, Any, List, Tuple, Optional
import urllib.request
import urllib.error

from config.settings import (
    GOOGLE_ACCOUNTS, GOOGLE_OPENAI_BASE,
    DEEPSEEK_ACCOUNTS, DEEPSEEK_API_BASE,
    OPENROUTER_ACCOUNTS, OPENROUTER_API_BASE,
    NVIDIA_ACCOUNTS, NVIDIA_API_BASE,
    DASHSCOPE_ACCOUNTS, DASHSCOPE_API_BASE,
    MISTRAL_ACCOUNTS, MISTRAL_API_BASE,
    GROQ_ACCOUNTS, GROQ_API_BASE,
    Z_AI_ACCOUNTS, Z_AI_API_BASE,
    ZEN_ACCOUNTS, ZEN_API_BASE,
    GROKIFIED_ACCOUNTS, GROKIFIED_API_BASE,
    GITHUB_TOKEN, GITHUB_MODELS_BASE,
    FIREWORKS_API_KEY, FIREWORKS_API_BASE,
    resolve_account_email
)
from src.core.db import get_db_connection, scrub_secrets

DEFAULT_PROBE_PROMPT = "¡hola di si!"
MAX_CONCURRENT_SCANS = 12
DEFAULT_TIMEOUT_SECS = 5.0

# 6 Estados Canónicos
STATUS_OK = "RESPUESTA_OK"
STATUS_NO_BALANCE = "SIN_SALDO"
STATUS_FREE_TIER_AGOTADO = "FREE_TIER_AGOTADO"
STATUS_FREE_TIER_EXHAUSTED = STATUS_FREE_TIER_AGOTADO
STATUS_UNAUTHORIZED = "NO_AUTORIZADO"
STATUS_NO_RESPONSE = "SIN_RESPUESTA"
STATUS_ERROR = "ERROR"

STATUS_LABELS = {
    STATUS_OK: "🟢 Respuesta OK (100% Funcional)",
    STATUS_NO_BALANCE: "💳 Sin Saldo / Cuota Agotada",
    STATUS_FREE_TIER_EXHAUSTED: "⏳ Free Tier Agotado / 429 Rate Limit",
    STATUS_UNAUTHORIZED: "🔒 No Autorizado (401/403)",
    STATUS_NO_RESPONSE: "⏱️ Sin Respuesta / Timeout",
    STATUS_ERROR: "⚠️ Error de Modelo / Gateway",
}


def classify_response(
    status_code: int,
    response_body: str,
    error_msg: str,
    latency_ms: float
) -> Tuple[str, str]:
    """
    Clasifica de forma determinista el resultado de la sonda en uno de los 6 estados canónicos.
    """
    body_low = (response_body or "").lower()
    err_low = (error_msg or "").lower()
    combined_text = f"{body_low} {err_low}"

    # 1. Éxito 200 OK
    if status_code == 200:
        if not response_body or not response_body.strip():
            return STATUS_NO_RESPONSE, "⏱️ Sin Respuesta (Cuerpo vacío)"
        try:
            data = json.loads(response_body)
            choices = data.get("choices", [])
            content = ""
            if choices and isinstance(choices, list):
                msg = choices[0].get("message", {})
                content = msg.get("content") or choices[0].get("text") or ""
            elif "candidates" in data:
                cands = data.get("candidates", [])
                if cands:
                    content = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if content and len(str(content).strip()) > 0:
                snippet = str(content).strip().replace("\n", " ")[:60]
                return STATUS_OK, f"🟢 OK: '{snippet}'"
            return STATUS_NO_RESPONSE, "⏱️ Sin Respuesta (Contenido vacío en JSON)"
        except Exception:
            snippet = response_body.strip().replace("\n", " ")[:40]
            return STATUS_OK, f"🟢 OK (200 Texto): '{snippet}'"

    # 2. Sin Saldo (402 o keywords específicas)
    if status_code == 402:
        return STATUS_NO_BALANCE, "💳 Sin Saldo (HTTP 402 Payment Required)"

    no_balance_keywords = [
        "insufficient_quota", "insufficient balance", "out of credits",
        "payment required", "credit limit", "billing not active",
        "quota exceeded", "exceeded your current quota", "zero balance",
        "no available balance", "run out of credits"
    ]
    if any(k in combined_text for k in no_balance_keywords):
        return STATUS_NO_BALANCE, f"💳 Sin Saldo: {error_msg[:60]}"

    # 3. Free Tier Agotado / 429 Rate Limit
    if status_code == 429 or any(k in combined_text for k in ["rate limit", "too many requests", "resource_exhausted", "quota_exceeded", "daily limit", "tpm limit", "rpm limit"]):
        return STATUS_FREE_TIER_AGOTADO, f"⏳ Free Tier Agotado (429): {error_msg[:60]}"

    # 4. No Autorizado (401, 403 o error de token)
    if status_code in (401, 403) or any(k in combined_text for k in ["unauthorized", "invalid api key", "invalid_api_key", "forbidden", "authentication failed", "permission denied"]):
        return STATUS_UNAUTHORIZED, f"🔒 No Autorizado ({status_code}): {error_msg[:60]}"

    # 5. Sin Respuesta / Timeout / Network
    if status_code in (408, 0) or any(k in combined_text for k in ["timeout", "timed out", "connection refused", "connection reset", "broken pipe", "no route to host", "network is unreachable", "nodename nor servname provided"]):
        return STATUS_NO_RESPONSE, f"⏱️ Sin Respuesta / Timeout ({error_msg[:60]})"

    # 6. Error General
    return STATUS_ERROR, f"⚠️ Error HTTP {status_code}: {error_msg[:60]}"


def build_probe_target_for_model(model_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Construye dinámicamente el objetivo de sonda (base_url, api_key, headers)
    para un modelo dado a partir de las credenciales configuradas en el entorno.
    """
    m_id = model_item.get("id") or model_item.get("model_id") or ""
    if not m_id:
        return None
    
    prov = (model_item.get("provider") or model_item.get("provider_id") or model_item.get("provider_name") or "").lower()
    c_name = model_item.get("canonical_name") or m_id
    ctx = model_item.get("context_window", 128000)
    is_free = bool(model_item.get("is_free_tier", False) or ":free" in m_id or "flash" in m_id or "gemma" in m_id)
    supports_tools = bool(model_item.get("supports_tools", True))
    supports_vision = bool(model_item.get("supports_vision", False) or "vision" in m_id or "vl" in m_id or "gemini" in m_id or "4o" in m_id)

    # 1. Google
    if "google" in prov or ("gemini" in m_id and "/" not in m_id) or ("gemma" in m_id and "/" not in m_id):
        acc = GOOGLE_ACCOUNTS[0] if GOOGLE_ACCOUNTS else {"name": "GOOGLE_AI_KEY", "key": ""}
        acc_name = acc["name"]
        return {
            "provider_id": "google",
            "provider_display": f"Google AI Studio [{acc_name}]",
            "account_key": acc_name,
            "account_email": resolve_account_email(acc_name),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": GOOGLE_OPENAI_BASE,
            "api_key": acc["key"],
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 2. DeepSeek
    if "deepseek" in prov and ("deepseek-chat" in m_id or "deepseek-reasoner" in m_id) and "/" not in m_id:
        acc = DEEPSEEK_ACCOUNTS[0] if DEEPSEEK_ACCOUNTS else {"name": "DEEPSEEK_API_KEY", "key": ""}
        acc_name = acc["name"]
        return {
            "provider_id": "deepseek",
            "provider_display": f"DeepSeek Direct [{acc_name}]",
            "account_key": acc_name,
            "account_email": resolve_account_email(acc_name),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": f"{DEEPSEEK_API_BASE.rstrip('/')}/v1",
            "api_key": acc["key"],
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 3. Groq
    if ("groq" in prov or (prov == "groq")) and ("/" not in m_id and ("llama-3" in m_id or "mixtral" in m_id or "gemma" in m_id) and GROQ_ACCOUNTS):
        acc = GROQ_ACCOUNTS[0] if GROQ_ACCOUNTS else {"name": "GROQ_API_KEY", "key": ""}
        acc_name = acc["name"]
        return {
            "provider_id": "groq",
            "provider_display": f"Groq LPU [{acc_name}]",
            "account_key": acc_name,
            "account_email": resolve_account_email(acc_name),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": GROQ_API_BASE,
            "api_key": acc["key"],
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 4. Mistral
    if "mistral" in prov and ("codestral" in m_id or "mistral" in m_id or "ministral" in m_id) and "/" not in m_id:
        acc = MISTRAL_ACCOUNTS[0] if MISTRAL_ACCOUNTS else {"name": "MISTRAL_API_KEY", "key": ""}
        acc_name = acc["name"]
        return {
            "provider_id": "mistral",
            "provider_display": f"Mistral AI [{acc_name}]",
            "account_key": acc_name,
            "account_email": resolve_account_email(acc_name),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": MISTRAL_API_BASE,
            "api_key": acc["key"],
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 5. DashScope (Alibaba)
    if ("dashscope" in prov or "alibaba" in prov or "qwen" in prov) and "/" not in m_id:
        acc = DASHSCOPE_ACCOUNTS[0] if DASHSCOPE_ACCOUNTS else {"name": "DASHSCOPE_API_KEY", "key": ""}
        acc_name = acc["name"]
        return {
            "provider_id": "dashscope",
            "provider_display": f"Alibaba DashScope [{acc_name}]",
            "account_key": acc_name,
            "account_email": resolve_account_email(acc_name),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": DASHSCOPE_API_BASE,
            "api_key": acc["key"],
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 6. NVIDIA NIM
    if "nvidia" in prov and NVIDIA_ACCOUNTS and "/" not in m_id:
        acc = NVIDIA_ACCOUNTS[0]
        acc_name = acc["name"]
        return {
            "provider_id": "nvidia",
            "provider_display": f"NVIDIA NIM [{acc_name}]",
            "account_key": acc_name,
            "account_email": resolve_account_email(acc_name),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": NVIDIA_API_BASE,
            "api_key": acc["key"],
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 7. Z.AI
    if ("z_ai" in prov or "zhipu" in prov or "glm" in m_id) and "/" not in m_id:
        acc = Z_AI_ACCOUNTS[0] if Z_AI_ACCOUNTS else {"name": "Z_AI_API_KEY", "key": ""}
        acc_name = acc["name"]
        return {
            "provider_id": "z_ai",
            "provider_display": f"Z.AI [{acc_name}]",
            "account_key": acc_name,
            "account_email": resolve_account_email(acc_name),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": Z_AI_API_BASE,
            "api_key": acc["key"],
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 8. GitHub Models
    if "github" in prov and GITHUB_TOKEN:
        return {
            "provider_id": "github",
            "provider_display": "GitHub Models",
            "account_key": "GITHUB_TOKEN",
            "account_email": resolve_account_email("S02_GITHUB_TOKEN_ANTIGRAVITY"),
            "model_id": m_id,
            "canonical_name": c_name,
            "base_url": GITHUB_MODELS_BASE,
            "api_key": GITHUB_TOKEN,
            "headers": {},
            "is_free_tier": is_free,
            "context_window": ctx,
            "supports_tools": supports_tools,
            "supports_vision": supports_vision
        }

    # 9. OpenRouter (por defecto para modelos con '/' o de catálogo OpenRouter)
    acc = OPENROUTER_ACCOUNTS[0] if OPENROUTER_ACCOUNTS else {"name": "OPENROUTER_API_KEY", "key": ""}
    acc_name = acc["name"]
    return {
        "provider_id": "openrouter",
        "provider_display": f"OpenRouter [{acc_name}]",
        "account_key": acc_name,
        "account_email": resolve_account_email(acc_name),
        "model_id": m_id,
        "canonical_name": c_name,
        "base_url": OPENROUTER_API_BASE,
        "api_key": acc["key"],
        "headers": {"HTTP-Referer": "https://floydia.site", "X-Title": "FloydIA Deep Probe"},
        "is_free_tier": is_free,
        "context_window": ctx,
        "supports_tools": supports_tools,
        "supports_vision": supports_vision
    }


def get_candidate_scan_targets(selected_models: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Genera la lista completa de candidatos a sondear extrayendo modelos y credenciales locales activas.
    Si se proporciona selected_models, genera objetivos específicos para esos modelos.
    """
    if selected_models is not None and len(selected_models) > 0:
        targets = []
        seen_keys = set()
        for m in selected_models:
            t = build_probe_target_for_model(m)
            if t:
                key = (t.get("provider_id"), t.get("model_id"))
                if key not in seen_keys:
                    seen_keys.add(key)
                    targets.append(t)
        return targets

    targets = []

    # 1. Google AI Studio (Multi-Cuenta C1..C6)
    for acc in GOOGLE_ACCOUNTS:
        acc_name = acc["name"]
        acc_tag = acc_name.split("_")[0] if "_" in acc_name else "Google"
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro", "gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemma-2-27b-it"]:
            clean_name = m_id.replace("-", " ").title()
            targets.append({
                "provider_id": "google",
                "provider_display": f"Google AI Studio [{acc_tag}]",
                "account_key": acc_name,
                "account_tag": acc_tag,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": f"{clean_name} [{acc_tag}]",
                "base_url": GOOGLE_OPENAI_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": "flash" in m_id or "gemma" in m_id,
                "context_window": 2097152 if "3.7" in m_id or "pro" in m_id else 1048576,
                "supports_tools": True,
                "supports_vision": "gemini" in m_id
            })

    # 2. DeepSeek Direct (Multi-Cuenta C1..C7)
    for acc in DEEPSEEK_ACCOUNTS:
        acc_name = acc["name"]
        acc_tag = acc_name.split("_")[0] if "_" in acc_name else "DeepSeek"
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash", "deepseek-v4-pro"]:
            clean_name = m_id.replace("-", " ").title()
            targets.append({
                "provider_id": "deepseek",
                "provider_display": f"DeepSeek Direct [{acc_tag}]",
                "account_key": acc_name,
                "account_tag": acc_tag,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": f"{clean_name} [{acc_tag}]",
                "base_url": f"{DEEPSEEK_API_BASE.rstrip('/')}/v1",
                "api_key": key,
                "headers": {},
                "is_free_tier": False,
                "context_window": 131072 if "chat" in m_id else 65536,
                "supports_tools": "chat" in m_id or "flash" in m_id,
                "supports_vision": False
            })

    # 3. OpenRouter Fleet (Top Cuentas C1..C7)
    for acc in OPENROUTER_ACCOUNTS[:3]:
        acc_name = acc["name"]
        acc_tag = acc_name.split("_")[0] if "_" in acc_name else "OpenRouter"
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id, is_free, ctx in [
            ("qwen/qwen-2.5-coder-32b-instruct:free", True, 131072),
            ("meta-llama/llama-3.3-70b-instruct:free", True, 131072),
            ("deepseek/deepseek-r1:free", True, 65536),
            ("deepseek/deepseek-chat", False, 131072),
            ("nvidia/nemotron-3.5-lightning:free", True, 262144),
            ("minimax/minimax-m3:free", True, 1048576),
            ("thinkingmachines/inkling:free", True, 1048576),
            ("google/gemini-2.5-flash", False, 1048576)
        ]:
            clean_name = m_id.split("/")[-1].replace("-", " ").replace(":free", "").title()
            targets.append({
                "provider_id": "openrouter",
                "provider_display": f"OpenRouter [{acc_tag}]",
                "account_key": acc_name,
                "account_tag": acc_tag,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": f"{clean_name} [{acc_tag}]",
                "base_url": OPENROUTER_API_BASE,
                "api_key": key,
                "headers": {"HTTP-Referer": "https://floydia.site", "X-Title": "FloydIA Deep Probe"},
                "is_free_tier": is_free,
                "context_window": ctx,
                "supports_tools": True,
                "supports_vision": False
            })

    # 4. NVIDIA NIM (Multi-Cuenta C1, C2, C7)
    for acc in NVIDIA_ACCOUNTS:
        acc_name = acc["name"]
        acc_tag = acc_name.split("_")[0] if "_" in acc_name else "NVIDIA"
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in [
            "moonshotai/kimi-k3",
            "deepseek-ai/deepseek-v4-flash-0731",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            "nvidia/nemotron-3-super-120b-a12b"
        ]:
            clean_name = m_id.split("/")[-1].replace("-", " ").title()
            targets.append({
                "provider_id": "nvidia",
                "provider_display": f"NVIDIA NIM [{acc_tag}]",
                "account_key": acc_name,
                "account_tag": acc_tag,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": f"{clean_name} [{acc_tag}]",
                "base_url": NVIDIA_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": True,
                "context_window": 262144,
                "supports_tools": True,
                "supports_vision": False
            })

    # 5. Alibaba DashScope
    for acc in DASHSCOPE_ACCOUNTS:
        acc_name = acc["name"]
        acc_tag = acc_name.split("_")[0] if "_" in acc_name else "Alibaba"
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["qwen3.8-max", "qwen3.8-flash", "qwen-2.5-coder-32b-instruct"]:
            clean_name = m_id.replace("-", " ").title()
            targets.append({
                "provider_id": "dashscope",
                "provider_display": f"Alibaba DashScope [{acc_tag}]",
                "account_key": acc_name,
                "account_tag": acc_tag,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": f"{clean_name} [{acc_tag}]",
                "base_url": DASHSCOPE_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": "flash" in m_id,
                "context_window": 131072,
                "supports_tools": True,
                "supports_vision": False
            })

    # 6. Mistral AI (Multi-Cuenta C1..C6)
    for acc in MISTRAL_ACCOUNTS:
        acc_name = acc["name"]
        acc_tag = acc_name.split("_")[0] if "_" in acc_name else "Mistral"
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["codestral-latest", "mistral-small-latest", "ministral-8b-latest"]:
            clean_name = m_id.replace("-", " ").title()
            targets.append({
                "provider_id": "mistral",
                "provider_display": f"Mistral AI [{acc_tag}]",
                "account_key": acc_name,
                "account_tag": acc_tag,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": f"{clean_name} [{acc_tag}]",
                "base_url": MISTRAL_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": True,
                "context_window": 131072,
                "supports_tools": True,
                "supports_vision": False
            })

    # 7. Z.AI (Multi-Cuenta C1..C6)
    for acc in Z_AI_ACCOUNTS:
        acc_name = acc["name"]
        acc_tag = acc_name.split("_")[0] if "_" in acc_name else "Z.AI"
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["glm-4-flash", "glm-5.3-flash", "glm-5.3-max"]:
            clean_name = m_id.replace("-", " ").title()
            targets.append({
                "provider_id": "z_ai",
                "provider_display": f"Z.AI [{acc_tag}]",
                "account_key": acc_name,
                "account_tag": acc_tag,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": f"{clean_name} [{acc_tag}]",
                "base_url": Z_AI_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": True,
                "context_window": 128000,
                "supports_tools": True,
                "supports_vision": False
            })

    # 8. Groq LPU
    for acc in GROQ_ACCOUNTS:
        acc_name = acc["name"]
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-2.5-coder-32b"]:
            targets.append({
                "provider_id": "groq",
                "provider_display": f"Groq LPU [{acc_name}]",
                "account_key": acc_name,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": m_id,
                "base_url": GROQ_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": True,
                "context_window": 131072,
                "supports_tools": True,
                "supports_vision": False
            })

    # 8. Z.AI (Zhipu GLM)
    for acc in Z_AI_ACCOUNTS:
        acc_name = acc["name"]
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["glm-4-flash", "glm-5.3-flash"]:
            targets.append({
                "provider_id": "z_ai",
                "provider_display": f"Z.AI [{acc_name}]",
                "account_key": acc_name,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": m_id,
                "base_url": Z_AI_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": True,
                "context_window": 131072,
                "supports_tools": True,
                "supports_vision": False
            })

    # 9. ZenMux
    for acc in ZEN_ACCOUNTS:
        acc_name = acc["name"]
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["qwen/qwen3.8-flash", "z-ai/glm-5.3-flash"]:
            targets.append({
                "provider_id": "zenmux",
                "provider_display": f"ZenMux [{acc_name}]",
                "account_key": acc_name,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": m_id,
                "base_url": ZEN_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": True,
                "context_window": 262144,
                "supports_tools": True,
                "supports_vision": False
            })

    # 10. Grokified
    for acc in GROKIFIED_ACCOUNTS:
        acc_name = acc["name"]
        key = acc["key"]
        email = resolve_account_email(acc_name)
        for m_id in ["grok-4.6", "grok-4.5"]:
            targets.append({
                "provider_id": "grokified",
                "provider_display": f"Grokified [{acc_name}]",
                "account_key": acc_name,
                "account_email": email,
                "model_id": m_id,
                "canonical_name": m_id,
                "base_url": GROKIFIED_API_BASE,
                "api_key": key,
                "headers": {},
                "is_free_tier": False,
                "context_window": 131072,
                "supports_tools": True,
                "supports_vision": False
            })

    # 11. GitHub Models
    if GITHUB_TOKEN:
        for m_id in ["gpt-4o", "gpt-4o-mini"]:
            targets.append({
                "provider_id": "github",
                "provider_display": "GitHub Models",
                "account_key": "GITHUB_TOKEN",
                "account_email": resolve_account_email("S02_GITHUB_TOKEN_ANTIGRAVITY"),
                "model_id": m_id,
                "canonical_name": m_id,
                "base_url": GITHUB_MODELS_BASE,
                "api_key": GITHUB_TOKEN,
                "headers": {},
                "is_free_tier": True,
                "context_window": 128000,
                "supports_tools": True,
                "supports_vision": True
            })

    # 12. Fireworks AI
    if FIREWORKS_API_KEY:
        for m_id in ["accounts/fireworks/models/deepseek-v3", "accounts/fireworks/models/llama-v3p3-70b-instruct"]:
            targets.append({
                "provider_id": "fireworks",
                "provider_display": "Fireworks AI",
                "account_key": "FIREWORKS_API_KEY",
                "account_email": resolve_account_email("C7_FIREWORKS_API_KEY"),
                "model_id": m_id,
                "canonical_name": m_id,
                "base_url": FIREWORKS_API_BASE,
                "api_key": FIREWORKS_API_KEY,
                "headers": {},
                "is_free_tier": False,
                "context_window": 131072,
                "supports_tools": True,
                "supports_vision": False
            })

    return targets


def execute_single_probe(target: Dict[str, Any], prompt: str = DEFAULT_PROBE_PROMPT, timeout: float = DEFAULT_TIMEOUT_SECS) -> Dict[str, Any]:
    """
    Ejecuta una petición síncrona HTTP POST a un endpoint OpenAI-compatible con la pregunta corta.
    """
    base_url = target.get("base_url", "").rstrip("/")
    url = f"{base_url}/chat/completions"
    api_key = target.get("api_key", "")
    
    if not api_key:
        return {
            **target,
            "status_code": 401,
            "classification": STATUS_UNAUTHORIZED,
            "status_message": "🔒 Clave API no configurada",
            "latency_ms": 0.0,
            "response_snippet": "",
            "is_functional": False
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    if target.get("headers"):
        headers.update(target["headers"])

    payload = {
        "model": target["model_id"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 16,
        "temperature": 0.1
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = round((time.perf_counter() - t0) * 1000, 1)
            status_code = resp.status
            body_str = resp.read().decode("utf-8", errors="ignore")
            classification, msg = classify_response(status_code, body_str, "", latency)
            
            # Extraer snippet limpio
            snippet = ""
            try:
                data_json = json.loads(body_str)
                choices = data_json.get("choices", [])
                if choices:
                    snippet = str(choices[0].get("message", {}).get("content", "")).strip()
            except Exception:
                snippet = body_str[:50].strip()

            return {
                **target,
                "status_code": status_code,
                "classification": classification,
                "status_message": msg,
                "latency_ms": latency,
                "response_snippet": snippet,
                "is_functional": (classification == STATUS_OK)
            }
    except urllib.error.HTTPError as e:
        latency = round((time.perf_counter() - t0) * 1000, 1)
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        classification, msg = classify_response(e.code, err_body, str(e.reason), latency)
        return {
            **target,
            "status_code": e.code,
            "classification": classification,
            "status_message": msg,
            "latency_ms": latency,
            "response_snippet": err_body[:100],
            "is_functional": False
        }
    except urllib.error.URLError as e:
        latency = round((time.perf_counter() - t0) * 1000, 1)
        classification, msg = classify_response(0, "", str(e.reason), latency)
        return {
            **target,
            "status_code": 0,
            "classification": classification,
            "status_message": msg,
            "latency_ms": latency,
            "response_snippet": str(e.reason),
            "is_functional": False
        }
    except Exception as e:
        latency = round((time.perf_counter() - t0) * 1000, 1)
        classification, msg = classify_response(500, "", str(e), latency)
        return {
            **target,
            "status_code": 500,
            "classification": classification,
            "status_message": msg,
            "latency_ms": latency,
            "response_snippet": str(e),
            "is_functional": False
        }


async def _probe_worker(target: Dict[str, Any], prompt: str, semaphore: asyncio.Semaphore, loop) -> Dict[str, Any]:
    async with semaphore:
        return await loop.run_in_executor(None, execute_single_probe, target, prompt)


def init_deep_scan_schema():
    """Garantiza que la tabla deep_scan_runs exista en SQLite."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deep_scan_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id TEXT NOT NULL,
                provider_display TEXT NOT NULL,
                account_key TEXT,
                account_email TEXT,
                model_id TEXT NOT NULL,
                canonical_name TEXT,
                status_code INTEGER,
                classification TEXT NOT NULL,
                status_message TEXT,
                latency_ms REAL,
                response_snippet TEXT,
                prompt_used TEXT,
                is_functional BOOLEAN NOT NULL,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_deep_scan_status ON deep_scan_runs (classification, scanned_at)
        """)


def record_deep_scan_result(res: Dict[str, Any], prompt_used: str = DEFAULT_PROBE_PROMPT):
    """Persiste el resultado de un escaneo en SQLite de forma sanitizada."""
    init_deep_scan_schema()
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO deep_scan_runs (
                    provider_id, provider_display, account_key, account_email,
                    model_id, canonical_name, status_code, classification,
                    status_message, latency_ms, response_snippet, prompt_used, is_functional
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                res.get("provider_id", "unknown"),
                res.get("provider_display", "Unknown"),
                res.get("account_key", ""),
                res.get("account_email", ""),
                res.get("model_id", ""),
                res.get("canonical_name", res.get("model_id")),
                res.get("status_code", 0),
                res.get("classification", STATUS_ERROR),
                scrub_secrets(res.get("status_message", "")),
                res.get("latency_ms", 0.0),
                scrub_secrets(res.get("response_snippet", "")),
                prompt_used,
                1 if res.get("is_functional") else 0
            ))
    except Exception as e:
        print(f"⚠️ [DeepProbeScanner] Error guardando resultado: {e}")


def get_latest_deep_scan_results(limit: int = 150) -> List[Dict[str, Any]]:
    """Recupera los resultados más recientes del escaneo profundo desde SQLite."""
    init_deep_scan_schema()
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM deep_scan_runs
                WHERE scanned_at >= datetime('now', '-24 hours')
                ORDER BY id DESC
            """)
            rows = c.fetchall()
            # De-duplicar por (provider_id, model_id) tomando el más reciente
            seen = set()
            results = []
            for r in rows:
                k = (r["provider_id"], r["model_id"], r["account_key"])
                if k not in seen:
                    seen.add(k)
                    results.append(dict(r))
            return results
    except Exception as e:
        print(f"⚠️ [DeepProbeScanner] Error leyendo deep_scan_runs: {e}")
        return []


async def run_deep_scan_async(
    prompt: str = DEFAULT_PROBE_PROMPT,
    progress_callback=None,
    targets: Optional[List[Dict[str, Any]]] = None,
    selected_models: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta el escaneo profundo en paralelo sobre los objetivos especificados o la flota global.
    """
    if targets is None:
        targets = get_candidate_scan_targets(selected_models=selected_models)
        
    print(f"🔬 [DeepProbeScanner] Iniciando escaneo profundo sobre {len(targets)} modelos (Prompt: '{prompt}')...")

    loop = asyncio.get_running_loop()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCANS)
    tasks = [_probe_worker(t, prompt, semaphore, loop) for t in targets]

    completed = 0
    total = len(tasks)
    results = []

    for f in asyncio.as_completed(tasks):
        res = await f
        record_deep_scan_result(res, prompt_used=prompt)
        results.append(res)
        completed += 1
        if progress_callback:
            progress_callback(completed, total, res)

    print(f"✅ [DeepProbeScanner] Escaneo finalizado. {sum(1 for r in results if r.get('is_functional'))}/{len(results)} modelos con RESPUESTA_OK.")
    return results


def run_deep_scan(
    prompt: str = DEFAULT_PROBE_PROMPT,
    progress_callback=None,
    targets: Optional[List[Dict[str, Any]]] = None,
    selected_models: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Punto de entrada síncrono para CLI, scripts o hilos de PyQt6.
    """
    try:
        resolved_targets = targets if targets is not None else get_candidate_scan_targets(selected_models=selected_models)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SCANS) as executor:
                futures = [executor.submit(execute_single_probe, t, prompt) for t in resolved_targets]
                results = []
                for i, fut in enumerate(futures, 1):
                    res = fut.result()
                    record_deep_scan_result(res, prompt_used=prompt)
                    results.append(res)
                    if progress_callback:
                        progress_callback(i, len(resolved_targets), res)
                return results
        else:
            return loop.run_until_complete(run_deep_scan_async(prompt, progress_callback, targets=resolved_targets))
    except RuntimeError:
        resolved_targets = targets if targets is not None else get_candidate_scan_targets(selected_models=selected_models)
        return asyncio.run(run_deep_scan_async(prompt, progress_callback, targets=resolved_targets))

