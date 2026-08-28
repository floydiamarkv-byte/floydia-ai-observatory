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

    def test_artificial_analysis_fallback_no_contamina(self):
        """
        Regresión anti-contaminación (Problema B): el fallback estático de
        Artificial Analysis debe guardarse con provenance='fallback' (nunca 'live')
        y NO debe escribir el snapshot con modelos inventados.
        """
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from src.core import db as db_module

        c = ArtificialAnalysisCollector()

        # Simular que NO hay API key ni snapshot -> cae al fallback en memoria
        with tempfile.TemporaryDirectory() as tmp:
            fake_snapshot = Path(tmp) / "artificial_analysis_snapshot.json"
            c.snapshot_file = fake_snapshot

            saved = []
            def fake_save_evaluation(model_id, source, benchmark_name, score, category="general", rank_position=None, unit="points", provenance="live"):
                saved.append({"model_id": model_id, "benchmark": benchmark_name, "provenance": provenance})

            with patch.object(db_module, "save_evaluation", side_effect=fake_save_evaluation), \
                 patch("src.collectors.artificial_analysis.get_secret", return_value=None), \
                 patch("src.collectors.artificial_analysis.save_evaluation", side_effect=fake_save_evaluation):
                n = c.collect()

            # 1. El fallback no debe persistir snapshot
            self.assertFalse(fake_snapshot.exists(), "El fallback no debe escribir el snapshot")

            # 2. Ninguna evaluación del fallback debe tener provenance='live'
            self.assertGreater(len(saved), 0, "El fallback debería emitir métricas")
            for s in saved:
                self.assertEqual(s["provenance"], "fallback", f"Provenance incorrecta para {s['model_id']}")

    def test_zen_prober_hace_llamadas_reales(self):
        """
        Regresión anti-falsificación: el prober de OpenCode Zen debe realizar llamadas
        reales y nunca marcar is_functional=True con latencia hardcodeada sin probe.
        """
        import time
        from unittest.mock import patch
        from src.probers import zen_prober

        # Forzar una cuenta fake y verificar que NO marca funcional sin HTTP 200 real
        fake_accounts = [{"name": "C1_ZEN_OPENCODE", "key": "fake-key-zen-prober-test"}]
        with patch.object(zen_prober, "ZEN_ACCOUNTS", fake_accounts), \
             patch("requests.post", side_effect=Exception("Red simulada caída")):
            results = zen_prober.probe_opencode_zen()

        self.assertGreater(len(results), 0)
        for r in results:
            self.assertFalse(r["is_functional"], "Sin respuesta 200 real, el modelo NO debe marcarse funcional")


if __name__ == "__main__":
    unittest.main()
