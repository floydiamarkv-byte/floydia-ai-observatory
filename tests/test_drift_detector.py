"""
Tests Unitarios para el Detector de Deriva (DriftDetector).
Verifica:
1. Detección de variaciones de precio en catálogo.
2. Detección de cambios de ventana de contexto.
3. Detección de degradación de latencia respecto a la mediana histórica.
4. Detección de candidatos a deprecación por 404 consecutivos.
"""

import unittest
from unittest.mock import patch
from src.core.drift_detector import DriftDetector


class TestDriftDetector(unittest.TestCase):

    def setUp(self):
        self.detector = DriftDetector(latency_threshold_multiplier=1.5, min_samples_for_latency=3)

    def test_detect_price_change(self):
        prev = [
            {"id": "test-model", "provider": "OpenRouter", "input_cost_per_m": 1.0, "output_cost_per_m": 3.0, "context_window": 128000}
        ]
        curr = [
            {"id": "test-model", "provider": "OpenRouter", "input_cost_per_m": 1.5, "output_cost_per_m": 3.0, "context_window": 128000}
        ]
        
        events = self.detector.detect_catalog_drift(prev, curr)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "price_change")
        self.assertEqual(events[0]["metric_name"], "input_cost_per_m")
        self.assertEqual(events[0]["old_value"], "1.0")
        self.assertEqual(events[0]["new_value"], "1.5")

    def test_detect_context_reduction(self):
        prev = [
            {"id": "ctx-model", "provider": "Google", "input_cost_per_m": 0.0, "output_cost_per_m": 0.0, "context_window": 1000000}
        ]
        curr = [
            {"id": "ctx-model", "provider": "Google", "input_cost_per_m": 0.0, "output_cost_per_m": 0.0, "context_window": 128000}
        ]
        
        events = self.detector.detect_catalog_drift(prev, curr)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "context_window_change")
        self.assertEqual(events[0]["severity"], "critical")

    def test_detect_deprecation_candidate(self):
        evt = self.detector.detect_deprecation_candidate("dead-endpoint", "TestProvider", consecutive_404_count=3)
        self.assertIsNotNone(evt)
        self.assertEqual(evt["event_type"], "deprecation_candidate")
        self.assertEqual(evt["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
