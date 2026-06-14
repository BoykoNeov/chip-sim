---
name: fab-game
description: New direction — a gamified full-line fab simulator (sand→chip) layered on top of chip-sim; vision synced + plan/ADR 0005 drafted 2026-06-12
metadata: 
  node_type: memory
  type: project
  originSessionId: dffe5088-7201-43e3-953e-bf624ab3edb8
---

**project (2026-06-12):** a NEW direction — a **gamified, full-production-line fab
simulator** (*sand → packaged chip*) built **on top of** chip-sim, not replacing it. Vision
synced with the user across two AskUserQuestion rounds, then **`docs/plans/fab-game.md` +
`docs/decisions/0005-fab-game-layering.md` drafted** (advisor-reviewed; docs-only commit).

**>> G1 BUILT 2026-06-12 → [[fab-game-g1]]** (the harness + vertical slice: `fab_game/` wired
through the validated back end, "one bad knob → dead die + failure trail", 5 mechanics invariants
green, fast lane 314). The defocus chain's primary signature = **NILS** not CD (plan §1 corrected).

**>> §9 guided ipywidgets slice BUILT 2026-06-14** (`fab_game/dashboard.py` + `plots.dashboard_figure`
+ the `fab_game.ipynb` "command the whole line" section): a thin, **tested** skin over `run_line`
(`run_dashboard`/`dashboard_summary`, 4 dramatic+legible knobs — defocus→edge ring · D₀→scattered
kills · slice_z→Scheil drift · t_ox→the G7 rescue lever) = the **headless, tested core of the
deferred Textual TUI**. Variation **ON** (else the map is a binary all-pass/all-fail flip, not a
story — the advisor's catch). Reuses `LineResult` (no new dataclass); **dropped a profit readout** —
default `speed_bins` grade everything `"pass"` so `score_wafer` prices revenue 0 → a profit line
would be a binning-policy artifact, not a signal. The real safety net is `tests/test_dashboard.py`
(10 tests), NOT the notebook run (`interact` swallows callback exceptions).

**>> Textual TUI v1 BUILT 2026-06-14 (`docs/plans/fab-game-tui.md`):** `fab_game/tui.py`
(`FabLineApp`) = a thin terminal driver of the §9 `run_dashboard`/`dashboard_summary` core + the
ONE new headless helper `plots.wafer_map_text(wafer, *, color=False)` (ASCII die map, `O` pass/`X`
fail, `color=True` wraps in Rich `[green]`/`[red]` markup). `tui.py` is the **only** `textual`
importer and — like `plots.py` — is **NOT** re-exported from `fab_game/__init__` (so `import
fab_game` + the fast lane stay headless); new `[tui]` extra `textual>=8` (verified on 8.2.7). Tested
in `tests/test_tui.py`: 4 pure-renderer legs + 2 `importorskip` App-pilot legs (`run_test()` via an
`asyncio.run` wrapper, NOT `pytest-asyncio`). **Advisor catches that bit:** summary `Static` needs
`markup=False` (arbitrary computed trail text can contain `[...]` → Rich `MarkupError`), map `Static`
`markup=True`; one sync `_run_and_render()` (shared by mount/button/Enter) stashes `last_summary`/
`last_map` for state assertions + the fidelity check (`last_summary == dashboard_summary(...)`).
**Verified:** fast lane 637 green; clean 5×5 under `-n auto` → **no notebook-style flake** (`run_test`
is in-process asyncio, no zmq → the slow/`xdist_group` escape hatch was NOT needed); textual-absent →
4 pass/2 skip. As-built deviation: the button-click pilot test needs `run_test(size=(120,50))` (the
default 80×24 screen clips the Run button below the fold). No new physics/ADR.

**>> Textual TUI v2 — the G7 roguelike loop — BUILT 2026-06-14 (`docs/plans/fab-game-tui.md` §7):**
the deferred session loop landed. NEW headless `fab_game/session_view.py` = the load-bearing string
renderers for a `GameSession` (`turn_recipe`/`oxide_recipe`/`projected_vt`/`inspect_line`/
`session_header`/`turn_line`/`history_trail`/`session_summary`), import-pure (peer to `dashboard.py`,
re-exported from `__init__`, tested by `tests/test_session_view.py` — the §9 discipline: the
swallow-prone Textual surface renders these verbatim, so they're tested WITHOUT textual). `tui.py`
gained `RoguelikeScreen` driving `game.py`'s `GameSession` down one boule: ONE oxide-minutes Input
(the *adapt* lever) + **Process/Scrap/New-run/Back Buttons** (NOT letter bindings — the auto-focused
Input would shadow them, the same v1 footgun; only `escape`/`q` are bindings), opened from a *Play
roguelike* button on `FabLineApp` (`escape` pops back). **THE bug found + fixed:** naming the repaint
helper `_render` **overrode Textual's internal `Widget._render()`** → `visual=None` → render crash;
renamed `_repaint`/`_apply_action` (don't shadow Textual internals). Two as-built calls: (a) **no wafer
map** (the `RunRecord` carries no `WaferState`; the map is the dashboard screen's job — this screen is
the economic/decision arc); (b) action handlers **no-op + buttons disable once `session.done`** (the
model *raises* when over — a thin driver must never throw into the swallow-prone loop, advisor's catch).
The pilot's load-bearing leg is **fidelity not movement**: a driven Process/adapt/Scrap sequence yields
a session == headless `play(new_session(cfg, seed), [same decisions])` verbatim. **Verified:** fast lane
651 green under `-n auto` (no flake across 3 repeats), `import fab_game` stays textual-free.

**>> Educational/Hardcore launch mode BUILT 2026-06-14 (`docs/plans/fab-game-tui.md` §9):** `python -m
fab_game.tui` now opens a `ModeSelectScreen` first. **Hardcore** = the bare cockpit (today's TUI, byte-
identical). **Educational** layers a verbatim **guide panel** on the dashboard + roguelike screens:
a glossary of every selector + readout (defocus, defect density, boule slice z, gate-oxide drive, seed,
V_t, I_Dsat, NILS, CD, leakage, bins, Scheil drift, the trail, process/adapt/scrap) PLUS *what-to-do*
strategy (exploratory on the dashboard, the adapt-vs-scrap decision + the I_Dsat-ceiling caveat on the
roguelike). **Same doctrine:** prose lives in a NEW import-pure **`fab_game/guide.py`** (`dashboard_guide`/
`roguelike_guide`/`glossary_text`/`MODE_INTRO`, re-exported, tested by `tests/test_guide.py` WITHOUT
textual), the TUI renders it verbatim. **Presentation only** → no knob/recipe/physics touched, the seam
is byte-identical, guide is `display:none` in hardcore (reserves no space → existing pilots untouched).
**Two flags forced by "don't break the pilots":** `FabLineApp(educational, prompt_mode)` — pilots build
`educational=…` directly (no chooser), only `main()` sets `prompt_mode=True`. The import-purity test
runs in a **fresh subprocess** (this process's `sys.modules` is polluted by a co-scheduled `test_tui`
pilot under `-n auto`). Verified green serially + `-n auto` (3 repeats, no flake). No new ADR.
**Remaining front-end = the tycoon ONLY** (roguelike loop + educational mode now built; named-consumer
physics backlog stays exhausted).

**>> Input-domain crash guard BUILT 2026-06-14 (`docs/plans/fab-game-tui.md` §10):** a knob that *parses*
but is out of the physics domain (`slice_z` ∉ [0,1), oxide bake ≤ 0) used to **raise into the Textual
handler and kill the App** — the old parse guards caught only non-numeric strings. Fix = headless validator
`dashboard.knob_errors`/`oxide_minutes_error` (friendly notes, tested + cross-checked it can't diverge from
what `run_dashboard` actually raises) + **belt-and-suspenders** in the TUI: pre-screen → note in the panel,
then a `try/except` **net** around the run. **Advisor catch:** scope the catch by *class* not the observed
one — `int(float("1e999"))`→`OverflowError`, so guards+nets widened to `(ValueError, ArithmeticError)`. Two
roguelike crash sites (preview `inspect_line→projected_vt→run_line` AND Process). **The pilot is the real
regression** (raises on un-fixed code; the headless test wouldn't). Seam untouched (defaults validate clean).
No physics/engine/ADR. The "more of a game" asks (more screens, challenge) stay a **design conversation**, not
yet built.

**The seven synced choices:** (1) **full grand tour** — every distinct step,
purification→Czochralski→wafer-prep→oxidation→litho→diffusion→etch/depo→device→dice/bond/test,
repeats collapsed; (2) **both failure models** — deterministic physics mean + stochastic
spread + spec windows → yield; (3) **boule→wafer-batch** (axial **Scheil** variation → each
slice starts different) **+ across-wafer die map** (per-die parameter/defect field, NOT a
full-wafer PDE); (4) **continuous recipe knobs**; (5) **physically-realistic rework** (re-polish
/ strip-&-regrow oxide / re-coat resist reworkable; dislocated crystal + over-driven junction
irreversible); (6) **roguelike-first + sandbox now, tycoon later**; (7) **no game engine as
authority** — Python sim is the source of truth, thin UI (notebook → Textual TUI → web).

**The architecture (ADR 0005):** two layers, one repo to start. **Physics layer** (`chip/`,
`engines/`) stays validated + GROWS the new process physics (purification, CZ/Scheil, wafer
prep, etch/depo, packaging) as cited triads; **game layer** = a new **`fab_game/` subpackage**
owning `WaferState`/die-map, pipeline driver, spec windows, stochastic+yield, rework, scoring,
UI. **One-way import** `fab_game → chip/engines` (import-direction guard test), **in-repo first,
split when mature** (rule-of-three + the BigSim monorepo→split precedent). Game tested for
**mechanics invariants** (determinism under seed, propagation-actually-wired, state bookkeeping,
seam-reproduces-existing-demos) NOT cited magnitudes.

**Build order = vertical slice FIRST** (advisor, load-bearing): **G1** = the harness +
WaferState wired through the *already-validated* diffusion→oxidation→litho→device back end
(the `process.py` that was never built — `device.py` only consumes scalars, chaining lives in
`demo_device.py`), banking "one bad knob → a dead die + the failure trail", ZERO new physics.
**Then G2** Czochralski/**Scheil** (the one verifiable front-of-line win: `C_s(z)=k·C₀·(1−z)^{k−1}`,
exact `k→1`=C₀ + `∫=C₀` conservation legs are tight; **diverges as z→1** so spread numbers are the
LOOSE leg). Then wafer-prep/particles (G3), purification/contamination field (G4), etch/depo (G5),
packaging/test (G6), roguelike shell + TUI (G7).

**OPEN (flagged, advisor-caught, settle at G2):** *unit of a run* — single-wafer-roguelike vs
boule→batch are in tension; Scheil's payoff is seeing resistivity vary DOWN the boule, which a
single-wafer view never shows. Clean reconcile = single-wafer run that surfaces where your slice
sits on the boule's Scheil curve. Other G1 opens: WaferState schema + die-grid resolution,
spec-window sources, variation σ defaults, pipeline-vs-state-machine, seeded-RNG home.

**CONTAMINATION/PURIFICATION feasibility (folded into plan §5a, advisor-verified 2026-06-12):**
THE crux = propagation is gated by the **device's receiving variable, NOT the engine** — today
that's **net doping**, so "simulate bad purification" = **extend the consequence model**, not
diffuse more species (engine is single-field, multi-species = independent runs). **Four buckets:**
(1) shallow dopant B/P → net doping → rides existing flow **FREE**; (2) Na → oxide charge → lift
`device.py`'s named `Q_ox=0` edge (`ΔV_FB=−Q_ox/C_ox`) **near-free**; (3) deep-level metal Fe/Cu/Ni
→ **SRH recombination center** (lifetime/leakage) NOT doping → propagates to **NOTHING today** (needs
new device output); (4) **oxygen** (crucible) → **thermal donors** via ~450°C kinetics → net doping
(the CZ-native first contamination demo). Metals: fast interstitial → flat profile → diffusion solve
**nearly pointless** → model as areal-dose budget + active fraction + SRH, NOT transport; fate
(gettering/precip) = Tier-3 edge. Unifying thread = the repo's existing **active-vs-chemical** edge
generalized. **Purification = segregation** (Pfann `C/C₀=1−(1−k)e^(−kx/L)` / Scheil), triad-able,
cited `k` (**Trumbore 1960 — ALREADY a repo citation**; Fe~1e-5/Cu~1e-4 vs B~0.8/P~0.35 = why
refining scrubs metals not B/P); Siemens distillation = a **grade knob**, NOT a column sim. **Tiers:**
T1 segregation+dopant/O+Na (cheap+verifiable), T2 a new `lifetime.py` SRH τ+leakage device output
(loose magnitudes), T3 gettering/oxide-breakdown/distillation (name+flag). Tight leg = segregation;
loose = metal magnitudes.

Inherits chip-sim's tar pits (no TCAD/EMF, microchip §5) + the export-control **educational
carve-out** (generic textbook physics, no real recipes/targeting). [[engine-unfrozen]] is the
reusable engine spine; [[lateral-diffusion-2d]]/[[chip-device-2d-v111]] are the 2-D reuse;
[[dopant-solid-solubility-source]] (Trumbore 1960) already covers the segregation `k`.
