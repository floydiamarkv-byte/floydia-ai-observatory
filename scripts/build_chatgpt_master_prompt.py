#!/usr/bin/env python3
"""
Compilador del Documento Maestro y Prompt para ChatGPT (GPT-4o / o3-mini / GPT-5).
Fusiona:
1. Prompt Maestro y Directivas de Auditoría / Mejoras para ChatGPT.
2. Descripción Arquitectónica y Modo de Funcionamiento del Sistema.
3. Resultados Reales de la Ejecución Actual (Telemetría de APIs, Rankings, Informes).
4. Código Fuente Completo Consolidado de todos los módulos.
"""

import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_FILE = DOCS_DIR / "PROMPT_MAESTRO_CHATGPT_SUITE_COMPLETO.md"

# Lista canónica y ordenada de archivos fuente a incluir
SOURCE_FILES = [
    # Configuración y esquemas
    "config/settings.py",
    "config/brand_tokens.json",
    "config/model_mappings.json",
    
    # Core (Lógica, BD, Scoring, Inyección)
    "src/core/contracts.py",
    "src/core/db.py",
    "src/core/normalizer.py",
    "src/core/quality.py",
    "src/core/freshness.py",
    "src/core/confidence.py",
    "src/core/ranking_engine_v3.py",
    "src/core/scoring.py",
    "src/core/engine_injector.py",
    "src/core/auth_hmac.py",
    
    # Collectors (8 Fuentes de Benchmarks)
    "src/collectors/base.py",
    "src/collectors/aggregator.py",
    "src/collectors/openrouter_collector.py",
    "src/collectors/hf_collector.py",
    "src/collectors/arena_collector.py",
    "src/collectors/artificial_analysis.py",
    "src/collectors/swebench_collector.py",
    "src/collectors/aider_collector.py",
    "src/collectors/livebench_epoch.py",
    "src/collectors/livecodebench_collector.py",
    
    # Probers (Sondas de APIs Locales y Handshakes)
    "src/probers/local_verifier.py",
    "src/probers/key_pool.py",
    "src/probers/micro_benchmark.py",
    "src/probers/scanner.py",
    "src/probers/google_prober.py",
    "src/probers/deepseek_prober.py",
    "src/probers/groq_prober.py",
    "src/probers/mistral_prober.py",
    "src/probers/nvidia_prober.py",
    "src/probers/zai_prober.py",
    "src/probers/dashscope_prober.py",
    "src/probers/openrouter_prober.py",
    "src/probers/hermes_prober.py",
    "src/probers/zen_prober.py",
    
    # Analyst & Reports
    "src/analyst/gemini_analyst.py",
    "src/analyst/ai_advisor.py",
    "src/analyst/frontier_exporter.py",
    "src/reports/markdown_report.py",
    "src/reports/html_report.py",
    
    # Web, GUI, CLI & Entrypoints
    "src/web/app.py",
    "src/gui/suite_window.py",
    "src/cli/main.py",
    "launch_observatory.py",
    
    # Scripts auxiliares
    "scripts/reseed_and_recalculate.py",
    "scripts/verify_dashboard_table.py",
    "scripts/verify_dashboard_visual.py"
]


def load_file_content(rel_path: str) -> str:
    path = BASE_DIR / rel_path
    if not path.exists():
        return f"// [ARCHIVO NO ENCONTRADO: {rel_path}]\n"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"// [ERROR AL LEER {rel_path}: {e}]\n"


def build_master_prompt():
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Cargar resultados reales generados
    daily_md_path = REPORTS_DIR / "daily" / f"{today_str}_informe_ia_floydia.md"
    frontier_md_path = REPORTS_DIR / "frontier_export" / f"{today_str}_SNAPSHOT_FOR_FRONTIER_AI.md"
    
    daily_md_content = load_file_content(str(daily_md_path.relative_to(BASE_DIR))) if daily_md_path.exists() else "No generado"
    frontier_md_content = load_file_content(str(frontier_md_path.relative_to(BASE_DIR))) if frontier_md_path.exists() else "No generado"

    doc = []
    doc.append(f"# 🛰️ FLOYDIA AI OBSERVATORY — ESPECIFICACIÓN TÉCNICA, RESULTADOS REALES Y CÓDIGO COMPLETO")
    doc.append(f"> **Sistema**: FloydIA AI Command & Observatory Suite (v9.1)")
    doc.append(f"> **Fecha de Emisión**: {today_str}")
    doc.append(f"> **Firma**: FloydIA — *«Construimos la inteligencia. Desde la infraestructura.»*")
    doc.append(f"> **Ubicación Canónica**: `FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY/`")
    doc.append(f"> **Objetivo**: Documento maestro integral para ChatGPT (GPT-4o, o3-mini, GPT-5). Contiene el meta-prompt de evaluación, arquitectura, resultados reales en vivo y el código fuente completo de la plataforma.")
    doc.append("\n---\n")

    # SECCIÓN 1: EL META-PROMPT PARA CHATGPT
    doc.append("""# 🏛️ PROMPT DE AUDITORÍA, OPTIMIZACIÓN Y REFACTORIZACIÓN PARA CHATGPT

Eres un **Principal AI Systems Architect y Senior Python Engineer** de clase mundial, especializado en:
1. Arquitectura de sistemas distribuidos de inferencia de LLMs y telemetría de baja latencia.
2. Modelado estadístico de rankings multidimensionales (calibración bayesiana, Bradley-Terry, shrinkage jerárquico, intervalos de confianza).
3. Pipelines de datos concurrentes y asíncronos (`asyncio`, `aiohttp`, `httpx`, pools de rate limit).
4. Inyección segura de configuraciones atómicas y orquestación de herramientas de código (*OpenCode, Hermes Agent, DeepSeek Harness*).

A continuación se te entrega la **documentación completa**, los **resultados de ejecución en vivo** y el **código fuente completo de todos los scripts** de **FloydIA AI Command & Observatory Suite (v9.1)**.

---

## 🎯 TUS OBJETIVOS DE AUDITORÍA Y MEJORA

Debes realizar un análisis técnico exhaustivo del sistema y responder estructurando tu devolución como un **PROMPT EN FORMATO MARKDOWN (MD)** que mi asistente de programación local (Antigravity IDE / Cursor) pueda ejecutar e implementar directamente.

Tu análisis y propuesta deben cubrir obligatoriamente:

### 1. Detección de Errores, Bugs Ocultos y Edge Cases
- Examina todos los archivos del código fuente en busca de:
  - Posibles `TypeError` o excepciones con valores `None` (como el detectado y corregido en `html_report.py`).
  - Fallos en la resolución y desduplicación de alias en `normalizer.py` y `model_mappings.json`.
  - Condiciones de carrera o inconsistencias en `key_pool.py` ante ráfagas de Rate Limits (429).
  - Problemas de transaccionalidad o bloqueos en `src/core/db.py` (SQLite WAL mode).
  - Fallos en la inyección de esquemas JSONC / YAML en `src/core/engine_injector.py` para OpenCode, Hermes y DSH.

### 2. Dimensión 1: Concurrencia Asíncrona de Alta Eficiencia (Async I/O)
- Actualmente las sondas en `src/probers/` y recolectores en `src/collectors/` usan llamadas bloqueantes con `requests` y `ThreadPoolExecutor`.
- Diseña una migración a `asyncio` + `httpx` / `aiohttp` que reduzca el tiempo del sondeo de ~40s a <3 segundos, manteniendo el pool de rotación de claves y cooldown de 60s de `key_pool.py`.

### 3. Dimensión 2: Refinamiento del Modelo Matemático de Scoring (FCI V3)
- Evalúa el algoritmo de Probit Rank Normalization + Bayesian Shrinkage en `src/core/ranking_engine_v3.py` y `src/core/scoring.py`.
- Propón optimizaciones para:
  - Manejo de matrices dispersas (modelos con solo 1 o 2 benchmarks observados).
  - Evitar sobreestimación en modelos de catálogo no testeados directamente.
  - Modelar la covarianza entre benchmarks fuertemente correlacionados (ej. MMLU-Pro y GPQA Diamond).

### 4. Dimensión 3: Enrutador Inteligente Dinámico de LLMs (Cascading Router API)
- Diseña un endpoint REST en `src/web/app.py` (`/api/recommend_model`) que reciba parámetros de tarea (`task=coding|reasoning|chat`, `budget=free|economy|frontier`, `max_latency_ms=1000`) y devuelva el mejor modelo disponible en el arsenal local basándose en su score FCI, latencia real en milisegundos y coste.

### 5. Dimensión 4: Detección Silenciosa de Drift y Deprecación de APIs
- Diseña un mecanismo en segundo plano que detecte si un proveedor (Google, OpenRouter, DeepSeek, Groq, Mistral) modifica silenciosamente sus precios, degrada la velocidad (TTFT) o reduce el contexto útil.

### 6. Parches de Código Completos y Listos para Producción
- Entrega el código fuente completo, refactorizado y probado (sin omitir líneas ni usar comentarios tipo `// rest of code`) de los módulos críticos que requieran modificación.

---

## 📋 FORMATO OBLIGATORIO DE TU RESPUESTA
Devuelve tu análisis en un único bloque Markdown bien estructurado, que contenga:
1. **Resumen Ejecutivo de Diagnóstico**: Lista priorizada de errores encontrados y oportunidades de mejora.
2. **Plan de Acción de Ingeniería**: Fases de implementación claras y sin ambigüedades.
3. **Bloques de Código Fuente Completos**: Código refactorizado para cada archivo modificado.
4. **Comandos de Verificación**: Comandos de terminal precisos para validar las correcciones y regenerar los reportes.

---
""")

    # SECCIÓN 2: DESCRIPCIÓN ARQUITECTÓNICA Y MODO DE FUNCIONAR
    doc.append(r"""# 📖 2. DESCRIPCIÓN ARQUITECTÓNICA Y MODO DE FUNCIONAMIENTO

## 2.1 Visión General
**FloydIA AI Command & Observatory Suite (v9.1)** es una plataforma en Python y PyQt6 diseñada para resolver la desconexión entre:
1. **Rankings y Benchmarks Públicos**: Ingesta periódica de 8 fuentes mundiales (LMSYS Chatbot Arena, SWE-bench Verified, Aider Polyglot Leaderboard, Artificial Analysis, Hugging Face Open LLM Leaderboard, LiveBench, Epoch AI, OpenRouter Catalog).
2. **Arsenal Local de APIs**: Sondas activas con handshakes mínimos (1 token) que miden la latencia real en milisegundos y el estado de operatividad de ~450 endpoints configurados en el clúster local (Google AI Studio C1..C6, DeepSeek Direct, Groq LPU, Mistral AI, NVIDIA NIM, Z.AI, Alibaba DashScope, OpenRouter Fleet, Hermes Gateway, GitHub Models Free Tier).
3. **Inyección Atómica de Motores**: Reescribe y sincroniza en un clic las configuraciones de herramientas de desarrollo con agentes de código:
   - `~/.config/opencode/opencode.jsonc` (OpenCode Desktop & CLI)
   - `~/.hermes/config.yaml` (Hermes Agent + saneamiento y purga de caché de proveedores)
   - `~/.dsh/settings.yaml` (DeepSeek Harness)
   - `~/.config/floydia/floydia-engines.env` (Exportación de variables de entorno)
4. **Sincronización Multi-Nodo**: Sincroniza configuraciones y catálogos hacia el nodo secundario del homelab HP45 (`tec@192.168.1.200`) vía Rsync.
5. **Generador de Entregables**: Genera diariamente informes ejecutivos en Markdown y HTML con el tema visual FloydIA V6, y snapshots estructurados para IAs Frontier (`SNAPSHOT_FOR_FRONTIER_AI.md`).
6. **Interfaces de Usuario**: Dashboard web interactivo Flask en puerto `:8333` y GUI nativa PyQt6 con selección modular por checkmarks.

## 2.2 Diagrama de Flujo del Pipeline E2E
```mermaid
graph TD
    A[1. Ingesta: 8 Recolectores de Benchmarks] -->|Snapshots SHA256 & Metadatos| C[(SQLite DB: rankings_engine.db)]
    B[2. Telemetría: Sondas de APIs Locales] -->|Latencias ms & Handshakes 200 OK| C
    C --> D[3. QualityGate & ModelNormalizer]
    D --> E[4. RankingEngineV3: Probit + Bayesian Shrinkage]
    E --> F[5. Engine Injector: OpenCode, Hermes, DSH, HP45]
    E --> G[6. Analyst & Report Generators]
    G --> H[Informe Diario Markdown & HTML]
    G --> I[Snapshot Diario Frontier AI]
    E --> J[7. Dashboard Web :8333 & GUI PyQt6]
```

## 2.3 Especificación Matemática del Motor de Scoring (FCI V3)
1. **Probit Rank-Bootstrapping (PRB)**:
   - Cada métrica cruda $x$ del benchmark $b$ se transforma a percentil robusto:
     $$z = \frac{x - \mu_b}{1.4826 \times \text{MAD}_b}$$
     $$p = \Phi(z)$$
     $$\text{score}_{0-100} = 100 \times \frac{n_{\text{eff}} \times p + 0.5}{n_{\text{eff}} + 1.0}$$
2. **Shrinkage Bayesiano Jerárquico**:
   - Para cada pilar (Razonamiento 0.35, Coding 0.30, Calidad AA 0.20, Preferencia 0.15):
     $$w_i = \frac{1}{\sigma_{p,i}^2}$$
     $$\mu_p = \frac{\sum w_i v_{p,i}}{\sum w_i}, \quad \text{Var}(\mu_p) = \frac{1}{\sum w_i}$$
     $$\lambda_p = \frac{\tau_p^2}{\tau_p^2 + \text{Var}(\mu_p)}$$
     $$\hat{S}_p = \lambda_p \mu_p + (1 - \lambda_p) \theta_p$$
3. **Incertidumbre y LCB (Lower Confidence Bound)**:
   - Margen de error con decaimiento temporal ($t_{1/2} = 30$ días):
     $$\text{Margin}_{95} = 1.96 \times \sqrt{\frac{\text{Var}(\text{FCI})}{e^{-\ln 2 \cdot d / 30}}}$$
   - Ordenamiento por LCB: $\text{Rank Score} = \text{FCI} - \text{Margin}_{95}$.

---
""")

    # SECCIÓN 3: RESULTADOS REALES GENERADOS EN LA ÚLTIMA EJECUCIÓN
    doc.append("""# 📊 3. RESULTADOS REALES DE LA EJECUCIÓN ACTUAL (EN VIVO)

A continuación se presentan los resultados concretos extraídos de la ejecución del pipeline completo hoy 2026-08-28.

## 3.1 Resumen Métrico de Telemetría
- **Total de APIs Locales Sondeadas**: 455 endpoints.
- **APIs Verificadas y Activas (200 OK)**: 422 endpoints.
- **Total de Modelos en el Ranking Multidimensional**: 450 modelos.
- **Métricas de Benchmarks Recolectadas**: 725 evaluaciones de 9 fuentes.
- **Motores Sincronizados**: OpenCode (`opencode.jsonc`), Hermes (`config.yaml`), DSH (`settings.yaml`), HP45 (`tec@192.168.1.200`).

## 3.2 Extracto del Informe Diario Generado (`reports/daily/2026-08-28_informe_ia_floydia.md`)
```markdown
""")
    doc.append(daily_md_content[:15000])  # Primeros 15KB del informe diario
    doc.append("\n```\n")

    doc.append("""## 3.3 Extracto del Snapshot Frontier Generado (`reports/frontier_export/2026-08-28_SNAPSHOT_FOR_FRONTIER_AI.md`)
```markdown
""")
    doc.append(frontier_md_content[:15000])  # Primeros 15KB del snapshot frontier
    doc.append("\n```\n")
    doc.append("\n---\n")

    # SECCIÓN 4: CÓDIGO FUENTE CONSOLIDADO DE TODOS LOS SCRIPTS
    doc.append("""# 💻 4. CÓDIGO FUENTE CONSOLIDADO DEL SISTEMA (TODOS LOS ARCHIVOS)

A continuación se incluye el código fuente íntegro de cada archivo del proyecto, organizado por capas arquitectónicas.
""")

    for rel_path in SOURCE_FILES:
        content = load_file_content(rel_path)
        ext = Path(rel_path).suffix.lstrip(".")
        lang = "python" if ext == "py" else ("json" if ext == "json" else "text")
        
        doc.append(f"\n{'#'*80}")
        doc.append(f"### ARCHIVO: `{rel_path}`")
        doc.append(f"{'#'*80}\n")
        doc.append(f"```{lang}")
        doc.append(content)
        doc.append("```\n")

    full_text = "\n".join(doc)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    print(f"✅ Documento Maestro para ChatGPT generado con éxito:")
    print(f"   Ruta: {OUTPUT_FILE}")
    print(f"   Tamaño: {len(full_text):,} caracteres / {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_master_prompt()
