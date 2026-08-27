"""
Tests unitarios para el normalizador y resolución de entidades canónicas (10 Categorías v9.5).
"""

import unittest
from src.core.normalizer import normalizer


class TestModelNormalizer(unittest.TestCase):
    def setUp(self):
        normalizer.load_mappings()

    def test_resolve_gemini(self):
        can_id, m = normalizer.resolve("gemini-2.5-flash")
        self.assertEqual(can_id, "gemini-2.5-flash")
        self.assertEqual(m["tier"], "long_context")
        self.assertEqual(m["provider"], "Google")

    def test_resolve_deepseek_r1(self):
        can_id_r1, m_r1 = normalizer.resolve("deepseek/deepseek-r1:free")
        self.assertEqual(can_id_r1, "deepseek-reasoner")
        self.assertEqual(m_r1["tier"], "reasoning")

    def test_resolve_claude(self):
        can_id_claude, m_claude = normalizer.resolve("claude-3-7-sonnet-20250219")
        self.assertEqual(can_id_claude, "claude-3-7-sonnet")
        self.assertEqual(m_claude["tier"], "agentic")


if __name__ == "__main__":
    unittest.main()
