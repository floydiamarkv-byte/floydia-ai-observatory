"""
Punto de Entrada CLI & GUI Unificado de FloydIA AI Command & Observatory Suite (v9.2).
Permite selección de tareas por checkmarks, consultas en lenguaje natural con IA,
escaneo profundo con preguntas cortas en 6 estados, inyección dinámica de motores y sincronización a HP45.
"""

import sys
import json
import argparse
from datetime import datetime
from typing import List

from src.collectors.aggregator import run_all_collectors
from src.probers.local_verifier import run_local_api_probes
from src.probers.deep_probe_scanner import (
    run_deep_scan, get_latest_deep_scan_results,
    STATUS_OK, STATUS_NO_BALANCE, STATUS_FREE_TIER_EXHAUSTED,
    STATUS_UNAUTHORIZED, STATUS_NO_RESPONSE, STATUS_ERROR,
    DEFAULT_PROBE_PROMPT, STATUS_LABELS
)
from src.core.scoring import calculate_multidimensional_rankings
from src.core.db import get_latest_local_verified_models, get_recent_drift_events
from src.core.router import recommend_model
from src.reports.markdown_report import generate_daily_markdown_report
from src.reports.html_report import generate_daily_html_report
from src.analyst.frontier_exporter import export_daily_snapshot_for_frontier_ai
from src.analyst.ai_advisor import ask_observatory
from src.core.engine_injector import apply_engine_configurations, sync_to_hp45


def _ssot_blocked(feature: str) -> None:
    """Bloqueo SSOT (2026-09-06): la única ruta de escritura de configs es
    SCRIPTS/sync_models_all.sh. Cualquier intento por CLI del Observatory
    imprime advertencia y NO escribe (early-return)."""
    print(f"\n{C_YELLOW}{C_BOLD}⛔ [{feature}] DESACTIVADO por Arquitectura SSOT.{C_RESET}")
    print(f"   OpenCode = única fuente de verdad de modelos. Propagación:")
    print(f"   👉 bash /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/SCRIPTS/sync_models_all.sh")
    print(f"   (journal: memory-bank/journal/processed/2026-09-06_arquitectura-ssot-fin-bucle-opencode-dsh-antigravity.md)\n")
from src.web.app import start_server


# Colores ANSI para terminal
C_TEAL = "\033[38;2;16;210;173m"
C_CYAN = "\033[38;2;16;214;189m"
C_MINT = "\033[38;2;112;203;172m"
C_NAVY = "\033[38;2;21;38;56m"
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_YELLOW = "\033[38;2;245;158;11m"
C_RED = "\033[38;2;239;68;68m"
C_GREEN = "\033[38;2;34;197;94m"


def print_banner():
    banner = f"""
{C_TEAL}{C_BOLD}======================================================================
  ███████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗ █████╗ 
  ██╔════╝██║     ██╔═══██╗╚██╗ ██╔╝██╔══██╗██║██╔══██╗
  █████╗  ██║     ██║   ██║ ╚████╔╝ ██║  ██║██║███████║
  ██╔══╝  ██║     ██║   ██║  ╚██╔╝  ██║  ██║██║██╔══██║
  ██║     ███████╗╚██████╔╝   ██║   ██████╔╝██║██║  ██║
  ╚═╝     ╚══════╝ ╚═════╝    ╚═╝   ╚═════╝ ╚═╝╚═╝  ╚═╝
  AI COMMAND & OBSERVATORY SUITE v9.2 (Deep Probe + Dynamic Reconfig)
======================================================================{C_RESET}
{C_MINT}«Construimos la inteligencia. Desde la infraestructura.»{C_RESET}
{C_DIM}Firma: FloydIA · Suite Unificada: Rankings + Radar + Sondas Async + Dynamic Injector{C_RESET}
"""
    print(banner)


def cli_ask_interactive():
    """Modo interactivo de consulta en lenguaje natural con el Asesor IA."""
    print(f"\n{C_TEAL}{C_BOLD}🤖 FloydIA AI Advisor (Consulta en Lenguaje Natural){C_RESET}")
    print(f"{C_DIM}Escribe tu pregunta sobre qué modelo te conviene, precios, velocidad o tareas específicas.{C_RESET}")
    print(f"{C_DIM}Escribe 'salir' o presiona Ctrl+C para volver al menú principal.{C_RESET}\n")

    while True:
        try:
            q = input(f"{C_CYAN}💬 Pregunta: {C_RESET}").strip()
            if not q or q.lower() in ["salir", "exit", "quit", "0"]:
                break
            
            print(f"{C_DIM}⏳ Consultando base de datos del Observatorio y analizando con IA...{C_RESET}")
            res = ask_observatory(q)
            
            print(f"\n{C_MINT}{C_BOLD}--- RESPUESTA DEL ASESOR ({res.get('engine', 'FloydIA Engine')}) ---{C_RESET}")
            print(res.get("answer", "No se pudo generar respuesta."))
            print(f"{C_MINT}------------------------------------------------------------{C_RESET}\n")
        except KeyboardInterrupt:
            print("\n")
            break


def cli_recommend_interactive():
    """Modo interactivo de consulta con el Enrutador Inteligente (Router)."""
    print(f"\n{C_TEAL}{C_BOLD}🎯 FloydIA Dynamic Router (Recomendación Multicriterio de LLM){C_RESET}")
    task = input(f"{C_CYAN}Tipo de tarea (coding / reasoning / chat / vision / fast / general) [general]: {C_RESET}").strip() or "general"
    budget = input(f"{C_CYAN}Presupuesto (free / economy / frontier / any) [any]: {C_RESET}").strip() or "any"
    max_lat_in = input(f"{C_CYAN}Latencia máxima en ms (ej. 1000, o Enter para omitir): {C_RESET}").strip()
    max_lat = float(max_lat_in) if max_lat_in.isdigit() else None

    print(f"{C_DIM}⏳ Evaluando candidatos locales, telemetría y restricciones duras...{C_RESET}")
    rec = recommend_model(task=task, budget=budget, max_latency_ms=max_lat)

    m = rec.get("recommended_model", {})
    print(f"\n{C_MINT}{C_BOLD}🏆 MODELO RECOMENDADO (PRIMARY):{C_RESET}")
    print(f"  {C_BOLD}Nombre:{C_RESET} {m.get('canonical_name')} ({m.get('id')})")
    print(f"  {C_BOLD}Proveedor:{C_RESET} {m.get('provider')} | {C_BOLD}Tier:{C_RESET} {m.get('tier')}")
    lat_txt = f"{m.get('local_latency_ms')} ms" if m.get("local_latency_ms") else "—"
    cost_txt = "Gratuito" if m.get("is_free_tier") else f"${m.get('input_cost_per_m')}/1M In"
    print(f"  {C_BOLD}Telemetría:{C_RESET} Latencia {lat_txt} | Coste {cost_txt} | FCI {m.get('intelligence_score')}/100 | Grado {m.get('evidence_grade')}")
    print(f"  {C_BOLD}Motivo:{C_RESET} {m.get('reason')}\n")

    fallbacks = rec.get("cascading_fallbacks", [])
    if fallbacks:
        print(f"{C_CYAN}{C_BOLD}📋 CASCADA DE ALTERNATIVAS (FALLBACKS):{C_RESET}")
        for fb in fallbacks:
            fb_lat = f"{fb.get('local_latency_ms')} ms" if fb.get("local_latency_ms") else "—"
            print(f"  - [{fb.get('reason', 'Alt')}] {fb.get('canonical_name')} ({fb.get('provider')}) — FCI: {fb.get('intelligence_score')}, Lat: {fb_lat}")
    print()


def show_drift_events():
    """Muestra el historial reciente de drift y anomalías detectadas."""
    print(f"\n{C_YELLOW}{C_BOLD}📉 EVENTOS DE DERIVA (DRIFT) Y ANOMALÍAS RECIENTES:{C_RESET}\n")
    events = get_recent_drift_events(limit=20)
    if not events:
        print(f"  {C_MINT}✅ No se han detectado anomalías de precio, latencia ni deprecaciones recientes.{C_RESET}\n")
        return

    for e in events:
        sev_color = C_YELLOW if e.get("severity") == "warning" else "\033[31m"
        print(f"  {sev_color}[{e.get('severity', 'INFO').upper()}]{C_RESET} {e.get('detected_at')} — {e.get('model_id')} ({e.get('provider')}): {e.get('event_type')}")
        print(f"    Métrica: {e.get('metric_name')} | Anterior: {e.get('old_value')} ➔ Nuevo: {e.get('new_value')}")
    print()


def run_cli_deep_scan(prompt: str = DEFAULT_PROBE_PROMPT, filter_status: str = "all", inject: bool = False):
    """Ejecuta el escaneo profundo en CLI mostrando tabla con los 6 estados de respuesta."""
    print(f"\n{C_TEAL}{C_BOLD}🔬 INICIANDO ESCANEO PROFUNDO DE MODELOS IA{C_RESET}")
    print(f"{C_DIM}Pregunta de sondeo:{C_RESET} {C_YELLOW}'{prompt}'{C_RESET} | {C_DIM}Concurrencia máx: 12 | Timeout: 5.0s{C_RESET}\n")

    results = run_deep_scan(prompt=prompt)

    # Filtrado según argumento
    status_map = {
        "ok": STATUS_OK,
        "sin_saldo": STATUS_NO_BALANCE,
        "429": STATUS_FREE_TIER_EXHAUSTED,
        "auth": STATUS_UNAUTHORIZED,
        "timeout": STATUS_NO_RESPONSE,
        "error": STATUS_ERROR
    }
    target_status = status_map.get(filter_status.lower(), None)

    filtered = [r for r in results if target_status is None or r.get("classification") == target_status]

    print(f"\n{C_BOLD}{'MODELO':<35} {'PROVEEDOR':<25} {'LAT':<8} {'ESTADO CLASIFICADO':<35} {'RESPUESTA / SNIPPET':<30}{C_RESET}")
    print("-" * 140)

    for r in filtered:
        cls = r.get("classification", STATUS_ERROR)
        if cls == STATUS_OK:
            col = C_GREEN
        elif cls in (STATUS_NO_BALANCE, STATUS_FREE_TIER_EXHAUSTED):
            col = C_YELLOW
        elif cls == STATUS_UNAUTHORIZED:
            col = C_RED
        elif cls == STATUS_NO_RESPONSE:
            col = C_DIM
        else:
            col = C_RED

        m_name = (r.get("canonical_name") or r.get("model_id"))[:33]
        prov = r.get("provider_display", "")[:23]
        lat = f"{r.get('latency_ms', 0):.0f}ms"
        status_lbl = STATUS_LABELS.get(cls, cls)[:33]
        snip = (r.get("response_snippet") or "")[:28].replace("\n", " ")

        print(f"{m_name:<35} {prov:<25} {lat:<8} {col}{status_lbl:<35}{C_RESET} {snip:<30}")

    # Resumen cuantitativo por estado
    counts = {}
    for r in results:
        c = r.get("classification", STATUS_ERROR)
        counts[c] = counts.get(c, 0) + 1

    print("\n" + "=" * 80)
    print(f"{C_BOLD}📊 RESUMEN DE RESPUESTAS ({len(results)} modelos sondeados):{C_RESET}")
    print(f"  {C_GREEN}🟢 Respuesta OK (100% Funcional):{C_RESET} {counts.get(STATUS_OK, 0)}")
    print(f"  {C_YELLOW}💳 Sin Saldo (402):{C_RESET} {counts.get(STATUS_NO_BALANCE, 0)}")
    print(f"  {C_YELLOW}⏳ Free Tier Agotado (429 Rate Limit):{C_RESET} {counts.get(STATUS_FREE_TIER_EXHAUSTED, 0)}")
    print(f"  {C_RED}🔒 No Autorizado (401/403):{C_RESET} {counts.get(STATUS_UNAUTHORIZED, 0)}")
    print(f"  {C_DIM}⏱️ Sin Respuesta / Timeout:{C_RESET} {counts.get(STATUS_NO_RESPONSE, 0)}")
    print(f"  {C_RED}⚠️ Error de Modelo / Gateway:{C_RESET} {counts.get(STATUS_ERROR, 0)}")
    print("=" * 80)

    if inject:
        _ssot_blocked("inyección post deep-scan")
        return


def interactive_menu():
    print_banner()
    print(f"{C_BOLD}Selecciona las acciones a ejecutar marcando los números separados por coma:{C_RESET}\n")
    print(f"  {C_CYAN}[1]{C_RESET} 🔄 Actualizar Rankings Globales en Vivo (LMSYS, OpenRouter, HF Leaderboard)")
    print(f"  {C_CYAN}[2]{C_RESET} ⚡ Probar y Validar APIs de mi PC (Google C1..C6, DeepSeek, Mistral, Groq, NIM)")
    print(f"  {C_CYAN}[3]{C_RESET} 🔬 ESCANEO PROFUNDO DE MODELOS (Pregunta Corta: '¡hola di si!' en 6 Estados)")
    print(f"  {C_CYAN}[4]{C_RESET} ⚡ INYECTAR MOTORES  ⛔ [DESACTIVADO por SSOT]")
    print(f"  {C_CYAN}[5]{C_RESET} 📡 Sincronizar HP45  ⛔ [ELIMINADO]")
    print(f"  {C_CYAN}[6]{C_RESET} 📄 Generar Informes Diarios con Analista IA (.md, .html y Frontier Snapshot)")
    print(f"  {C_CYAN}[7]{C_RESET} 🌐 Iniciar Dashboard Web de FloydIA (http://localhost:8333)")
    print(f"  {C_CYAN}[8]{C_RESET} 🚀 EJECUCIÓN COMPLETA (Rankings + Sonda + Escáner + Inyección + Sync + Informes)")
    print(f"  {C_CYAN}[9]{C_RESET} 🤖 PREGUNTAR AL ASESOR IA (Consulta en Lenguaje Natural)")
    print(f"  {C_CYAN}[10]{C_RESET} 🖥️  Abrir Interfaz Gráfica PyQt6 con Checkmarks y Filtros Reactivos")
    print(f"  {C_CYAN}[11]{C_RESET} 🎯 RECOMENDAR MODELO (Enrutador Inteligente / Dynamic Router)")
    print(f"  {C_CYAN}[12]{C_RESET} 📉 Ver Eventos de Drift y Deprecación de APIs")
    print(f"  {C_CYAN}[0]{C_RESET} ❌ Salir\n")

    choice = input(f"{C_TEAL}Ingresa tu selección (ej. 3,4 o 10): {C_RESET}").strip()
    if not choice or choice == "0":
        print("Operación cancelada.")
        return

    selected = [c.strip() for c in choice.split(",")]

    if "12" in selected:
        show_drift_events()

    if "11" in selected:
        cli_recommend_interactive()

    if "10" in selected:
        from src.gui.suite_window import run_gui_suite
        run_gui_suite()
        return

    if "9" in selected:
        cli_ask_interactive()
        return

    if "8" in selected:
        run_full_pipeline()
        return

    if "1" in selected:
        run_all_collectors()

    if "2" in selected:
        run_local_api_probes()

    if "3" in selected:
        run_cli_deep_scan(inject=False)

    if "4" in selected:
        _ssot_blocked("inyección de motores (menú opción 4)")

    if "5" in selected:
        print(f"\n{C_BOLD}⛔ Sincronización HP45 ELIMINADA (2026-09-06).{C_RESET}")
        print(f"   La propagación multi-nodo quedó retirada del ecosistema por decisión de arquitectura SSOT.")

    if "6" in selected:
        rankings = calculate_multidimensional_rankings()
        local_apis = get_latest_local_verified_models()
        md_file = generate_daily_markdown_report(rankings, local_apis)
        html_file = generate_daily_html_report(rankings, local_apis)
        frontier_file = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
        print(f"\n{C_TEAL}✅ Informes generados en:{C_RESET}")
        print(f"  - Markdown: {md_file}")
        print(f"  - HTML: {html_file}")
        print(f"  - Snapshot Frontier: {frontier_file}")

    if "7" in selected:
        start_server(8333)


def run_full_pipeline():
    print(f"\n{C_BOLD}🚀 [Pipeline Completo Suite v9.2] Iniciando ejecución integral...{C_RESET}\n")
    # 1. Recolección
    run_all_collectors()
    print()
    # 2. Sonda local
    run_local_api_probes()
    print()
    # 3. Escaneo Profundo 6 estados
    run_cli_deep_scan(inject=False)
    print()
    # 4. Scoring
    rankings = calculate_multidimensional_rankings()
    local_apis = get_latest_local_verified_models()
    print(f"📊 [Scoring] Calculados {len(rankings)} modelos en el ranking.")
    # 5. Inyección de Motores — DESHABILITADA (Arquitectura SSOT)
    #    OpenCode (~/.opencode/opencode.jsonc) es la ÚNICA fuente de verdad de
    #    modelos. El Observatory ya NO escribe OpenCode/Hermes/DSH para evitar
    #    el bucle de regresiones. Propagar el catálogo curado con:
    #        SCRIPTS/sync_models_all.sh
    print(f"\n{C_BOLD}⚙️  [SSOT] Inyección de motores deshabilitada. Usar SCRIPTS/sync_models_all.sh.{C_RESET}")
    # 6. Sincronización HP45 — movida a sync_models_all.sh
    # 7. Informes
    md_file = generate_daily_markdown_report(rankings, local_apis)
    html_file = generate_daily_html_report(rankings, local_apis)
    frontier_file = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
    
    print(f"\n{C_TEAL}{C_BOLD}🎉 PIPELINE SUITE v9.2 EJECUTADO CON ÉXITO:{C_RESET}")
    print(f"  📄 Informe Diario Markdown: {md_file}")
    print(f"  🌐 Visualizador HTML: {html_file}")
    print(f"  📋 Snapshot Frontier AI: {frontier_file}")
    print(f"\n{C_MINT}«Desde la infraestructura, todo.» — FloydIA{C_RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="FloydIA AI Command & Observatory Suite v9.2")
    parser.add_argument("--gui", action="store_true", help="Abre la interfaz gráfica PyQt6 con checkmarks y filtros reactivos")
    parser.add_argument("--full-run", action="store_true", help="Ejecuta recolección, sonda, escáner profundo, inyección, sync e informes")
    parser.add_argument("--collect", action="store_true", help="Actualiza benchmarks y catálogo")
    parser.add_argument("--probe-apis", action="store_true", help="Verifica las APIs configuradas en el equipo")
    parser.add_argument("--deep-scan", action="store_true", help="Ejecuta el escaneo profundo de modelos con la pregunta corta en 6 estados")
    parser.add_argument("--probe-prompt", type=str, default=DEFAULT_PROBE_PROMPT, help="Prompt corto a enviar a cada modelo (default: '¡hola di si!')")
    parser.add_argument("--filter-status", type=str, default="all", help="Filtra por estado: ok, sin_saldo, 429, auth, timeout, error, all")
    parser.add_argument("--inject-selected", action="store_true", help="[DESACTIVADO por SSOT] Antes reescribía OpenCode/Hermes/DSH. No-op; usar SCRIPTS/sync_models_all.sh")
    parser.add_argument("--apply-configs", action="store_true", help="[DESACTIVADO por SSOT] No-op; usar SCRIPTS/sync_models_all.sh")
    parser.add_argument("--sync-hp45", action="store_true", help="[ELIMINADO] Sincronización HP45 retirada del ecosistema")
    parser.add_argument("--generate-daily", action="store_true", help="Genera el informe diario con IA (.md y .html)")
    parser.add_argument("--export-frontier", action="store_true", help="Genera el snapshot .md para IAs Frontier")
    parser.add_argument("--ask", type=str, help="Realiza una pregunta al Asesor IA sobre modelos y costes")
    parser.add_argument("--recommend-model", type=str, nargs="?", const="general", help="Recomienda dinámicamente un modelo según la tarea")
    parser.add_argument("--budget", type=str, default="any", help="Presupuesto para el recomendador: free, economy, frontier, any")
    parser.add_argument("--drift-events", action="store_true", help="Muestra los eventos de drift y anomalías detectadas")
    parser.add_argument("--serve", action="store_true", help="Levanta el servidor web dashboard")
    parser.add_argument("--port", type=int, default=8333, help="Puerto para el servidor web (default: 8333)")

    args = parser.parse_args()

    if args.gui:
        from src.gui.suite_window import run_gui_suite
        run_gui_suite()
        return

    if args.drift_events:
        show_drift_events()
        return

    if args.deep_scan:
        run_cli_deep_scan(prompt=args.probe_prompt, filter_status=args.filter_status, inject=args.inject_selected)
        return

    if args.inject_selected:
        _ssot_blocked("--inject-selected")
        return

    if args.recommend_model is not None:
        rec = recommend_model(task=args.recommend_model, budget=args.budget)
        m = rec.get("recommended_model", {})
        print(f"\n🎯 [FloydIA Dynamic Router] Tarea: '{args.recommend_model}' | Presupuesto: '{args.budget}'")
        print(f"🏆 Modelo Recomendado: {m.get('canonical_name')} ({m.get('provider')})")
        print(f"📊 FCI: {m.get('intelligence_score')}/100 | Latencia: {m.get('local_latency_ms')}ms | Coste: ${m.get('input_cost_per_m')}/1M")
        print(f"📝 Razón: {m.get('reason')}\n")
        return

    if args.ask:
        print(f"🤖 [FloydIA AI Advisor] Analizando: '{args.ask}'...\n")
        res = ask_observatory(args.ask)
        print(res.get("answer", ""))
        return

    if len(sys.argv) == 1:
        interactive_menu()
        return

    if args.full_run:
        run_full_pipeline()
    else:
        if args.collect:
            run_all_collectors()
        if args.probe_apis:
            run_local_api_probes()
        if args.apply_configs:
            _ssot_blocked("--apply-configs")
        if args.sync_hp45:
            print(f"\n{C_BOLD}⛔ --sync-hp45 ELIMINADO (2026-09-06). La sincronización multi-nodo quedó retirada por arquitectura SSOT.{C_RESET}")
        if args.generate_daily:
            rankings = calculate_multidimensional_rankings()
            local_apis = get_latest_local_verified_models()
            generate_daily_markdown_report(rankings, local_apis)
            generate_daily_html_report(rankings, local_apis)
        if args.export_frontier:
            rankings = calculate_multidimensional_rankings()
            local_apis = get_latest_local_verified_models()
            export_daily_snapshot_for_frontier_ai(rankings, local_apis)
        if args.serve:
            start_server(args.port)


if __name__ == "__main__":
    main()
