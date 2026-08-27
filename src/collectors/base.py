"""
Clase base para todos los recolectores de datos de benchmarks y rankings.
Proporciona manejo de snapshots con hash SHA256, reintentos con backoff exponencial,
jitter aleatorio y respeto de la cabecera Retry-After (Fix V-06).
"""

import time
import random
from typing import Dict, Any, Optional
import requests
from src.core.db import save_raw_snapshot


class BaseCollector:
    def __init__(self, name: str, default_timeout: int = 15):
        self.name = name
        self.timeout = default_timeout
        self.headers = {
            "User-Agent": "FloydIA-AI-Rankings-Observatory/9.5 (+https://floydia.com)",
            "Accept": "application/json"
        }
        self.session = requests.Session()

    def fetch_url(self, url: str, custom_headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Realiza una petición HTTP GET con reintentos exponenciales, jitter y guarda el snapshot crudo."""
        req_headers = self.headers.copy()
        if custom_headers:
            req_headers.update(custom_headers)

        max_attempts = 4
        base_delay = 1.0

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.session.get(url, headers=req_headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    text_content = response.text
                    save_raw_snapshot(self.name, url, text_content, response.status_code)
                    return text_content
                
                elif response.status_code in [401, 403, 404]:
                    print(f"⚠️ [{self.name}] Error HTTP {response.status_code} no reintentable en {url}")
                    return None
                
                elif response.status_code in [429, 500, 502, 503, 504]:
                    # Respetar Retry-After si viene en la cabecera
                    retry_after_str = response.headers.get("Retry-After")
                    if retry_after_str:
                        try:
                            delay = float(retry_after_str)
                        except ValueError:
                            delay = (2 ** attempt) + random.uniform(0.1, 0.5)
                    else:
                        delay = (base_delay * (2 ** (attempt - 1))) + random.uniform(0.1, 0.5)

                    print(f"🟡 [{self.name}] HTTP {response.status_code} en {url}. Reintentando en {delay:.2f}s (Intento {attempt}/{max_attempts})...")
                    time.sleep(delay)
                else:
                    print(f"⚠️ [{self.name}] HTTP {response.status_code} en {url}")
                    return None

            except (requests.exceptions.RequestException, Exception) as e:
                delay = (base_delay * (2 ** (attempt - 1))) + random.uniform(0.1, 0.5)
                print(f"⚠️ [{self.name}] Intento {attempt}/{max_attempts} fallido para {url}: {e}. Esperando {delay:.2f}s...")
                time.sleep(delay)

        print(f"❌ [{self.name}] Se agotaron los {max_attempts} intentos para {url}.")
        return None

    def collect(self) -> int:
        """Método abstracto que cada recolector debe implementar."""
        raise NotImplementedError
