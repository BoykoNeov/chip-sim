---
name: historical-modes-a2
description: "project (2026-07-10): historical-modes A2 BUILT — the wavelength/lens ladder (Rayleigh floor) + proximity √(λg) gap wall (rides the engine, BE); A4 next"
metadata:
  node_type: memory
  type: project
  originSessionId: 01c80eec-bd70-49fc-94b0-b48db9d07937
---

**Historical-modes A2 BUILT** (`chip/litho_history.py` + `demo_litho_history.py` + tests; gallery card
`hist·A2`; H0 timeline rung stage=Lithography; `chip-litho-history.png`). Pure additive **consumer** of
`chip/litho.py` — no engine change, no existing behaviour touched (same discipline as [[historical-modes-a1]]
/ [[historical-modes-a3]] / [[historical-modes-b6]]). First **Tier-2** (surface-fed) mode after H0 stood up
the era surface. Order A1 ✅ → A3 ✅ → B6 ✅ → H0 ✅ → **A2 ✅** → **A4 next** → B5. Two orthogonal modes in
one chunk (the A3 two-modes precedent):

**§A — the wavelength/lens ladder (pure reuse, the tight leg).** `NODES`: g-line 436/0.28 → i-line 365/0.45
→ KrF 248/0.60 → **ArF 193/0.85/σ0.5 (default)** → 193i 193/1.35 → EUV 13.5/0.33. `image_at_node` is
*literally* `litho.expose_grating` at that node's `Imaging`, so the **ArF default = demo_litho bit-for-bit**
(the seam is a real reduction, not a wrapper artefact — the advisor made me pin ArF exactly to demo_litho's
stepper for this). Demo left panel = contrast-vs-pitch, one curve/node, resolution wall `λ/NA` marching left
(EUV→g-line); a 300 nm target line resolves at 4/6 nodes (KrF-and-finer — partial coherence resolves *below*
λ/NA, so the naive "g/i/KrF flat" was wrong, computed the split instead).

**§B — contact/proximity/projection shadow printing (the one small new model).** Proximity gap `g` blurs the
mask on a **`√(λg)`** near-field length ([[litho-tool-proximity-source]]). Modelled as a Gaussian blur of the
*true binary mask* that **rides the diffusion engine** — `litho.peb_blur` in **backward-Euler**. This was the
key build decision (advisor Trap 1): the *analytic* periodic heat-kernel on truncated `grating_orders`
**Gibbs-rings** (I_min<0, contrast>1, non-monotone) because a binary square wave truncated to n_orders
overshoots; BE's discrete max-principle blurs the real step ring-free (≥0). A **second** optical reason litho
leans on the program's PDE (after v1.7 PEB). **Contact (g=0) → σ=0 → sharp mask bit-for-bit** (peb_blur
returns input). Wall = monotone **contrast/NILS** collapse — NOT CD: a symmetric 50%-duty grating mean-clipped
holds CD≈duty until it abruptly unresolves (advisor Trap 2), so CD is the resolves/doesn't binary only.

**Realism finding (drove the demo scale):** `√(λg)` resolves **microns, not sub-micron** — a 600 nm feature
dies by a ~0.25 µm gap, so §B demo uses a realistic **8 µm** proximity feature (4 µm L/S), gaps 0–50 µm,
`proximity_resolution_gap ≈ 37 µm` (where σ=half-pitch). g-line 436 nm = the classic broadband contact/prox
aligner line.

**Triad, sharpened by advisor** — keep two claims SEPARATE: **tight** = `R=k₁λ/NA` monotone in the *ratio*
λ/NA (a formula property, sign-robust, tested on a synthetic ratio sweep) + the ArF seam + the g=0 contact
seam + the blur's mean conservation (BE conserves total to ~1e-9, NOT 1e-12 — linear-solve roundoff, relaxed
the test). **flagged** = the *historical-ladder* λ/NA ordering g→EUV (rests on the NA table, tested as a
documented-flagged consequence, not a law) + the `√(λg)` prefactor `k≈1` (well-founded: grating fundamental
dies where half-pitch≈√(λg)). **Scope edges named:** blur *envelope* not the Talbot near-field; BE is ~6×
CN kernel error but ring-free (flagged-magnitude trade); contact's real wall is defectivity not blur; scalar
model overstates 193i/EUV (vector/reflective); a node carries only λ/NA/σ (resist=A4, mask/OPC/OAI not
abstracted). Fast lane 967 green. See [[litho-aerial-image-source]], [[litho-peb-v17]] (the other engine-ride),
[[litho-car-v19]].
