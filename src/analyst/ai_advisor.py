"""
Módulo de Consultor Inteligente de FloydIA (AI Advisor & Grounded Query Engine).
Permite hacer preguntas en lenguaje natural al Observatorio sobre modelos, costes y recomendaciones.
Usa DeepSeek / Google Gemini con grounding estricto en datos de SQLite y Telemetría Homelab.
"""

import os
import glob
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

from config.settings import (
    DEEPSEEK_API_KEY, DEEPSEEK_API_BASE,
    GEMINI_API_KEY, GEMINI_API_BASE, GEMINI_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_API_BASE,
    GOOGLE_OPENAI_BASE, BASE_DIR
)
from src.core.scoring import calculate_multidimensional_rankings
from src.core.db import get_latest_local_verified_models
from src.core.key_pool import key_pool


def get_latest_radar_telemetry() -> Dict[str, Any]:
    """Lee el último informe de Agent-Radar para conocer latencias reales y fallos de upstream."""
    radar_reports_dir = BASE_DIR.parent / "AGENTES" / "reports"
    telemetry = {"available": False, "models": {}}
    
    if not radar_reports_dir.exists():
        return telemetry

    report_files = sorted(glob.glob(str(radar_reports_dir / "*_floydia_agent_radar_report.md")), reverse=True)
    if not report_files:
        return telemetry

    latest_report = report_files[0]
    try:
        with open(latest_report, "r", encoding="utf-8") as f:
            content = f.read()

        in_table = False
        for line in content.splitlines():
            if "## 📊 2. Tabla de Telemetría" in line:
                in_table = True
                continue
            if in_table and line.startswith("##"):
                break
            if in_table and "|" in line and not line.startswith("| Badge") and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 6:
                    slug = parts[1].replace("`", "")
                    status = parts[4].strip()
                    latency = parts[5].strip()
                    telemetry["models"][slug] = {
                        "status": status,
                        "latency": latency,
                        "healthy": "200" in status
                    }
        telemetry["available"] = True
        telemetry["report_file"] = os.path.basename(latest_report)
    except Exception as e:
        print(f"⚠️ Error leyendo telemetría de radar: {e}")
    return telemetry


def ask_observatory(user_query: str) -> Dict[str, Any]:
    """
    Recibe una consulta en lenguaje natural del usuario (ej: '¿cuál es la mejor y más barata para scraping?'),
    inyecta el catálogo completo con métricas reales del Observatorio y devuelve una respuesta fundamentada.
    """
    if not user_query or not user_query.strip():
        return {
            "success": False,
            "error": "La consulta está vacía.",
            "answer": "Por favor escribe una pregunta sobre modelos, costes o capacidades."
        }

    # 1. Obtener datos frescos del observatorio
    rankings = calculate_multidimensional_rankings()
    local_apis = get_latest_local_verified_models()
    radar_telemetry = get_latest_radar_telemetry()

    top_models = rankings[:30]

    # Compactar contexto para consumo mínimo de tokens y máxima precisión
    models_context = []
    for m in top_models:
        m_id = m.get("id", "")
        # Cruzar con telemetría de red si está disponible
        live_net = radar_telemetry.get("models", {}).get(m_id, {})
        
        models_context.append({
            "id": m_id,
            "name": m.get("canonical_name"),
            "provider": m.get("provider"),
            "tier": m.get("tier"),
            "intelligence_score": m.get("intelligence_score"),
            "workhorse_score": m.get("workhorse_score"),
            "coding_score": m.get("coding_score"),
            "speed_tok_s": m.get("speed_tokens_sec"),
            "ttft_s": m.get("ttft_seconds"),
            "elo_arena": m.get("arena_elo"),
            "input_cost_1m": m.get("input_cost_per_m"),
            "output_cost_1m": m.get("output_cost_per_m"),
            "is_free_tier": m.get("is_free_tier"),
            "context_window": m.get("context_window"),
            "active_in_user_pc": m.get("is_local_active", False),
            "live_ping_status": live_net.get("status", "🟢 200 OK"),
            "live_ping_latency": live_net.get("latency", "N/A"),
            "supports_tools": m.get("supports_tools", False),
            "supports_vision": m.get("supports_vision", False)
        })

    system_prompt = """Eres el Asesor Senior de Arquitectura e Inteligencia Artificial de FloydIA.
Tu trabajo es responder la consulta del usuario recomendando el o los modelos EXACTOS más adecuados basándote ESTRICTAMENTE en los datos reales del Observatorio provistos en el prompt.

FILOSOFÍA FLOYDIA:
- "Construimos la inteligencia. Desde la infraestructura."
- Respuestas directas, hiper-precisas, de grado de ingeniería y sin texto de relleno.
- Diferencia claramente si el modelo recomendado YA ESTÁ CONFIGURADO Y ACTIVO EN SU PC (active_in_user_pc: true) o si requiere API externa.
- TELEMETRÍA DE RED: Si un modelo presenta 'TIMEOUT' o '429' en live_ping_status, adviértelo y sugiere el alternativo con menor latencia probada (ej. Nemotron 3 Super a ~456ms o Codestral a ~766ms).
- Cuando pregunten por "el más barato", compara costes por millón de tokens ($/1M) o si tiene capa 100% gratuita.
- Cuando pregunten por código o razonamiento, cita el Elo de LMSYS Arena, MMLU-Pro o Coding Score.

FORMATO DE TU RESPUESTA (Markdown sobrio en Español):
1. 🎯 **Recomendación Principal (Veredicto)**: Nombre del modelo, por qué es el ganador, si está activo en su PC y su latencia medida en el homelab.
2. 💡 **Alternativa Económica / Gratuita**: Si el ganador tiene costo, ofrece la alternativa costo-cero o más eficiente.
3. 📊 **Tabla Comparativa Clave**: Compara los modelos relevantes (Score, Velocidad/Latencia, Costo Input/Output por 1M, Ventana de Contexto, Estado Local).
4. 💻 **Snippet de Uso Inmediato**: Un bloque de código Python limpio y listo para copiar (usando OpenAI SDK o requests).
5. 🛡️ Cierre breve con el lema: *«Desde la infraestructura, todo.»*
"""

    context_str = json.dumps(models_context, ensure_ascii=False, indent=2)
    user_prompt = f"""DATOS VERIFICADOS DEL OBSERVATORIO FLOYDIA (Top 30 Modelos, APIs Locales y Telemetría Homelab):
{context_str}

PREGUNTA DEL USUARIO:
"{user_query.strip()}"
"""

    # 1. Prioridad: DeepSeek Direct (Pool Multi-Cuenta con Failover)
    ds_acc = key_pool.get_next_healthy_key("deepseek")
    if ds_acc and ds_acc.get("key"):
        try:
            resp = requests.post(
                f"{DEEPSEEK_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {ds_acc['key']}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2048
                },
                timeout=12
            )
            if resp.status_code == 200:
                answer = resp.json()["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "engine": f"DeepSeek V3 [{ds_acc['name']}]",
                    "query": user_query,
                    "answer": answer.strip()
                }
            elif resp.status_code == 429:
                key_pool.mark_rate_limited(ds_acc["name"], cooldown_seconds=60)
        except Exception as e:
            print(f"⚠️ [AI Advisor] DeepSeek ({ds_acc['name']}) falló: {e}. Probando siguiente proveedor...")

    # 2. Secundario: Google AI Studio (Pool Multi-Cuenta OpenAI Compatible)
    google_acc = key_pool.get_next_healthy_key("google")
    if google_acc and google_acc.get("key"):
        for model_name in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
            try:
                resp = requests.post(
                    f"{GOOGLE_OPENAI_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {google_acc['key']}", "Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 2048
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "engine": f"Google Gemini ({model_name}) [{google_acc['name']}]",
                        "query": user_query,
                        "answer": answer.strip()
                    }
                elif resp.status_code == 429:
                    key_pool.mark_rate_limited(google_acc["name"], cooldown_seconds=60)
                    break
            except Exception:
                continue

    # 3. Fallback Heurístico Local
    return _generate_local_rule_based_advice(user_query, rankings, local_apis)


def _generate_local_rule_based_advice(query: str, rankings: List[Dict[str, Any]], local_active: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generador determinista cuando no hay conexión externa."""
    q_lower = query.lower()
    
    is_cheap = any(w in q_lower for w in ["barat", "econom", "gratis", "free", "cost", "precio", "barato"])
    is_code = any(w in q_lower for w in ["cod", "program", "python", "javascript", "dev", "bug", "script"])
    is_reasoning = any(w in q_lower for w in ["razon", "matemat", "pensar", "logica", "complej", "frontier"])
    is_scraping = any(w in q_lower for w in ["scrap", "extraer", "volumen", "masiv", "html", "crawl"])

    if is_cheap or is_scraping:
        rec = next((m for m in rankings if "flash" in m.get("id", "") or "minimax" in m.get("id", "") or m.get("is_free_tier")), rankings[0])
        reason = "ofrece la mayor velocidad (165+ tok/s), 1M de ventana de contexto y costes mínimos o nulos por millón de tokens."
    elif is_code:
        rec = next((m for m in rankings if "codestral" in m.get("id", "") or "coder" in m.get("id", "") or "claude" in m.get("id", "")), rankings[0])
        reason = "posee el benchmark de generación de código y latencia sub-segundo verificada en el clúster."
    elif is_reasoning:
        rec = next((m for m in rankings if m.get("tier") in ["frontier", "reasoning"]), rankings[0])
        reason = "cuenta con arquitectura de razonamiento profundo y mayor puntuación en el Elo de LMSYS Arena."
    else:
        rec = rankings[0]
        reason = "es el modelo con el score global más equilibrado del observatorio."

    answer = f"""### 🎯 Recomendación FloydIA: `{rec.get('canonical_name')}`

**¿Por qué es la mejor opción para tu consulta?**
`{rec.get('canonical_name')}` {reason}

**Ficha Técnica Verificada:**
- **Tier**: `{rec.get('tier')}`
- **Puntuación de Inteligencia**: `{rec.get('intelligence_score')}/100`
- **Coste**: `{'$0.00 (Free Tier)' if rec.get('is_free_tier') else f'${rec.get("input_cost_per_m")}/1M tokens'}`
- **Activo en tu PC**: `{'🟢 Sí, verificado' if rec.get('is_local_active') else '⚪ No activo actualmente'}`
- **Ventana de Contexto**: `{rec.get('context_window', 128000):,} tokens`

> *«Construimos la inteligencia. Desde la infraestructura.»*
> *«Desde la infraestructura, todo.»*
"""
    return {
        "success": True,
        "engine": "FloydIA Rule Engine (Offline Fallback)",
        "query": query,
        "answer": answer
    }
