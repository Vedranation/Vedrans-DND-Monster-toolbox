// Monsters screen — roster list + full editor (combat, multi-attack sequence,
// saving throws, creature info, damage modifiers) + 5etools import.

import { api } from "../api.js";
import { store } from "../store.js";
import { el, modal, toast } from "../dom.js";
import { textField, numField, checkField, selectField } from "../forms.js";

const SAVES = ["STR", "DEX", "CON", "WIS", "INT", "CHA"];  // matches constants ordering
const SPEEDS = [["walk", "Walk"], ["fly", "Fly"], ["climb", "Climb"], ["burrow", "Burrow"], ["swim", "Swim"]];
const SENSES = [["darkvision", "Darkvision"], ["blindsight", "Blindsight"],
                ["tremorsense", "Tremorsense"], ["truesight", "Truesight"]];

let selectedId = null;

// Pre-select a monster by name (used by the board's double-click-to-edit).
export function selectByName(name) {
  const m = (store.state?.monsters || []).find((x) => x.name_str === name);
  if (m) selectedId = m.id;
}

function newAttack() {
  return {
    name: "Attack", to_hit_mod: 5, roll_type: "Normal", n_attacks: 1, crit_number: 20,
    dmg_n_die_1: 1, dmg_die_type_1: "d6", dmg_flat_1: 0, dmg_type_1: "slashing",
    dmg_n_die_2: 0, dmg_die_type_2: "d6", dmg_flat_2: 0, dmg_type_2: "None",
    reroll_1_on_hit: false, reroll_1_2_dmg: false, brutal_critical: false,
    savage_attacker: false, bless: false, bane: false,
    on_hit_force_save: false, on_hit_save_dc: 8, on_hit_save_type: "CON",
  };
}

export async function renderMonsters(root) {
  await store.refreshState();
  const monsters = store.state.monsters;
  if (!monsters.some((m) => m.id === selectedId)) selectedId = monsters[0]?.id ?? null;

  root.replaceChildren(el("h2", { text: "Monsters" }));
  const split = el("div", { class: "split" });

  // ── list ──
  const listCol = el("div");
  listCol.append(el("div", { class: "btn-row add-row" }, [
    el("button", {
      class: "btn primary",
      onclick: async () => {
        const m = await api.post("/api/monsters", { name_str: "New Monster", max_hp_int: 8 });
        selectedId = m.id; renderMonsters(root); toast("Monster added");
      },
    }, "+ Add"),
    el("button", { class: "btn neutral", onclick: () => openImport(root) }, "Import 5etools"),
  ]));
  const list = el("div", { class: "list" });
  for (const m of monsters) {
    list.append(el("div", {
      class: "row" + (m.id === selectedId ? " selected" : ""),
      onclick: () => { selectedId = m.id; renderMonsters(root); },
    }, m.name_str || "(unnamed)"));
  }
  if (!monsters.length) list.append(el("div", { class: "placeholder", text: "No monsters yet." }));
  listCol.append(list);

  // ── editor ──
  const editorCol = el("div");
  const entry = monsters.find((m) => m.id === selectedId);
  if (entry) {
    renderEditor(editorCol, structuredClone(entry), root);  // edit a working copy
  } else {
    editorCol.append(el("p", { class: "placeholder", text: "Add or select a monster." }));
  }

  split.append(listCol, editorCol);
  root.append(split);
}

function renderEditor(container, m, root) {
  const C = store.constants;
  container.replaceChildren();
  const panel = el("div", { class: "panel" });
  const refs = { saves: {}, speeds: {}, senses: {}, attacks: [], mods: {} };

  // ── combat ──
  const [nameF, name] = textField("Name", m.name_str); refs.name = name;
  const [acF, ac] = numField("AC", m.ac_int); refs.ac = ac;
  const [hpF, hp] = numField("Max HP", m.max_hp_int); refs.hp = hp;
  const [rngF, rng] = numField("Attack range (ft)", m.attack_range_ft); refs.rng = rng;
  const [hlF, hl] = numField("Highlight range (ft)", m.highlight_range_ft); refs.hl = hl;
  const [ignF, ign] = checkField("Ignore ranged-in-melee penalty", m.ignore_ranged_in_melee); refs.ign = ign;
  const [ppF, pp] = numField("Passive perception", m.passiveperception_int); refs.pp = pp;
  const [initF, init] = numField("Initiative mod", m.initiative_mod); refs.init = init;
  panel.append(el("fieldset", {}, [el("legend", { text: "Combat" }),
    nameF, acF, hpF, rngF, hlF, ignF, ppF, initF]));

  // ── attacks (multi-attack sequence) ──
  const atkFs = el("fieldset", {}, el("legend", { text: "Attacks" }));
  const atkList = el("div");
  refs.attacks = [];
  (m.attacks.length ? m.attacks : [newAttack()]).forEach((atk, i) => {
    const { node, read } = attackCard(atk, i, C, () => {
      collect(m, refs);                 // preserve edits
      m.attacks.splice(i, 1);
      if (!m.attacks.length) m.attacks.push(newAttack());
      renderEditor(container, m, root);
    }, m.attacks.length > 1);
    refs.attacks.push(read);
    atkList.append(node);
  });
  atkFs.append(atkList, el("button", {
    class: "btn neutral", onclick: () => {
      collect(m, refs); m.attacks.push(newAttack()); renderEditor(container, m, root);
    },
  }, "+ Add attack"));
  panel.append(atkFs);

  // ── saving throws ──
  const savesFs = el("fieldset", {}, el("legend", { text: "Saving throws" }));
  for (const ab of SAVES) {
    const mod = el("input", { type: "number", value: m[`savingthrow_${ab.toLowerCase()}_mod_int`] ?? 0 });
    const rt = el("select", {}, C.roll_types.map((o) =>
      el("option", { value: o, selected: o === m[`savingthrow_${ab.toLowerCase()}_roll_type_str`] }, o)));
    refs.saves[ab] = { mod, rt };
    savesFs.append(el("div", { class: "skill-row" }, [el("label", { text: ab }), mod, rt]));
  }
  panel.append(savesFs);

  // ── creature info / speeds / senses ──
  const infoFs = el("fieldset", {}, el("legend", { text: "Creature info" }));
  const [typeF, type] = selectField("Type", m.creature_type, C.creature_types); refs.type = type;
  const [sizeF, size] = selectField("Size", m.creature_size, C.creature_sizes); refs.size = size;
  infoFs.append(typeF, sizeF);
  const speedGrid = el("div", { class: "mini-grid" });
  for (const [key, label] of SPEEDS) {
    const inp = el("input", { type: "number", value: m[`${{walk:"walking",fly:"flying",climb:"climbing",burrow:"burrowing",swim:"swimming"}[key]}_speed_int`] ?? 0 });
    refs.speeds[key] = inp;
    speedGrid.append(el("div", { class: "mini" }, [el("label", { text: label }), inp]));
  }
  infoFs.append(el("div", { class: "subhead", text: "Speeds (ft)" }), speedGrid);
  const senseGrid = el("div", { class: "mini-grid" });
  for (const [key, label] of SENSES) {
    const inp = el("input", { type: "number", value: m[`senses_${key}`] ?? 0 });
    refs.senses[key] = inp;
    senseGrid.append(el("div", { class: "mini" }, [el("label", { text: label }), inp]));
  }
  infoFs.append(el("div", { class: "subhead", text: "Senses (ft)" }), senseGrid);
  panel.append(infoFs);

  // ── damage modifiers ──
  const modFs = el("fieldset", {}, el("legend", { text: "Damage modifiers" }));
  refs.mods.resist = checkGroup(modFs, "Resistances", C.dmg_types, m.damage_resistances);
  refs.mods.immune = checkGroup(modFs, "Immunities", C.dmg_types, m.damage_immunities);
  refs.mods.vuln = checkGroup(modFs, "Vulnerabilities", C.dmg_types, m.damage_vulnerabilities);
  refs.mods.cond = checkGroup(modFs, "Condition immunities", C.conditions, m.condition_immunities);
  panel.append(modFs);

  // ── actions ──
  panel.append(el("div", { class: "btn-row" }, [
    el("button", { class: "btn primary", onclick: () => save(m, refs, root) }, "Save"),
    el("button", {
      class: "btn danger",
      onclick: async () => {
        await api.del(`/api/monsters/${m.id}`); selectedId = null; renderMonsters(root); toast("Monster deleted");
      },
    }, "Delete"),
  ]));

  container.append(panel);
}

// ── attack card ──────────────────────────────────────────────────────────────
function mini(label, node) {
  return el("div", { class: "mini" }, [el("label", { text: label }), node]);
}
function num(value) { return el("input", { type: "number", value: value ?? 0 }); }
function sel(value, options) {
  return el("select", {}, options.map((o) => el("option", { value: o, selected: o === value }, o)));
}

function attackCard(atk, index, C, onRemove, canRemove) {
  const dmg2Types = C.dmg_types;  // no "None" — set Dmg2 dice to 0 for no second damage
  const r = {
    name: el("input", { type: "text", value: atk.name ?? "Attack" }),
    to_hit: num(atk.to_hit_mod), roll_type: sel(atk.roll_type, C.roll_types),
    n_attacks: num(atk.n_attacks), crit: num(atk.crit_number),
    d1n: num(atk.dmg_n_die_1), d1t: sel(atk.dmg_die_type_1, C.dice_types), d1f: num(atk.dmg_flat_1),
    d1type: sel(atk.dmg_type_1, C.dmg_types),
    d2n: num(atk.dmg_n_die_2), d2t: sel(atk.dmg_die_type_2, C.dice_types), d2f: num(atk.dmg_flat_2),
    d2type: sel(atk.dmg_type_2, dmg2Types),
    force_save: el("input", { type: "checkbox" }),
    save_dc: num(atk.on_hit_save_dc), save_type: sel(atk.on_hit_save_type, C.saving_throw_types),
    flags: {},
  };
  if (atk.on_hit_force_save) r.force_save.checked = true;

  const FLAGS = [
    ["reroll_1_on_hit", "Halfling luck"], ["reroll_1_2_dmg", "Great Weapon (reroll 1–2)"],
    ["brutal_critical", "Brutal critical"], ["savage_attacker", "Savage attacker"],
    ["bless", "Bless (+d4)"], ["bane", "Bane (−d4)"],
  ];
  const flagsWrap = el("div", { class: "flag-row" });
  for (const [key, label] of FLAGS) {
    const cb = el("input", { type: "checkbox" });
    if (atk[key]) cb.checked = true;
    r.flags[key] = cb;
    flagsWrap.append(el("label", { class: "toggle" }, [cb, label]));
  }

  const node = el("div", { class: "attack-card" }, [
    el("div", { class: "mini-grid" }, [
      mini("Name", r.name), mini("To-hit", r.to_hit), mini("Roll type", r.roll_type),
      mini("# attacks", r.n_attacks), mini("Crit ≥", r.crit),
      mini("Dmg1 dice", r.d1n), mini("Die", r.d1t), mini("Flat", r.d1f), mini("Type", r.d1type),
      mini("Dmg2 dice", r.d2n), mini("Die", r.d2t), mini("Flat", r.d2f), mini("Type", r.d2type),
    ]),
    flagsWrap,
    el("div", { class: "mini-grid" }, [
      el("div", { class: "mini" }, [el("label", { text: "On-hit forces save" }), r.force_save]),
      mini("Save DC", r.save_dc), mini("Save type", r.save_type),
    ]),
    el("div", { class: "btn-row" }, [
      el("button", { class: "btn danger", disabled: !canRemove, onclick: onRemove }, "Remove attack"),
    ]),
  ]);

  const read = () => ({
    name: r.name.value, to_hit_mod: +r.to_hit.value, roll_type: r.roll_type.value,
    n_attacks: +r.n_attacks.value, crit_number: +r.crit.value,
    dmg_n_die_1: +r.d1n.value, dmg_die_type_1: r.d1t.value, dmg_flat_1: +r.d1f.value, dmg_type_1: r.d1type.value,
    dmg_n_die_2: +r.d2n.value, dmg_die_type_2: r.d2t.value, dmg_flat_2: +r.d2f.value, dmg_type_2: r.d2type.value,
    reroll_1_on_hit: r.flags.reroll_1_on_hit.checked, reroll_1_2_dmg: r.flags.reroll_1_2_dmg.checked,
    brutal_critical: r.flags.brutal_critical.checked, savage_attacker: r.flags.savage_attacker.checked,
    bless: r.flags.bless.checked, bane: r.flags.bane.checked,
    on_hit_force_save: r.force_save.checked, on_hit_save_dc: +r.save_dc.value, on_hit_save_type: r.save_type.value,
  });
  return { node, read };
}

// ── multi-select checkbox group (collapsible) ──────────────────────────────────
function checkGroup(parent, title, options, selectedList) {
  const chosen = new Set(selectedList || []);
  const grid = el("div", { class: "check-grid" });
  const boxes = {};
  for (const opt of options) {
    const cb = el("input", { type: "checkbox" });
    if (chosen.has(opt)) cb.checked = true;
    boxes[opt] = cb;
    grid.append(el("label", { class: "toggle" }, [cb, opt]));
  }
  parent.append(el("details", {}, [
    el("summary", { text: `${title} (${chosen.size})` }), grid,
  ]));
  return () => options.filter((o) => boxes[o].checked);
}

// ── collect working copy from inputs ───────────────────────────────────────────
function collect(m, refs) {
  m.name_str = refs.name.value;
  m.ac_int = +refs.ac.value;
  m.max_hp_int = +refs.hp.value;
  m.attack_range_ft = +refs.rng.value;
  m.highlight_range_ft = +refs.hl.value;
  m.ignore_ranged_in_melee = refs.ign.checked;
  m.passiveperception_int = +refs.pp.value;
  m.initiative_mod = +refs.init.value;
  m.attacks = refs.attacks.map((read) => read());
  for (const ab of SAVES) {
    m[`savingthrow_${ab.toLowerCase()}_mod_int`] = +refs.saves[ab].mod.value;
    m[`savingthrow_${ab.toLowerCase()}_roll_type_str`] = refs.saves[ab].rt.value;
  }
  m.creature_type = refs.type.value;
  m.creature_size = refs.size.value;
  const speedKey = { walk: "walking", fly: "flying", climb: "climbing", burrow: "burrowing", swim: "swimming" };
  for (const [key] of SPEEDS) m[`${speedKey[key]}_speed_int`] = +refs.speeds[key].value;
  for (const [key] of SENSES) m[`senses_${key}`] = +refs.senses[key].value;
  m.damage_resistances = refs.mods.resist();
  m.damage_immunities = refs.mods.immune();
  m.damage_vulnerabilities = refs.mods.vuln();
  m.condition_immunities = refs.mods.cond();
}

async function save(m, refs, root) {
  collect(m, refs);
  try {
    await api.put(`/api/monsters/${m.id}`, m);
    toast("Saved");
    renderMonsters(root);
  } catch (err) {
    toast(err.message, true);
  }
}

// ── 5etools import ─────────────────────────────────────────────────────────────
function openImport(root) {
  const ta = el("textarea", { class: "json", placeholder: "Paste a 5etools monster JSON object…" });
  const status = el("div", { class: "status-line" });
  const body = el("div", {}, [
    el("p", { class: "muted", text: "Paste one monster's 5etools JSON, then Import." }),
    ta, status,
    el("div", { class: "btn-row" }, [
      el("button", {
        class: "btn primary",
        onclick: async () => {
          let data;
          try { data = JSON.parse(ta.value); }
          catch (e) { status.textContent = "Invalid JSON: " + e.message; return; }
          try {
            const m = await api.post("/api/monsters/import-5etools", data);
            selectedId = m.id; dialog.close(); renderMonsters(root); toast(`Imported ${m.name_str}`);
          } catch (err) { status.textContent = "Import failed: " + err.message; }
        },
      }, "Import"),
    ]),
  ]);
  const dialog = modal("Import 5etools monster", body);
}
