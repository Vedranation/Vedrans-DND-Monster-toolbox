// Tiny DOM helpers to keep screens terse (no framework, no build step).

export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, "");
    else if (v !== false && v != null) node.setAttribute(k, v);
  }
  for (const c of [].concat(children)) {
    if (c == null) continue;
    node.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return node;
}

export function clear(node) { node.replaceChildren(); }

// A simple modal overlay (replaces Tkinter Toplevel dialogs). Returns { close }.
export function modal(title, body, { onClose } = {}) {
  const overlay = el("div", { class: "modal-overlay" });
  const close = () => { overlay.remove(); if (onClose) onClose(); };
  overlay.append(el("div", { class: "modal" }, [
    el("div", { class: "modal-head" }, [
      el("h3", { text: title }),
      el("button", { class: "icon-btn", onclick: close }, "✕"),
    ]),
    body,
  ]));
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
  document.body.append(overlay);
  return { close };
}

// WebView-safe replacement for window.prompt() (Android WebView blocks the native
// one, so + Team / Rename silently did nothing). Calls onSubmit(trimmedValue) on OK.
export function promptDialog(title, { value = "", placeholder = "", okLabel = "OK", onSubmit } = {}) {
  const input = el("input", { type: "text", value, placeholder });
  input.style.width = "100%";
  const submit = () => { const v = input.value.trim(); dlg.close(); if (v && onSubmit) onSubmit(v); };
  const body = el("div", {}, [
    input,
    el("div", { class: "btn-row" }, [
      el("button", { class: "btn primary", onclick: submit }, okLabel),
      el("button", { class: "btn neutral", onclick: () => dlg.close() }, "Cancel"),
    ]),
  ]);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
  const dlg = modal(title, body);
  setTimeout(() => { input.focus(); input.select(); }, 0);
  return dlg;
}

// WebView-safe replacement for window.confirm(). Calls onConfirm() if the user accepts.
export function confirmDialog(title, message, { okLabel = "OK", danger = false, onConfirm } = {}) {
  const body = el("div", {}, [
    el("p", { text: message }),
    el("div", { class: "btn-row" }, [
      el("button", { class: "btn " + (danger ? "danger" : "primary"), onclick: () => { dlg.close(); if (onConfirm) onConfirm(); } }, okLabel),
      el("button", { class: "btn neutral", onclick: () => dlg.close() }, "Cancel"),
    ]),
  ]);
  const dlg = modal(title, body);
  return dlg;
}

// Right-click / long-press context menu. items: {label,onClick,disabled} | {separator}.
export function popupMenu(x, y, items) {
  closeMenus();
  const menu = el("div", { class: "ctx-menu" });
  for (const it of items) {
    if (it.separator) { menu.append(el("div", { class: "ctx-sep" })); continue; }
    if (it.header) { menu.append(el("div", { class: "ctx-header", text: it.header })); continue; }
    const b = el("button", {
      class: "ctx-item",
      disabled: !!it.disabled,
      onclick: () => { closeMenus(); it.onClick && it.onClick(); },
    }, it.label);
    menu.append(b);
  }
  menu.style.left = x + "px";
  menu.style.top = y + "px";
  document.body.append(menu);
  // Keep the menu on-screen if it overflows the right/bottom edge.
  const r = menu.getBoundingClientRect();
  if (r.right > innerWidth) menu.style.left = Math.max(0, innerWidth - r.width - 4) + "px";
  if (r.bottom > innerHeight) menu.style.top = Math.max(0, innerHeight - r.height - 4) + "px";
  setTimeout(() => document.addEventListener("mousedown", _closer), 0);
  return menu;
}
function _closer(e) { if (!e.target.closest(".ctx-menu")) closeMenus(); }
export function closeMenus() {
  document.querySelectorAll(".ctx-menu").forEach((m) => m.remove());
  document.removeEventListener("mousedown", _closer);
}

let _toastTimer = null;
export function toast(message, bad = false) {
  const t = document.getElementById("toast");
  t.textContent = message;
  t.className = "toast" + (bad ? " bad" : "");
  t.hidden = false;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { t.hidden = true; }, 2500);
}
