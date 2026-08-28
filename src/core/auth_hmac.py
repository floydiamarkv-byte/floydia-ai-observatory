"""
Módulo de Autenticación HMAC Anti-Replay (M-2 - Protocolo FloydIA v11.1 / Production Hardened).
Implementa firma HMAC-SHA256 con ventana de tiempo (+/-300s), nonce único persistido
en SQLite para evitar ataques de repetición y comparación en tiempo constante.

Seguridad Fail-Closed:
- Si no se encuentra FLOYDIA_DASH_TOKEN o HMAC_SECRET configurado, se rechaza cualquier
  petición protegida (fail-closed, 401 Unauthorized). No se utilizan secretos predecibles.
"""

import hmac
import hashlib
import time
import sqlite3
from typing import Tuple, Optional
from src.core.db import get_db_connection
from config.settings import get_secret

HMAC_SECRET = get_secret("FLOYDIA_DASH_TOKEN") or get_secret("HMAC_SECRET")
MAX_TIMESTAMP_DRIFT_SEC = 300  # Ventana de validez +/- 5 minutos


def generate_hmac_signature(secret: str, timestamp: int, nonce: str, body: str = "") -> str:
    """Genera la firma HMAC-SHA256 para un payload dado."""
    if not secret:
        raise ValueError("HMAC Secret cannot be empty")
    message = f"{timestamp}.{nonce}.{body}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_hmac_request(
    headers: dict,
    body: str = "",
    secret: Optional[str] = None
) -> Tuple[bool, int, str]:
    """
    Verifica la firma HMAC y previene ataques de repetición mediante nonces y ventana de tiempo.
    Retorna (is_valid, http_status_code, error_message).
    Fail-closed: si no hay secreto configurado, se rechaza la autenticación.
    """
    sec = secret or HMAC_SECRET
    if not sec:
        return False, 401, "Authentication secret not configured on server (fail-closed)"

    ts_header = headers.get("X-Floydia-Timestamp") or headers.get("x-floydia-timestamp")
    nonce_header = headers.get("X-Floydia-Nonce") or headers.get("x-floydia-nonce")
    sig_header = headers.get("X-Floydia-Signature") or headers.get("x-floydia-signature")

    # Si no se usan headers HMAC, verificar token estático como fallback seguro
    if not ts_header or not nonce_header or not sig_header:
        token_header = headers.get("X-Floydia-Token") or headers.get("x-floydia-token")
        if token_header and hmac.compare_digest(token_header, sec):
            return True, 200, "OK (Static Token)"
        return False, 403, "Missing authentication headers (HMAC or X-Floydia-Token required)"

    # 1. Validar formato y ventana de tiempo (+/- 300s)
    try:
        req_ts = int(ts_header)
    except (ValueError, TypeError):
        return False, 401, "Invalid X-Floydia-Timestamp format"

    now = int(time.time())
    if abs(now - req_ts) > MAX_TIMESTAMP_DRIFT_SEC:
        return False, 401, f"Timestamp expired or out of window (drift: {abs(now - req_ts)}s, max: {MAX_TIMESTAMP_DRIFT_SEC}s)"

    # 2. Validar firma HMAC en tiempo constante
    expected_sig = generate_hmac_signature(sec, req_ts, nonce_header, body)
    if not hmac.compare_digest(sig_header.lower(), expected_sig.lower()):
        return False, 401, "Invalid HMAC signature"

    # 3. Validar nonce único en SQLite de forma atómica (Anti-Replay)
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # Limpiar nonces viejos (> 10 minutos)
            c.execute("DELETE FROM auth_nonces WHERE ts < ?", (now - 600,))
            
            # Inserción atómica con manejo de colisión de PRIMARY KEY
            try:
                c.execute("INSERT INTO auth_nonces (nonce, ts) VALUES (?, ?)", (nonce_header, req_ts))
            except sqlite3.IntegrityError:
                return False, 401, f"Replay attack detected: Nonce '{nonce_header}' has already been used"
    except Exception as e:
        print(f"⚠️ [HMAC Auth] Error verificando nonce en DB: {e}")
        return False, 500, "Database error during nonce validation"

    return True, 200, "OK"
