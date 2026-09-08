"""
src/core/engine_injector.py — Módulo Unificado de Inyección Dinámica y Saneamiento de Motores.
Reescribe y sincroniza configuraciones con escrituras atómicas transaccionales,
backups rotativos .bak y validación sintáctica (Fix V-05, V-18, V-19) para:
- OpenCode Desktop & CLI (~/.config/opencode/opencode.jsonc)
- Hermes Desktop & CLI (~/.hermes/config.yaml + purga de caché)
- DeepSeek Harness DSH (~/.dsh/settings.yaml)
- Sincronización multi-nodo hacia HP45 vía Rsync resiliente.
"""

import os
import json
import time
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Tuple, Optional, Callable
from pathlib import Path
from config.settings import (
    BASE_DIR, GOOGLE_OPENAI_BASE, DEEPSEEK_API_BASE,
    OPENROUTER_API_BASE, NVIDIA_API_BASE, DASHSCOPE_API_BASE,
    MISTRAL_API_BASE, GROQ_API_BASE, Z_AI_API_BASE,
    ZEN_API_BASE, GROKIFIED_API_BASE, GITHUB_MODELS_BASE,
    FIREWORKS_API_BASE
)

WORKSPACE = Path("/home/tec/Dropbox/ANTIGRAVITY_PROJECTS")
OPENCODE_CONFIG = Path(os.path.expanduser("~/.config/opencode/opencode.jsonc"))
HERMES_CONFIG = Path(os.path.expanduser("~/.hermes/config.yaml"))
HERMES_CACHE = Path(os.path.expanduser("~/.hermes/provider_models_cache.json"))
DSH_CONFIG_USER = Path(os.path.expanduser("~/.dsh/settings.yaml"))
DSH_CONFIG_WORKSPACE = WORKSPACE / "SCRIPTS" / "dsh-settings.yaml"
SYNC_HP45_SCRIPT = WORKSPACE / "SCRIPTS" / "sync_models_hp45.sh"


class SecurityError(Exception):
    """Destino de escritura inseguro (p.ej. symlink)."""
    pass


def _validate_json(text: str) -> None:
    """Valida que el contenido sea JSON sintácticamente correcto antes de escribir."""
    json.loads(text)


def _validate_yaml(text: str) -> None:
    """Valida que el contenido sea YAML sintácticamente correcto antes de escribir."""
    try:
        import yaml
        yaml.safe_load(text)
    except ImportError:
        pass


def atomic_write(
    path: Path,
    content: str,
    mode: int = 0o600,
    validator: Optional[Callable[[str], None]] = None,
    keep_backups: int = 3,
) -> Path:
    """
    Escritura transaccional y atómica de configuraciones críticas:
      1. Rechaza symlinks (anti-clobber / anti-escalada).
      2. Crea backup rotativo .<timestamp>.bak antes de modificar.
      3. Valida la sintaxis del contenido ANTES de tocar el destino.
      4. Escribe a archivo temporal en el MISMO directorio + fsync.
      5. os.replace() atómico (POSIX) + chmod 600.
    """
    path = Path(path)

    if path.is_symlink():
        raise SecurityError(f"Destino es un symlink; abortando por seguridad: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        bak = path.with_name(f"{path.name}.{time.strftime('%Y%m%d-%H%M%S')}.bak")
        try:
            shutil.copy2(path, bak)
            backups = sorted(path.parent.glob(f"{path.name}.*.bak"))
            for old in backups[:-keep_backups]:
                old.unlink(missing_ok=True)
        except Exception as e:
            print(f"⚠️ [EngineInjector] No se pudo crear backup de {path}: {e}")

    if validator:
        validator(content)

    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, str(path))
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return path


# Mapeo de proveedores base con metadatos para OpenCode, Hermes y DSH
PROVIDER_METADATA = {
    "google": {
        "npm": "@ai-sdk/google",
        "name": "Google AI Studio Pro",
        "env_key": "C1_GOOGLE_AISTUDIO",
        "base_url": GOOGLE_OPENAI_BASE,
        "dsh_api": "openai-completions"
    },
    "deepseek": {
        "npm": "@ai-sdk/openai",
        "name": "DeepSeek Direct",
        "env_key": "C7_DEEPSEEK",
        "base_url": f"{DEEPSEEK_API_BASE.rstrip('/')}/v1",
        "dsh_api": "openai-completions"
    },
    "openrouter": {
        "npm": "@ai-sdk/openai",
        "name": "OpenRouter Fleet",
        "env_key": "C7_OPENROUTER_OPENCODE_HP15",
        "base_url": OPENROUTER_API_BASE,
        "dsh_api": "openai-completions"
    },
    "nvidia": {
        "npm": "@ai-sdk/openai",
        "name": "NVIDIA NIM",
        "env_key": "C1_NVIDIA",
        "base_url": NVIDIA_API_BASE,
        "dsh_api": "openai-completions"
    },
    "dashscope": {
        "npm": "@ai-sdk/openai",
        "name": "Alibaba DashScope (Qwen)",
        "env_key": "C7_DASHSCOPE_API_KEY",
        "base_url": DASHSCOPE_API_BASE,
        "dsh_api": "openai-completions"
    },
    "mistral": {
        "npm": "@ai-sdk/mistral",
        "name": "Mistral AI Pro",
        "env_key": "C1_MISTRAL",
        "base_url": MISTRAL_API_BASE,
        "dsh_api": "openai-completions"
    },
    "groq": {
        "npm": "@ai-sdk/openai",
        "name": "Groq LPU",
        "env_key": "C1_GROQ",
        "base_url": GROQ_API_BASE,
        "dsh_api": "openai-completions"
    },
    "z_ai": {
        "npm": "@ai-sdk/openai",
        "name": "Z.AI (Zhipu GLM)",
        "env_key": "C1_Z_AI",
        "base_url": Z_AI_API_BASE,
        "dsh_api": "openai-completions"
    },
    "zenmux": {
        "npm": "@ai-sdk/openai",
        "name": "ZenMux Gateway",
        "env_key": "C1_ZEN_OPENCODE",
        "base_url": ZEN_API_BASE,
        "dsh_api": "openai-completions"
    },
    "grokified": {
        "npm": "@ai-sdk/openai",
        "name": "Grokified (xAI)",
        "env_key": "GROKIFIED_API_KEY",
        "base_url": GROKIFIED_API_BASE,
        "dsh_api": "openai-completions"
    },
    "github": {
        "npm": "@ai-sdk/openai",
        "name": "GitHub Models",
        "env_key": "S02_GITHUB_TOKEN_ANTIGRAVITY",
        "base_url": GITHUB_MODELS_BASE,
        "dsh_api": "openai-completions"
    },
    "fireworks": {
        "npm": "@ai-sdk/openai",
        "name": "Fireworks AI",
        "env_key": "C7_FIREWORKS_API_KEY",
        "base_url": FIREWORKS_API_BASE,
        "dsh_api": "openai-completions"
    }
}


def _resolve_default_model(models_by_provider: Dict[str, List[Dict[str, Any]]]) -> Tuple[str, str, str, str]:
    """
    Selecciona el mejor modelo principal y modelo ligero (small) disponible en la flota activa.
    Retorna: (primary_full, small_full, primary_provider, primary_model_id)
    """
    # Prioridad para modelo principal
    primary_candidates = [
        ("google", "gemini-2.5-flash"),
        ("google", "gemini-2.0-flash"),
        ("deepseek", "deepseek-chat"),
        ("openrouter", "deepseek/deepseek-chat"),
        ("openrouter", "google/gemini-2.5-flash"),
        ("openrouter", "qwen/qwen-2.5-coder-32b-instruct:free"),
        ("dashscope", "qwen3.8-max"),
        ("mistral", "codestral-latest")
    ]
    
    # Prioridad para modelo secundario (small / ultra-rápido)
    small_candidates = [
        ("groq", "llama-3.1-8b-instant"),
        ("openrouter", "nvidia/nemotron-3.5-lightning:free"),
        ("google", "gemini-2.0-flash"),
        ("dashscope", "qwen3.8-flash"),
        ("mistral", "ministral-8b-latest"),
        ("z_ai", "glm-4-flash")
    ]

    selected_primary = None
    selected_small = None

    for prov, m_id in primary_candidates:
        if prov in models_by_provider:
            for item in models_by_provider[prov]:
                if item["model_id"] == m_id:
                    selected_primary = (prov, m_id)
                    break
        if selected_primary:
            break

    for prov, m_id in small_candidates:
        if prov in models_by_provider:
            for item in models_by_provider[prov]:
                if item["model_id"] == m_id:
                    selected_small = (prov, m_id)
                    break
        if selected_small:
            break

    # Fallback si ninguno de los candidatos prioritarios está activo
    if not selected_primary and models_by_provider:
        first_prov = next(iter(models_by_provider))
        first_model = models_by_provider[first_prov][0]["model_id"]
        selected_primary = (first_prov, first_model)

    if not selected_small and models_by_provider:
        selected_small = selected_primary

    p_prov, p_mid = selected_primary if selected_primary else ("google", "gemini-2.5-flash")
    s_prov, s_mid = selected_small if selected_small else ("openrouter", "nvidia/nemotron-3.5-lightning:free")

    return f"{p_prov}/{p_mid}", f"{s_prov}/{s_mid}", p_prov, p_mid


def apply_engine_configurations(
    selected_models: Optional[List[Dict[str, Any]]] = None
) -> List[Tuple[str, str]]:
    """
    Reescribe las configuraciones de OpenCode, Hermes y DSH con escrituras atómicas.
    Si se suministra `selected_models`, inyecta ÚNICAMENTE dichos modelos/proveedores.
    """
    logs = []

    # Si no se pasan modelos explícitos, recuperar del escaneo profundo o catálogo DB
    if selected_models is None:
        try:
            from src.probers.deep_probe_scanner import get_latest_deep_scan_results
            latest = get_latest_deep_scan_results()
            selected_models = [m for m in latest if m.get("is_functional") or m.get("classification") == "RESPUESTA_OK"]
        except Exception:
            selected_models = []

    # Si aún está vacío, usar un conjunto curado seguro de respaldo
    if not selected_models:
        selected_models = [
            {"provider_id": "google", "model_id": "gemini-2.5-flash", "canonical_name": "[1M•Free] Gemini 2.5 Flash", "context_window": 1048576, "is_free_tier": True},
            {"provider_id": "deepseek", "model_id": "deepseek-chat", "canonical_name": "[128k•Paid] DeepSeek Chat V3", "context_window": 131072, "is_free_tier": False},
            {"provider_id": "openrouter", "model_id": "qwen/qwen-2.5-coder-32b-instruct:free", "canonical_name": "[128k•Free] Qwen 2.5 Coder 32B", "context_window": 131072, "is_free_tier": True},
            {"provider_id": "openrouter", "model_id": "nvidia/nemotron-3.5-lightning:free", "canonical_name": "[262k•Free] Nemotron 3.5 Lightning", "context_window": 262144, "is_free_tier": True},
            {"provider_id": "groq", "model_id": "llama-3.3-70b-versatile", "canonical_name": "[128k•Free] Llama 3.3 70B", "context_window": 131072, "is_free_tier": True},
            {"provider_id": "groq", "model_id": "llama-3.1-8b-instant", "canonical_name": "[128k•Free] Llama 3.1 8B Instant", "context_window": 131072, "is_free_tier": True}
        ]

    # Agrupar modelos por provider_id
    models_by_prov: Dict[str, List[Dict[str, Any]]] = {}
    for m in selected_models:
        p_id = m.get("provider_id") or "openrouter"
        p_id = p_id.lower().replace("-", "_").split(" ")[0].split("[")[0]
        if p_id not in models_by_prov:
            models_by_prov[p_id] = []
        
        # Evitar duplicados por model_id dentro del mismo proveedor
        if not any(x["model_id"] == m["model_id"] for x in models_by_prov[p_id]):
            models_by_prov[p_id].append(m)

    primary_full, small_full, prim_prov, prim_mid = _resolve_default_model(models_by_prov)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. OpenCode (~/.config/opencode/opencode.jsonc)
    # ──────────────────────────────────────────────────────────────────────────
    opencode_providers = {}
    for p_id, m_list in models_by_prov.items():
        meta = PROVIDER_METADATA.get(p_id)
        if not meta:
            continue

        prov_models = {}
        for m in m_list:
            mid = m["model_id"]
            cname = m.get("canonical_name") or mid
            ctx = m.get("context_window", 128000)
            ctx_str = f"{int(ctx/1000)}k" if ctx < 1000000 else "1M"
            cost_tag = "Free" if m.get("is_free_tier") else "Paid"
            disp_name = f"[{ctx_str}•{cost_tag}] {cname}" if "[" not in cname else cname
            prov_models[mid] = {"name": disp_name}

        if p_id == "google":
            opencode_providers[p_id] = {
                "npm": "@ai-sdk/google",
                "name": meta["name"],
                "options": {"apiKey": f"{{env:{meta['env_key']}}}"},
                "models": prov_models
            }
        else:
            opencode_providers[p_id] = {
                "npm": "@ai-sdk/openai",
                "name": meta["name"],
                "options": {
                    "baseURL": meta["base_url"],
                    "apiKey": f"{{env:{meta['env_key']}}}"
                },
                "models": prov_models
            }

    opencode_cfg = {
        "$schema": "https://opencode.ai/config.json",
        "model": primary_full,
        "small_model": small_full,
        "provider": opencode_providers
    }

    try:
        content_json = json.dumps(opencode_cfg, indent=2, ensure_ascii=False)
        atomic_write(OPENCODE_CONFIG, content_json, validator=_validate_json)
        total_oc_models = sum(len(p["models"]) for p in opencode_providers.values())
        logs.append((f"✅ OpenCode configurado ({len(opencode_providers)} proveedores, {total_oc_models} modelos OK): {OPENCODE_CONFIG}", "SUCCESS"))
    except Exception as e:
        logs.append((f"❌ Error configurando OpenCode: {e}", "ERROR"))

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Hermes Agent CLI & Desktop (~/.hermes/config.yaml & cache)
    # ──────────────────────────────────────────────────────────────────────────
    hermes_providers_yaml = []
    hermes_cache_providers = {}

    for p_id, m_list in models_by_prov.items():
        meta = PROVIDER_METADATA.get(p_id)
        if not meta:
            continue

        model_ids = [m["model_id"] for m in m_list]
        hermes_cache_providers[p_id] = {
            "name": meta["name"],
            "models": model_ids,
            "base_url": meta["base_url"]
        }

        m_lines = "\n".join([f"      - {mid}" for mid in model_ids])
        hermes_providers_yaml.append(f"""  {p_id}:
    name: "{meta['name']}"
    env_key: {meta['env_key']}
    base_url: "{meta['base_url']}"
    api: openai-completions
    models:
{m_lines}""")

    prim_meta = PROVIDER_METADATA.get(prim_prov, PROVIDER_METADATA["google"])
    hermes_yaml_content = f"""model:
  default: "{prim_mid}"
  provider: "{prim_prov}"
  base_url: "{prim_meta['base_url']}"
providers:
""" + "\n".join(hermes_providers_yaml) + "\n"

    try:
        atomic_write(HERMES_CONFIG, hermes_yaml_content, validator=_validate_yaml)
        # Escribir caché de modelos Hermes
        cache_content = json.dumps({
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "providers": hermes_cache_providers
        }, indent=2)
        atomic_write(HERMES_CACHE, cache_content, validator=_validate_json)
        logs.append((f"✅ Hermes Agent configurado ({len(hermes_providers_yaml)} proveedores OK): {HERMES_CONFIG}", "SUCCESS"))
    except Exception as e:
        logs.append((f"❌ Error configurando Hermes: {e}", "ERROR"))

    # ──────────────────────────────────────────────────────────────────────────
    # 3. DeepSeek Harness DSH (~/.dsh/settings.yaml)
    # ──────────────────────────────────────────────────────────────────────────
    dsh_providers_yaml = []
    for p_id, m_list in models_by_prov.items():
        meta = PROVIDER_METADATA.get(p_id)
        if not meta:
            continue

        model_entries = []
        for m in m_list:
            mid = m["model_id"]
            cname = m.get("canonical_name") or mid
            ctx = m.get("context_window", 131072)
            model_entries.append(f"""        - id: "{mid}"
          name: "{cname}"
          contextWindow: {ctx}""")

        models_block = "\n".join(model_entries)
        dsh_providers_yaml.append(f"""    {p_id}:
      api: {meta['dsh_api']}
      displayName: "{meta['name']}"
      apiKeyEnv: {meta['env_key']}
      baseURL: "{meta['base_url']}"
      models:
{models_block}""")

    dsh_yaml_content = f"""version: 2
default_provider: "{prim_prov}"
default_model: "{prim_mid}"
theme: dark
providers:
""" + "\n".join(dsh_providers_yaml) + "\n"

    try:
        atomic_write(DSH_CONFIG_USER, dsh_yaml_content, validator=_validate_yaml)
        atomic_write(DSH_CONFIG_WORKSPACE, dsh_yaml_content, validator=_validate_yaml)
        logs.append((f"✅ DeepSeek Harness sincronizado ({len(dsh_providers_yaml)} proveedores OK): {DSH_CONFIG_USER}", "SUCCESS"))
    except Exception as e:
        logs.append((f"❌ Error configurando DSH: {e}", "ERROR"))

    return logs


def sync_to_hp45() -> Tuple[str, str]:
    """Sincroniza las configuraciones saneadas hacia el nodo secundario HP45 con tolerancia a fallos."""
    if not SYNC_HP45_SCRIPT.exists():
        return (f"⚠️ Script de sincronización no encontrado: {SYNC_HP45_SCRIPT}", "WARN")

    cmd = ["bash", str(SYNC_HP45_SCRIPT), "hp45", "tec"]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=25,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/home/tec")}
        )
        if res.returncode == 0:
            return ("✅ Sincronización resiliente completada exitosamente hacia HP45 (192.168.1.200).", "SUCCESS")
        return (f"⚠️ Rsync finalizado con advertencias: {res.stdout.strip()[:150]}", "WARN")
    except subprocess.TimeoutExpired:
        return ("⚠️ Timeout conectando a HP45 (nodo portátil apagado o fuera de red).", "WARN")
    except Exception as e:
        return (f"❌ Error en sincronización a HP45: {e}", "ERROR")
