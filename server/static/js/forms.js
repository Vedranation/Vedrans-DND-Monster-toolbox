// Shared form-field builders. Each returns [fieldNode, inputNode] so callers can
// lay out the field and read the input's value later.

import { el } from "./dom.js";

export function textField(label, value) {
  const input = el("input", { type: "text", value: value ?? "" });
  return [el("div", { class: "field" }, [el("label", { text: label }), input]), input];
}

export function numField(label, value) {
  const input = el("input", { type: "number", value: value ?? 0 });
  return [el("div", { class: "field" }, [el("label", { text: label }), input]), input];
}

export function checkField(label, checked) {
  const input = el("input", { type: "checkbox" });
  if (checked) input.checked = true;
  return [el("label", { class: "toggle" }, [input, label]), input];
}

export function selectField(label, value, options) {
  const sel = el("select", {}, options.map((o) => el("option", { value: o, selected: o === value }, o)));
  return [el("div", { class: "field" }, [el("label", { text: label }), sel]), sel];
}

// Dropdown of numeric values 0..max in `step` increments (default 5) — for ranges
// and speeds, which are always multiples of 5 ft. An off-grid current value (e.g.
// from an odd import) is inserted so it isn't lost. Read with +input.value.
export function stepField(label, value, { min = 0, max = 120, step = 5 } = {}) {
  const v = Number(value) || 0;
  const opts = [];
  for (let n = min; n <= max; n += step) opts.push(n);
  if (!opts.includes(v)) { opts.push(v); opts.sort((a, b) => a - b); }
  const sel = el("select", {}, opts.map((n) => el("option", { value: n, selected: n === v }, `${n} ft`)));
  return [el("div", { class: "field" }, [el("label", { text: label }), sel]), sel];
}

// Compact variant (just the <select>) for grid layouts like the speeds grid.
export function stepSelect(value, { min = 0, max = 120, step = 5 } = {}) {
  const [, sel] = stepField("", value, { min, max, step });
  return sel;
}

// Token color: a hex text field + a native picker that stay in sync. Blank = auto
// (name-hashed default). Returns [fieldNode, read] where read() → "#rrggbb" or "".
const _HEX = /^#[0-9a-fA-F]{6}$/;
export function colorField(label, value) {
  const txt = el("input", { type: "text", value: value || "", placeholder: "#rrggbb (blank = auto)" });
  txt.style.maxWidth = "150px";
  const pick = el("input", { type: "color", value: _HEX.test(value || "") ? value : "#888888" });
  pick.addEventListener("input", () => { txt.value = pick.value; txt.dispatchEvent(new Event("change", { bubbles: true })); });
  txt.addEventListener("change", () => { const v = txt.value.trim(); if (_HEX.test(v)) pick.value = v; });
  const read = () => {
    let v = txt.value.trim();
    if (!v) return "";
    if (!v.startsWith("#")) v = "#" + v;
    return _HEX.test(v) ? v : "";
  };
  const node = el("div", { class: "field" }, [el("label", { text: label }),
    el("span", { style: "display:flex; gap:.4rem; align-items:center;" }, [pick, txt])]);
  return [node, read];
}
