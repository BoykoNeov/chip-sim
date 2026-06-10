"""Chip v1.4 validation: lithographic **defocus** — the depth of focus & the Bossung curve.

The Phase-3 §-named scope edge ("ideal in-focus pupil"), **promoted** (the steel-ferrite-bay /
oxidation-Massoud / coupling / D(N) move). Defocus is a pure **phase** aberration on the pupil, so it
lives inside the existing Fourier-optics machinery (``litho.defocus_phase`` multiplies each collected
order, ``abbe_image``/``expose_grating`` thread ``defocus_nm``) — no new code path. Like the rest of
litho there is no engine underneath, so these tests carry the whole mini-triad:

* **Analytic (tight).** (a) The degenerate seam — ``z = 0`` is the in-focus image **bit-for-bit**.
  (b) A **symmetric two-beam (dipole)** image is defocus-invariant to machine precision (the "infinite
  DOF of the dipole": equal pupil radii → an identical phase that factors out); an **asymmetric**
  two-beam keeps its modulation *magnitude* but **rotates** it (the fundamental ``= 2cos φ``) — a fringe
  shift, not a contrast loss. (c) The on-axis **three-beam fundamental is exactly ``4·c₀·c₁·cos φ``**
  (the :func:`~chip.litho.fundamental_amplitude` projection — NOT the contrast metric), nulling at
  ``φ = π/2`` — where the image is a pure double-frequency fringe (defocus-induced frequency doubling,
  Mack), so the *contrast* there is NOT zero.
* **Conservation (tight) — defocus is unitary.** Phase-only ⇒ ``|amplitude|²`` unchanged ⇒ the
  power balance ``mean(image) = Σ|c_m|²`` holds at **every** defocus, to machine precision.
* **Benchmark (loose) + the k₂ tie.** The Bossung CD/contrast/NILS degrade with ``|z|``; the usable
  defocus is ``DOF = k₂·λ/NA²`` with ``k₂ = 0.5`` **derived** (not cited cold) from the ``φ = π/2``
  fundamental null at the resolution-limited pitch — the *paraxial* value, which the exact full-cosθ
  null converges onto as ``NA → 0`` (high-NA is honestly non-paraxial).
"""
import numpy as np
import pytest

from chip import litho as L

LAMBDA = 193.0      # nm, ArF — the demo system wavelength used throughout
NA = 0.85


# --------------------------------------------------------------------------- #
# Benchmark: the cited Rayleigh second-equation constant (pinned)
# --------------------------------------------------------------------------- #
def test_cited_k2_dof_constant():
    # Pin k₂ (DOF = k₂·λ/NA²) like k₁ is pinned. 0.5 is the value DERIVED from the φ=π/2 fundamental
    # null at the resolution limit (test below) — citation-fidelity + validated-as-a-consequence.
    assert L.K2_DOF == 0.5


# --------------------------------------------------------------------------- #
# Analytic: the degenerate seam — z = 0 is the in-focus image, bit-for-bit
# --------------------------------------------------------------------------- #
def test_defocus_zero_is_the_in_focus_image_bit_for_bit():
    # The seam (the v1.x discipline): defocus_nm=0.0 must reproduce v1 EXACTLY, not approximately —
    # defocus_phase short-circuits to the float 1.0, so the collected orders stay real and coherent_image
    # is the identical computation. Asserted with array_equal (bit-for-bit), not allclose.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    p = 350.0
    x = np.linspace(0.0, p, 512, endpoint=False)
    orders = L.grating_orders(p)
    src = L.conventional_source(img)
    in_focus = L.abbe_image(x, orders, img, source_fs=src)
    z_zero = L.abbe_image(x, orders, img, source_fs=src, defocus_nm=0.0)
    assert np.array_equal(in_focus, z_zero)
    # And through the high-level entry: the in-focus PrintedFeature is unchanged.
    assert L.expose_grating(img, p).cd_nm == L.expose_grating(img, p, defocus_nm=0.0).cd_nm
    # defocus_phase itself is the literal 1.0 at z=0 (so the multiply is a no-op on real amplitudes).
    assert L.defocus_phase(0.012, img, 0.0) == 1.0


def test_defocus_phase_is_unity_on_axis_for_any_defocus():
    # The on-axis order (f_total = 0 ⇒ cosθ = 1 ⇒ 1−cosθ = 0) carries NO defocus phase at any z — defocus
    # is referenced to the axial ray. So the 0th order is the defocus-invariant anchor the others rotate
    # against (this is why the three-beam fundamental is ∝ cos of the ±1 phase alone).
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    for z in (50.0, 250.0, -120.0):
        assert L.defocus_phase(0.0, img, z) == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Analytic: two-beam imaging — the dipole's infinite DOF, the asymmetric rotation
# --------------------------------------------------------------------------- #
def _defocused_orders_image(x, orders, img, z):
    """A coherent image of explicit orders with each order's defocus phase applied (test helper)."""
    return L.coherent_image(x, [(f, c * L.defocus_phase(f, img, z)) for (f, c) in orders])


def test_symmetric_dipole_has_infinite_depth_of_focus():
    # The literal "infinite DOF of the dipole" as a machine-precision test: two equal beams placed
    # SYMMETRICALLY at ±f_cut share an identical pupil radius |f| = f_cut → an identical defocus phase →
    # it factors out of |Σ|² → the image is bit-for-bit the same at EVERY defocus. (This is why
    # dipole/two-beam illumination buys huge focus latitude.)
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    fc = img.f_cut
    x = np.linspace(0.0, 1.0 / fc, 1024, endpoint=False)     # one fringe period p = 1/f_cut
    sym = [(-fc, 1.0), (fc, 1.0)]
    base = _defocused_orders_image(x, sym, img, 0.0)
    for z in (75.0, 250.0, -400.0):
        np.testing.assert_allclose(_defocused_orders_image(x, sym, img, z), base, atol=1e-12)


def test_asymmetric_two_beam_rotates_the_fringe_keeps_its_magnitude():
    # An asymmetric two-beam (0th & +1st) is NOT defocus-invariant like the dipole, but defocus only
    # ROTATES the modulation, it does not shrink it: I = 2 + 2cos(2πx/p + φ), so the cos(2πx/p)
    # projection is exactly 2cos φ (machine precision) — it falls to 0 at φ=π/2 — while the fringe
    # VISIBILITY stays ≈1 (the fringe has merely translated by φ·p/2π). Contrast preserved, not lost.
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    p = 320.0
    x = np.linspace(0.0, p, 4096, endpoint=False)
    asym = [(0.0, 1.0), (1.0 / p, 1.0)]
    cos_theta = np.sqrt(1.0 - (LAMBDA / p) ** 2)
    for z in (0.0, 90.0, 200.0):
        phi = (2.0 * np.pi / LAMBDA) * z * (1.0 - cos_theta)
        I = _defocused_orders_image(x, asym, img, z)
        # the fundamental rotates as 2cos φ — exact (the magnitude of the modulation is conserved)
        assert L.fundamental_amplitude(x, I, p) == pytest.approx(2.0 * np.cos(phi), abs=1e-9)
        # …and the visibility is preserved (a true two-beam fringe, only translated) — within the
        # discrete-sampling floor of locating a shifted peak/trough on the grid.
        assert L.image_contrast(I) == pytest.approx(1.0, abs=1e-3)
    # The fringe has demonstrably MOVED: the peak is at x=0 in focus, off it under defocus.
    I_def = _defocused_orders_image(x, asym, img, 90.0)
    assert abs(x[np.argmax(I_def)]) > 5.0


# --------------------------------------------------------------------------- #
# Analytic: the on-axis three-beam fundamental = exactly 4·c₀·c₁·cos φ (the tight anchor)
# --------------------------------------------------------------------------- #
def _three_beam_setup(p=350.0):
    """A pitch where on-axis coherent imaging collects EXACTLY {0, ±1} → the closed-form three-beam case."""
    img = L.Imaging(LAMBDA, NA, sigma=0.0)
    assert img.pitch_min_coherent <= p < 3.0 * img.pitch_min_coherent   # only {0, ±1} pass on-axis
    x = np.linspace(0.0, p, 256, endpoint=False)
    orders = L.grating_orders(p)
    cos_theta = np.sqrt(1.0 - (LAMBDA / p) ** 2)                          # the ±1 order's pupil cosθ
    return img, p, x, orders, cos_theta


def test_three_beam_fundamental_is_exactly_4c0c1_cosphi():
    # THE tight defocus anchor (the advisor's load-bearing correction): the fundamental Fourier component
    # of the on-axis three-beam image is exactly 4·c₀·c₁·cos φ, with φ the ±1 order's defocus phase
    # computed with the code's OWN full cosθ — to machine precision, across defocus. NOT the contrast
    # metric (which keeps the defocus-independent 4c₁²cos²ψ second harmonic).
    img, p, x, orders, cos_theta = _three_beam_setup()
    src = L.on_axis_source()
    c0, c1 = 0.5, 1.0 / np.pi                                             # 50%-duty grating amplitudes
    for z in (0.0, 80.0, 150.0, 300.0, -110.0):
        phi = (2.0 * np.pi / LAMBDA) * z * (1.0 - cos_theta)
        I = L.abbe_image(x, orders, img, source_fs=src, defocus_nm=z)
        assert L.fundamental_amplitude(x, I, p) == pytest.approx(4.0 * c0 * c1 * np.cos(phi), abs=1e-12)


def test_dof_null_is_frequency_doubling_not_a_blank_image():
    # The depth-of-focus event, pinned exactly: at the defocus where φ = π/2 the FUNDAMENTAL vanishes
    # (4c₀c₁·cos(π/2) = 0) — but the image is NOT blank: it collapses to a pure DOUBLE-frequency fringe
    # (the surviving 4c₁²cos²ψ term), so image_contrast stays well above zero. This is exactly why the
    # tight anchor asserts on the fundamental, not on contrast (the advisor's correction, pinned).
    img, p, x, orders, cos_theta = _three_beam_setup()
    src = L.on_axis_source()
    z_null = (np.pi / 2.0) / ((2.0 * np.pi / LAMBDA) * (1.0 - cos_theta))
    I = L.abbe_image(x, orders, img, source_fs=src, defocus_nm=z_null)
    assert L.fundamental_amplitude(x, I, p) == pytest.approx(0.0, abs=1e-9)   # fundamental nulled
    assert L.image_contrast(I) > 0.3                                          # but NOT a flat image
    # The survivor is the 2nd harmonic: the period-p/2 component dominates (frequency doubling).
    half_period = float(2.0 * np.mean(I * np.cos(2.0 * np.pi * x / (p / 2.0))))
    assert abs(half_period) > 0.1


# --------------------------------------------------------------------------- #
# Conservation: defocus is unitary — image DC = transmitted power at EVERY defocus
# --------------------------------------------------------------------------- #
def test_defocus_conserves_power_at_every_defocus():
    # The elegant conservation leg: defocus is phase-only, so |c_m|² is untouched and the Parseval power
    # balance mean(image) = Σ|c_m|² = transmitted_power holds at EVERY defocus — to machine precision.
    # transmitted_power never sees the phase (it sums |c|²), so this is a genuine check that the
    # implementation added PHASE and not amplitude (a bug that scaled an order would break it here).
    img = L.Imaging(LAMBDA, NA, sigma=0.6)
    p = 180.0
    orders = L.grating_orders(p, n_orders=15)
    src = L.conventional_source(img, n_source=21)
    x = np.linspace(0.0, p, 4096, endpoint=False)
    power = L.transmitted_power(orders, img, source_fs=src)               # phase-free reference
    for z in (0.0, 75.0, 200.0, 500.0):
        I = L.abbe_image(x, orders, img, source_fs=src, defocus_nm=z)
        assert I.mean() == pytest.approx(power, rel=1e-10)


# --------------------------------------------------------------------------- #
# Benchmark: depth of focus DOF = k₂·λ/NA² and the paraxial k₂=0.5 tie
# --------------------------------------------------------------------------- #
def test_depth_of_focus_formula():
    # DOF = k₂·λ/NA² (the second Rayleigh equation); the method and standalone agree, and k₂=0.5 is
    # literally λ/2NA² (the paraxial φ=π/2 null at the rim). Companion to the k₁ resolution formula.
    img = L.Imaging(LAMBDA, NA)
    assert img.depth_of_focus(0.5) == pytest.approx(0.5 * LAMBDA / NA ** 2)
    assert img.depth_of_focus() == pytest.approx(LAMBDA / (2.0 * NA ** 2))   # k₂=0.5 default
    assert L.rayleigh_depth_of_focus(LAMBDA, NA, 0.5) == pytest.approx(img.depth_of_focus(0.5))
    # The resolution/DOF squeeze: doubling NA quarters the DOF (λ/NA²) but only halves the pitch (λ/NA).
    hi = L.Imaging(LAMBDA, 2 * NA)
    assert img.depth_of_focus() / hi.depth_of_focus() == pytest.approx(4.0)


def test_paraxial_k2_dof_converges_to_the_exact_null_at_low_NA():
    # k₂=0.5 (= λ/2NA²) is the PARAXIAL DOF; the exact full-cosθ φ=π/2 null sits below it at high NA
    # (honestly non-paraxial — ~24% low at NA=0.85) and converges UP onto it as NA→0. Pin both: the
    # high-NA gap and the low-NA agreement. This is what makes k₂ a derived consequence, not a fudge.
    def exact_null(na):
        img = L.Imaging(LAMBDA, na, sigma=0.0)
        p = img.pitch_min_coherent * 1.0001                  # ±1 ride the rim: sinθ → NA
        cos_theta = np.sqrt(1.0 - (LAMBDA / p) ** 2)
        return (np.pi / 2.0) / ((2.0 * np.pi / LAMBDA) * (1.0 - cos_theta))

    ratios = [exact_null(na) / L.rayleigh_depth_of_focus(LAMBDA, na) for na in (0.85, 0.5, 0.3, 0.15)]
    assert all(a < b for a, b in zip(ratios, ratios[1:]))    # monotonically → 1 as NA shrinks
    assert ratios[0] < 0.8                                   # high-NA: exact null ~24% below paraxial
    assert ratios[-1] == pytest.approx(1.0, abs=0.01)        # low-NA: paraxial is exact


def test_bossung_contrast_and_nils_degrade_with_defocus():
    # The Bossung benchmark (loose): at a fixed dose, image quality degrades monotonically as |z| grows
    # — contrast and NILS both fall — and the printability (NILS) drops out of the robust band on the
    # order of the DOF. The classic focus-exposure behaviour the process window is built on.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    p = 350.0
    dose = L.expose_grating(img, p, defocus_nm=0.0).threshold            # the in-focus mean clip
    rows = [L.expose_grating(img, p, threshold=dose, defocus_nm=z)
            for z in (0.0, 50.0, 100.0, 150.0, 200.0)]
    assert all(a.contrast >= b.contrast - 1e-9 for a, b in zip(rows, rows[1:]))
    assert all(a.nils >= b.nils - 1e-9 for a, b in zip(rows, rows[1:]))
    assert rows[0].nils > L.NILS_PRINTABLE                               # in focus: robustly printable
    assert rows[-1].nils < rows[0].nils                                  # defocused: degraded
    # Image quality has fallen substantially by ~1.5·DOF of defocus (the focus budget is finite).
    assert rows[-1].contrast < 0.6 * rows[0].contrast
