---
name: litho-defocus-v14
description: "Microchip v1.4 lithographic defocus / depth of focus / Bossung BUILT 2026-06-10 (litho.py §7, 16-test mini-triad, chip 161): defocus = a pure pupil PHASE → fits inside the litho module, no new path; the advisor's load-bearing fix = assert the fundamental 4c₀c₁cosφ not the contrast (frequency doubling at the null); conservation = defocus is unitary; k₂=0.5 derived-but-paraxial"
metadata: 
  node_type: memory
  type: project
  originSessionId: f544de15-3c68-41c4-8380-e27d823888bd
---

Microchip **v1.4 — lithographic defocus, the depth of focus & the Bossung curve** — BUILT
2026-06-10. Phase 3's §3-named scope edge (**"ideal in-focus aberration-free pupil"**) **promoted**
(the steel-ferrite-bay / Massoud / [[chip-coupling-v12]] / [[chip-highconc-v13]] move). `chip/litho.py`
§7 + `demo_defocus.py` + `plots.defocus_figure`; 11 module + 5 demo tests; chip fast lane **161** (+16,
145→161). Banked artifact `docs/figures/chip-defocus.png` (Bossung CD-vs-defocus dose family + process
window + DOF marker | the through-focus fundamental riding the exact envelope, nulling then reversing).

**The decisive finding (same v1.x thesis):** defocus is a pure **phase** aberration on the pupil, and
`coherent_image` already sums *complex* amplitudes — so it fits **inside the litho module with no new
code path** (cf. v1.2/v1.3 fitting inside the *frozen engine*). `defocus_phase(f_total, img, z) =
exp(i·(2π/λ)·z·(1−cosθ))`, `cosθ = √(1−(f_total·λ)²)`, keyed to the order's **full pupil coordinate**
`f_m+f_s` (its true propagation angle); threaded through `abbe_image`/`expose_grating` as
`defocus_nm=0.0`. `z=0` short-circuits to the float `1.0` → in-focus path is v1 **bit-for-bit** (the
degenerate seam; all 25 prior litho + device tests untouched).

**The mini-triad.** *Analytic (tight):* (a) z=0 seam bit-for-bit; (b) **symmetric-dipole infinite DOF**
— two equal beams at ±f_cut share an identical pupil radius → identical defocus phase that factors out
of `|Σ|²` → image unchanged at *every* z to machine precision (the asymmetric 0&+1 two-beam instead
**rotates** its fundamental as `2cosφ` = a fringe shift, contrast preserved); (c) the on-axis
**three-beam fundamental = `4·c₀·c₁·cosφ` to machine precision**, via `fundamental_amplitude` (the
`⟨I,cos(2πx/p)⟩` projector). *Conservation (tight):* **defocus is unitary** — phase-only ⇒ `|c_m|²`
untouched ⇒ `mean(image)=Σ|c_m|²=transmitted_power` at every z to machine precision (a real check the
build added *phase* not amplitude — `transmitted_power` never sees the phase). *Benchmark (loose):*
Bossung CD/NILS degradation + `DOF=k₂λ/NA²`, `k₂=0.5` **derived** from the φ=π/2 null.

**Durable advisor calls (the steering this build turned on):**
1. **Gating:** defocus was the right promotion — clean exact anchors, the conservation leg extends for
   free. Build it (don't relitigate).
2. **THE load-bearing fix — assert the fundamental, NOT the contrast.** "Three-beam contrast ∝ |cosφ|"
   is *false* under `(I_max−I_min)/(I_max+I_min)`: the image is `c₀² + 4c₁²cos²ψ + 4c₀c₁cosφ·cosψ`,
   whose `4c₁²cos²ψ` is a **defocus-independent 2nd harmonic** → the *fundamental* coefficient is the
   machine-precision `4c₀c₁cosφ`, but the contrast does **not** vanish at the φ=π/2 null — the image
   **frequency-doubles / contrast-reverses** there (Mack). Pinned as a *positive* test
   (`test_dof_null_is_frequency_doubling_not_a_blank_image`). This was the exact "exact-in-my-head,
   red-in-pytest" trap the advisor caught before any test was written.
3. Symmetric dipole = **bit-for-bit** (not just contrast-invariant); asymmetric two-beam = the
   lateral-shift case — two distinct exact tests.
4. Keep the analytic-leg φ **identical** to the code's (**full** cosθ, not paraxial `−½πzλ/p²`); then
   the φ=π/2 null → `z=λ/2NA²` → `k₂=0.5` falls out — but that is **paraxial**, so the exact full-cosθ
   null sits ~24% inside the paraxial DOF at NA 0.85 (±119 vs ±134 nm) and **converges** onto it as
   NA→0 (pinned NA 0.85→0.15: ratio 0.76→0.99). Demo pitch = **240 nm** (the resolution limit, where
   DOF is defined) so the null and the DOF marker share a focus scale; a coarser pitch tolerates more
   defocus (DOF is the densest-feature worst case).

**Scope edges named-not-modelled:** Zernike aberrations (coma/astigmatism/spherical — only *defocus*
is added); immersion NA≥1 (the scalar model's evanescent edge / the named vector tar pit); the
constant-threshold resist — **no acid-diffusion/PEB blur**, flagged as the *next* litho promotion
candidate (the "PEB blur = a Gaussian = a diffusion solve → potential **frozen-engine reuse**" angle).
The docstring's old "no defocus phase, no Zernikes" scope line was amended to "aberration-free apart
from defocus." Units stay litho-native **nm**; notebook gains no section (as v1.1/v1.2/v1.3). Source
pin (DOF / k₂ / Bossung / frequency doubling) appended to [[litho-aerial-image-source]] (Mack).
