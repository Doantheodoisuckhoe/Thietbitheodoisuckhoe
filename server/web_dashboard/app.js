// HealthWatch web dashboard — JavaScript thuần, gọi API của server FastAPI.
"use strict";

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const LEVEL = { info: "Thông tin", warning: "Cảnh báo", danger: "Nguy hiểm" };
const STATUS = { open: "Chưa xác nhận", acknowledged: "Đã xác nhận", resolved: "Đã xử lý" };
const fmtTime = (iso) => (iso ? new Date(iso).toLocaleString("vi-VN", { hour12: false }) : "–");
const fmtHM = (ms) => new Date(ms).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", hour12: false });
const ago = (iso) => {
  if (!iso) return "chưa có dữ liệu";
  const s = (Date.now() - new Date(iso)) / 1000;
  if (s < 60) return "vừa xong";
  if (s < 3600) return `${Math.round(s / 60)} phút trước`;
  if (s < 86400) return `${Math.round(s / 3600)} giờ trước`;
  return fmtTime(iso);
};

// ------------------------------------------------------------------ lưu token
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch { /* bỏ qua */ } },
};

// ------------------------------------------------------------------ API
const api = {
  token: store.get("hw_token"),
  async req(method, path, body, form) {
    const headers = {};
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    let payload;
    if (form) { payload = new URLSearchParams(body); }
    else if (body !== undefined) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }
    const r = await fetch(path, { method, headers, body: payload });
    if (r.status === 401 && path !== "/api/auth/login") { logout(); throw new Error("Hết phiên đăng nhập"); }
    if (r.status === 204) return null;
    const data = await r.json().catch(() => null);
    if (!r.ok) {
      const d = data?.detail;
      throw new Error(typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join("; ") : `Lỗi ${r.status}`);
    }
    return data;
  },
  get(p) { return this.req("GET", p); },
  post(p, b) { return this.req("POST", p, b ?? {}); },
  put(p, b) { return this.req("PUT", p, b); },
  del(p) { return this.req("DELETE", p); },
};

function toast(msg, level = "info", ms = 6000) {
  const el = document.createElement("div");
  el.className = `toast ${level}`;
  el.innerHTML = msg;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), ms);
}

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    o.frequency.value = 880;
    o.connect(ctx.destination);
    o.start();
    setTimeout(() => { o.stop(); ctx.close(); }, 400);
  } catch { /* trình duyệt chặn âm thanh */ }
}

// ------------------------------------------------------------------ trạng thái
const state = { me: null, patients: [], pid: null, tab: "overview", charts: {}, lastAlertId: 0, ecgs: [] };

// ================================================================== Đăng nhập
let registering = false;
$("#toggle-register").onclick = (e) => {
  e.preventDefault();
  registering = !registering;
  $(".reg-only").classList.toggle("hidden", !registering);
  $("#auth-submit").textContent = registering ? "Đăng ký" : "Đăng nhập";
  e.target.textContent = registering ? "Đã có tài khoản? Đăng nhập" : "Chưa có tài khoản? Đăng ký";
};

$("#login-form").onsubmit = async (e) => {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target));
  $("#auth-error").textContent = "";
  try {
    const res = registering
      ? await api.post("/api/auth/register", { email: f.email, password: f.password, full_name: f.full_name || f.email, phone: f.phone || null })
      : await api.req("POST", "/api/auth/login", { username: f.email, password: f.password }, true);
    api.token = res.access_token;
    store.set("hw_token", api.token);
    start();
  } catch (err) {
    $("#auth-error").textContent = err.message;
  }
};

function logout() {
  api.token = null;
  store.set("hw_token", null);
  $("#app-view").classList.add("hidden");
  $("#auth-view").classList.remove("hidden");
}
$("#logout").onclick = logout;

async function start() {
  try {
    state.me = await api.get("/api/auth/me");
  } catch {
    return logout();
  }
  $("#auth-view").classList.add("hidden");
  $("#app-view").classList.remove("hidden");
  $("#me-name").textContent = `${state.me.full_name} (${state.me.role === "admin" ? "quản trị" : "người nhà"})`;
  await loadPatients();
  const saved = Number(store.get("hw_pid"));
  if (state.patients.some((p) => p.id === saved)) selectPatient(saved);
  else if (state.patients.length) selectPatient(state.patients[0].id);
  const recent = await api.get("/api/alerts?limit=1").catch(() => []);
  state.lastAlertId = recent[0]?.id || 0;
  setInterval(poll, 10000);
}

// ================================================================== Danh sách người
async function loadPatients() {
  state.patients = await api.get("/api/patients");
  const open = await api.get("/api/alerts?status=open&limit=500").catch(() => []);
  const count = {};
  open.forEach((a) => (count[a.patient_id] = (count[a.patient_id] || 0) + 1));
  $("#patient-list").innerHTML = state.patients
    .map((p) => `<li data-id="${p.id}" class="${p.id === state.pid ? "active" : ""}">
      <span>${esc(p.full_name)}</span>${count[p.id] ? `<span class="badge">${count[p.id]}</span>` : ""}</li>`)
    .join("");
  $$("#patient-list li").forEach((li) => (li.onclick = () => selectPatient(Number(li.dataset.id))));
}

$("#patient-form").onsubmit = async (e) => {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target));
  try {
    const p = await api.post("/api/patients", { full_name: f.full_name, birth_year: f.birth_year ? Number(f.birth_year) : null, phone: f.phone || null });
    e.target.reset();
    await loadPatients();
    selectPatient(p.id);
  } catch (err) { toast(esc(err.message), "danger"); }
};

function selectPatient(id) {
  state.pid = id;
  store.set("hw_pid", String(id));
  $$("#patient-list li").forEach((li) => li.classList.toggle("active", Number(li.dataset.id) === id));
  $("#empty-state").classList.add("hidden");
  $("#patient-view").classList.remove("hidden");
  $("#ecg-view").classList.add("hidden");
  refresh();
}

// ================================================================== Tabs
$$(".tabs button").forEach((b) => (b.onclick = () => {
  state.tab = b.dataset.tab;
  $$(".tabs button").forEach((x) => x.classList.toggle("active", x === b));
  $$(".tab").forEach((t) => t.classList.toggle("hidden", t.id !== `tab-${state.tab}`));
  refresh();
}));

async function refresh() {
  if (!state.pid) return;
  await loadSummary();
  if (state.tab === "overview") await loadCharts();
  if (state.tab === "alerts") await loadAlerts();
  if (state.tab === "ecg") await loadEcg();
  if (state.tab === "settings") await loadSettings();
}

// ================================================================== Tổng quan
async function loadSummary() {
  const s = await api.get(`/api/patients/${state.pid}`);
  const p = s.patient;
  $("#p-name").textContent = p.full_name + (p.birth_year ? ` (${new Date().getFullYear() - p.birth_year} tuổi)` : "");
  const dev = s.devices[0];
  const online = dev?.last_seen_at && Date.now() - new Date(dev.last_seen_at) < 5 * 60 * 1000;
  $("#p-device").textContent = dev ? `${online ? "● Đang kết nối" : "○ Mất kết nối"} · ${ago(dev.last_seen_at)}` : "Chưa có thiết bị";
  $("#p-device").className = `chip ${dev ? (online ? "ok" : "off") : ""}`;

  const L = s.latest;
  $("#c-hr").textContent = s.last_hr ? `${Math.round(s.last_hr)}` : "–";
  $("#c-hr-sub").textContent = L ? (L.hr ? `chất lượng ${L.hr_quality ?? "–"}` : (L.worn ? "đang đo..." : "không đeo")) : "";
  $("#c-spo2").textContent = s.last_spo2 ? `${Math.round(s.last_spo2)}%` : "–";
  $("#c-spo2-sub").textContent = s.last_spo2_at ? ago(s.last_spo2_at) : "";
  $("#c-temp").textContent = s.last_temp ? `${s.last_temp.toFixed(1)}°` : "–";
  $("#c-temp-sub").textContent = p.temp_baseline ? `mức nền ${p.temp_baseline.toFixed(1)}°C` : "chưa đủ dữ liệu mức nền";
  const e = s.last_ecg;
  $("#c-bp").textContent = e?.sbp_est ? `${Math.round(e.sbp_est)}/${Math.round(e.dbp_est)}` : "–";
  $("#c-bp-sub").textContent = e ? (e.sbp_est ? `${ago(e.ts)} · tham khảo` : "chưa hiệu chuẩn") : "chưa đo ECG";
  $("#c-bat").textContent = dev?.last_battery != null ? `${dev.last_battery}%` : "–";
  $("#c-seen").textContent = dev ? `${dev.last_charging ? "đang sạc · " : ""}${dev.last_worn === false ? "không đeo" : "đang đeo"}` : "";

  const banner = $("#open-alert-banner");
  if (s.open_alerts) {
    banner.innerHTML = `<b>${s.open_alerts} cảnh báo chưa xác nhận.</b> <a href="#" id="go-alerts">Xem ngay</a>`;
    banner.classList.remove("hidden");
    $("#go-alerts").onclick = (ev) => { ev.preventDefault(); $('.tabs button[data-tab="alerts"]').click(); };
  } else banner.classList.add("hidden");
}

function lineChart(id, label, color, points, opts = {}) {
  const old = state.charts[id];
  if (old) old.destroy();
  const ctx = document.getElementById(id);
  state.charts[id] = new Chart(ctx, {
    type: opts.type || "line",
    data: { datasets: [{ label, data: points, borderColor: color, backgroundColor: color, pointRadius: opts.points ? 3 : 0, borderWidth: 1.5, showLine: !opts.points, spanGaps: false }] },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false, parsing: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { type: "linear", min: opts.xmin, max: opts.xmax, ticks: { callback: (v) => fmtHM(v), maxTicksLimit: 8 } },
        y: { suggestedMin: opts.min, suggestedMax: opts.max },
      },
    },
  });
}

async function loadCharts() {
  const hours = Number($("#range").value);
  const start = new Date(Date.now() - hours * 3600e3).toISOString();
  const bucket = hours <= 6 ? 60 : hours <= 24 ? 300 : 1800;
  const rows = await api.get(`/api/patients/${state.pid}/vitals?start=${start}&bucket_s=${bucket}`);
  const pts = (k) => rows.filter((r) => r[k] != null).map((r) => ({ x: new Date(r.ts).getTime(), y: r[k] }));
  const xr = { xmin: Date.now() - hours * 3600e3, xmax: Date.now() };
  lineChart("ch-hr", "HR", "#ef4444", pts("hr"), { min: 40, max: 130, ...xr });
  lineChart("ch-spo2", "SpO2", "#3b82f6", pts("spo2"), { min: 85, max: 100, points: true, ...xr });
  lineChart("ch-temp", "Nhiệt độ", "#f59e0b", pts("skin_temp"), { min: 30, max: 37, ...xr });
  lineChart("ch-act", "Vận động", "#10b981", pts("activity"), { type: "bar", min: 0, ...xr });
}
$("#range").onchange = loadCharts;

// ================================================================== Cảnh báo
async function loadAlerts() {
  const st = $("#alert-filter").value;
  const rows = await api.get(`/api/alerts?patient_id=${state.pid}${st ? `&status=${st}` : ""}`);
  const lat = (a) => {
    if (!a.event_ts) return "–";
    const d = (x) => (x ? ((new Date(x) - new Date(a.event_ts)) / 1000).toFixed(1) + " s" : null);
    return [d(a.push_sent_at) && `push ${d(a.push_sent_at)}`, d(a.sms_sent_at) && `SMS ${d(a.sms_sent_at)}`].filter(Boolean).join("<br>") || "–";
  };
  $("#alert-rows").innerHTML = rows.map((a) => `
    <tr class="${a.status === "open" ? "open" : ""}">
      <td>${fmtTime(a.event_ts || a.created_at)}</td>
      <td><span class="lvl ${a.level}">${LEVEL[a.level]}</span></td>
      <td><b>${esc(a.title)}</b><br><span class="muted small">${esc(a.message)}</span></td>
      <td>${STATUS[a.status]}${a.acknowledged_at ? `<br><span class="muted small">${fmtTime(a.acknowledged_at)}</span>` : ""}</td>
      <td class="small">${lat(a)}</td>
      <td>${a.status === "open" ? `<button class="small primary" data-ack="${a.id}">Đã nhận</button>` : ""}
          ${a.status !== "resolved" ? `<button class="small" data-res="${a.id}">Đã xử lý</button>` : ""}</td>
    </tr>`).join("") || `<tr><td colspan="6" class="muted">Không có cảnh báo.</td></tr>`;
  $$("[data-ack]").forEach((b) => (b.onclick = () => alertAction(b.dataset.ack, "ack")));
  $$("[data-res]").forEach((b) => (b.onclick = () => alertAction(b.dataset.res, "resolve")));
}
$("#alert-filter").onchange = loadAlerts;

async function alertAction(id, action) {
  try {
    await api.post(`/api/alerts/${id}/${action}`);
    await Promise.all([loadAlerts(), loadSummary(), loadPatients()]);
  } catch (err) { toast(esc(err.message), "danger"); }
}

// ================================================================== ECG & huyết áp
async function loadEcg() {
  const [ecgs, cals, model] = await Promise.all([
    api.get(`/api/patients/${state.pid}/ecg`),
    api.get(`/api/patients/${state.pid}/bp-calibrations`),
    api.get(`/api/patients/${state.pid}/bp-model`),
  ]);
  state.ecgs = ecgs;
  $("#ecg-rows").innerHTML = ecgs.map((e) => `
    <tr><td>${fmtTime(e.ts)}</td><td>${e.hr ? Math.round(e.hr) : "–"}</td>
    <td>${e.pat_ms ? e.pat_ms.toFixed(0) + " ms" : "–"}</td>
    <td>${e.sbp_est ? `${Math.round(e.sbp_est)}/${Math.round(e.dbp_est)}` : "–"}</td>
    <td><button class="small" data-ecg="${e.id}">Xem</button></td></tr>`).join("") || `<tr><td colspan="5" class="muted">Chưa có lần đo ECG.</td></tr>`;
  $$("[data-ecg]").forEach((b) => (b.onclick = () => showEcg(Number(b.dataset.ecg))));
  $("#cal-ecg").innerHTML = ecgs.filter((e) => e.pat_ms).map((e) => `<option value="${e.id}">${fmtTime(e.ts)} · PAT ${e.pat_ms.toFixed(0)} ms</option>`).join("")
    || `<option value="">(cần 1 lần đo ECG có PAT)</option>`;
  $("#cal-rows").innerHTML = cals.map((c) => `<tr><td>${fmtTime(c.ts)}</td><td>${c.pat_ms.toFixed(0)} ms</td>
    <td>${Math.round(c.sbp_ref)}/${Math.round(c.dbp_ref)}</td><td><button class="small" data-delcal="${c.id}">Xoá</button></td></tr>`).join("");
  $$("[data-delcal]").forEach((b) => (b.onclick = async () => { await api.del(`/api/patients/${state.pid}/bp-calibrations/${b.dataset.delcal}`); loadEcg(); }));
  $("#bp-model").textContent = model
    ? `Mô hình: SBP = ${model.a_sbp.toFixed(1)} + ${model.b_sbp.toFixed(1)}/PAT(s) · ${model.n_points} điểm · ${model.method === "regression" ? "hồi quy cá nhân" : "bù lệch (độ dốc mặc định)"}`
    : "Chưa hiệu chuẩn — huyết áp sẽ không được ước lượng.";
}

$("#cal-form").onsubmit = async (e) => {
  e.preventDefault();
  const f = Object.fromEntries(new FormData(e.target));
  if (!f.ecg_id) return toast("Cần 1 lần đo ECG có PAT để hiệu chuẩn", "warning");
  try {
    await api.post(`/api/patients/${state.pid}/bp-calibrations`, { ecg_id: Number(f.ecg_id), sbp_ref: Number(f.sbp_ref), dbp_ref: Number(f.dbp_ref) });
    e.target.reset();
    toast("Đã lưu điểm hiệu chuẩn");
    loadEcg();
  } catch (err) { toast(esc(err.message), "danger"); }
};

async function showEcg(id) {
  const e = await api.get(`/api/ecg/${id}`);
  $("#ecg-view").classList.remove("hidden");
  $("#ecg-title").textContent = `ECG ${fmtTime(e.ts)} · HR ${e.hr ? Math.round(e.hr) : "–"} · ${e.fs} Hz`;
  const old = state.charts.ecg;
  if (old) old.destroy();
  const data = (e.samples || []).map((v, i) => ({ x: i / e.fs, y: v }));
  state.charts.ecg = new Chart($("#ecg-canvas"), {
    type: "line",
    data: { datasets: [{ data, borderColor: "#dc2626", borderWidth: 1, pointRadius: 0 }] },
    options: { animation: false, parsing: false, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { type: "linear", title: { display: true, text: "giây" } }, y: { ticks: { display: false } } } },
  });
  $("#ecg-view").scrollIntoView({ behavior: "smooth" });
}

// ================================================================== Cài đặt
async function loadSettings() {
  const [th, cgs, devs] = await Promise.all([
    api.get(`/api/patients/${state.pid}/thresholds`),
    api.get(`/api/patients/${state.pid}/caregivers`),
    api.get(`/api/patients/${state.pid}/devices`),
  ]);
  const form = $("#th-form");
  for (const [k, v] of Object.entries(th)) {
    const el = form.elements[k];
    if (!el) continue;
    if (el.type === "checkbox") el.checked = !!v; else el.value = v;
  }
  $("#cg-rows").innerHTML = cgs.map((c) => `<tr><td>${c.priority}</td><td>${esc(c.user.full_name)}<br><span class="muted small">${esc(c.user.email)} · ${esc(c.user.phone || "chưa có SĐT")}</span></td>
    <td>${esc(c.relation || "")}</td><td>${c.receive_sms ? "SMS ✓" : "chỉ push"}</td><td><button class="small" data-delcg="${c.id}">Xoá</button></td></tr>`).join("");
  $$("[data-delcg]").forEach((b) => (b.onclick = async () => { await api.del(`/api/patients/${state.pid}/caregivers/${b.dataset.delcg}`); loadSettings(); }));
  $("#dev-rows").innerHTML = devs.map((d) => `<tr><td>${esc(d.name)}</td><td class="small muted">${ago(d.last_seen_at)}${d.firmware ? " · FW " + esc(d.firmware) : ""}</td>
    <td><button class="small" data-deldev="${d.id}">Xoá</button></td></tr>`).join("") || `<tr><td class="muted">Chưa có thiết bị.</td></tr>`;
  $$("[data-deldev]").forEach((b) => (b.onclick = async () => {
    if (!confirm("Xoá thiết bị này? App gateway đang dùng API key của nó sẽ ngừng gửi được dữ liệu.")) return;
    await api.del(`/api/patients/${state.pid}/devices/${b.dataset.deldev}`);
    loadSettings();
  }));
}

$("#th-form").onsubmit = async (e) => {
  e.preventDefault();
  const body = {};
  for (const el of e.target.elements) {
    if (!el.name) continue;
    body[el.name] = el.type === "checkbox" ? el.checked : Number(el.value);
  }
  try {
    await api.put(`/api/patients/${state.pid}/thresholds`, body);
    $("#th-msg").textContent = "Đã lưu ✓";
    setTimeout(() => ($("#th-msg").textContent = ""), 3000);
  } catch (err) { toast(esc(err.message), "danger"); }
};

$("#cg-form").onsubmit = async (e) => {
  e.preventDefault();
  const f = e.target;
  try {
    await api.post(`/api/patients/${state.pid}/caregivers`, {
      email: f.email.value, relation: f.relation.value || null, priority: Number(f.priority.value) || 1, receive_sms: f.receive_sms.checked,
    });
    f.reset();
    loadSettings();
  } catch (err) { toast(esc(err.message), "danger"); }
};

$("#dev-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const d = await api.post(`/api/patients/${state.pid}/devices`, { name: e.target.name.value || "HealthWatch" });
    const box = $("#dev-key");
    box.innerHTML = `<b>API key (chỉ hiện 1 lần — nhập vào app gateway):</b><br>${esc(d.api_key)}<br>
      <span class="muted small">Địa chỉ server: ${esc(location.origin)}</span>`;
    box.classList.remove("hidden");
    loadSettings();
  } catch (err) { toast(esc(err.message), "danger"); }
};

// ================================================================== Theo dõi cảnh báo mới
async function poll() {
  try {
    const recent = await api.get("/api/alerts?limit=10");
    const fresh = recent.filter((a) => a.id > state.lastAlertId).reverse();
    if (fresh.length) {
      state.lastAlertId = Math.max(...recent.map((a) => a.id));
      const names = Object.fromEntries(state.patients.map((p) => [p.id, p.full_name]));
      fresh.forEach((a) => toast(`<b>${LEVEL[a.level]}: ${esc(a.title)}</b><br>${esc(names[a.patient_id] || "")} — ${esc(a.message)}`, a.level, 15000));
      if (fresh.some((a) => a.level === "danger")) beep();
      await loadPatients();
    }
    if (state.pid && (state.tab === "overview" || state.tab === "alerts" || fresh.length)) await refresh();
  } catch { /* mất mạng tạm thời */ }
}

if (api.token) start(); else $("#auth-view").classList.remove("hidden");
