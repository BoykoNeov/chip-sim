---
name: lateral-diffusion-source
description: "Microchip v1.8: cited lateral-diffusion-under-a-mask-edge model — the constant-source 2-D mask-window config, the lateral/vertical junction ratio ≈ 0.75–0.85 (contour-dependent, RISING toward deeper/lower-C_B/N_s contours), anchored on the worked point ≈0.82 at C_B/N_s=1e-4 (vert 2.8 / horiz 2.3 in 2√Dt units), after Kennedy–O'Brien 1965 — but read via a SECONDARY fab text, not K-O directly. The model runs ~5–10% high vs that one point → a LOOSE benchmark; Gaussian (limited-source) ratio is lower (~0.65–0.70)."
metadata:
  node_type: memory
  type: reference
  originSessionId: 8d11ce4f-d9fa-4270-9767-146279ab9c6c
---

Microchip **v1.8 (lateral diffusion under a mask edge — the 2-D regime)** benchmark/model facts,
pinned at build (2026-06-12) under the `[[…-source]]` discipline (cited from live pages this session,
NOT carried from memory — the previous `RATIO_BAND=(0.75,0.85)` in code was a memory-carried value
with no citation; this note is what replaced it).

**The canonical reference — Kennedy & O'Brien (1965)**, "Analysis of the Impurity Atom Distribution
Near the Diffusion Mask for a Planar p-n Junction," *IBM J. Res. Dev.* **9(3):179–186**
(ieeexplore.ieee.org/document/5392117). The original **numerical reflecting-mask** 2-D solution
(constant surface concentration in the window; **no-flux / reflecting under the mask** — the *same*
BC as our `MaskedSurface`). Its load-bearing findings:
- A **1-D approximation is inadequate** near a planar junction — the junction is **not** at a constant
  distance from its source: it sits **closer to the source at the surface than deep in the bulk**.
  This *is* the contour-dependence — the lateral/vertical ratio **rises toward deeper (lower-`C_B/N_s`)
  contours**, the textbook nuance the single "≈0.8" rule hides.
- Two diffusion regimes solved: **constant surface concentration** (= our erfc predep / Dirichlet
  window) and **fixed dose** (Gaussian / limited-source drive-in). Our v1.8 demo is the **constant-
  source** case.

**The worked numbers — read via a SECONDARY fabrication text, not K-O directly** (honesty flag):
ebrary.net/184567/engineering/lateral_diffusion (a fab textbook page, the K-O contour replotted):
- General rule-of-thumb quoted there: **"lateral/vertical diffusion is between 65–70%."**
- Worked constant-source example: at **`N/Ns = 1e-4`, vertical ≈ 2.8, horizontal ≈ 2.3 → ≈ 0.82**
  (the units are **2√(Dt)**: `erfcinv(1e-4)=2.751 ≈ 2.8`).
- **Do NOT encode a clean "constant-source 0.75–0.85 vs Gaussian 0.65–0.70" split as cited** — that
  is *my inference*. The page muddily gave the general "65–70%" *and* the contradictory 82% example;
  the only firmly-cited point is **≈0.82 at `N/Ns=1e-4`**, constant-source. (The lower ~0.65–0.70 is
  commonly the Gaussian/limited-source figure, but that attribution is not nailed in a source here.)

**How chip `diffusion_2d` / `demo_lateral_diffusion` use it (the validated-vs-loose split):**
- **TIGHT anchor (carries the validation weight) = the seam, not the ratio:** the window-centre column
  (far from the edge, locally 1-D) equals the analytic constant-source junction
  **`erfcinv(C_B/N_s)·2√(Dt)`** to numerical precision (`rtol 1.5e-2`). That ties the 2-D solve to the
  blessed 1-D engine; combined with the engine's machine-precision **dimensional-collapse seam**, the
  vertical physics is anchored hard.
- **LOOSE benchmark = the ratio:** the model reproduces the **regime** and the **contour-dependence**,
  with shallow contours in the 0.75–0.85 band, but at the one cited point it runs **~5–10 % high**
  (model **0.87** vs cited **0.82** at `C_B/N_s=1e-4`); finer grids nudge it *up*, not toward 0.82.
  So the device deep-contour **~0.90 is the model's own value within the read-off uncertainty of a
  1965 graph — NOT a sourced number**, and **NOT** "more accurate" than K-O (same reflecting BC;
  higher ≠ better — likely read-off / finite-window-vs-semi-infinite definition difference). Asserted
  as **intervals**, never equalities.
- **Domain-converged** (not a numerical wall artifact): a 2× domain (8×5 µm vs 4×2.5 µm) is
  bit-identical — the field is ~0 well before the reflecting far wall.
- **Surface-lateral ≡ max-over-depth** for this constant-source geometry (the maximum lateral
  encroachment is *at* the surface — no deeper bulge), so the "where to measure lateral" ambiguity is
  moot here.

Used by [[lateral-diffusion-2d]]. Companions: [[dopant-diffusivity-source]] (the Fair `D(T)` and the
erfc constant-source form this demo's vertical anchor reuses), [[dopant-solid-solubility-source]]
(the Trumbore `N_s` window value).
