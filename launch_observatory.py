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


def is_port_in_use(port: int = PORT) -> bool:
    """Comprueba si el puerto ya está escuchando conexiones."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_observatory_server_running(port: int = PORT, wait_timeout: float = 2.5) -> bool:
    """Garantiza que el servidor de Observatory esté corriendo en segundo plano sin bloquear."""
    if is_port_in_use(port):
        return True

    try:
        subprocess.Popen(
            [sys.executable, "-m", "src.cli.main", "--serve", "--port", str(port)],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        start_time = time.time()
        while time.time() - start_time < wait_timeout:
            time.sleep(0.25)
            if is_port_in_use(port):
                return True
    except Exception as e:
        print(f"⚠️ Error al intentar levantar el servidor Observatory: {e}", file=sys.stderr)

    return is_port_in_use(port)


def main():
    if not is_port_in_use(PORT):
        print(f"🚀 Iniciando servidor FloydIA Observatory en http://localhost:{PORT}...")
    server_ok = ensure_observatory_server_running(PORT)
    if not server_ok:
        print(f"⚠️ Advertencia: No se pudo confirmar el inicio del servidor en puerto {PORT}.")
    else:
        print(f"✅ Servidor FloydIA Observatory activo en {URL}")
    print(f"🌐 Abriendo navegador en {URL}...")
    webbrowser.open(URL)


if __name__ == "__main__":
    main()
