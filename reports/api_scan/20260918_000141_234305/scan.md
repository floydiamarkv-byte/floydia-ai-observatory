# Informe de Escaneo SRE — FloydIA API Scanner v2.0
- **Scan ID:** `20260918_000141_234305`
- **Fecha (UTC):** 2026-09-18 00:01:45 UTC
- **Modo:** PRODUCCIÓN (En Vivo)
- **Coste Total:** $0.00 USD
- **Cuentas Auditadas:** 39 (✅ 35 Operativas | ⚠️ 4 Errores)
- **Saldo Detectado:** $6.61 USD
- **Latencia Media:** 459.6 ms

## 1. Tabla de Cuentas y Modelos

| Proveedor | Cuenta / Modelo | Tier | Estado | HTTP | Total (ms) | TTFT (ms) | Saldo ($) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| openrouter | `C1_OPENROUTER` | T0 | ✅ OK | 200 | 665.11 | — | $0.20 |
| openrouter | `C2_OPENROUTER` | T0 | ✅ OK | 200 | 579.83 | — | $0.00 |
| openrouter | `C3_OPENROUTER` | T0 | ✅ OK | 200 | 396.18 | — | $0.00 |
| openrouter | `C4_OPENROUTER` | T0 | ✅ OK | 200 | 475.88 | — | $0.00 |
| openrouter | `C5_OPENROUTER` | T0 | ✅ OK | 200 | 432.62 | — | $0.00 |
| openrouter | `C6_OPENROUTER` | T0 | ✅ OK | 200 | 439.44 | — | $0.00 |
| openrouter | `C7_OPENROUTER` | T0 | ✅ OK | 200 | 1157.04 | — | $3.20 |
| openrouter | `OPENROUTER_API_KEY` | T0 | ✅ OK | 200 | 352.49 | — | $3.20 |
| nvidia | `C1_NVIDIA` | T0 | ✅ OK | 200 | 303.12 | — | — |
| nvidia | `C2_NVIDIA` | T0 | ✅ OK | 200 | 202.23 | — | — |
| nvidia | `C7_NVIDIA` | T0 | ✅ OK | 200 | 71.5 | — | — |
| nvidia | `C9_NVIDIA` | T0 | ✅ OK | 200 | 80.85 | — | — |
| google | `C1_GOOGLE_AISTUDIO` | T0 | ✅ OK | 200 | 306.34 | — | — |
| google | `C2_GOOGLE_AISTUDIO` | T0 | ✅ OK | 200 | 428.67 | — | — |
| google | `C3_GOOGLE_AISTUDIO` | T0 | ✅ OK | 200 | 264.34 | — | — |
| google | `C4_GOOGLE_AISTUDIO` | T0 | ✅ OK | 200 | 232.02 | — | — |
| google | `C5_GOOGLE_AISTUDIO` | T0 | ✅ OK | 200 | 125.06 | — | — |
| google | `C6_GOOGLE_AISTUDIO` | T0 | ✅ OK | 200 | 127.93 | — | — |
| mistral | `C1_MISTRAL` | T0 | ✅ OK | 200 | 435.54 | — | — |
| mistral | `C2_MISTRAL` | T0 | ✅ OK | 200 | 400.31 | — | — |
| mistral | `C3_MISTRAL` | T0 | ✅ OK | 200 | 401.02 | — | — |
| mistral | `C4_MISTRAL` | T0 | ✅ OK | 200 | 365.8 | — | — |
| mistral | `C5_MISTRAL` | T0 | ✅ OK | 200 | 371.97 | — | — |
| mistral | `C6_MISTRAL` | T0 | ✅ OK | 200 | 404.39 | — | — |
| deepseek | `DEEPSEEK_API_KEY` | T0 | ✅ OK | 200 | 555.9 | — | — |
| deepseek | `C1_DEEPSEEK` | T0 | ✅ OK | 200 | 489.95 | — | — |
| deepseek | `C2_DEEPSEEK` | T0 | ✅ OK | 200 | 385.15 | — | — |
| zen | `C1_ZEN_OPENCODE` | T0 | ✅ OK | 200 | 499.41 | — | — |
| zen | `C2_ZEN_OPENCODE` | T0 | ✅ OK | 200 | 513.08 | — | — |
| zen | `C7_ZEN_OPENCODE` | T0 | ✅ OK | 200 | 501.83 | — | — |
| zai | `C1_Z_AI` | T0 | ✅ OK | 200 | 677.3 | — | — |
| zai | `C2_Z_AI` | T0 | ✅ OK | 200 | 558.37 | — | — |
| zai | `C3_Z_AI` | T0 | ✅ OK | 200 | 317.88 | — | — |
| dashscope | `C7_DASHSCOPE_API_KEY` | T0 | ✅ OK | 200 | 1038.77 | — | — |
| dashscope | `C7_QWEN_API_KEY` | T0 | ✅ OK | 200 | 1530.08 | — | — |
| fireworks | `C7_FIREWORKS_API_KEY` | T0 | ⚠️ CACHED_NEGATIVE | 400 | 0.0 | — | — |
| fireworks | `C8_FIREWORKS_API` | T0 | ⚠️ CACHED_NEGATIVE | 400 | 0.0 | — | — |
| github | `S02_GITHUB_TOKEN_ANTIGRAVITY` | T0 | ⚠️ CACHED_NEGATIVE | 400 | 0.0 | — | — |
| github | `S02_GITHUB_PAT` | T0 | ⚠️ CACHED_NEGATIVE | 400 | 0.0 | — | — |