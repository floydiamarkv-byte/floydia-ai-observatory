"""
Generador de Informes en HTML Estático con Estilo FloydIA V6.
Permite visualizar el informe diario en cualquier navegador con interactividad visual.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from config.settings import DAILY_REPORTS_DIR


def generate_daily_html_report(rankings_data: List[Dict[str, Any]], local_apis_data: List[Dict[str, Any]], analysis_text: str = "") -> Path:
    """Genera un archivo HTML autocontenido para visualización del informe diario."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_path = DAILY_REPORTS_DIR / f"{today_str}_informe_ia_floydia.html"

    local_active = [m for m in rankings_data if m.get("is_local_active")]
    external_models = [m for m in rankings_data if not m.get("is_local_active")]

    # Renderizado HTML limpio y premium
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FloydIA AI Rankings & Local API Observatory — {today_str}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --floydia-teal: #10D2AD;
      --floydia-cyan: #10D6BD;
      --floydia-mint: #70CBAC;
      --floydia-navy: #152638;
      --floydia-ink: #0B111C;
      --floydia-paper: #F5F8F7;
      --floydia-card-bg: #FFFFFF;
      --floydia-card-dark: #111C2B;
      --floydia-text-main: #111827;
      --floydia-text-muted: #4B5563;
      --floydia-border: #E5E7EB;
      --floydia-border-dark: #1F3347;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'IBM Plex Sans', sans-serif;
      background-color: var(--floydia-ink);
      color: #E2E8F0;
      line-height: 1.6;
      padding: 30px 20px;
    }}
    .container {{ max-width: 1280px; margin: 0 auto; }}
    header {{
      border-bottom: 1px solid var(--floydia-border-dark);
      padding-bottom: 24px;
      margin-bottom: 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .brand-title {{
      font-family: 'Chakra Petch', sans-serif;
      font-size: 32px;
      font-weight: 700;
      color: #FFFFFF;
      letter-spacing: -0.02em;
    }}
    .brand-title span {{ color: var(--floydia-teal); }}
    .brand-subtitle {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: var(--floydia-mint);
      margin-top: 4px;
    }}
    .date-badge {{
      background: var(--floydia-navy);
      border: 1px solid var(--floydia-teal);
      color: var(--floydia-teal);
      padding: 6px 14px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      font-weight: 600;
    }}
    .section-card {{
      background: var(--floydia-card-dark);
      border: 1px solid var(--floydia-border-dark);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 32px;
    }}
    .section-title {{
      font-family: 'Chakra Petch', sans-serif;
      font-size: 22px;
      color: #FFFFFF;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .badge-local {{
      background: #064E3B;
      color: var(--floydia-teal);
      padding: 4px 10px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 600;
      border: 1px solid #059669;
    }}
    .badge-external {{
      background: #1F2937;
      color: #9CA3AF;
      padding: 4px 10px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      border: 1px solid #374151;
    }}
    .tier-badge {{
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase;
      font-weight: 600;
    }}
    .tier-frontier {{ background: rgba(139, 92, 246, 0.2); color: #C4B5FD; border: 1px solid #8B5CF6; }}
    .tier-workhorse {{ background: rgba(59, 130, 246, 0.2); color: #93C5FD; border: 1px solid #3B82F6; }}
    .tier-coding {{ background: rgba(16, 185, 129, 0.2); color: #6EE7B7; border: 1px solid #10B981; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--floydia-border-dark);
    }}
    th {{
      font-family: 'JetBrains Mono', monospace;
      color: var(--floydia-mint);
      background: rgba(21, 38, 56, 0.5);
      font-size: 12px;
      text-transform: uppercase;
    }}
    tr:hover {{ background: rgba(16, 210, 173, 0.03); }}
    .code-val {{ font-family: 'JetBrains Mono', monospace; }}
    .score-cell {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      color: var(--floydia-teal);
    }}
    .free-tag {{ color: var(--floydia-teal); font-weight: 600; }}
    footer {{
      text-align: center;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--floydia-border-dark);
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: #64748B;
    }}
    footer strong {{ color: var(--floydia-teal); }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <div class="brand-title">FLOYD<span>IA</span> OBSERVATORY</div>
        <div class="brand-subtitle">WEB & IA AUTOMATION · SISTEMA DE BENCHMARKS Y ARSENAL LOCAL</div>
      </div>
      <div class="date-badge">📅 {today_str}</div>
    </header>

    <!-- SECCIÓN 1: ARSENAL LOCAL -->
    <div class="section-card" style="border-left: 4px solid var(--floydia-teal);">
      <div class="section-title">
        <span>🟢 Modelos Activos en tu Computadora (APIs Verificadas)</span>
      </div>
      <p style="font-size: 14px; color: #94A3B8; margin-bottom: 16px;">
        Modelos con credenciales operativas detectadas en tu entorno local.
      </p>
      <table>
        <thead>
          <tr>
            <th>Modelo Local</th>
            <th>Proveedor</th>
            <th>Categoría</th>
            <th>Ventana Contexto</th>
            <th>Latencia</th>
            <th>Precio ($/1M)</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
"""

    for m in local_active:
        tier_val = m.get('tier') or 'workhorse'
        tier_cls = f"tier-{tier_val}"
        if m.get("is_free_tier"):
            free_txt = "<span class='free-tag'>🆓 GRATIS</span>"
        elif m.get("input_cost_per_m") is not None:
            free_txt = f"${m['input_cost_per_m']:.3f} / ${m.get('output_cost_per_m', 0.0):.3f}"
        else:
            free_txt = "—"
        lat = f"{m['local_latency_ms']} ms" if m.get("local_latency_ms") is not None else "-"
        ctx = f"{m['context_window']:,} tok" if m.get('context_window') else "—"
        intel = f"{m.get('intelligence_score', '—')} / 100"
        html += f"""
          <tr>
            <td><strong>{m.get('canonical_name', 'Unknown')}</strong></td>
            <td>{m.get('provider', '—')}</td>
            <td><span class="tier-badge {tier_cls}">{tier_val}</span></td>
            <td class="code-val">{ctx}</td>
            <td class="code-val">{lat}</td>
            <td class="code-val">{free_txt}</td>
            <td class="score-cell">{intel}</td>
          </tr>
        """

    if not local_active:
        html += "<tr><td colspan='7' style='text-align: center; color: #94A3B8;'>No se detectaron APIs con claves válidas en este sondeo.</td></tr>"

    html += f"""
        </tbody>
      </table>
    </div>

    <!-- SECCIÓN 2: RADAR DE FRONTERA GLOBAL -->
    <div class="section-card">
      <div class="section-title">
        <span>⚪ Radar de Frontera Global (Modelos de Referencia Externa)</span>
      </div>
      <p style="font-size: 14px; color: #94A3B8; margin-bottom: 16px;">
        Modelos punteros a nivel mundial que no tienes configurados localmente.
      </p>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Modelo</th>
            <th>Proveedor</th>
            <th>Categoría</th>
            <th>Inteligencia</th>
            <th>Elo LMSYS</th>
            <th>Precio / 1M</th>
          </tr>
        </thead>
        <tbody>
"""

    for m in external_models[:12]:
        tier_val = m.get('tier') or 'workhorse'
        tier_cls = f"tier-{tier_val}"
        if m.get("is_free_tier"):
            cost_txt = "Gratis"
        elif m.get("input_cost_per_m") is not None:
            cost_txt = f"${m['input_cost_per_m']} / ${m.get('output_cost_per_m', 0.0)}"
        else:
            cost_txt = "—"
        
        pref = m.get('preference_score')
        elo = f"{pref*4 + 1000:.0f}" if pref is not None else "—"
        intel_score = f"{m.get('intelligence_score', '—')}"
        html += f"""
          <tr>
            <td class="code-val">#{m.get('global_rank', '—')}</td>
            <td><strong>{m.get('canonical_name', 'Unknown')}</strong></td>
            <td>{m.get('provider', '—')}</td>
            <td><span class="tier-badge {tier_cls}">{tier_val}</span></td>
            <td class="score-cell">{intel_score}</td>
            <td class="code-val">{elo}</td>
            <td class="code-val">{cost_txt}</td>
          </tr>
        """

    html += f"""
        </tbody>
      </table>
    </div>

    <footer>
      <p>«Construimos la inteligencia. Desde la infraestructura.» — <strong>FloydIA</strong></p>
      <p style="margin-top: 4px; color: #475569;">«Desde la infraestructura, todo.»</p>
    </footer>
  </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"🌐 [HTML Report] Guardado en: {output_path}")
    return output_path
