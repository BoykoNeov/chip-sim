---
name: historical-modes-a4
description: "project (2026-07-10): historical-modes A4 BUILT — negative-resist swelling → an OPTICS-INDEPENDENT CD floor ≈ film thickness (geometric, NOT an engine ride); B5 next"
metadata:
  node_type: memory
  type: project
  originSessionId: 601bec46-6810-41f2-a6af-919ed1b6c8d9
---

**Historical-modes A4 BUILT** (`chip/resist_history.py` + `demo_resist_history.py` + tests; gallery card
`hist·A4`; H0 timeline rung stage=**Photoresist**; `chip-resist-history.png`). Pure additive **consumer**
of `chip/litho.py` — no engine change, no existing behaviour touched (same discipline as A1/A2/A3/B6). The
**second Tier-2** mode after H0. Order A1→A3→B6→H0→A2→**A4 ✅**→**B5 next** (B5 = LOCOS bird's beak, the
2-D engine's consumer — the last historical chunk). See [[historical-modes-a2]], [[historical-modes-a1]],
[[litho-car-v19]], [[litho-peb-v17]], [[gradual-failure-preferred]].

**The physics.** Three photoresist generations developed on the *same* aerial image: **negative** (Kodak
KTFR, ≈1960s — the period mode) crosslinks the **exposed** region into the line, then the network **absorbs
solvent developer and swells**, dilating the line → the space shrinks → adjacent lines **bridge** below a
pitch floor. **Positive** (DQN/novolak, the successor + the DEFAULT/seam) dissolves — no swell. **CAR**
(v1.9, already built) = the DUV successor, **delegated straight to `litho.expose_grating_car`** (shown, not
reimplemented).

**THE decisive build call (advisor Trap, load-bearing): swelling is GEOMETRIC, NOT an engine ride.** Unlike
A2 §B (where the `√(λg)` blur WAS the physics) and v1.7/v1.9 (the bake IS the engine's PDE), a diffusion
solve is **conservative & symmetric** but swelling **adds volume** (solvent uptake) and **dilates** the line
— non-conservative & asymmetric. The tempting ride — blur the developed line via `peb_blur`, then
re-threshold **below the midpoint** to make it grow — needs a **free contour level `c`** that silently
absorbs the calibration (`Δ = σ·√2·erfinv(1−2c)` — both σ and c free): a **fudge dressed as an engine ride**,
exactly the [[gradual-failure-preferred]] trap. **Discriminating test (advisor):** *delete the diffusion
solve and the CD floor is unchanged* → it was never the engine's, so don't present it as tight. So swelling
= a **fixed geometric edge displacement `s = swelling_factor·thickness`** (∝ **thickness**, NOT ∝ CD — that
independence is what makes the floor optics-independent), added `2·s` to the exposed-line width. "Reuse the
PEB/CAR machinery" (per the plan) is honestly the **develop/metric path** (`print_cd`/`image_contrast`/`nils`
+ the `*Feature` dataclass) **+ the CAR successor** (`expose_grating_car`), **not** a decorative solve. The
plan text originally implied a "swelling term" on the engine; the honest build made it geometric and said so.

**THE headline (orthogonal to A2 — the reason this mode earns its place):** the swelling floor `≈ film
thickness` is **OPTICS-INDEPENDENT**. A2 walked the Rayleigh floor `k₁λ/NA` DOWN with wavelength; A4 shows a
floor the wavelength race **cannot touch** — sharpen λ/NA all you like and a negative line still bridges near
the film thickness. Only *changing the resist* (positive/CAR) removes it. Tight leg made **structural**:
`swelling_resolution_floor(thickness, swelling_factor, duty)` takes **no `Imaging`** (a test asserts its
signature has no wavelength/NA), and `half_pitch_floor = s/(1−duty)` = **exactly one film thickness** at the
cited `factor=0.5` / `duty=0.5` (the KTFR "resolution ≈ thickness" rule). Demo **isolates the two floors**
(advisor requirement) by developing the same fine i-line-class image (365/0.45) as positive (resolves to the
~0.6 µm optical floor) and negative (bridges ≈1.7 µm ≈ 2× the 1 µm film), CAR resolving in the bridged band.

**Key implementation gotcha:** the **bright** (exposed, crosslinked) negative line **straddles the period
boundary** (centered at x=0/pitch), so `litho.print_cd(polarity="bright")` returns 0 — it needs the feature
*interior*. Fix: the bright line = **`pitch − dark_cd`** (the two threshold crossings partition the period,
so bright+dark=pitch), guarded to 0 when `dark_cd=0` (unresolved). The **positive seam** IS
`litho.print_cd(polarity="dark")` at the mean clip on the exact `expose_grating` grid → byte-identical
(a test asserts `cd/contrast/nils == expose_grating`).

**Triad — tight:** the positive seam (= `expose_grating` bit-for-bit), the swelling **sign** (`s≥0` only
grows the line → space shrinks monotonically → bridges), the CAR delegation (= `expose_grating_car`), and
the floor's `∝ thickness` / optics-independence (structural). **Flagged:** `SWELLING_FACTOR=0.5` +
`RESIST_THICKNESS_NM=1000` — magnitudes, not laws. **Named edges:** uniform lateral dilation (not a
differential-swell profile solve → no serpentine distortion, no aspect-ratio collapse); bridging read as a
per-feature cliff at `space=0` (a **graded** bridged-*fraction* via line-edge non-uniformity is the
[[gradual-failure-preferred]] move — **named, not built**, no distribution knob); the optical develop stays
litho's constant-threshold resist. Fast lane green (+11 A4 tests). Committed direct to `main`
(`b013eff`), pushed to origin ([[commit-at-end-of-batch]]).
