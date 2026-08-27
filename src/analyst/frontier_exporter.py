"""
Exportador de Snapshots Diarios para IAs Frontier (Claude 3.7, GPT-4o, DeepSeek-R1).
Genera un documento Markdown portable empaquetado con directivas de meta-prompting
y el dataset sanitizado del día listo para copiar y pegar.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from config.settings import FRONTIER_EXPORT_DIR


def export_daily_snapshot_for_frontier_ai(rankings_data: List[Dict[str, Any]], local_apis_data: List[Dict[str, Any]]) -> Path:
    """
    Genera el archivo Markdown diario optimizado para ser consumido por IAs Frontier externas.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_file = FRONTIER_EXPORT_DIR / f"{today_str}_SNAPSHOT_FOR_FRONTIER_AI.md"

    # Filtrar modelos
    local_active = [m for m in rankings_data if m.get("is_local_active")]
    external_models = [m for m in rankings_data if not m.get("is_local_active")]
    top_frontier = [m for m in rankings_data if m.get("tier") == "frontier"]
    top_workhorses = [m for m in rankings_data if m.get("tier") == "workhorse"]
    top_coding = [m for m in rankings_data if m.get("tier") == "coding"]

    content = f"""# 🌐 FLOYDIA AI BENCHMARKS & LOCAL APIS — SNAPSHOT DIARIO
> **Fecha de Extracción**: {today_str}  
> **Sistema Emisor**: FloydIA AI Rankings & Local API Observatory v6.0  
> **Firma**: FloydIA — *«Construimos la inteligencia. Desde la infraestructura.»*  
> **Uso Previsto**: Pega este archivo completo en **Claude 3.7 Sonnet, GPT-4o o DeepSeek-R1** para análisis estratégicos avanzados.

---

## 🎯 META-DIRECTIVA PARA LA IA FRONTIER RECEPTORA
```xml
<system>
<role>Consultor Estratégico Senior en Arquitectura de Modelos de Lenguaje, Costes de Inferencia y Eficiencia de LLMs</role>
<task>
Analiza exhaustivamente el dataset adjunto abajo. Este dataset contiene:
1. Las APIs de IA que el usuario TIENE ACTIVAS Y VERIFICADAS EN SU PROPIA MÁQUINA (con ventana de contexto, latencia y costes).
2. El ranking mundial de modelos Frontier, Caballos de Batalla y Coding con puntuaciones normalizadas de LMSYS, Hugging Face, Artificial Analysis y LiveBench.

Responde al usuario ofreciendo:
- Recomendaciones de arquitectura y selección de modelos según el caso de uso que te plantee.
- Auditoría de costes: Cuándo usar sus modelos gratuitos locales vs cuándo vale la pena pagar por un modelo de frontera.
- Diagnóstico de cuellos de botella de contexto y latencia.
</task>
</system>
```

---

## 🟢 1. ARSENAL LOCAL: MODELOS ACTIVOS EN MI COMPUTADORA
*(Estos son los modelos que tengo configurados con API Keys funcionales y probadas hoy en mi equipo)*

| Modelo | Proveedor | Tier | Ventana Contexto | Latencia (ms) | Modo Precio | Coste In/Out ($/1M) | Score Global |
|---|---|---|---|---|---|---|---|
"""

    for m in local_active:
        free_label = "🆓 GRATIS" if m.get("is_free_tier") else f"${m['input_cost_per_m']:.3f} / ${m['output_cost_per_m']:.3f}"
        lat = f"{m['local_latency_ms']} ms" if m.get("local_latency_ms") else "N/A"
        ctx = f"{m['context_window']:,} tok"
        content += f"| **{m['canonical_name']}** | {m['provider']} | `{m['tier']}` | {ctx} | {lat} | {free_label} | ${m['input_cost_per_m']} / ${m['output_cost_per_m']} | **{m['intelligence_score']} / 100** |\n"

    if not local_active:
        content += "| *No se registraron modelos locales activos en este sondeo* | - | - | - | - | - | - | - |\n"

    content += f"""
---

## ⚪ 2. RADAR GLOBAL: MODELOS DE REFERENCIA MUNDIAL (NO INSTALADOS LOCALMENTE)
*(Modelos punteros del mercado que NO tengo activados en mi equipo, para benchmarking comparativo)*

| Ranking | Modelo | Proveedor | Categoría | Inteligencia | Elo LMSYS | Coste / 1M |
|:---:|---|---|---|:---:|:---:|---|
"""

    for m in external_models[:15]:
        cost_str = "Gratis" if m.get("is_free_tier") else f"${m['input_cost_per_m']} / ${m['output_cost_per_m']}"
        content += f"| #{m['global_rank']} | **{m['canonical_name']}** | {m['provider']} | `{m['tier']}` | {m['intelligence_score']} / 100 | {m['preference_score']*4 + 1000:.0f} | {cost_str} |\n"

    content += f"""
---

## 📊 3. SEGMENTACIÓN DETALLADA POR CASOS DE USO

### 👑 Top Modelos Frontier (Máximo Razonamiento)
"""
    for m in top_frontier[:5]:
        badge = "🟢 [EN MI PC]" if m["is_local_active"] else "⚪ [EXTERNO]"
        content += f"- {badge} **{m['canonical_name']}** ({m['provider']}): Score **{m['intelligence_score']}/100** · Contexto: {m['context_window']:,} tokens\n"

    content += f"""
### ⚡ Top Caballos de Batalla (Workhorses de Alta Eficiencia)
"""
    for m in top_workhorses[:5]:
        badge = "🟢 [EN MI PC]" if m["is_local_active"] else "⚪ [EXTERNO]"
        free_note = "(Free Tier)" if m["is_free_tier"] else f"(${m['input_cost_per_m']}/M)"
        content += f"- {badge} **{m['canonical_name']}** {free_note}: Eficiencia **{m['workhorse_score']}/100** · Contexto: {m['context_window']:,} tokens\n"

    content += f"""
### 💻 Top Especialistas en Programación y Agentes
"""
    for m in top_coding[:5]:
        badge = "🟢 [EN MI PC]" if m["is_local_active"] else "⚪ [EXTERNO]"
        content += f"- {badge} **{m['canonical_name']}**: Score Coding **{m['coding_score']}/100**\n"

    content += f"""
---

## 💬 PROMPTS SUGERIDOS PARA PREGUNTAR A LA IA FRONTIER:
1. *«Teniendo en cuenta mis APIs locales activas, ¿cuál es el mejor modelo para armar un agente de extracción de datos masivo con el menor coste?»*
2. *«Compara mi modelo local más potente contra el #1 del ranking mundial: ¿en qué tareas concretas notaré la diferencia y vale la pena pagar la API externa?»*
3. *«Diseña un pipeline de cascada de modelos utilizando exclusivamente mis APIs gratuitas y de bajo costo listadas en la sección 1.»*

---
*Generado automáticamente por FloydIA AI Rankings Observatory el {today_str}.*  
*«Desde la infraestructura, todo.»*
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📄 [Frontier Exporter] Snapshot generado en: {output_file}")
    return output_file
