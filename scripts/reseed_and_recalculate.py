#!/usr/bin/env python3
"""
Script maestro de re-ingestión y recalibración de FCI V3 con datos reales de Arena.ai (Agosto 2026).
"""

import os
import sys
import sqlite3
from pathlib import Path

# Configurar path
OBS_ROOT = Path("/home/tec/Dropbox/ANTIGRAVITY_PROJECTS/FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY")
sys.path.insert(0, str(OBS_ROOT))

from src.core.db import init_db
from src.core.normalizer import normalizer
from src.collectors.openrouter_collector import OpenRouterCollector
from src.collectors.hf_collector import HuggingFaceCollector
from src.collectors.arena_collector import ArenaCollector
from src.collectors.livebench_epoch import LiveBenchEpochCollector
from src.collectors.swebench_collector import SWEBenchCollector
from src.collectors.aider_collector import AiderCollector
from src.collectors.livecodebench_collector import LiveCodeBenchCollector
from src.collectors.artificial_analysis import ArtificialAnalysisCollector
from src.core.ranking_engine_v3 import ranking_engine_v3

def main():
    print("=" * 60)
    print("⚡ FLOYDIA OBSERVATORY: RE-SEED & RECALCULATE V3")
    print("=" * 60)

    db_path = OBS_ROOT / "data" / "rankings_engine.db"
    
    # 1. Limpiar evaluaciones y catálogo para evitar duplicados históricos y huérfanos
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM evaluations")
        c.execute("DELETE FROM models")
        conn.commit()
        conn.close()
        print("🧹 Tablas 'evaluations' y 'models' limpiadas para ingesta fresca.")

    # 2. Inicializar DB y recargar normalizador
    init_db()
    normalizer.canonical_models.clear()
    normalizer.alias_to_id.clear()
    normalizer.normalized_alias_to_id.clear()
    normalizer.load_mappings()
    print(f"📦 Mapeos canónicos cargados: {len(normalizer.canonical_models)} modelos.")

    # 3. Ejecutar collectors completos (9 fuentes)
    c_openrouter = OpenRouterCollector()
    n_openrouter = c_openrouter.collect()

    c_hf = HuggingFaceCollector()
    n_hf = c_hf.collect()

    c_arena = ArenaCollector()
    n_arena = c_arena.collect()

    c_lb = LiveBenchEpochCollector()
    n_lb = c_lb.collect()

    c_swe = SWEBenchCollector()
    n_swe = c_swe.collect()

    c_aider = AiderCollector()
    n_aider = c_aider.collect()

    c_lcb = LiveCodeBenchCollector()
    n_lcb = c_lcb.collect()

    c_aa = ArtificialAnalysisCollector()
    n_aa = c_aa.collect()

    print(f"\n📊 Total Ingestado: OpenRouter={n_openrouter}, HF={n_hf}, Arena={n_arena}, LiveBench/Epoch={n_lb}, SWE={n_swe}, Aider={n_aider}, LCB={n_lcb}, AA={n_aa}")

    # 4. Calcular rankings multidimensionales V11
    from src.core.scoring import calculate_multidimensional_rankings
    from src.reports.markdown_report import generate_daily_markdown_report
    from src.core.db import get_latest_local_verified_models

    scored_models = calculate_multidimensional_rankings()
    local_apis = get_latest_local_verified_models()

    print("\n" + "=" * 60)
    print("🏆 TOP 15 RANKING GLOBAL FCI V11 (Agosto 2026):")
    print("=" * 60)
    for m in scored_models[:15]:
        print(f"#{m['global_rank']:02d} | {m['id']:<28} | FCI: {m['intelligence_score']:5.2f} | IC 95%: {m['ci_display']:<14} | Conf: {m['confidence_score']:4.2f} ({m['evidence_grade']}) | Tier: {m.get('tier', 'N/A')}")

    print("\nPosición de Gemini 2.5 Pro vs Gemini 3.7 Flash:")
    for m in scored_models:
        if m["id"] in ("gemini-2.5-pro", "gemini-3.7-flash-high", "gemini-3-pro", "gemini-2.5-flash", "claude-opus-5-high", "kimi-k3-max"):
            print(f"  -> #{m['global_rank']:02d} {m['id']:<25} | FCI: {m['intelligence_score']:5.2f} | IC: {m['ci_display']}")

    # 5. Generar informe diario V11 en Markdown
    report_file = generate_daily_markdown_report(scored_models, local_apis)
    print(f"📄 [Recalculate V11] Informe generado exitosamente: {report_file}")

if __name__ == "__main__":
    main()
