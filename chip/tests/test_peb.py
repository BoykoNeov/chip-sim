"""Chip v1.7 validation: **PEB acid-diffusion blur** — the resist back-end rides the engine.

The Phase-3 §-named scope edge ("constant-threshold resist — no acid diffusion / PEB blur"),
**promoted** (the defocus / Massoud / coupling move) — and the architecture finding inverts litho's
founding line: the post-exposure bake IS the program's PDE, so litho (the one chip module that
"does not touch the engine") now rides ``engines.diffusion`` in **acid mode** — ``u`` = latent acid,
constant ``D``, ``Neumann(0)`` both faces (the cited sealed-film BC), on the **half-period symmetry
cell** ``[0, p/2]`` whose Neumann eigenmodes are exactly the even image's cosine harmonics. Unlike
the rest of litho these tests do NOT carry the solver itself (the engine suite does); they carry the
**instantiation**: that the bounded engine solve is the infinite periodic blur, and what the bake
does to the printed feature.

* **Analytic (tight).** (a) The degenerate seam — ``σ = 0`` is the unblurred path **bit-for-bit**
  (``peb_blur`` never touches the engine; ``expose_grating``'s default never enters the PEB branch),
  and the ``σ → 0`` limit lands on the v1 metrics within sampling resolution (no hidden jump).
  (b) A bare **Neumann eigenmode decays by its exact eigenvalue exponential**; a realistic Abbe
  image is attenuated **per harmonic** by the periodic heat kernel ``exp(−2π²k²σ²/p²)`` — engine vs
  closed form, to the documented discretization floor (FV eigenvalue gap ``(kΔx)²/12`` + CN time
  error — measured ~2e-6 on the fundamental).
* **Conservation (tight).** No-flux ⇒ the bake conserves acid dose ⇒ the image mean — and with it
  the v1 Parseval power balance ``mean(image) = Σ|c_m|² = transmitted_power`` — survives **every** σ
  to machine precision; corollary: the default mean-clip dose is blur-invariant.
* **Benchmark (loose) + the PEB window.** Contrast/NILS degrade monotonically over the cited
  20/40/60 nm series and the CD collapses onto the pure-fundamental ``p/2`` readout (blur kills
  harmonics as ``k²``); the cited half-period smoothing rule (``σ ≥ λ/4n``) erases the standing-wave
  ripple while keeping ≥¾ of a 240 nm image's fundamental — and the same rule at 150 nm pitch keeps
  *less than half*: the **PEB window closes at dense pitch** (why modern stacks lean on a BARC).
"""
import numpy as np
import pytest

from chip import litho as L

LAMBDA = 193.0      # nm, ArF — the demo system wavelength used throughout
NA = 0.85
PITCH = 240.0       # the defocus-demo three-beam pitch — dense but resolved (CD = 120 nm)
N_RESIST = 1.70     # representative ArF resist index (illustrative — only λ/2n is load-bearing)


def _peb_image(img, pitch_nm, sigma_nm, n_x=512, n_steps=200):
    """The PEB path's image pipeline, bare (offset grid → half-period blur → mirror) for assertions."""
    orders = L.grating_orders(pitch_nm)
    x = (np.arange(n_x) + 0.5) * (pitch_nm / n_x)
    aerial = L.abbe_image(x, orders, img, source_fs=L.conventional_source(img))
    half = n_x // 2
    blurred = L.peb_blur(aerial[:half], pitch_nm / 2.0, sigma_nm, n_steps=n_steps)
    return x, aerial, np.concatenate([blurred, blurred[::-1]])


def _cos_coeff(x, intensity, pitch_nm, k):
    """The image's k-th cosine Fourier coefficient (the k=1 case is litho.fundamental_amplitude)."""
    return float(2.0 * np.mean(np.asarray(intensity) * np.cos(2.0 * np.pi * k * x / pitch_nm)))


# --------------------------------------------------------------------------- #
# Benchmark pins: the cited constants and the recipe→σ map (citation fidelity)
# --------------------------------------------------------------------------- #
def test_cited_peb_constants_and_diffusion_length():
    # Pin the cited values like k₁/k₂/NILS are pinned (peb-acid-diffusion-source): Mack's PEB
    # profile-simulation series (20/40/60 nm), the standing-wave period λ/2n (Mack eq. (12)),
    # and the recipe-facing σ = √(2·D·t) (Kirchauer §7.1.2 / Mack 1995).
    assert L.PEB_DIFFUSION_SERIES_NM == (20.0, 40.0, 60.0)
    assert L.standing_wave_period(LAMBDA, N_RESIST) == pytest.approx(LAMBDA / (2.0 * N_RESIST))
    assert L.peb_diffusion_length(50.0, 8.0) == pytest.approx(np.sqrt(800.0))
    # Only the product D·t enters: hotter-shorter and cooler-longer bakes with equal D·t blur alike.
    assert L.peb_diffusion_length(100.0, 4.0) == L.peb_diffusion_length(4.0, 100.0)
    with pytest.raises(ValueError):
        L.peb_diffusion_length(-1.0, 8.0)


# --------------------------------------------------------------------------- #
# Analytic: the degenerate seam — σ = 0 is the unblurred path, bit-for-bit
# --------------------------------------------------------------------------- #
def test_peb_zero_is_the_unblurred_path_bit_for_bit():
    # The seam (the v1.x discipline): σ=0 must reproduce the prior path EXACTLY, not approximately.
    # peb_blur short-circuits before ever touching the engine; expose_grating's σ=0 default never
    # enters the PEB branch, so the v1 (defocus-era) PrintedFeature is reproduced field-for-field.
    rng = np.random.default_rng(7)
    latent = 1.0 + rng.random(64)
    out = L.peb_blur(latent, 120.0, 0.0)
    assert np.array_equal(out, latent) and out is not latent        # same values, defensive copy
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    base = L.expose_grating(img, PITCH)
    seam = L.expose_grating(img, PITCH, peb_diffusion_length_nm=0.0)
    assert base == seam                                             # frozen dataclass: all fields
    assert base.peb_diffusion_length_nm == 0.0                      # the readout knows it is unbaked


def test_peb_sigma_to_zero_is_continuous_with_the_seam():
    # The PEB branch samples the period at half-offset cell centers (the no-flux faces must be cell
    # FACES), so its σ→0 limit can differ from the v1 node grid only at sampling resolution — assert
    # the limit lands on the v1 metrics (no hidden jump behind the bit-for-bit short-circuit).
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    base = L.expose_grating(img, PITCH)
    eps = L.expose_grating(img, PITCH, peb_diffusion_length_nm=1.0e-3)
    assert eps.contrast == pytest.approx(base.contrast, abs=1e-4)
    assert eps.nils == pytest.approx(base.nils, abs=1e-3)
    assert eps.cd_nm == pytest.approx(base.cd_nm, abs=1e-2)


# --------------------------------------------------------------------------- #
# Analytic: the engine blur IS the periodic heat kernel (eigenmode + per-harmonic)
# --------------------------------------------------------------------------- #
def test_neumann_eigenmode_decays_by_its_exact_exponential():
    # The tight anchor, bare: cos(jπx/L) is an eigenmode of the sealed domain, so one bake multiplies
    # it by exactly exp(−(jπ/L)²·σ²/2) — engine vs closed form at the documented discretization floor
    # (FV eigenvalue gap (kΔx)²/12 → ~1e-5 for j=1, ~1e-3 for j=3 at these σ; CN time error ≪ both).
    Ldom, n = 120.0, 256
    xc = (np.arange(n) + 0.5) * (Ldom / n)
    for j, tol in ((1, 1e-5), (3, 1e-3)):
        k = j * np.pi / Ldom
        for sigma in (10.0, 25.0):
            latent = 1.0 + 0.5 * np.cos(k * xc)
            out = L.peb_blur(latent, Ldom, sigma)
            exact = 1.0 + 0.5 * np.exp(-0.5 * (k * sigma) ** 2) * np.cos(k * xc)
            np.testing.assert_allclose(out, exact, atol=0.5 * tol)


def test_realistic_image_attenuates_per_harmonic_by_the_periodic_heat_kernel():
    # The composition anchor: a realistic partially-coherent Abbe image (several harmonics) blurred
    # through the half-period engine solve has EACH cosine coefficient multiplied by the periodic
    # heat kernel exp(−2π²k²σ²/p²) — the Gaussian-convolution closed form (Kirchauer/Mack), computed
    # here independently of the engine. Pitch 700 nm collects orders {0,±1,±3} → harmonics to k≈6.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    p, sigma = 700.0, 30.0
    x, aerial, baked = _peb_image(img, p, sigma, n_x=512)
    floor = 1e-6 * float(np.mean(aerial))
    checked = 0
    for k in (1, 2, 3, 4):
        b0 = _cos_coeff(x, aerial, p, k)
        if abs(b0) < floor:                       # 50%-duty kills some even harmonics — skip those
            continue
        kernel = np.exp(-2.0 * np.pi ** 2 * k ** 2 * sigma ** 2 / p ** 2)
        assert _cos_coeff(x, baked, p, k) == pytest.approx(b0 * kernel, rel=2e-3), f"harmonic {k}"
        checked += 1
    assert checked >= 2                           # the anchor really exercised several harmonics


def test_blurred_image_respects_the_input_bounds():
    # Max-principle face of the same physics: diffusion only levels — the baked latent image never
    # overshoots the unbaked envelope (no ringing, no negative acid). Small slack for CN round-off.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    for sigma in (5.0, 25.0, 60.0):
        _, aerial, baked = _peb_image(img, PITCH, sigma)
        span = float(aerial.max() - aerial.min())
        assert baked.min() >= aerial.min() - 1e-6 * span
        assert baked.max() <= aerial.max() + 1e-6 * span


# --------------------------------------------------------------------------- #
# Conservation: the bake conserves acid dose — the power balance survives every σ
# --------------------------------------------------------------------------- #
def test_peb_conserves_dose_and_the_power_balance():
    # No-flux ⇒ ∫a dx is structural in the engine ⇒ the image MEAN is bake-invariant — so the v1
    # Parseval power balance mean(image) = Σ|c_m|² = transmitted_power (computed phase-free,
    # blur-free, engine-free) holds at EVERY diffusion length, to machine precision. Blur
    # redistributes acid; it neither makes nor loses it.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    orders = L.grating_orders(PITCH)
    power = L.transmitted_power(orders, img)
    for sigma in (0.0, 8.0, 25.0, 60.0):
        _, _, baked = _peb_image(img, PITCH, sigma)
        assert float(baked.mean()) == pytest.approx(power, rel=1e-11)
    # Corollary at the readout: the default clip (the image mean = the dose-to-clear) is
    # blur-invariant, so baked and unbaked features are developed at the SAME dose by default.
    f0 = L.expose_grating(img, PITCH)
    f1 = L.expose_grating(img, PITCH, peb_diffusion_length_nm=40.0)
    assert f1.threshold == pytest.approx(f0.threshold, rel=1e-12)


# --------------------------------------------------------------------------- #
# Benchmark: the cited series degrades the feature; blur is harmonic-selective
# --------------------------------------------------------------------------- #
def test_cited_series_degrades_contrast_and_nils_monotonically():
    # The loose leg on the cited 20/40/60 nm PEB series (Mack's smoothing illustration): image
    # quality falls monotonically with σ at fixed dose — contrast and NILS both — and by the top of
    # the series the dense-pitch latent image has lost most of its modulation (printability gone).
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    dose = L.expose_grating(img, PITCH).threshold
    rows = [L.expose_grating(img, PITCH, threshold=dose, peb_diffusion_length_nm=s)
            for s in (0.0,) + L.PEB_DIFFUSION_SERIES_NM]
    assert all(a.contrast > b.contrast for a, b in zip(rows, rows[1:]))
    assert all(a.nils > b.nils for a, b in zip(rows, rows[1:]))
    assert rows[0].nils > L.NILS_PRINTABLE                  # unbaked: robustly printable...
    assert rows[-1].nils < 1.0                              # ...60 nm of spread: below even the
    assert rows[-1].contrast < 0.35 * rows[0].contrast      # cited NILS≥1 minimal-resolution floor


def test_cd_collapses_onto_the_pure_fundamental_readout():
    # Blur kills harmonics as k² (the heat kernel), so the baked image collapses onto its
    # fundamental — and a mean-clipped pure cosine prints CD = p/2 exactly. Assert the printed CD
    # walks monotonically onto that readout as σ grows (the harmonic-selectivity signature at the
    # feature level, not just in Fourier space). The walk is gradual: the image's 2nd harmonic
    # (the 4c₁²cos²ψ term) decays as the k=2 kernel, ~11% left at σ=40 (gap ≈ 1.2 nm), ~0.7% at 60.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    gaps = []
    for sigma in (0.0, 10.0, 20.0, 40.0, 60.0):
        f = L.expose_grating(img, PITCH, peb_diffusion_length_nm=sigma)
        gaps.append(abs(f.cd_nm - PITCH / 2.0))
    assert all(a > b for a, b in zip(gaps, gaps[1:]))
    assert gaps[0] > 5.0                                    # unbaked: harmonics push the CD off p/2
    assert gaps[-1] < 0.2                                   # at σ=60 the CD sits on p/2 within 0.2 nm


def test_peb_window_smooths_standing_waves_but_keeps_the_image():
    # THE trade-off that defines the bake (the cited half-period rule, Mack's glossary): a diffusion
    # length of the standing-wave HALF period λ/4n must erase the depth ripple (period λ/2n, Mack
    # eq. (12)) — same peb_blur, now along z where no-flux is the literal sealed-film BC — while the
    # lateral image at 240 nm pitch keeps ≥ ~3/4 of its fundamental: the PEB window is OPEN there.
    T_sw = L.standing_wave_period(LAMBDA, N_RESIST)             # ≈ 56.8 nm
    sigma_rule = 0.5 * T_sw                                     # the cited smoothing floor (λ/4n)
    film, n = 4.0 * T_sw, 512                                   # ripple = a Neumann eigenmode (j=8)
    z = (np.arange(n) + 0.5) * (film / n)
    ripple = 1.0 + 0.4 * np.cos(2.0 * np.pi * z / T_sw)
    baked = L.peb_blur(ripple, film, sigma_rule)
    swing = (baked.max() - baked.min()) / (ripple.max() - ripple.min())
    assert swing == pytest.approx(np.exp(-2.0 * np.pi ** 2 * (sigma_rule / T_sw) ** 2), rel=5e-3)
    assert swing < 0.02                                         # ≥98% of the ridges erased
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    x, aerial, lateral = _peb_image(img, PITCH, sigma_rule)
    keep = _cos_coeff(x, lateral, PITCH, 1) / _cos_coeff(x, aerial, PITCH, 1)
    assert keep == pytest.approx(np.exp(-2.0 * np.pi ** 2 * (sigma_rule / PITCH) ** 2), rel=1e-3)
    assert keep > 0.70                                          # the window is open at 240 nm…


def test_peb_window_closes_at_dense_pitch_the_lens_outresolves_the_bake():
    # …and CLOSED where the lens can still see. The closure pitch p_close = λ/(4nc) is NA-INDEPENDENT
    # (resist index + keep-floor only); on this NA-0.85 system it lands on the partial-coherence
    # optical cutoff λ/(NA(1+σ)) ≈ 151 nm — a λ-independent coincidence of two independent groups
    # (NA(1+σ)=1.275 vs 4nc=1.274, equal to 0.06%), not a law. Push the dry lens to NA 0.93 (still
    # scalar-honest, NA<1) and the cutoff slides below the pinned p_close: a 145 nm pitch now images
    # fine, yet obeying the SAME cited smoothing rule keeps < half its fundamental. The lens
    # out-resolves the bake — the resist blur, not the optics, sets the dense-pitch floor; you cannot
    # both erase the standing waves and keep the latent image, which is exactly why modern stacks
    # attack reflectivity with a BARC instead (the cited mitigation list: ARC / dye / PEB).
    T_sw = L.standing_wave_period(LAMBDA, N_RESIST)
    sigma_rule = 0.5 * T_sw
    img_hi = L.Imaging(LAMBDA, 0.93, sigma=0.5)
    p_dense = 145.0
    x, aerial, lateral = _peb_image(img_hi, p_dense, sigma_rule)
    assert _cos_coeff(x, aerial, p_dense, 1) > 0.01             # optically alive before the bake
    keep = _cos_coeff(x, lateral, p_dense, 1) / _cos_coeff(x, aerial, p_dense, 1)
    assert keep < 0.5


# --------------------------------------------------------------------------- #
# The named scope edge: the half-period domain refuses an asymmetric image
# --------------------------------------------------------------------------- #
def test_peb_path_refuses_an_asymmetric_image_and_bad_inputs():
    # The PEB domain is the even image's symmetry cell; an off-axis pole under defocus SHIFTS the
    # fringe (the v1.4 finding) off the mirror planes, so the half-period no-flux solve would not be
    # its periodic blur — refused, not silently mis-blurred (the Massoud refuse-outside-the-fit
    # discipline). The same exposure without PEB remains a perfectly good v1.4 computation.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    p = 2.2 * img.pitch_min_two_beam
    asym = dict(source_fs=L.offaxis_source(img), defocus_nm=80.0)
    L.expose_grating(img, p, **asym)                            # fine without the bake
    with pytest.raises(ValueError, match="symmetric"):
        L.expose_grating(img, p, peb_diffusion_length_nm=10.0, **asym)
    with pytest.raises(ValueError, match="even n_x"):
        L.expose_grating(img, PITCH, peb_diffusion_length_nm=10.0, n_x=511)
    with pytest.raises(ValueError):
        L.peb_blur(np.ones(8), 100.0, -1.0)
