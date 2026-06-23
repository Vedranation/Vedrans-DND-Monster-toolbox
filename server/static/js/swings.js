// Shared rendering for attack swings + damage-type coloring (board Resolve modal
// and the Attack tab use the same code so results look identical everywhere).

import { el } from "./dom.js";

// Damage-type colors. Plain physical → grey; magic physical → teal; elemental
// types use the map. Magic-prefixed elemental (none today) would share their base.
const DMG_COLORS = {
  acid: "#80b000", cold: "#3399cc", fire: "#ee5500", force: "#cc3333",
  lightning: "#3366cc", necrotic: "#2b6942", poison: "#44bb00",
  radiant: "#ccaa00", thunder: "#8844bb", psychic: "#cc77aa",
};
export function dmgColor(type) {
  type = type || "";
  if (type.startsWith("magic ")) return "#30bbbb";   // magic physical → cyan
  return DMG_COLORS[type] || "#8c8c8c";               // elemental, else plain physical
}
export function dmgSpan(amount, type) {
  return el("span", { style: `color:${dmgColor(type)}`, text: `${amount} ${type}` });
}

// "d20=10|16" with the kept die bolded, dropped dice greyed (adv/disadv aware).
// Reused by the Attack swings and the quick-save report.
export function d20Span(d20s, kept) {
  const ds = (d20s && d20s.length) ? d20s : [kept];
  const span = el("span", {}, "d20=");
  let boldUsed = false;
  ds.forEach((d, i) => {
    if (i > 0) span.append("|");
    if (!boldUsed && d === kept) { boldUsed = true; span.append(el("b", { text: String(d) })); }
    else span.append(el("span", { class: "die-dropped", text: String(d) }));
  });
  return span;
}

// A list of per-swing rows: kept die bold, dropped dice greyed; damage colored by type.
export function renderSwings(rolls) {
  const wrap = el("div");
  if (!rolls.length) { wrap.append(el("div", { class: "muted", text: "no attacks" })); return wrap; }
  for (const r of rolls) {
    const outcome = r.is_crit ? "CRIT" : (r.is_hit ? "HIT" : "MISS");
    const color = outcome === "MISS" ? "#cc3333" : outcome === "CRIT" ? "#cc7700" : "#228822";
    // Dice shown in roll order; the KEPT die (r.d20) is bolded wherever it lands,
    // the rest greyed — so adv/disadv shows the real sequence, not a sorted one.
    const dice = el("span", { class: "swing-dice" });
    dice.append(`[${r.attack_name}] d20=`);
    const ds = (r.all_d20s && r.all_d20s.length) ? r.all_d20s : [r.d20];
    let boldUsed = false;
    ds.forEach((d, i) => {
      if (i > 0) dice.append("|");
      if (!boldUsed && d === r.d20) { boldUsed = true; dice.append(el("b", { text: String(d) })); }
      else dice.append(el("span", { class: "die-dropped", text: String(d) }));
    });
    dice.append(` → total ${r.total}`);
    const dmg = el("span", { class: "swing-dmg" });
    if (r.is_hit) {
      dmg.append(dmgSpan(r.dmg1, r.dmg_type_1));
      if (r.dmg2 > 0) { dmg.append(" + "); dmg.append(dmgSpan(r.dmg2, r.dmg_type_2)); }
      dmg.append(` = ${r.dmg1 + r.dmg2}`);
      const [forceSave, dc, saveType] = r.save_info || [false, 0, ""];
      if (forceSave) dmg.append(`  | DC ${dc} ${saveType} save`);
    } else {
      dmg.append("—");
    }
    wrap.append(el("div", { class: "swing" }, [
      dice,
      el("span", { class: "swing-outcome", style: `color:${color}`, text: outcome }),
      dmg,
    ]));
  }
  return wrap;
}

// Colored "N type, M type [= total]" inline element from typed_damage_parts.
export function breakdownInline(parts, total) {
  const span = el("span");
  if (!parts || !parts.length) { span.append("0"); return span; }
  parts.forEach((p, i) => {
    if (i > 0) span.append(", ");
    const label = `${p.amount} ${p.type}` + (p.status ? ` (${p.status})` : "");
    span.append(el("span", { style: `color:${dmgColor(p.type)}`, text: label }));
  });
  if (parts.length > 1) span.append(` = ${total}`);
  return span;
}
