# Prompt para Antigravity (Gemini 3.7 con visión) — Fix template dashboard FloydIA

Copia y pega este prompt completo en Antigravity. El contexto es el bug preexistente de `src/web/app.py` que ya dejamos documentado: el dashboard renderiza el shell HTML y embebe los datos, pero las líneas con template literals JS (`${...}`) dentro de f-strings de Python 3.14 fallan al renderizar el HTML servido.

---

## PROMPT (copiar desde aquí)

Eres un agente Antigravity con visión Gemini 3.7. Necesito que arregles un bug preexistente de template HTML/JS en el dashboard de FloydIA AI Observatory.

**Contexto del bug:**

El fichero `src/web/app.py` (2282 líneas) en el proyecto `/home/tec/Dropbox/ANTIGRAVITY_PROJECTS/FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY` contiene un método `_render_dashboard()` (línea 1677+) que construye el HTML del dashboard como una f-string de Python enorme. Dentro de esa f-string hay bloques `<script>` con JavaScript que usa **template literals** (`` `texto ${variable} más texto` ``) y **arrow functions** con backticks.

El problema: Python 3.14 (instalado en este sistema) interpreta `${c}`, `${m.foo}`, etc. como **referencias a variables Python dentro de la f-string**. Esto causa:

- `NameError: name 'c' is not defined` en líneas donde la variable no existe en el scope Python (ej. `c` en un `.map(c => \`...\${c}...\`)`, línea 1677).
- Outputs rotos en líneas donde la variable Python SÍ existe (líneas 1817+, `m.foo` se imprime como `m.foo` Python en vez del atributo del modelo).

El dashboard actualmente **NO renderiza** (GET / devuelve 500, `{"error": "internal_error"}`), aunque el endpoint `/api/rankings` funciona perfectamente con 510 modelos y 1090269 bytes.

**Tu tarea concreta:**

1. **Inspecciona visualmente** el screenshot del dashboard roto que ya capturé:
   - Ruta: `/tmp/floydia_qa/dashboard_top_v3.png`
   - SHA256: `e3e4aadef68edd0c611262553f8f1c86c60644b5f485182947a0a8c8e498c72e`
   - Dimensiones: 1920×1200
   - Tamaño: 339128 bytes
   - Captúralo visualmente con tu herramienta de visión. Describe qué ves y qué falta.

2. **Diagnostica las líneas problemáticas**. Usa `grep -nE '\$\{|`[^`]*`' src/web/app.py` para listar las ~45 ocurrencias de template literals JS dentro de f-strings. Las líneas más críticas verificadas son:
   - Línea 1677: `const capsHtml = (m.capabilities || [m.tier || 'workhorse']).slice(0, 2).map(c => \`<span class="tier-badge tier-\${c.toLowerCase().replace(' ', '_').replace('+', '')}">\${c}</span>\`).join(" ");`
   - Línea 1715: idéntica pero con `.slice(0, 3)`
   - Líneas 1817, 1824, 1831-1834, 1840, 1864: template literals en `openModal()` y otros handlers

3. **Estrategia de fix recomendada (elige una, justifícala):**

   **Opción A — Extracción del JS a archivo estático `.js`** (RECOMENDADA):
   - Mueve todo el bloque `<script>...</script>` que está en la f-string a un archivo estático `src/web/static/dashboard.js`.
   - El HTML servido queda con `<script src="/static/dashboard.js"></script>`.
   - Los datos ya se sirven vía `const allModels = [...]` — puedes dejarlos como `<script>const allModels = {{JSON}};</script>` corto en el HTML, o exponer un endpoint `/api/rankings` y hacer `fetch` desde el JS.
   - **Ventaja**: elimina 100% del problema de f-string vs template literal, es mantenible, no requiere tocar las ~45 líneas.
   - **Riesgo bajo**.

   **Opción B — Escape con backslash-dollar (`\$`)**:
   - En cada `\${...}` añadir `\$` para que Python lo trate como literal.
   - Verificación: `f'...\${x}...'` produce literal `${x}` en Python 3.14 (probado).
   - **Riesgo alto**: hay 45 lugares y algunos están en scope Python donde `m` SÍ existe, así que el output actual es semánticamente incorrecto aunque no falle. Tendrías que distinguir caso por caso.

   **Opción C — String concatenation en JS en vez de template literals**:
   - Reescribir las ~45 líneas con `'<span class="tier-badge tier-' + c.toLowerCase().replace(' ', '_').replace('+', '') + '">' + c + '</span>'`.
   - **Riesgo medio**: tedioso pero funciona.

   **Opción D — Doble escape `\${{...}}` estilo Python 3.11**:
   - En Python 3.11, `\${{x}}` produce literal `${x}`. En Python 3.14 también, pero hay casos sutiles donde la doble-llave post-`\$` se reinterpreta.
   - Ya intentamos esto y falló con `NameError: c`. No recomendado.

   **Recomendación: Opción A** (extracción a `.js` estático). Es la solución arquitectónicamente correcta.

4. **Si eliges Opción A** (o equivalente), implementa:

   ```python
   # En app.py, en _render_dashboard(), reemplaza el bloque <script>...</script>
   # gigante por:
   <script src="/static/dashboard.js"></script>
   <script>
     const allModels = {{JSON_ENCODE(rankings)}};
   </script>
   ```

   Y crea `src/web/static/dashboard.js` con todo el JS extraído verbatim (sin las dobles llaves `{{` que eran para escapar la f-string de Python).

5. **Verificación post-fix** (obligatoria):

   ```bash
   pkill -f "src.cli.main.*--serve"
   cd /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY
   nohup python3 -m src.cli.main --serve --port 8333 > /tmp/floydia_observatory.log 2>&1 < /dev/null &
   disown
   sleep 6
   curl -sS -o /tmp/dashboard_fixed.html -w "GET / -> HTTP %{http_code} size=%{size_download}\n" http://localhost:8333/
   ```

   El `GET /` debe devolver **HTTP 200** y un HTML que contenga:
   - `<title>FloydIA — AI Rankings</title>` (preservado)
   - `const allModels = [...]` con 510 modelos
   - `script src="/static/dashboard.js"` o equivalente
   - **Sin** `{"error": "internal_error"}`

6. **Certificación visual con hash anclado** (Regla 33 del workspace):

   ```bash
   google-chrome-stable --headless --no-sandbox --disable-gpu --hide-scrollbars \
     --window-size=1920,1200 \
     --screenshot=/tmp/floydia_qa/dashboard_fixed.png \
     --virtual-time-budget=10000 \
     http://localhost:8333/

   sha256sum /tmp/floydia_qa/dashboard_fixed.png
   ```

   **ABRE el screenshot con tu herramienta de visión y describe lo que ves**. La regla 33 es estricta: NO certificar sin inspección visual. Lo que esperas ver:
   - Header con el logo y título "FloydIA AI Rankings"
   - Una tabla o grid con los modelos rankeados, **empezando por `gemini-2.5-pro`** en la posición #1 con FCI ≈ 91.3
   - Badges o columnas con confidence, family, variant
   - Sin errores en consola, sin pantalla en blanco, sin "internal_error"

   Reporta:
   - Ruta del PNG: `/tmp/floydia_qa/dashboard_fixed.png`
   - SHA256 del PNG
   - Tamaño en bytes y dimensiones
   - **Descripción visual de lo que ves** (esta es la certificación)

7. **Si todo va bien, commit:**

   ```bash
   cd /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/FLOYDIA/SUBTOOLS/AI_RANKINGS_OBSERVATORY
   git add src/web/app.py src/web/static/dashboard.js docs/SPEC_FCI_V3.md src/core/ranking_engine_v3.py src/core/scoring.py
   git commit -m "fix: extract dashboard JS to static file to fix f-string template literal bug

   - The f-string in _render_dashboard() could not coexist with JS template
     literals (\\\${...}) in Python 3.14. Extracted the script block to
     src/web/static/dashboard.js.
   - GET / now returns HTTP 200 with rendered HTML and embedded allModels
     containing 510 models with the V3 ranking shape.
   - See docs/SPEC_FCI_V3.md and src/core/ranking_engine_v3.py for the
     underlying mathematical engine (probit normalization + bayesian
     shrinkage, ranking by Lower Confidence Bound)."
   ```

**Estado actual verificable antes de tu trabajo:**

- Motor V3 funcionando: `python3 -c "from src.core.scoring import calculate_multidimensional_rankings; r = calculate_multidimensional_rankings(); print(len(r), r[0]['id'], r[0]['fci_score'])"`
  → debe imprimir: `510 gemini-2.5-pro 91.3`
- API: `curl -s http://localhost:8333/api/rankings | head -c 200` → JSON con `"id": "gemini-2.5-pro"`.
- Dashboard: `curl -s -o /dev/null -w '%{http_code}' http://localhost:8333/` → `500` (ahora) o `200` (después de tu fix).
- Documentación: `docs/SPEC_FCI_V3.md` contiene la matemática del motor.

**Lo que NO debes tocar:**
- `src/core/ranking_engine_v3.py` (funciona, no modificar).
- `src/core/scoring.py` (fachada V3, no modificar).
- `docs/SPEC_FCI_V3.md` (documentación, no modificar).

Solo el template HTML/JS del dashboard. Adelante.

---

## Notas finales para el usuario

- He guardado este prompt en `docs/PROMPT_FIX_TEMPLATE_DASHBOARD.md` para que lo puedas copiar/pegar en Antigravity.
- Mi modelo (minimax-m3) no acepta input de imagen, por eso no puedo certificar visualmente el dashboard actual. Gemini 3.7 sí puede, y con visión puede verificar el screenshot y la captura post-fix.
- El bug es preexistente, no introducido por el refactor V3. La matemática V3 está enchufada y operativa vía `/api/rankings` y embebida en el HTML del dashboard. Solo falta que el JS del cliente renderice la tabla — eso es lo que arregla este prompt.
