"""
Tests unitarios para el exportador de snapshots para IAs Frontier.
"""

from src.analyst.frontier_exporter import export_daily_snapshot_for_frontier_ai


def test_export_frontier_snapshot():
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
            "workhorse_score": 88.0,
            "coding_score": 85.0,
            "preference_score": 86.2,
            "is_local_active": True,
            "local_latency_ms": 120.5,
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
            "workhorse_score": 70.0,
            "coding_score": 96.0,
            "preference_score": 98.0,
            "is_local_active": False,
            "local_latency_ms": None,
            "global_rank": 2
        }
    ]

    out_file = export_daily_snapshot_for_frontier_ai(mock_rankings, [])
    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FLOYDIA AI BENCHMARKS & LOCAL APIS" in content
    assert "ARSENAL LOCAL" in content
    assert "Google Gemini 2.5 Flash" in content
    assert "RADAR GLOBAL" in content
    assert "Anthropic Claude 3.7 Sonnet" in content

    print("✅ test_export_frontier_snapshot PASSED")


if __name__ == "__main__":
    test_export_frontier_snapshot()
