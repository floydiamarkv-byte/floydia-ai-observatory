"""
Servidor y Dashboard Web Interactivo de FloydIA AI Rankings & Local API Observatory v9.0.
Incluye:
- 10 categorías especializadas (Frontier, Agentes, Razonamiento, Visión, Contexto 1M+, Caballos, Coding, Soberanos, Realtime, Edge).
- 8 fuentes de benchmark: Arena.ai, SWE-bench, Aider, Artificial Analysis, OpenRouter, HuggingFace, LiveBench, Epoch AI.
- Transparencia de benchmarks: desglose de qué métricas contribuyeron a cada score.
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

import os
import secrets
import time
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
from src.core.auth_hmac import verify_hmac_request

# FIX V-02: Token de sesión para acciones mutadoras
AUTH_TOKEN = os.getenv("FLOYDIA_DASH_TOKEN") or secrets.token_urlsafe(32)

# FIX V-17: Caché TTL en memoria para rankings
_RANKINGS_CACHE = {"data": None, "ts": 0.0}
CACHE_TTL_SECONDS = 300


def cached_rankings():
    """Retorna rankings desde caché o los recalcula si expiró el TTL."""
    now = time.time()
    if _RANKINGS_CACHE["data"] is None or (now - _RANKINGS_CACHE["ts"]) > CACHE_TTL_SECONDS:
        _RANKINGS_CACHE["data"] = calculate_multidimensional_rankings()
        _RANKINGS_CACHE["ts"] = now
    return _RANKINGS_CACHE["data"]


def invalidate_rankings_cache():
    """Invalida la caché de rankings tras una recolección."""
    _RANKINGS_CACHE["data"] = None
    _RANKINGS_CACHE["ts"] = 0.0


class FloydIAWebServer(http.server.SimpleHTTPRequestHandler):
    def _authorized(self, body: str = "") -> tuple[bool, int, str]:
        """Verifica la autenticación mediante HMAC Anti-Replay (M-2) o Token estático."""
        headers_dict = {k: v for k, v in self.headers.items()}
        return verify_hmac_request(headers_dict, body, AUTH_TOKEN)
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/rankings":
                rankings = cached_rankings()
                self._send_json(rankings)
                return

            elif path == "/api/local-apis":
                local_apis = get_latest_local_verified_models()
                self._send_json(local_apis)
                return

            elif path == "/api/recommend_model":
                query_params = urllib.parse.parse_qs(parsed.query)
                task = query_params.get("task", ["general"])[0]
                budget = query_params.get("budget", ["any"])[0]
                max_lat_str = query_params.get("max_latency_ms", [None])[0]
                max_lat = float(max_lat_str) if max_lat_str is not None else None
                ctx_str = query_params.get("context_required", ["4000"])[0]
                ctx = int(ctx_str) if ctx_str.isdigit() else 4000
                req_tools = query_params.get("requires_tools", ["false"])[0].lower() in ("true", "1")
                req_vision = query_params.get("requires_vision", ["false"])[0].lower() in ("true", "1")
                req_reasoning = query_params.get("requires_reasoning", ["false"])[0].lower() in ("true", "1")
                req_coding = query_params.get("requires_coding", ["false"])[0].lower() in ("true", "1")
                local_only = query_params.get("prefer_local_only", ["true"])[0].lower() in ("true", "1")

                from src.core.router import recommend_model
                rec = recommend_model(
                    task=task,
                    budget=budget,
                    max_latency_ms=max_lat,
                    context_required=ctx,
                    requires_tools=req_tools,
                    requires_vision=req_vision,
                    requires_reasoning=req_reasoning,
                    requires_coding=req_coding,
                    prefer_local_only=local_only
                )
                self._send_json(rec)
                return

            elif path == "/api/drift_events":
                from src.core.db import get_recent_drift_events
                events = get_recent_drift_events(limit=50)
                self._send_json({"events": events, "count": len(events)})
                return

            elif path == "/download/report":
                today_str = datetime.now().strftime("%Y-%m-%d")
                report_file = DAILY_REPORTS_DIR / f"{today_str}_informe_ia_floydia.md"
                if not report_file.exists():
                    rankings = cached_rankings()
                    local_apis = get_latest_local_verified_models()
                    report_file = generate_daily_markdown_report(rankings, local_apis)
                self._send_file_download(report_file, f"{today_str}_informe_ia_floydia.md")
                return

            elif path == "/download/frontier":
                today_str = datetime.now().strftime("%Y-%m-%d")
                frontier_file = FRONTIER_EXPORT_DIR / f"{today_str}_SNAPSHOT_FOR_FRONTIER_AI.md"
                if not frontier_file.exists():
                    rankings = cached_rankings()
                    local_apis = get_latest_local_verified_models()
                    frontier_file = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
                self._send_file_download(frontier_file, f"{today_str}_SNAPSHOT_FOR_FRONTIER_AI.md")
                return

            elif path == "/" or path == "/index.html":
                self._render_dashboard()
                return

            elif path.startswith("/static/"):
                static_dir = (Path(__file__).parent / "static").resolve()
                rel_path = path[len("/static/"):].lstrip("/")
                target_file = (static_dir / rel_path).resolve()
                if not str(target_file).startswith(str(static_dir)) or not target_file.is_file():
                    self.send_response(404)
                    self.end_headers()
                    return

                content_type = "application/javascript" if target_file.suffix == ".js" else "text/css" if target_file.suffix == ".css" else "application/octet-stream"
                with open(target_file, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", f"{content_type}; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            else:
                # FIX V-03: No servir el árbol del proyecto
                self.send_response(404)
                self.end_headers()
                return
        except Exception:
            traceback.print_exc()
            # FIX V-23: Error 500 sanitizado sin trazas crudas
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "internal_error"}')

    def do_POST(self):
        # FIX V-02 / M-2: Gate de autenticación con soporte HMAC Anti-Replay
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""

        is_auth, status_code, auth_msg = self._authorized(body)
        if not is_auth:
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "unauthorized" if status_code == 401 else "forbidden", "message": auth_msg}).encode("utf-8"))
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/action/probe":
            results = run_local_api_probes()
            self._send_json({"success": True, "tested_count": len(results), "results": results})
            return

        elif path == "/api/action/collect":
            results = run_all_collectors()
            invalidate_rankings_cache()
            self._send_json({"success": True, "collectors": results})
            return

        elif path == "/api/recommend_model":
            try:
                req_data = json.loads(body) if body else {}
            except Exception:
                req_data = {}
            from src.core.router import recommend_model
            rec = recommend_model(
                task=req_data.get("task", "general"),
                budget=req_data.get("budget", "any"),
                max_latency_ms=req_data.get("max_latency_ms"),
                context_required=req_data.get("context_required", 4000),
                requires_tools=req_data.get("requires_tools", False),
                requires_vision=req_data.get("requires_vision", False),
                requires_reasoning=req_data.get("requires_reasoning", False),
                requires_coding=req_data.get("requires_coding", False),
                prefer_local_only=req_data.get("prefer_local_only", True)
            )
            self._send_json(rec)
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
            rankings = cached_rankings()
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
        rankings = cached_rankings()
        today_str = datetime.now().strftime("%Y-%m-%d")
        rankings_json = json.dumps(rankings).replace("</", "<\\/")

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FloydIA — AI Rankings & Local API Observatory v9.0</title>
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
          <option value="all">🌐 Todas las Fuentes (8 Benchmarks + APIs)</option>
          <option value="ArenaAI">🏆 Arena.ai (Elo Preferencia Humana)</option>
          <option value="SWEBench">🐛 SWE-bench Verified (Issues Reales)</option>
          <option value="Aider">🧑‍💻 Aider Polyglot (Coding Multi-Lenguaje)</option>
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

      <!-- DESPLEGABLE DE VENTANA DE CONTEXTO -->
      <div class="dropdown-group">
        <span>📚 Contexto:</span>
        <select id="contextSelect" class="dropdown-select" style="border-color: #F59E0B; color: #FBBF24;" onchange="filterAndRender()">
          <option value="all">📚 Todo Contexto</option>
          <option value="32k">≥ 32k tokens</option>
          <option value="128k">≥ 128k tokens</option>
          <option value="256k">≥ 256k tokens</option>
          <option value="1m">≥ 1M tokens</option>
          <option value="2m">≥ 2M tokens</option>
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

        <div class="modal-section">
          <div class="modal-section-title">🔬 Transparencia de Benchmarks</div>
          <div id="modalBenchmarks" class="modal-desc" style="border-left-color: #6366F1;"></div>
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
    const DASH_AUTH_TOKEN = "{AUTH_TOKEN}";
  </script>
  <script src="/static/dashboard.js"></script>
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
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    handler = FloydIAWebServer
    # FIX V-02: Bind exclusivo a 127.0.0.1 (loopback)
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"🟢 [FloydIA Observatory Web] http://127.0.0.1:{port} (solo localhost)")
        if not os.getenv("FLOYDIA_DASH_TOKEN"):
            print(f"🔑 [FloydIA Web Token]: {AUTH_TOKEN}")
        httpd.serve_forever()


if __name__ == "__main__":
    start_server(8333)
