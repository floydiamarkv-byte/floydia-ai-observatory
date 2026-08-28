"""
Tests unitarios para la arquitectura FloydIA V11 (Procedencia Estricta, Top-Stretch y Verificación Etapa C).
"""

import unittest
from src.core.contracts import Measurement
from src.core.normalizer import normalizer
from src.core.ranking_engine_v3 import ranking_engine_v3, BenchmarkNormalizer
from src.core.confidence import confidence_engine
from src.analyst.gemini_analyst import verify_report_stage_c


class TestFloydIAV11(unittest.TestCase):

    def test_measurement_contract(self):
        """Verifica que Measurement devuelva SIN DATO / None cuando measured=False."""
        m_unmeasured = Measurement(value=85.0, measured=False, n_obs=0)
        self.assertEqual(m_unmeasured.to_display_view(), "SIN DATO")
        self.assertIsNone(m_unmeasured.to_redactor_view())

        m_measured = Measurement(value=98.5, measured=True, n_obs=3, source="livecodebench")
        self.assertEqual(m_measured.to_display_view(), "98.5")
        self.assertEqual(m_measured.to_redactor_view(), 98.5)

    def test_top_stretch_preserves_monotonicity(self):
        """Verifica que el estiramiento del percentil superior sea estrictamente monótono."""
        normalizer_bench = BenchmarkNormalizer()
        p90 = normalizer_bench.stretch_top(0.90)
        p95 = normalizer_bench.stretch_top(0.95)
        p99 = normalizer_bench.stretch_top(0.99)
        p100 = normalizer_bench.stretch_top(1.00)

        self.assertAlmostEqual(p90, 0.90, places=2)
        self.assertGreater(p95, 0.95)
        self.assertGreater(p99, 0.99)
        self.assertAlmostEqual(p100, 1.00, places=4)
        self.assertTrue(p90 < p95 < p99 <= p100)

    def test_canonical_resolution_v11(self):
        """Verifica la resolución unívoca sin duplicados de los nuevos modelos."""
        can_kimi, _ = normalizer.resolve("kimi-k3-max")
        can_qwen, _ = normalizer.resolve("qwen3.8-flash")
        can_grok, _ = normalizer.resolve("grok-4.6-high")
        can_glm, _ = normalizer.resolve("glm-5.3-max")

        self.assertIn("kimi", can_kimi.lower())
        self.assertIn("qwen", can_qwen.lower())
        self.assertIn("grok", can_grok.lower())
        self.assertIn("glm", can_glm.lower())

    def test_stage_c_verifier(self):
        """Verifica que Etapa C rechace números no grounded en INPUT_DATA."""
        input_data = {
            "models": [
                {
                    "id": "claude-opus-5-max",
                    "intelligence_index": 99.33,
                    "coding_index": 98.8,
                    "raw_benchmarks": {"swe_bench": 84.5}
                }
            ]
        }

        # Texto válido
        valid_text = "El modelo Claude Opus 5 Max tiene un índice de inteligencia de 99.33 y coding de 98.8."
        violations_valid = verify_report_stage_c(valid_text, input_data)
        self.assertEqual(len(violations_valid), 0)

        # Texto con número inventado
        invalid_text = "El modelo Claude Opus 5 Max tiene una latencia inventada de 142.7 ms y coste de $44.9."
        violations_invalid = verify_report_stage_c(invalid_text, input_data)
        self.assertGreater(len(violations_invalid), 0)
        self.assertIn("142.7", violations_invalid)


if __name__ == "__main__":
    unittest.main()
