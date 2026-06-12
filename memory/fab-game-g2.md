---
name: fab-game-g2
description: "project (2026-06-12): G2 BUILT — Czochralski/Scheil boule (first new front-of-line physics) + the unit-of-run resolution"
metadata: 
  node_type: memory
  type: project
  originSessionId: a21daec3-839b-407c-a5c5-d784dda1a87d
---

**G2 BUILT (2026-06-12)** — the first new **front-of-line** physics on [[fab-game]], and the build
where the single-wafer-vs-boule unit-of-run question (flagged by [[fab-game-g1]]) became load-bearing
and was **resolved**. `chip/czochralski.py` (cited Scheil + Boule + resistivity, triad-tested 12) +
`fab_game` wiring + the `demo_boule` artifact. Fast lane 314→**338** (+24). **No engine amendment, no
ADR, no chip demo/gallery card** (G2's artifact lives in the game layer per ADR 0005's two-layer split;
the chip gallery globs `chip/demo_*.py` so a chip demo would force an index.html regen — skipped).

**THE physics — Scheil normal-freezing closed form.** `C_s(z) = N_seed·(1−z)^(k−1)`, z = fraction
solidified. For k<1 (every shallow dopant) the rejected solute piles up → later-frozen solid is MORE
doped → wafers down the boule start at rising N_A. Purification is the same eqn read backwards:
`C_s(0)/C_0 = k`, so tiny-k metals (Fe ~1e-5) scrub ~5 orders at the seed, B (k≈0.8) barely — why CZ
purifies, straight from the k table.

**Triad** (`test_czochralski.py`): **tight** = k→1 uniform limit (`C_s≡N_seed`, machine-precision) +
**exact seed value** for any k; **conservation** = closed-form axial integral `(N_seed/k)(1−(1−z)^k)`
vs `np.trapezoid` on [0, 0.9] (genuine independent anchor, not algebra) + the full-boule limit
`∫₀¹ C_s = N_seed/k = C_0` (the z→1 divergence is **integrable** for k>0 → conservation is tight over
the WHOLE boule, not just partial); **benchmark (loose)** = cited **Trumbore 1960** k (B 0.80 / P 0.35
**verified vs source**, same ref as [[dopant-solid-solubility-source]] which also tabulates k) +
resistivity `ρ=1/(qμN)` reusing **Masetti** `μ(N)` from `junction.py` ([[dopant-mobility-source]], an
INDEPENDENT transport model → non-circular; 0.196 Ω·cm at 1e17 B = textbook).

**THE advisor seam fix (load-bearing).** First plan was `C_0=N_A/k` then `slice(0)=k·C_0` = the
`x/y·y ≠ x` float trap — and `1e17 > 2^53` isn't exactly representable, so the bit-for-bit
`demo_device` seam (through V_t's `log(N_A/n_i)`/`√N_A`) would fail. Fix = **parameterize by the
seed-end concentration** `N_seed ≡ C_s(0)`: `C_s(z)=N_seed·(1−z)^(k−1)` → `slice(0)=N_seed·1.0=N_seed`
**exactly** (IEEE `pow(1.0,·)=1.0`, `×1.0` exact), AND it's the physically natural knob (wafer #1's
spec'd doping). The v1.4/v1.6 "construct the seam to be exact" move.

**THE unit-of-run resolution (the task's named load-bearing deliverable; plan §10 marked RESOLVED).**
Unit of a run = **one wafer at axial `slice_z`** (a `CzochralskiKnobs.slice_z` field); the boule is
**shared context** that sets the wafer's starting substrate via the `channel_N_A` Scheil-slice
**property** (was a plain field — now derived). `run_batch` = the sweep **down** the boule (an
analysis/demo VIEW that surfaces where each slice sits on the Scheil curve, NOT the roguelike loop).
"single-wafer run, surface where your slice sits on the curve" realized. Axial story is per-wafer →
composes **orthogonally** with the radial die-map (focus bowl); G1's "diffusion once, broadcast"
survives within each wafer.

**The payoff (banked `demo_boule`/`fab-game-g2.png`).** Boron k=0.8<1: over z=0→0.9, N_A rises 1.585×
(1e17→1.585e17) → device **V_t walks 0.547→0.747** purely from substrate doping → crosses the [0.45,
0.68] V_t window at **z≈0.8** → the boule **tail is scrapped** (2/10 slices). With `NO_VARIATION`
(run_batch default — isolates the clean Scheil signal) yield is a 100→0 **step**; the [[mos-threshold-voltage-source]]
device just reads N_A→V_t (the propagation), only the front-of-line WIRING is new.

**Oxygen→thermal-donors DEFERRED (advisor).** Planned for G2 ("+ first contamination demo") but
fenced to a G2 follow-on / G4: oxygen's k is **contested ~0.25–1.4** and incorporation is
dissolution-controlled (not dopant segregation), and the ~450 °C donor kinetics are calibrated — so
folding it into `czochralski.py` would borrow Scheil's tight anchors for a loose number. Bank the tight
Scheil core clean first. Table asymmetry noted: `SEGREGATION_K` has Sb/Fe/Cu but Masetti `μ(N)` only
B/P/As → `resistivity()` defined for those three (off the G2 path).
