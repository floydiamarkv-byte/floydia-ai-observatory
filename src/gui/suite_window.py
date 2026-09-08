"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║  🛰️  FLOYDIA AI COMMAND & OBSERVATORY SUITE (v9.3) — GUI PyQt6 Ultra-Liviana     ║
║  Panel de Control de Rankings, Escáner Profundo 6 Estados e Inyección Dinámica  ║
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
from typing import Dict, Any, List, Optional
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QTimer
from PyQt6.QtGui import QIcon, QFont, QCursor, QTextCursor, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QScrollArea, QFrame,
    QProgressBar, QPlainTextEdit, QGridLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QSplitter, QMessageBox
)

from config.settings import BASE_DIR, DAILY_REPORTS_DIR, FRONTIER_EXPORT_DIR
from src.collectors.aggregator import run_all_collectors
from src.probers.local_verifier import run_local_api_probes
from src.probers.deep_probe_scanner import (
    run_deep_scan, get_latest_deep_scan_results,
    STATUS_OK, STATUS_NO_BALANCE, STATUS_FREE_TIER_EXHAUSTED,
    STATUS_UNAUTHORIZED, STATUS_NO_RESPONSE, STATUS_ERROR,
    DEFAULT_PROBE_PROMPT, STATUS_LABELS, build_probe_target_for_model
)
from src.core.scoring import calculate_multidimensional_rankings
from src.core.db import get_latest_local_verified_models, get_all_models_count
from src.analyst.ai_advisor import ask_observatory
from src.core.engine_injector import apply_engine_configurations, sync_to_hp45
from src.reports.markdown_report import generate_daily_markdown_report
from src.reports.html_report import generate_daily_html_report
from src.analyst.frontier_exporter import export_daily_snapshot_for_frontier_ai
from src.core.router import recommend_model
from src.core.normalizer import format_display_name

ICON_APP_PATH = "/home/tec/.local/share/icons/floydia_ai_suite.png"
DASHBOARD_PORT = 8333


def is_port_in_use(port: int = DASHBOARD_PORT) -> bool:
    """Comprueba si el puerto del dashboard web ya está activo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
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
        for _ in range(10):
            time.sleep(0.15)
            if is_port_in_use(port):
                return True
    except Exception as e:
        print(f"Error iniciando servidor web: {e}")
    return is_port_in_use(port)


# Estilos CSS QSS
FLOYDIA_QSS = """
QMainWindow {
    background-color: #070C14;
}
QWidget {
    background-color: #070C14;
    color: #F1F5F9;
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 13px;
}
QFrame#CardFrame {
    background-color: #0C1524;
    border: 1px solid #16263B;
    border-radius: 8px;
    padding: 12px;
}
QFrame#HeaderFrame {
    background-color: #0C1524;
    border-bottom: 2px solid #10D2AD;
}
QTabWidget::pane {
    border: 1px solid #16263B;
    background: #0C1524;
    border-radius: 6px;
}
QTabBar::tab {
    background: #0B111C;
    color: #94A3B8;
    padding: 9px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 700;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: #10D2AD;
    color: #070C14;
}
QPushButton#PrimaryBtn {
    background-color: #10D2AD;
    color: #070C14;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#PrimaryBtn:hover {
    background-color: #12E6BD;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #0B3830;
    color: #4A6B63;
}
QPushButton#SecondaryBtn {
    background-color: #16263B;
    color: #E2E8F0;
    border: 1px solid #233B59;
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#SecondaryBtn:hover {
    background-color: #213753;
    border: 1px solid #38BDF8;
}
QPushButton#SecondaryBtn:disabled {
    background-color: #0A1320;
    color: #475569;
    border: 1px solid #121F30;
}
QPushButton#DangerBtn {
    background-color: #3B161B;
    color: #F87171;
    border: 1px solid #7F1D1D;
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#DangerBtn:hover {
    background-color: #5C1D24;
    border: 1px solid #EF4444;
}
QPushButton#DangerBtn:disabled {
    background-color: #1A0D10;
    color: #5C2B30;
    border: 1px solid #2B1417;
}
QCheckBox {
    spacing: 8px;
    font-weight: 600;
    font-size: 12px;
    color: #E2E8F0;
}
QCheckBox:hover {
    color: #10D2AD;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #38BDF8;
    background-color: #0B111C;
}
QCheckBox::indicator:checked {
    background-color: #10D2AD;
    border: 1px solid #10D2AD;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: #070C14;
    border: 1px solid #1E3A5F;
    border-radius: 5px;
    color: #F5F8F7;
    padding: 5px 8px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #10D2AD;
}
QTableWidget {
    background-color: #070C14;
    border: 1px solid #16263B;
    border-radius: 6px;
    gridline-color: #121F30;
    color: #E2E8F0;
    selection-background-color: #16263B;
    selection-color: #10D2AD;
}
QHeaderView::section {
    background-color: #0C1524;
    color: #38BDF8;
    font-weight: 700;
    padding: 7px;
    border: 1px solid #16263B;
}
QProgressBar {
    background-color: #070C14;
    border: 1px solid #1E3A5F;
    border-radius: 5px;
    text-align: center;
    color: #FFFFFF;
    font-weight: 700;
    height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10D2AD, stop:1 #38BDF8);
    border-radius: 4px;
}
QPlainTextEdit {
    background-color: #070C14;
    border: 1px solid #16263B;
    border-radius: 6px;
    color: #E2E8F0;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 12px;
    padding: 8px;
}
"""


# ── WORKERS ASÍNCRONOS (QThread) PARA EVITAR CONGELAMIENTO DE UI ─────────────

class SuiteWorkerSignals(QObject):
    log = pyqtSignal(str, str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)


class SuiteWorker(QThread):
    def __init__(self, tasks: Dict[str, bool], probe_prompt: str = DEFAULT_PROBE_PROMPT):
        super().__init__()
        self.tasks = tasks
        self.probe_prompt = probe_prompt
        self.signals = SuiteWorkerSignals()

    def _ts_log(self, msg: str, lvl: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.signals.log.emit(f"[{ts}] {msg}", lvl)

    def run(self):
        active_steps = [k for k, v in self.tasks.items() if v]
        total_steps = len(active_steps)
        if total_steps == 0:
            self._ts_log("⚠️ No se seleccionó ninguna tarea.", "WARN")
            self.signals.finished.emit({})
            return

        current = 0

        # 1. Recolección de rankings globales
        if self.tasks.get("collect_rankings"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("🌐 [1/7] Recolectando Rankings Globales en Vivo...", "INFO")
            try:
                res = run_all_collectors()
                self._ts_log(f"  ↳ LMSYS Arena Elo: {res.get('lmsys', 0)} modelos", "INFO")
                self._ts_log(f"  ↳ Hugging Face Leaderboard: {res.get('hf', 0)} benchmarks", "INFO")
                self._ts_log(f"  ↳ OpenRouter API: {res.get('openrouter', 0)} modelos", "INFO")
                self._ts_log("  ✅ Rankings Globales sincronizados.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error recolectando rankings: {e}", "ERROR")

        # 2. Sondeo y auditoría de APIs locales
        if self.tasks.get("probe_apis"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("🔍 [2/7] Sondeando APIs Locales y Clúster Homelab...", "INFO")
            try:
                probe_res = run_local_api_probes()
                active_count = sum(1 for c in probe_res if c.get("is_functional"))
                self._ts_log(f"  ✅ Resumen: {active_count}/{len(probe_res)} APIs locales activas.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error en sonda local: {e}", "ERROR")

        # 3. Escaneo Profundo (Deep Probe con pregunta corta)
        if self.tasks.get("deep_scan"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log(f"🔬 [3/7] Ejecutando Escaneo Profundo (Prompt: '{self.probe_prompt}')...", "INFO")
            try:
                scan_res = run_deep_scan(prompt=self.probe_prompt)
                ok_count = sum(1 for r in scan_res if r.get("classification") == STATUS_OK)
                no_bal = sum(1 for r in scan_res if r.get("classification") == STATUS_NO_BALANCE)
                tier_ex = sum(1 for r in scan_res if r.get("classification") == STATUS_FREE_TIER_EXHAUSTED)
                unauth = sum(1 for r in scan_res if r.get("classification") == STATUS_UNAUTHORIZED)
                
                self._ts_log(f"  ↳ 🟢 Respuesta OK: {ok_count} modelos", "SUCCESS")
                if no_bal: self._ts_log(f"  ↳ 💳 Sin Saldo: {no_bal} modelos", "WARN")
                if tier_ex: self._ts_log(f"  ↳ ⏳ Free Tier Agotado: {tier_ex} modelos", "WARN")
                if unauth: self._ts_log(f"  ↳ 🔒 No Autorizado: {unauth} modelos", "WARN")
                self._ts_log(f"  ✅ Escaneo profundo completado sobre {len(scan_res)} modelos.", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error en escaneo profundo: {e}", "ERROR")

        # 4. Diagnóstico de IA
        if self.tasks.get("ai_diagnosis"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("🧠 [4/7] Generando Diagnóstico Ejecutivo con IA...", "INFO")
            try:
                diag = ask_observatory("Haz un resumen del estado del clúster y roles de modelos recomendados.")
                if diag.get("success"):
                    self._ts_log(f"  ✅ Motor IA Activo: {diag.get('engine')}", "SUCCESS")
                else:
                    self._ts_log(f"  ⚠️ Asesor: {diag.get('error', 'Sin respuesta')}", "WARN")
            except Exception as e:
                self._ts_log(f"  ❌ Error en diagnóstico: {e}", "ERROR")

        # 5. Reescribir e inyectar motores
        if self.tasks.get("inject_engines"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("⚡ [5/7] Reconfigurando OpenCode, Hermes y DeepSeek Harness...", "INFO")
            try:
                logs = apply_engine_configurations()
                for msg, lvl in logs:
                    self._ts_log(f"  {msg}", lvl)
            except Exception as e:
                self._ts_log(f"  ❌ Error inyectando motores: {e}", "ERROR")

        # 6. Sincronización HP45
        if self.tasks.get("sync_hp45"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("📡 [6/7] Sincronizando Clúster hacia HP45 (192.168.1.200)...", "INFO")
            try:
                msg, lvl = sync_to_hp45()
                self._ts_log(f"  {msg}", lvl)
            except Exception as e:
                self._ts_log(f"  ❌ Error sincronizando a HP45: {e}", "ERROR")

        # 7. Generación de informes
        if self.tasks.get("generate_reports"):
            current += 1
            self.signals.progress.emit(int(current / total_steps * 100))
            self._ts_log("📄 [7/7] Generando Informes Diarios...", "INFO")
            try:
                rankings = calculate_multidimensional_rankings()
                local_apis = get_latest_local_verified_models()
                md_f = generate_daily_markdown_report(rankings, local_apis)
                html_f = generate_daily_html_report(rankings, local_apis)
                export_daily_snapshot_for_frontier_ai(rankings, local_apis)
                self._ts_log(f"  ✅ Informe Markdown: {md_f.name}", "SUCCESS")
                self._ts_log(f"  ✅ Informe HTML: {html_f.name}", "SUCCESS")
            except Exception as e:
                self._ts_log(f"  ❌ Error generando informes: {e}", "ERROR")

        self.signals.progress.emit(100)
        self._ts_log("🎉 Pipeline ejecutado con éxito.", "SUCCESS")
        self.signals.finished.emit({})


class RankingDataLoaderSignals(QObject):
    loaded = pyqtSignal(list, dict)
    error = pyqtSignal(str)


class RankingDataLoaderWorker(QThread):
    def __init__(self):
        super().__init__()
        self.signals = RankingDataLoaderSignals()

    def run(self):
        try:
            models = calculate_multidimensional_rankings()
            deep_res = get_latest_deep_scan_results()
            deep_cache = {}
            for r in deep_res:
                mid = (r.get("model_id") or "").lower()
                mid_raw = r.get("model_id") or ""
                cname = (r.get("canonical_name") or "").lower()
                cname_raw = r.get("canonical_name") or ""
                prov = (r.get("provider_id") or "").lower()
                pdisp = (r.get("provider_display") or "").lower()
                
                deep_cache[mid] = r
                deep_cache[mid_raw] = r
                if cname:
                    deep_cache[cname] = r
                if cname_raw:
                    deep_cache[cname_raw] = r
                if prov and mid:
                    deep_cache[f"{prov}:{mid}"] = r
                if pdisp and mid:
                    deep_cache[f"{pdisp}:{mid}"] = r
            self.signals.loaded.emit(models, deep_cache)
        except Exception as e:
            self.signals.error.emit(str(e))


class DeepScanWorkerSignals(QObject):
    log = pyqtSignal(str, str)
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)


class DeepScanWorker(QThread):
    def __init__(self, prompt: str = DEFAULT_PROBE_PROMPT, selected_models: Optional[List[Dict[str, Any]]] = None, targets: Optional[List[Dict[str, Any]]] = None):
        super().__init__()
        self.prompt = prompt
        self.selected_models = selected_models
        self.targets = targets
        self.signals = DeepScanWorkerSignals()
        self._is_cancelled = False

    def _ts_log(self, msg: str, lvl: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.signals.log.emit(f"[{ts}] {msg}", lvl)

    def cancel(self):
        self._is_cancelled = True
        self.requestInterruption()

    def run(self):
        self._ts_log(f"🔬 Iniciando escaneo profundo (Prompt: '{self.prompt}')...", "INFO")
        
        def _prog_cb(completed: int, total: int, res: dict):
            if self._is_cancelled:
                return
            m_name = res.get("canonical_name") or res.get("model_id") or "Modelo"
            cls = res.get("classification", STATUS_ERROR)
            lat = res.get("latency_ms", 0.0)
            status_desc = f"{m_name} ({lat:.0f}ms) ➔ {STATUS_LABELS.get(cls, cls)}"
            self.signals.progress.emit(completed, total, status_desc)
            lvl = "SUCCESS" if cls == STATUS_OK else ("WARN" if cls in (STATUS_NO_BALANCE, STATUS_FREE_TIER_EXHAUSTED) else "ERROR")
            self._ts_log(f"  ↳ [{completed}/{total}] {status_desc}", lvl)

        try:
            results = run_deep_scan(
                prompt=self.prompt,
                progress_callback=_prog_cb,
                targets=self.targets,
                selected_models=self.selected_models
            )
            ok_c = sum(1 for r in results if r.get("classification") == STATUS_OK)
            self._ts_log(f"✅ Escaneo completado: {ok_c}/{len(results)} modelos con RESPUESTA_OK.", "SUCCESS")
            self.signals.finished.emit(results)
        except Exception as e:
            self._ts_log(f"❌ Error durante escaneo profundo: {e}", "ERROR")
            self.signals.finished.emit([])


class InjectionWorkerSignals(QObject):
    log = pyqtSignal(str, str)
    finished = pyqtSignal(list, str)


class InjectionWorker(QThread):
    def __init__(self, selected_models: List[Dict[str, Any]]):
        super().__init__()
        self.selected_models = selected_models
        self.signals = InjectionWorkerSignals()

    def _ts_log(self, msg: str, lvl: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.signals.log.emit(f"[{ts}] {msg}", lvl)

    def run(self):
        self._ts_log(f"⚡ Inyectando {len(self.selected_models)} modelos en OpenCode, Hermes y DSH...", "INFO")
        try:
            logs = apply_engine_configurations(self.selected_models)
            for m, lvl in logs:
                self._ts_log(f"  {m}", lvl)
            
            self._ts_log("📡 Sincronizando configuraciones a HP45 (192.168.1.200)...", "INFO")
            hp45_msg, hp45_lvl = sync_to_hp45()
            self._ts_log(f"  ↳ HP45: {hp45_msg}", hp45_lvl)
            
            self.signals.finished.emit(logs, hp45_msg)
        except Exception as e:
            self._ts_log(f"❌ Error en inyección / sincronización: {e}", "ERROR")
class CheckTableWidgetItem(QTableWidgetItem):
    """Permite ordenar la columna de checkboxes por estado marcado/desmarcado."""
    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):
            c1 = 1 if self.checkState() == Qt.CheckState.Checked else 0
            c2 = 1 if other.checkState() == Qt.CheckState.Checked else 0
            return c1 < c2
        return super().__lt__(other)


class StatusTableWidgetItem(QTableWidgetItem):
    """Permite ordenar la columna de estado del escáner según jerarquía de funcionalidad."""
    STATUS_ORDER = {
        STATUS_OK: 1,
        STATUS_NO_BALANCE: 2,
        STATUS_FREE_TIER_EXHAUSTED: 3,
        STATUS_UNAUTHORIZED: 4,
        STATUS_NO_RESPONSE: 5,
        STATUS_ERROR: 6,
        None: 7
    }

    def __init__(self, display_text: str, status_code: Optional[str] = None):
        super().__init__(display_text)
        self.status_code = status_code

    def __lt__(self, other):
        if isinstance(other, StatusTableWidgetItem):
            p1 = self.STATUS_ORDER.get(self.status_code, 99)
            p2 = self.STATUS_ORDER.get(other.status_code, 99)
            return p1 < p2
        return super().__lt__(other)


class NumericTableWidgetItem(QTableWidgetItem):
    """Permite ordenar columnas numéricas (Latencia en ms, Score FCI) por valor real y no alfabético."""
    def __init__(self, display_text: str, numeric_value: float):
        super().__init__(display_text)
        self.numeric_value = numeric_value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)


class FloydIASuiteWindow(QMainWindow):
    """Ventana Principal Ultra-Liviana de FloydIA AI Command & Observatory Suite v9.3."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FloydIA — AI Command & Observatory Suite v9.3")
        self.resize(1300, 900)
        if os.path.exists(ICON_APP_PATH):
            self.setWindowIcon(QIcon(ICON_APP_PATH))
        self.setStyleSheet(FLOYDIA_QSS)
        self._all_models_cache: List[Dict[str, Any]] = []
        self._deep_scan_cache: Dict[str, Dict[str, Any]] = {}
        
        # Debouncing para búsqueda en tiempo real
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self._apply_model_filters)
        
        self.worker: Optional[SuiteWorker] = None
        self._data_worker: Optional[RankingDataLoaderWorker] = None
        self._scan_worker: Optional[DeepScanWorker] = None
        self._inject_worker: Optional[InjectionWorker] = None

        self._init_ui()
        # Carga asíncrona no bloqueante
        QTimer.singleShot(50, self._load_models_into_explorer)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Header Frame ──────────────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 10)

        title_vbox = QVBoxLayout()
        title_lbl = QLabel("🛰️ FLOYDIA AI COMMAND & OBSERVATORY SUITE")
        title_lbl.setFont(QFont("IBM Plex Sans", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #10D2AD; letter-spacing: 0.5px;")
        sub_lbl = QLabel("Escáner Profundo Dinámico · Inyección Asíncrona · Telemetría HP15/HP45 · TokenRouter")
        sub_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        title_vbox.addWidget(title_lbl)
        title_vbox.addWidget(sub_lbl)
        header_layout.addLayout(title_vbox)

        header_layout.addStretch()

        html_btn = QPushButton("📄 Informe HTML")
        html_btn.setObjectName("SecondaryBtn")
        html_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        html_btn.clicked.connect(self._open_html_report)
        header_layout.addWidget(html_btn)

        web_btn = QPushButton("🌐 Dashboard (:8333)")
        web_btn.setObjectName("SecondaryBtn")
        web_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        web_btn.clicked.connect(self._open_web_dashboard)
        header_layout.addWidget(web_btn)

        main_layout.addWidget(header_frame)

        # ── Tab Widget ────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Control & Pipeline
        self.tab_pipeline = QWidget()
        self._setup_pipeline_tab()
        self.tabs.addTab(self.tab_pipeline, "🚀 Control & Pipeline")

        # Tab 2: Explorador, Escaneo Profundo & Inyector
        self.tab_explorer = QWidget()
        self._setup_explorer_tab()
        self.tabs.addTab(self.tab_explorer, "🔬 Escáner Profundo & Inyector de Modelos")

        # Tab 3: TokenRouter en Vivo
        self.tab_router = QWidget()
        self._setup_router_tab()
        self.tabs.addTab(self.tab_router, "⚡ TokenRouter")

    # ── TAB 1: PIPELINE & EJECUCIÓN ──────────────────────────────────────────
    def _setup_pipeline_tab(self):
        layout = QVBoxLayout(self.tab_pipeline)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        card_frame = QFrame()
        card_frame.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(8)

        card_title = QLabel("⚙️  TAREAS DEL PIPELINE PRINCIPAL (CHECKMARKS)")
        card_title.setFont(QFont("IBM Plex Sans", 11, QFont.Weight.Bold))
        card_title.setStyleSheet("color: #38BDF8;")
        card_layout.addWidget(card_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(6)

        self.chk_collect = QCheckBox("🌐 1. Recolectar Rankings Globales (LMSYS, HF, OpenRouter)")
        self.chk_collect.setChecked(False)
        grid.addWidget(self.chk_collect, 0, 0)

        self.chk_probe = QCheckBox("🔍 2. Sondear APIs Locales (Sonda Rápida de Salud)")
        self.chk_probe.setChecked(True)
        grid.addWidget(self.chk_probe, 0, 1)

        self.chk_deep_scan = QCheckBox("🔬 3. Escaneo Profundo (Pregunta Corta en 6 Estados)")
        self.chk_deep_scan.setChecked(True)
        grid.addWidget(self.chk_deep_scan, 1, 0)

        self.chk_ai = QCheckBox("🧠 4. Diagnóstico Ejecutivo con IA (Asesor Local)")
        self.chk_ai.setChecked(False)
        grid.addWidget(self.chk_ai, 1, 1)

        self.chk_inject = QCheckBox("⚡ 5. Inyectar Modelos OK a OpenCode, Hermes y DSH")
        self.chk_inject.setChecked(True)
        grid.addWidget(self.chk_inject, 2, 0)

        self.chk_sync = QCheckBox("📡 6. Sincronizar Clúster HP15 ➔ HP45 (192.168.1.200)")
        self.chk_sync.setChecked(True)
        grid.addWidget(self.chk_sync, 2, 1)

        self.chk_reports = QCheckBox("📄 7. Generar Informes Diarios (Markdown & HTML)")
        self.chk_reports.setChecked(False)
        grid.addWidget(self.chk_reports, 3, 0)

        card_layout.addLayout(grid)

        # Prompt input para escaneo
        prompt_hbox = QHBoxLayout()
        prompt_hbox.addWidget(QLabel("💬 Prompt de Prueba para Escaneo:"))
        self.txt_probe_prompt = QLineEdit(DEFAULT_PROBE_PROMPT)
        prompt_hbox.addWidget(self.txt_probe_prompt, stretch=2)
        card_layout.addLayout(prompt_hbox)

        sel_hbox = QHBoxLayout()
        btn_all = QPushButton("Seleccionar Todo")
        btn_all.setObjectName("SecondaryBtn")
        btn_all.clicked.connect(self._select_all)
        btn_none = QPushButton("Deseleccionar Todo")
        btn_none.setObjectName("SecondaryBtn")
        btn_none.clicked.connect(self._deselect_all)
        btn_deep_only = QPushButton("🔬 Solo Escaneo + Inyección")
        btn_deep_only.setObjectName("SecondaryBtn")
        btn_deep_only.clicked.connect(self._select_deep_only)
        btn_clear_log = QPushButton("🧹 Limpiar Consola")
        btn_clear_log.setObjectName("SecondaryBtn")
        btn_clear_log.clicked.connect(self._clear_console)

        sel_hbox.addWidget(btn_all)
        sel_hbox.addWidget(btn_none)
        sel_hbox.addWidget(btn_deep_only)
        sel_hbox.addWidget(btn_clear_log)
        sel_hbox.addStretch()
        card_layout.addLayout(sel_hbox)

        layout.addWidget(card_frame)

        action_hbox = QHBoxLayout()
        self.prog_bar = QProgressBar()
        self.prog_bar.setValue(0)
        action_hbox.addWidget(self.prog_bar, stretch=3)

        self.run_btn = QPushButton("🚀 EJECUTAR PIPELINE SELECCIONADO")
        self.run_btn.setObjectName("PrimaryBtn")
        self.run_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.run_btn.clicked.connect(self._start_pipeline)
        action_hbox.addWidget(self.run_btn, stretch=1)

        layout.addLayout(action_hbox)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        ts_now = datetime.now().strftime("%H:%M:%S")
        self.console.appendPlainText(f"[{ts_now}] 🟢 [FloydIA Suite v9.3] Listo. Selecciona las tareas y presiona Ejecutar.")
        layout.addWidget(self.console)

    # ── TAB 2: EXPLORADOR, ESCANEO PROFUNDO & FILTROS 6 ESTADOS ─────────────
    def _setup_explorer_tab(self):
        layout = QVBoxLayout(self.tab_explorer)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        filter_card = QFrame()
        filter_card.setObjectName("CardFrame")
        f_layout = QVBoxLayout(filter_card)
        f_layout.setSpacing(8)

        f_title = QLabel("🎛️ FILTROS REACTIVOS DE ESTADO DE RESPUESTA (6 ESTADOS)")
        f_title.setFont(QFont("IBM Plex Sans", 11, QFont.Weight.Bold))
        f_title.setStyleSheet("color: #38BDF8;")
        f_layout.addWidget(f_title)

        f_grid = QGridLayout()
        f_grid.setHorizontalSpacing(16)
        f_grid.setVerticalSpacing(6)

        self.chk_status_ok = QCheckBox("🟢 Solo Respuesta OK (100% Funcional)")
        self.chk_status_ok.setChecked(False)
        self.chk_status_ok.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_status_ok, 0, 0)

        self.chk_status_no_balance = QCheckBox("💳 Sin Saldo (HTTP 402 / Créditos)")
        self.chk_status_no_balance.setChecked(False)
        self.chk_status_no_balance.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_status_no_balance, 0, 1)

        self.chk_status_rate_limit = QCheckBox("⏳ Free Tier Agotado (429 Rate Limit)")
        self.chk_status_rate_limit.setChecked(False)
        self.chk_status_rate_limit.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_status_rate_limit, 0, 2)

        self.chk_status_auth = QCheckBox("🔒 No Autorizado (401/403)")
        self.chk_status_auth.setChecked(False)
        self.chk_status_auth.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_status_auth, 1, 0)

        self.chk_status_timeout = QCheckBox("⏱️ Sin Respuesta / Timeout (>5s)")
        self.chk_status_timeout.setChecked(False)
        self.chk_status_timeout.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_status_timeout, 1, 1)

        self.chk_status_error = QCheckBox("⚠️ Error de Modelo / Gateway (5xx/404)")
        self.chk_status_error.setChecked(False)
        self.chk_status_error.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_status_error, 1, 2)

        self.chk_filter_free = QCheckBox("💸 Solo Gratuitos ($0)")
        self.chk_filter_free.setChecked(False)
        self.chk_filter_free.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_filter_free, 2, 0)

        self.chk_filter_vision = QCheckBox("👁️ Visión / Multimodal")
        self.chk_filter_vision.setChecked(False)
        self.chk_filter_vision.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_filter_vision, 2, 1)

        self.chk_filter_tools = QCheckBox("⚙️ Function Calling / Tools")
        self.chk_filter_tools.setChecked(False)
        self.chk_filter_tools.stateChanged.connect(self._on_filter_changed)
        f_grid.addWidget(self.chk_filter_tools, 2, 2)

        f_layout.addLayout(f_grid)

        # Fila 1: Búsqueda y Selección Rápida
        search_hbox = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Buscar por modelo, proveedor o ID...")
        self.txt_search.textChanged.connect(self._on_search_text_changed)
        search_hbox.addWidget(self.txt_search, stretch=2)

        self.btn_sel_all = QPushButton("☑️ Marcar Todo")
        self.btn_sel_all.setObjectName("SecondaryBtn")
        self.btn_sel_all.clicked.connect(self._select_table_all)
        search_hbox.addWidget(self.btn_sel_all)

        self.btn_sel_ok = QPushButton("🟢 Marcar Solo OK")
        self.btn_sel_ok.setObjectName("SecondaryBtn")
        self.btn_sel_ok.clicked.connect(self._select_table_ok_only)
        search_hbox.addWidget(self.btn_sel_ok)

        self.btn_desel_all = QPushButton("⬜ Desmarcar")
        self.btn_desel_all.setObjectName("SecondaryBtn")
        self.btn_desel_all.clicked.connect(self._deselect_table_all)
        search_hbox.addWidget(self.btn_desel_all)

        self.lbl_model_count = QLabel("Modelos: 0")
        self.lbl_model_count.setStyleSheet("color: #10D2AD; font-weight: 700;")
        search_hbox.addWidget(self.lbl_model_count)

        f_layout.addLayout(search_hbox)

        # Fila 2: Acciones Directas de Sonda e Inyección
        action_row = QHBoxLayout()
        
        self.btn_probe_selected = QPushButton("🔬 PROBAR SELECCIONADOS")
        self.btn_probe_selected.setObjectName("PrimaryBtn")
        self.btn_probe_selected.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_probe_selected.setToolTip("Ejecuta la sonda profunda sobre los modelos marcados con el checkbox")
        self.btn_probe_selected.clicked.connect(self._run_deep_scan_selected)
        action_row.addWidget(self.btn_probe_selected)

        self.btn_probe_visible = QPushButton("🌐 Probar Todos los Visibles")
        self.btn_probe_visible.setObjectName("SecondaryBtn")
        self.btn_probe_visible.setToolTip("Ejecuta la sonda sobre todos los modelos visibles en la tabla")
        self.btn_probe_visible.clicked.connect(self._run_deep_scan_visible)
        action_row.addWidget(self.btn_probe_visible)

        self.btn_run_deep = QPushButton("🔬 Escanear Catálogo Base")
        self.btn_run_deep.setObjectName("SecondaryBtn")
        self.btn_run_deep.clicked.connect(self._run_deep_scan_direct)
        action_row.addWidget(self.btn_run_deep)

        self.btn_inject_selected = QPushButton("⚡ INYECTAR SELECCIONADOS")
        self.btn_inject_selected.setObjectName("PrimaryBtn")
        self.btn_inject_selected.clicked.connect(self._inject_selected_models)
        action_row.addWidget(self.btn_inject_selected)

        self.btn_cancel_tab2 = QPushButton("⏹️ Detener")
        self.btn_cancel_tab2.setObjectName("DangerBtn")
        self.btn_cancel_tab2.setEnabled(False)
        self.btn_cancel_tab2.clicked.connect(self._cancel_tab2_action)
        action_row.addWidget(self.btn_cancel_tab2)

        action_row.addStretch()
        f_layout.addLayout(action_row)

        # Fila 3: Barra de progreso y estado en tiempo real de Tab 2
        progress_row = QVBoxLayout()
        self.tab2_prog_bar = QProgressBar()
        self.tab2_prog_bar.setValue(0)
        self.tab2_prog_bar.setVisible(False)
        progress_row.addWidget(self.tab2_prog_bar)

        self.tab2_lbl_status = QLabel("🟢 Listo. Marca modelos con el checkbox y pulsa 'Probar Seleccionados' o 'Inyectar'.")
        self.tab2_lbl_status.setStyleSheet("color: #94A3B8; font-size: 11px;")
        progress_row.addWidget(self.tab2_lbl_status)
        f_layout.addLayout(progress_row)

        layout.addWidget(filter_card)

        # Tabla de Modelos con Checkbox por Fila
        self.table_models = QTableWidget()
        self.table_models.setColumnCount(7)
        self.table_models.setHorizontalHeaderLabels([
            "Sel",
            "Nombre Estandarizado [Contexto•Costo] (Proveedor)",
            "Estado del Escáner (6 Estados)",
            "Latencia",
            "Extracto de Respuesta / Detalle",
            "Tier / Categoría",
            "Score FCI"
        ])
        self.table_models.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_models.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_models.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_models.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_models.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_models.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table_models.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table_models.horizontalHeader().setSectionsClickable(True)
        self.table_models.horizontalHeader().setSortIndicatorShown(True)
        self.table_models.setSortingEnabled(True)
        self.table_models.setAlternatingRowColors(True)
        layout.addWidget(self.table_models)

    # ── TAB 3: TOKENROUTER EN VIVO ───────────────────────────────────────────
    def _setup_router_tab(self):
        layout = QVBoxLayout(self.tab_router)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        ctrl_card = QFrame()
        ctrl_card.setObjectName("CardFrame")
        c_layout = QVBoxLayout(ctrl_card)

        c_title = QLabel("⚡ ENRUTADOR DINÁMICO DE TOKENS (TOKENROUTER)")
        c_title.setFont(QFont("IBM Plex Sans", 11, QFont.Weight.Bold))
        c_title.setStyleSheet("color: #38BDF8;")
        c_layout.addWidget(c_title)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(14)
        form_grid.setVerticalSpacing(8)

        form_grid.addWidget(QLabel("🎯 Tarea Objetivo:"), 0, 0)
        self.cmb_task = QComboBox()
        self.cmb_task.addItems([
            "general (Propósito General)",
            "coding (Programación & Copiloto)",
            "reasoning (Matemáticas & Lógica STEM)",
            "fast (Inferencia de Ultra-Velocidad)"
        ])
        form_grid.addWidget(self.cmb_task, 0, 1)

        form_grid.addWidget(QLabel("💰 Presupuesto / Costo:"), 0, 2)
        self.cmb_budget = QComboBox()
        self.cmb_budget.addItems([
            "any (Cualquiera / Balance Óptimo)",
            "free (100% Gratuito / $0)",
            "economy (Bajo Costo < $1.5/M)",
            "frontier (Máxima Calidad SOTA)"
        ])
        form_grid.addWidget(self.cmb_budget, 0, 3)

        form_grid.addWidget(QLabel("⏱️ Latencia Máxima (ms):"), 1, 0)
        self.spn_latency = QSpinBox()
        self.spn_latency.setRange(0, 10000)
        self.spn_latency.setValue(0)
        self.spn_latency.setSpecialValueText("Sin límite")
        form_grid.addWidget(self.spn_latency, 1, 1)

        form_grid.addWidget(QLabel("📚 Contexto Mínimo:"), 1, 2)
        self.spn_context = QSpinBox()
        self.spn_context.setRange(2000, 2000000)
        self.spn_context.setSingleStep(4000)
        self.spn_context.setValue(4000)
        form_grid.addWidget(self.spn_context, 1, 3)

        self.chk_router_tools = QCheckBox("Requiere Tools")
        self.chk_router_vision = QCheckBox("Requiere Visión")
        self.chk_router_reasoning = QCheckBox("Requiere Razonamiento")
        self.chk_router_local_only = QCheckBox("Solo APIs Verificadas")
        self.chk_router_local_only.setChecked(True)

        req_hbox = QHBoxLayout()
        req_hbox.addWidget(self.chk_router_tools)
        req_hbox.addWidget(self.chk_router_vision)
        req_hbox.addWidget(self.chk_router_reasoning)
        req_hbox.addWidget(self.chk_router_local_only)
        c_layout.addLayout(form_grid)
        c_layout.addLayout(req_hbox)

        btn_route = QPushButton("🎯 CONSULTAR TOKENROUTER")
        btn_route.setObjectName("PrimaryBtn")
        btn_route.clicked.connect(self._run_token_router)
        c_layout.addWidget(btn_route)

        layout.addWidget(ctrl_card)

        # Tarjeta de Resultados
        self.res_card = QFrame()
        self.res_card.setObjectName("CardFrame")
        res_layout = QVBoxLayout(self.res_card)

        res_title = QLabel("🏆 MODELO ÓPTIMO RECOMENDADO")
        res_title.setFont(QFont("IBM Plex Sans", 11, QFont.Weight.Bold))
        res_title.setStyleSheet("color: #10D2AD;")
        res_layout.addWidget(res_title)

        self.lbl_recommended_model = QLabel("Presiona 'Consultar TokenRouter'...")
        self.lbl_recommended_model.setFont(QFont("JetBrains Mono", 13, QFont.Weight.Bold))
        self.lbl_recommended_model.setStyleSheet("color: #FFFFFF; padding: 4px 0;")
        res_layout.addWidget(self.lbl_recommended_model)

        self.lbl_router_reason = QLabel("")
        self.lbl_router_reason.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.lbl_router_reason.setWordWrap(True)
        res_layout.addWidget(self.lbl_router_reason)

        res_layout.addWidget(QLabel("🔀 Cascada de Alternativas (Fallbacks):"))
        self.lbl_router_fallbacks = QLabel("—")
        self.lbl_router_fallbacks.setStyleSheet("color: #38BDF8; font-family: 'JetBrains Mono';")
        res_layout.addWidget(self.lbl_router_fallbacks)

        layout.addWidget(self.res_card)
        layout.addStretch()

    # ── MÉTODOS DE CARGA ASÍNCRONA Y FILTRADO DE TABLA ───────────────────────
    def _load_models_into_explorer(self):
        """Carga en memoria los modelos del ranking y el escaneo profundo en segundo plano."""
        self.lbl_model_count.setText("⏳ Cargando catálogo y rankings...")
        self.tab2_lbl_status.setText("⏳ Calculando métricas y recuperando historial de escaneo...")
        
        self._data_worker = RankingDataLoaderWorker()
        self._data_worker.signals.loaded.connect(self._on_rankings_loaded)
        self._data_worker.signals.error.connect(self._on_rankings_error)
        self._data_worker.start()

    def _on_rankings_loaded(self, models: list, deep_cache: dict):
        self._all_models_cache = models
        self._deep_scan_cache = deep_cache
        self.tab2_lbl_status.setText(f"🟢 {len(models)} modelos en catálogo cargados con éxito.")
        self._apply_model_filters()

    def _on_rankings_error(self, err_msg: str):
        self.lbl_model_count.setText("❌ Error cargando modelos")
        self.tab2_lbl_status.setText(f"❌ Error calculando rankings: {err_msg}")

    def _on_search_text_changed(self):
        self._search_timer.start()

    def _on_filter_changed(self):
        self._apply_model_filters()

    def _apply_model_filters(self):
        if not self._all_models_cache:
            return

        query = self.txt_search.text().strip().lower()
        filter_ok = self.chk_status_ok.isChecked()
        filter_no_bal = self.chk_status_no_balance.isChecked()
        filter_rate = self.chk_status_rate_limit.isChecked()
        filter_auth = self.chk_status_auth.isChecked()
        filter_timeout = self.chk_status_timeout.isChecked()
        filter_err = self.chk_status_error.isChecked()

        any_state_filter = filter_ok or filter_no_bal or filter_rate or filter_auth or filter_timeout or filter_err

        free_only = self.chk_filter_free.isChecked()
        vision_only = self.chk_filter_vision.isChecked()
        tools_only = self.chk_filter_tools.isChecked()

        filtered = []
        for m in self._all_models_cache:
            d_name = format_display_name(m)
            c_name = (m.get("canonical_name") or "").lower()
            m_id = (m.get("id") or "").lower()
            m_id_raw = m.get("id") or ""
            m_id = m_id_raw.lower()
            c_name_raw = m.get("canonical_name") or ""
            c_name = c_name_raw.lower()
            prov = (m.get("provider") or "").lower()

            if query and query not in d_name.lower() and query not in c_name and query not in m_id and query not in prov:
                continue

            # Buscar en caché de escaneo profundo con múltiples claves
            scan_info = (
                self._deep_scan_cache.get(f"{prov}:{m_id}")
                or self._deep_scan_cache.get(m_id)
                or self._deep_scan_cache.get(c_name)
                or self._deep_scan_cache.get(m_id_raw)
                or self._deep_scan_cache.get(c_name_raw)
            )
            cls = scan_info.get("classification") if scan_info else (STATUS_OK if m.get("is_local_active") else None)

            if any_state_filter:
                match_state = False
                if filter_ok and cls == STATUS_OK: match_state = True
                if filter_no_bal and cls == STATUS_NO_BALANCE: match_state = True
                if filter_rate and cls == STATUS_FREE_TIER_EXHAUSTED: match_state = True
                if filter_auth and cls == STATUS_UNAUTHORIZED: match_state = True
                if filter_timeout and cls == STATUS_NO_RESPONSE: match_state = True
                if filter_err and cls == STATUS_ERROR: match_state = True
                if not match_state:
                    continue

            if free_only and not m.get("is_free_tier"):
                continue
            if vision_only and not m.get("supports_vision"):
                continue
            if tools_only and not m.get("supports_tools"):
                continue

            filtered.append((m, scan_info, cls))

        # Renderizado ultra-eficiente
        self.table_models.setSortingEnabled(False)
        self.table_models.setUpdatesEnabled(False)
        self.table_models.blockSignals(True)
        self.lbl_model_count.setText(f"Modelos visibles: {len(filtered)} / {len(self._all_models_cache)}")
        self.table_models.setRowCount(len(filtered))

        for row, (m, scan_info, cls) in enumerate(filtered):
            # Col 0: Checkbox (CheckTableWidgetItem)
            chk_item = CheckTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Checked if cls == STATUS_OK else Qt.CheckState.Unchecked)
            self.table_models.setItem(row, 0, chk_item)

            # Col 1: Nombre Estandarizado
            disp_name = format_display_name(m)
            item_name = QTableWidgetItem(disp_name)
            item_name.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
            if cls == STATUS_OK:
                item_name.setForeground(QColor("#10D2AD"))
            self.table_models.setItem(row, 1, item_name)

            # Col 2: Estado del Escáner (StatusTableWidgetItem)
            status_txt = STATUS_LABELS.get(cls, "⚪ Sin Escanear") if cls else "⚪ Sin Escanear"
            item_status = StatusTableWidgetItem(status_txt, cls)
            if cls == STATUS_OK:
                item_status.setForeground(QColor("#10D2AD"))
            elif cls in (STATUS_NO_BALANCE, STATUS_FREE_TIER_EXHAUSTED):
                item_status.setForeground(QColor("#F59E0B"))
            elif cls in (STATUS_UNAUTHORIZED, STATUS_ERROR):
                item_status.setForeground(QColor("#EF4444"))
            self.table_models.setItem(row, 2, item_status)

            # Col 3: Latencia (NumericTableWidgetItem)
            lat = scan_info.get("latency_ms") if scan_info else m.get("local_latency_ms")
            lat_str = f"{round(lat, 0):.0f}ms" if lat is not None else "—"
            lat_val = float(lat) if lat is not None else 999999.0
            item_lat = NumericTableWidgetItem(lat_str, lat_val)
            item_lat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_models.setItem(row, 3, item_lat)

            # Col 4: Extracto de respuesta
            snip = scan_info.get("response_snippet") if scan_info else m.get("evidence_grade", "—")
            item_snip = QTableWidgetItem(str(snip)[:45])
            self.table_models.setItem(row, 4, item_snip)

            # Col 5: Tier
            tier = (m.get("tier") or "workhorse").upper()
            item_tier = QTableWidgetItem(tier)
            item_tier.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_models.setItem(row, 5, item_tier)

            # Col 6: Score FCI (NumericTableWidgetItem)
            fci = round(m.get("intelligence_score") or 0.0, 1)
            item_fci = NumericTableWidgetItem(f"{fci}/100", fci)
            item_fci.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_models.setItem(row, 6, item_fci)

        self.table_models.blockSignals(False)
        self.table_models.setUpdatesEnabled(True)
        self.table_models.setSortingEnabled(True)

    # ── ACCIONES DE SELECCIÓN E INYECCIÓN ────────────────────────────────────
    def _select_table_ok_only(self):
        self.table_models.blockSignals(True)
        for row in range(self.table_models.rowCount()):
            status_item = self.table_models.item(row, 2)
            chk_item = self.table_models.item(row, 0)
            if chk_item:
                if status_item and "🟢" in status_item.text():
                    chk_item.setCheckState(Qt.CheckState.Checked)
                else:
                    chk_item.setCheckState(Qt.CheckState.Unchecked)
        self.table_models.blockSignals(False)

    def _select_table_all(self):
        self.table_models.blockSignals(True)
        for row in range(self.table_models.rowCount()):
            item = self.table_models.item(row, 0)
            if item: item.setCheckState(Qt.CheckState.Checked)
        self.table_models.blockSignals(False)

    def _deselect_table_all(self):
        self.table_models.blockSignals(True)
        for row in range(self.table_models.rowCount()):
            item = self.table_models.item(row, 0)
            if item: item.setCheckState(Qt.CheckState.Unchecked)
        self.table_models.blockSignals(False)

    def _get_selected_table_models(self) -> List[Dict[str, Any]]:
        selected = []
        for row in range(self.table_models.rowCount()):
            chk_item = self.table_models.item(row, 0)
            if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                name_item = self.table_models.item(row, 1)
                # Buscar objeto en cache
                for m in self._all_models_cache:
                    if format_display_name(m) == name_item.text():
                        selected.append({
                            "provider": m.get("provider", "openrouter"),
                            "provider_id": m.get("provider", "openrouter"),
                            "id": m.get("id"),
                            "model_id": m.get("id"),
                            "canonical_name": m.get("canonical_name", m.get("id")),
                            "context_window": m.get("context_window", 128000),
                            "is_free_tier": m.get("is_free_tier", False),
                            "supports_tools": m.get("supports_tools", True),
                            "supports_vision": m.get("supports_vision", False)
                        })
                        break
        return selected

    def _get_visible_table_models(self) -> List[Dict[str, Any]]:
        visible = []
        for row in range(self.table_models.rowCount()):
            name_item = self.table_models.item(row, 1)
            if not name_item:
                continue
            for m in self._all_models_cache:
                if format_display_name(m) == name_item.text():
                    visible.append({
                        "provider": m.get("provider", "openrouter"),
                        "provider_id": m.get("provider", "openrouter"),
                        "id": m.get("id"),
                        "model_id": m.get("id"),
                        "canonical_name": m.get("canonical_name", m.get("id")),
                        "context_window": m.get("context_window", 128000),
                        "is_free_tier": m.get("is_free_tier", False),
                        "supports_tools": m.get("supports_tools", True),
                        "supports_vision": m.get("supports_vision", False)
                    })
                    break
        return visible

    def _set_tab2_busy(self, busy: bool):
        self.btn_probe_selected.setEnabled(not busy)
        self.btn_probe_visible.setEnabled(not busy)
        self.btn_run_deep.setEnabled(not busy)
        self.btn_inject_selected.setEnabled(not busy)
        self.btn_cancel_tab2.setEnabled(busy)
        self.tab2_prog_bar.setVisible(busy)

    def _cancel_tab2_action(self):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self.tab2_lbl_status.setText("⏹️ Escaneo detenido por el usuario.")
            self._set_tab2_busy(False)

    def _run_deep_scan_selected(self):
        selected = self._get_selected_table_models()
        if not selected:
            QMessageBox.warning(self, "Atención", "No has marcado ningún modelo con el checkbox. Marca al menos uno para probar.")
            return

        prompt = self.txt_probe_prompt.text().strip() or DEFAULT_PROBE_PROMPT
        self._set_tab2_busy(True)
        self.tab2_prog_bar.setValue(0)
        self.tab2_prog_bar.setMaximum(len(selected))
        self.tab2_lbl_status.setText(f"🔬 Probando {len(selected)} modelos seleccionados...")
        self._append_log(f"\n🔬 Probando {len(selected)} modelos seleccionados en segundo plano...", "INFO")

        self._scan_worker = DeepScanWorker(prompt=prompt, selected_models=selected)
        self._scan_worker.signals.log.connect(self._append_log)
        self._scan_worker.signals.progress.connect(self._on_deep_scan_progress)
        self._scan_worker.signals.finished.connect(self._on_deep_scan_finished)
        self._scan_worker.start()

    def _run_deep_scan_visible(self):
        visible = self._get_visible_table_models()
        if not visible:
            QMessageBox.warning(self, "Atención", "No hay modelos visibles en la tabla para probar.")
            return

        prompt = self.txt_probe_prompt.text().strip() or DEFAULT_PROBE_PROMPT
        self._set_tab2_busy(True)
        self.tab2_prog_bar.setValue(0)
        self.tab2_prog_bar.setMaximum(len(visible))
        self.tab2_lbl_status.setText(f"🔬 Probando {len(visible)} modelos visibles...")
        self._append_log(f"\n🔬 Probando {len(visible)} modelos visibles en segundo plano...", "INFO")

        self._scan_worker = DeepScanWorker(prompt=prompt, selected_models=visible)
        self._scan_worker.signals.log.connect(self._append_log)
        self._scan_worker.signals.progress.connect(self._on_deep_scan_progress)
        self._scan_worker.signals.finished.connect(self._on_deep_scan_finished)
        self._scan_worker.start()

    def _run_deep_scan_direct(self):
        prompt = self.txt_probe_prompt.text().strip() or DEFAULT_PROBE_PROMPT
        self._set_tab2_busy(True)
        self.tab2_prog_bar.setValue(0)
        self.tab2_prog_bar.setMaximum(100)
        self.tab2_lbl_status.setText("🔬 Escaneando catálogo base...")
        self._append_log(f"\n🔬 Iniciando Escaneo Profundo directo del catálogo base (Prompt: '{prompt}')...", "INFO")

        self._scan_worker = DeepScanWorker(prompt=prompt)
        self._scan_worker.signals.log.connect(self._append_log)
        self._scan_worker.signals.progress.connect(self._on_deep_scan_progress)
        self._scan_worker.signals.finished.connect(self._on_deep_scan_finished)
        self._scan_worker.start()

    def _on_deep_scan_progress(self, completed: int, total: int, status_desc: str):
        self.tab2_prog_bar.setMaximum(total)
        self.tab2_prog_bar.setValue(completed)
        self.tab2_lbl_status.setText(f"🔬 [{completed}/{total}] {status_desc}")

    def _on_deep_scan_finished(self, results: list):
        self._set_tab2_busy(False)
        ok_count = sum(1 for r in results if r.get("classification") == STATUS_OK)
        self.tab2_lbl_status.setText(f"✅ Escaneo finalizado: {ok_count}/{len(results)} modelos con Respuesta OK.")
        # Recargar datos sin bloquear UI
        self._load_models_into_explorer()

    def _inject_selected_models(self):
        selected = self._get_selected_table_models()
        if not selected:
            QMessageBox.warning(self, "Atención", "No has marcado ningún modelo con el checkbox. Selecciona al menos uno.")
            return

        self._set_tab2_busy(True)
        self.tab2_lbl_status.setText(f"⚡ Inyectando {len(selected)} modelos y sincronizando clúster HP45...")
        self._append_log(f"\n⚡ Iniciando inyección asíncrona de {len(selected)} modelos...", "INFO")

        self._inject_worker = InjectionWorker(selected)
        self._inject_worker.signals.log.connect(self._append_log)
        self._inject_worker.signals.finished.connect(self._on_injection_finished)
        self._inject_worker.start()

    def _on_injection_finished(self, logs: list, hp45_msg: str):
        self._set_tab2_busy(False)
        self.tab2_lbl_status.setText(f"✅ Inyección completada. {hp45_msg}")
        msg_lines = "\n".join([f"• {m}" for m, _ in logs])
        msg_lines += f"\n\n📡 Sincronización a HP45:\n• {hp45_msg}"
        QMessageBox.information(self, "Motores Reconfigurados con Éxito", f"Se han inyectado los modelos seleccionados en OpenCode, Hermes y DSH:\n\n{msg_lines}")

    # ── TOKENROUTER ──────────────────────────────────────────────────────────
    def _run_token_router(self):
        task_val = self.cmb_task.currentText().split(" ")[0]
        budget_val = self.cmb_budget.currentText().split(" ")[0]
        max_lat = self.spn_latency.value() if self.spn_latency.value() > 0 else None
        ctx = self.spn_context.value()

        try:
            res = recommend_model(
                task=task_val,
                budget=budget_val,
                max_latency_ms=max_lat,
                context_required=ctx,
                requires_tools=self.chk_router_tools.isChecked(),
                requires_vision=self.chk_router_vision.isChecked(),
                requires_reasoning=self.chk_router_reasoning.isChecked(),
                requires_coding=(task_val == "coding"),
                prefer_local_only=self.chk_router_local_only.isChecked()
            )
            rec = res.get("recommended_model", {})
            d_name = rec.get("display_name") or format_display_name(rec)
            self.lbl_recommended_model.setText(f"🎯 {d_name}")
            self.lbl_router_reason.setText(f"💡 {rec.get('reason', '')}")

            fallbacks = res.get("cascading_fallbacks", [])
            if fallbacks:
                fb_texts = [f"• [{fb.get('reason', 'Alt')}] {fb.get('display_name', format_display_name(fb))}" for fb in fallbacks]
                self.lbl_router_fallbacks.setText("\n".join(fb_texts))
            else:
                self.lbl_router_fallbacks.setText("No se requirieron fallbacks.")
        except Exception as e:
            self.lbl_recommended_model.setText(f"❌ Error en TokenRouter: {e}")

    # ── HELPERS & PIPELINE ───────────────────────────────────────────────────
    def _select_all(self):
        for chk in [self.chk_collect, self.chk_probe, self.chk_deep_scan, self.chk_ai, self.chk_inject, self.chk_sync, self.chk_reports]:
            chk.setChecked(True)

    def _deselect_all(self):
        for chk in [self.chk_collect, self.chk_probe, self.chk_deep_scan, self.chk_ai, self.chk_inject, self.chk_sync, self.chk_reports]:
            chk.setChecked(False)

    def _select_deep_only(self):
        self._deselect_all()
        self.chk_deep_scan.setChecked(True)
        self.chk_inject.setChecked(True)
        self.chk_sync.setChecked(True)

    def _clear_console(self):
        self.console.clear()
        ts_now = datetime.now().strftime("%H:%M:%S")
        self.console.appendPlainText(f"[{ts_now}] 🟢 Consola reiniciada.")

    def _open_html_report(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        html_file = DAILY_REPORTS_DIR / f"{today_str}_informe_ia_floydia.html"
        if not html_file.exists():
            reports = sorted(DAILY_REPORTS_DIR.glob("*_informe_ia_floydia.html"), reverse=True)
            if reports: html_file = reports[0]

        if html_file.exists():
            webbrowser.open(f"file://{html_file.resolve()}")
        else:
            self._append_log("⚠️ No se encontró informe HTML generado. Ejecuta primero la tarea 7.", "WARN")

    def _open_web_dashboard(self):
        if not is_port_in_use(DASHBOARD_PORT):
            ensure_dashboard_server(DASHBOARD_PORT)
        webbrowser.open(f"http://localhost:{DASHBOARD_PORT}")

    def _start_pipeline(self):
        tasks = {
            "collect_rankings": self.chk_collect.isChecked(),
            "probe_apis": self.chk_probe.isChecked(),
            "deep_scan": self.chk_deep_scan.isChecked(),
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

        prompt = self.txt_probe_prompt.text().strip() or DEFAULT_PROBE_PROMPT
        self.worker = SuiteWorker(tasks, probe_prompt=prompt)
        self.worker.signals.log.connect(self._append_log)
        self.worker.signals.progress.connect(self.prog_bar.setValue)
        self.worker.signals.finished.connect(self._pipeline_finished)
        self.worker.start()

    def _append_log(self, msg: str, level: str = "INFO"):
        self.console.appendPlainText(msg)
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.ensureCursorVisible()

    def _pipeline_finished(self, res: dict):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("🚀 EJECUTAR PIPELINE SELECCIONADO")
        self._load_models_into_explorer()

    def closeEvent(self, event):
        for w in [self.worker, self._data_worker, self._scan_worker, self._inject_worker]:
            if w and w.isRunning():
                w.requestInterruption()
                w.wait(1500)
        event.accept()


def run_gui_suite():
    app = QApplication(sys.argv)
    window = FloydIASuiteWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui_suite()
