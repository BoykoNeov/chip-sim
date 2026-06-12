"""Czochralski / Scheil validation: the front-of-line segregation triad (plan §7).

No engine underneath — the Scheil profile is a closed form (like Deal–Grove / the compact ``V_t``)
— so these tests carry the whole triad:

* **Analytical limit (tight) — the ``k→1`` uniform-doping limit + the exact seed-end value.** At
  ``k=1`` segregation vanishes (``C_s ≡ N_seed``) to machine precision; and ``C_s(0) = N_seed``
  **exactly** for any ``k`` (the seam the G2 harness rides).
* **Conservation (tight) — the solute mass balance.** The closed-form axial integral matches direct
  quadrature on ``[0, 0.9]`` and the analytic full-boule limit ``∫₀¹ C_s = N_seed/k = C_0`` (all the
  charged solute lands in the boule; the ``z→1`` divergence is integrable).
* **Benchmark (loose) — the cited Trumbore ``k`` + Masetti resistivity.** ``k`` values pinned to the
  source (B ≈ 0.80, P ≈ 0.35 verified); ``ρ = 1/(qμN)`` reuses the independent Masetti model
  (``~0.2 Ω·cm`` at ``1e17`` boron). The segregation *direction* (B barely moves, monotonic rise)
  and the metal-vs-dopant scrubbing contrast are asserted; the tail magnitudes are not.

Non-circularity: the segregation ``k`` is cited equilibrium data (Trumbore 1960), not fit to any
device; the resistivity ``μ(N)`` is the cited Masetti transport model (junction.py), independent of
any resistivity-vs-doping chart — so the resistivity is a cross-check, not a refit.
"""
import math

import numpy as np
import pytest

from chip import czochralski as cz


# --------------------------------------------------------------------------- #
# Benchmark: the cited Trumbore segregation coefficients (pinned)
# --------------------------------------------------------------------------- #
def test_segregation_coefficients_are_the_cited_values():
    # Trumbore (1960, BSTJ 39:205) equilibrium distribution coefficients. B and P are load-bearing
    # (verified against the source: B ≈ 0.80, P ≈ 0.35) — the substrate is boron, whose near-unity k
    # is the "barely segregates" lesson.
    assert cz.SEGREGATION_K["B"] == pytest.approx(0.80)
    assert cz.SEGREGATION_K["P"] == pytest.approx(0.35)
    assert cz.segregation_coefficient("B") == cz.SEGREGATION_K["B"]
    # Every shallow dopant has k < 1 (solute rejected into the melt → C_s rises down the boule).
    for d in ("B", "P", "As", "Sb"):
        assert 0.0 < cz.SEGREGATION_K[d] < 1.0
    # Metals segregate far harder than dopants (the purification contrast — order of magnitude only).
    assert cz.SEGREGATION_K["Fe"] < 1e-4 < cz.SEGREGATION_K["B"]
    with pytest.raises(KeyError):
        cz.segregation_coefficient("Xx")


# --------------------------------------------------------------------------- #
# Analytical limit (tight): the k→1 uniform limit + the exact seed-end seam
# --------------------------------------------------------------------------- #
def test_k_to_one_is_uniform_doping():
    # No segregation at k=1: C_s(z) ≡ N_seed for every z, to machine precision (anything**0 == 1).
    z = np.linspace(0.0, 0.95, 50)
    profile = cz.scheil_profile(z, N_seed=1.0e17, k=1.0)
    assert np.allclose(profile, 1.0e17, rtol=0.0, atol=0.0)       # bit-for-bit uniform


def test_seed_end_value_is_exact_for_any_k():
    # C_s(0) = N_seed EXACTLY for any k — (1-0)^(k-1) = 1.0, N_seed*1.0 == N_seed. The G2 seam:
    # 1e17 is > 2**53, so only an exact identity (not a k·C0/k round-trip) survives bit-for-bit.
    for k in (0.80, 0.35, 0.023, 1.0):
        assert cz.scheil_profile(0.0, N_seed=1.0e17, k=k) == 1.0e17


def test_k_less_than_one_rises_monotonically_down_the_boule():
    # For k<1 the rejected solute piles up → C_s strictly increases with z (and diverges as z→1).
    z = np.linspace(0.0, 0.95, 40)
    b = cz.scheil_profile(z, N_seed=1.0e15, k=cz.SEGREGATION_K["B"])
    assert np.all(np.diff(b) > 0.0)


# --------------------------------------------------------------------------- #
# Conservation (tight): the solute mass balance ∫₀¹ C_s dz = N_seed/k = C_0
# --------------------------------------------------------------------------- #
def test_cumulative_matches_quadrature_off_the_singularity():
    # The closed-form axial integral equals direct quadrature on [0, 0.9] (off the z→1 singular
    # endpoint), for both a near-unity (B) and a strong (Sb) segregator.
    for k in (cz.SEGREGATION_K["B"], cz.SEGREGATION_K["Sb"]):
        z = np.linspace(0.0, 0.9, 200001)                        # fine grid for trapezoid accuracy
        prof = cz.scheil_profile(z, N_seed=1.0e15, k=k)
        numeric = np.trapezoid(prof, z)
        closed = cz.scheil_cumulative(0.9, N_seed=1.0e15, k=k)
        assert closed == pytest.approx(numeric, rel=1e-5)


def test_full_boule_recovers_the_melt_concentration():
    # ∫₀¹ C_s dz = N_seed/k = C_0 — all the dopant charged into the melt ends up in the boule (the
    # mass-balance identity; finite despite the integrable z→1 divergence).
    N_seed, k = 1.0e15, cz.SEGREGATION_K["B"]
    C0 = cz.melt_concentration(N_seed, k)
    # The closed form at z→1: (N_seed/k)·(1 − 0) = N_seed/k.
    assert cz.scheil_cumulative(1.0 - 1e-12, N_seed, k) == pytest.approx(C0, rel=1e-9)
    assert C0 == pytest.approx(N_seed / k)
    assert C0 > N_seed                                            # k<1 → the melt is richer than the seed


def test_seed_is_fraction_k_of_the_melt_the_purification_lesson():
    # C_s(0)/C_0 = k EXACTLY — the seed end gets only fraction k of the melt average. A tiny-k metal
    # is scrubbed ~5 orders of magnitude at the seed; B (k≈0.8) is barely purified. The "why CZ
    # purifies" result, straight from the k table.
    for d in ("B", "Fe"):
        k = cz.SEGREGATION_K[d]
        C0 = cz.melt_concentration(1.0e15, k)
        assert cz.scheil_profile(0.0, 1.0e15, k) / C0 == pytest.approx(k)
    # The contrast is ~5 orders of magnitude (Fe scrubbed, B not).
    assert cz.SEGREGATION_K["B"] / cz.SEGREGATION_K["Fe"] > 1e4


# --------------------------------------------------------------------------- #
# Benchmark (loose): resistivity via the independent Masetti μ(N)
# --------------------------------------------------------------------------- #
def test_resistivity_of_a_substrate_is_in_the_textbook_band():
    # 1e17 boron → ρ ≈ 0.2 Ω·cm (the standard value); a lighter 1e15 substrate is ~13 Ω·cm. Loose
    # band — the magnitude is the Masetti μ(N) cross-check, not a tight anchor.
    rho_1e17 = cz.resistivity(1.0e17, "B")
    assert 0.1 < rho_1e17 < 0.5
    rho_1e15 = cz.resistivity(1.0e15, "B")
    assert 5.0 < rho_1e15 < 30.0


def test_resistivity_decreases_with_doping():
    # More dopant → more carriers → lower resistivity (monotonic), over the substrate range.
    N = np.array([1e15, 1e16, 1e17, 5e17])
    rho = cz.resistivity(N, "B")
    assert np.all(np.diff(rho) < 0.0)


# --------------------------------------------------------------------------- #
# The boule + its slices (the seam the G2 harness consumes)
# --------------------------------------------------------------------------- #
def test_boule_defaults_to_the_cited_k_and_slices_exactly_at_the_seed():
    b = cz.Boule(dopant="B", N_seed=1.0e17)
    assert b.k == cz.SEGREGATION_K["B"]                           # default k = cited Trumbore value
    s0 = b.slice(0.0)
    assert s0.N_A == 1.0e17                                       # the seed slice is exact (the seam)
    assert s0.z == 0.0
    # A deeper slice is more heavily doped (k<1) and lower-resistivity than the seed.
    s_deep = b.slice(0.8)
    assert s_deep.N_A > s0.N_A
    assert s_deep.resistivity_ohm_cm < s0.resistivity_ohm_cm


def test_boule_resistivity_tracks_its_doping():
    b = cz.Boule(dopant="B", N_seed=1.0e15)
    z = 0.5
    assert b.axial_resistivity(z) == pytest.approx(cz.resistivity(b.axial_doping(z), "B"))


def test_scheil_rejects_out_of_range_fraction():
    with pytest.raises(ValueError):
        cz.scheil_profile(1.0, 1.0e15, 0.8)                      # z must be < 1
    with pytest.raises(ValueError):
        cz.scheil_profile(-0.01, 1.0e15, 0.8)
