---
name: historical-modes-h0
description: "project (2026-07-10): historical-modes H0 BUILT — the era-timeline display surface (chip/history_gallery.py → docs/history.html); Tier-2 modes A2/A4/B5 now unblocked"
metadata: 
  node_type: memory
  type: project
  originSessionId: 36a81d94-d558-46a7-a2e1-69900e11de4e
---

**Historical-modes H0 BUILT** — the **era display surface**, the shared consumer that unblocks the
consumer-less **Tier-2** modes ([[historical-modes-a1]]'s three-tier bar). Order: A1 ✅ → A3 ✅ →
B6 ✅ → **H0 ✅** → A2 → A4 → B5. **A2 (litho tool/wavelength) is next** (Tier-2, now buildable).

**What it is:** a *third* gallery generator, `chip/history_gallery.py` → `docs/history.html` +
`docs/history.local.html`, golden-tested by `chip/tests/test_history_gallery.py` (7 asserts mirroring
[[gallery-local-edition]]'s split: manifest completeness, figures-exist, public+local currency,
public=GitHub-only, local=localhost-only). **Home = `chip/` not `fab_game/`** because the modes it
reads are `chip/demo_*_history.py` → chip→chip introspection, no ADR-0005 direction problem (unlike the
game gallery). **The timeline is a re-cut, not new figures:** the same banked `chip-*-history.png`
the flat physics gallery already lists, but the `demo_*_history.py` **subset**, re-ordered along the
process spine (doping→oxidation→metallization) and annotated with a **period → wall → successor** row
the flat gallery has no slot for. Pure display — introspects each `DOCS_FIGURE` via
`chip.gallery.figure_relpath` (viz-free import), never runs the demos' compute.

**The reuse discipline (advisor's load-bearing catch):** import `_STYLE` / `figure_relpath` / the
`_BLOB`/`_TREE`/`_LAB`/`_LAB_ROOT`/`_REPO_URL`/`_LOCAL_PORT`/`DOCS_DIR` constants from `chip.gallery`
**unchanged** — do NOT edit `_card`/`_grid`/`_STYLE` (they feed three golden-tested pages + the fab_game
gallery). The `_card`/`Demo` shape can't show era/wall/successor, so H0 defines its own `HistoryMode`
dataclass + `_rung` renderer + a local `_TIMELINE_CSS` layered on top of the shared `_STYLE` (a vertical
timeline: dotted spine, era badge, a 2-col figure|story card, colour-coded Period/The-wall/Replaced-by
rows). Inclusion **glob-anchored on `demo_*_history.py`** (a subset glob — NOT `demo_*.py` like the
physics test, which asserts full coverage). Timeline text lifted verbatim from the plan's
"historical/educational spine" (doping→implant, drifting-oxide→HCl + 1-atm→high-pressure, Al-spiking→
barrier metal), not re-invented.

**Discoverability — USER-CHOSEN at build (AskUserQuestion), overriding the plan's "no existing page
changes" seam:** cross-link cards added **both ways** (the fab-game precedent). `index.html` +
`fab-game.html` each gained ONE "era timeline" Go-deeper card, **both editions** — verified the git diff
is exactly **+6 lines/file × 4 files** (public+local × 2 galleries), nothing else drifted. Added the
`history`/`history.local.html` link var to both branches of both generators' `render_html`; the
public/local split holds (history.html: github-only; history.local.html: localhost-only). Plus a
**markdown backward-axis cell** in `chip/chip.ipynb` (markdown-only to dodge the [[chip-notebook-flake]];
notebook smoke test only checks clean execution, no cell-count/hash). Regenerate all six pages with
`python -m chip.gallery && python -m fab_game.gallery && python -m chip.history_gallery`.

See [[historical-modes-a1]] (the axis + tier bar), [[historical-modes-a3]], [[historical-modes-b6]],
[[gallery-local-edition]] (the two-gallery/public+local rules H0 extends to a fourth+fifth page pair).
