// Attack tab — single-roll combat (mirrors the desktop Attack tab): pick an
// attacker, tick which attacks to use, a defender, a roll-type override; results
// accumulate in a log (newest first) with per-swing detail and a colored total.

import { api } from "../api.js";
import { store } from "../store.js";
import { el, toast } from "../dom.js";
import { renderSwings, breakdownInline } from "../swings.js";

let _results = [];     // newest-first roll responses (persists across tab switches)
let _preset = null;    // {attackerName, defenderName} from the board's "Send to Attack"

// Pre-load a matchup (used by the board: select 2 tokens → Send to Attack tab).
export function presetMatchup(attackerName, defenderName) {
  _preset = { attackerName, defenderName };
}

export async function renderAttack(root) {
  await store.refreshState();
  const monsters = store.state.monsters;
  const players = store.state.players;

  root.replaceChildren();
  if (!monsters.length) {
    root.append(el("p", { class: "placeholder", text: "Create a monster first — only monsters have attacks." }));
    return;
  }

  const panel = el("div", { class: "panel" });

  const attackerSel = el("select", {}, monsters.map((m) => el("option", { value: m.id }, m.name_str || "(unnamed)")));
  const attacksWrap = el("div", { class: "flag-row" });
  const acHp = (e) => `(AC ${e.ac_int}, HP ${e.max_hp_int})`;
  const defenderSel = el("select", {}, [
    el("option", { value: "" }, "None (AC 0 — always hits)"),
    ...monsters.map((m) => el("option", { value: m.id }, `[M] ${m.name_str} ${acHp(m)}`)),
    ...players.map((p) => el("option", { value: p.id }, `[P] ${p.name_str} ${acHp(p)}`)),
  ]);
  const rtSel = el("select", {}, store.constants.roll_types.map((o) => el("option", { value: o }, o)));
  rtSel.value = "Normal";

  function rebuildAttacks() {
    attacksWrap.replaceChildren();
    const m = monsters.find((x) => x.id === attackerSel.value);
    (m ? m.attacks : []).forEach((atk, i) => {
      const cb = el("input", { type: "checkbox" });
      cb.checked = true; cb.dataset.idx = i;
      const label = (atk.name || "Attack") + (atk.n_attacks > 1 ? ` ×${atk.n_attacks}` : "");
      attacksWrap.append(el("label", { class: "toggle" }, [cb, label]));
    });
  }
  attackerSel.addEventListener("change", rebuildAttacks);
  rebuildAttacks();

  const log = el("div", { class: "attack-log" });

  async function roll() {
    const indices = [...attacksWrap.querySelectorAll("input:checked")].map((cb) => +cb.dataset.idx);
    if (!indices.length) { toast("Select at least one attack.", true); return; }
    const body = { attacker_id: attackerSel.value, attack_indices: indices, override_roll_type: rtSel.value };
    let defInfo = "";
    if (defenderSel.value) {
      body.defender_id = defenderSel.value;
      const d = monsters.find((x) => x.id === defenderSel.value) || players.find((x) => x.id === defenderSel.value);
      if (d) defInfo = ` ${acHp(d)}`;
    }
    try {
      const res = await api.post("/api/roll-attack", body);
      res._defInfo = defInfo;
      _results.unshift(res);
      if (_results.length > 12) _results.length = 12;
      renderLog(log);
    } catch (err) { toast(err.message, true); }
  }

  panel.append(
    el("div", { class: "field" }, [el("label", { text: "Attacker" }), attackerSel]),
    el("div", { class: "field" }, [el("label", { text: "Use attacks" }), attacksWrap]),
    el("div", { class: "field" }, [el("label", { text: "Defender" }), defenderSel]),
    el("div", { class: "field" }, [el("label", { text: "Roll with" }), rtSel]),
    el("div", { class: "muted", text: "Note: “Roll with” overrides ALL roll types." }),
    el("div", { class: "btn-row" }, [el("button", { class: "btn primary", onclick: roll }, "Roll attack")]),
  );
  root.append(panel, el("h3", { text: "Results" }), log);

  // Apply a board-sent matchup, if any.
  if (_preset) {
    const m = monsters.find((x) => x.name_str === _preset.attackerName);
    if (m) { attackerSel.value = m.id; rebuildAttacks(); }
    if (_preset.defenderName) {
      const d = monsters.find((x) => x.name_str === _preset.defenderName)
             || players.find((x) => x.name_str === _preset.defenderName);
      if (d) defenderSel.value = d.id;
    }
    _preset = null;
  }

  renderLog(log);
}

function renderLog(log) {
  log.replaceChildren();
  for (const res of _results) {
    const tag = res.override_roll_type && res.override_roll_type !== "Normal" ? `  [${res.override_roll_type}]` : "";
    const block = el("div", { class: "attack-card" }, [
      el("div", { class: "swing-head", text: `${res.attacker} → ${res.defender}${res._defInfo || ""}${tag}` }),
      renderSwings(res.rolls),
    ]);
    const total = el("div", { class: "swing-total" }, ["Total damage: ", breakdownInline(res.breakdown_parts, res.total)]);
    block.append(total);
    log.append(block);
  }
}
