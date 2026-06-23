// Settings screen — combat rules + board settings. Each change PUTs immediately.
// Also hosts the named-preset manager (save / load / delete whole scenarios).

import { api } from "../api.js";
import { store } from "../store.js";
import { el, toast } from "../dom.js";

const BOOL_FIELDS = [
  ["meets_it_beats_it", "Attack roll = AC counts as a hit (meets it, beats it)"],
  ["crits_double_dmg", "Crits double TOTAL damage (instead of doubling dice)"],
  ["crits_extra_die_is_max", "Crit bonus dice roll maximum (anti snake-eyes)"],
  ["nat1_always_miss", "Natural 1 always misses"],
  ["adv_combine", "Two Advantages combine into one Super Advantage"],
  ["auto_disable_zero_hp", "Automatically disable 0 HP tokens"],
  ["ignore_resistances", "Ignore monster damage resistances/immunities/vulnerabilities"],
];

const SELECT_FIELDS = [
  ["adv_mode", "Adv/Disadv stacking", ["RAW", "Arithmetic"]],
  ["board_diagonal_mode", "Board diagonal movement", ["standard", "5-10-5"]],
  ["board_flank_geometry", "Flanking geometry", ["hard", "soft"]],
  ["board_flank_benefit", "Flank benefit", ["advantage", "+2"]],
  ["board_range_mode", "Range check", ["warn", "block"]],
];

export async function renderSettings(root) {
  let settings = await api.get("/api/settings");
  let presets = (await api.get("/api/presets")).presets;

  // Optimistic: the control already shows the new value (native), so update local
  // state immediately and PUT in the background; only re-render when this key gates
  // another control. Roll back + re-render only if the server rejects it.
  async function patch(key, value, gating = false) {
    const prev = settings[key];
    settings[key] = value;
    if (gating) draw();
    try {
      await api.put("/api/settings", { [key]: value });
    } catch (err) {
      settings[key] = prev;
      draw();
      toast(err.message, true);
    }
  }

  function draw() {
    root.replaceChildren();
    root.append(el("h2", { text: "Settings" }));
    const panel = el("div", { class: "panel" });

    const rules = el("fieldset", {}, el("legend", { text: "Combat rules" }));
    for (const [key, label] of BOOL_FIELDS) {
      // "crit bonus dice = max" only applies when NOT doubling total damage, so
      // toggling crits_double_dmg must re-render to update that control's gating.
      const gated = key === "crits_extra_die_is_max" && settings.crits_double_dmg;
      const input = el("input", {
        type: "checkbox",
        onchange: (e) => patch(key, e.target.checked, key === "crits_double_dmg"),
      });
      if (settings[key]) input.checked = true;
      if (gated) input.disabled = true;
      rules.append(el("label", { class: "toggle" + (gated ? " disabled" : "") }, [input, label]));
    }
    panel.append(rules);

    const opts = el("fieldset", {}, el("legend", { text: "Modes & board" }));
    for (const [key, label, choices] of SELECT_FIELDS) {
      const sel = el("select", { onchange: (e) => patch(key, e.target.value) },
        choices.map((c) => el("option", { value: c, selected: settings[key] === c }, c)));
      opts.append(el("div", { class: "field" }, [el("label", { text: label }), sel]));
    }
    panel.append(opts);

    root.append(panel, presetsPanel());
  }

  // ── presets (save / load / delete whole scenarios) ──────────────────────────
  function presetsPanel() {
    const panel = el("div", { class: "panel" }, el("h3", { text: "Presets" }));
    panel.append(el("p", { class: "muted", text:
      "A preset saves the full scenario: monsters, players, spell library, casters, board, initiative, and these settings." }));

    const list = el("div", { class: "list" });
    for (const name of presets) {
      list.append(el("div", { class: "row" }, [
        el("span", { text: name }),
        el("span", {}, [
          el("button", { class: "btn neutral", onclick: () => loadPreset(name) }, "Load"),
          " ",
          el("button", { class: "btn danger", onclick: () => deletePreset(name) }, "Delete"),
        ]),
      ]));
    }
    if (!presets.length) list.append(el("div", { class: "placeholder", text: "No saved presets." }));

    const nameIn = el("input", { type: "text", placeholder: "Preset name" });
    panel.append(list, el("div", { class: "field" }, [
      el("label", { text: "Save current as" }), nameIn,
      el("button", { class: "btn primary", onclick: () => savePreset(nameIn.value) }, "Save"),
    ]));
    return panel;
  }

  async function refresh() {
    settings = await api.get("/api/settings");
    presets = (await api.get("/api/presets")).presets;
    await store.refreshState();   // so other tabs see the loaded roster/board
    draw();
  }

  async function loadPreset(name) {
    try { await api.get(`/api/presets/${encodeURIComponent(name)}`); }
    catch (err) { toast(err.message, true); return; }
    await refresh();
    toast(`Loaded "${name}"`);
  }

  async function savePreset(name) {
    name = (name || "").trim();
    if (!name) { toast("Enter a preset name.", true); return; }
    if (presets.includes(name) && !confirm(`Overwrite preset "${name}"?`)) return;
    try { await api.post("/api/presets", { name }); }
    catch (err) { toast(err.message, true); return; }
    presets = (await api.get("/api/presets")).presets;
    draw();
    toast(`Saved "${name}"`);
  }

  async function deletePreset(name) {
    if (!confirm(`Delete preset "${name}"?`)) return;
    try { await api.del(`/api/presets/${encodeURIComponent(name)}`); }
    catch (err) { toast(err.message, true); return; }
    presets = (await api.get("/api/presets")).presets;
    draw();
    toast(`Deleted "${name}"`);
  }

  draw();
}
