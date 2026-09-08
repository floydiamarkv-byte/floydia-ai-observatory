"""
tests/test_deep_scanner_and_injection.py — Pruebas Unitarias y de Integración.
Valida el clasificador determinista de 6 estados, la extracción de candidatos
y la reconfiguración atómica en frío de OpenCode, Hermes y DeepSeek Harness.
"""

import os
import json
import yaml
from pathlib import Path

from src.probers.deep_probe_scanner import (
    classify_response, get_candidate_scan_targets,
    STATUS_OK, STATUS_NO_BALANCE, STATUS_FREE_TIER_EXHAUSTED,
    STATUS_UNAUTHORIZED, STATUS_NO_RESPONSE, STATUS_ERROR
)
from src.core.engine_injector import (
    apply_engine_configurations, OPENCODE_CONFIG,
    HERMES_CONFIG, HERMES_CACHE, DSH_CONFIG_USER
)


def test_classify_response_ok():
    """Valida que una respuesta HTTP 200 con contenido válido se clasifique como RESPUESTA_OK."""
    mock_body = json.dumps({
        "choices": [{"message": {"content": "¡Hola! Sí, estoy funcionando correctamente."}}]
    })
    cls, msg = classify_response(200, mock_body, "", 120.0)
    assert cls == STATUS_OK
    assert "🟢" in msg


def test_classify_response_no_balance():
    """Valida que un HTTP 402 o mensaje de cuota insuficiente se clasifique como SIN_SALDO."""
    cls_402, _ = classify_response(402, "Payment Required", "Payment Required", 50.0)
    assert cls_402 == STATUS_NO_BALANCE

    mock_err_body = json.dumps({"error": {"message": "You exceeded your current quota, please check your plan and billing details."}})
    cls_quota, _ = classify_response(400, mock_err_body, "insufficient_quota", 80.0)
    assert cls_quota == STATUS_NO_BALANCE


def test_classify_response_free_tier_exhausted():
    """Valida que un HTTP 429 o rate limit se clasifique como FREE_TIER_AGOTADO."""
    cls_429, _ = classify_response(429, "Too Many Requests", "Rate limit exceeded", 40.0)
    assert cls_429 == STATUS_FREE_TIER_EXHAUSTED


def test_classify_response_unauthorized():
    """Valida que un HTTP 401/403 o error de token se clasifique como NO_AUTORIZADO."""
    cls_401, _ = classify_response(401, "Unauthorized", "Invalid API key provided", 30.0)
    assert cls_401 == STATUS_UNAUTHORIZED

    cls_403, _ = classify_response(403, "Forbidden", "Permission Denied", 30.0)
    assert cls_403 == STATUS_UNAUTHORIZED


def test_classify_response_timeout_and_empty():
    """Valida que un timeout o cuerpo vacío se clasifique como SIN_RESPUESTA."""
    cls_empty, _ = classify_response(200, "", "", 0.0)
    assert cls_empty == STATUS_NO_RESPONSE

    cls_timeout, _ = classify_response(0, "", "timed out", 5000.0)
    assert cls_timeout == STATUS_NO_RESPONSE


def test_classify_response_error():
    """Valida que un HTTP 500 o 503 se clasifique como ERROR."""
    cls_500, _ = classify_response(500, "Internal Server Error", "Server Error", 200.0)
    assert cls_500 == STATUS_ERROR


def test_get_candidate_scan_targets():
    """Valida que el generador de candidatos retorne una lista poblada con metadatos válidos."""
    targets = get_candidate_scan_targets()
    assert isinstance(targets, list)
    assert len(targets) > 0
    for t in targets:
        assert "provider_id" in t
        assert "model_id" in t
        assert "base_url" in t


def test_apply_engine_configurations_dynamic(tmp_path):
    """Valida la inyección dinámica de configuraciones a OpenCode, Hermes y DSH."""
    mock_selected = [
        {
            "provider_id": "google",
            "model_id": "gemini-2.5-flash",
            "canonical_name": "[1M•Free] Gemini 2.5 Flash",
            "context_window": 1048576,
            "is_free_tier": True
        },
        {
            "provider_id": "deepseek",
            "model_id": "deepseek-chat",
            "canonical_name": "[128k•Paid] DeepSeek Chat V3",
            "context_window": 131072,
            "is_free_tier": False
        },
        {
            "provider_id": "groq",
            "model_id": "llama-3.1-8b-instant",
            "canonical_name": "[128k•Free] Llama 3.1 8B",
            "context_window": 131072,
            "is_free_tier": True
        }
    ]

    logs = apply_engine_configurations(mock_selected)
    assert len(logs) >= 3

    # 1. Verificar OpenCode
    assert OPENCODE_CONFIG.exists()
    with open(OPENCODE_CONFIG, "r", encoding="utf-8") as f:
        oc_data = json.load(f)
        assert oc_data["model"] == "google/gemini-2.5-flash"
        assert "google" in oc_data["provider"]
        assert "deepseek" in oc_data["provider"]
        assert "gemini-2.5-flash" in oc_data["provider"]["google"]["models"]

    # 2. Verificar Hermes
    assert HERMES_CONFIG.exists()
    with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
        hermes_data = yaml.safe_load(f)
        assert hermes_data["model"]["default"] == "gemini-2.5-flash"
        assert "google" in hermes_data["providers"]
        assert "deepseek" in hermes_data["providers"]

    # 3. Verificar DeepSeek Harness
    assert DSH_CONFIG_USER.exists()
    with open(DSH_CONFIG_USER, "r", encoding="utf-8") as f:
        dsh_data = yaml.safe_load(f)
        assert "providers" in dsh_data
        assert "deepseek" in dsh_data["providers"]
