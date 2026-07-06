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
from chip import junction as jn


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


# --------------------------------------------------------------------------- #
# Slice 3 — the channeling tail (the deep exponential → deeper junction → punchthrough)
# --------------------------------------------------------------------------- #
# Physics: in a single-crystal target a fraction of the dose steers down the open low-index channels and
# stops in a DEEP exponential tail past R_p (Plummer §8; Campbell §5). It is a FAILURE MODE — the tail
# drags the annealed junction x_j DEEPER → source/drain punchthrough — suppressed by tilting off-axis (the
# 7° convention). Modelled as a two-population partition N = (1−f)·primary + f·Q·tail (dose-conserving),
# f = f0·e^(−tilt/τ). Triad:
#   * Tight/sign-robust: (a) the SEAM — channel=None is the exact slice-1/2 primary, bit-for-bit; (b) dose
#     — the partition ∫N dx = Q analytically, and the sealed drive-in conserves the grid-dose (structural);
#     (c) the deeper-junction discriminator — a long tail (λ ≫ ΔR_p) deepens the ANNEALED x_j (asserted
#     through two_step, the punchthrough consumer); (d) tilt monotonicity — more tilt ⇒ shallower x_j.
#   * Flagged: the f0/λ/τ magnitudes (house-calibrated; the SIGN — channeling deepens, tilt suppresses —
#     is the cited part). The two-sided (surface + deep-tail) grid-dose truncation, as for Pearson.
def test_channel_none_is_bit_for_bit_seam():
    # The seam: channel defaults to None and the profile is the exact slice-1/2 primary, bit-for-bit, for
    # BOTH shapes — the whole slice-1/2 suite is byte-identical (the opt-in discipline, cf. implant=None).
    x = dd.uniform_grid(2.0 * UM, 800).centers
    for imp in (dd.Implant(dose=1e14, energy_keV=100.0, species="B"),
                dd.Implant(dose=1e14, energy_keV=100.0, species="B", shape="pearson")):
        assert imp.channel is None
        Rp, dRp = imp.range_statistics()
        if imp.shape == "gaussian":
            primary = (imp.dose / (math.sqrt(2.0 * math.pi) * dRp)) * np.exp(-((x - Rp) ** 2) / (2.0 * dRp ** 2))
        else:
            gamma, beta = dd.skew_kurtosis("B", 100.0)
            primary = dd.pearson4_profile(x, imp.dose, Rp, dRp, gamma, beta)
        assert np.array_equal(dd.implant_profile(x, imp), primary)


def test_channeled_fraction_sign_trend_and_guards():
    # The cited content: f = f0 at 0° (on-axis, full channeling), strictly DECREASING with tilt (the 7°
    # convention suppresses it), always a valid partition weight (< f0 < 1). Magnitudes flagged.
    f0 = 0.1
    assert dd.channeled_fraction(f0, 0.0) == pytest.approx(f0)          # on-axis = the full fraction
    tilts = [0.0, 3.5, 7.0, 10.0]
    fs = [dd.channeled_fraction(f0, t) for t in tilts]
    assert all(b < a for a, b in zip(fs, fs[1:]))                       # strictly decreasing in tilt
    assert 0.0 < fs[-1] < f0 < 1.0                                      # a valid partition weight
    with pytest.raises(ValueError):
        dd.channeled_fraction(1.5, 0.0)                                 # fraction out of (0,1)
    with pytest.raises(ValueError):
        dd.channeled_fraction(0.1, -1.0)                               # negative tilt


def test_channeling_validates_inputs():
    with pytest.raises(ValueError):
        dd.Channeling(fraction=0.0, length_um=0.2)                      # f0 must be in (0,1)
    with pytest.raises(ValueError):
        dd.Channeling(fraction=1.0, length_um=0.2)
    with pytest.raises(ValueError):
        dd.Channeling(fraction=0.1, length_um=0.0)                      # positive tail length
    with pytest.raises(ValueError):
        dd.Channeling(fraction=0.1, length_um=0.2, tilt_deg=-1.0)       # tilt ≥ 0
    with pytest.raises(ValueError):
        dd.Implant(dose=1e13, energy_keV=100.0, channel="not-a-channeling")  # wrong type


def test_channeling_tail_is_unit_area_deep_side_only():
    # The tail is a UNIT-AREA deep-side exponential: zero shallower than R_p (a Heaviside deep side),
    # positive beyond, and ∫_{R_p}^∞ tail dx = 1 (so scaling by Q puts exactly Q under the tail).
    Rp = 0.3 * UM
    lam = 0.25 * UM
    x = np.linspace(0.0, 60.0 * lam, 3_000_001)
    tail = dd.channeling_tail(x, Rp, lam)
    assert np.all(tail[x < Rp] == 0.0)                                 # nothing on the surface side
    assert np.all(tail[x > Rp] > 0.0)                                  # positive deep side
    assert np.trapezoid(tail, x) == pytest.approx(1.0, rel=1e-4)       # unit area


def test_channeling_partitions_dose_analytically():
    # Dose (tight, analytic): the two-population split N = (1−f)·primary + f·Q·tail conserves ∫N dx = Q
    # exactly — the channeled ions come OUT of the primary, not on top (adding-on-top would violate dose).
    ch = dd.Channeling(fraction=0.15, length_um=0.25, tilt_deg=0.0)
    imp = dd.Implant(dose=1e14, energy_keV=100.0, species="B", channel=ch)
    Rp, dRp = imp.range_statistics()
    s = np.linspace(-40.0 * dRp, 220.0 * dRp, 2_000_001)               # full support (covers the long tail)
    Q = np.trapezoid(dd.implant_profile(Rp + s, imp), s)
    assert Q == pytest.approx(imp.dose, rel=1e-4)                       # partition conserves Q analytically


def test_channeling_deepens_the_annealed_junction():
    # THE slice-3 discriminator (sign-robust): a long channeling tail (λ ≫ ΔR_p) dominates the super-
    # exponential Gaussian in the DEEP-TAIL region where the junction lives, so the ANNEALED x_j (through
    # the constant-D drive-in — the punchthrough consumer) sits DEEPER than the no-channel implant. N_B is
    # taken in the tail (the z≈3 region junction_depth assumes); at a high N_B near R_p channeling can push
    # x_j shallower (the flagged trap) — this asserts only the deep-junction sign.
    base = dd.Implant(dose=1e14, energy_keV=100.0, species="B")                          # no channel
    ch = dd.Channeling(fraction=0.15, length_um=0.25, tilt_deg=0.0)
    imp = dd.Implant(dose=1e14, energy_keV=100.0, species="B", channel=ch)
    _, dRp = base.range_statistics()
    assert ch.length_cm / dRp > 3.0                                    # λ ≫ ΔR_p (the tail-dominant regime)
    N_B = 1e15                                                          # background in the deep tail
    _, dv_base = dd.two_step("B", implant=base, length_um=4.0, n_cells=1200)
    _, dv_ch = dd.two_step("B", implant=imp, length_um=4.0, n_cells=1200)
    xj_base = jn.junction_depth(dv_base.x, dv_base.N, N_B)
    xj_ch = jn.junction_depth(dv_ch.x, dv_ch.N, N_B)
    assert np.isfinite(xj_base) and np.isfinite(xj_ch)                 # both junctions resolve in-domain
    assert xj_ch > xj_base                                             # channeling drags the junction DEEPER


def test_tilt_suppresses_the_channeling_junction_deepening():
    # Tilt monotonicity (the second tight leg): more tilt ⇒ smaller channeled fraction ⇒ shallower x_j.
    # The 7° convention pulls the junction back toward (never below) the no-channel case — the physical
    # reason wafers are implanted off-axis (punchthrough control).
    base = dd.Implant(dose=1e14, energy_keV=100.0, species="B")
    on_axis = dd.Implant(dose=1e14, energy_keV=100.0, species="B",
                         channel=dd.Channeling(0.15, 0.25, tilt_deg=0.0))
    tilted = dd.Implant(dose=1e14, energy_keV=100.0, species="B",
                        channel=dd.Channeling(0.15, 0.25, tilt_deg=7.0))
    N_B = 1e15
    xjs = []
    for imp in (base, on_axis, tilted):
        _, dv = dd.two_step("B", implant=imp, length_um=4.0, n_cells=1200)
        xjs.append(jn.junction_depth(dv.x, dv.N, N_B))
    xj_base, xj_on, xj_tilt = xjs
    assert xj_on > xj_tilt > xj_base                                   # tilt pulls x_j back toward no-channel


def test_channeling_grid_dose_two_sided_truncation_and_structural_conservation():
    # Flagged: on a finite grid the channeling IC loses dose off BOTH ends (surface truncation of the
    # primary + the long tail running off the deep boundary), so the grid-dose sits below Q. Tight: the
    # sealed drive-in nonetheless conserves whatever grid-dose it is HANDED to machine precision.
    ch = dd.Channeling(fraction=0.2, length_um=0.3, tilt_deg=0.0)
    imp = dd.Implant(dose=1e14, energy_keV=100.0, species="B", channel=ch)
    grid = dd.uniform_grid(1.5 * UM, 900)                              # domain shallower than the full tail
    ic = dd.implant_ic(grid, imp)
    assert ic.stage == "implant"
    assert ic.dose < imp.dose                                         # two-sided truncation (< Q, flagged)
    ic2, drivein = dd.two_step("B", implant=imp, length_um=1.5, n_cells=900)
    assert drivein.dose == pytest.approx(ic2.dose, rel=1e-10)          # structural conservation


def test_channeling_applies_to_both_shapes():
    # The channeling partition rides on WHICHEVER primary — Gaussian or Pearson-IV — since it scales the
    # whole primary by (1−f). Both differ from their no-channel selves by the same added deep tail.
    ch = dd.Channeling(fraction=0.15, length_um=0.25, tilt_deg=0.0)
    grid = dd.uniform_grid(3.0 * UM, 1500)
    for shape in ("gaussian", "pearson"):
        plain = dd.Implant(dose=1e14, energy_keV=100.0, species="B", shape=shape)
        chan = dd.Implant(dose=1e14, energy_keV=100.0, species="B", shape=shape, channel=ch)
        Np, Nc = dd.implant_profile(grid.centers, plain), dd.implant_profile(grid.centers, chan)
        Rp, _ = plain.range_statistics()
        deep = grid.centers > Rp + 0.3 * UM                            # well into the tail region
        assert np.all(Nc[deep] > Np[deep])                            # the channel adds a deep-side tail


# --------------------------------------------------------------------------- #
# Slice 4 — damage → leakage (the residual displacement damage an incomplete anneal leaves)
# --------------------------------------------------------------------------- #
# Physics: the ions smash the lattice on the way in (nuclear collisions → Frenkel pairs); the modified
# Kinchin–Pease / NRT count N_d = 0.8·E_n/(2·E_d) (E_n = ν·E) sets the displacement damage, which anneals
# out with a separate Arrhenius. The residual-after-anneal density feeds chip.lifetime's 1/τ channel.
#   * Tight/sign-robust: (a) N_d monotone in energy + HEAVIER ion (P) damages more than lighter (B); (b)
#     the recovery seam — r = 1 at t = 0 (as-implanted), monotone DECREASING in anneal T and t; (c) damage
#     density monotone in dose; (d) anneal recovers it (density falls with anneal T) — the discriminator.
#   * Flagged: ν, E_d, the recovery Ea/k0 magnitudes (the SIGN — more dose/energy/mass → more damage, more
#     anneal → less — is cited; NRT form + E_d≈15 eV cited).
def test_displacements_per_ion_nrt_form_and_energy_monotone():
    # N_d = 0.8·E_n/(2·E_d), E_n = ν·E: the closed NRT form, and monotone increasing in energy.
    E = 100.0
    nu = dd._NUCLEAR_STOPPING_FRACTION["B"]
    expected = dd._NRT_EFFICIENCY * (nu * E * 1e3) / (2.0 * dd._SI_DISPLACEMENT_ENERGY_EV)
    assert dd.displacements_per_ion("B", E) == pytest.approx(expected)
    Nd = [dd.displacements_per_ion("B", e) for e in (10.0, 50.0, 100.0, 200.0)]
    assert all(a < b for a, b in zip(Nd, Nd[1:]))                     # more energy → more displacements


def test_heavier_ion_displaces_more_than_lighter():
    # The cited SIGN: a HEAVIER ion (P) sheds more of its energy to nuclear stopping (larger ν) → more
    # displacement damage than the lighter B at equal energy (the same physics that makes B penetrate deeper).
    for E in (30.0, 100.0, 200.0):
        assert dd.displacements_per_ion("P", E) > dd.displacements_per_ion("B", E)


def test_displacements_per_ion_guards():
    with pytest.raises(ValueError):
        dd.displacements_per_ion("B", 0.0)                            # non-positive energy
    with pytest.raises(ValueError):
        dd.displacements_per_ion("Xe", 100.0)                        # no ν → no fabricated damage


def test_damage_residual_fraction_seam_and_monotone_recovery():
    # The recovery seam: no anneal (t = 0) leaves the FULL as-implanted damage (r = 1). With anneal, r is
    # in (0, 1] and DECREASES monotonically with both anneal temperature and time (the cited recovery SIGN).
    assert dd.damage_residual_fraction(700.0, 0.0) == 1.0             # t = 0 → full damage (the seam)
    r_by_T = [dd.damage_residual_fraction(T, 1800.0) for T in (500.0, 700.0, 900.0, 1100.0)]
    assert all(0.0 < r <= 1.0 for r in r_by_T)
    assert all(b < a for a, b in zip(r_by_T, r_by_T[1:]))            # hotter anneal → less residual
    r_by_t = [dd.damage_residual_fraction(750.0, t) for t in (60.0, 300.0, 1800.0, 7200.0)]
    assert all(b < a for a, b in zip(r_by_t, r_by_t[1:]))            # longer anneal → less residual


def test_damage_residual_fraction_guards():
    with pytest.raises(ValueError):
        dd.damage_residual_fraction(700.0, -1.0)                      # negative anneal time
    with pytest.raises(ValueError):
        dd.damage_residual_fraction(-400.0, 1800.0)                  # below absolute zero


def test_implant_damage_density_dose_monotone_and_as_implanted_default():
    # The characteristic residual trap density: with no anneal args it is the FULL as-implanted damage
    # (r = 1), and it scales linearly with dose Q (more ions → more displacement damage).
    peaks = []
    for Q in (1e13, 1e14, 1e15):
        imp = dd.Implant(dose=Q, energy_keV=100.0, species="B")
        peaks.append(dd.implant_damage_density(imp))
    assert all(a < b for a, b in zip(peaks, peaks[1:]))              # more dose → more damage
    # linear in Q: doubling the dose doubles the density (the areal displacement dose is Q·N_d).
    base = dd.implant_damage_density(dd.Implant(dose=1e14, energy_keV=100.0, species="B"))
    dbl = dd.implant_damage_density(dd.Implant(dose=2e14, energy_keV=100.0, species="B"))
    assert dbl == pytest.approx(2.0 * base)


def test_anneal_recovers_the_implant_damage():
    # THE slice-4 discriminator (sign-robust): the residual damage density falls monotonically as the
    # anneal temperature rises — the leakage anneals OUT (unlike the metals/dislocations). The as-implanted
    # (no-anneal) density is the ceiling; a hot anneal drives it toward zero.
    imp = dd.Implant(dose=1e14, energy_keV=100.0, species="B")
    as_implanted = dd.implant_damage_density(imp)
    residuals = [
        dd.implant_damage_density(imp, anneal_T_celsius=T, anneal_time_s=1800.0)
        for T in (500.0, 700.0, 900.0, 1050.0)
    ]
    assert all(r < as_implanted for r in residuals)                 # any anneal removes some damage
    assert all(b < a for a, b in zip(residuals, residuals[1:]))     # hotter anneal → less residual
