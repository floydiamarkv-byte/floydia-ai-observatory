# 📐 FloydIA Ranking v3 — Especificación Matemática y Arquitectónica

Auditoría: 2026-08-20. Sustituye la lógica de `src/core/scoring.py` y `src/core/confidence.py`.

---

## 1. Diagnóstico de los defectos actuales (trazabilidad código→defecto)

| Defecto | Ubicación | Causa raíz |
|---|---|---|
| A (mezcla de escalas) | `scoring.py:312` `(Elo-1000)/5.2` mezclado con % crudos | No hay transformación a una métrica latente común |
| B (compresión 81–89) | `scoring.py:326-330` | Imputación plana al `tier_base` retrae todo a la media del tier |
| C (n=1 inflado / colapso) | `scoring.py:324-333` + `confidence.py:80` (varianza fija 16) | No hay shrinkage: o se confía ciegamente en el dato, o se clava al baseline |
| D (identidades) | `scoring.py:237-271` heurísticas de substring | Falta grafo canónico Familia→Variante→Proveedor |
| E (incertidumbre) | `confidence.py:90` margen acotado 0.9–4.5 | Acotado simétrico que ignora n, k, σ real y decaimiento |

---

## 2. Normalización por benchmark: Probit Rank-Boostrapping (PRB)

**Principio rector:** nunca se suman escalas crudas. Cada observación cruda `x` del benchmark `b` se transforma a un **percentil robusto dentro del benchmark**, no dentro del cohorte de modelos (no hay que recalcular todo el ranking al añadir un modelo nuevo).

### 2.1 Transformación por benchmark (estática, por configuración)

Cada benchmark `b` se define por parámetros calibrados contra su población histórica:

```
z = (x - μ_b) / s_b        con s_b = 1.4826 × MAD_b   (escala robusta, Winsorizada)
p = Φ(z)                   CDF normal estándar
score_0_100 = 100 × p_adj,    p_adj = (n_eff × p + α) / (n_eff + 2α), α = 0.5
```

- `μ_b`, `MAD_b` son **constantes de calibración** por benchmark (`BENCHMARK_CALIBRATION` en el código), no estadísticos del cohorte actual. Esto da **estabilidad temporal**: el score de un modelo no cambia porque aparezcan modelos nuevos.
- Winsorización implícita vía MAD (resistente a outliers tipo Arena Elo con picos).
- `n_eff` = tamaño de efectivo histórico del benchmark; el ajuste de Laplace `α=0.5` evita 0 y 100 exactos.

### 2.2 CalibrationMars (constantes por fuente)

| Benchmark | μ | MAD | n_eff | Justificación |
|---|---|---|---|---|
| `arena_elo` | 1250 | 120 | 300 | Población Arena: mediana ~1250, SOTA ~1400 |
| `aa_quality_index` | 45 | 12 | 200 | AA: media poblacional ~45, SOTA ~63 |
| `livebench` | 45 | 15 | 150 | Distribución LLMs en LiveBench |
| `swe_bench` | 25 | 15 | 120 | Resolución Verified: mediana ~25%, SOTA ~75% |
| `aider_polyglot` | 40 | 18 | 100 | |
| `mmlu_pro` | 55 | 12 | 250 | |
| `gpqa` | 40 | 12 | 200 | |
| `math_500` | 55 | 18 | 150 | |
| `epoch_science` | 35 | 14 | 100 | |

> **Calibración periódica:** un script `scripts/calibrate_benchmarks.py` recalcula estas constantes mensualmente desde snapshots históricos y las fija en `benchmark_calibration.json` (versionado, no calculado en caliente). Esto es deliberado: la medición no debe depender del conjunto transitivo presente.

### 2.3 Efecto sobre el Defecto B (separación generacional)

PRB expande las diferencias en las colas: pasar de Elo 1300→1350 (z=0.42→0.83) produce p: 0.66→0.80 (14 puntos FCI), mientras que 1100→1150 produce ~7 puntos. La CDF normal **amplifica la distancia en la zona SOTA**, resolviendo la compresión 81–89.

---

## 3. Fusión multidimensional con shrinkage bayesiano jerárquico

### 3.1 Pilares y renormalización de pesos

Pilares: Razonamiento (0.35), Coding (0.30), Calidad AA (0.20), Preferencia (0.15).

Para cada pilar `p` el modelo tiene `n_p` observaciones normalizadas `v_{p,i}` con varianza de medición `σ²_{p,i}` (incertidumbre de la transformación + varianza entre fuentes del mismo benchmark).

**Media del pilar con mínima varianza (BLUE):**

```
w_i = 1/σ²_{p,i}
μ_p = Σ w_i v_{p,i} / Σ w_i          Var(μ_p) = 1/Σ w_i
```

### 3.2 Shrinkage hacia el prior jerárquico (solución al Defecto C)

Prior por pilar: `N(θ_p, τ²_p)` donde `θ_p` es la **esperanza del pilar para la familia canónica** (heredada de las variantes hermanas ya medidas de la misma familia; si no existen, del tier) y `τ²_p` su varianza (dispersión real intra-familia; default 100 puntos² — vaga pero no plana).

Posterior:

```
λ_p = τ²_p / (τ²_p + Var(μ_p))          # factor de shrinkage ∈ (0,1)
̂S_p = λ_p · μ_p + (1 − λ_p) · θ_p
Var(S_p) = λ_p · Var(μ_p)
```

Propiedades demostradas:
- **n grande** (Var(μ)→0): `λ→1`, el dato manda. Nada de arrastre al tier.
- **n=1 ruidoso** (Var(μ) grande): `λ→0`, domina el prior de familia. El modelo `claude-opus-4-6-high` con un solo Elo ya NO lidera: queda cerca del prior de la familia `claude-opus` con enorme margen.
- **Sin colapso**: como `θ_p` es **por familia** (no un valor global), modelos de familias distintas con pocos datos obtienen scores distintos — se respeta la jerarquía sin empate artificial en 81.5.

**Cobertura completa vs parcial.** El FCI **nunca** redefine su fórmula: siempre se usan los 4 pilares; cuando un pilar no se observó, `λ_p = 0` y `Ŝ_p = θ_p` con `Var(S_p) = τ²_p`. La diferencia n≥5 vs 1≤n≤4 se manifiesta **sólo en el margen**, no en la ecuación. Esto elimina la discontinuidad binaria OBSERVED/ESTIMATED que hoy distorsiona el ordenamiento.

### 3.3 FCI final

```
FCI = ( 0.35·Ŝ_r + 0.30·Ŝ_c + 0.20·Ŝ_q + 0.15·Ŝ_f )
Var(FCI) = 0.35²·Var(S_r) + 0.30²·Var(S_c) + 0.20²·Var(S_q) + 0.15²·Var(S_f)
   (se asume independencia condicional entre pilares; covarianza estimable opcionalmente)
```

---

## 4. Incertidumbre, frescura y confianza

### 4.1 Margen de error con inflación temporal

```
fresh_f = e^(−ln2·d/30)                 (FreshnessEngine, t½=30d)
Var̃(FCI) = Var(FCI) / fresh_f²           # varianza inflada por antigüedad del dato
σ_FCI = √Var̃(FCI)
Margin_95 = 1.96 · σ_FCI
```

Sin acotado arbitrario: un modelo con un solo dato viejo puede tener Margin ±12, lo cual es *información verdadera*, no ruido visual.

### 4.2 Score de confianza

```
C = λ̄_fresh · g(k) · h(σ_between)
λ̄_fresh = Σ w_p λ_p / Σ w_p                         (ponderado por pesos de pilares presentes)
g(k) = 1 − exp(−k/3)                                 (k = fuentes independientes)
h(σ) = 1/(1 + σ_between/10)                          (penalización por discordancia inter-fuente)
```

`C ∈ [0,1]`, continuo, sin umbrales de corte duros. Grados de evidencia solo para UI (A: C≥0.85, B: ≥0.70, C: ≥0.50, D: <0.50).

### 4.3 Empate estadístico (test de Welch formal)

Para los modelos `i, j`:

```
Empate ⇔  |FCI_i − FCI_j|  <  1.96 · √(σ²_i + σ²_j)
```

(diferencia de dos medias independientes aprox. normales). Sustituye la actual regla de la media de márgenes (`scoring.py:454`) que no es un test estadístico en ninguna métrica.

### 4.4 Ordenamiento por "lower bound"

Para el ranking público se ordena por `FCI − Margin` (LCB, Lower Confidence Bound): un modelo con 12 datos a 85 le gana a uno con 1 dato a 90. Es el criterio UC​B/LCB estándar de bandits, y responde exactamente a "cómo evitar que un ruido lidere sin aplanar".

---

## 5. Esquema canónico de identidades (Defecto D)

### 5.1 Grafo jerárquico

```
Family  (claude-3-7-sonnet)
 └── Variant  (reasoning_effort: max | high | standard | fast)
      └── ProviderEndpoint  (anthropic | openrouter | groq | …)
           └── Observation  (benchmark, valor, fecha, fuente)
```

### 5.2 Normalizador determinista

Regla en `IdentityResolver.resolve(raw_id) -> (family_id, variant, provider)`:

1. Lowercase, strip prefijo `~`, separar `proveedor/slug`.
2. Regex de proveedores conocidos → campo `provider`.
3. Slug → alias table (`ALIAS_MAP` versionada): e.g. `claude-fable-5` → familia `claude-fable-5`.
4. Sufijos de variante: `-(max|high|fast|turbo|flash|mini|nano|pro|standard|thinking-\d+k)$` → `variant`.
5. Si no calza: `family_id = slug normalizado` (fail-open, nunca se descarta el dato).

Regla de deduplicación: las observaciones se agregan **a nivel Variant**; las métricas que capturamos de OpenRouter catálogo se registran en el Variant y son heredables como prior débil de la Family solo si la Family no tiene otra evidencia.

---

## 6. Arquitectura de clases (v3)

| Clase | Responsabilidad | Fichero |
|---|---|---|
| `BenchmarkNormalizer` | PRB por benchmark con `BENCHMARK_CALIBRATION` | `src/core/normalization.py` |
| `IdentityResolver` | Grafo Familia→Variante→Proveedor | `src/core/identity.py` |
| `BayesianPillarAggregator` | BLUE + shrinkage jerárquico | `src/core/aggregation.py` |
| `RankingEngineV3` | Orquesta FCI, margen, confianza, empates, LCB | `src/core/ranking_engine_v3.py` |

La clase `RankingEngineV3` entregada en `src/core/ranking_engine_v3.py` integra las 4 piezas en un solo artefacto drop-in para facilitar la migración; la factorización interna por `_normalize`, `_aggregate_pillar`, etc. permite luego extraer los módulos sin reescritura.
