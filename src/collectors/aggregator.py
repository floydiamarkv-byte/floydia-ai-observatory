"""
Orquestador de Recolección de Datos de Benchmarks y Rankings de IA.
Ejecuta los recolectores de fuentes públicas y sincroniza el catálogo.
"""

from typing import Dict, Any
from src.collectors.openrouter_collector import OpenRouterCollector
from src.collectors.hf_collector import HuggingFaceCollector
from src.collectors.artificial_analysis import ArtificialAnalysisCollector
from src.collectors.lmsys_collector import LMSYSCollector
from src.collectors.livebench_epoch import LiveBenchEpochCollector
from src.core.normalizer import normalizer


def run_all_collectors() -> Dict[str, int]:
    """Ejecuta todos los recolectores de datos y devuelve el recuento de métricas."""
    print("🚀 [Collectors] Iniciando recolección multidimensional de rankings de IA...")
    
    # 1. Asegurar catálogo canónico
    normalizer.load_mappings()
    
    results = {}
    collectors = [
        OpenRouterCollector(),
        HuggingFaceCollector(),
        ArtificialAnalysisCollector(),
        LMSYSCollector(),
        LiveBenchEpochCollector()
    ]
    
    for c in collectors:
        try:
            count = c.collect()
            results[c.name] = count
        except Exception as e:
            print(f"❌ [Collectors] Error en {c.name}: {e}")
            results[c.name] = 0
            
    print("✨ [Collectors] Recolección completada con éxito.")
    return results
