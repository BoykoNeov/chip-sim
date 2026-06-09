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

The constants ``C, Ea`` are cited Deal–Grove data (deal-grove-oxidation-source memory note), NOT fit
to any thickness here — what makes the thickness benchmark a cross-check, not a tautology.
"""
import math

import numpy as np
import pytest

from projects.chip import oxidation as ox


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


def test_thin_dry_massoud_regime_is_a_named_scope_edge():
    # Scope edge, NAMED not modeled: v1 is plain Deal–Grove. At x→0 its dry growth rate is exactly the
    # finite linear rate B/A — it has NO Massoud enhancement term, so it UNDER-predicts the real
    # rapid initial growth of thin (<~30 nm) dry oxide. We pin that v1 is the plain model (the honest
    # ceiling), exactly as carburize pins the constant-D erfc as its named simplification.
    r = ox.oxide_rate_constants("dry", 1000.0, "100")
    assert ox.growth_rate(0.0, r.B, r.A) == pytest.approx(r.B_over_A, rel=1e-12)   # finite B/A, no Massoud burst
    # Reassurance that this is the regime that matters: a short dry oxidation lands in the thin band
    # where the anomaly lives (tens of nm), i.e. where the named limitation actually bites.
    thin = ox.grow_oxide("dry", 1000.0, t_minutes=20.0)
    assert thin.t_ox_nm < 40.0


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
