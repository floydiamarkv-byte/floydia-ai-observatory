"""
Módulo Unificado de Inyección y Saneamiento de Motores de FloydIA.
Reescribe y sincroniza configuraciones con escrituras atómicas transaccionales,
backups rotativos .bak y validación sintáctica (Fix V-05, V-18, V-19) para:
- OpenCode Desktop & CLI (~/.config/opencode/opencode.jsonc)
- Hermes Desktop & CLI (~/.hermes/config.yaml + purga de caché)
- DeepSeek Harness DSH (~/.dsh/settings.yaml)
- Sincronización multi-nodo hacia HP45 vía Rsync.
"""

import os
import json
import time
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Tuple, Optional, Callable
from pathlib import Path
from config.settings import BASE_DIR

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
        # Fallback si PyYAML no está instalado en el entorno mínimo
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


def apply_engine_configurations() -> List[Tuple[str, str]]:
    """
    Reescribe las configuraciones de OpenCode, Hermes y DSH con los modelos más recientes
    y comprobados de la flota de FloydIA de forma atómica. Retorna lista de mensajes (mensaje, nivel).
    """
    logs = []

    # 1. OpenCode (~/.config/opencode/opencode.jsonc)
    opencode_cfg = {
        "$schema": "https://opencode.ai/config.json",
        "model": "google/gemini-3.6-flash",
        "small_model": "openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "provider": {
            "google": {
                "npm": "@ai-sdk/google",
                "name": "Google AI Studio Pro",
                "options": {"apiKey": "{env:C1_GOOGLE_AISTUDIO}"},
                "models": {
                    "gemini-3.7-flash": {"name": "[1M•Pro] Gemini 3.7 (Reasoning)"},
                    "gemini-3.6-flash": {"name": "[1M•Pro] Gemini 3.6 (Fast)"},
                    "gemini-3.5-flash": {"name": "[1M•Pro] Gemini 3.5 (Multi)"},
                    "gemma-4-31b-it": {"name": "[262k•Pro] Gemma 4 31B (Agent)"}
                }
            },
            "mistral": {
                "npm": "@ai-sdk/mistral",
                "name": "Mistral AI Pro",
                "options": {"apiKey": "{env:C1_MISTRAL}"},
                "models": {
                    "codestral-latest": {"name": "[256k•Trial] Codestral (Code)"}
                }
            },
            "openrouter": {
                "npm": "@ai-sdk/openai",
                "name": "OpenRouter Free",
                "options": {
                    "baseURL": "https://openrouter.ai/api/v1",
                    "apiKey": "{env:C7_OPENROUTER_OPENCODE_HP15}"
                },
                "models": {
                    "openrouter/auto": {"name": "[Auto•Free] OpenRouter Auto"},
                    "openrouter/free": {"name": "[Auto•Free] OpenRouter Free"},
                    "minimax/minimax-m3:free": {"name": "[1M•Free] MiniMax M3 (Frontier)"},
                    "nvidia/nemotron-3-super-120b-a12b:free": {"name": "[262k•Free] Nemotron 3 Super"},
                    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": {"name": "[256k•Free] Nemotron 3 Nano"},
                    "z-ai/glm-5.2:free": {"name": "[256k•Free] GLM 5.2 (Frontier)"},
                    "poolside/laguna-s-2.1:free": {"name": "[262k•Free] Laguna S 2.1 (Code)"}
                }
            },
            "nvidia": {
                "npm": "@ai-sdk/openai",
                "name": "NVIDIA NIM",
                "options": {
                    "baseURL": "https://integrate.api.nvidia.com/v1",
                    "apiKey": "{env:C7_NVIDIA}"
                },
                "models": {
                    "deepseek-ai/deepseek-v4-flash-0731": {"name": "[256k•Trial] DeepSeek V4 (NIM)"},
                    "moonshotai/kimi-k3": {"name": "[256k•Trial] Kimi K3 (NIM)"},
                    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": {"name": "[256k•Trial] Nemotron 3 Nano (NIM)"}
                }
            },
            "deepseek": {
                "npm": "@ai-sdk/openai",
                "name": "DeepSeek Direct",
                "options": {
                    "baseURL": "https://api.deepseek.com/v1",
                    "apiKey": "{env:DEEPSEEK_API_KEY}"
                },
                "models": {
                    "deepseek-chat": {"name": "[128k•Paid] DeepSeek Chat V3"},
                    "deepseek-reasoner": {"name": "[64k•Paid] DeepSeek Reasoner R1"}
                }
            }
        }
    }

    try:
        content_json = json.dumps(opencode_cfg, indent=2, ensure_ascii=False)
        atomic_write(OPENCODE_CONFIG, content_json, validator=_validate_json)
        logs.append((f"✅ OpenCode configurado (atómico): {OPENCODE_CONFIG}", "SUCCESS"))
    except Exception as e:
        logs.append((f"❌ Error configurando OpenCode: {e}", "ERROR"))

    # 2. Hermes (~/.hermes/config.yaml)
    hermes_yaml = """model:
  default: gemini-3.6-flash
  provider: google
  base_url: https://generativelanguage.googleapis.com/v1beta/openai/
providers:
  google:
    name: Google AI Studio Pro
    env_key: C1_GOOGLE_AISTUDIO
    base_url: https://generativelanguage.googleapis.com/v1beta/openai/
    api: openai-completions
    models:
      - gemini-3.7-flash
      - gemini-3.6-flash
      - gemini-3.5-flash
      - gemma-4-31b-it
  openrouter:
    name: OpenRouter Free
    env_key: C7_OPENROUTER_OPENCODE_HP15
    base_url: https://openrouter.ai/api/v1
    api: openai-completions
    models:
      - openrouter/auto
      - openrouter/free
      - minimax/minimax-m3:free
      - nvidia/nemotron-3-super-120b-a12b:free
      - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
      - z-ai/glm-5.2:free
      - poolside/laguna-s-2.1:free
  nvidia:
    name: NVIDIA NIM
    env_key: C7_NVIDIA
    base_url: https://integrate.api.nvidia.com/v1
    api: openai-completions
    models:
      - deepseek-ai/deepseek-v4-flash-0731
      - moonshotai/kimi-k3
      - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
  mistral:
    name: Mistral AI Pro
    env_key: C1_MISTRAL
    base_url: https://api.mistral.ai/v1
    api: openai-completions
    models:
      - codestral-latest
  deepseek:
    name: DeepSeek Direct
    env_key: DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/v1
    api: openai-completions
    models:
      - deepseek-chat
      - deepseek-reasoner
database:
  journal_mode: wal
runtime:
  nofile_soft_limit: 4096
_config_version: 41
fallback_model:
  provider: openrouter
  model: minimax/minimax-m3:free
model_aliases:
  gemini-37: gemini-3.7-flash
  gemini-36: gemini-3.6-flash
  auto-free: openrouter/auto
  minimax-free: minimax/minimax-m3:free
  nemotron-super: nvidia/nemotron-3-super-120b-a12b:free
  nemotron-nano: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
  glm-free: z-ai/glm-5.2:free
  deepseek-flash-nim: deepseek-ai/deepseek-v4-flash-0731
  kimi-k3-nim: moonshotai/kimi-k3
  codestral: codestral-latest
  deepseek-chat: deepseek-chat
plugins:
  enabled: []
mcp_servers:
  colab:
    command: uvx
    args:
      - git+https://github.com/googlecolab/colab-mcp
  inkscape:
    command: python3
    args:
      - /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/SCRIPTS/mcp_servers/inkscape_mcp.py
  stitch:
    command: /home/tec/.local/bin/stitch-mcp-wrapper.sh
  obsidian:
    command: /home/tec/.npm-global/bin/obsidian-mcp-rs
    args:
      - /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/memory-bank
  novamira_mcp:
    command: /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/SCRIPTS/launch-mcp-wordpress.sh
  crawl4ai:
    command: /home/tec/.local/bin/crawl4ai-mcp
"""
    try:
        atomic_write(HERMES_CONFIG, hermes_yaml, validator=_validate_yaml)
        logs.append((f"✅ Hermes config.yaml actualizado (atómico): {HERMES_CONFIG}", "SUCCESS"))
    except Exception as e:
        logs.append((f"❌ Error configurando Hermes: {e}", "ERROR"))

    # 3. Purga de Caché de Hermes
    hermes_clean_cache = {
        "google": {"fp": "google-curated-v4", "at": time.time(), "models": ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemma-4-31b-it"]},
        "openrouter": {"fp": "openrouter-curated-v4", "at": time.time(), "models": ["openrouter/auto", "openrouter/free", "minimax/minimax-m3:free", "nvidia/nemotron-3-super-120b-a12b:free", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "z-ai/glm-5.2:free", "poolside/laguna-s-2.1:free"]},
        "nvidia": {"fp": "nvidia-curated-v4", "at": time.time(), "models": ["deepseek-ai/deepseek-v4-flash-0731", "moonshotai/kimi-k3", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"]},
        "mistral": {"fp": "mistral-curated-v4", "at": time.time(), "models": ["codestral-latest"]},
        "deepseek": {"fp": "deepseek-curated-v4", "at": time.time(), "models": ["deepseek-chat", "deepseek-reasoner"]}
    }
    try:
        cache_json = json.dumps(hermes_clean_cache, indent=2)
        atomic_write(HERMES_CACHE, cache_json, validator=_validate_json)
        logs.append(("✅ Caché de Hermes saneada (atómico)", "SUCCESS"))
    except Exception as e:
        logs.append((f"⚠️ No se pudo purgar caché de Hermes: {e}", "WARN"))

    # 4. DeepSeek Harness (~/.dsh/settings.yaml)
    dsh_yaml = """ui-onboarding:
  welcomeNoticeVersion: 2026-08-13.1

agent-default-model:
  provider: google
  model: gemini-3.6-flash

llm-deepseek:
  models:
    - id: deepseek-ai/deepseek-v4-flash-0731
      name: "[256k•Trial] DeepSeek V4 (NIM)"
      contextWindow: 262144

llm-pi-ai:
  providers:
    google:
      apiKeyEnv: C1_GOOGLE_AISTUDIO
      baseURL: "https://generativelanguage.googleapis.com/v1beta/openai/"
      models:
        - id: "gemini-3.7-flash"
          name: "[1M•Pro] Gemini 3.7 (Reasoning)"
          contextWindow: 1048576
        - id: "gemini-3.6-flash"
          name: "[1M•Pro] Gemini 3.6 (Fast)"
          contextWindow: 1048576
        - id: "gemini-3.5-flash"
          name: "[1M•Pro] Gemini 3.5 (Multi)"
          contextWindow: 1048576
        - id: "gemma-4-31b-it"
          name: "[262k•Pro] Gemma 4 31B (Agent)"
          contextWindow: 262144

    mistral:
      apiKeyEnv: C1_MISTRAL
      baseURL: "https://api.mistral.ai/v1"
      models:
        - id: "codestral-latest"
          name: "[256k•Trial] Codestral (Code)"
          contextWindow: 262144

    openrouter:
      apiKeyEnv: C7_OPENROUTER_OPENCODE_HP15
      baseURL: "https://openrouter.ai/api/v1"
      models:
        - id: "openrouter/auto"
          name: "[Auto•Free] OpenRouter Auto"
          contextWindow: 262144
        - id: "openrouter/free"
          name: "[Auto•Free] OpenRouter Free"
          contextWindow: 262144
        - id: "minimax/minimax-m3:free"
          name: "[1M•Free] MiniMax M3 (Frontier)"
          contextWindow: 1048576
        - id: "nvidia/nemotron-3-super-120b-a12b:free"
          name: "[262k•Free] Nemotron 3 Super"
          contextWindow: 262144
        - id: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
          name: "[256k•Free] Nemotron 3 Nano"
          contextWindow: 262144
        - id: "z-ai/glm-5.2:free"
          name: "[256k•Free] GLM 5.2 (Frontier)"
          contextWindow: 262144
        - id: "poolside/laguna-s-2.1:free"
          name: "[262k•Free] Laguna S 2.1 (Code)"
          contextWindow: 262144

    nvidia:
      apiKeyEnv: C7_NVIDIA
      baseURL: "https://integrate.api.nvidia.com/v1"
      models:
        - id: "deepseek-ai/deepseek-v4-flash-0731"
          name: "[256k•Trial] DeepSeek V4 (NIM)"
          contextWindow: 262144
        - id: "moonshotai/kimi-k3"
          name: "[256k•Trial] Kimi K3 (NIM)"
          contextWindow: 262144
        - id: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
          name: "[256k•Trial] Nemotron 3 Nano (NIM)"
          contextWindow: 256000

    deepseek:
      apiKeyEnv: DEEPSEEK_API_KEY
      baseURL: "https://api.deepseek.com/v1"
      models:
        - id: "deepseek-chat"
          name: "[128k•Paid] DeepSeek Chat V3"
          contextWindow: 131072
"""
    try:
        atomic_write(DSH_CONFIG_USER, dsh_yaml, validator=_validate_yaml)
        atomic_write(DSH_CONFIG_WORKSPACE, dsh_yaml, validator=_validate_yaml)
        logs.append((f"✅ DeepSeek Harness sincronizado (atómico): {DSH_CONFIG_USER}", "SUCCESS"))
    except Exception as e:
        logs.append((f"❌ Error configurando DSH: {e}", "ERROR"))

    return logs


def sync_to_hp45() -> Tuple[str, str]:
    """Sincroniza las configuraciones saneadas hacia el nodo secundario HP45."""
    if not SYNC_HP45_SCRIPT.exists():
        return ("⚠️ Script de sincronización no encontrado: " + str(SYNC_HP45_SCRIPT), "WARN")

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
            return ("✅ Sincronización exitosa hacia HP45 (tec@192.168.1.200).", "SUCCESS")
        return (f"⚠️ Rsync finalizado: {res.stdout.strip()[:100]}", "WARN")
    except subprocess.TimeoutExpired:
        return ("⚠️ Timeout conectando a HP45 (nodo portátil apagado o suspendido).", "WARN")
    except Exception as e:
        return (f"❌ Error en sincronización a HP45: {e}", "ERROR")
