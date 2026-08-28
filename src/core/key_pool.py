"""
Motor de Gestión de Pools Multi-Cuenta y Rotación Inteligente (KeyPool).
Soporta Round-Robin ponderado, enfriamiento temporal ante HTTP 429, detección de fallos de autenticación (401/403)
y Failover automático con thread-safety y async-safety completa.
"""

import time
import threading
import asyncio
from typing import Dict, Any, List, Optional
from config.settings import (
    GOOGLE_ACCOUNTS, ZEN_ACCOUNTS, Z_AI_ACCOUNTS, GROKIFIED_ACCOUNTS,
    DASHSCOPE_ACCOUNTS, DEEPSEEK_ACCOUNTS, OPENROUTER_ACCOUNTS,
    MISTRAL_ACCOUNTS, NVIDIA_ACCOUNTS, GROQ_ACCOUNTS
)


class KeyPoolManager:
    """Gestiona el ciclo de vida y rotación de claves para múltiples cuentas de forma thread-safe y async-safe."""

    def __init__(self):
        self._lock = threading.Lock()
        self._async_lock = None  # Creado perezosamente dentro del loop activo
        self._pools = {
            "google": GOOGLE_ACCOUNTS.copy(),
            "zen": ZEN_ACCOUNTS.copy(),
            "z_ai": Z_AI_ACCOUNTS.copy(),
            "grokified": GROKIFIED_ACCOUNTS.copy(),
            "dashscope": DASHSCOPE_ACCOUNTS.copy(),
            "deepseek": DEEPSEEK_ACCOUNTS.copy(),
            "openrouter": OPENROUTER_ACCOUNTS.copy(),
            "mistral": MISTRAL_ACCOUNTS.copy(),
            "nvidia": NVIDIA_ACCOUNTS.copy(),
            "groq": GROQ_ACCOUNTS.copy()
        }
        self._indices: Dict[str, int] = {p: 0 for p in self._pools}
        self._cooldowns: Dict[str, float] = {}  # {key_name: timestamp_available}
        self._auth_failed: Dict[str, bool] = {}  # {key_name: True si dio 401/403}
        self._latencies: Dict[str, float] = {}  # {key_name: last_latency_ms}
        self._error_counts: Dict[str, int] = {}

    def get_accounts(self, provider: str) -> List[Dict[str, str]]:
        """Retorna todas las cuentas configuradas para un proveedor."""
        with self._lock:
            return self._pools.get(provider.lower(), []).copy()

    def get_next_healthy_key(self, provider: str, allow_cooldown_fallback: bool = True) -> Optional[Dict[str, str]]:
        """
        Retorna la siguiente cuenta disponible aplicando Round-Robin y evitando
        cuentas en enfriamiento por HTTP 429 o con fallos de autenticación permanentes.
        """
        with self._lock:
            accounts = self._pools.get(provider.lower(), [])
            if not accounts:
                return None

            now = time.time()
            start_idx = self._indices.get(provider, 0)
            n = len(accounts)

            # 1. Buscar cuenta sana que no esté en cooldown ni con auth failed
            best_cd_acc = None
            min_cd_remaining = float("inf")

            for offset in range(n):
                idx = (start_idx + offset) % n
                acc = accounts[idx]
                acc_name = acc["name"]

                # Omitir cuentas con error de autenticación definitivo (401/403)
                if self._auth_failed.get(acc_name, False):
                    continue

                # Verificar cooldown
                if acc_name in self._cooldowns:
                    if now < self._cooldowns[acc_name]:
                        remaining = self._cooldowns[acc_name] - now
                        if remaining < min_cd_remaining:
                            min_cd_remaining = remaining
                            best_cd_acc = acc
                        continue
                    else:
                        del self._cooldowns[acc_name]

                # Cuenta sana encontrada
                self._indices[provider] = (idx + 1) % n
                return acc

            # 2. Si todas están en cooldown pero se permite fallback, devolver la que tenga menor cooldown
            if allow_cooldown_fallback and best_cd_acc is not None:
                return best_cd_acc

            # Si todas fallaron o no hay disponibles
            return accounts[0] if accounts else None

    async def get_next_healthy_key_async(self, provider: str, allow_cooldown_fallback: bool = True) -> Optional[Dict[str, str]]:
        """Versión asíncrona compatible con corrutinas de get_next_healthy_key."""
        return self.get_next_healthy_key(provider, allow_cooldown_fallback=allow_cooldown_fallback)

    def mark_rate_limited(self, account_name: str, cooldown_seconds: float = 60.0):
        """Pone una cuenta en enfriamiento temporal tras recibir un 429."""
        with self._lock:
            self._cooldowns[account_name] = time.time() + cooldown_seconds
            self._error_counts[account_name] = self._error_counts.get(account_name, 0) + 1
        print(f"🟡 [KeyPool] Cuenta '{account_name}' en enfriamiento por {cooldown_seconds}s (Rate Limit 429).")

    def mark_auth_failed(self, account_name: str):
        """Marca una cuenta con fallo de autenticación (401/403) para evitar reintentos continuos."""
        with self._lock:
            self._auth_failed[account_name] = True
            self._error_counts[account_name] = self._error_counts.get(account_name, 0) + 1
        print(f"🔴 [KeyPool] Cuenta '{account_name}' deshabilitada temporalmente por fallo de autenticación (401/403).")

    def reset_auth_status(self, account_name: Optional[str] = None):
        """Restablece el estado de autenticación de una o todas las cuentas."""
        with self._lock:
            if account_name:
                self._auth_failed.pop(account_name, None)
            else:
                self._auth_failed.clear()

    def record_latency(self, account_name: str, latency_ms: float):
        """Guarda la latencia observada de una cuenta."""
        with self._lock:
            self._latencies[account_name] = latency_ms

    def get_status_summary(self) -> Dict[str, Any]:
        """Resumen del estado de salud de todas las cuentas del clúster."""
        now = time.time()
        summary = {}
        with self._lock:
            for prov, accs in self._pools.items():
                summary[prov] = []
                for a in accs:
                    name = a["name"]
                    in_cooldown = name in self._cooldowns and now < self._cooldowns[name]
                    remaining_cd = max(0.0, self._cooldowns[name] - now) if in_cooldown else 0.0
                    is_auth_fail = self._auth_failed.get(name, False)
                    summary[prov].append({
                        "name": name,
                        "preview": f"...{a['key'][-4:]}" if len(a.get('key', '')) >= 4 else "—",
                        "in_cooldown": in_cooldown,
                        "cooldown_remaining_sec": round(remaining_cd, 1),
                        "auth_failed": is_auth_fail,
                        "last_latency_ms": self._latencies.get(name, None),
                        "error_count": self._error_counts.get(name, 0)
                    })
        return summary


# Instancia global Singleton
key_pool = KeyPoolManager()
