"""
Analista IA de FloydIA — Motor de Redacción v2 (Anti-Alucinación y Grounded Reporting V11).
Separa Etapa A (Retrieval determinista), Etapa B (Redacción fundamentada estricta) y Etapa C (Verificación determinista).
"""

import re
import json
from typing import Dict, Any, List, Optional, Set
import requests
from config.settings import (
    DEEPSEEK_API_KEY, DEEPSEEK_API_BASE,
    GEMINI_API_KEY, GOOGLE_OPENAI_BASE
)
from src.core.scoring import build_input_data_payload


def verify_historical_facts(md_text: str) -> List[str]:
    """
    D-4: Verifica que las citas históricas no contengan alucinaciones de versiones anteriores.
    Hecho verificado: En v10.0, el 100% de los modelos colapsaron en Grado C (377/377 modelos).
    """
    violations = []
    # Si menciona v10 y porcentajes erróneos de grado C
    if "v10" in md_text.lower() or "versión 10" in md_text.lower():
        # Validar que si cita el colapso v10, cite 100% o 377/377
        match_wrong_c = re.search(r"v10[^\n]*?(\d{1,3}(?:\.\d+)?)\s*%[^\n]*?grado\s+c", md_text, re.IGNORECASE)
        if match_wrong_c:
            val = float(match_wrong_c.group(1))
            if abs(val - 100.0) > 1.0:
                violations.append(f"Historical misquote (D-4): v10 Grade C reported as {val}%, actual historical SSOT was 100.0% (377/377)")
    return violations



def verify_report_stage_c(md_text: str, input_data: Dict[str, Any]) -> List[str]:
    """
    ETAPA C (FloydIA Verifier Anti-Hallucination V11.1):
    Valida que toda cifra cuantitativa en el Markdown generado exista en INPUT_DATA o sea derivable/constante,
    y que las citas históricas coincidan con los hechos certificados (D-4).
    """
    allowed_numbers: Set[float] = {
        0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
        12.0, 15.0, 20.0, 24.0, 28.0, 30.0, 90.0, 95.0, 100.0, 360.0, 361.9,
        1000.0, 8192.0, 16384.0, 32768.0, 65536.0, 128000.0, 200000.0, 256000.0,
        500000.0, 1000000.0, 1048576.0, 2000000.0, 2097152.0, 2026.0, 377.0
    }

    # Recolectar todos los valores permitidos del payload INPUT_DATA
    for m in input_data.get("models", []):
        for k, v in m.items():
            if isinstance(v, (int, float)):
                val = float(v)
                allowed_numbers.add(round(val, 2))
                allowed_numbers.add(round(val, 1))
                allowed_numbers.add(float(int(val)))
        raw_b = m.get("raw_benchmarks", {})
        for _, bv in raw_b.items():
            if isinstance(bv, (int, float)):
                allowed_numbers.add(round(float(bv), 2))
                allowed_numbers.add(round(float(bv), 1))

    # Extraer números del markdown
    violations = []
    found_nums = re.findall(r"(?<![\w/.#-])(\d{1,4}(?:\.\d{1,3})?)(?![\w.])", md_text)
    for num_str in found_nums:
        try:
            num = float(num_str)
            if num in allowed_numbers or round(num, 1) in allowed_numbers or round(num, 2) in allowed_numbers:
                continue
            if int(num) in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 20, 2026, 28, 29):
                continue
            violations.append(num_str)
        except ValueError:
            continue

    # Agregar violaciones históricas (D-4)
    violations.extend(verify_historical_facts(md_text))

    return violations


def generate_executive_analysis_with_gemini(
    rankings_data: List[Dict[str, Any]], 
    local_apis_data: List[Dict[str, Any]]
) -> str:
    """
    ETAPA B + ETAPA C:
    Redacta el informe ejecutivo basándose EXCLUSIVAMENTE en el bloque JSON INPUT_DATA de Etapa A.
    Valida con Etapa C antes de publicar; si hay alucinaciones, conmuta a síntesis determinista.
    """
    input_data = build_input_data_payload(rankings_data, local_apis_data)
    
    total_models = len(input_data["models"])
    intel_count = sum(1 for m in input_data["models"] if m.get("is_measured"))
    coding_count = sum(1 for m in input_data["models"] if m.get("coding_index") is not None)
    elo_count = sum(1 for m in input_data["models"] if m.get("elo_lmsys") is not None)
    latency_count = sum(1 for m in input_data["models"] if m.get("latency_ms") is not None)

    system_prompt = """Rol: sos el redactor del Observatorio FloydIA (AI Rankings & Local APIs Observatory).
Vas a recibir un bloque INPUT_DATA en JSON con datos YA VERIFICADOS de cada modelo, obtenidos por retrieval real (OpenRouter + Artificial Analysis + Benchmarks Oficiales + Sonda Local).
Tu única fuente de datos numéricos es ese JSON. Nunca completes, estimes ni "redondees a partir de lo que sabés" ningún precio, latencia, score o Elo que no venga explícito ahí.

Reglas no negociables:
1. Si un campo numérico llega como null, escribí exactamente "SIN DATO" en esa celda/mención. Nunca un número inventado ni un valor por defecto.
2. Nunca atribuyas un valor a una fuente salvo que ese valor venga acompañado de ese mismo *_source en el JSON. Si *_source es null, no menciones ninguna fuente para ese dato.
3. No incluyas en el informe ningún modelo que no esté en INPUT_DATA.models, aunque lo reconozcas de tu entrenamiento y sepas que existe.
4. Tu conocimiento general se usa solo para clasificar o describir en una frase qué distingue a un modelo (ej. "orientado a coding agentic") — nunca para calcular o estimar una cifra.
5. Separá los modelos usando profile_categories: los que matchean van a la tabla principal («Tu Arsenal» / «Radar Global»); el resto va a un apéndice al final («Fuera de tu perfil de uso») — no los ocultes, pero no los mezcles con tus modelos de trabajo real.
6. Si dos modelos distintos tienen exactamente el mismo valor numérico en un campo, no lo "suavices" ni lo cambies para que parezca más variado — repetilo tal cual viene.
7. Antes de cerrar el informe, incluí obligatoriamente la línea de cobertura de datos reales.

Estructura de salida (Markdown en Español, conservar el formato y tono ejecutivo de ingeniería):
1. 🏛️ Diagnóstico de tu Arsenal Local (solo modelos con is_local: true)
2. 🌐 Radar de Frontera Global (is_local: false)
3. 🧠 Síntesis Ejecutiva (texto libre, pero cada afirmación cuantitativa debe señalar a un campo real del JSON)
4. 📋 Tabla Comparativa Principal (solo modelos en profile_categories)
5. 📎 Fuera de tu perfil de uso (el resto)
6. 📊 Línea de Cobertura de Datos Medidos y Fuentes Usadas

Cierre Fijo Obligatorio:
> **FloydIA** — «Construimos la inteligencia. Desde la infraestructura.»
> «Desde la infraestructura, todo.»
"""

    user_prompt = f"""INPUT_DATA (Datos reales y verificados fuera del LLM):
{json.dumps(input_data, ensure_ascii=False, indent=2)}

Genera el informe técnico de hoy siguiendo estrictamente las 7 reglas anti-alucinación."""

    # 1. DeepSeek V3 (Directo, ultra fiable y económico)
    if DEEPSEEK_API_KEY:
        try:
            resp = requests.post(
                f"{DEEPSEEK_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 3000
                },
                timeout=15
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                violations = verify_report_stage_c(text, input_data)
                if not violations:
                    print("✨ [Analyst] Informe ejecutivo redactado con DeepSeek V3 y certificado por Etapa C (0 alucinaciones).")
                    return text
                else:
                    print(f"⚠️ [Analyst] Etapa C detectó {len(violations)} cifras no autorizadas: {violations[:5]}. Conmutando a fallback seguro...")
        except Exception as e:
            print(f"⚠️ [Analyst] DeepSeek no disponible: {e}")

    # 2. Google AI Studio (Gemini 2.5 Flash / 3.6 Flash)
    if GEMINI_API_KEY:
        for model_name in ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]:
            try:
                resp = requests.post(
                    f"{GOOGLE_OPENAI_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 3000
                    },
                    timeout=15
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    violations = verify_report_stage_c(text, input_data)
                    if not violations:
                        print(f"✨ [Gemini Analyst] Informe redactado con '{model_name}' y certificado por Etapa C.")
                        return text
                    else:
                        print(f"⚠️ [Gemini Analyst] Etapa C detectó {len(violations)} cifras no verificadas en {model_name}.")
            except Exception:
                continue

    # 3. Fallback Determinista 100% Cero Alucinación
    print("⚠️ [Analyst] Generando informe con motor determinista local certificado...")
    return _generate_deterministic_grounded_analysis(input_data, intel_count, coding_count, elo_count, latency_count, total_models)


def _generate_deterministic_grounded_analysis(
    input_data: Dict[str, Any],
    intel_count: int,
    coding_count: int,
    elo_count: int,
    latency_count: int,
    total_models: int
) -> str:
    """Generador determinista estricto sin dependencias de red ni LLM (FloydIA Protocol V11)."""
    models = input_data.get("models", [])
    local_models = [m for m in models if m.get("is_local")]
    external_models = [m for m in models if not m.get("is_local")]

    lines = [
        "### 🧠 Síntesis Ejecutiva del Observatorio FloydIA (Grounded v2 - Procedencia Estricta V11)",
        "",
        "#### 1. 🏛️ Diagnóstico de tu Arsenal Local (APIs Verificadas en tu PC)",
        f"- Cuentas con **{len(local_models)} modelos locales activos** verificados.",
    ]

    if local_models:
        best_local = local_models[0]
        lat_str = f"{best_local['latency_ms']} ms" if best_local.get('latency_ms') is not None else "— (Catálogo / Sin sonda directa)"
        score_str = f"{best_local['intelligence_index']}/100" if best_local.get('intelligence_index') is not None else "SIN DATO (Prior teórico)"
        lines.append(f"- **Modelo local líder**: `{best_local['display_name']}` (Inteligencia: {score_str}, Latencia local: {lat_str}).")
        free_locals = [m for m in local_models if m.get("pricing_in_per_1m") == 0.0 and m.get("pricing_out_per_1m") == 0.0]
        if free_locals:
            free_names = ", ".join([f"`{m['display_name']}`" for m in free_locals[:5]])
            lines.append(f"- **Opciones costo-cero locales**: {free_names}.")
    else:
        lines.append("- *Nota*: No se detectaron APIs con estado funcional en este sondeo.")

    ext_names = ", ".join([f"`{m['display_name']}`" for m in external_models[:5]])
    lines.extend([
        "",
        "#### 2. 🌐 Radar de Frontera Global (Modelos de Referencia Externa)",
        f"- **Modelos de Frontera Evaluados**: {ext_names}.",
        "",
        "#### 3. 📊 Cobertura Empírica Real de Mediciones",
        f"- **Índice de Inteligencia / Calidad Medido**: {intel_count}/{total_models} modelos con benchmarks empíricos reales.",
        f"- **Índice de Coding Medido**: {coding_count}/{total_models} modelos con evaluaciones de código comprobadas.",
        f"- **Preferencia Humana (Elo)**: {elo_count}/{total_models} modelos con votos en Arena registrados.",
        f"- **Latencia en Homelab Directa**: {latency_count}/{total_models} modelos sondeados localmente.",
        "",
        "> **FloydIA** — «Construimos la inteligencia. Desde la infraestructura.»  ",
        "> «Desde la infraestructura, todo.»"
    ])
    return "\n".join(lines)


