"""
Tests unitarios para el normalizador y resolución de entidades.
"""

from src.core.normalizer import normalizer


def test_resolve_canonical_models():
    # 1. Gemini Flash
    can_id, m = normalizer.resolve("gemini-2.5-flash")
    assert can_id == "gemini-2.5-flash"
    assert m["tier"] == "workhorse"
    assert m["provider"] == "Google"

    # 2. DeepSeek R1
    can_id_r1, m_r1 = normalizer.resolve("deepseek/deepseek-r1:free")
    assert can_id_r1 == "deepseek-reasoner"
    assert m_r1["tier"] == "frontier"

    # 3. Claude 3.7
    can_id_claude, m_claude = normalizer.resolve("claude-3-7-sonnet-20250219")
    assert can_id_claude == "claude-3-7-sonnet"
    assert m_claude["tier"] == "frontier"

    print("✅ test_resolve_canonical_models PASSED")


if __name__ == "__main__":
    test_resolve_canonical_models()
