#!/usr/bin/env python3
"""
Lanzador Automático de FloydIA AI Rankings & Local API Observatory.
Verifica si el servidor está activo (o lo inicia en segundo plano) y abre el navegador en http://localhost:8333.
"""

import sys
import time
import socket
import webbrowser
import subprocess
from pathlib import Path

PORT = 8333
URL = f"http://localhost:{PORT}"
BASE_DIR = Path(__file__).resolve().parent


def is_port_in_use(port: int) -> bool:
    """Comprueba si el puerto ya está escuchando conexiones."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    if not is_port_in_use(PORT):
        print(f"🚀 Iniciando servidor FloydIA Observatory en http://localhost:{PORT}...")
        subprocess.Popen(
            [sys.executable, "-m", "src.cli.main", "--serve", "--port", str(PORT)],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        # Esperar a que el socket responda
        for _ in range(10):
            time.sleep(0.3)
            if is_port_in_use(PORT):
                break

    print(f"🌐 Abriendo navegador en {URL}...")
    webbrowser.open(URL)


if __name__ == "__main__":
    main()
