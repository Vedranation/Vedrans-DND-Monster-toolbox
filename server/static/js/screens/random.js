// Random Generator — fumble table (more tables can be added later).

import { api } from "../api.js";
import { el, toast } from "../dom.js";

export async function renderRandom(root) {
  root.replaceChildren();
  const result = el("div", { class: "panel", text: "Roll a fumble to see what happens." });
  root.append(
    el("div", { class: "btn-row" }, [
      el("button", {
        class: "btn primary",
        onclick: async () => {
          try { result.textContent = (await api.post("/api/rolls/fumble")).result; }
          catch (err) { toast(err.message, true); }
        },
      }, "Roll fumble"),
    ]),
    result,
  );
}
