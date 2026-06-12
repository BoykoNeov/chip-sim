"""Chip v1.9 validation: **CAR reaction–diffusion PEB** — amplification competes with diffusion + loss.

The §8-named scope edge ("constant D — no CAR reaction–diffusion"), **promoted** — and where v1.7
found the bake *is* the engine's pure linear PDE, the realistic chemically-amplified bake is a coupled
**two-field** system (acid ``h`` + blocked-site fraction ``m``) that does **not** fit the single-field
engine natively, so it is built **consumer-side by operator splitting**: the engine carries only the
acid-**diffusion** sub-step (``Neumann(0)`` sealed faces, ``D_h(m)`` frozen per step from the lagged
deprotection — the array-``D`` path), while the local reaction (acid-catalyzed deprotection + first-
order acid loss) is integrated in **closed form** (``litho._car_react``). Like v1.7 these tests do not
carry the solver (the engine suite does); they carry the **instantiation** — that the split is exact
where it must be, and what the bake does to the printed feature.

* **Analytic (tight).** (a) The degenerate seam — ``k_amp = k_loss = 0`` reduces ``car_peb`` to the
  v1.7 linear acid-diffusion blur **bit-for-bit** (it short-circuits to ``peb_blur``; ``m`` stays 1,
  deprotection 0). (b) A **spatially-flat** acid sees identity diffusion (``Neumann(0)``) so the split
  is the exact reaction flow — the deprotection matches the **closed-form ODE** to machine precision,
  at ``k_loss = 0`` and ``k_loss > 0`` alike (the reaction operator is an exactly-composed semigroup).
* **Conservation (tight).** Acid is a **pure catalyst** (the Kirchauer ``h`` equation has no ``h·m``
  sink) ⇒ ``∫h dx`` is conserved at ``k_loss = 0`` and decays *exactly* ``e^{−k_loss·t}`` otherwise —
  on flat **and** structured images, to machine precision; and the deprotection ``1−m`` stays in
  ``[0, 1]`` and is monotone in bake time (``m`` only ever decreases).
* **Benchmark (loose).** **Chemical amplification sharpens** — in the amplification-dominated (small
  ``D``, short bake) regime the superlinear ``hⁿ`` map makes the deprotection edge *steeper* than the
  acid's (``NILS`` up) — the signature that makes CAR high-resolution; **diffusion + loss + over-bake
  degrade** the developed feature (the acutely PEB-sensitive CD; the cited "control of the PEB is
  extremely critical"). Regime claims, not monotone laws. The split is convergent (first order,
  backward-Euler-limited). Cited APEX-E @ 90 °C constants.
"""
import numpy as np
import pytest

from chip import litho as L

LAMBDA = 193.0      # nm, ArF — the demo system used throughout (as in test_peb)
NA = 0.85
PITCH = 240.0       # dense-but-resolved line/space (CD = 120 nm)


def _aerial_half(img, pitch_nm, n_x=512):
    """The half-period latent-acid cell (peak normalized to 1) the CAR bake runs on, bare."""
    x = (np.arange(n_x) + 0.5) * (pitch_nm / n_x)
    aerial = L.abbe_image(x, L.grating_orders(pitch_nm), img, source_fs=L.conventional_source(img))
    h0 = aerial / float(aerial.max())
    return x, aerial, h0


# --------------------------------------------------------------------------- #
# Benchmark pins: the cited APEX-E constants and the two-field model (citation fidelity)
# --------------------------------------------------------------------------- #
def test_cited_car_constants():
    # Pin the cited values like k₁/k₂/NILS are pinned (peb-acid-diffusion-source): the IBM APEX-E
    # @ 90 °C reaction–diffusion constants of the Kirchauer §7.1.2 two-field CAR PEB model.
    assert L.CAR_K_AMP_APEX_E == 2.0
    assert L.CAR_K_LOSS_APEX_E == 0.0033
    assert L.CAR_REACTION_ORDER_APEX_E == 1.8
    assert L.CAR_D_H0_APEX_E == 0.0933
    # the recipe defaults to those cited constants
    bake = L.CARBake(t_bake_s=10.0)
    assert (bake.k_amp, bake.k_loss, bake.reaction_order, bake.D_h0_nm2_s) == (2.0, 0.0033, 1.8, 0.0933)
    assert bake.D_h1_nm2_s == 0.0          # constant D by default (D_h1 is illustrative, uncalibrated)


# --------------------------------------------------------------------------- #
# Analytic: the degenerate seam — no reaction is the v1.7 linear blur, bit-for-bit
# --------------------------------------------------------------------------- #
def test_no_reaction_is_the_v17_blur_bit_for_bit():
    # The seam (the v1.x discipline): with no amplification and no loss the acid is a pure linear
    # blur (constant D, m≡1), so car_peb must short-circuit to peb_blur and reproduce the v1.7 path
    # EXACTLY — and the deprotection is identically zero (nothing deprotects without acid catalysis).
    rng = np.random.default_rng(3)
    acid = 1.0 + rng.random(64)
    bake = L.CARBake(t_bake_s=30.0, k_amp=0.0, k_loss=0.0, D_h0_nm2_s=0.05)
    depro, h = L.car_peb(acid, 120.0, bake)
    sigma = np.sqrt(2.0 * 0.05 * 30.0)
    assert np.array_equal(h, L.peb_blur(acid, 120.0, sigma))      # bit-for-bit, not approximately
    assert np.array_equal(depro, np.zeros_like(acid))


# --------------------------------------------------------------------------- #
# Analytic: a spatially-flat acid is the exact reaction ODE (diffusion is identity)
# --------------------------------------------------------------------------- #
def test_flat_field_is_the_exact_reaction_ode():
    # The tight anchor: a uniform acid sees identity diffusion under Neumann(0), so the Strang split
    # collapses to the pure reaction flow — and that flow integrates in CLOSED FORM (a semigroup, so
    # sub-steps compose exactly): m = exp(−k_amp·hⁿ·Φ), h = h₀·e^{−k_loss·t}, with
    # Φ = (1−e^{−n·k_loss·t})/(n·k_loss) → t as k_loss → 0. Machine precision, both loss regimes.
    n, h0, t = 1.8, 0.7, 1.0   # a partial-deprotection regime (m ≈ 0.33) — exactness on a meaningful
    for k_loss in (0.0, 0.01):  # value, not an underflowed-to-zero one
        bake = L.CARBake(t_bake_s=t, k_amp=2.0, k_loss=k_loss, reaction_order=n, D_h0_nm2_s=0.09)
        depro, h = L.car_peb(np.full(32, h0), 100.0, bake, n_steps=200)
        phi = (1.0 - np.exp(-n * k_loss * t)) / (n * k_loss) if k_loss > 0 else t
        m_exact = np.exp(-bake.k_amp * h0 ** n * phi)
        h_exact = h0 * np.exp(-k_loss * t)
        np.testing.assert_allclose(1.0 - depro, m_exact, rtol=1e-12)
        np.testing.assert_allclose(h, h_exact, rtol=1e-12)


# --------------------------------------------------------------------------- #
# Conservation: acid is a catalyst — ∫h conserved / decays exactly e^{−k_loss·t}
# --------------------------------------------------------------------------- #
def test_acid_is_a_catalyst_conserved_or_exact_decay():
    # The tightest leg, on a STRUCTURED (non-flat) image where diffusion is genuinely active: the
    # cited h equation has NO h·m sink (deprotection consumes blocked sites, not acid — acid is a
    # catalyst), so ∫h dx is conserved at k_loss=0 and decays EXACTLY e^{−k_loss·t} otherwise (uniform
    # scalar loss commutes with the conservative engine diffusion). To machine precision.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    _, aerial, _ = _aerial_half(img, PITCH, n_x=256)
    for k_loss in (0.0, 0.005):
        bake = L.CARBake(t_bake_s=40.0, k_amp=2.0, k_loss=k_loss, D_h0_nm2_s=0.09)
        _, h = L.car_peb(aerial, PITCH, bake, n_steps=200)
        assert h.sum() == pytest.approx(aerial.sum() * np.exp(-k_loss * 40.0), rel=1e-10)


def test_deprotection_stays_bounded_and_grows_with_bake():
    # Structural: m starts at 1 and each reaction step multiplies it by exp(−nonneg), and diffusion
    # never touches m, so the deprotection 1−m stays in [0, 1] and grows monotonically with bake time
    # (more bake ⇒ more cumulative ∫hⁿ dt ⇒ more deprotection) — even with acid loss active.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    _, _, h0 = _aerial_half(img, PITCH, n_x=256)
    prev_mean = -1.0
    for t in (5.0, 20.0, 60.0):
        depro, _ = L.car_peb(h0, PITCH, L.CARBake(t_bake_s=t))
        assert depro.min() >= -1e-12 and depro.max() <= 1.0 + 1e-12
        assert depro.mean() > prev_mean
        prev_mean = depro.mean()


# --------------------------------------------------------------------------- #
# Benchmark: amplification sharpens; diffusion / loss / over-bake degrade
# --------------------------------------------------------------------------- #
def test_amplification_sharpens_the_edge():
    # The CAR enhancement signature (loose, a REGIME not a law): in the amplification-dominated regime
    # (cited tiny D ⇒ σ ≈ 0.4 nm, negligible blur over a 240 nm pitch; a short bake ⇒ partial, not
    # saturated, deprotection) the superlinear hⁿ deprotection map is STEEPER at the edge than the
    # acid it came from — NILS(deprotection) > NILS(acid) and the contrast is higher too.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    x, _, h0 = _aerial_half(img, PITCH, n_x=512)
    edge, w = 0.25 * PITCH, 0.5 * PITCH
    nils_acid = L.nils(x, h0, edge, w)
    depro_half, _ = L.car_peb(h0[:256], PITCH / 2.0, L.CARBake(t_bake_s=1.0, k_loss=0.0))
    depro = np.concatenate([depro_half, depro_half[::-1]])
    assert 0.4 < depro.max() < 1.0                         # partial deprotection (not saturated)
    assert L.nils(x, depro, edge, w) > nils_acid            # amplification sharpened the edge
    assert L.image_contrast(depro) > L.image_contrast(h0)


def test_acid_diffusion_blurs_the_developed_image():
    # The acid-diffusion resolution floor (loose): blurring the latent acid before/while it deprotects
    # softens the deprotection edge — larger D (here illustratively far above the cited nm-scale value,
    # to make the small floor visible at this pitch) monotonically drops the contrast and NILS.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    feats = [L.expose_grating_car(img, PITCH,
                                  L.CARBake(t_bake_s=2.0, k_loss=0.0, D_h0_nm2_s=D))
             for D in (0.0933, 50.0, 200.0)]
    assert all(a.contrast > b.contrast for a, b in zip(feats, feats[1:]))
    assert all(a.nils > b.nils for a, b in zip(feats, feats[1:]))


def test_overbake_degrades_the_feature_the_peb_is_critical():
    # The cited "control of the PEB is extremely critical": at fixed dose the developed CD is acutely
    # bake-sensitive — more bake over-amplifies (the bright regions saturate, the line shrinks), so
    # both the printed CD and the deprotection NILS fall monotonically with bake time.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    feats = [L.expose_grating_car(img, PITCH, L.CARBake(t_bake_s=t)) for t in (0.5, 1.0, 2.0, 4.0)]
    assert all(a.cd_nm > b.cd_nm for a, b in zip(feats, feats[1:]))
    assert all(a.nils > b.nils for a, b in zip(feats, feats[1:]))
    assert feats[1].cd_nm == pytest.approx(PITCH / 2.0, abs=20.0)   # a near-nominal bake exists


def test_strang_split_converges_first_order():
    # The coupled-regime defensibility: the bake converges as the step is refined. The split is Strang
    # (½-react · diffuse · ½-react), but the backward-Euler diffusion sub-step caps the time accuracy
    # at FIRST order (honest — not the split's formal second), so the error roughly halves per doubling
    # of n_steps. Shown on a fully coupled case (reaction AND diffusion AND loss all active).
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    _, _, h0 = _aerial_half(img, PITCH, n_x=512)
    bake = L.CARBake(t_bake_s=20.0, k_amp=2.0, k_loss=0.01, D_h0_nm2_s=0.5)
    ref, _ = L.car_peb(h0[:256], PITCH / 2.0, bake, n_steps=1600)
    e_coarse = np.max(np.abs(L.car_peb(h0[:256], PITCH / 2.0, bake, n_steps=100)[0] - ref))
    e_fine = np.max(np.abs(L.car_peb(h0[:256], PITCH / 2.0, bake, n_steps=200)[0] - ref))
    assert e_fine < 0.6 * e_coarse                          # ~halve per doubling (first order)


# --------------------------------------------------------------------------- #
# The named scope edge + guards: the half-period cell refuses an asymmetric image
# --------------------------------------------------------------------------- #
def test_car_refuses_asymmetric_image_and_bad_inputs():
    # The half-period sealed cell is the even image's symmetry cell; an off-axis pole under defocus
    # SHIFTS the fringe (the v1.4 finding) off the mirror planes — refused, not mis-baked (the same
    # Massoud refuse-outside-the-fit discipline as the v1.7 PEB path). Plus the input guards.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    p = 2.2 * img.pitch_min_two_beam
    bake = L.CARBake(t_bake_s=10.0)
    asym = dict(source_fs=L.offaxis_source(img), defocus_nm=80.0)
    with pytest.raises(ValueError, match="symmetric"):
        L.expose_grating_car(img, p, bake, **asym)
    with pytest.raises(ValueError, match="even n_x"):
        L.expose_grating_car(img, PITCH, bake, n_x=511)
    with pytest.raises(ValueError):                         # D=0 ⇒ undefined harmonic-mean face D
        L.car_peb(np.ones(8), 100.0, L.CARBake(t_bake_s=5.0, D_h0_nm2_s=0.0))
    with pytest.raises(ValueError):
        L.car_peb(np.ones(8), 100.0, L.CARBake(t_bake_s=-1.0))


def test_car_uses_backward_euler_no_nan_on_fractional_power():
    # The reason the diffusion sub-step is BE not v1.7's CN: hⁿ with non-integer n (1.8) NaNs on any
    # negative acid ring. A realistic Abbe image baked through the full coupled model stays finite —
    # the developed feature, the NILS, and the peak deprotection are all well-defined.
    img = L.Imaging(LAMBDA, NA, sigma=0.5)
    f = L.expose_grating_car(img, PITCH, L.CARBake(t_bake_s=2.0))
    assert np.isfinite(f.cd_nm) and np.isfinite(f.nils) and np.isfinite(f.contrast)
    assert 0.0 <= f.peak_deprotection <= 1.0
    assert f.cd_um == pytest.approx(f.cd_nm * 1e-3)
