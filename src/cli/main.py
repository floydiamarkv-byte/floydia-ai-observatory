"""
Punto de Entrada CLI & GUI Unificado de FloydIA AI Command & Observatory Suite (v9.0).
Permite selección de tareas por checkmarks, consultas en lenguaje natural con IA,
reescritura de motores y ejecución modular / visual.
"""

import sys
import argparse
from datetime import datetime
from typing import List

from src.collectors.aggregator import run_all_collectors
from src.probers.local_verifier import run_local_api_probes
from src.core.scoring import calculate_multidimensional_rankings
from src.core.db import get_latest_local_verified_models
from src.reports.markdown_report import generate_daily_markdown_report
from src.reports.html_report import generate_daily_html_report
from src.analyst.frontier_exporter import export_daily_snapshot_for_frontier_ai
from src.analyst.ai_advisor import ask_observatory
from src.core.engine_injector import apply_engine_configurations, sync_to_hp45
from src.web.app import start_server


# Colores ANSI para terminal
C_TEAL = "\033[38;2;16;210;173m"
C_CYAN = "\033[38;2;16;214;189m"
C_MINT = "\033[38;2;112;203;172m"
C_NAVY = "\033[38;2;21;38;56m"
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"


def print_banner():
    banner = f"""
{C_TEAL}{C_BOLD}======================================================================
  ███████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗ █████╗ 
  ██╔════╝██║     ██╔═══██╗╚██╗ ██╔╝██╔══██╗██║██╔══██╗
  █████╗  ██║     ██║   ██║ ╚████╔╝ ██║  ██║██║███████║
  ██╔══╝  ██║     ██║   ██║  ╚██╔╝  ██║  ██║██║██╔══██║
  ██║     ███████╗╚██████╔╝   ██║   ██████╔╝██║██║  ██║
  ╚═╝     ╚══════╝ ╚═════╝    ╚═╝   ╚═════╝ ╚═╝╚═╝  ╚═╝
  AI COMMAND & OBSERVATORY SUITE v9.0 (8 Benchmark Sources)
======================================================================{C_RESET}
{C_MINT}«Construimos la inteligencia. Desde la infraestructura.»{C_RESET}
{C_DIM}Firma: FloydIA · Suite Unificada: Rankings + Radar + Inyector de Motores{C_RESET}
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


def interactive_menu():
    print_banner()
    print(f"{C_BOLD}Selecciona las acciones a ejecutar marcando los números separados por coma:{C_RESET}\n")
    print(f"  {C_CYAN}[1]{C_RESET} 🔄 Actualizar Rankings Globales en Vivo (LMSYS, OpenRouter, HF Leaderboard)")
    print(f"  {C_CYAN}[2]{C_RESET} ⚡ Probar y Validar APIs de mi PC (Google C1..C6, DeepSeek, Mistral, Groq, NIM)")
    print(f"  {C_CYAN}[3]{C_RESET} ⚙️  Reescribir e Inyectar Motores (OpenCode + Hermes + DeepSeek Harness)")
    print(f"  {C_CYAN}[4]{C_RESET} 📡 Sincronizar Clúster hacia HP45 (Rsync tec@192.168.1.200)")
    print(f"  {C_CYAN}[5]{C_RESET} 📄 Generar Informes Diarios con Analista IA (.md, .html y Frontier Snapshot)")
    print(f"  {C_CYAN}[6]{C_RESET} 🌐 Iniciar Dashboard Web de FloydIA (http://localhost:8333)")
    print(f"  {C_CYAN}[7]{C_RESET} 🚀 EJECUCIÓN COMPLETA (Rankings + Sonda + Motores + Sync + Informes)")
    print(f"  {C_CYAN}[8]{C_RESET} 🤖 PREGUNTAR AL ASESOR IA (Consulta en Lenguaje Natural)")
    print(f"  {C_CYAN}[9]{C_RESET} 🖥️  Abrir Interfaz Gráfica PyQt6 con Checkmarks")
    print(f"  {C_CYAN}[0]{C_RESET} ❌ Salir\n")

    choice = input(f"{C_TEAL}Ingresa tu selección (ej. 1,2,3 o 7): {C_RESET}").strip()
    if not choice or choice == "0":
        print("Operación cancelada.")
        return

    selected = [c.strip() for c in choice.split(",")]

    if "9" in selected:
        from src.gui.suite_window import run_gui_suite
        run_gui_suite()
        return

    if "8" in selected:
        cli_ask_interactive()
        return

    if "7" in selected:
        run_full_pipeline()
        return

    if "1" in selected:
        run_all_collectors()

    if "2" in selected:
        run_local_api_probes()

    if "3" in selected:
        print(f"\n{C_BOLD}⚙️  Inyectando configuraciones a OpenCode, Hermes y DSH...{C_RESET}")
        for msg, lvl in apply_engine_configurations():
            print(f"  {msg}")

    if "4" in selected:
        print(f"\n{C_BOLD}📡 Sincronizando con HP45...{C_RESET}")
        msg, lvl = sync_to_hp45()
        print(f"  {msg}")

    if "5" in selected:
        rankings = calculate_multidimensional_rankings()
        local_apis = get_latest_local_verified_models()
        md_file = generate_daily_markdown_report(rankings, local_apis)
        html_file = generate_daily_html_report(rankings, local_apis)
        frontier_file = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
        print(f"\n{C_TEAL}✅ Informes generados en:{C_RESET}")
        print(f"  - Markdown: {md_file}")
        print(f"  - HTML: {html_file}")
        print(f"  - Snapshot Frontier: {frontier_file}")

    if "6" in selected:
        start_server(8333)


def run_full_pipeline():
    print(f"\n{C_BOLD}🚀 [Pipeline Completo Suite v8.0] Iniciando ejecución integral...{C_RESET}\n")
    # 1. Recolección
    run_all_collectors()
    print()
    # 2. Sonda local
    run_local_api_probes()
    print()
    # 3. Scoring
    rankings = calculate_multidimensional_rankings()
    local_apis = get_latest_local_verified_models()
    print(f"📊 [Scoring] Calculados {len(rankings)} modelos en el ranking.")
    # 4. Inyección de Motores
    print(f"\n{C_BOLD}⚙️  Inyectando configuraciones a OpenCode, Hermes y DSH...{C_RESET}")
    for msg, lvl in apply_engine_configurations():
        print(f"  {msg}")
    # 5. Sincronización HP45
    print(f"\n{C_BOLD}📡 Sincronizando hacia HP45...{C_RESET}")
    msg, lvl = sync_to_hp45()
    print(f"  {msg}")
    # 6. Informes
    md_file = generate_daily_markdown_report(rankings, local_apis)
    html_file = generate_daily_html_report(rankings, local_apis)
    frontier_file = export_daily_snapshot_for_frontier_ai(rankings, local_apis)
    
    print(f"\n{C_TEAL}{C_BOLD}🎉 PIPELINE SUITE v8.0 EJECUTADO CON ÉXITO:{C_RESET}")
    print(f"  📄 Informe Diario Markdown: {md_file}")
    print(f"  🌐 Visualizador HTML: {html_file}")
    print(f"  📋 Snapshot Frontier AI: {frontier_file}")
    print(f"\n{C_MINT}«Desde la infraestructura, todo.» — FloydIA{C_RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="FloydIA AI Command & Observatory Suite v8.0")
    parser.add_argument("--gui", action="store_true", help="Abre la interfaz gráfica PyQt6 con checkmarks")
    parser.add_argument("--full-run", action="store_true", help="Ejecuta recolección, sonda, inyección de motores, sincronización e informes")
    parser.add_argument("--collect", action="store_true", help="Actualiza benchmarks y catálogo")
    parser.add_argument("--probe-apis", action="store_true", help="Verifica las APIs configuradas en el equipo")
    parser.add_argument("--apply-configs", action="store_true", help="Reescribe e inyecta las configuraciones en OpenCode, Hermes y DSH")
    parser.add_argument("--sync-hp45", action="store_true", help="Sincroniza configuraciones al nodo secundario HP45 vía Rsync")
    parser.add_argument("--generate-daily", action="store_true", help="Genera el informe diario con IA (.md y .html)")
    parser.add_argument("--export-frontier", action="store_true", help="Genera el snapshot .md para IAs Frontier")
    parser.add_argument("--ask", type=str, help="Realiza una pregunta al Asesor IA sobre modelos y costes")
    parser.add_argument("--serve", action="store_true", help="Levanta el servidor web dashboard")
    parser.add_argument("--port", type=int, default=8333, help="Puerto para el servidor web (default: 8333)")

    args = parser.parse_args()

    if args.gui:
        from src.gui.suite_window import run_gui_suite
        run_gui_suite()
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
            for msg, lvl in apply_engine_configurations():
                print(f"  {msg}")
        if args.sync_hp45:
            msg, lvl = sync_to_hp45()
            print(f"  {msg}")
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
