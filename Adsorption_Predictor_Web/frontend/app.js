/* ==========================================================================
 * 生物炭吸附性能预测器 · 前端交互
 *
 * 主题
 *   离线预测器的浏览器端：负责收集表单输入、调用本地 Python 接口、渲染结果。
 *   模型加载、特征工程、标准化与预测全部由 Python 侧完成，本文件不做任何数值计算。
 *
 * 结构
 *   ① 状态与工具   全局状态、DOM 取值/赋值、格式化
 *   ② 元数据渲染   拉 /api/meta，渲染目标切换、模型卡片、字段表单、示例
 *   ③ 表单行为     污染物联动分子描述符、填充典型值、重置、载入示例
 *   ④ 预测与渲染   调 /api/predict 与 /api/compare，画结果、对比表、特征明细
 *   ⑤ 入口         init：绑定事件并首次渲染
 *
 * 调用树
 *   init
 *   ├── loadMeta
 *   │   ├── renderTargetSwitch
 *   │   ├── renderModelList
 *   │   ├── renderPollutantSelect
 *   │   ├── renderFieldGroups
 *   │   └── renderSamples
 *   ├── bindEvents
 *   └── onPollutantChange            （框架调用：select 的 change 事件）
 *       └── applyDescriptors
 *
 *   runPrediction                      （框架调用：按钮点击）
 *   ├── collectInputs
 *   ├── requestPrediction              → POST /api/predict
 *   ├── requestComparison              → POST /api/compare
 *   └── renderResult
 *       ├── renderPrediction
 *       ├── renderTruthCompare
 *       ├── renderCompareTable
 *       └── renderFeatureRow
 *
 * 数据流
 *   /api/meta → 表单 DOM → collectInputs → JSON
 *     → /api/predict（单模型）与 /api/compare（多模型）→ 结果 DOM
 * ========================================================================== */

(function () {
  'use strict';

  /* ---------- ① 状态与工具 ---------- */

  var META = null;                 // /api/meta 的返回
  var state = {
    target: 'amount',              // 当前目标变量
    modelKey: null,                // 当前选中的模型
    truth: null                    // 载入示例时带的实测值，用于对照
  };

  function $(id) { return document.getElementById(id); }

  function create(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = text;
    return el;
  }

  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  function fmt(value, digits) {
    if (value === null || value === undefined || isNaN(value)) return '—';
    var d = (digits === undefined) ? 3 : digits;
    return Number(value).toFixed(d);
  }

  function showError(message) {
    var box = $('error-box');
    box.textContent = message;
    box.classList.remove('hidden');
  }

  function hideError() { $('error-box').classList.add('hidden'); }

  /* ---------- ② 元数据渲染 ---------- */

  function loadMeta() {
    return fetch('/api/meta')
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '元数据读取失败');
        META = data;
        $('dataset-line').textContent =
          '训练数据：' + (data.source || '未知') +
          ' · 分子描述符可由污染物唯一确定：' + (data.descriptorsConstant ? '是' : '否');
        renderTargetSwitch();
        renderModelList();
        renderPollutantSelect();
        renderFieldGroups();
        renderSamples();
        selectDefaultModel();
        handleAutorun();
      })
      .catch(function (err) {
        showError('无法连接本地预测服务：' + err.message +
                  '。请确认 start.bat 已在运行。');
      });
  }

  /* 演示入口：地址后加 ?autorun=1 时自动载入首条示例并预测。
     可选参数：sample=<污染物名> 指定示例，target=capacity 切到吸附容量。
     用途一是给演示/截图一个直达链接，二是让自动化验证能覆盖完整交互链路。 */
  function handleAutorun() {
    var params = new URLSearchParams(window.location.search);
    if (params.get('autorun') !== '1') return;

    var wantedTarget = params.get('target');
    if (wantedTarget && META.targets[wantedTarget] && wantedTarget !== state.target) {
      state.target = wantedTarget;
      Array.prototype.forEach.call($('target-switch').children, function (child) {
        child.classList.toggle('active', child.dataset.target === wantedTarget);
      });
      renderModelList();
      selectDefaultModel();
    }

    if (META.samples && META.samples.length) {
      var wantedSample = params.get('sample');
      var sample = META.samples[0];
      if (wantedSample) {
        META.samples.forEach(function (item) {
          if (item.pollutant === wantedSample) sample = item;
        });
      }
      loadSample(sample);
    }
    runPrediction();
  }

  function renderTargetSwitch() {
    var box = $('target-switch');
    clear(box);
    Object.keys(META.targets).forEach(function (key) {
      var target = META.targets[key];
      var btn = create('button', 'target-btn', target.label);
      btn.type = 'button';
      btn.dataset.target = key;
      if (key === state.target) btn.classList.add('active');
      btn.addEventListener('click', function () {
        state.target = key;
        state.truth = null;
        Array.prototype.forEach.call(box.children, function (child) {
          child.classList.toggle('active', child.dataset.target === key);
        });
        renderModelList();
        selectDefaultModel();
        hideTruthCompare();
      });
      box.appendChild(btn);
    });
  }

  function modelsForTarget(target) {
    return META.models.filter(function (m) { return m.target === target; });
  }

  function renderModelList() {
    var box = $('model-list');
    clear(box);
    var list = modelsForTarget(state.target);
    $('model-hint').textContent = list.length + ' 个可用模型';

    list.forEach(function (model) {
      var card = create('div', 'model-card');
      card.dataset.key = model.key;

      var main = create('div', 'model-card-main');
      main.appendChild(create('span', 'model-card-name', model.label));
      main.appendChild(create('span', 'model-card-sub',
        model.family + ' · ' + model.featureSetLabel));
      main.appendChild(create('span', 'model-card-sub dim',
        '精度口径：' + (model.metrics.protocol || '未标注')));

      var score = create('div', 'model-card-score');
      score.appendChild(document.createTextNode('R² ' + fmt(model.metrics.r2, 4)));
      score.appendChild(create('small', null, ' / RMSE ' + fmt(model.metrics.rmse, 2)));

      card.appendChild(main);
      card.appendChild(score);
      card.addEventListener('click', function () {
        state.modelKey = model.key;
        highlightModel();
      });
      box.appendChild(card);
    });
  }

  function highlightModel() {
    Array.prototype.forEach.call($('model-list').children, function (card) {
      card.classList.toggle('active', card.dataset.key === state.modelKey);
    });
    var spec = currentModel();
    $('model-note').textContent = spec ? (spec.note || '') : '';
  }

  function currentModel() {
    if (!META) return null;
    var found = null;
    META.models.forEach(function (m) { if (m.key === state.modelKey) found = m; });
    return found;
  }

  function selectDefaultModel() {
    var list = modelsForTarget(state.target);
    if (!list.length) { state.modelKey = null; return; }
    // 默认模型由注册表显式声明，不按 R² 取最大：
    // 各模型的 R² 评估口径不同（5 折 CV / 80/20 留出），比大小会误导。
    var chosen = null;
    list.forEach(function (m) { if (m.isDefault) chosen = m; });
    state.modelKey = (chosen || list[0]).key;
    highlightModel();
  }

  function renderPollutantSelect() {
    var select = $('pollutant-select');
    clear(select);
    META.pollutants.forEach(function (item) {
      var option = create('option', null, item.name + '（' + item.nRecords + ' 条记录）');
      option.value = item.name;
      select.appendChild(option);
    });
    applyDescriptors();
  }

  function renderFieldGroups() {
    var host = $('dynamic-groups');
    clear(host);

    host.appendChild(buildGroup('生物炭性质', META.groups.biochar.fields, false));
    host.appendChild(buildGroup('吸附条件', META.groups.condition.fields, false));

    // 分子描述符由污染物自动带出，收进折叠区
    var details = create('details', 'advanced');
    details.appendChild(create('summary', null,
      '分子描述符（随污染物自动带出，可手动覆盖）'));
    details.appendChild(buildGrid(META.groups.pollutant.fields));
    host.appendChild(details);
  }

  function buildGroup(title, fields, isAdvanced) {
    var wrapper = create('div', 'field-group');
    if (isAdvanced) {
      wrapper.classList.add('advanced-wrap');
    } else {
      var head = create('div', 'group-head');
      head.appendChild(create('span', 'group-name', title));
      wrapper.appendChild(head);
    }
    wrapper.appendChild(buildGrid(fields));
    return wrapper;
  }

  function buildGrid(fields) {
    var grid = create('div', 'field-grid');
    fields.forEach(function (name) {
      var info = META.fields[name];
      if (!info) return;

      var label = create('label', 'field');
      var labelRow = create('span', 'field-label');
      labelRow.appendChild(create('span', null, info.label));
      labelRow.appendChild(create('span', 'unit', info.unit || ''));
      label.appendChild(labelRow);

      var input = document.createElement('input');
      input.type = 'number';
      input.step = 'any';
      input.id = 'input-' + cssId(name);
      input.dataset.field = name;
      input.placeholder = '典型值 ' + fmt(info.median, 4);
      // 允许范围用后端真正接受的区间，与校验口径一致；下方的提示仍展示数据实际范围
      input.min = (info.acceptLow !== undefined) ? info.acceptLow : info.min;
      input.max = (info.acceptHigh !== undefined) ? info.acceptHigh : info.max;
      label.appendChild(input);

      var tip = create('span', 'field-tip',
        '数据范围 ' + fmt(info.min, 3) + ' ~ ' + fmt(info.max, 3));
      label.appendChild(tip);

      grid.appendChild(label);
    });
    return grid;
  }

  function cssId(name) {
    return name.replace(/[^A-Za-z0-9]/g, '_');
  }

  function renderSamples() {
    var box = $('sample-list');
    clear(box);
    (META.samples || []).forEach(function (sample) {
      var chip = create('button', 'sample-chip', sample.pollutant);
      chip.type = 'button';
      chip.title = sample.id;
      chip.addEventListener('click', function () { loadSample(sample); });
      box.appendChild(chip);
    });
  }

  /* ---------- ③ 表单行为 ---------- */

  function applyDescriptors() {
    if (!META || !META.descriptorsConstant) return;
    var selected = $('pollutant-select').value;
    var entry = null;
    META.pollutants.forEach(function (item) {
      if (item.name === selected) entry = item;
    });
    if (!entry) return;
    META.molecularDescriptors.forEach(function (field) {
      var input = $('input-' + cssId(field));
      if (input && entry.descriptors[field] !== null && entry.descriptors[field] !== undefined) {
        input.value = entry.descriptors[field];
      }
    });
  }

  function fillTypical() {
    META.groups.biochar.fields.concat(META.groups.condition.fields).forEach(function (field) {
      var input = $('input-' + cssId(field));
      if (input && !input.value) {
        input.value = Number(META.typical[field]).toFixed(4);
      }
    });
    applyDescriptors();
  }

  function resetForm() {
    document.querySelectorAll('#form-panel input[data-field]').forEach(function (input) {
      input.value = '';
      input.classList.remove('invalid');
    });
    state.truth = null;
    hideTruthCompare();
    $('result-body').classList.add('hidden');
    $('result-placeholder').classList.remove('hidden');
    hideError();
  }

  function loadSample(sample) {
    document.querySelectorAll('#form-panel input[data-field]').forEach(function (input) {
      var value = sample.inputs[input.dataset.field];
      input.value = (value === null || value === undefined) ? '' : value;
      input.classList.remove('invalid');
    });
    $('pollutant-select').value = sample.pollutant;
    applyDescriptors();
    // 描述符仍以数据集实际值为准（示例可能来自缺失描述的记录）
    META.molecularDescriptors.forEach(function (field) {
      var value = sample.inputs[field];
      var input = $('input-' + cssId(field));
      if (input && value !== null && value !== undefined) input.value = value;
    });
    state.truth = sample.truth;
    hideError();
  }

  function collectInputs() {
    var inputs = { Pollutant: $('pollutant-select').value };
    var missing = [];
    var invalid = [];
    document.querySelectorAll('#form-panel input[data-field]').forEach(function (input) {
      var raw = input.value.trim();
      if (raw === '') {
        if (!input.classList.contains('advanced-optional')) missing.push(input.dataset.field);
        input.classList.add('invalid');
        return;
      }
      var num = Number(raw);
      if (!isFinite(num)) { invalid.push(input.dataset.field); input.classList.add('invalid'); return; }
      input.classList.remove('invalid');
      inputs[input.dataset.field] = num;
    });
    return { inputs: inputs, missing: missing, invalid: invalid };
  }

  /* ---------- ④ 预测与渲染 ---------- */

  function requestPrediction(modelKey, inputs) {
    return fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modelKey: modelKey, inputs: inputs })
    }).then(function (res) { return res.json(); });
  }

  function requestComparison(target, inputs) {
    return fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: target, inputs: inputs })
    }).then(function (res) { return res.json(); });
  }

  function runPrediction() {
    hideError();
    if (!state.modelKey) { showError('请先选择模型。'); return; }

    var collected = collectInputs();
    if (collected.missing.length) {
      showError('以下字段未填写：' + collected.missing.join('、'));
      return;
    }
    if (collected.invalid.length) {
      showError('以下字段不是有效数字：' + collected.invalid.join('、'));
      return;
    }

    var button = $('predict-btn');
    button.disabled = true;
    button.textContent = '预测中…';

    Promise.all([
      requestPrediction(state.modelKey, collected.inputs),
      requestComparison(state.target, collected.inputs)
    ]).then(function (responses) {
      var single = responses[0];
      var compare = responses[1];
      if (!single.ok) { showError(single.error || '预测失败'); return; }
      renderResult(single, compare);
    }).catch(function (err) {
      showError('请求失败：' + err.message);
    }).then(function () {
      button.disabled = false;
      button.textContent = '开始预测';
    });
  }

  function renderResult(single, compare) {
    $('result-placeholder').classList.add('hidden');
    $('result-body').classList.remove('hidden');

    renderPrediction(single);
    renderTruthCompare(single);
    renderCompareTable(compare, single.modelKey);
    renderFeatureRow(single.featureRow);
    highlightModel();
  }

  function renderPrediction(single) {
    $('prediction-label').textContent =
      single.targetLabel + ' · ' + single.modelLabel;
    $('prediction-number').textContent = fmt(single.prediction, 3);
    $('prediction-unit').textContent = single.unit;
    $('prediction-sub').textContent =
      '该模型测试集 R² = ' + fmt(single.metrics.r2, 4) +
      '，RMSE = ' + fmt(single.metrics.rmse, 2) + ' ' + single.unit +
      '（口径：' + (single.metrics.protocol || '未标注') +
      '；来源：' + single.metrics.source + '）' +
      (single.standardized ? ' · 输入已标准化' : ' · 输入未标准化');
  }

  function renderTruthCompare(single) {
    var box = $('truth-compare');
    clear(box);
    if (!state.truth) { box.classList.add('hidden'); return; }

    var truth = state.truth[single.target];
    if (truth === null || truth === undefined) { box.classList.add('hidden'); return; }

    var diff = single.prediction - truth;
    var row1 = create('div', 'truth-row');
    row1.appendChild(create('span', null, '该记录的实测值'));
    row1.appendChild(create('b', null, fmt(truth, 3) + ' ' + single.unit));
    var row2 = create('div', 'truth-row');
    row2.appendChild(create('span', null, '偏差（预测 − 实测）'));
    row2.appendChild(create('b', null, (diff >= 0 ? '+' : '') + fmt(diff, 3) +
      ' ' + single.unit));
    box.appendChild(row1);
    box.appendChild(row2);
    box.classList.remove('hidden');
  }

  function hideTruthCompare() { $('truth-compare').classList.add('hidden'); }

  function renderCompareTable(compare, selectedKey) {
    var host = $('compare-table');
    clear(host);
    if (!compare || !compare.ok) {
      host.appendChild(create('p', 'dim', '多模型对比不可用。'));
      return;
    }

    var table = create('table', 'cmp');
    var thead = create('thead');
    var headRow = create('tr');
    ['模型', '特征集', 'R²', '评估口径', '预测值 (' + compare.unit + ')'].forEach(function (text, i) {
      var th = create('th', i >= 2 ? 'num' : null, text);
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    // 保持注册表顺序，不按 R² 重排：口径不同，排序会暗示"可以比大小"
    var rows = compare.results;

    var tbody = create('tbody');
    rows.forEach(function (item) {
      var tr = create('tr');
      if (item.modelKey === selectedKey) tr.classList.add('is-selected');

      var nameCell = create('td');
      nameCell.appendChild(document.createTextNode(item.label));
      if (item.modelKey === selectedKey) {
        nameCell.appendChild(document.createTextNode(' '));
        nameCell.appendChild(create('span', 'badge', '当前'));
      }
      tr.appendChild(nameCell);

      tr.appendChild(create('td', null, item.featureSetShort || item.featureSetLabel));

      var r2Cell = create('td', 'num');
      r2Cell.appendChild(document.createTextNode(fmt(item.metrics.r2, 4)));
      tr.appendChild(r2Cell);

      // 口径不同则 R² 不可直接横比，这里显式列出，避免误读
      tr.appendChild(create('td', null, item.metrics.protocol || '未标注'));

      tr.appendChild(create('td', 'num',
        item.ok ? fmt(item.prediction, 3) : '不可用'));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    host.appendChild(table);

    var protocols = [];
    rows.forEach(function (item) {
      var p = item.metrics.protocol || '未标注';
      if (protocols.indexOf(p) < 0) protocols.push(p);
    });
    if (protocols.length > 1) {
      host.appendChild(create('p', 'spread-line',
        '注意：各模型的 R² 评估口径不完全相同（' + protocols.join(' / ') +
        '），不宜直接横向比较；预测值本身由同一份输入得出，可直接对比。'));
    }

    if (compare.spread) {
      host.appendChild(create('p', 'spread-line',
        '各模型预测区间 ' + fmt(compare.spread.min, 2) + ' ~ ' +
        fmt(compare.spread.max, 2) + ' ' + compare.unit +
        '（极差 ' + fmt(compare.spread.range, 2) + '）'));
    }
  }

  function renderFeatureRow(featureRow) {
    var host = $('feature-row');
    clear(host);
    if (!featureRow) return;
    var table = create('table', 'feat');
    featureRow.forEach(function (item) {
      var tr = create('tr');
      tr.appendChild(create('td', null, item.name));
      tr.appendChild(create('td', null, fmt(item.value, 4)));
      table.appendChild(tr);
    });
    host.appendChild(table);
  }

  /* ---------- ⑤ 入口 ---------- */

  function bindEvents() {
    $('pollutant-select').addEventListener('change', applyDescriptors);
    $('predict-btn').addEventListener('click', runPrediction);
    $('typical-btn').addEventListener('click', fillTypical);
    $('reset-btn').addEventListener('click', resetForm);
  }

  function init() {
    bindEvents();
    loadMeta();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
