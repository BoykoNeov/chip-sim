---
name: litho-tool-proximity-source
description: "A2: cited proximity-printing √(λg) resolution limit (Levinson/Madou) + the g-line→EUV wavelength/NA node ladder as representative (flagged) values"
metadata:
  node_type: memory
  type: reference
  originSessionId: 01c80eec-bd70-49fc-94b0-b48db9d07937
---

Sources behind **historical-modes A2** ([[historical-modes-a2]], `chip/litho_history.py`):

**§B proximity/contact printing — the `√(λg)` gap wall.** Shadow (contact/proximity) printing: the smallest
printable half-pitch scales as **`b_min ≈ √(λ·g)`** (sometimes `√(λ(g+t/2))` including resist thickness `t`),
the near-field Fresnel diffraction limit over the mask-to-wafer gap `g`. Cited: Levinson, *Principles of
Lithography* §1 (proximity resolution); Madou, *Fundamentals of Microfabrication*. In-code it becomes a
Gaussian blur length `σ = k·√(λg)`, prefactor `k≈1` **FLAGGED** (well-founded, not asserted: the grating
fundamental `exp(−2π²σ²/p²)` dies right when σ≈half-pitch, i.e. `g ≈ (p/2)²/λ`). NOT modelled: the Talbot
self-imaging oscillation of the *periodic* near-field (we take the monotone blur envelope). Consequence
verified in build: `√(λg)` resolves **microns** (an 8 µm feature at 436 nm walls out ≈37 µm gap), not
sub-micron — why proximity aligners were coarse and projection replaced them.

**§A the wavelength/lens ladder — REPRESENTATIVE (flagged) node table.** g-line 436 / i-line 365 / KrF 248 /
ArF 193 / ArF-immersion 193 / EUV 13.5 nm are the real exposure lines; the per-node **NA** values
(0.28/0.45/0.60/0.85/1.35/0.33) are *representative* historical numbers (real tools spanned a range) — the
tight leg is the `R=k₁λ/NA` formula-monotonicity, NOT the table (the table only supports the *flagged*
"ladder λ/NA falls g→EUV" claim). ArF `(193, 0.85, σ0.5)` is pinned to match `chip/demo_litho.py`'s stepper
exactly (the bit-for-bit seam). k₁/NILS printability rule stays cited in [[litho-aerial-image-source]] (Mack).
Scalar-diffraction caveat: immersion (NA>1, vector/polarised) and EUV (reflective, vacuum, its own resist)
are only their λ/NA *point* on the scalar curve.
