// Search — fuzzy "did you mean" over the 5e.tools catalog + local spell library.
// Click a catalog result to open it on 5e.tools.

import { api } from "../api.js";
import { el, toast } from "../dom.js";

let _debounce = null;

export async function renderSearch(root) {
  root.replaceChildren();

  const input = el("input", { type: "text", placeholder: "Spell, monster, item, or feat…" });
  input.style.minWidth = "340px";

  const suggBox = el("div", { class: "list" });
  const localBox = el("div", { class: "list" });

  async function doSearch(q) {
    q = q.trim();
    if (!q) { suggBox.replaceChildren(); localBox.replaceChildren(); return; }
    let data;
    try { data = await api.get(`/api/search?q=${encodeURIComponent(q)}`); }
    catch (err) { toast(err.message, true); return; }

    suggBox.replaceChildren();
    for (const s of data.suggestions) {
      suggBox.append(el("div", {
        class: "row",
        title: s.url ? "Open on 5e.tools" : "No 5e.tools page",
        onclick: () => { if (s.url) window.open(s.url, "_blank", "noopener"); },
      }, `${s.name}   (${s.category})`));
    }
    if (!data.suggestions.length) suggBox.append(el("div", { class: "placeholder", text: "No matches." }));

    localBox.replaceChildren();
    for (const sp of data.local) {
      localBox.append(el("div", {
        class: "row", title: "Open in Spellcasters",
        onclick: () => window.dispatchEvent(new CustomEvent("navigate", {
          detail: { tab: "spellcasters", selectSpellName: sp.name } })),
      }, `Lv${sp.level === 0 ? "C" : sp.level}  ${sp.name}`));
    }
    if (!data.local.length) localBox.append(el("div", { class: "placeholder", text: "Nothing in your spell library." }));
  }

  input.addEventListener("input", () => {
    clearTimeout(_debounce);
    _debounce = setTimeout(() => doSearch(input.value), 200);
  });

  root.append(
    el("div", { class: "field" }, [el("label", { text: "Query" }), input]),
    el("p", { class: "muted", text: "Click a catalog result to open it on 5e.tools (new tab)." }),
    el("div", { class: "split" }, [
      el("div", {}, [el("div", { class: "subhead", text: "5e.tools catalog" }), suggBox]),
      el("div", {}, [el("div", { class: "subhead", text: "Your spell library" }), localBox]),
    ]),
  );
  input.focus();
}
