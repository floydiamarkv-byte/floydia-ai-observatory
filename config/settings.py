"""
Configuración centralizada de FloydIA AI Rankings & Local API Observatory.
Carga segura de variables de entorno y rutas canónicas sin exponer secretos.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

# Directorio raíz de la herramienta (código)
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

# Directorios de datos y reportes
STATE_DIR = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "floydia"
DATA_DIR = Path(os.getenv("FLOYDIA_DATA_DIR", BASE_DIR / "data"))
REPORTS_DIR = BASE_DIR / "reports"
DAILY_REPORTS_DIR = REPORTS_DIR / "daily"
FRONTIER_EXPORT_DIR = REPORTS_DIR / "frontier_export"
RAW_SNAPSHOTS_DIR = DATA_DIR / "raw_snapshots"

# Asegurar directorios
for d in [DATA_DIR, REPORTS_DIR, DAILY_REPORTS_DIR, FRONTIER_EXPORT_DIR, RAW_SNAPSHOTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Base de datos SQLite
DB_PATH = DATA_DIR / "rankings_engine.db"

# ---------------------------------------------------------------------------
# Registro PRIVADO de secretos y accessor auditado (Fix V-15).
# ---------------------------------------------------------------------------
_PRIVATE_SECRETS: Dict[str, str] = {}


def get_secret(name: str) -> Optional[str]:
    """Accessor único y auditado de credenciales."""
    return _PRIVATE_SECRETS.get(name) or os.getenv(name)


def load_env_file(filepath: Path) -> Dict[str, str]:
    """Lee un archivo .env endurecido: rechaza symlinks y exige chmod 600 (Fix V-04)."""
    env_vars: Dict[str, str] = {}
    if not filepath.exists():
        return env_vars

    if filepath.is_symlink():
        print(f"⚠️ [Settings] {filepath} es un symlink; ignorado por seguridad.")
        return env_vars

    try:
        mode = filepath.stat().st_mode & 0o777
        if mode != 0o600:
            os.chmod(filepath, 0o600)
            print(f"🔐 [Settings] Permisos corregidos a 600 en {filepath}")
    except Exception as e:
        print(f"⚠️ [Settings] No se pudo verificar chmod en {filepath}: {e}")

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                env_vars[k] = v
                _PRIVATE_SECRETS[k] = v
                os.environ.setdefault(k, v)
    except Exception as e:
        print(f"⚠️ [Settings] Error cargando {filepath}: {e}")
    return env_vars


# ÚNICA fuente canónica de secretos (Fix V-04)
SECRETS_PATHS = [
    Path("/home/tec/.secrets/antigravity.env"),
]

for p in SECRETS_PATHS:
    load_env_file(p)

# ---------------------------------------------------------------------------
# Helper de saneamiento criptográfico de secretos en logs/DB (Fix V-16).
# ---------------------------------------------------------------------------
_SECRET_RX = re.compile(
    r"(AIza[\w\-]{10,}|sk-[\w\-]{10,}|ghp_[\w]{10,}|hf_[\w]{10,}|Bearer\s+[\w.\-]{10,}|key=[\w\-]{8,})"
)


def scrub_secrets(text: str) -> str:
    """Elimina tokens y claves privadas de cualquier texto antes de persistir o imprimir."""
    return _SECRET_RX.sub("[REDACTED]", text) if text else text


def get_first_available_key(candidate_keys: list[str]) -> Optional[str]:
    """Busca la primera clave disponible en el entorno o registro privado."""
    for k in candidate_keys:
        val = get_secret(k)
        if val and len(val.strip()) > 5:
            return val.strip()
    return None


def get_all_available_keys(candidate_keys: list[str]) -> List[Dict[str, str]]:
    """Busca y retorna todas las claves configuradas para un proveedor con su nombre de variable."""
    found = []
    for k in candidate_keys:
        val = get_secret(k)
        if val and len(val.strip()) > 5:
            found.append({"name": k, "key": val.strip()})
    return found


# Listas Multi-Cuenta completas para pools de alta disponibilidad y rotación
GOOGLE_ACCOUNTS = get_all_available_keys([
    "C1_GOOGLE_AISTUDIO", "C2_GOOGLE_AISTUDIO", "C3_GOOGLE_AISTUDIO", 
    "C4_GOOGLE_AISTUDIO", "C5_GOOGLE_AISTUDIO", "C6_GOOGLE_AISTUDIO",
    "GEMINI_API_KEY", "GOOGLE_API_KEY"
])

ZEN_ACCOUNTS = get_all_available_keys([
    "C1_ZEN_OPENCODE", "C2_ZEN_OPENCODE", "C3_ZEN_OPENCODE",
    "C4_ZEN_OPENCODE", "C5_ZEN_OPENCODE", "C6_ZEN_OPENCODE", "C7_ZEN_OPENCODE"
])

Z_AI_ACCOUNTS = get_all_available_keys([
    "C1_Z_AI", "C2_Z_AI", "C3_Z_AI", "C4_Z_AI", "C5_Z_AI", "C6_Z_AI"
])

GROKIFIED_ACCOUNTS = get_all_available_keys([
    "GROKIFIED_API_KEY", "GROKIFIED_API_KEY_AUX"
])

DASHSCOPE_ACCOUNTS = get_all_available_keys([
    "C7_DASHSCOPE_API_KEY", "C7_QWEN_API_KEY", "C8_ALIBABA_API"
])

DEEPSEEK_ACCOUNTS = get_all_available_keys([
    "C1_DEEPSEEK", "C2_DEEPSEEK", "C3_DEEPSEEK", "C4_DEEPSEEK", 
    "C5_DEEPSEEK", "C6_DEEPSEEK", "C7_DEEPSEEK", "DEEPSEEK_API_KEY"
])

OPENROUTER_ACCOUNTS = get_all_available_keys([
    "C1_OPENROUTER", "C2_OPENROUTER", "C3_OPENROUTER", "C4_OPENROUTER",
    "C5_OPENROUTER", "C6_OPENROUTER", "C7_OPENROUTER", "C7_OPENROUTER_API_KEY",
    "C7_OPENROUTER_OPENCODE_HP15", "OPENROUTER_API_KEY"
])

MISTRAL_ACCOUNTS = get_all_available_keys([
    "C1_MISTRAL", "C2_MISTRAL", "C3_MISTRAL", "C4_MISTRAL", "C5_MISTRAL", "C6_MISTRAL",
    "MISTRAL_API_KEY"
])

NVIDIA_ACCOUNTS = get_all_available_keys([
    "C1_NVIDIA", "C2_NVIDIA", "C7_NVIDIA", "NVIDIA_API_KEY"
])

GROQ_ACCOUNTS = get_all_available_keys([
    "C1_GROQ", "C2_GROQ", "C3_GROQ", "C4_GROQ", "C5_GROQ", "C6_GROQ", "GROQ_API_KEY"
])

# Claves primarias individuales (Compatibilidad hacia atrás)
GEMINI_API_KEY = GOOGLE_ACCOUNTS[0]["key"] if GOOGLE_ACCOUNTS else None
ZEN_API_KEY = ZEN_ACCOUNTS[0]["key"] if ZEN_ACCOUNTS else None
Z_AI_API_KEY = Z_AI_ACCOUNTS[0]["key"] if Z_AI_ACCOUNTS else None
GROKIFIED_API_KEY = GROKIFIED_ACCOUNTS[0]["key"] if GROKIFIED_ACCOUNTS else None
DASHSCOPE_API_KEY = DASHSCOPE_ACCOUNTS[0]["key"] if DASHSCOPE_ACCOUNTS else None
OPENROUTER_API_KEY = OPENROUTER_ACCOUNTS[0]["key"] if OPENROUTER_ACCOUNTS else None
DEEPSEEK_API_KEY = DEEPSEEK_ACCOUNTS[0]["key"] if DEEPSEEK_ACCOUNTS else None
NVIDIA_API_KEY = NVIDIA_ACCOUNTS[0]["key"] if NVIDIA_ACCOUNTS else None
MISTRAL_API_KEY = MISTRAL_ACCOUNTS[0]["key"] if MISTRAL_ACCOUNTS else None
GROQ_API_KEY = GROQ_ACCOUNTS[0]["key"] if GROQ_ACCOUNTS else None

FIREWORKS_API_KEY = get_first_available_key([
    "FIREWORKS_API_KEY", "C7_FIREWORKS_API_KEY", "C8_FIREWORKS_API"
])

GITHUB_TOKEN = get_first_available_key([
    "GITHUB_TOKEN", "S02_GITHUB_TOKEN_ANTIGRAVITY", "S02_GITHUB_PAT", "GH_TOKEN"
])

HF_TOKEN = get_first_available_key(["HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN"])

# Configuración de Endpoints
GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GOOGLE_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
ZEN_API_BASE = "https://api.opencode.ai/zen/v1"
Z_AI_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
GROKIFIED_API_BASE = os.getenv("GROKIFIED_BASE_URL", "https://api.grokified.com/v1")
DASHSCOPE_API_BASE = os.getenv("C7_DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"
MISTRAL_API_BASE = "https://api.mistral.ai/v1"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
FIREWORKS_API_BASE = "https://api.fireworks.ai/inference/v1"
GITHUB_MODELS_BASE = "https://models.inference.ai.azure.com"

# ---------------------------------------------------------------------------
# Mapeo de Cuentas: variable env → email/label para mostrar en la UI.
# NO expone secretos, solo el nombre legible de la cuenta asociada.
# ---------------------------------------------------------------------------
ACCOUNT_LABELS: Dict[str, str] = {
    # Cuenta 1 (Pro)
    "C1_GOOGLE_AISTUDIO": "eliutec.aux.ia1@gmail.com",
    "C1_NVIDIA": "eliutec.aux.ia1@gmail.com",
    "C1_GROQ": "eliutec.aux.ia1@gmail.com",
    "C1_OPENROUTER": "eliutec.aux.ia1@gmail.com",
    "C1_Z_AI": "eliutec.aux.ia1@gmail.com",
    "C1_MISTRAL": "eliutec.aux.ia1@gmail.com",
    "C1_ZEN_OPENCODE": "eliutec.aux.ia1@gmail.com",
    "C1_DEEPSEEK": "eliutec.aux.ia1@gmail.com",
    # Cuenta 2
    "C2_GOOGLE_AISTUDIO": "eliutec.aux.ia2@gmail.com",
    "C2_NVIDIA": "eliutec.aux.ia2@gmail.com",
    "C2_GROQ": "eliutec.aux.ia2@gmail.com",
    "C2_OPENROUTER": "eliutec.aux.ia2@gmail.com",
    "C2_Z_AI": "eliutec.aux.ia2@gmail.com",
    "C2_MISTRAL": "eliutec.aux.ia2@gmail.com",
    "C2_ZEN_OPENCODE": "eliutec.aux.ia2@gmail.com",
    "C2_DEEPSEEK": "eliutec.aux.ia2@gmail.com",
    # Cuenta 3
    "C3_GOOGLE_AISTUDIO": "eliutec.aux.ia3@gmail.com",
    "C3_GROQ": "eliutec.aux.ia3@gmail.com",
    "C3_OPENROUTER": "eliutec.aux.ia3@gmail.com",
    "C3_Z_AI": "eliutec.aux.ia3@gmail.com",
    "C3_MISTRAL": "eliutec.aux.ia3@gmail.com",
    "C3_ZEN_OPENCODE": "eliutec.aux.ia3@gmail.com",
    "C3_DEEPSEEK": "eliutec.aux.ia3@gmail.com",
    # Cuenta 4
    "C4_GOOGLE_AISTUDIO": "eliutec.aux.ia4@gmail.com",
    "C4_GROQ": "eliutec.aux.ia4@gmail.com",
    "C4_OPENROUTER": "eliutec.aux.ia4@gmail.com",
    "C4_Z_AI": "eliutec.aux.ia4@gmail.com",
    "C4_MISTRAL": "eliutec.aux.ia4@gmail.com",
    "C4_ZEN_OPENCODE": "eliutec.aux.ia4@gmail.com",
    "C4_DEEPSEEK": "eliutec.aux.ia4@gmail.com",
    # Cuenta 5
    "C5_GOOGLE_AISTUDIO": "eliutec.aux.ia5@gmail.com",
    "C5_GROQ": "eliutec.aux.ia5@gmail.com",
    "C5_OPENROUTER": "eliutec.aux.ia5@gmail.com",
    "C5_Z_AI": "eliutec.aux.ia5@gmail.com",
    "C5_MISTRAL": "eliutec.aux.ia5@gmail.com",
    "C5_ZEN_OPENCODE": "eliutec.aux.ia5@gmail.com",
    "C5_DEEPSEEK": "eliutec.aux.ia5@gmail.com",
    # Cuenta 6
    "C6_GOOGLE_AISTUDIO": "eliutec.aux.ia6@gmail.com",
    "C6_GROQ": "eliutec.aux.ia6@gmail.com",
    "C6_OPENROUTER": "eliutec.aux.ia6@gmail.com",
    "C6_Z_AI": "eliutec.aux.ia6@gmail.com",
    "C6_MISTRAL": "eliutec.aux.ia6@gmail.com",
    "C6_ZEN_OPENCODE": "eliutec.aux.ia6@gmail.com",
    "C6_DEEPSEEK": "eliutec.aux.ia6@gmail.com",
    # Cuenta 7 (Master)
    "C7_OPENROUTER": "floydiamarkv@gmail.com",
    "C7_OPENROUTER_HERMES_HP15": "floydiamarkv@gmail.com",
    "C7_OPENROUTER_OPENCODE_HP15": "floydiamarkv@gmail.com",
    "C7_OPENROUTER_API_KEY": "floydiamarkv@gmail.com",
    "C7_DEEPSEEK": "floydiamarkv@gmail.com",
    "C7_NVIDIA": "floydiamarkv@gmail.com",
    "C7_ZEN_OPENCODE": "floydiamarkv@gmail.com",
    "C7_DASHSCOPE_API_KEY": "floydiamarkv@gmail.com",
    "C7_QWEN_API_KEY": "floydiamarkv@gmail.com",
    "C7_FIREWORKS_API_KEY": "floydiamarkv@gmail.com",
    "C7_KIMI_PLATFORM_API": "floydiamarkv@gmail.com",
    # Cuenta 8
    "C8_ALIBABA_API": "lacoquita.elsa@gmail.com",
    "C8_FIREWORKS_API": "lacoquita.elsa@gmail.com",
    # Claves standalone (fuera de serie C1..C8)
    "GROKIFIED_API_KEY": "floydiamarkv@gmail.com",
    "GROKIFIED_API_KEY_AUX": "eliutec.aux.ia1@gmail.com",
    "DEEPSEEK_API_KEY": "floydiamarkv@gmail.com",
    "NVIDIA_API_KEY": "eliutec.aux.ia1@gmail.com",
    "MISTRAL_API_KEY": "eliutec.aux.ia1@gmail.com",
    "GROQ_API_KEY": "eliutec.aux.ia1@gmail.com",
    "OPENROUTER_API_KEY": "floydiamarkv@gmail.com",
    "S02_GITHUB_TOKEN_ANTIGRAVITY": "floydiamarkv@gmail.com",
    "S02_GITHUB_PAT": "floydiamarkv@gmail.com",
}


def resolve_account_email(env_key_name: str) -> str:
    """Dado el nombre de la variable de entorno, retorna el email de la cuenta asociada."""
    return ACCOUNT_LABELS.get(env_key_name, "—")


# M-6: Vida media continua por fuente de benchmark (en días)
HALF_LIVES_BY_SOURCE: Dict[str, float] = {
    "arena_ai": 30.0,
    "arenaai": 30.0,
    "lmsys": 30.0,
    "livebench": 45.0,
    "epoch_ai": 45.0,
    "epochai": 45.0,
    "swebench": 45.0,
    "swe_bench": 45.0,
    "aider": 30.0,
    "livecodebench": 30.0,
    "artificial_analysis": 30.0,
    "artificialanalysis": 30.0,
    "huggingface": 60.0,
    "openrouter": 7.0,
    "default": 30.0
}

