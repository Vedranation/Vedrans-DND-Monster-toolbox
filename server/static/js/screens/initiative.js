// Initiative tracker — manual entries + quick-add from rosters, roll-all, turn cycling.

import { api } from "../api.js";
import { el, toast } from "../dom.js";

let _turn = 0;  // index of the current combatant in the sorted list

export async function renderInitiative(root) {
  let entries = (await api.get("/api/initiative")).entries;
  root.replaceChildren(el("h2", { text: "Initiative" }));

  const nameIn = el("input", { type: "text", placeholder: "Name" });
  const initIn = el("input", { type: "number", value: 10, onfocus: (e) => e.target.select() });
  initIn.style.maxWidth = "64px";
  const table = el("div", { class: "init-table" });

  const reload = async () => { entries = (await api.get("/api/initiative")).entries; clampTurn(); paint(); };
  const clampTurn = () => { if (_turn >= entries.length) _turn = 0; };
  // Move to the next/previous ACTIVE combatant (skips disabled entries).
  const step = (dir) => {
    const n = entries.length;
    if (!n) return;
    for (let k = 1; k <= n; k++) {
      const idx = (((_turn + dir * k) % n) + n) % n;
      if (entries[idx].is_active) { _turn = idx; paint(); return; }
    }
  };

  root.append(el("div", { class: "btn-row" }, [
    nameIn, initIn,
    el("button", { class: "btn primary", onclick: async () => {
      if (!nameIn.value.trim()) return;
      await api.post("/api/initiative/entry", { name: nameIn.value.trim(), initiative: +initIn.value });
      nameIn.value = ""; reload();
    } }, "Add"),
    el("button", { class: "btn neutral", onclick: async () => { await api.post("/api/initiative/quick-add"); reload(); } }, "Add from rosters"),
    el("button", { class: "btn neutral", onclick: async () => { await api.post("/api/initiative/roll-all"); reload(); } }, "Roll all"),
    el("button", { class: "btn neutral", onclick: () => step(-1) }, "◀ Prev"),
    el("button", { class: "btn neutral", onclick: () => step(1) }, "Next ▶"),
    el("button", { class: "btn danger", onclick: async () => { await api.post("/api/initiative/clear"); _turn = 0; reload(); } }, "Clear"),
  ]), table);

  function paint() {
    table.replaceChildren();
    entries.forEach((e, i) => {
      const initInput = el("input", { type: "number", value: e.initiative, onfocus: (ev) => ev.target.select() });
      initInput.style.maxWidth = "58px";
      initInput.addEventListener("change", async () => {
        entries = (await api.patch(`/api/initiative/entry/${e.id}`, { initiative: +initInput.value })).entries;
        clampTurn(); paint();
      });
      const act = el("input", { type: "checkbox" }); if (e.is_active) act.checked = true;
      act.addEventListener("change", async () => {
        entries = (await api.patch(`/api/initiative/entry/${e.id}`, { is_active: act.checked })).entries;
        paint();
      });
      table.append(el("div", { class: "init-row" + (i === _turn ? " current" : "") + (e.is_active ? "" : " inactive") }, [
        initInput,
        el("span", { text: e.name }),
        el("span", { class: "muted", text: e.is_player ? "player" : "monster" }),
        act,
        el("button", { class: "btn neutral", onclick: async () => {
          entries = (await api.del(`/api/initiative/entry/${e.id}`)).entries; clampTurn(); paint();
        } }, "✕"),
      ]));
    });
    if (!entries.length) table.append(el("div", { class: "placeholder", text: "No combatants. Add manually or use “Add from rosters”." }));
  }

  clampTurn();
  paint();
}
