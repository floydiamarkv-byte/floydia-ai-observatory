"""
Motor de Gestión de Pools Multi-Cuenta y Rotación Inteligente (KeyPool).
Soporta Round-Robin ponderado, enfriamiento temporal ante HTTP 429 y Failover automático.
"""

import time
from typing import Dict, Any, List, Optional
from config.settings import (
    GOOGLE_ACCOUNTS, DEEPSEEK_ACCOUNTS, OPENROUTER_ACCOUNTS,
    MISTRAL_ACCOUNTS, NVIDIA_ACCOUNTS, GROQ_ACCOUNTS
)


class KeyPoolManager:
    """Gestiona el ciclo de vida y rotación de claves para múltiples cuentas."""

    def __init__(self):
        self._pools = {
            "google": GOOGLE_ACCOUNTS.copy(),
            "deepseek": DEEPSEEK_ACCOUNTS.copy(),
            "openrouter": OPENROUTER_ACCOUNTS.copy(),
            "mistral": MISTRAL_ACCOUNTS.copy(),
            "nvidia": NVIDIA_ACCOUNTS.copy(),
            "groq": GROQ_ACCOUNTS.copy()
        }
        self._indices: Dict[str, int] = {p: 0 for p in self._pools}
        self._cooldowns: Dict[str, float] = {}  # {key_name: timestamp_available}
        self._latencies: Dict[str, float] = {}  # {key_name: last_latency_ms}

    def get_accounts(self, provider: str) -> List[Dict[str, str]]:
        """Retorna todas las cuentas configuradas para un proveedor."""
        return self._pools.get(provider.lower(), [])

    def get_next_healthy_key(self, provider: str) -> Optional[Dict[str, str]]:
        """
        Retorna la siguiente cuenta disponible aplicando Round-Robin y evitando
        cuentas en enfriamiento por HTTP 429.
        """
        accounts = self.get_accounts(provider)
        if not accounts:
            return None

        now = time.time()
        start_idx = self._indices.get(provider, 0)
        n = len(accounts)

        # Buscar una cuenta que no esté en enfriamiento
        for offset in range(n):
            idx = (start_idx + offset) % n
            acc = accounts[idx]
            acc_name = acc["name"]
            
            # Verificar si expiró el enfriamiento
            if acc_name in self._cooldowns:
                if now < self._cooldowns[acc_name]:
                    continue  # Sigue en cooldown
                else:
                    del self._cooldowns[acc_name]  # Cooldown superado

            # Avanzar índice para la próxima llamada
            self._indices[provider] = (idx + 1) % n
            return acc

        # Si todas están en cooldown, devolver la primera disponible
        return accounts[0]

    def mark_rate_limited(self, account_name: str, cooldown_seconds: float = 60.0):
        """Pone una cuenta en enfriamiento temporal tras recibir un 429."""
        self._cooldowns[account_name] = time.time() + cooldown_seconds
        print(f"🟡 [KeyPool] Cuenta '{account_name}' en enfriamiento por {cooldown_seconds}s (Rate Limit 429).")

    def record_latency(self, account_name: str, latency_ms: float):
        """Guarda la latencia observada de una cuenta."""
        self._latencies[account_name] = latency_ms

    def get_status_summary(self) -> Dict[str, Any]:
        """Resumen del estado de salud de todas las cuentas del clúster."""
        now = time.time()
        summary = {}
        for prov, accs in self._pools.items():
            summary[prov] = []
            for a in accs:
                name = a["name"]
                in_cooldown = name in self._cooldowns and now < self._cooldowns[name]
                remaining_cd = max(0.0, self._cooldowns[name] - now) if in_cooldown else 0.0
                summary[prov].append({
                    "name": name,
                    "preview": f"...{a['key'][-4:]}",
                    "in_cooldown": in_cooldown,
                    "cooldown_remaining_sec": round(remaining_cd, 1),
                    "last_latency_ms": self._latencies.get(name, None)
                })
        return summary


# Instancia global Singleton
key_pool = KeyPoolManager()
