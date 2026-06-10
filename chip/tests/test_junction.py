"""Chip Phase-1a validation: the junction reading — x_j + sheet resistance (the benchmark leg).

This carries the **benchmark** leg of the plan's Phase-1 triad (microchip-fabrication.md §3):
junction depth ``x_j`` and sheet resistance ``R_s`` vs Irvin's (1962) published curves. The
comparison is a genuine **cross-check**, not a refit, because the two inputs are independently
cited: the diffusivity ``D₀, Ea`` (Fair, in ``diffusion_dopant``) is *diffusion* data not fit to
junction depth, and the mobility ``μ(N)`` (Masetti 1983) is an *independent transport* model, not
Irvin's own resistivity curves.

The deep-tail certification (the non-obvious correctness gate). The junction sits where the
profile crosses the background ``N_B`` — at ``z = x/2√(Dt) ≈ 3``, **far deeper** in the tail than
carburize's mid-profile case depth (``z ≈ 0.7``). The interior erfc check does not certify the
profile that deep, so two tests pin the numeric ``x_j`` against the **analytic** crossing for the
idealized erfc and Gaussian at ``z ≈ 3``: passing them at the demo's grid resolution is what
licenses trusting the realistic two-step demo's numeric ``x_j`` (which has no closed form).

Scope edge, named: Masetti + Irvin assume full activation at 300 K; at the solubility-limit
surface the electrically active N is below the chemical N — the active-vs-chemical ceiling.
"""
import math

import numpy as np
import pytest
from scipy.special import erfc, erfcinv

from engines.diffusion import uniform_grid, Neumann
from chip import diffusion_dopant as dd
from chip import junction as jn


# --------------------------------------------------------------------------- #
# Masetti (1983) mobility μ(N) — cited constants + limit behaviour (the integrand)
# --------------------------------------------------------------------------- #
def test_masetti_parameters_are_the_cited_table_values():
    # Pin the cited Masetti Table-I silicon values (verified vs IUE-Vienna for P, allpix²/CERN for
    # B & P). These are load-bearing for R_s, so pin them like carburize pins D0/Q.
    b = jn.MASETTI["B"]
    assert (b.mu_max, b.mu_min1, b.mu_min2, b.mu_1) == (470.5, 44.9, 0.0, 29.0)
    assert (b.Pc, b.Cr, b.Cs, b.alpha, b.beta) == (9.23e16, 2.23e17, 6.10e20, 0.719, 2.00)
    p = jn.MASETTI["P"]
    assert (p.mu_max, p.mu_min1, p.mu_min2, p.mu_1) == (1414.0, 68.5, 68.5, 56.1)
    assert (p.Pc, p.Cr, p.Cs, p.alpha, p.beta) == (0.0, 9.20e16, 3.41e20, 0.711, 1.98)


def test_mobility_lattice_limit_and_monotone_decrease():
    # Lightly doped → the lattice (low-doping) mobility μ_max; heavily doped → falls toward the
    # high-doping floor. Electrons (P) outrun holes (B) at every concentration.
    assert jn.mobility(1e14, "B") == pytest.approx(470.5, rel=0.01)
    assert jn.mobility(1e14, "P") == pytest.approx(1414.0, rel=0.01)
    N = np.logspace(15, 21, 50)
    muB, muP = jn.mobility(N, "B"), jn.mobility(N, "P")
    assert np.all(np.diff(muB) < 0) and np.all(np.diff(muP) < 0)   # monotone decreasing
    # Electrons outrun holes across the practical doping range (≤ 2e20). Above ~5e20 — extreme
    # degenerate doping past boron's solubility — the Masetti P/B curves cross (the strong P dip
    # term overtakes), a documented model feature, not asserted against.
    practical = N <= 2e20
    assert np.all(muP[practical] > muB[practical])
    # High-doping values land in the physically sensible degenerate band (tens of cm²/V·s).
    assert 40.0 < jn.mobility(1e20, "B") < 90.0
    assert 60.0 < jn.mobility(1e20, "P") < 130.0


def test_mobility_unknown_dopant_raises():
    with pytest.raises(KeyError):
        jn.mobility(1e18, "Ga")


# --------------------------------------------------------------------------- #
# Junction depth: the deep-tail (z ≈ 3) numeric-vs-analytic certification
# --------------------------------------------------------------------------- #
def test_junction_depth_matches_analytic_erfc_at_the_deep_tail():
    # Certify that the numeric predep solve resolves the profile at z ≈ 3 (where the junction
    # lives), by comparing the numeric crossing to the closed form x_j = 2√(Dt)·erfc⁻¹(N_B/N_s).
    # This is at the DEMO's grid resolution (n_cells = 600 over 3 µm), so passing it licenses the
    # realistic demo's numeric x_j.
    Ns = 3.0e20
    grid = uniform_grid(3.0e-4, 600)
    p = dd.predeposit(grid, "B", 950.0, 15 * 60.0, N_surface=Ns)
    NB = Ns * float(erfc(3.0))                          # background placing the junction at z ≈ 3
    xj_num = jn.junction_depth(p.x, p.N, NB)
    xj_ana = 2.0 * math.sqrt(p.D * p.t) * float(erfcinv(NB / Ns))
    assert xj_ana / (2.0 * math.sqrt(p.D * p.t)) == pytest.approx(3.0, abs=0.05)   # really z ≈ 3
    assert xj_num == pytest.approx(xj_ana, rel=0.03)   # numeric resolves the deep tail to ~3 %


def test_junction_depth_matches_analytic_gaussian_at_the_deep_tail():
    # The Gaussian counterpart: warm-start the exact Gaussian, propagate, and check the numeric
    # crossing matches x_j = 2√(Dt)·√(ln(N0/N_B)) with N0 = Q/√(πDt) the surface value at t1.
    D = dd.diffusivity("B", 1100.0)
    grid = uniform_grid(4.0e-4, 800)
    dose, t0, t1 = 1.0e15, 100.0, 1000.0
    N0_seed = dd.analytic_drivein_gaussian(grid.centers, t0, D, dose)
    N_num, _, _ = dd._diffuse(grid, D, N0_seed, Neumann(0.0), Neumann(0.0), t1 - t0, 900, "backward_euler")
    N_peak = dose / math.sqrt(math.pi * D * t1)
    NB = N_peak * math.exp(-9.0)                        # ln(N0/NB) = 9 → z = √9 = 3
    xj_num = jn.junction_depth(grid.centers, N_num, NB)
    xj_ana = 2.0 * math.sqrt(D * t1) * math.sqrt(math.log(N_peak / NB))
    assert xj_num == pytest.approx(xj_ana, rel=0.03)


def test_junction_depth_scales_as_sqrt_Dt():
    # The plan's benchmark phrasing "x_j(√Dt)": the erfc junction depth ∝ √(Dt) (the self-similar
    # variable x/2√(Dt) at the fixed level set N_B/N_s). Solve predep at several times (fixed T, N_s,
    # N_B) and confirm x_j/√t is constant — parity with carburize's case-depth ∝ √(Dt) leg. TIGHT.
    Ns, NB = 3.0e20, 3.0e15                            # N_B/N_s = 1e-5 → z ≈ 3.1 (the deep-tail crossing)
    grid = uniform_grid(4.0e-4, 800)
    ratios = []
    for t_min in (10.0, 20.0, 40.0):
        p = dd.predeposit(grid, "B", 1050.0, t_min * 60.0, N_surface=Ns)
        ratios.append(jn.junction_depth(p.x, p.N, NB) / math.sqrt(t_min))
    ratios = np.array(ratios)
    assert np.all(np.isfinite(ratios))
    assert ratios.std() / ratios.mean() < 0.02         # constant ratio → x_j ∝ √t


def test_junction_depth_nan_when_no_crossing():
    x = np.linspace(0, 1e-4, 100)
    N = 1e18 * np.exp(-x / 2e-5)                        # decays from 1e18
    assert math.isnan(jn.junction_depth(x, N, N_background=1e19))   # surface below background
    assert math.isnan(jn.junction_depth(x, N, N_background=1e10))   # never crosses in the domain


# --------------------------------------------------------------------------- #
# Sheet resistance + the Irvin benchmark (loose cross-check) and the trends
# --------------------------------------------------------------------------- #
def test_pn_junction_demo_benchmark_band():
    # The banked two-step boron junction into a 1e15 n-type wafer: junction ~1 µm, sheet
    # resistance in the published diffused-layer band, average resistivity ~1e-2 Ω·cm. These are
    # the Irvin cross-check handles — asserted LOOSELY (Irvin's curves are graphical; D and μ are
    # cited-not-fit, so agreement is a real cross-check, but the bands are wide).
    _, drivein = dd.two_step("B")
    j = jn.analyze_junction(drivein, "B", N_background=1e15)
    assert 0.5 < j.x_j_um < 2.0                         # ~1 µm junction
    assert 40.0 < j.R_s < 400.0                         # ohms/sq — typical boron diffused layer
    assert 3e-3 < j.rho_avg < 5e-2                      # Ω·cm — Irvin's plotted average resistivity


def test_sheet_resistance_and_junction_trends():
    # The physical monotonic trends (what a cross-check really tests, beyond one number):
    # (a) a higher background N_B moves the junction shallower (the profile crosses it sooner).
    _, drivein = dd.two_step("B")
    xj_lowB = jn.junction_depth(drivein.x, drivein.N, 1e15)
    xj_highB = jn.junction_depth(drivein.x, drivein.N, 1e17)
    assert xj_highB < xj_lowB
    # (b) a larger predep dose (longer predep) lays down more dopant → more conductance → lower R_s.
    grid = uniform_grid(3.0e-4, 600)
    light = dd.drive_in(grid, dd.predeposit(grid, "B", 950.0, 5 * 60.0).N, "B", 1100.0, 30 * 60.0)
    heavy = dd.drive_in(grid, dd.predeposit(grid, "B", 950.0, 30 * 60.0).N, "B", 1100.0, 30 * 60.0)
    Rs_light = jn.analyze_junction(light, "B", 1e15).R_s
    Rs_heavy = jn.analyze_junction(heavy, "B", 1e15).R_s
    assert Rs_heavy < Rs_light


def test_sheet_resistance_nan_for_unresolved_junction():
    # No junction (nan x_j) → no sheet resistance to report.
    x = np.linspace(0, 1e-4, 100)
    N = 1e18 * np.exp(-x / 2e-5)
    assert math.isnan(jn.sheet_resistance(x, N, "B", x_j=float("nan")))


def test_analyze_junction_phosphorus_n_type_layer():
    # The reading works for an n-type (phosphorus) layer into a p-type wafer too — the demo's
    # complementary junction (electrons, the higher-mobility carrier → lower R_s at equal dose).
    grid = uniform_grid(3.0e-4, 600)
    predep = dd.predeposit(grid, "P", 950.0, 15 * 60.0, N_surface=1e20)
    drivein = dd.drive_in(grid, predep.N, "P", 1100.0, 30 * 60.0)
    j = jn.analyze_junction(drivein, "P", N_background=1e15)
    assert j.dopant == "P"
    assert math.isfinite(j.x_j) and j.x_j > 0.0
    assert math.isfinite(j.R_s) and j.R_s > 0.0
