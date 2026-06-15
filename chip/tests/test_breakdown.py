"""Junction avalanche breakdown validation — the breakdown triad (device-targets slice 2).

No engine underneath — the breakdown is the cited ionization integral over the cylindrical depletion field,
a closed-form law plus a 1-D root-find (like the compact ``V_t`` / the SRH lifetime / Deal–Grove) — so these
tests carry the whole triad:

* **Analytical limit (tight).** The plane-parallel closed form reproduces the cited ``BV_pp ∝ N_B^(−3/4)``
  law (and the cited critical field ``E_crit ~3–5e5 V/cm``), *both* falling out of the one ionization
  coefficient; the avalanche criterion ``∫α dx = 1`` closes on the triangular field at that ``E_m``. The
  cylindrical solve **reduces to that planar ceiling** as the junction deepens (the curvature ratio → 1).
* **Monotonicity (by construction).** ``BV`` rises with junction depth ``x_j`` (toward the ceiling) and
  falls with body doping ``N_B`` — the two cited directions, asserted across the physical junction range.
* **Benchmark (loose).** The cited Sze worked point: a Si one-sided abrupt junction at ``N_B = 1e15`` with
  ``r_j = 1 µm`` breaks down at a curvature ratio ≈ 0.24 (~80 V vs ~330 V plane-parallel,
  [[avalanche-breakdown-source]]). The model independently lands the **ratio** at ≈ 0.24; the ionization
  coefficient ``a``, ``m`` are flagged literature values, only the form + the N^(−3/4) trend are cited.

Non-circularity: the curvature reduction is *derived* (the ionization integral over cylindrical Poisson, no
empirical fit), so reproducing Sze's ≈0.24 ratio is a genuine cross-check, not a refit; the ``a``/``m``
magnitudes are flagged, never anchored.
"""
import numpy as np
import pytest

from chip import breakdown as bd


# --------------------------------------------------------------------------- #
# Analytical limit (tight): the plane-parallel law + the avalanche criterion
# --------------------------------------------------------------------------- #
def test_plane_parallel_follows_the_cited_N_to_the_minus_three_quarters_law():
    # BV_pp ∝ N_B^(−3/4): each decade of doping drops BV_pp by 10^(3/4) ≈ 5.62× (the cited Baliga law).
    for N in (1.0e15, 1.0e16, 1.0e17):
        ratio = bd.plane_parallel_breakdown(N) / bd.plane_parallel_breakdown(10.0 * N)
        assert ratio == pytest.approx(10.0 ** 0.75, rel=1e-9)
    # And the absolute magnitude tracks the cited 5.34e13·N^(−3/4) V to ~10 % (the planar number is loose).
    for N in (1.0e15, 1.0e16, 1.0e17):
        assert bd.plane_parallel_breakdown(N) == pytest.approx(5.34e13 * N ** -0.75, rel=0.10)


def test_critical_field_is_the_cited_few_times_1e5_range():
    # The self-consistent peak field at planar breakdown — the cited Si critical field, ~3e5 rising slowly.
    assert bd.plane_parallel_field(1.0e15) == pytest.approx(3.0e5, rel=0.10)
    assert 3.0e5 < bd.plane_parallel_field(1.0e17) < 6.0e5
    # Weak N^(1/8) dependence: 100× doping lifts E_crit only ~1.78× (the cited weak field-vs-doping trend).
    assert bd.plane_parallel_field(1.0e17) / bd.plane_parallel_field(1.0e15) == pytest.approx(100.0 ** 0.125, rel=1e-9)


def test_avalanche_criterion_closes_on_the_triangular_field():
    # The planar peak field E_m is defined by ∫₀^W α(E) dx = 1 on the triangular field E = E_m(1−x/W):
    # a·E_m^m·W/(m+1) = 1. Recompute that ionization integral and confirm it is unity (the criterion closes).
    N = 1.0e16
    E_m = bd.plane_parallel_field(N)
    W = bd.EPS_SI * E_m / (bd.Q_ELEMENTARY * N)              # depletion width at breakdown (Poisson)
    x = np.linspace(0.0, W, 20001)
    alpha = bd.A_IONIZATION * (E_m * (1.0 - x / W)) ** bd.M_IONIZATION   # α(E) along the triangular field
    assert np.trapezoid(alpha, x) == pytest.approx(1.0, rel=1e-3)


def test_deep_junction_reduces_to_the_plane_parallel_ceiling():
    # As x_j grows the cylindrical solve approaches the planar ceiling from below (curvature ratio → 1):
    # the analytic-limit seam. A 5 µm junction (≫ the physical sub-µm range) is already within ~4 %.
    N = 1.0e17
    bv_pp = bd.plane_parallel_breakdown(N)
    jb = bd.junction_breakdown(N, 5.0)
    assert jb.bv < jb.bv_pp                                  # always below the ceiling (curvature only reduces)
    assert jb.bv_pp == pytest.approx(bv_pp)
    assert 0.96 < jb.curvature_ratio < 1.0                   # converged to within a few %


# --------------------------------------------------------------------------- #
# Monotonicity (by construction): the two cited directions
# --------------------------------------------------------------------------- #
def test_breakdown_rises_with_junction_depth():
    # A deeper junction relaxes curvature crowding → higher BV (the slice-2 axis: the drive-in sets x_j).
    N = 1.0e17
    bvs = [bd.junction_breakdown(N, x).bv for x in (0.05, 0.10, 0.15, 0.25, 0.5, 1.0, 2.0)]
    assert all(b1 < b2 for b1, b2 in zip(bvs, bvs[1:]))      # strictly increasing over the physical range
    assert all(b < bd.plane_parallel_breakdown(N) for b in bvs)   # all under the planar ceiling


def test_breakdown_falls_with_body_doping():
    # A lighter body → higher BV (the slice-3 axis: high-resistivity substrate for HV), at fixed depth.
    bvs = [bd.junction_breakdown(N, 0.15).bv for N in (3.0e16, 1.0e17, 3.0e17, 1.0e18)]
    assert all(b1 > b2 for b1, b2 in zip(bvs, bvs[1:]))      # strictly decreasing in N_B


def test_breakdown_decouples_from_threshold_voltage():
    # THE slice-2 point (advisor): two junctions at the SAME body doping (→ same V_t-relevant N_A) but
    # different depth have DIFFERENT BV — so BV is an axis independent of the substrate/V_t, set by the
    # diffusion drive-in. (V_t reads N_A + t_ox, neither of which is x_j.)
    N = 1.0e17
    shallow = bd.junction_breakdown(N, 0.09)
    deep = bd.junction_breakdown(N, 0.27)
    assert shallow.N_B == deep.N_B                           # identical body doping → identical V_t
    assert deep.bv > shallow.bv * 1.2                        # yet a materially higher breakdown


# --------------------------------------------------------------------------- #
# Benchmark (loose): the cited Sze curvature-ratio point + the flagged coefficient
# --------------------------------------------------------------------------- #
def test_sze_curvature_ratio_anchor():
    # Sze's worked Si one-sided abrupt junction: N_B = 1e15, r_j = 1 µm → BV ≈ 80 V vs ≈ 330 V plane-parallel
    # → curvature ratio ≈ 0.24. The DERIVED ratio (ionization integral over cylindrical Poisson, no fit)
    # lands there — the genuine cross-check. LOOSE: the ratio within ~15 %, the absolute BV within ~20 %.
    jb = bd.junction_breakdown(1.0e15, 1.0)
    assert jb.curvature_ratio == pytest.approx(0.24, abs=0.04)
    assert jb.bv == pytest.approx(80.0, rel=0.20)


def test_non_finite_inputs_raise_not_silently_mislead():
    # An UNRESOLVED junction gives x_j = nan (the profile never crosses N_B), which slips past a bare
    # `r_j <= 0` guard (nan comparisons are all False) — the function must reject it loudly, not fail to
    # bracket. Guards the device-step regression (an unresolved junction → no breakdown, screened upstream).
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError):
            bd.cylindrical_breakdown(1.0e17, bad)
        with pytest.raises(ValueError):
            bd.junction_breakdown(1.0e17, bad)


def test_ionization_coefficient_is_flagged_order_of_magnitude():
    # The Si effective ionization power law α = a·E^m (Baliga/Sze) — FLAGGED magnitudes, only the steep
    # high-field power and the order are asserted (the loose tier).
    assert bd.M_IONIZATION == 7
    assert 1.0e-36 < bd.A_IONIZATION < 1.0e-34
    # Steeply field-dependent: doubling the field raises α by 2^7 = 128× (why breakdown tracks the peak field).
    assert bd.ionization_coefficient(2.0e5) / bd.ionization_coefficient(1.0e5) == pytest.approx(128.0, rel=1e-9)
