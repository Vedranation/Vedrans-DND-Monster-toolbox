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
