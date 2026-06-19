let capabilities = [];
let selected = null;

const $ = (id) => document.getElementById(id);

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, ch => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[ch]));
}

async function getJson(url) {
  const res = await fetch(url);
  return await res.json();
}

function fillSelect(id, values) {
  const select = $(id);
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
}

function renderMetrics(summary) {
  $("moduleCount").textContent = summary.module_count || 0;
  $("functionCount").textContent = summary.function_count || 0;
  $("classCount").textContent = summary.class_count || 0;
  $("capabilityCount").textContent = summary.capability_count || 0;
}

function renderList() {
  const q = $("search").value.toLowerCase();
  const category = $("categoryFilter").value;
  const visualizer = $("visualizerFilter").value;

  const box = $("capabilityList");
  box.innerHTML = "";

  const filtered = capabilities.filter(cap => {
    const text = `${cap.name} ${cap.qualified_name} ${cap.category} ${cap.visualizer} ${cap.doc}`.toLowerCase();
    return (
      text.includes(q) &&
      (category === "all" || cap.category === category) &&
      (visualizer === "all" || cap.visualizer === visualizer)
    );
  });

  for (const cap of filtered) {
    const div = document.createElement("div");
    div.className = "capability";
    div.innerHTML = `
      <div class="cap-title">${escapeHtml(cap.name)}</div>
      <div class="cap-sub">${escapeHtml(cap.qualified_name)}</div>
      <span class="badge">${escapeHtml(cap.kind)}</span>
      <span class="badge">${escapeHtml(cap.category)}</span>
      <span class="badge">${escapeHtml(cap.visualizer)}</span>
    `;
    div.onclick = () => selectCapability(cap);
    box.appendChild(div);
  }
}

function selectCapability(cap) {
  selected = cap;

  $("selectedName").textContent = cap.name;
  $("badges").innerHTML = `
    <span class="badge">${escapeHtml(cap.kind)}</span>
    <span class="badge">${escapeHtml(cap.category)}</span>
    <span class="badge">${escapeHtml(cap.visualizer)}</span>
    <span class="badge">${escapeHtml(cap.qualified_name)}</span>
  `;
  $("signature").textContent = cap.signature || "";
  $("doc").textContent = cap.doc || "No docstring found.";
  $("runOutput").textContent = "";
}

function renderCapabilityMap() {
  const grouped = {};

  for (const cap of capabilities) {
    if (!grouped[cap.category]) grouped[cap.category] = [];
    grouped[cap.category].push(cap);
  }

  const map = $("map");
  map.innerHTML = "";

  for (const [category, items] of Object.entries(grouped).sort()) {
    const card = document.createElement("div");
    card.className = "category-card";
    card.innerHTML = `
      <strong>${escapeHtml(category)}</strong>
      <span class="badge">${items.length} capabilities</span>
      <div class="small">${items.slice(0, 8).map(x => escapeHtml(x.name)).join(", ")}${items.length > 8 ? "..." : ""}</div>
    `;
    map.appendChild(card);
  }
}

async function runSelected() {
  if (!selected) {
    $("runOutput").textContent = "No capability selected.";
    return;
  }

  let args = [];
  let kwargs = {};

  try {
    args = JSON.parse($("argsInput").value || "[]");
    kwargs = JSON.parse($("kwargsInput").value || "{}");
  } catch (err) {
    $("runOutput").textContent = "Invalid JSON: " + err.message;
    return;
  }

  const res = await fetch("/api/run", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      qualified_name: selected.qualified_name,
      args,
      kwargs
    })
  });

  const data = await res.json();
  $("runOutput").textContent = JSON.stringify(data, null, 2);
}

async function runSmoke() {
  $("runOutput").textContent = "Running no-argument smoke test...";
  const res = await fetch("/api/run-batch-smoke?limit=50", { method: "POST" });
  const data = await res.json();
  $("runOutput").textContent = JSON.stringify(data, null, 2);
}

async function init() {
  const summary = await getJson("/api/summary");
  renderMetrics(summary);

  capabilities = await getJson("/api/capabilities");

  const categories = [...new Set(capabilities.map(x => x.category))].sort();
  const visualizers = [...new Set(capabilities.map(x => x.visualizer))].sort();

  fillSelect("categoryFilter", categories);
  fillSelect("visualizerFilter", visualizers);

  renderList();
  renderCapabilityMap();

  if (capabilities.length) {
    selectCapability(capabilities[0]);
  }
}

$("search").oninput = renderList;
$("categoryFilter").onchange = renderList;
$("visualizerFilter").onchange = renderList;
$("runBtn").onclick = runSelected;
$("smokeBtn").onclick = runSmoke;

init();