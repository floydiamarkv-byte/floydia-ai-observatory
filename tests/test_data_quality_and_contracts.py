"""
Tests unitarios para la puerta de calidad (QualityGate), contratos canónicos y detección de anomalías.
"""

import unittest
from datetime import datetime
from src.core.contracts import (
    ModelIdentity, MetricObservation, ModelStatus, ObservationType, QualityStatus
)
from src.core.quality import quality_engine


class TestDataQualityAndContracts(unittest.TestCase):
    def test_reject_negative_price(self):
        status, reason = quality_engine.validate_metric("input_cost_per_m", -100.0)
        self.assertEqual(status, QualityStatus.REJECTED)
        self.assertEqual(reason, "NEGATIVE_PRICE")

    def test_reject_negative_latency(self):
        status, reason = quality_engine.validate_metric("latency_ms", -50.0)
        self.assertEqual(status, QualityStatus.REJECTED)
        self.assertEqual(reason, "NEGATIVE_LATENCY")

    def test_reject_score_out_of_bounds(self):
        status_high, reason_high = quality_engine.validate_metric("mmlu_pro", 150.0)
        self.assertEqual(status_high, QualityStatus.REJECTED)
        
        status_low, reason_low = quality_engine.validate_metric("gpqa", -5.0)
        self.assertEqual(status_low, QualityStatus.REJECTED)

    def test_pass_valid_metrics(self):
        status, reason = quality_engine.validate_metric("mmlu_pro", 88.5)
        self.assertEqual(status, QualityStatus.VALID)
        self.assertEqual(reason, "PASS")

    def test_detect_constant_synthetic_values(self):
        # Simular 10 observaciones con el mismo valor constante sospechoso (ej. 352.1 ms)
        obs_list = [
            MetricObservation(
                model_id=f"model-{i}",
                metric="latency_ms",
                value=352.1,
                source="synthetic_source"
            )
            for i in range(10)
        ]
        
        sanitized = quality_engine.detect_constant_values(obs_list)
        for obs in sanitized:
            self.assertEqual(obs.observation_type, ObservationType.DEFAULT)
            self.assertEqual(obs.quality_status, QualityStatus.SUSPICIOUS)
            self.assertLess(obs.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
