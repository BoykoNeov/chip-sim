"""Lateral diffusion under a mask edge — the mask-edge instantiation's mini-triad (Chip v1.8).

The 2-D solver *machinery* (conservation, the dimensional-collapse seam, isotropy, monotonicity)
is sealed in ``engines/diffusion/tests/test_diffusion2d.py``. These tests validate the **chip
instantiation** of it — the constant-source masked diffusion:

* **Seam (tight) — the window-centre column IS the 1-D erfc.** Far from the mask edge the window
  is locally 1-D, so the window-centre vertical junction must equal the analytic constant-source
  junction ``erfcinv(C_B/N_s)·2√(Dt)`` — tying the 2-D demo back to the validated spine, and
  confirming the lateral build did not disturb the vertical physics.
* **Benchmark (loose, cited) — the lateral/vertical ratio and its contour-dependence.** The
  lateral junction reaches ≈ 0.75–0.85 of the vertical at the shallow contours (the cited constant-
  source band) and the ratio **rises monotonically toward deeper (lower-``C_B/N_s``) contours** — the
  textbook contour-dependence (Kennedy–O'Brien 1965: the junction sits closer to its source at the
  surface than in the bulk), falling straight out of the 2-D solve (cited, not fit). This is a
  *loose* benchmark: at the one cited point (≈ 0.82 at ``C_B/N_s = 1e-4``) the model runs ~5–10 %
  high, so the assertions are intervals, not equalities — the validation weight is the tight erfc
  anchor above, not hitting 0.8 precisely.
* **Non-separable signature.** The lateral reach is a real, sub-vertical fraction (``0 < lateral
  < vertical``): dopant genuinely encroaches under the mask, which a 1-D / separable model cannot
  produce — the reason the 2-D regime is needed at all. (For this constant-source geometry the
  maximum lateral encroachment is *at the surface* — surface-lateral and max-over-depth coincide.)
* **Bounds / sanity.** The field stays within ``[0, N_s]`` (the M-matrix maximum principle) and the
  window surface sits at ≈ ``N_s`` (the Dirichlet window is honoured).
"""
import math

import numpy as np
import pytest
from scipy.special import erfcinv

from chip.diffusion_2d import lateral_diffusion, junction_geometry
from chip.diffusion_dopant import CM_PER_UM


@pytest.fixture(scope="module")
def boron_profile():
    # One masked boron diffusion shared by the suite (1100 °C / 60 min, solubility surface).
    return lateral_diffusion("B", T_celsius=1100.0, t_min=60.0, nx=200, ny=160, n_steps=400)


# --------------------------------------------------------------------------- #
# Seam — the window-centre column is the analytic 1-D constant-source erfc junction
# --------------------------------------------------------------------------- #
def test_window_center_vertical_junction_matches_1d_erfc(boron_profile):
    p = boron_profile
    two_sqrt_Dt = 2.0 * math.sqrt(p.D * p.t)
    for frac in (1e-2, 1e-3, 1e-4):
        N_B = frac * p.N_surface
        jg = junction_geometry(p, N_B)
        analytic_um = erfcinv(frac) * two_sqrt_Dt / CM_PER_UM
        assert jg.vertical_um == pytest.approx(analytic_um, rel=1.5e-2)


# --------------------------------------------------------------------------- #
# Benchmark — lateral/vertical ≈ 0.75–0.85, rising toward deeper contours
# --------------------------------------------------------------------------- #
def test_lateral_vertical_ratio_in_cited_band_at_mid_contours(boron_profile):
    p = boron_profile
    # The canonical "lateral ≈ 0.8 × vertical" rule is a mid-contour statement (C_B/N_s ~ 1e-2..1e-3).
    r_shallow = junction_geometry(p, 1e-2 * p.N_surface).ratio
    r_mid = junction_geometry(p, 1e-3 * p.N_surface).ratio
    assert 0.72 <= r_shallow <= 0.86           # the cited 0.75–0.85 band (± a small margin)
    assert 0.78 <= r_mid <= 0.88


def test_ratio_rises_toward_deeper_contours(boron_profile):
    # Contour-dependence (the textbook nuance the single "0.8" hides): the ratio increases
    # monotonically as the contour deepens (C_B/N_s falls). Falls straight out of the 2-D field.
    p = boron_profile
    fracs = (1e-2, 1e-3, 1e-4, 1e-5)
    ratios = [junction_geometry(p, f * p.N_surface).ratio for f in fracs]
    assert all(a < b for a, b in zip(ratios, ratios[1:]))
    assert all(0.7 < r < 0.95 for r in ratios)   # all physically sane (sub-unity)


# --------------------------------------------------------------------------- #
# Non-separable signature + bounds
# --------------------------------------------------------------------------- #
def test_lateral_reach_is_real_and_sub_vertical(boron_profile):
    # The genuinely-2-D point: a real lateral encroachment under the mask, but less than the vertical
    # depth (a 1-D model gives lateral = 0; an isotropic point source would give ratio → 1).
    jg = junction_geometry(boron_profile, 1e-3 * boron_profile.N_surface)
    assert jg.lateral_um > 0.0
    assert 0.0 < jg.ratio < 1.0


def test_field_bounded_and_window_surface_honoured(boron_profile):
    p = boron_profile
    assert p.N.min() >= -1e-6                                   # no negative undershoot
    assert p.N.max() <= p.N_surface * (1.0 + 1e-9)             # no overshoot past the source
    # the window-centre surface cell sits near N_s (Dirichlet face, one half-cell above the centre)
    assert p.window_column[0] == pytest.approx(p.N_surface, rel=0.05)
