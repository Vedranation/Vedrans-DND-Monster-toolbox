// Players screen — roster list + editor. CRUD over /api/players.

import { api } from "../api.js";
import { store } from "../store.js";
import { el, toast } from "../dom.js";
import { textField, numField, checkField, selectField } from "../forms.js";

const SKILLS = ["perception", "investigation", "arcana", "insight", "stealth"];

let selectedId = null;

// Pre-select a player by name (used by the board's double-click-to-edit).
export function selectByName(name) {
  const p = (store.state?.players || []).find((x) => x.name_str === name);
  if (p) selectedId = p.id;
}

export async function renderPlayers(root) {
  await store.refreshState();
  const players = store.state.players;
  const rollTypes = store.constants.roll_types;

  if (!players.some((p) => p.id === selectedId)) selectedId = players[0]?.id ?? null;

  root.replaceChildren(el("h2", { text: "Players" }));
  const split = el("div", { class: "split" });

  // ── left: list ──
  const listCol = el("div");
  listCol.append(el("button", {
    class: "btn primary add-row",
    onclick: async () => {
      const p = await api.post("/api/players", { name_str: "New Player", max_hp_int: 8 });
      selectedId = p.id;
      renderPlayers(root);
      toast("Player added");
    },
  }, "+ Add player"));

  const list = el("div", { class: "list" });
  for (const p of players) {
    list.append(el("div", {
      class: "row" + (p.id === selectedId ? " selected" : ""),
      onclick: () => { selectedId = p.id; renderPlayers(root); },
    }, p.name_str || "(unnamed)"));
  }
  if (!players.length) list.append(el("div", { class: "placeholder", text: "No players yet." }));
  listCol.append(list);

  // ── right: editor ──
  const editorCol = el("div");
  const sel = players.find((p) => p.id === selectedId);
  editorCol.append(sel ? buildEditor(sel, root, rollTypes)
                       : el("p", { class: "placeholder", text: "Add or select a player." }));

  split.append(listCol, editorCol);
  root.append(split);
}

function buildEditor(p, root, rollTypes) {
  const panel = el("div", { class: "panel" });
  const refs = {};

  const [nameF, name] = textField("Name", p.name_str); refs.name = name;
  const [acF, ac] = numField("AC", p.ac_int); refs.ac = ac;
  const [hpF, hp] = numField("Max HP", p.max_hp_int); refs.hp = hp;
  const [rngF, rng] = numField("Attack range (ft)", p.attack_range_ft); refs.rng = rng;
  const [hlF, hl] = numField("Highlight range (ft)", p.highlight_range_ft); refs.hl = hl;
  const [ignF, ign] = checkField("Ignore ranged-in-melee penalty", p.ignore_ranged_in_melee); refs.ign = ign;
  const [impF, imp] = selectField("Imposes on attackers", p.monster_roll_type_against_str, rollTypes); refs.imp = imp;
  const [adamF, adam] = checkField("Adamantine (crits → normal hits)", p.adamantine); refs.adam = adam;
  const [ppF, pp] = numField("Passive perception", p.passiveperception_int); refs.pp = pp;
  const [initF, init] = numField("Initiative mod", p.initiative_mod); refs.init = init;

  const combat = el("fieldset", {}, [el("legend", { text: "Combat" }),
    nameF, acF, hpF, rngF, hlF, ignF, impF, adamF, ppF, initF]);

  // skills: mod + roll type per skill
  const skillRefs = {};
  const skillsFs = el("fieldset", {}, el("legend", { text: "Skills" }));
  for (const sk of SKILLS) {
    const mod = el("input", { type: "number", value: p[`${sk}_mod_int`] ?? 0 });
    const rt = el("select", {}, rollTypes.map((o) =>
      el("option", { value: o, selected: o === p[`${sk}_roll_type_str`] }, o)));
    skillRefs[sk] = { mod, rt };
    skillsFs.append(el("div", { class: "skill-row" },
      [el("label", { text: sk[0].toUpperCase() + sk.slice(1) }), mod, rt]));
  }

  const save = el("button", { class: "btn primary", onclick: () => doSave(p.id, refs, skillRefs, root) }, "Save");
  const del = el("button", {
    class: "btn danger",
    onclick: async () => {
      await api.del(`/api/players/${p.id}`);
      selectedId = null;
      renderPlayers(root);
      toast("Player deleted");
    },
  }, "Delete");

  panel.append(combat, skillsFs, el("div", { class: "btn-row" }, [save, del]));
  return panel;
}

async function doSave(id, refs, skillRefs, root) {
  const body = {
    name_str: refs.name.value,
    ac_int: +refs.ac.value,
    max_hp_int: +refs.hp.value,
    attack_range_ft: +refs.rng.value,
    highlight_range_ft: +refs.hl.value,
    ignore_ranged_in_melee: refs.ign.checked,
    monster_roll_type_against_str: refs.imp.value,
    adamantine: refs.adam.checked,
    passiveperception_int: +refs.pp.value,
    initiative_mod: +refs.init.value,
  };
  for (const sk of SKILLS) {
    body[`${sk}_mod_int`] = +skillRefs[sk].mod.value;
    body[`${sk}_roll_type_str`] = skillRefs[sk].rt.value;
  }
  try {
    await api.put(`/api/players/${id}`, body);
    toast("Saved");
    renderPlayers(root);  // refresh list (name may have changed)
  } catch (err) {
    toast(err.message, true);
  }
}
