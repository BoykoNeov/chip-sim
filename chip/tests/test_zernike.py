"""Chip v1.10 validation: lithographic **Zernike aberrations** — coma, astigmatism & spherical.

The Phase-3 §-named scope edge ("aberration-free pupil apart from defocus"), **promoted** — and it
lands on the **same finding as v1.4**: a Zernike aberration is a pure **phase** on the pupil, so it
lives inside the existing Fourier-optics machinery (``litho.zernike_phase`` multiplies each collected
order at its pupil-slice coordinate ``u = f_total/f_cut``; ``abbe_image``/``expose_grating`` thread an
``Aberrations`` dataclass) — no new code path. Like the rest of litho there is no engine underneath, so
these tests carry the whole mini-triad:

* **Analytic (tight).** (a) The degenerate seam — ``aberrations=None`` (or all-zero) is the unaberrated
  image **bit-for-bit**. (b) **Parity** — an EVEN aberration (astigmatism / spherical) leaves a
  symmetric two-beam pair invariant to machine precision (equal even phase factors out of ``|Σ|²``);
  the ODD coma gives the two beams *opposite* phase → a **pure lateral fringe shift**, contrast
  preserved. (c) **The coma↔defocus discriminator** — both give the same fundamental *magnitude*
  ``4c₀c₁cos φ`` (invisible to the cos-only :func:`~chip.litho.fundamental_amplitude`), but the
  **complex** fundamental phase is exactly the ±1 order's aberration phase: ``0`` for defocus, the
  coma shift for coma.
* **Conservation (tight) — aberrations are unitary.** Phase-only ⇒ ``|amplitude|²`` is unchanged ⇒ the
  power balance ``mean(image) = Σ|c_m|² = transmitted_power`` holds at **every** aberration level, to
  machine precision (``transmitted_power`` never sees the phase).
* **Benchmark (loose) — the litho-native signatures.** Coma → pattern placement error (the fringe
  shift) + an asymmetric image the PEB cell refuses; astigmatism → the **H↔V best-focus split** (a
  defocus offset cannot mimic it — the thing that makes astig ≠ defocus in 1-D); spherical → **pitch-
  dependent best focus** (pure defocus best focus is pitch-independent at z = 0).
"""
import numpy as np
import pytest

from chip import litho as L

LAMBDA = 193.0      # nm, ArF — the demo system wavelength used throughout
NA = 0.85


# --------------------------------------------------------------------------- #
# Analytic: the degenerate seam — no aberration is the v1 image, bit-for-bit
# --------------------------------------------------------------------------- #
def test_no_aberration_is_the_v1_image_bit_for_bit():
    # The seam (the v1.x discipline): aberrations=None AND an all-zero Aberrations() must both reproduce
    # the unaberrated image EXACTLY — zernike_phase short-circuits to the float 1.0, so the collected
    # orders stay untouched and coherent_image is the identical computation. array_equal, not allclose.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    p = 350.0
    x = np.linspace(0.0, p, 512, endpoint=False)
    orders = L.grating_orders(p)
    src = L.conventional_source(img)
    base = L.abbe_image(x, orders, img, source_fs=src)
    assert np.array_equal(base, L.abbe_image(x, orders, img, source_fs=src, aberrations=None))
    assert np.array_equal(base, L.abbe_image(x, orders, img, source_fs=src, aberrations=L.Aberrations()))
    # And through the high-level entry: the unaberrated PrintedFeature is unchanged.
    assert L.expose_grating(img, p).cd_nm == L.expose_grating(img, p, aberrations=L.Aberrations()).cd_nm
    # zernike_phase itself is the literal 1.0 for the zero pupil (so the multiply is a no-op).
    assert L.zernike_phase(0.012, img, None) == 1.0
    assert L.zernike_phase(0.012, img, L.Aberrations()) == 1.0
    assert L.Aberrations().is_zero and not L.Aberrations(coma=0.1).is_zero


# --------------------------------------------------------------------------- #
# Analytic: parity — even aberrations leave a symmetric pair invariant; coma shifts it
# --------------------------------------------------------------------------- #
def _aberrated_orders_image(x, orders, img, ab):
    """A coherent image of explicit orders with each order's Zernike phase applied (test helper)."""
    return L.coherent_image(x, [(f, c * L.zernike_phase(f, img, ab)) for (f, c) in orders])


def test_even_aberration_leaves_a_symmetric_dipole_invariant():
    # Parity, the even half: a symmetric two-beam pair at ±u shares an IDENTICAL even-aberration phase
    # (astig ∝ u², spherical ∝ 6u⁴−6u² are even in u) → it factors out of |Σ|² → the image is bit-for-bit
    # the same at every coefficient (the defocus-dipole-invariance story of v1.4, now driven by PARITY).
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    fc = img.f_cut
    # Astigmatism at the pupil RIM (u = ±1 ⇒ u² = 1, a clean NONZERO even phase).
    x = np.linspace(0.0, 1.0 / fc, 1024, endpoint=False)
    rim = [(-fc, 1.0), (fc, 1.0)]
    base = _aberrated_orders_image(x, rim, img, None)
    for a in (0.15, 0.4, -0.3):
        np.testing.assert_allclose(_aberrated_orders_image(x, rim, img, L.Aberrations(astigmatism=a)),
                                   base, atol=1e-12)
    # Spherical at the rim is TRIVIAL (6−6 = 0 ⇒ zero phase, tests nothing) — the advisor's trap. Use an
    # INTERIOR pair u = ±1/√2 where the balanced form peaks (6·¼ − 6·½ = −1.5), a real nonzero even phase.
    assert L.zernike_phase(fc, img, L.Aberrations(spherical=0.3)) == 1.0          # rim: trivially flat
    fi = fc / np.sqrt(2.0)
    assert abs(L.zernike_phase(fi, img, L.Aberrations(spherical=0.3)) - 1.0) > 0.1  # interior: nonzero
    xi = np.linspace(0.0, 1.0 / fi, 1024, endpoint=False)
    interior = [(-fi, 1.0), (fi, 1.0)]
    base_i = _aberrated_orders_image(xi, interior, img, None)
    for s in (0.2, 0.5, -0.35):
        np.testing.assert_allclose(_aberrated_orders_image(xi, interior, img, L.Aberrations(spherical=s)),
                                   base_i, atol=1e-12)


def test_odd_coma_shifts_a_symmetric_dipole_keeps_its_contrast():
    # Parity, the odd half: coma ∝ 3u³−2u is ODD, so the ±u beams get OPPOSITE phase ±φ_c → the dipole
    # |e^{iφ}e^{2πif x} + e^{−iφ}e^{−2πif x}|² = 4cos²(2πf x + φ_c) — a PURE lateral shift, full contrast
    # preserved. (Where v1.4's even defocus left the dipole invariant, odd coma TRANSLATES it.)
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    fc = img.f_cut
    x = np.linspace(0.0, 1.0 / fc, 2048, endpoint=False)
    rim = [(-fc, 1.0), (fc, 1.0)]
    base = _aberrated_orders_image(x, rim, img, None)
    for c in (0.1, 0.25):
        coma = _aberrated_orders_image(x, rim, img, L.Aberrations(coma=c))
        assert not np.allclose(coma, base, atol=1e-6)            # NOT invariant — it moved
        assert L.image_contrast(coma) == pytest.approx(1.0, abs=1e-3)   # …but full contrast (a shift)
        # I = 4cos²(2π·fc·x + φ_c), φ_c the +fc beam's coma phase ⇒ the peak shifts by −φ_c/(2π·fc). The
        # cos² has period p = 1/(2·fc), so compare peak positions on that ring (modular distance).
        phi_c = 2.0 * np.pi * c * (3.0 - 2.0)                     # u=+1 ⇒ 3u³−2u = 1
        period = 1.0 / (2.0 * fc)
        x_expected = (-phi_c / (2.0 * np.pi * fc)) % period
        d = abs(x[np.argmax(coma)] % period - x_expected) % period
        assert min(d, period - d) < 0.02 * period


# --------------------------------------------------------------------------- #
# Analytic: the coma↔defocus discriminator — the complex fundamental PHASE (the load-bearing anchor)
# --------------------------------------------------------------------------- #
def _three_beam_setup(p=350.0):
    """A pitch where on-axis coherent imaging collects EXACTLY {0, ±1} → the closed-form three-beam case."""
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    assert img.pitch_min_coherent <= p < 3.0 * img.pitch_min_coherent
    x = np.linspace(0.0, p, 256, endpoint=False)
    orders = L.grating_orders(p)
    u1 = (1.0 / p) / img.f_cut                                    # the +1 order's pupil-slice coordinate
    return img, p, x, orders, u1


def test_coma_fundamental_phase_is_exactly_the_order_aberration_phase():
    # THE load-bearing anchor (the advisor's correction): the cos-only fundamental_amplitude returns
    # 4c₀c₁cos φ for BOTH coma and defocus — it cannot tell them apart. The COMPLEX fundamental can: its
    # phase is EXACTLY the +1 order's coma phase φ_c = 2π·coma·(3u³−2u), to machine precision, while its
    # real part still equals fundamental_amplitude (consistency). Coma is a pattern PLACEMENT error.
    img, p, x, orders, u1 = _three_beam_setup()
    src = L.on_axis_source()
    for c in (0.05, 0.15, -0.2):
        ab = L.Aberrations(coma=c)
        phi_c = 2.0 * np.pi * c * (3.0 * u1 ** 3 - 2.0 * u1)
        I = L.abbe_image(x, orders, img, source_fs=src, aberrations=ab)
        Fc = L.fundamental_complex(x, I, p)
        assert np.angle(Fc) == pytest.approx(phi_c, abs=1e-12)            # the fringe shift, exact
        assert Fc.real == pytest.approx(L.fundamental_amplitude(x, I, p), abs=1e-12)  # Re ≡ cos-projection


def test_defocus_is_even_so_its_fundamental_phase_is_zero():
    # The discriminator's other arm: a pure (even) defocus leaves the on-axis three-beam image symmetric,
    # so its complex-fundamental PHASE is 0 (no fringe shift) — even though its fundamental MAGNITUDE
    # tracks 4c₀c₁cos φ exactly like coma's. Same |F|, different arg → that is how you separate them.
    img, p, x, orders, _ = _three_beam_setup()
    src = L.on_axis_source()
    for z in (60.0, 150.0, -120.0):
        I = L.abbe_image(x, orders, img, source_fs=src, defocus_nm=z)
        assert np.angle(L.fundamental_complex(x, I, p)) == pytest.approx(0.0, abs=1e-9)


def test_coma_and_defocus_share_a_fundamental_magnitude_invisible_to_cos_projection():
    # Pin the actual ambiguity the discriminator resolves: a coma and a defocus can be tuned to the SAME
    # fundamental magnitude (here trivially both ≈ the unaberrated 4c₀c₁ at small phase), so the cos-only
    # fundamental_amplitude is NOT a coma/defocus discriminator — only the quadrature (phase) is.
    img, p, x, orders, u1 = _three_beam_setup()
    src = L.on_axis_source()
    I_coma = L.abbe_image(x, orders, img, source_fs=src, aberrations=L.Aberrations(coma=0.12))
    I_def = L.abbe_image(x, orders, img, source_fs=src, defocus_nm=0.0)   # in-focus, even
    # |fundamental| close (cos-projection can't separate), but the PHASE differs (coma shifted, defocus 0).
    assert abs(abs(L.fundamental_complex(x, I_coma, p)) - abs(L.fundamental_complex(x, I_def, p))) < 0.05
    assert abs(np.angle(L.fundamental_complex(x, I_coma, p))) > 0.3
    assert abs(np.angle(L.fundamental_complex(x, I_def, p))) < 1e-9


# --------------------------------------------------------------------------- #
# Conservation: aberrations are unitary — image DC = transmitted power at EVERY coefficient
# --------------------------------------------------------------------------- #
def test_aberrations_conserve_power_at_every_coefficient():
    # The conservation leg, extended from defocus for free: every Zernike aberration is phase-only, so
    # |c_m|² is untouched and the Parseval power balance mean(image) = Σ|c_m|² = transmitted_power holds
    # at EVERY coefficient — to machine precision. transmitted_power never sees the phase (it sums |c|²),
    # so this is a genuine check the build added PHASE not amplitude (a bug scaling an order breaks it).
    img = L.Imaging(LAMBDA, NA, sigma=0.6)
    p = 180.0
    orders = L.grating_orders(p, n_orders=15)
    src = L.conventional_source(img, n_source=21)
    x = np.linspace(0.0, p, 4096, endpoint=False)
    power = L.transmitted_power(orders, img, source_fs=src)               # phase-free reference
    for ab in (L.Aberrations(coma=0.3), L.Aberrations(astigmatism=0.5), L.Aberrations(spherical=0.4),
               L.Aberrations(coma=0.2, astigmatism=0.3, spherical=0.15, grating_azimuth_deg=30.0)):
        I = L.abbe_image(x, orders, img, source_fs=src, aberrations=ab)
        assert I.mean() == pytest.approx(power, rel=1e-10)


# --------------------------------------------------------------------------- #
# Benchmark (loose): the litho-native aberration signatures
# --------------------------------------------------------------------------- #
def _best_focus(img, orders, x, p, ab, zspan=200.0, n=401):
    """The defocus z that maximizes the fundamental magnitude (the empirical best-focus plane)."""
    zs = np.linspace(-zspan, zspan, n)
    fund = [abs(L.fundamental_complex(x, L.abbe_image(x, orders, img, source_fs=L.on_axis_source(),
                                                      defocus_nm=z, aberrations=ab), p)) for z in zs]
    return zs[int(np.argmax(fund))]


def test_astigmatism_splits_best_focus_between_orientations():
    # Astigmatism's SIGNATURE — the thing a defocus offset cannot mimic, and what makes astig ≠ defocus
    # in 1-D: horizontal (φ_g=0) and vertical (φ_g=90°) lines focus at OPPOSITE defocus planes (cos2φ_g
    # flips sign), straddling z=0. A pure defocus offset shifts BOTH the same way; no aberration → both
    # at z=0. This is why you need two orientations to tell astigmatism from a focus error.
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    p = 350.0
    x = np.linspace(0.0, p, 256, endpoint=False)
    orders = L.grating_orders(p)
    bf0 = _best_focus(img, orders, x, p, None)
    bf_h = _best_focus(img, orders, x, p, L.Aberrations(astigmatism=0.25, grating_azimuth_deg=0.0))
    bf_v = _best_focus(img, orders, x, p, L.Aberrations(astigmatism=0.25, grating_azimuth_deg=90.0))
    assert bf0 == pytest.approx(0.0, abs=2.0)            # unaberrated: best focus at z=0
    assert bf_h * bf_v < 0                               # H and V straddle focus — opposite signs
    assert abs(bf_h) > 20.0 and abs(bf_v) > 20.0         # …by a meaningful, symmetric amount
    assert bf_h == pytest.approx(-bf_v, abs=2.0)


def test_spherical_makes_best_focus_pitch_dependent():
    # Spherical's SIGNATURE: the balanced −6u² term shifts best focus by an amount that depends on WHERE
    # the orders ride the pupil — i.e. on the pitch. Two pitches focus at DIFFERENT planes under spherical,
    # but at the SAME plane (z=0) under pure defocus. (This is why spherical hurts a mix of feature sizes:
    # you cannot focus them all at once.)
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    sph = L.Aberrations(spherical=0.4)
    def bf(pp, ab):
        x = np.linspace(0.0, pp, 256, endpoint=False)
        return _best_focus(img, L.grating_orders(pp), x, pp, ab)
    bf_fine_sph, bf_coarse_sph = bf(300.0, sph), bf(450.0, sph)
    assert abs(bf_fine_sph - bf_coarse_sph) > 30.0       # spherical: best focus moves with pitch
    # …while with no aberration both pitches share best focus at z=0 (pitch-independent).
    assert bf(300.0, None) == pytest.approx(0.0, abs=2.0)
    assert bf(450.0, None) == pytest.approx(0.0, abs=2.0)


def test_aberration_threads_through_expose_grating_and_degrades_the_feature():
    # End-to-end through the high-level entry (the non-PEB CD path): an aberration must reach the printed
    # PrintedFeature, not silently no-op. Astigmatism acts like a defocus-curvature, so at nominal focus it
    # DEGRADES the image — contrast and NILS fall below the unaberrated feature — confirming the parameter
    # threads abbe_image → metrics. (Coma, by contrast, is a placement error that preserves linewidth.)
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    p = 350.0
    base = L.expose_grating(img, p)
    astig = L.expose_grating(img, p, aberrations=L.Aberrations(astigmatism=0.3))
    assert astig.contrast < base.contrast - 1e-3
    assert astig.nils < base.nils - 1e-3
    assert base.resolved and astig.resolved                  # still a real image, just degraded


def test_coma_asymmetric_image_is_refused_by_the_peb_cell():
    # Consistency with the v1.4 off-axis-defocus refusal: coma breaks the x→−x image symmetry, so the
    # v1.7/v1.9 half-period PEB symmetry cell (which needs a mirror plane) REFUSES it — not silently
    # mis-baked. An EVEN aberration (astigmatism) keeps the mirror plane and bakes fine. (The same
    # Massoud refuse-outside-the-fit discipline.)
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    with pytest.raises(ValueError, match="even .*symmetric"):
        L.expose_grating(img, 300.0, aberrations=L.Aberrations(coma=0.2),
                         peb_diffusion_length_nm=20.0)
    feat = L.expose_grating(img, 300.0, aberrations=L.Aberrations(astigmatism=0.3),
                            peb_diffusion_length_nm=20.0)   # even → mirror plane intact → bakes fine
    assert feat.peb_diffusion_length_nm == 20.0
