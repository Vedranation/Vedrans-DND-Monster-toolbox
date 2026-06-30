// Skills / Saves — mass monster saving throws, quick save, party skill check.

import { api } from "../api.js";
import { store } from "../store.js";
import { el, toast } from "../dom.js";
import { d20Span } from "../swings.js";

const sel = (values, value) => {
  const s = el("select", {}, values.map((v) => el("option", { value: v }, v)));
  s.value = value;
  return s;
};
const monSel = (monsters) => el("select", {}, monsters.map((m) => el("option", { value: m.id }, m.name_str || "(unnamed)")));
const numInput = (v) => el("input", { type: "number", value: v });
const field = (label, node) => el("div", { class: "field" }, [el("label", { text: label }), node]);
const _capWords = (s) => s.replace(/\b\w/g, (c) => c.toUpperCase());
const skillSel = (skills, value) => {
  const s = el("select", {}, skills.map((v) => el("option", { value: v }, _capWords(v))));
  s.value = value;
  return s;
};
const sign = (n) => (n >= 0 ? "+" : "") + n;

// Briefly outline a panel to draw attention when navigated to from another tab.
function flash(panel) {
  setTimeout(() => {
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
    panel.classList.add("flash-highlight");
    setTimeout(() => panel.classList.remove("flash-highlight"), 2000);
  }, 0);
}

let _presetMassSaves = null;   // [{name, count}] from the board's "Mass saving throw…"
let _presetQuickSave = null;   // {monsterName, save, dc} from a caster's "Concentration save"

// Preload the mass-save panel with grouped monster tokens, then navigate to "skills".
export function presetMassSaves(groups) { _presetMassSaves = groups; }
// Preload the quick monster save (e.g. concentration: a monster + CON + DC), then navigate.
export function presetQuickSave(opts) { _presetQuickSave = opts; }

export async function renderSkills(root) {
  await store.refreshState();
  const C = store.constants;
  const monsters = store.state.monsters;
  const players = store.state.players;

  root.replaceChildren();
  const grid = el("div", { class: "skills-grid" });

  grid.append(
    massSavesPanel(C, monsters), quickSavePanel(C, monsters),
    massMonsterSkillPanel(C, monsters), quickMonsterSkillPanel(C, monsters),
    partySkillPanel(C, players),
  );
  root.append(grid);
}

// ── mass monster saving throws ─────────────────────────────────────────────
function massSavesPanel(C, monsters) {
  const panel = el("div", { class: "panel" }, el("h3", { text: "Mass monster saving throws" }));
  const save = sel(C.saving_throw_types, "DEX");
  const dc = numInput(15);
  const rt = sel(["Monster default", ...C.roll_types], "Monster default");
  panel.append(field("Save", save), field("DC", dc), field("Roll type", rt));

  const rowsWrap = el("div");
  const rows = [];
  const addRow = (monsterId, count) => {
    const m = monSel(monsters);
    if (monsterId) m.value = monsterId;
    const cnt = numInput(count ?? 1); cnt.style.maxWidth = "64px";
    const rowEl = el("div", { class: "mass-row" }, [
      m, el("span", { text: "×" }), cnt,
      el("button", { class: "btn neutral", onclick: () => { rowEl.remove(); const i = rows.findIndex((r) => r.rowEl === rowEl); if (i >= 0) rows.splice(i, 1); } }, "✕"),
    ]);
    rows.push({ rowEl, m, cnt });
    rowsWrap.append(rowEl);
  };
  if (monsters.length) {
    // Board "Mass saving throw…" preset: one row per monster name (mapped to id).
    const preset = _presetMassSaves;
    _presetMassSaves = null;
    if (preset && preset.length) {
      for (const g of preset) {
        const mm = monsters.find((x) => x.name_str === g.name);
        if (mm) addRow(mm.id, g.count);
      }
      flash(panel);   // arrived from the board → draw attention to this panel
    }
    if (!rows.length) { addRow(); addRow(); }   // no preset (or none matched) → defaults
  } else {
    _presetMassSaves = null;
    rowsWrap.append(el("div", { class: "placeholder", text: "No monsters yet." }));
  }

  const results = el("div", { class: "roll-results" });
  panel.append(rowsWrap, el("div", { class: "btn-row" }, [
    el("button", { class: "btn neutral", onclick: addRow, disabled: !monsters.length }, "+ Add row"),
    el("button", { class: "btn primary", onclick: roll, disabled: !monsters.length }, "Roll mass saves"),
  ]), results);

  async function roll() {
    const groups = rows.map((r) => ({ monster_id: r.m.value, count: +r.cnt.value })).filter((g) => g.count > 0);
    if (!groups.length) { toast("Add at least one monster row.", true); return; }
    let data;
    try { data = await api.post("/api/rolls/mass-saves", { save: save.value, dc: +dc.value, roll_type: rt.value, groups }); }
    catch (err) { toast(err.message, true); return; }
    results.replaceChildren();
    for (const g of data.results) {
      results.append(el("div", {}, [
        el("span", { text: `${g.name}: ` }),
        el("span", { style: "color:#33aa55", text: `${g.passes} passed` }),
        ", ",
        el("span", { style: "color:#cc3333", text: `${g.fails} failed` }),
        el("span", { class: "muted", text: `  (${g.roll_type}, ${sign(g.modifier)})` }),
      ]));
    }
    results.append(el("div", { class: "swing-total", text: `Total: ${data.total_pass}/${data.total} passed DC ${data.dc}` }));
  }
  return panel;
}

// ── quick monster save ──────────────────────────────────────────────────────
function quickSavePanel(C, monsters) {
  const panel = el("div", { class: "panel" }, el("h3", { text: "Quick monster save" }));
  if (!monsters.length) { panel.append(el("div", { class: "placeholder", text: "No monsters yet." })); return panel; }
  const m = monSel(monsters);
  const save = sel(C.saving_throw_types, "DEX");
  const rt = sel(["Monster default", ...C.roll_types], "Monster default");
  const dc = el("input", { type: "number", placeholder: "—" }); dc.style.maxWidth = "64px";
  const res = el("div", { class: "roll-results" });

  // Concentration-save preset (from a caster card): select monster by name, set CON + DC.
  if (_presetQuickSave) {
    const p = _presetQuickSave; _presetQuickSave = null;
    if (p.monsterName) { const mm = monsters.find((x) => x.name_str === p.monsterName); if (mm) m.value = mm.id; }
    if (p.save) save.value = p.save;
    if (p.dc != null) dc.value = p.dc;
    flash(panel);
  }

  panel.append(field("Monster", m), field("Save", save), field("Roll type", rt),
    field("DC (optional)", dc),
    el("div", { class: "btn-row" }, [el("button", { class: "btn primary", onclick: roll }, "Roll save")]), res);

  async function roll() {
    let d;
    try { d = await api.post("/api/rolls/quick-save", { monster_id: m.value, save: save.value, roll_type: rt.value }); }
    catch (err) { toast(err.message, true); return; }
    const color = d.is_nat1 ? "#cc3333" : d.is_nat20 ? "#228822" : "var(--txt)";
    const line = el("div", { class: "swing-total", style: `color:${color}; font-size:17px` }, [
      d20Span(d.d20s, d.d20), ` ${sign(d.modifier)} = ${d.total}`,
    ]);
    res.replaceChildren(line);
    const dcVal = dc.value === "" ? null : +dc.value;
    if (dcVal != null) {
      const pass = d.total >= dcVal;
      line.append(el("span", { style: `color:${pass ? "#33aa55" : "#cc3333"}`, text: `  ${pass ? "PASS" : "FAIL"} (DC ${dcVal})` }));
    }
  }
  return panel;
}

// ── mass monster skill check ───────────────────────────────────────────────
function massMonsterSkillPanel(C, monsters) {
  const panel = el("div", { class: "panel" }, el("h3", { text: "Mass monster skill check" }));
  const skill = skillSel(C.all_skills || C.skills, "perception");
  const dc = numInput(15);
  const rt = sel(["Monster default", ...C.roll_types], "Monster default");
  panel.append(field("Skill", skill), field("DC", dc), field("Roll type", rt));

  const rowsWrap = el("div");
  const rows = [];
  const addRow = () => {
    const m = monSel(monsters);
    const cnt = numInput(1); cnt.style.maxWidth = "64px";
    const rowEl = el("div", { class: "mass-row" }, [
      m, el("span", { text: "×" }), cnt,
      el("button", { class: "btn neutral", onclick: () => { rowEl.remove(); const i = rows.findIndex((r) => r.rowEl === rowEl); if (i >= 0) rows.splice(i, 1); } }, "✕"),
    ]);
    rows.push({ rowEl, m, cnt });
    rowsWrap.append(rowEl);
  };
  if (monsters.length) { addRow(); addRow(); }
  else rowsWrap.append(el("div", { class: "placeholder", text: "No monsters yet." }));

  const results = el("div", { class: "roll-results" });
  panel.append(rowsWrap, el("div", { class: "btn-row" }, [
    el("button", { class: "btn neutral", onclick: addRow, disabled: !monsters.length }, "+ Add row"),
    el("button", { class: "btn primary", onclick: roll, disabled: !monsters.length }, "Roll mass checks"),
  ]), results);

  async function roll() {
    const groups = rows.map((r) => ({ monster_id: r.m.value, count: +r.cnt.value })).filter((g) => g.count > 0);
    if (!groups.length) { toast("Add at least one monster row.", true); return; }
    let data;
    try { data = await api.post("/api/rolls/mass-skill-check", { skill: skill.value, dc: +dc.value, roll_type: rt.value, groups }); }
    catch (err) { toast(err.message, true); return; }
    results.replaceChildren();
    for (const g of data.results) {
      results.append(el("div", {}, [
        el("span", { text: `${g.name}: ` }),
        el("span", { style: "color:#33aa55", text: `${g.passes} passed` }),
        ", ",
        el("span", { style: "color:#cc3333", text: `${g.fails} failed` }),
        el("span", { class: "muted", text: `  (${g.roll_type}, ${sign(g.modifier)})` }),
      ]));
    }
    results.append(el("div", { class: "swing-total", text: `Total: ${data.total_pass}/${data.total} passed DC ${data.dc}` }));
  }
  return panel;
}

// ── quick monster skill check ───────────────────────────────────────────────
function quickMonsterSkillPanel(C, monsters) {
  const panel = el("div", { class: "panel" }, el("h3", { text: "Quick monster skill check" }));
  if (!monsters.length) { panel.append(el("div", { class: "placeholder", text: "No monsters yet." })); return panel; }
  const m = monSel(monsters);
  const skill = skillSel(C.all_skills || C.skills, "perception");
  const rt = sel(["Monster default", ...C.roll_types], "Monster default");
  const res = el("div", { class: "roll-results" });
  panel.append(field("Monster", m), field("Skill", skill), field("Roll type", rt),
    el("div", { class: "btn-row" }, [el("button", { class: "btn primary", onclick: roll }, "Roll check")]), res);

  async function roll() {
    let d;
    try { d = await api.post("/api/rolls/monster-skill-check", { monster_id: m.value, skill: skill.value, roll_type: rt.value }); }
    catch (err) { toast(err.message, true); return; }
    const color = d.is_nat1 ? "#cc3333" : d.is_nat20 ? "#228822" : "var(--txt)";
    res.replaceChildren(el("div", { class: "swing-total", style: `color:${color}; font-size:17px` }, [
      d20Span(d.d20s, d.d20), ` ${sign(d.modifier)} = ${d.total}`,
    ]));
  }
  return panel;
}

// ── party skill check ─────────────────────────────────────────────────────────
function partySkillPanel(C, players) {
  const panel = el("div", { class: "panel" }, el("h3", { text: "Party skill check" }));
  const skill = el("select", {}, C.skills.map((s) => el("option", { value: s }, s[0].toUpperCase() + s.slice(1))));
  const dc = numInput(15);
  const res = el("div", { class: "roll-results" });
  panel.append(field("Skill", skill), field("DC", dc),
    el("div", { class: "btn-row" }, [el("button", { class: "btn primary", onclick: roll, disabled: !players.length }, "Roll for party")]),
    players.length ? res : el("div", { class: "placeholder", text: "No players yet." }));

  async function roll() {
    let data;
    try { data = await api.post("/api/rolls/party-skill-check", { skill: skill.value, dc: +dc.value }); }
    catch (err) { toast(err.message, true); return; }
    res.replaceChildren();
    for (const r of data.results) {
      const color = r.status === "Nat1" || r.status === "Failed" ? "#cc3333"
                  : r.status === "Nat20" ? "#228822" : "var(--txt)";
      res.append(el("div", { class: "skillcheck-row", style: `color:${color}` }, [
        el("span", { text: r.name }), el("span", { text: String(r.total) }), el("span", { text: r.status }),
      ]));
    }
  }
  return panel;
}
