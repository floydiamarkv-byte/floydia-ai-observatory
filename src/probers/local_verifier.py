"""
Orquestador Principal de Verificación de APIs Locales.
Ejecuta todas las sondas de APIs configuradas en el equipo en paralelo mediante ThreadPoolExecutor
y persiste los resultados en SQLite con saneamiento de secretos.
Soporta: Google AI Studio, DeepSeek, OpenRouter, NVIDIA NIM, Mistral AI, Groq LPU, Fireworks AI, GitHub Models, Hermes.
"""

from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.probers.google_prober import probe_google_ai_studio
from src.probers.deepseek_prober import probe_deepseek
from src.probers.openrouter_prober import probe_openrouter
from src.probers.hermes_prober import probe_hermes_endpoint
from src.probers.nvidia_prober import probe_nvidia_nim
from src.probers.mistral_prober import probe_mistral
from src.probers.groq_prober import probe_groq
from src.probers.fireworks_prober import probe_fireworks
from src.probers.github_prober import probe_github_models
from src.core.db import record_local_api_check, get_latest_local_verified_models


PROBER_FUNCS = [
    probe_google_ai_studio,
    probe_deepseek,
    probe_groq,
    probe_github_models,
    probe_fireworks,
    probe_nvidia_nim,
    probe_mistral,
    probe_openrouter,
    probe_hermes_endpoint,
]


def run_local_api_probes() -> List[Dict[str, Any]]:
    """Ejecuta la batería de comprobaciones en vivo de todas las APIs locales en paralelo."""
    print("🔍 [Local Verifier] Escaneando y verificando APIs configuradas en tu PC (Paralelo)...")
    all_results = []

    with ThreadPoolExecutor(max_workers=min(9, len(PROBER_FUNCS))) as executor:
        future_to_name = {executor.submit(p): p.__name__ for p in PROBER_FUNCS}
        for future in as_completed(future_to_name):
            p_name = future_to_name[future]
            try:
                checks = future.result()
                if isinstance(checks, list):
                    for c in checks:
                        record_local_api_check(c)
                        all_results.append(c)
            except Exception as e:
                print(f"⚠️ [Local Verifier] Sonda {p_name} falló: {e}")

    verified_count = sum(1 for c in all_results if c.get("is_functional"))
    print(f"✅ [Local Verifier] {verified_count}/{len(all_results)} APIs locales verificadas y activas.")
    return all_results
