"""
Orquestador de Recolección de Datos de Benchmarks y Rankings de IA v9.0.
Ejecuta los 8 recolectores de fuentes públicas y sincroniza el catálogo.
"""

from typing import Dict, Any
from src.collectors.openrouter_collector import OpenRouterCollector
from src.collectors.hf_collector import HuggingFaceCollector
from src.collectors.artificial_analysis import ArtificialAnalysisCollector
from src.collectors.lmsys_collector import LMSYSCollector
from src.collectors.livebench_epoch import LiveBenchEpochCollector
from src.collectors.arena_collector import ArenaCollector
from src.collectors.swebench_collector import SWEBenchCollector
from src.collectors.aider_collector import AiderCollector
from src.core.normalizer import normalizer


def run_all_collectors() -> Dict[str, int]:
    """Ejecuta todos los recolectores de datos y devuelve el recuento de métricas."""
    print("🚀 [Collectors] Iniciando recolección multidimensional de rankings de IA (8 fuentes)...")
    
    # 1. Asegurar catálogo canónico
    normalizer.load_mappings()
    
    results = {}
    collectors = [
        OpenRouterCollector(),       # Catálogo + precios en vivo
        HuggingFaceCollector(),      # MMLU-Pro, GPQA, MATH, IFEval
        ArtificialAnalysisCollector(), # Velocidad, latencia, quality index
        LMSYSCollector(),            # Elo de preferencia humana (HF dataset)
        ArenaCollector(),            # Arena.ai Elo general + coding (API comunitaria)
        LiveBenchEpochCollector(),   # LiveBench + Epoch AI (razonamiento y ciencia)
        SWEBenchCollector(),         # SWE-bench Verified (resolución de issues)
        AiderCollector(),            # Aider Polyglot (coding multi-lenguaje)
    ]
    
    for c in collectors:
        try:
            count = c.collect()
            results[c.name] = count
        except Exception as e:
            print(f"❌ [Collectors] Error en {c.name}: {e}")
            results[c.name] = 0
            
    total = sum(results.values())
    print(f"✨ [Collectors] Recolección completada: {total} métricas de {len(results)} fuentes.")
    return results
