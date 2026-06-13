"""Etch / deposition validation: the seam + the etch/void machinery (plan §7, the flagged tier).

No engine underneath — etch bias and the keyhole-void criterion are closed forms (like Deal–Grove /
Scheil / the yield law) — so these tests carry the whole triad, but with the §7 *flagged-phenomenology*
honesty: the one genuinely tight leg is the **bit-for-bit seam**, the algebra is **machinery
(regression guards)** not a conservation anchor, and the magnitudes are **flagged house numbers** (only
the cited forms / orderings are asserted).

* **Analytical limit / seam (tight).** ``anisotropy = 1`` ⇒ ``bias = 0`` and ``CD_out == CD_in``
  **bit-for-bit** (for any film / over-etch); ``step_coverage = 1`` ⇒ ``AR_crit = ∞`` ⇒ never voids.
* **Machinery (regression guards).** ``bias = 2(1−A)·h(1+OE)``, the underlayer loss ``OE·h/S``, the gap
  aspect ratio ``h/(pitch−CD)``, and the monotonicities — exact bookkeeping, asserted as guards (there
  is no only-possible-law content here, unlike wafer-prep area-additivity).
* **Benchmark (loose).** The :data:`ETCH_ANISOTROPY` / :data:`STEP_COVERAGE` band **orderings** and the
  cited-form contrasts (RIE preserves CD where wet undercuts; CVD fills a gap PVD voids) — magnitudes
  flagged, never asserted.

The stochastic etch-rate non-uniformity (the ``bias_factor`` consumer hook) lives in the game layer
(``fab_game/tests``) — no RNG here.
"""
import math

import pytest

from chip import etch_deposition as ed


# --------------------------------------------------------------------------- #
# Analytical limit / seam (tight): A=1 → bias 0 bit-for-bit; SC=1 → never voids
# --------------------------------------------------------------------------- #
def test_perfect_anisotropy_transfers_cd_bit_for_bit():
    # The one bit-exact anchor: a perfectly anisotropic etch (A=1) changes the CD by EXACTLY zero,
    # for any film thickness / over-etch — (1 − A) = 0 exactly, so the bias is 0.0 to the last bit.
    for h, oe in ((150.0, 0.0), (220.0, 0.5), (90.0, 2.0)):
        r = ed.etch_feature(167.3, film_thickness_nm=h, anisotropy=1.0, over_etch_frac=oe)
        assert r.etch_bias_nm == 0.0
        assert r.cd_out_nm == 167.3            # == , not approx — the seam is exact
        assert r.gate_height_nm == h


def test_conformal_deposition_never_voids():
    # SC = 1 → AR_crit = ∞ → no void at any aspect ratio (the deposition seam).
    assert ed.critical_aspect_ratio(1.0) == math.inf
    # A brutally high-AR gap still fills void-free at perfect conformality.
    r = ed.deposit_fill(gate_height_nm=500.0, pitch_nm=300.0, cd_nm=250.0, step_coverage=1.0)
    assert r.voided is False
    assert r.critical_aspect_ratio == math.inf


def test_perfect_etch_plus_conformal_is_a_full_identity():
    # The combined seam the game wiring rides: A=1 (CD unchanged) AND SC=1 (no void).
    r = ed.etch_feature(167.0, anisotropy=1.0, over_etch_frac=0.3)
    d = ed.deposit_fill(r.gate_height_nm, pitch_nm=300.0, cd_nm=r.cd_out_nm, step_coverage=1.0)
    assert r.cd_out_nm == 167.0 and d.voided is False


# --------------------------------------------------------------------------- #
# Machinery (regression guards): the exact bias / underlayer / aspect-ratio algebra
# --------------------------------------------------------------------------- #
def test_etch_bias_is_twice_the_undercut_exact():
    # bias = 2·(1 − A)·h·(1 + OE) — exact machinery (a regression guard, NOT a conservation anchor).
    h, A, OE = 150.0, 0.8, 0.5
    r = ed.etch_feature(167.0, film_thickness_nm=h, anisotropy=A, over_etch_frac=OE)
    d = h * (1.0 + OE)
    assert r.etch_depth_nm == pytest.approx(d)
    assert r.lateral_undercut_nm == pytest.approx((1.0 - A) * d)
    assert r.etch_bias_nm == pytest.approx(2.0 * (1.0 - A) * d)
    assert r.cd_out_nm == pytest.approx(167.0 - 2.0 * (1.0 - A) * d)


def test_underlayer_loss_is_overetch_over_selectivity():
    # The over-etch excess OE·h, divided by the selectivity, is the underlayer consumed (loss = OE·h/S).
    r = ed.etch_feature(167.0, film_thickness_nm=150.0, anisotropy=0.9,
                        over_etch_frac=0.4, selectivity=20.0)
    assert r.underlayer_loss_nm == pytest.approx(150.0 * 0.4 / 20.0)
    # No over-etch → no underlayer loss.
    r0 = ed.etch_feature(167.0, anisotropy=0.9, over_etch_frac=0.0)
    assert r0.underlayer_loss_nm == 0.0


def test_more_overetch_and_less_anisotropy_shrink_cd():
    # Over-etch → wider undercut → smaller CD (the "over-etch → CD out of spec" failure); and a less
    # anisotropic etch (smaller A) shrinks the CD harder. Monotone — a worse knob, a smaller CD.
    base = ed.etch_feature(167.0, film_thickness_nm=150.0, anisotropy=0.9, over_etch_frac=0.0)
    over = ed.etch_feature(167.0, film_thickness_nm=150.0, anisotropy=0.9, over_etch_frac=0.6)
    assert over.cd_out_nm < base.cd_out_nm
    aniso = ed.etch_feature(167.0, film_thickness_nm=150.0, anisotropy=0.7, over_etch_frac=0.0)
    assert aniso.cd_out_nm < base.cd_out_nm


def test_gap_aspect_ratio_is_height_over_gap():
    # AR = h / (pitch − CD): a taller gate or a tighter gap raises the aspect ratio (the propagation).
    assert ed.gap_aspect_ratio(150.0, 300.0, 167.0) == pytest.approx(150.0 / (300.0 - 167.0))
    taller = ed.gap_aspect_ratio(250.0, 300.0, 167.0)
    tighter = ed.gap_aspect_ratio(150.0, 250.0, 167.0)
    base = ed.gap_aspect_ratio(150.0, 300.0, 167.0)
    assert taller > base and tighter > base


def test_critical_aspect_ratio_limits_and_monotonicity():
    # AR_crit = SC/(1−SC): rises monotonically with coverage, → 0 as SC → 0, → ∞ as SC → 1.
    assert ed.critical_aspect_ratio(0.0) == 0.0
    assert ed.critical_aspect_ratio(0.5) == pytest.approx(1.0)
    covs = [0.1, 0.3, 0.5, 0.8, 0.95]
    crits = [ed.critical_aspect_ratio(c) for c in covs]
    assert crits == sorted(crits)                              # monotone increasing in coverage


def test_lower_coverage_voids_a_gap_a_conformal_film_fills():
    # The same gate gap: a poor PVD (low SC) voids where a conformal CVD (high SC) fills (the contrast).
    geom = dict(gate_height_nm=150.0, pitch_nm=300.0, cd_nm=167.0)   # AR ≈ 1.13
    cvd = ed.deposit_fill(**geom, step_coverage=ed.STEP_COVERAGE["CVD"])
    pvd = ed.deposit_fill(**geom, step_coverage=ed.STEP_COVERAGE["PVD"])
    assert cvd.voided is False
    assert pvd.voided is True
    assert pvd.aspect_ratio == cvd.aspect_ratio                # same geometry — only coverage differs


# --------------------------------------------------------------------------- #
# Benchmark (loose): the flagged process-band orderings + the cited-form contrasts
# --------------------------------------------------------------------------- #
def test_anisotropy_band_orders_directional_highest():
    # FLAGGED illustrative levels — only the ordering is asserted (ideal perfectly anisotropic;
    # RIE highly directional; wet fully isotropic). The numbers are house.
    a = ed.ETCH_ANISOTROPY
    assert a["ideal"] == 1.0 and a["wet"] == 0.0
    assert a["wet"] < a["plasma"] < a["RIE"] < a["ideal"]
    # The cited-form consequence: at the same film, a wet (isotropic) etch undercuts a masked line
    # far more than RIE → a much smaller transferred CD.
    rie = ed.etch_feature(167.0, anisotropy=a["RIE"])
    wet = ed.etch_feature(220.0, anisotropy=a["wet"], film_thickness_nm=40.0)   # thin film, still undercuts
    assert wet.etch_bias_nm > rie.etch_bias_nm


def test_step_coverage_band_orders_conformal_highest():
    # FLAGGED illustrative levels — CVD ≫ PVD step coverage; only the ordering / limits asserted.
    s = ed.STEP_COVERAGE
    assert s["ideal"] == 1.0
    assert s["PVD"] < s["LPCVD"] < s["CVD"] < s["ideal"]
    # A higher coverage fills a strictly higher aspect ratio void-free.
    assert ed.critical_aspect_ratio(s["CVD"]) > ed.critical_aspect_ratio(s["PVD"])


# --------------------------------------------------------------------------- #
# Error guards (the physical limits the game's rework / knobs run into)
# --------------------------------------------------------------------------- #
def test_etch_that_consumes_the_whole_line_raises():
    # A bias ≥ the CD would erase the gate — unphysical, the limit a runaway over-etch hits.
    with pytest.raises(ValueError):
        ed.etch_feature(100.0, film_thickness_nm=200.0, anisotropy=0.0, over_etch_frac=1.0)


def test_invalid_knobs_raise():
    with pytest.raises(ValueError):
        ed.etch_feature(167.0, anisotropy=1.5)
    with pytest.raises(ValueError):
        ed.etch_feature(167.0, over_etch_frac=-0.1)
    with pytest.raises(ValueError):
        ed.etch_feature(167.0, selectivity=0.0)
    with pytest.raises(ValueError):
        ed.critical_aspect_ratio(1.5)


def test_touching_gate_lines_have_no_gap_to_fill():
    # CD ≥ pitch → the gate lines touch → no gap (a degenerate geometry the void model rejects).
    with pytest.raises(ValueError):
        ed.gap_aspect_ratio(150.0, 300.0, 300.0)
