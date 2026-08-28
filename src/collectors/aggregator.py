"""
Orquestador de Recolección de Datos de Benchmarks y Rankings de IA v10.0.
Ejecuta los 9 recolectores de fuentes públicas y sincroniza el catálogo.
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
from src.collectors.livecodebench_collector import LiveCodeBenchCollector
from src.core.normalizer import normalizer


def run_all_collectors() -> Dict[str, int]:
    """Ejecuta todos los recolectores de datos y devuelve el recuento de métricas."""
    print("🚀 [Collectors] Iniciando recolección multidimensional de rankings de IA (9 fuentes)...")
    
    # 1. Asegurar catálogo canónico
    normalizer.load_mappings()
    
    results = {}
    collectors = [
        OpenRouterCollector(),         # SSOT Catálogo + precios en vivo
        HuggingFaceCollector(),        # SSOT Benchmarks académicos (MMLU-Pro, GPQA, MATH, IFEval)
        ArtificialAnalysisCollector(), # SSOT Velocidad, latencia, quality index
        LMSYSCollector(),              # SSOT Elo de preferencia humana (HF dataset)
        ArenaCollector(),              # Arena.ai Elo general + WebDev coding (API comunitaria)
        LiveBenchEpochCollector(),     # LiveBench + Epoch AI (razonamiento y ciencia no contaminados)
        SWEBenchCollector(),           # SWE-bench Verified (resolución real de issues de GitHub)
        AiderCollector(),              # Aider Polyglot (coding multi-lenguaje)
        LiveCodeBenchCollector(),      # LiveCodeBench (evaluación holística de código no contaminada)
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

