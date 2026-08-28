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
        "small_model": "opencode/nemotron-3.5-lightning-free",
        "provider": {
            "opencode": {
                "npm": "@ai-sdk/openai",
                "name": "OpenCode Zen",
                "options": {
                    "baseURL": "https://api.opencode.ai/zen/v1",
                    "apiKey": "{env:C1_ZEN_OPENCODE}"
                },
                "models": {
                    "opencode/nemotron-3-ultra-free": {"name": "[262k•Zen Free] Nemotron 3 Ultra 550B"},
                    "opencode/nemotron-3.5-lightning-free": {"name": "[262k•Zen Free] Nemotron 3.5 Lightning"},
                    "opencode/mimo-v2.5-free": {"name": "[262k•Zen Free] MiMo V2.5"},
                    "opencode/hy3-free": {"name": "[262k•Zen Free] Hy3 Free"},
                    "opencode/big-pickle": {"name": "[131k•Zen] Big Pickle"},
                    "opencode/muse-spark-1.2-contributor-free": {"name": "[262k•Zen Free] Muse Spark 1.2"}
                }
            },
            "google": {
                "npm": "@ai-sdk/google",
                "name": "Google AI Studio Pro",
                "options": {"apiKey": "{env:C1_GOOGLE_AISTUDIO}"},
                "models": {
                    "gemini-3.7-flash": {"name": "[1M•Pro] Gemini 3.7 (Reasoning)"},
                    "gemini-3.6-flash": {"name": "[1M•Pro] Gemini 3.6 (Fast)"},
                    "gemini-3.5-flash": {"name": "[1M•Pro] Gemini 3.5 (Multi)"},
                    "gemma-4-31b-it": {"name": "[262k•Pro] Gemma 4 31B (Agent)"},
                    "gemma-4-26b-a4b-it": {"name": "[262k•Pro] Gemma 4 26B (Fast)"},
                    "gemini-2.5-pro": {"name": "[1M•Pro] Gemini 2.5 Pro (Frontier)"},
                    "gemini-2.5-flash": {"name": "[1M•Pro] Gemini 2.5 Flash (Workhorse)"}
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
                    "deepseek-v4-flash": {"name": "[262k•Paid] DeepSeek V4 Flash"},
                    "deepseek-v4-pro": {"name": "[262k•Paid] DeepSeek V4 Pro"},
                    "deepseek-chat": {"name": "[128k•Paid] DeepSeek Chat V3"},
                    "deepseek-reasoner": {"name": "[64k•Paid] DeepSeek Reasoner R1"}
                }
            },
            "mistral": {
                "npm": "@ai-sdk/mistral",
                "name": "Mistral AI Pro",
                "options": {"apiKey": "{env:C1_MISTRAL}"},
                "models": {
                    "codestral-latest": {"name": "[256k•Trial] Codestral (Code)"},
                    "devstral-latest": {"name": "[256k•Trial] Devstral (Agent)"},
                    "mistral-large-latest": {"name": "[128k•Trial] Mistral Large"},
                    "mistral-small-latest": {"name": "[128k•Trial] Mistral Small"},
                    "ministral-8b-latest": {"name": "[128k•Trial] Ministral 8B"}
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
                    "deepseek-ai/deepseek-v4-pro-0813": {"name": "[256k•Trial] DeepSeek V4 Pro (NIM)"},
                    "moonshotai/kimi-k3": {"name": "[256k•Trial] Kimi K3 (NIM)"},
                    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": {"name": "[256k•Trial] Nemotron 3 Nano (NIM)"},
                    "nvidia/nemotron-3-super-120b-a12b": {"name": "[262k•Trial] Nemotron 3 Super (NIM)"},
                    "nvidia/nemotron-3-ultra-550b-a55b": {"name": "[262k•Trial] Nemotron 3 Ultra (NIM)"}
                }
            },
            "z_ai": {
                "npm": "@ai-sdk/openai",
                "name": "Z.AI (Zhipu GLM)",
                "options": {
                    "baseURL": "https://open.bigmodel.cn/api/paas/v4",
                    "apiKey": "{env:C1_Z_AI}"
                },
                "models": {
                    "glm-5.3": {"name": "[262k•Pro] GLM 5.3 (Frontier)"},
                    "glm-5.2": {"name": "[262k•Pro] GLM 5.2 (Workhorse)"},
                    "glm-5-turbo": {"name": "[131k•Pro] GLM 5 Turbo"},
                    "glm-5.3-flash": {"name": "[131k•Free] GLM 5.3 Flash"}
                }
            },
            "grokified": {
                "npm": "@ai-sdk/openai",
                "name": "Grokified (xAI)",
                "options": {
                    "baseURL": "https://api.grokified.com/v1",
                    "apiKey": "{env:GROKIFIED_API_KEY}"
                },
                "models": {
                    "grok-4.6": {"name": "[262k•Pro] Grok 4.6 (Frontier)"},
                    "grok-4.5": {"name": "[131k•Pro] Grok 4.5"},
                    "grok-4.20-multi-agent-0309": {"name": "[262k•Pro] Grok 4.20 Multi-Agent"},
                    "grok-build-0.1": {"name": "[131k•Pro] Grok Build 0.1 (Code)"}
                }
            },
            "dashscope": {
                "npm": "@ai-sdk/openai",
                "name": "Alibaba DashScope (Qwen)",
                "options": {
                    "baseURL": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                    "apiKey": "{env:C7_DASHSCOPE_API_KEY}"
                },
                "models": {
                    "qwen3.8-max": {"name": "[262k•Pro] Qwen 3.8 Max (Frontier)"},
                    "qwen3.8-flash": {"name": "[131k•Free] Qwen 3.8 Flash"},
                    "qwen3.8-27b": {"name": "[131k•Pro] Qwen 3.8 27B"},
                    "qwen3.7-flash": {"name": "[131k•Free] Qwen 3.7 Flash"}
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
                    "poolside/laguna-s-2.1:free": {"name": "[262k•Free] Laguna S 2.1 (Code)"},
                    "thinkingmachines/inkling:free": {"name": "[256k•Free] TM Inkling"}
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
  base_url: https://generativelanguage.googleapis.com/v1beta/openai
providers:
  google:
    name: Google AI Studio Pro
    env_key: C1_GOOGLE_AISTUDIO
    base_url: https://generativelanguage.googleapis.com/v1beta/openai
    api: openai-completions
    models:
      - gemini-3.7-flash
      - gemini-3.6-flash
      - gemini-3.5-flash
      - gemma-4-31b-it
      - gemma-4-26b-a4b-it
      - gemini-2.5-pro
      - gemini-2.5-flash
  opencode:
    name: OpenCode Zen
    env_key: C1_ZEN_OPENCODE
    base_url: https://api.opencode.ai/zen/v1
    api: openai-completions
    models:
      - opencode/nemotron-3-ultra-free
      - opencode/nemotron-3.5-lightning-free
      - opencode/mimo-v2.5-free
      - opencode/hy3-free
      - opencode/big-pickle
      - opencode/muse-spark-1.2-contributor-free
  deepseek:
    name: DeepSeek Direct
    env_key: DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/v1
    api: openai-completions
    models:
      - deepseek-v4-flash
      - deepseek-v4-pro
      - deepseek-chat
      - deepseek-reasoner
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
      - thinkingmachines/inkling:free
  nvidia:
    name: NVIDIA NIM
    env_key: C7_NVIDIA
    base_url: https://integrate.api.nvidia.com/v1
    api: openai-completions
    models:
      - deepseek-ai/deepseek-v4-flash-0731
      - deepseek-ai/deepseek-v4-pro-0813
      - moonshotai/kimi-k3
      - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
      - nvidia/nemotron-3-super-120b-a12b
      - nvidia/nemotron-3-ultra-550b-a55b
  mistral:
    name: Mistral AI Pro
    env_key: C1_MISTRAL
    base_url: https://api.mistral.ai/v1
    api: openai-completions
    models:
      - codestral-latest
      - devstral-latest
      - mistral-large-latest
      - mistral-small-latest
      - ministral-8b-latest
  z_ai:
    name: Z.AI (Zhipu GLM)
    env_key: C1_Z_AI
    base_url: https://open.bigmodel.cn/api/paas/v4
    api: openai-completions
    models:
      - glm-5.3
      - glm-5.2
      - glm-5-turbo
      - glm-5.3-flash
  grokified:
    name: Grokified (xAI)
    env_key: GROKIFIED_API_KEY
    base_url: https://api.grokified.com/v1
    api: openai-completions
    models:
      - grok-4.6
      - grok-4.5
      - grok-4.20-multi-agent-0309
      - grok-build-0.1
  dashscope:
    name: Alibaba DashScope (Qwen)
    env_key: C7_DASHSCOPE_API_KEY
    base_url: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    api: openai-completions
    models:
      - qwen3.8-max
      - qwen3.8-flash
      - qwen3.8-27b
      - qwen3.7-flash
database:
  journal_mode: wal
runtime:
  nofile_soft_limit: 4096
_config_version: 42
fallback_model:
  provider: opencode
  model: opencode/nemotron-3.5-lightning-free
model_aliases:
  gemini-37: gemini-3.7-flash
  gemini-36: gemini-3.6-flash
  zen-ultra: opencode/nemotron-3-ultra-free
  zen-lightning: opencode/nemotron-3.5-lightning-free
  zen-mimo: opencode/mimo-v2.5-free
  zen-hy3: opencode/hy3-free
  auto-free: openrouter/auto
  minimax-free: minimax/minimax-m3:free
  nemotron-super: nvidia/nemotron-3-super-120b-a12b:free
  nemotron-nano: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
  glm-free: z-ai/glm-5.2:free
  glm-53: glm-5.3
  glm-52: glm-5.2
  grok-46: grok-4.6
  grok-agent: grok-4.20-multi-agent-0309
  qwen-max: qwen3.8-max
  qwen-flash: qwen3.8-flash
  deepseek-flash: deepseek-v4-flash
  deepseek-pro: deepseek-v4-pro
  deepseek-chat: deepseek-chat
  deepseek-r1: deepseek-reasoner
  kimi-k3-nim: moonshotai/kimi-k3
  codestral: codestral-latest
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
        "google": {"fp": "google-curated-v5", "at": time.time(), "models": ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-2.5-pro", "gemini-2.5-flash"]},
        "opencode": {"fp": "opencode-curated-v5", "at": time.time(), "models": ["opencode/nemotron-3-ultra-free", "opencode/nemotron-3.5-lightning-free", "opencode/mimo-v2.5-free", "opencode/hy3-free", "opencode/big-pickle", "opencode/muse-spark-1.2-contributor-free"]},
        "z_ai": {"fp": "zai-curated-v5", "at": time.time(), "models": ["glm-5.3", "glm-5.2", "glm-5-turbo", "glm-5.3-flash"]},
        "grokified": {"fp": "grokified-curated-v5", "at": time.time(), "models": ["grok-4.6", "grok-4.5", "grok-4.20-multi-agent-0309", "grok-build-0.1"]},
        "dashscope": {"fp": "dashscope-curated-v5", "at": time.time(), "models": ["qwen3.8-max", "qwen3.8-flash", "qwen3.8-27b", "qwen3.7-flash"]},
        "deepseek": {"fp": "deepseek-curated-v5", "at": time.time(), "models": ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"]},
        "openrouter": {"fp": "openrouter-curated-v5", "at": time.time(), "models": ["openrouter/auto", "openrouter/free", "minimax/minimax-m3:free", "nvidia/nemotron-3-super-120b-a12b:free", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "z-ai/glm-5.2:free", "poolside/laguna-s-2.1:free", "thinkingmachines/inkling:free"]},
        "nvidia": {"fp": "nvidia-curated-v5", "at": time.time(), "models": ["deepseek-ai/deepseek-v4-flash-0731", "deepseek-ai/deepseek-v4-pro-0813", "moonshotai/kimi-k3", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "nvidia/nemotron-3-super-120b-a12b", "nvidia/nemotron-3-ultra-550b-a55b"]},
        "mistral": {"fp": "mistral-curated-v5", "at": time.time(), "models": ["codestral-latest", "devstral-latest", "mistral-large-latest", "mistral-small-latest", "ministral-8b-latest"]}
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

# ── Flota Completa Multi-Proveedor en llm-deepseek (Selector Nativo DSH) ──
llm-deepseek:
  models:
    # Google AI Studio Pro
    - id: "gemini-3.7-flash"
      name: "[1M•Pro] Gemini 3.7 (Reasoning) · Google"
      contextWindow: 1048576
    - id: "gemini-3.6-flash"
      name: "[1M•Pro] Gemini 3.6 (Fast) · Google"
      contextWindow: 1048576
    - id: "gemini-3.5-flash"
      name: "[1M•Pro] Gemini 3.5 (Multi) · Google"
      contextWindow: 1048576
    - id: "gemma-4-31b-it"
      name: "[262k•Pro] Gemma 4 31B (Agent) · Google"
      contextWindow: 262144
    - id: "gemini-2.5-pro"
      name: "[1M•Pro] Gemini 2.5 Pro (Frontier) · Google"
      contextWindow: 1048576
    - id: "gemini-2.5-flash"
      name: "[1M•Pro] Gemini 2.5 Flash (Workhorse) · Google"
      contextWindow: 1048576

    # OpenCode Zen Free Fleet
    - id: "opencode/nemotron-3-ultra-free"
      name: "[262k•Zen Free] Nemotron 3 Ultra 550B"
      contextWindow: 262144
    - id: "opencode/nemotron-3.5-lightning-free"
      name: "[262k•Zen Free] Nemotron 3.5 Lightning"
      contextWindow: 262144
    - id: "opencode/mimo-v2.5-free"
      name: "[262k•Zen Free] MiMo V2.5"
      contextWindow: 262144
    - id: "opencode/hy3-free"
      name: "[262k•Zen Free] Hy3 Free"
      contextWindow: 262144
    - id: "opencode/muse-spark-1.2-contributor-free"
      name: "[262k•Zen Free] Muse Spark 1.2"
      contextWindow: 262144

    # DeepSeek Direct
    - id: deepseek-v4-flash
      name: "[262k•Paid] DeepSeek V4 Flash"
      contextWindow: 262144
    - id: deepseek-v4-pro
      name: "[262k•Paid] DeepSeek V4 Pro"
      contextWindow: 262144
    - id: deepseek-chat
      name: "[128k•Paid] DeepSeek Chat V3"
      contextWindow: 131072
    - id: deepseek-reasoner
      name: "[64k•Paid] DeepSeek Reasoner R1"
      contextWindow: 65536

    # Alibaba DashScope (Qwen)
    - id: "qwen3.8-max"
      name: "[262k•Pro] Qwen 3.8 Max (Frontier)"
      contextWindow: 262144
    - id: "qwen3.8-flash"
      name: "[131k•Free] Qwen 3.8 Flash"
      contextWindow: 131072
    - id: "qwen3.8-27b"
      name: "[131k•Pro] Qwen 3.8 27B"
      contextWindow: 131072

    # Mistral AI Pro
    - id: "codestral-latest"
      name: "[256k•Trial] Codestral (Code) · Mistral"
      contextWindow: 262144
    - id: "devstral-latest"
      name: "[256k•Trial] Devstral (Agent) · Mistral"
      contextWindow: 262144
    - id: "mistral-large-latest"
      name: "[128k•Trial] Mistral Large"
      contextWindow: 131072

    # NVIDIA NIM
    - id: "deepseek-ai/deepseek-v4-flash-0731"
      name: "[256k•Trial] DeepSeek V4 (NIM)"
      contextWindow: 262144
    - id: "moonshotai/kimi-k3"
      name: "[256k•Trial] Kimi K3 (NIM)"
      contextWindow: 262144
    - id: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
      name: "[256k•Trial] Nemotron 3 Nano (NIM)"
      contextWindow: 256000
    - id: "nvidia/nemotron-3-super-120b-a12b"
      name: "[262k•Trial] Nemotron 3 Super (NIM)"
      contextWindow: 262144

    # Z.AI (GLM)
    - id: "glm-5.3"
      name: "[262k•Pro] GLM 5.3 (Frontier)"
      contextWindow: 262144
    - id: "glm-5.2"
      name: "[262k•Pro] GLM 5.2 (Workhorse)"
      contextWindow: 262144

    # OpenRouter Free Fleet
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
    - id: "z-ai/glm-5.2:free"
      name: "[256k•Free] GLM 5.2 (Frontier)"
      contextWindow: 262144
    - id: "poolside/laguna-s-2.1:free"
      name: "[262k•Free] Laguna S 2.1 (Code)"
      contextWindow: 262144

llm-pi-ai:
  providers:
    google:
      apiKeyEnv: C1_GOOGLE_AISTUDIO
      baseURL: "https://generativelanguage.googleapis.com/v1beta/openai"
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
        - id: "gemma-4-26b-a4b-it"
          name: "[262k•Pro] Gemma 4 26B (Fast)"
          contextWindow: 262144
        - id: "gemini-2.5-pro"
          name: "[1M•Pro] Gemini 2.5 Pro (Frontier)"
          contextWindow: 1048576
        - id: "gemini-2.5-flash"
          name: "[1M•Pro] Gemini 2.5 Flash (Workhorse)"
          contextWindow: 1048576

    opencode:
      apiKeyEnv: C1_ZEN_OPENCODE
      baseURL: "https://api.opencode.ai/zen/v1"
      models:
        - id: "opencode/nemotron-3-ultra-free"
          name: "[262k•Zen Free] Nemotron 3 Ultra 550B"
          contextWindow: 262144
        - id: "opencode/nemotron-3.5-lightning-free"
          name: "[262k•Zen Free] Nemotron 3.5 Lightning"
          contextWindow: 262144
        - id: "opencode/mimo-v2.5-free"
          name: "[262k•Zen Free] MiMo V2.5"
          contextWindow: 262144
        - id: "opencode/hy3-free"
          name: "[262k•Zen Free] Hy3 Free"
          contextWindow: 262144
        - id: "opencode/big-pickle"
          name: "[131k•Zen] Big Pickle"
          contextWindow: 131072
        - id: "opencode/muse-spark-1.2-contributor-free"
          name: "[262k•Zen Free] Muse Spark 1.2"
          contextWindow: 262144

    z_ai:
      apiKeyEnv: C1_Z_AI
      baseURL: "https://open.bigmodel.cn/api/paas/v4"
      models:
        - id: "glm-5.3"
          name: "[262k•Pro] GLM 5.3 (Frontier)"
          contextWindow: 262144
        - id: "glm-5.2"
          name: "[262k•Pro] GLM 5.2 (Workhorse)"
          contextWindow: 262144
        - id: "glm-5-turbo"
          name: "[131k•Pro] GLM 5 Turbo"
          contextWindow: 131072
        - id: "glm-5.3-flash"
          name: "[131k•Free] GLM 5.3 Flash"
          contextWindow: 131072

    grokified:
      apiKeyEnv: GROKIFIED_API_KEY
      baseURL: "https://api.grokified.com/v1"
      models:
        - id: "grok-4.6"
          name: "[262k•Pro] Grok 4.6 (Frontier)"
          contextWindow: 262144
        - id: "grok-4.5"
          name: "[131k•Pro] Grok 4.5"
          contextWindow: 131072
        - id: "grok-4.20-multi-agent-0309"
          name: "[262k•Pro] Grok 4.20 Multi-Agent"
          contextWindow: 262144
        - id: "grok-build-0.1"
          name: "[131k•Pro] Grok Build 0.1 (Code)"
          contextWindow: 131072

    dashscope:
      apiKeyEnv: C7_DASHSCOPE_API_KEY
      baseURL: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
      models:
        - id: "qwen3.8-max"
          name: "[262k•Pro] Qwen 3.8 Max (Frontier)"
          contextWindow: 262144
        - id: "qwen3.8-flash"
          name: "[131k•Free] Qwen 3.8 Flash"
          contextWindow: 131072
        - id: "qwen3.8-27b"
          name: "[131k•Pro] Qwen 3.8 27B"
          contextWindow: 131072
        - id: "qwen3.7-flash"
          name: "[131k•Free] Qwen 3.7 Flash"
          contextWindow: 131072

    deepseek:
      apiKeyEnv: DEEPSEEK_API_KEY
      baseURL: "https://api.deepseek.com/v1"
      models:
        - id: "deepseek-v4-flash"
          name: "[262k•Paid] DeepSeek V4 Flash"
          contextWindow: 262144
        - id: "deepseek-v4-pro"
          name: "[262k•Paid] DeepSeek V4 Pro"
          contextWindow: 262144
        - id: "deepseek-chat"
          name: "[128k•Paid] DeepSeek Chat V3"
          contextWindow: 131072
        - id: "deepseek-reasoner"
          name: "[64k•Paid] DeepSeek Reasoner R1"
          contextWindow: 65536

    mistral:
      apiKeyEnv: C1_MISTRAL
      baseURL: "https://api.mistral.ai/v1"
      models:
        - id: "codestral-latest"
          name: "[256k•Trial] Codestral (Code)"
          contextWindow: 262144
        - id: "devstral-latest"
          name: "[256k•Trial] Devstral (Agent)"
          contextWindow: 262144
        - id: "mistral-large-latest"
          name: "[128k•Trial] Mistral Large"
          contextWindow: 131072
        - id: "mistral-small-latest"
          name: "[128k•Trial] Mistral Small"
          contextWindow: 131072
        - id: "ministral-8b-latest"
          name: "[128k•Trial] Ministral 8B"
          contextWindow: 131072

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
        - id: "thinkingmachines/inkling:free"
          name: "[256k•Free] TM Inkling"
          contextWindow: 262144

    nvidia:
      apiKeyEnv: C7_NVIDIA
      baseURL: "https://integrate.api.nvidia.com/v1"
      models:
        - id: "deepseek-ai/deepseek-v4-flash-0731"
          name: "[256k•Trial] DeepSeek V4 (NIM)"
          contextWindow: 262144
        - id: "deepseek-ai/deepseek-v4-pro-0813"
          name: "[256k•Trial] DeepSeek V4 Pro (NIM)"
          contextWindow: 262144
        - id: "moonshotai/kimi-k3"
          name: "[256k•Trial] Kimi K3 (NIM)"
          contextWindow: 262144
        - id: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
          name: "[256k•Trial] Nemotron 3 Nano (NIM)"
          contextWindow: 256000
        - id: "nvidia/nemotron-3-super-120b-a12b"
          name: "[262k•Trial] Nemotron 3 Super (NIM)"
          contextWindow: 262144
        - id: "nvidia/nemotron-3-ultra-550b-a55b"
          name: "[262k•Trial] Nemotron 3 Ultra (NIM)"
          contextWindow: 262144
ui-theme:
  preference: dark
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
