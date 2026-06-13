"""Silicon-purification validation: the zone-refining segregation triad (plan §7, §5a).

No engine underneath — the Pfann single-pass profile is a closed form (like Deal–Grove / Scheil /
the compact ``V_t``) — so these tests carry the whole triad:

* **Analytical limit (tight) — the ``k→1`` no-purification limit + the scrubbing identity.** At
  ``k = 1`` the profile is the constant ``C_0`` **bit-for-bit** (``(1−k) = 0`` exactly); the leading
  solid is ``C(0) = k·C_0`` (the scrubbing fraction) and ``C(u) → C_0`` as ``u → ∞`` (steady state).
* **Conservation (tight, *reframed*) — the swept-out solute, not a recovered dose.** The closed-form
  deficit ``∫₀^u (C_0 − C) du' = (C_0/k)(1−k)(1−e^{−k u})`` matches direct quadrature, and ``∫ C du``
  over the swept ingot falls **short** of ``C_0·u`` by exactly that deficit (the single-pass formula
  omits the final-zone pile-up — the named scope edge; "mass recovers ``C_0``" is *not* claimed).
* **Benchmark (loose) — the cited Trumbore ``k`` (reused from czochralski) + the grade contrast.** The
  tiny-``k`` metals are scrubbed orders of magnitude while ``B`` (``k ≈ 0.8``) is barely touched — the
  segregation-purification contrast, straight from the one cited ``k`` table. Grade vectors are flagged.

Non-circularity: the segregation ``k`` is cited equilibrium data (Trumbore 1960), reused from
:mod:`chip.czochralski` — not duplicated, not fit to any device; the ``Na → Q_ox`` consequence
magnitude is flagged calibrated (loose), not asserted with the segregation anchors.
"""
import numpy as np
import pytest

from chip import czochralski as cz
from chip import purification as pur
from chip.junction import Q_ELEMENTARY


# --------------------------------------------------------------------------- #
# Benchmark: the cited k is REUSED from czochralski (not duplicated), + the grade contrast
# --------------------------------------------------------------------------- #
def test_segregation_k_is_the_one_reused_czochralski_table():
    # The single source of truth: purification imports czochralski's SEGREGATION_K (the advisor's
    # "reuse, don't duplicate" — a second table would drift). Same object, same cited values.
    assert pur.SEGREGATION_K is cz.SEGREGATION_K
    assert pur.segregation_coefficient is cz.segregation_coefficient
    # Na was added to that one table as the device-poisoning mobile ion — a strong segregator (k ≪ 1).
    assert 0.0 < cz.SEGREGATION_K["Na"] < 0.1


def test_feedstock_grades_get_dirtier_from_egs_to_mgs():
    # FLAGGED house vectors — only the *contrast* is asserted: MGS ≫ solar ≫ EGS for every species,
    # and "clean" is the idealized pristine baseline (all zero — the seam default).
    assert pur.FEEDSTOCK_GRADES["clean"].is_clean
    for sp in ("Na", "Fe", "Cu"):
        egs = getattr(pur.FEEDSTOCK_GRADES["EGS"], sp)
        sol = getattr(pur.FEEDSTOCK_GRADES["solar"], sp)
        mgs = getattr(pur.FEEDSTOCK_GRADES["MGS"], sp)
        assert egs < sol < mgs


# --------------------------------------------------------------------------- #
# Analytical limit (tight): k→1 uniform (bit-exact) + scrubbing identity + steady state
# --------------------------------------------------------------------------- #
def test_k_to_one_is_no_purification_bit_for_bit():
    # k=1: C(u) = C_0·[1 − (1−1)·e^…] = C_0 for every u, to machine precision ((1−k)=0 exactly).
    u = np.linspace(0.0, 12.0, 60)
    profile = pur.pfann_profile(u, C0=1.0e18, k=1.0)
    assert np.allclose(profile, 1.0e18, rtol=0.0, atol=0.0)        # bit-for-bit uniform


def test_leading_end_is_fraction_k_the_scrubbing_identity():
    # C(0)/C_0 = k (the leading solid gets only fraction k of the charge). A tiny-k metal is scrubbed
    # ~5 orders in one pass at the leading end; B (k≈0.8) is barely purified — the "why refining works"
    # result, straight from the k table. (Good to ~1e-12, not bit-exact: the 1−(1−k) form loses a few
    # ULPs for tiny k — unlike Scheil's exact (1−0)^… seed; this is the loose/benchmark leg anyway.)
    C0 = 1.0e18
    for d in ("B", "Fe", "Na"):
        k = cz.SEGREGATION_K[d]
        assert pur.pfann_profile(0.0, C0, k) == pytest.approx(k * C0, rel=1e-9)
    # ~5 orders of magnitude contrast (Fe scrubbed hard, B not).
    assert pur.pfann_profile(0.0, C0, cz.SEGREGATION_K["B"]) \
        / pur.pfann_profile(0.0, C0, cz.SEGREGATION_K["Fe"]) > 1e4


def test_zone_saturates_to_C0_far_from_the_start():
    # As the zone sweeps it enriches; far from the start the solid freezes at C_0 (solid out = liquid in).
    C0 = 1.0e18
    for k in (0.35, 0.80):
        assert pur.pfann_profile(40.0, C0, k) == pytest.approx(C0, rel=1e-6)
    # Monotonic rise toward C_0 for k<1 (rejected solute enriches the zone).
    prof = pur.pfann_profile(np.linspace(0.0, 10.0, 50), C0, 0.35)
    assert np.all(np.diff(prof) > 0.0)


# --------------------------------------------------------------------------- #
# Conservation (tight, reframed): the swept-out solute closed form vs quadrature
# --------------------------------------------------------------------------- #
def test_swept_solute_closed_form_matches_quadrature():
    # The closed-form deficit ∫(C_0−C)du equals direct quadrature, for a near-unity (B) and a strong
    # (Fe) segregator — the conservation (machinery) leg.
    C0 = 1.0e18
    for k in (cz.SEGREGATION_K["B"], cz.SEGREGATION_K["Fe"]):
        u = np.linspace(0.0, 8.0, 800001)
        C = pur.pfann_profile(u, C0, k)
        numeric = np.trapezoid(C0 - C, u)
        closed = pur.pfann_swept_solute(8.0, C0, k)
        assert closed == pytest.approx(numeric, rel=1e-5)


def test_integral_falls_short_of_the_charge_by_exactly_the_deficit():
    # The honest conservation statement: ∫C du over the swept ingot is SHORT of C_0·u — by exactly the
    # swept-out solute (carried into the unmodelled end-zone pile-up, the named scope edge). NOT a
    # "mass recovers C_0" identity (cf. Scheil's ∫₀¹ = C_0).
    C0, k, U = 1.0e18, 0.35, 6.0
    u = np.linspace(0.0, U, 600001)
    C = pur.pfann_profile(u, C0, k)
    shortfall = C0 * U - np.trapezoid(C, u)
    assert shortfall > 0.0                                          # it falls short (depleted leading end)
    assert shortfall == pytest.approx(pur.pfann_swept_solute(U, C0, k), rel=1e-5)
    # The full-sweep limit of the deficit is (C_0/k)(1−k).
    assert pur.pfann_swept_solute(1e3, C0, k) == pytest.approx((C0 / k) * (1.0 - k), rel=1e-6)


# --------------------------------------------------------------------------- #
# zone_refine — the purification operation the game consumes (the contrast + the seam)
# --------------------------------------------------------------------------- #
def test_zone_refine_scrubs_metals_hard_but_barely_touches_boron():
    feed = pur.Contamination(Fe=1.0e18, B=1.0e17, Na=1.0e18)
    out = pur.zone_refine(feed, n_passes=1)
    # Single pass leaves each species at k·C_0 (the exact leading-end value).
    assert out.Fe == pytest.approx(feed.Fe * cz.SEGREGATION_K["Fe"], rel=1e-12)
    assert out.B == pytest.approx(feed.B * cz.SEGREGATION_K["B"], rel=1e-12)
    # Fe scrubbed ~5 orders, B barely moved → the contrast (the segregation-purification lesson).
    assert out.Fe / feed.Fe < 1e-4
    assert out.B / feed.B > 0.5


def test_zone_refine_clean_stays_clean_the_seam():
    # A clean feed stays clean for any k / n (0·k^n = 0) — the seam (a clean feedstock adds no
    # contamination, so the device demo is byte-for-byte the ideal-oxide value).
    assert pur.zone_refine(pur.Contamination(), n_passes=5).is_clean
    # n_passes = 0 is a no-op (no refining).
    feed = pur.FEEDSTOCK_GRADES["MGS"]
    assert pur.zone_refine(feed, n_passes=0) == feed
    # More passes scrub further (front-tracking k^n; n=1 exact, n>1 the flagged approximation).
    one = pur.zone_refine(feed, n_passes=1)
    two = pur.zone_refine(feed, n_passes=2)
    assert two.Na < one.Na < feed.Na


def test_net_doping_shift_is_residual_acceptor_minus_donor():
    # Residual B (acceptor) raises the p-channel doping; residual P (donor) lowers it.
    assert pur.Contamination(B=2.0e16, P=5.0e15).net_doping_shift == pytest.approx(1.5e16)
    assert pur.Contamination().net_doping_shift == 0.0


# --------------------------------------------------------------------------- #
# The Na → Q_ox consequence (flagged magnitude; the direction is the wired leg)
# --------------------------------------------------------------------------- #
def test_sodium_oxide_charge_is_positive_and_zero_when_clean():
    # Q_ox = q·N_Na·d_incorp (C/cm²): bulk Na → areal mobile-ion charge via the flagged incorporation
    # length. Positive (Na⁺) → a NEGATIVE V_FB/V_t shift (asserted in test_device). Clean → 0 (the seam).
    N_Na = 1.0e16
    q_ox = pur.sodium_oxide_charge(N_Na)
    assert q_ox == pytest.approx(Q_ELEMENTARY * N_Na * pur.NA_OXIDE_INCORPORATION_CM, rel=1e-12)
    assert q_ox > 0.0
    assert pur.sodium_oxide_charge(0.0) == 0.0
    # The flagged house length lands a residual ~1e16 cm⁻³ Na in the classic mobile-ion regime
    # (~1e11–1e12 cm⁻² areal → a ~0.1 V flat-band shift at a thin gate oxide).
    assert 1.0e11 < N_Na * pur.NA_OXIDE_INCORPORATION_CM < 1.0e12


# --------------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------------- #
def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        pur.pfann_profile(-0.5, 1.0e18, 0.35)        # zones must be ≥ 0
    with pytest.raises(ValueError):
        pur.zone_refine(pur.FEEDSTOCK_GRADES["MGS"], n_passes=-1)
    with pytest.raises(ValueError):
        pur.front_purity(0.35, n_passes=-1)
