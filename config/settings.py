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
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"
MISTRAL_API_BASE = "https://api.mistral.ai/v1"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
FIREWORKS_API_BASE = "https://api.fireworks.ai/inference/v1"
GITHUB_MODELS_BASE = "https://models.inference.ai.azure.com"
