---
name: fab-game-g4
description: "project (2026-06-13): G4a BUILT — silicon purification (Pfann zone refining) + the contamination consequence model; Na→Q_ox→V_t lifts the device edge; Tier-2 lifetime.py deferred to G4b"
metadata: 
  node_type: memory
  type: project
  originSessionId: c9ff1370-a3f8-4dab-af30-dca9ec852293
---

**G4a BUILT (2026-06-13)** — silicon purification + the Tier-1 contamination consequence model, the
fab-line game's first **back-of-feedstock** physics on [[fab-game]] (after [[fab-game-g3]]).

**The split (advisor, decisive):** G4 cleaves along the plan §7 **tight/loose** boundary →
**G4a = the verifiable purification physics + Tier-1 consequences** (built); **G4b = the loose Tier-2
SRH `lifetime.py`** (τ(N_metal) + junction leakage — the deep-level-metal consequence net doping
*can't* carry; deferred, fenced like G2's oxygen→donors). Shipping loose SRH magnitudes beside the
verifiable win would blur the discipline. Tier-3 (gettering/precipitation/Siemens column) stays named.

**New cited physics `chip/purification.py`** — the **Pfann single-pass** zone-refining closed form
`C(u)=C₀[1−(1−k)e^(−k·u)]` (`u=x/L` zone-lengths), **reusing czochralski's one `SEGREGATION_K` table**
(advisor: "reuse, don't duplicate" — `Na` k≈1e-2 added *there*). Full triad (`test_purification.py`, 12):
- **tight** `k→1 ≡ C₀` **bit-exact** ((1−k)=0) + the `C(0)/C₀=k` **scrubbing identity** (the demo
  punchline — tiny-k metals scrubbed ~5 orders, B k≈0.8 barely) + steady-state `C→C₀` as `u→∞`;
- **conservation REFRAMED (the one real trap, advisor-flagged, verified numerically FIRST):** the
  single-pass formula models only the swept region — the depleted leading-end solute is carried into
  the **final-zone pile-up the formula omits** → `∫C` falls **short** of `C₀·u` by exactly the
  closed-form **swept-out deficit** `(C₀/k)(1−k)(1−e^{−k u})` (= `pfann_swept_solute`, checked vs
  quadrature). **"Mass recovers C₀" is NOT claimed** (it's the named scope edge) — *unlike* Scheil's
  clean `∫₀¹=C₀`. This is THE difference from [[fab-game-g2]]'s Scheil.
- **loose** = cited Trumbore `k` (reused) + flagged `FEEDSTOCK_GRADES` (MGS/solar/EGS/`clean`).
- Numerical note: `C(0)=k·C₀` is good to ~1e-12 not bit-exact (the `1−(1−k)` cancellation for tiny k),
  unlike Scheil's exact `(1−0)^…` seed — it's the loose leg anyway.

**`chip/device.py` lifts the named `Q_ox=0` edge:** `ΔV_FB=−Q_ox/C_ox`, `Q_ox` param default 0.0 →
the term is skipped entirely → **byte-for-byte seam** (no C_ox needed at Q_ox=0; the advisor's watch
point). `D_it` interface traps stay out. `MOSDevice.Q_ox` field added. (`test_device.py` +4.)

**`fab_game` wiring (Tier-1 consequences):** `PurificationKnobs(grade, zone_passes)` → a wafer-level
`Contamination` impurity vector (carries the FULL set incl. Fe/Cu metals now, like state.py's
"arrive with their named consumers"; **uniform across the die map**, composes orthogonally like
`slice_z`/geometry). Two wired reads — **Na → gate-oxide `Q_ox` → V_t DOWN (the headline, lifts the
edge)** via `sodium_oxide_charge` (flagged bulk→areal incorporation length `NA_OXIDE_INCORPORATION_CM`
~0.3µm); **residual B/P → net doping** folded into `Recipe.effective_channel_N_A` (fed to BOTH junction
and device for coherence). **Deep-level metals ride along, scrubbed, NO consequence yet** = the G4b gap.
`diagnose` names the Q_ox/Na root cause in the trail.

**Seam (hard constraint, advisor):** default `grade="clean"` → all-zero vector → Q_ox=0 + net-shift=0
→ `DEFAULT_RECIPE+NO_VARIATION` reproduces `demo_device` bit-for-bit; G1/G2/G3 demos byte-unchanged.
Purification is a **wafer-level provenance step** (no per-die record — surfaces per-die at the device
Q_ox), so `test_bookkeeping` provenance list gained `purification` at index 0 (die history did not).

**The tuning finding:** residual dopant must stay **small vs the intentional 1e17** (a real flow
refines before growth) or residual **B** (k≈0.8, un-refinable) raises V_t and **opposes/masks** the Na
shift — my first MGS B=1e17 made net-doping dominate (V_t *up*). Realistic small B/P → **Na dominates**,
matching the advisor's Na-headline. Bonus: **more zone passes = the rework** (plan step-1 "re-refine")
— 2nd pass scrubs Na ~2 orders → V_t recovers; **residual B persists** across passes (V_t lands
slightly *above* clean) = the un-refinable footnote.

**Banked `demo_purification`/`fab-game-g4.png`** (3 panels): scrubbing contrast (Fe ×8e-6 vs B ×0.8,
one pass) | grade-ladder V_t walk (clean/EGS/solar pass, **MGS V_t→0.374 < 0.45 floor, scrapped**) |
rework recovery (passes 1→2: 0%→100% yield). Fast lane 373→**400** (+27); no engine amendment, no ADR,
no chip gallery card. Mechanics in `test_contamination.py` (5) + `test_propagation.py` (+2) +
`test_demo_purification.py` (4). [[fab-game-g3]] [[mos-threshold-voltage-source]] [[dopant-solid-solubility-source]]
