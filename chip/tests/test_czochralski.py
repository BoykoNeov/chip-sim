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


# --------------------------------------------------------------------------- #
# CG-1: Burton–Prim–Slichter effective segregation k_eff(Δ) — pull rate vs the
# boundary layer. Triad shape (plan §6a): the two LIMITS are the tight legs (no
# independent conservation law — like the etch/packaging tiers); the cited BPS
# form + flagged δ/D are the benchmark; monotone-bounded-[k₀,1] is machinery.
# --------------------------------------------------------------------------- #
def test_keff_at_zero_velocity_is_exactly_k0_the_wellmixed_seam():
    # Δ=0 (slow pull / vigorous stirring) → k_eff = k₀/[k₀+(1−k₀)·1] = k₀ EXACTLY — the well-mixed
    # Scheil limit the fab-line boule rides when CG-1 is off (the seam). Bit-exact for any k₀.
    for k0 in (0.80, 0.35, 0.023, 1.0):
        assert cz.effective_segregation_coefficient(k0, 0.0) == k0


def test_keff_tends_to_one_complete_solute_trapping():
    # Δ→∞ (fast pull / no stirring) → e^(−Δ)→0 → k_eff→1: complete solute trapping, no segregation.
    k0 = cz.SEGREGATION_K["B"]
    assert cz.effective_segregation_coefficient(k0, 50.0) == pytest.approx(1.0, abs=1e-9)
    # A strong segregator also tends to 1 (just needs a larger Δ to get there).
    assert cz.effective_segregation_coefficient(cz.SEGREGATION_K["Sb"], 200.0) == pytest.approx(1.0, abs=1e-9)


def test_keff_is_one_for_any_velocity_when_k0_is_one():
    # k₀=1 → nothing to segregate → k_eff=1 for every Δ (the no-segregation degenerate case).
    for delta in (0.0, 0.3, 2.0, 10.0):
        assert cz.effective_segregation_coefficient(1.0, delta) == 1.0


def test_keff_rises_monotonically_and_stays_bounded():
    # Machinery: k_eff increases monotonically with Δ and stays in [k₀, 1] (between equilibrium and
    # complete trapping) — pulling faster only ever reduces segregation, never reverses it.
    k0 = cz.SEGREGATION_K["B"]
    deltas = [0.0, 0.1, 0.3, 1.0, 3.0, 10.0]
    keffs = [cz.effective_segregation_coefficient(k0, d) for d in deltas]
    assert keffs == sorted(keffs)                                # monotone increasing
    assert all(k0 <= ke <= 1.0 for ke in keffs)                  # bounded in [k₀, 1]
    assert keffs[1] > k0                                         # any Δ>0 strictly lifts k_eff (k₀<1)


def test_keff_segregation_deficit_decays_exponentially():
    # The structural identity 1/k_eff − 1 = (1/k₀ − 1)·e^(−Δ) (a regression guard, NOT a conservation
    # law): the fractional segregation "deficit" decays exponentially in the normalized velocity.
    k0 = 0.35
    for delta in (0.2, 1.0, 2.5):
        ke = cz.effective_segregation_coefficient(k0, delta)
        assert (1.0 / ke - 1.0) == pytest.approx((1.0 / k0 - 1.0) * math.exp(-delta))


def test_normalized_velocity_form_and_realistic_magnitude():
    # Δ = v·δ/D with the flagged δ/D. The HONEST magnitude (the load-bearing flag): boron at realistic
    # Si pull (≈1 mm/min) gives a SMALL Δ and so only a MODEST k_eff lift — not a flat boule.
    delta = cz.normalized_growth_velocity(1.0)                   # 1 mm/min, default δ/D
    assert 0.0 < delta < 0.5                                     # realistic Si pull → small Δ
    keff = cz.effective_segregation_coefficient(cz.SEGREGATION_K["B"], delta)
    assert 0.80 < keff < 0.85                                    # boron barely moves at realistic pull
    # Δ scales linearly with pull rate, and zero pull is the well-mixed Δ=0 seam.
    assert cz.normalized_growth_velocity(2.0) == pytest.approx(2.0 * delta)
    assert cz.normalized_growth_velocity(0.0) == 0.0


def test_keff_invalid_inputs_raise():
    with pytest.raises(ValueError):
        cz.effective_segregation_coefficient(0.0, 1.0)           # k0 must be in (0, 1]
    with pytest.raises(ValueError):
        cz.effective_segregation_coefficient(1.2, 1.0)
    with pytest.raises(ValueError):
        cz.effective_segregation_coefficient(0.8, -0.1)          # Δ ≥ 0
    with pytest.raises(ValueError):
        cz.normalized_growth_velocity(-1.0)


def test_boule_with_keff_flattens_the_axial_profile():
    # The consumer payoff at the physics layer: a boule built with k_eff (faster pull) has a FLATTER
    # axial doping profile than the equilibrium-k₀ boule — less rise from seed to tail.
    k0 = cz.SEGREGATION_K["B"]
    keff = cz.effective_segregation_coefficient(k0, cz.normalized_growth_velocity(10.0))
    slow = cz.Boule(dopant="B", N_seed=1.0e17, k=k0)
    fast = cz.Boule(dopant="B", N_seed=1.0e17, k=keff)
    assert slow.axial_doping(0.0) == fast.axial_doping(0.0) == 1.0e17     # same seed (the seam holds)
    assert fast.axial_doping(0.9) < slow.axial_doping(0.9)               # faster pull → flatter tail
    assert keff > k0


# --------------------------------------------------------------------------- #
# CG-2: the Voronkov V/G grown-in point-defect criterion — the in-model brake on
# pulling faster. Triad shape (plan §6a, the flagged-phenomenology tier — like
# the G5 etch/depo bias, NO independent conservation law): the tight legs are the
# cited criterion form + ξ_t value and the definitional-exact regime flip at ξ_t;
# the void→density coefficient is the FLAGGED house consequence; the zero-below-
# threshold + monotone-above are by-construction regression guards (not anchors).
# --------------------------------------------------------------------------- #
def test_voronkov_critical_ratio_is_the_cited_value():
    # ξ_t ≈ 0.13 mm²/(K·min), pinned to the cited Voronkov (J. Cryst. Growth 59:625, 1982) value
    # (= the often-quoted ~1.3e-3 cm²/(K·min) ×100 mm²/cm²) — the tight cited anchor, NOT from memory.
    assert cz.VORONKOV_CRITICAL_RATIO == pytest.approx(0.13)


def test_voronkov_ratio_units_and_form():
    # ξ = V/G with V in mm/min, G in K/mm → mm²/(K·min) (the pinned units matching ξ_t).
    assert cz.voronkov_ratio(1.0, 4.0) == pytest.approx(0.25)
    assert cz.voronkov_ratio(2.0, 4.0) == pytest.approx(0.50)     # ∝ pull rate
    assert cz.voronkov_ratio(1.0, 8.0) == pytest.approx(0.125)    # ∝ 1/gradient (cooler hot zone → ξ↑)
    assert cz.voronkov_ratio(0.0, 4.0) == 0.0                     # zero pull → ξ=0 (deep interstitial)


def test_regime_flips_at_the_critical_ratio_the_definitional_limit():
    # The tight LIMIT leg (like CG-1's Δ=0→k₀): the V/I boundary is exact at ξ_t. Just above → vacancy
    # (voids/COPs), just below → interstitial (dislocations), exactly at → the OSF ring.
    xi_t = cz.VORONKOV_CRITICAL_RATIO
    assert cz.grown_in_defect_regime(xi_t * 1.001) == "vacancy"
    assert cz.grown_in_defect_regime(xi_t * 0.999) == "interstitial"
    assert cz.grown_in_defect_regime(xi_t) == "osf"               # exactly on the boundary


def test_void_density_zero_at_and_below_threshold_is_a_guard():
    # By-construction regression guard (NOT a tight anchor): no vacancy supersaturation at/below ξ_t →
    # no voids. This zero is the seam lever — a sub-ξ_t (interstitial) or boundary growth adds nothing
    # to the killer-defect density, so the G3 defect map is untouched.
    xi_t = cz.VORONKOV_CRITICAL_RATIO
    assert cz.void_defect_density(xi_t) == 0.0
    assert cz.void_defect_density(xi_t * 0.5) == 0.0              # deep interstitial → 0
    assert cz.void_defect_density(0.0) == 0.0


def test_void_density_rises_monotonically_above_threshold():
    # Machinery: above ξ_t the COP/void killer density rises monotonically with the excess ξ−ξ_t, and
    # is continuous at the threshold (→0⁺). The *direction* is criterion-driven; the slope is flagged.
    xi_t = cz.VORONKOV_CRITICAL_RATIO
    ratios = [xi_t, xi_t + 0.05, xi_t + 0.16, xi_t + 0.5, xi_t + 1.0]
    dens = [cz.void_defect_density(r) for r in ratios]
    assert dens == sorted(dens)                                  # monotone non-decreasing
    assert dens[0] == 0.0 and dens[1] > 0.0                      # switches on just above ξ_t
    assert cz.void_defect_density(xi_t + 1e-9) == pytest.approx(0.0, abs=1e-6)   # continuous at ξ_t
    # Linear in the excess with the (flagged) coefficient.
    assert cz.void_defect_density(xi_t + 0.4) == pytest.approx(cz.COP_DENSITY_PER_RATIO_EXCESS_CM2 * 0.4)


def test_voronkov_realistic_magnitude_typical_cz_is_vacancy_rich():
    # The HONEST magnitude (the load-bearing flag, like CG-1's): realistic CZ (V≈1 mm/min, G≈3.5 K/mm)
    # gives ξ≈0.29 > ξ_t → VACANCY-rich (historically COP-containing) — NOT defect-free by default.
    ratio = cz.voronkov_ratio(1.0, 3.5)
    assert ratio == pytest.approx(0.2857, abs=1e-3)
    assert cz.grown_in_defect_regime(ratio) == "vacancy"
    assert cz.void_defect_density(ratio) > 0.0                   # a real (if modest) COP killer density
    # The hot-zone lever: raising G to ≈ V/ξ_t pulls ξ back to the boundary (defect-free window).
    g_star = 1.0 / cz.VORONKOV_CRITICAL_RATIO                    # ≈7.7 K/mm at V=1
    assert cz.voronkov_ratio(1.0, g_star) == pytest.approx(cz.VORONKOV_CRITICAL_RATIO)
    assert cz.void_defect_density(cz.voronkov_ratio(1.0, g_star)) == 0.0


def test_voronkov_invalid_inputs_raise():
    with pytest.raises(ValueError):
        cz.voronkov_ratio(-1.0, 4.0)                             # pull rate ≥ 0
    with pytest.raises(ValueError):
        cz.voronkov_ratio(1.0, 0.0)                              # gradient > 0
    with pytest.raises(ValueError):
        cz.void_defect_density(0.5, coefficient=-1.0)            # coefficient ≥ 0
