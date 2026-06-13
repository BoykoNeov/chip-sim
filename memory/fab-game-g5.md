---
name: fab-game-g5
description: fab-game G5 BUILT — chip/etch_deposition.py (etch bias → gate CD + step-coverage voids) wired into the mid-line; the flagged-phenomenology tier
metadata:
  node_type: memory
  type: project
---

**project (2026-06-13):** **G5 BUILT** — the mid-line **etch & deposition** step (plan §6 G5, §5
step 7), the first **flagged-phenomenology** tier ([[fab-game]] §7) where *no* detailed-balance /
only-possible-law invariant exists. New cited physics `chip/etch_deposition.py` (triad 14), two
sectioned parts:

1. **Pattern-transfer etch** — anisotropy `A` → **etch bias** `2·(1−A)·h·(1+OE)` shrinks the resist
   CD into the gate CD (over-etch deepens the etch → widens the undercut → CD↓); over-etch underlayer
   loss `OE·h/S`. `EtchResult` (cd_out, bias, gate_height, …).
2. **Deposition step coverage** — keyhole **void** when the gap aspect ratio `AR = h/(pitch−CD)`
   exceeds `AR_crit = SC/(1−SC)` (a poor PVD `SC≈0.3` voids the gap a conformal CVD `SC≈0.9` fills).
   `DepositionResult(aspect_ratio, critical_aspect_ratio, voided)`; AR **derived from inherited gate
   geometry** (a genuine propagation, not a free knob).

**The validation honesty (advisor, the load-bearing call):** the ONE genuinely tight leg is the
**bit-for-bit seam** (`A=1` ⇒ bias 0 for ANY film/over-etch; `SC=1` ⇒ never voids — structural,
`(1−A)=0` exactly, NOT a small number); the bias/underlayer/AR algebra is **machinery (regression
guards), NOT a conservation anchor** (no area-additivity/`pn=n_i²` content here, unlike
[[fab-game-g3]]/[[fab-game-g4b]]); magnitudes (anisotropy, step coverage, the pinch-off AR) are
**flagged house numbers** — only the cited *forms* (Wolf & Tauber; Plummer–Deal–Griffin; Campbell) +
band orderings asserted. Defocus's "assert the right observable" analogue: the seam is the anchor.

**Game wiring:** `EtchDepositionKnobs` (default anisotropic+conformal = seam); `etch_deposition_step`
inserted **after litho, before device** — **overwrites `cd_nm`** (device reads the etched gate CD →
propagation needs NO device change; over-etch → CD↓ → `I_Dsat∝W/L`↑ over its ceiling / CD out the
bottom), sets new `voided` field (a **functional kill**, parallel to a killer particle) + `gate_height_nm`.
New spec **void gate**; `diagnose` etch-bias/void branches; `rework_deposition` banks the plan's
**reworkable (depo void strippable) / irreversible (etched CD) contrast**.

**THE advisor traps, all handled:** (A) the etch-rate non-uniformity is a **conditional 4th RNG
draw** — fires only when `etch_bias_sigma_frac>0` (default 0), drawn LAST → enabled runs with σ=0 draw
byte-identically → **G1–G4 banked demos byte-for-byte unchanged** (verified: 423→451 all green, +28
all-new); (B) framed the algebra as guards not anchors; (C) etch step **degrades, doesn't crash** —
unresolved litho passes through to the device refusal, a runaway over-etch (or gates-touch) is a
functional kill. **CMP named & DEFERRED** (no device consumer in the compact model — dishing→opens /
planarity→focus-budget unwired, TTV→focus already a [[fab-game-g3]] `wafer_prep` edge; don't let
"(+ CMP)" pull filler in). **Under-etch** (incomplete-clear → bridging short) also **named as a
deferred edge** (the symmetric counterpart, plan §5 lists "over/under-etch").

Banked `demo_etch`/`fab-game-g5.png` (over-etch CD walk out of window | PVD-voids/CVD-fills map | the
rework contrast). Fast lane 423→**451** (+28); no engine amendment, no ADR, no chip gallery card.
Tests: `chip/tests/test_etch_deposition.py` (14), `fab_game/tests/test_etch.py` (9),
`test_demo_etch.py` (4), + a `test_bookkeeping` deposition-rework leg. Next main-line = **G6**
packaging & test & binning. [[fab-game-g4]] [[engine-unfrozen]]
