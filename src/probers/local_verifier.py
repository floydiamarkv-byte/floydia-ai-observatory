"""
Orquestador Principal de Verificación de APIs Locales (Async & Concurrency Hardened).
Ejecuta todas las sondas de APIs configuradas en el equipo concurrentemente mediante asyncio / thread-pool acotado,
persiste los resultados en SQLite con saneamiento de secretos y dispara detección de drift de latencias.
Soporta: Google AI Studio, OpenCode Zen, Z.AI (Zhipu), Grokified (xAI), Alibaba DashScope,
DeepSeek, OpenRouter, NVIDIA NIM, Mistral AI, Groq LPU, Fireworks AI, GitHub Models, Hermes.
"""

import re
import asyncio
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from src.probers.google_prober import probe_google_ai_studio
from src.probers.zen_prober import probe_opencode_zen
from src.probers.zai_prober import probe_z_ai
from src.probers.grokified_prober import probe_grokified
from src.probers.dashscope_prober import probe_dashscope
from src.probers.deepseek_prober import probe_deepseek
from src.probers.openrouter_prober import probe_openrouter
from src.probers.hermes_prober import probe_hermes_endpoint
from src.probers.nvidia_prober import probe_nvidia_nim
from src.probers.mistral_prober import probe_mistral
from src.probers.groq_prober import probe_groq
from src.probers.fireworks_prober import probe_fireworks
from src.probers.github_prober import probe_github_models
from src.core.db import record_local_api_check, get_latest_local_verified_models
from src.core.drift_detector import drift_detector
from config.settings import resolve_account_email, ACCOUNT_LABELS

MAX_CONCURRENT_PROBERS = 12

PROBER_FUNCS = [
    probe_google_ai_studio,
    probe_opencode_zen,
    probe_z_ai,
    probe_grokified,
    probe_dashscope,
    probe_deepseek,
    probe_groq,
    probe_github_models,
    probe_fireworks,
    probe_nvidia_nim,
    probe_mistral,
    probe_openrouter,
    probe_hermes_endpoint,
]

# Mapeo proveedor → variable env default
_PROVIDER_DEFAULT_KEYS = {
    "Google AI Studio": "C1_GOOGLE_AISTUDIO",
    "OpenCode Zen": "C1_ZEN_OPENCODE",
    "Z.AI (Zhipu)": "C1_Z_AI",
    "Grokified (xAI)": "GROKIFIED_API_KEY",
    "Alibaba DashScope": "C7_DASHSCOPE_API_KEY",
    "DeepSeek Direct": "C1_DEEPSEEK",
    "DeepSeek": "C1_DEEPSEEK",
    "OpenRouter Free": "C7_OPENROUTER_OPENCODE_HP15",
    "OpenRouter": "C7_OPENROUTER_OPENCODE_HP15",
    "NVIDIA NIM": "C7_NVIDIA",
    "Mistral AI Pro": "C1_MISTRAL",
    "Mistral AI": "C1_MISTRAL",
    "Groq LPU": "C1_GROQ",
    "Groq": "C1_GROQ",
    "Fireworks AI": "C7_FIREWORKS_API_KEY",
    "GitHub Models": "S02_GITHUB_TOKEN_ANTIGRAVITY",
    "Hermes (Local)": "C1_GOOGLE_AISTUDIO",
}

_BRACKET_RX = re.compile(r"\[(\w+)\]")


def _inject_account_email(check: Dict[str, Any]) -> Dict[str, Any]:
    """Inyecta el campo account_email en un resultado de sonda basándose en provider_name."""
    if check.get("account_email"):
        return check

    prov = check.get("provider_name", "")
    m = _BRACKET_RX.search(prov)
    if m:
        env_key = m.group(1)
        check["account_email"] = resolve_account_email(env_key)
        check["account_key"] = env_key
        return check

    for provider_base, default_key in _PROVIDER_DEFAULT_KEYS.items():
        if prov.startswith(provider_base):
            check["account_email"] = resolve_account_email(default_key)
            check["account_key"] = default_key
            return check

    check["account_email"] = "—"
    check["account_key"] = ""
    return check


async def _execute_prober_async(prober_func, semaphore: asyncio.Semaphore, loop) -> List[Dict[str, Any]]:
    """Ejecuta una función de sonda dentro de un semáforo acotado."""
    async with semaphore:
        try:
            results = await loop.run_in_executor(None, prober_func)
            return results if isinstance(results, list) else []
        except Exception as e:
            print(f"⚠️ [Local Verifier] Sonda {prober_func.__name__} falló: {e}")
            return []


async def run_local_api_probes_async() -> List[Dict[str, Any]]:
    """Ejecuta todas las sondas locales concurrentemente con asyncio y semáforos."""
    print("🔍 [Local Verifier] Escaneando y verificando APIs configuradas en tu PC (Async Concurrente)...")
    loop = asyncio.get_running_loop()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PROBERS)

    tasks = [_execute_prober_async(p, semaphore, loop) for p in PROBER_FUNCS]
    results_nested = await asyncio.gather(*tasks, return_exceptions=False)

    all_results = []
    for checks in results_nested:
        for c in checks:
            _inject_account_email(c)
            record_local_api_check(c)
            
            # Chequeo de drift de latencia en tiempo real
            if c.get("is_functional") and c.get("latency_ms"):
                model_id = c.get("canonical_id") or c.get("model_identifier")
                prov = c.get("provider_name", "Unknown")
                drift_detector.detect_latency_drift(model_id, prov, c["latency_ms"])
                
            all_results.append(c)

    verified_count = sum(1 for c in all_results if c.get("is_functional"))
    print(f"✅ [Local Verifier] {verified_count}/{len(all_results)} APIs locales verificadas y activas.")
    return all_results


def run_local_api_probes() -> List[Dict[str, Any]]:
    """
    Wrapper síncrono para ejecutar las sondas en cualquier contexto (CLI, GUI, scripts).
    Detecta si ya existe un event loop activo o crea uno nuevo.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si ya hay un event loop corriendo (ej. FastAPI o Jupyter), usar ThreadPool
            with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT_PROBERS, len(PROBER_FUNCS))) as executor:
                futures = [executor.submit(p) for p in PROBER_FUNCS]
                all_results = []
                for f in futures:
                    try:
                        checks = f.result()
                        if isinstance(checks, list):
                            for c in checks:
                                _inject_account_email(c)
                                record_local_api_check(c)
                                if c.get("is_functional") and c.get("latency_ms"):
                                    drift_detector.detect_latency_drift(c.get("canonical_id") or c.get("model_identifier"), c.get("provider_name", ""), c["latency_ms"])
                                all_results.append(c)
                    except Exception as e:
                        print(f"⚠️ [Local Verifier] Sonda falló: {e}")
                verified_count = sum(1 for c in all_results if c.get("is_functional"))
                print(f"✅ [Local Verifier] {verified_count}/{len(all_results)} APIs locales verificadas y activas.")
                return all_results
        else:
            return loop.run_until_complete(run_local_api_probes_async())
    except RuntimeError:
        return asyncio.run(run_local_api_probes_async())
