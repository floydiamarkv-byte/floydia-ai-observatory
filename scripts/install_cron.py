#!/usr/bin/env python3
"""
Instalador y Gestor de Tarea Cron para FloydIA AI Observatory.
Configura la ejecución desatendida diaria a las 00:00 (medianoche) con backup previo (Fix V-14).
"""

import sys
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = BASE_DIR / "scripts" / "cron_nightly_job.sh"
CRON_COMMENT = "# FloydIA AI Rankings & Local API Observatory — Actualización Diaria"
CRON_ENTRY = f"0 0 * * * {SCRIPT_PATH} > /dev/null 2>&1"


def get_current_crontab() -> str:
    """Obtiene el crontab actual distinguiendo 'sin crontab' de un error real."""
    res = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        if "no crontab for" in res.stderr.lower():
            return ""
        raise RuntimeError(f"crontab -l falló inesperadamente: {res.stderr.strip()}")
    return res.stdout


def set_crontab(content: str):
    """Escribe el crontab generando un backup de seguridad previo en /tmp."""
    try:
        current = get_current_crontab()
        Path("/tmp/crontab.floydia.bak").write_text(current, encoding="utf-8")
    except Exception as e:
        print(f"⚠️ No se pudo guardar backup de crontab: {e}")
    subprocess.run(["crontab", "-"], input=content, text=True, check=True)


def is_installed() -> bool:
    content = get_current_crontab()
    return str(SCRIPT_PATH) in content


def install():
    if not SCRIPT_PATH.exists():
        print(f"❌ Error: No se encontró el script en {SCRIPT_PATH}")
        sys.exit(1)

    SCRIPT_PATH.chmod(0o755)
    current = get_current_crontab().strip()
    
    if str(SCRIPT_PATH) in current:
        print("ℹ️ La tarea cron de FloydIA AI Observatory ya se encuentra instalada.")
        return

    new_crontab = current + f"\n\n{CRON_COMMENT}\n{CRON_ENTRY}\n" if current else f"{CRON_COMMENT}\n{CRON_ENTRY}\n"
    set_crontab(new_crontab)
    print("✅ [Cron] Tarea programada instalada exitosamente:")
    print(f"   ⏰ Horario: Diariamente a las 00:00 (Medianoche)")
    print(f"   📜 Script: {SCRIPT_PATH}")
    print(f"   📁 Logs: {BASE_DIR / 'reports' / 'cron.log'}")


def uninstall():
    current = get_current_crontab()
    if str(SCRIPT_PATH) not in current:
        print("ℹ️ No hay ninguna tarea de FloydIA Observatory registrada en el crontab.")
        return

    lines = current.splitlines()
    filtered = []
    for line in lines:
        if CRON_COMMENT in line or str(SCRIPT_PATH) in line:
            continue
        filtered.append(line)

    new_crontab = "\n".join(filtered).strip() + "\n"
    set_crontab(new_crontab)
    print("🗑️ [Cron] Tarea desinstalada del crontab.")


def status():
    installed = is_installed()
    print("=== Estado de Automatización FloydIA AI Observatory ===")
    print(f"Estado en Crontab: {'🟢 ACTIVO (00:00 Diaria)' if installed else '⚪ NO INSTALADO'}")
    print(f"Ruta del Script: {SCRIPT_PATH} ({'Existe' if SCRIPT_PATH.exists() else 'No existe'})")
    log_file = BASE_DIR / "reports" / "cron.log"
    if log_file.exists():
        print(f"Archivo de Log: {log_file} ({log_file.stat().st_size} bytes)")
    else:
        print(f"Archivo de Log: {log_file} (Aún no generado)")


def main():
    parser = argparse.ArgumentParser(description="Gestor de Cron para FloydIA AI Observatory")
    parser.add_argument("--install", action="store_true", help="Instala la tarea en crontab para las 00:00")
    parser.add_argument("--uninstall", action="store_true", help="Elimina la tarea del crontab")
    parser.add_argument("--status", action="store_true", help="Muestra el estado actual de la tarea cron")
    args = parser.parse_args()

    if args.install:
        install()
    elif args.uninstall:
        uninstall()
    elif args.status:
        status()
    else:
        install()


if __name__ == "__main__":
    main()
