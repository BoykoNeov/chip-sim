---
name: roadmap-page
description: "docs/roadmap.html BUILT (2026-07-14) — 4th docs page, schematic previews for PLANNED slices F3–F10; plus site-wide dark mode + nav strip in the shared _STYLE"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6c5bc832-57a3-4cdc-afa4-69991f96e7f3
---

**Roadmap page + gallery visual overhaul (2026-07-14, commit a70071c).**

Two additions to the docs surface:

1. **Site-wide visuals** — `chip/gallery.py`'s shared `_STYLE` now drives all FOUR pages with
   CSS variables + a `prefers-color-scheme: dark` counterpart for every color; a `_nav(current,
   local)` strip cross-links physics / fab-game / history / roadmap (public↔public,
   local↔local); the local-edition note moved from inline styles to a `.localnote` class.
   `fab_game/gallery.py` and `chip/history_gallery.py` import `_nav`; timeline wall/next inks
   are variables now.

2. **`docs/roadmap.html` (+ `.local`)** — the 4th docs page: visual resources for the
   **planned-but-unbuilt** slices of `future-steps.md` (F3 high-κ, F4 BEOL RC, F5 SiGe, F6 epi,
   F7 STI remainder, F8 CMP, F9 FinFET/GAA, F10 EUV). Deliberately a SEPARATE page: the other
   three show only built/banked artifacts; mixing planned schematics into them would blur the
   honesty line.
   - `chip/roadmap_figures.py` — one matplotlib schematic per slice, **in-image stamp
     "PLANNED — schematic preview, not simulator output"** (so a hot-linked copy can't
     impersonate a banked demo figure); only cited era landmarks as numbers (13.5 nm, ~1.2 nm
     wall, 2007/45 nm); lazy matplotlib import (demo-module convention).
   - `chip/roadmap_gallery.py` — cards carry the plan's verdicts VERBATIM (Promotable /
     Coupled to F1 / Partly built (B5) / Deferred) + "Would add" (the observable) + "Gated on"
     (the named consumer) — it **displays** the triage, never re-triages.
   - Drift guard `chip/tests/test_roadmap_gallery.py` mirrors the other three PLUS honesty
     chrome: every card ribboned "planned — schematic"; the page may reference only
     `roadmap-*.png`, never `chip-*`/`fab-game-*` figures.

**The graduation rule:** when a slice ships, its card comes OFF the roadmap (remove from
`SLICES` + `FIGURES`, delete the `roadmap-*.png`) and its real demo joins the galleries — the
manifest↔registry sync test forces this to happen together.

Related: [[scope-edge-backlog]] (B1 gates F9), [[historical-modes-b5]] (F7's built half),
[[historical-modes-b7]] (F2 already built → not on the roadmap), [[gallery-local-edition]].
