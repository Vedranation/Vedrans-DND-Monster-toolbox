// Client-side mirror of server state. The web equivalent of GlobalStateManager's
// domain data — loaded from the API, refreshed after mutations.

import { api } from "./api.js";

export const store = {
  constants: null,   // dropdown lists (roll types, dmg types, …)
  state: null,       // { monsters, players, spell_library, settings }

  async load() {
    this.constants = await api.get("/api/constants");
    this.state = await api.get("/api/state");
  },

  async refreshState() {
    this.state = await api.get("/api/state");
    return this.state;
  },
};
