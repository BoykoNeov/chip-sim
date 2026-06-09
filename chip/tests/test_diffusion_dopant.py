"""Chip Phase-1a validation: dopant diffusion — the frozen spine in mass mode.

This carries the analytical-limit and conservation legs of the plan's Phase-1 triad
(microchip-fabrication.md §3). Like carburize, the two headline legs are the **frozen
engine's own guarantees** re-instantiated in dopant mass mode — no new calibration:

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
import math

import numpy as np
import pytest
from scipy.special import erfc, erfcinv

from engines.diffusion import uniform_grid, Neumann
from projects.chip import diffusion_dopant as dd


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
    # The frozen engine (mass mode, constant D + Dirichlet surface) reproduces the error-function
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
