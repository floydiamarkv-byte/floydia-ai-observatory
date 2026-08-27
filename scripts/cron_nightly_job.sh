#!/usr/bin/env bash
# ==============================================================================
# FloydIA AI Observatory — Actualización Diaria Desatendida (00:00)
# ==============================================================================
set -uo pipefail

OBSERVATORY_DIR="/home/tec/Dropbox/ANTIGRAVITY_PROJECTS/FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY"
LOG_FILE="$OBSERVATORY_DIR/reports/cron.log"
ENV_FILE="/home/tec/.secrets/antigravity.env"

mkdir -p "$OBSERVATORY_DIR/reports"

# Rotación de log si supera 5MB (Fix V-13)
if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE" 2>/dev/null || stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)" -gt 5242880 ]; then
    tail -n 2000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

echo "==============================================================================" >> "$LOG_FILE"
echo "🕒 [$(date '+%Y-%m-%d %H:%M:%S')] INICIO: Actualización Nocturna FloydIA AI Observatory" >> "$LOG_FILE"
echo "==============================================================================" >> "$LOG_FILE"

# Cargar variables de entorno si existen
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE" 2>/dev/null || true
    set +a
fi

cd "$OBSERVATORY_DIR"
export PYTHONPATH="$OBSERVATORY_DIR"

# Ejecutar pipeline completo: recolección + sonda local + scoring + reportes diarios + snapshot
python3 -m src.cli.main --full-run >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] FIN: Actualización completada con éxito (Exit 0)." >> "$LOG_FILE"
else
    echo "❌ [$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Actualización falló con código $EXIT_CODE." >> "$LOG_FILE"
fi
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
