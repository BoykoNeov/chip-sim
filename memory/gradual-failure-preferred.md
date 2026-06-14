---
name: gradual-failure-preferred
description: standing policy — model graded/gradual failure over cliff (all-or-nothing) failure whenever it is physically realistic
metadata:
  type: feedback
---

Standing policy for the fab-game (and consequence modelling generally): **gradual /
graded failure is the preferred failure mode whenever it is physically realistic.**
When a decision's downstream consequence *could* honestly produce a partial-yield
slope (some dies fail, a yield gradient) rather than an all-or-nothing cliff, build
the slope.

**Why:** the user wants the game's stages to span the full ok → doesn't-matter →
problems/rework → outright-failure spectrum (their message-4 brief). A cliff (a knob
that flips the whole wafer 0%↔100%) collapses that spectrum to a coin flip and kills
the "marginal feedstock → rework" middle band that makes the decisions interesting.

**How to apply:** when a stage's consequence comes out binary, look for the *realistic*
mechanism that makes it graded before accepting the cliff — and distinguish it from a
fudge. The honest move is usually **spatial non-uniformity of the offending quantity**
(which is real fab physics and often *lifts a named scope edge*, the [[scope-edge-backlog]]
"promote when a consumer appears" pattern); the fudge is inflating an *unrelated*
receiving-variable's spread past its real value just to smear the cliff. Keep the
magnitude flagged (cite the channel, flag the gradient steepness) — graded ≠ predicted
numbers.

**First application — BUILT 2026-06-14 (the graded-failure *mechanism*, not yet a player
stage).** The **purification** Na→Q_ox→V_t consequence was a near-step (whole wafer flips
between Na≈3e15 and 8e15 cm⁻³; decade-spaced grades + ~1/k-per-pass refining jump right
over the half-decade partial band → grade choice is a *cliff*, EGS=100% / solar=0%). The
honest slope shipped as **edge-loaded Na**: `Variation.na_factor(r) = 1 + na_edge_boost·r²`
(`na_edge_boost=2.5`, a flagged ~3.5× rim/centre — handling/edge-bead/furnace radial
gradients), applied per-die at the device step (`pipeline._die_contamination` scales the
wafer Na by it). A marginal feed now kills an **outboard ring** (verified ~46% yield, kills
on the rim) where a uniform model saw a clean pass.

**The key honesty move (advisor-confirmed):** a 10× rim boost would have been needed to
force the *coarse discrete* levers into the band — that's the fudge. Instead the slope is
bought with a **continuous refining lever** (`front_purity`'s `k^n` is smooth in `n` →
`zone_passes` relaxed to `float`; a fractional pass lands the band integer passes leap
over), so a *modest, clearly-real* 3.5× rim suffices. BOTH the `r²` profile AND the
steepness are flagged (not derived). Seam-exact: gated off when variation disabled (uniform
Na ⇒ `demo_device`) and irrelevant to a clean Na=0 feed; composes with the focus bowl
through a *different* spec channel (Q_ox→V_t vs CD→NILS), so they stack not double-count;
litho-rework does NOT rescue it (only purifying does). Lifts the purification module's own
flagged scope edge ("within-wafer contamination non-uniformity is out") for the Na channel
only. Tests: `fab_game/tests/test_na_ring.py` (9). Channel anchors to Snow–Grove–Deal–Sah
mobile-ion transport. **No player surface yet** — reachable only via a test probe; the
purification *stage* (continuous lever as a UX knob + multi-step + consequence preview +
the staged journey scaffold) is the next phase. [[fab-game]] [[scope-edge-backlog]] [[engine-unfrozen]]
