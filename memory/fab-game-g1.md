---
name: fab-game-g1
description: Fab-game G1 BUILT 2026-06-12 — fab_game/ harness wired through the validated back end; one bad knob (defocus) → dead die + failure trail; 5 mechanics invariants green
metadata: 
  node_type: memory
  type: project
  originSessionId: dffe5088-7201-43e3-953e-bf624ab3edb8
---

**project (2026-06-12):** **G1 of [[fab-game]] BUILT** — the harness + vertical slice. New
**`fab_game/`** subpackage (`state.py` immutable `WaferState`/`Die` die-map + append-only
provenance, `recipe.py`, `variation.py`, `spec.py`, `steps.py`, `pipeline.py`, `demo_fab_game.py`
+ `plots.py` + `fab_game.ipynb`), wired through the *already-validated* diffusion→oxidation→litho→
device back end. **ZERO new physics** — every number is a `chip/` module that already passes its
triad. 25-test mechanics suite, fast lane → **314** (+25). `testpaths`/`setuptools.include` += `fab_game`.
Banked artifact `docs/figures/fab-game-g1.png`. **The `process.py` that was never built** (ADR 0005:
`device.py` consumed scalars, chaining lived only in `demo_device.py`).

**The 5 ADR-0005 §5 mechanics invariants (all green):** (1) **seam** — nominal + zero-variation
single die reproduces `chip.demo_device.compute()` **bit-for-bit** (`==`, demo IS the oracle →
self-maintaining); the **load-bearing one, built FIRST** (advisor's order, before die-map/yield/
rework exist). (2) **determinism** — one `np.random.default_rng(seed)` threaded in **fixed die
order** → same (seed,recipe)→identical `WaferState`. (3) **propagation-wired** — device genuinely
*reads* inherited `t_ox`→`V_t` (monotone ↑) and `cd`→`I_Dsat` (∝1/L, ↓) **but not** `V_t`, and
**refuses** (no device) on an upstream functional fail. (4) **bookkeeping** — good+bad=total,
provenance append-only, rework accounting closes. (5) **import-direction guard** — AST scan: no
`chip/`||`engines/` file imports `fab_game` (the one-way boundary, mechanical not by convention).

**THE finding (advisor-confirmed; CORRECTS plan §1 prose, note added there):** defocus's **primary
casualty is NILS** (image sharpness, the cited printability metric), **NOT CD** — for a symmetric
line/space feature the **CD midpoint is defocus-robust** (CD 167.2→167.6 nm over 0–200 nm while
**NILS collapses 4.6→1.5**). CD only collapses at **EXTREME** defocus (z≳250), and when it does it
**raises** `I_Dsat` (shorter L over-drives) → **I_Dsat *ceiling* not floor**. **`V_t` is NEVER on
the defocus chain** (device's own scope edge: no channel-length term; only `saturation_current`
reads CD). So the plan's *"defocus→CD out of window→`V_t`/`I_Dsat` leave spec"* is the EXTREME
regime, not the primary. Demo shows BOTH: **NILS edge-ring at defocus=90 nm** (yield 100%→**67.6%**,
dead edge ring via the **center-to-edge focus bowl**; worst die eff-defocus +145 nm) **and** the
literal **CD/I_Dsat collapse at 320 nm** (CD 115 nm <150 floor, I_Dsat 4.9 mA >4.2 ceiling). Specs =
**flagged house defaults** (NILS floor 2.8 ← cited printability rule [[litho-aerial-image-source]];
CD/I_Dsat/V_t = house bands) — ADR 0005 §5: game is mechanics, not magnitudes.

**Advisor's other load-bearing calls:** (a) **systematic knob through physics** (per-die effective
focus = base + center-to-edge tilt → real Bossung optics), **die-to-die scatter at the output**
(CD/t_ox jitter) — zero-variation collapses both → the seam (**trend off ⇔ variation off**).
(b) **NO `device_2d.mosfet_cross_section` per die** — a full 2-D solve (nx180×ny140×150 steps), not
in `demo_device` so it can't be in the seam; per-die path is `device.py` (CD=channel length).
(c) **diffusion computed ONCE and broadcast** (die-independent in G1, the one engine solve avoided
per die). **Rework realism (my own design fix):** the **center-to-edge focus bowl PERSISTS across
re-exposure** (same scanner) — `rework_litho` re-applies the systematic tilt (drops the random
scatter), only the player's **global** focus offset is corrected → an *insufficient* correction
leaves the worst edge dies failed (re-exposing the same recipe rescues nothing; honest). **Notebook
executes headless but is NOT gated** ([[chip-notebook-flake]] — no live-kernel gate test).
Single-wafer for G1 (boule load-bearing at G2). [[engine-unfrozen]].
