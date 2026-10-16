/**
 * EcoCampus AI - Enterprise Real-World Application Controller
 * Features:
 * - Real-time live sensor telemetry stream with fluctuating meters & simulation triggers
 * - Real live camera (webcam/mobile) capture directly in browser with HUD reticle
 * - Real CSV utility meter data ingestion & anomaly detection
 * - Institutional Financial & ESG Scope 1/2 Carbon Calculator ($ USD / ₹ INR)
 * - Work order management with technician dispatch, SLAs, and search
 * - Pretrained YOLOv8 computer vision inference for waste audits
 * - Interactive Campus Digital Twin with facility-linked alerts
 */

// Dynamic API Base URL: Automatically points to Flask (Port 5000)
// whether served via VS Code Live Server (Port 5500) or directly by Flask.
const API_BASE = (window.location.port === "5000") 
  ? "" 
  : "http://127.0.0.1:5000";

// Global Application State
let appState = {
  isBackendOnline: false,
  selectedImageFile: null,
  activeFacilityId: null,
  currentMapFilter: "all",
  currentFilterCategory: "all",
  currentFilterStatus: "all",
  currentSearchTerm: "",
  currentFilterLocation: "",
  currentFilterFacilityId: "",
  activeCurrency: "usd", // 'usd' or 'inr'
  alerts: [],
  facilitiesData: {},
  latestDetectionData: null,
  cameraStream: null,
  liveStreamActive: true
};

document.getElementById("myButton").addEventListener("click", () => {
  alert("EcoNova is working!");
});




fetch("http://127.0.0.1:5000/api/status")
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));

// -------------------------------------------------------------
// Safe API Fetch Helper (Robust against network and parsing errors)
// -------------------------------------------------------------
async function safeFetchJson(endpoint, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, options);
    const rawText = await response.text();

    if (!rawText || rawText.trim() === "") {
      throw new Error(`Empty response from server (HTTP ${response.status}). Ensure the Flask backend is running on port 5000.`);
    }

    let parsedData;
    try {
      parsedData = JSON.parse(rawText);
    } catch (parseErr) {
      if (rawText.includes("<!DOCTYPE html>") || rawText.includes("<html")) {
        throw new Error(
          `Received HTML instead of JSON (HTTP ${response.status}). If using VS Code Live Server, ensure Python Flask is running at http://127.0.0.1:5000.`
        );
      }
      throw new Error(`Invalid JSON received: ${rawText.substring(0, 100)}...`);
    }

    if (!response.ok) {
      const errorMsg = parsedData.message || parsedData.error || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }

    return parsedData;
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new Error("Unable to connect to AI server. Please start Flask via `python backend/app.py`.");
    }
    throw err;
  }
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[character]);
}

// -------------------------------------------------------------
// Application Initialization
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initHealthMonitor();
  initNavigation();
  initLiveTelemetryHUD();
  initCampusDigitalTwin();
  initWasteIntelligence();
  initWebcamStream();
  initCSVUtilityIngestion();
  initActionCenter();
  initFinancialESGCalculator();
  initReports();
  loadCampusTelemetry();
  loadFinancialImpact();
});

// -------------------------------------------------------------
// 1. Health Monitoring & Status Pill
// -------------------------------------------------------------
async function initHealthMonitor() {
  const pill = document.getElementById("api-health-pill");
  const pillText = document.getElementById("api-status-text");
  const sideDot = document.querySelector(".status-indicator-dot");
  const sideTitle = document.getElementById("sidebar-status-title");
  const sideDesc = document.getElementById("sidebar-status-desc");

  async function check() {
    try {
      const data = await safeFetchJson("/api/health");
      appState.isBackendOnline = true;
      
      pill.className = "api-pill connected";
      pillText.textContent = "● AI ENGINE CONNECTED (PORT 5000)";
      
      if (sideDot) {
        sideDot.className = "status-indicator-dot online";
        sideTitle.textContent = "AI ENGINE READY";
        sideDesc.textContent = "Flask 5000 · YOLOv8n";
      }
    } catch (err) {
      appState.isBackendOnline = false;
      pill.className = "api-pill disconnected";
      pillText.textContent = "○ AI BACKEND OFFLINE (PORT 5000)";
      
      if (sideDot) {
        sideDot.className = "status-indicator-dot offline";
        sideTitle.textContent = "BACKEND DISCONNECTED";
        sideDesc.textContent = "Run: python backend/app.py";
      }
    }
  }

  await check();
  setInterval(check, 12000);
}

// -------------------------------------------------------------
// 2. Real-Time Live Telemetry HUD Bar & Anomaly Simulator
// -------------------------------------------------------------
function initLiveTelemetryHUD() {
  const energyEl = document.getElementById("hud-energy-kw");
  const waterEl = document.getElementById("hud-water-lpm");
  const solarEl = document.getElementById("hud-solar-kw");
  const occEl = document.getElementById("hud-occupancy");
  const tickerEl = document.getElementById("live-ticker-message");
  const streamText = document.getElementById("hud-stream-text");
  const streamBadge = document.getElementById("hud-stream-status");

  const simEnergyBtn = document.getElementById("sim-energy-btn");
  const simWaterBtn = document.getElementById("sim-water-btn");
  const simWasteBtn = document.getElementById("sim-waste-btn");
  const simResetBtn = document.getElementById("sim-reset-btn");

  async function pollLiveTick() {
    if (!appState.liveStreamActive) return;

    try {
      const data = await safeFetchJson("/api/telemetry/live-tick");
      if (data.metrics) {
        if (energyEl) energyEl.textContent = Number(data.metrics.energy_kw).toLocaleString();
        if (waterEl) waterEl.textContent = Number(data.metrics.water_lps).toFixed(2);
        if (solarEl) solarEl.textContent = Number(data.metrics.solar_generation_kw).toLocaleString();
        if (occEl) occEl.textContent = Number(data.metrics.campus_occupancy).toLocaleString();
      }
      if (streamText) streamText.textContent = "DEMO SIMULATOR · NO LIVE SENSORS";
      if (streamBadge) streamBadge.classList.add("simulated");

      // Live Ticker updates
      if (data.recent_events && data.recent_events.length > 0 && tickerEl) {
        const latest = data.recent_events[data.recent_events.length - 1];
        tickerEl.textContent = `[${latest.time}] ${latest.text}`;
      }

      // Highlight active anomaly visually
      if (data.anomaly && data.anomaly.is_active) {
        handleActiveAnomalyFeedback(data.anomaly.detail);
      } else {
        clearAnomalyHighlighting();
      }

    } catch (err) {
      if (streamText) streamText.textContent = "SIMULATOR UNAVAILABLE · NO LIVE FEED";
      if (streamBadge) streamBadge.classList.remove("simulated");
      [energyEl, waterEl, solarEl, occEl].forEach(element => {
        if (element) element.textContent = "--";
      });
    }
  }

  pollLiveTick();
  setInterval(pollLiveTick, 3000);

  // Simulation Trigger Buttons
  if (simEnergyBtn) {
    simEnergyBtn.addEventListener("click", async () => {
      if (await triggerSimulation("energy_spike", "Energy surge demo started.")) simEnergyBtn.classList.add("active-sim");
    });
  }

  if (simWaterBtn) {
    simWaterBtn.addEventListener("click", async () => {
      if (await triggerSimulation("water_leak", "Water leak demo started.")) simWaterBtn.classList.add("active-sim");
    });
  }

  if (simWasteBtn) {
    simWasteBtn.addEventListener("click", async () => {
      if (await triggerSimulation("waste_overflow", "Waste overflow demo started.")) simWasteBtn.classList.add("active-sim");
    });
  }

  if (simResetBtn) {
    simResetBtn.addEventListener("click", async () => {
      if (await triggerSimulation("reset", "Demo readings reset; stored work orders remain labeled.")) {
        [simEnergyBtn, simWaterBtn, simWasteBtn].forEach(button => button && button.classList.remove("active-sim"));
      }
    });
  }
}

async function triggerSimulation(type, toastMsg) {
  try {
    const res = await safeFetchJson("/api/telemetry/simulate-anomaly", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type })
    });
    showToast(toastMsg, type === "reset" ? "success" : "error");
    await loadAlerts();
    return true;
  } catch (err) {
    showToast(`Simulation note: ${err.message}`, "info");
    return false;
  }
}

function handleActiveAnomalyFeedback(detail) {
  if (!detail) return;
  document.querySelectorAll(".facility-marker[data-facility]").forEach(marker => {
    marker.classList.toggle("demo-scenario-highlight", marker.dataset.facility === detail.facility_id);
  });
}

function clearAnomalyHighlighting() {
  document.querySelectorAll(".facility-marker").forEach(marker => marker.classList.remove("demo-scenario-highlight"));
}

// -------------------------------------------------------------
// 3. Live Webcam & Mobile Camera Stream Capture
// -------------------------------------------------------------
function initWebcamStream() {
  const tabFile = document.getElementById("tab-mode-file");
  const tabCamera = document.getElementById("tab-mode-camera");
  const dropzone = document.getElementById("upload-dropzone");
  const sampleBox = document.querySelector(".sample-picker-box");
  const videoBox = document.getElementById("webcam-viewfinder-box");
  const videoEl = document.getElementById("webcam-video");
  const cameraControls = document.getElementById("camera-controls-row");
  const captureBtn = document.getElementById("capture-webcam-btn");
  const stopBtn = document.getElementById("stop-webcam-btn");
  const previewContainer = document.getElementById("preview-container");

  if (!tabFile || !tabCamera) return;

  tabFile.addEventListener("click", () => {
    tabFile.classList.add("active");
    tabCamera.classList.remove("active");
    dropzone.hidden = false;
    if (sampleBox) sampleBox.hidden = false;
    if (videoBox) videoBox.hidden = true;
    if (cameraControls) cameraControls.hidden = true;
    stopCamera();
  });

  tabCamera.addEventListener("click", async () => {
    tabCamera.classList.add("active");
    tabFile.classList.remove("active");
    dropzone.hidden = true;
    if (sampleBox) sampleBox.hidden = true;
    if (videoBox) videoBox.hidden = false;
    if (cameraControls) cameraControls.hidden = false;
    await startCamera();
  });

  async function startCamera() {
    try {
      if (appState.cameraStream) stopCamera();

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "environment"
        },
        audio: false
      });

      appState.cameraStream = stream;
      if (videoEl) {
        videoEl.srcObject = stream;
        await videoEl.play();
      }
      showToast("Live Camera Viewfinder Connected. Aim at objects.", "success");
    } catch (err) {
      showToast(`Camera access denied or unavailable: ${err.message}`, "error");
      tabFile.click();
    }
  }

  function stopCamera() {
    if (appState.cameraStream) {
      appState.cameraStream.getTracks().forEach(track => track.stop());
      appState.cameraStream = null;
    }
    if (videoEl) videoEl.srcObject = null;
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      tabFile.click();
    });
  }

  if (captureBtn) {
    captureBtn.addEventListener("click", () => {
      if (!videoEl || !appState.cameraStream) {
        showToast("No active camera stream to capture.", "error");
        return;
      }

      // Draw current video frame to an offscreen canvas
      const canvas = document.createElement("canvas");
      canvas.width = videoEl.videoWidth || 640;
      canvas.height = videoEl.videoHeight || 480;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(blob => {
        if (!blob) {
          showToast("Failed to capture frame from camera.", "error");
          return;
        }

        const snapshotFile = new File([blob], `live_capture_${Date.now()}.jpg`, { type: "image/jpeg" });
        handleSelectedImage(snapshotFile);
        stopCamera();
        tabFile.click();

        // Auto-run analysis for seamless user experience
        const analyzeBtn = document.getElementById("analyze-image-btn");
        if (analyzeBtn) analyzeBtn.click();

        showToast("Snapshot captured! Running AI object detection...", "success");
      }, "image/jpeg", 0.92);
    });
  }

  window.addEventListener("pagehide", stopCamera, { once: true });
}

// -------------------------------------------------------------
// 4. Real CSV Utility Meter Data Ingestion
// -------------------------------------------------------------
function initCSVUtilityIngestion() {
  const dropZone = document.getElementById("csv-drop-zone");
  const fileInput = document.getElementById("csv-file-input");
  const resultPanel = document.getElementById("csv-result-panel");
  const statRecords = document.getElementById("csv-stat-records");
  const statMean = document.getElementById("csv-stat-mean");
  const statMax = document.getElementById("csv-stat-max");
  const statAnomalies = document.getElementById("csv-stat-anomalies");
  const statusMsg = document.getElementById("csv-status-msg");

  if (!dropZone || !fileInput) return;

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      handleCSVUpload(fileInput.files[0]);
    }
  });

  ["dragenter", "dragover"].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--accent-cyan)";
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "";
    });
  });

  dropZone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleCSVUpload(e.dataTransfer.files[0]);
    }
  });

  async function handleCSVUpload(file) {
    if (!file.name.endsWith(".csv")) {
      showToast("Please upload a .csv spreadsheet file.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      showToast(`Uploading and parsing ${file.name}...`, "info");
      const res = await safeFetchJson("/api/telemetry/upload-csv", {
        method: "POST",
        body: formData
      });

      if (resultPanel) resultPanel.hidden = false;
      if (statusMsg) statusMsg.textContent = `${res.message} Source: ${res.data_source}.`;
      if (statRecords) statRecords.textContent = res.total_records;
      if (statMean) statMean.textContent = (res.metrics || []).map(metric => `${metric.metric}: ${metric.mean} ${metric.unit}`).join(" · ") || "No metric readings";
      if (statMax) statMax.textContent = (res.metrics || []).map(metric => `${metric.metric}: ${metric.peak} ${metric.unit}`).join(" · ") || "No metric peaks";
      if (statAnomalies) statAnomalies.textContent = `${res.anomalies_detected} flagged`;

      await loadCampusTelemetry();
      showToast(`CSV Parsed: ${res.anomalies_detected} high-consumption anomalies detected!`, "success");
    } catch (err) {
      showToast(`CSV Ingestion error: ${err.message}`, "error");
    }
  }
}

// -------------------------------------------------------------
// 5. Real-World Financial Cost & ESG Carbon Calculator
// -------------------------------------------------------------
function initFinancialESGCalculator() {
  const btnUsd = document.getElementById("btn-curr-usd");
  const btnInr = document.getElementById("btn-curr-inr");

  if (btnUsd && btnInr) {
    btnUsd.addEventListener("click", () => {
      appState.activeCurrency = "usd";
      btnUsd.classList.add("active");
      btnInr.classList.remove("active");
      loadFinancialImpact();
    });

    btnInr.addEventListener("click", () => {
      appState.activeCurrency = "inr";
      btnInr.classList.add("active");
      btnUsd.classList.remove("active");
      loadFinancialImpact();
    });
  }
}

async function loadFinancialImpact() {
  const totalSavingsEl = document.getElementById("fin-total-savings");
  const breakdownSubEl = document.getElementById("fin-breakdown-sub");
  const co2ValEl = document.getElementById("fin-co2-val");
  const wasteValEl = document.getElementById("fin-waste-val");
  const treesValEl = document.getElementById("fin-trees-val");

  try {
    const data = await safeFetchJson("/api/financial-impact");
    if (!data.financial_cost_avoidance) return;

    const isUsd = appState.activeCurrency === "usd";
    const curr = isUsd ? data.financial_cost_avoidance.usd : data.financial_cost_avoidance.inr;
    const sym = curr.currency_symbol;

    if (totalSavingsEl) {
      totalSavingsEl.textContent = `${sym}${curr.total_savings.toLocaleString()}`;
    }

    if (breakdownSubEl) {
      breakdownSubEl.textContent = `⚡ Power: ${sym}${curr.energy_savings.toLocaleString()} · ♢ Water: ${sym}${curr.water_savings.toLocaleString()}`;
    }

    if (co2ValEl) {
      co2ValEl.textContent = `${data.environmental_esg.ghg_co2e_avoided_kg} kg CO₂e`;
    }

    const reportCo2 = document.getElementById("rep-co2e");
    const kpiCo2 = document.getElementById("kpi-co2e-val");
    if (reportCo2) reportCo2.textContent = `${data.environmental_esg.ghg_co2e_avoided_kg} kg`;
    if (kpiCo2) kpiCo2.textContent = data.environmental_esg.ghg_co2e_avoided_kg;

    if (wasteValEl) {
      wasteValEl.textContent = `${data.environmental_esg.waste_diverted_landfill_kg} kg`;
    }

    const reportWater = document.getElementById("rep-water");
    if (reportWater) reportWater.textContent = `${Number(data.environmental_esg.water_conserved_liters).toLocaleString()} L`;

    if (treesValEl) {
      treesValEl.textContent = `${data.environmental_esg.trees_equivalent_annual} trees`;
    }

  } catch (err) {
    console.log("Financial impact initialized with local metrics.");
  }
}

// -------------------------------------------------------------
// 6. Navigation
// -------------------------------------------------------------
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  const mobileToggle = document.getElementById("mobile-menu-toggle");
  const sidebar = document.getElementById("sidebar");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(n => n.classList.remove("active"));
      item.classList.add("active");

      if (window.innerWidth <= 820 && sidebar) {
        sidebar.classList.remove("open");
      }
    });
  });

  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }
}

// -------------------------------------------------------------
// 7. Campus Digital Twin Schematic
// -------------------------------------------------------------
function initCampusDigitalTwin() {
  const markers = document.querySelectorAll(".facility-marker");
  markers.forEach(marker => {
    marker.addEventListener("click", () => {
      const facilityId = marker.dataset.facility;
      if (facilityId) selectFacility(facilityId);
    });

    marker.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const facilityId = marker.dataset.facility;
        if (facilityId) selectFacility(facilityId);
      }
    });
  });

  const filterButtons = document.querySelectorAll(".map-filter");
  filterButtons.forEach(button => {
    button.addEventListener("click", () => {
      setMapFilter(button.dataset.mapFilter);
    });
  });

  const filterAlertsBtn = document.getElementById("detail-filter-alerts-btn");
  if (filterAlertsBtn) {
    filterAlertsBtn.addEventListener("click", () => {
      if (!appState.activeFacilityId) return;
      scrollToSection("action-center");
      filterAlertsByFacility(appState.activeFacilityId);
    });
  }

  const logIssueBtn = document.getElementById("detail-log-issue-btn");
  if (logIssueBtn) {
    logIssueBtn.addEventListener("click", () => {
      openCreateAlertModal();
      const facility = appState.facilitiesData[appState.activeFacilityId];
      if (facility) {
        const facilitySelect = document.getElementById("new-location");
        if (facilitySelect) facilitySelect.value = appState.activeFacilityId;
      }
    });
  }
}

function selectFacility(facilityId) {
  appState.activeFacilityId = facilityId;
  const facility = appState.facilitiesData[facilityId];

  document.querySelectorAll(".facility-marker").forEach(marker => {
    marker.classList.toggle("active-facility", marker.dataset.facility === facilityId);
  });

  if (!facility) return;

  const linkedAlerts = appState.alerts.filter(alert => alert.facility_id === facilityId);
  const activeAlerts = linkedAlerts.filter(alert => alert.status !== "Completed");
  const status = activeAlerts.some(alert => alert.priority === "High")
    ? "alert"
    : activeAlerts.length ? "attention" : facility.status || "unknown";
  const energy = facility.telemetry?.energy;
  const water = facility.telemetry?.water;
  const waste = facility.telemetry?.waste;

  document.getElementById("detail-title").textContent = facility.name;
  document.getElementById("detail-summary").textContent = facility.description;
  document.getElementById("detail-source").textContent = `DSU E-brochure (Pages ${facility.source_pages})`;
  document.getElementById("detail-energy").textContent = energy
    ? `${Number(energy.value).toLocaleString()} ${energy.unit}`
    : "No imported meter reading";
  document.getElementById("detail-water").textContent = water
    ? `${Number(water.value).toLocaleString()} ${water.unit}`
    : "No imported meter reading";
  const wasteDetections = linkedAlerts.filter(alert => alert.category === "Waste" && /YOLO|AI/i.test(alert.source || ""));
  document.getElementById("detail-waste").textContent = waste
    ? `${Number(waste.value).toLocaleString()} ${waste.unit} · CSV import`
    : wasteDetections.length
      ? wasteDetections.map(alert => alert.evidence).join("; ")
      : "No linked YOLO detection or imported waste reading";
  document.getElementById("detail-operational-status").textContent = status === "unknown"
    ? "Unknown · no connected status feed"
    : status === "normal" ? "Normal · uploaded readings" : `${status === "alert" ? "Alert" : "Attention"} · linked record`;
  document.getElementById("detail-data-source").textContent = facility.telemetry?.data_source
    ? `${facility.telemetry.data_source} · historical, not live`
    : "No physical meter or sensor feed connected";
  document.getElementById("detail-updated").textContent = facility.telemetry?.last_updated || "No imported reading timestamp";

  const statusBadge = document.getElementById("detail-status-badge");
  statusBadge.textContent = status === "unknown" ? "NO LIVE FEED" : status.toUpperCase();
  statusBadge.className = `status-badge ${status === "alert" ? "red" : status === "normal" ? "green" : "yellow"}`;

  renderFacilityAlerts(linkedAlerts);

  const filterBtn = document.getElementById("detail-filter-alerts-btn");
  const logBtn = document.getElementById("detail-log-issue-btn");
  if (filterBtn) filterBtn.disabled = linkedAlerts.length === 0;
  if (logBtn) logBtn.disabled = false;
}

function renderFacilityAlerts(alerts) {
  const list = document.getElementById("detail-alerts-list");
  if (!list) return;
  document.getElementById("detail-alert-count").textContent = String(alerts.length);
  list.replaceChildren();

  if (alerts.length === 0) {
    const empty = document.createElement("p");
    empty.className = "facility-empty-state";
    empty.textContent = "No alerts linked to this facility.";
    list.appendChild(empty);
    return;
  }

  alerts.slice(0, 5).forEach(alert => {
    const item = document.createElement("article");
    item.className = "facility-alert-item";
    const title = document.createElement("strong");
    title.textContent = alert.title;
    const metadata = document.createElement("span");
    const provenance = alert.source === "Demo Simulation" ? " · DEMO" : "";
    metadata.textContent = `${alert.category} · ${alert.status} · ${alert.source || "Manual"}${provenance} · ${alert.assignee || "Unassigned"}`;
    item.append(title, metadata);
    list.appendChild(item);
  });
}

function setMapFilter(filter) {
  appState.currentMapFilter = filter;
  document.querySelectorAll(".map-filter").forEach(button => {
    const active = button.dataset.mapFilter === filter;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  let visibleCount = 0;
  document.querySelectorAll(".facility-marker").forEach(marker => {
    const facilityAlerts = marker.dataset.facility
      ? appState.alerts.filter(alert => alert.facility_id === marker.dataset.facility)
      : [];
    const activeAlerts = facilityAlerts.filter(alert => alert.status !== "Completed");
    const facility = appState.facilitiesData[marker.dataset.facility];
    const matchesCategory = facilityAlerts.some(alert => alert.category.toLowerCase() === filter);
    const visible = filter === "all"
      || (filter === "alerts" && activeAlerts.length > 0)
      || marker.dataset.layer === filter
      || matchesCategory;

    marker.classList.toggle("marker-hidden", !visible);
    marker.classList.toggle("marker-has-alert", activeAlerts.length > 0);
    const status = activeAlerts.some(alert => alert.priority === "High")
      ? "alert"
      : activeAlerts.length ? "attention" : facility?.status || "unknown";
    marker.classList.remove("status-normal", "status-attention", "status-alert", "status-unknown");
    marker.classList.add(`status-${status}`);
    if (visible) visibleCount += 1;
  });

  const notes = {
    all: "Illustrative campus scene, not to scale. Building, road, path, and utility positions are representative, not a verified DSU site plan.",
    waste: "Showing the illustrative waste point and facilities with linked waste work orders. No bin locations or live capacity sensors are configured.",
    energy: "Showing brochure-described solar features and facilities with linked energy work orders. No live energy meters are configured.",
    water: "Showing the illustrative water point and facilities with linked water work orders. No live water meters are configured.",
    alerts: visibleCount
      ? `${visibleCount} facility marker(s) have linked work orders.`
      : "No active work orders are linked to a verified facility. Unassigned work orders are not placed on this schematic."
  };
  const note = document.getElementById("map-layer-note");
  if (note) note.textContent = notes[filter] || notes.all;
}

// -------------------------------------------------------------
// 8. AI Waste Intelligence (YOLOv8 Computer Vision)
// -------------------------------------------------------------
function initWasteIntelligence() {
  const dropzone = document.getElementById("upload-dropzone");
  const fileInput = document.getElementById("waste-image-input");
  const previewContainer = document.getElementById("preview-container");
  const previewImg = document.getElementById("image-preview");
  const previewName = document.getElementById("preview-filename");
  const removeBtn = document.getElementById("remove-image-btn");
  const analyzeBtn = document.getElementById("analyze-image-btn");
  const statusMsg = document.getElementById("ai-status-message");

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      handleSelectedImage(fileInput.files[0]);
    }
  });

  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedImage(e.dataTransfer.files[0]);
    }
  });

  removeBtn.addEventListener("click", () => {
    appState.selectedImageFile = null;
    fileInput.value = "";
    previewContainer.hidden = true;
    previewImg.src = "";
    statusMsg.textContent = "Select a photo, capture via camera, or click a 1-click test image.";
    statusMsg.className = "ai-status-message muted";
  });

  // 1-Click Sample Image Picker Buttons
  const sampleBtns = document.querySelectorAll(".sample-btn");
  sampleBtns.forEach(btn => {
    btn.addEventListener("click", async () => {
      const type = btn.dataset.sample;
      let filename = "sample_campus_bus.jpg";
      if (type === "canteen") filename = "canteen_bottles.jpg";
      if (type === "tray") filename = "cafeteria_tray.jpg";
      if (type === "pathway") filename = "littered_pathway.jpg";

      statusMsg.textContent = `Loading test image (${filename})...`;
      statusMsg.className = "ai-status-message muted";

      try {
        const resp = await fetch(`${API_BASE}/sample_images/${filename}`);
        if (!resp.ok) throw new Error("Could not load sample image from server.");
        const blob = await resp.blob();
        const testFile = new File([blob], filename, { type: "image/jpeg" });
        handleSelectedImage(testFile);
        showToast(`Loaded test image: ${filename}`, "success");
      } catch (err) {
        statusMsg.textContent = `Sample note: ${err.message}`;
        statusMsg.className = "ai-status-message error";
      }
    });
  });

  // Analyze Button
  analyzeBtn.addEventListener("click", async () => {
    if (!appState.selectedImageFile) {
      statusMsg.textContent = "Please select an image or snap with the camera first.";
      statusMsg.className = "ai-status-message error";
      return;
    }

    analyzeBtn.disabled = true;
    const btnText = analyzeBtn.querySelector(".btn-text");
    const btnSpinner = analyzeBtn.querySelector(".btn-spinner");
    if (btnText) btnText.textContent = "AI Model Running Inference...";
    if (btnSpinner) btnSpinner.hidden = false;

    statusMsg.textContent = "Validating image & running YOLOv8 object detector...";
    statusMsg.className = "ai-status-message muted";

    try {
      const formData = new FormData();
      formData.append("image", appState.selectedImageFile);

      const result = await safeFetchJson("/api/detect-waste", {
        method: "POST",
        body: formData
      });

      renderDetectionResults(result);

      statusMsg.textContent = "Analysis complete. Review detections and verify findings below.";
      statusMsg.className = "ai-status-message success";
      showToast("AI Detection Completed Successfully", "success");

    } catch (err) {
      statusMsg.textContent = err.message;
      statusMsg.className = "ai-status-message error";
      showToast(err.message, "error");
    } finally {
      analyzeBtn.disabled = false;
      if (btnText) btnText.textContent = "Analyze Image with AI ↗";
      if (btnSpinner) btnSpinner.hidden = true;
    }
  });

  const confirmBtn = document.getElementById("confirm-waste-issue-btn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", () => openConfirmWasteModal());
  }

  const dismissBtn = document.getElementById("dismiss-waste-btn");
  if (dismissBtn) {
    dismissBtn.addEventListener("click", () => {
      showToast("Detection dismissed as non-issue / verified clear.", "info");
      document.getElementById("results-content").hidden = true;
      document.getElementById("results-empty-state").hidden = false;
    });
  }
}

function handleSelectedImage(file) {
  const statusMsg = document.getElementById("ai-status-message");
  const previewContainer = document.getElementById("preview-container");
  const previewImg = document.getElementById("image-preview");
  const previewName = document.getElementById("preview-filename");

  const validTypes = ["image/jpeg", "image/png", "image/jpg"];
  if (!validTypes.includes(file.type.toLowerCase())) {
    statusMsg.textContent = "Unsupported format. Please select a JPG, JPEG, or PNG image.";
    statusMsg.className = "ai-status-message error";
    return;
  }

  if (file.size > 8 * 1024 * 1024) {
    statusMsg.textContent = "File is oversized. Maximum allowed image size is 8 MB.";
    statusMsg.className = "ai-status-message error";
    return;
  }

  appState.selectedImageFile = file;
  previewName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  previewImg.src = URL.createObjectURL(file);
  previewContainer.hidden = false;

  statusMsg.textContent = "Image loaded. Ready for AI inference.";
  statusMsg.className = "ai-status-message muted";
}

function renderDetectionResults(data) {
  appState.latestDetectionData = data;

  const emptyState = document.getElementById("results-empty-state");
  const resultsContent = document.getElementById("results-content");
  emptyState.hidden = true;
  resultsContent.hidden = false;

  document.getElementById("res-total-objects").textContent = data.total_objects;
  document.getElementById("res-waste-objects").textContent = data.possible_waste_related_count;
  document.getElementById("res-recyclable-count").textContent = data.waste_breakdown ? data.waste_breakdown.recyclable : 0;
  document.getElementById("res-organic-count").textContent = data.waste_breakdown ? data.waste_breakdown.organic : 0;

  const annotImg = document.getElementById("annotated-image");
  annotImg.src = `${API_BASE}${data.annotated_image}?t=${Date.now()}`;

  const chipsList = document.getElementById("detection-chips-list");
  chipsList.innerHTML = "";

  if (data.detections.length === 0) {
    const emptyNotice = document.createElement("p");
    emptyNotice.className = "muted";
    emptyNotice.textContent = "No recognizable COCO objects detected above threshold.";
    chipsList.appendChild(emptyNotice);
  } else {
    data.detections.forEach(item => {
      const chip = document.createElement("div");
      chip.className = `detection-chip tag-${item.category || "other"}`;
      chip.innerHTML = `
        <strong>${item.display_name || item.label}</strong>
        <span>${item.confidence}% conf</span>
      `;
      chipsList.appendChild(chip);
    });
  }

  document.getElementById("results-rec-message").textContent = data.message;
}

// -------------------------------------------------------------
// 9. Priority Action Center & Work Order Management
// -------------------------------------------------------------
function initActionCenter() {
  loadAlerts();

  // Search input listener
  const searchInput = document.getElementById("alert-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      appState.currentSearchTerm = e.target.value.trim().toLowerCase();
      renderAlertsList();
    });
  }

  // Filter chips listeners
  const filterChips = document.querySelectorAll(".filter-chip");
  filterChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const type = chip.dataset.filterType;
      const val = chip.dataset.val;

      document.querySelectorAll(`.filter-chip[data-filter-type="${type}"]`).forEach(c => c.classList.remove("active"));
      chip.classList.add("active");

      if (type === "category") appState.currentFilterCategory = val;
      if (type === "status") appState.currentFilterStatus = val;
      appState.currentFilterLocation = "";
      appState.currentFilterFacilityId = "";

      renderAlertsList();
    });
  });

  // Modal setup
  const openModalBtn = document.getElementById("btn-open-create-modal");
  const topLogBtn = document.getElementById("top-log-btn");
  const modal = document.getElementById("create-modal");
  const closeModalBtn = document.getElementById("close-create-modal");
  const cancelModalBtn = document.getElementById("cancel-create-modal");
  const createForm = document.getElementById("create-issue-form");

  [openModalBtn, topLogBtn].forEach(btn => {
    if (btn) btn.addEventListener("click", openCreateAlertModal);
  });

  if (closeModalBtn) closeModalBtn.addEventListener("click", closeCreateAlertModal);
  if (cancelModalBtn) cancelModalBtn.addEventListener("click", closeCreateAlertModal);

  if (createForm) {
    createForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await handleCreateAlertSubmit();
    });
  }

  // Confirmation modal setup
  const confModal = document.getElementById("confirm-modal");
  const closeConfBtn = document.getElementById("close-confirm-modal");
  const cancelConfBtn = document.getElementById("cancel-confirm-modal");
  const confirmForm = document.getElementById("confirm-waste-form");

  if (closeConfBtn) closeConfBtn.addEventListener("click", () => confModal.hidden = true);
  if (cancelConfBtn) cancelConfBtn.addEventListener("click", () => confModal.hidden = true);

  if (confirmForm) {
    confirmForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await handleConfirmWasteSubmit();
    });
  }
}

async function loadAlerts() {
  try {
    const data = await safeFetchJson("/api/alerts");
    appState.alerts = data.alerts || [];
    renderAlertsList();
    updateKpiNumbers();
    loadFinancialImpact();
    setMapFilter(appState.currentMapFilter);
    if (appState.activeFacilityId) selectFacility(appState.activeFacilityId);
  } catch (err) {
    console.warn("Using local alert cache due to server state:", err.message);
  }
}

function renderAlertsList() {
  const container = document.getElementById("alerts-list");
  if (!container) return;

  container.innerHTML = "";

  let filtered = appState.alerts.filter(a => {
    const matchesCat = (appState.currentFilterCategory === "all") || 
                       (a.category.toLowerCase() === appState.currentFilterCategory.toLowerCase());
    const matchesStatus = (appState.currentFilterStatus === "all") || 
                          (a.status.toLowerCase() === appState.currentFilterStatus.toLowerCase());
    const matchesLocation = !appState.currentFilterLocation ||
                a.location.toLowerCase().includes(appState.currentFilterLocation.toLowerCase());
    const matchesFacility = !appState.currentFilterFacilityId || a.facility_id === appState.currentFilterFacilityId;
    
    // Search text filter
    let matchesSearch = true;
    if (appState.currentSearchTerm) {
      const term = appState.currentSearchTerm;
      const combined = `${a.title} ${a.location} ${a.evidence} ${a.assignee || ''} ${a.action}`.toLowerCase();
      matchesSearch = combined.includes(term);
    }

    return matchesCat && matchesStatus && matchesLocation && matchesFacility && matchesSearch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="results-empty-state">
        <div class="empty-icon">✓</div>
        <h4>No Work Orders Matching Filter</h4>
        <p>No issues found matching your selected search criteria.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(alert => {
    const card = document.createElement("article");
    card.className = `alert-card ${alert.status === "Completed" ? "status-completed" : ""}`;

    const catIcon = alert.category === "Waste" ? "♻" : alert.category === "Energy" ? "ϟ" : "♢";
    const catClass = alert.category.toLowerCase();
    const priorityClass = alert.priority ? alert.priority.toLowerCase() : "medium";
    const priorityLabel = { High: "P1 · High", Medium: "P2 · Medium", Low: "P3 · Low" }[alert.priority] || alert.priority;

    card.innerHTML = `
      <div class="alert-type-icon ${catClass}">${catIcon}</div>
      <div class="alert-meta-col">
        <div class="alert-header-row">
          <span class="alert-priority-tag ${priorityClass}">${escapeHtml(priorityLabel)}</span>
          <span class="alert-location-tag">📍 ${escapeHtml(alert.location)}</span>
          <span class="alert-assignee-tag">👤 ${escapeHtml(alert.assignee || "Facility Crew Alpha")}</span>
        </div>
        <div class="alert-title">${escapeHtml(alert.title)}</div>
        <small style="font-size:10px; color:var(--text-dim);">Reported: ${escapeHtml(alert.created_at)} · Source: ${escapeHtml(alert.source || "Manual")}</small>
      </div>
      <div class="alert-evidence-col">
        <div class="alert-evidence-text">${escapeHtml(alert.evidence)}</div>
        <div class="alert-action-text">↳ Plan: ${escapeHtml(alert.action)}</div>
        ${alert.notes ? `<div style="font-size:10px; color:var(--accent-yellow); margin-top:2px;">📝 Tech Note: ${escapeHtml(alert.notes)}</div>` : ""}
      </div>
      <div class="alert-status-col">
        <select class="status-dropdown" data-id="${alert.id}">
          <option value="Open" ${alert.status === "Open" ? "selected" : ""}>Open</option>
          <option value="In Progress" ${alert.status === "In Progress" ? "selected" : ""}>In Progress</option>
          <option value="Completed" ${alert.status === "Completed" ? "selected" : ""}>Completed</option>
        </select>
        <select class="assignee-dropdown" data-id="${alert.id}" aria-label="Assign maintenance crew">
          <option ${alert.assignee === "Facility Crew Alpha" ? "selected" : ""}>Facility Crew Alpha</option>
          <option ${alert.assignee === "Plumbing Unit 2" ? "selected" : ""}>Plumbing Unit 2</option>
          <option ${alert.assignee === "Green Volunteers Guild" ? "selected" : ""}>Green Volunteers Guild</option>
        </select>
        <span class="alert-sla-badge ${alert.sla_breached ? "overdue" : ""}">${alert.sla_breached ? "OVERDUE" : "SLA due"}: ${escapeHtml(alert.due_at || `${alert.sla_hours || 4}h`)}</span>
      </div>
      <div class="alert-actions-col">
        <button class="btn-delete-alert" data-id="${alert.id}" title="Delete alert">🗑</button>
      </div>
    `;

    const dropdown = card.querySelector(".status-dropdown");
    dropdown.addEventListener("change", async (e) => {
      const newStatus = e.target.value;
      if (newStatus !== "Completed") {
        await updateAlertStatus(alert.id, newStatus, alert.notes || "");
        return;
      }

      const editor = document.createElement("div");
      editor.className = "resolution-editor";
      const notesInput = document.createElement("textarea");
      notesInput.rows = 2;
      notesInput.maxLength = 1000;
      notesInput.placeholder = "Required resolution notes";
      notesInput.value = alert.notes || "";
      const saveButton = document.createElement("button");
      saveButton.type = "button";
      saveButton.className = "resolution-save-btn";
      saveButton.textContent = "Save resolution";
      const cancelButton = document.createElement("button");
      cancelButton.type = "button";
      cancelButton.className = "resolution-cancel-btn";
      cancelButton.textContent = "Cancel";
      editor.append(notesInput, saveButton, cancelButton);
      card.querySelector(".alert-status-col").appendChild(editor);

      cancelButton.addEventListener("click", () => {
        dropdown.value = alert.status;
        editor.remove();
      });
      saveButton.addEventListener("click", async () => {
        const notes = notesInput.value.trim();
        if (!notes) {
          notesInput.setCustomValidity("Resolution notes are required.");
          notesInput.reportValidity();
          return;
        }
        saveButton.disabled = true;
        await updateAlertStatus(alert.id, newStatus, notes);
      });
    });

    card.querySelector(".assignee-dropdown").addEventListener("change", async event => {
      await updateAlertStatus(alert.id, alert.status, alert.notes || "", event.target.value);
    });

    const delBtn = card.querySelector(".btn-delete-alert");
    delBtn.addEventListener("click", async () => {
      if (confirm(`Remove alert: "${alert.title}"?`)) {
        await deleteAlert(alert.id);
      }
    });

    container.appendChild(card);
  });
}

async function updateAlertStatus(alertId, newStatus, notes = "", assignee = null) {
  try {
    await safeFetchJson(`/api/alerts/${alertId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus, notes, ...(assignee ? { assignee } : {}) })
    });

    const target = appState.alerts.find(a => a.id === alertId);
    if (target) {
      target.status = newStatus;
      if (notes) target.notes = notes;
      if (assignee) target.assignee = assignee;
    }

    renderAlertsList();
    updateKpiNumbers();
    loadFinancialImpact();
    setMapFilter(appState.currentMapFilter);
    if (appState.activeFacilityId) selectFacility(appState.activeFacilityId);
    showToast(`Work Order #${alertId} updated to ${newStatus}`, "success");
  } catch (err) {
    showToast(`Failed to update status: ${err.message}`, "error");
  }
}

async function deleteAlert(alertId) {
  try {
    await safeFetchJson(`/api/alerts/${alertId}`, { method: "DELETE" });
    appState.alerts = appState.alerts.filter(a => a.id !== alertId);
    renderAlertsList();
    updateKpiNumbers();
    loadFinancialImpact();
    setMapFilter(appState.currentMapFilter);
    if (appState.activeFacilityId) selectFacility(appState.activeFacilityId);
    showToast("Alert removed from database", "info");
  } catch (err) {
    showToast(`Error deleting alert: ${err.message}`, "error");
  }
}

function openCreateAlertModal() {
  const modal = document.getElementById("create-modal");
  if (modal) modal.hidden = false;
}

function closeCreateAlertModal() {
  const modal = document.getElementById("create-modal");
  if (modal) modal.hidden = true;
}

async function handleCreateAlertSubmit() {
  const title = document.getElementById("new-title").value.trim();
  const category = document.getElementById("new-category").value;
  const facilitySelect = document.getElementById("new-location");
  const facilityId = facilitySelect.value || null;
  const location = facilityId ? facilitySelect.selectedOptions[0].textContent : "Campus-wide / location unverified";
  const priority = document.getElementById("new-priority").value;
  const source = document.getElementById("new-source").value;
  const assignee = document.getElementById("new-assignee").value;
  const slaHours = Number(document.getElementById("new-sla-hours").value);
  const evidence = document.getElementById("new-evidence").value.trim();
  const action = document.getElementById("new-action").value.trim();
  const energySavings = Number(document.getElementById("new-energy-saved").value || 0);
  const waterSavings = Number(document.getElementById("new-water-saved").value || 0);
  const wasteDiverted = Number(document.getElementById("new-waste-diverted").value || 0);

  try {
    await safeFetchJson("/api/alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title, category, location, priority, source, evidence, action,
        facility_id: facilityId, assignee, sla_hours: slaHours,
        energy_savings_kwh: energySavings, water_savings_liters: waterSavings,
        waste_diverted_kg: wasteDiverted, status: "Open"
      })
    });

    closeCreateAlertModal();
    document.getElementById("create-issue-form").reset();
    showToast("New alert saved to SQLite database!", "success");
    await loadAlerts();
  } catch (err) {
    showToast(`Failed to save alert: ${err.message}`, "error");
  }
}

function openConfirmWasteModal() {
  const confModal = document.getElementById("confirm-modal");
  const evidenceBox = document.getElementById("conf-evidence");
  
  if (appState.latestDetectionData) {
    const d = appState.latestDetectionData;
    const items = d.detections.map(i => `${i.label} (${i.confidence}%)`).join(", ");
    evidenceBox.value = `YOLOv8 detected ${d.possible_waste_related_count} potential waste items: ${items}.`;
  }

  confModal.hidden = false;
}

async function handleConfirmWasteSubmit() {
  const title = document.getElementById("conf-title").value.trim();
  const facilitySelect = document.getElementById("conf-location");
  const facilityId = facilitySelect.value || null;
  const location = facilityId ? facilitySelect.selectedOptions[0].textContent : "Campus-wide / location unverified";
  const priority = document.getElementById("conf-priority").value;
  const assignee = document.getElementById("conf-assignee").value;
  const slaHours = Number(document.getElementById("conf-sla-hours").value);
  const evidence = document.getElementById("conf-evidence").value.trim();
  const action = document.getElementById("conf-action").value.trim();

  try {
    await safeFetchJson("/api/alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        category: "Waste",
        location,
        facility_id: facilityId,
        priority,
        assignee,
        sla_hours: slaHours,
        source: appState.selectedImageFile?.name.startsWith("live_capture_")
          ? "Webcam AI Verified Detection"
          : "AI Verified Detection",
        evidence,
        action,
        status: "Open"
      })
    });

    document.getElementById("confirm-modal").hidden = true;
    showToast("AI Waste Alert Confirmed & Logged to SQLite!", "success");
    await loadAlerts();
    scrollToSection("action-center");
  } catch (err) {
    showToast(`Error creating alert: ${err.message}`, "error");
  }
}

function updateKpiNumbers() {
  const total = appState.alerts.length;
  const openCount = appState.alerts.filter(a => a.status === "Open").length;
  const inProgressCount = appState.alerts.filter(a => a.status === "In Progress").length;
  const completedCount = appState.alerts.filter(a => a.status === "Completed").length;
  const wasteAlerts = appState.alerts.filter(a => a.category === "Waste" && a.status !== "Completed").length;

  const navBadge = document.getElementById("nav-open-count");
  if (navBadge) navBadge.textContent = openCount;

  // Update the "All" category filter chip count dynamically
  const filterChipAll = document.getElementById("filter-chip-all");
  if (filterChipAll) filterChipAll.textContent = `All (${total})`;

  const kpiOpen = document.getElementById("kpi-open-alerts-count");
  if (kpiOpen) kpiOpen.textContent = String(openCount).padStart(2, "0");

  const kpiProg = document.getElementById("kpi-in-progress-pill");
  if (kpiProg) kpiProg.textContent = `${inProgressCount} In Progress · ${completedCount} Completed`;

  const kpiWaste = document.getElementById("kpi-waste-count");
  if (kpiWaste) kpiWaste.textContent = String(wasteAlerts).padStart(2, "0");

  const calcScore = Math.max(50, Math.min(98, Math.round(92 - (openCount * 3.5 + inProgressCount * 1.5))));
  const scoreBadge = document.getElementById("kpi-sustainability-score");
  if (scoreBadge) scoreBadge.textContent = calcScore;

  const scorePillBadge = document.getElementById("kpi-score-badge");
  if (scorePillBadge) scorePillBadge.textContent = calcScore;

  const scoreFill = document.getElementById("score-meter-fill");
  if (scoreFill) {
    const offset = 264 - (264 * (calcScore / 100));
    scoreFill.style.strokeDashoffset = offset;
  }
  const scoreRating = document.getElementById("score-rating-text");
  if (scoreRating) scoreRating.textContent = "Illustrative work-order index · not an audited campus rating";

  const repTotal = document.getElementById("rep-total-issues");
  if (repTotal) repTotal.textContent = total;

  const resRate = total > 0 ? Math.round((completedCount / total) * 100) : 0;
  const repRate = document.getElementById("rep-res-rate");
  if (repRate) repRate.textContent = `${resRate}%`;

  const repDetail = document.getElementById("rep-res-detail");
  if (repDetail) repDetail.textContent = `${completedCount} Resolved · ${openCount + inProgressCount} Pending`;

  renderReportCategoryRows();
}

function renderReportCategoryRows() {
  const container = document.getElementById("report-category-rows");
  if (!container) return;
  container.replaceChildren();

  const categories = [
    { name: "Waste diversion", key: "Waste" },
    { name: "Energy efficiency", key: "Energy" },
    { name: "Water conservation", key: "Water" }
  ];
  categories.forEach(category => {
    const records = appState.alerts.filter(alert => alert.category === category.key);
    const completed = records.filter(alert => alert.status === "Completed");
    const rows = [
      category.name,
      String(records.length),
      `${records.filter(alert => alert.status === "Open").length} Open · ${records.filter(alert => alert.status === "In Progress").length} In Progress · ${completed.length} Completed`,
      category.key === "Energy"
        ? `${completed.reduce((sum, alert) => sum + Number(alert.energy_savings_kwh || 0), 0).toFixed(1)} kWh estimated; Scope 2 at 0.82 kg CO₂e/kWh`
        : category.key === "Water"
          ? `${completed.reduce((sum, alert) => sum + Number(alert.water_savings_liters || 0), 0).toFixed(1)} L estimated`
          : `${completed.reduce((sum, alert) => sum + Number(alert.waste_diverted_kg || 0), 0).toFixed(1)} kg estimated`,
      completed.some(alert => alert.notes) ? "Completed with technician notes" : "Work-order estimate only"
    ];
    const row = document.createElement("tr");
    rows.forEach(value => {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    });
    container.appendChild(row);
  });
}

// -------------------------------------------------------------
// 10. Campus Telemetry Loading
// -------------------------------------------------------------
async function loadCampusTelemetry() {
  try {
    const data = await safeFetchJson("/api/campus-data");
    appState.facilitiesData = Object.fromEntries((data.facilities || []).map(facility => [facility.id, facility]));
    setMapFilter(appState.currentMapFilter);
    if (appState.activeFacilityId) selectFacility(appState.activeFacilityId);
  } catch (err) {
    console.log("Telemetry loaded with default state.");
  }
}

// -------------------------------------------------------------
// 11. Reports & Export Functions
// -------------------------------------------------------------
function initReports() {
  const printBtn = document.getElementById("btn-print-report");
  if (printBtn) {
    printBtn.addEventListener("click", () => window.print());
  }

  const exportBtn = document.getElementById("btn-export-csv");
  if (exportBtn) {
    exportBtn.addEventListener("click", exportAlertsToCSV);
  }
}

async function exportAlertsToCSV() {
  let readings = [];
  try {
    const result = await safeFetchJson("/api/telemetry/readings");
    readings = result.readings || [];
  } catch (error) {
    showToast(`Could not load meter readings: ${error.message}`, "error");
    return;
  }

  if (appState.alerts.length === 0 && readings.length === 0) {
    showToast("No work orders or meter readings to export.", "error");
    return;
  }

  const quote = value => {
    let text = String(value ?? "");
    if (/^[=+@\-]/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  };
  const headers = ["Record Type", "ID", "Timestamp", "Facility", "Category / Metric", "Title / Value", "Unit", "Priority", "Status / Anomaly", "Assigned Crew", "Source", "Evidence", "Action", "Notes"];
  const workOrderRows = appState.alerts.map(alert => [
    "Work Order", alert.id, alert.created_at, alert.location, alert.category, alert.title, "",
    alert.priority, alert.status, alert.assignee, alert.source, alert.evidence, alert.action, alert.notes
  ]);
  const meterRows = readings.map(reading => [
    "Meter Reading", reading.id, reading.measured_at, reading.facility_label, reading.metric,
    reading.value, reading.unit, "", reading.is_anomaly ? "Anomaly" : "Within Import Threshold",
    "", `CSV: ${reading.filename}`, "", "", `Imported ${reading.imported_at}`
  ]);
  const csvContent = [headers, ...workOrderRows, ...meterRows].map(row => row.map(quote).join(",")).join("\r\n");
  const objectUrl = URL.createObjectURL(new Blob([csvContent], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = `EcoCampus_AI_Operations_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  showToast("Work orders and imported meter readings exported.", "success");
}

// -------------------------------------------------------------
// Helper UI Utilities
// -------------------------------------------------------------
function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function filterAlertsByCategory(cat) {
  scrollToSection("action-center");
  const chip = document.querySelector(`.filter-chip[data-filter-type="category"][data-val="${cat}"]`);
  if (chip) chip.click();
}

function filterAlertsByLocation(loc) {
  appState.currentFilterCategory = "all";
  appState.currentFilterStatus = "all";
  appState.currentFilterLocation = loc;
  document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
  document.querySelectorAll('.filter-chip[data-val="all"]').forEach(c => c.classList.add("active"));
  renderAlertsList();
  const matches = appState.alerts.filter(a => a.location.toLowerCase().includes(loc.toLowerCase()));
  showToast(matches.length ? `Filtered ${matches.length} alert(s) for ${loc}` : `No alerts found for ${loc}`, "info");
}

function filterAlertsByFacility(facilityId) {
  appState.currentFilterCategory = "all";
  appState.currentFilterStatus = "all";
  appState.currentFilterLocation = "";
  appState.currentFilterFacilityId = facilityId;
  document.querySelectorAll(".filter-chip").forEach(chip => chip.classList.remove("active"));
  document.querySelectorAll('.filter-chip[data-val="all"]').forEach(chip => chip.classList.add("active"));
  renderAlertsList();
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === "success" ? "✓" : type === "error" ? "⚠" : "ℹ"}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}
