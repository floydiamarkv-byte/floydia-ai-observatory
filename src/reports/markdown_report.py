"""
Generador de Informes Diarios en Markdown con Separación Estricta Local vs Externo.
Aplica el sistema de marca FloydIA V6 y estructura AIDA sobria.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from config.settings import DAILY_REPORTS_DIR
from src.analyst.gemini_analyst import generate_executive_analysis_with_gemini


def generate_daily_markdown_report(rankings_data: List[Dict[str, Any]], local_apis_data: List[Dict[str, Any]]) -> Path:
    """
    Construye el informe diario completo en Markdown guardándolo en reports/daily/.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_path = DAILY_REPORTS_DIR / f"{today_str}_informe_ia_floydia.md"

    local_active = [m for m in rankings_data if m.get("is_local_active")]
    external_models = [m for m in rankings_data if not m.get("is_local_active")]

    # Generar síntesis analítica con Gemini 2.5 Flash Free
    ai_analysis = generate_executive_analysis_with_gemini(rankings_data, local_apis_data)

    report_text = f"""# 📊 FLOYDIA AI RANKINGS & LOCAL APIS OBSERVATORY
> **Informe Ejecutivo Diario** · Fecha: **{today_str}**  
> **Firma**: FloydIA — *WEB & IA AUTOMATION*  
> **Motor Analista**: Google AI Studio Free API (`gemini-2.5-flash`)  
> **SSOT**: `FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY/reports/daily/`

---

## 🏛️ 1. DIAGNÓSTICO DE TU ARSENAL LOCAL (APIS ACTIVAS EN TU PC)
> Estos son los modelos que **tienes configurados y funcionando en tu equipo** según el sondeo de hoy.

| Modelo Local | Proveedor | Ventana Contexto | Latencia | Coste / 1M Tokens | Score Inteligencia | Estado Sonda |
|---|---|---|---|---|:---:|:---:|
"""

    if local_active:
        for m in local_active:
            free_tag = "🆓 GRATUITO" if m.get("is_free_tier") else f"${m['input_cost_per_m']:.3f} In / ${m['output_cost_per_m']:.3f} Out"
            lat = f"{m['local_latency_ms']} ms" if m.get("local_latency_ms") else "-"
            ctx = f"{m['context_window']:,} tokens"
            report_text += f"| **{m['canonical_name']}** | {m['provider']} | {ctx} | {lat} | {free_tag} | **{m['intelligence_score']} / 100** | {m.get('local_status_msg', '🟢 OK')} |\n"
    else:
        report_text += "| *No se detectaron APIs con claves válidas en este sondeo* | - | - | - | - | - | 🔴 Inactiva |\n"

    report_text += f"""
---

## 🌐 2. RADAR DE FRONTERA GLOBAL (MODELOS EXTERNOS DE REFERENCIA)
> Modelos punteros en el ranking mundial que **NO tienes instalados/configurados localmente**.

| Ranking | Modelo | Proveedor | Categoría | Score Inteligencia | Elo LMSYS | Coste / 1M Tokens |
|:---:|---|---|---|:---:|:---:|---|
"""

    for m in external_models[:12]:
        cost_str = "Gratis" if m.get("is_free_tier") else f"${m['input_cost_per_m']} In / ${m['output_cost_per_m']} Out"
        elo_str = f"{m['preference_score']*4 + 1000:.0f}"
        report_text += f"| #{m['global_rank']} | **{m['canonical_name']}** | {m['provider']} | `{m['tier']}` | {m['intelligence_score']} / 100 | {elo_str} | {cost_str} |\n"

    report_text += f"""
---

## 🧠 3. ANÁLISIS ESTRATÉGICO Y RECOMENDACIONES (GEMINI 2.5 FLASH)

{ai_analysis}

---

## 📋 4. TABLA COMPARATIVA MULTIDIMENSIONAL COMPLETA

| Rank | Modelo | Disponibilidad | Categoría | Inteligencia (0-100) | Eficiencia Caballo Batalla | Coding (0-100) | Preferencia Elo |
|:---:|---|:---:|---|:---:|:---:|:---:|:---:|
"""

    for m in rankings_data:
        badge = "🟢 **LOCAL**" if m["is_local_active"] else "⚪ EXTERNO"
        report_text += f"| #{m['global_rank']} | **{m['canonical_name']}** | {badge} | `{m['tier']}` | **{m['intelligence_score']}** | {m['workhorse_score']} | {m['coding_score']} | {m['preference_score']} |\n"

    report_text += f"""
---

### 🛡️ Metadatos de Auditoría y Fuentes
- **LMSYS Chatbot Arena**: Evaluaciones A/B con Elo normalizado.
- **Artificial Analysis**: Métricas de velocidad (tok/s), TTFT y calidad.
- **OpenRouter Datasets**: Catálogo, precios de mercado y adopción.
- **Hugging Face**: Open LLM Leaderboard v2 (MMLU-Pro, MATH, GPQA).
- **LiveBench & Epoch AI**: Benchmarks científicos no contaminados.

> **FloydIA** — *«Construimos la inteligencia. Desde la infraestructura.»*  
> **«Desde la infraestructura, todo.»**
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"📄 [Report Generator] Informe diario guardado en: {output_path}")
    return output_path
