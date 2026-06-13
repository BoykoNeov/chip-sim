"""Wafer-prep validation: the defect-limited yield triad + the geometry bookkeeping (plan §7).

No engine underneath — the yield law is a closed form (like Deal–Grove / Scheil / the compact
``V_t``) — so these tests carry the whole triad:

* **Analytical limit.** ``Y(0)=1`` **exactly** (the one bit-exact anchor) + the negative-binomial
  → Poisson convergent limit as ``α→∞`` (a tolerance, not bit-for-bit) + clustering raises yield.
* **Conservation / identity (tight).** Area additivity ``Y(A₁+A₂) = Y(A₁)·Y(A₂)`` and the
  ``Y = exp(−λ)``, ``λ = D₀·A`` rate identity (the Poisson rate the game's placement converges to).
* **Benchmark (loose).** The cited Murphy (1964) Poisson / Stapper negative-binomial **forms**, an
  illustrative ``D₀`` band (development ≫ production), and the geometry **relations** (removal eats
  thickness, CMP reduces TTV) — magnitudes flagged, not asserted.

The **stochastic** placement and its Monte-Carlo convergence to ``exp(−D₀A)`` live in the game layer
(``fab_game/tests/test_defects.py``) — no RNG here (this repo is flake-sensitive; the deterministic
identity, area additivity, stands in for it on the physics side).
"""
import numpy as np
import pytest

from chip import wafer_prep as wp


# --------------------------------------------------------------------------- #
# Analytical limit: Y(0)=1 exact, NB→Poisson as α→∞, clustering raises yield
# --------------------------------------------------------------------------- #
def test_zero_defects_yields_unity_exactly():
    # The one bit-exact anchor: no defects (or zero area) → perfect yield, to the last bit.
    assert wp.poisson_yield(0.0, 10.0) == 1.0
    assert wp.poisson_yield(0.5, 0.0) == 1.0
    assert wp.negative_binomial_yield(0.0, 10.0, alpha=3.0) == 1.0
    assert wp.negative_binomial_yield(0.5, 0.0, alpha=3.0) == 1.0


def test_negative_binomial_converges_to_poisson_as_alpha_grows():
    # (1 + D₀A/α)^(−α) → exp(−D₀A) as α→∞ — a *convergent* limit, asserted to a tolerance (NOT
    # bit-for-bit; unlike Czochralski's k→1, this is a numerical limit, not anything**0==1).
    D0, A = 0.5, 12.0
    poisson = wp.poisson_yield(D0, A)
    approaching = [wp.negative_binomial_yield(D0, A, alpha=a) for a in (10.0, 1e3, 1e6, 1e9)]
    gaps = [abs(y - poisson) for y in approaching]
    assert gaps == sorted(gaps, reverse=True)          # monotonically closing on Poisson
    assert wp.negative_binomial_yield(D0, A, alpha=1e9) == pytest.approx(poisson, rel=1e-6)


def test_clustering_raises_yield_above_poisson():
    # Finite α (clustered defects) is ALWAYS ≥ the Poisson yield: clustering concentrates defects on
    # fewer dies → more zero-defect dies. Stronger clustering (smaller α) → higher yield.
    D0, A = 0.5, 12.0
    poisson = wp.poisson_yield(D0, A)
    y_weak = wp.negative_binomial_yield(D0, A, alpha=10.0)
    y_strong = wp.negative_binomial_yield(D0, A, alpha=1.0)
    assert y_strong > y_weak > poisson


def test_negative_binomial_rejects_nonpositive_alpha():
    with pytest.raises(ValueError):
        wp.negative_binomial_yield(0.5, 10.0, alpha=0.0)


# --------------------------------------------------------------------------- #
# Conservation / identity (tight): area additivity + the λ = D₀·A rate identity
# --------------------------------------------------------------------------- #
def test_poisson_yield_is_multiplicative_in_area():
    # Y(A₁+A₂) = Y(A₁)·Y(A₂): a die of combined area kills exactly as two independent sub-dies. This
    # multiplicativity is what makes exp(−D₀A) the *only* defect-independent law (approx, not == —
    # exp(a+b) vs exp(a)·exp(b) differ in the last bits).
    D0, A1, A2 = 0.3, 7.0, 11.0
    assert wp.poisson_yield(D0, A1 + A2) == pytest.approx(
        wp.poisson_yield(D0, A1) * wp.poisson_yield(D0, A2))


def test_yield_is_exp_of_the_expected_count():
    # Y = exp(−λ), λ = D₀·A — the Poisson rate the stochastic placement must converge to.
    D0, A = 0.4, 9.0
    lam = wp.expected_killer_defects(D0, A)
    assert lam == pytest.approx(D0 * A)
    assert wp.poisson_yield(D0, A) == pytest.approx(np.exp(-lam))


def test_yield_decreases_with_density_and_area():
    # More defects, or more area to catch them on → strictly lower yield (monotone in both).
    A = 10.0
    D = np.array([0.0, 0.05, 0.15, 0.5])
    y = wp.poisson_yield(D, A)
    assert np.all(np.diff(y) < 0.0)
    D0 = 0.2
    areas = np.array([1.0, 5.0, 16.0, 40.0])
    assert np.all(np.diff(wp.poisson_yield(D0, areas)) < 0.0)


# --------------------------------------------------------------------------- #
# Benchmark (loose): the illustrative D₀ band + the Murphy α≈4.2 landmark
# --------------------------------------------------------------------------- #
def test_defect_density_band_orders_cleanest_lowest():
    # FLAGGED illustrative levels: a clean production line carries far fewer killer defects than a
    # dirty development line → higher yield at the same die area. Only the ordering is asserted.
    bands = wp.DEFECT_DENSITY_BANDS
    assert 0.0 < bands["production"] < bands["pilot"] < bands["development"]
    A = 16.0
    assert wp.poisson_yield(bands["production"], A) > wp.poisson_yield(bands["development"], A)


def test_murphy_triangular_is_a_moderate_clustering_landmark():
    # Murphy's triangular-f(D) model ≈ negative-binomial α ≈ 4.2 — a named landmark: it sits between
    # Poisson (α→∞) and strong clustering (α≈1). Not an asserted magnitude, just the ordering.
    D0, A = 0.5, 16.0
    y_murphy = wp.negative_binomial_yield(D0, A, alpha=4.2)
    assert wp.poisson_yield(D0, A) < y_murphy < wp.negative_binomial_yield(D0, A, alpha=1.0)


# --------------------------------------------------------------------------- #
# Geometry bookkeeping (exact): removal eats thickness, CMP reduces TTV, bow carries
# --------------------------------------------------------------------------- #
def test_prep_removes_thickness_and_improves_ttv():
    g = wp.prep_geometry(incoming_thickness_um=800.0, slice_ttv_um=2.0,
                         removal_um=60.0, ttv_improvement=0.85)
    assert g.thickness_um == pytest.approx(740.0)          # 800 − 60 removed
    assert g.ttv_um == pytest.approx(2.0 * 0.15)           # CMP improves TTV by 85 %
    assert g.ttv_um < 2.0


def test_bow_is_carried_through_cmp_does_not_fix_it():
    # Bow is set at slicing/crystal; CMP planarizes TTV but does NOT correct bow (anneal/edge-grind
    # are out of scope) — so bow_out == slice_bow_um exactly.
    g = wp.prep_geometry(slice_bow_um=30.0, removal_um=40.0)
    assert g.bow_um == 30.0


def test_more_removal_leaves_a_thinner_wafer():
    light = wp.prep_geometry(incoming_thickness_um=800.0, removal_um=40.0)
    heavy = wp.prep_geometry(incoming_thickness_um=800.0, removal_um=120.0)
    assert heavy.thickness_um < light.thickness_um


def test_no_ttv_improvement_leaves_ttv_unchanged():
    g = wp.prep_geometry(slice_ttv_um=2.0, ttv_improvement=0.0)
    assert g.ttv_um == pytest.approx(2.0)


def test_over_removal_raises():
    # A re-polish that eats the whole wafer is unphysical — the limit the re-polish rework hits.
    with pytest.raises(ValueError):
        wp.prep_geometry(incoming_thickness_um=50.0, removal_um=60.0)
    with pytest.raises(ValueError):
        wp.prep_geometry(ttv_improvement=1.5)
