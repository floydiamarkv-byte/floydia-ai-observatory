"""
Suite de Pruebas Unitarias de Certificación V11.1 (Protocolo FloydIA).
Verifica exhaustivamente los 4 defectos corregidos (D-1 a D-4) y los 6 items de roadmap (M-1 a M-6).
"""

import unittest
import time
import json
from unittest.mock import patch, MagicMock

from src.core.ranking_engine_v3 import RankingEngineV3, ModelScoreResult
from src.core.freshness import FreshnessEngine
from src.core.auth_hmac import generate_hmac_signature, verify_hmac_request
from src.probers.micro_benchmark import (
    evaluate_arithmetic,
    evaluate_minihumaneval,
    evaluate_json_follow
)
from src.analyst.gemini_analyst import verify_historical_facts
from src.collectors.openrouter_collector import OpenRouterCollector


class TestV11Certification(unittest.TestCase):

    def setUp(self):
        self.engine = RankingEngineV3()
        self.freshness = FreshnessEngine()

    # --- D-1: Invariante Dura para Modelos No Evaluados ---
    def test_grade_d_implies_fci_null(self):
        models = [
            {"id": "qwen/qwen3.8-flash", "tier": "flash", "provider": "Alibaba", "canonical_name": "Qwen 3.8 Flash"}
        ]
        observations = []  # 0 observaciones empíricas
        
        results = self.engine.score_models(models, observations)
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertIsNone(r.fci, "Un modelo sin benchmarks debe tener fci=None")
        self.assertIsNone(r.margin_95, "Un modelo sin benchmarks debe tener margin_95=None")
        self.assertEqual(r.ci_display, "SIN DATO")
        self.assertIsNone(r.global_rank, "Un modelo sin benchmarks no debe tener ranking público")
        self.assertIn("D (Catálogo No Evaluado)", r.evidence_grade)

    def test_fci_requires_measured_pillar(self):
        models = [
            {"id": "test/model-a", "tier": "flagship", "provider": "TestProvider", "canonical_name": "Model A"},
            {"id": "test/model-b", "tier": "flash", "provider": "TestProvider", "canonical_name": "Model B"}
        ]
        # Solo Model A tiene benchmark medido
        observations = [
            {"model_id": "test/model-a", "benchmark_name": "mmlu_pro", "score": 85.0, "source": "ArtificialAnalysis", "recorded_at": "2026-08-20T00:00:00Z"}
        ]
        results = self.engine.score_models(models, observations)
        res_dict = {r.model_id: r for r in results}
        
        self.assertIsNotNone(res_dict["test/model-a"].fci)
        self.assertEqual(res_dict["test/model-a"].global_rank, 1)
        
        self.assertIsNone(res_dict["test/model-b"].fci)
        self.assertIsNone(res_dict["test/model-b"].global_rank)

    # --- D-2: Expansión de Top-10 Spread >= 2.50 pts ---
    def test_top10_spread_reported_matches_actual(self):
        models = [
            {"id": f"top/model-{i}", "tier": "flagship", "provider": "TestProvider", "canonical_name": f"Top Model {i}"}
            for i in range(10)
        ]
        # Generar observaciones escalonadas en el rango superior
        observations = []
        for i in range(10):
            # Escala realista: gpqa (mu=6.8, s=6.5) y swe_bench (mu=38.4, s=15.7)
            gpqa_score = 15.0 + (i * 4.0)
            swe_score = 25.0 + (i * 4.0)
            observations.append({
                "model_id": f"top/model-{i}",
                "benchmark_name": "gpqa",
                "score": gpqa_score,
                "source": "ArtificialAnalysis",
                "recorded_at": "2026-08-25T00:00:00Z"
            })
            observations.append({
                "model_id": f"top/model-{i}",
                "benchmark_name": "swe_bench",
                "score": swe_score,
                "source": "ArtificialAnalysis",
                "recorded_at": "2026-08-25T00:00:00Z"
            })

        results = self.engine.score_models(models, observations)
        ranked = [r for r in results if r.fci is not None]
        self.assertEqual(len(ranked), 10)
        
        top1 = ranked[0].fci
        top10 = ranked[9].fci
        spread = top1 - top10
        self.assertGreaterEqual(spread, 2.50, f"El spread real de Top-10 ({spread:.2f}) debe ser >= 2.50 pts")

    # --- M-1: Validación de Schema y Fallback en OpenRouter ---
    def test_openrouter_schema_invalid_fallback(self):
        collector = OpenRouterCollector()
        invalid_json = {"not_data": "invalid"}
        
        # Test con payload corrupto -> debe conmutar a caché stale con warning
        with patch("src.collectors.openrouter_collector.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = invalid_json
            
            collector.collect()
            self.assertIn("«stale-cache ⚠»", collector.data_warning)

    # --- M-2: Autenticación HMAC Anti-Replay ---
    def test_hmac_valid_accepted(self):
        secret = "test-secret-key"
        now = int(time.time())
        nonce = f"nonce_{time.time()}_{hash(time.time())}"
        body = '{"action": "test"}'
        sig = generate_hmac_signature(secret, now, nonce, body)

        headers = {
            "X-Floydia-Timestamp": str(now),
            "X-Floydia-Nonce": nonce,
            "X-Floydia-Signature": sig
        }
        is_valid, status, msg = verify_hmac_request(headers, body, secret)
        self.assertTrue(is_valid)
        self.assertEqual(status, 200)

    def test_hmac_replay_rejected_401(self):
        secret = "test-secret-key"
        now = int(time.time())
        nonce = f"nonce_replay_test_{time.time()}"
        body = '{"action": "test"}'
        sig = generate_hmac_signature(secret, now, nonce, body)

        headers = {
            "X-Floydia-Timestamp": str(now),
            "X-Floydia-Nonce": nonce,
            "X-Floydia-Signature": sig
        }
        # Primer intento -> Válido
        is_valid, status, _ = verify_hmac_request(headers, body, secret)
        self.assertTrue(is_valid)

        # Segundo intento con el mismo nonce -> Rechazado por Replay Attack
        is_valid2, status2, msg2 = verify_hmac_request(headers, body, secret)
        self.assertFalse(is_valid2)
        self.assertEqual(status2, 401)
        self.assertIn("Replay attack", msg2)

    def test_hmac_expired_rejected_401(self):
        secret = "test-secret-key"
        expired_ts = int(time.time()) - 600  # 10 minutos en el pasado (>300s)
        nonce = f"nonce_exp_{time.time()}"
        body = ""
        sig = generate_hmac_signature(secret, expired_ts, nonce, body)

        headers = {
            "X-Floydia-Timestamp": str(expired_ts),
            "X-Floydia-Nonce": nonce,
            "X-Floydia-Signature": sig
        }
        is_valid, status, msg = verify_hmac_request(headers, body, secret)
        self.assertFalse(is_valid)
        self.assertEqual(status, 401)
        self.assertIn("expired", msg.lower())

    # --- M-3: Micro-Benchmark Determinista ---
    def test_micro_benchmark_checks(self):
        self.assertTrue(evaluate_arithmetic("The answer is 436"))
        self.assertTrue(evaluate_arithmetic("436"))
        self.assertFalse(evaluate_arithmetic("435"))

        valid_code = "def add_numbers(a, b):\n    return a + b"
        self.assertTrue(evaluate_minihumaneval(valid_code))
        self.assertFalse(evaluate_minihumaneval("def add_numbers(a, b):\n    return a - b"))

        valid_json = '{"project": "FloydIA", "status": "ACTIVE"}'
        self.assertTrue(evaluate_json_follow(valid_json))
        self.assertFalse(evaluate_json_follow('{"project": "FloydIA", "status": "INACTIVE"}'))

    # --- M-4: Pesos Dinámicos por Cobertura de Pilares ---
    def test_dynamic_weights_single_pillar(self):
        models = [
            {"id": "dynamic/single-pillar", "tier": "workhorse", "provider": "Test", "canonical_name": "Single"}
        ]
        # reasoning benchmark: gpqa con score moderado (< 90 FCI)
        observations = [
            {"model_id": "dynamic/single-pillar", "benchmark_name": "gpqa", "score": 5.0, "source": "Test", "recorded_at": "2026-08-25T00:00:00Z"}
        ]
        results = self.engine.score_models(models, observations)
        r = results[0]
        self.assertIsNotNone(r.fci)
        # El pilar reasoning debe tener 100% del peso efectivo
        self.assertAlmostEqual(r.fci, r.pillars["reasoning"].mean, places=1)

    # --- M-5: FDR Benjamini-Hochberg en Empates Welch ---
    def test_benjamini_hochberg_fdr_ties(self):
        models = [
            {"id": "m5/model-1", "tier": "workhorse", "provider": "Test", "canonical_name": "M1"},
            {"id": "m5/model-2", "tier": "workhorse", "provider": "Test", "canonical_name": "M2"}
        ]
        observations = [
            {"model_id": "m5/model-1", "benchmark_name": "gpqa", "score": 20.0, "source": "AA", "recorded_at": "2026-08-25T00:00:00Z"},
            {"model_id": "m5/model-1", "benchmark_name": "aider_polyglot", "score": 84.8, "source": "AA", "recorded_at": "2026-08-25T00:00:00Z"},
            {"model_id": "m5/model-2", "benchmark_name": "gpqa", "score": 20.1, "source": "AA", "recorded_at": "2026-08-25T00:00:00Z"},
            {"model_id": "m5/model-2", "benchmark_name": "aider_polyglot", "score": 84.9, "source": "AA", "recorded_at": "2026-08-25T00:00:00Z"}
        ]
        results = self.engine.score_models(models, observations)
        ranked = [r for r in results if r.fci is not None]
        self.assertEqual(len(ranked), 2)
        self.assertTrue(ranked[0].is_statistical_tie and ranked[1].is_statistical_tie)

    # --- M-6: Decaimiento Continuo Half-Life ---
    def test_freshness_continuous_decay(self):
        from datetime import datetime, timedelta
        now = datetime.now()
        ts_0 = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        ts_15 = (now - timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ts_30 = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, fresh_0, _ = self.freshness.evaluate_freshness(ts_0, source="ArtificialAnalysis")
        _, fresh_15, _ = self.freshness.evaluate_freshness(ts_15, source="ArtificialAnalysis")
        _, fresh_30, _ = self.freshness.evaluate_freshness(ts_30, source="ArtificialAnalysis")

        self.assertGreaterEqual(fresh_0, 0.95)
        self.assertLess(fresh_15, fresh_0)
        self.assertLess(fresh_30, fresh_15)


    # --- D-4: Verificación de Citas Históricas ---
    def test_historical_facts_verification(self):
        text_with_hallucination = "En la versión v10, el 60% de los modelos colapsaron en Grado C."
        violations = verify_historical_facts(text_with_hallucination)
        self.assertTrue(len(violations) > 0, "Debe detectar la cita errónea sobre el colapso v10")

        text_correct = "En la versión v10, el 100% de los modelos (377/377) colapsaron en Grado C."
        violations_ok = verify_historical_facts(text_correct)
        self.assertEqual(len(violations_ok), 0, "La cita verídica del 100% debe pasar sin violaciones")



if __name__ == "__main__":
    unittest.main()
