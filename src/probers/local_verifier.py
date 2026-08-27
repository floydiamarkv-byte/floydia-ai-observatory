"""
Orquestador Principal de Verificación de APIs Locales.
Ejecuta todas las sondas de APIs configuradas en el equipo y persiste los resultados en SQLite.
Soporta: Google AI Studio, DeepSeek, OpenRouter, NVIDIA NIM, Mistral AI, Groq LPU, Fireworks AI, GitHub Models, Hermes.
"""

from typing import Dict, Any, List
from src.probers.scanner import scan_configured_providers
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


def run_local_api_probes() -> List[Dict[str, Any]]:
    """Ejecuta la batería de comprobaciones en vivo de todas las APIs locales."""
    print("🔍 [Local Verifier] Escaneando y verificando APIs configuradas en tu PC...")
    all_results = []

    # 1. Google AI Studio (OpenAI Compatible)
    google_checks = probe_google_ai_studio()
    for c in google_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 2. DeepSeek Direct
    deepseek_checks = probe_deepseek()
    for c in deepseek_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 3. Groq LPU (Ultra-rápido)
    groq_checks = probe_groq()
    for c in groq_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 4. GitHub Models (Azure AI Inference)
    github_checks = probe_github_models()
    for c in github_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 5. Fireworks AI
    fireworks_checks = probe_fireworks()
    for c in fireworks_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 6. NVIDIA NIM
    nvidia_checks = probe_nvidia_nim()
    for c in nvidia_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 7. Mistral AI
    mistral_checks = probe_mistral()
    for c in mistral_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 8. OpenRouter Fleet
    openrouter_checks = probe_openrouter()
    for c in openrouter_checks:
        record_local_api_check(c)
        all_results.append(c)

    # 9. Hermes
    hermes_checks = probe_hermes_endpoint()
    for c in hermes_checks:
        record_local_api_check(c)
        all_results.append(c)

    verified_count = sum(1 for c in all_results if c.get("is_functional"))
    print(f"✅ [Local Verifier] {verified_count}/{len(all_results)} APIs locales verificadas y activas.")
    return all_results
