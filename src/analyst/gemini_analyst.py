"""
Analista IA impulsado por DeepSeek V3 / Google AI Studio.
Genera análisis estratégicos y cruce de datos con estricta separación de hechos vs conjeturas.
"""

import json
from typing import Dict, Any, List
import requests
from config.settings import (
    DEEPSEEK_API_KEY, DEEPSEEK_API_BASE,
    GEMINI_API_KEY, GOOGLE_OPENAI_BASE
)


def generate_executive_analysis_with_gemini(rankings_data: List[Dict[str, Any]], local_apis_data: List[Dict[str, Any]]) -> str:
    """
    Envía el resumen estructurado al motor de IA para generar el análisis ejecutivo del día.
    Prioriza DeepSeek V3 / Gemini Flash con fallback determinista.
    """
    local_active = [m for m in rankings_data if m.get("is_local_active")]
    top_frontier = [m for m in rankings_data if m.get("tier") == "frontier"][:5]
    top_workhorses = [m for m in rankings_data if m.get("tier") == "workhorse"][:5]

    prompt = f"""Eres el Analista Principal de IA de FloydIA (Firma de Ingeniería y Automatización de IA).
Tu tarea es generar un informe ejecutivo, técnico y sin rodeos (estilo sobrio de FloydIA: "Construimos la inteligencia desde la infraestructura") analizando los rankings de IA del día y el estado de las APIs locales activas en el equipo.

DATOS DISPONIBLES DEL DÍA:

1. MODELOS ACTIVOS EN TU PC (APIs Locales Verificadas):
{json.dumps([{"name": m["canonical_name"], "tier": m["tier"], "score": m["intelligence_score"], "free": m["is_free_tier"], "cost_m": m["input_cost_per_m"]} for m in local_active[:15]], indent=2)}

2. TOP 5 MODELOS FRONTIER / RAZONAMIENTO MUNDIAL:
{json.dumps([{"name": m["canonical_name"], "score": m["intelligence_score"], "active_in_pc": m["is_local_active"]} for m in top_frontier], indent=2)}

3. TOP 5 CABALLOS DE BATALLA (WORKHORSES):
{json.dumps([{"name": m["canonical_name"], "workhorse_score": m["workhorse_score"], "active_in_pc": m["is_local_active"]} for m in top_workhorses], indent=2)}

DIRECTIVAS DE RESPUESTA:
- Separa claramente: Lo que está ACTIVO EN TU PC vs lo que es SOLO REFERENCIA EXTERNA.
- Destaca cuál es el mejor modelo gratuito o de bajo costo para tareas diarias.
- Recomienda qué modelo local usar para: 1) Razonamiento pesado, 2) Flujos de alto volumen / scraping, 3) Programación / Tool Calling.
- Cierra con la frase oficial de FloydIA: "Desde la infraestructura, todo."
- Responde en Markdown estructurado en Español con tono profesional de ingeniería.
"""

    # 1. DeepSeek Direct (Ultra fiable, <1s)
    if DEEPSEEK_API_KEY:
        try:
            resp = requests.post(
                f"{DEEPSEEK_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 2048
                },
                timeout=12
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                print("✨ [Analyst] Informe ejecutivo generado exitosamente con DeepSeek V3.")
                return text
        except Exception:
            pass

    # 2. Google AI Studio (Endpoint OpenAI Compatible — más estable)
    if GEMINI_API_KEY:
        for model_name in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
            try:
                resp = requests.post(
                    f"{GOOGLE_OPENAI_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": 2048
                    },
                    timeout=10
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    print(f"✨ [Gemini Analyst] Informe generado con '{model_name}' (OpenAI-compat).")
                    return text
            except Exception:
                continue

    print("⚠️ [Analyst] Usando síntesis determinista.")
    return _generate_deterministic_fallback_analysis(rankings_data, local_apis_data)


def _generate_deterministic_fallback_analysis(rankings: List[Dict[str, Any]], local_apis: List[Dict[str, Any]]) -> str:
    """Generador determinista de análisis cuando las APIs no están disponibles."""
    local_active = [m for m in rankings if m.get("is_local_active")]
    top_frontier = [m for m in rankings if m.get("tier") == "frontier"][:3]
    top_workhorse = [m for m in rankings if m.get("tier") == "workhorse"][:3]

    lines = [
        "### 🧠 Síntesis Ejecutiva del Observatorio FloydIA",
        "",
        "#### 1. Diagnóstico de tu Arsenal Local (APIs Verificadas)",
        f"- Cuentas con **{len(local_active)} modelos activos** y verificados en tu equipo.",
    ]
    
    if local_active:
        best_local = local_active[0]
        lines.append(f"- **Tu modelo local más potente**: `{best_local['canonical_name']}` (Score Inteligencia: {best_local['intelligence_score']}/100).")
        free_locals = [m for m in local_active if m.get("is_free_tier")]
        if free_locals:
            lines.append(f"- **Tus opciones gratuitas recomendadas**: {', '.join([f'`{m['canonical_name']}`' for m in free_locals[:5]])}.")
    else:
        lines.append("- *Nota*: No se detectaron APIs con estado funcional en este sondeo. Revisa tus claves en `.secrets/antigravity.env`.")

    lines.extend([
        "",
        "#### 2. Radar de Frontera Global (Modelos de Referencia)",
        f"- **Líderes Mundiales en Razonamiento**: {', '.join([f'`{m['canonical_name']}`' for m in top_frontier])}.",
        f"- **Líderes en Eficiencia Diaria (Caballos de Batalla)**: {', '.join([f'`{m['canonical_name']}`' for m in top_workhorse])}.",
        "",
        "> *«Construimos la inteligencia. Desde la infraestructura.»* — **FloydIA**",
        "> *«Desde la infraestructura, todo.»*"
    ])
    return "\n".join(lines)
