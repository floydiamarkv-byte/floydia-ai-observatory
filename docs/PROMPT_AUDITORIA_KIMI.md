# 🛰️ PROMPT MAESTRO PARA AUDITORÍA Y FIX EN KIMI (MOONSHOT AI)
> **Proyecto**: FloydIA AI Command & Observatory Suite (v9.0 / v10.0)  
> **Ubicación Canónica**: `FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY/`  
> **Archivo de Código Consolidado**: `FLOYDIA_SUITE_V9_CODEBASE_CONSOLIDATED.txt`  
> **Objetivo**: Auditoría técnica profunda, corrección de propagación de motores (bug "Solo DeepSeek") y recalibración de veracidad en métricas de benchmarking.

---

```markdown
# 🛠️ DIRECTIVA DE AUDITORÍA Y REFACTORIZACIÓN TÉCNICA — FLOYDIA OBSERVATORY SUITE

Eres un **Arquitecto de Software Senior especializado en Python, Infraestructura de IA y Data Pipelines de LLMs**. 
Se te entrega el código fuente consolidado y los resultados de ejecución de **FloydIA AI Command & Observatory Suite**, un sistema autónomo de telemetría de APIs de IA, agregación de benchmarks globales y sincronización de motores de inferencia.

---

## 🏛️ 1. CONTEXTO Y ARQUITECTURA DEL SISTEMA

El sistema opera en un entorno Linux (Debian/Arch/Proxmox) con sincronización de configs hacia nodos del homelab y herramientas de desarrollo locales (*OpenCode, Hermes Agent, DeepSeek Harness*).

### Módulos Principales:
1. **`src/collectors/` (8 Recolectores de Rankings Globales)**:
   - LMSYS Chatbot Arena (`arena_collector.py`)
   - SWE-bench Verified (`swebench_collector.py`)
   - Aider Polyglot Leaderboard (`aider_collector.py`)
   - Artificial Analysis Speed & Intelligence (`aa_collector.py`)
   - Hugging Face Open LLM Leaderboard (`hf_collector.py`)
   - LiveBench & Epoch AI (`livebench_collector.py`)
   - OpenRouter Live Catalog & Pricing (`openrouter_collector.py`)
2. **`src/probers/` (Telemetría y Sondas de APIs Locales)**:
   - Sondas activas con llamadas de 1 token para medir latencia real y operatividad: Google AI Studio (`C1..C6`), DeepSeek Direct, Groq LPU, Mistral AI, NVIDIA NIM, Z.AI (GLM), Alibaba DashScope (Qwen), OpenRouter Fleet, Hermes Gateway.
   - Pool de claves y gestión de Rate Limits (`key_pool.py`, `local_verifier.py`).
3. **`src/core/` (Base de Datos, Scoring y Motores)**:
   - Base de datos SQLite (`db.py` con `rankings_engine.db` en modo WAL).
   - Motor de Scoring Multidimensional (`scoring.py`, `ranking_engine_v3.py`, `normalizer.py`, `confidence.py`) con calibración Probit y Shrinkage bayesiano.
   - Inyector y saneador de configuraciones (`engine_injector.py` para OpenCode `.jsonc`, Hermes `config.yaml`, DSH `settings.yaml`).
4. **`src/analyst/` & `src/reports/` (Generación de Informes y Exportación)**:
   - Generación de informe diario Markdown y HTML (`2026-08-28_informe_ia_floydia.md/.html`).
   - Snapshot optimizado para IAs Frontier (`frontier_exporter.py` ➔ `SNAPSHOT_FOR_FRONTIER_AI.md`).
5. **`src/web/` & `src/gui/`**: Dashboard interactivo Flask/JS (`app.py`, `:8333`) y GUI nativa PyQt6 (`suite_window.py`).

---

## 🚨 2. SÍNTOMAS Y PROBLEMAS CRÍTICOS DETECTADOS

Tras la última ejecución de la Suite, se han identificado anomalías graves que requieren tu diagnóstico y corrección:

### ❌ Problema A: Bug "Solo Aparecen Motores DeepSeek"
- **Comportamiento Anómalo**: En las aplicaciones/herramientas clientes o selectores de motor (OpenCode, Hermes, DeepSeek Harness o el selector del dashboard), solo se listan o habilitan motores de **DeepSeek**, ignorando el resto de proveedores activos y verificados (Google Gemini, Alibaba Qwen, Mistral, Z.AI, Groq, NVIDIA NIM, OpenRouter).
- **Puntos a Investigar**:
  - Revisa `src/core/engine_injector.py`: ¿Cómo se construyen y serializan los archivos `~/.config/opencode/opencode.jsonc`, `~/.hermes/config.yaml` y `~/.dsh/settings.yaml`? ¿Hay claves mal formateadas, esquemas JSON/YAML incompatibles con los clientes o nombres de variables `.env` que no resuelven?
  - Revisa `src/web/app.py` y `src/gui/suite_window.py`: ¿Existe algún filtro hardcodeado o bug en el parseo del payload `/api/rankings` o `/api/models` que trunque la lista a solo DeepSeek?
  - Revisa la caché de Hermes (`provider_models_cache.json`) y DSH (`settings.yaml`): ¿Por qué DSH tiene la sección `llm-deepseek` aislada y cómo maneja `llm-pi-ai` / `google`?

### ❌ Problema B: Veracidad y Calibración de los Valores / Scores
- **Comportamiento Anómalo**: 
  - El informe diario genera puntajes sintéticos irreales (ej. `Anthropic Claude Opus 5 (Max)` con score `99.56/100`, `OpenAI GPT 5.5 (High)` con `99.42/100`, `Meta Muse Spark 1.2`), mezclando modelos hipotéticos o entradas de catálogo no verificadas con modelos reales.
  - Varios recolectores devuelven errores HTTP 404 o tablas rotas en vivo (ej. *Arena.ai Coding 404*, *Aider HTML parse failure*) y recurren a fallbacks estáticos descalibrados.
  - El archivo `2026-08-28_SNAPSHOT_FOR_FRONTIER_AI.md` sufrió un colapso: solo exportó **2 modelos** (Gemini 2.5 Flash y Claude 3.7 Sonnet) en lugar de la flota completa de más de 40 modelos locales activos.
- **Puntos a Investigar**:
  - Revisa `src/core/ranking_engine_v3.py` y `src/core/scoring.py`: ¿Cómo se calculan los scores de Inteligencia, Coding y Eficiencia? ¿Por qué se inflan los valores o por qué se mezclan modelos sintéticos del catálogo con los modelos realmente testeados?
  - Revisa `src/analyst/frontier_exporter.py`: ¿Por qué el filtrado `is_local_active` falló y dejó fuera a casi todos los modelos locales en el snapshot frontier?
  - Revisa `src/core/db.py` y `get_latest_local_verified_models()`: ¿El join de la base de datos SQLite está perdiendo registros o rechazando modelos por discrepancia en el `canonical_name` vs `model_id`?

---

## 🎯 3. TU MISIÓN DE AUDITORÍA Y FIX

Analiza el código y proporciona una respuesta estructurada en los siguientes apartados:

### Paso 1: Diagnóstico Causal Detallado
1. Explica con precisión quirúrgica **por qué solo aparecen motores DeepSeek** en los destinos configurados o en la interfaz. Identifica la línea y archivo exactos del fallo.
2. Explica **por qué los valores de score carecen de realismo**, de dónde provienen los modelos sintéticos/alucinados y por qué falló el cálculo/exportación en `frontier_exporter.py`.
3. Enumera los posibles fallos de sincronización entre `model_mappings.json`, los recolectores de scraping y las tablas SQLite.

### Paso 2: Plan de Corrección Arquitectónica
- Diseña una estrategia clara para:
  1. Separar inequívocamente los **Modelos Verificados en Vivo (Telemetría Real)** de los **Modelos Teóricos/Catálogo Global**.
  2. Asegurar que `engine_injector.py` configure correctamente el 100% de los proveedores soportados (*Google, Qwen, Mistral, NVIDIA NIM, Z.AI, OpenRouter, DeepSeek*) con la sintaxis exacta que OpenCode, Hermes y DSH esperan.
  3. Arreglar el pipeline de exportación `frontier_exporter.py` para que incluya todos los modelos locales con credenciales activas.

### Paso 3: Parches de Código Completos y Listos para Producción
Entrega los bloques de código modificados (sin omitir código con comentarios tipo `// ... rest of code`) para los archivos afectados:
- `src/core/engine_injector.py`
- `src/analyst/frontier_exporter.py`
- `src/core/scoring.py` / `src/core/ranking_engine_v3.py` (si aplica ajuste en la calibración/normalización)
- `src/core/db.py` (si aplica corrección en queries de resolución)

### Paso 4: Procedimiento de Verificación y Validación
- Proporciona comandos de terminal precisos para ejecutar la suite, regenerar la base de datos, validar las configuraciones inyectadas y verificar los archivos Markdown generados.
```
