"""
Generador de Informes Diarios en Markdown con Separación Estricta Local vs Externo.
Aplica el sistema de marca FloydIA V6 y política estricta Grounded Anti-Alucinación (SIN DATO).
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

    profile_categories = {"frontier", "workhorse", "reasoning", "coding", "agentic"}
    local_active = [m for m in rankings_data if m.get("is_local_active")]
    external_models = [m for m in rankings_data if not m.get("is_local_active")]

    # Modelos dentro del perfil vs apéndice fuera de perfil
    in_profile = [m for m in rankings_data if (m.get("tier") or "workhorse").lower() in profile_categories]
    out_profile = [m for m in rankings_data if (m.get("tier") or "workhorse").lower() not in profile_categories]

    # Generar síntesis analítica con motor Grounded v2 (DeepSeek / Gemini)
    ai_analysis = generate_executive_analysis_with_gemini(rankings_data, local_apis_data)

    report_text = f"""# 📊 FLOYDIA AI RANKINGS & LOCAL APIS OBSERVATORY
> **Informe Ejecutivo Diario** · Fecha: **{today_str}**  
> **Firma**: FloydIA — *WEB & IA AUTOMATION*  
> **Motor Analista**: Motor Grounded v2 (Anti-Alucinación & Procedencia Estricta V11)  
> **SSOT**: `FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY/reports/daily/`

---

## 🏛️ 1. DIAGNÓSTICO DE TU ARSENAL LOCAL (APIS ACTIVAS EN TU PC)
> Estos son los modelos que **tienes configurados y funcionando en tu equipo** según el sondeo de hoy.

| Modelo Local | Proveedor | Ventana Contexto | Latencia Inferencia | Coste / 1M Tokens | Score Inteligencia | Estado Sonda |
|---|---|---|---|---|:---:|:---:|
"""

    if local_active:
        for m in local_active:
            free_tag = "🆓 GRATUITO" if m.get("is_free_tier") else f"${m.get('input_cost_per_m', 0.0):.3f} In / ${m.get('output_cost_per_m', 0.0):.3f} Out"
            lat = f"{m['local_latency_ms']} ms" if m.get("local_latency_ms") is not None else "— (Catálogo)"
            ctx = f"{m['context_window']:,} tokens" if m.get("context_window") else "SIN DATO"
            intel = f"**{m['intelligence_score']} / 100**" if m.get('intelligence_score') is not None else "SIN DATO"
            report_text += f"| **{m['canonical_name']}** | {m.get('provider', 'Unknown')} | {ctx} | {lat} | {free_tag} | {intel} | {m.get('local_status_msg', '🟢 OK')} |\n"

    else:
        report_text += "| *No se detectaron APIs con claves válidas en este sondeo* | - | - | - | - | - | 🔴 Inactiva |\n"

    report_text += f"""
---

## 🌐 2. RADAR DE FRONTERA GLOBAL (MODELOS EXTERNOS DE REFERENCIA)
> Modelos punteros en el ranking mundial que **NO tienes instalados/configurados localmente**.

| Ranking | Modelo | Proveedor | Categoría | Score Inteligencia | IC 95% | Preferencia Humana | Coste / 1M Tokens |
|:---:|---|---|---|:---:|:---:|:---:|---|
"""

    for m in external_models[:12]:
        cost_str = "Gratis" if m.get("is_free_tier") else (f"${m['input_cost_per_m']} In / ${m['output_cost_per_m']} Out" if m.get("input_cost_per_m") is not None else "SIN DATO")
        raw_b = m.get("raw_benchmarks", {})
        elo_val = raw_b.get("arena_elo") or raw_b.get("chatbot_arena")
        elo_str = f"{elo_val:.0f} Elo" if elo_val is not None else "SIN DATO"
        intel_str = f"{m['intelligence_score']} / 100" if m.get('intelligence_score') is not None else "SIN DATO"
        ci_str = m.get("ci_display", "SIN DATO")
        rank_str = f"#{m['global_rank']}" if m.get("global_rank") is not None else "—"
        report_text += f"| {rank_str} | **{m['canonical_name']}** | {m.get('provider', 'Unknown')} | `{m.get('tier', 'workhorse')}` | {intel_str} | {ci_str} | {elo_str} | {cost_str} |\n"

    report_text += f"""
---

## 🧠 3. ANÁLISIS ESTRATÉGICO Y RECOMENDACIONES (GROUNDED V2)

{ai_analysis}

---

## 📋 4. TABLA COMPARATIVA PRINCIPAL («TU ARSENAL Y RADAR DE TRABAJO»)

| Rank | Modelo | Disponibilidad | Categoría | FCI (0-100) | IC 95% | Eficiencia | Coding (0-100) | Preferencia (0-100) | Certeza |
|:---:|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
"""

    for m in in_profile:
        badge = "🟢 **LOCAL**" if m.get("is_local_active") else "⚪ EXTERNO"
        coding_str = str(m["coding_score"]) if m.get("coding_score") is not None else "SIN DATO"
        pref_str = str(m["preference_score"]) if m.get("preference_score") is not None else "SIN DATO"
        intel_str = f"**{m['intelligence_score']}**" if m.get("intelligence_score") is not None else "SIN DATO"
        conf_str = m.get("evidence_grade", "D")
        ci_str = m.get("ci_display", "SIN DATO")
        rank_str = f"#{m['global_rank']}" if m.get("global_rank") is not None else "—"
        report_text += f"| {rank_str} | **{m['canonical_name']}** | {badge} | `{m.get('tier', 'workhorse')}` | {intel_str} | {ci_str} | {m.get('workhorse_score', '—')} | {coding_str} | {pref_str} | {conf_str} |\n"

    if out_profile:
        report_text += f"""
---

## 📎 5. APÉNDICE: MODELOS FUERA DE TU PERFIL DE USO PRINCIPAL

| Rank | Modelo | Proveedor | Categoría | Inteligencia | Coste / 1M |
|:---:|---|---|---|:---:|:---:|
"""
        for m in out_profile[:20]:
            cost_str = "Gratis" if m.get("is_free_tier") else (f"${m['input_cost_per_m']} In" if m.get("input_cost_per_m") is not None else "SIN DATO")
            intel_str = str(m.get("intelligence_score", "SIN DATO"))
            rank_str = f"#{m['global_rank']}" if m.get("global_rank") is not None else "—"
            report_text += f"| {rank_str} | **{m['canonical_name']}** | {m.get('provider', 'Unknown')} | `{m.get('tier', 'other')}` | {intel_str} | {cost_str} |\n"

    # Cobertura real de métricas (Procedencia Estricta V11)
    total_m = len(rankings_data)
    n_intel = sum(1 for m in rankings_data if m.get("is_empirically_measured"))
    n_coding = sum(1 for m in rankings_data if m.get("coding_score") is not None)
    n_pref = sum(1 for m in rankings_data if m.get("preference_score") is not None)
    n_local = sum(1 for m in rankings_data if m.get("is_local_active") and m.get("local_latency_ms") is not None)

    report_text += f"""
---

### 🛡️ Metadatos de Auditoría y Fuentes Verificadas
- **Artificial Analysis**: Velocidad (tok/s), latencia (TTFT) y Quality Index.
- **OpenRouter Datasets**: SSOT de catálogo, precios de mercado y context length.
- **Hugging Face**: Open LLM Leaderboard v2 (MMLU-Pro, MATH, GPQA, IFEval).
- **LiveCodeBench & SWE-bench & Aider**: Evaluación holística de código no contaminada.
- **LMSYS / Arena.ai**: Preferencia Humana (Elo).
- **Cobertura Empírica Real**: Inteligencia Medida: {n_intel}/{total_m} | Coding: {n_coding}/{total_m} | Preferencia Humana: {n_pref}/{total_m} | Sonda Directa: {n_local}/{total_m}

> **FloydIA** — *«Construimos la inteligencia. Desde la infraestructura.»*  
> **«Desde la infraestructura, todo.»**
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"📄 [Report Generator] Informe diario guardado en: {output_path}")
    return output_path

