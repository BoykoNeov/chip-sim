---
name: lateral-diffusion-2d
description: "Microchip v1.8 (2026-06-12): the 2-D regime BUILT — engines.diffusion gained a NEW module diffusion2d.py (Diffusion2D, Grid2D, MaskedSurface), the THIRD exercise of the unfreeze and the engine's LAST deferred regime, finally pulled in by its named consumer (chip diffusion_2d: lateral dopant diffusion under a mask edge). Backward-Euler-only tensor-product FV; additive (34 prior engine invariants UNMODIFIED). Tight anchor = the dimensional-collapse seam (NOT the outer-product theorem, which discrete BE breaks at O(dt²)); the lateral/vertical ratio is a LOOSE benchmark. 3-D is now the only deferred regime."
metadata:
  node_type: memory
  type: project
  originSessionId: 8d11ce4f-d9fa-4270-9767-146279ab9c6c
---

**Microchip v1.8 (lateral diffusion under a mask edge — the 2-D regime): BUILT 2026-06-12.** Both the
**third engine amendment** ([[engine-unfrozen]]) **and** a chip phase in one — unlike the pure-engine
v1.5/v1.6, this is the regime v1.6's advisor told us to *wait* for ("2-D waits for a real consumer =
lateral diffusion under a mask edge, the cited lateral/vertical ≈ 0.8 rule"). That consumer arrived.

**Engine** — a *new module* `engines/diffusion/diffusion2d.py` (NOT an edit to `diffusion1d.py`):
- `Diffusion2D` on a tensor-product `Grid2D` (x-grid ⊗ y-grid → non-uniform grids inherited per
  direction), `uniform_grid_2d`, a sparse **5-point cell-centered FV** operator, **backward-Euler
  only**, `scipy.sparse.linalg.splu` cached per `dt` (A time-independent), harmonic-mean faces.
- `(I − dt·A)` is an **M-matrix** → the 1-D engine's headline guarantees (unconditional stability,
  monotonicity / discrete max principle, structural conservation of `Σ uᵢⱼΔxᵢΔyⱼ`) carry over verbatim.
- New BC `MaskedSurface(value, open_mask)` — per-cell **Dirichlet under the window / no-flux under the
  mask**; the one genuinely-2-D addition. `state` is a plain `(nx, ny)` ndarray (flat `k=i·ny+j`),
  same ADR-0001 data boundary.
- **Additive by construction:** imports the 1-D primitives but executes **no 1-D code path**, so the
  **34 prior engine invariants pass UNMODIFIED**. New seal `tests/test_diffusion2d.py` (**11 tests**,
  CONTRACT invariant 7). Engine suite **34→45**; whole-repo fast lane **218→238**. **No new ADR**
  (ADR 0004 names 2-D as a pre-authorized regime).

**Chip consumer** — `chip/diffusion_2d.py` (`lateral_diffusion`, `junction_geometry`,
`MaskEdgeProfile`/`JunctionGeometry`) + demo `chip/demo_lateral_diffusion.py` +
`plots.lateral_diffusion_figure` → `docs/figures/chip-lateral-diffusion.png`. Boron constant source
(Trumbore `N_s`, 1100 °C / 60 min) through a 2 µm-edge mask window; the pn junction is a 2-D contour
curving up under the mask. Mini-triad `tests/test_diffusion_2d.py` (5) + `test_demo_lateral_diffusion.py`
(4). Device junction ≈ 0.85 µm vertical, ratio ≈ 0.90.

**The three load-bearing findings (advisor-traced):**
1. **The problem is only genuinely 2-D because of the piecewise `MaskedSurface` BC.** A sealed drive-in
   from a windowed initial condition with all four edges no-flux is **separable** = the outer product
   of two 1-D runs → would NOT need a 2-D engine (hollow). The constant-source window step beside the
   no-flux mask is the non-separability; the lateral-under-mask curvature is its signature.
2. **The tight anchor is the DIMENSIONAL-COLLAPSE seam, NOT the outer-product theorem.** The textbook
   "2-D = outer product of two 1-D runs" is *continuous-only*; the discrete backward-Euler 2-D operator
   is a Kronecker **sum** in the exponent, so `(I−dt(Lx⊕Ly))⁻¹ ≠ (I−dtLx)⁻¹⊗(I−dtLy)⁻¹` (differ at
   O(dt²)). So the machine-precision seam is: a 2-D run uniform + no-flux in one direction reproduces
   the blessed 1-D engine in the other (`<1e-12`). The outer-product is demoted to an O(dt)
   *convergence* check (splitting error halves with dt). Plus: chip-side, the window-centre column ==
   the analytic 1-D `erfc` junction `erfcinv(C_B/N_s)·2√(Dt)`.
3. **The lateral/vertical ratio is a LOOSE benchmark — own the gap, don't dress it up** ([[lateral-
   diffusion-source]]). Domain-converged (2× domain bit-identical → NOT a wall artifact). At the one
   cited point (≈0.82 at `C_B/N_s=1e-4`, after Kennedy–O'Brien 1965, via a secondary text) the model
   runs **~5–10 % high** (0.87); grid refinement nudges it *up*. So shallow contours sit in the cited
   0.75–0.85 band, the ratio **rises toward deeper contours** (K-O's own finding), and the device
   ~0.90 is the **model's own deep-contour value within the read-off uncertainty of a 1965 graph —
   not sourced, and not "more accurate" than K-O** (same reflecting BC). Validation weight = the tight
   erfc anchor, not hitting 0.8. Also: surface-lateral ≡ max-over-depth here (max encroachment is at
   the surface).

**Docs:** CONTRACT.md amended (title "1-D + 2-D", status-banner third-amendment line, invariant 7, the
2-D API subsection, "2-D built" / "Not built: **3-D**"); engine + chip READMEs + plan §10 v1.8 record
+ `engines/__init__` docstring. **3-D is now the engine's only remaining deferred regime.** Deferred
2-D extensions named-not-built (no consumer): CN / explicit / nonlinear-`D(u)` / anisotropic-tensor
`D`. Committed direct to `main` (solo repo), pushed to origin ([[commit-at-end-of-batch]]).
