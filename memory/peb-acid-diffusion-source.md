---
name: peb-acid-diffusion-source
description: "Microchip v1.7: cited PEB model — σ=√(2Dt) Gaussian latent-image blur with sealed-film Neumann BC (Kirchauer §7.1.2 / Mack 1995), the standing-wave period λ/2n (Mack Tutor eq. 12), the half-period smoothing rule (Mack glossary), the 20/40/60 nm series + 100–130 °C (lithobasics), the ARC/dye/PEB mitigation list; CAR reaction–diffusion (conc-dependent D_h, APEX-E params) = the named scope edge"
metadata:
  node_type: memory
  type: reference
  originSessionId: 19949d4e-99a6-4fd8-b8e7-b084226469ea
---

Microchip **v1.7 (PEB acid-diffusion blur)** benchmark constants and model facts, pinned at build
(2026-06-11) — the `[[…-source]]` discipline (cited from the live pages/PDFs this session, not from
memory). All four pins are from the **same two corpora the project already cites** (Mack/lithoguru;
the IUE-Vienna theses) — a coherent-set bonus, like Massoud-on-Hollauer.

**The PEB diffusion model** (what `litho.peb_blur` instantiates) — **Kirchauer, IUE-Vienna diss.
§7.1.2** (iue.tuwien.ac.at/phd/kirchauer/node109.html; the *same* thesis family already pinned for
the NILS≥1 floor in [[litho-aerial-image-source]]):
- Conventional resist: PEB reduces "the vertically non-uniform exposure pattern … that leads to
  standing waves" by **Fickean diffusion** of the PAC: `∂m/∂t = D_peb·∇²m`.
- **`σ_peb = √(2·D_peb·t_peb)`** — the diffusion-length definition (the one knob).
- Solution = "a **convolution** of the PAC concentration right after exposure **with the Gaussian**
  distribution function" (→ our per-harmonic heat kernel `exp(−2π²k²σ²/p²)` on a period).
- BC: "**homogeneous Neumann** conditions (no out-diffusion across resist surface)" — the
  sealed-film `Neumann(0)` is **cited, not invented**. Typical ~100 °C, ~10 min (oven).
- **CAR = the named scope edge in v1.7 — now BUILT in v1.9** ([[litho-car-v19]]): coupled
  reaction–diffusion — deprotection rate ∝ acid^n, **concentration-dependent `D_h`**, acid loss,
  surface evaporation BC; IBM APEX-E @ 90 °C: `k₁=2.0 s⁻¹`, `k₂=0.0033 s⁻¹`, `n=1.8`,
  `D_h,0=0.0933 nm²/s`. v1.7 was the **linear-exposure, constant-D** teaching reduction. **Verbatim
  from the live Kirchauer node (fetched 2026-06-12 for v1.9):** `∂m/∂t = −k_peb,1·m·hⁿ` (the `n` sits
  on **`hⁿ·m`**, NOT `(h·m)ⁿ`) and `∂h/∂t = −k_peb,2·h + div(D_h·grad h)` — **acid loss is FIRST-ORDER
  `−k₂·h`, with NO `h·m` sink** (acid is a pure **catalyst** → `∫h` conserved/exact-decay, the load-
  bearing conservation fact for v1.9); `D_h = D_h0 + D_h1·(1−m)` [linear] or `D_h0·exp(−w(1−m))`
  [exponential free-volume]; surface-evap BC `∂h/∂t = −k_evap(h−h_air)`; IC `m=1`, `h=h_exp`. (Only
  `D_h0` is a cited value → v1.9 defaults constant `D`; `D_h1` left illustrative.) The Ferguson/Zuniga
  3-field variant — acid `+` base **quencher** `B`, loss `∝klHB`, `∂B/∂t=klHB` — is a DIFFERENT (more
  complex) model NOT used; v1.9 uses the simpler cited 2-field Kirchauer form.

**Acid diffusion in CAR + the small-vs-feature rule** — **Mack, "Lithographic Effects of Acid
Diffusion in Chemically Amplified Resists" (1995)** (lithoguru.com litho_papers #48): σ=√(2Dt),
Gaussian acid spread, latent-image blur degrades CD control; diffusion length must stay **small
relative to the feature size** (the keep-the-image ceiling of the v1.7 window).

**The smoothing rule (the window's floor)** — **Mack's glossary, "Diffusion Length"**
(lithoguru.com/scientist/glossary/D.html): "The diffusion length of photoactive compound during PEB
**must be larger than the standing wave half period** to be effective at removing standing waves"
→ **σ ≥ λ/4n**. At σ = λ/4n the period-λ/2n ripple retains `exp(−π²/2) ≈ 0.7%` — the rule erases.

**PEB practicalities** — **Mack, lithobasics** (lithoguru.com/scientist/lithobasics.html): PEB
purpose = smooth the standing-wave ridges; **100–130 °C**; the profile-simulation series
**20/40/60 nm** (→ `litho.PEB_DIFFUSION_SERIES_NM`, the demo sweep + loose band); for CAR the PEB
*drives the deprotection* ("control of the PEB is extremely critical").

**Standing waves** — **Mack, *Lithography Tutor* Spring 1994 "Standing Waves in Photoresist"**
(TUTOR06; analytic backbone in Mack, *Applied Optics* 25:1958, 1986): intensity
`I(z) ≈ (e^{−αz} + |ρ₂₃|²e^{−α(2D−z)}) − 2|ρ₂₃|e^{−αD}·cos(4πn₂(D−z)/λ)` (eq. 11) →
**`Period = λ/2n₂`** (eq. 12) — `litho.standing_wave_period`. Mitigation list: **reduce substrate
reflectivity (ARC/BARC), dye the resist (raise α)** — plus PEB; the cited list behind the demo's
"the window closes at dense pitch → use a BARC" punchline. Resist index **n = 1.70 is
representative only** (illustrative; only λ/2n is load-bearing — flagged in code/tests).

**How litho.py §8 uses it** (the validated-vs-calibrated split): the per-harmonic **heat kernel
`exp(−2π²k²σ²/p²)` is DERIVED** (the engine solve vs the closed form — the tight anchor, ~2e-6
floor), and the half-period-cell construction (no-flux faces = the even image's mirror planes,
Neumann eigenmodes = the cosine harmonics) is *proved by that anchor*, not assumed; the **cited
calibrations** are σ=√(2Dt) (a definition), the sealed-film BC, the 20/40/60 nm series, and the
λ/4n smoothing rule (loose benchmark legs). Non-circular: the engine never sees the kernel.

Used by [[litho-peb-v17]] (the v1.7 linear blur) and [[litho-car-v19]] (the v1.9 CAR reaction–diffusion
— the scope edge, now built). Companions: [[litho-aerial-image-source]] (P3/v1.4 — same Mack corpus,
same Kirchauer thesis family), [[massoud-thin-oxide-source]] (the coherent-set precedent).
