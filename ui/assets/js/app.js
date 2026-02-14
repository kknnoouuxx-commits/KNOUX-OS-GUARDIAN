const MODULE_ORDER = [
  "DiskSpaceOrchestrator",
  "NetworkMonitor",
  "PerformanceOptimizer",
  "SecurityHardener",
  "UpdateGuardian",
  "DriverHealthManager",
  "ForensicAnalyzer",
  "ThermalController",
  "PowerManager",
  "ApplicationCurator",
  "RegistryGuardian",
  "BackupOrchestrator",
];

const refs = {
  appShell: document.getElementById("appShell"),
  lastUpdated: document.getElementById("lastUpdated"),
  networkBadge: document.getElementById("networkBadge"),
  readinessRing: document.getElementById("readinessRing"),
  readinessValue: document.getElementById("readinessValue"),
  readinessState: document.getElementById("readinessState"),
  cpuValue: document.getElementById("cpuValue"),
  ramValue: document.getElementById("ramValue"),
  diskValue: document.getElementById("diskValue"),
  healthyModules: document.getElementById("healthyModules"),
  totalModules: document.getElementById("totalModules"),
  moduleGrid: document.getElementById("moduleGrid"),
  alertCritical: document.getElementById("alertCritical"),
  alertHigh: document.getElementById("alertHigh"),
  alertMedium: document.getElementById("alertMedium"),
  alertLow: document.getElementById("alertLow"),
  alertInfo: document.getElementById("alertInfo"),
};

const moduleCardRefs = new Map();
let pollHandle = null;
let requestInFlight = false;

function classByValue(value, warning, critical) {
  if (value >= critical) return "critical";
  if (value >= warning) return "warning";
  return "healthy";
}

function normalizeStatus(status) {
  const raw = String(status || "unknown").toLowerCase();
  if (raw.includes("critical")) return "critical";
  if (raw.includes("warn")) return "warning";
  if (raw.includes("healthy")) return "healthy";
  if (raw === "passed") return "healthy";
  return "warning";
}

function metricTone(metricEl, status) {
  metricEl.classList.remove("healthy", "warning", "critical");
  metricEl.classList.add(status);
}

function formatTime(value) {
  if (!value) return "No data";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "No data";
  return dt.toLocaleString();
}

function applyReadiness(readiness) {
  const value = Math.max(0, Math.min(100, Number(readiness) || 0));
  refs.readinessRing.style.setProperty("--readiness", String(value));
  refs.readinessValue.textContent = String(value);

  let stateText = "Stabilizing";
  if (value >= 95) stateText = "Release Ready";
  else if (value >= 85) stateText = "Operational";
  else if (value >= 70) stateText = "Monitoring";
  else stateText = "Intervention Required";

  refs.readinessState.textContent = stateText;
}

function ensureModuleCards(modules) {
  const fragment = document.createDocumentFragment();

  modules.forEach((mod) => {
    if (moduleCardRefs.has(mod.module)) return;

    const card = document.createElement("article");
    card.className = "module-card";
    card.innerHTML = `
      <div class="module-header">
        <p class="module-title"></p>
        <span class="health-pill healthy">Healthy</span>
      </div>
      <p class="module-meta module-errors">Errors: 0</p>
      <p class="module-meta module-last-run">Last run: --</p>
    `;

    card.querySelector(".module-title").textContent = mod.module;
    moduleCardRefs.set(mod.module, card);
    fragment.appendChild(card);
  });

  refs.moduleGrid.appendChild(fragment);
}

function updateModuleCards(health) {
  const normalized = MODULE_ORDER.map((name) => {
    const found = health.find((item) => item.module === name);
    return found || {
      module: name,
      status: "warning",
      errors: 1,
      last_run: null,
      active: false,
    };
  });

  ensureModuleCards(normalized);

  normalized.forEach((entry) => {
    const card = moduleCardRefs.get(entry.module);
    if (!card) return;

    const pill = card.querySelector(".health-pill");
    const errors = card.querySelector(".module-errors");
    const lastRun = card.querySelector(".module-last-run");
    const status = normalizeStatus(entry.status);

    pill.className = `health-pill ${status}`;
    pill.textContent = status === "healthy" ? "Healthy" : status === "critical" ? "Critical" : "Warning";
    errors.textContent = `Errors: ${Number(entry.errors || 0)}`;
    lastRun.textContent = `Last run: ${formatTime(entry.last_run)}`;
  });
}

function updateSecurityAlerts(alerts = {}) {
  refs.alertCritical.textContent = String(alerts.critical ?? 0);
  refs.alertHigh.textContent = String(alerts.high ?? 0);
  refs.alertMedium.textContent = String(alerts.medium ?? 0);
  refs.alertLow.textContent = String(alerts.low ?? 0);
  refs.alertInfo.textContent = String(alerts.info ?? 0);
}

function updateMetrics(summary) {
  const system = summary.system_status || {};
  const network = summary.network_status || {};
  const modulesStatus = summary.modules_status || {};

  const cpu = Number(system.cpu_percent ?? 0);
  const ram = Number(system.ram_percent ?? 0);
  const disk = Number(system.disk_percent ?? 0);

  refs.cpuValue.textContent = `${cpu.toFixed(1)}%`;
  refs.ramValue.textContent = `${ram.toFixed(1)}%`;
  refs.diskValue.textContent = `${disk.toFixed(1)}%`;

  metricTone(refs.cpuValue, classByValue(cpu, 65, 80));
  metricTone(refs.ramValue, classByValue(ram, 60, 75));
  metricTone(refs.diskValue, classByValue(disk, 60, 70));

  const totalConnections = Number(network.total_connections ?? network.established_connections ?? 0);
  refs.networkBadge.textContent = `Network: ${totalConnections} links`;
  refs.networkBadge.className = `status-badge ${totalConnections > 0 ? "healthy" : "warning"}`;

  refs.healthyModules.textContent = String(modulesStatus.healthy_modules ?? 0);
  refs.totalModules.textContent = String(modulesStatus.total_modules ?? MODULE_ORDER.length);
}

async function loadTelemetry() {
  if (requestInFlight) return;
  requestInFlight = true;

  try {
    const [summaryRes, healthRes] = await Promise.all([
      fetch("/", { cache: "no-store" }),
      fetch("/health", { cache: "no-store" }),
    ]);

    if (!summaryRes.ok || !healthRes.ok) throw new Error("Telemetry endpoint unavailable");

    const summary = await summaryRes.json();
    const health = await healthRes.json();

    updateMetrics(summary);
    applyReadiness(summary.overall_readiness_percent ?? 0);
    updateSecurityAlerts(summary.security_alerts || {});
    updateModuleCards(Array.isArray(health.module_health) ? health.module_health : []);

    refs.lastUpdated.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    refs.appShell.classList.add("ready");
  } catch (error) {
    refs.networkBadge.textContent = "Network: reconnecting";
    refs.networkBadge.className = "status-badge warning";
    refs.lastUpdated.textContent = "Telemetry refresh failed, retrying...";
  } finally {
    requestInFlight = false;
    pollHandle = window.setTimeout(loadTelemetry, 5000);
  }
}

window.addEventListener("beforeunload", () => {
  if (pollHandle) {
    window.clearTimeout(pollHandle);
  }
});

loadTelemetry();
