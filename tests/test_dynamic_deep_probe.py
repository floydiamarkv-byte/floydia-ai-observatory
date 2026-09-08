"""
Tests unitarios para la resolución dinámica de objetivos de escaneo profundo y clasificación de estados.
"""

import unittest
from src.probers.deep_probe_scanner import (
    build_probe_target_for_model,
    get_candidate_scan_targets,
    classify_response,
    STATUS_OK, STATUS_NO_BALANCE, STATUS_FREE_TIER_AGOTADO,
    STATUS_UNAUTHORIZED, STATUS_NO_RESPONSE, STATUS_ERROR
)


class TestDynamicDeepProbe(unittest.TestCase):

    def test_build_probe_target_google(self):
        item = {
            "id": "gemini-2.5-flash",
            "provider": "google",
            "canonical_name": "gemini-2.5-flash",
            "context_window": 1048576,
            "is_free_tier": True
        }
        target = build_probe_target_for_model(item)
        self.assertIsNotNone(target)
        self.assertEqual(target["provider_id"], "google")
        self.assertEqual(target["model_id"], "gemini-2.5-flash")
        self.assertTrue(target["is_free_tier"])

    def test_build_probe_target_openrouter_custom(self):
        item = {
            "id": "anthropic/claude-3.7-sonnet",
            "provider": "openrouter",
            "canonical_name": "claude-3.7-sonnet",
            "context_window": 200000,
            "is_free_tier": False
        }
        target = build_probe_target_for_model(item)
        self.assertIsNotNone(target)
        self.assertEqual(target["provider_id"], "openrouter")
        self.assertEqual(target["model_id"], "anthropic/claude-3.7-sonnet")
        self.assertIn("HTTP-Referer", target["headers"])

    def test_build_probe_target_deepseek(self):
        item = {
            "id": "deepseek-chat",
            "provider": "deepseek",
            "canonical_name": "deepseek-chat"
        }
        target = build_probe_target_for_model(item)
        self.assertIsNotNone(target)
        self.assertEqual(target["provider_id"], "deepseek")
        self.assertEqual(target["model_id"], "deepseek-chat")

    def test_build_probe_target_invalid(self):
        self.assertIsNone(build_probe_target_for_model({}))
        self.assertIsNone(build_probe_target_for_model({"id": ""}))

    def test_get_candidate_scan_targets_selected_models(self):
        selected = [
            {"id": "qwen/qwen-2.5-coder-32b-instruct:free", "provider": "openrouter"},
            {"id": "deepseek-chat", "provider": "deepseek"},
            {"id": "qwen/qwen-2.5-coder-32b-instruct:free", "provider": "openrouter"}  # Duplicado intencional
        ]
        targets = get_candidate_scan_targets(selected_models=selected)
        self.assertEqual(len(targets), 2)  # Debería deduplicar
        target_models = [t["model_id"] for t in targets]
        self.assertIn("qwen/qwen-2.5-coder-32b-instruct:free", target_models)
        self.assertIn("deepseek-chat", target_models)

    def test_classify_response_states(self):
        # 1. OK
        body_ok = '{"choices": [{"message": {"content": "¡Sí, hola!"}}]}'
        st, msg = classify_response(200, body_ok, "", 120.0)
        self.assertEqual(st, STATUS_OK)
        self.assertIn("Sí, hola", msg)

        # 2. Sin saldo (402)
        st, msg = classify_response(402, "Payment Required", "Out of credits", 50.0)
        self.assertEqual(st, STATUS_NO_BALANCE)

        # 3. Free tier / Rate limit (429)
        st, msg = classify_response(429, "Too Many Requests", "Rate limit exceeded", 80.0)
        self.assertEqual(st, STATUS_FREE_TIER_AGOTADO)

        # 4. No autorizado (401)
        st, msg = classify_response(401, "Unauthorized", "Invalid API key", 40.0)
        self.assertEqual(st, STATUS_UNAUTHORIZED)

        # 5. Sin respuesta / Timeout
        st, msg = classify_response(0, "", "timed out", 5000.0)
        self.assertEqual(st, STATUS_NO_RESPONSE)

        # 6. Error general 500
        st, msg = classify_response(500, "Internal Server Error", "Server crashed", 200.0)
        self.assertEqual(st, STATUS_ERROR)


if __name__ == "__main__":
    unittest.main()
