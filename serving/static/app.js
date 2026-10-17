(function () {
  'use strict';

  var ASPECTS = [
    { key: 'stayingpower', label: 'Độ lưu hương' },
    { key: 'texture', label: 'Kết cấu / chất son' },
    { key: 'smell', label: 'Mùi hương' },
    { key: 'price', label: 'Giá cả' },
    { key: 'colour', label: 'Màu sắc' },
    { key: 'shipping', label: 'Vận chuyển' },
    { key: 'packing', label: 'Đóng gói' }
  ];

  var LABEL_VI = {
    positive: 'Tích cực',
    negative: 'Tiêu cực',
    not_mentioned: 'Không nhắc tới',
    neutral: 'Trung lập',
    unknown: 'Không rõ'
  };

  var BADGE_CLASS = {
    positive: 'is-positive',
    negative: 'is-negative',
    not_mentioned: 'is-not-mentioned',
    neutral: 'is-neutral',
    unknown: 'is-unknown'
  };

  var SAMPLES = {
    positive: 'Son lên màu rất đẹp, chất son mịn màng và giữ màu lâu. Mùi thơm nhẹ dễ chịu, giá cả hợp lý, đóng gói chắc chắn và giao hàng nhanh.',
    negative: 'Son rất nhanh trôi, chất son khô và bết dính. Mùi hơi hắc khó chịu, giá lại quá đắt so với chất lượng. Hộp bị móp khi nhận và giao hàng chậm mấy ngày.',
    mixed: 'Màu son lên rất đẹp, chất son mịn, nhưng độ lưu hương kém nên nhanh trôi. Mùi thơm nhẹ dễ chịu, còn giá hơi cao và đóng gói tạm được.'
  };

  var MAX_ENCODER = 4000;
  var MAX_LLM = 6000;
  var TIMEOUT_ENCODER = 30000;
  var TIMEOUT_LLM = 240000;

  var STATUS_MESSAGE = {
    413: 'Văn bản quá dài. Rút ngắn văn bản rồi thử lại.',
    422: 'Dữ liệu không hợp lệ. Kiểm tra mô hình và văn bản nhập.',
    503: 'Mô hình chưa sẵn sàng hoặc dịch vụ đang bận. Thử lại sau.',
    504: 'Yêu cầu quá hạn. Thử lại hoặc chọn mô hình khác.'
  };

  var body = document.body;
  var state = {
    models: [],
    modelById: {},
    current: null,
    controller: null
  };

  var modelSelect = document.getElementById('model-select');
  var textarea = document.getElementById('input-text');
  var charCount = document.getElementById('char-count');
  var charLimit = document.getElementById('char-limit');
  var analyzeBtn = document.getElementById('analyze-btn');
  var errorBox = document.getElementById('error-box');
  var errorText = document.getElementById('error-text');
  var resultsSection = document.getElementById('results');
  var resultBody = document.getElementById('result-body');
  var metaBox = document.getElementById('meta');
  var rawDetails = document.getElementById('raw-details');
  var rawJson = document.getElementById('raw-json');

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }

  function showError(message) {
    errorText.textContent = message;
    errorBox.hidden = false;
  }

  function hideError() {
    errorBox.hidden = true;
    errorText.textContent = '';
  }

  function setLoading(loading) {
    analyzeBtn.disabled = loading;
    if (loading) {
      analyzeBtn.setAttribute('aria-disabled', 'true');
      analyzeBtn.textContent = 'Đang phân tích…';
    } else {
      analyzeBtn.removeAttribute('aria-disabled');
      analyzeBtn.textContent = 'Phân tích';
    }
  }

  function isLlm(model) {
    return !!(model && model.kind === 'llm');
  }

  function updateCharCount() {
    charCount.textContent = String(textarea.value.length);
  }

  function updateCharLimit() {
    var limit = isLlm(state.current) ? MAX_LLM : MAX_ENCODER;
    textarea.maxLength = limit;
    charLimit.textContent = String(limit);
    updateCharCount();
  }

  function buildOptions() {
    modelSelect.textContent = '';
    if (state.models.length === 0) {
      var empty = el('option', '', 'Không có mô hình khả dụng');
      empty.value = '';
      empty.disabled = true;
      empty.selected = true;
      modelSelect.appendChild(empty);
      modelSelect.disabled = true;
      return;
    }
    modelSelect.disabled = false;
    state.models.forEach(function (m) {
      var opt = el('option', '', m.id + (m.kind === 'llm' ? ' (LLM)' : ''));
      opt.value = m.id;
      modelSelect.appendChild(opt);
    });
    var hybrid = el('option', '', 'Hybrid (chưa hỗ trợ)');
    hybrid.value = 'hybrid';
    hybrid.disabled = true;
    hybrid.title = 'Chế độ Hybrid hiện chưa được hỗ trợ (HTTP 501).';
    modelSelect.appendChild(hybrid);
  }

  function selectDefault() {
    var configured = body.getAttribute('data-default-model') || '';
    var chosen = null;
    var i;
    if (configured) {
      for (i = 0; i < state.models.length; i++) {
        if (state.models[i].id === configured) { chosen = state.models[i]; break; }
      }
    }
    if (!chosen) {
      for (i = 0; i < state.models.length; i++) {
        if (state.models[i].id === 'cafebert_exp027') { chosen = state.models[i]; break; }
      }
    }
    if (!chosen) { chosen = state.models[0] || null; }
    state.current = chosen;
    if (chosen) { modelSelect.value = chosen.id; }
  }

  function onModelChange() {
    state.current = state.modelById[modelSelect.value] || null;
    updateCharLimit();
  }

  function loadModels() {
    fetch('/models', { headers: { Accept: 'application/json' } })
      .then(function (resp) {
        if (!resp.ok) { throw new Error('HTTP ' + resp.status); }
        return resp.json();
      })
      .then(function (data) {
        var all = (data && data.models) || [];
        state.modelById = {};
        state.models = [];
        all.forEach(function (m) {
          if (!m || !m.id) { return; }
          state.modelById[m.id] = m;
          if (m.enabled) { state.models.push(m); }
        });
        buildOptions();
        selectDefault();
        updateCharLimit();
      })
      .catch(function (err) {
        showError('Không tải được danh sách mô hình (' + err.message + '). Vui lòng thử lại.');
        modelSelect.disabled = true;
      });
  }

  function normalizeLabel(info) {
    var l = String(info.label || '').toLowerCase();
    if (Object.prototype.hasOwnProperty.call(LABEL_VI, l)) { return l; }
    return 'unknown';
  }

  function badgeTextFor(info, label) {
    if (info.label_vi) { return info.label_vi; }
    return LABEL_VI[label] || String(info.label || LABEL_VI.unknown);
  }

  function formatLatency(ms) {
    if (ms >= 1000) { return (ms / 1000).toFixed(2) + ' s'; }
    return String(Math.round(ms * 10) / 10) + ' ms';
  }

  function renderMeta(data) {
    var parts = [];
    if (data.model) { parts.push(data.model); }
    if (data.model_version) { parts.push(data.model_version); }
    if (typeof data.latency_ms === 'number') { parts.push(formatLatency(data.latency_ms)); }
    if (data.device) { parts.push(data.device); }
    if (typeof data.cache_hit === 'boolean') { parts.push(data.cache_hit ? 'cache hit' : 'cache miss'); }
    metaBox.textContent = parts.join(' · ');
  }

  function renderResult(data) {
    if (!data || !Array.isArray(data.results) || data.results.length === 0) {
      showError('Phản hồi không chứa kết quả.');
      return;
    }
    var result = data.results[0];
    var aspects = result.aspects || {};

    resultBody.textContent = '';

    ASPECTS.forEach(function (a) {
      var info = aspects[a.key] || {};
      var label = normalizeLabel(info);
      var badgeText = badgeTextFor(info, label);
      var cls = BADGE_CLASS[label] || BADGE_CLASS.unknown;

      var tr = el('tr');

      var tdAspect = el('td', 'aspect', a.label);
      tdAspect.setAttribute('data-label', 'Khía cạnh');

      var tdLabel = el('td', 'label-cell');
      tdLabel.setAttribute('data-label', 'Nhãn');
      tdLabel.appendChild(el('span', 'badge ' + cls, badgeText));

      var tdConf = el('td', 'conf-cell');
      tdConf.setAttribute('data-label', 'Độ tin cậy');
      if (typeof info.confidence === 'number' && isFinite(info.confidence)) {
        var pct = Math.round(info.confidence * 100);
        var wrap = el('div', 'conf-wrap');
        var track = el('div', 'conf-track');
        var bar = el('div', 'conf-bar ' + cls);
        bar.style.width = pct + '%';
        track.appendChild(bar);
        wrap.appendChild(track);
        wrap.appendChild(el('span', 'conf-text', pct + '%'));
        tdConf.appendChild(wrap);
      } else {
        tdConf.appendChild(el('span', 'conf-text', '—'));
      }

      tr.appendChild(tdAspect);
      tr.appendChild(tdLabel);
      tr.appendChild(tdConf);
      resultBody.appendChild(tr);
    });

    renderMeta(data);
    rawJson.textContent = JSON.stringify(data, null, 2);
    resultsSection.hidden = false;
  }

  function extractError(status, body) {
    var code = null;
    var message = null;
    if (body && typeof body === 'object') {
      if (body.error && typeof body.error === 'object') {
        code = body.error.code;
        message = body.error.message;
      }
      if (code === null || code === undefined) { code = body.code; }
      if (message === null || message === undefined) { message = body.message; }
      if (message === null || message === undefined) {
        if (typeof body.detail === 'string') { message = body.detail; }
        else if (body.detail !== undefined && body.detail !== null) { message = JSON.stringify(body.detail); }
      }
    }
    return { code: code, message: message };
  }

  function handleHttpError(status, body) {
    var ex = extractError(status, body);
    var parts = [];
    if (ex.code !== null && ex.code !== undefined) { parts.push('[' + ex.code + ']'); }
    parts.push(ex.message || STATUS_MESSAGE[status] || ('Lỗi máy chủ (HTTP ' + status + ').'));
    showError(parts.join(' '));
  }

  function predict() {
    var text = textarea.value.trim();
    if (!text) {
      showError('Vui lòng nhập văn bản cần phân tích.');
      textarea.focus();
      return;
    }
    var model = state.current;
    if (!model) {
      showError('Chưa chọn mô hình. Vui lòng tải lại danh sách mô hình.');
      return;
    }

    hideError();
    resultsSection.hidden = true;
    resultsSection.setAttribute('aria-busy', 'true');
    metaBox.textContent = '';
    rawJson.textContent = '';
    rawDetails.open = false;
    setLoading(true);

    var timeout = isLlm(model) ? TIMEOUT_LLM : TIMEOUT_ENCODER;
    var controller = new AbortController();
    state.controller = controller;
    var timer = setTimeout(function () { controller.abort(); }, timeout);

    function finish() {
      clearTimeout(timer);
      state.controller = null;
      setLoading(false);
      resultsSection.setAttribute('aria-busy', 'false');
    }

    fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ model: model.id, text: text }),
      signal: controller.signal
    })
      .then(function (resp) {
        return resp.json().catch(function () { return null; }).then(function (body) {
          return { ok: resp.ok, status: resp.status, body: body };
        });
      })
      .then(function (res) {
        if (!res.ok) { handleHttpError(res.status, res.body); return; }
        renderResult(res.body);
      })
      .catch(function (err) {
        if (err && err.name === 'AbortError') {
          showError('Yêu cầu quá thời gian chờ (' + Math.round(timeout / 1000) + 's). Thử lại hoặc chọn mô hình khác.');
        } else {
          showError('Không gửi được yêu cầu: ' + (err && err.message ? err.message : err));
        }
      })
      .then(finish);
  }

  modelSelect.addEventListener('change', onModelChange);
  analyzeBtn.addEventListener('click', predict);
  textarea.addEventListener('input', updateCharCount);

  var sampleButtons = document.querySelectorAll('.sample');
  sampleButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var key = btn.getAttribute('data-sample');
      textarea.value = SAMPLES[key] || '';
      updateCharCount();
      textarea.focus();
    });
  });

  updateCharCount();
  loadModels();
})();