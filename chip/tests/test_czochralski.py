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


# --------------------------------------------------------------------------- #
# A2 (OSF ring): CG-2 made radial — a radial G(r) → ξ(r) → the V/I boundary.
# Triad shape (plan §6a flagged-phenomenology tier, NO conservation law, and — the
# A2 correction — NO engine heat leg, the gradient is a closed-form house profile):
# the TIGHT legs are the ring LOCATION (ξ(r_OSF)=ξ_t, coefficient-robust — the solver
# never sees the void coefficient) and the topology SIGNS (vacancy centre / interstitial
# edge). The G(r) profile, the boost, the ring width, and the ring's on-wafer existence
# are FLAGGED house numbers. boost=0 recovers CG-2 byte-for-byte (the seam). The
# density-falls-with-radius is a by-construction guard, NOT an anchor.
# --------------------------------------------------------------------------- #
# A (V, G_center, boost) with the V/I boundary ON-wafer: ξ(0)=V/G_center=0.20 > ξ_t > ξ(1)=0.10
# (need G_center ∈ (V/2ξ_t, V/ξ_t) = (7.7, 15.4) at V=2, boost=1).
_V_RING, _GC_RING, _BOOST_RING = 2.0, 10.0, 1.0


def test_radial_gradient_boost_zero_is_the_cg2_seam():
    # boost=0 → G(r) ≡ G_center for every r (uniform) — bit-for-bit the single-G CG-2 picture, and
    # osf_ring_radius has no interior boundary (None). The seam: the radial knob off recovers CG-2.
    for r in (0.0, 0.3, 0.71, 1.0):
        assert cz.radial_thermal_gradient(r, _GC_RING, boost=0.0) == _GC_RING   # exact uniform
    assert cz.osf_ring_radius(_V_RING, _GC_RING, boost=0.0) is None


def test_radial_gradient_rises_toward_the_edge():
    # The one physics DIRECTION (flagged shape, but the sign is the OSF topology): G rises outward, so
    # ξ=V/G falls outward → centre higher-ξ than edge. G(0)=G_center exactly.
    assert cz.radial_thermal_gradient(0.0, _GC_RING, boost=_BOOST_RING) == _GC_RING
    g_edge = cz.radial_thermal_gradient(1.0, _GC_RING, boost=_BOOST_RING)
    assert g_edge == pytest.approx(_GC_RING * (1.0 + _BOOST_RING))              # G(1)=G_center·(1+boost)
    assert g_edge > _GC_RING                                                    # rises toward the edge
    # array form (the demo's radial sweep) — monotone increasing in r.
    g = cz.radial_thermal_gradient(np.array([0.0, 0.5, 1.0]), _GC_RING, boost=_BOOST_RING)
    assert np.all(np.diff(g) > 0.0)


def test_osf_ring_location_sits_exactly_at_xi_t_the_tight_leg():
    # THE tight leg: the ring is where ξ(r_OSF)=ξ_t — a definitional crossing, to machine precision.
    r_osf = cz.osf_ring_radius(_V_RING, _GC_RING, boost=_BOOST_RING)
    assert r_osf is not None and 0.0 < r_osf < 1.0
    g_at = cz.radial_thermal_gradient(r_osf, _GC_RING, boost=_BOOST_RING)
    assert cz.voronkov_ratio(_V_RING, g_at) == pytest.approx(cz.VORONKOV_CRITICAL_RATIO)
    # The closed form: r_OSF = √((V/(ξ_t·G_center) − 1)/boost).
    import math
    expected = math.sqrt((_V_RING / (cz.VORONKOV_CRITICAL_RATIO * _GC_RING) - 1.0) / _BOOST_RING)
    assert r_osf == pytest.approx(expected)


def test_osf_ring_location_is_coefficient_robust():
    # The ring LOCATION does not depend on the flagged void coefficient (osf_ring_radius never takes
    # one) — the coefficient sets only the kill DEPTH, never the boundary. So the void density's
    # zero-crossing sits at r_OSF for ANY coefficient (inside kills, at/outside is clean).
    r_osf = cz.osf_ring_radius(_V_RING, _GC_RING, boost=_BOOST_RING)
    def density_at(r, coef):
        g = cz.radial_thermal_gradient(r, _GC_RING, boost=_BOOST_RING)
        return cz.void_defect_density(cz.voronkov_ratio(_V_RING, g), coefficient=coef)
    for coef in (0.05, 0.3, 5.0):
        assert density_at(r_osf * 0.99, coef) > 0.0                # just inside the ring → vacancy kills
        assert density_at(r_osf, coef) == pytest.approx(0.0, abs=1e-12)   # AT the ring → exactly zero
        assert density_at(min(r_osf * 1.01, 1.0), coef) == 0.0     # outside → clean interstitial rim


def test_osf_topology_signs_vacancy_core_interstitial_edge():
    # The topology-sign leg: with the ring on-wafer the centre is vacancy-rich, the edge interstitial.
    assert cz.radial_defect_regime(0.0, _V_RING, _GC_RING, _BOOST_RING) == "vacancy"
    assert cz.radial_defect_regime(1.0, _V_RING, _GC_RING, _BOOST_RING) == "interstitial"
    # The killer (vacancy void) density is a by-construction guard: it FALLS to zero with radius
    # (NOT an anchor — the magnitude is the flagged coefficient; only the monotone direction is asserted).
    def vd(r):
        g = cz.radial_thermal_gradient(r, _GC_RING, boost=_BOOST_RING)
        return cz.void_defect_density(cz.voronkov_ratio(_V_RING, g))
    dens = [vd(r) for r in np.linspace(0.0, 1.0, 11)]
    assert dens[0] > 0.0                                           # COP-degraded vacancy core (centre)
    assert dens[-1] == 0.0                                         # clean interstitial rim
    assert all(a >= b for a, b in zip(dens, dens[1:]))            # monotone non-increasing (the guard)


def test_osf_ring_off_wafer_both_cases_return_none():
    # None means NO on-wafer boundary — but the two off-wafer cases are distinct, so the caller reads
    # the regime (not the None) to tell them apart (advisor: don't conflate no-kills with all-kills).
    # (a) all-interstitial: even the centre is interstitial (G_center ≥ V/ξ_t → ξ(0) ≤ ξ_t).
    g_big = _V_RING / cz.VORONKOV_CRITICAL_RATIO + 1.0
    assert cz.osf_ring_radius(_V_RING, g_big, boost=_BOOST_RING) is None
    assert cz.radial_defect_regime(0.0, _V_RING, g_big, _BOOST_RING) in ("interstitial", "osf")
    assert cz.radial_defect_regime(1.0, _V_RING, g_big, _BOOST_RING) == "interstitial"
    # (b) all-vacancy: even the EDGE has ξ > ξ_t (G(1)=G_center·(1+boost) < V/ξ_t).
    g_tiny = 1.0                                                   # G(1)=2 ≪ V/ξ_t=15.4
    assert cz.osf_ring_radius(_V_RING, g_tiny, boost=_BOOST_RING) is None
    assert cz.radial_defect_regime(0.0, _V_RING, g_tiny, _BOOST_RING) == "vacancy"
    assert cz.radial_defect_regime(1.0, _V_RING, g_tiny, _BOOST_RING) == "vacancy"


def test_osf_pull_rate_moves_the_ring_outward():
    # The classic CZ behaviour (a cross-check on the direction, not a magnitude): a FASTER pull (higher
    # ξ everywhere) pushes the vacancy core outward → the ring moves toward the edge (larger r_OSF),
    # and eventually off-wafer (all-vacancy → None). Coefficient-free, pure ξ_t + profile.
    r_slow = cz.osf_ring_radius(1.8, _GC_RING, boost=_BOOST_RING)
    r_fast = cz.osf_ring_radius(2.2, _GC_RING, boost=_BOOST_RING)
    assert r_slow is not None and r_fast is not None
    assert r_fast > r_slow                                         # faster pull → ring moves outward
    assert cz.osf_ring_radius(5.0, _GC_RING, boost=_BOOST_RING) is None   # too fast → all-vacancy, off-wafer


def test_osf_invalid_inputs_raise():
    with pytest.raises(ValueError):
        cz.radial_thermal_gradient(0.5, 0.0)                      # G_center > 0
    with pytest.raises(ValueError):
        cz.radial_thermal_gradient(0.5, 10.0, boost=-1.0)         # boost ≥ 0
    with pytest.raises(ValueError):
        cz.radial_thermal_gradient(-0.1, 10.0)                    # radius_frac ≥ 0
    with pytest.raises(ValueError):
        cz.osf_ring_radius(_V_RING, 0.0, boost=_BOOST_RING)       # G_center > 0


# --------------------------------------------------------------------------- #
# CG-3: the Stefan interface heat balance — where CG-2's gradient G comes from.
# Triad shape (plan §6a, same honesty tier as CG-2 — NO independent conservation
# law): the tight legs are the two analytic LIMITS (V→0 pure conduction-matching;
# V→∞ ξ saturation, the headline + the CG-1 Δ=0→k₀ analogue) + cited Si melt-point
# constants. The flux-balance round-trip is a by-construction guard, NOT a
# conservation leg (it re-derives the defining equation). G_l stays a house number.
# --------------------------------------------------------------------------- #
def test_stefan_v_zero_limit_is_pure_conduction_matching():
    # V→0 (no growth): the latent term vanishes → G_s = k_l·G_l/k_s exactly (the interface is just a
    # conduction matching point). The tight V→0 analytic limit.
    g_l = 3.0                                                    # K/mm
    g_s = cz.stefan_interface_gradient(0.0, g_l)
    expected = cz.SI_LIQUID_THERMAL_COND_W_PER_M_K * g_l / cz.SI_SOLID_THERMAL_COND_W_PER_M_K
    assert g_s == pytest.approx(expected)                        # K/mm (the unit factors cancel)


def test_stefan_ratio_saturates_at_xi_max_the_headline():
    # THE CG-3 finding (the tight V→∞ limit): ξ = V/G_s saturates at ξ_max = k_s/(L·ρ) — latent heat
    # caps the vacancy supersaturation. With NO melt gradient (G_l=0) ξ = ξ_max EXACTLY for any V>0
    # (the latent term alone sets G_s ∝ V), and with G_l>0 ξ → ξ_max from below as V→∞.
    xi_max = cz.max_voronkov_ratio()
    for v in (0.5, 1.0, 5.0, 100.0):
        g_s = cz.stefan_interface_gradient(v, 0.0)               # G_l = 0
        assert cz.voronkov_ratio(v, g_s) == pytest.approx(xi_max)
    # G_l > 0 → strictly below ξ_max, approaching it as V grows.
    xi_slow = cz.voronkov_ratio(1.0, cz.stefan_interface_gradient(1.0, 2.0))
    xi_fast = cz.voronkov_ratio(50.0, cz.stefan_interface_gradient(50.0, 2.0))
    assert xi_slow < xi_fast < xi_max
    assert cz.voronkov_ratio(1.0e6, cz.stefan_interface_gradient(1.0e6, 2.0)) == pytest.approx(xi_max, rel=1e-3)


def test_xi_max_is_a_few_times_xi_t_with_cited_constants():
    # Order-of-magnitude (set by the cited Si constants, k_l-independent): ξ_max ≈ 0.3 mm²/(K·min),
    # ~2–3× the cited ξ_t (≈0.13). So even an infinitely fast pull lands only modestly vacancy-rich —
    # NOT the unbounded ξ of CG-2's fixed G. k_l does NOT enter ξ_max (only the V→∞ / G_l→0 limit).
    xi_max = cz.max_voronkov_ratio()
    assert 0.2 < xi_max < 0.45
    assert 2.0 < xi_max / cz.VORONKOV_CRITICAL_RATIO < 3.0
    assert cz.max_voronkov_ratio(k_solid_W_per_m_K=cz.SI_SOLID_THERMAL_COND_W_PER_M_K) == xi_max  # k_l absent


def test_stefan_gradient_rises_linearly_with_pull_the_coupling():
    # The coupling (machinery/guard): G_s is affine in V with slope L·ρ/k_s (the latent-heat term), so
    # equal pull increments add equal gradient — and G_s rises with the melt gradient G_l too.
    g0 = cz.stefan_interface_gradient(0.0, 1.0)
    g1 = cz.stefan_interface_gradient(1.0, 1.0)
    g2 = cz.stefan_interface_gradient(2.0, 1.0)
    assert (g2 - g1) == pytest.approx(g1 - g0)                   # affine in V (constant latent slope)
    assert g1 > g0                                               # rises with pull rate
    assert cz.stefan_interface_gradient(1.0, 3.0) > cz.stefan_interface_gradient(1.0, 1.0)  # rises with G_l


def test_cited_si_melt_point_constants_pinned():
    # The benchmark leg: the Si melt-point thermophysical constants, pinned (not from memory). k_s is
    # the MELT-POINT value (~22 W/m·K), NOT room-temperature (~150) — the load-bearing distinction.
    assert cz.SI_SOLID_THERMAL_COND_W_PER_M_K == pytest.approx(22.0)
    assert cz.SI_SOLID_THERMAL_COND_W_PER_M_K < 40.0             # melt-point, not the RT ~150 value
    assert cz.SI_LATENT_HEAT_FUSION_J_PER_KG == pytest.approx(1.79e6)
    assert cz.SI_SOLID_DENSITY_KG_PER_M3 == pytest.approx(2330.0)


def test_stefan_flux_balance_roundtrip_is_a_guard_not_conservation():
    # By-construction regression guard (NOT a conservation leg — re-deriving the flux balance from G_s
    # is the defining equation read backwards): k_s·G_s − k_l·G_l == L·ρ·V in SI. Pinned so a sign/unit
    # slip is caught, but explicitly NOT claimed as an independent conservation check.
    v, g_l = 1.5, 2.0
    g_s = cz.stefan_interface_gradient(v, g_l)
    lhs = (cz.SI_SOLID_THERMAL_COND_W_PER_M_K * g_s * 1.0e3
           - cz.SI_LIQUID_THERMAL_COND_W_PER_M_K * g_l * 1.0e3)   # k_s·G_s − k_l·G_l (W/m², G in K/m)
    rhs = cz.SI_LATENT_HEAT_FUSION_J_PER_KG * cz.SI_SOLID_DENSITY_KG_PER_M3 * (v * 1.0e-3 / 60.0)  # L·ρ·V
    assert lhs == pytest.approx(rhs)


def test_stefan_invalid_inputs_raise():
    with pytest.raises(ValueError):
        cz.stefan_interface_gradient(-1.0, 2.0)                  # pull rate ≥ 0
    with pytest.raises(ValueError):
        cz.stefan_interface_gradient(1.0, -2.0)                  # melt gradient ≥ 0
    with pytest.raises(ValueError):
        cz.stefan_interface_gradient(1.0, 2.0, k_solid_W_per_m_K=0.0)  # k_s > 0


# --------------------------------------------------------------------------- #
# C1: crucible oxygen → thermal donors — the ELECTRICAL crystal-growth deepening.
# Triad shape (the flagged-phenomenology tier, like CG-1/2/3 — NO independent
# conservation law): the tight legs are the SEAM (no oxygen OR no anneal ⇒ N_TD=0,
# exact, by BOTH paths) + the EXACT compensation algebra (N_A−N_TD); the one CITED
# benchmark direction is the Kaiser–Frisch–Reiss FOURTH-power initial rate ∝[O_i]⁴;
# the saturating form, the cube-law saturation exponent, and EVERY magnitude are
# FLAGGED house numbers (not asserted with Scheil's anchors). Type inversion is a
# guarded named edge.
# --------------------------------------------------------------------------- #
def test_thermal_donor_seam_zero_by_both_paths_exact():
    # The seam (tight, EXACT): donors form only at the ~450 °C anneal, not during growth — so N_TD=0
    # bit-for-bit when there is NO oxygen (any anneal) OR NO anneal (any oxygen). Either path is the
    # seam lever that keeps the pre-C1 substrate byte-for-byte.
    for t in (0.0, 60.0, 600.0):
        assert cz.thermal_donor_density(0.0, t) == 0.0           # no oxygen ⇒ no donors (exact)
    for O in (0.0, 5e17, 1.2e18):
        assert cz.thermal_donor_density(O, 0.0) == 0.0           # no anneal ⇒ no donors (exact)


def test_thermal_donor_initial_rate_is_the_cited_fourth_power():
    # The CITED direction (Kaiser–Frisch–Reiss, Phys. Rev. 112, 1546, 1958): the INITIAL formation rate
    # scales as the FOURTH power of [O_i]. Asserted DIRECTLY on the rate function (not a fixed-t finite
    # difference, which would understate the high-[O_i] ratio once it saturates, since τ ∝ 1/[O_i]).
    r1 = cz.thermal_donor_formation_rate(5.0e17)
    r2 = cz.thermal_donor_formation_rate(1.0e18)                 # doubled oxygen
    assert r2 / r1 == pytest.approx(2.0 ** 4)                    # 16× — the fourth power
    r3 = cz.thermal_donor_formation_rate(1.5e18)                 # tripled vs r1
    assert r3 / r1 == pytest.approx(3.0 ** 4)                    # 81×
    assert cz.thermal_donor_formation_rate(0.0) == 0.0           # no oxygen ⇒ no rate (the seam)
    # The exponent constant is pinned to the cited fourth power (not from memory).
    assert cz.TD_RATE_OXYGEN_EXPONENT == 4.0


def test_thermal_donor_small_t_slope_matches_the_initial_rate():
    # The initial rate IS the t→0 slope of N_TD(t): N_TD(O, dt) ≈ rate₀(O)·dt for dt ≪ τ. Ties the
    # cited fourth-power rate to the actual density function (the whole composition, not just a constant).
    O, dt = 8.0e17, 1.0e-3                                       # dt ≪ τ (τ ~ 75 min here)
    rate0 = cz.thermal_donor_formation_rate(O)
    assert cz.thermal_donor_density(O, dt) == pytest.approx(rate0 * dt, rel=1e-3)


def test_thermal_donor_saturation_is_the_flagged_cube_law():
    # The saturation (FLAGGED, cube law — reported but more literature-variable than the rate's fourth
    # power, so not an anchor): N_sat ∝ [O_i]³. The direction (more oxygen → steeply more donors) is the
    # physics; the coefficient + exponent are house.
    s1 = cz.thermal_donor_saturation(5.0e17)
    s2 = cz.thermal_donor_saturation(1.0e18)
    assert s2 / s1 == pytest.approx(2.0 ** 3)                    # 8× — the cube law
    assert cz.thermal_donor_saturation(0.0) == 0.0              # no oxygen ⇒ no ceiling (the seam)
    assert cz.TD_SAT_OXYGEN_EXPONENT == 3.0                      # the flagged saturation exponent


def test_thermal_donor_density_saturates_and_is_bounded_monotone():
    # Machinery: N_TD rises monotonically with anneal time, bounded by N_sat, → N_sat as t→∞ (the
    # saturating exponential). The cited fourth power is the INITIAL slope; the long-time ceiling is N_sat.
    O = 8.0e17
    n_sat = cz.thermal_donor_saturation(O)
    times = [10.0, 30.0, 60.0, 120.0, 300.0, 1000.0]
    dens = [cz.thermal_donor_density(O, t) for t in times]
    assert dens == sorted(dens)                                  # monotone increasing in anneal time
    assert all(0.0 < d < n_sat for d in dens)                    # bounded below the ceiling
    assert cz.thermal_donor_density(O, 1.0e6) == pytest.approx(n_sat, rel=1e-6)  # → N_sat as t→∞


def test_net_doping_after_donors_is_exact_compensation_with_a_seam():
    # The EXACT algebra leg: n-type donors compensate the p-substrate one-for-one, N_net = N_A − N_TD.
    # N_TD=0 returns N_A BIT-FOR-BIT (the seam — 1e17 > 2**53, so only an exact identity survives).
    assert cz.net_doping_after_donors(1.0e17, 0.0) == 1.0e17     # exact seam
    assert cz.net_doping_after_donors(1.0e17, 2.0e16) == pytest.approx(8.0e16)   # exact subtraction


def test_thermal_donor_type_inversion_is_a_guarded_edge():
    # Type inversion (N_TD ≥ N_A → the substrate goes n-type) is a NAMED, GUARDED edge: it raises,
    # because the compact p-substrate device does not model an n-channel device (the demo scraps via the
    # V_t floor instead, staying p-type).
    with pytest.raises(ValueError):
        cz.net_doping_after_donors(1.0e17, 1.0e17)               # exactly compensated → n-type
    with pytest.raises(ValueError):
        cz.net_doping_after_donors(1.0e17, 1.2e17)               # over-compensated


def test_thermal_donor_cited_constants_and_band_pinned():
    # The benchmark leg: the ~450 °C donor-formation peak + the common-CZ reference [O_i]=1e18, pinned
    # (not from memory). The OXYGEN_BANDS span the typical CZ ~1e17–1e18 range, "none" the seam.
    assert cz.TD_ANNEAL_PEAK_C == pytest.approx(450.0)
    assert cz.TD_OXYGEN_REFERENCE_CM3 == pytest.approx(1.0e18)
    assert cz.OXYGEN_BANDS["none"] == 0.0                        # the seam baseline (no oxygen)
    assert cz.OXYGEN_BANDS["low"] < cz.OXYGEN_BANDS["typical"] < cz.OXYGEN_BANDS["high"]
    assert 1.0e17 <= cz.OXYGEN_BANDS["typical"] <= 1.0e18        # in the typical CZ range


def test_thermal_donor_invalid_inputs_raise():
    with pytest.raises(ValueError):
        cz.thermal_donor_density(-1.0, 60.0)                     # oxygen ≥ 0
    with pytest.raises(ValueError):
        cz.thermal_donor_density(8e17, -1.0)                     # anneal ≥ 0
    with pytest.raises(ValueError):
        cz.net_doping_after_donors(1e17, -1.0)                   # N_TD ≥ 0


def test_thermal_donor_realistic_magnitude_shifts_vt_down():
    # The HONEST magnitude (the load-bearing flag, like CG-1's): a typical [O_i]≈8e17 + a moderate anneal
    # trims a 1e17 boron substrate only MODESTLY (stays p-type, V_t still near nominal), while a high
    # [O_i]≈1.2e18 + a long anneal walks the net doping far down (the scrap case) — WITHOUT inverting.
    from chip.device import threshold_voltage
    n_typ = cz.thermal_donor_density(8.0e17, 120.0)
    n_hi = cz.thermal_donor_density(1.2e18, 240.0)
    eff_typ = cz.net_doping_after_donors(1.0e17, n_typ)
    eff_hi = cz.net_doping_after_donors(1.0e17, n_hi)            # must NOT raise (stays p-type)
    assert eff_typ > eff_hi > 0.0                                # both p-type; high oxygen drops it further
    vt_clean = threshold_voltage(1.0e17, 0.014).V_t
    vt_typ = threshold_voltage(eff_typ, 0.014).V_t
    vt_hi = threshold_voltage(eff_hi, 0.014).V_t
    assert vt_hi < vt_typ < vt_clean                            # donors push V_t monotonically DOWN
