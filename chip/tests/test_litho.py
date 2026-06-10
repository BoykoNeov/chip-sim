"""Chip Phase-3 validation: the lithography aerial image — the Fourier-optics triad.

This carries the whole plan §3 Phase-3 triad (microchip-fabrication.md). Like Phase 2 (and unlike
Phase 1a) there is **no engine underneath** — this module *is* its own Fourier-optics
computation — so its tests carry every leg:

* **Analytical limit (tight, on its idealization).** The exact two-beam image is ``4·cos²(πx/p)`` to
  machine precision (two **equal** orders through :func:`coherent_image` — pure trig), and the Rayleigh
  ``k₁`` **emerges from the pupil-cutoff arithmetic**: on-axis ±1 just fit at ``p=λ/NA`` (k₁=0.5), the
  off-axis source point spans the full pupil at ``p=λ/2NA`` (k₁=0.25) where exactly {0,+1} pass and the
  cos² falls out of the Abbe workhorse itself. Scope edge, named: scalar / ideal-in-focus-pupil /
  Abbe-not-Hopkins / constant-threshold-resist / 1-D — asserted as documented idealizations (the
  realistic grating's visibility < the ideal cos²'s, kept separate — the Phase 1a discipline).

* **Conservation (tight) — power balance.** The DC (mean) of the aerial image = the total power passed
  by the pupil ``Σ_collected |c_m|²`` (= the zeroth order, when only it passes) — Parseval, computed two
  independent ways (a squared sum vs a sum of squares), to machine precision.

* **Benchmark (loose).** Contrast and NILS vs pitch follow the classic resolution curves — contrast → 0
  as pitch → the pupil cutoff, NILS drops out of the printable band — against the cited ``k₁``/NILS rules
  (litho-aerial-image-source: Mack / lithoguru). The constants are pinned exactly (citation fidelity, NOT
  a tautology); the ``k₁`` *values themselves are validated as a consequence* of the pupil arithmetic.
"""
import numpy as np
import pytest

from chip import litho as L


# --------------------------------------------------------------------------- #
# Benchmark: the cited resolution / printability constants (pinned exactly)
# --------------------------------------------------------------------------- #
def test_cited_k1_and_nils_constants():
    # Pin the cited Rayleigh k₁ factors and the NILS rule of thumb (litho-aerial-image-source — Mack /
    # lithoguru). Load-bearing for the resolution claims, so pin them like oxidation pins B/(B/A).
    assert L.K1_TWO_BEAM == 0.25      # the physical half-pitch floor (two-beam / extreme off-axis)
    assert L.K1_COHERENT == 0.5       # the conventional coherent (on-axis, three-beam) limit
    assert L.NILS_PRINTABLE == 2.0    # robust-process rule of thumb (~20% exposure latitude)


# --------------------------------------------------------------------------- #
# Analytical limit: the exact two-beam cos² anchor
# --------------------------------------------------------------------------- #
def test_two_beam_image_is_exactly_4cos2():
    # The analytical anchor: two equal unit beams (0th + 1st) interfere to 4·cos²(πx/p) to machine
    # precision (pure trig). Full visibility — I_min = 0 at x=p/2, I_max = 4 at x=0. TIGHT.
    p = 200.0
    x = np.linspace(0.0, 2 * p, 401)
    np.testing.assert_allclose(L.two_beam_image(x, p), 4.0 * np.cos(np.pi * x / p) ** 2, atol=1e-12)
    assert L.two_beam_image(0.0, p) == pytest.approx(4.0)        # bright peak
    assert L.two_beam_image(p / 2.0, p) == pytest.approx(0.0, abs=1e-12)   # dark null


def test_two_beam_is_the_core_primitive_with_two_equal_orders():
    # The anchor IS coherent_image of exactly two equal orders — so it validates the same core the Abbe
    # workhorse reuses (not a parallel code path). The cos² is not special-cased, it falls out of |Σ|².
    p = 180.0
    x = np.linspace(0.0, p, 257, endpoint=False)
    direct = L.coherent_image(x, [(0.0, 1.0), (1.0 / p, 1.0)])
    np.testing.assert_allclose(L.two_beam_image(x, p), direct, atol=1e-14)


# --------------------------------------------------------------------------- #
# Analytical limit: Rayleigh R = k₁·λ/NA emerges from the pupil cutoff
# --------------------------------------------------------------------------- #
def test_rayleigh_resolution_formula():
    # R = k₁·λ/NA (half-pitch). The standalone and the method agree; the two pitch limits are λ/NA
    # (coherent) and λ/2NA (two-beam) — i.e. half-pitch k₁ = 0.5 and 0.25.
    img = L.Imaging(wavelength_nm=193.0, NA=0.85)
    assert img.resolution(0.25) == pytest.approx(0.25 * 193.0 / 0.85)
    assert img.resolution(0.5) == pytest.approx(0.5 * 193.0 / 0.85)
    assert L.rayleigh_resolution(193.0, 0.85, 0.25) == pytest.approx(img.resolution(0.25))
    assert img.pitch_min_coherent == pytest.approx(193.0 / 0.85)
    assert img.pitch_min_two_beam == pytest.approx(193.0 / (2 * 0.85))
    assert img.f_cut == pytest.approx(0.85 / 193.0)
    # Half-pitch of the coherent limit = the k₁=0.5 resolution.
    assert 0.5 * img.pitch_min_coherent == pytest.approx(img.resolution(0.5))


def test_coherent_resolution_limit_is_a_consequence_of_the_pupil():
    # k₁=0.5 DERIVED, not echoed: on-axis (σ=0) illumination images a grating only while its ±1 orders
    # fit the pupil (1/p ≤ NA/λ ⇒ p ≥ λ/NA). Above the limit the image fully modulates (contrast→1);
    # below it only the DC order survives → a flat image → contrast 0. The cutoff sits exactly at λ/NA.
    img = L.Imaging(193.0, 0.85, sigma=0.0)
    src = L.on_axis_source()
    contrasts = {}
    for frac in (1.10, 1.02, 0.98, 0.85):
        p = frac * img.pitch_min_coherent
        x = np.linspace(0.0, p, 1024, endpoint=False)
        I = L.abbe_image(x, L.grating_orders(p), img, source_fs=src)
        contrasts[frac] = L.image_contrast(I)
    assert contrasts[1.10] > 0.9 and contrasts[1.02] > 0.9   # resolves above λ/NA
    assert contrasts[0.98] < 1e-9 and contrasts[0.85] < 1e-9  # flat (unresolved) below λ/NA


def test_offaxis_two_beam_extends_resolution_to_k1_0p25():
    # k₁=0.25 DERIVED: the off-axis source point puts the 0th order at one pupil rim, so a 1st order as
    # fine as 2·NA/λ reaches the other rim — a grating at p=λ/2NA still passes TWO beams and images,
    # exactly where on-axis illumination has gone flat. This is the two-beam (dipole) resolution gain.
    img = L.Imaging(193.0, 0.85, sigma=0.0)
    p = img.pitch_min_two_beam * 1.001                # just inside the two-beam limit
    x = np.linspace(0.0, p, 2048, endpoint=False)
    orders = L.grating_orders(p)
    on_axis = L.image_contrast(L.abbe_image(x, orders, img, source_fs=L.on_axis_source()))
    off_axis = L.image_contrast(L.abbe_image(x, orders, img, source_fs=L.offaxis_source(img)))
    assert on_axis < 1e-9          # on-axis cannot resolve this fine pitch
    assert off_axis > 0.5          # off-axis still images (a strong fringe)


def test_offaxis_passes_exactly_two_orders_at_the_limit():
    # At p = λ/2NA the off-axis pole selects EXACTLY the 0th and +1st orders (the −1st and ±2 fall
    # outside the shifted pupil) — the literal two-beam configuration, from which the cos² emerges.
    img = L.Imaging(193.0, 0.85, sigma=0.0)
    p = img.pitch_min_two_beam
    fs = L.offaxis_source(img)[0]
    cutoff = img.f_cut * (1 + 1e-9)
    passed = sorted(round(f * p) for (f, c) in L.grating_orders(p) if abs(f + fs) <= cutoff)
    assert passed == [0, 1]


def test_realistic_grating_image_is_not_the_exact_cos2():
    # The exact-anchor-vs-realistic-demo split (the Phase 1a discipline): the exact 4·cos² needs EQUAL
    # amplitudes, but a real 50%-duty grating has c₀=0.5 ≠ c₁=1/π. So the off-axis two-beam image off a
    # real grating is a cos fringe of visibility 2c₀c₁/(c₀²+c₁²) ≈ 0.906 < 1 — NOT the exact cos². We
    # assert it lands on that predicted unequal-order visibility, and is NOT full-contrast.
    img = L.Imaging(193.0, 0.85, sigma=0.0)
    p = img.pitch_min_two_beam * 1.001
    x = np.linspace(0.0, p, 2048, endpoint=False)
    I = L.abbe_image(x, L.grating_orders(p), img, source_fs=L.offaxis_source(img))
    c0, c1 = 0.5, 1.0 / np.pi
    assert L.image_contrast(I) == pytest.approx(2 * c0 * c1 / (c0 ** 2 + c1 ** 2), rel=1e-3)
    assert L.image_contrast(I) < 0.95          # not the full-visibility ideal cos²


# --------------------------------------------------------------------------- #
# Analytical limit: the mask spectrum (binary square-wave grating)
# --------------------------------------------------------------------------- #
def test_grating_orders_are_the_square_wave_spectrum():
    # A 50%-duty binary grating: c₀=0.5 (DC = clear fraction), c₁=1/π, c₂=0 (even orders vanish),
    # c₃=−1/3π. Real and even (symmetric about x=0). The classic line/space diffraction spectrum.
    p = 300.0
    orders = dict((round(f * p), c) for (f, c) in L.grating_orders(p, n_orders=4, duty=0.5))
    assert orders[0] == pytest.approx(0.5)
    assert orders[1] == pytest.approx(1.0 / np.pi)
    assert orders[2] == pytest.approx(0.0, abs=1e-15)
    assert orders[3] == pytest.approx(-1.0 / (3 * np.pi))
    assert orders[-1] == pytest.approx(orders[1])      # even symmetry c_{-m} = c_m


def test_grating_orders_rejects_bad_duty():
    with pytest.raises(ValueError):
        L.grating_orders(300.0, duty=0.0)
    with pytest.raises(ValueError):
        L.grating_orders(300.0, duty=1.0)


def test_pupil_is_an_ideal_sharp_cutoff_named_scope_edge():
    # Scope edge, NAMED not modeled: v1's pupil is an ideal BINARY sharp cutoff — in-focus,
    # aberration-free — an order is either fully collected (|f| ≤ f_cut) or fully blocked, with no
    # defocus apodization / partial transmission. We pin that idealization: an order just inside the rim
    # contributes its full power, one just outside contributes nothing (a step, not a roll-off). Real
    # pupils carry a defocus phase + Zernike aberrations — out of v1 (the honest ceiling).
    img = L.Imaging(193.0, 0.85, sigma=0.0)
    inside = [(img.f_cut * 0.999, 1.0)]
    outside = [(img.f_cut * 1.001, 1.0)]
    assert L.transmitted_power(inside, img, source_fs=L.on_axis_source()) == pytest.approx(1.0)
    assert L.transmitted_power(outside, img, source_fs=L.on_axis_source()) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# Conservation: image DC = total transmitted power (Parseval / power balance)
# --------------------------------------------------------------------------- #
def test_image_dc_equals_transmitted_power_partial_coherence():
    # The power-balance check: the spatial MEAN (DC component) of the partially-coherent Abbe image
    # equals the total power the pupil passes, Σ|c_m|² averaged over the source — computed two
    # INDEPENDENT ways (a squared sum |Σ a e^{iωx}|² vs a sum of squares Σ|c|²). Sampling an integer
    # period with endpoint=False and N ≫ 2·n_orders makes the discrete mean exact, so this holds to
    # machine precision (not a coincidence of a coarse grid). TIGHT.
    img = L.Imaging(193.0, 0.85, sigma=0.6)
    p = 180.0
    orders = L.grating_orders(p, n_orders=15)
    src = L.conventional_source(img, n_source=21)
    x = np.linspace(0.0, p, 4096, endpoint=False)
    I = L.abbe_image(x, orders, img, source_fs=src)
    power = L.transmitted_power(orders, img, source_fs=src)
    assert I.mean() == pytest.approx(power, rel=1e-10)


def test_image_dc_is_the_zeroth_order_when_only_it_passes():
    # The triple-equality's limiting case (the plan's "DC = the zeroth diffraction order = total
    # transmitted power"): for a sub-resolution pitch under on-axis illumination, ONLY the 0th order
    # passes → the image is flat at |c₀|² = duty², and that constant equals both the image mean and the
    # transmitted power. The DC component is literally the zeroth order here.
    img = L.Imaging(193.0, 0.85, sigma=0.0)
    p = 0.8 * img.pitch_min_coherent              # below λ/NA: ±1 orders are cut, only the 0th survives
    orders = L.grating_orders(p)
    x = np.linspace(0.0, p, 1024, endpoint=False)
    I = L.abbe_image(x, orders, img, source_fs=L.on_axis_source())
    np.testing.assert_allclose(I, 0.25, atol=1e-12)        # flat = c₀² = 0.5²
    assert L.transmitted_power(orders, img, source_fs=L.on_axis_source()) == pytest.approx(0.25)


def test_transmitted_power_is_the_sum_of_collected_order_squares():
    # transmitted_power independently = Σ over collected orders of |c_m|². For an on-axis well-resolved
    # 1:1 grating the pupil collects {0, ±1} (the next, ±3, is out): power = c₀² + 2·c₁².
    img = L.Imaging(193.0, 0.85, sigma=0.0)
    p = 1.5 * img.pitch_min_coherent               # passes 0, ±1 (±3 at 3/p > f_cut is blocked)
    orders = L.grating_orders(p)
    expected = 0.5 ** 2 + 2 * (1.0 / np.pi) ** 2
    assert L.transmitted_power(orders, img, source_fs=L.on_axis_source()) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Benchmark: contrast & NILS vs pitch (the resolution curves) — loose
# --------------------------------------------------------------------------- #
def test_contrast_falls_with_pitch_toward_the_resolution_limit():
    # The classic resolution trend: with a conventional source, contrast is high for coarse pitch and
    # decreases monotonically as the pitch shrinks toward the cutoff (fewer/weaker orders collected).
    img = L.Imaging(193.0, 0.85, sigma=0.5)
    pitches = [600.0, 400.0, 300.0, 240.0]
    contrasts = [L.expose_grating(img, p).contrast for p in pitches]
    assert all(earlier >= later - 1e-9 for earlier, later in zip(contrasts, contrasts[1:]))
    assert contrasts[0] > 0.8                       # a coarse pitch images cleanly


def test_nils_in_printable_band_for_resolved_collapses_when_unresolved():
    # NILS (the printability metric) is well above the printable band for a comfortably-resolved pitch,
    # and collapses to ~0 when the pattern stops resolving (a flat image has zero log-slope). The
    # NILS≳2 rule is the cited calibration; here it cleanly separates resolved from unresolved.
    img = L.Imaging(193.0, 0.85, sigma=0.5)
    resolved = L.expose_grating(img, 500.0)
    assert resolved.nils > L.NILS_PRINTABLE         # steep edge — robustly printable
    unresolved = L.expose_grating(L.Imaging(193.0, 0.85, sigma=0.0), 0.8 * img.pitch_min_coherent)
    assert unresolved.nils < 1e-6                   # flat image → no edge → NILS ≈ 0


# --------------------------------------------------------------------------- #
# Constant-threshold resist → printed CD (recipe in, feature out)
# --------------------------------------------------------------------------- #
def test_print_cd_constant_threshold_dark_and_bright():
    # A symmetric two-beam cos² clipped at its mid level (I=2) prints a 50%-duty feature: the dark line
    # (I<2) is half the period, the bright space the other half. The polarity selects which — each read
    # on a range with that feature INTERIOR (print_cd requires the feature not to wrap the array ends).
    p = 300.0
    x_dark = np.linspace(0.0, p, 2001)              # dark line centred at p/2 (interior)
    I_dark = L.two_beam_image(x_dark, p)            # 4cos²: bright at x=0, dark at x=p/2
    assert L.print_cd(x_dark, I_dark, threshold=2.0, polarity="dark") == pytest.approx(p / 2, rel=1e-2)
    x_bright = np.linspace(-p / 2, p / 2, 2001)     # bright space centred at 0 (interior)
    I_bright = L.two_beam_image(x_bright, p)
    assert L.print_cd(x_bright, I_bright, threshold=2.0, polarity="bright") == pytest.approx(p / 2, rel=1e-2)
    # A flat (unresolved) image never crosses the threshold → CD 0.
    assert L.print_cd(x_dark, np.full_like(x_dark, 0.25), threshold=2.0) == 0.0


def test_expose_grating_recipe_in_cd_out():
    # The Phase-3 'recipe in, feature out' entry: a resolved 1:1 grating prints CD ≈ p/2 (at the
    # mean-intensity clip), reported in nm and µm (the cross-module currency), flagged resolved.
    img = L.Imaging(193.0, 0.85, sigma=0.5)
    pf = L.expose_grating(img, 400.0)
    # ~half-pitch line — a band, not exactly p/2: the mean-intensity clip on a real (harmonic-bearing)
    # grating image doesn't bisect the period into an exact 50/50, so the dark line is a half-pitch-ISH
    # fraction of the pitch, reported in nm and µm (the cross-module currency).
    assert 0.4 * 400.0 < pf.cd_nm < 0.65 * 400.0
    assert pf.cd_um == pytest.approx(pf.cd_nm * 1e-3)
    assert pf.resolved and pf.contrast > 0.8
    # A sub-resolution pitch under coherent illumination: flat image, CD 0, not resolved.
    fine = L.expose_grating(L.Imaging(193.0, 0.85, sigma=0.0), 0.8 * img.pitch_min_coherent)
    assert not fine.resolved and fine.cd_nm == 0.0


def test_fixed_threshold_cd_collapses_as_pitch_shrinks():
    # Held at a FIXED dose (threshold), the printed CD shrinks as the pitch shrinks (less light through
    # the smaller features), until the pattern collapses — the constant-dose pitch sweep the demo shows.
    img = L.Imaging(193.0, 0.85, sigma=0.5)
    clip = 0.25                                          # a fixed exposure clip (the DC level)
    cds = [L.expose_grating(img, p, threshold=clip).cd_nm for p in (600.0, 400.0, 300.0)]
    assert cds[0] > cds[1] > cds[2]
