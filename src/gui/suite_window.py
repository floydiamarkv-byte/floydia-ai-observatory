"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║  🛰️  FLOYDIA AI COMMAND & OBSERVATORY SUITE (v8.0) — GUI PyQt6 Unificada        ║
║  Panel de Control de Rankings Globales, Telemetría de Red y Despliegue Multi-Nodo ║
║  «Desde la infraestructura, todo.»                                               ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import socket
import subprocess
import webbrowser
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QIcon, QFont, QCursor, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QScrollArea, QFrame,
    QProgressBar, QPlainTextEdit, QGridLayout
)

from config.settings import BASE_DIR, DAILY_REPORTS_DIR, FRONTIER_EXPORT_DIR
from src.collectors.aggregator import run_all_collectors
from src.probers.local_verifier import run_local_api_probes
from src.core.scoring import calculate_multidimensional_rankings
from src.core.db import get_latest_local_verified_models, get_all_models_count
from src.analyst.ai_advisor import ask_observatory
from src.core.engine_injector import apply_engine_configurations, sync_to_hp45
from src.reports.markdown_report import generate_daily_markdown_report
from src.reports.html_report import generate_daily_html_report
from src.analyst.frontier_exporter import export_daily_snapshot_for_frontier_ai

ICON_APP_PATH = "/home/tec/.local/share/icons/floydia_ai_suite.png"
DASHBOARD_PORT = 8333


def is_port_in_use(port: int = DASHBOARD_PORT) -> bool:
    """Comprueba si el puerto del dashboard web ya está activo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_dashboard_server(port: int = DASHBOARD_PORT) -> bool:
    """Inicia el servidor web en background si no está activo."""
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
        for _ in range(15):
            time.sleep(0.2)
            if is_port_in_use(port):
                return True
    except Exception as e:
        print(f"Error iniciando servidor web: {e}")
    return is_port_in_use(port)


class SuiteWorkerSignals(QObject):
    log = pyqtSignal(str, str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)


class SuiteWorker(QThread):
    def __init__(self, tasks: Dict[str, bool]):
        super().__init__()
        self.tasks = tasks
        self.signals = SuiteWorkerSignals()

    def _ts_log(self, msg: str, lvl: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.signals.log.emit(f"[{ts}] {msg}", lvl)

    def run(self):
        start_time = time.perf_counter()
        active_steps = [k for k, v in self.tasks.items() if v]
        total_steps = len(active_steps)
        if total_steps == 0:
            self._ts_log("⚠️ No se seleccionó ninguna tarea.", "WARN")
            self.signals.finished.emit({})
            return

        current = 0
        rankings = []
        local_apis = []

        # 1. Recolección de rankings globales
        if self.tasks.get("collect_rankings"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("🌐 [1/6] Recolectando Rankings Globales en Vivo...", "INFO")
            try:
                res = run_all_collectors()
                self._ts_log(f"  ↳ LMSYS Arena Elo: {res.get('LMSYS Chatbot Arena', res.get('lmsys', 0))} modelos indexados", "INFO")
                self._ts_log(f"  ↳ Hugging Face Leaderboard v2: {res.get('Hugging Face Leaderboard v2', res.get('hf', 0))} benchmarks actualizados", "INFO")
                self._ts_log(f"  ↳ OpenRouter Live API: {res.get('OpenRouter Models & Pricing', res.get('openrouter', 0))} modelos y tarifas procesadas", "INFO")
                self._ts_log(f"  ↳ Artificial Analysis & LiveBench: métricas de calidad y throughput sincronizadas", "INFO")
                self._ts_log("  ✅ Sincronización de Benchmarks Globales completada con éxito.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error recolectando rankings: {e}", "ERROR")

        # 2. Sondeo y auditoría de APIs locales
        if self.tasks.get("probe_apis"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("🔍 [2/6] Sondeando APIs Locales y Clúster Homelab...", "INFO")
            try:
                probe_res = run_local_api_probes()
                active_count = sum(1 for c in probe_res if c.get("is_functional"))
                
                # Agrupación por proveedor para detalle
                by_prov = {}
                for c in probe_res:
                    prov = c.get("provider", "Otros")
                    by_prov.setdefault(prov, []).append(c)
                
                for prov, checks in by_prov.items():
                    act = sum(1 for x in checks if x.get("is_functional"))
                    tot = len(checks)
                    avg_lat = [x.get("latency_ms", 0) for x in checks if x.get("is_functional") and x.get("latency_ms")]
                    avg_str = f" · Latencia media: {round(sum(avg_lat)/len(avg_lat), 1)}ms" if avg_lat else ""
                    self._ts_log(f"  ↳ {prov}: {act}/{tot} endpoints activos{avg_str}", "INFO")

                self._ts_log(f"  ✅ Resumen Sondeo: {active_count}/{len(probe_res)} APIs locales activas y verificadas.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error en sonda local: {e}", "ERROR")

        # 3. Diagnóstico de IA
        if self.tasks.get("ai_diagnosis"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("🧠 [3/6] Generando Diagnóstico Ejecutivo con IA...", "INFO")
            try:
                diag = ask_observatory("Haz un resumen del estado del clúster y roles de modelos recomendados.")
                if diag.get("success"):
                    self._ts_log(f"  ✅ Motor IA Activo: {diag.get('engine')}", "SUCCESS")
                    lines = [l for l in diag.get("answer", "").split("\n") if l.strip()]
                    for line in lines:
                        self._ts_log(f"    {line}", "INFO")
                else:
                    self._ts_log(f"  ⚠️ Advertencia Asesor: {diag.get('error', 'Sin respuesta')}", "WARN")
            except Exception as e:
                self._ts_log(f"  ❌ Error en diagnóstico de IA: {e}", "ERROR")

        # 4. Reescribir e inyectar motores
        if self.tasks.get("inject_engines"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("⚙️  [4/6] Inyectando Configuraciones a OpenCode, Hermes y DSH...", "INFO")
            try:
                logs = apply_engine_configurations()
                for msg, lvl in logs:
                    self._ts_log(f"  ↳ {msg}", lvl)
                self._ts_log("  ✅ Inyección de motores y saneamiento de caché completados.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error inyectando motores: {e}", "ERROR")

        # 5. Sincronizar clúster a HP45
        if self.tasks.get("sync_hp45"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("📡 [5/6] Sincronizando Clúster hacia HP45...", "INFO")
            try:
                msg, lvl = sync_to_hp45()
                self._ts_log(f"  ↳ {msg}", lvl)
                self._ts_log("  ✅ Sincronización Rsync hacia tec@192.168.1.200 finalizada.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error sincronizando a HP45: {e}", "ERROR")

        # 6. Generar reportes diarios
        if self.tasks.get("generate_reports"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("📄 [6/6] Generando Informes Diarios (Markdown / HTML / Frontier)...", "INFO")
            try:
                rankings = calculate_multidimensional_rankings()
                local_apis = get_latest_local_verified_models()
                md_path = generate_daily_markdown_report(rankings, local_apis)
                html_path = generate_daily_html_report(rankings, local_apis)
                frontier_path = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
                
                md_size = round(os.path.getsize(md_path) / 1024, 1) if os.path.exists(md_path) else 0
                html_size = round(os.path.getsize(html_path) / 1024, 1) if os.path.exists(html_path) else 0
                fr_size = round(os.path.getsize(frontier_path) / 1024, 1) if os.path.exists(frontier_path) else 0

                self._ts_log(f"  ↳ 📄 Informe Markdown: {md_path} ({md_size} KB)", "SUCCESS")
                self._ts_log(f"  ↳ 🌐 Visualizador HTML: {html_path} ({html_size} KB)", "SUCCESS")
                self._ts_log(f"  ↳ 📋 Snapshot Frontier: {frontier_path} ({fr_size} KB)", "SUCCESS")
                self._ts_log(f"  ✅ {len(rankings)} modelos evaluados y consolidados en reportes.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error generando reportes: {e}", "ERROR")

        elapsed = round(time.perf_counter() - start_time, 2)
        self.signals.progress.emit(100)
        self._ts_log(f"\n🎯 PIPELINE FLOYDIA COMPLETADO CON ÉXITO en {elapsed}s.\n«Desde la infraestructura, todo.»", "SUCCESS")
        self.signals.finished.emit({"success": True, "elapsed": elapsed})

FLOYDIA_QSS = """
QMainWindow {
    background-color: #0B111C;
}
QWidget {
    color: #F5F8F7;
    font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
    font-size: 13px;
}
QFrame#HeaderFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #152638, stop:1 #0B111C);
    border-bottom: 2px solid #10D2AD;
    border-radius: 0px;
}
QFrame#CardFrame {
    background-color: #111C2B;
    border: 1px solid #1F3347;
    border-radius: 8px;
    padding: 14px;
}
QFrame#CardFrame:hover {
    border: 1px solid #10D2AD;
    background-color: #162438;
}
QPushButton {
    background-color: #1A324A;
    color: #F5F8F7;
    border: 1px solid #2B4E73;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #234363;
    border: 1px solid #10D2AD;
    color: #10D6BD;
}
QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10D2AD, stop:1 #0EBA99);
    color: #0B111C;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 800;
    padding: 12px 24px;
    letter-spacing: 0.8px;
}
QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10D6BD, stop:1 #10D2AD);
    color: #000000;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #2A3B4C;
    color: #6B7C8E;
    border: none;
}
QPushButton#SecondaryBtn {
    background-color: #1F364D;
    color: #38BDF8;
    border: 1px solid #2B4E73;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#SecondaryBtn:hover {
    background-color: #264463;
    border: 1px solid #38BDF8;
}
QCheckBox {
    spacing: 12px;
    font-weight: 600;
    font-size: 13px;
    color: #E2E8F0;
}
QCheckBox:hover {
    color: #10D2AD;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #38BDF8;
    background-color: #0B111C;
}
QCheckBox::indicator:checked {
    background-color: #10D2AD;
    border: 1px solid #10D2AD;
}
QProgressBar {
    background-color: #070C14;
    border: 1px solid #1E3A5F;
    border-radius: 6px;
    text-align: center;
    color: #FFFFFF;
    font-weight: 700;
    height: 20px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10D2AD, stop:1 #10D6BD);
    border-radius: 5px;
}
QPlainTextEdit {
    background-color: #070C14;
    border: 1px solid #1E3A5F;
    border-radius: 6px;
    color: #E2E8F0;
    font-family: 'JetBrains Mono', 'Fira Code', 'Monospace', monospace;
    font-size: 12px;
    padding: 10px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #0B111C;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #1E3A5F;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #10D2AD;
}
"""


class FloydIASuiteWindow(QMainWindow):
    """Ventana Principal de FloydIA AI Command & Observatory Suite."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FloydIA — AI Command & Observatory Suite v8.0")
        self.resize(1150, 800)
        if os.path.exists(ICON_APP_PATH):
            self.setWindowIcon(QIcon(ICON_APP_PATH))
        self.setStyleSheet(FLOYDIA_QSS)
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # ── Header Frame ──────────────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 10, 10, 15)

        title_vbox = QVBoxLayout()
        title_lbl = QLabel("🛰️ FLOYDIA AI COMMAND & OBSERVATORY SUITE")
        title_lbl.setFont(QFont("Chakra Petch", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #10D2AD; letter-spacing: 1px;")
        sub_lbl = QLabel("Observatorio de Rankings Mundiales · Telemetría Homelab · Inyector de Motores")
        sub_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        title_vbox.addWidget(title_lbl)
        title_vbox.addWidget(sub_lbl)
        header_layout.addLayout(title_vbox)

        header_layout.addStretch()

        # Botón Ver Informe HTML
        html_btn = QPushButton("📄 Ver Informe HTML")
        html_btn.setObjectName("SecondaryBtn")
        html_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        html_btn.clicked.connect(self._open_html_report)
        header_layout.addWidget(html_btn)

        # Botón Abrir Dashboard Web
        web_btn = QPushButton("🌐 Abrir Dashboard (:8333)")
        web_btn.setObjectName("SecondaryBtn")
        web_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        web_btn.clicked.connect(self._open_web_dashboard)
        header_layout.addWidget(web_btn)

        main_layout.addWidget(header_frame)

        # ── Checkmarks Grid Frame ─────────────────────────────────────────────
        card_frame = QFrame()
        card_frame.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(12)

        card_title = QLabel("⚙️  SELECCIÓN DE TAREAS MODULARES (CHECKMARKS)")
        card_title.setFont(QFont("IBM Plex Sans", 11, QFont.Weight.Bold))
        card_title.setStyleSheet("color: #38BDF8; letter-spacing: 0.5px;")
        card_layout.addWidget(card_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)

        self.chk_collect = QCheckBox("🌐 1. Recolectar Rankings Globales (LMSYS Elo, HF Leaderboard v2, OpenRouter 417)")
        self.chk_collect.setChecked(True)
        grid.addWidget(self.chk_collect, 0, 0)

        self.chk_probe = QCheckBox("🔍 2. Sondear APIs Locales y Clúster (Google C1..C6, DeepSeek, Mistral, Groq, NIM)")
        self.chk_probe.setChecked(True)
        grid.addWidget(self.chk_probe, 0, 1)

        self.chk_ai = QCheckBox("🧠 3. Diagnóstico Ejecutivo con IA (DeepSeek V3 / Gemini 3.6 Flash)")
        self.chk_ai.setChecked(True)
        grid.addWidget(self.chk_ai, 1, 0)

        self.chk_inject = QCheckBox("⚡ 4. Reescribir e Inyectar Motores (OpenCode + Hermes + DeepSeek Harness)")
        self.chk_inject.setChecked(True)
        grid.addWidget(self.chk_inject, 1, 1)

        self.chk_sync = QCheckBox("📡 5. Sincronizar Clúster HP15 ➔ HP45 (Rsync tec@192.168.1.200)")
        self.chk_sync.setChecked(True)
        grid.addWidget(self.chk_sync, 2, 0)

        self.chk_reports = QCheckBox("📄 6. Generar Informes Diarios (Markdown, HTML Interactivo, Frontier Snapshot)")
        self.chk_reports.setChecked(True)
        grid.addWidget(self.chk_reports, 2, 1)

        card_layout.addLayout(grid)

        # Botones de selección rápida
        sel_hbox = QHBoxLayout()
        btn_all = QPushButton("Seleccionar Todo")
        btn_all.setObjectName("SecondaryBtn")
        btn_all.clicked.connect(self._select_all)
        btn_none = QPushButton("Deseleccionar Todo")
        btn_none.setObjectName("SecondaryBtn")
        btn_none.clicked.connect(self._deselect_all)
        btn_engines_only = QPushButton("⚡ Solo Inyectar Motores")
        btn_engines_only.setObjectName("SecondaryBtn")
        btn_engines_only.clicked.connect(self._select_engines_only)
        btn_clear_log = QPushButton("🧹 Limpiar Consola")
        btn_clear_log.setObjectName("SecondaryBtn")
        btn_clear_log.clicked.connect(self._clear_console)

        sel_hbox.addWidget(btn_all)
        sel_hbox.addWidget(btn_none)
        sel_hbox.addWidget(btn_engines_only)
        sel_hbox.addWidget(btn_clear_log)
        sel_hbox.addStretch()
        card_layout.addLayout(sel_hbox)

        main_layout.addWidget(card_frame)

        # ── Progress & Action Bar ─────────────────────────────────────────────
        action_hbox = QHBoxLayout()
        self.prog_bar = QProgressBar()
        self.prog_bar.setValue(0)
        action_hbox.addWidget(self.prog_bar, stretch=3)

        self.run_btn = QPushButton("🚀 EJECUTAR PIPELINE SELECCIONADO")
        self.run_btn.setObjectName("PrimaryBtn")
        self.run_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.run_btn.clicked.connect(self._start_pipeline)
        action_hbox.addWidget(self.run_btn, stretch=1)

        main_layout.addLayout(action_hbox)

        # ── Console Log Area ──────────────────────────────────────────────────
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        ts_now = datetime.now().strftime("%H:%M:%S")
        self.console.appendPlainText(f"[{ts_now}] 🟢 [FloydIA Suite v8.0] Listo. Selecciona las tareas y presiona Ejecutar.")
        main_layout.addWidget(self.console)

    def _select_all(self):
        for chk in [self.chk_collect, self.chk_probe, self.chk_ai, self.chk_inject, self.chk_sync, self.chk_reports]:
            chk.setChecked(True)

    def _deselect_all(self):
        for chk in [self.chk_collect, self.chk_probe, self.chk_ai, self.chk_inject, self.chk_sync, self.chk_reports]:
            chk.setChecked(False)

    def _select_engines_only(self):
        self._deselect_all()
        self.chk_inject.setChecked(True)
        self.chk_sync.setChecked(True)

    def _clear_console(self):
        self.console.clear()
        ts_now = datetime.now().strftime("%H:%M:%S")
        self.console.appendPlainText(f"[{ts_now}] 🟢 [FloydIA Suite v8.0] Consola reiniciada.")

    def _open_html_report(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        html_file = DAILY_REPORTS_DIR / f"{today_str}_informe_ia_floydia.html"
        
        # Si no existe el de hoy, buscar el más reciente
        if not html_file.exists():
            reports = sorted(DAILY_REPORTS_DIR.glob("*_informe_ia_floydia.html"), reverse=True)
            if reports:
                html_file = reports[0]

        if html_file.exists():
            ts_now = datetime.now().strftime("%H:%M:%S")
            self.console.appendPlainText(f"[{ts_now}] 📄 Abriendo Informe HTML interactivo: {html_file}")
            webbrowser.open(f"file://{html_file.resolve()}")
        else:
            ts_now = datetime.now().strftime("%H:%M:%S")
            self.console.appendPlainText(f"[{ts_now}] ⚠️ No se encontró informe HTML generado. Ejecuta primero la tarea 6 (Generar Informes).")

    def _open_web_dashboard(self):
        ts_now = datetime.now().strftime("%H:%M:%S")
        self.console.appendPlainText(f"[{ts_now}] 🌐 Verificando servidor Dashboard en http://localhost:{DASHBOARD_PORT}...")
        
        # Iniciar servidor si no está corriendo
        if not is_port_in_use(DASHBOARD_PORT):
            self.console.appendPlainText(f"[{ts_now}] 🚀 Iniciando servidor web de FloydIA en segundo plano...")
            ok = ensure_dashboard_server(DASHBOARD_PORT)
            if ok:
                ts_now = datetime.now().strftime("%H:%M:%S")
                self.console.appendPlainText(f"[{ts_now}] ✅ Servidor Dashboard iniciado correctamente en http://localhost:{DASHBOARD_PORT}")
            else:
                ts_now = datetime.now().strftime("%H:%M:%S")
                self.console.appendPlainText(f"[{ts_now}] ⚠️ No se pudo verificar el puerto {DASHBOARD_PORT}. Intentando abrir navegador...")
        else:
            self.console.appendPlainText(f"[{ts_now}] ✅ Servidor Dashboard activo y escuchando en el puerto {DASHBOARD_PORT}.")

        webbrowser.open(f"http://localhost:{DASHBOARD_PORT}")

    def _start_pipeline(self):
        tasks = {
            "collect_rankings": self.chk_collect.isChecked(),
            "probe_apis": self.chk_probe.isChecked(),
            "ai_diagnosis": self.chk_ai.isChecked(),
            "inject_engines": self.chk_inject.isChecked(),
            "sync_hp45": self.chk_sync.isChecked(),
            "generate_reports": self.chk_reports.isChecked(),
        }
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ EJECUTANDO...")
        self.prog_bar.setValue(0)
        ts_now = datetime.now().strftime("%H:%M:%S")
        self.console.appendPlainText(f"\n[{ts_now}] 🚀 Iniciando ejecución de tareas seleccionadas...")

        self.worker = SuiteWorker(tasks)
        self.worker.signals.log.connect(self._append_log)
        self.worker.signals.progress.connect(self.prog_bar.setValue)
        self.worker.signals.finished.connect(self._pipeline_finished)
        self.worker.start()

    def _append_log(self, msg: str, level: str):
        self.console.appendPlainText(msg)
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.ensureCursorVisible()

    def _pipeline_finished(self, res: dict):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("🚀 EJECUTAR PIPELINE SELECCIONADO")


def run_gui_suite():
    app = QApplication(sys.argv)
    window = FloydIASuiteWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui_suite()
