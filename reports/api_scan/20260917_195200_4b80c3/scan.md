# 📡 FloydIA API Intelligence Scanner — Reporte `20260917_195200_4b80c3`
- **Fecha**: 2026-09-17 19:52:22
- **Total Sondas**: 45
- **Modo**: En Vivo

## 📊 Resumen por Proveedor y Cuenta (T0 Pasivo)
| Proveedor | Cuenta | Status | HTTP | Latencia | Saldo USD | Detalle |
|---|---|:---:|:---:|:---:|:---:|---|
| `openrouter` | `C1_OPENROUTER` | **OK** | 200 | 609.95ms | $0.20 | OK |
| `openrouter` | `C2_OPENROUTER` | **OK** | 200 | 686.57ms | $0.00 | OK |
| `openrouter` | `C3_OPENROUTER` | **OK** | 200 | 517.43ms | $0.00 | OK |
| `openrouter` | `C4_OPENROUTER` | **OK** | 200 | 778.13ms | $0.00 | OK |
| `openrouter` | `C5_OPENROUTER` | **OK** | 200 | 473.93ms | $0.00 | OK |
| `openrouter` | `C6_OPENROUTER` | **OK** | 200 | 458.34ms | $0.00 | OK |
| `openrouter` | `C7_OPENROUTER` | **OK** | 200 | 448.48ms | $3.20 | OK |
| `openrouter` | `OPENROUTER_API_KEY` | **OK** | 200 | 436.67ms | $3.20 | OK |
| `nvidia` | `C1_NVIDIA` | **OK** | 200 | 306.18ms | — | OK |
| `nvidia` | `C2_NVIDIA` | **OK** | 200 | 216.29ms | — | OK |
| `nvidia` | `C7_NVIDIA` | **OK** | 200 | 217.73ms | — | OK |
| `nvidia` | `C9_NVIDIA` | **OK** | 200 | 86.77ms | — | OK |
| `google` | `C1_GOOGLE_AISTUDIO` | **OK** | 200 | 307.77ms | — | OK |
| `google` | `C2_GOOGLE_AISTUDIO` | **OK** | 200 | 282.85ms | — | OK |
| `google` | `C3_GOOGLE_AISTUDIO` | **OK** | 200 | 379.77ms | — | OK |
| `google` | `C4_GOOGLE_AISTUDIO` | **OK** | 200 | 259.93ms | — | OK |
| `google` | `C5_GOOGLE_AISTUDIO` | **OK** | 200 | 252.11ms | — | OK |
| `google` | `C6_GOOGLE_AISTUDIO` | **OK** | 200 | 107.4ms | — | OK |
| `groq` | `C1_GROQ` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | FORBIDDEN: HTTP 403 |
| `groq` | `C2_GROQ` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | FORBIDDEN: HTTP 403 |
| `groq` | `C3_GROQ` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | FORBIDDEN: HTTP 403 |
| `groq` | `C4_GROQ` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | FORBIDDEN: HTTP 403 |
| `groq` | `C5_GROQ` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | FORBIDDEN: HTTP 403 |
| `groq` | `C6_GROQ` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | FORBIDDEN: HTTP 403 |
| `mistral` | `C1_MISTRAL` | **OK** | 200 | 426.06ms | — | OK |
| `mistral` | `C2_MISTRAL` | **OK** | 200 | 444.33ms | — | OK |
| `mistral` | `C3_MISTRAL` | **OK** | 200 | 401.86ms | — | OK |
| `mistral` | `C4_MISTRAL` | **OK** | 200 | 498.55ms | — | OK |
| `mistral` | `C5_MISTRAL` | **OK** | 200 | 374.36ms | — | OK |
| `mistral` | `C6_MISTRAL` | **OK** | 200 | 371.69ms | — | OK |
| `deepseek` | `DEEPSEEK_API_KEY` | **OK** | 200 | 565.63ms | — | OK |
| `deepseek` | `C1_DEEPSEEK` | **OK** | 200 | 549.61ms | — | OK |
| `deepseek` | `C2_DEEPSEEK` | **OK** | 200 | 390.02ms | — | OK |
| `zen` | `C1_ZEN_OPENCODE` | **OK** | 200 | 1166.95ms | — | OK |
| `zen` | `C2_ZEN_OPENCODE` | **OK** | 200 | 528.28ms | — | OK |
| `zen` | `C7_ZEN_OPENCODE` | **OK** | 200 | 370.46ms | — | OK |
| `zai` | `C1_Z_AI` | **OK** | 200 | 651.89ms | — | OK |
| `zai` | `C2_Z_AI` | **OK** | 200 | 529.94ms | — | OK |
| `zai` | `C3_Z_AI` | **OK** | 200 | 321.87ms | — | OK |
| `dashscope` | `C7_DASHSCOPE_API_KEY` | **OK** | 200 | 1198.26ms | — | OK |
| `dashscope` | `C7_QWEN_API_KEY` | **OK** | 200 | 1012.22ms | — | OK |
| `fireworks` | `C7_FIREWORKS_API_KEY` | **HTTP_412** | 412 | 546.92ms | — | HTTP 412 |
| `fireworks` | `C8_FIREWORKS_API` | **HTTP_412** | 412 | 406.67ms | — | HTTP 412 |
| `github` | `S02_GITHUB_TOKEN_ANTIGRAVITY` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | PROVIDER_DOWN: Cannot connect to host models.inference.ai.azure.com:443 ssl:default [Name or service not known] |
| `github` | `S02_GITHUB_PAT` | **CACHED_NEGATIVE** | 400 | 0.0ms | — | PROVIDER_DOWN: Cannot connect to host models.inference.ai.azure.com:443 ssl:default [Name or service not known] |

---

### 🧠 Dictamen Ejecutivo SRE (AI Radar — Modo Heurístico Local)

1. **Estado de Salud de la Flota**: 35 de 45 cuentas operativas. Latencia media P50: 475.1ms, P95: 1167.0ms.

2. **Análisis de Anomalías**:
   • `groq` (C1_GROQ): HTTP 400 — FORBIDDEN: HTTP 403
   • `groq` (C2_GROQ): HTTP 400 — FORBIDDEN: HTTP 403
   • `groq` (C3_GROQ): HTTP 400 — FORBIDDEN: HTTP 403
   • `groq` (C4_GROQ): HTTP 400 — FORBIDDEN: HTTP 403
   • `groq` (C5_GROQ): HTTP 400 — FORBIDDEN: HTTP 403
   • `groq` (C6_GROQ): HTTP 400 — FORBIDDEN: HTTP 403

3. **Recomendación de Presets y Ruteo**:
   • **Preset A (Resiliencia $0.00)**: Recomendado activo debido a latencias pasivas estables.
   • **OpenRouter C7**: Saldo detectado y disponible para ruteo de emergencia.

4. **Acciones SRE Prioritarias**:
   • Purgar claves con HTTP 403 de la negative cache tras rotación de credenciales.
   • Inferencia remota en NVIDIA NIM temporalmente saturada (The read operation timed out). Diagnóstico SRE generado por fallback local.

*(Generado por el motor SRE determinista local de FloydIA)*

