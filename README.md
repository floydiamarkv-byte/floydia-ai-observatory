# 🛰️ FloydIA AI Command & Observatory Suite (v8.0)

> **Firma**: FloydIA — *WEB & IA AUTOMATION*  
> **Slogan**: *«Construimos la inteligencia. Desde la infraestructura.»*  
> **Cierre**: *«Desde la infraestructura, todo.»*  
> **Ubicación Canónica**: `FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY/`

---

## 📖 Visión General

**FloydIA AI Command & Observatory Suite (v8.0)** es una plataforma integral en Python y PyQt6 diseñada para resolver la desconexión entre los rankings mundiales de LLMs, las APIs en vivo del clúster homelab y las herramientas de código que utilizas a diario (*OpenCode, Hermes Agent, DeepSeek Harness*).

### Capacidades Principales:
1. **🟢 Arsenal Local & Telemetría Homelab**: Escanea y audita activamente credenciales y endpoints (*Google AI Studio C1..C6, DeepSeek, Groq LPU, Mistral, NVIDIA NIM, OpenRouter Fleet y Hermes Gateway*), midiendo latencias sub-segundo reales y disponibilidad.
2. **⚪ Radar Global de Inteligencia (480+ Modelos)**: Agrega y normaliza datos de **LMSYS Chatbot Arena (Elo)**, **Hugging Face Leaderboard v2**, **OpenRouter Live API Pricing**, **Artificial Analysis** y **LiveBench**.
3. **⚙️ Inyector y Saneador de Motores**: Reescribe y sincroniza en un clic las configuraciones de:
   - **OpenCode Desktop & CLI** (`~/.config/opencode/opencode.jsonc`)
   - **Hermes Desktop & CLI** (`~/.hermes/config.yaml` + saneamiento y purga de caché)
   - **DeepSeek Harness** (`~/.dsh/settings.yaml`)
4. **📡 Sincronización Multi-Nodo Clúster**: Sincroniza configuraciones y catálogos hacia el nodo secundario HP45 (`tec@192.168.1.200`) vía Rsync.
5. **🤖 Asesor IA Grounded**: Consultor en lenguaje natural impulsado por DeepSeek V3 y Gemini 3.6/3.7 con failover automático y grounding estricto en la telemetría local.
6. **⚔️ Comparador Cara a Cara (VS)**: Duelo multidimensional de modelos (*Gemini 2.5 Pro vs Claude 3.7 Sonnet*, *DeepSeek R1 vs o3-mini*, etc.) con veredicto ejecutivo y generador de snippets (Python / cURL).
7. **🖥️ GUI Unificada PyQt6**: Panel de control nativo con checkmarks modulares, progreso visual y logs detallados con marcas de tiempo.

---

## 🚀 Inicio Rápido

### 1. Lanzador Gráfico PyQt6 (Recomendado)
```bash
python3 -m src.cli.main --gui
# O mediante el script directo:
./launch-floydia-suite.sh
```

### 2. Dashboard Web en Vivo (:8333)
```bash
python3 launch_observatory.py
# O abre directamente en tu navegador:
# http://localhost:8333
```

### 3. Menú Interactivo en Terminal (CLI)
```bash
python3 -m src.cli.main
```

---

## 🌐 Dashboard Web Interactivo
Al ejecutar con `--serve`, puedes abrir en tu navegador:
👉 **`http://localhost:8333`**

El dashboard incluye:
- **Botón "⚡ Probar APIs Locales"**: Ejecuta una sonda de salud en vivo de tus credenciales.
- **Botón "🔄 Actualizar Rankings"**: Sincroniza los últimos benchmarks.
- **Botón "📥 Descargar Informe (.md)"**: Descarga el informe ejecutivo generado por Gemini 2.5 Flash.
- **Botón "📋 Exportar Snapshot Frontier (.md)"**: Descarga el archivo estructurado para Claude/ChatGPT.
- **Filtros por Casillas de Selección**: Filtra por *Solo Activos en mi PC*, *Frontier*, *Caballos de Batalla* o *Especialistas en Código*.

---

## 📁 Estructura del Proyecto

```
FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY/
├── config/
│   ├── brand_tokens.json          # Tokens visuales FloydIA V6
│   ├── model_mappings.json        # Catálogo canónico y alias de modelos
│   └── settings.py                # Carga segura de variables (.secrets/antigravity.env)
├── src/
│   ├── collectors/                # Recolectores de datos públicos (LMSYS, OpenRouter, HF, AA, Epoch)
│   ├── probers/                   # Sondas en vivo de APIs locales (Google, DeepSeek, OpenRouter, Hermes)
│   ├── core/                      # SQLite DB, resolución de entidades y scoring multidimensional
│   ├── analyst/                   # Analista Gemini 2.5 Flash y exportador para IAs Frontier
│   ├── reports/                   # Generadores de Markdown y HTML con FloydIA Theme
│   ├── web/                       # Servidor web y dashboard interactivo
│   └── cli/                       # Interfaz de terminal
├── reports/
│   ├── daily/                     # Informes diarios en .md y .html
│   └── frontier_export/           # Snapshots diarios para Claude / ChatGPT
├── data/                          # Base de datos SQLite (rankings_engine.db)
└── tests/                         # Suite de tests unitarios
```

---

## 🛡️ Seguridad y Anti-Fuga de Credenciales
- La herramienta busca automáticamente tus claves en `/home/tec/.secrets/antigravity.env` o `.env` sin necesidad de exponerlas.
- **PROHIBIDO el hardcodeo**: Las credenciales jamás se escriben en los snapshots de base de datos, logs o archivos generados.
- Las comprobaciones activas realizan llamadas de metadata y un handshake de 1 token de respuesta para garantizar cero impacto en saldos o cuotas.

---
*Desarrollado para el ecosistema FloydIA.*  
*«Desde la infraestructura, todo.»*
