"""
Clase base para todos los recolectores de datos de benchmarks y rankings.
Proporciona manejo de snapshots con hash SHA256, reintentos y timeouts.
"""

import json
import time
from typing import Dict, Any, Optional
import requests
from src.core.db import save_raw_snapshot


class BaseCollector:
    def __init__(self, name: str, default_timeout: int = 15):
        self.name = name
        self.timeout = default_timeout
        self.headers = {
            "User-Agent": "FloydIA-AI-Rankings-Observatory/6.0 (+https://floydia.com)",
            "Accept": "application/json"
        }

    def fetch_url(self, url: str, custom_headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Realiza una petición HTTP GET con reintentos y guarda el snapshot crudo."""
        req_headers = self.headers.copy()
        if custom_headers:
            req_headers.update(custom_headers)

        for attempt in range(1, 4):
            try:
                response = requests.get(url, headers=req_headers, timeout=self.timeout)
                if response.status_code == 200:
                    text_content = response.text
                    save_raw_snapshot(self.name, url, text_content, response.status_code)
                    return text_content
                elif response.status_code in [401, 403, 404]:
                    print(f"⚠️ [{self.name}] Error HTTP {response.status_code} en {url}")
                    return None
            except Exception as e:
                print(f"⚠️ [{self.name}] Intento {attempt} fallido para {url}: {e}")
                time.sleep(1.0 * attempt)
        return None

    def collect(self) -> int:
        """Método abstracto que cada recolector debe implementar."""
        raise NotImplementedError
