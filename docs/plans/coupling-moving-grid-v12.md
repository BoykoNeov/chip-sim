# Moving-grid fix for the v1.2 segregation swept-sliver edge

## Context

The Phase 1↔2 back-coupling (`chip/coupling.py`, v1.2) applies the dopant-segregation
mass balance `J = N_surf·(0.44 − 1/m)·(dx_ox/dt)` as a `Neumann(flux)` boundary on a
**fixed** grid. That flux is a *moving-interface* balance, but the grid does not recede,
so the `0.44·R` term ("dopant freed by consumed silicon") is **double-counted**: the swept
region `[0, 0.44·x_ox]` stays in the domain *and* its dopant is re-injected at the surface.
Consequence (named, owned in the code): **phosphorus pile-up is ~2× inflated** (boron
depletion stays robust because it is oxide-uptake-dominated). The module docstring calls the
real fix "a Stefan-problem treatment the pure-diffusion engine cannot express."

**It can — consumer-side.** This plan builds a **receding active sub-grid** in `coupling.py`
(the engine stays pure-diffusion, fixed-grid, *untouched*). It retires the named scope edge
and, as a bonus, **upgrades the conservation leg from an accounting identity to a real
magnitude check**.

### The derivation that licenses the scheme

For the silicon dose `Q_Si(t) = ∫_{s(t)}^{L} N dx` with the interface at `s(t) = 0.44·x_ox(t)`
receding at `v = ds/dt = 0.44·R`, Leibniz + the engine's flux identity give the true loss rate:

```
dQ_Si/dt = J_diff(s) − v·N_surf
         = N_surf·(0.44 − 1/m)·R − 0.44·N_surf·R
         = −(N_surf/m)·R  =  −C_ox·R          (C_ox = N_surf/m, the oxide's dopant conc.)
```

So silicon loses **exactly** what the growing oxide takes — total dopant conserved. The
existing flux `J_diff = N_surf·(0.44 − 1/m)·R` is **correct**; the fixed grid only omits the
geometric `−v·N_surf` (Leibniz) term. The fix supplies that term by **receding the mesh** —
the *same* flux stays, the mesh motion adds the missing sink.

Checked in both limits (per sub-step: `ΔQ_Si = dt·J_diff − removed_sliver`, `removed_sliver ≈ N_surf·v·dt`):
- **inert oxide** (m→∞): `J_diff = +0.44·N_surf·R` (spurious inflow, today's bug) is exactly cancelled by `removed = 0.44·N_surf·R` → net 0 (conserved). The artifact vanishes.
- **boron** (m=0.3): `J_diff = −2.89·N_surf·R`, `removed = +0.44·N_surf·R` → net `−3.33·N_surf·R = −C_ox·R`. ✓

## Approach

A **truncated-first-cell receding active sub-grid**, gated on `segregation=True`, marched
inside `oxidize_couple`'s existing sub-step loop. Engine untouched; all new logic in `coupling.py`.

### The per-sub-step march (replacing the loop body in `oxidize_couple`)

State: full-length `N` (cell averages on the original `grid` edges), interface position `s`
(starts 0), and `k0 = searchsorted(edges, s)` (the cell containing `s`).

1. **Build the active sub-grid** via `grid_from_edges([s, edges[k0+1], …, edges[-1]])` —
   the first (interface) cell is truncated to `[s, edges[k0+1]]`; all deeper cells are the
   original ones (zero interpolation in the bulk → no added numerical diffusion). Active state
   `= N[k0:]` (the truncated cell keeps its average — a first-order treatment, O(Δx), matching
   the already-lagged BC).
2. **Diffuse one step** on the active grid: `Diffusion1D(active_grid, D_of_t, Neumann(J_diff), Neumann(0))`,
   with `J_diff = N_active[0]·(0.44 − 1/m)·R_cm_s` — the **unchanged** segregation flux.
   Write the result back into `N[k0:]`.
3. **Advance the interface geometrically** to `s_new = SI_SIO2_RATIO · x_ox(t+dt)` using the
   closed-form `oxidation.oxide_thickness` / `oxide_thickness_massoud` (exact, Phase-2-consistent
   — not a dt-accumulated `Σv·dt`). Accumulate `removed = ∫_{s}^{s_new} N dx` over the just-updated
   profile (sum of cell slivers across whatever edges `s_new` crosses); add to the recession reservoir.
4. **Small-cell guard:** advance `k0` past any cell whose right edge `s` has reached; never let a
   truncated cell width fall to ~0 (backward-Euler is unconditionally stable and conservation holds
   on non-uniform grids — invariant 2 — so a small first cell is safe; a zero-width one is not).

`R=0` ⇒ `s` never moves ⇒ active grid ≡ full grid ⇒ the `segregation=False` and degenerate
paths are **bit-for-bit unchanged**.

### Conservation — upgraded to a real check

Track `oxide_uptake = oxide_uptake_flux (−Σ dt·J_diff) + oxide_uptake_recession (Σ removed)`.
Per step `ΔSi = dt·J_diff − removed` and `Δoxide_uptake = −dt·J_diff + removed`, so the
identity `si_dose + oxide_uptake = si_dose_initial` stays **machine-exact** (regression-safe).
The new, non-trivial leg: `oxide_uptake ≈ ∫ C_ox·R dt = ∫ (N_surf(t)/m)·R dt`, computed
**independently** of the flux bookkeeping — the diffusive and recession parts must *combine* to
the physical oxide dopant content. (For inert m→∞ this independent integral is 0 ⇒ the
inert-oxide conservation test.)

### Result-object & semantic changes (`CoupledResult`)

- **New field `interface_depth: float`** (cm) = `s_final = 0.44·x_ox(t_end)`. Output `N` stays
  **full-length** on the original grid (consumed cells zeroed; silicon occupies `x ≥ interface_depth`)
  so `inert.x.shape == coupled.N.shape` and `plots.py` keep working. `si_dose` is computed on the
  *active* (truncated) grid, so it stays exact.
- **`oxide_uptake` semantics change** from "signed reservoir (negative = rejected toward silicon)"
  to "**dopant content of the grown oxide, ≥ 0 for both dopants**" — the oxide is always a small
  positive sink at `C_ox > 0`. Phosphorus still **piles up locally** (surface concentration rises)
  while the total silicon dose slightly drops — the physically correct picture. `surface_concentration`
  = `N` at the first active (receded-surface) cell.

### Public knob

Add `moving_boundary: bool = True` to `oxidize_couple`. `True` is the new default (the fix);
`False` recovers the old fixed-grid behavior so the artifact is still demonstrable and the
"before" is pinned by a regression test. Recession is gated on `segregation and moving_boundary`.

**Why gate recession on `segregation`:** the OED-only path (`segregation=False`) is a *deliberate
sealed-surface idealization* — `test_oed_is_the_engine_effective_integral_D_dt` and
`test_oed_alone_sealed_surface_conserves_dose_machine_exact` rely on the fixed-grid sealed solve
matching the `∫D dt` time-substitution. Recession belongs to the moving-interface (segregation)
physics; keeping OED-only fixed-grid preserves that clean analytic anchor.

## Critical files

- **`chip/coupling.py`** — the work. New private helper(s) for the receding-mesh march
  (active-grid build + sliver bookkeeping); rewrite the `oxidize_couple` sub-step loop; add
  `moving_boundary` param; add `CoupledResult.interface_depth`; update the `oxide_uptake` docstring
  semantics and the module docstring's "swept-sliver" / "Stefan-problem the engine cannot express"
  prose to "now built as a consumer-side receding mesh." Reuse: `grid_from_edges`,
  `oxidation.oxide_thickness` / `oxide_thickness_massoud`, `SI_SIO2_RATIO`, `CM_PER_UM`.
- **`chip/tests/test_coupling.py`** — see test plan below.
- **`chip/tests/test_demo_coupling.py`** — surface-direction assertions hold; verify the
  `conservation_residual` leg still closes; no `oxide_uptake`-sign assertion lives here (safe).
- **`chip/demo_coupling.py`** + **`chip/plots.py`** — update the "~2× inflated" honesty caveat to
  "corrected by the receding-mesh treatment"; optionally mark `interface_depth` on the figure.
  `plots.py` already plots `coupled.N` vs `inert.x` (full-length) → no structural change.
- **`docs/plans/microchip-fabrication.md`** — append a v1.2-revision / v1.6 build-history note
  (mirroring the v1.5 promotion narrative); reword the v1.2 swept-sliver paragraph.
- **Engine, `CONTRACT.md`, ADRs** — **untouched** (consumer-side fix; no engine governance change,
  so no new ADR per ADR 0004). Memory `chip-coupling-v12` updated at the end.

## Test plan (`test_coupling.py` — triad discipline preserved)

**Tight / analytical (unchanged):** `test_zero_oxidation_collapses_to_plain_drive_in_bit_for_bit`,
`test_oed_is_the_engine_effective_integral_D_dt`, `test_oed_alone_sealed_surface_conserves_dose_machine_exact`,
`test_enhancement_and_flux_vanish_at_zero_oxidation_rate`, `test_segregation_flux_sign_follows_the_mass_balance`.

**Rewritten:**
- `test_inert_oxide_reveals_swept_sliver_artifact` → split into
  `test_inert_oxide_conserves_with_moving_boundary` (moving on, m→∞: `|spurious_gain| < ~1e-3`, the
  fix) **and** `test_fixed_grid_still_shows_swept_sliver_artifact` (`moving_boundary=False`, m→∞:
  `0.02 < gain < 0.20`, the documented "before").
- `test_boron_depletes_phosphorus_piles_up` — surface directions unchanged; update `oxide_uptake`
  assertions to **both > 0** with `boron_uptake > phosphorus_uptake`.

**New:**
- `test_moving_boundary_conserves_total_dopant` — the headline: `oxide_uptake ≈ ∫C_ox·R dt`
  (independent integral, within a few %) **and** identity machine-exact.
- `test_interface_recedes_by_silicon_consumed` — `interface_depth ≈ 0.44·oxide_thickness(t_end)` (tight).
- `test_phosphorus_pileup_magnitude_reduced_by_moving_boundary` — pile-up ratio (coupled/OED surface)
  is smaller with `moving_boundary=True` than `False` (quantifies ~2×→~1×; the edge retired).
- `test_segregation_off_leaves_no_recession` — `segregation=False` ⇒ `interface_depth == 0` and the
  full-grid result is unchanged.

**Kept:** `test_coupled_silicon_plus_oxide_accounting_closes`, `test_conservation_is_exact_at_any_step_count`
(now moving-boundary), and all OED/`f_I`/`m`/Massoud/refuse tests (segregation-independent).

Approx. count: coupling triad ~19 → ~24.

## Verification

1. **Fast lane:** `./run_tests.ps1` (or `pytest -m "not slow" -n auto`) — the engine suite must
   stay green (proves the engine is genuinely untouched), and the rewritten/new coupling tests pass.
2. **Inert-oxide conservation by hand:** run `oxidize_couple(..., "P", segregation_m=1e9, moving_boundary=True)`
   and confirm `(si_dose − si_dose_initial)/si_dose_initial ≈ 0` (was 0.02–0.20).
3. **Demo:** `python -m chip.demo_coupling` — phosphorus pile-up ratio should drop from ~1.17 toward
   ~1.0×, boron depletion essentially unchanged, conservation residual still machine-zero; the figure
   builds and the printed caveat reflects the fix.
4. **Independent magnitude check:** confirm `oxide_uptake` matches `∫(N_surf/m)·R dt` within a few %
   for boron and phosphorus (the conservation leg is now a real check, not just an identity).
