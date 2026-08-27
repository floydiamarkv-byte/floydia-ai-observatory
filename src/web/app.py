"""
Servidor y Dashboard Web Interactivo de FloydIA AI Rankings & Local API Observatory v7.0.
Incluye:
- 10 categorías especializadas (Frontier, Agentes, Razonamiento, Visión, Contexto 1M+, Caballos, Coding, Soberanos, Realtime, Edge).
- Botones de Recomendación Rápida ("Smart Pills").
- Generador de Snippets de Código (Python SDK / cURL) en 1 clic dentro del Modal.
- Selector de fuentes y ordenamiento bidireccional Free Tier + Score.
- Comparador Visual Cara a Cara (Model VS Model Side-by-Side) con Veredicto FloydIA.
"""

import http.server
import socketserver
import json
import urllib.parse
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from config.settings import BASE_DIR, DAILY_REPORTS_DIR, FRONTIER_EXPORT_DIR
from src.core.scoring import calculate_multidimensional_rankings
from src.core.db import get_latest_local_verified_models
from src.probers.local_verifier import run_local_api_probes
from src.collectors.aggregator import run_all_collectors
from src.reports.markdown_report import generate_daily_markdown_report
from src.reports.html_report import generate_daily_html_report
from src.analyst.frontier_exporter import export_daily_snapshot_for_frontier_ai
from src.analyst.ai_advisor import ask_observatory
from src.core.engine_injector import apply_engine_configurations, sync_to_hp45


class FloydIAWebServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/rankings":
                rankings = calculate_multidimensional_rankings()
                self._send_json(rankings)
                return

            elif path == "/api/local-apis":
                local_apis = get_latest_local_verified_models()
                self._send_json(local_apis)
                return

            elif path == "/download/report":
                today_str = datetime.now().strftime("%Y-%m-%d")
                report_file = DAILY_REPORTS_DIR / f"{today_str}_informe_ia_floydia.md"
                if not report_file.exists():
                    rankings = calculate_multidimensional_rankings()
                    local_apis = get_latest_local_verified_models()
                    report_file = generate_daily_markdown_report(rankings, local_apis)
                self._send_file_download(report_file, f"{today_str}_informe_ia_floydia.md")
                return

            elif path == "/download/frontier":
                today_str = datetime.now().strftime("%Y-%m-%d")
                frontier_file = FRONTIER_EXPORT_DIR / f"{today_str}_SNAPSHOT_FOR_FRONTIER_AI.md"
                if not frontier_file.exists():
                    rankings = calculate_multidimensional_rankings()
                    local_apis = get_latest_local_verified_models()
                    frontier_file = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
                self._send_file_download(frontier_file, f"{today_str}_SNAPSHOT_FOR_FRONTIER_AI.md")
                return

            elif path == "/" or path == "/index.html":
                self._render_dashboard()
                return

            super().do_GET()
        except Exception as e:
            traceback.print_exc()
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error 500: {e}".encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/action/probe":
            results = run_local_api_probes()
            self._send_json({"success": True, "tested_count": len(results), "results": results})
            return

        elif path == "/api/action/collect":
            results = run_all_collectors()
            self._send_json({"success": True, "collectors": results})
            return

        elif path == "/api/action/ask":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                req_data = json.loads(body)
                query = req_data.get("query", "")
            except Exception:
                query = ""
            result = ask_observatory(query)
            self._send_json(result)
            return

        elif path == "/api/action/generate-reports":
            rankings = calculate_multidimensional_rankings()
            local_apis = get_latest_local_verified_models()
            md_path = generate_daily_markdown_report(rankings, local_apis)
            frontier_path = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
            self._send_json({
                "success": True,
                "markdown_report": str(md_path),
                "frontier_snapshot": str(frontier_path)
            })
            return

        elif path == "/api/action/apply-configs":
            logs = apply_engine_configurations()
            self._send_json({"success": True, "logs": logs})
            return

        elif path == "/api/action/sync-hp45":
            msg, lvl = sync_to_hp45()
            self._send_json({"success": (lvl == "SUCCESS"), "message": msg, "level": lvl})
            return

        self.send_response(404)
        self.end_headers()

    def _send_json(self, data: Any):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _send_file_download(self, filepath: Path, filename: str):
        if not filepath.exists():
            self.send_response(404)
            self.end_headers()
            return
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _render_dashboard(self):
        rankings = calculate_multidimensional_rankings()
        today_str = datetime.now().strftime("%Y-%m-%d")
        rankings_json = json.dumps(rankings).replace("</", "<\\/")

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FloydIA — AI Rankings & Local API Observatory v7.0</title>
  <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --floydia-teal: #10D2AD;
      --floydia-cyan: #10D6BD;
      --floydia-mint: #70CBAC;
      --floydia-navy: #152638;
      --floydia-ink: #0B111C;
      --floydia-card: #111C2B;
      --floydia-card-hover: #162438;
      --floydia-border: #1F3347;
      --floydia-border-glow: rgba(16, 210, 173, 0.4);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'IBM Plex Sans', sans-serif;
      background-color: var(--floydia-ink);
      color: #E2E8F0;
      padding: 24px;
      line-height: 1.5;
    }}
    .container {{ max-width: 1540px; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--floydia-border);
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .brand-title {{
      font-family: 'Chakra Petch', sans-serif;
      font-size: 30px;
      font-weight: 700;
      color: #FFFFFF;
      letter-spacing: -0.01em;
    }}
    .brand-title span {{ color: var(--floydia-teal); }}
    .brand-sub {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: var(--floydia-mint);
      margin-top: 4px;
    }}
    .action-bar {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .btn {{
      background: var(--floydia-navy);
      border: 1px solid var(--floydia-teal);
      color: var(--floydia-teal);
      padding: 8px 14px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      background: var(--floydia-teal);
      color: var(--floydia-ink);
      box-shadow: 0 0 12px rgba(16, 210, 173, 0.3);
    }}
    .btn-primary {{
      background: var(--floydia-teal);
      color: var(--floydia-ink);
      border-color: var(--floydia-cyan);
    }}
    .btn-primary:hover {{
      background: var(--floydia-cyan);
    }}
    .btn-free {{
      background: rgba(16, 185, 129, 0.2);
      border-color: #10B981;
      color: #6EE7B7;
      font-weight: 700;
    }}
    .btn-free:hover {{
      background: #10B981;
      color: var(--floydia-ink);
      box-shadow: 0 0 14px rgba(16, 185, 129, 0.4);
    }}
    .btn-vs {{
      background: rgba(139, 92, 246, 0.2);
      border-color: #8B5CF6;
      color: #DDD6FE;
      font-weight: 700;
    }}
    .btn-vs:hover {{
      background: #8B5CF6;
      color: #FFFFFF;
      box-shadow: 0 0 14px rgba(139, 92, 246, 0.4);
    }}

    /* SMART RECOMENDACIÓN PILLS */
    .smart-pills-bar {{
      display: flex;
      gap: 8px;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .smart-pill-title {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #94A3B8;
      text-transform: uppercase;
      margin-right: 4px;
    }}
    .smart-pill {{
      background: rgba(21, 38, 56, 0.6);
      border: 1px solid var(--floydia-border);
      color: #CBD5E1;
      padding: 5px 11px;
      border-radius: 20px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.15s ease;
      user-select: none;
    }}
    .smart-pill:hover {{
      background: var(--floydia-navy);
      border-color: var(--floydia-teal);
      color: #FFFFFF;
      transform: translateY(-1px);
    }}
    .smart-pill.active {{
      background: var(--floydia-teal);
      color: var(--floydia-ink);
      border-color: var(--floydia-cyan);
      font-weight: 700;
    }}

    .control-panel {{
      background: var(--floydia-card);
      border: 1px solid var(--floydia-border);
      border-radius: 10px;
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
    }}
    .search-box {{
      position: relative;
      min-width: 220px;
    }}
    .search-input {{
      width: 100%;
      background: var(--floydia-ink);
      border: 1px solid var(--floydia-border);
      color: #FFFFFF;
      padding: 8px 14px 8px 34px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s ease;
    }}
    .search-input:focus {{
      border-color: var(--floydia-teal);
      box-shadow: 0 0 8px rgba(16, 210, 173, 0.2);
    }}
    .search-icon {{
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--floydia-mint);
      font-size: 14px;
    }}
    .dropdown-group {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #94A3B8;
    }}
    .dropdown-select {{
      background: var(--floydia-ink);
      border: 1px solid var(--floydia-border);
      color: #FFFFFF;
      padding: 7px 12px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 600;
      outline: none;
      cursor: pointer;
      transition: border-color 0.2s ease;
    }}
    .dropdown-select:focus {{
      border-color: var(--floydia-teal);
    }}
    .dropdown-select option {{
      background: var(--floydia-card);
      color: #FFFFFF;
    }}
    .checkbox-group {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .check-label {{
      display: flex;
      align-items: center;
      gap: 5px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      cursor: pointer;
      color: #CBD5E1;
      user-select: none;
      background: rgba(21, 38, 56, 0.4);
      padding: 4px 8px;
      border-radius: 5px;
      border: 1px solid var(--floydia-border);
    }}
    .check-label input[type="checkbox"] {{
      accent-color: var(--floydia-teal);
      width: 14px;
      height: 14px;
      cursor: pointer;
    }}
    .check-label-free {{
      background: rgba(16, 185, 129, 0.15);
      border-color: #059669;
      color: #6EE7B7;
      font-weight: 600;
    }}
    .card {{
      background: var(--floydia-card);
      border: 1px solid var(--floydia-border);
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }}
    .card-title {{
      font-family: 'Chakra Petch', sans-serif;
      font-size: 19px;
      color: #FFFFFF;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .card-subtext {{
      font-size: 13px;
      color: #94A3B8;
      margin-bottom: 14px;
    }}
    .badge-local {{
      background: #064E3B;
      color: var(--floydia-teal);
      padding: 3px 8px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid #059669;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .badge-external {{
      background: #1F2937;
      color: #9CA3AF;
      padding: 3px 8px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      border: 1px solid #374151;
    }}
    .tier-badge {{
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      text-transform: uppercase;
      display: inline-block;
    }}
    .tier-frontier {{ background: rgba(99, 102, 241, 0.2); color: #A5B4FC; border: 1px solid #6366F1; }}
    .tier-agentic {{ background: rgba(236, 72, 153, 0.2); color: #F472B6; border: 1px solid #EC4899; }}
    .tier-reasoning {{ background: rgba(139, 92, 246, 0.2); color: #C4B5FD; border: 1px solid #8B5CF6; }}
    .tier-multimodal {{ background: rgba(6, 182, 212, 0.2); color: #67E8F9; border: 1px solid #06B6D4; }}
    .tier-long_context {{ background: rgba(245, 158, 11, 0.2); color: #FCD34D; border: 1px solid #F59E0B; }}
    .tier-workhorse {{ background: rgba(59, 130, 246, 0.2); color: #93C5FD; border: 1px solid #3B82F6; }}
    .tier-coding {{ background: rgba(16, 185, 129, 0.2); color: #6EE7B7; border: 1px solid #10B981; }}
    .tier-uncensored {{ background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid #EF4444; }}
    .tier-realtime {{ background: rgba(250, 204, 21, 0.2); color: #FEF08A; border: 1px solid #FACC15; }}
    .tier-edge {{ background: rgba(100, 116, 139, 0.2); color: #CBD5E1; border: 1px solid #64748B; }}
    .source-tag {{
      background: rgba(21, 38, 56, 0.8);
      color: #94A3B8;
      border: 1px solid #1E3A5F;
      font-size: 10px;
      padding: 1px 5px;
      border-radius: 3px;
      font-family: 'JetBrains Mono', monospace;
      margin-right: 4px;
      margin-bottom: 2px;
      display: inline-block;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th {{
      font-family: 'JetBrains Mono', monospace;
      color: var(--floydia-mint);
      background: rgba(21, 38, 56, 0.7);
      font-size: 12px;
      text-transform: uppercase;
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--floydia-border);
      cursor: pointer;
      user-select: none;
      transition: background 0.15s ease, color 0.15s ease;
      white-space: nowrap;
    }}
    th:hover {{
      background: var(--floydia-navy);
      color: #FFFFFF;
    }}
    th .sort-arrow {{
      font-size: 10px;
      margin-left: 4px;
      opacity: 0.6;
    }}
    th.sorted-asc .sort-arrow, th.sorted-desc .sort-arrow {{
      opacity: 1;
      color: var(--floydia-teal);
    }}
    td {{
      padding: 9px 12px;
      text-align: left;
      border-bottom: 1px solid var(--floydia-border);
    }}
    tr.model-row {{
      cursor: pointer;
      transition: background 0.15s ease;
    }}
    tr.model-row:hover {{
      background: var(--floydia-card-hover);
    }}
    tr.model-row:hover td:first-child {{
      border-left: 3px solid var(--floydia-teal);
    }}
    .code-val {{ font-family: 'JetBrains Mono', monospace; }}
    .score-val {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      color: var(--floydia-teal);
    }}
    .free-badge {{
      background: rgba(16, 185, 129, 0.2);
      color: #34D399;
      border: 1px solid #059669;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      display: inline-block;
    }}
    .mini-vs-btn {{
      background: rgba(139, 92, 246, 0.25);
      border: 1px solid #8B5CF6;
      color: #DDD6FE;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .mini-vs-btn:hover {{
      background: #8B5CF6;
      color: #FFFFFF;
      transform: scale(1.05);
    }}

    /* MODALES ESTILO FLOYDIA */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(11, 17, 28, 0.88);
      backdrop-filter: blur(8px);
      z-index: 10000;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .modal-overlay.active {{
      display: flex;
    }}
    .modal-box {{
      background: var(--floydia-card);
      border: 1px solid var(--floydia-teal);
      border-radius: 12px;
      max-width: 880px;
      width: 100%;
      max-height: 92vh;
      overflow-y: auto;
      box-shadow: 0 0 35px rgba(16, 210, 173, 0.25);
      animation: modalFadeIn 0.25s ease-out;
    }}
    .modal-box-wide {{
      max-width: 1200px;
      border-color: #8B5CF6;
      box-shadow: 0 0 40px rgba(139, 92, 246, 0.25);
    }}
    @keyframes modalFadeIn {{
      from {{ opacity: 0; transform: translateY(-15px) scale(0.98); }}
      to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    .modal-header {{
      padding: 20px 24px;
      border-bottom: 1px solid var(--floydia-border);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .modal-title {{
      font-family: 'Chakra Petch', sans-serif;
      font-size: 24px;
      color: #FFFFFF;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .modal-close {{
      background: transparent;
      border: none;
      color: #94A3B8;
      font-size: 22px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      transition: color 0.15s ease;
    }}
    .modal-close:hover {{
      color: #FFFFFF;
      background: rgba(255, 255, 255, 0.1);
    }}
    .modal-body {{
      padding: 24px;
      font-size: 14px;
    }}
    .modal-section {{
      margin-bottom: 20px;
    }}
    .modal-section-title {{
      font-family: 'Chakra Petch', sans-serif;
      font-size: 16px;
      color: var(--floydia-mint);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .modal-desc {{
      color: #E2E8F0;
      line-height: 1.6;
      background: rgba(21, 38, 56, 0.3);
      padding: 12px 16px;
      border-radius: 6px;
      border-left: 3px solid var(--floydia-teal);
    }}
    .use-cases-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .use-cases-list li {{
      background: rgba(21, 38, 56, 0.5);
      padding: 10px 14px;
      border-radius: 6px;
      border: 1px solid var(--floydia-border);
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }}
    .use-cases-list li::before {{
      content: "✦";
      color: var(--floydia-teal);
      font-weight: bold;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }}
    .stat-card {{
      background: var(--floydia-ink);
      border: 1px solid var(--floydia-border);
      padding: 12px;
      border-radius: 6px;
      text-align: center;
    }}
    .stat-label {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #94A3B8;
      text-transform: uppercase;
    }}
    .stat-value {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 18px;
      font-weight: 700;
      color: var(--floydia-teal);
      margin-top: 4px;
    }}

    /* SNIPPET DE CÓDIGO INTERACTIVO */
    .snippet-container {{
      background: var(--floydia-ink);
      border: 1px solid var(--floydia-border);
      border-radius: 8px;
      padding: 14px;
      position: relative;
    }}
    .snippet-tabs {{
      display: flex;
      gap: 8px;
      margin-bottom: 10px;
      border-bottom: 1px solid var(--floydia-border);
      padding-bottom: 8px;
    }}
    .snippet-tab {{
      background: transparent;
      border: none;
      color: #94A3B8;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
    }}
    .snippet-tab.active {{
      background: var(--floydia-navy);
      color: var(--floydia-teal);
      font-weight: 700;
    }}
    .code-pre {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #E2E8F0;
      overflow-x: auto;
      white-space: pre;
      background: #070C14;
      padding: 12px;
      border-radius: 6px;
    }}
    .copy-btn {{
      position: absolute;
      top: 14px;
      right: 14px;
      background: var(--floydia-navy);
      border: 1px solid var(--floydia-teal);
      color: var(--floydia-teal);
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 4px;
      cursor: pointer;
    }}
    .copy-btn:hover {{
      background: var(--floydia-teal);
      color: var(--floydia-ink);
    }}

    /* COMPARADOR VS LADO A LADO */
    .vs-presets-bar {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 18px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--floydia-border);
    }}
    .vs-selectors-grid {{
      display: grid;
      grid-template-columns: 1fr 60px 1fr;
      gap: 16px;
      align-items: center;
      margin-bottom: 24px;
    }}
    @media (max-width: 860px) {{
      .vs-selectors-grid {{ grid-template-columns: 1fr; }}
    }}
    .vs-badge-center {{
      text-align: center;
      font-family: 'Chakra Petch', sans-serif;
      font-size: 22px;
      font-weight: 700;
      color: #DDD6FE;
      background: #6D28D9;
      width: 44px;
      height: 44px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto;
      box-shadow: 0 0 16px rgba(139, 92, 246, 0.5);
    }}
    .vs-columns-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}
    @media (max-width: 860px) {{
      .vs-columns-grid {{ grid-template-columns: 1fr; }}
    }}
    .vs-card {{
      background: rgba(21, 38, 56, 0.4);
      border: 1px solid var(--floydia-border);
      border-radius: 10px;
      padding: 18px;
    }}
    .vs-card.model-a {{
      border-top: 3px solid var(--floydia-teal);
    }}
    .vs-card.model-b {{
      border-top: 3px solid #8B5CF6;
    }}
    .vs-metric-row {{
      margin-bottom: 14px;
    }}
    .vs-metric-header {{
      display: flex;
      justify-content: space-between;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .vs-bar-track {{
      background: #0B111C;
      height: 8px;
      border-radius: 4px;
      overflow: hidden;
      display: flex;
    }}
    .vs-bar-fill-a {{
      background: var(--floydia-teal);
      height: 100%;
      transition: width 0.3s ease;
    }}
    .vs-bar-fill-b {{
      background: #8B5CF6;
      height: 100%;
      transition: width 0.3s ease;
    }}
    .vs-verdict-box {{
      background: rgba(139, 92, 246, 0.12);
      border: 1px solid #8B5CF6;
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 20px;
    }}
    .vs-diff-winner {{
      color: #34D399;
      font-weight: 700;
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
    }}

    /* AI ADVISOR CARD */
    .ai-advisor-card {{
      background: linear-gradient(135deg, rgba(17, 28, 43, 0.95), rgba(21, 38, 56, 0.95));
      border: 1px solid var(--floydia-teal);
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 24px;
      box-shadow: 0 0 20px rgba(16, 210, 173, 0.15);
    }}
    .ai-advisor-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .ai-advisor-title {{
      font-family: 'Chakra Petch', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: #FFFFFF;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .ai-advisor-title span {{
      color: var(--floydia-teal);
    }}
    .ai-advisor-sub {{
      font-size: 13px;
      color: #94A3B8;
      margin-bottom: 14px;
    }}
    .ai-advisor-input-box {{
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .ai-advisor-input {{
      flex: 1;
      background: var(--floydia-ink);
      border: 1px solid var(--floydia-border);
      color: #FFFFFF;
      padding: 12px 16px;
      border-radius: 8px;
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }}
    .ai-advisor-input:focus {{
      border-color: var(--floydia-teal);
      box-shadow: 0 0 12px rgba(16, 210, 173, 0.3);
    }}
    .ai-advisor-btn {{
      background: var(--floydia-teal);
      color: var(--floydia-ink);
      border: none;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 13px;
      padding: 0 22px;
      border-radius: 8px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .ai-advisor-btn:hover {{
      background: var(--floydia-cyan);
      box-shadow: 0 0 16px rgba(16, 210, 173, 0.4);
      transform: translateY(-1px);
    }}
    .quick-prompts-bar {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .quick-prompt-label {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: var(--floydia-mint);
    }}
    .quick-prompt-pill {{
      background: rgba(16, 210, 173, 0.08);
      border: 1px solid rgba(16, 210, 173, 0.3);
      color: #E2E8F0;
      padding: 4px 10px;
      border-radius: 16px;
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .quick-prompt-pill:hover {{
      background: rgba(16, 210, 173, 0.25);
      border-color: var(--floydia-teal);
      color: #FFFFFF;
    }}
    .ai-advisor-result-card {{
      background: var(--floydia-ink);
      border: 1px solid var(--floydia-border-glow);
      border-radius: 8px;
      padding: 18px 20px;
      margin-top: 16px;
      display: none;
      animation: fadeIn 0.3s ease;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(-6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .ai-result-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--floydia-border);
    }}
    .ai-engine-tag {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      color: var(--floydia-teal);
      background: rgba(16, 210, 173, 0.12);
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid rgba(16, 210, 173, 0.3);
    }}
    .ai-result-content {{
      color: #E2E8F0;
      font-size: 13.5px;
      line-height: 1.6;
      white-space: pre-wrap;
      font-family: 'IBM Plex Sans', sans-serif;
    }}

    footer {{
      text-align: center;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--floydia-border);
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #64748B;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <div class="brand-title">FLOYD<span>IA</span> AI OBSERVATORY <span>v7.5</span></div>
        <div class="brand-sub">SISTEMA MULTIDIMENSIONAL DE RANKINGS, ARSENAL LOCAL & ASESOR IA · {today_str}</div>
      </div>
      <div class="action-bar">
        <button class="btn btn-vs" onclick="openVsModal()">⚔️ Comparar Modelos (VS)</button>
        <button class="btn btn-free" onclick="setSortMode('free_score_desc')">🆓 Gratuitos Top Score</button>
        <button class="btn btn-primary" onclick="runProbe()">⚡ Probar APIs</button>
        <button class="btn" style="border-color: #10D2AD; color: #10D2AD; font-weight: 700;" onclick="runApplyConfigs()">⚙️ Inyectar a Motores</button>
        <button class="btn" style="border-color: #38BDF8; color: #38BDF8;" onclick="runSyncHp45()">📡 Sincronizar HP45</button>
        <button class="btn" onclick="runCollect()">🔄 Actualizar Rankings</button>
        <a href="/download/report" class="btn">📥 Informe (.md)</a>
        <a href="/download/frontier" class="btn" style="border-color: #8B5CF6; color: #C4B5FD;">📋 Snapshot Frontier (.md)</a>
      </div>
    </header>

    <!-- AI ADVISOR CARD (CONSULTAS EN LENGUAJE NATURAL) -->
    <div class="ai-advisor-card">
      <div class="ai-advisor-header">
        <div class="ai-advisor-title">🤖 FLOYD<span>IA</span> AI ADVISOR <span>· Consultor Inteligente en Vivo</span></div>
        <span class="ai-engine-tag" id="advisorStatusBadge">⚡ Grounding Activo (Rankings + APIs PC)</span>
      </div>
      <div class="ai-advisor-sub">Pregunta en lenguaje natural cuál modelo es el mejor, más barato o más rápido para tu caso de uso específico.</div>
      <div class="ai-advisor-input-box">
        <input type="text" id="advisorInput" class="ai-advisor-input" placeholder="Ej: Según tu criterio, ¿cuál es la mejor y más barata para scraping y extracción de datos JSON?" onkeydown="if(event.key==='Enter') submitAdvisorQuestion()">
        <button id="advisorBtn" class="ai-advisor-btn" onclick="submitAdvisorQuestion()">Preguntar a la IA 🚀</button>
      </div>
      <div class="quick-prompts-bar">
        <span class="quick-prompt-label">Sugerencias:</span>
        <span class="quick-prompt-pill" onclick="setAdvisorPreset('Según tu criterio, ¿cuál es la mejor y más barata para scraping y extracción de datos JSON?')">⚡ Scraping & Extracción JSON</span>
        <span class="quick-prompt-pill" onclick="setAdvisorPreset('¿Cuál es la mejor opción gratuita activa en mi PC para escribir código en Python?')">💻 Programar Gratis en mi PC</span>
        <span class="quick-prompt-pill" onclick="setAdvisorPreset('¿Qué modelo Frontier tiene el razonamiento más potente para lógica matemática y algoritmos complejos?')">🧠 Máximo Razonamiento Frontier</span>
        <span class="quick-prompt-pill" onclick="setAdvisorPreset('¿Cuál modelo tiene la menor latencia (TTFT) y mayor velocidad para un asistente en tiempo real?')">⏱️ Menor Latencia / Streaming</span>
      </div>

      <div id="advisorResultCard" class="ai-advisor-result-card">
        <div class="ai-result-top">
          <span id="advisorResultEngine" class="ai-engine-tag">Motor: DeepSeek V3 Grounded</span>
          <button class="btn" style="padding: 4px 10px; font-size: 11px;" onclick="copyAdvisorText()">📋 Copiar Respuesta</button>
        </div>
        <div id="advisorResultBody" class="ai-result-content"></div>
      </div>
    </div>

    <!-- SMART RECOMENDACIÓN RÁPIDA -->
    <div class="smart-pills-bar">
      <span class="smart-pill-title">🎯 Recomiéndame el mejor para:</span>
      <span class="smart-pill" onclick="applyPreset('coding_free')">💻 Programar Gratis</span>
      <span class="smart-pill" onclick="applyPreset('agentic')">🤖 Agentes Autónomos</span>
      <span class="smart-pill" onclick="applyPreset('long_doc')">📚 Documentos Gigantes (1M+)</span>
      <span class="smart-pill" onclick="applyPreset('stem_reasoning')">🧠 Matemáticas & Lógica</span>
      <span class="smart-pill" onclick="applyPreset('realtime')">⚡ Chatbot Ultrarrápido</span>
      <span class="smart-pill" onclick="applyPreset('uncensored')">🛡️ Sin Filtro / Pentesting</span>
      <span class="smart-pill" style="border-color: #64748B; color: #94A3B8;" onclick="applyPreset('reset')">🔄 Ver Todos</span>
    </div>

    <!-- PANEL DE CONTROL Y FILTROS -->
    <div class="control-panel">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" class="search-input" placeholder="Buscar modelo o proveedor..." oninput="filterAndRender()">
      </div>

      <!-- DESPLEGABLE DE FUENTES DE CONSULTA -->
      <div class="dropdown-group">
        <span>📡 Fuente:</span>
        <select id="sourceSelect" class="dropdown-select" onchange="filterAndRender()">
          <option value="all">🌐 Todas las Fuentes (6 Benchmarks + APIs)</option>
          <option value="LMSYS Arena">🏆 LMSYS Chatbot Arena (Elo)</option>
          <option value="Artificial Analysis">⚡ Artificial Analysis (Velocidad & Precios)</option>
          <option value="OpenRouter">🛒 OpenRouter (Catálogo & Adopción)</option>
          <option value="Hugging Face">🎓 Hugging Face Leaderboard (Académico)</option>
          <option value="LiveBench">🔬 LiveBench (Sin contaminación)</option>
          <option value="Epoch AI">🧪 Epoch AI (Ciencia & Cómputo)</option>
          <option value="Google AI Studio">🔷 Google AI Studio (Gemini)</option>
          <option value="DeepSeek">🐋 DeepSeek API (V3 / R1)</option>
          <option value="Hermes">🦅 Hermes / Soberanos</option>
        </select>
      </div>

      <!-- DESPLEGABLE DE ORDENAMIENTO -->
      <div class="dropdown-group">
        <span>📶 Ordenar:</span>
        <select id="sortSelect" class="dropdown-select" style="border-color: var(--floydia-teal); color: #34D399;" onchange="onSortSelectChange()">
          <option value="free_score_desc">🆓 Gratuitos Primero + Mayor Score</option>
          <option value="score_desc">🧠 Mayor Inteligencia Global (Score)</option>
          <option value="score_asc">📉 Menor Inteligencia Global</option>
          <option value="workhorse_desc">⚡ Mayor Eficiencia (Caballo Batalla)</option>
          <option value="coding_desc">💻 Mayor Rendimiento en Coding</option>
          <option value="price_asc">💰 Menor Precio ($/1M Tokens)</option>
          <option value="price_desc">💎 Mayor Precio ($/1M Tokens)</option>
          <option value="local_first">🟢 Activos en mi PC Primero</option>
          <option value="context_desc">📚 Mayor Ventana de Contexto</option>
          <option value="name_asc">🔤 Nombre Alfabético (A-Z)</option>
        </select>
      </div>

      <!-- 10 CATEGORÍAS ESPECIALIZADAS -->
      <div class="checkbox-group">
        <label class="check-label check-label-free">
          <input type="checkbox" id="filterFreeOnly" onchange="filterAndRender()"> 🆓 Gratis
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterLocalOnly" onchange="filterAndRender()"> 🟢 En PC
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterFrontier" checked onchange="filterAndRender()"> 👑 Frontier
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterAgentic" checked onchange="filterAndRender()"> 🤖 Agentes
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterReasoning" checked onchange="filterAndRender()"> 🧠 Razonamiento
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterMultimodal" checked onchange="filterAndRender()"> 👁️ Visión
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterLongContext" checked onchange="filterAndRender()"> 📚 1M+ Contexto
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterWorkhorse" checked onchange="filterAndRender()"> ⚡ Caballos
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterCoding" checked onchange="filterAndRender()"> 💻 Coding
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterUncensored" checked onchange="filterAndRender()"> 🛡️ Soberanos
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterRealtime" checked onchange="filterAndRender()"> ⚡ Realtime
        </label>
        <label class="check-label">
          <input type="checkbox" id="filterEdge" checked onchange="filterAndRender()"> 📱 Edge
        </label>
      </div>
    </div>

    <!-- SECCIÓN 1: ARSENAL LOCAL (EN TU PC) -->
    <div class="card" style="border-left: 4px solid var(--floydia-teal);">
      <div class="card-title">
        <span>🟢 Modelos Activos y Verificados en tu Computadora</span>
        <span style="font-size: 13px; font-family: 'JetBrains Mono'; color: var(--floydia-mint);" id="localCountBadge">0 modelos</span>
      </div>
      <div class="card-subtext">Haz clic en cualquier modelo para ver su ficha técnica o en <strong>VS</strong> para compararlo directamente.</div>
      <div style="overflow-x: auto;">
        <table>
          <thead>
            <tr>
              <th onclick="sortTable('localTable', 0)">Modelo Local <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('localTable', 1)">Proveedor <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('localTable', 2)">Categoría <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('localTable', 3)">Contexto <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('localTable', 4)">Latencia <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('localTable', 5)">Precio / 1M <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('localTable', 6)">Score <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('localTable', 7)">Estado Sonda <span class="sort-arrow">↕</span></th>
              <th style="cursor: default;">Acción</th>
            </tr>
          </thead>
          <tbody id="localTableBody"></tbody>
        </table>
      </div>
    </div>

    <!-- SECCIÓN 2: TABLA GENERAL DE RANKINGS -->
    <div class="card">
      <div class="card-title">
        <span>📊 Tabla Global de Rankings y Benchmarks Multidimensional</span>
        <span style="font-size: 13px; font-family: 'JetBrains Mono'; color: #94A3B8;" id="totalCountBadge">0 modelos</span>
      </div>
      <div class="card-subtext">Haz clic en cualquier fila para ficha completa o en el botón <strong>VS</strong> para enfrentarlo cara a cara.</div>
      <div style="overflow-x: auto;">
        <table id="rankingsTable">
          <thead>
            <tr>
              <th onclick="sortTable('globalTable', 0)">Rank <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 1)">Modelo <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 2)">Disponibilidad <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 3)">Categoría <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 4)">Inteligencia <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 5)">Eficiencia Batalla <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 6)">Coding <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 7)">Elo LMSYS <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 8)">Precio / 1M <span class="sort-arrow">↕</span></th>
              <th onclick="sortTable('globalTable', 9)">Fuentes de Datos <span class="sort-arrow">↕</span></th>
              <th style="cursor: default;">Acción</th>
            </tr>
          </thead>
          <tbody id="globalTableBody"></tbody>
        </table>
      </div>
    </div>

    <footer>
      <p>«Construimos la inteligencia. Desde la infraestructura.» — <strong>FloydIA</strong></p>
      <p style="margin-top: 4px; color: #475569;">«Desde la infraestructura, todo.»</p>
    </footer>
  </div>

  <!-- POP-UP MODAL DE DETALLE DEL MODELO -->
  <div class="modal-overlay" id="modelModal" onclick="closeModalOnBackdrop(event)">
    <div class="modal-box">
      <div class="modal-header">
        <div>
          <div class="modal-title" id="modalTitle">
            <span id="modalModelName">Modelo</span>
            <span id="modalLocalBadge"></span>
            <span id="modalTierBadge"></span>
          </div>
          <div style="font-family: 'JetBrains Mono'; font-size: 13px; color: var(--floydia-mint); margin-top: 4px;" id="modalProvider">Proveedor</div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
          <button class="btn btn-vs" style="padding: 4px 10px; font-size: 11px;" onclick="compareFromModal()">⚔️ Comparar en VS</button>
          <button class="modal-close" onclick="closeModal()">✖</button>
        </div>
      </div>
      <div class="modal-body">
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-label">Inteligencia Global</div>
            <div class="stat-value" id="modalIntelScore">0 / 100</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Eficiencia Batalla</div>
            <div class="stat-value" id="modalWorkhorseScore">0 / 100</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Score Coding</div>
            <div class="stat-value" id="modalCodingScore">0 / 100</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Ventana Contexto</div>
            <div class="stat-value" id="modalContextWindow">0 tok</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Precio ($/1M)</div>
            <div class="stat-value" id="modalPricing">Gratis</div>
          </div>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">📖 Descripción y Arquitectura</div>
          <div class="modal-desc" id="modalDescription"></div>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">💡 Usos Típicos Recomendados</div>
          <ul class="use-cases-list" id="modalUseCases"></ul>
        </div>

        <!-- GENERADOR DE CÓDIGO LISTO PARA USAR -->
        <div class="modal-section">
          <div class="modal-section-title">💻 Snippet de Código Listo para Integrar</div>
          <div class="snippet-container">
            <button class="copy-btn" onclick="copySnippet()">📋 Copiar Código</button>
            <div class="snippet-tabs">
              <button class="snippet-tab active" onclick="switchTab('python')">Python (OpenAI SDK)</button>
              <button class="snippet-tab" onclick="switchTab('curl')">cURL / Terminal</button>
            </div>
            <div class="code-pre" id="snippetCode"></div>
          </div>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">⚔️ Comparativa de Rendimiento</div>
          <div class="modal-desc" id="modalComparison" style="border-left-color: #8B5CF6;"></div>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">📡 Fuentes de Datos y Benchmarks</div>
          <div id="modalSources"></div>
        </div>

        <div class="modal-section" id="modalLocalSection">
          <div class="modal-section-title">🟢 Estado en tu Computadora</div>
          <div class="modal-desc" id="modalLocalStatus" style="border-left-color: var(--floydia-teal);"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- POP-UP MODAL COMPARADOR CARA A CARA (MODEL VS MODEL) -->
  <div class="modal-overlay" id="vsModal" onclick="closeVsModalOnBackdrop(event)">
    <div class="modal-box modal-box-wide">
      <div class="modal-header" style="border-bottom-color: #372860;">
        <div>
          <div class="modal-title" style="color: #DDD6FE;">
            <span>⚔️ FloydIA Model VS Model Comparator</span>
            <span class="tier-badge" style="background: #5B21B6; color: #DDD6FE; border-color: #8B5CF6;">HEAD-TO-HEAD</span>
          </div>
          <div style="font-family: 'JetBrains Mono'; font-size: 13px; color: #A78BFA; margin-top: 4px;">Comparación multidimensional de benchmarks, specs, latencia y costes.</div>
        </div>
        <button class="modal-close" onclick="closeVsModal()">✖</button>
      </div>
      <div class="modal-body">
        
        <!-- PRESETS RÁPIDOS DE COMPARACIÓN -->
        <div class="vs-presets-bar">
          <span class="smart-pill-title">⚡ Duelos Populares:</span>
          <span class="smart-pill" style="border-color: #8B5CF6; color: #DDD6FE;" onclick="setVsPair('gemini-2.5-pro', 'claude-3-7-sonnet')">👑 Gemini 2.5 Pro vs Claude 3.7 Sonnet</span>
          <span class="smart-pill" style="border-color: #8B5CF6; color: #DDD6FE;" onclick="setVsPair('deepseek-reasoner', 'o3-mini')">🧠 DeepSeek R1 vs o3-mini</span>
          <span class="smart-pill" style="border-color: #8B5CF6; color: #DDD6FE;" onclick="setVsPair('gemini-2.5-flash', 'claude-3-5-haiku')">⚡ Gemini 2.5 Flash vs Claude 3.5 Haiku</span>
          <span class="smart-pill" style="border-color: #8B5CF6; color: #DDD6FE;" onclick="setVsPair('qwen-2.5-coder-32b', 'deepseek-chat')">💻 Qwen 2.5 Coder vs DeepSeek V3</span>
          <span class="smart-pill" style="border-color: #8B5CF6; color: #DDD6FE;" onclick="setVsPair('llama-3.3-70b', 'nous-hermes-3-70b')">🛡️ Llama 3.3 70B vs Hermes 3 70B</span>
        </div>

        <!-- SELECTORES DE MODELOS -->
        <div class="vs-selectors-grid">
          <div>
            <label style="font-family: 'JetBrains Mono'; font-size: 12px; color: var(--floydia-teal); font-weight: 700; display: block; margin-bottom: 6px;">🔵 MODELO A (Lado Izquierdo):</label>
            <select id="vsSelectA" class="dropdown-select" style="width: 100%; border-color: var(--floydia-teal);" onchange="updateVsComparison()"></select>
          </div>
          <div class="vs-badge-center">VS</div>
          <div>
            <label style="font-family: 'JetBrains Mono'; font-size: 12px; color: #C4B5FD; font-weight: 700; display: block; margin-bottom: 6px;">🟣 MODELO B (Lado Derecho):</label>
            <select id="vsSelectB" class="dropdown-select" style="width: 100%; border-color: #8B5CF6;" onchange="updateVsComparison()"></select>
          </div>
        </div>

        <!-- VEREDICTO EJECUTIVO FLOYDIA -->
        <div class="vs-verdict-box" id="vsVerdictBox">
          <div style="font-family: 'Chakra Petch'; font-size: 17px; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span>⚖️ Veredicto Ejecutivo FloydIA</span>
          </div>
          <div id="vsVerdictContent" style="font-size: 13px; color: #E2E8F0; line-height: 1.6;"></div>
        </div>

        <!-- COLUMNAS LADO A LADO -->
        <div class="vs-columns-grid">
          <!-- CARD MODELO A -->
          <div class="vs-card model-a" id="vsCardA"></div>
          <!-- CARD MODELO B -->
          <div class="vs-card model-b" id="vsCardB"></div>
        </div>

        <!-- COMPARACIÓN GRÁFICA DE MÉTRICAS -->
        <div class="modal-section">
          <div class="modal-section-title">📊 Comparativa Cara a Cara de Rendimiento</div>
          <div id="vsMetricsBars"></div>
        </div>

      </div>
    </div>
  </div>

  <script>
    const allModels = {rankings_json};
    let currentFiltered = [...allModels];
    let sortState = {{ table: null, col: null, asc: false }};
    let selectedModel = null;
    let currentTab = "python";
    let vsModelAId = "gemini-2.5-pro";
    let vsModelBId = "claude-3-7-sonnet";

    function init() {{
      populateVsSelects();
      setSortMode('free_score_desc');
    }}

    function populateVsSelects() {{
      const selA = document.getElementById("vsSelectA");
      const selB = document.getElementById("vsSelectB");
      if (!selA || !selB) return;

      const opts = allModels.map(m => '<option value="' + m.id + '">' + m.canonical_name + ' (' + m.provider + ' · ' + m.tier + ')</option>').join("");
      selA.innerHTML = opts;
      selB.innerHTML = opts;

      if (allModels.some(m => m.id === vsModelAId)) selA.value = vsModelAId;
      else if (allModels.length > 0) selA.value = allModels[0].id;

      if (allModels.some(m => m.id === vsModelBId)) selB.value = vsModelBId;
      else if (allModels.length > 1) selB.value = allModels[1].id;
    }}

    function setSortMode(mode) {{
      const sel = document.getElementById("sortSelect");
      if (sel) sel.value = mode;
      sortState = {{ table: null, col: null, asc: false }};
      applySortByMode(mode);
      renderGlobalTable();
      renderLocalTable();
    }}

    function onSortSelectChange() {{
      const sel = document.getElementById("sortSelect");
      const mode = sel ? sel.value : "free_score_desc";
      sortState = {{ table: null, col: null, asc: false }};
      applySortByMode(mode);
      renderGlobalTable();
      renderLocalTable();
    }}

    function applySortByMode(mode) {{
      if (mode === "free_score_desc") {{
        currentFiltered.sort((a, b) => {{
          const freeA = Boolean(a.is_free_tier) ? 1 : 0;
          const freeB = Boolean(b.is_free_tier) ? 1 : 0;
          if (freeA !== freeB) return freeB - freeA;
          return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
        }});
      }} else if (mode === "score_desc") {{
        currentFiltered.sort((a, b) => (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0));
      }} else if (mode === "score_asc") {{
        currentFiltered.sort((a, b) => (Number(a.intelligence_score) || 0) - (Number(b.intelligence_score) || 0));
      }} else if (mode === "workhorse_desc") {{
        currentFiltered.sort((a, b) => (Number(b.workhorse_score) || 0) - (Number(a.workhorse_score) || 0));
      }} else if (mode === "coding_desc") {{
        currentFiltered.sort((a, b) => (Number(b.coding_score) || 0) - (Number(a.coding_score) || 0));
      }} else if (mode === "price_asc") {{
        currentFiltered.sort((a, b) => {{
          const costA = Boolean(a.is_free_tier) ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0));
          const costB = Boolean(b.is_free_tier) ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0));
          if (costA !== costB) return costA - costB;
          return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
        }});
      }} else if (mode === "price_desc") {{
        currentFiltered.sort((a, b) => {{
          const costA = Boolean(a.is_free_tier) ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0));
          const costB = Boolean(b.is_free_tier) ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0));
          if (costA !== costB) return costB - costA;
          return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
        }});
      }} else if (mode === "local_first") {{
        currentFiltered.sort((a, b) => {{
          const locA = Boolean(a.is_local_active) ? 1 : 0;
          const locB = Boolean(b.is_local_active) ? 1 : 0;
          if (locA !== locB) return locB - locA;
          return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
        }});
      }} else if (mode === "context_desc") {{
        currentFiltered.sort((a, b) => (Number(b.context_window) || 0) - (Number(a.context_window) || 0));
      }} else if (mode === "name_asc") {{
        currentFiltered.sort((a, b) => (a.canonical_name || "").localeCompare(b.canonical_name || ""));
      }}
    }}

    function applyPreset(preset) {{
      document.querySelectorAll(".smart-pill").forEach(p => p.classList.remove("active"));
      if (event && event.target) event.target.classList.add("active");

      const setCats = (obj) => {{
        document.getElementById("filterFreeOnly").checked = Boolean(obj.free);
        document.getElementById("filterLocalOnly").checked = Boolean(obj.local);
        document.getElementById("filterFrontier").checked = Boolean(obj.frontier);
        document.getElementById("filterAgentic").checked = Boolean(obj.agentic);
        document.getElementById("filterReasoning").checked = Boolean(obj.reasoning);
        document.getElementById("filterMultimodal").checked = Boolean(obj.multimodal);
        document.getElementById("filterLongContext").checked = Boolean(obj.long_context);
        document.getElementById("filterWorkhorse").checked = Boolean(obj.workhorse);
        document.getElementById("filterCoding").checked = Boolean(obj.coding);
        document.getElementById("filterUncensored").checked = Boolean(obj.uncensored);
        document.getElementById("filterRealtime").checked = Boolean(obj.realtime);
        if (document.getElementById("filterEdge")) document.getElementById("filterEdge").checked = Boolean(obj.edge);
      }};

      if (preset === "coding_free") {{
        setCats({{ free: true, coding: true }});
        setSortMode("coding_desc");
      }} else if (preset === "agentic") {{
        setCats({{ agentic: true, frontier: true }});
        setSortMode("score_desc");
      }} else if (preset === "long_doc") {{
        setCats({{ long_context: true }});
        setSortMode("score_desc");
      }} else if (preset === "stem_reasoning") {{
        setCats({{ reasoning: true }});
        setSortMode("score_desc");
      }} else if (preset === "realtime") {{
        setCats({{ realtime: true, workhorse: true }});
        setSortMode("workhorse_desc");
      }} else if (preset === "uncensored") {{
        setCats({{ uncensored: true }});
        setSortMode("score_desc");
      }} else {{
        setCats({{ frontier: true, agentic: true, reasoning: true, multimodal: true, long_context: true, workhorse: true, coding: true, uncensored: true, realtime: true, edge: true }});
        setSortMode("free_score_desc");
      }}
    }}

    function filterAndRender() {{
      const q = document.getElementById("searchInput").value.toLowerCase().trim();
      const selectedSource = document.getElementById("sourceSelect").value;
      const onlyFree = document.getElementById("filterFreeOnly").checked;
      const onlyLocal = document.getElementById("filterLocalOnly").checked;

      const showFrontier = document.getElementById("filterFrontier").checked;
      const showAgentic = document.getElementById("filterAgentic").checked;
      const showReasoning = document.getElementById("filterReasoning").checked;
      const showMultimodal = document.getElementById("filterMultimodal").checked;
      const showLongContext = document.getElementById("filterLongContext").checked;
      const showWorkhorse = document.getElementById("filterWorkhorse").checked;
      const showCoding = document.getElementById("filterCoding").checked;
      const showUncensored = document.getElementById("filterUncensored").checked;
      const showRealtime = document.getElementById("filterRealtime").checked;
      const showEdge = document.getElementById("filterEdge") ? document.getElementById("filterEdge").checked : true;

      currentFiltered = allModels.filter(m => {{
        if (onlyFree && !Boolean(m.is_free_tier)) return false;
        if (onlyLocal && !Boolean(m.is_local_active)) return false;

        const t = m.tier;
        if (t === "frontier" && !showFrontier) return false;
        if (t === "agentic" && !showAgentic) return false;
        if (t === "reasoning" && !showReasoning) return false;
        if (t === "multimodal" && !showMultimodal) return false;
        if (t === "long_context" && !showLongContext) return false;
        if (t === "workhorse" && !showWorkhorse) return false;
        if (t === "coding" && !showCoding) return false;
        if (t === "uncensored" && !showUncensored) return false;
        if (t === "realtime" && !showRealtime) return false;
        if (t === "edge" && !showEdge) return false;

        if (selectedSource !== "all") {{
          const sources = (m.sources || []).map(s => String(s).toLowerCase());
          const prov = (m.provider || "").toLowerCase();
          const target = selectedSource.toLowerCase();

          const hasSource = sources.some(s => s.includes(target) || target.includes(s));
          const hasProv = prov.includes(target) || target.includes(prov);

          if (!hasSource && !hasProv) return false;
        }}

        if (q) {{
          const matchName = (m.canonical_name || "").toLowerCase().includes(q);
          const matchProv = (m.provider || "").toLowerCase().includes(q);
          const matchId = (m.id || "").toLowerCase().includes(q);
          if (!matchName && !matchProv && !matchId) return false;
        }}
        return true;
      }});

      if (sortState.table !== null && sortState.col !== null) {{
        applyTableSort(sortState.table, sortState.col, sortState.asc);
      }} else {{
        const currentMode = document.getElementById("sortSelect").value;
        applySortByMode(currentMode);
      }}

      renderLocalTable();
      renderGlobalTable();
    }}

    function renderLocalTable() {{
      const tbody = document.getElementById("localTableBody");
      const localModels = currentFiltered.filter(m => Boolean(m.is_local_active));
      document.getElementById("localCountBadge").innerText = localModels.length + " activos";

      if (localModels.length === 0) {{
        tbody.innerHTML = "<tr><td colspan='9' style='text-align: center; color: #94A3B8;'>No hay modelos locales que coincidan con los filtros.</td></tr>";
        return;
      }}

      tbody.innerHTML = localModels.map(m => {{
        const freeTxt = m.is_free_tier ? "<span class='free-badge'>🆓 GRATIS</span>" : ('$' + (Number(m.input_cost_per_m) || 0).toFixed(3) + ' / $' + (Number(m.output_cost_per_m) || 0).toFixed(3));
        const lat = m.local_latency_ms ? (m.local_latency_ms + " ms") : "-";
        const statusTxt = m.local_status_msg || '🟢 OK';
        return `
          <tr class="model-row">
            <td onclick="openModal('${{m.id}}')"><strong>${{m.canonical_name}}</strong> <span style="font-size: 11px; color: var(--floydia-teal);">ℹ️</span></td>
            <td onclick="openModal('${{m.id}}')">${{m.provider}}</td>
            <td onclick="openModal('${{m.id}}')"><span class="tier-badge tier-${{m.tier}}">${{m.tier}}</span></td>
            <td onclick="openModal('${{m.id}}')" class="code-val">${{(Number(m.context_window) || 0).toLocaleString()}} tok</td>
            <td onclick="openModal('${{m.id}}')" class="code-val">${{lat}}</td>
            <td onclick="openModal('${{m.id}}')" class="code-val">${{freeTxt}}</td>
            <td onclick="openModal('${{m.id}}')" class="score-val">${{m.intelligence_score}} / 100</td>
            <td onclick="openModal('${{m.id}}')"><span class="badge-local">${{statusTxt}}</span></td>
            <td>
              <button class="mini-vs-btn" onclick="triggerVsDirect('${{m.id}}', event)">⚔️ VS</button>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    function renderGlobalTable() {{
      const tbody = document.getElementById("globalTableBody");
      document.getElementById("totalCountBadge").innerText = currentFiltered.length + " modelos";

      if (currentFiltered.length === 0) {{
        tbody.innerHTML = "<tr><td colspan='11' style='text-align: center; color: #94A3B8;'>Ningún modelo coincide con los filtros seleccionados.</td></tr>";
        return;
      }}

      tbody.innerHTML = currentFiltered.map(m => {{
        const badgeHtml = m.is_local_active ? "<span class='badge-local'>🟢 LOCAL</span>" : "<span class='badge-external'>⚪ EXTERNO</span>";
        const costStr = m.is_free_tier ? "<span class='free-badge'>🆓 GRATIS</span>" : ('$' + (Number(m.input_cost_per_m) || 0).toFixed(3) + ' / $' + (Number(m.output_cost_per_m) || 0).toFixed(3));
        const eloVal = Math.round((Number(m.preference_score) || 0) * 4 + 1000);
        const sourcesHtml = (m.sources || []).map(s => '<span class="source-tag">' + s + '</span>').join("");

        return `
          <tr class="model-row">
            <td onclick="openModal('${{m.id}}')" class="code-val">#${{m.global_rank}}</td>
            <td onclick="openModal('${{m.id}}')"><strong>${{m.canonical_name}}</strong> <span style="font-size: 11px; color: #64748B;">(${{m.provider}})</span> <span style="font-size: 11px; color: var(--floydia-teal);">ℹ️</span></td>
            <td onclick="openModal('${{m.id}}')">${{badgeHtml}}</td>
            <td onclick="openModal('${{m.id}}')"><span class="tier-badge tier-${{m.tier}}">${{m.tier}}</span></td>
            <td onclick="openModal('${{m.id}}')" class="score-val">${{m.intelligence_score}}</td>
            <td onclick="openModal('${{m.id}}')" class="code-val">${{m.workhorse_score}}</td>
            <td onclick="openModal('${{m.id}}')" class="code-val">${{m.coding_score}}</td>
            <td onclick="openModal('${{m.id}}')" class="code-val">${{eloVal}}</td>
            <td onclick="openModal('${{m.id}}')" class="code-val">${{costStr}}</td>
            <td onclick="openModal('${{m.id}}')">${{sourcesHtml}}</td>
            <td>
              <button class="mini-vs-btn" onclick="triggerVsDirect('${{m.id}}', event)">⚔️ VS</button>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    function applyTableSort(tableType, colIndex, isAsc) {{
      currentFiltered.sort((a, b) => {{
        let valA, valB;
        if (tableType === "localTable") {{
          if (colIndex === 0) {{ valA = (a.canonical_name || "").toLowerCase(); valB = (b.canonical_name || "").toLowerCase(); }}
          else if (colIndex === 1) {{ valA = (a.provider || "").toLowerCase(); valB = (b.provider || "").toLowerCase(); }}
          else if (colIndex === 2) {{ valA = (a.tier || "").toLowerCase(); valB = (b.tier || "").toLowerCase(); }}
          else if (colIndex === 3) {{ valA = Number(a.context_window) || 0; valB = Number(b.context_window) || 0; }}
          else if (colIndex === 4) {{ valA = Number(a.local_latency_ms) || 999999; valB = Number(b.local_latency_ms) || 999999; }}
          else if (colIndex === 5) {{ 
            valA = a.is_free_tier ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0)); 
            valB = b.is_free_tier ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0)); 
          }}
          else if (colIndex === 6) {{ valA = Number(a.intelligence_score) || 0; valB = Number(b.intelligence_score) || 0; }}
          else if (colIndex === 7) {{ valA = (a.local_status_msg || "").toLowerCase(); valB = (b.local_status_msg || "").toLowerCase(); }}
          else {{ valA = a.id; valB = b.id; }}
        }} else {{
          if (colIndex === 0) {{ valA = Number(a.global_rank) || 0; valB = Number(b.global_rank) || 0; }}
          else if (colIndex === 1) {{ valA = (a.canonical_name || "").toLowerCase(); valB = (b.canonical_name || "").toLowerCase(); }}
          else if (colIndex === 2) {{ valA = a.is_local_active ? 1 : 0; valB = b.is_local_active ? 1 : 0; }}
          else if (colIndex === 3) {{ valA = (a.tier || "").toLowerCase(); valB = (b.tier || "").toLowerCase(); }}
          else if (colIndex === 4) {{ valA = Number(a.intelligence_score) || 0; valB = Number(b.intelligence_score) || 0; }}
          else if (colIndex === 5) {{ valA = Number(a.workhorse_score) || 0; valB = Number(b.workhorse_score) || 0; }}
          else if (colIndex === 6) {{ valA = Number(a.coding_score) || 0; valB = Number(b.coding_score) || 0; }}
          else if (colIndex === 7) {{ valA = Number(a.preference_score) || 0; valB = Number(b.preference_score) || 0; }}
          else if (colIndex === 8) {{ 
            valA = a.is_free_tier ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0)); 
            valB = b.is_free_tier ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0)); 
          }}
          else if (colIndex === 9) {{ valA = (a.sources || []).length; valB = (b.sources || []).length; }}
          else {{ valA = a.id; valB = b.id; }}
        }}

        if (typeof valA === "string") {{
          return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }}
        return isAsc ? (valA - valB) : (valB - valA);
      }});
    }}

    function sortTable(tableType, colIndex) {{
      const isAsc = (sortState.table === tableType && sortState.col === colIndex) ? !sortState.asc : (colIndex === 0 || colIndex === 1);
      sortState = {{ table: tableType, col: colIndex, asc: isAsc }};

      applyTableSort(tableType, colIndex, isAsc);
      renderGlobalTable();
      renderLocalTable();
    }}

    function openModal(modelId) {{
      const m = allModels.find(item => item.id === modelId);
      if (!m) return;
      selectedModel = m;

      document.getElementById("modalModelName").innerText = m.canonical_name;
      document.getElementById("modalProvider").innerText = "Proveedor: " + m.provider + " · ID: " + m.id;
      
      const localBadge = document.getElementById("modalLocalBadge");
      localBadge.className = m.is_local_active ? "badge-local" : "badge-external";
      localBadge.innerText = m.is_local_active ? "🟢 ACTIVO EN TU PC" : "⚪ REFERENCIA EXTERNA";

      const tierBadge = document.getElementById("modalTierBadge");
      tierBadge.className = "tier-badge tier-" + m.tier;
      tierBadge.innerText = m.tier;

      document.getElementById("modalIntelScore").innerText = m.intelligence_score + " / 100";
      document.getElementById("modalWorkhorseScore").innerText = m.workhorse_score + " / 100";
      document.getElementById("modalCodingScore").innerText = m.coding_score + " / 100";
      document.getElementById("modalContextWindow").innerText = m.context_window.toLocaleString() + " tok";
      document.getElementById("modalPricing").innerText = m.is_free_tier ? "🆓 Gratis" : ('$' + m.input_cost_per_m.toFixed(3) + ' In / $' + m.output_cost_per_m.toFixed(3) + ' Out');

      document.getElementById("modalDescription").innerText = m.description || "Sin descripción disponible.";
      document.getElementById("modalComparison").innerText = m.comparison || "Sin datos comparativos.";

      const useCasesList = document.getElementById("modalUseCases");
      useCasesList.innerHTML = (m.use_cases || []).map(uc => '<li>' + uc + '</li>').join("");

      const sourcesDiv = document.getElementById("modalSources");
      sourcesDiv.innerHTML = (m.sources || []).map(s => '<span class="source-tag" style="font-size: 12px; padding: 4px 8px;">📊 ' + s + '</span>').join(" ");

      updateSnippet();

      const localSection = document.getElementById("modalLocalSection");
      const localStatus = document.getElementById("modalLocalStatus");
      if (m.is_local_active) {{
        const toolsTxt = m.supports_tools ? '✅ Sí' : '❌ No';
        const visionTxt = m.supports_vision ? '✅ Sí' : '❌ No';
        const reasoningTxt = m.supports_reasoning ? '✅ Sí' : '❌ No';
        const latTxt = m.local_latency_ms ? (m.local_latency_ms + ' ms') : '-';
        const stMsg = m.local_status_msg || '🟢 Operativa y verificada';

        localSection.style.display = "block";
        localStatus.innerHTML = 
          '<strong>Estado de Conexión:</strong> ' + stMsg + '<br>' +
          '<strong>Latencia Medida:</strong> ' + latTxt + '<br>' +
          '<strong>Ventana Detectada:</strong> ' + m.local_detected_context.toLocaleString() + ' tokens<br>' +
          '<strong>Soporte de Herramientas:</strong> ' + toolsTxt + ' | ' +
          '<strong>Visión:</strong> ' + visionTxt + ' | ' +
          '<strong>Razonamiento Nativo:</strong> ' + reasoningTxt;
      }} else {{
        localSection.style.display = "block";
        localStatus.innerHTML = '<em>Este modelo no está configurado actualmente en tu archivo <code>.secrets/antigravity.env</code>. Para activarlo, configura la API key correspondiente en tu entorno.</em>';
      }}

      document.getElementById("modelModal").classList.add("active");
    }}

    function compareFromModal() {{
      if (!selectedModel) return;
      closeModal();
      vsModelAId = selectedModel.id;
      openVsModal();
    }}

    function triggerVsDirect(modelId, e) {{
      if (e) e.stopPropagation();
      vsModelAId = modelId;
      openVsModal();
    }}

    function switchTab(tab) {{
      currentTab = tab;
      document.querySelectorAll(".snippet-tab").forEach(t => t.classList.remove("active"));
      if (event && event.target) event.target.classList.add("active");
      updateSnippet();
    }}

    function updateSnippet() {{
      if (!selectedModel) return;
      const m = selectedModel;
      const snippetPre = document.getElementById("snippetCode");

      if (currentTab === 'python') {{
        snippetPre.innerText = 'from openai import OpenAI\\n\\nclient = OpenAI(\\n    base_url="https://openrouter.ai/api/v1",\\n    api_key="TU_API_KEY"\\n)\\n\\nresponse = client.chat.completions.create(\\n    model="' + m.id + '",\\n    messages=[{{"role": "user", "content": "Hola mundo"}}],\\n    temperature=0.2\\n)\\nprint(response.choices[0].message.content)';
      }} else {{
        snippetPre.innerText = 'curl https://openrouter.ai/api/v1/chat/completions \\n  -H "Authorization: Bearer $OPENROUTER_API_KEY" \\n  -H "Content-Type: application/json" \\n  -d \\'{{"model": "' + m.id + '", "messages": [{{"role": "user", "content": "Hola mundo"}}]}}\\'';
      }}
    }}

    function copySnippet() {{
      const code = document.getElementById("snippetCode").innerText;
      navigator.clipboard.writeText(code);
      const btn = event.target;
      btn.innerText = "✅ ¡Copiado!";
      setTimeout(() => btn.innerText = "📋 Copiar Código", 2000);
    }}

    function closeModal() {{
      document.getElementById("modelModal").classList.remove("active");
    }}

    function closeModalOnBackdrop(e) {{
      if (e.target.id === "modelModal") closeModal();
    }}

    /* LÓGICA COMPARADOR VS CARA A CARA */
    function openVsModal() {{
      const selA = document.getElementById("vsSelectA");
      const selB = document.getElementById("vsSelectB");
      if (selA && vsModelAId) selA.value = vsModelAId;
      if (selB && vsModelBId) selB.value = vsModelBId;
      updateVsComparison();
      document.getElementById("vsModal").classList.add("active");
    }}

    function closeVsModal() {{
      document.getElementById("vsModal").classList.remove("active");
    }}

    function closeVsModalOnBackdrop(e) {{
      if (e.target.id === "vsModal") closeVsModal();
    }}

    function setVsPair(idA, idB) {{
      vsModelAId = idA;
      vsModelBId = idB;
      const selA = document.getElementById("vsSelectA");
      const selB = document.getElementById("vsSelectB");
      if (selA) selA.value = idA;
      if (selB) selB.value = idB;
      updateVsComparison();
    }}

    function updateVsComparison() {{
      const idA = document.getElementById("vsSelectA").value;
      const idB = document.getElementById("vsSelectB").value;
      vsModelAId = idA;
      vsModelBId = idB;

      const mA = allModels.find(m => m.id === idA) || allModels[0];
      const mB = allModels.find(m => m.id === idB) || (allModels[1] || allModels[0]);

      renderVsCard("vsCardA", mA, "A", "--floydia-teal");
      renderVsCard("vsCardB", mB, "B", "#8B5CF6");
      renderVsMetricBars(mA, mB);
      renderVsVerdict(mA, mB);
    }}

    function renderVsCard(containerId, m, label, colorVar) {{
      const card = document.getElementById(containerId);
      const isFree = m.is_free_tier;
      const pricingStr = isFree ? "🆓 Gratuito (Free Tier)" : ('$' + m.input_cost_per_m.toFixed(3) + ' In / $' + m.output_cost_per_m.toFixed(3) + ' Out');
      const localBadge = m.is_local_active ? "<span class='badge-local'>🟢 EN TU PC</span>" : "<span class='badge-external'>⚪ EXTERNO</span>";
      const totalCostStr = isFree ? "<span class='free-badge'>🆓 $0.00</span>" : ('<span class="source-tag">💰 $' + (m.input_cost_per_m + m.output_cost_per_m).toFixed(2) + '/1M</span>');
      const toolTxt = m.supports_tools ? '✅ Soportado' : '❌ No';
      const visTxt = m.supports_vision ? '✅ Soportado' : '❌ No';
      const reasonTxt = m.supports_reasoning ? '✅ Sí (CoT)' : '⚡ Directo';
      const latTxt = m.local_latency_ms ? (m.local_latency_ms + ' ms') : 'No probada en local';
      const descTxt = m.description || 'Sin descripción disponible.';

      card.innerHTML = 
        '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">' +
          '<div>' +
            '<div style="font-family: Chakra Petch, sans-serif; font-size: 20px; font-weight: 700; color: #FFFFFF;">' + m.canonical_name + '</div>' +
            '<div style="font-family: JetBrains Mono, monospace; font-size: 12px; color: #94A3B8;">' + m.provider + ' · <code>' + m.id + '</code></div>' +
          '</div>' +
          '<span class="tier-badge tier-' + m.tier + '">' + m.tier + '</span>' +
        '</div>' +
        '<div style="display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap;">' +
          localBadge +
          '<span class="source-tag">📚 ' + m.context_window.toLocaleString() + ' tokens</span>' +
          totalCostStr +
        '</div>' +
        '<div style="background: rgba(11, 17, 28, 0.6); padding: 12px; border-radius: 6px; font-size: 13px; margin-bottom: 12px; border-left: 3px solid var(' + colorVar + ');">' +
          descTxt +
        '</div>' +
        '<div style="font-family: JetBrains Mono, monospace; font-size: 12px; display: flex; flex-direction: column; gap: 6px; color: #CBD5E1;">' +
          '<div>🛠️ <strong>Tool Calling:</strong> ' + toolTxt + '</div>' +
          '<div>👁️ <strong>Visión / Multimodal:</strong> ' + visTxt + '</div>' +
          '<div>🧠 <strong>Razonamiento Nativo:</strong> ' + reasonTxt + '</div>' +
          '<div>⏱️ <strong>Latencia Local:</strong> ' + latTxt + '</div>' +
        '</div>';
    }}

    function renderVsMetricBars(mA, mB) {{
      const container = document.getElementById("vsMetricsBars");
      const metrics = [
        {{ label: "🧠 Inteligencia Global", valA: mA.intelligence_score, valB: mB.intelligence_score, max: 100, unit: "pts", isTok: false }},
        {{ label: "💻 Coding & Software", valA: mA.coding_score, valB: mB.coding_score, max: 100, unit: "pts", isTok: false }},
        {{ label: "⚡ Eficiencia Batalla", valA: mA.workhorse_score, valB: mB.workhorse_score, max: 100, unit: "pts", isTok: false }},
        {{ label: "🏆 Preferencia LMSYS Elo", valA: Math.round(mA.preference_score * 4 + 1000), valB: Math.round(mB.preference_score * 4 + 1000), max: 1500, min: 1000, unit: "Elo", isTok: false }},
        {{ label: "📚 Ventana de Contexto", valA: mA.context_window, valB: mB.context_window, max: Math.max(mA.context_window, mB.context_window, 2097152), unit: "tok", isTok: true }}
      ];

      container.innerHTML = metrics.map(met => {{
        const diff = met.valA - met.valB;
        let diffBadge = "";
        if (diff > 0) {{
          const diffTxt = met.isTok ? diff.toLocaleString() : diff.toFixed(1);
          diffBadge = '<span class="vs-diff-winner">◀ ' + mA.canonical_name + ' gana por +' + diffTxt + ' ' + met.unit + '</span>';
        }} else if (diff < 0) {{
          const diffTxt = met.isTok ? Math.abs(diff).toLocaleString() : Math.abs(diff).toFixed(1);
          diffBadge = '<span class="vs-diff-winner" style="color: #A78BFA;">▶ ' + mB.canonical_name + ' gana por +' + diffTxt + ' ' + met.unit + '</span>';
        }} else {{
          diffBadge = '<span style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #94A3B8;">⚖️ Empate técnico</span>';
        }}

        const pctA = Math.min(100, Math.max(5, (met.valA / met.max) * 100));
        const pctB = Math.min(100, Math.max(5, (met.valB / met.max) * 100));

        const displayValA = met.isTok ? met.valA.toLocaleString() : met.valA;
        const displayValB = met.isTok ? met.valB.toLocaleString() : met.valB;

        return `
          <div class="vs-metric-row">
            <div class="vs-metric-header">
              <span style="color: var(--floydia-teal); font-weight: 700;">${{mA.canonical_name}}: ${{displayValA}}</span>
              <span style="color: #CBD5E1; font-weight: 600;">${{met.label}}</span>
              <span style="color: #A78BFA; font-weight: 700;">${{mB.canonical_name}}: ${{displayValB}}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 4px;">
              <div class="vs-bar-track" style="justify-content: flex-end;">
                <div class="vs-bar-fill-a" style="width: ${{pctA}}%;"></div>
              </div>
              <div class="vs-bar-track">
                <div class="vs-bar-fill-b" style="width: ${{pctB}}%;"></div>
              </div>
            </div>
            <div style="text-align: center; margin-top: 2px;">${{diffBadge}}</div>
          </div>
        `;
      }}).join("");
    }}

    function renderVsVerdict(mA, mB) {{
      const verdictEl = document.getElementById("vsVerdictContent");
      const costA = mA.is_free_tier ? 0 : (mA.input_cost_per_m + mA.output_cost_per_m);
      const costB = mB.is_free_tier ? 0 : (mB.input_cost_per_m + mB.output_cost_per_m);

      let bulletA = [];
      let bulletB = [];

      if (mA.intelligence_score > mB.intelligence_score) bulletA.push('Mayor score de inteligencia (+' + (mA.intelligence_score - mB.intelligence_score).toFixed(1) + ' pts)');
      if (mA.coding_score > mB.coding_score) bulletA.push('Superior en tareas de programación (+' + (mA.coding_score - mB.coding_score).toFixed(1) + ' pts)');
      if (mA.context_window > mB.context_window) bulletA.push('Ventana de contexto superior (' + mA.context_window.toLocaleString() + ' vs ' + mB.context_window.toLocaleString() + ')');
      if (mA.is_free_tier && !mB.is_free_tier) bulletA.push('Disponibilidad gratuita (Free Tier $0.00)');
      else if (costA < costB) bulletA.push('Coste por token más económico');
      if (mA.is_local_active && !mB.is_local_active) bulletA.push('Listo y verificado en tu PC (.env local)');

      if (mB.intelligence_score > mA.intelligence_score) bulletB.push('Mayor score de inteligencia (+' + (mB.intelligence_score - mA.intelligence_score).toFixed(1) + ' pts)');
      if (mB.coding_score > mA.coding_score) bulletB.push('Superior en tareas de programación (+' + (mB.coding_score - mA.coding_score).toFixed(1) + ' pts)');
      if (mB.context_window > mA.context_window) bulletB.push('Ventana de contexto superior (' + mB.context_window.toLocaleString() + ' vs ' + mA.context_window.toLocaleString() + ')');
      if (mB.is_free_tier && !mA.is_free_tier) bulletB.push('Disponibilidad gratuita (Free Tier $0.00)');
      else if (costB < costA) bulletB.push('Coste por token más económico');
      if (mB.is_local_active && !mA.is_local_active) bulletB.push('Listo y verificado en tu PC (.env local)');

      const listAHtml = bulletA.length ? bulletA.map(b => '<li>' + b + '</li>').join('') : '<li>Modelo de referencia equilibrado para su categoría.</li>';
      const listBHtml = bulletB.length ? bulletB.map(b => '<li>' + b + '</li>').join('') : '<li>Modelo de referencia equilibrado para su categoría.</li>';

      verdictEl.innerHTML = 
        '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">' +
          '<div>' +
            '<strong style="color: var(--floydia-teal);">🔹 Elige ' + mA.canonical_name + ' si:</strong>' +
            '<ul style="margin-left: 18px; margin-top: 4px;">' + listAHtml + '</ul>' +
          '</div>' +
          '<div>' +
            '<strong style="color: #C4B5FD;">🔸 Elige ' + mB.canonical_name + ' si:</strong>' +
            '<ul style="margin-left: 18px; margin-top: 4px;">' + listBHtml + '</ul>' +
          '</div>' +
        '</div>';
    }}

    document.addEventListener("keydown", (e) => {{
      if (e.key === "Escape") {{
        closeModal();
        closeVsModal();
      }}
    }});

    async function submitAdvisorQuestion() {{
      const input = document.getElementById("advisorInput");
      const btn = document.getElementById("advisorBtn");
      const resultCard = document.getElementById("advisorResultCard");
      const engineBadge = document.getElementById("advisorResultEngine");
      const resultBody = document.getElementById("advisorResultBody");
      const query = input.value.trim();

      if (!query) {{
        alert("Por favor escribe una consulta.");
        return;
      }}

      btn.innerText = "Pensando...";
      btn.disabled = true;
      resultCard.style.display = "block";
      resultBody.innerText = "⏳ Consultando con base de conocimiento y analizando rankings...";

      try {{
        const res = await fetch("/api/action/ask", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ query: query }})
        }});
        const data = await res.json();
        if (data.success) {{
          engineBadge.innerText = "Motor: " + (data.engine || "FloydIA Grounded Advisor");
          resultBody.innerText = data.answer;
        }} else {{
          resultBody.innerText = "❌ Error: " + (data.error || "No se pudo obtener respuesta.");
        }}
      }} catch (e) {{
        resultBody.innerText = "❌ Error de conexión: " + e;
      }} finally {{
        btn.innerText = "Preguntar a la IA 🚀";
        btn.disabled = false;
      }}
    }}

    function setAdvisorPreset(text) {{
      const input = document.getElementById("advisorInput");
      input.value = text;
      submitAdvisorQuestion();
    }}

    function copyAdvisorText() {{
      const text = document.getElementById("advisorResultBody").innerText;
      navigator.clipboard.writeText(text).then(() => {{
        alert("📋 Respuesta copiada al portapapeles.");
      }}).catch(e => {{
        alert("Error al copiar: " + e);
      }});
    }}

    async function runProbe() {{
      const btn = event.target;
      btn.innerText = "⏳ Probando...";
      try {{
        const res = await fetch("/api/action/probe", {{ method: "POST" }});
        const data = await res.json();
        alert("✅ Sonda completada: " + data.tested_count + " endpoints evaluados.");
        window.location.reload();
      }} catch (e) {{
        alert("Error ejecutando sonda: " + e);
      }} finally {{
        btn.innerText = "⚡ Probar APIs Locales";
      }}
    }}

    async function runCollect() {{
      const btn = event.target;
      btn.innerText = "⏳ Recolectando...";
      try {{
        const res = await fetch("/api/action/collect", {{ method: "POST" }});
        alert("✅ Benchmarks actualizados desde fuentes públicas.");
        window.location.reload();
      }} catch (e) {{
        alert("Error: " + e);
      }} finally {{
        btn.innerText = "🔄 Actualizar Rankings";
      }}
    }}

    async function runApplyConfigs() {{
      const btn = event.target;
      btn.innerText = "⏳ Inyectando...";
      try {{
        const res = await fetch("/api/action/apply-configs", {{ method: "POST" }});
        const data = await res.json();
        if (data.success) {{
          let msg = "✅ Configuraciones aplicadas con éxito:\\\\n";
          for (const l of data.logs) {{
            msg += "• " + l[0] + "\\\\n";
          }}
          alert(msg);
        }} else {{
          alert("Error aplicando configuraciones.");
        }}
      }} catch (e) {{
        alert("Error de red: " + e);
      }} finally {{
        btn.innerText = "⚙️ Inyectar a Motores";
      }}
    }}

    async function runSyncHp45() {{
      const btn = event.target;
      btn.innerText = "⏳ Sincronizando...";
      try {{
        const res = await fetch("/api/action/sync-hp45", {{ method: "POST" }});
        const data = await res.json();
        alert(data.message);
      }} catch (e) {{
        alert("Error de sincronización: " + e);
      }} finally {{
        btn.innerText = "📡 Sincronizar HP45";
      }}
    }}

    window.onload = init;
  </script>
</body>
</html>
"""
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def start_server(port: int = 8333):
    socketserver.TCPServer.allow_reuse_address = True
    handler = FloydIAWebServer
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🟢 [FloydIA Observatory Web] Dashboard activo en: http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    start_server(8333)
