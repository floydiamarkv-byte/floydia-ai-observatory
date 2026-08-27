"""
Tests unitarios para el exportador de snapshots para IAs Frontier.
"""

import unittest
from src.analyst.frontier_exporter import export_daily_snapshot_for_frontier_ai


class TestFrontierExporter(unittest.TestCase):
    def test_export_frontier_snapshot(self):
        mock_rankings = [
            {
                "id": "gemini-2.5-flash",
                "canonical_name": "Google Gemini 2.5 Flash",
                "tier": "workhorse",
                "provider": "Google",
                "context_window": 1048576,
                "max_output": 8192,
                "is_free_tier": True,
                "input_cost_per_m": 0.0,
                "output_cost_per_m": 0.0,
                "intelligence_score": 78.4,
                "effective_score": 77.5,
                "workhorse_score": 88.0,
                "coding_score": 85.0,
                "preference_score": 86.2,
                "is_local_active": True,
                "local_latency_ms": 120.5,
                "confidence_score": 0.95,
                "confidence_badge": "🟢 HIGH CONFIDENCE",
                "freshness_days": 1.0,
                "freshness_status": "🟢 FRESH",
                "global_rank": 1
            },
            {
                "id": "claude-3-7-sonnet",
                "canonical_name": "Anthropic Claude 3.7 Sonnet",
                "tier": "frontier",
                "provider": "Anthropic",
                "context_window": 200000,
                "max_output": 8192,
                "is_free_tier": False,
                "input_cost_per_m": 3.0,
                "output_cost_per_m": 15.0,
                "intelligence_score": 92.5,
                "effective_score": 91.8,
                "workhorse_score": 70.0,
                "coding_score": 96.0,
                "preference_score": 98.0,
                "is_local_active": False,
                "local_latency_ms": None,
                "confidence_score": 0.94,
                "confidence_badge": "🟢 HIGH CONFIDENCE",
                "freshness_days": 2.0,
                "freshness_status": "🟢 FRESH",
                "global_rank": 2
            }
        ]

        out_file = export_daily_snapshot_for_frontier_ai(mock_rankings, [])
        self.assertTrue(out_file.exists())

        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("FLOYDIA AI BENCHMARKS & LOCAL APIS", content)
        self.assertIn("ARSENAL LOCAL", content)
        self.assertIn("Google Gemini 2.5 Flash", content)
        self.assertIn("RADAR GLOBAL", content)
        self.assertIn("Anthropic Claude 3.7 Sonnet", content)


if __name__ == "__main__":
    unittest.main()
