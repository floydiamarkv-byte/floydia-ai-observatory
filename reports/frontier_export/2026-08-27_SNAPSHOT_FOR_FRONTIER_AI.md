# 🌐 FLOYDIA AI BENCHMARKS & LOCAL APIS — SNAPSHOT DIARIO
> **Fecha de Extracción**: 2026-08-27  
> **Sistema Emisor**: FloydIA AI Rankings & Local API Observatory v6.0  
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

## 🟢 1. ARSENAL LOCAL: MODELOS ACTIVOS EN MI COMPUTADORA
*(Estos son los modelos que tengo configurados con API Keys funcionales y probadas hoy en mi equipo)*

| Modelo | Proveedor | Tier | Ventana Contexto | Latencia (ms) | Modo Precio | Coste In/Out ($/1M) | Score Global |
|---|---|---|---|---|---|---|---|
| **qwen/qwen3.8-max** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **96.5 / 100** |
| **anthropic/claude-opus-5-fast** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $5.000 / $25.000 | $5.0 / $25.0 | **96.5 / 100** |
| **anthropic/claude-opus-5:batch** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $2.500 / $12.500 | $2.5 / $12.5 | **96.5 / 100** |
| **openai/gpt-5.6-luna:batch** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $0.100 / $0.600 | $0.1 / $0.6 | **96.5 / 100** |
| **openai/gpt-5.6-terra-pro** | OpenRouter | `frontier` | 1,050,000 tok | 507.4 ms | $2.000 / $12.000 | $2.0 / $12.0 | **96.5 / 100** |
| **openai/gpt-5.6-terra:batch** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $1.000 / $6.000 | $1.0 / $6.0 | **96.5 / 100** |
| **openai/gpt-5.6-sol-pro** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $2.000 / $10.000 | $2.0 / $10.0 | **96.5 / 100** |
| **openai/gpt-5.6-sol:batch** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $1.000 / $5.000 | $1.0 / $5.0 | **96.5 / 100** |
| **anthropic/claude-opus-4.8:batch** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $2.500 / $12.500 | $2.5 / $12.5 | **96.5 / 100** |
| **qwen/qwen3.7-max** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $1.475 / $4.425 | $1.475 / $4.425 | **96.5 / 100** |
| **anthropic/claude-opus-4.7-fast** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $5.000 / $25.000 | $5.0 / $25.0 | **96.5 / 100** |
| **~google/gemini-pro-latest** | OpenRouter | `frontier` | 1,048,576 tok | 477.8 ms | $2.000 / $12.000 | $2.0 / $12.0 | **96.5 / 100** |
| **openai/gpt-5.5-pro** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $5.000 / $30.000 | $5.0 / $30.0 | **96.5 / 100** |
| **openai/gpt-5.5:batch** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $2.500 / $15.000 | $2.5 / $15.0 | **96.5 / 100** |
| **xiaomi/mimo-v2.5-pro** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $0.140 / $0.280 | $0.14 / $0.28 | **96.5 / 100** |
| **~anthropic/claude-opus-latest** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $5.000 / $25.000 | $5.0 / $25.0 | **96.5 / 100** |
| **anthropic/claude-opus-4.7:batch** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $2.500 / $12.500 | $2.5 / $12.5 | **96.5 / 100** |
| **google/lyria-3-pro-preview** | OpenRouter | `frontier` | 1,048,576 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **96.5 / 100** |
| **openai/gpt-5.4-pro** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $15.000 / $90.000 | $15.0 / $90.0 | **96.5 / 100** |
| **openai/gpt-5.4:batch** | OpenRouter | `frontier` | 1,050,000 tok | 477.8 ms | $1.250 / $7.500 | $1.25 / $7.5 | **96.5 / 100** |
| **google/gemini-3.1-pro-preview:batch** | OpenRouter | `frontier` | 1,048,576 tok | 477.8 ms | $1.000 / $6.000 | $1.0 / $6.0 | **96.5 / 100** |
| **anthropic/claude-opus-4.6** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $2.500 / $12.500 | $2.5 / $12.5 | **96.5 / 100** |
| **minimax/minimax-m1** | OpenRouter | `frontier` | 1,000,000 tok | 477.8 ms | $0.550 / $2.200 | $0.55 / $2.2 | **96.5 / 100** |
| **minimax/minimax-01** | OpenRouter | `frontier` | 1,000,192 tok | 477.8 ms | $0.200 / $1.100 | $0.2 / $1.1 | **96.5 / 100** |
| **Google Gemini 3.7 Flash (Reasoning)** | Google | `frontier` | 1,048,576 tok | 477.8 ms | $0.188 / $0.938 | $0.1875 / $0.9375 | **96.5 / 100** |
| **DeepSeek V4 Flash** | DeepSeek | `frontier` | 1,048,576 tok | 685.5 ms | $0.089 / $0.177 | $0.0886 / $0.1772 | **96.5 / 100** |
| **upstage/solar-pro4** | OpenRouter | `frontier` | 524,288 tok | 477.8 ms | $0.030 / $0.120 | $0.03 / $0.12 | **94.1 / 100** |
| **openai/gpt-5.6-luna-pro** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $1.250 / $10.000 | $1.25 / $10.0 | **93.5 / 100** |
| **openai/gpt-5.4-nano** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $0.100 / $0.625 | $0.1 / $0.625 | **93.5 / 100** |
| **openai/gpt-5.4-mini** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $0.375 / $2.250 | $0.375 / $2.25 | **93.5 / 100** |
| **openai/gpt-5.2-pro** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $10.500 / $84.000 | $10.5 / $84.0 | **93.5 / 100** |
| **openai/gpt-5.2:batch** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $0.875 / $7.000 | $0.875 / $7.0 | **93.5 / 100** |
| **openai/gpt-5.1:batch** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $0.625 / $5.000 | $0.625 / $5.0 | **93.5 / 100** |
| **openai/gpt-5-pro** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $7.500 / $60.000 | $7.5 / $60.0 | **93.5 / 100** |
| **openai/gpt-5:batch** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $0.625 / $5.000 | $0.625 / $5.0 | **93.5 / 100** |
| **openai/gpt-5-mini** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $0.125 / $1.000 | $0.125 / $1.0 | **93.5 / 100** |
| **openai/gpt-5-nano** | OpenRouter | `frontier` | 400,000 tok | 477.8 ms | $0.025 / $0.200 | $0.025 / $0.2 | **93.5 / 100** |
| **amazon/nova-pro-v1** | OpenRouter | `frontier` | 300,000 tok | 477.8 ms | $0.800 / $3.200 | $0.8 / $3.2 | **93.0 / 100** |
| **nex-agi/nex-n2-pro** | OpenRouter | `frontier` | 262,144 tok | 477.8 ms | $0.250 / $1.000 | $0.25 / $1.0 | **92.8 / 100** |
| **qwen/qwen3.6-max-preview** | OpenRouter | `frontier` | 262,144 tok | 477.8 ms | $1.027 / $6.162 | $1.027 / $6.162 | **92.8 / 100** |
| **anthropic/claude-opus-4.8-fast** | OpenRouter | `frontier` | 200,000 tok | 477.8 ms | $15.000 / $75.000 | $15.0 / $75.0 | **92.5 / 100** |
| **minimax/minimax-m2.7** | OpenRouter | `frontier` | 204,800 tok | 477.8 ms | $0.255 / $1.020 | $0.255 / $1.02 | **92.5 / 100** |
| **minimax/minimax-m2.5** | OpenRouter | `frontier` | 204,800 tok | 477.8 ms | $0.270 / $1.080 | $0.27 / $1.08 | **92.5 / 100** |
| **minimax/minimax-m2.1** | OpenRouter | `frontier` | 204,800 tok | 477.8 ms | $0.300 / $1.200 | $0.3 / $1.2 | **92.5 / 100** |
| **anthropic/claude-opus-4.5** | OpenRouter | `frontier` | 200,000 tok | 477.8 ms | $2.500 / $12.500 | $2.5 / $12.5 | **92.5 / 100** |
| **anthropic/claude-opus-4.1** | OpenRouter | `frontier` | 200,000 tok | 477.8 ms | $7.500 / $37.500 | $7.5 / $37.5 | **92.5 / 100** |
| **Zhipu GLM 5.2 Frontier** | Zhipu AI | `frontier` | 204,800 tok | 477.8 ms | $0.600 / $1.920 | $0.6 / $1.92 | **92.5 / 100** |
| **upstage/solar-pro-3** | OpenRouter | `frontier` | 131,072 tok | 477.8 ms | $0.150 / $0.600 | $0.15 / $0.6 | **92.2 / 100** |
| **thinkingmachines/inkling-small** | OpenRouter | `reasoning` | 1,048,576 tok | 477.8 ms | $0.950 / $4.050 | $0.95 / $4.05 | **92.1 / 100** |
| **thinkingmachines/inkling:free** | OpenRouter | `reasoning` | 1,048,576 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **92.1 / 100** |
| **openai/gpt-5.2-chat** | OpenRouter | `frontier` | 128,000 tok | 477.8 ms | $1.750 / $14.000 | $1.75 / $14.0 | **92.1 / 100** |
| **perplexity/sonar-pro-search** | OpenRouter | `frontier` | 127,072 tok | 477.8 ms | $1.000 / $1.000 | $1.0 / $1.0 | **92.1 / 100** |
| **perplexity/sonar-reasoning-pro** | OpenRouter | `frontier` | 128,000 tok | 477.8 ms | $2.000 / $8.000 | $2.0 / $8.0 | **92.1 / 100** |
| **minimax/minimax-m2-her** | OpenRouter | `frontier` | 65,536 tok | 477.8 ms | $0.300 / $1.200 | $0.3 / $1.2 | **91.8 / 100** |
| **gryphe/mythomax-l2-13b** | OpenRouter | `frontier` | 8,192 tok | 477.8 ms | $0.060 / $0.060 | $0.06 / $0.06 | **91.5 / 100** |
| **x-ai/grok-4.20-multi-agent** | OpenRouter | `agentic` | 2,000,000 tok | 477.8 ms | $1.250 / $2.500 | $1.25 / $2.5 | **91.4 / 100** |
| **google/gemini-3.1-pro-preview-customtools** | OpenRouter | `agentic` | 1,048,576 tok | 477.8 ms | $2.000 / $12.000 | $2.0 / $12.0 | **91.4 / 100** |
| **NVIDIA Nemotron 3 Super 120B** | NVIDIA | `reasoning` | 262,144 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **90.4 / 100** |
| **thinkingmachines/inkling:batch** | OpenRouter | `reasoning` | 524,288 tok | 477.8 ms | $1.000 / $4.050 | $1.0 / $4.05 | **89.7 / 100** |
| **Moonshot Kimi K3** | Moonshot AI | `long_context` | 1,048,576 tok | 624.7 ms | $3.000 / $15.000 | $3.0 / $15.0 | **89.5 / 100** |
| **Google Gemini 2.5 Pro** | Google | `long_context` | 1,048,576 tok | 477.8 ms | $1.250 / $10.000 | $1.25 / $10.0 | **89.0 / 100** |
| **OpenAI o3-mini** | OpenAI | `reasoning` | 200,000 tok | 477.8 ms | $0.550 / $2.200 | $0.55 / $2.2 | **88.5 / 100** |
| **arcee-ai/trinity-large-thinking** | OpenRouter | `reasoning` | 262,144 tok | 477.8 ms | $0.220 / $0.850 | $0.22 / $0.85 | **88.4 / 100** |
| **qwen/qwen3-max-thinking** | OpenRouter | `reasoning` | 262,144 tok | 477.8 ms | $0.780 / $3.900 | $0.78 / $3.9 | **88.4 / 100** |
| **moonshotai/kimi-k2-thinking** | OpenRouter | `reasoning` | 262,144 tok | 477.8 ms | $0.600 / $2.500 | $0.6 / $2.5 | **88.4 / 100** |
| **qwen/qwen3-vl-30b-a3b-thinking** | OpenRouter | `reasoning` | 262,144 tok | 477.8 ms | $0.200 / $2.400 | $0.2 / $2.4 | **88.4 / 100** |
| **qwen/qwen3-next-80b-a3b-thinking** | OpenRouter | `reasoning` | 262,144 tok | 477.8 ms | $0.150 / $1.200 | $0.15 / $1.2 | **88.4 / 100** |
| **openai/o3-pro** | OpenRouter | `reasoning` | 200,000 tok | 477.8 ms | $10.000 / $40.000 | $10.0 / $40.0 | **88.1 / 100** |
| **openai/o3:batch** | OpenRouter | `reasoning` | 200,000 tok | 477.8 ms | $1.000 / $4.000 | $1.0 / $4.0 | **88.1 / 100** |
| **openai/o1-pro** | OpenRouter | `reasoning` | 200,000 tok | 477.8 ms | $15.000 / $60.000 | $15.0 / $60.0 | **88.1 / 100** |
| **openai/o1:batch** | OpenRouter | `reasoning` | 200,000 tok | 477.8 ms | $7.500 / $30.000 | $7.5 / $30.0 | **88.1 / 100** |
| **DeepSeek R1 (Reasoner)** | DeepSeek | `reasoning` | 64,000 tok | 685.5 ms | $0.700 / $2.500 | $0.7 / $2.5 | **87.9 / 100** |
| **qwen/qwen3-vl-8b-thinking** | OpenRouter | `reasoning` | 131,072 tok | 477.8 ms | $0.180 / $2.100 | $0.18 / $2.1 | **87.8 / 100** |
| **qwen/qwen3-vl-235b-a22b-thinking** | OpenRouter | `reasoning` | 131,072 tok | 477.8 ms | $0.400 / $4.000 | $0.4 / $4.0 | **87.8 / 100** |
| **qwen/qwen3-30b-a3b-thinking-2507** | OpenRouter | `reasoning` | 131,072 tok | 477.8 ms | $0.120 / $0.500 | $0.12 / $0.5 | **87.8 / 100** |
| **qwen/qwen3-235b-a22b-thinking-2507** | OpenRouter | `reasoning` | 131,072 tok | 477.8 ms | $0.455 / $1.820 | $0.455 / $1.82 | **87.8 / 100** |
| **sao10k/l3.3-euryale-70b** | OpenRouter | `reasoning` | 131,072 tok | 477.8 ms | $0.650 / $0.750 | $0.65 / $0.75 | **87.8 / 100** |
| **sao10k/l3.1-euryale-70b** | OpenRouter | `reasoning` | 131,072 tok | 477.8 ms | $0.850 / $0.850 | $0.85 / $0.85 | **87.8 / 100** |
| **Google Gemini 3.5 Flash (Multi)** | Google | `multimodal` | 1,048,576 tok | 477.8 ms | $0.750 / $4.500 | $0.75 / $4.5 | **87.3 / 100** |
| **sao10k/l3-lunaris-8b** | OpenRouter | `reasoning` | 8,192 tok | 477.8 ms | $0.040 / $0.050 | $0.04 / $0.05 | **87.1 / 100** |
| **Gemma 4 31B IT (Agent)** | Google | `agentic` | 262,144 tok | 941.3 ms | 🆓 GRATIS | $0.0 / $0.0 | **84.7 / 100** |
| **meituan/longcat-2.0** | OpenRouter | `long_context` | 1,048,756 tok | 477.8 ms | $0.300 / $1.200 | $0.3 / $1.2 | **84.5 / 100** |
| **Google Gemini 3.6 Flash (Fast)** | Google | `workhorse` | 1,048,576 tok | 477.8 ms | $0.375 / $1.875 | $0.375 / $1.875 | **83.2 / 100** |
| **openrouter/pareto-code** | OpenRouter | `coding` | 2,000,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **82.8 / 100** |
| **qwen/qwen3-coder-plus** | OpenRouter | `coding` | 1,000,000 tok | 477.8 ms | $0.650 / $3.250 | $0.65 / $3.25 | **82.8 / 100** |
| **qwen/qwen3-coder-flash** | OpenRouter | `coding` | 1,000,000 tok | 477.8 ms | $0.195 / $0.975 | $0.195 / $0.975 | **82.8 / 100** |
| **openai/gpt-5.4-image-2** | OpenRouter | `multimodal` | 1,050,000 tok | 477.8 ms | $2.500 / $15.000 | $2.5 / $15.0 | **82.3 / 100** |
| **Poolside Laguna S 2.1 (Code)** | Poolside | `coding` | 262,144 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **82.1 / 100** |
| **Google Gemini 2.5 Flash** | Google | `long_context` | 1,048,576 tok | 477.8 ms | $0.150 / $1.250 | $0.15 / $1.25 | **81.1 / 100** |
| **DeepSeek V3 (Chat)** | DeepSeek | `workhorse` | 163,840 tok | 685.5 ms | $0.257 / $1.029 | $0.2574 / $1.0287 | **80.4 / 100** |
| **qwen/qwen3.8-flash** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.150 / $0.470 | $0.15 / $0.47 | **80.2 / 100** |
| **z-ai/glm-5.3-flash** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | $1.400 / $4.400 | $1.4 / $4.4 | **80.2 / 100** |
| **meta/muse-spark-1.2-contributor** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | $1.250 / $4.250 | $1.25 / $4.25 | **80.2 / 100** |
| **~z-ai/glm-latest** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | $1.400 / $4.400 | $1.4 / $4.4 | **80.2 / 100** |
| **qwen/qwen3.8-2.4t-a95b** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **80.2 / 100** |
| **nvidia/nemotron-3.5-lightning** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **80.2 / 100** |
| **qwen/qwen3.7-flash** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.030 / $0.130 | $0.03 / $0.13 | **80.2 / 100** |
| **openrouter/auto-beta** | OpenRouter | `workhorse` | 2,000,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **80.2 / 100** |
| **meta/muse-spark-1.1** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | $1.250 / $4.250 | $1.25 / $4.25 | **80.2 / 100** |
| **anthropic/claude-sonnet-5** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $1.000 / $5.000 | $1.0 / $5.0 | **80.2 / 100** |
| **sakana/fugu-ultra** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $5.000 / $30.000 | $5.0 / $30.0 | **80.2 / 100** |
| **openrouter/fusion** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **80.2 / 100** |
| **~anthropic/claude-fable-latest** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $10.000 / $50.000 | $10.0 / $50.0 | **80.2 / 100** |
| **anthropic/claude-fable-5** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $5.000 / $25.000 | $5.0 / $25.0 | **80.2 / 100** |
| **nvidia/nemotron-3-ultra-550b-a55b** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **80.2 / 100** |
| **qwen/qwen3.7-plus** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.320 / $1.280 | $0.32 / $1.28 | **80.2 / 100** |
| **x-ai/grok-4.3** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $1.250 / $2.500 | $1.25 / $2.5 | **80.2 / 100** |
| **~moonshotai/kimi-latest** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | $2.550 / $12.750 | $2.55 / $12.75 | **80.2 / 100** |
| **~anthropic/claude-sonnet-latest** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $2.000 / $10.000 | $2.0 / $10.0 | **80.2 / 100** |
| **~openai/gpt-latest** | OpenRouter | `workhorse` | 1,050,000 tok | 477.8 ms | $2.000 / $10.000 | $2.0 / $10.0 | **80.2 / 100** |
| **qwen/qwen3.5-plus-20260420** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.300 / $1.800 | $0.3 / $1.8 | **80.2 / 100** |
| **qwen/qwen3.6-flash** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.188 / $1.125 | $0.1875 / $1.125 | **80.2 / 100** |
| **qwen/qwen3.6-plus** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.325 / $1.950 | $0.325 / $1.95 | **80.2 / 100** |
| **google/lyria-3-clip-preview** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **80.2 / 100** |
| **qwen/qwen3.5-flash-02-23** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.065 / $0.260 | $0.065 / $0.26 | **80.2 / 100** |
| **anthropic/claude-sonnet-4.6** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $3.000 / $15.000 | $3.0 / $15.0 | **80.2 / 100** |
| **qwen/qwen3.5-plus-02-15** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.260 / $1.560 | $0.26 / $1.56 | **80.2 / 100** |
| **writer/palmyra-x5** | OpenRouter | `workhorse` | 1,040,000 tok | 477.8 ms | $0.600 / $6.000 | $0.6 / $6.0 | **80.2 / 100** |
| **amazon/nova-2-lite-v1** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.300 / $2.500 | $0.3 / $2.5 | **80.2 / 100** |
| **amazon/nova-premier-v1** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $2.500 / $12.500 | $2.5 / $12.5 | **80.2 / 100** |
| **anthropic/claude-sonnet-4.5** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $1.500 / $7.500 | $1.5 / $7.5 | **80.2 / 100** |
| **qwen/qwen-plus-2025-07-28** | OpenRouter | `workhorse` | 1,000,000 tok | 477.8 ms | $0.260 / $0.780 | $0.26 / $0.78 | **80.2 / 100** |
| **openai/gpt-4.1** | OpenRouter | `workhorse` | 1,047,576 tok | 477.8 ms | $0.050 / $0.200 | $0.05 / $0.2 | **80.2 / 100** |
| **meta-llama/llama-4-maverick** | OpenRouter | `workhorse` | 1,048,576 tok | 477.8 ms | $0.200 / $0.800 | $0.2 / $0.8 | **80.2 / 100** |
| **meta-llama/llama-4-scout** | OpenRouter | `workhorse` | 1,310,720 tok | 477.8 ms | $0.110 / $0.340 | $0.11 / $0.34 | **80.2 / 100** |
| **thedrummer/unslopnemo-12b** | OpenRouter | `workhorse` | 1,024,000 tok | 477.8 ms | $0.400 / $0.400 | $0.4 / $0.4 | **80.2 / 100** |
| **openai/gpt-5.3-codex** | OpenRouter | `coding` | 400,000 tok | 477.8 ms | $1.750 / $14.000 | $1.75 / $14.0 | **79.8 / 100** |
| **openai/gpt-5.2-codex** | OpenRouter | `coding` | 400,000 tok | 477.8 ms | $1.750 / $14.000 | $1.75 / $14.0 | **79.8 / 100** |
| **openai/gpt-5.1-codex-max** | OpenRouter | `coding` | 400,000 tok | 477.8 ms | $1.250 / $10.000 | $1.25 / $10.0 | **79.8 / 100** |
| **openai/gpt-5.1-codex-mini** | OpenRouter | `coding` | 400,000 tok | 477.8 ms | $0.250 / $2.000 | $0.25 / $2.0 | **79.8 / 100** |
| **openai/gpt-5-codex:batch** | OpenRouter | `coding` | 400,000 tok | 477.8 ms | $0.625 / $5.000 | $0.625 / $5.0 | **79.8 / 100** |
| **openai/gpt-5-image-mini** | OpenRouter | `multimodal` | 400,000 tok | 477.8 ms | $10.000 / $10.000 | $10.0 / $10.0 | **79.3 / 100** |
| **bytedance-seed/seed-2.0-code** | OpenRouter | `coding` | 262,144 tok | 477.8 ms | $0.500 / $3.000 | $0.5 / $3.0 | **79.1 / 100** |
| **kwaipilot/kat-coder-air-v2.5** | OpenRouter | `coding` | 256,000 tok | 477.8 ms | $0.150 / $0.600 | $0.15 / $0.6 | **79.1 / 100** |
| **kwaipilot/kat-coder-pro-v2.5** | OpenRouter | `coding` | 262,144 tok | 477.8 ms | $0.300 / $1.200 | $0.3 / $1.2 | **79.1 / 100** |
| **cohere/north-mini-code:free** | OpenRouter | `coding` | 256,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **79.1 / 100** |
| **qwen/qwen3-coder-next** | OpenRouter | `coding` | 262,144 tok | 477.8 ms | $0.300 / $1.000 | $0.3 / $1.0 | **79.1 / 100** |
| **mistralai/devstral-2512** | OpenRouter | `coding` | 262,144 tok | 477.8 ms | $0.440 / $2.200 | $0.44 / $2.2 | **79.1 / 100** |
| **qwen/qwen3-coder-30b-a3b-instruct** | OpenRouter | `coding` | 262,144 tok | 477.8 ms | $0.070 / $0.280 | $0.07 / $0.28 | **79.1 / 100** |
| **OpenAI GPT-4o (GitHub Models Free Tier)** | OpenAI | `frontier` | 8,191 tok | 477.8 ms | $30.000 / $60.000 | $30.0 / $60.0 | **78.9 / 100** |
| **qwen/qwen3-vl-8b-instruct** | OpenRouter | `multimodal` | 262,144 tok | 477.8 ms | $0.117 / $0.455 | $0.117 / $0.455 | **78.6 / 100** |
| **qwen/qwen3-vl-30b-a3b-instruct** | OpenRouter | `multimodal` | 262,144 tok | 477.8 ms | $0.130 / $0.520 | $0.13 / $0.52 | **78.6 / 100** |
| **qwen/qwen3-vl-235b-a22b-instruct** | OpenRouter | `multimodal` | 262,144 tok | 477.8 ms | $0.210 / $1.900 | $0.21 / $1.9 | **78.6 / 100** |
| **moonshotai/kimi-k2.7-code** | OpenRouter | `coding` | 131,072 tok | 477.8 ms | $0.570 / $2.300 | $0.57 / $2.3 | **78.5 / 100** |
| **opencode/nemotron-3-ultra-free** | OpenCode | `coding` | 128,000 tok | 45.0 ms | 🆓 GRATIS | $0.0 / $0.0 | **78.4 / 100** |
| **opencode/nemotron-3.5-lightning-free** | OpenCode | `coding` | 128,000 tok | 45.0 ms | 🆓 GRATIS | $0.0 / $0.0 | **78.4 / 100** |
| **opencode/mimo-v2.5-free** | OpenCode | `coding` | 128,000 tok | 45.0 ms | 🆓 GRATIS | $0.0 / $0.0 | **78.4 / 100** |
| **opencode/hy3-free** | OpenCode | `coding` | 128,000 tok | 45.0 ms | 🆓 GRATIS | $0.0 / $0.0 | **78.4 / 100** |
| **opencode/big-pickle** | OpenCode | `coding` | 128,000 tok | 45.0 ms | 🆓 GRATIS | $0.0 / $0.0 | **78.4 / 100** |
| **opencode/muse-spark-1.2-contributor-free** | OpenCode | `coding` | 128,000 tok | 45.0 ms | 🆓 GRATIS | $0.0 / $0.0 | **78.4 / 100** |
| **qwen/qwen3-vl-32b-instruct** | OpenRouter | `multimodal` | 131,072 tok | 477.8 ms | $0.104 / $0.416 | $0.104 / $0.416 | **78.0 / 100** |
| **openai/gpt-audio** | OpenRouter | `multimodal` | 128,000 tok | 477.8 ms | $0.600 / $2.400 | $0.6 / $2.4 | **77.9 / 100** |
| **baidu/ernie-4.5-vl-424b-a47b** | OpenRouter | `multimodal` | 123,000 tok | 477.8 ms | $0.420 / $1.250 | $0.42 / $1.25 | **77.9 / 100** |
| **qwen/qwen2.5-vl-72b-instruct** | OpenRouter | `multimodal` | 128,000 tok | 477.8 ms | $0.250 / $0.750 | $0.25 / $0.75 | **77.9 / 100** |
| **dots-studio/dots-3-note-preview:free** | OpenRouter | `workhorse` | 512,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **77.8 / 100** |
| **x-ai/grok-4.6** | OpenRouter | `workhorse` | 500,000 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **77.7 / 100** |
| **x-ai/grok-4.5** | OpenRouter | `workhorse` | 500,000 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **77.7 / 100** |
| **~x-ai/grok-latest** | OpenRouter | `workhorse` | 500,000 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **77.7 / 100** |
| **google/gemini-3.1-flash-image** | OpenRouter | `multimodal` | 65,536 tok | 477.8 ms | $0.500 / $3.000 | $0.5 / $3.0 | **77.6 / 100** |
| **google/gemini-3-pro-image** | OpenRouter | `multimodal` | 65,536 tok | 477.8 ms | $2.000 / $12.000 | $2.0 / $12.0 | **77.6 / 100** |
| **Google Gemini 2.0 Flash** | Google | `realtime` | 1,048,576 tok | 474.1 ms | 🆓 GRATIS | $0.1 / $0.4 | **77.4 / 100** |
| **openai/gpt-chat-latest** | OpenRouter | `workhorse` | 400,000 tok | 477.8 ms | $5.000 / $30.000 | $5.0 / $30.0 | **77.2 / 100** |
| **amazon/nova-lite-v1** | OpenRouter | `workhorse` | 300,000 tok | 477.8 ms | $0.060 / $0.240 | $0.06 / $0.24 | **76.7 / 100** |
| **sakana/sakana-namazu** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.950 / $4.000 | $0.95 / $4.0 | **76.5 / 100** |
| **tencent/hy3** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.180 / $0.600 | $0.18 / $0.6 | **76.5 / 100** |
| **poolside/laguna-xs-2.1** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **76.5 / 100** |
| **stepfun/step-3.7-flash** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.200 / $1.150 | $0.2 / $1.15 | **76.5 / 100** |
| **x-ai/grok-build-0.1** | OpenRouter | `workhorse` | 256,000 tok | 477.8 ms | $1.000 / $2.000 | $1.0 / $2.0 | **76.5 / 100** |
| **moonshotai/kimi-k2.6** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.950 / $4.000 | $0.95 / $4.0 | **76.5 / 100** |
| **google/gemma-4-26b-a4b-it** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **76.5 / 100** |
| **bytedance-seed/seed-2.0-lite** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.250 / $2.000 | $0.25 / $2.0 | **76.5 / 100** |
| **qwen/qwen3.5-9b** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.100 / $0.150 | $0.1 / $0.15 | **76.5 / 100** |
| **qwen/qwen3.5-122b-a10b** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.260 / $2.080 | $0.26 / $2.08 | **76.5 / 100** |
| **stepfun/step-3.5-flash** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.100 / $0.300 | $0.1 / $0.3 | **76.5 / 100** |
| **moonshotai/kimi-k2.5** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.600 / $3.000 | $0.6 / $3.0 | **76.5 / 100** |
| **bytedance-seed/seed-1.6-flash** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.250 / $2.000 | $0.25 / $2.0 | **76.5 / 100** |
| **relace/relace-search** | OpenRouter | `workhorse` | 256,000 tok | 477.8 ms | $1.000 / $3.000 | $1.0 / $3.0 | **76.5 / 100** |
| **relace/relace-apply-3** | OpenRouter | `workhorse` | 256,000 tok | 477.8 ms | $0.850 / $1.250 | $0.85 / $1.25 | **76.5 / 100** |
| **moonshotai/kimi-k2-0905** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.600 / $2.500 | $0.6 / $2.5 | **76.5 / 100** |
| **qwen/qwen3-235b-a22b-2507** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.087 / $0.350 | $0.0875 / $0.35 | **76.5 / 100** |
| **morph/morph-v3-large** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.900 / $1.900 | $0.9 / $1.9 | **76.5 / 100** |
| **cohere/command-a** | OpenRouter | `workhorse` | 256,000 tok | 477.8 ms | $2.500 / $10.000 | $2.5 / $10.0 | **76.5 / 100** |
| **inclusionai/ling-3.0-flash-fin:free** | OpenRouter | `workhorse` | 262,144 tok | 477.8 ms | $0.021 / $0.063 | $0.021 / $0.063 | **76.5 / 100** |
| **Qwen 2.5 Coder 32B Instruct** | Alibaba | `coding` | 32,768 tok | 477.8 ms | $0.660 / $1.000 | $0.66 / $1.0 | **76.2 / 100** |
| **~anthropic/claude-haiku-latest** | OpenRouter | `workhorse` | 200,000 tok | 477.8 ms | $1.000 / $5.000 | $1.0 / $5.0 | **76.2 / 100** |
| **z-ai/glm-5.1** | OpenRouter | `workhorse` | 204,800 tok | 477.8 ms | $1.260 / $3.960 | $1.26 / $3.96 | **76.2 / 100** |
| **openrouter/free** | OpenRouter | `workhorse` | 200,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **76.2 / 100** |
| **z-ai/glm-4.7-flash** | OpenRouter | `workhorse` | 204,800 tok | 477.8 ms | $0.400 / $1.750 | $0.4 / $1.75 | **76.2 / 100** |
| **z-ai/glm-4.6v** | OpenRouter | `workhorse` | 204,800 tok | 477.8 ms | $0.430 / $1.750 | $0.43 / $1.75 | **76.2 / 100** |
| **anthropic/claude-haiku-4.5** | OpenRouter | `workhorse` | 200,000 tok | 477.8 ms | $0.500 / $2.500 | $0.5 / $2.5 | **76.2 / 100** |
| **anthropic/claude-3-haiku** | OpenRouter | `workhorse` | 200,000 tok | 477.8 ms | $0.250 / $1.250 | $0.25 / $1.25 | **76.2 / 100** |
| **meta-llama/llama-guard-4-12b** | OpenRouter | `workhorse` | 163,840 tok | 477.8 ms | $0.180 / $0.180 | $0.18 / $0.18 | **76.0 / 100** |
| **meta/muse-glimmer-30b** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.350 / $1.500 | $0.35 / $1.5 | **75.9 / 100** |
| **mistralai/mistral-medium-3-5** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.400 / $2.000 | $0.4 / $2.0 | **75.9 / 100** |
| **aion-labs/aion-2.0** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.800 / $1.600 | $0.8 / $1.6 | **75.9 / 100** |
| **openai/gpt-oss-safeguard-20b** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.075 / $0.300 | $0.075 / $0.3 | **75.9 / 100** |
| **ibm-granite/granite-4.0-h-micro** | OpenRouter | `workhorse` | 131,000 tok | 477.8 ms | $0.017 / $0.112 | $0.017 / $0.112 | **75.9 / 100** |
| **thedrummer/cydonia-24b-v4.1** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.300 / $0.500 | $0.3 / $0.5 | **75.9 / 100** |
| **mistralai/mistral-medium-3.1** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.400 / $2.000 | $0.4 / $2.0 | **75.9 / 100** |
| **z-ai/glm-4.5v** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.600 / $2.200 | $0.6 / $2.2 | **75.9 / 100** |
| **openai/gpt-oss-120b** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.037 / $0.170 | $0.037 / $0.17 | **75.9 / 100** |
| **openai/gpt-oss-20b** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.030 / $0.130 | $0.03 / $0.13 | **75.9 / 100** |
| **z-ai/glm-4.5-air** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.130 / $0.850 | $0.13 / $0.85 | **75.9 / 100** |
| **arcee-ai/virtuoso-large** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.750 / $1.200 | $0.75 / $1.2 | **75.9 / 100** |
| **qwen/qwen3-14b** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.120 / $0.240 | $0.12 / $0.24 | **75.9 / 100** |
| **qwen/qwen3-32b** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.080 / $0.280 | $0.08 / $0.28 | **75.9 / 100** |
| **google/gemma-3-4b-it** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.050 / $0.100 | $0.05 / $0.1 | **75.9 / 100** |
| **google/gemma-3-12b-it** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.050 / $0.150 | $0.05 / $0.15 | **75.9 / 100** |
| **mistralai/mistral-large-2407** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **75.9 / 100** |
| **meta-llama/llama-3.1-70b-instruct** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.400 / $0.400 | $0.4 / $0.4 | **75.9 / 100** |
| **mistralai/mistral-nemo** | OpenRouter | `workhorse` | 131,072 tok | 477.8 ms | $0.019 / $0.030 | $0.019 / $0.03 | **75.9 / 100** |
| **mistralai/mistral-large-2512** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **75.8 / 100** |
| **nvidia/nemotron-3.5-content-safety:free** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **75.8 / 100** |
| **inception/mercury-2** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | $0.250 / $0.750 | $0.25 / $0.75 | **75.8 / 100** |
| **openrouter/bodybuilder** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **75.8 / 100** |
| **perplexity/sonar-deep-research** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | $2.000 / $8.000 | $2.0 / $8.0 | **75.8 / 100** |
| **amazon/nova-micro-v1** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | $0.035 / $0.140 | $0.035 / $0.14 | **75.8 / 100** |
| **cohere/command-r-08-2024** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | $0.150 / $0.600 | $0.15 / $0.6 | **75.8 / 100** |
| **cohere/command-r-plus-08-2024** | OpenRouter | `workhorse` | 128,000 tok | 477.8 ms | $2.500 / $10.000 | $2.5 / $10.0 | **75.8 / 100** |
| **NVIDIA Nemotron 3 Nano Omni 30B** | NVIDIA | `realtime` | 262,144 tok | 477.8 ms | $0.050 / $0.200 | $0.05 / $0.2 | **75.7 / 100** |
| **morph/morph-v3-fast** | OpenRouter | `workhorse` | 81,920 tok | 477.8 ms | $0.800 / $1.200 | $0.8 / $1.2 | **75.6 / 100** |
| **liquid/lfm-2.5-2.6b:free** | OpenRouter | `workhorse` | 65,536 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **75.5 / 100** |
| **allenai/olmo-3-32b-think** | OpenRouter | `workhorse` | 65,536 tok | 477.8 ms | $0.150 / $0.500 | $0.15 / $0.5 | **75.5 / 100** |
| **rekaai/reka-flash-3** | OpenRouter | `workhorse` | 65,536 tok | 477.8 ms | $0.100 / $0.200 | $0.1 / $0.2 | **75.5 / 100** |
| **thedrummer/rocinante-12b** | OpenRouter | `workhorse` | 65,536 tok | 432.1 ms | $0.250 / $0.500 | $0.25 / $0.5 | **75.5 / 100** |
| **mistralai/mixtral-8x22b-instruct** | OpenRouter | `workhorse` | 65,536 tok | 477.8 ms | $2.000 / $6.000 | $2.0 / $6.0 | **75.5 / 100** |
| **perceptron/perceptron-mk1** | OpenRouter | `workhorse` | 32,768 tok | 477.8 ms | $0.150 / $1.500 | $0.15 / $1.5 | **75.4 / 100** |
| **thedrummer/skyfall-36b-v2** | OpenRouter | `workhorse` | 32,768 tok | 477.8 ms | $0.550 / $0.800 | $0.55 / $0.8 | **75.4 / 100** |
| **mistralai/mistral-saba** | OpenRouter | `workhorse` | 32,768 tok | 477.8 ms | $0.200 / $0.600 | $0.2 / $0.6 | **75.4 / 100** |
| **anthracite-org/magnum-v4-72b** | OpenRouter | `workhorse` | 32,768 tok | 477.8 ms | $3.000 / $5.000 | $3.0 / $5.0 | **75.4 / 100** |
| **qwen/qwen-2.5-72b-instruct** | OpenRouter | `workhorse` | 32,768 tok | 477.8 ms | $0.360 / $0.400 | $0.36 / $0.4 | **75.4 / 100** |
| **mancer/weaver** | OpenRouter | `workhorse` | 8,000 tok | 477.8 ms | $0.500 / $0.750 | $0.5 / $0.75 | **75.2 / 100** |
| **google/gemini-3.1-flash-lite-image** | OpenRouter | `realtime` | 1,048,576 tok | 477.8 ms | $0.250 / $1.500 | $0.25 / $1.5 | **74.4 / 100** |
| **google/gemini-3.1-flash-lite:batch** | OpenRouter | `realtime` | 1,048,576 tok | 477.8 ms | $0.125 / $0.750 | $0.125 / $0.75 | **74.4 / 100** |
| **google/gemini-3.1-flash-lite-preview** | OpenRouter | `realtime` | 1,048,576 tok | 477.8 ms | $0.250 / $1.500 | $0.25 / $1.5 | **74.4 / 100** |
| **Meta Llama 3.3 70B Instruct** | Meta | `agentic` | 131,072 tok | 477.8 ms | $0.710 / $0.710 | $0.71 / $0.71 | **73.9 / 100** |
| **nousresearch/hermes-4-70b** | OpenRouter | `uncensored` | 131,072 tok | 477.8 ms | $0.130 / $0.400 | $0.13 / $0.4 | **73.7 / 100** |
| **nousresearch/hermes-4-405b** | OpenRouter | `uncensored` | 131,072 tok | 477.8 ms | $1.000 / $3.000 | $1.0 / $3.0 | **73.7 / 100** |
| **nousresearch/hermes-3-llama-3.1-405b** | OpenRouter | `uncensored` | 131,072 tok | 477.8 ms | $1.000 / $1.000 | $1.0 / $1.0 | **73.7 / 100** |
| **cognitivecomputations/dolphin-mistral-24b-venice-edition** | OpenRouter | `uncensored` | 128,000 tok | 477.8 ms | $0.200 / $0.900 | $0.2 / $0.9 | **73.6 / 100** |
| **microsoft/wizardlm-2-8x22b** | OpenRouter | `uncensored` | 65,535 tok | 477.8 ms | $0.620 / $0.620 | $0.62 / $0.62 | **73.3 / 100** |
| **Mistral Codestral Latest** | Mistral | `coding` | 256,000 tok | 579.9 ms | $0.300 / $0.900 | $0.3 / $0.9 | **71.2 / 100** |
| **OpenAI GPT-4o-mini** | OpenAI | `workhorse` | 128,000 tok | 477.8 ms | $0.150 / $0.600 | $0.15 / $0.6 | **71.0 / 100** |
| **bytedance-seed/seed-2-1-turbo** | OpenRouter | `realtime` | 262,144 tok | 477.8 ms | $0.500 / $2.500 | $0.5 / $2.5 | **70.7 / 100** |
| **z-ai/glm-5v-turbo** | OpenRouter | `realtime` | 202,752 tok | 477.8 ms | $1.200 / $4.000 | $1.2 / $4.0 | **70.4 / 100** |
| **z-ai/glm-5-turbo** | OpenRouter | `realtime` | 202,752 tok | 477.8 ms | $1.200 / $4.000 | $1.2 / $4.0 | **70.4 / 100** |
| **Nous Hermes 3 70B** | Nous Research | `uncensored` | 131,072 tok | 477.8 ms | $0.700 / $0.700 | $0.7 / $0.7 | **70.2 / 100** |
| **openai/gpt-4-turbo** | OpenRouter | `realtime` | 128,000 tok | 477.8 ms | $10.000 / $30.000 | $10.0 / $30.0 | **70.0 / 100** |
| **openai/gpt-3.5-turbo-0613** | OpenRouter | `realtime` | 16,385 tok | 477.8 ms | $0.500 / $1.500 | $0.5 / $1.5 | **69.5 / 100** |
| **openai/gpt-3.5-turbo-16k** | OpenRouter | `realtime` | 16,385 tok | 477.8 ms | $3.000 / $4.000 | $3.0 / $4.0 | **69.5 / 100** |
| **openai/gpt-3.5-turbo:batch** | OpenRouter | `realtime` | 16,385 tok | 477.8 ms | $0.250 / $0.750 | $0.25 / $0.75 | **69.5 / 100** |
| **openai/gpt-3.5-turbo-instruct** | OpenRouter | `realtime` | 4,095 tok | 477.8 ms | $1.500 / $2.000 | $1.5 / $2.0 | **69.4 / 100** |
| **minimax/minimax-m3** | OpenRouter | `frontier` | 1,048,576 tok | 477.8 ms | 🆓 GRATIS | $0.0 / $0.0 | **68.0 / 100** |
| **google/gemma-2-27b-it** | OpenRouter | `edge` | 8,192 tok | 477.8 ms | $0.650 / $0.650 | $0.65 / $0.65 | **67.6 / 100** |
| **qwen/qwen3.8-27b** | OpenRouter | `edge` | 1,000,000 tok | 477.8 ms | $0.425 / $2.550 | $0.425 / $2.55 | **66.5 / 100** |
| **~google/gemini-flash-latest** | OpenRouter | `edge` | 1,048,576 tok | 477.8 ms | $0.375 / $1.875 | $0.375 / $1.875 | **66.5 / 100** |
| **google/gemini-3-flash-preview** | OpenRouter | `edge` | 1,048,576 tok | 477.8 ms | $0.250 / $1.500 | $0.25 / $1.5 | **66.5 / 100** |
| **~openai/gpt-mini-latest** | OpenRouter | `edge` | 400,000 tok | 477.8 ms | $0.750 / $4.500 | $0.75 / $4.5 | **63.5 / 100** |
| **nex-agi/nex-n2-mini** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.025 / $0.100 | $0.025 / $0.1 | **62.8 / 100** |
| **qwen/qwen3.6-35b-a3b** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.100 / $0.900 | $0.1 / $0.9 | **62.8 / 100** |
| **qwen/qwen3.6-27b** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.320 / $3.200 | $0.32 / $3.2 | **62.8 / 100** |
| **mistralai/mistral-small-2603** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.150 / $0.600 | $0.15 / $0.6 | **62.8 / 100** |
| **bytedance-seed/seed-2.0-mini** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.100 / $0.400 | $0.1 / $0.4 | **62.8 / 100** |
| **qwen/qwen3.5-35b-a3b** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.250 / $1.250 | $0.25 / $1.25 | **62.8 / 100** |
| **qwen/qwen3.5-27b** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.195 / $1.560 | $0.195 / $1.56 | **62.8 / 100** |
| **qwen/qwen3.5-397b-a17b** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.390 / $2.340 | $0.39 / $2.34 | **62.8 / 100** |
| **mistralai/ministral-14b-2512** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.200 / $0.200 | $0.2 / $0.2 | **62.8 / 100** |
| **mistralai/ministral-8b-2512** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.150 / $0.150 | $0.15 / $0.15 | **62.8 / 100** |
| **qwen/qwen3-next-80b-a3b-instruct** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.100 / $1.100 | $0.1 / $1.1 | **62.8 / 100** |
| **qwen/qwen3-30b-a3b-instruct-2507** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.048 / $0.193 | $0.0481 / $0.193 | **62.8 / 100** |
| **google/gemma-3-27b-it** | OpenRouter | `edge` | 262,144 tok | 477.8 ms | $0.080 / $0.450 | $0.08 / $0.45 | **62.8 / 100** |
| **openai/o4-mini-high** | OpenRouter | `edge` | 200,000 tok | 477.8 ms | $1.100 / $4.400 | $1.1 / $4.4 | **62.5 / 100** |
| **openai/o4-mini:batch** | OpenRouter | `edge` | 200,000 tok | 477.8 ms | $0.550 / $2.200 | $0.55 / $2.2 | **62.5 / 100** |
| **aion-labs/aion-3.0-mini** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $3.000 / $6.000 | $3.0 / $6.0 | **62.2 / 100** |
| **ibm-granite/granite-4.1-8b** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $0.050 / $0.100 | $0.05 / $0.1 | **62.2 / 100** |
| **mistralai/ministral-3b-2512** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $0.100 / $0.100 | $0.1 / $0.1 | **62.2 / 100** |
| **tencent/hunyuan-a13b-instruct** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $0.140 / $0.570 | $0.14 / $0.57 | **62.2 / 100** |
| **mistralai/mistral-small-3.2-24b-instruct** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $0.075 / $0.200 | $0.075 / $0.2 | **62.2 / 100** |
| **qwen/qwen3-8b** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $0.117 / $0.455 | $0.117 / $0.455 | **62.2 / 100** |
| **meta-llama/llama-3.2-3b-instruct** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $0.050 / $0.330 | $0.05 / $0.33 | **62.2 / 100** |
| **meta-llama/llama-3.1-8b-instruct** | OpenRouter | `edge` | 131,072 tok | 477.8 ms | $0.050 / $0.080 | $0.05 / $0.08 | **62.2 / 100** |
| **bytedance/ui-tars-1.5-7b** | OpenRouter | `edge` | 128,000 tok | 477.8 ms | $0.100 / $0.200 | $0.1 / $0.2 | **62.1 / 100** |
| **mistralai/mistral-small-3.1-24b-instruct** | OpenRouter | `edge` | 128,000 tok | 477.8 ms | $0.351 / $0.555 | $0.351 / $0.555 | **62.1 / 100** |
| **cohere/command-r7b-12-2024** | OpenRouter | `edge` | 128,000 tok | 477.8 ms | $0.037 / $0.150 | $0.0375 / $0.15 | **62.1 / 100** |
| **meta-llama/llama-3.2-1b-instruct** | OpenRouter | `edge` | 60,000 tok | 477.8 ms | $0.027 / $0.201 | $0.027 / $0.201 | **61.8 / 100** |
| **mistralai/voxtral-small-24b-2507** | OpenRouter | `edge` | 32,000 tok | 477.8 ms | $0.100 / $0.300 | $0.1 / $0.3 | **61.7 / 100** |
| **aion-labs/aion-rp-llama-3.1-8b** | OpenRouter | `edge` | 32,768 tok | 477.8 ms | $0.800 / $1.600 | $0.8 / $1.6 | **61.7 / 100** |
| **mistralai/mistral-small-24b-instruct-2501** | OpenRouter | `edge` | 32,768 tok | 477.8 ms | $0.050 / $0.080 | $0.05 / $0.08 | **61.7 / 100** |
| **qwen/qwen-2.5-7b-instruct** | OpenRouter | `edge` | 32,768 tok | 477.8 ms | $0.100 / $0.200 | $0.1 / $0.2 | **61.7 / 100** |
| **rekaai/reka-edge** | OpenRouter | `edge` | 16,384 tok | 477.8 ms | $0.100 / $0.100 | $0.1 / $0.1 | **61.6 / 100** |
| **tencent/hy-mt2-1.8b** | OpenRouter | `edge` | 8,192 tok | 477.8 ms | $0.044 / $0.177 | $0.044 / $0.177 | **61.5 / 100** |
| **tencent/hy-mt2-30b-a3b** | OpenRouter | `edge` | 8,192 tok | 477.8 ms | $0.074 / $0.295 | $0.074 / $0.295 | **61.5 / 100** |
| **tencent/hy-mt2-7b** | OpenRouter | `edge` | 8,192 tok | 477.8 ms | $0.074 / $0.295 | $0.074 / $0.295 | **61.5 / 100** |
| **undi95/remm-slerp-l2-13b** | OpenRouter | `edge` | 6,144 tok | 477.8 ms | $0.450 / $0.650 | $0.45 / $0.65 | **61.5 / 100** |
| **Microsoft Phi-4 (GitHub Models)** | Microsoft | `reasoning` | 16,384 tok | 477.8 ms | $0.070 / $0.140 | $0.07 / $0.14 | **30.0 / 100** |

---

## ⚪ 2. RADAR GLOBAL: MODELOS DE REFERENCIA MUNDIAL (NO INSTALADOS LOCALMENTE)
*(Modelos punteros del mercado que NO tengo activados en mi equipo, para benchmarking comparativo)*

| Ranking | Modelo | Proveedor | Categoría | Inteligencia | Elo LMSYS | Coste / 1M |
|:---:|---|---|---|:---:|:---:|---|
| #1 | **deepseek/deepseek-v4-pro-0813** | OpenRouter | `frontier` | 96.5 / 100 | 1150 | $0.87 / $1.74 |
| #55 | **GPT-4.5-Preview** | Unknown | `frontier` | 92.1 / 100 | 1400 | Gratis |
| #56 | **Claude Opus 4 (20250514)** | Unknown | `frontier` | 92.1 / 100 | 1368 | Gratis |
| #57 | **Qwen2.5-Max** | Unknown | `frontier` | 92.1 / 100 | 1363 | Gratis |
| #58 | **Gemini-1.5-Pro-002** | Unknown | `frontier` | 92.1 / 100 | 1317 | Gratis |
| #59 | **Qwen-Max-0919** | Unknown | `frontier` | 92.1 / 100 | 1278 | Gratis |
| #60 | **Gemini-1.5-Pro-001** | Unknown | `frontier` | 92.1 / 100 | 1275 | Gratis |
| #61 | **Claude 3 Opus** | Unknown | `frontier` | 92.1 / 100 | 1262 | Gratis |
| #62 | **Amazon Nova Pro 1.0** | Unknown | `frontier` | 92.1 / 100 | 1260 | Gratis |
| #63 | **claude-opus-4-6-high** | Unknown | `frontier` | 92.1 / 100 | 1400 | Gratis |
| #64 | **claude-opus-4-7-high** | Unknown | `frontier` | 92.1 / 100 | 1400 | Gratis |
| #65 | **claude-opus-5-high** | Unknown | `frontier` | 92.1 / 100 | 1400 | Gratis |
| #66 | **claude-opus-5-max** | Unknown | `frontier` | 92.1 / 100 | 1400 | Gratis |
| #67 | **glm-5.3-max** | Unknown | `frontier` | 92.1 / 100 | 1400 | Gratis |
| #68 | **gpt-5.6-sol-xhigh** | Unknown | `frontier` | 92.1 / 100 | 1400 | Gratis |

---

## 📊 3. SEGMENTACIÓN DETALLADA POR CASOS DE USO

### 👑 Top Modelos Frontier (Máximo Razonamiento)
- ⚪ [EXTERNO] **deepseek/deepseek-v4-pro-0813** (OpenRouter): Score **96.5/100** · Contexto: 1,048,576 tokens
- 🟢 [EN MI PC] **qwen/qwen3.8-max** (OpenRouter): Score **96.5/100** · Contexto: 1,000,000 tokens
- 🟢 [EN MI PC] **anthropic/claude-opus-5-fast** (OpenRouter): Score **96.5/100** · Contexto: 1,000,000 tokens
- 🟢 [EN MI PC] **anthropic/claude-opus-5:batch** (OpenRouter): Score **96.5/100** · Contexto: 1,000,000 tokens
- 🟢 [EN MI PC] **openai/gpt-5.6-luna:batch** (OpenRouter): Score **96.5/100** · Contexto: 1,050,000 tokens

### ⚡ Top Caballos de Batalla (Workhorses de Alta Eficiencia)
- 🟢 [EN MI PC] **Google Gemini 3.6 Flash (Fast)** ($0.375/M): Eficiencia **68.7/100** · Contexto: 1,048,576 tokens
- 🟢 [EN MI PC] **DeepSeek V3 (Chat)** ($0.2574/M): Eficiencia **64.6/100** · Contexto: 163,840 tokens
- 🟢 [EN MI PC] **qwen/qwen3.8-flash** ($0.15/M): Eficiencia **78.7/100** · Contexto: 1,000,000 tokens
- 🟢 [EN MI PC] **z-ai/glm-5.3-flash** ($1.4/M): Eficiencia **58.4/100** · Contexto: 1,048,576 tokens
- 🟢 [EN MI PC] **meta/muse-spark-1.2-contributor** ($1.25/M): Eficiencia **58.8/100** · Contexto: 1,048,576 tokens

### 💻 Top Especialistas en Programación y Agentes
- ⚪ [EXTERNO] **Anthropic Claude 3.5 Sonnet**: Score Coding **72.1/100**
- 🟢 [EN MI PC] **openrouter/pareto-code**: Score Coding **89.4/100**
- 🟢 [EN MI PC] **qwen/qwen3-coder-plus**: Score Coding **89.4/100**
- 🟢 [EN MI PC] **qwen/qwen3-coder-flash**: Score Coding **89.4/100**
- 🟢 [EN MI PC] **Poolside Laguna S 2.1 (Code)**: Score Coding **88.7/100**

---

## 💬 PROMPTS SUGERIDOS PARA PREGUNTAR A LA IA FRONTIER:
1. *«Teniendo en cuenta mis APIs locales activas, ¿cuál es el mejor modelo para armar un agente de extracción de datos masivo con el menor coste?»*
2. *«Compara mi modelo local más potente contra el #1 del ranking mundial: ¿en qué tareas concretas notaré la diferencia y vale la pena pagar la API externa?»*
3. *«Diseña un pipeline de cascada de modelos utilizando exclusivamente mis APIs gratuitas y de bajo costo listadas en la sección 1.»*

---
*Generado automáticamente por FloydIA AI Rankings Observatory el 2026-08-27.*  
*«Desde la infraestructura, todo.»*
