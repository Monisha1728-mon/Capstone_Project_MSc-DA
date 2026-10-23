(() => {
  const records = Array.isArray(window.AT_RISK_RECORDS)
    ? window.AT_RISK_RECORDS
    : [];
  const colors = {
    teal: "#0d8078",
    blue: "#4269e1",
    red: "#d85855",
    amber: "#d48a18",
    green: "#2aa879",
    purple: "#8565c7",
    gray: "#9aa7b5",
    muted: "#728095",
    grid: "#edf1f4",
  };
  const charts = {};
  const defaults = [
    "trendChart",
    "riskChart",
    "statusChart",
    "disabilityChart",
    "settingChart",
    "settingRiskChart",
    "barrierChart",
    "conditionChart",
    "deviceNeedChart",
  ];
  const layoutKey = "at-risk-dashboard-layout-v3";
  const els = {
    risk: document.getElementById("riskSlicer"),
    status: document.getElementById("statusSlicer"),
    disability: document.getElementById("disabilitySlicer"),
    setting: document.getElementById("settingSlicer"),
  };
  const clean = (value) =>
    String(value ?? "Unknown")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  const filtered = () =>
    records.filter(
      (record) =>
        (els.risk.value === "all" || record.risk === els.risk.value) &&
        (els.status.value === "all" || record.status === els.status.value) &&
        (els.disability.value === "all" ||
          record.disability === els.disability.value) &&
        (els.setting.value === "all" || record.setting === els.setting.value),
    );
  const countBy = (items, key) =>
    items.reduce((result, record) => {
      const value = clean(record[key]);
      result[value] = (result[value] || 0) + 1;
      return result;
    }, {});
  const base = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 350 },
    plugins: {
      legend: { display: false },
      tooltip: { backgroundColor: "#17212f", padding: 10, cornerRadius: 8 },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: colors.muted, font: { size: 10 } },
      },
      y: {
        grid: { color: colors.grid },
        ticks: { color: colors.muted, font: { size: 10 }, precision: 0 },
        beginAtZero: true,
      },
    },
  };
  const axis = (x, y) => ({
    scales: {
      x: {
        ...base.scales.x,
        title: {
          display: true,
          text: x,
          color: colors.muted,
          font: { size: 10, weight: "600" },
        },
      },
      y: {
        ...base.scales.y,
        title: {
          display: true,
          text: y,
          color: colors.muted,
          font: { size: 10, weight: "600" },
        },
      },
    },
  });
  const make = (id, type, data, options = {}) => {
    const node = document.getElementById(id);
    if (!node || !window.Chart) return;
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(node, {
      type,
      data,
      options: { ...base, ...options },
    });
  };
  const months = (items) =>
    items.reduce((result, record) => {
      const month = (record.date || "").slice(0, 7) || "Unknown";
      result[month] = (result[month] || 0) + 1;
      return result;
    }, {});
  const labelsFor = (items, field) =>
    Object.keys(countBy(items, field))
      .sort((a, b) => countBy(items, field)[b] - countBy(items, field)[a])
      .slice(0, 8);
  const numericCount = (items, field) =>
    items.filter((record) => Number(record[field]) === 1).length;
  const showEmpty = (id, hasData) => {
    const card = document.querySelector(`[data-chart-id="${id}"]`);
    const empty = card?.querySelector(".chart-empty");
    if (empty) empty.classList.toggle("visible", !hasData);
  };
  const setText = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  };

  function renderFixed(items) {
    const risk = countBy(items, "risk"),
      status = countBy(items, "status"),
      disability = countBy(items, "disability"),
      setting = countBy(items, "setting");
    const high = risk.High || 0,
      medium = risk.Medium || 0,
      low = risk.Low || 0;
    const pending = items.filter(
      (record) => record.status === "submitted",
    ).length;
    const reviewed = items.filter(
      (record) => record.status === "predicted",
    ).length;
    const notApplicable = items.filter(
      (record) => record.status === "not_applicable",
    ).length;
    setText("kpiTotal", items.length);
    setText("kpiHigh", high);
    setText("kpiMedium", medium);
    setText("kpiLow", low);
    setText("kpiPending", pending);
    setText("kpiReviewed", reviewed);
    setText("statusPending", pending);
    setText("statusReviewed", reviewed);
    setText("statusNA", notApplicable);
    setText("priorityCount", high);
    const total = pending + reviewed + notApplicable;
    const completion = total ? Math.round((reviewed / total) * 100) : 0;
    setText("completionRate", `${completion}%`);
    setText(
      "completionText",
      total
        ? `${reviewed} of ${total} feedback entries have a completed review.`
        : "No feedback matches the current filters.",
    );
    const fill = document.getElementById("completionFill");
    if (fill) fill.style.width = `${completion}%`;
    const monthData = months(items),
      monthLabels = Object.keys(monthData).sort();
    make(
      "trendChart",
      "line",
      {
        labels: monthLabels.length ? monthLabels : ["No feedback"],
        datasets: [
          {
            label: "Feedback entries",
            data: monthLabels.length
              ? monthLabels.map((label) => monthData[label])
              : [0],
            borderColor: colors.teal,
            backgroundColor: "rgba(13,128,120,.14)",
            fill: true,
            tension: 0.38,
            pointRadius: 4,
          },
        ],
      },
      axis("Month received", "Number of feedback entries"),
    );
    showEmpty("trendChart", items.length > 0);
    make(
      "riskChart",
      "doughnut",
      {
        labels: ["High risk", "Medium risk", "Low risk"],
        datasets: [
          {
            label: "Reviewed feedback",
            data: [high, medium, low],
            backgroundColor: [colors.red, colors.amber, colors.green],
            borderWidth: 0,
            hoverOffset: 7,
          },
        ],
      },
      {
        cutout: "68%",
        plugins: { legend: { display: true, position: "bottom" } },
      },
    );
    showEmpty("riskChart", reviewed > 0);
    const disabilityLabels = labelsFor(items, "disability");
    make(
      "disabilityChart",
      "bar",
      {
        labels: disabilityLabels.length ? disabilityLabels : ["No data"],
        datasets: [
          {
            label: "Feedback entries",
            data: disabilityLabels.map((label) => disability[label]),
            backgroundColor: colors.blue,
            borderRadius: 7,
            barThickness: 18,
          },
        ],
      },
      {
        indexAxis: "y",
        ...axis("Number of feedback entries", "Disability type"),
      },
    );
    showEmpty("disabilityChart", disabilityLabels.length > 0);
    const settingLabels = Object.keys(setting);
    make(
      "settingChart",
      "polarArea",
      {
        labels: settingLabels.length ? settingLabels : ["No data"],
        datasets: [
          {
            label: "Feedback entries",
            data: settingLabels.length
              ? settingLabels.map((label) => setting[label])
              : [0],
            backgroundColor: [
              colors.teal,
              colors.blue,
              colors.amber,
              colors.purple,
              colors.red,
            ],
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      {
        scales: {
          r: {
            beginAtZero: true,
            ticks: { precision: 0, color: colors.muted },
            grid: { color: colors.grid },
          },
        },
        plugins: { legend: { display: true, position: "bottom" } },
      },
    );
    showEmpty("settingChart", settingLabels.length > 0);
    const settingRisk = ["High", "Medium", "Low"].map((riskName) => ({
      label: riskName,
      data: settingLabels.map(
        (label) =>
          items.filter(
            (record) =>
              clean(record.setting) === label && record.risk === riskName,
          ).length,
      ),
      backgroundColor:
        riskName === "High"
          ? colors.red
          : riskName === "Medium"
            ? colors.amber
            : colors.green,
    }));
    make(
      "settingRiskChart",
      "bar",
      {
        labels: settingLabels.length ? settingLabels : ["No data"],
        datasets: settingRisk,
      },
      {
        scales: {
          x: {
            stacked: true,
            title: { display: true, text: "Service setting" },
          },
          y: {
            stacked: true,
            beginAtZero: true,
            title: { display: true, text: "Number of feedback entries" },
          },
        },
        plugins: { legend: { display: true, position: "bottom" } },
      },
    );
    showEmpty("settingRiskChart", reviewed > 0);
    make(
      "statusChart",
      "pie",
      {
        labels: ["Pending review", "Reviewed", "Not applicable"],
        datasets: [
          {
            label: "Feedback entries",
            data: [pending, reviewed, notApplicable],
            backgroundColor: [colors.blue, colors.teal, colors.gray],
            borderWidth: 0,
          },
        ],
      },
      { plugins: { legend: { display: true, position: "bottom" } } },
    );
    showEmpty("statusChart", total > 0);
    const barriers = {
      Financial: numericCount(items, "financial"),
      Access: numericCount(items, "access"),
      Distance: numericCount(items, "distance"),
      "Unmet need": numericCount(items, "unmet"),
      "Device damage": numericCount(items, "broken"),
    };
    make(
      "barrierChart",
      "radar",
      {
        labels: Object.keys(barriers),
        datasets: [
          {
            label: "Feedback entries",
            data: Object.values(barriers),
            borderColor: colors.purple,
            backgroundColor: "rgba(133,101,199,.18)",
            pointBackgroundColor: colors.purple,
          },
        ],
      },
      {
        scales: {
          r: {
            beginAtZero: true,
            ticks: { precision: 0 },
            grid: { color: colors.grid },
          },
        },
        plugins: { legend: { display: true, position: "bottom" } },
      },
    );
    showEmpty("barrierChart", items.length > 0);
    const conditions = [
      items.filter((record) => record.broken === 1).length,
      items.filter((record) => record.broken !== 1).length,
    ];
    make(
      "conditionChart",
      "bar",
      {
        labels: ["Damaged / broken", "No damage reported"],
        datasets: [
          {
            label: "Feedback entries",
            data: conditions,
            backgroundColor: [colors.red, colors.green],
            borderRadius: 7,
            barThickness: 30,
          },
        ],
      },
      axis("Device condition", "Number of feedback entries"),
    );
    showEmpty("conditionChart", items.length > 0);
    const devices = countBy(items, "device"),
      deviceLabels = Object.keys(devices).slice(0, 7);
    make(
      "deviceNeedChart",
      "bar",
      {
        labels: deviceLabels.length ? deviceLabels : ["No data"],
        datasets: [
          {
            label: "Feedback entries",
            data: deviceLabels.map((label) => devices[label]),
            backgroundColor: colors.purple,
            borderRadius: 7,
            barThickness: 18,
          },
        ],
      },
      {
        indexAxis: "y",
        ...axis("Number of feedback entries", "Device requested"),
      },
    );
    showEmpty("deviceNeedChart", deviceLabels.length > 0);
    const title = document.getElementById("insightTitle"),
      text = document.getElementById("insightText");
    if (high) {
      title.textContent = "Priority insight";
      text.textContent = `${high} high-risk ${high === 1 ? "entry needs" : "entries need"} early follow-up.`;
    } else if (pending) {
      title.textContent = "Review queue insight";
      text.textContent = `${pending} feedback ${pending === 1 ? "entry is" : "entries are"} waiting for administrator review.`;
    } else if (!items.length) {
      title.textContent = "No matching feedback";
      text.textContent =
        "Try resetting the filters or open View submissions to see the full queue.";
    } else {
      title.textContent = "Actionable insight";
      text.textContent =
        "No high-risk entries in this view. Continue routine monitoring and follow-up.";
    }
  }

  function renderCustom(card, items) {
    const config = JSON.parse(card.dataset.config || "{}");
    const field = config.field || "setting";
    const counts = countBy(items, field);
    const labels = Object.keys(counts).slice(0, 10);
    const palette = [
      colors.teal,
      colors.blue,
      colors.amber,
      colors.purple,
      colors.red,
      colors.green,
    ];
    const data = labels.length ? labels.map((label) => counts[label]) : [0];
    const type = config.type || "bar";
    const options = ["bar", "line"].includes(type)
      ? axis("Selected category", "Number of feedback entries")
      : { plugins: { legend: { display: true, position: "bottom" } } };
    if (type === "bar") options.indexAxis = config.horizontal ? "y" : "x";
    make(
      config.id,
      type,
      {
        labels: labels.length ? labels : ["No data"],
        datasets: [
          {
            label: "Feedback entries",
            data,
            backgroundColor: palette,
            borderColor: colors.teal,
            borderWidth: type === "line" ? 2 : 0,
            fill: type === "line" ? true : false,
            tension: 0.35,
            borderRadius: type === "bar" ? 7 : 0,
          },
        ],
      },
      options,
    );
    showEmpty(config.id, items.length > 0 && labels.length > 0);
  }

  function readLayout() {
    try {
      return (
        JSON.parse(localStorage.getItem(layoutKey)) || {
          order: defaults,
          hidden: [],
          custom: [],
        }
      );
    } catch {
      return { order: defaults, hidden: [], custom: [] };
    }
  }
  function saveLayout(layout) {
    localStorage.setItem(layoutKey, JSON.stringify(layout));
    const saved = document.getElementById("layoutSaved");
    if (saved) {
      saved.innerHTML = '<i class="fa-solid fa-check"></i> Layout saved';
      window.setTimeout(() => {
        saved.innerHTML =
          '<i class="fa-solid fa-cloud-arrow-up"></i> Layout saved';
      }, 1000);
    }
  }
  function customCard(config) {
    const article = document.createElement("article");
    article.className = `visual-card chart-card custom-chart-card ${config.wide ? "visual-wide" : ""}`;
    article.draggable = true;
    article.dataset.chartId = config.id;
    article.dataset.config = JSON.stringify(config);
    article.innerHTML = `<div class="visual-head"><div><span class="drag-handle"><i class="fa-solid fa-grip-vertical"></i></span><span class="section-kicker">Custom view</span><h2>${config.title}</h2></div><button class="chart-remove" title="Remove this chart"><i class="fa-solid fa-xmark"></i></button></div><div class="chart-box"><canvas id="${config.id}"></canvas><div class="chart-empty">No records match this view.</div></div><p class="chart-axis-note"><b>Group:</b> ${clean(config.field)} &nbsp; <b>Measure:</b> Number of feedback entries</p>`;
    return article;
  }
  function applyLayout() {
    const layout = readLayout();
    const grid = document.getElementById("chartGrid");
    if (!grid) return;
    document
      .querySelectorAll(".custom-chart-card")
      .forEach((card) => card.remove());
    layout.custom.forEach((config) => grid.appendChild(customCard(config)));
    layout.hidden.forEach((id) =>
      document.querySelector(`[data-chart-id="${id}"]`)?.remove(),
    );
    layout.order
      .concat(layout.custom.map((config) => config.id))
      .forEach((id) => {
        const card = grid.querySelector(`[data-chart-id="${id}"]`);
        if (card) grid.appendChild(card);
      });
    bindCardActions();
  }
  function bindCardActions() {
    document.querySelectorAll(".chart-card").forEach((card) => {
      card.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/plain", card.dataset.chartId);
        card.classList.add("dragging");
      });
      card.addEventListener("dragend", () => card.classList.remove("dragging"));
      card.addEventListener("dragover", (event) => event.preventDefault());
      card.addEventListener("drop", (event) => {
        event.preventDefault();
        const dragged = document.querySelector(
          `[data-chart-id="${event.dataTransfer.getData("text/plain")}"]`,
        );
        if (dragged && dragged !== card) {
          const rect = card.getBoundingClientRect();
          card.parentNode.insertBefore(
            dragged,
            event.clientY < rect.top + rect.height / 2
              ? card
              : card.nextSibling,
          );
          persistOrder();
        }
      });
      card.querySelector(".chart-remove")?.addEventListener("click", () => {
        const id = card.dataset.chartId;
        if (charts[id]) charts[id].destroy();
        card.remove();
        const layout = readLayout();
        layout.hidden = [...new Set([...(layout.hidden || []), id])];
        layout.custom = (layout.custom || []).filter(
          (config) => config.id !== id,
        );
        saveLayout(layout);
      });
    });
  }
  function persistOrder() {
    const layout = readLayout();
    layout.order = [
      ...document.querySelectorAll("#chartGrid > .chart-card"),
    ].map((card) => card.dataset.chartId);
    saveLayout(layout);
  }
  function addCustomChart() {
    const id = `customChart${Date.now()}`;
    const config = {
      id,
      type: document.getElementById("builderType").value,
      field: document.getElementById("builderField").value,
      title:
        document.getElementById("builderTitle").value.trim() ||
        "Custom feedback view",
    };
    const layout = readLayout();
    layout.custom = [...(layout.custom || []), config];
    layout.order = [...(layout.order || defaults), id];
    layout.hidden = (layout.hidden || []).filter((hiddenId) => hiddenId !== id);
    saveLayout(layout);
    const grid = document.getElementById("chartGrid");
    grid.appendChild(customCard(config));
    bindCardActions();
    render();
    document.getElementById("builderTitle").value = "Custom feedback view";
  }
  function render() {
    const items = filtered();
    renderFixed(items);
    document
      .querySelectorAll(".custom-chart-card")
      .forEach((card) => renderCustom(card, items));
  }

  Object.values(els).forEach((element) =>
    element?.addEventListener("change", render),
  );
  document.querySelectorAll(".power-kpi[data-kpi]").forEach((card) =>
    card.addEventListener("click", () => {
      const value = card.dataset.kpi;
      if (value === "users") return;
      els.risk.value = ["High", "Medium", "Low"].includes(value)
        ? value
        : "all";
      els.status.value = ["submitted", "predicted", "not_applicable"].includes(
        value,
      )
        ? value
        : "all";
      document
        .querySelectorAll(".power-kpi")
        .forEach((item) => item.classList.remove("active"));
      card.classList.add("active");
      render();
    }),
  );
  document.getElementById("resetDashboard")?.addEventListener("click", () => {
    Object.values(els).forEach((element) => {
      if (element) element.value = "all";
    });
    document
      .querySelectorAll(".power-kpi")
      .forEach((item) => item.classList.remove("active"));
    document
      .querySelector('.power-kpi[data-kpi="all"]')
      ?.classList.add("active");
    render();
  });
  document
    .getElementById("addChart")
    ?.addEventListener("click", addCustomChart);
  document.getElementById("resetChartLayout")?.addEventListener("click", () => {
    localStorage.removeItem(layoutKey);
    window.location.reload();
  });
  applyLayout();
  render();
})();
