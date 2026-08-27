"""
Tests unitarios para los recolectores de benchmarks v9.0.
Verifica que los colectores se inicialicen correctamente y que sus métodos básicos respondan.
"""

import unittest
from src.collectors.arena_collector import ArenaCollector
from src.collectors.swebench_collector import SWEBenchCollector
from src.collectors.aider_collector import AiderCollector
from src.collectors.artificial_analysis import ArtificialAnalysisCollector
from src.collectors.livebench_epoch import LiveBenchEpochCollector
from src.collectors.aggregator import run_all_collectors
from src.core.scoring import calculate_multidimensional_rankings


class TestCollectorsV9(unittest.TestCase):
    def test_collectors_instantiation(self):
        c1 = ArenaCollector()
        self.assertEqual(c1.name, "ArenaAI")
        
        c2 = SWEBenchCollector()
        self.assertEqual(c2.name, "SWEBench")
        
        c3 = AiderCollector()
        self.assertEqual(c3.name, "Aider")
        
        c4 = ArtificialAnalysisCollector()
        self.assertEqual(c4.name, "ArtificialAnalysis")
        
        c5 = LiveBenchEpochCollector()
        self.assertEqual(c5.name, "LiveBenchEpoch")

    def test_scoring_multidimensional_v9(self):
        rankings = calculate_multidimensional_rankings()
        self.assertIsInstance(rankings, list)
        self.assertGreater(len(rankings), 0)
        
        first = rankings[0]
        self.assertIn("global_rank", first)
        self.assertIn("intelligence_score", first)
        self.assertIn("coding_score", first)
        self.assertIn("workhorse_score", first)
        self.assertIn("preference_score", first)
        self.assertIn("sources", first)
        self.assertIn("intel_benchmarks", first)
        self.assertIn("coding_benchmarks", first)


if __name__ == "__main__":
    unittest.main()
