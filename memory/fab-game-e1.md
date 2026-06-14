---
name: fab-game-e1
description: "fab-game E1 SPLIT on verification (heat-mode FALSIFIED, D(t) budget BUILT) — transient spike/RTA anneal T(t)→D(T(t)). THE gate ('is T emergent or setpoint?') resolves to SETPOINT: √(D_dopant/α_thermal)≈1.2e-6 → T flat over the junction → D(T(t)) IS the engine's shipped D(t) (the OED effective_Dt twin), NOT a heat-mode engine. Heat-mode joins Robin-G as falsified → NO chip-side heat-mode consumer → Steel-only. BUILT: chip/diffusion_dopant.py §4 ThermalProgram/thermal_budget/equivalent_isothermal_time/drive_in_program/spike_budget_time_laplace; faster ramp → smaller ∫D dt → shallower x_j (why RTA). No engine, no ADR."
metadata: 
  node_type: memory
  type: project
  originSessionId: c1b14123-ec09-413e-846f-ee192c0ef39b
---

**project (2026-06-14):** **E1 SPLIT on verification** — the last named-but-credible scope edge (the
[[scope-edge-backlog]] E1, *"the one real heat-mode consumer"*). Like A2 ([[fab-game-a2]]), the build had a
two-clause premise and **verify-at-build falsified one clause**: the emergent-`T` **heat-mode engine** is
FALSIFIED; the real (`D(t)`) **thermal-budget** deepening is BUILT. User pre-cleared an engine build ("I have
no problems with engine builds") — the falsification is a *physics* verdict, not a cost dodge.

**THE verify-at-build gate ("is `T` emergent or just the setpoint?") → SETPOINT.** The discriminator is the
**dopant/thermal diffusivity ratio** `√(D_dopant/α_thermal) ≈ √(1.5e-13/0.1) ≈ 1.2e-6` in Si (order-of-mag
robust — α_Si never below ~0.1 cm²/s). Heat is ~10⁶× more diffusive than dopant ⇒ **at a junction's length
scale the thermal field is ALWAYS flat** (to sharpen a gradient across a 0.5 µm junction needs a ~25 ns pulse,
during which a B atom moves ~0.001 nm). Two independent legs (advisor's precision fix — don't overclaim "`T`
never emergent"): (a) E1's *named* consumer (dopant diffusion via `D(T)`) sees only a spatially-uniform `T(t)`
→ `D(T(t))` **IS** the engine's shipped `D(t)`; (b) the one place `T` *is* spatially emergent — the ~775 µm
**wafer-thickness** gradient in a flash anneal — has **no chip-diffusion consumer** (its would-be consumer is
thermoelastic slip/stress, unmodeled, not E1). This is exactly how TSUPREM/Sentaurus model ramps: uniform
`T(t)` through `D(T(t))`, never a heat PDE coupled to dopant. (Melt/liquid laser anneal — the *only* place a
transient heat solve bites — is the deferred **A5** Stefan front, a *liquid-*`D` regime, not solid `D(T(t))`.)

**The `D(t)` budget path — BUILT, the OED `effective_Dt` twin.** `chip/diffusion_dopant.py` §4 (additive; all
prior dopant/coupling tests untouched):
- `ThermalProgram` — a piecewise-linear spike `T(t)` (`T_base→T_peak` ramp-up, `hold_s`, ramp-down), with
  `.isothermal(T,dur)` (T_base==T_peak) = **the seam**.
- `thermal_budget = ∫₀^dur D(T(t))dt` — the **direct analogue of `coupling.effective_Dt`** ([[oed-source]]
  [[chip-coupling-v12]]), driven by `T(t)` instead of the oxidation rate; trapezoid over the marched sub-steps.
- `equivalent_isothermal_time = budget/D(T_peak)` — the inverse; the spike's peak-equivalent time.
- `drive_in_program` — sealed drive-in under the schedule via the engine's **callable `D(t)`** (`_diffuse`
  unchanged — engine accepts `D(t)`, passes straight through; **no engine amendment**). Reports
  `D=budget/t` (time-averaged) so `D·t=effective_Dt` keeps `.gaussian_profile()` self-consistent AND the
  isothermal seam reduces `D→D(T)` exactly (advisor fix #3).
- `spike_budget_time_laplace` — the `D0`-independent **Laplace closed form** `t_eq ≈ hold +
  (k·T_peak²/Ea)·(1/β_up+1/β_down)` (units eV·K²/eV/(K/s)=s).

**Triad (advisor-sharpened — only the first two tight-tight).** SEAM = `ThermalProgram.isothermal` ⇒ `drive_in`
**BIT-FOR-BIT** (`max|dN|=0.0`, the constant-callable-`D`==scalar engine guarantee, `test_variable_d`); the `D`
field too. EQUIVALENCE-INVERSE (advisor fix #1, the *tight* leg, NOT vs the analytic Gaussian) = a ramp run ==
an isothermal `drive_in` at `(T_peak, equivalent_isothermal_time)` — **numeric≈numeric, shared truncation
cancels → rel 2.6e-7** at n_steps=2000 (validates `equivalent_isothermal_time` genuinely inverts
`thermal_budget`). CONSERVATION = sealed drive-in conserves dose under `D(t)` (rel 1e-10). FINDING-LEG (advisor
fix #2 — the bare `∫D dt < D_max·t` is a *tautology*) = the Laplace closed form, exact-vs-Laplace ~**5–6 %**,
and `D0`-independence **exact** (rel 2.7e-16). Tolerances: seam 1e-12, conservation 1e-10, equivalence/Laplace
O(dt) (advisor fix #5). No conservation amendment (sealed drive-in inherits it); NO engine, NO ADR.

**THE finding — the Arrhenius collapse (why RTA is shallow).** `∫D dt` is dominated by a **narrow window near
the peak**: a 19 s spike to 1050 °C (600→peak→600, 1 s hold, 50 °C/s) deposits only **~2.5 s** of
peak-equivalent budget (a **~7× collapse**; the top ~50 °C of the ramp carries **~84 %** of the budget while
spanning ~16 % of the clock). So a **faster ramp → smaller `∫D dt` → shallower `x_j`** (and higher `R_s`) — the
budget, not the clock, sets the depth. Demo sweep (n⁺ P, 10→300 °C/s): `x_j` 0.086→0.079 µm monotone, all below
the 950 °C/8 min isothermal baseline 0.104 µm.

**Wired — opt-in, seam-safe.** `DiffusionKnobs.drivein_program: ThermalProgram|None=None` →
`two_step(drivein_program=…)` (when set, `program.duration` governs — `T_drivein`/`t_drivein_min` **bypassed**,
documented; advisor fix #4) → `diffusion_junction` (knobs_in gains spike peak/duration only when set).
**Default `None` ⇒ the isothermal step, the pipeline byte-for-byte** (full suite **621 passed**, 1 deselected).
Demo `fab_game/demo_thermal_budget.py` (`fab-game-e1.png`, 2 panels: budget-accrual collapse · `x_j`/`t_eq` vs
ramp rate, Laplace overlaid). `analyze_junction` reads only `.x`/`.N` (verified) → the `D=budget/t` choice is safe.

**The heat-mode engine — DEFERRED, premise FALSIFIED (joins Robin-`G`).** Building heat-mode here would
reproduce the uniform-`T` setpoint = **proof of its own redundancy** (A2's Robin-`G` flag verbatim — *"the
engine T(r)==slab leg would be proof of REDUNDANCY"*). **E1 closes the heat-mode search: NO chip-side heat-mode
consumer exists → heat-mode is confirmed Steel-program-only** (`test_robin_heat.py`). The rule A2 surfaced now
holds end-to-end: heat-mode beats a closed form only for a *transient* problem, and E1's "transient" was a
junction-uniform `T(t)` the `D(t)` path already serves. **Next promotable across the whole backlog = NONE.**
[[scope-edge-backlog]] [[fab-game]] [[fab-game-a2]] [[oed-source]] [[chip-coupling-v12]] [[engine-unfrozen]]
