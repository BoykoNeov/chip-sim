---
name: litho-car-v19
description: "Microchip v1.9 (2026-06-12): CAR reaction-diffusion PEB BUILT (litho.py §9, 16-test mini-triad, fast lane 238→254) — the §8-named CAR scope edge of v1.7, promoted. INVERTS v1.7's finding: where the linear blur WAS the engine's pure PDE, the realistic chemically-amplified bake is a coupled TWO-FIELD (acid h + blocked m) reaction-diffusion system that does NOT fit the single-field engine, so it's built CONSUMER-SIDE by operator splitting (engine = acid-diffusion sub-step only; reaction integrated in closed form). No engine amendment/ADR. Diffusion sub-step is BE not v1.7's CN (h^n NaN trap + exact-conservation). Acid is a pure catalyst → ∫h exact. Amplification sharpens (loose, regime)."
metadata:
  node_type: memory
  type: project
  originSessionId: car-v19-build
---

**Microchip v1.9 — CAR (chemically-amplified resist) reaction–diffusion PEB — BUILT 2026-06-12.**
The **§8-named scope edge of v1.7** ("constant `D` — the CAR reaction–diffusion system is the cited
next rung"), **promoted**. `chip/litho.py` §9 + `demo_car.py` + `plots.car_figure`; 11 module + 5 demo
tests (`test_car.py`/`test_demo_car.py`); fast lane **238→254**. Banked artifact
`docs/figures/chip-car.png` (the latent image developing — the deprotection edge sharpening above the
acid | the PEB process window: CD vs bake time + the exact acid-loss decay). User said "do CAR
reaction-diffusion PEB" → repo-global counter made it **v1.9** (v1.8 = the 2-D regime). Advisor
**enabled** this session (unlike v1.7) — design calls below are advisor-traced.

**The decisive finding (the v1.x thesis, inverted AGAIN).** v1.7 inverted litho's founding line (the
bake IS `engines.diffusion` — the one engine-free module now rides it). v1.9 inverts **v1.7's** own
finding: the linear blur was the engine's *pure single-field PDE*, but the **realistic** chemically-
amplified bake is a **coupled two-field reaction–diffusion** system that does **NOT** fit the single-
field engine natively — so it returns to the **v1.2 consumer-side pattern** (operator splitting, engine
carries one sub-step, no engine amendment/ADR). The cited model (Kirchauer §7.1.2, the **same thesis**
as v1.7 — [[peb-acid-diffusion-source]]), on the blocked-site fraction `m` (1→0) and acid `h`:
`∂m/∂t = −k_amp·m·hⁿ` (deprotection) and `∂h/∂t = −k_loss·h + ∂ₓ(D_h(m)∂ₓh)` (acid: 1st-order loss +
Fickian diffusion). Built: `CARBake` (cited **APEX-E @ 90 °C**: `k_amp=2.0/s`, `k_loss=0.0033/s`,
`n=1.8`, `D_h,0=0.0933 nm²/s`) → `car_peb` (the bake, returns `(deprotection=1−m, acid)`) →
`expose_grating_car` (develop on the **deprotection** `1−m` — the chemically-faithful resist, where
v1.7 clipped the acid image). `_car_react` does the local reaction.

**The four load-bearing advisor findings:**
1. **Operator splitting is FORCED, not just convenient.** None of CAR fits the single-field engine: the
   `−k_loss·h` loss is ∝`u` (the engine's `source` is *additive* `S(x,t)`, can't express a decay sink);
   `m` is a second field; `D_h` depends on `m` not `h`. So the engine carries **only** the acid-
   diffusion sub-step (`Neumann(0)` sealed faces on the same v1.7 half-period cell; `D_h(m)=D_h0+D_h1(1−m)`
   **array-`D`** frozen per step from the lagged deprotection — NOT `StateDependent`, since D depends on
   `m` not the diffusing field `h`), reaction done consumer-side. Strang split (½-react · diffuse · ½-react).
2. **The diffusion sub-step is BACKWARD EULER — NOT v1.7's celebrated CN** (a deliberate departure from
   the [[litho-peb-v17]] CN-default). `hⁿ` with **non-integer n=1.8 is a NaN trap** on any negative ring,
   and CN has no max-principle. BE's discrete maximum principle keeps `h≥0`, so the bake (a) never NaNs
   AND (b) keeps `∫h` conservation **exact** — a CN ring would force a mass-adding `max(h,0)` clamp that
   breaks the tightest anchor (the clamp IS still applied defensively, but BE makes it a no-op). Cost:
   the scheme is O(dt) (BE-limited), honestly **first-order** — NOT claimed as Strang's formal O(dt²).
3. **The cited model makes acid a PURE CATALYST** — the `h` equation has **no `h·m` sink** (deprotection
   consumes blocked sites, not acid; verified verbatim from the Kirchauer node). So `∫h dx` is conserved
   at `k_loss=0` and decays **exactly `e^{−k_loss·t}`** otherwise (uniform scalar loss commutes with the
   conservative engine diffusion) — the **tightest leg**, holds on flat AND structured images to machine
   precision (~3e-15). This was advisor concern #2: confirm no `−k_amp·h·m` term on `h`. Confirmed.
4. **The local reaction integrates in CLOSED FORM** (a semigroup, so Strang sub-steps compose exactly):
   `h(τ)=h·e^{−k_loss·τ}`, `m=m·exp(−k_amp·hⁿ·Φ)`, `Φ=(1−e^{−n·k_loss·dt})/(n·k_loss)→dt`. So the
   **flat-field anchor is MACHINE-PRECISION-EXACT** (a uniform acid sees identity diffusion under
   `Neumann(0)` ⇒ the split = the exact reaction flow), not integrator-tol (stronger than first told the
   advisor). The no-reaction limit (`k_amp=k_loss=0`) **short-circuits to `peb_blur`** → the v1.7 linear
   blur **bit-for-bit** (advisor #3: short-circuit, don't run the split with identity reaction-steps).

**The mini-triad.** *Tight:* the no-reaction → v1.7-blur **bit-for-bit seam** + the **flat-field exact-
ODE** (machine precision, `k_loss` 0 and >0) + the **catalyst `∫h` conservation/decay** + deprotection
bounded `[0,1]` & monotone in bake. *Loose:* **amplification sharpens** — the superlinear `hⁿ` map makes
the deprotection edge **steeper than the acid's** (NILS 3.4→4.5 at the nominal bake), the signature that
makes CAR high-resolution; framed as a **REGIME not a monotone law** (at large σ / over-bake it reverses
— the v1.8 [[lateral-diffusion-2d]] "own the gap" discipline) — vs **diffusion + loss + over-bake
degrade** (the acutely bake-sensitive CD; the cited "control of the PEB is extremely critical"). **The
honest scope note:** with the cited **tiny `D` (σ~nm)** the acid diffusion is **negligible vs the
~150 nm optical resolution** — CAR makes *sharp* features (the resist out-resolves the optics here; the
acid-diffusion floor only bites sub-50 nm). The **exposure dose + bake times are illustrative knobs**
(`acid_dose=0.13`, ~60 s nominal bake) — only the four reaction–diffusion constants are cited.

**The seam bug found the hard way:** `D_h0=0` crashes the engine's **harmonic-mean face diffusivity**
(`2·D₀D₁/(D₀+D₁)` → 0/0 NaN), so the "pure-reaction" regime uses tiny-cited-`D` + short bake, not `D=0`
(added a `D_h0>0` guard). And the flat-field test first failed at `t=50 s` because the deprotection
**underflowed** (`m≈1e-23`, fully deprotected) → 0 vs 1.4e-23 at rtol=1e-12; fixed by testing a
**partial** regime (`t=1 s`, `m≈0.33`) where exactness is on a meaningful value.

Asymmetric images **refused** (the half-period cell, as v1.7 — reaction is pointwise so even `h`→even
`m`→even `D_h`, the symmetry carries over). Scope edges named-not-built: **linear exposure** (no Dill
bleaching), **constant-threshold development** (no Mack dissolution-rate kinetics), the **uncalibrated
free-volume `D_h1`** (cited in form, no cited coefficient → default constant `D`, `D_h1>0` illustrative),
the **uncoupled `x`/`z`** blurs (no 2-D resist volume). README (status + "to work on" + counts) + plan
§ v1.9 record + module docstring §8/§9 updated. **No engine amendment, no new ADR** (a pure chip build).
[[litho-peb-v17]] is the linear-blur predecessor; [[peb-acid-diffusion-source]] the cited model.
Committed direct to `main` (solo repo), pushed to origin ([[commit-at-end-of-batch]]).
