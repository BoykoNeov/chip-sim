---
name: litho-peb-v17
description: "Microchip v1.7 PEB acid-diffusion blur BUILT 2026-06-11 (litho.py §8, 17-test mini-triad, fast lane 218): the finding INVERTS litho's founding line — the bake IS the engine's PDE, so the one engine-free module now runs its resist back-end on engines.diffusion in acid mode (pure consumer, no amendment); half-period symmetry cell = exact periodic blur; bake conserves dose → power balance survives; the PEB window closes at dense pitch (lens out-resolves the bake → BARC)"
metadata:
  node_type: memory
  type: project
  originSessionId: 19949d4e-99a6-4fd8-b8e7-b084226469ea
---

Microchip **v1.7 — PEB acid-diffusion blur** — BUILT 2026-06-11. Phase 3's §-named scope edge
(**"constant-threshold resist — no acid diffusion / PEB blur"**) **promoted**, the candidate
[[litho-defocus-v14]] flagged as next. `chip/litho.py` §8 + `demo_peb.py` + `plots.peb_figure`;
12 module + 5 demo tests (`test_peb.py`/`test_demo_peb.py`); fast lane **201→218**. Banked artifact
`docs/figures/chip-peb.png` (the latent image dissolving over the cited 20/40/60 nm series | the
PEB window: engine retention points riding the two analytic heat kernels). **Versioning:** user
requested "Litho v1.5" (litho's next after v1.4); repo-global counter made it **v1.7** (v1.5 =
native `D(u)`, v1.6 = explicit stepping — both engine amendments). **Advisor disabled this
session** (`/advisor` → "Advisor disabled") — design calls below are self-steered.

**The decisive finding (the v1.x thesis, inverted):** v1.2–v1.4 found promotions fit *within*
existing machinery; v1.7's is that litho — the chip's one module whose founding line was "does
not touch the engine" — has a resist back-end that **IS the engine's PDE**: the bake is Fick's law
on the latent acid (cited: σ=√(2Dt), Gaussian-kernel solution, sealed-film homogeneous-Neumann BC —
[[peb-acid-diffusion-source]]). So `peb_blur` runs `engines.diffusion` in **acid mode** (`u` =
latent acid, constant `D = σ²/2`, unit bake, `Neumann(0)` both faces, **Crank–Nicolson** default;
ENGINE UNTOUCHED, pure consumer, no ADR). **CN-default rationale sharpened (2026-06-11 review):**
CN has NO unconditional discrete max-principle, so the load-bearing reason it's safe here is
**band-limiting by the optics** (the latent image is a handful of harmonics far below CN's
oscillation scale → nothing to ring on; the bounds test confirms), NOT "temporal accuracy" per se.
With negativity ruled out, the only axis left is fidelity to the calibrated σ — CN (2nd-order)
matches the exact per-harmonic kernel to the FV floor, so it WINS; `backward_euler` is offered for
a guaranteed max-principle on a non-band-limited input but is a **~6× less accurate** kernel match
at equal n_steps (measured: CN err 1.3e-5 vs BE 7.9e-5 on the fundamental) → kept CN default, did
NOT flip to BE (advisor concurred: BE "extra dissipation benign for a blur" is true for the killed
high modes but BE biases the *retained* σ, and the blur is calibrated to a physical σ).

**The load-bearing construction — the half-period symmetry cell.** A symmetric grating under a
symmetric source gives an *even* periodic image; its mirror planes x=0, p/2 become the **no-flux
faces** and its cosine harmonics are exactly the domain's **Neumann eigenmodes** — so the bounded
engine solve **IS the infinite periodic blur** (no approximation). Two consequences threaded into
`expose_grating(..., peb_diffusion_length_nm=σ)`: (1) the no-flux faces must be cell FACES, so the
PEB path samples the period at **half-offset cell centers** `(j+½)p/n_x` (still uniform → means and
Fourier projections stay exact; σ→0 lands on the v1 metrics within sampling resolution, σ=0 default
IS the v1 path **bit-for-bit**); (2) an **asymmetric image is REFUSED** (off-axis pole + defocus =
the v1.4 fringe shift, no mirror plane) — the Massoud refuse-outside-the-fit discipline. Every
PrintedFeature metric then reads the **post-bake latent image** (the diffused-image resist model);
`PrintedFeature` gained `peb_diffusion_length_nm` (additive default 0.0).

**The mini-triad.** *Analytic (tight):* σ=0 bit-for-bit seam + σ→0 continuity (no jump hidden
behind the short-circuit); a bare Neumann eigenmode decays by its exact eigenvalue exponential; a
realistic Abbe image attenuates **per harmonic** by the periodic heat kernel `exp(−2π²k²σ²/p²)` —
engine vs closed form at the documented discretization floor (FV eigenvalue gap `(kΔx)²/12` + CN
time error; measured ~2e-6 on the fundamental); max-principle bounds (no ringing/negative acid).
*Conservation (tight):* no-flux ⇒ the bake conserves acid dose ⇒ the image mean — and the v1
Parseval power balance `mean = Σ|c_m|² = transmitted_power` — survives EVERY σ (~6e-14); corollary:
the default mean-clip dose is **blur-invariant** (baked and unbaked develop at the same dose).
*Benchmark (loose):* contrast/NILS monotone down the cited 20/40/60 series (NILS falls through the
cited ≥1 floor by 60 nm); **CD collapses onto the pure-fundamental p/2 readout** (blur kills
harmonics as k²; the residual gap tracks the k=2 kernel — 1.2 nm at σ=40, 0.15 at 60).

**The PEB window (the demo story).** One bake, two jobs: erase the standing-wave depth ripple
(period λ/2n — same `peb_blur` along z, where no-flux is the literal sealed-film BC) yet keep the
lateral fundamental (period p). Cited floor σ ≥ λ/4n (≈28.4 nm at 193/n1.7; erases 99.3% of the
ripple) + illustrative keep-half ceiling (45 nm at p=240) → window **[28, 45] nm**, closing at
**`p_close = λ/(4nc)` ≈ 151 nm**. **The coincidence SHARPENED (2026-06-11 review):** the original
"~151 ≈ this system's optical cutoff, a coincidence not a law" undersold it. `p_close = λ/(4nc)` is
**NA-INDEPENDENT** (resist index + keep-floor only); this system's **partial-coherence** optical
cutoff is **`λ/(NA(1+σ))` = 151.37 nm** (NOT the two-beam floor λ/2NA=113.5 — the demo runs a
conventional σ=0.5 source; the triple-match 151.37 ≈ computed p_close 151.46 ≈ the hardcoded "~151"
AND README's own "image goes flat below ~151 nm" all confirm the partial-coherence cutoff is what
was meant). The two pitches **both scale as λ**, so their ratio **`NA(1+σ)/(4nc)` is λ-INDEPENDENT**
— at NA 0.85/σ0.5 it is **1.0006** (closure ≈ cutoff to 0.06%, `NA(1+σ)=1.275` vs `4nc=1.274`): a
**λ-independent coincidence of two INDEPENDENT parameter groups** (lens+source vs resist+keep-floor,
no law forcing them equal), now **with an NA-mechanism** — not the advisor's "mechanism INSTEAD of
coincidence" (over-claim; rejected) and NOT the advisor's factor `NA/(2nc)`=1.33 (that's the
two-beam cutoff, wrong for the σ=0.5 demo). The non-tautological closure: push to **NA 0.93** (max
dry ArF) and the cutoff slides to **~138 nm** while `p_close` stays **pinned** at 151 — a 138–151 nm
band where a **145 nm pitch images fine but cannot survive a rule-abiding bake** (keep 0.47) — the
**lens out-resolves the bake**; the resist blur, not the optics, sets the dense-pitch floor → why
modern stacks use a **BARC** (the cited ARC/dye/PEB mitigation list). (Crossover NA = `4nc/(1+σ)` ≈
0.8495 for THIS n/σ/keep-floor — not a universal constant; the chosen lens sits right on it.) Found
the hard way originally: a first closure test at p=150/NA0.85 hit a *flat aerial image* (= that same
151 nm cutoff) — at NA 0.85 there is no optically-alive-but-PEB-dead pitch at the keep-half floor.
Demo now **computes** `p_cutoff`/`p_cutoff_hi`/`closure_ratio` (was a hardcoded "~151").

**Scope edges named-not-modelled:** linear exposure (latent acid ∝ I — no Dill bleaching), constant
D (the CAR reaction–diffusion system with concentration-dependent `D_h` = the cited next rung),
development still a constant threshold, lateral x-blur and depth z-smoothing **uncoupled** (no 2-D
(x,z) resist volume — the engine's own last deferred regime, a named future tie-in). Units stay
litho-native nm (σ, D·t in nm²); notebook gains no section (as v1.1–v1.4). README load-pointer +
status entries added; stale fast-lane counts (188) refreshed to 218 across README/pyproject.
