// Spellcasters — global spell library (CRUD + 5etools import) and casters
// (level → slot grid, assigned spells, cast/restore).

import { api } from "../api.js";
import { store } from "../store.js";
import { el, modal, toast } from "../dom.js";

let _lib = [];
let _casters = [];
let _tokens = [];       // board tokens (for the caster→token link dropdown)
let _selIdx = -1;       // selected spell in the library
let _filter = "All";
let _presetSpellName = null;   // jump to this spell (from Search)
let _presetCasterId = null;    // scroll/highlight this caster (from board "Go to spells")

export function presetSpell(name) { _presetSpellName = name; }
export function presetCaster(id) { _presetCasterId = id; }

export async function renderSpellcasters(root) {
  _lib = (await api.get("/api/spell-library")).spells;
  _casters = (await api.get("/api/casters")).casters;
  _tokens = (await api.get("/api/board")).tokens;
  if (_presetSpellName) {
    const i = _lib.findIndex((s) => s.name === _presetSpellName);
    if (i >= 0) { _selIdx = i; _filter = "All"; }
    _presetSpellName = null;
  }
  root.replaceChildren();
  root.append(librarySection(root), castersSection(root));
  if (_presetCasterId) {
    const card = root.querySelector(`[data-caster="${_presetCasterId}"]`);
    if (card) {
      card.scrollIntoView({ behavior: "smooth", block: "center" });
      card.classList.add("caster-highlight");
      setTimeout(() => card.classList.remove("caster-highlight"), 2000);
    }
    _presetCasterId = null;
  }
}

async function reloadLib(root) { _lib = (await api.get("/api/spell-library")).spells; renderSpellcasters(root); }
async function reloadCasters(root) { _casters = (await api.get("/api/casters")).casters; renderSpellcasters(root); }

// ── spell library ─────────────────────────────────────────────────────────────
function librarySection(root) {
  const C = store.constants;
  const section = el("div", { class: "panel" }, el("h3", { text: "Global spell library" }));
  const split = el("div", { class: "split" });

  // left: filter + list
  const left = el("div");
  const levels = ["All", "0 (Cantrip)", ...Array.from({ length: 9 }, (_, i) => String(i + 1))];
  const filterSel = el("select", {}, levels.map((l) => el("option", { value: l }, l)));
  filterSel.value = _filter;
  filterSel.addEventListener("change", () => { _filter = filterSel.value; renderSpellcasters(root); });
  const list = el("div", { class: "list" });
  const filtered = _lib
    .map((s, idx) => ({ s, idx }))
    .filter(({ s }) => _filter === "All" || (_filter.startsWith("0") ? s.level === 0 : s.level === +_filter))
    .sort((a, b) => (a.s.level - b.s.level) || a.s.name.localeCompare(b.s.name));
  for (const { s, idx } of filtered) {
    list.append(el("div", { class: "row" + (idx === _selIdx ? " selected" : ""), onclick: () => { _selIdx = idx; renderSpellcasters(root); } },
      `Lv${s.level === 0 ? "C" : s.level}  ${s.name}`));
  }
  if (!filtered.length) list.append(el("div", { class: "placeholder", text: "No spells." }));
  // In-place text filter (no re-render → keeps focus while typing).
  const search = el("input", { type: "text", placeholder: "Search library…", class: "lib-search" });
  search.style.width = "100%";
  search.addEventListener("input", () => {
    const q = search.value.toLowerCase();
    for (const row of list.children) {
      if (row.classList.contains("placeholder")) continue;
      row.style.display = row.textContent.toLowerCase().includes(q) ? "" : "none";
    }
  });
  left.append(el("div", { class: "field" }, [el("label", { text: "Filter level" }), filterSel]), search, list);

  // right: form
  const spell = (_selIdx >= 0 && _selIdx < _lib.length) ? _lib[_selIdx] : null;
  split.append(left, spellForm(root, C, spell));
  section.append(
    el("div", { class: "btn-row" }, [
      el("button", { class: "btn neutral", onclick: () => { _selIdx = -1; renderSpellcasters(root); } }, "New spell"),
      el("button", { class: "btn neutral", onclick: () => openImport(root) }, "Import 5etools"),
    ]),
    split,
  );
  return section;
}

function spellForm(root, C, spell) {
  const s = spell || {};
  const refs = {};
  const tf = (k, v) => { const i = el("input", { type: "text", value: v ?? "" }); refs[k] = i; return i; };
  const ck = (k, v) => { const i = el("input", { type: "checkbox" }); if (v) i.checked = true; refs[k] = i; return i; };

  const name = tf("name", s.name);
  const level = el("select", {}, Array.from({ length: 10 }, (_, i) => el("option", { value: i }, i === 0 ? "Cantrip" : i)));
  level.value = String(s.level ?? 1); refs.level = level;
  const school = el("select", {}, C.spell_schools.map((x) => el("option", { value: x }, x || "—")));
  school.value = s.school ?? ""; refs.school = school;

  // Damage dice (e.g. 8d6) → one-click "Roll dice" sends it to the Dice tab.
  const diceTypes = (C.dice_types && C.dice_types.length) ? C.dice_types : ["d4", "d6", "d8", "d10", "d12", "d20", "d100"];
  const diceCount = el("input", { type: "number", value: s.dice_count ?? 0, min: 0, onfocus: (e) => e.target.select() });
  diceCount.style.maxWidth = "64px"; refs.dice_count = diceCount;
  const diceType = el("select", {}, diceTypes.map((d) => el("option", { value: d }, d)));
  diceType.value = diceTypes.includes(s.dice_type) ? s.dice_type : "d6"; refs.dice_type = diceType;
  const rollDice = el("button", { class: "btn neutral", onclick: () => {
    const n = +diceCount.value || 0;
    if (n <= 0) { toast("Set a dice count first (e.g. 8 for 8d6).", true); return; }
    window.dispatchEvent(new CustomEvent("navigate", { detail: {
      tab: "dice", dice: { count: n, die: diceType.value, modifier: 0 } } }));
  } }, "Roll dice");

  const panel = el("div", { class: "panel" }, [
    el("div", { class: "field" }, [el("label", { text: "Name *" }), name]),
    el("div", { class: "field" }, [el("label", { text: "Level" }), level]),
    el("div", { class: "field" }, [el("label", { text: "School" }), school]),
    el("div", { class: "field" }, [el("label", { text: "Casting time" }), tf("casting_time", s.casting_time)]),
    el("div", { class: "field" }, [el("label", { text: "Range" }), tf("range", s.range)]),
    el("div", { class: "field" }, [el("label", { text: "Duration" }), tf("duration", s.duration)]),
    el("label", { class: "toggle" }, [ck("concentration", s.concentration), "Concentration"]),
    el("div", { class: "flag-row" }, [
      el("label", { class: "toggle" }, [ck("component_v", s.component_v), "V"]),
      el("label", { class: "toggle" }, [ck("component_s", s.component_s), "S"]),
      el("label", { class: "toggle" }, [ck("component_m", s.component_m), "M"]),
    ]),
    el("div", { class: "field" }, [el("label", { text: "Material (gp)" }), tf("material_cost", s.material_cost)]),
    el("label", { class: "toggle" }, [ck("material_consumed", s.material_consumed), "Material consumed"]),
    el("div", { class: "field" }, [el("label", { text: "Damage dice" }),
      el("span", { style: "display:flex; gap:.35rem; align-items:center;" }, [diceCount, diceType, rollDice])]),
  ]);
  const desc = el("textarea", { class: "json" }); desc.value = s.description ?? ""; desc.style.minHeight = "120px";
  panel.append(el("div", { class: "subhead", text: "Description" }), desc);

  const collect = () => ({
    name: refs.name.value.trim(), level: +refs.level.value, school: refs.school.value,
    casting_time: refs.casting_time.value, range: refs.range.value, duration: refs.duration.value,
    concentration: refs.concentration.checked,
    component_v: refs.component_v.checked, component_s: refs.component_s.checked, component_m: refs.component_m.checked,
    material_cost: refs.material_cost.value, material_consumed: refs.material_consumed.checked,
    dice_count: +refs.dice_count.value || 0, dice_type: refs.dice_type.value,
    description: desc.value,
  });

  const buttons = [el("button", { class: "btn primary", onclick: async () => {
    const body = collect();
    if (!body.name) { toast("Spell name is required.", true); return; }
    try {
      if (_selIdx >= 0) await api.put(`/api/spell-library/${_selIdx}`, body);
      else { await api.post("/api/spell-library", body); }
      toast("Saved"); reloadLib(root);
    } catch (err) { toast(err.message, true); }
  } }, _selIdx >= 0 ? "Save" : "Add")];
  if (_selIdx >= 0) buttons.push(el("button", { class: "btn danger", onclick: async () => {
    await api.del(`/api/spell-library/${_selIdx}`); _selIdx = -1; reloadLib(root);
  } }, "Delete"));
  panel.append(el("div", { class: "btn-row" }, buttons));
  return panel;
}

function openImport(root) {
  const ta = el("textarea", { class: "json", placeholder: "Paste a single 5etools spell JSON object…" });
  const status = el("div", { class: "status-line" });
  const dlg = modal("Import 5etools spell", el("div", {}, [
    ta, status,
    el("div", { class: "btn-row" }, [el("button", { class: "btn primary", onclick: async () => {
      let data;
      try { data = JSON.parse(ta.value); } catch (e) { status.textContent = "Invalid JSON: " + e.message; return; }
      try { const r = await api.post("/api/spell-library/import-5etools", data); dlg.close(); toast(`Imported ${r.name}`); reloadLib(root); }
      catch (err) { status.textContent = "Import failed: " + err.message; }
    } }, "Import")]),
  ]));
}

// ── casters ───────────────────────────────────────────────────────────────────
function castersSection(root) {
  const section = el("div", { class: "panel" }, el("h3", { text: "Casters" }));
  section.append(el("div", { class: "btn-row" }, [
    el("button", { class: "btn primary", onclick: async () => { await api.post("/api/casters", { name: "New Caster", level: 1 }); reloadCasters(root); } }, "+ Add caster"),
  ]));
  const wrap = el("div", { class: "skills-grid" });
  for (const c of _casters) wrap.append(casterCard(root, c));
  if (!_casters.length) wrap.append(el("div", { class: "placeholder", text: "No casters yet." }));
  section.append(wrap);
  return section;
}

function casterCard(root, c) {
  const card = el("div", { class: "panel", "data-caster": String(c.id) });
  const name = el("input", { type: "text", value: c.name });
  name.addEventListener("change", () => api.patch(`/api/casters/${c.id}`, { name: name.value }));
  const level = el("input", { type: "number", value: c.level }); level.style.maxWidth = "64px";
  level.addEventListener("change", async () => { await api.patch(`/api/casters/${c.id}`, { level: +level.value }); reloadCasters(root); });

  // Link to a battleboard token; once linked, "Go to token" jumps to it on the board.
  const tokenSel = el("select", {}, [
    el("option", { value: "" }, "— not linked —"),
    ..._tokens.map((t) => el("option", { value: String(t.id) }, `${t.data_ref || "token"} (#${t.id})`)),
  ]);
  tokenSel.value = c.token_id != null ? String(c.token_id) : "";
  tokenSel.addEventListener("change", async () => {
    await api.patch(`/api/casters/${c.id}`, { token_id: tokenSel.value === "" ? null : tokenSel.value });
    reloadCasters(root);
  });
  const linkedTok = _tokens.find((t) => String(t.id) === String(c.token_id));
  const goToken = el("button", {
    class: "btn neutral", disabled: !linkedTok,
    onclick: () => window.dispatchEvent(new CustomEvent("navigate", { detail: { tab: "board", selectTokenId: c.token_id } })),
  }, "Go to token");

  // Concentration: toggle drives the on-token marker (only shown when linked).
  const concCb = el("input", { type: "checkbox" });
  if (c.concentrating) concCb.checked = true;
  concCb.addEventListener("change", async () => {
    await api.patch(`/api/casters/${c.id}`, { concentrating: concCb.checked }); reloadCasters(root);
  });
  // Concentration save → linked monster uses its CON save (incl. adv/dis); otherwise
  // a flat d20+2 (no statblock) sent to the Dice tab. DC 10 either way.
  const concSave = el("button", { class: "btn neutral", onclick: () => {
    if (linkedTok && linkedTok.kind === "monster") {
      window.dispatchEvent(new CustomEvent("navigate", { detail: {
        tab: "skills", quickSave: { monsterName: linkedTok.data_ref, save: "CON", dc: 10 } } }));
    } else {
      window.dispatchEvent(new CustomEvent("navigate", { detail: {
        tab: "dice", dice: { count: 1, die: "d20", modifier: 2 } } }));
    }
  } }, "Concentration save");

  card.append(
    el("div", { class: "field caster-field" }, [el("label", { text: "Name" }), name]),
    el("div", { class: "field caster-field" }, [el("label", { text: "Level" }), level]),
    el("div", { class: "field caster-field" }, [el("label", { text: "Token" }), tokenSel]),
    el("div", { class: "field caster-field" }, [el("label", { text: "Concentrating" }), concCb]),
    el("div", { class: "btn-row" }, [goToken, concSave]),
  );

  // slot grid
  const slots = el("div", { class: "slot-grid" });
  Object.entries(c.slots).forEach(([lvl, info]) => {
    const pip = el("button", {
      class: "slot-pip", title: "click: cast · shift-click: restore",
      onclick: async (e) => { await api.post(`/api/casters/${c.id}/cast`, { level: +lvl, restore: e.shiftKey }); reloadCasters(root); },
    }, `L${lvl}: ${info.max - info.used}/${info.max}`);
    slots.append(pip);
  });
  card.append(el("div", { class: "subhead", text: "Spell slots (remaining/max — click to cast)" }), slots,
    el("div", { class: "btn-row" }, [el("button", { class: "btn neutral", onclick: async () => { await api.post(`/api/casters/${c.id}/reset-slots`); reloadCasters(root); } }, "Long rest (reset)")]));

  // assigned spells
  const spellWrap = el("div");
  const levelsWithSpells = Object.keys(c.spells).filter((l) => c.spells[l].length).sort((a, b) => +a - +b);
  for (const lvl of levelsWithSpells) {
    for (const nm of c.spells[lvl]) {
      spellWrap.append(el("div", { class: "caster-spell" }, [
        el("span", { text: `Lv${lvl === "0" ? "C" : lvl}  ${nm}` }),
        el("button", { class: "btn neutral", title: "Cast (use a slot)", onclick: async () => { await api.post(`/api/casters/${c.id}/cast`, { level: +lvl }); reloadCasters(root); } }, "Cast"),
        el("button", { class: "btn neutral", onclick: async () => { await api.del(`/api/casters/${c.id}/spells`, { level: +lvl, name: nm }); reloadCasters(root); } }, "✕"),
      ]));
    }
  }
  card.append(el("div", { class: "subhead", text: "Spells" }), spellWrap,
    el("div", { class: "btn-row" }, [
      el("button", { class: "btn neutral", onclick: () => addSpellDialog(root, c) }, "Add from library"),
      el("button", { class: "btn neutral", onclick: async () => { await api.post(`/api/casters/${c.id}/duplicate`); reloadCasters(root); } }, "Duplicate"),
      el("button", { class: "btn danger", onclick: async () => { await api.del(`/api/casters/${c.id}`); reloadCasters(root); } }, "Remove caster"),
    ]));
  return card;
}

function addSpellDialog(root, c) {
  if (!_lib.length) { toast("Spell library is empty.", true); return; }
  const list = el("div", { class: "list" });
  _lib.slice().sort((a, b) => (a.level - b.level) || a.name.localeCompare(b.name)).forEach((sp) => {
    list.append(el("div", { class: "row", onclick: async () => {
      await api.post(`/api/casters/${c.id}/spells`, { level: sp.level, name: sp.name });
      dlg.close(); reloadCasters(root);
    } }, `Lv${sp.level === 0 ? "C" : sp.level}  ${sp.name}`));
  });
  const dlg = modal("Add spell to caster", list);
}
