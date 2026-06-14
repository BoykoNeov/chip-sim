"""Chip Phase-1a validation: dopant diffusion — the spine in mass mode.

This carries the analytical-limit and conservation legs of the plan's Phase-1 triad
(microchip-fabrication.md §3). Like carburize, the two headline legs are the **engine's
own guarantees** re-instantiated in dopant mass mode — no new calibration:

* **Analytical limit (constant D).** The numeric **predeposition** (constant Dirichlet
  surface) matches ``N_s·erfc(x/2√(Dt))``; the **drive-in** of an exact delta-IC
  ``Gaussian`` (warm-started, sealed surface) matches ``(Q/√(πDt))·exp(−x²/4Dt)`` as it
  propagates. Both are asserted *tight* on their **idealizations** — **constant, intrinsic
  D**. The scope edge, named: a real predep runs *at* the solid-solubility limit, exactly
  where concentration-enhanced ``D(N)`` makes constant-D erfc weakest (the engine's
  flagged-unbuilt v1.1 case); so the realistic two-step (:func:`two_step`) is only
  *near-Gaussian* and is **not** asserted against the exact form — its job is the junction.

* **Conservation.** The drive-in dose ``∫N dx`` is conserved to machine precision (no-flux
  both ends — the engine's exact finite-volume guarantee), independent of whether the erfc
  holds. The predep dose *grows* as the exact flux-bookkeeping identity
  ``Q(t) = (2/√π)·N_s·√(Dt)``, matched by the engine's surface-flux integral
  ``Σ dt·flux(left)`` to machine precision (the carburize Dirichlet identity, re-confirmed).

The diffusivity ``D₀, Ea`` are cited Fair data (not fit to junction depth), which is what
makes the junction/sheet-resistance benchmark in ``test_junction.py`` a genuine cross-check.
"""
import dataclasses
import math

import numpy as np
import pytest
from scipy.special import erfc, erfcinv

from engines.diffusion import uniform_grid, Neumann
from chip import diffusion_dopant as dd


# --------------------------------------------------------------------------- #
# The cited physics constant: Fair intrinsic dopant diffusivity D(T)
# --------------------------------------------------------------------------- #
def test_dopant_diffusivity_matches_cited_fair_arrhenius():
    # Pin the cited Fair boron value (D0 = 0.76 cm²/s, Ea = 3.46 eV). At 1100 °C ≈ 1.52e-13
    # cm²/s — the diffusivity that sets the ~0.5 µm junction scale.
    assert dd.diffusivity("B", 1100.0) == pytest.approx(1.52e-13, rel=0.02)
    # Phosphorus (D0 = 3.85, Ea = 3.66) diffuses at a comparable rate to boron — both ~1.5e-13
    # at 1100 °C (the known fact that B and P are the "fast" dopants, Sb/As slower).
    assert dd.diffusivity("P", 1100.0) == pytest.approx(1.43e-13, rel=0.03)
    assert dd.diffusivity("Sb", 1100.0) < dd.diffusivity("B", 1100.0)   # Sb slower
    # Arrhenius: rises sharply with temperature.
    assert dd.diffusivity("B", 1150.0) > dd.diffusivity("B", 1100.0) > dd.diffusivity("B", 1050.0)


def test_diffusivity_scale_is_sub_micron_junction_depth():
    # 2√(Dt) for boron at 1100 °C over 1 h ≈ 0.47 µm — a sane junction-depth scale (matches
    # the cited CityU Example 8.1 ~0.76–0.94 µm at longer/hotter cycles). Recipe in, µm out.
    D = dd.diffusivity("B", 1100.0)
    two_root_Dt_um = 2.0 * math.sqrt(D * 3600.0) / dd.CM_PER_UM
    assert 0.3 < two_root_Dt_um < 0.7


def test_diffusivity_rejects_below_absolute_zero():
    with pytest.raises(ValueError):
        dd.diffusivity("B", -300.0)


# --------------------------------------------------------------------------- #
# Analytical limit: the predeposition erfc profile (constant D, Dirichlet surface)
# --------------------------------------------------------------------------- #
def _deep_predep():
    """A well-resolved predep (1100 °C / 30 min, √(Dt) ≈ 0.165 µm ≈ 33 cells) for the erfc anchor.

    Deliberately deeper/hotter than the *demo's* shallow predep so the active erfc region spans
    many cells — the exact-anchor leg is about the engine reproducing erfc, decoupled from the
    demo recipe (whose job is the junction, not the exact form).
    """
    grid = uniform_grid(4.0e-4, 800)
    return dd.predeposit(grid, "B", 1100.0, 30 * 60.0)


def test_predep_matches_erfc_in_the_interior():
    # The engine (mass mode, constant D + Dirichlet surface) reproduces the error-function
    # solution. Compare the interior (drop the Dirichlet surface cell, which carries the half-cell
    # first-order error); the active region is where erfc rises meaningfully above zero.
    p = _deep_predep()
    ana = p.erfc_profile()
    active = ana > 1e-3 * p.N_surface
    active[0] = False
    rel_err = np.abs(p.N[active] - ana[active]) / p.N_surface
    assert np.max(rel_err) < 1e-3                       # tight interior agreement


def test_predep_surface_monotone_and_semi_infinite():
    p = _deep_predep()
    # Surface ≈ the solid-solubility Dirichlet value; profile decreases monotonically into the
    # un-doped far field (semi-infinite — the deep end stays untouched).
    assert p.N[0] == pytest.approx(p.N_surface, rel=0.05)
    assert np.all(np.diff(p.N) <= 1e-3 * p.N_surface)
    assert p.N[-1] < 1e-6 * p.N_surface                # far field essentially zero


def test_predep_defaults_surface_to_solid_solubility():
    # With no N_surface given, the predep surface is the dopant's cited Trumbore solubility ceiling.
    grid = uniform_grid(3.0e-4, 400)
    p = dd.predeposit(grid, "B", 1000.0, 10 * 60.0)
    assert p.N_surface == dd.DOPANTS["B"].N_solid_solubility


# --------------------------------------------------------------------------- #
# Analytical limit: the drive-in exact Gaussian (delta-IC idealization, warm-started)
# --------------------------------------------------------------------------- #
def test_drivein_propagates_the_exact_gaussian():
    # The exact-Gaussian leg, kept on its idealization (a delta-function surface dose). Warm-start
    # the numeric solver with the analytic Gaussian at t0 (width √(2Dt0) spans ~11 cells — resolved)
    # and propagate to t1 = 10·t0 (a 3.16× broadening, so backward-Euler truncation is exercised),
    # sealed surface (the even Gaussian satisfies no-flux at x=0 automatically). L ≫ √(2Dt1) keeps it
    # semi-infinite. The propagated profile must match the analytic Gaussian at t1 — TIGHT.
    D = dd.diffusivity("B", 1100.0)
    grid = uniform_grid(4.0e-4, 800)
    dose, t0, t1 = 1.0e15, 100.0, 1000.0
    N0 = dd.analytic_drivein_gaussian(grid.centers, t0, D, dose)
    N_num, _, _ = dd._diffuse(grid, D, N0, Neumann(0.0), Neumann(0.0), t1 - t0, 900, "backward_euler")
    N_ana = dd.analytic_drivein_gaussian(grid.centers, t1, D, dose)
    assert np.max(np.abs(N_num - N_ana)) / N_ana.max() < 2e-3


def test_predep_dose_identity_form():
    # Closed form Q = (2/√π)·N_s·√(Dt) ∝ √(Dt): 4× time → 2× dose, linear in N_s.
    D = dd.diffusivity("B", 1100.0)
    q1 = dd.predep_dose(3e20, D, 3600.0)
    q4 = dd.predep_dose(3e20, D, 4 * 3600.0)
    assert q4 == pytest.approx(2.0 * q1, rel=1e-9)
    assert dd.predep_dose(6e20, D, 3600.0) == pytest.approx(2.0 * q1, rel=1e-9)


# --------------------------------------------------------------------------- #
# Conservation: drive-in dose conserved + predep dose = surface-flux integral
# --------------------------------------------------------------------------- #
def test_drivein_conserves_dose_to_machine_precision():
    # No-flux both ends → ∫N dx is conserved exactly (the engine's finite-volume guarantee). Run a
    # realistic predep, then drive it in: the dose is unchanged to machine precision.
    grid = uniform_grid(3.0e-4, 600)
    predep = dd.predeposit(grid, "B", 950.0, 15 * 60.0)
    drivein = dd.drive_in(grid, predep.N, "B", 1100.0, 30 * 60.0)
    assert drivein.dose == pytest.approx(predep.dose, rel=1e-10)
    # And the sealed surface carries (essentially) no flux — the redistribution is internal.
    assert abs(drivein.surface_flux_dose) < 1e-6 * drivein.dose


def test_drivein_conserves_dose_even_when_not_semi_infinite():
    # Conservation is structural (no-flux both ends), independent of the Gaussian holding: a shallow
    # domain so the dose reaches and reflects off the far end — the Gaussian form breaks, the mass
    # balance does NOT (mirrors carburize's analogous test).
    grid = uniform_grid(0.4e-4, 200)                    # 0.4 µm — far too shallow to be semi-infinite
    seed = dd.analytic_drivein_gaussian(grid.centers, 200.0, dd.diffusivity("B", 1100.0), 1e15)
    drivein = dd.drive_in(grid, seed, "B", 1150.0, 60 * 60.0)
    assert drivein.N[-1] > 1e-3 * drivein.N[0]          # far end is NOT untouched here (reflected)
    # Conserved in the engine's own finite-volume measure Σ Nᵢ·Δxᵢ (== DopantProfile.dose), not the
    # trapezoid rule (they differ by O(Δx²)·curvature on a curved profile — that gap is integration
    # convention, not a leak; the engine conserves *its* total exactly).
    seed_total = float(np.sum(seed * grid.widths))
    assert drivein.dose == pytest.approx(seed_total, rel=1e-10)


def test_predep_dose_equals_surface_flux_and_analytic_identity():
    # The conservation/flux-bookkeeping leg: the predep dose (∫N dx, from zero) equals the
    # accumulated surface flux Σ dt·flux(left) to machine precision (the engine's exact
    # backward-Euler identity, no-flux far end), AND both match the analytic 1.128·N_s·√(Dt).
    p = _deep_predep()
    assert p.dose > 0.0
    assert p.dose == pytest.approx(p.surface_flux_dose, rel=1e-10)
    analytic = dd.predep_dose(p.N_surface, p.D, p.t)
    assert p.dose == pytest.approx(analytic, rel=0.015)


# --------------------------------------------------------------------------- #
# The realistic two-step demo chain: the erfc → Gaussian morph (NOT an exact test)
# --------------------------------------------------------------------------- #
def test_two_step_redistributes_dopant_deeper_conserving_dose():
    # The banked-demo chain: a short hot predep lays down a thin erfc dose; the longer drive-in
    # redistributes it much deeper (D_drive·t_drive ≫ D_predep·t_predep), so the surface
    # concentration falls by ~an order of magnitude and the profile spreads — the erfc→Gaussian
    # morph. The dose is conserved through the (sealed) drive-in; the surface drops because the
    # fixed dose now occupies a wider, deeper distribution.
    predep, drivein = dd.two_step("B")
    assert drivein.N[0] < 0.2 * predep.N[0]             # surface fell ~order of magnitude
    assert drivein.dose == pytest.approx(predep.dose, rel=1e-10)   # dose conserved
    # The drive-in profile is wider: it has appreciable dopant far deeper than the predep did.
    depth_predep = predep.x[predep.N > 1e-3 * predep.N[0]][-1]
    depth_drivein = drivein.x[drivein.N > 1e-3 * drivein.N[0]][-1]
    assert depth_drivein > 3.0 * depth_predep


def test_two_step_drivein_is_only_near_gaussian_not_exact():
    # The honest split: because the drive-in starts from the *actual erfc* (not a delta), its
    # profile is only NEAR-Gaussian — it does NOT match the exact delta-IC Gaussian for its own
    # dose. In this demo's regime (predep much shallower than the drive-in, so the seed ≈ a delta)
    # the agreement is GOOD near the surface (~0.4 %) but the finite seed width makes the drive-in
    # **tail fuller** than a pure delta-IC Gaussian — the deviation grows to ~8 % deep in the tail
    # (right where the junction lives). We assert the deviation is real but bounded: a good
    # near-Gaussian, not the exact anchor — so a future session keeps the exact leg on its
    # idealization (tested to 2e-3 above) and the demo's job on the junction.
    _, drivein = dd.two_step("B")
    near = drivein.gaussian_profile()                   # exact Gaussian for this dose at t_drivein
    active = drivein.N > 1e-3 * drivein.N[0]
    max_dev = np.max(np.abs(drivein.N[active] - near[active]) / drivein.N[active])
    assert abs(drivein.N[0] - near[0]) / drivein.N[0] < 0.02   # near-Gaussian at the surface
    assert 0.02 < max_dev < 0.20                               # but measurably not exact (tail)


# --------------------------------------------------------------------------- #
# E1 — the transient spike/RTA thermal budget: D(T(t)) → ∫D dt (the D(t) path)
# --------------------------------------------------------------------------- #
# The heat-mode premise is FALSIFIED (√(D/α) ≈ 1.2e-6 → T flat over the junction → setpoint, not
# emergent); this is the engine's already-shipped time-dependent D(t), the twin of OED's
# effective_Dt. The legs: the isothermal SEAM (constant program == drive_in bit-for-bit), the
# EQUIVALENCE inverse (equivalent_isothermal_time genuinely inverts thermal_budget), dose
# CONSERVATION under D(t), and the FINDING (Arrhenius collapse → t_eq ≪ ramp time, Laplace form).
def test_isothermal_program_recovers_drivein_bit_for_bit():
    # The seam: a flat ThermalProgram == the scalar-D drive_in, BIT-FOR-BIT (the engine's
    # constant-callable-D == scalar-D guarantee, test_callable_D_constant_equals_scalar). Same
    # grid / dose / n_steps. D = budget/t reduces to D(T) exactly, so even the D field matches.
    grid = uniform_grid(3.0e-4, 600)
    seed = dd.analytic_drivein_gaussian(grid.centers, 200.0, dd.diffusivity("B", 1100.0), 1e15)
    iso = dd.drive_in(grid, seed, "B", 1050.0, 90.0)
    ramp = dd.drive_in_program(grid, seed, "B", dd.ThermalProgram.isothermal(1050.0, 90.0))
    assert np.max(np.abs(ramp.N - iso.N)) < 1e-12              # byte-for-byte profile
    assert ramp.D == pytest.approx(iso.D, rel=1e-12)          # reported D == D(T) for isothermal
    assert ramp.t == pytest.approx(iso.t)                     # duration == hold_s
    assert ramp.effective_Dt == pytest.approx(iso.D * iso.t, rel=1e-10)  # budget == D·t


def test_equivalent_isothermal_time_inverts_thermal_budget():
    # The tight equivalence leg: a transient drive-in equals an isothermal drive_in at
    # (T_peak, equivalent_isothermal_time(T_peak, budget)) — numeric vs numeric, shared spatial
    # truncation cancels (far tighter than vs the closed form). This validates
    # equivalent_isothermal_time as the genuine inverse of thermal_budget (the τ=∫D dt substitution
    # made concrete through our own functions), and that the run depends on T(t) only via the budget.
    grid = uniform_grid(4.0e-4, 800)
    seed = dd.analytic_drivein_gaussian(grid.centers, 200.0, dd.diffusivity("B", 1050.0), 1e15)
    prog = dd.ThermalProgram(T_peak=1050.0, ramp_up_C_per_s=40.0, ramp_down_C_per_s=40.0, hold_s=2.0)
    budget = dd.thermal_budget("B", prog, n_steps=2000)
    t_eq = dd.equivalent_isothermal_time("B", 1050.0, budget)
    ramp = dd.drive_in_program(grid, seed, "B", prog, n_steps=2000)
    iso_eq = dd.drive_in(grid, seed, "B", 1050.0, t_eq, n_steps=2000)
    assert np.max(np.abs(ramp.N - iso_eq.N)) / iso_eq.N.max() < 1e-5   # numeric≈numeric (O(dt) cancels)
    assert ramp.effective_Dt == pytest.approx(budget, rel=1e-12)      # the budget the profile carries
    # Looser secondary: vs the analytic Gaussian at the budget age (call the analytic form directly,
    # not .gaussian_profile()) — the same warm-started-propagation leg as the exact-Gaussian test.
    tau0 = dd.diffusivity("B", 1050.0) * 200.0
    N_ana = dd.analytic_drivein_gaussian(grid.centers, 1.0, tau0 + budget, 1e15)
    assert np.max(np.abs(ramp.N - N_ana)) / N_ana.max() < 3e-3


def test_thermal_budget_drivein_conserves_dose():
    # Sealed (no-flux both ends) drive-in under a time-varying D(T(t)) conserves dose to machine
    # precision — the engine's structural finite-volume guarantee, here exercised with a spike D(t).
    grid = uniform_grid(3.0e-4, 600)
    predep = dd.predeposit(grid, "B", 950.0, 15 * 60.0)
    prog = dd.ThermalProgram(T_peak=1100.0, ramp_up_C_per_s=50.0, ramp_down_C_per_s=50.0, hold_s=1.0)
    ramp = dd.drive_in_program(grid, predep.N, "B", prog)
    assert ramp.dose == pytest.approx(predep.dose, rel=1e-10)
    assert abs(ramp.surface_flux_dose) < 1e-6 * ramp.dose     # sealed surface carries ~no flux


def test_spike_budget_collapses_to_a_narrow_peak_window_laplace():
    # THE finding (not the tautology ∫D dt < D_max·t): the Arrhenius integral is dominated by a
    # narrow window near the peak, so the equivalent isothermal time is set by the ramp RATE, not the
    # ramp duration. Laplace asymptotics give the D0-independent closed form
    # t_eq ≈ hold + (k·T_peak²/Ea)·(1/β_up + 1/β_down); a 50 °C/s spike 600→1050→600 °C (an 18 s ramp)
    # deposits only ~1.6 s of peak-equivalent budget — an ~11× collapse. *This* is why RTA is shallow.
    spike = dd.ThermalProgram(T_peak=1050.0, ramp_up_C_per_s=50.0, ramp_down_C_per_s=50.0,
                              hold_s=0.0, T_base=600.0)
    budget = dd.thermal_budget("B", spike, n_steps=4000)
    t_eq = dd.equivalent_isothermal_time("B", 1050.0, budget)
    laplace = dd.spike_budget_time_laplace("B", spike)
    assert t_eq == pytest.approx(laplace, rel=0.10)           # exact (trapezoid) ≈ Laplace (~6%)
    assert t_eq < 0.3 * spike.duration                       # the collapse: t_eq ≪ the 18 s ramp


def test_equivalent_isothermal_time_is_D0_independent():
    # t_eq = budget/D(T_peak); budget ∝ D0 and D(T_peak) ∝ D0, so t_eq cancels D0 EXACTLY — a clean
    # invariance (two dopants differing only in D0 give the identical equivalent time).
    spike = dd.ThermalProgram(T_peak=1050.0, ramp_up_C_per_s=50.0, ramp_down_C_per_s=50.0, T_base=600.0)
    B = dd.DOPANTS["B"]
    B2 = dataclasses.replace(B, name="B2", D0=B.D0 * 10.0)    # same Ea, 10× pre-exponential
    teq_B = dd.equivalent_isothermal_time(B, 1050.0, dd.thermal_budget(B, spike, n_steps=2000))
    teq_B2 = dd.equivalent_isothermal_time(B2, 1050.0, dd.thermal_budget(B2, spike, n_steps=2000))
    assert teq_B == pytest.approx(teq_B2, rel=1e-12)


def test_thermal_program_isothermal_and_validation():
    # ThermalProgram mechanics: the isothermal seam is flat at T everywhere; a spike peaks at T_peak
    # and returns to T_base; bad rates raise.
    iso = dd.ThermalProgram.isothermal(1000.0, 30.0)
    assert iso(0.0) == iso(15.0) == iso(30.0) == 1000.0       # flat schedule
    assert iso.duration == pytest.approx(30.0)
    spike = dd.ThermalProgram(T_peak=1050.0, ramp_up_C_per_s=50.0, ramp_down_C_per_s=25.0, hold_s=2.0)
    assert spike(spike.ramp_up_s) == pytest.approx(1050.0)    # reaches the peak
    assert spike.ramp_down_s == pytest.approx(2.0 * spike.ramp_up_s)  # half-rate ⇒ twice as long
    assert spike(spike.duration + 1.0) == spike.T_base        # back to base after the anneal
    with pytest.raises(ValueError):
        dd.ThermalProgram(T_peak=1000.0, ramp_up_C_per_s=0.0, ramp_down_C_per_s=10.0)
