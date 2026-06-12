"""Search tab — fuzzy lookup of the local library or live 5e.tools.

Type a spell, monster, item, or feat. Fuzzy "did you mean" correction against
the canonical 5e.tools catalog (merged with local homebrew names) resolves
noisy input to the real entity, then the user picks:

  • Search Local    — opens the matching spell in the Global Spell Library
  • Search 5e.tools — opens a direct deep-link in the default browser

Matching is case-insensitive. Deep-linking the user's real browser sidesteps
the site's bot protection entirely.
"""

import tkinter as tk
import webbrowser

from rapidfuzz import fuzz, process, utils

from GlobalStateManager import GSM
from search.links import url_for
from search.matcher import build_matcher
from tabs.Spellcasters import _open_global_spell_library

_matcher = None
_matcher_local_count = -1


def _get_matcher():
    """Cached catalog matcher, rebuilt when the local spell library changes."""
    global _matcher, _matcher_local_count
    local = [(s.get("name", ""), "spell") for s in GSM.Spell_library if s.get("name")]
    if _matcher is None or _matcher_local_count != len(local):
        _matcher = build_matcher(extra=local)
        _matcher_local_count = len(local)
    return _matcher


def Search(frame) -> None:
    tk.Label(frame, text="Search", font=GSM.Title_font).place(x=10, y=10)
    tk.Label(
        frame,
        text="Type a spell, monster, item, or feat — then search your library or 5e.tools.",
    ).place(x=10, y=45)

    # ── search field ──────────────────────────────────────────────────────
    query_var = tk.StringVar()
    entry = tk.Entry(frame, textvariable=query_var, width=48, font=("Helvetica", 12))
    entry.place(x=10, y=80)
    entry.focus_set()

    # ── button row ────────────────────────────────────────────────────────
    local_btn = tk.Button(frame, text="Search Local", width=14, bg="#336633", fg="white")
    local_btn.place(x=10, y=115)
    web_btn = tk.Button(frame, text="Search 5e.tools", width=14, bg="#554488", fg="white")
    web_btn.place(x=145, y=115)

    # ── status + suggestions ──────────────────────────────────────────────
    status_var = tk.StringVar(value="Ready.")
    tk.Label(frame, textvariable=status_var, fg="#444", anchor="w").place(x=10, y=155)

    tk.Label(frame, text="Did you mean…  (double-click to use)").place(x=10, y=185)
    sugg_frame = tk.Frame(frame)
    sugg_frame.place(x=10, y=210, width=440, height=300)
    sugg_scroll = tk.Scrollbar(sugg_frame, orient="vertical")
    sugg_lb = tk.Listbox(sugg_frame, yscrollcommand=sugg_scroll.set, font=("Helvetica", 11))
    sugg_scroll.config(command=sugg_lb.yview)
    sugg_scroll.pack(side="right", fill="y")
    sugg_lb.pack(side="left", fill="both", expand=True)

    _suggestions: list = []  # parallel to listbox rows (MatchResult)

    # ── suggestions ───────────────────────────────────────────────────────
    def _show_suggestions(query: str) -> None:
        sugg_lb.delete(0, "end")
        _suggestions.clear()
        for r in _get_matcher().suggestions(query, limit=20):
            _suggestions.append(r)
            sugg_lb.insert("end", f"{r.name}   ({r.category}, {int(r.score)}%)")

    def _use_selected(_event=None) -> None:
        sel = sugg_lb.curselection()
        if sel and sel[0] < len(_suggestions):
            query_var.set(_suggestions[sel[0]].name)
            entry.icursor("end")

    sugg_lb.bind("<Double-Button-1>", _use_selected)

    # ── local search (spells only for now) ────────────────────────────────
    # TODO: Search Local fails ~99.9% of the time today because the only local
    #   library that exists is the spell library, which is usually empty/small.
    #   It stays here as the intended entry point for once the local MONSTER,
    #   ITEM, and FEAT libraries are built — then it should search all of them,
    #   not just spells. Until then it almost always falls through to "try 5e.tools".
    def _search_local() -> None:
        query = query_var.get().strip()
        if not query:
            return
        names = [s.get("name", "") for s in GSM.Spell_library if s.get("name")]
        if not names:
            status_var.set("Local spell library is empty.")
            return
        hit = process.extractOne(
            query, names, scorer=fuzz.token_sort_ratio,
            processor=utils.default_process, score_cutoff=65,
        )
        if hit is not None:
            name = hit[0]
            status_var.set(f"Opened “{name}” from the local library.")
            _open_global_spell_library(preselect_name=name)
        else:
            status_var.set(f"“{query}” isn't in your local spell library — try 5e.tools.")

    # ── 5e.tools search (direct deep-link in the user's default browser) ──
    def _search_5etools() -> None:
        query = query_var.get().strip()
        if not query:
            return
        match = _get_matcher().best(query, score_cutoff=60)
        if match is not None:
            url = url_for(match.name, match.category, match.source)
            if url:
                webbrowser.open(url)
                status_var.set(f"Opened 5e.tools: {match.name} ({match.category}).")
                return
        # No catalog match (or homebrew with no 5e.tools page) — open the site.
        webbrowser.open("https://5e.tools/")
        status_var.set(f"No catalog match for “{query}” — opened 5e.tools.")

    # ── field QoL: live suggestions, select-all on focus, ctrl-clear ──────
    def _on_type(_event=None) -> None:
        q = query_var.get().strip()
        if len(q) >= 3:
            _show_suggestions(q)

    def _select_all_on_focus(_event=None) -> None:
        # Defer so the click's own cursor placement doesn't drop the selection.
        entry.after(0, lambda: (entry.select_range(0, "end"), entry.icursor("end")))

    def _clear_field(_event=None) -> str:
        query_var.set("")
        return "break"  # suppress the default single-char delete

    entry.bind("<KeyRelease>", _on_type)
    entry.bind("<Return>", lambda _e: _search_local())
    entry.bind("<FocusIn>", _select_all_on_focus)  # clicking in selects all → type to replace
    entry.bind("<Control-Delete>", _clear_field)
    entry.bind("<Control-BackSpace>", _clear_field)

    local_btn.config(command=_search_local)
    web_btn.config(command=_search_5etools)
