"""Packaging validation: the back-end yield funnel — the seam + the multiplicativity identity.

No engine underneath — the cumulative (multiplicative) yield ``Y = Π yᵢ`` is a closed form (like
Deal–Grove / Scheil / the defect law) — so these tests carry the whole triad:

* **Analytical limit / seam (tight, bit-exact).** ``assembly_yield()`` over all-perfect steps is
  **exactly 1.0**, and a single step returns *itself* bit-for-bit (the identity the G6 game wiring
  rides), exactly as Czochralski's ``k → 1`` and wafer-prep's ``Y(0) = 1``.
* **Conservation / identity (multiplicativity — a genuine identity, like area-additivity).**
  ``Y(A ∪ B) = Y(A)·Y(B)`` (regrouping the steps is the independence of the stages) and ``n`` steps
  of ``y`` give ``yⁿ``. *Honest caveat (the §7 discipline):* the algebra is structural — that ``Π yᵢ``
  is the only independent-composition law is validated by the **realization** (the per-die Bernoulli →
  ``Π yᵢ`` convergence, asserted in the game layer, ``fab_game/tests``), not by the arithmetic here.
* **Benchmark (loose).** The :data:`ASSEMBLY_STEPS` step-yield band orderings + the monotonicity
  (more steps / a worse step → strictly lower yield) — magnitudes flagged, never asserted.

The stochastic per-die assembly realization and the binning partition live in the game layer
(``fab_game/tests``) — no RNG here.
"""
import pytest

from chip import packaging as pkg


# --------------------------------------------------------------------------- #
# Analytical limit / seam (tight, bit-exact): perfect funnel = identity
# --------------------------------------------------------------------------- #
def test_empty_and_perfect_funnel_is_exactly_one():
    # An empty funnel loses nothing; an all-perfect funnel loses nothing — exactly 1.0 (the seam).
    assert pkg.assembly_yield() == 1.0
    assert pkg.assembly_yield(1.0, 1.0, 1.0, 1.0) == 1.0


def test_single_step_returns_itself_bit_for_bit():
    # A one-step funnel is the identity on its own yield (== , not approx — the seam is exact).
    for y in (0.9942, 0.5, 1.0, 0.0):
        assert pkg.assembly_yield(y) == y


def test_default_steps_are_a_high_but_imperfect_yield():
    # The flagged default back end loses a little (every step < 1) — a high but sub-unity funnel.
    y = pkg.assembly_yield(*pkg.ASSEMBLY_STEPS.values())
    assert 0.97 < y < 1.0                                      # high-yield mature back end, but not perfect


# --------------------------------------------------------------------------- #
# Conservation / identity (multiplicativity — the independence law)
# --------------------------------------------------------------------------- #
def test_multiplicativity_over_a_partition():
    # Y(A ∪ B) = Y(A)·Y(B): regrouping the steps does not change the funnel (the independence identity,
    # the packaging analogue of wafer-prep's area-additivity Y(A₁+A₂)=Y(A₁)·Y(A₂)).
    a, b, c, d = 0.995, 0.997, 0.994, 0.998
    assert pkg.assembly_yield(a, b, c, d) == pytest.approx(
        pkg.assembly_yield(a, b) * pkg.assembly_yield(c, d))
    # And splitting one step of yield y² into two steps of yield y is the same total.
    assert pkg.assembly_yield(0.9 * 0.9) == pytest.approx(pkg.assembly_yield(0.9, 0.9))


def test_n_identical_steps_give_y_to_the_n():
    # n steps each at yield y → yⁿ (the funnel of a repeated operation).
    y, n = 0.99, 5
    assert pkg.assembly_yield(*([y] * n)) == pytest.approx(y ** n)


def test_expected_packaged_is_n_times_the_yield():
    # The expected shipped count out of n good dies is n·Π yᵢ — the rate the game's Bernoulli
    # realization converges to (the non-circular leg, packaging's analogue of λ = D₀·A).
    n, ys = 21, (0.99, 0.98)
    assert pkg.expected_packaged(n, *ys) == pytest.approx(n * pkg.assembly_yield(*ys))
    assert pkg.expected_packaged(0, 0.5) == 0.0


# --------------------------------------------------------------------------- #
# Benchmark (loose): the flagged step bands + monotonicity (orderings only)
# --------------------------------------------------------------------------- #
def test_adding_a_step_or_worsening_one_lowers_the_yield():
    # Monotone: a longer funnel (one more sub-unity step) yields strictly less, and a worse step
    # lowers it further. Only the direction is asserted — the magnitudes are house.
    base = pkg.assembly_yield(0.99, 0.99)
    longer = pkg.assembly_yield(0.99, 0.99, 0.99)              # one more lossy step
    assert longer < base
    worse = pkg.assembly_yield(0.99, 0.90)                     # a worse second step
    assert worse < base


def test_assembly_step_band_is_high_yield_and_named():
    # FLAGGED illustrative levels — only that each is a high (<1) survival probability and the bond is
    # the lossiest (the busiest back-end step) is asserted; the numbers are house.
    s = pkg.ASSEMBLY_STEPS
    assert set(s) == {"dice", "attach", "bond", "encapsulate"}
    assert all(0.9 < y < 1.0 for y in s.values())
    assert s["bond"] == min(s.values())                       # wire-bond is the lossiest step


# --------------------------------------------------------------------------- #
# Error guards (the physical limits the game's knobs run into)
# --------------------------------------------------------------------------- #
def test_non_probability_yield_raises():
    with pytest.raises(ValueError):
        pkg.assembly_yield(1.5)
    with pytest.raises(ValueError):
        pkg.assembly_yield(0.99, -0.1)
    with pytest.raises(ValueError):
        pkg.expected_packaged(-1, 0.99)
