// FloydIA AI Rankings & Local API Observatory - Dashboard Client Logic
let currentFiltered = typeof allModels !== 'undefined' ? [...allModels] : [];
let sortState = { table: null, col: null, asc: false };
let selectedModel = null;
let currentTab = "python";
let vsModelAId = "gemini-2.5-pro";
let vsModelBId = "claude-3-7-sonnet";

function init() {
  if (typeof allModels !== 'undefined') {
    currentFiltered = [...allModels];
  }
  populateVsSelects();
  setSortMode('free_score_desc');
}

function populateVsSelects() {
  const selA = document.getElementById("vsSelectA");
  const selB = document.getElementById("vsSelectB");
  if (!selA || !selB || !Array.isArray(allModels)) return;

  const opts = allModels.map(m => '<option value="' + m.id + '">' + m.canonical_name + ' (' + m.provider + ' · ' + m.tier + ')</option>').join("");
  selA.innerHTML = opts;
  selB.innerHTML = opts;

  if (allModels.some(m => m.id === vsModelAId)) selA.value = vsModelAId;
  else if (allModels.length > 0) selA.value = allModels[0].id;

  if (allModels.some(m => m.id === vsModelBId)) selB.value = vsModelBId;
  else if (allModels.length > 1) selB.value = allModels[1].id;
}

function setSortMode(mode) {
  const sel = document.getElementById("sortSelect");
  if (sel) sel.value = mode;
  sortState = { table: null, col: null, asc: false };
  applySortByMode(mode);
  renderGlobalTable();
  renderLocalTable();
}

function onSortSelectChange() {
  const sel = document.getElementById("sortSelect");
  const mode = sel ? sel.value : "free_score_desc";
  sortState = { table: null, col: null, asc: false };
  applySortByMode(mode);
  renderGlobalTable();
  renderLocalTable();
}

function applySortByMode(mode) {
  if (mode === "free_score_desc") {
    currentFiltered.sort((a, b) => {
      const freeA = Boolean(a.is_free_tier) ? 1 : 0;
      const freeB = Boolean(b.is_free_tier) ? 1 : 0;
      if (freeA !== freeB) return freeB - freeA;
      return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
    });
  } else if (mode === "score_desc") {
    currentFiltered.sort((a, b) => (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0));
  } else if (mode === "score_asc") {
    currentFiltered.sort((a, b) => (Number(a.intelligence_score) || 0) - (Number(b.intelligence_score) || 0));
  } else if (mode === "workhorse_desc") {
    currentFiltered.sort((a, b) => (Number(b.workhorse_score) || 0) - (Number(a.workhorse_score) || 0));
  } else if (mode === "coding_desc") {
    currentFiltered.sort((a, b) => (Number(b.coding_score) || 0) - (Number(a.coding_score) || 0));
  } else if (mode === "price_asc") {
    currentFiltered.sort((a, b) => {
      const costA = Boolean(a.is_free_tier) ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0));
      const costB = Boolean(b.is_free_tier) ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0));
      if (costA !== costB) return costA - costB;
      return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
    });
  } else if (mode === "price_desc") {
    currentFiltered.sort((a, b) => {
      const costA = Boolean(a.is_free_tier) ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0));
      const costB = Boolean(b.is_free_tier) ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0));
      if (costA !== costB) return costB - costA;
      return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
    });
  } else if (mode === "local_first") {
    currentFiltered.sort((a, b) => {
      const locA = Boolean(a.is_local_active) ? 1 : 0;
      const locB = Boolean(b.is_local_active) ? 1 : 0;
      if (locA !== locB) return locB - locA;
      return (Number(b.intelligence_score) || 0) - (Number(a.intelligence_score) || 0);
    });
  } else if (mode === "context_desc") {
    currentFiltered.sort((a, b) => (Number(b.context_window) || 0) - (Number(a.context_window) || 0));
  } else if (mode === "name_asc") {
    currentFiltered.sort((a, b) => (a.canonical_name || "").localeCompare(b.canonical_name || ""));
  }
}

function applyPreset(preset) {
  document.querySelectorAll(".smart-pill").forEach(p => p.classList.remove("active"));
  if (window.event && window.event.target) window.event.target.classList.add("active");

  const setCats = (obj) => {
    document.getElementById("filterFreeOnly").checked = Boolean(obj.free);
    document.getElementById("filterLocalOnly").checked = Boolean(obj.local);
    document.getElementById("filterFrontier").checked = Boolean(obj.frontier);
    document.getElementById("filterAgentic").checked = Boolean(obj.agentic);
    document.getElementById("filterReasoning").checked = Boolean(obj.reasoning);
    document.getElementById("filterMultimodal").checked = Boolean(obj.multimodal);
    document.getElementById("filterLongContext").checked = Boolean(obj.long_context);
    document.getElementById("filterWorkhorse").checked = Boolean(obj.workhorse);
    document.getElementById("filterCoding").checked = Boolean(obj.coding);
    document.getElementById("filterUncensored").checked = Boolean(obj.uncensored);
    document.getElementById("filterRealtime").checked = Boolean(obj.realtime);
    if (document.getElementById("filterEdge")) document.getElementById("filterEdge").checked = Boolean(obj.edge);
  };

  if (preset === "coding_free") {
    setCats({ free: true, coding: true });
    if (document.getElementById("contextSelect")) document.getElementById("contextSelect").value = "all";
    setSortMode("coding_desc");
  } else if (preset === "agentic") {
    setCats({ agentic: true, frontier: true });
    if (document.getElementById("contextSelect")) document.getElementById("contextSelect").value = "all";
    setSortMode("score_desc");
  } else if (preset === "long_doc") {
    setCats({ long_context: true });
    if (document.getElementById("contextSelect")) document.getElementById("contextSelect").value = "1m";
    setSortMode("score_desc");
  } else if (preset === "stem_reasoning") {
    setCats({ reasoning: true });
    if (document.getElementById("contextSelect")) document.getElementById("contextSelect").value = "all";
    setSortMode("score_desc");
  } else if (preset === "realtime") {
    setCats({ realtime: true, workhorse: true });
    if (document.getElementById("contextSelect")) document.getElementById("contextSelect").value = "all";
    setSortMode("workhorse_desc");
  } else if (preset === "uncensored") {
    setCats({ uncensored: true });
    if (document.getElementById("contextSelect")) document.getElementById("contextSelect").value = "all";
    setSortMode("score_desc");
  } else {
    setCats({ frontier: true, agentic: true, reasoning: true, multimodal: true, long_context: true, workhorse: true, coding: true, uncensored: true, realtime: true, edge: true });
    if (document.getElementById("contextSelect")) document.getElementById("contextSelect").value = "all";
    setSortMode("free_score_desc");
  }
}

function filterAndRender() {
  const q = document.getElementById("searchInput").value.toLowerCase().trim();
  const selectedSource = document.getElementById("sourceSelect").value;
  const selectedContext = document.getElementById("contextSelect") ? document.getElementById("contextSelect").value : "all";
  const onlyFree = document.getElementById("filterFreeOnly").checked;
  const onlyLocal = document.getElementById("filterLocalOnly").checked;

  const showFrontier = document.getElementById("filterFrontier").checked;
  const showAgentic = document.getElementById("filterAgentic").checked;
  const showReasoning = document.getElementById("filterReasoning").checked;
  const showMultimodal = document.getElementById("filterMultimodal").checked;
  const showLongContext = document.getElementById("filterLongContext").checked;
  const showWorkhorse = document.getElementById("filterWorkhorse").checked;
  const showCoding = document.getElementById("filterCoding").checked;
  const showUncensored = document.getElementById("filterUncensored").checked;
  const showRealtime = document.getElementById("filterRealtime").checked;
  const showEdge = document.getElementById("filterEdge") ? document.getElementById("filterEdge").checked : true;

  currentFiltered = allModels.filter(m => {
    if (onlyFree && !Boolean(m.is_free_tier)) return false;
    if (onlyLocal && !Boolean(m.is_local_active)) return false;

    const t = m.tier;
    if (t === "frontier" && !showFrontier) return false;
    if (t === "agentic" && !showAgentic) return false;
    if (t === "reasoning" && !showReasoning) return false;
    if (t === "multimodal" && !showMultimodal) return false;
    if (t === "long_context" && !showLongContext) return false;
    if (t === "workhorse" && !showWorkhorse) return false;
    if (t === "coding" && !showCoding) return false;
    if (t === "uncensored" && !showUncensored) return false;
    if (t === "realtime" && !showRealtime) return false;
    if (t === "edge" && !showEdge) return false;

    if (selectedSource !== "all") {
      const sources = (m.sources || []).map(s => String(s).toLowerCase());
      const prov = (m.provider || "").toLowerCase();
      const target = selectedSource.toLowerCase();

      const hasSource = sources.some(s => s.includes(target) || target.includes(s));
      const hasProv = prov.includes(target) || target.includes(prov);

      if (!hasSource && !hasProv) return false;
    }

    if (selectedContext !== "all") {
      const ctx = Number(m.context_window) || 0;
      if (selectedContext === "32k" && ctx < 32000) return false;
      if (selectedContext === "128k" && ctx < 128000) return false;
      if (selectedContext === "256k" && ctx < 256000) return false;
      if (selectedContext === "1m" && ctx < 1000000) return false;
      if (selectedContext === "2m" && ctx < 2000000) return false;
    }

    if (q) {
      const matchName = (m.canonical_name || "").toLowerCase().includes(q);
      const matchProv = (m.provider || "").toLowerCase().includes(q);
      const matchId = (m.id || "").toLowerCase().includes(q);
      if (!matchName && !matchProv && !matchId) return false;
    }
    return true;
  });

  if (sortState.table !== null && sortState.col !== null) {
    applyTableSort(sortState.table, sortState.col, sortState.asc);
  } else {
    const currentMode = document.getElementById("sortSelect").value;
    applySortByMode(currentMode);
  }

  renderLocalTable();
  renderGlobalTable();
}

function renderLocalTable() {
  const tbody = document.getElementById("localTableBody");
  if (!tbody) return;
  const localModels = currentFiltered.filter(m => Boolean(m.is_local_active));
  const badgeEl = document.getElementById("localCountBadge");
  if (badgeEl) badgeEl.innerText = localModels.length + " activos";

  if (localModels.length === 0) {
    tbody.innerHTML = "<tr><td colspan='9' style='text-align: center; color: #94A3B8;'>No hay modelos locales que coincidan con los filtros.</td></tr>";
    return;
  }

  tbody.innerHTML = localModels.map(m => {
    const freeTxt = m.is_free_tier ? "<span class='free-badge'>🆓 GRATIS</span>" : ('$' + (Number(m.input_cost_per_m) || 0).toFixed(3) + ' / $' + (Number(m.output_cost_per_m) || 0).toFixed(3));
    const lat = m.local_latency_ms ? (m.local_latency_ms + " ms") : "-";
    const statusTxt = m.local_status_msg || '🟢 OK';
    return `
      <tr class="model-row">
        <td onclick="openModal('${m.id}')"><strong>${m.canonical_name}</strong> <span style="font-size: 11px; color: var(--floydia-teal);">ℹ️</span></td>
        <td onclick="openModal('${m.id}')">${m.provider}</td>
        <td onclick="openModal('${m.id}')"><span class="tier-badge tier-${m.tier}">${m.tier}</span></td>
        <td onclick="openModal('${m.id}')" class="code-val">${(Number(m.context_window) || 0).toLocaleString()} tok</td>
        <td onclick="openModal('${m.id}')" class="code-val">${lat}</td>
        <td onclick="openModal('${m.id}')" class="code-val">${freeTxt}</td>
        <td onclick="openModal('${m.id}')" class="score-val">${m.intelligence_score} / 100</td>
        <td onclick="openModal('${m.id}')"><span class="badge-local">${statusTxt}</span></td>
        <td>
          <button class="mini-vs-btn" onclick="triggerVsDirect('${m.id}', event)">⚔️ VS</button>
        </td>
      </tr>
    `;
  }).join("");
}

function renderGlobalTable() {
  const tbody = document.getElementById("globalTableBody");
  if (!tbody) return;
  const countBadge = document.getElementById("totalCountBadge");
  if (countBadge) countBadge.innerText = currentFiltered.length + " modelos";

  if (currentFiltered.length === 0) {
    tbody.innerHTML = "<tr><td colspan='11' style='text-align: center; color: #94A3B8;'>Ningún modelo coincide con los filtros seleccionados.</td></tr>";
    return;
  }

  tbody.innerHTML = currentFiltered.map(m => {
    const badgeHtml = m.is_local_active ? "<span class='badge-local'>🟢 LOCAL</span>" : "<span class='badge-external'>⚪ EXTERNO</span>";
    const costStr = m.is_free_tier ? "<span class='free-badge'>🆓 GRATIS</span>" : ('$' + (Number(m.input_cost_per_m) || 0).toFixed(3) + ' / $' + (Number(m.output_cost_per_m) || 0).toFixed(3));
    const eloVal = Math.round((Number(m.preference_score) || 0) * 4 + 1000);
    const sourcesHtml = (m.sources || []).map(s => '<span class="source-tag">' + s + '</span>').join("");

    return `
      <tr class="model-row">
        <td onclick="openModal('${m.id}')" class="code-val">#${m.global_rank}</td>
        <td onclick="openModal('${m.id}')"><strong>${m.canonical_name}</strong> <span style="font-size: 11px; color: #64748B;">(${m.provider})</span> <span style="font-size: 11px; color: var(--floydia-teal);">ℹ️</span></td>
        <td onclick="openModal('${m.id}')">${badgeHtml}</td>
        <td onclick="openModal('${m.id}')"><span class="tier-badge tier-${m.tier}">${m.tier}</span></td>
        <td onclick="openModal('${m.id}')" class="score-val">${m.intelligence_score}</td>
        <td onclick="openModal('${m.id}')" class="code-val">${m.workhorse_score}</td>
        <td onclick="openModal('${m.id}')" class="code-val">${m.coding_score}</td>
        <td onclick="openModal('${m.id}')" class="code-val">${eloVal}</td>
        <td onclick="openModal('${m.id}')" class="code-val">${costStr}</td>
        <td onclick="openModal('${m.id}')">${sourcesHtml}</td>
        <td>
          <button class="mini-vs-btn" onclick="triggerVsDirect('${m.id}', event)">⚔️ VS</button>
        </td>
      </tr>
    `;
  }).join("");
}

function applyTableSort(tableType, colIndex, isAsc) {
  currentFiltered.sort((a, b) => {
    let valA, valB;
    if (tableType === "localTable") {
      if (colIndex === 0) { valA = (a.canonical_name || "").toLowerCase(); valB = (b.canonical_name || "").toLowerCase(); }
      else if (colIndex === 1) { valA = (a.provider || "").toLowerCase(); valB = (b.provider || "").toLowerCase(); }
      else if (colIndex === 2) { valA = (a.tier || "").toLowerCase(); valB = (b.tier || "").toLowerCase(); }
      else if (colIndex === 3) { valA = Number(a.context_window) || 0; valB = Number(b.context_window) || 0; }
      else if (colIndex === 4) { valA = Number(a.local_latency_ms) || 999999; valB = Number(b.local_latency_ms) || 999999; }
      else if (colIndex === 5) { 
        valA = a.is_free_tier ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0)); 
        valB = b.is_free_tier ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0)); 
      }
      else if (colIndex === 6) { valA = Number(a.intelligence_score) || 0; valB = Number(b.intelligence_score) || 0; }
      else if (colIndex === 7) { valA = (a.local_status_msg || "").toLowerCase(); valB = (b.local_status_msg || "").toLowerCase(); }
      else { valA = a.id; valB = b.id; }
    } else {
      if (colIndex === 0) { valA = Number(a.global_rank) || 0; valB = Number(b.global_rank) || 0; }
      else if (colIndex === 1) { valA = (a.canonical_name || "").toLowerCase(); valB = (b.canonical_name || "").toLowerCase(); }
      else if (colIndex === 2) { valA = a.is_local_active ? 1 : 0; valB = b.is_local_active ? 1 : 0; }
      else if (colIndex === 3) { valA = (a.tier || "").toLowerCase(); valB = (b.tier || "").toLowerCase(); }
      else if (colIndex === 4) { valA = Number(a.intelligence_score) || 0; valB = Number(b.intelligence_score) || 0; }
      else if (colIndex === 5) { valA = Number(a.workhorse_score) || 0; valB = Number(b.workhorse_score) || 0; }
      else if (colIndex === 6) { valA = Number(a.coding_score) || 0; valB = Number(b.coding_score) || 0; }
      else if (colIndex === 7) { valA = Number(a.preference_score) || 0; valB = Number(b.preference_score) || 0; }
      else if (colIndex === 8) { 
        valA = a.is_free_tier ? 0 : ((Number(a.input_cost_per_m) || 0) + (Number(a.output_cost_per_m) || 0)); 
        valB = b.is_free_tier ? 0 : ((Number(b.input_cost_per_m) || 0) + (Number(b.output_cost_per_m) || 0)); 
      }
      else if (colIndex === 9) { valA = (a.sources || []).length; valB = (b.sources || []).length; }
      else { valA = a.id; valB = b.id; }
    }

    if (typeof valA === "string") {
      return isAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return isAsc ? (valA - valB) : (valB - valA);
  });
}

function sortTable(tableType, colIndex) {
  const isAsc = (sortState.table === tableType && sortState.col === colIndex) ? !sortState.asc : (colIndex === 0 || colIndex === 1);
  sortState = { table: tableType, col: colIndex, asc: isAsc };

  applyTableSort(tableType, colIndex, isAsc);
  renderGlobalTable();
  renderLocalTable();
}

function openModal(modelId) {
  const m = allModels.find(item => item.id === modelId);
  if (!m) return;
  selectedModel = m;

  document.getElementById("modalModelName").innerText = m.canonical_name;
  document.getElementById("modalProvider").innerText = "Proveedor: " + m.provider + " · ID: " + m.id;
  
  const localBadge = document.getElementById("modalLocalBadge");
  localBadge.className = m.is_local_active ? "badge-local" : "badge-external";
  localBadge.innerText = m.is_local_active ? "🟢 ACTIVO EN TU PC" : "⚪ REFERENCIA EXTERNA";

  const tierBadge = document.getElementById("modalTierBadge");
  tierBadge.className = "tier-badge tier-" + m.tier;
  tierBadge.innerText = m.tier;

  document.getElementById("modalIntelScore").innerText = m.intelligence_score + " / 100";
  document.getElementById("modalWorkhorseScore").innerText = m.workhorse_score + " / 100";
  document.getElementById("modalCodingScore").innerText = m.coding_score + " / 100";
  document.getElementById("modalContextWindow").innerText = (Number(m.context_window) || 0).toLocaleString() + " tok";
  document.getElementById("modalPricing").innerText = m.is_free_tier ? "🆓 Gratis" : ('$' + (Number(m.input_cost_per_m) || 0).toFixed(3) + ' In / $' + (Number(m.output_cost_per_m) || 0).toFixed(3) + ' Out');

  document.getElementById("modalDescription").innerText = m.description || "Sin descripción disponible.";
  document.getElementById("modalComparison").innerText = m.comparison || "Sin datos comparativos.";

  const useCasesList = document.getElementById("modalUseCases");
  useCasesList.innerHTML = (m.use_cases || []).map(uc => '<li>' + uc + '</li>').join("");

  const sourcesDiv = document.getElementById("modalSources");
  sourcesDiv.innerHTML = (m.sources || []).map(s => '<span class="source-tag" style="font-size: 12px; padding: 4px 8px;">📊 ' + s + '</span>').join(" ");

  // Transparencia de Benchmarks: qué métricas contribuyeron a cada score
  const benchSection = document.getElementById("modalBenchmarks");
  if (benchSection) {
    let benchHtml = '';
    const intelBench = m.intel_benchmarks || [];
    const codingBench = m.coding_benchmarks || [];
    const benchLabels = {
      'mmlu_pro': 'MMLU-Pro', 'gpqa': 'GPQA', 'livebench': 'LiveBench',
      'math_500': 'MATH-500', 'epoch_science': 'Epoch AI', 'aa_quality_index': 'AA Quality',
      'humaneval': 'HumanEval', 'swe_bench': 'SWE-bench', 'aider_polyglot': 'Aider',
      'livecodebench': 'LiveCodeBench', 'arena_coding_elo': 'Arena Coding'
    };
    if (intelBench.length > 0) {
      benchHtml += '<div style="margin-bottom:6px;"><strong>🧠 Inteligencia:</strong> ';
      benchHtml += intelBench.map(b => '<span class="source-tag" style="font-size:11px;padding:2px 6px;background:rgba(99,102,241,0.15);color:#818CF8;">' + (benchLabels[b]||b) + '</span>').join(' ');
      benchHtml += '</div>';
    }
    if (codingBench.length > 0) {
      benchHtml += '<div><strong>💻 Coding:</strong> ';
      benchHtml += codingBench.map(b => '<span class="source-tag" style="font-size:11px;padding:2px 6px;background:rgba(52,211,153,0.15);color:#34D399;">' + (benchLabels[b]||b) + '</span>').join(' ');
      benchHtml += '</div>';
    }
    if (!benchHtml) benchHtml = '<em style="color:#6B7280;">Scores calculados con heurísticas de categoría (sin benchmarks directos).</em>';
    benchSection.innerHTML = benchHtml;
  }

  updateSnippet();

  const localSection = document.getElementById("modalLocalSection");
  const localStatus = document.getElementById("modalLocalStatus");
  if (m.is_local_active) {
    const toolsTxt = m.supports_tools ? '✅ Sí' : '❌ No';
    const visionTxt = m.supports_vision ? '✅ Sí' : '❌ No';
    const reasoningTxt = m.supports_reasoning ? '✅ Sí' : '⚡ Directo';
    const latTxt = m.local_latency_ms ? (m.local_latency_ms + ' ms') : '-';
    const stMsg = m.local_status_msg || '🟢 Operativa y verificada';

    localSection.style.display = "block";
    localStatus.innerHTML = 
      '<strong>Estado de Conexión:</strong> ' + stMsg + '<br>' +
      '<strong>Latencia Medida:</strong> ' + latTxt + '<br>' +
      '<strong>Ventana Detectada:</strong> ' + (Number(m.local_detected_context) || 0).toLocaleString() + ' tokens<br>' +
      '<strong>Soporte de Herramientas:</strong> ' + toolsTxt + ' | ' +
      '<strong>Visión:</strong> ' + visionTxt + ' | ' +
      '<strong>Razonamiento Nativo:</strong> ' + reasoningTxt;
  } else {
    localSection.style.display = "block";
    localStatus.innerHTML = '<em>Este modelo no está configurado actualmente en tu archivo <code>.secrets/antigravity.env</code>. Para activarlo, configura la API key correspondiente en tu entorno.</em>';
  }

  document.getElementById("modelModal").classList.add("active");
}

function compareFromModal() {
  if (!selectedModel) return;
  closeModal();
  vsModelAId = selectedModel.id;
  openVsModal();
}

function triggerVsDirect(modelId, e) {
  if (e) e.stopPropagation();
  vsModelAId = modelId;
  openVsModal();
}

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll(".snippet-tab").forEach(t => t.classList.remove("active"));
  if (window.event && window.event.target) window.event.target.classList.add("active");
  updateSnippet();
}

function updateSnippet() {
  if (!selectedModel) return;
  const m = selectedModel;
  const snippetPre = document.getElementById("snippetCode");
  if (!snippetPre) return;

  if (currentTab === 'python') {
    snippetPre.innerText = 'from openai import OpenAI\n\nclient = OpenAI(\n    base_url="https://openrouter.ai/api/v1",\n    api_key="TU_API_KEY"\n)\n\nresponse = client.chat.completions.create(\n    model="' + m.id + '",\n    messages=[{"role": "user", "content": "Hola mundo"}],\n    temperature=0.2\n)\nprint(response.choices[0].message.content)';
  } else {
    snippetPre.innerText = 'curl https://openrouter.ai/api/v1/chat/completions \\\n  -H "Authorization: Bearer $OPENROUTER_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d \'{"model": "' + m.id + '", "messages": [{"role": "user", "content": "Hola mundo"}]\'';
  }
}

function copySnippet() {
  const code = document.getElementById("snippetCode").innerText;
  navigator.clipboard.writeText(code);
  const btn = window.event ? window.event.target : null;
  if (btn) {
    btn.innerText = "✅ ¡Copiado!";
    setTimeout(() => btn.innerText = "📋 Copiar Código", 2000);
  }
}

function closeModal() {
  const modal = document.getElementById("modelModal");
  if (modal) modal.classList.remove("active");
}

function closeModalOnBackdrop(e) {
  if (e.target.id === "modelModal") closeModal();
}

/* LÓGICA COMPARADOR VS CARA A CARA */
function openVsModal() {
  const selA = document.getElementById("vsSelectA");
  const selB = document.getElementById("vsSelectB");
  if (selA && vsModelAId) selA.value = vsModelAId;
  if (selB && vsModelBId) selB.value = vsModelBId;
  updateVsComparison();
  const vsModal = document.getElementById("vsModal");
  if (vsModal) vsModal.classList.add("active");
}

function closeVsModal() {
  const vsModal = document.getElementById("vsModal");
  if (vsModal) vsModal.classList.remove("active");
}

function closeVsModalOnBackdrop(e) {
  if (e.target.id === "vsModal") closeVsModal();
}

function setVsPair(idA, idB) {
  vsModelAId = idA;
  vsModelBId = idB;
  const selA = document.getElementById("vsSelectA");
  const selB = document.getElementById("vsSelectB");
  if (selA) selA.value = idA;
  if (selB) selB.value = idB;
  updateVsComparison();
}

function updateVsComparison() {
  const selA = document.getElementById("vsSelectA");
  const selB = document.getElementById("vsSelectB");
  if (!selA || !selB || !Array.isArray(allModels) || allModels.length === 0) return;

  const idA = selA.value;
  const idB = selB.value;
  vsModelAId = idA;
  vsModelBId = idB;

  const mA = allModels.find(m => m.id === idA) || allModels[0];
  const mB = allModels.find(m => m.id === idB) || (allModels[1] || allModels[0]);

  renderVsCard("vsCardA", mA, "A", "--floydia-teal");
  renderVsCard("vsCardB", mB, "B", "#8B5CF6");
  renderVsMetricBars(mA, mB);
  renderVsVerdict(mA, mB);
}

function renderVsCard(containerId, m, label, colorVar) {
  const card = document.getElementById(containerId);
  if (!card || !m) return;
  const isFree = m.is_free_tier;
  const pricingStr = isFree ? "🆓 Gratuito (Free Tier)" : ('$' + (Number(m.input_cost_per_m) || 0).toFixed(3) + ' In / $' + (Number(m.output_cost_per_m) || 0).toFixed(3) + ' Out');
  const localBadge = m.is_local_active ? "<span class='badge-local'>🟢 EN TU PC</span>" : "<span class='badge-external'>⚪ EXTERNO</span>";
  const totalCostStr = isFree ? "<span class='free-badge'>🆓 $0.00</span>" : ('<span class="source-tag">💰 $' + ((Number(m.input_cost_per_m) || 0) + (Number(m.output_cost_per_m) || 0)).toFixed(2) + '/1M</span>');
  const toolTxt = m.supports_tools ? '✅ Soportado' : '❌ No';
  const visTxt = m.supports_vision ? '✅ Soportado' : '❌ No';
  const reasonTxt = m.supports_reasoning ? '✅ Sí (CoT)' : '⚡ Directo';
  const latTxt = m.local_latency_ms ? (m.local_latency_ms + ' ms') : 'No probada en local';
  const descTxt = m.description || 'Sin descripción disponible.';

  card.innerHTML = 
    '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">' +
      '<div>' +
        '<div style="font-family: Chakra Petch, sans-serif; font-size: 20px; font-weight: 700; color: #FFFFFF;">' + m.canonical_name + '</div>' +
        '<div style="font-family: JetBrains Mono, monospace; font-size: 12px; color: #94A3B8;">' + m.provider + ' · <code>' + m.id + '</code></div>' +
      '</div>' +
      '<span class="tier-badge tier-' + m.tier + '">' + m.tier + '</span>' +
    '</div>' +
    '<div style="display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap;">' +
      localBadge +
      '<span class="source-tag">📚 ' + (Number(m.context_window) || 0).toLocaleString() + ' tokens</span>' +
      totalCostStr +
    '</div>' +
    '<div style="background: rgba(11, 17, 28, 0.6); padding: 12px; border-radius: 6px; font-size: 13px; margin-bottom: 12px; border-left: 3px solid var(' + colorVar + ');">' +
      descTxt +
    '</div>' +
    '<div style="font-family: JetBrains Mono, monospace; font-size: 12px; display: flex; flex-direction: column; gap: 6px; color: #CBD5E1;">' +
      '<div>🛠️ <strong>Tool Calling:</strong> ' + toolTxt + '</div>' +
      '<div>👁️ <strong>Visión / Multimodal:</strong> ' + visTxt + '</div>' +
      '<div>🧠 <strong>Razonamiento Nativo:</strong> ' + reasonTxt + '</div>' +
      '<div>⏱️ <strong>Latencia Local:</strong> ' + latTxt + '</div>' +
    '</div>';
}

function renderVsMetricBars(mA, mB) {
  const container = document.getElementById("vsMetricsBars");
  if (!container || !mA || !mB) return;
  const metrics = [
    { label: "🧠 Inteligencia Global", valA: Number(mA.intelligence_score) || 0, valB: Number(mB.intelligence_score) || 0, max: 100, unit: "pts", isTok: false },
    { label: "💻 Coding & Software", valA: Number(mA.coding_score) || 0, valB: Number(mB.coding_score) || 0, max: 100, unit: "pts", isTok: false },
    { label: "⚡ Eficiencia Batalla", valA: Number(mA.workhorse_score) || 0, valB: Number(mB.workhorse_score) || 0, max: 100, unit: "pts", isTok: false },
    { label: "🏆 Preferencia LMSYS Elo", valA: Math.round((Number(mA.preference_score) || 0) * 4 + 1000), valB: Math.round((Number(mB.preference_score) || 0) * 4 + 1000), max: 1500, min: 1000, unit: "Elo", isTok: false },
    { label: "📚 Ventana de Contexto", valA: Number(mA.context_window) || 0, valB: Number(mB.context_window) || 0, max: Math.max(Number(mA.context_window) || 0, Number(mB.context_window) || 0, 2097152), unit: "tok", isTok: true }
  ];

  container.innerHTML = metrics.map(met => {
    const diff = met.valA - met.valB;
    let diffBadge = "";
    if (diff > 0) {
      const diffTxt = met.isTok ? diff.toLocaleString() : diff.toFixed(1);
      diffBadge = '<span class="vs-diff-winner">◀ ' + mA.canonical_name + ' gana por +' + diffTxt + ' ' + met.unit + '</span>';
    } else if (diff < 0) {
      const diffTxt = met.isTok ? Math.abs(diff).toLocaleString() : Math.abs(diff).toFixed(1);
      diffBadge = '<span class="vs-diff-winner" style="color: #A78BFA;">▶ ' + mB.canonical_name + ' gana por +' + diffTxt + ' ' + met.unit + '</span>';
    } else {
      diffBadge = '<span style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #94A3B8;">⚖️ Empate técnico</span>';
    }

    const pctA = Math.min(100, Math.max(5, (met.valA / met.max) * 100));
    const pctB = Math.min(100, Math.max(5, (met.valB / met.max) * 100));

    const displayValA = met.isTok ? met.valA.toLocaleString() : met.valA;
    const displayValB = met.isTok ? met.valB.toLocaleString() : met.valB;

    return `
      <div class="vs-metric-row">
        <div class="vs-metric-header">
          <span style="color: var(--floydia-teal); font-weight: 700;">${mA.canonical_name}: ${displayValA}</span>
          <span style="color: #CBD5E1; font-weight: 600;">${met.label}</span>
          <span style="color: #A78BFA; font-weight: 700;">${mB.canonical_name}: ${displayValB}</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 4px;">
          <div class="vs-bar-track" style="justify-content: flex-end;">
            <div class="vs-bar-fill-a" style="width: ${pctA}%;"></div>
          </div>
          <div class="vs-bar-track">
            <div class="vs-bar-fill-b" style="width: ${pctB}%;"></div>
          </div>
        </div>
        <div style="text-align: center; margin-top: 2px;">${diffBadge}</div>
      </div>
    `;
  }).join("");
}

function renderVsVerdict(mA, mB) {
  const verdictEl = document.getElementById("vsVerdictContent");
  if (!verdictEl || !mA || !mB) return;
  const costA = mA.is_free_tier ? 0 : ((Number(mA.input_cost_per_m) || 0) + (Number(mA.output_cost_per_m) || 0));
  const costB = mB.is_free_tier ? 0 : ((Number(mB.input_cost_per_m) || 0) + (Number(mB.output_cost_per_m) || 0));

  let bulletA = [];
  let bulletB = [];

  const scoreA = Number(mA.intelligence_score) || 0;
  const scoreB = Number(mB.intelligence_score) || 0;
  const codingA = Number(mA.coding_score) || 0;
  const codingB = Number(mB.coding_score) || 0;
  const ctxA = Number(mA.context_window) || 0;
  const ctxB = Number(mB.context_window) || 0;

  if (scoreA > scoreB) bulletA.push('Mayor score de inteligencia (+' + (scoreA - scoreB).toFixed(1) + ' pts)');
  if (codingA > codingB) bulletA.push('Superior en tareas de programación (+' + (codingA - codingB).toFixed(1) + ' pts)');
  if (ctxA > ctxB) bulletA.push('Ventana de contexto superior (' + ctxA.toLocaleString() + ' vs ' + ctxB.toLocaleString() + ')');
  if (mA.is_free_tier && !mB.is_free_tier) bulletA.push('Disponibilidad gratuita (Free Tier $0.00)');
  else if (costA < costB) bulletA.push('Coste por token más económico');
  if (mA.is_local_active && !mB.is_local_active) bulletA.push('Listo y verificado en tu PC (.env local)');

  if (scoreB > scoreA) bulletB.push('Mayor score de inteligencia (+' + (scoreB - scoreA).toFixed(1) + ' pts)');
  if (codingB > codingA) bulletB.push('Superior en tareas de programación (+' + (codingB - codingA).toFixed(1) + ' pts)');
  if (ctxB > ctxA) bulletB.push('Ventana de contexto superior (' + ctxB.toLocaleString() + ' vs ' + ctxA.toLocaleString() + ')');
  if (mB.is_free_tier && !mA.is_free_tier) bulletB.push('Disponibilidad gratuita (Free Tier $0.00)');
  else if (costB < costA) bulletB.push('Coste por token más económico');
  if (mB.is_local_active && !mA.is_local_active) bulletB.push('Listo y verificado en tu PC (.env local)');

  const listAHtml = bulletA.length ? bulletA.map(b => '<li>' + b + '</li>').join('') : '<li>Modelo de referencia equilibrado para su categoría.</li>';
  const listBHtml = bulletB.length ? bulletB.map(b => '<li>' + b + '</li>').join('') : '<li>Modelo de referencia equilibrado para su categoría.</li>';

  verdictEl.innerHTML = 
    '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">' +
      '<div>' +
        '<strong style="color: var(--floydia-teal);">🔹 Elige ' + mA.canonical_name + ' si:</strong>' +
        '<ul style="margin-left: 18px; margin-top: 4px;">' + listAHtml + '</ul>' +
      '</div>' +
      '<div>' +
        '<strong style="color: #C4B5FD;">🔸 Elige ' + mB.canonical_name + ' si:</strong>' +
        '<ul style="margin-left: 18px; margin-top: 4px;">' + listBHtml + '</ul>' +
      '</div>' +
    '</div>';
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeModal();
    closeVsModal();
  }
});

async function submitAdvisorQuestion() {
  const input = document.getElementById("advisorInput");
  const btn = document.getElementById("advisorBtn");
  const resultCard = document.getElementById("advisorResultCard");
  const engineBadge = document.getElementById("advisorResultEngine");
  const resultBody = document.getElementById("advisorResultBody");
  const query = input.value.trim();

  if (!query) {
    alert("Por favor escribe una consulta.");
    return;
  }

  btn.innerText = "Pensando...";
  btn.disabled = true;
  resultCard.style.display = "block";
  resultBody.innerText = "⏳ Consultando con base de conocimiento y analizando rankings...";

  try {
    const res = await fetch("/api/action/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });
    const data = await res.json();
    if (data.success) {
      engineBadge.innerText = "Motor: " + (data.engine || "FloydIA Grounded Advisor");
      resultBody.innerText = data.answer;
    } else {
      resultBody.innerText = "❌ Error: " + (data.error || "No se pudo obtener respuesta.");
    }
  } catch (e) {
    resultBody.innerText = "❌ Error de conexión: " + e;
  } finally {
    btn.innerText = "Preguntar a la IA 🚀";
    btn.disabled = false;
  }
}

function setAdvisorPreset(text) {
  const input = document.getElementById("advisorInput");
  input.value = text;
  submitAdvisorQuestion();
}

function copyAdvisorText() {
  const text = document.getElementById("advisorResultBody").innerText;
  navigator.clipboard.writeText(text).then(() => {
    alert("📋 Respuesta copiada al portapapeles.");
  }).catch(e => {
    alert("Error al copiar: " + e);
  });
}

async function runProbe() {
  const btn = window.event ? window.event.target : null;
  if (btn) btn.innerText = "⏳ Probando...";
  try {
    const res = await fetch("/api/action/probe", {
      method: "POST",
      headers: { "X-Floydia-Token": (typeof DASH_AUTH_TOKEN !== 'undefined' ? DASH_AUTH_TOKEN : ""), "Content-Type": "application/json" }
    });
    const data = await res.json();
    alert("✅ Sonda completada: " + (data.tested_count || 0) + " endpoints evaluados.");
    window.location.reload();
  } catch (e) {
    alert("Error ejecutando sonda: " + e);
  } finally {
    if (btn) btn.innerText = "⚡ Probar APIs Locales";
  }
}

async function runCollect() {
  const btn = window.event ? window.event.target : null;
  if (btn) btn.innerText = "⏳ Recolectando...";
  try {
    const res = await fetch("/api/action/collect", {
      method: "POST",
      headers: { "X-Floydia-Token": (typeof DASH_AUTH_TOKEN !== 'undefined' ? DASH_AUTH_TOKEN : ""), "Content-Type": "application/json" }
    });
    alert("✅ Benchmarks actualizados desde fuentes públicas.");
    window.location.reload();
  } catch (e) {
    alert("Error: " + e);
  } finally {
    if (btn) btn.innerText = "🔄 Actualizar Rankings";
  }
}

async function runApplyConfigs() {
  const btn = window.event ? window.event.target : null;
  if (btn) btn.innerText = "⏳ Inyectando...";
  try {
    const res = await fetch("/api/action/apply-configs", {
      method: "POST",
      headers: { "X-Floydia-Token": (typeof DASH_AUTH_TOKEN !== 'undefined' ? DASH_AUTH_TOKEN : ""), "Content-Type": "application/json" }
    });
    const data = await res.json();
    if (data.success) {
      let msg = "✅ Configuraciones aplicadas con éxito:\n";
      for (const l of (data.logs || [])) {
        msg += "• " + l[0] + "\n";
      }
      alert(msg);
    } else {
      alert("Error aplicando configuraciones.");
    }
  } catch (e) {
    alert("Error de red: " + e);
  } finally {
    if (btn) btn.innerText = "⚙️ Inyectar a Motores";
  }
}

async function runSyncHp45() {
  const btn = window.event ? window.event.target : null;
  if (btn) btn.innerText = "⏳ Sincronizando...";
  try {
    const res = await fetch("/api/action/sync-hp45", {
      method: "POST",
      headers: { "X-Floydia-Token": (typeof DASH_AUTH_TOKEN !== 'undefined' ? DASH_AUTH_TOKEN : ""), "Content-Type": "application/json" }
    });
    const data = await res.json();
    alert(data.message || "Sincronización finalizada.");
  } catch (e) {
    alert("Error de sincronización: " + e);
  } finally {
    if (btn) btn.innerText = "📡 Sincronizar HP45";
  }
}

window.onload = init;
