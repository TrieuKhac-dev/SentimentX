(function () {
  "use strict";

  var DEFAULT_MODEL_ID = "cafebert_exp027";
  var POLL_INTERVAL = 500, TIMEOUT_ENCODER = 30000, TIMEOUT_LLM = 240000;
  var MAX_ENCODER = 4000, MAX_LLM = 6000;
  var ENCODER_HINT = "Tối đa 4.000 ký tự.";
  var LLM_HINT = "Tối đa 6.000 ký tự. Lần đầu nạp Qwen có thể mất 30–60 giây.";

  var MSG = {
    loadingModels: "Đang tải mô hình…",
    noModels: "Không có mô hình khả dụng.",
    modelsFailed: "Không tải được danh sách mô hình.",
    ready: "Sẵn sàng",
    loadFailed: "Không nạp được mô hình.",
    analyzing: "Đang phân tích…",
    cancelled: "Đã hủy yêu cầu.",
    noResults: "Không có kết quả trả về.",
    generic: "Không gửi được yêu cầu. Vui lòng thử lại.",
    timeout: "Yêu cầu quá thời gian. Vui lòng thử lại.",
    tooLong: "Đánh giá quá dài. Hãy rút ngắn rồi thử lại.",
    invalid: "Dữ liệu gửi lên không hợp lệ.",
    unavailable: "Mô hình chưa sẵn sàng. Vui lòng thử lại sau.",
    unreadable: "Một số khía cạnh không đọc được.",
    empty: "Không có dữ liệu",
    distinctModels: "Cần chọn hai mô hình khác nhau để so sánh.",
    noResultCell: "Không có kết quả",
    pendingCell: "Đang chờ kết quả…",
    oneFailed: "Đang hiển thị kết quả của mô hình còn lại.",
    bothFailed: "Không có kết quả từ cả hai mô hình."
  };

  var ASPECT_ORDER = ["stayingpower", "texture", "smell", "price", "colour", "shipping", "packing"];
  var ASPECT_LABELS = {
    stayingpower: "Độ bền", texture: "Chất son", smell: "Mùi hương", price: "Giá cả",
    colour: "Màu sắc", shipping: "Vận chuyển", packing: "Đóng gói"
  };
  var SAMPLE_SETS = ["positive", "negative", "mixed"];
  var SAMPLE_LABELS = { positive: "Mẫu tích cực", negative: "Mẫu tiêu cực", mixed: "Mẫu hỗn hợp" };
  var SAMPLE_STATUS_LABELS = { positive: "tích cực", negative: "tiêu cực", mixed: "hỗn hợp" };
  var PROB_LABELS = {
    positive: "Tích cực", negative: "Tiêu cực", neutral: "Trung lập",
    not_mentioned: "Không nhắc tới", unknown: "Không đọc được"
  };
  var PILLS = {
    1: { kind: "positive", className: "pill-positive", text: "Tích cực" },
    2: { kind: "negative", className: "pill-negative", text: "Tiêu cực" },
    0: { kind: "not-mentioned", className: "pill-not-mentioned", text: "Không nhắc tới" },
    3: { kind: "neutral", className: "pill-neutral", text: "Trung lập" },
    unknown: { kind: "unknown", className: "pill-unknown", text: "Không đọc được" }
  };
  var ELS = {
    modeSingle: "mode-single", modeCompare: "mode-compare",
    modelSelect: "model-select-primary", modelLoadStatus: "model-load-status",
    compareControls: "compare-controls", modelSelectSecondary: "model-select-secondary",
    swapModels: "swap-models", reviewInput: "review-input", charCount: "char-count",
    inputHint: "input-hint", sampleButtons: "sample-buttons", sampleStatus: "sample-status",
    analyzeButton: "analyze-button", cancelButton: "cancel-button",
    resultsHeading: "results-heading", resultMeta: "result-meta", resultStatus: "result-status",
    emptyState: "empty-state", resultsContent: "results-content",
    resultTable: "result-table"
  };

  var samples = window.SENTIMENTX_SAMPLES || null;
  var els, models = [], selectedId = "", secondaryId = "", mode = "single";
  var entries = [], activeIndex = -1, isLlm = false, analysisModel = null, comparison = null;
  var loadingModel = false, loadingModelId = null, loadGeneration = 0, loadController = null, loadPromise = null;
  var analyzing = false, analysisController = null, compareController = null, runToken = 0;
  var activeSet = null, sampleIndex = { positive: 0, negative: 0, mixed: 0 }, sampleButtons = {};
  var resultCache = new Map();
  var CACHE_LIMIT = 30;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function queryElements() {
    var missing = [], out = {};
    Object.keys(ELS).forEach(function (key) {
      var node = document.getElementById(ELS[key]);
      if (!node) missing.push(ELS[key]);
      out[key] = node;
    });
    if (missing.length) throw new Error("Thiếu phần tử DOM bắt buộc: " + missing.join(", "));
    return out;
  }

  function stateOf(model) { return model && model.state ? String(model.state).toUpperCase() : ""; }
  function findModel(modelId, source) {
    var list = source || models;
    for (var i = 0; i < list.length; i += 1) {
      if (String(list[i].id) === String(modelId)) return list[i];
    }
    return null;
  }
  function findFirstKind(kind) {
    for (var i = 0; i < models.length; i += 1) {
      if (models[i].kind === kind) return models[i];
    }
    return null;
  }
  function friendlyName(model) {
    if (model && model.kind === "encoder") return "CafeBERT · LoRA";
    if (model && model.kind === "llm") return "Qwen3-4B · Chuỗi suy luận";
    return model && model.id ? String(model.id) : "";
  }
  function shortModelName(model) {
    if (model && model.kind === "encoder") return "CafeBERT";
    if (model && model.kind === "llm") return "Qwen";
    return model && model.id ? String(model.id) : "mô hình";
  }
  function compareModelName(model) {
    if (model && model.kind === "encoder") return "CafeBERT";
    if (model && model.kind === "llm") return "Qwen3-4B";
    return model && model.id ? String(model.id) : "mô hình";
  }
  function maxCharsFor(model) { return model && model.kind === "llm" ? MAX_LLM : MAX_ENCODER; }
  function timeoutForModel(model) { return model && model.kind === "llm" ? TIMEOUT_LLM : TIMEOUT_ENCODER; }
  function aspectLabel(name) { return ASPECT_LABELS[name] || String(name); }
  function formatInt(value) { return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function formatSeconds(ms) { return (ms / 1000).toFixed(1).replace(".", ","); }
  function timeSuffix(data) {
    return data && typeof data.latency_ms === "number" && Number.isFinite(data.latency_ms)
      ? " · " + formatSeconds(data.latency_ms) + " giây" : "";
  }
  function numberOf(value) {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() !== "" && !Number.isNaN(Number(value))) return Number(value);
    return null;
  }
  function parseJson(text) {
    if (!text) return null;
    try { return JSON.parse(text); } catch (error) { return null; }
  }
  function delay(ms) {
    return new Promise(function (resolve) { window.setTimeout(resolve, ms); });
  }
  function cacheKey(model, text) {
    return String(model.id) + "\u0000" + String(model.version || "") + "\u0000" + text;
  }
  function cacheGet(model, text) {
    var key = cacheKey(model, text);
    if (!resultCache.has(key)) return null;
    var value = resultCache.get(key);
    resultCache.delete(key);
    resultCache.set(key, value);
    return value;
  }
  function cacheSet(model, text, data, item) {
    var key = cacheKey(model, text);
    if (resultCache.has(key)) resultCache.delete(key);
    resultCache.set(key, { data: data, item: item });
    while (resultCache.size > CACHE_LIMIT) {
      var oldest = resultCache.keys().next();
      if (oldest.done) break;
      resultCache.delete(oldest.value);
    }
  }
  function errorMessageForStatus(status) {
    if (status === 413) return MSG.tooLong;
    if (status === 422) return MSG.invalid;
    if (status === 503) return MSG.unavailable;
    if (status === 504) return MSG.timeout;
    return MSG.generic;
  }

  function setLoadStatus(message, variant) {
    els.modelLoadStatus.classList.remove("is-loading", "is-ready", "is-error");
    if (variant) els.modelLoadStatus.classList.add(variant);
    els.modelLoadStatus.textContent = message;
  }
  function setStatus(message, variant) {
    els.resultStatus.classList.remove("is-error", "is-warning", "is-success");
    if (variant) els.resultStatus.classList.add(variant);
    els.resultStatus.textContent = message;
    els.resultStatus.hidden = false;
  }
  function clearStatus() {
    els.resultStatus.hidden = true;
    els.resultStatus.classList.remove("is-error", "is-warning", "is-success");
    els.resultStatus.textContent = "";
  }
  function focusElement(node) {
    try { node.focus({ preventScroll: true }); } catch (error) { node.focus(); }
  }
  function focusStatus() { focusElement(els.resultStatus); }
  function focusResults() { focusElement(els.resultsHeading); }
  function hideResults() {
    entries = [];
    activeIndex = -1;
    analysisModel = null;
    comparison = null;
    els.resultsContent.hidden = true;
    els.resultTable.replaceChildren();
    els.emptyState.hidden = false;
    els.resultMeta.textContent = "";
  }
  function showStatusError(message) {
    hideResults();
    setStatus(message, "is-error");
    var retry = el("button", "text-button", "Thử lại");
    retry.type = "button";
    retry.addEventListener("click", analyze);
    els.resultStatus.append(retry);
    focusStatus();
  }

  function currentMaxChars() {
    var model = findModel(selectedId);
    if (mode === "compare") {
      var secondary = findModel(secondaryId);
      if (secondary) return Math.min(maxCharsFor(model), maxCharsFor(secondary));
    }
    return maxCharsFor(model);
  }
  function syncControls() {
    var model = findModel(selectedId);
    var secondary = findModel(secondaryId);
    var compare = mode === "compare";
    var missingCompare = compare && (!secondary || String(secondary.id) === String(selectedId));
    var overLimit = els.reviewInput.value.length > currentMaxChars();
    els.analyzeButton.disabled = analyzing || loadingModel || !model || overLimit || missingCompare;
    els.analyzeButton.classList.toggle("is-loading", analyzing);
    els.analyzeButton.setAttribute("aria-busy", analyzing ? "true" : "false");
    els.cancelButton.hidden = !analyzing;
    els.modelSelect.disabled = analyzing;
    els.modelSelectSecondary.disabled = analyzing || !secondary;
    els.swapModels.disabled = analyzing || !secondary || String(secondary.id) === String(selectedId);
    var buttons = els.sampleButtons.querySelectorAll("button");
    Array.prototype.forEach.call(buttons, function (button) { button.disabled = analyzing; });
  }
  function setAnalyzing(value) {
    analyzing = value;
    els.resultsContent.setAttribute("aria-busy", value ? "true" : "false");
    syncControls();
  }
  function refreshCount() {
    var length = els.reviewInput.value.length;
    var max = currentMaxChars();
    var text = formatInt(length) + " ký tự";
    if (length > max) text += " · vượt " + formatInt(length - max);
    els.charCount.textContent = text;
    syncControls();
  }
  function applyModelMeta(model) {
    els.reviewInput.maxLength = maxCharsFor(model);
    els.inputHint.textContent = model && model.kind === "llm" ? LLM_HINT : ENCODER_HINT;
    refreshCount();
  }
  function filterEnabled(list) {
    return list.filter(function (model) { return model && model.enabled === true; });
  }

  async function fetchModelList(signal) {
    var options = { headers: { Accept: "application/json" } };
    if (signal) options.signal = signal;
    var response = await fetch("/models", options);
    if (!response.ok) throw new Error("HTTP " + response.status);
    var data = await response.json();
    if (!data || !Array.isArray(data.models)) throw new Error("Dữ liệu mô hình không hợp lệ.");
    return filterEnabled(data.models);
  }

  async function runLoad(modelId, generation, controller) {
    try {
      var response = await fetch("/models/" + encodeURIComponent(modelId) + "/load", {
        method: "POST",
        headers: { Accept: "application/json" },
        signal: controller.signal
      });
      if (!response.ok) throw new Error("HTTP " + response.status);
      while (generation === loadGeneration && !controller.signal.aborted) {
        await delay(POLL_INTERVAL);
        if (generation !== loadGeneration || controller.signal.aborted) return false;
        var list = await fetchModelList(controller.signal);
        if (generation !== loadGeneration || controller.signal.aborted) return false;
        models = list;
        var state = stateOf(findModel(modelId));
        if (state === "READY") {
          setLoadStatus(MSG.ready, "is-ready");
          return true;
        }
        if (state === "FAILED") {
          setLoadStatus(MSG.loadFailed, "is-error");
          return false;
        }
      }
      return false;
    } catch (error) {
      if (generation !== loadGeneration || controller.signal.aborted) return false;
      console.error("Không nạp được mô hình:", error);
      setLoadStatus(MSG.loadFailed, "is-error");
      return false;
    } finally {
      if (generation === loadGeneration) {
        loadingModel = false;
        loadingModelId = null;
        loadController = null;
        loadPromise = null;
        syncControls();
      }
    }
  }

  function requestModelLoad(modelId) {
    if (stateOf(findModel(modelId)) === "READY") {
      cancelModelLoad();
      setLoadStatus(MSG.ready, "is-ready");
      syncControls();
      return Promise.resolve(true);
    }
    if (loadingModel && loadingModelId === modelId && loadPromise) return loadPromise;
    var generation = loadGeneration + 1;
    loadGeneration = generation;
    if (loadController) loadController.abort();
    var controller = new AbortController();
    loadController = controller;
    loadingModel = true;
    loadingModelId = modelId;
    setLoadStatus("Đang nạp mô hình", "is-loading");
    syncControls();
    loadPromise = runLoad(modelId, generation, controller);
    return loadPromise;
  }
  function cancelModelLoad() {
    loadGeneration += 1;
    if (loadController) {
      loadController.abort();
      loadController = null;
    }
    loadPromise = null;
    loadingModel = false;
    loadingModelId = null;
  }
  function handleModelChange() {
    stopComparisonForInputChange();
    var modelId = String(els.modelSelect.value || "");
    selectedId = modelId;
    var model = findModel(modelId);
    applyModelMeta(model);
    ensureSecondaryDistinct(mode === "compare");
    if (!model) {
      setLoadStatus(MSG.noModels, "is-error");
      syncControls();
      return;
    }
    if (stateOf(model) === "READY") {
      cancelModelLoad();
      setLoadStatus(MSG.ready, "is-ready");
      syncControls();
      return;
    }
    requestModelLoad(modelId);
  }
  function pickDistinctModel(excludeId) {
    var excluded = findModel(excludeId);
    var preferredKind = excluded && excluded.kind === "llm" ? "encoder" : "llm";
    var candidate = findFirstKind(preferredKind);
    if (candidate && String(candidate.id) !== String(excludeId)) return candidate;
    for (var i = 0; i < models.length; i += 1) {
      if (String(models[i].id) !== String(excludeId)) return models[i];
    }
    return null;
  }
  function pickSecondaryCandidate(excludeId) {
    var excluded = findModel(excludeId);
    var excludeKey = String(excludeId), qwen = null, cafe = null;
    models.forEach(function (model) {
      var key = String(model.id);
      if (key === excludeKey) return;
      var lower = key.toLowerCase();
      if (!qwen && lower.indexOf("qwen") !== -1) qwen = model;
      if (!cafe && lower.indexOf("cafe") !== -1) cafe = model;
    });
    if (excluded && excluded.kind === "llm") return cafe || pickDistinctModel(excludeId);
    return qwen || cafe || pickDistinctModel(excludeId);
  }
  function ensureSecondaryDistinct(announce) {
    if (!secondaryId || String(secondaryId) !== String(selectedId)) return true;
    var candidate = pickSecondaryCandidate(selectedId);
    if (candidate) {
      secondaryId = String(candidate.id);
      els.modelSelectSecondary.value = secondaryId;
      return true;
    }
    secondaryId = "";
    els.modelSelectSecondary.value = "";
    if (announce) setStatus(MSG.distinctModels, "is-warning");
    return false;
  }
  function handleSecondaryChange() {
    stopComparisonForInputChange();
    var modelId = String(els.modelSelectSecondary.value || "");
    if (!modelId) {
      secondaryId = "";
      syncControls();
      return;
    }
    if (modelId === selectedId) {
      var candidate = pickSecondaryCandidate(selectedId);
      if (candidate) {
        secondaryId = String(candidate.id);
        els.modelSelectSecondary.value = secondaryId;
        requestModelLoad(secondaryId);
      } else {
        els.modelSelectSecondary.value = secondaryId || "";
        setStatus(MSG.distinctModels, "is-warning");
      }
      syncControls();
      return;
    }
    secondaryId = modelId;
    requestModelLoad(secondaryId);
    syncControls();
  }
  function handleSwap() {
    if (analyzing) return;
    if (!secondaryId || String(secondaryId) === String(selectedId)) {
      setStatus(MSG.distinctModels, "is-warning");
      els.modelSelectSecondary.focus();
      return;
    }
    var previousPrimary = selectedId;
    selectedId = secondaryId;
    secondaryId = previousPrimary;
    els.modelSelect.value = selectedId;
    els.modelSelectSecondary.value = secondaryId;
    var model = findModel(selectedId);
    applyModelMeta(model);
    if (!model) {
      setLoadStatus(MSG.noModels, "is-error");
    } else if (stateOf(model) === "READY") {
      setLoadStatus(MSG.ready, "is-ready");
    } else {
      requestModelLoad(selectedId);
    }
    syncControls();
  }
  function populatePrimary() {
    els.modelSelect.replaceChildren();
    models.forEach(function (model) {
      var option = document.createElement("option");
      option.value = String(model.id);
      option.textContent = friendlyName(model);
      els.modelSelect.append(option);
    });
    var preferred = findModel(DEFAULT_MODEL_ID) || findFirstKind("encoder") || models[0];
    if (!preferred) {
      selectedId = "";
      setLoadStatus(MSG.noModels, "is-error");
      applyModelMeta(null);
      return;
    }
    selectedId = String(preferred.id);
    els.modelSelect.value = selectedId;
    applyModelMeta(preferred);
    if (stateOf(preferred) === "READY") {
      cancelModelLoad();
      setLoadStatus(MSG.ready, "is-ready");
      syncControls();
      return;
    }
    requestModelLoad(selectedId);
  }
  function populateSecondary() {
    els.modelSelectSecondary.replaceChildren();
    models.forEach(function (model) {
      var option = document.createElement("option");
      option.value = String(model.id);
      option.textContent = friendlyName(model);
      els.modelSelectSecondary.append(option);
    });
    var preferred = selectedId ? pickSecondaryCandidate(selectedId) : (findFirstKind("llm") || models[0]);
    if (!preferred) {
      secondaryId = "";
      els.modelSelectSecondary.value = "";
      syncControls();
      return;
    }
    secondaryId = String(preferred.id);
    els.modelSelectSecondary.value = secondaryId;
    syncControls();
  }
  async function loadModels() {
    setLoadStatus(MSG.loadingModels, "is-loading");
    try {
      models = await fetchModelList(null);
      if (!models.length) {
        els.modelSelect.replaceChildren();
        els.modelSelectSecondary.replaceChildren();
        selectedId = "";
        secondaryId = "";
        setLoadStatus(MSG.noModels, "is-error");
        applyModelMeta(null);
        return;
      }
      populatePrimary();
      populateSecondary();
    } catch (error) {
      console.error("Không tải được danh sách mô hình:", error);
      models = [];
      selectedId = "";
      secondaryId = "";
      els.modelSelect.replaceChildren();
      els.modelSelectSecondary.replaceChildren();
      setLoadStatus(MSG.modelsFailed, "is-error");
      applyModelMeta(null);
    }
  }
  function ensureReady(modelId) {
    if (stateOf(findModel(modelId)) === "READY") return Promise.resolve(true);
    if (loadingModel && loadingModelId === modelId && loadPromise) return loadPromise;
    return requestModelLoad(modelId);
  }

  function labelMeta(aspect) {
    var code = numberOf(aspect && aspect.code);
    return PILLS[code] || PILLS.unknown;
  }
  function pillText(aspect, meta) {
    return aspect && typeof aspect.label_vi === "string" && aspect.label_vi.trim() !== ""
      ? aspect.label_vi : meta.text;
  }
  function buildPill(aspect, meta) {
    var pill = el("span", "label-pill " + meta.className);
    pill.textContent = pillText(aspect, meta);
    return pill;
  }
  function formatConfidence(value) {
    var number = numberOf(value);
    return number === null ? null : Math.round(number * 100) + "%";
  }
  function probLabel(key) {
    var normalized = String(key).trim().toLowerCase().replace(/[\s-]+/g, "_");
    return PROB_LABELS[normalized] || String(key);
  }
  function formatProbs(probs) {
    if (!probs || typeof probs !== "object") return null;
    var parts = [];
    Object.keys(probs).forEach(function (key) {
      var value = numberOf(probs[key]);
      if (value !== null) parts.push(probLabel(key) + " " + Math.round(value * 100) + "%");
    });
    return parts.length ? parts.join(" · ") : null;
  }
  function hasText(value) { return typeof value === "string" && value.trim() !== ""; }

  function collectComparisonEntries(state) {
    var ordered = [], index = {};
    ["a", "b"].forEach(function (key) {
      var side = state && state[key];
      var aspects = side && side.item && side.item.aspects && typeof side.item.aspects === "object"
        ? side.item.aspects : {};
      orderEntries(aspects).forEach(function (entry) {
        if (!index[entry.name]) {
          index[entry.name] = { name: entry.name, a: null, b: null };
          ordered.push(index[entry.name]);
        }
        index[entry.name][key] = entry.aspect;
      });
    });
    return ordered;
  }
  function comparisonLabelKey(aspect) {
    var meta = labelMeta(aspect);
    return meta.kind + "|" + pillText(aspect, meta);
  }
  function comparisonLabelsDiffer(entry) {
    if (!entry || !entry.a || !entry.b) return false;
    return comparisonLabelKey(entry.a) !== comparisonLabelKey(entry.b);
  }
  function buildComparisonMeta(state, count) {
    var parts = [];
    if (state && state.a && state.b) {
      parts.push(compareModelName(state.a.model) + " vs " + compareModelName(state.b.model));
    }
    parts.push(count + " khía cạnh");
    return parts.join(" · ");
  }

  function buildColgroup(classes) {
    var group = document.createElement("colgroup");
    classes.forEach(function (name) {
      var col = document.createElement("col");
      col.className = name;
      group.append(col);
    });
    return group;
  }
  function thCell(text, scope, rowSpan, colSpan) {
    var cell = el("th", "", text);
    if (scope) cell.scope = scope;
    if (rowSpan) cell.rowSpan = rowSpan;
    if (colSpan) cell.colSpan = colSpan;
    return cell;
  }
  function tdCell(label, className) {
    var cell = el("td", className || "");
    if (label) cell.dataset.label = label;
    return cell;
  }
  function toggleClamp(clamp, button) {
    var expanded = clamp.classList.toggle("is-expanded");
    button.textContent = expanded ? "Thu gọn" : "Xem thêm";
  }
  function appendClamp(cell, value) {
    if (!hasText(value)) {
      cell.append(el("span", "empty-value", MSG.empty));
      return;
    }
    var clamp = el("div", "cell-clamp", value);
    var button = el("button", "cell-more", "Xem thêm");
    button.type = "button";
    button.hidden = true;
    button.addEventListener("click", function () { toggleClamp(clamp, button); });
    cell.append(clamp, button);
  }
  var clampResizeTimer = 0;
  function setupClamps() {
    window.requestAnimationFrame(function () {
      var cells = els.resultTable.querySelectorAll(".cell-clamp");
      Array.prototype.forEach.call(cells, function (clamp) {
        var button = clamp.nextElementSibling;
        if (!button || !button.classList.contains("cell-more")) return;
        if (clamp.scrollHeight > clamp.clientHeight + 2) {
          button.hidden = false;
          button.classList.add("is-visible");
        }
      });
    });
  }
  function handleClampResize() {
    window.clearTimeout(clampResizeTimer);
    clampResizeTimer = window.setTimeout(setupClamps, 150);
  }

  function renderSingleTable(data) {
    var headings = isLlm
      ? ["Khía cạnh", "Nhãn", "Đoạn trích", "Lý do mô hình đưa ra"]
      : ["Khía cạnh", "Nhãn", "Độ tin cậy"];
    var columns = isLlm
      ? ["col-aspect", "col-label", "col-quote", "col-reason"]
      : ["col-aspect", "col-label", "col-confidence"];
    var table = el("table", "result-table is-single " + (isLlm ? "is-llm" : "is-encoder"));
    table.append(buildColgroup(columns));
    var headModel = el("tr");
    headModel.append(thCell(friendlyName(analysisModel) + timeSuffix(data), "colgroup", 0, headings.length));
    var headRow = el("tr");
    headings.forEach(function (text) { headRow.append(thCell(text, "col")); });
    var thead = el("thead");
    thead.append(headModel, headRow);
    var tbody = el("tbody");
    if (!entries.length) {
      var emptyRow = el("tr");
      var emptyCell = el("td", "empty-value", MSG.noResults);
      emptyCell.colSpan = headings.length;
      emptyRow.append(emptyCell);
      tbody.append(emptyRow);
    } else {
      entries.forEach(function (entry) {
        var meta = labelMeta(entry.aspect);
        var row = el("tr");
        row.dataset.sentiment = meta.kind;
        var aspectCell = thCell(aspectLabel(entry.name), "row");
        aspectCell.classList.add("aspect-cell");
        row.append(aspectCell);
        var labelCell = tdCell("Nhãn");
        labelCell.append(buildPill(entry.aspect, meta));
        row.append(labelCell);
        if (isLlm) {
          var quoteCell = tdCell("Đoạn trích", "quote-cell");
          appendClamp(quoteCell, entry.aspect.quote);
          var reasonCell = tdCell("Lý do mô hình đưa ra", "reason-cell");
          appendClamp(reasonCell, entry.aspect.reason);
          row.append(quoteCell, reasonCell);
        } else {
          var confidence = formatConfidence(entry.aspect.confidence);
          var confidenceCell = tdCell("Độ tin cậy");
          if (confidence) confidenceCell.textContent = confidence;
          else confidenceCell.append(el("span", "empty-value", MSG.empty));
          row.append(confidenceCell);
        }
        tbody.append(row);
      });
    }
    table.append(thead, tbody);
    els.resultTable.replaceChildren(table);
    setupClamps();
  }

  function compareColumnSpecs(side) {
    var isLlmSide = side && side.model && side.model.kind === "llm";
    return isLlmSide
      ? [
          { key: "label", label: "Nhãn", cls: "col-label" },
          { key: "quote", label: "Đoạn trích", cls: "col-quote" },
          { key: "reason", label: "Lý do mô hình đưa ra", cls: "col-reason" }
        ]
      : [
          { key: "label", label: "Nhãn", cls: "col-label" },
          { key: "confidence", label: "Độ tin cậy", cls: "col-confidence" }
        ];
  }
  function buildCompareSideCells(aspect, side, specs, key, differ) {
    var prefix = shortModelName(side && side.model) + " · ";
    var cells = specs.map(function (spec) {
      var cellClass = spec.key === "quote" ? "quote-cell"
        : spec.key === "reason" ? "reason-cell"
        : spec.key === "confidence" ? "confidence-cell" : "";
      return tdCell(prefix + spec.label, cellClass);
    });
    if (!side || side.pending) {
      cells.forEach(function (cell) { cell.append(el("span", "empty-value", MSG.pendingCell)); });
      return cells;
    }
    if (side.error || !aspect) {
      cells.forEach(function (cell) { cell.append(el("span", "empty-value", MSG.noResultCell)); });
      return cells;
    }
    specs.forEach(function (spec, index) {
      var cell = cells[index];
      if (spec.key === "label") {
        cell.append(buildPill(aspect, labelMeta(aspect)));
        if (differ && key === "b") cell.append(el("span", "label-diff-badge", "Khác"));
      } else if (spec.key === "confidence") {
        var confidence = formatConfidence(aspect.confidence);
        if (confidence) cell.textContent = confidence;
        else cell.append(el("span", "empty-value", MSG.empty));
      } else {
        appendClamp(cell, spec.key === "quote" ? aspect.quote : aspect.reason);
      }
    });
    return cells;
  }

  function renderCompareTable() {
    var state = comparison;
    var list = collectComparisonEntries(state);
    var specsA = compareColumnSpecs(state && state.a);
    var specsB = compareColumnSpecs(state && state.b);
    var table = el("table", "result-table is-compare");
    table.append(buildColgroup(["col-aspect"].concat(
      specsA.map(function (s) { return s.cls; }),
      specsB.map(function (s) { return s.cls; })
    )));
    var headOne = el("tr");
    headOne.append(thCell("Khía cạnh", "col", 2));
    headOne.append(thCell(compareModelName(state && state.a && state.a.model) + timeSuffix(state && state.a && state.a.result), "colgroup", 0, specsA.length));
    headOne.append(thCell(compareModelName(state && state.b && state.b.model) + timeSuffix(state && state.b && state.b.result), "colgroup", 0, specsB.length));
    var headTwo = el("tr");
    specsA.concat(specsB).forEach(function (spec) {
      headTwo.append(thCell(spec.label, "col"));
    });
    var thead = el("thead");
    thead.append(headOne, headTwo);
    var tbody = el("tbody");
    if (!list.length) {
      var emptyRow = el("tr");
      var emptyCell = el("td", "empty-value", MSG.noResults);
      emptyCell.colSpan = 1 + specsA.length + specsB.length;
      emptyRow.append(emptyCell);
      tbody.append(emptyRow);
    } else {
      list.forEach(function (entry) {
        var sideA = state && state.a;
        var sideB = state && state.b;
        var metaA = entry.a ? labelMeta(entry.a) : (entry.b ? labelMeta(entry.b) : PILLS.unknown);
        var differ = comparisonLabelsDiffer(entry);
        var row = el("tr");
        row.dataset.sentiment = metaA.kind;
        var aspectCell = thCell(aspectLabel(entry.name), "row");
        aspectCell.classList.add("aspect-cell");
        row.append(aspectCell);
        buildCompareSideCells(entry.a, sideA, specsA, "a", differ).forEach(function (cell) { row.append(cell); });
        buildCompareSideCells(entry.b, sideB, specsB, "b", differ).forEach(function (cell) { row.append(cell); });
        tbody.append(row);
      });
    }
    table.append(thead, tbody);
    els.resultTable.replaceChildren(table);
    setupClamps();
  }

  function renderComparison() {
    var list = collectComparisonEntries(comparison);
    els.emptyState.hidden = true;
    els.resultsContent.hidden = false;
    els.resultsContent.classList.add("is-comparison");
    els.resultMeta.textContent = buildComparisonMeta(comparison, list.length);
    renderCompareTable();
  }
  function orderEntries(aspects) {
    var ordered = [];
    ASPECT_ORDER.forEach(function (name) {
      if (Object.prototype.hasOwnProperty.call(aspects, name)) {
        ordered.push({ name: name, aspect: aspects[name] && typeof aspects[name] === "object" ? aspects[name] : {} });
      }
    });
    Object.keys(aspects).forEach(function (name) {
      if (ASPECT_ORDER.indexOf(name) === -1) {
        ordered.push({ name: name, aspect: aspects[name] && typeof aspects[name] === "object" ? aspects[name] : {} });
      }
    });
    return ordered;
  }
  function buildResultMeta(count) {
    var parts = [];
    var name = friendlyName(analysisModel);
    if (name) parts.push(name);
    parts.push(count + " khía cạnh");
    return parts.join(" · ");
  }
  function renderResult(data, item, model) {
    var aspects = item && item.aspects && typeof item.aspects === "object" ? item.aspects : {};
    analysisModel = model;
    comparison = null;
    entries = orderEntries(aspects);
    isLlm = Boolean(model && model.kind === "llm");
    activeIndex = entries.length ? 0 : -1;
    els.emptyState.hidden = true;
    els.resultsContent.hidden = false;
    if (mode === "single") els.resultsContent.classList.remove("is-comparison");
    els.resultMeta.textContent = buildResultMeta(entries.length);
    renderSingleTable(data);
    if (item.readable === false) setStatus(MSG.unreadable, "is-warning");
    else clearStatus();
    focusResults();
  }

  function updateSampleLabels() {
    SAMPLE_SETS.forEach(function (set) {
      var button = sampleButtons[set];
      if (!button || !samples || !Array.isArray(samples[set]) || !samples[set].length) return;
      button.textContent = SAMPLE_LABELS[set] + " · " + (sampleIndex[set] + 1) + "/" + samples[set].length;
      var active = activeSet === set;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }
  function handleSampleClick(set) {
    if (analyzing || !samples || !Array.isArray(samples[set]) || !samples[set].length) return;
    if (activeSet !== set) activeSet = set;
    else sampleIndex[set] = (sampleIndex[set] + 1) % samples[set].length;
    els.reviewInput.value = samples[set][sampleIndex[set]];
    updateSampleLabels();
    refreshCount();
    els.sampleStatus.textContent = "Đã điền mẫu " + SAMPLE_STATUS_LABELS[set] + " " +
      (sampleIndex[set] + 1) + "/" + samples[set].length + ".";
  }
  function renderSamples() {
    els.sampleButtons.replaceChildren();
    sampleButtons = {};
    if (!samples || typeof samples !== "object") {
      els.sampleButtons.hidden = true;
      els.sampleStatus.textContent = "Không có dữ liệu mẫu.";
      return;
    }
    var complete = SAMPLE_SETS.every(function (set) {
      return Array.isArray(samples[set]) && samples[set].length > 0;
    });
    if (!complete) {
      els.sampleButtons.hidden = true;
      els.sampleStatus.textContent = "Không có dữ liệu mẫu.";
      return;
    }
    SAMPLE_SETS.forEach(function (set) {
      var button = el("button", "sample-button");
      button.type = "button";
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", function () { handleSampleClick(set); });
      sampleButtons[set] = button;
      els.sampleButtons.append(button);
    });
    updateSampleLabels();
  }

  function applyModeUi() {
    var compare = mode === "compare";
    els.modeSingle.setAttribute("aria-pressed", compare ? "false" : "true");
    els.modeCompare.setAttribute("aria-pressed", compare ? "true" : "false");
    els.compareControls.hidden = !compare;
    els.resultsContent.classList.toggle("is-comparison", compare);
    els.analyzeButton.textContent = compare ? "So sánh đánh giá" : "Phân tích đánh giá";
    refreshCount();
  }
  function switchMode(nextMode) {
    if (mode === nextMode) return;
    stopActiveRun();
    mode = nextMode;
    applyModeUi();
    hideResults();
    clearStatus();
  }
  function initModes() {
    applyModeUi();
    els.modeSingle.addEventListener("click", function () { switchMode("single"); });
    els.modeCompare.addEventListener("click", function () { switchMode("compare"); });
  }

  function stopActiveRun() {
    runToken += 1;
    if (analysisController) {
      analysisController.abort();
      analysisController = null;
    }
    if (compareController) {
      compareController.abort();
      compareController = null;
    }
    if (analyzing) setAnalyzing(false);
  }
  function stopComparisonForInputChange() {
    if (!(analyzing && mode === "compare")) return false;
    stopActiveRun();
    setStatus(MSG.cancelled, "is-warning");
    return true;
  }
  function cancelAnalysis() {
    if (!analyzing) return;
    stopActiveRun();
    setStatus(MSG.cancelled, "is-warning");
  }

  async function fetchPrediction(modelId, text, parentSignal, timeoutMs) {
    var controller = new AbortController();
    var timedOut = false;
    var onParentAbort = function () { controller.abort(); };
    if (parentSignal) {
      if (parentSignal.aborted) controller.abort();
      else parentSignal.addEventListener("abort", onParentAbort, { once: true });
    }
    var timeout = window.setTimeout(function () {
      timedOut = true;
      controller.abort();
    }, timeoutMs);
    try {
      var response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ model: modelId, text: text }),
        signal: controller.signal
      });
      var raw = await response.text();
      var body = parseJson(raw);
      if (!response.ok) {
        return {
          ok: false,
          kind: "http",
          message: errorMessageForStatus(response.status),
          data: body !== null ? body : { status: response.status, body: raw }
        };
      }
      if (!body || typeof body !== "object") {
        return { ok: false, kind: "invalid", message: MSG.generic, data: { status: response.status, body: raw } };
      }
      var item = body.results && body.results[0];
      if (!item) {
        return { ok: false, kind: "empty", message: MSG.noResults, data: body };
      }
      return { ok: true, data: body, item: item };
    } catch (error) {
      if (error && error.name === "AbortError") {
        if (timedOut) return { ok: false, kind: "timeout", message: MSG.timeout, data: { timeout_ms: timeoutMs } };
        return { ok: false, kind: "abort", message: MSG.cancelled, data: null };
      }
      return {
        ok: false,
        kind: "network",
        message: MSG.generic,
        data: { message: String(error && error.message ? error.message : error) }
      };
    } finally {
      window.clearTimeout(timeout);
      if (parentSignal && parentSignal.removeEventListener) {
        parentSignal.removeEventListener("abort", onParentAbort);
      }
    }
  }

  async function runPrediction(modelId, text, model) {
    var token = runToken + 1;
    runToken = token;
    var controller = new AbortController();
    analysisController = controller;
    setAnalyzing(true);
    setStatus(MSG.analyzing, "");
    try {
      var outcome = await fetchPrediction(modelId, text, controller.signal, timeoutForModel(model));
      if (token !== runToken) return;
      if (outcome.ok) {
        cacheSet(model, text, outcome.data, outcome.item);
        renderResult(outcome.data, outcome.item, model);
        return;
      }
      if (outcome.kind === "abort") {
        setStatus(MSG.cancelled, "is-warning");
        return;
      }
      showStatusError(outcome.message);
    } catch (error) {
      if (token !== runToken) return;
      console.error("Không gửi được yêu cầu:", error);
      showStatusError(MSG.generic);
    } finally {
      if (analysisController === controller) analysisController = null;
      if (token === runToken) setAnalyzing(false);
    }
  }

  function createComparisonSide(model) {
    return { model: model, result: null, item: null, error: null, pending: true };
  }
  function applyComparisonOutcome(key, outcome) {
    var side = comparison && comparison[key];
    if (!side) return;
    side.pending = false;
    if (outcome && outcome.ok) {
      side.result = outcome.data;
      side.item = outcome.item;
      return;
    }
    side.error = outcome && outcome.message ? outcome.message : MSG.noResults;
  }
  function finishComparison() {
    var failedA = Boolean(comparison.a.error);
    var failedB = Boolean(comparison.b.error);
    if (failedA && failedB) {
      setStatus(MSG.bothFailed, "is-error");
    } else if (failedA || failedB) {
      var failedName = compareModelName((failedA ? comparison.a : comparison.b).model);
      setStatus("Không có kết quả từ " + failedName + ". " + MSG.oneFailed, "is-warning");
    } else if ((comparison.a.item && comparison.a.item.readable === false) ||
               (comparison.b.item && comparison.b.item.readable === false)) {
      setStatus(MSG.unreadable, "is-warning");
    } else {
      clearStatus();
    }
    focusResults();
  }
  async function analyzeComparison(text, modelA, modelB) {
    hideResults();
    var token = runToken + 1;
    runToken = token;
    var controller = new AbortController();
    compareController = controller;
    comparison = { a: createComparisonSide(modelA), b: createComparisonSide(modelB) };
    setAnalyzing(true);
    els.resultsContent.hidden = true;
    try {
      var cachedA = cacheGet(modelA, text);
      var cachedB = cacheGet(modelB, text);
      if (cachedA) applyComparisonOutcome("a", { ok: true, data: cachedA.data, item: cachedA.item });
      if (cachedB) applyComparisonOutcome("b", { ok: true, data: cachedB.data, item: cachedB.item });
      var queue = [];
      if (!cachedA) queue.push("a");
      if (!cachedB) queue.push("b");
      if (!queue.length) {
        renderComparison();
        finishComparison();
        return;
      }
      if (queue.length === 2) {
        var readyA = stateOf(modelA) === "READY";
        var readyB = stateOf(modelB) === "READY";
        if (readyB && !readyA) queue = ["b", "a"];
      }
      if (cachedA || cachedB) renderComparison();
      for (var i = 0; i < queue.length; i += 1) {
        if (token !== runToken) return;
        var key = queue[i];
        var side = comparison[key];
        var model = side.model;
        setStatus("Đang chạy " + compareModelName(model) + " (" + (i + 1) + "/" + queue.length + ")…", "");
        var ready = await ensureReady(String(model.id));
        if (token !== runToken) return;
        var outcome = ready
          ? await fetchPrediction(String(model.id), text, controller.signal, timeoutForModel(model))
          : { ok: false, message: MSG.loadFailed, data: null };
        if (token !== runToken) return;
        if (outcome.ok) cacheSet(model, text, outcome.data, outcome.item);
        applyComparisonOutcome(key, outcome);
        renderComparison();
      }
      finishComparison();
    } catch (error) {
      if (token !== runToken) return;
      console.error("Không so sánh được:", error);
      setStatus(MSG.generic, "is-error");
      focusStatus();
    } finally {
      if (compareController === controller) compareController = null;
      if (token === runToken) setAnalyzing(false);
    }
  }

  async function analyze() {
    if (analyzing) return;
    var text = els.reviewInput.value;
    var modelId = selectedId;
    var model = findModel(modelId);
    if (!model) {
      setStatus("Vui lòng chọn mô hình.", "is-warning");
      els.modelSelect.focus();
      return;
    }
    if (!text.trim()) {
      setStatus("Vui lòng nhập đánh giá.", "is-warning");
      els.reviewInput.focus();
      return;
    }
    if (mode === "compare") {
      var secondary = findModel(secondaryId);
      if (!secondary || String(secondary.id) === String(model.id)) {
        setStatus(MSG.distinctModels, "is-warning");
        els.modelSelectSecondary.focus();
        return;
      }
      if (text.length > Math.min(maxCharsFor(model), maxCharsFor(secondary))) {
        setStatus(MSG.tooLong, "is-warning");
        els.reviewInput.focus();
        return;
      }
      await analyzeComparison(text, model, secondary);
      return;
    }
    if (text.length > maxCharsFor(model)) {
      setStatus(MSG.tooLong, "is-warning");
      els.reviewInput.focus();
      return;
    }
    var cached = cacheGet(model, text);
    if (cached) {
      renderResult(cached.data, cached.item, model);
      return;
    }
    var startToken = runToken;
    if (stateOf(model) !== "READY") {
      var ready = await ensureReady(modelId);
      if (startToken !== runToken) return;
      if (!ready) {
        if (selectedId === modelId) {
          setStatus(MSG.loadFailed, "is-error");
          focusStatus();
        }
        return;
      }
      if (selectedId !== modelId) return;
      model = findModel(modelId);
      if (stateOf(model) !== "READY") {
        setStatus(MSG.unavailable, "is-warning");
        focusStatus();
        return;
      }
    }
    if (selectedId !== modelId) return;
    await runPrediction(modelId, text, model);
  }

  function handleReviewInput() {
    stopComparisonForInputChange();
    refreshCount();
  }

  function init() {
    els = queryElements();
    els.resultsHeading.setAttribute("tabindex", "-1");
    els.resultStatus.setAttribute("tabindex", "-1");
    els.analyzeButton.addEventListener("click", analyze);
    els.cancelButton.addEventListener("click", cancelAnalysis);
    els.reviewInput.addEventListener("input", handleReviewInput);
    els.modelSelect.addEventListener("change", handleModelChange);
    els.modelSelectSecondary.addEventListener("change", handleSecondaryChange);
    els.swapModels.addEventListener("click", handleSwap);
    window.addEventListener("resize", handleClampResize);
    initModes();
    renderSamples();
    applyModelMeta(null);
    loadModels();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      try { init(); } catch (error) { console.error(error); throw error; }
    }, { once: true });
  } else {
    try { init(); } catch (error) { console.error(error); throw error; }
  }
})();