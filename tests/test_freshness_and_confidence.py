"""
Tests unitarios para el motor de frescura y cálculo probabilístico de confianza (Kimi Protocol).
"""

import unittest
from datetime import datetime, timezone, timedelta
from src.core.freshness import freshness_engine
from src.core.confidence import confidence_engine
from src.core.contracts import ObservationType


class TestFreshnessAndConfidence(unittest.TestCase):
    def test_freshness_evaluation_fresh(self):
        # 1 día de antigüedad
        recent_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        days, decay, status = freshness_engine.evaluate_freshness(recent_date)
        self.assertAlmostEqual(days, 1.0, delta=0.5)
        self.assertGreater(decay, 0.90)
        self.assertEqual(status, "🟢 FRESH")

    def test_freshness_evaluation_stale(self):
        # 45 días de antigüedad
        stale_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=45)
        days, decay, status = freshness_engine.evaluate_freshness(stale_date)
        self.assertAlmostEqual(days, 45.0, delta=1.0)
        self.assertLess(decay, 0.50)
        self.assertEqual(status, "🔴 STALE")

    def test_confidence_calculation_high(self):
        # Múltiples fuentes de alta fiabilidad, dato fresco y observado
        conf = confidence_engine.calculate_confidence(
            sources=["Arena.ai", "Artificial Analysis", "LiveBench"],
            freshness_decay=0.98,
            metrics_count=6,
            has_local_verification=True,
            observation_type=ObservationType.OBSERVED
        )
        self.assertGreaterEqual(conf, 0.85)
        badge = confidence_engine.get_badge(conf)
        self.assertEqual(badge, "🟢 HIGH CONFIDENCE")

    def test_confidence_calculation_low_for_unverified(self):
        # Sin fuentes externas, dato sintético/default
        conf = confidence_engine.calculate_confidence(
            sources=[],
            freshness_decay=0.20,
            metrics_count=0,
            has_local_verification=False,
            observation_type=ObservationType.DEFAULT
        )
        self.assertLess(conf, 0.70)
        badge = confidence_engine.get_badge(conf)
        self.assertEqual(badge, "🟠 LIMITED EVIDENCE")


if __name__ == "__main__":
    unittest.main()
