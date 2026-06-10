"""Chip Phase-2 validation: thermal oxidation — the Deal–Grove triad.

This carries the whole plan §3 Phase-2 triad (microchip-fabrication.md). Unlike Phase 1a there is
**no frozen engine underneath** — this module *is* the closed form — so its tests carry every leg:

* **Analytical limit (tight, on its idealization).** The exact ``x_ox(t)`` satisfies the algebraic
  identity ``x_ox² + A·x_ox − B(t+τ) = 0`` to machine precision; reproduces the linear ``(B/A)·t``
  (thin) and parabolic ``√(B·t)`` (thick) asymptotes in their regimes; and an **independent ODE**
  integration of ``dx/dt = B/(A+2x)`` recovers it. Scope edge, named: the thin-dry (Massoud)
  anomaly — v1 is plain Deal–Grove, which does NOT model it (asserted as a documented limitation,
  not a failure).

* **Conservation (tight).** Growing oxide consumes silicon at the fixed ``0.44`` ratio; the
  moving-boundary bookkeeping ``si_consumed + oxide_above = x_ox`` closes exactly.

* **Benchmark (loose).** The cited rate constants (pinned exactly, like Phase 1a pins Fair/Masetti)
  and the wet-vs-dry thicknesses vs the published Deal–Grove table (wide band — published points
  carry pressure/orientation/source spread).

The benchmark leg's strength, stated precisely (the validated-vs-calibrated discipline): it rests on
**citation fidelity** — the constants pinned to the published Deal–Grove table (deal-grove-oxidation-source
memory note), which is NOT a tautology (they could be miscited) — plus the independent tight
algebraic-identity leg. The **thickness comparison is a consistency check, not an independent cross-check**:
Deal–Grove's B/(B/A) were originally fit to oxide-thickness data, so thickness-from-constants vs published
thickness is closer to model-vs-itself than carburize's tracer-diffusion D (a separate measurement domain).
Hence thickness asserted loosely, constants tightly.
"""
import math

import numpy as np
import pytest

from chip import oxidation as ox


# --------------------------------------------------------------------------- #
# Benchmark: the cited Deal–Grove rate-constant table (pinned exactly)
# --------------------------------------------------------------------------- #
def test_rate_constants_are_the_cited_deal_grove_table():
    # Pin the cited Deal & Grove (1965) / Plummer–Deal–Griffin constants (deal-grove-oxidation-source).
    # Load-bearing for every thickness, so pin them like carburize pins D0/Q. (111) silicon, eV + µm-hr;
    # wet Ea_B is the TABLE value 0.78 eV (not the 0.71 that floats in prose summaries).
    dry = ox.AMBIENTS["dry"]
    assert (dry.C_B, dry.Ea_B, dry.C_lin, dry.Ea_lin) == (7.72e2, 1.23, 6.23e6, 2.00)
    wet = ox.AMBIENTS["wet"]
    assert (wet.C_B, wet.Ea_B, wet.C_lin, wet.Ea_lin) == (3.86e2, 0.78, 1.63e8, 2.05)
    # The orientation factor (linear only) and the Si/SiO₂ consumption ratio.
    assert ox.ORIENTATION_FACTOR["111"] == 1.0
    assert ox.ORIENTATION_FACTOR["100"] == pytest.approx(1.0 / 1.68)
    assert ox.SI_SIO2_RATIO == 0.44


def test_rate_constants_evaluate_to_published_magnitudes():
    # B and B/A at 1100 °C, (111) — the cited table evaluated. Independent hand values
    # (k = 8.617e-5 eV/K): dry B ≈ 0.0236 µm²/hr, B/A ≈ 0.284 µm/hr; wet B ≈ 0.530, B/A ≈ 4.87.
    rd = ox.oxide_rate_constants("dry", 1100.0, "111")
    assert rd.B == pytest.approx(0.0236, rel=0.02)
    assert rd.B_over_A == pytest.approx(0.284, rel=0.02)
    rw = ox.oxide_rate_constants("wet", 1100.0, "111")
    assert rw.B == pytest.approx(0.530, rel=0.02)
    assert rw.B_over_A == pytest.approx(4.87, rel=0.02)
    # A = B/(B/A): a sub-tenth-micron crossover length for both.
    assert rd.A == pytest.approx(rd.B / rd.B_over_A)
    assert 0.05 < rd.A < 0.3 and 0.05 < rw.A < 0.3


def test_rate_constants_are_arrhenius_in_temperature():
    # B and B/A rise sharply with temperature (the Arrhenius form).
    lo = ox.oxide_rate_constants("dry", 1000.0)
    hi = ox.oxide_rate_constants("dry", 1100.0)
    assert hi.B > lo.B and hi.B_over_A > lo.B_over_A


def test_orientation_factor_scales_linear_constant_only():
    # (B/A)₍₁₁₁₎ = 1.68·(B/A)₍₁₀₀₎ exactly; B (oxidant diffusion through amorphous oxide) is
    # orientation-INDEPENDENT — the same for (100) and (111).
    r100 = ox.oxide_rate_constants("wet", 1100.0, "100")
    r111 = ox.oxide_rate_constants("wet", 1100.0, "111")
    assert r111.B_over_A == pytest.approx(1.68 * r100.B_over_A)
    assert r100.B == pytest.approx(r111.B)


def test_unknown_orientation_and_subzero_temperature_raise():
    with pytest.raises(ValueError):
        ox.oxide_rate_constants("dry", 1000.0, orientation="110")
    with pytest.raises(ValueError):
        ox.oxide_rate_constants("dry", -300.0)        # below absolute zero (via _arrhenius)


# --------------------------------------------------------------------------- #
# Analytical limit: the exact closed form satisfies its own quadratic identity
# --------------------------------------------------------------------------- #
def test_closed_form_satisfies_the_linear_parabolic_identity():
    # The exact anchor: x_ox(t) solves x² + A·x = B(t+τ) to machine precision (pure algebra), for a
    # bare wafer (τ=0) at several times and for both ambients. TIGHT.
    for ambient in ("dry", "wet"):
        r = ox.oxide_rate_constants(ambient, 1100.0, "100")
        for t in (0.01, 0.1, 1.0, 10.0):
            x = ox.oxide_thickness(t, r.B, r.A)
            assert x**2 + r.A * x == pytest.approx(r.B * t, rel=1e-12)


def test_closed_form_recovers_initial_oxide_and_the_tau_machinery():
    # Free tight checks on the re-oxidation path. (a) At t=0 the closed form returns x_initial
    # exactly (the τ offset recovers the seed). (b) Growing from a seed x_i for time t equals growing
    # from bare for time (t + τ_i) — the τ machinery is just a time-origin shift. Both pure algebra.
    r = ox.oxide_rate_constants("wet", 1100.0, "100")
    xi = 0.05
    assert ox.oxide_thickness(0.0, r.B, r.A, x_initial=xi) == pytest.approx(xi, rel=1e-12)
    tau_i = ox.tau_offset(xi, r.B, r.A)
    grown_from_seed = ox.oxide_thickness(0.5, r.B, r.A, x_initial=xi)
    grown_from_bare = ox.oxide_thickness(0.5 + tau_i, r.B, r.A, x_initial=0.0)
    assert grown_from_seed == pytest.approx(grown_from_bare, rel=1e-12)


def test_thin_limit_is_linear_in_time():
    # Thin oxide (x ≪ A/2): the closed form → the linear asymptote (B/A)·t. At a tiny time the two
    # agree closely (the o(t²) correction is negligible), and the growth is ∝ t.
    r = ox.oxide_rate_constants("dry", 1100.0, "100")
    t = 1.0e-4
    assert ox.oxide_thickness(t, r.B, r.A) == pytest.approx(ox.linear_limit(t, r.B, r.A), rel=1e-3)
    # Doubling the (tiny) time doubles the thickness — linear kinetics.
    assert ox.oxide_thickness(2 * t, r.B, r.A) == pytest.approx(2 * ox.oxide_thickness(t, r.B, r.A), rel=1e-3)


def test_thick_limit_is_parabolic_in_time():
    # Thick oxide (x ≫ A/2): the closed form → the parabolic asymptote √(B·t). At a large time the
    # two agree (the −A/2 offset is negligible), and the growth is ∝ √t (4× time → 2× thickness).
    r = ox.oxide_rate_constants("wet", 1100.0, "100")
    t = 1.0e5
    assert ox.oxide_thickness(t, r.B, r.A) == pytest.approx(ox.parabolic_limit(t, r.B), rel=5e-3)
    assert ox.oxide_thickness(4 * t, r.B, r.A) == pytest.approx(2 * ox.oxide_thickness(t, r.B, r.A), rel=5e-3)


def test_ode_integration_recovers_the_closed_form():
    # The analytic↔ODE consistency leg: integrating dx/dt = B/(A+2x) reproduces the closed form. Not
    # machine precision (it is a numerical IVP) but tight — solve_ivp at rtol 1e-9 lands well under 1e-6.
    r = ox.oxide_rate_constants("dry", 1100.0, "100")
    t, x_ode = ox.integrate_growth_ode(2.0, r.B, r.A, n_eval=100)
    x_exact = ox.oxide_thickness(t, r.B, r.A)
    interior = t > 0                                  # skip t=0 (0/0 in the relative error)
    rel = np.abs(x_ode[interior] - x_exact[interior]) / x_exact[interior]
    assert np.max(rel) < 1e-6


def test_oxide_thickness_rejects_negative_time():
    r = ox.oxide_rate_constants("dry", 1000.0)
    with pytest.raises(ValueError):
        ox.oxide_thickness(-1.0, r.B, r.A)


def test_thin_dry_massoud_regime_stays_out_of_the_plain_path():
    # The scope edge was PROMOTED in v1.1 (the Massoud correction below), but the plain Deal–Grove
    # path keeps its exact anchor bit-for-bit: at x→0 the default dry growth rate is exactly the
    # finite linear rate B/A — NO enhancement leaks into grow_oxide/growth_rate (the same
    # defaults-recover-v1 discipline as the exoplanet knobs).
    r = ox.oxide_rate_constants("dry", 1000.0, "100")
    assert ox.growth_rate(0.0, r.B, r.A) == pytest.approx(r.B_over_A, rel=1e-12)   # finite B/A, no burst
    thin = ox.grow_oxide("dry", 1000.0, t_minutes=20.0)
    assert thin.t_ox_nm < 40.0          # the gate recipe lands in the thin band where the anomaly bites
    assert thin.model == "deal-grove"   # the default path is tagged plain


# --------------------------------------------------------------------------- #
# Conservation: silicon consumed = 0.44·x_ox (the moving-boundary mass balance)
# --------------------------------------------------------------------------- #
def test_silicon_consumed_is_the_cited_044_ratio():
    # The Si→SiO₂ number-density bookkeeping: 0.44 µm of silicon per µm of oxide. Pin the ratio.
    assert ox.silicon_consumed(1.0) == pytest.approx(0.44)
    assert ox.silicon_consumed(0.5) == pytest.approx(0.22)
    # Vectorized over a thickness array too.
    np.testing.assert_allclose(ox.silicon_consumed(np.array([0.0, 1.0, 2.0])), [0.0, 0.44, 0.88])


def test_moving_boundary_bookkeeping_closes_exactly():
    # The free mass balance: of every micron of oxide, 0.44 µm is consumed silicon (interface drops
    # below the original surface) and 0.56 µm is net swelling (oxide above it) — the two sum to x_ox.
    g = ox.grow_oxide("wet", 1100.0, t_minutes=60.0)
    assert g.si_consumed == pytest.approx(0.44 * g.t_ox)
    assert g.oxide_above_original_surface == pytest.approx(0.56 * g.t_ox)
    assert g.si_consumed + g.oxide_above_original_surface == pytest.approx(g.t_ox, rel=1e-12)


# --------------------------------------------------------------------------- #
# Benchmark: wet vs dry thicknesses vs the published Deal–Grove table (loose)
# --------------------------------------------------------------------------- #
def test_wet_vs_dry_thickness_at_1100C_one_hour():
    # The headline benchmark, (100) silicon, 1100 °C, 1 h. Published Deal–Grove: dry ≈ 0.10 µm, wet
    # ≈ 0.64 µm (wet ~6× faster — the diffusivity of H₂O in oxide far exceeds O₂'s). Loose bands
    # (the published points carry pressure/orientation/source spread); the WET ≫ DRY contrast is the
    # robust physical thesis.
    dry = ox.grow_oxide("dry", 1100.0, t_minutes=60.0)
    wet = ox.grow_oxide("wet", 1100.0, t_minutes=60.0)
    assert 0.07 < dry.t_ox < 0.13                     # ~0.10 µm
    assert 0.55 < wet.t_ox < 0.75                     # ~0.64 µm
    assert wet.t_ox > 5.0 * dry.t_ox                  # wet dominates


def test_oxide_grows_with_time_and_temperature():
    # Monotone in the recipe knobs: longer time and higher temperature both grow more oxide.
    assert ox.grow_oxide("wet", 1100.0, 120.0).t_ox > ox.grow_oxide("wet", 1100.0, 30.0).t_ox
    assert ox.grow_oxide("wet", 1150.0, 60.0).t_ox > ox.grow_oxide("wet", 1050.0, 60.0).t_ox


def test_regime_classification_thin_linear_thick_parabolic():
    # A short oxidation sits in the linear (reaction-limited) regime; a long wet one reaches the
    # parabolic (diffusion-limited) regime — the annotation the demo curve marks.
    assert ox.grow_oxide("dry", 1000.0, t_minutes=10.0).regime == "linear"
    assert ox.grow_oxide("wet", 1100.0, t_minutes=600.0).regime == "parabolic"


def test_grow_oxide_reports_um_and_nm_consistently():
    # t_ox is µm (the cross-module length currency); t_ox_nm the same length in nm (×1000).
    g = ox.grow_oxide("dry", 1000.0, t_minutes=30.0)
    assert g.t_ox_nm == pytest.approx(g.t_ox * 1000.0)
    assert g.ambient == "dry" and g.orientation == "100"


# --------------------------------------------------------------------------- #
# v1.1 — the Massoud thin-dry correction (its own mini-triad)
# --------------------------------------------------------------------------- #
# Benchmark (tight pins): the cited Hollauer §2.7 tables ------------------------------------
def test_massoud_constants_are_the_cited_hollauer_tables():
    # Pin Table 2.4 (K/τ Arrhenius, dry, 800–1000 °C) and Table 2.3's T<1000 °C Massoud B / B/A
    # per orientation — the massoud-thin-oxide source pin (Massoud & Plummer 1987 / JECS 132:1746,
    # compiled in Hollauer TU Wien diss. 2007). Load-bearing for every v1.1 thickness.
    m100 = ox.MASSOUD_DRY["100"]
    assert (m100.C_B, m100.Ea_B, m100.C_lin, m100.Ea_lin) == (1.70e11, 2.22, 7.35e6, 1.76)
    assert (m100.K1_0, m100.Ea_K1, m100.K2_0, m100.Ea_K2) == (2.49e11, 2.18, 3.72e11, 2.28)
    assert (m100.tau1_0, m100.Ea_tau1, m100.tau2_0, m100.Ea_tau2) == (4.14e-6, 1.38, 2.71e-7, 1.88)
    m111 = ox.MASSOUD_DRY["111"]
    assert (m111.C_B, m111.Ea_B, m111.C_lin, m111.Ea_lin) == (1.34e9, 1.71, 1.32e7, 1.74)
    assert (m111.K1_0, m111.Ea_K1, m111.K2_0, m111.Ea_K2) == (2.70e9, 1.74, 1.33e9, 1.76)
    assert (m111.tau1_0, m111.Ea_tau1, m111.tau2_0, m111.Ea_tau2) == (1.72e-6, 1.45, 1.56e-7, 1.90)
    m110 = ox.MASSOUD_DRY["110"]
    assert (m110.C_B, m110.Ea_B, m110.C_lin, m110.Ea_lin) == (3.73e8, 1.63, 4.73e8, 2.10)
    assert (m110.K1_0, m110.Ea_K1, m110.K2_0, m110.Ea_K2) == (4.07e8, 1.54, 1.20e8, 1.56)
    assert (m110.tau1_0, m110.Ea_tau1, m110.tau2_0, m110.Ea_tau2) == (5.38e-9, 2.02, 1.63e-8, 2.12)
    assert ox.MASSOUD_T_RANGE_C == (800.0, 1000.0)


def test_massoud_rates_evaluate_to_hand_checked_magnitudes():
    # The evaluated model at 1000 °C, (100) — independent hand values (k = 8.617e-5 eV/K):
    # B ≈ 277 nm²/min, B/A ≈ 0.793 nm/min, K₁ ≈ 584, K₂ ≈ 351 nm²/min, τ₁ ≈ 1.20, τ₂ ≈ 7.50 min.
    # τ uses the POSITIVE exponent (the sign-typo finding) — the negative sign would give ~1e-11 min.
    r = ox.massoud_rate_constants(1000.0, "100")
    assert r.B == pytest.approx(277.0, rel=0.02)
    assert r.B_over_A == pytest.approx(0.793, rel=0.02)
    assert r.K1 == pytest.approx(584.0, rel=0.02)
    assert r.K2 == pytest.approx(351.0, rel=0.02)
    assert r.tau1 == pytest.approx(1.20, rel=0.02)
    assert r.tau2 == pytest.approx(7.50, rel=0.02)
    assert r.A == pytest.approx(r.B / r.B_over_A)


def test_massoud_reproduces_the_dissertation_growth_curve():
    # Hollauer's own Fig. 2.19 consistency point: (100), 1000 °C, 20 min, bare → ≈ 23 nm by the
    # closed form (the figure shows ~25 nm with its ~1 nm native seed). The check that the pinned
    # tables + positive-τ reading reproduce the source's own plotted output. Loose band.
    x = ox.oxide_thickness_massoud(20.0, ox.massoud_rate_constants(1000.0, "100"))
    assert 0.021 < x < 0.026                          # µm — ~23.3 nm


def test_massoud_enhancement_is_the_headline_thin_dry_burst():
    # The promoted scope edge, quantified: for the Phase-4 GATE RECIPE (dry 1000 °C / 20 min) the
    # Massoud model grows ~1.5× the oxide of the SAME linear-parabolic law without the burst —
    # and meaningfully more than the v1 plain-DG-1965 path predicted (the chain's payoff input
    # was under-predicted). Both contrasts asserted loosely.
    r = ox.massoud_rate_constants(1000.0, "100")
    x_massoud = ox.oxide_thickness_massoud(20.0, r)
    x_same_BA = ox.oxide_thickness(20.0 / 60.0, r.B * ox._NM2_MIN_TO_UM2_HR, r.A / ox.NM_PER_UM)
    assert 1.3 < x_massoud / x_same_BA < 1.8          # the burst itself (same B, A)
    x_v1 = ox.grow_oxide("dry", 1000.0, 20.0).t_ox
    assert x_massoud > 1.4 * x_v1                     # vs the v1 chain's prediction


def test_massoud_refuses_outside_the_cited_fit_range():
    # Refuse-don't-extrapolate: the cited fit is dry O₂, 800–1000 °C, (100)/(111)/(110).
    with pytest.raises(ValueError):
        ox.massoud_rate_constants(799.0, "100")
    with pytest.raises(ValueError):
        ox.massoud_rate_constants(1001.0, "100")
    with pytest.raises(ValueError):
        ox.massoud_rate_constants(900.0, "211")
    # The boundary temperatures themselves are in range.
    assert ox.massoud_rate_constants(800.0).B > 0
    assert ox.massoud_rate_constants(1000.0).B > 0


# Analytical limit (tight): the closed form, its identity, and its seams ---------------------
def test_massoud_closed_form_satisfies_the_integrated_identity():
    # The v1.1 exact anchor: x² + A·x = B·t + M₁(1−e^{−t/τ₁}) + M₂(1−e^{−t/τ₂}) + (x_i²+A·x_i)
    # to machine precision (pure algebra), at several times, orientations, and with a seed.
    for orientation in ("100", "111", "110"):
        r = ox.massoud_rate_constants(950.0, orientation)
        for t in (0.5, 5.0, 50.0):
            for xi in (0.0, 0.002):                   # bare + a 2 nm native seed
                x_nm = ox.oxide_thickness_massoud(t, r, x_initial=xi) * ox.NM_PER_UM
                xi_nm = xi * ox.NM_PER_UM
                rhs = (r.B * t + r.M1 * (1.0 - math.exp(-t / r.tau1))
                       + r.M2 * (1.0 - math.exp(-t / r.tau2)) + xi_nm**2 + r.A * xi_nm)
                assert x_nm**2 + r.A * x_nm == pytest.approx(rhs, rel=1e-12)


def test_massoud_with_zero_enhancement_is_exactly_deal_grove():
    # The degenerate-recovery seam: K₁ = K₂ = 0 collapses the closed form onto the plain
    # Deal–Grove solution with the same B, A — the correction is purely additive machinery.
    import dataclasses
    r = ox.massoud_rate_constants(1000.0, "100")
    r0 = dataclasses.replace(r, K1=0.0, K2=0.0)
    for t_min in (5.0, 60.0, 240.0):
        x_massoud = ox.oxide_thickness_massoud(t_min, r0)
        x_dg = ox.oxide_thickness(t_min / 60.0, r.B * ox._NM2_MIN_TO_UM2_HR, r.A / ox.NM_PER_UM)
        assert x_massoud == pytest.approx(x_dg, rel=1e-12)


def test_massoud_ode_integration_recovers_the_closed_form():
    # The analytic↔ODE consistency leg (the v1.1 twin of the plain model's): integrating the
    # time-dependent rate (B + K₁e^{−t/τ₁} + K₂e^{−t/τ₂})/(A+2x) reproduces the closed form.
    r = ox.massoud_rate_constants(1000.0, "100")
    t, x_ode = ox.integrate_massoud_ode(30.0, r, n_eval=100)
    x_exact = ox.oxide_thickness_massoud(t, r)
    interior = t > 0
    rel = np.abs(x_ode[interior] - x_exact[interior]) / x_exact[interior]
    assert np.max(rel) < 1e-6


def test_massoud_burst_saturates_onto_pure_linear_parabolic():
    # The anomaly is a FINITE transient: for t ≫ τ₂ the quadratic invariant's extra dose
    # saturates at exactly M₁+M₂ (nm²) and the growth rate relaxes onto the plain B/(A+2x) —
    # "the growth becomes pure linear-parabolic" (the ~25 nm ceiling, in time form).
    r = ox.massoud_rate_constants(1000.0, "100")
    t_late = 300.0                                    # ≫ τ₂ ≈ 7.5 min
    x_nm = ox.oxide_thickness_massoud(t_late, r) * ox.NM_PER_UM
    offset = x_nm**2 + r.A * x_nm - r.B * t_late
    assert offset == pytest.approx(r.M1 + r.M2, rel=1e-9)
    x_um = x_nm / ox.NM_PER_UM
    plain = r.B / (r.A + 2.0 * x_nm)
    assert ox.massoud_growth_rate(x_um, t_late, r) == pytest.approx(plain, rel=1e-9)


def test_massoud_seed_and_time_edges():
    # τ-machinery analogue: at t = 0 the closed form returns the seed exactly; negative time raises.
    r = ox.massoud_rate_constants(900.0, "100")
    assert ox.oxide_thickness_massoud(0.0, r, x_initial=0.005) == pytest.approx(0.005, rel=1e-12)
    with pytest.raises(ValueError):
        ox.oxide_thickness_massoud(-1.0, r)
    # Monotone in temperature across the cited range (sanity on the combined Arrhenius set).
    assert (ox.oxide_thickness_massoud(20.0, ox.massoud_rate_constants(1000.0))
            > ox.oxide_thickness_massoud(20.0, ox.massoud_rate_constants(800.0)))


# Conservation: the moving-boundary bookkeeping is growth-law-independent --------------------
def test_massoud_growth_keeps_the_044_bookkeeping():
    # The 0.44 Si-consumption mass balance carries over unchanged — it books the Si→SiO₂
    # number-density ratio, not the rate law. grow_oxide_massoud closes it exactly.
    g = ox.grow_oxide_massoud(1000.0, 20.0)
    assert g.model == "massoud" and g.ambient == "dry"
    assert g.si_consumed == pytest.approx(0.44 * g.t_ox)
    assert g.si_consumed + g.oxide_above_original_surface == pytest.approx(g.t_ox, rel=1e-12)
    # And the bundled (reporting) rate constants carry the µm-hr display units coherently.
    assert g.rates.A == pytest.approx(g.rates.B / g.rates.B_over_A)
