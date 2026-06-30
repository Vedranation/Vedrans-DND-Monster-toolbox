// App shell: nav bar + screen routing + bootstrap.

import { store } from "./store.js";
import { el, clear, toast } from "./dom.js";
import { renderSettings } from "./screens/settings.js";
import { renderPlayers, selectByName as selectPlayerByName } from "./screens/players.js";
import { renderMonsters, selectByName as selectMonsterByName } from "./screens/monsters.js";
import { renderBoard } from "./screens/board.js";
import { renderAttack, presetMatchup } from "./screens/attack.js";
import { renderSkills, presetMassSaves, presetQuickSave } from "./screens/skills.js";
import { renderSearch } from "./screens/search.js";
import { renderRandom } from "./screens/random.js";
import { renderInitiative } from "./screens/initiative.js";
import { renderSpellcasters, presetSpell, presetCaster } from "./screens/spellcasters.js";
import { presetSelectToken } from "./screens/board.js";
import { renderDice, presetDice } from "./screens/dice.js";

const TABS = [
  { id: "board", label: "Battle Board" },
  { id: "attack", label: "Attack" },
  { id: "monsters", label: "Monsters" },
  { id: "players", label: "Players" },
  { id: "spellcasters", label: "Spellcasters" },
  { id: "skills", label: "Skills/Saves" },
  { id: "initiative", label: "Initiative" },
  { id: "dice", label: "Dice" },
  { id: "search", label: "Search" },
  { id: "settings", label: "Settings" },
  { id: "random", label: "Random" },
];

// Screens implemented so far (others show a placeholder).
const SCREENS = {
  board: renderBoard,
  attack: renderAttack,
  monsters: renderMonsters,
  players: renderPlayers,
  spellcasters: renderSpellcasters,
  skills: renderSkills,
  initiative: renderInitiative,
  dice: renderDice,
  search: renderSearch,
  random: renderRandom,
  settings: renderSettings,
};

// Remember the active tab so a page reload (e.g. Android rotating the WebView)
// returns here instead of resetting to Players.
function loadCurrent() {
  try { const t = localStorage.getItem("dnd.tab"); if (t && TABS.some((x) => x.id === t)) return t; } catch {}
  return "players";
}
let current = loadCurrent();

function setCurrent(tab) {
  current = tab;
  try { localStorage.setItem("dnd.tab", tab); } catch {}
}

function renderNav() {
  const nav = document.getElementById("nav");
  clear(nav);
  for (const tab of TABS) {
    nav.append(el("button", {
      class: tab.id === current ? "active" : "",
      onclick: () => { setCurrent(tab.id); renderNav(); renderScreen(); },
    }, tab.label));
  }
}

async function renderScreen() {
  const content = document.getElementById("content");
  // Let the outgoing screen commit anything pending (e.g. monster/player autosave).
  window.dispatchEvent(new CustomEvent("screen-leaving"));
  clear(content);
  const render = SCREENS[current];
  if (!render) {
    const label = TABS.find((t) => t.id === current)?.label ?? current;
    content.append(el("div", { class: "placeholder", html:
      `<h2>${label}</h2><p>This screen arrives in a later Phase 2 increment.</p>` }));
    return;
  }
  try {
    await render(content);
  } catch (err) {
    content.append(el("p", { class: "placeholder", text: "Error: " + err.message }));
    toast(err.message, true);
  }
}

// Cross-screen navigation (e.g. board double-click → edit a token's roster entry).
window.addEventListener("navigate", (e) => {
  const { tab, selectName } = e.detail || {};
  if (!tab) return;
  if (tab === "monsters" && selectName) selectMonsterByName(selectName);
  if (tab === "players" && selectName) selectPlayerByName(selectName);
  if (tab === "attack") presetMatchup(e.detail.attackerName, e.detail.defenderName);
  if (tab === "board" && e.detail.selectTokenId != null) presetSelectToken(e.detail.selectTokenId);
  if (tab === "spellcasters" && e.detail.selectCasterId != null) presetCaster(e.detail.selectCasterId);
  if (tab === "spellcasters" && e.detail.selectSpellName) presetSpell(e.detail.selectSpellName);
  if (tab === "dice" && e.detail.dice) presetDice(e.detail.dice.count, e.detail.dice.die, e.detail.dice.modifier);
  if (tab === "skills" && e.detail.massSaves) presetMassSaves(e.detail.massSaves);
  if (tab === "skills" && e.detail.quickSave) presetQuickSave(e.detail.quickSave);
  setCurrent(tab);
  renderNav();
  renderScreen();
});

async function main() {
  try {
    await store.load();
  } catch (err) {
    document.getElementById("content").textContent = "Failed to reach server: " + err.message;
    return;
  }
  renderNav();
  renderScreen();
}

main();
