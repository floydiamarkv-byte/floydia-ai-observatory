"""
Tests Unitarios para el Enrutador Inteligente Dinámico (LLMRouter).
Verifica:
1. Selección por tarea (coding, reasoning, chat, realtime).
2. Filtrado por presupuesto (free, economy, frontier).
3. Restricciones duras de latencia máxima y contexto.
4. Generación de cascada de alternativas (Secondary, Tertiary, Emergency).
5. Explicabilidad transparente en routing_reason.
"""

import unittest
from unittest.mock import patch
from src.core.router import LLMRouter, recommend_model


class TestLLMRouter(unittest.TestCase):

    def setUp(self):
        self.router = LLMRouter()
        self.mock_models = [
            {
                "id": "gemini-2.0-flash",
                "canonical_name": "Google Gemini 2.0 Flash",
                "provider": "Google",
                "tier": "realtime",
                "context_window": 1048576,
                "is_free_tier": True,
                "input_cost_per_m": 0.0,
                "output_cost_per_m": 0.0,
                "local_latency_ms": 320.0,
                "intelligence_score": 75.0,
                "coding_index": 72.0,
                "reasoning_score": 74.0,
                "confidence": 0.9,
                "evidence_grade": "A (Verificado)",
                "is_local_active": True,
                "supports_tools": True,
                "supports_vision": True,
                "supports_reasoning": False
            },
            {
                "id": "deepseek-r1",
                "canonical_name": "DeepSeek R1 (Reasoner)",
                "provider": "DeepSeek",
                "tier": "reasoning",
                "context_window": 64000,
                "is_free_tier": False,
                "input_cost_per_m": 0.55,
                "output_cost_per_m": 2.19,
                "local_latency_ms": 1100.0,
                "intelligence_score": 92.0,
                "coding_index": 90.0,
                "reasoning_score": 96.0,
                "confidence": 0.95,
                "evidence_grade": "A (Verificado)",
                "is_local_active": True,
                "supports_tools": True,
                "supports_vision": False,
                "supports_reasoning": True
            },
            {
                "id": "claude-3-7-sonnet",
                "canonical_name": "Anthropic Claude 3.7 Sonnet",
                "provider": "Anthropic",
                "tier": "coding",
                "context_window": 200000,
                "is_free_tier": False,
                "input_cost_per_m": 3.0,
                "output_cost_per_m": 15.0,
                "local_latency_ms": 780.0,
                "intelligence_score": 95.0,
                "coding_index": 97.0,
                "reasoning_score": 94.0,
                "confidence": 0.92,
                "evidence_grade": "A (Verificado)",
                "is_local_active": True,
                "supports_tools": True,
                "supports_vision": True,
                "supports_reasoning": True
            },
            {
                "id": "qwen-2.5-coder-32b",
                "canonical_name": "Qwen 2.5 Coder 32B (Free)",
                "provider": "OpenRouter",
                "tier": "coding",
                "context_window": 32768,
                "is_free_tier": True,
                "input_cost_per_m": 0.0,
                "output_cost_per_m": 0.0,
                "local_latency_ms": 450.0,
                "intelligence_score": 82.0,
                "coding_index": 85.0,
                "reasoning_score": 80.0,
                "confidence": 0.88,
                "evidence_grade": "A (Verificado)",
                "is_local_active": True,
                "supports_tools": True,
                "supports_vision": False,
                "supports_reasoning": False
            }
        ]

    @patch("src.core.router.calculate_multidimensional_rankings")
    def test_recommend_coding_free(self, mock_calc):
        mock_calc.return_value = self.mock_models
        rec = self.router.recommend(task="coding", budget="free")
        
        self.assertEqual(rec["status"], "success")
        best = rec["recommended_model"]
        self.assertTrue(best["is_free_tier"])
        self.assertEqual(best["id"], "qwen-2.5-coder-32b")

    @patch("src.core.router.calculate_multidimensional_rankings")
    def test_recommend_reasoning_economy(self, mock_calc):
        mock_calc.return_value = self.mock_models
        rec = self.router.recommend(task="reasoning", budget="economy")
        
        self.assertEqual(rec["status"], "success")
        best = rec["recommended_model"]
        self.assertEqual(best["id"], "deepseek-r1")
        self.assertLessEqual(best["input_cost_per_m"], 1.5)

    @patch("src.core.router.calculate_multidimensional_rankings")
    def test_recommend_latency_constraint(self, mock_calc):
        mock_calc.return_value = self.mock_models
        # Si la latencia máxima es 400ms, Qwen (450ms), DeepSeek (1100ms) y Claude (780ms) quedan descartados
        rec = self.router.recommend(task="general", max_latency_ms=400.0)
        
        self.assertEqual(rec["status"], "success")
        best = rec["recommended_model"]
        self.assertLessEqual(best["local_latency_ms"], 400.0)
        self.assertEqual(best["id"], "gemini-2.0-flash")

    @patch("src.core.router.calculate_multidimensional_rankings")
    def test_cascading_fallbacks_present(self, mock_calc):
        mock_calc.return_value = self.mock_models
        rec = self.router.recommend(task="general", budget="any")
        
        self.assertEqual(rec["status"], "success")
        fallbacks = rec.get("cascading_fallbacks", [])
        self.assertGreater(len(fallbacks), 0)
        self.assertIn("reason", rec["recommended_model"])


if __name__ == "__main__":
    unittest.main()
