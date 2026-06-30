// Players screen — roster list + editor. CRUD over /api/players.

import { api } from "../api.js";
import { store } from "../store.js";
import { el, toast } from "../dom.js";
import { textField, numField, checkField, selectField, colorField } from "../forms.js";

const SKILLS = ["perception", "investigation", "arcana", "insight", "stealth"];
const PLAYER_DEFAULT_COLOR = "#5b96d6";  // blue (board default for player tokens)

let selectedId = null;

// ── autosave (no Save button — commit on field blur + when leaving the editor) ──
let _pending = null;     // { id, read } where read() builds the PUT body
let _saveTimer = null;

function autosaveNow() {
  if (!_pending) return Promise.resolve();
  clearTimeout(_saveTimer);
  const { id, read } = _pending;
  return api.put(`/api/players/${id}`, read()).catch((err) => toast(err.message, true));
}
function autosaveSoon() { clearTimeout(_saveTimer); _saveTimer = setTimeout(autosaveNow, 250); }
window.addEventListener("screen-leaving", () => { autosaveNow(); _pending = null; });
window.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") autosaveNow(); });

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

  root.replaceChildren();
  const split = el("div", { class: "split" });

  // ── left: list ──
  const listCol = el("div");
  listCol.append(el("button", {
    class: "btn primary add-row",
    onclick: async () => {
      await autosaveNow();
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
      onclick: async () => { await autosaveNow(); selectedId = p.id; renderPlayers(root); },
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
  const [colorF, colorRead] = colorField("Token color", p.color_str || PLAYER_DEFAULT_COLOR); refs.color = colorRead;
  // Players don't attack on the board, so no attack-range / ranged-in-melee fields.
  const [impF, imp] = selectField("Imposes on attackers", p.monster_roll_type_against_str, rollTypes); refs.imp = imp;
  const [adamF, adam] = checkField("Adamantine (crits → normal hits)", p.adamantine); refs.adam = adam;
  const [ppF, pp] = numField("Passive perception", p.passiveperception_int); refs.pp = pp;
  const [initF, init] = numField("Initiative mod", p.initiative_mod); refs.init = init;

  const combat = el("fieldset", {}, [el("legend", { text: "Combat" }),
    nameF, acF, hpF, colorF, impF, adamF, ppF, initF]);

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

  const del = el("button", {
    class: "btn danger",
    onclick: async () => {
      _pending = null;  // don't autosave a player we're deleting
      await api.del(`/api/players/${p.id}`);
      selectedId = null;
      renderPlayers(root);
      toast("Player deleted");
    },
  }, "Delete");

  panel.append(combat, skillsFs, el("div", { class: "btn-row" }, [
    el("span", { class: "muted", text: "Changes save automatically." }), del,
  ]));

  // Build the PUT body from the current inputs (used by autosave).
  const read = () => {
    const body = {
      name_str: refs.name.value,
      ac_int: +refs.ac.value,
      max_hp_int: +refs.hp.value,
      color_str: refs.color(),
      monster_roll_type_against_str: refs.imp.value,
      adamantine: refs.adam.checked,
      passiveperception_int: +refs.pp.value,
      initiative_mod: +refs.init.value,
    };
    for (const sk of SKILLS) {
      body[`${sk}_mod_int`] = +skillRefs[sk].mod.value;
      body[`${sk}_roll_type_str`] = skillRefs[sk].rt.value;
    }
    return body;
  };
  _pending = { id: p.id, read };
  panel.addEventListener("change", autosaveSoon);
  return panel;
}
