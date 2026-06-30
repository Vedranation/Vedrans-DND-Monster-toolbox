// Battle Board — canvas grid with drag/touch tokens, teams, context menu.
// (Targeting/inference + Resolve arrive in increment 3b.)

import { api } from "../api.js";
import { store } from "../store.js";
import { el, modal, popupMenu, toast, promptDialog } from "../dom.js";
import { renderSwings, breakdownInline, dmgColor } from "../swings.js";

const CELL = 32;        // fixed grid cell size in px (autosize reverted; revisit later)

let board = null;
const selected = new Set();
let canvas, ctx;
let _dragBound = false;
let _lines = [];                 // target lines [{from_id,to_id,in_range}]
let _ranges = [];                // attack-range overlays [{token_id, cells, color}] for show_range tokens
let _infl = null;                // selected-token inference {rangeCells, flanked:Set}
let _infoEl = null;              // DOM info line for the selected token
let _lpTimer = null;             // long-press timer (touch → context menu)
let _casterByToken = new Map();  // token_id → caster (for "Go to spells")
let _presetTokenId = null;       // select+center this token on next render (from Spellcasters)

// Select a token when arriving from another tab (e.g. caster's "Go to token").
export function presetSelectToken(id) { _presetTokenId = id; }

// drag state
const drag = { active: false, moved: false, startCol: 0, startRow: 0, origins: null };
// box-select (marquee) state — a drag that starts on empty space
const marquee = { active: false, additive: false, moved: false, x0: 0, y0: 0, x1: 0, y1: 0 };

// ── colors ───────────────────────────────────────────────────────────────────
// Defaults when a token has no explicit color: players blue, monsters yellow.
export const MONSTER_DEFAULT_COLOR = "#d6a52e";
export const PLAYER_DEFAULT_COLOR = "#5b96d6";
function kindDefaultColor(kind) { return kind === "monster" ? MONSTER_DEFAULT_COLOR : PLAYER_DEFAULT_COLOR; }
// A token's chosen hex color (dimmed when inactive), else the kind default.
function tokenColor(t) {
  if (!t.active) return "#888";
  return t.color || kindDefaultColor(t.kind);
}
function teamColor(name) {
  return (board.teams.find((t) => t.name === name) || {}).color || "#888";
}
// "#rrggbb" → "rgba(r,g,b,a)" for translucent range fills.
function hexToRgba(hex, a) {
  const m = /^#?([0-9a-fA-F]{6})$/.exec(hex || "");
  if (!m) return `rgba(255,214,82,${a})`;
  const n = parseInt(m[1], 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

// ── render ─────────────────────────────────────────────────────────────────
function cellCenter(col, row) { return [col * CELL + CELL / 2, row * CELL + CELL / 2]; }

function tokenRadius() { return CELL * 0.4; }

function drawTargetLine(ln) {
  const a = tk(ln.from_id), b = tk(ln.to_id);
  if (!a || !b) return;
  const R = tokenRadius();
  const [x1, y1] = cellCenter(a.col, a.row);
  const [x2, y2] = cellCenter(b.col, b.row);
  const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1;
  const ex = x2 - (dx / len) * R, ey = y2 - (dy / len) * R;  // stop at target's edge
  ctx.strokeStyle = ln.in_range ? "rgba(34,170,68,.85)" : "rgba(204,102,0,.85)";
  ctx.fillStyle = ctx.strokeStyle;
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(ex, ey); ctx.stroke();
  const ang = Math.atan2(dy, dx), ah = 7;
  ctx.beginPath();
  ctx.moveTo(ex, ey);
  ctx.lineTo(ex - ah * Math.cos(ang - 0.4), ey - ah * Math.sin(ang - 0.4));
  ctx.lineTo(ex - ah * Math.cos(ang + 0.4), ey - ah * Math.sin(ang + 0.4));
  ctx.closePath(); ctx.fill();
}

function draw() {
  const W = board.width * CELL, H = board.height * CELL;
  const R = tokenRadius(), DOT = Math.max(3, CELL * 0.15);
  ctx.clearRect(0, 0, W, H);
  // attack-range overlays for tokens with "show range" on (tinted by token color)
  for (const rg of _ranges) {
    ctx.fillStyle = hexToRgba(rg.color, 0.16);
    for (const [c, r] of rg.cells) ctx.fillRect(c * CELL, r * CELL, CELL, CELL);
  }
  // grid
  ctx.strokeStyle = "#cfd2da";
  ctx.lineWidth = 1;
  for (let c = 0; c <= board.width; c++) {
    ctx.beginPath(); ctx.moveTo(c * CELL, 0); ctx.lineTo(c * CELL, H); ctx.stroke();
  }
  for (let r = 0; r <= board.height; r++) {
    ctx.beginPath(); ctx.moveTo(0, r * CELL); ctx.lineTo(W, r * CELL); ctx.stroke();
  }
  // tokens
  const flanked = _infl ? _infl.flanked : new Set();
  for (const t of board.tokens) {
    const [cx, cy] = cellCenter(t.col, t.row);
    const isSel = selected.has(t.id);
    if (flanked.has(t.id)) {  // flank highlight ring
      ctx.beginPath(); ctx.arc(cx, cy, R + 4, 0, Math.PI * 2);
      ctx.strokeStyle = "#33cc55"; ctx.lineWidth = 2; ctx.stroke();
    }
    ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fillStyle = tokenColor(t); ctx.fill();
    ctx.lineWidth = isSel ? 3 : 1;
    ctx.strokeStyle = isSel ? "#ff6600" : "#111"; ctx.stroke();
    // team dot
    ctx.beginPath(); ctx.arc(cx + R * 0.8, cy - R * 0.8, DOT, 0, Math.PI * 2);
    ctx.fillStyle = teamColor(t.team); ctx.fill();
    ctx.lineWidth = 1; ctx.strokeStyle = "#fff"; ctx.stroke();
    // hp bar
    if (t.max_hp > 0) {
      const ratio = Math.max(0, Math.min(1, t.hp / t.max_hp));
      const bw = R * 2, bx = cx - R, by = cy + R + 2;
      ctx.fillStyle = "#222"; ctx.fillRect(bx, by, bw, 3);
      ctx.fillStyle = ratio > 0.5 ? "#44cc44" : ratio > 0.25 ? "#ccaa00" : "#cc3333";
      ctx.fillRect(bx, by, bw * ratio, 3);
    }
    // name
    ctx.fillStyle = "#000"; ctx.font = `${Math.round(CELL * 0.22)}px sans-serif`; ctx.textAlign = "center";
    ctx.fillText((t.data_ref || "").slice(0, 7), cx, cy + 2);
    // condition marker — red "!" disc at the top-left corner
    if (t.conditions && t.conditions.length) {
      const mx = cx - R * 0.8, my = cy - R * 0.8, mr = Math.max(4, CELL * 0.17);
      ctx.beginPath(); ctx.arc(mx, my, mr, 0, Math.PI * 2);
      ctx.fillStyle = "#cc2222"; ctx.fill();
      ctx.lineWidth = 1; ctx.strokeStyle = "#fff"; ctx.stroke();
      ctx.fillStyle = "#fff"; ctx.font = `bold ${Math.round(mr * 1.5)}px sans-serif`;
      ctx.textBaseline = "middle";
      ctx.fillText("!", mx, my + 0.5);
      ctx.textBaseline = "alphabetic";
    }
    // concentration marker — purple "C" disc at the bottom-left (linked caster concentrating)
    const linkedCaster = _casterByToken.get(t.id);
    if (linkedCaster && linkedCaster.concentrating) {
      const cmx = cx - R * 0.8, cmy = cy + R * 0.8, cmr = Math.max(4, CELL * 0.17);
      ctx.beginPath(); ctx.arc(cmx, cmy, cmr, 0, Math.PI * 2);
      ctx.fillStyle = "#7e57c2"; ctx.fill();
      ctx.lineWidth = 1; ctx.strokeStyle = "#fff"; ctx.stroke();
      ctx.fillStyle = "#fff"; ctx.font = `bold ${Math.round(cmr * 1.4)}px sans-serif`;
      ctx.textBaseline = "middle";
      ctx.fillText("C", cmx, cmy + 0.5);
      ctx.textBaseline = "alphabetic";
    }
  }
  // target lines drawn ON TOP of tokens so it's clear who targets whom in a melee scrum
  for (const ln of _lines) drawTargetLine(ln);
  // box-select rectangle (on top of everything)
  if (marquee.active && marquee.moved) {
    const x = Math.min(marquee.x0, marquee.x1), y = Math.min(marquee.y0, marquee.y1);
    const w = Math.abs(marquee.x1 - marquee.x0), h = Math.abs(marquee.y1 - marquee.y0);
    ctx.fillStyle = "rgba(255,102,0,.12)";
    ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = "#ff6600"; ctx.lineWidth = 1; ctx.setLineDash([4, 3]);
    ctx.strokeRect(x, y, w, h);
    ctx.setLineDash([]);
  }
}

function tokenAt(px, py) {
  const rr = (tokenRadius() + 2) ** 2;
  for (let i = board.tokens.length - 1; i >= 0; i--) {
    const t = board.tokens[i];
    const [cx, cy] = cellCenter(t.col, t.row);
    if ((px - cx) ** 2 + (py - cy) ** 2 <= rr) return t;
  }
  return null;
}
function cellAt(px, py) {
  return [Math.max(0, Math.min(board.width - 1, Math.floor(px / CELL))),
          Math.max(0, Math.min(board.height - 1, Math.floor(py / CELL)))];
}

// ── data helpers ───────────────────────────────────────────────────────────
let _bar = null;
let _selBar = null;            // touch-friendly action bar (mirrors the R/T/D/H/Del shortcuts)
let _multiSelect = false;      // toggle: tapping tokens adds to selection (like holding Ctrl)

// Rebuild the selection action bar to reflect the current selection. These buttons
// give touch users (no keyboard) the same actions as the hotkeys/context menu.
function renderSelBar() {
  if (!_selBar) return;
  const ids = [...selected];
  const primary = ids.length ? tk(ids[ids.length - 1]) : null;
  const monsterTokens = ids.map((id) => tk(id)).filter((t) => t && t.kind === "monster");
  const monsterIds = monsterTokens.map((t) => t.id);
  const none = ids.length === 0;
  // Send-to-Attack needs exactly two tokens with at least one monster.
  const pair = ids.length === 2 ? [tk(ids[0]), tk(ids[1])] : null;
  const canAttack = pair && pair[0] && pair[1] && (pair[0].kind === "monster" || pair[1].kind === "monster");
  // Go-to-spells needs a single token with a linked caster.
  const caster = ids.length === 1 ? _casterByToken.get(ids[0]) : null;
  _selBar.replaceChildren(
    el("button", { class: "btn neutral" + (_multiSelect ? " active" : ""),
      title: "Tap tokens to add to the selection (like holding Ctrl)",
      onclick: () => { _multiSelect = !_multiSelect; renderSelBar(); } }, _multiSelect ? "Multi ✓" : "Multi-select"),
    el("span", { class: "muted sel-count", text: `${ids.length} selected` }),
    el("button", { class: "btn primary", disabled: none, onclick: () => setHpDialog(ids) }, "Set HP"),
    el("button", { class: "btn neutral", disabled: none, onclick: () => conditionsDialog(ids, primary) }, "Conditions"),
    el("button", { class: "btn neutral", disabled: !monsterIds.length,
      onclick: () => retarget(monsterIds, primary && primary.id) }, "Cycle target"),
    el("button", { class: "btn neutral", disabled: !canAttack,
      onclick: () => sendToAttack(pair[0], pair[1]) }, "To Attack"),
    el("button", { class: "btn neutral", disabled: !monsterTokens.length,
      onclick: () => sendToMassSaves(monsterTokens) }, "Mass save"),
    el("button", { class: "btn neutral", disabled: !caster,
      onclick: () => window.dispatchEvent(new CustomEvent("navigate", { detail: { tab: "spellcasters", selectCasterId: caster.id } })) }, "Go to spells"),
    el("button", { class: "btn danger", disabled: none,
      onclick: () => patchAll(ids, { active: !(primary && primary.active) }) },
      primary && !primary.active ? "Activate" : "Deactivate"),
    el("button", { class: "btn danger", disabled: none, onclick: () => removeTokens(ids) }, "Remove"),
  );
}

// ── inspector panel ──────────────────────────────────────────────────────────
let _panelEl = null;       // <aside> shell
let _panelBody = null;     // body container (hidden when collapsed)
let _panelCaret = null;    // ▸/▾ toggle
let _panelOpen = false;    // collapsed/expanded (persists across tab switches)
let _panelAuto = true;     // "auto-show on select" checkbox (persists)
let _panelData = null;     // last single-selection panel payload

const _sign = (n) => (n >= 0 ? "+" : "") + n;
const _cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const _humanSource = (k) => k.replace(/^target_/, "target ").replace(/_/g, " ");

function buildPanelShell() {
  _panelCaret = el("button", { class: "caret", onclick: () => { _panelOpen = !_panelOpen; applyPanelState(); } },
    _panelOpen ? "▾" : "▸");
  const autoCb = el("input", { type: "checkbox" });
  autoCb.checked = _panelAuto;
  autoCb.addEventListener("change", () => { _panelAuto = autoCb.checked; });
  const head = el("div", { class: "panel-head" }, [
    _panelCaret, el("span", { class: "panel-title", text: "Token info" }),
    el("label", { class: "toggle auto-show", title: "Expand the panel when you select a token" }, [autoCb, "auto-show"]),
  ]);
  _panelBody = el("div", { class: "panel-body" });
  _panelEl.replaceChildren(head, _panelBody);
  renderPanel();
  applyPanelState();
}

function applyPanelState() {
  if (!_panelBody) return;
  _panelCaret.textContent = _panelOpen ? "▾" : "▸";
  _panelBody.style.display = _panelOpen ? "" : "none";
}

function dmgPart(p) {
  const dice = p.n_die > 0 ? `${p.n_die}${p.die}` : "";
  const flat = p.flat > 0 ? `+${p.flat}` : (p.flat < 0 ? `${p.flat}` : "");
  const expr = (dice + flat) || "0";
  return el("span", { style: `color:${dmgColor(p.type)}`, text: `${expr} ${p.type}` });
}

function dmgTypeList(arr) {
  if (!arr || !arr.length) return el("span", { class: "muted", text: "none" });
  const span = el("span");
  arr.forEach((tp, i) => {
    if (i > 0) span.append(", ");
    span.append(el("span", { style: `color:${dmgColor(tp)}`, text: tp }));
  });
  return span;
}

function infoRow(label, node) {
  return el("div", { class: "insp-row" }, [el("span", { class: "insp-label", text: label }), node]);
}

function renderPanel() {
  if (!_panelBody) return;
  const d = _panelData;
  if (!d) {
    _panelBody.replaceChildren(el("div", { class: "muted", text: "Select a single token to inspect." }));
    return;
  }
  const body = el("div");

  // identity + vitals
  body.append(el("div", { class: "insp-name" }, [
    el("span", { class: "dot", style: `background:${teamColor(d.team)}` }),
    el("b", { text: d.name }), el("span", { class: "muted", text: `  ${d.kind} · ${d.team}` }),
  ]));
  const hpStr = d.max_hp > 0 ? `${d.hp} / ${d.max_hp}` : String(d.hp);
  body.append(infoRow("HP", el("span", { text: hpStr })));
  body.append(infoRow("AC", el("span", { text: d.ac != null ? String(d.ac) : "—" })));

  // auto-crit / helpless / sight banners
  if (d.auto_crit) body.append(el("div", { class: "insp-warn", text: "⚡ Hits auto-crit (target helpless, ≤5 ft)" }));
  if (d.is_helpless) body.append(el("div", { class: "insp-warn", text: "⚡ Helpless — attackers within 5 ft auto-crit" }));
  if (d.sees_invisible) body.append(el("div", { class: "insp-note", text: "👁 Sees invisible (target in blindsight/truesight)" }));
  if (d.can_attack === false) body.append(el("div", { class: "insp-warn", text: "🚫 Incapacitated — can't attack" }));
  if (d.charmer_name) body.append(el("div", { class: "insp-note", text:
    d.charm_warn ? `💗 Charmed by ${d.charmer_name} — targeting charmer (⚠ warn)`
                 : `💗 Charmed by ${d.charmer_name} — won't target charmer` }));

  // conditions
  const conds = el("span");
  if (d.conditions.length) {
    d.conditions.forEach((c) => conds.append(el("span", { class: "cond-chip", text: c })));
  } else conds.append(el("span", { class: "muted", text: "none" }));
  body.append(infoRow("Conditions", conds));

  // roll type + why
  const why = [...d.adv_sources.map((s) => `+${_humanSource(s)}`), ...d.disadv_sources.map((s) => `−${_humanSource(s)}`)];
  const rt = el("span", { text: d.roll_type });
  if (why.length) rt.append(el("span", { class: "muted", text: `  (${why.join(", ")})` }));
  body.append(infoRow("Roll", rt));

  // attacks (monster)
  if (d.attacks && d.attacks.length) {
    const wrap = el("div", { class: "insp-attacks" });
    for (const a of d.attacks) {
      const row = el("div", { class: "insp-attack" });
      row.append(el("span", { text: `${a.n}× ${a.name}  ${_sign(a.to_hit)}` }));
      if (a.dmg1 || a.dmg2) {
        row.append(el("span", { text: "  ·  " }));
        if (a.dmg1) row.append(dmgPart(a.dmg1));
        if (a.dmg2) { row.append(" + "); row.append(dmgPart(a.dmg2)); }
      }
      wrap.append(row);
    }
    body.append(el("div", { class: "subhead", text: "Attacks" }), wrap);
  }

  // ranges (attack range is monster-only; players don't attack) + movement + senses
  const ranges = [];
  if (d.kind === "monster") ranges.push(`Attack ${d.attack_range_ft} ft`);
  for (const [k, v] of Object.entries(d.speeds || {})) ranges.push(`${_cap(k)} ${v} ft`);
  for (const [k, v] of Object.entries(d.senses || {})) ranges.push(`${_cap(k)} ${v} ft`);
  if (ranges.length) body.append(infoRow("Ranges", el("span", { text: ranges.join(" · ") })));

  // resistances / immunities / vulnerabilities (monster)
  if (d.kind === "monster") {
    body.append(infoRow("Resist", dmgTypeList(d.resistances)));
    body.append(infoRow("Immune", dmgTypeList(d.immunities)));
    body.append(infoRow("Vulnerable", dmgTypeList(d.vulnerabilities)));
    const ci = d.condition_immunities.length
      ? el("span", {}, d.condition_immunities.map((c) => el("span", { class: "cond-chip", text: c })))
      : el("span", { class: "muted", text: "none" });
    body.append(infoRow("Cond. immune", ci));

    // Skills + languages — lower priority, tucked into a collapsible block.
    const more = el("details", { class: "insp-more" }, el("summary", { text: "Skills & languages" }));
    const skills = (d.skills && d.skills.length)
      ? el("span", { text: d.skills.map(([n, m]) => `${_cap(n)} ${_sign(m)}`).join(" · ") })
      : el("span", { class: "muted", text: "none" });
    const langs = (d.languages && d.languages.length)
      ? el("span", { text: d.languages.join(", ") })
      : el("span", { class: "muted", text: "none" });
    more.append(infoRow("Skills", skills), infoRow("Languages", langs));
    body.append(more);
  }

  _panelBody.replaceChildren(body);
}

function paint() { if (_bar) renderTeamBar(_bar); draw(); }            // refresh team counts + canvas
async function reload() {
  board = await api.get("/api/board");
  await loadCasterLinks();
  if (_bar) renderTeamBar(_bar);
  await fetchOverlays();   // target lines + selected-token highlights, then draw
}

async function loadCasterLinks() {
  try {
    const casters = (await api.get("/api/casters")).casters;
    _casterByToken = new Map(casters.filter((c) => c.token_id != null).map((c) => [c.token_id, c]));
  } catch { _casterByToken = new Map(); }
}
function tk(id) { return board.tokens.find((t) => t.id === id); }

async function fetchOverlays() {
  try { const d = await api.get("/api/board/targets"); _lines = d.lines; _ranges = d.ranges || []; }
  catch { _lines = []; _ranges = []; }
  const ids = [...selected];
  if (ids.length === 1) {
    try {
      const d = await api.get(`/api/board/inference/${ids[0]}`);
      _infl = { rangeCells: d.range_cells, flanked: new Set(d.flanked_ids) };
      updateInfo(d, tk(ids[0]));
      _panelData = d.panel;
      // auto-show on: expand for the new token; off: collapse (so the toggle actually sticks).
      _panelOpen = _panelAuto;
    } catch { _infl = null; updateInfo(null); _panelData = null; }
  } else {
    _infl = null;
    updateInfo(null);
    _panelData = null;
  }
  renderSelBar();
  renderPanel();
  applyPanelState();
  draw();
}

function updateInfo(d, token) {
  if (!_infoEl) return;
  // Only the target + out-of-range note lives here now; everything else (name, HP,
  // roll type, conditions…) is in the Token info panel.
  if (!d || !token || token.kind !== "monster") { _infoEl.textContent = ""; return; }
  const tgt = d.target_id ? tk(d.target_id) : null;
  _infoEl.textContent = `target: ${tgt ? tgt.data_ref : "none"}${tgt && !d.target_in_range ? " ⚠ out of range" : ""}`;
}

// ── pointer interactions ─────────────────────────────────────────────────────
// Map a pointer event to the canvas DRAWING space (CSS-px grid coords), correcting
// for any difference between the canvas's displayed size and its buffer — this is
// what keeps hit-testing and drag deltas aligned with the rendered grid.
function localXY(e) {
  const r = canvas.getBoundingClientRect();
  const W = board.width * CELL, H = board.height * CELL;
  return [(e.clientX - r.left) * (W / r.width), (e.clientY - r.top) * (H / r.height)];
}

function onPointerDown(e) {
  if (e.button === 2) return;  // right-click handled by contextmenu
  const multi = e.ctrlKey || e.shiftKey || _multiSelect;  // Multi-select button == holding Ctrl
  const [x, y] = localXY(e);
  const t = tokenAt(x, y);
  if (!t) {
    // Empty space → begin a box-select. Selection is applied (or cleared, if it
    // stays a plain click) on pointerup, so a drag can rubber-band tokens.
    drag.active = false;
    marquee.active = true;
    marquee.additive = multi;
    marquee.moved = false;
    marquee.x0 = marquee.x1 = x; marquee.y0 = marquee.y1 = y;
    return;
  }
  if (multi) {
    selected.has(t.id) ? selected.delete(t.id) : selected.add(t.id);
  } else if (!selected.has(t.id)) {
    selected.clear(); selected.add(t.id);
  }
  drag.active = true; drag.moved = false;
  drag.startCol = Math.floor(x / CELL); drag.startRow = Math.floor(y / CELL);
  drag.origins = new Map([...selected].map((id) => { const o = tk(id); return [id, { col: o.col, row: o.row }]; }));
  // Touch long-press → context menu (no right-click on touch devices).
  clearTimeout(_lpTimer);
  if (e.pointerType === "touch") {
    _lpTimer = setTimeout(() => { _lpTimer = null; drag.active = false; showTokenMenu(t, e.clientX, e.clientY); }, 500);
  }
  fetchOverlays();  // selection changed → refresh highlights/info
}

// Live cell-snapped move: update token data directly so the view never desyncs
// from the data (no separate "visual offset" that could fail to commit).
function onPointerMove(e) {
  if (marquee.active) {
    const [mx, my] = localXY(e);
    marquee.x1 = mx; marquee.y1 = my;
    if (Math.abs(mx - marquee.x0) > 3 || Math.abs(my - marquee.y0) > 3) marquee.moved = true;
    draw();
    return;
  }
  if (!drag.active) return;
  const [x, y] = localXY(e);
  const dCol = Math.floor(x / CELL) - drag.startCol;
  const dRow = Math.floor(y / CELL) - drag.startRow;
  if (dCol !== 0 || dRow !== 0) { drag.moved = true; clearTimeout(_lpTimer); }
  let changed = false;
  for (const [id, o] of drag.origins) {
    const col = Math.max(0, Math.min(board.width - 1, o.col + dCol));
    const row = Math.max(0, Math.min(board.height - 1, o.row + dRow));
    const t = tk(id);
    if (t && (t.col !== col || t.row !== row)) { t.col = col; t.row = row; changed = true; }
  }
  if (changed) draw();
}

async function onPointerUp(e) {
  clearTimeout(_lpTimer);
  if (marquee.active) {
    marquee.active = false;
    if (marquee.moved) {
      if (!marquee.additive) selected.clear();
      const x0 = Math.min(marquee.x0, marquee.x1), x1 = Math.max(marquee.x0, marquee.x1);
      const y0 = Math.min(marquee.y0, marquee.y1), y1 = Math.max(marquee.y0, marquee.y1);
      for (const t of board.tokens) {
        const [cx, cy] = cellCenter(t.col, t.row);
        if (cx >= x0 && cx <= x1 && cy >= y0 && cy <= y1) selected.add(t.id);
      }
    } else if (!marquee.additive) {
      selected.clear();   // plain click on empty space → deselect
    }
    fetchOverlays();      // refresh highlights/info + redraw
    return;
  }
  if (!drag.active) return;
  drag.active = false;

  // Dropped on a team box → assign team (and restore positions, since this drag
  // was for team assignment, not movement).
  const over = e && document.elementFromPoint(e.clientX, e.clientY);
  const box = over && over.closest && over.closest(".team-box");
  if (box && box.dataset.team) {
    for (const [id, o] of drag.origins) { const t = tk(id); if (t) { t.col = o.col; t.row = o.row; } }
    draw();
    await patchAll([...drag.origins.keys()], { team: box.dataset.team });
    return;
  }

  if (!drag.moved) return;  // a plain click — selection already handled on pointerdown
  const calls = [...drag.origins.keys()].map((id) => {
    const t = tk(id);
    return t ? api.patch(`/api/board/tokens/${id}`, { col: t.col, row: t.row }) : null;
  }).filter(Boolean);
  try { await Promise.all(calls); fetchOverlays(); }  // positions changed → refresh lines/highlights
  catch (err) { toast(err.message, true); reload(); }
}

// ── context menu ───────────────────────────────────────────────────────────
function onContextMenu(e) {
  e.preventDefault();
  const [x, y] = localXY(e);
  const t = tokenAt(x, y);
  if (!t) return;
  showTokenMenu(t, e.clientX, e.clientY);
}

function showTokenMenu(t, clientX, clientY) {
  if (!selected.has(t.id)) { selected.clear(); selected.add(t.id); fetchOverlays(); }
  const ids = [...selected];
  const primary = tk(ids[ids.length - 1]) || t;
  const n = ids.length;
  const items = [
    { header: n > 1 ? `${n} tokens` : `${primary.data_ref} (${primary.kind})` },
    { label: "Set HP…", onClick: () => setHpDialog(ids) },
    { label: "Conditions…", onClick: () => conditionsDialog(ids, primary) },
    { label: "Assign team…", onClick: () => assignTeamDialog(ids) },
    { label: primary.active ? "Deactivate" : "Activate",
      onClick: () => patchAll(ids, { active: !primary.active }) },
  ];
  const monsterIds = ids.filter((id) => { const t = tk(id); return t && t.kind === "monster"; });
  if (monsterIds.length) {
    items.push({ label: monsterIds.length > 1 ? `Cycle target (${monsterIds.length})` : "Cycle target",
      onClick: () => retarget(monsterIds, primary.id) });
  }
  if (n === 1 && _casterByToken.has(primary.id)) {
    const caster = _casterByToken.get(primary.id);
    items.push({ label: "Go to spells", onClick: () => window.dispatchEvent(new CustomEvent("navigate", {
      detail: { tab: "spellcasters", selectCasterId: caster.id } })) });
  }
  // Exactly two tokens (with at least one monster) → send to the Attack tab.
  if (n === 2) {
    const a = tk(ids[0]), b = tk(ids[1]);
    if (a && b && (a.kind === "monster" || b.kind === "monster")) {
      items.push({ label: "Send to Attack tab", onClick: () => sendToAttack(a, b) });
    }
  }
  // Any selected monster tokens → preload the mass saving-throw panel.
  const monsterTokens = ids.map((id) => tk(id)).filter((t) => t && t.kind === "monster");
  if (monsterTokens.length) {
    items.push({ label: "Mass saving throw…", onClick: () => sendToMassSaves(monsterTokens) });
  }
  items.push({ separator: true });
  items.push({ label: n > 1 ? `Remove ${n} tokens` : "Remove token", onClick: () => removeTokens(ids) });
  popupMenu(clientX, clientY, items);
}

async function retarget(tokenIds, primaryId) {
  const ids = Array.isArray(tokenIds) ? tokenIds : [tokenIds];
  try {
    const r = await api.post("/api/board/retarget", { token_ids: ids, primary_id: primaryId ?? ids[ids.length - 1] });
    if (r && r.blocked) toast("Blocked by range — no reachable target.", true);
    fetchOverlays();
  } catch (err) { toast(err.message, true); }
}

// Two selected tokens → Attack tab. Player+monster: monster attacks, player defends.
// Two monsters: the first-selected (a = ids[0]) attacks.
function sendToAttack(a, b) {
  let attacker, defender;
  if (a.kind === "monster" && b.kind !== "monster") { attacker = a; defender = b; }
  else if (b.kind === "monster" && a.kind !== "monster") { attacker = b; defender = a; }
  else if (a.kind === "monster" && b.kind === "monster") { attacker = a; defender = b; }
  else { toast("Need a monster to attack.", true); return; }
  window.dispatchEvent(new CustomEvent("navigate", { detail: {
    tab: "attack", attackerName: attacker.data_ref, defenderName: defender.data_ref } }));
}

// Group selected monster tokens by their roster name (→ count) and preload them
// into the Skills/Saves mass saving-throw panel, mirroring the desktop feature.
function sendToMassSaves(tokens) {
  const counts = {};
  for (const t of tokens) counts[t.data_ref] = (counts[t.data_ref] || 0) + 1;
  const groups = Object.entries(counts).map(([name, count]) => ({ name, count }));
  window.dispatchEvent(new CustomEvent("navigate", { detail: { tab: "skills", massSaves: groups } }));
}

function cycleTeam(ids) {
  const primary = tk(ids[ids.length - 1]);
  const names = board.teams.map((t) => t.name);
  if (!primary || !names.length) return;
  const next = names[(names.indexOf(primary.team) + 1) % names.length];
  patchAll(ids, { team: next });
}

function onBoardKey(e) {
  if (!canvas || !canvas.isConnected) return;                 // only on the board screen
  if (/^(input|textarea|select)$/i.test(document.activeElement?.tagName || "")) return;
  if (document.querySelector(".modal-overlay")) return;       // a dialog owns the keyboard
  const ids = [...selected];
  if (!ids.length && e.key.toLowerCase() !== "r") return;
  const primary = tk(ids[ids.length - 1]);
  switch (e.key) {
    case "r": case "R": {
      const monsterIds = ids.filter((id) => { const t = tk(id); return t && t.kind === "monster"; });
      if (monsterIds.length) retarget(monsterIds, primary && primary.id);
      break;
    }
    case "t": case "T":
      cycleTeam(ids);
      break;
    case "d": case "D":
      if (primary) patchAll(ids, { active: !primary.active });
      break;
    case "h": case "H":
      setHpDialog(ids);
      break;
    case "Delete": case "Backspace":
      e.preventDefault();
      removeTokens(ids);
      break;
  }
}

async function patchAll(ids, body) {
  try { await Promise.all(ids.map((id) => api.patch(`/api/board/tokens/${id}`, body))); }
  catch (err) { toast(err.message, true); }
  reload();
}

async function removeTokens(ids) {
  try { await Promise.all(ids.map((id) => api.del(`/api/board/tokens/${id}`))); }
  catch (err) { toast(err.message, true); }
  selected.clear(); reload();
}

function setHpDialog(ids) {
  const input = el("input", { type: "text", placeholder: "e.g. 12, +5, -3" });
  const body = el("div", {}, [
    el("p", { class: "muted", text: "Set HP: a number, or +N / -N to adjust." }),
    el("div", { class: "field" }, [el("label", { text: "HP" }), input]),
    el("div", { class: "btn-row" }, [el("button", { class: "btn primary", onclick: apply }, "Apply")]),
  ]);
  const dlg = modal("Set HP", body);
  input.focus();
  async function apply() {
    const raw = input.value.trim();
    const calls = ids.map((id) => {
      const t = tk(id);
      let hp;
      if (raw.startsWith("+")) hp = t.hp + (+raw.slice(1) || 0);
      else if (raw.startsWith("-")) hp = t.hp - (+raw.slice(1) || 0);
      else hp = +raw;
      if (Number.isNaN(hp)) return null;
      return api.patch(`/api/board/tokens/${id}`, { hp });
    }).filter(Boolean);
    try { await Promise.all(calls); } catch (err) { toast(err.message, true); }
    dlg.close(); reload();
  }
}

// Conditions that imply "incapacitated" (can't attack). The UI auto-adds/removes
// incapacitated with them, but it stays independently toggleable for overrides.
const INCAP_PARENTS = ["paralyzed", "petrified", "stunned", "unconscious"];

function conditionsDialog(ids, primary) {
  const others = board.tokens.filter((t) => !ids.includes(t.id));
  const wrap = el("div");

  function render() {
    const cur = new Set((tk(primary.id) || primary).conditions);
    const grid = el("div", { class: "check-grid" });
    for (const cond of store.constants.conditions) {
      if (cond === "charmed") continue;          // charmed has its own row (needs a charmer)
      const cb = el("input", { type: "checkbox" });
      if (cur.has(cond)) cb.checked = true;
      cb.addEventListener("change", async () => { await toggleCondition(ids, cond, cb.checked); render(); });
      grid.append(el("label", { class: "toggle" }, [cb, cond]));
    }

    // charmed + charmer picker
    const charmCb = el("input", { type: "checkbox" });
    if (cur.has("charmed")) charmCb.checked = true;
    const charmerSel = el("select", {}, [
      el("option", { value: "" }, "— charmer —"),
      ...others.map((t) => el("option", { value: t.id }, `${t.data_ref} (${t.team})`)),
    ]);
    const pc = (tk(primary.id) || primary).charmed_by;
    if (pc) charmerSel.value = pc;
    charmerSel.disabled = !charmCb.checked || !others.length;
    charmCb.addEventListener("change", async () => {
      if (charmCb.checked) {
        if (!charmerSel.value && others.length) charmerSel.value = others[0].id;
        if (!charmerSel.value) { toast("No other token to be the charmer.", true); charmCb.checked = false; return; }
        await setCharm(ids, charmerSel.value);
      } else {
        await clearCharm(ids);
      }
      render();
    });
    charmerSel.addEventListener("change", async () => {
      if (charmCb.checked && charmerSel.value) await setCharm(ids, charmerSel.value);
    });
    grid.append(el("label", { class: "toggle" }, [charmCb, "charmed"]));

    wrap.replaceChildren(
      el("p", { class: "muted", text: "Applies to all selected. Paralyzed/petrified/stunned/unconscious auto-add incapacitated (can't attack)." }),
      grid,
      el("div", { class: "field" }, [el("label", { text: "Charmer" }), charmerSel]),
    );
  }

  render();
  modal("Conditions", wrap, { onClose: reload });
}

async function toggleCondition(ids, cond, add) {
  const calls = ids.map((id) => {
    const t = tk(id);
    const set = new Set(t.conditions);
    add ? set.add(cond) : set.delete(cond);
    // Parent incapacitating conditions auto-link "incapacitated".
    if (INCAP_PARENTS.includes(cond)) {
      if (add) set.add("incapacitated");
      else if (!INCAP_PARENTS.some((p) => set.has(p))) set.delete("incapacitated");
    }
    t.conditions = [...set];  // optimistic
    return api.patch(`/api/board/tokens/${id}`, { conditions: t.conditions });
  });
  try { await Promise.all(calls); } catch (err) { toast(err.message, true); }
}

async function setCharm(ids, charmerId) {
  const calls = ids.map((id) => {
    const t = tk(id);
    const set = new Set(t.conditions); set.add("charmed");
    t.conditions = [...set]; t.charmed_by = charmerId;  // optimistic
    return api.patch(`/api/board/tokens/${id}`, { conditions: t.conditions, charmed_by: charmerId });
  });
  try { await Promise.all(calls); } catch (err) { toast(err.message, true); }
}

async function clearCharm(ids) {
  const calls = ids.map((id) => {
    const t = tk(id);
    const set = new Set(t.conditions); set.delete("charmed");
    t.conditions = [...set]; t.charmed_by = null;  // optimistic
    return api.patch(`/api/board/tokens/${id}`, { conditions: t.conditions, charmed_by: null });
  });
  try { await Promise.all(calls); } catch (err) { toast(err.message, true); }
}

function assignTeamDialog(ids) {
  const rows = board.teams.map((tm) => el("button", {
    class: "btn neutral", style: `border-left: 6px solid ${tm.color}`,
    onclick: async () => { await patchAll(ids, { team: tm.name }); dlg.close(); },
  }, tm.name));
  const dlg = modal("Assign to team", el("div", { class: "btn-row vert" }, rows));
}

// ── add tokens ───────────────────────────────────────────────────────────────
function openAddDialog(col = null, row = null) {
  const body = el("div");
  const addOne = async (kind, id) => {
    const payload = { kind, ref_id: id };
    if (col != null) { payload.col = col; payload.row = row; }
    await api.post("/api/board/tokens", payload);
    dlg.close(); reload();
  };
  const section = (title, kind, roster) => {
    const list = el("div", { class: "list" });
    for (const e of roster) {
      list.append(el("div", { class: "row", onclick: () => addOne(kind, e.id) }, e.name_str || "(unnamed)"));
    }
    if (!roster.length) list.append(el("div", { class: "placeholder", text: "none" }));
    return el("div", {}, [el("div", { class: "subhead", text: title }), list]);
  };
  body.append(
    section("Players", "player", store.state.players),
    section("Monsters", "monster", store.state.monsters),
    el("div", { class: "btn-row" }, [
      el("button", { class: "btn neutral", onclick: () => addAll("player") }, "Add all players"),
      el("button", { class: "btn neutral", onclick: () => addAll("monster") }, "Add all monsters"),
    ]),
  );
  const dlg = modal("Add token", body);
  async function addAll(kind) { await api.post("/api/board/tokens/add-all", { kind }); dlg.close(); reload(); }
}

// ── teams bar ────────────────────────────────────────────────────────────────
function renderTeamBar(barEl) {
  barEl.replaceChildren(el("span", { class: "muted", text: "Teams:" }));
  const counts = {};
  for (const t of board.tokens) counts[t.team] = (counts[t.team] || 0) + 1;
  for (const tm of board.teams) {
    const box = el("div", {
      class: "team-box", style: `background:${tm.color}`, "data-team": tm.name,
      // Tap with a selection → assign it to this team; tap with nothing selected →
      // open the team menu (so rename/recolor/delete is reachable on touch too).
      onclick: (e) => {
        if (selected.size) {
          const ids = [...selected];
          patchAll(ids, { team: tm.name });
          toast(`${ids.length} → ${tm.name}`);
        } else {
          teamMenu(e, tm);
        }
      },
      oncontextmenu: (e) => { e.preventDefault(); teamMenu(e, tm); },
    }, `${tm.name} (${counts[tm.name] || 0})`);
    barEl.append(box);
  }
  barEl.append(el("button", { class: "btn neutral", onclick: addTeam }, "+ Team"));
}

function addTeam() {
  promptDialog("New team", { placeholder: "Team name", okLabel: "Add", onSubmit: async (name) => {
    try { board = await api.post("/api/board/teams", { name }); paint(); }
    catch (err) { toast(err.message, true); }
  } });
}

function teamMenu(e, tm) {
  popupMenu(e.clientX, e.clientY, [
    { header: `Team: ${tm.name}` },
    { label: "Rename…", onClick: () => {
        promptDialog("Rename team", { value: tm.name, okLabel: "Rename", onSubmit: async (n) => {
          try { board = await api.patch(`/api/board/teams/${encodeURIComponent(tm.name)}`, { new_name: n }); paint(); }
          catch (err) { toast(err.message, true); }
        } });
      } },
    { label: "Change color…", onClick: () => recolor(tm) },
    { label: "Delete", onClick: async () => {
        try { board = await api.del(`/api/board/teams/${encodeURIComponent(tm.name)}`); paint(); }
        catch (err) { toast(err.message, true); }
      } },
  ]);
}

function recolor(tm) {
  const input = el("input", { type: "color", value: tm.color });
  const dlg = modal("Team color", el("div", {}, [
    input,
    el("div", { class: "btn-row" }, [el("button", { class: "btn primary", onclick: async () => {
      try { board = await api.patch(`/api/board/teams/${encodeURIComponent(tm.name)}`, { color: input.value }); paint(); }
      catch (err) { toast(err.message, true); }
      dlg.close();
    } }, "Apply")]),
  ]));
}

// ── resolve ──────────────────────────────────────────────────────────────────
async function doResolve() {
  let data;
  try { data = await api.post("/api/board/resolve"); }
  catch (err) { toast(err.message, true); return; }
  const body = el("div");
  if (!data.pairs.length) body.append(el("p", { class: "muted", text: "No active monster → target pairs." }));
  const applies = [];
  for (const p of data.pairs) {
    const mods = [`roll: ${p.roll_mod}`];
    if (p.tohit_bonus) mods.push(`+${p.tohit_bonus} flank`);
    let hdr = `${p.attacker} → ${p.defender}  [${mods.join(", ")}]`;
    if (p.auto_crit) hdr += "  ⚡ AUTO-CRIT";
    if (p.charm_warning) hdr += "  💗 ATTACKING CHARMER";
    if (p.out_of_range) hdr += "  ⚠ OUT OF RANGE";
    const card = el("div", { class: "attack-card" }, [
      el("div", { class: "swing-head", text: hdr }),
      renderSwings(p.rolls),
    ]);
    if (p.defender_concentrating) {
      card.append(el("div", { class: "insp-note", text: `💜 ${p.defender} needs a concentration saving throw` }));
    }
    const cb = el("input", { type: "checkbox" });
    if (p.applied > 0) { cb.checked = true; applies.push({ cb, token_id: p.defender_id, amount: p.applied }); }
    card.append(el("label", { class: "toggle" }, [
      cb, "Apply  ", breakdownInline(p.breakdown_parts, p.applied),
      `  →  ${p.defender}  (HP ${p.defender_hp}/${p.defender_max_hp})`,
    ]));
    body.append(card);
  }
  if (data.skipped && data.skipped.length) {
    body.append(el("p", { class: "muted", text: "Skipped (no target / blocked): " + data.skipped.join(", ") }));
  }
  const dlg = modal("Resolve board", body);
  body.append(el("div", { class: "btn-row" }, [
    el("button", { class: "btn primary", onclick: async () => {
      const payload = applies.filter((a) => a.cb.checked).map((a) => ({ token_id: a.token_id, amount: a.amount }));
      try { await api.post("/api/board/apply-damage", { applies: payload }); }
      catch (err) { toast(err.message, true); }
      dlg.close(); reload();
    } }, "Apply checked & close"),
    el("button", { class: "btn neutral", onclick: () => dlg.close() }, "Close"),
  ]));
}

// ── screen ───────────────────────────────────────────────────────────────────
export async function renderBoard(root) {
  await store.refreshState();
  board = await api.get("/api/board");
  await loadCasterLinks();
  selected.clear();
  if (_presetTokenId != null) {
    if (board.tokens.some((t) => t.id === _presetTokenId)) selected.add(_presetTokenId);
    _presetTokenId = null;
  }
  root.replaceChildren();

  root.append(el("div", { class: "btn-row" }, [
    el("button", { class: "btn primary", onclick: () => openAddDialog() }, "Add token"),
    el("button", { class: "btn neutral", onclick: async () => { await api.post("/api/board/clear-deactivated"); reload(); } }, "Clear deactivated"),
    el("button", { class: "btn danger", onclick: async () => { await api.post("/api/board/clear"); selected.clear(); reload(); } }, "Clear board"),
    el("button", { class: "btn primary", onclick: doResolve }, "Resolve board"),
    el("button", { class: "btn neutral", onclick: showBoardHelp }, "Help"),
  ]));

  const bar = el("div", { class: "team-bar" });
  _bar = bar;
  renderTeamBar(bar);
  root.append(bar);

  _selBar = el("div", { class: "sel-bar" });
  renderSelBar();
  root.append(_selBar);

  _infoEl = el("div", { class: "board-info muted" });
  root.append(_infoEl);

  canvas = el("canvas", { class: "board-canvas", width: board.width * CELL, height: board.height * CELL });
  ctx = canvas.getContext("2d");
  canvas.addEventListener("pointerdown", onPointerDown);
  canvas.addEventListener("contextmenu", onContextMenu);
  canvas.addEventListener("dblclick", (e) => {
    const [x, y] = localXY(e);
    const t = tokenAt(x, y);
    if (t) {
      // Jump to this token's entry in the Monsters/Players tab.
      window.dispatchEvent(new CustomEvent("navigate", { detail: {
        tab: t.kind === "monster" ? "monsters" : "players", selectName: t.data_ref } }));
    } else {
      const [c, r] = cellAt(x, y); openAddDialog(c, r);
    }
  });
  _panelEl = el("aside", { class: "token-panel" });
  buildPanelShell();
  root.append(el("div", { class: "board-layout" }, [
    el("div", { class: "board-wrap" }, canvas),
    _panelEl,
  ]));
  // Window-level (bound once): move/up so a drag commits even if released off the
  // canvas, and the board keyboard shortcuts (R/T/D/H/Delete).
  if (!_dragBound) {
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", () => { drag.active = false; marquee.active = false; });
    window.addEventListener("keydown", onBoardKey);
    _dragBound = true;
  }

  fetchOverlays();   // initial target lines (+ highlights once something is selected)
}

// Board usage tips — shown from the "Help" button (was a permanent line at the bottom).
const BOARD_HELP = [
  "Tap/click a token to select it.",
  "Ctrl-click (or the Multi-select button) to select several.",
  "Drag empty space to box-select; drag a token to move it.",
  "Tap a team name to assign the current selection to it.",
  "Use the action bar (or right-click / keys R T D H Del) for token actions.",
  "Double-tap an empty cell to add a token there.",
];
function showBoardHelp() {
  modal("Battle board — help", el("div", {},
    BOARD_HELP.map((line) => el("p", { class: "muted", text: line }))));
}
