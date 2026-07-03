"""Chip §5 validation: ion implantation — the buried initial condition (slice 1).

The observable a thermal predep physically **cannot** make: predep lays a surface-peaked ``erfc``
(maximum *at* the surface), while implantation embeds ions at a controlled depth ``R_p`` → a **buried**
Gaussian peak. This carries slice 1's triad (``docs/plans/ion-implantation.md`` §"Triad tiers"):

* **Tight (exact/analytic).** (a) The **seam** — ``two_step(implant=None)`` reproduces the predep path
  bit-for-bit. (b) **Dose conservation** — the sealed (no-flux) drive-in conserves the IC's grid dose to
  machine precision (the engine's finite-volume guarantee, for *any* IC). (c) The **buried Gaussian IC →
  drive-in warm-start** reduces to a known **broadened Gaussian** (``ΔR_p² → ΔR_p² + 2Dt``) for a deep
  implant. (d) The **buried-peak topology** (peak at ``x = R_p > 0``, ``dN/dx > 0`` shallower) — the
  discriminator, sign-robust.
* **Flagged (magnitude).** The absolute ``R_p(E)``/``ΔR_p(E)`` vs the cited Gibbons anchors
  ([[range-statistics-source]]) — a ~10% benchmark; and the IC-dose = ``Q`` amplitude, exact only to the
  **surface-truncation** error (the ``x<0`` tail lost for a shallow implant — the named scope edge).

The V_t-adjust consumer (``device.vt_adjust_shift``, the honest de-fake of the faked uniform offset) is
validated in ``test_device.py``; here we check only the profile physics and the seam.
"""
import dataclasses
import math

import numpy as np
import pytest

from chip import diffusion_dopant as dd


UM = dd.CM_PER_UM


# --------------------------------------------------------------------------- #
# Flagged benchmark: R_p(E), ΔR_p(E) vs the cited Gibbons anchors
# --------------------------------------------------------------------------- #
def test_range_statistics_reproduce_cited_anchors():
    # The flagged power-law fit reproduces the web-corroborated Gibbons anchors to ~10% across the
    # decade 10→200 keV (range-statistics-source). Not asserted exact — a coefficient-flagged benchmark.
    for species, anchors in dd._RP_ANCHORS_UM.items():
        for E_keV, Rp_um in anchors:
            Rp, _ = dd.range_statistics(species, E_keV)
            assert Rp / UM == pytest.approx(Rp_um, rel=0.12), (species, E_keV)
    for species, anchors in dd._DRP_ANCHORS_UM.items():
        for E_keV, dRp_um in anchors:
            _, dRp = dd.range_statistics(species, E_keV)
            assert dRp / UM == pytest.approx(dRp_um, rel=0.12), (species, E_keV)


def test_range_is_monotone_in_energy():
    # The teaching lever: higher energy → deeper implant (a strictly increasing R_p(E)). This sign is
    # cited/robust even where the absolute µm is flagged.
    energies = [10.0, 20.0, 50.0, 100.0, 200.0]
    for species in ("B", "P"):
        rps = [dd.range_statistics(species, E)[0] for E in energies]
        assert all(b > a for a, b in zip(rps, rps[1:])), species


def test_boron_penetrates_deeper_than_phosphorus():
    # Species ordering (cited): B (lighter, Z=5) ranges DEEPER than P (heavier, Z=15) at equal energy —
    # less nuclear stopping per collision. The physics the two-species fit must capture.
    for E in (30.0, 60.0, 100.0, 150.0):
        assert dd.range_statistics("B", E)[0] > dd.range_statistics("P", E)[0], E


def test_straggle_is_a_sane_fraction_of_range():
    # ΔR_p/R_p ~ 0.2–0.5 (larger for the lighter ion). A sanity band, not a tight anchor.
    for species in ("B", "P"):
        for E in (30.0, 100.0):
            Rp, dRp = dd.range_statistics(species, E)
            assert 0.1 < dRp / Rp < 0.7, (species, E)


def test_range_statistics_validates_inputs():
    with pytest.raises(ValueError):
        dd.range_statistics("B", 0.0)
    with pytest.raises(ValueError):
        dd.range_statistics("Xx", 100.0)          # no range data for an unknown species


# --------------------------------------------------------------------------- #
# The Implant dataclass + the buried-peak discriminator (the licence)
# --------------------------------------------------------------------------- #
def test_implant_validates_inputs():
    with pytest.raises(ValueError):
        dd.Implant(dose=0.0, energy_keV=100.0)
    with pytest.raises(ValueError):
        dd.Implant(dose=1e13, energy_keV=0.0)
    with pytest.raises(ValueError):
        dd.Implant(dose=1e13, energy_keV=100.0, species="Xx")


def test_buried_peak_is_the_discriminator():
    # THE discriminating observable (sign-robust): the profile peaks at a depth x = R_p > 0 (buried),
    # and RISES from the surface toward it (dN/dx > 0 for x < R_p) — the retrograde shape a surface-peaked
    # predep erfc (max at x=0, dN/dx ≤ 0 everywhere) physically cannot make.
    imp = dd.Implant(dose=1e13, energy_keV=100.0, species="B")
    grid = dd.uniform_grid(2.0 * UM, 600)
    N = dd.implant_profile(grid.centers, imp)
    Rp, _ = imp.range_statistics()
    i_peak = int(np.argmax(N))
    assert grid.centers[i_peak] > 0.0                       # buried (peak below the surface)
    assert grid.centers[i_peak] == pytest.approx(Rp, rel=0.02)   # at the projected range
    assert np.all(np.diff(N[: i_peak + 1]) > 0.0)           # rising toward the peak — the retrograde slope
    assert N[i_peak] > N[0]                                  # peak concentration exceeds the surface


def test_implant_profile_is_symmetric_gaussian_about_Rp():
    # Slice-1 first cut = the SYMMETRIC two-moment Gaussian (the Pearson-IV skew is slice 2). Equal
    # concentration at R_p ± ΔR_p.
    imp = dd.Implant(dose=1e13, energy_keV=120.0, species="B")
    Rp, dRp = imp.range_statistics()
    lo = dd.implant_profile(np.array([Rp - dRp]), imp)[0]
    hi = dd.implant_profile(np.array([Rp + dRp]), imp)[0]
    assert lo == pytest.approx(hi, rel=1e-12)


# --------------------------------------------------------------------------- #
# Tight: dose conservation + the deep-implant amplitude (truncation-flagged)
# --------------------------------------------------------------------------- #
def test_drivein_conserves_the_implant_ic_dose():
    # Conservation is STRUCTURAL — the no-flux (sealed) drive-in conserves ∫N dx to machine precision for
    # ANY initial condition (the engine's finite-volume guarantee), independent of the Gaussian holding.
    imp = dd.Implant(dose=1e14, energy_keV=100.0, species="B")
    ic, drivein = dd.two_step("B", implant=imp, length_um=3.0)
    assert ic.stage == "implant"
    assert drivein.stage == "drive-in"
    assert drivein.dose == pytest.approx(ic.dose, rel=1e-10)


def test_deep_implant_ic_dose_equals_Q_to_truncation():
    # Amplitude (flagged): the IC grid-dose equals the implanted dose Q to the QUADRATURE + surface-
    # truncation error. For a DEEP implant (R_p ≳ 4·ΔR_p, away from both boundaries) truncation is
    # negligible — grid dose = Q to <0.1%.
    imp = dd.Implant(dose=1e14, energy_keV=100.0, species="B")
    grid = dd.uniform_grid(3.0 * UM, 900)
    ic = dd.implant_ic(grid, imp)
    Rp, dRp = imp.range_statistics()
    assert Rp / dRp > 4.0                                    # deep (the truncation-negligible regime)
    assert ic.dose == pytest.approx(imp.dose, rel=1e-3)


def test_shallow_implant_loses_dose_to_surface_truncation():
    # The named scope edge: a SHALLOW implant (R_p not ≫ ΔR_p) puts part of the analytic Gaussian at
    # x<0, which is lost (surface reflection is NOT modelled in slice 1) — the grid dose falls
    # measurably below Q. Flagged, not fudged (we do not renormalize the IC to Q).
    imp = dd.Implant(dose=1e14, energy_keV=10.0, species="B")
    grid = dd.uniform_grid(1.0 * UM, 1000)
    ic = dd.implant_ic(grid, imp)
    Rp, dRp = imp.range_statistics()
    assert Rp / dRp < 3.0                                    # shallow
    assert ic.dose < 0.99 * imp.dose                         # a real (>1%) surface-truncation loss


# --------------------------------------------------------------------------- #
# Tight: the warm-start buried Gaussian → broadened Gaussian
# --------------------------------------------------------------------------- #
def test_drivein_broadens_the_buried_gaussian():
    # A Gaussian IC diffusing at constant D in the (effectively) semi-infinite bulk broadens as a pure
    # convolution with the heat kernel: ΔR_p² → ΔR_p² + 2Dt, the peak fixed at R_p (mass-conserving). A
    # DEEP implant (R_p/σ_final ≈ 4.7, far from both boundaries → surface reflection negligible) matches
    # the analytic broadened Gaussian TIGHT — the implant-IC analogue of the exact-Gaussian warm-start.
    imp = dd.Implant(dose=1e14, energy_keV=150.0, species="B")
    Rp, sigma = imp.range_statistics()
    grid = dd.uniform_grid(4.0 * UM, 800)
    N0 = dd.implant_profile(grid.centers, imp)
    T, t = 950.0, 20.0 * 60.0
    D = dd.diffusivity("B", T)
    drivein = dd.drive_in(grid, N0, "B", T, t, n_steps=800)

    sigma_f = math.sqrt(sigma ** 2 + 2.0 * D * t)
    A = imp.dose / (math.sqrt(2.0 * math.pi) * sigma_f)
    N_ana = A * np.exp(-((grid.centers - Rp) ** 2) / (2.0 * sigma_f ** 2))

    assert grid.centers[int(np.argmax(drivein.N))] == pytest.approx(Rp, abs=grid.widths[0])  # peak fixed
    bulk = N_ana > 0.01 * N_ana.max()
    assert np.max(np.abs(drivein.N[bulk] - N_ana[bulk]) / N_ana[bulk]) < 5e-3   # broadened Gaussian, tight


# --------------------------------------------------------------------------- #
# The seam: implant=None reproduces the predep two-step bit-for-bit
# --------------------------------------------------------------------------- #
def test_seam_implant_none_is_bit_for_bit_predep():
    # implant=None ⇒ the predep→drive-in path runs byte-for-byte unchanged (the established opt-in seam
    # discipline — the entire existing suite is untouched by §5).
    p0, d0 = dd.two_step("B")
    p1, d1 = dd.two_step("B", implant=None)
    assert np.array_equal(d0.N, d1.N)
    assert np.array_equal(p0.N, p1.N)
    assert p0.stage == "predeposition"


def test_implant_replaces_the_predep_source():
    # With an implant the first returned profile is the athermal as-implanted IC (stage="implant"),
    # NOT a predep — the implant IS the source, so T_predep/t_predep/N_surface are bypassed.
    imp = dd.Implant(dose=1e13, energy_keV=80.0, species="P")
    ic, drivein = dd.two_step("P", implant=imp)
    assert ic.stage == "implant"
    assert ic.t == 0.0 and ic.D == 0.0                       # athermal placement (the anneal is the drive-in)
    # Changing the (bypassed) predep knobs does not move the implant result.
    ic2, drivein2 = dd.two_step("P", implant=imp, T_predep=1200.0, t_predep_min=99.0)
    assert np.array_equal(drivein.N, drivein2.N)


# --------------------------------------------------------------------------- #
# Slice 2 — Pearson-IV skew (the tightened, asymmetric as-implanted profile)
# --------------------------------------------------------------------------- #
# Physics: a light ion (boron) backscatters toward the surface → a NEGATIVE skewness γ (surface tail,
# peak DEEPER than R_p), growing more negative with energy (Plummer §8, "light ions backscatter to skew
# the profile up"). The four-moment Pearson-IV distribution is the workhorse branch; slice-1's symmetric
# Gaussian is the seam (shape="gaussian", default). Triad:
#   * Tight/exact: (a) the SEAM — default shape="gaussian" is the slice-1 Gaussian bit-for-bit; (b) the
#     construction reproduces the four moments (mean=R_p, var=σ² exact; γ, β by design); (c) the mode
#     sits at the analytic R_p+b1, DEEPER than R_p for boron — the sign-robust skew discriminator;
#     (d) dose conservation through the drive-in is STRUCTURAL (shape-independent, machine precision).
#   * Flagged: the γ(E)/β magnitudes (house-calibrated into the type-IV band — SIGN/TREND cited, numbers
#     not table anchors); the two-sided (surface AND heavy deep-tail) analytic-∫=Q truncation.
def test_pearson_default_shape_is_gaussian_seam():
    # The seam: shape defaults to "gaussian" and reproduces the slice-1 symmetric Gaussian bit-for-bit,
    # so the entire slice-1 suite is byte-identical (the opt-in discipline, cf. implant=None).
    imp = dd.Implant(dose=1e13, energy_keV=100.0, species="B")
    assert imp.shape == "gaussian"
    x = dd.uniform_grid(2.0 * UM, 600).centers
    Rp, dRp = imp.range_statistics()
    gaussian = (imp.dose / (math.sqrt(2.0 * math.pi) * dRp)) * np.exp(-((x - Rp) ** 2) / (2.0 * dRp ** 2))
    assert np.array_equal(dd.implant_profile(x, imp), gaussian)


def test_pearson4_reproduces_the_four_moments():
    # THE tight leg (validates the whole closed-form construction incl. the skew SIGN): integrated over
    # its full support, the Pearson-IV density has mean=R_p and variance=σ² EXACTLY, and skewness=γ,
    # kurtosis=β by design. A quadrature check (any sign error in the coefficients fails here).
    Rp, dRp, gamma, beta = dd.range_moments("B", 100.0)
    assert gamma < 0.0                                          # boron: negative skew (cited)
    s = np.linspace(-40.0 * dRp, 40.0 * dRp, 400001)           # full support, symmetric about R_p
    N = dd.pearson4_profile(Rp + s, 1e13, Rp, dRp, gamma, beta)
    Q = np.trapezoid(N, s)
    m1 = np.trapezoid(s * N, s) / Q
    m2 = np.trapezoid((s - m1) ** 2 * N, s) / Q
    m3 = np.trapezoid((s - m1) ** 3 * N, s) / Q
    m4 = np.trapezoid((s - m1) ** 4 * N, s) / Q
    assert Q == pytest.approx(1e13, rel=1e-4)                   # normalized to the dose over the full line
    assert m1 == pytest.approx(0.0, abs=1e-3 * dRp)            # mean = R_p (exact by construction)
    assert m2 == pytest.approx(dRp ** 2, rel=1e-3)            # variance = σ² (exact by construction)
    assert m3 / m2 ** 1.5 == pytest.approx(gamma, abs=3e-3)   # skewness = γ
    assert m4 / m2 ** 2 == pytest.approx(beta, rel=3e-3)      # kurtosis = β


def test_boron_pearson_peak_is_deeper_than_Rp():
    # The slice-2 discriminator (sign-robust), stacking on slice-1's buried peak: boron's NEGATIVE skew
    # displaces the mode DEEPER than R_p (mode = R_p + b1, b1 > 0), where slice-1's symmetric Gaussian
    # peaks exactly at R_p. The profile is still buried (rises from the surface) — an ASYMMETRIC bury.
    imp = dd.Implant(dose=1e13, energy_keV=100.0, species="B", shape="pearson")
    Rp, dRp, gamma, beta = imp.moments()
    b0, b1, b2 = dd._pearson4_coeffs(dRp, gamma, beta)
    assert b1 > 0.0                                             # mode offset deeper (γ < 0)
    grid = dd.uniform_grid(2.0 * UM, 4000)                      # fine grid to resolve the ~0.1σ shift
    N = dd.implant_profile(grid.centers, imp)
    i_peak = int(np.argmax(N))
    assert grid.centers[i_peak] == pytest.approx(Rp + b1, abs=2.0 * grid.widths[0])  # mode at R_p+b1
    assert grid.centers[i_peak] > Rp                            # DEEPER than the projected range
    assert np.all(np.diff(N[: i_peak + 1]) > 0.0)              # still rises from the surface (buried)


def test_boron_pearson_tail_is_heavier_toward_the_surface():
    # "Skewed up" (Plummer): the negative-skew boron profile carries a HEAVIER tail toward the SURFACE —
    # at matched distances k·σ either side of R_p the surface side exceeds the deep side (the physical
    # content of γ < 0, independent of the exact magnitude).
    Rp, dRp, gamma, beta = dd.range_moments("B", 100.0)
    for k in (2.0, 3.0, 4.0):
        surface = dd.pearson4_profile(np.array([Rp - k * dRp]), 1e13, Rp, dRp, gamma, beta)[0]
        deep = dd.pearson4_profile(np.array([Rp + k * dRp]), 1e13, Rp, dRp, gamma, beta)[0]
        assert surface > deep, k


def test_pearson4_type_iv_guard():
    # The honest guard: (γ, β) outside the type-IV region (real denominator roots, or the b2=0 Gaussian
    # limit) RAISES rather than silently take a negative-base power. β near the Gaussian 3 is out of
    # region — the reason β is pinned into the ≳4 band (the flagged house calibration).
    Rp, dRp = dd.range_statistics("B", 100.0)
    for gamma, beta in ((0.0, 3.0), (-0.4, 3.3), (0.9, 3.2)):
        with pytest.raises(ValueError):
            dd.pearson4_profile(np.array([Rp]), 1e13, Rp, dRp, gamma, beta)


def test_skew_kurtosis_boron_sign_trend_and_guards():
    # The CITED content: boron skew is negative at device energies and grows MORE negative with energy
    # (β constant, > the Gaussian 3). Magnitudes are flagged; the sign and trend are the assertions.
    g50, b50 = dd.skew_kurtosis("B", 50.0)
    g200, b200 = dd.skew_kurtosis("B", 200.0)
    assert g50 < 0.0 and g200 < 0.0                            # negative at device energies (cited)
    assert g200 < g50                                          # more negative with energy (cited trend)
    assert b50 == b200 > 3.0                                   # kurtosis pinned into the type-IV band
    with pytest.raises(ValueError):
        dd.skew_kurtosis("P", 100.0)                           # no fabricated skew for un-tabulated species
    with pytest.raises(ValueError):
        dd.skew_kurtosis("B", 0.0)


def test_implant_pearson_requires_skew_data_and_valid_shape():
    # Fail early at construction: shape="pearson" for a species without skew data (P), or an unknown
    # shape, raises — we never silently produce a garbage or fabricated profile.
    with pytest.raises(ValueError):
        dd.Implant(dose=1e13, energy_keV=100.0, species="P", shape="pearson")
    with pytest.raises(ValueError):
        dd.Implant(dose=1e13, energy_keV=100.0, species="B", shape="bogus")


def test_pearson_ic_two_sided_truncation_and_structural_conservation():
    # Flagged: the Pearson-IV IC loses dose to BOTH the surface and the (heavier, power-law) deep tail,
    # so its grid-dose sits below Q even for a mid-depth implant. Tight: the sealed drive-in nonetheless
    # conserves whatever grid-dose it is HANDED to machine precision (structural, shape-independent).
    imp = dd.Implant(dose=1e14, energy_keV=100.0, species="B", shape="pearson")
    grid = dd.uniform_grid(3.0 * UM, 900)
    ic = dd.implant_ic(grid, imp)
    assert ic.stage == "implant"
    assert ic.dose < imp.dose                                  # two-sided truncation (< Q, flagged)
    ic2, drivein = dd.two_step("B", implant=imp, length_um=3.0)
    assert drivein.dose == pytest.approx(ic2.dose, rel=1e-10)  # structural conservation (machine precision)


def test_two_step_pearson_vs_gaussian_ic_differ_by_the_skew():
    # The observable through the SAME pipeline (no new solver): a Pearson-IV implant and a Gaussian
    # implant of identical dose/energy give different ICs — the Pearson peak buried deeper (the skew) —
    # while a shape="gaussian" implant is bit-for-bit the slice-1 path.
    g = dd.Implant(dose=1e13, energy_keV=100.0, species="B")               # gaussian (default)
    p = dd.Implant(dose=1e13, energy_keV=100.0, species="B", shape="pearson")
    grid = dd.uniform_grid(2.0 * UM, 4000)
    Ng = dd.implant_profile(grid.centers, g)
    Np = dd.implant_profile(grid.centers, p)
    assert not np.allclose(Ng, Np)                             # the skew is a real, visible difference
    assert grid.centers[int(np.argmax(Np))] > grid.centers[int(np.argmax(Ng))]  # Pearson peak deeper
