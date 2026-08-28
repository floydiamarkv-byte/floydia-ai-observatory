"""
Exportador de Snapshots Diarios para IAs Frontier (Claude 3.7, GPT-4o, DeepSeek-R1) v9.1.
Genera un documento Markdown portable empaquetado con directivas de meta-prompting
y el dataset sanitizado del día listo para copiar y pegar, garantizando que
todos los modelos verificados localmente aparezcan en el arsenal.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.settings import FRONTIER_EXPORT_DIR


def export_daily_snapshot_for_frontier_ai(rankings_data: List[Dict[str, Any]], local_apis_data: List[Dict[str, Any]]) -> Path:
    """
    Genera el archivo Markdown diario optimizado para ser consumido por IAs Frontier externas.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_file = FRONTIER_EXPORT_DIR / f"{today_str}_SNAPSHOT_FOR_FRONTIER_AI.md"

    # Mapeo de ranking por múltiples identificadores
    ranking_by_key = {}
    for m in rankings_data:
        ranking_by_key[m["id"]] = m
        ranking_by_key[m.get("canonical_name", "")] = m

    # 1. Arsenal local: Unir modelos de rankings_data con is_local_active y checks funcionales de local_apis_data
    local_models_dict = {}

    # A) Desde rankings_data
    for m in rankings_data:
        if m.get("is_local_active"):
            local_models_dict[m["id"]] = m

    # B) Desde local_apis_data (para no perder ningún check funcional, excluyendo catálogo sintético y sin probe)
    for c in local_apis_data:
        if c.get("is_functional") and not c.get("is_synthetic") and c.get("latency_ms") is not None:
            can_id = c.get("canonical_id") or c.get("model_identifier")
            if can_id and can_id not in local_models_dict:
                matched_rank = ranking_by_key.get(can_id) or ranking_by_key.get(c.get("model_identifier"))
                if matched_rank:
                    matched_rank = dict(matched_rank)
                    matched_rank["is_local_active"] = True
                    matched_rank["local_latency_ms"] = c.get("latency_ms")
                    local_models_dict[can_id] = matched_rank
                else:
                    # Crear entrada sintética enriquecida desde telemetría
                    local_models_dict[can_id] = {
                        "id": can_id,
                        "canonical_name": c.get("canonical_name") or c.get("model_identifier"),
                        "provider": c.get("provider_name", "Local"),
                        "tier": c.get("tier", "workhorse"),
                        "context_window": c.get("detected_context_window", 128000),
                        "local_latency_ms": c.get("latency_ms", 0.0),
                        "is_free_tier": bool(c.get("is_free_tier")),
                        "input_cost_per_m": c.get("cost_input_m", 0.0),
                        "output_cost_per_m": c.get("cost_output_m", 0.0),
                        "intelligence_score": "Verificado",
                        "is_local_active": True
                    }

    local_active = sorted(local_models_dict.values(), key=lambda x: (x.get("local_latency_ms") or 9999))
    external_models = [m for m in rankings_data if m["id"] not in local_models_dict]

    top_frontier = [m for m in rankings_data if m.get("tier") == "frontier"]
    top_workhorses = [m for m in rankings_data if m.get("tier") == "workhorse"]
    top_coding = [m for m in rankings_data if m.get("tier") == "coding"]

    content = f"""# 🌐 FLOYDIA AI BENCHMARKS & LOCAL APIS — SNAPSHOT DIARIO
> **Fecha de Extracción**: {today_str}  
> **Sistema Emisor**: FloydIA AI Rankings & Local API Observatory v9.1  
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

## 🟢 1. ARSENAL LOCAL: MODELOS ACTIVOS EN MI COMPUTADORA ({len(local_active)} Modelos Verificados)
*(Estos son los modelos que tengo configurados con API Keys funcionales y probadas hoy en mi equipo)*

| Modelo | Proveedor | Tier | Ventana Contexto | Latencia (ms) | Modo Precio | Coste In/Out ($/1M) | Score Global |
|---|---|---|---|---|---|---|---|
"""

    for m in local_active:
        free_label = "🆓 GRATIS" if m.get("is_free_tier") else f"${m.get('input_cost_per_m', 0.0):.3f} / ${m.get('output_cost_per_m', 0.0):.3f}"
        lat = f"{m['local_latency_ms']:.1f} ms" if m.get("local_latency_ms") else "—"
        ctx = f"{m.get('context_window', 128000):,} tok"
        score = f"**{m.get('intelligence_score', '—')} / 100**" if isinstance(m.get('intelligence_score'), (int, float)) else f"**{m.get('intelligence_score', 'Activo')}**"
        content += f"| **{m['canonical_name']}** | {m.get('provider', 'Local')} | `{m.get('tier', 'workhorse')}` | {ctx} | {lat} | {free_label} | ${m.get('input_cost_per_m', 0.0)} / ${m.get('output_cost_per_m', 0.0)} | {score} |\n"

    if not local_active:
        content += "| *No se registraron modelos locales activos en este sondeo* | - | - | - | - | - | - | - |\n"

    content += f"""
---

## ⚪ 2. RADAR GLOBAL: MODELOS DE REFERENCIA MUNDIAL (NO INSTALADOS LOCALMENTE)
*(Modelos punteros del mercado que NO tengo activados en mi equipo, para benchmarking comparativo)*

| Ranking | Modelo | Proveedor | Categoría | Inteligencia | Elo LMSYS | Coste / 1M |
|:---:|---|---|---|:---:|:---:|---|
"""

    for m in external_models[:20]:
        cost_str = "Gratis" if m.get("is_free_tier") else f"${m.get('input_cost_per_m', 0.0)} / ${m.get('output_cost_per_m', 0.0)}"
        pref = f"{m.get('preference_score', 0)*4 + 1000:.0f}" if isinstance(m.get('preference_score'), (int, float)) else "—"
        intel = f"{m.get('intelligence_score', '—')} / 100" if isinstance(m.get('intelligence_score'), (int, float)) else "—"
        content += f"| #{m.get('global_rank', '—')} | **{m['canonical_name']}** | {m.get('provider', 'External')} | `{m.get('tier', 'workhorse')}` | {intel} | {pref} | {cost_str} |\n"

    content += f"""
---

## 📊 3. SEGMENTACIÓN DETALLADA POR CASOS DE USO

### 👑 Top Modelos Frontier (Máximo Razonamiento)
"""
    for m in top_frontier[:5]:
        badge = "🟢 [EN MI PC]" if m.get("is_local_active") or m["id"] in local_models_dict else "⚪ [EXTERNO]"
        content += f"- {badge} **{m['canonical_name']}** ({m.get('provider')}): Score **{m.get('intelligence_score', '—')}/100** · Contexto: {m.get('context_window', 0):,} tokens\n"

    content += f"""
### ⚡ Top Caballos de Batalla (Workhorses de Alta Eficiencia)
"""
    for m in top_workhorses[:5]:
        badge = "🟢 [EN MI PC]" if m.get("is_local_active") or m["id"] in local_models_dict else "⚪ [EXTERNO]"
        free_note = "(Free Tier)" if m.get("is_free_tier") else f"(${m.get('input_cost_per_m', 0.0)}/M)"
        content += f"- {badge} **{m['canonical_name']}** {free_note}: Eficiencia **{m.get('workhorse_score', '—')}/100** · Contexto: {m.get('context_window', 0):,} tokens\n"

    content += f"""
### 💻 Top Especialistas en Programación y Agentes
"""
    for m in top_coding[:5]:
        badge = "🟢 [EN MI PC]" if m.get("is_local_active") or m["id"] in local_models_dict else "⚪ [EXTERNO]"
        content += f"- {badge} **{m['canonical_name']}**: Score Coding **{m.get('coding_score', '—')}/100**\n"

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
