// Dice — quick roller: how many, which die, plus a flat modifier, with a queue of
// past rolls (newest-first, like the Attack tab). Designed for reuse: presetDice()
// lets other tabs (e.g. spells) pre-fill the roller before navigating here.

import { api } from "../api.js";
import { store } from "../store.js";
import { el, toast } from "../dom.js";

let _preset = null;       // {count, die, modifier} applied on next render
let _history = [];        // newest-first roll responses (persists across tab switches)

// Pre-fill the roller from another tab, then navigate to "dice".
export function presetDice(count = 1, die = "d20", modifier = 0) {
  _preset = { count, die, modifier };
}

const sign = (n) => (n >= 0 ? "+" : "") + n;
const exprOf = (d) => `${d.count}${d.die}${d.modifier ? ` ${sign(d.modifier)}` : ""}`;

export async function renderDice(root) {
  const C = store.constants;
  const dice = (C.dice_types && C.dice_types.length) ? C.dice_types : ["d4", "d6", "d8", "d10", "d12", "d20", "d100"];
  const p = _preset || { count: 1, die: "d20", modifier: 0 };
  _preset = null;

  root.replaceChildren(el("h2", { text: "Dice" }));

  const count = el("input", { type: "number", value: p.count, min: 1, max: 100, onfocus: (e) => e.target.select() });
  count.style.maxWidth = "80px";
  const die = el("select", {}, dice.map((d) => el("option", { value: d }, d)));
  die.value = dice.includes(p.die) ? p.die : "d20";
  const mod = el("input", { type: "number", value: p.modifier, onfocus: (e) => e.target.select() });
  mod.style.maxWidth = "80px";

  const log = el("div", { class: "dice-log" });

  async function roll() {
    let d;
    try {
      d = await api.post("/api/rolls/dice", {
        count: Math.max(1, Math.min(100, +count.value || 1)),
        die: die.value,
        modifier: +mod.value || 0,
      });
    } catch (err) { toast(err.message, true); return; }
    _history.unshift(d);
    if (_history.length > 15) _history.length = 15;
    renderLog(log);
  }

  const field = (label, node) => el("div", { class: "field" }, [el("label", { text: label }), node]);
  root.append(
    el("div", { class: "panel" }, [
      field("How many", count),
      field("Die", die),
      field("Modifier", mod),
      el("div", { class: "btn-row" }, [
        el("button", { class: "btn primary", onclick: roll }, "Roll"),
        el("button", { class: "btn neutral", onclick: () => { _history = []; renderLog(log); } }, "Clear log"),
      ]),
    ]),
    el("h3", { text: "Rolls" }), log,
  );
  renderLog(log);
}

function renderLog(log) {
  log.replaceChildren();
  if (!_history.length) { log.append(el("div", { class: "placeholder", text: "No rolls yet." })); return; }
  for (const d of _history) {
    const breakdown = d.rolls.join(" + ") + (d.modifier ? ` ${sign(d.modifier)}` : "");
    log.append(el("div", { class: "dice-row" }, [
      el("span", { class: "dice-expr", text: exprOf(d) }),
      el("span", { class: "muted", text: d.count > 1 || d.modifier ? `  ${breakdown}` : "" }),
      el("span", { class: "dice-total", text: `= ${d.total}` }),
    ]));
  }
}
