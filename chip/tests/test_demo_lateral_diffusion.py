"""Integration test for the lateral-diffusion demo (Chip v1.8 — the demo IS the integration test).

The demo wires the v1.8 chain — ``diffusion_2d.lateral_diffusion`` (the 2-D engine, masked
constant source) + ``junction_geometry`` (the contour reading) → ``plots`` — and its ``compute``
pipeline is the end-to-end check that they compose. Asserted on the *robust* thesis (the
window-centre column is the 1-D erfc; the ratio sits in the cited constant-source regime and is
contour-dependent — a loose benchmark, running slightly above the one cited point), not brittle
exact numbers (those are pinned in ``test_diffusion_2d.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_lateral_diffusion import compute, RATIO_BAND, N_B_DEVICE


@pytest.fixture(scope="module")
def data():
    return compute()


def test_demo_window_column_is_the_1d_erfc_junction(data):
    # The seam surfaced in the demo: the engine's window-centre vertical junction equals the analytic
    # 1-D erfc junction across the whole contour family (the last two summary columns agree).
    np.testing.assert_allclose(data["verticals"], data["analytic_vert"], rtol=1.5e-2)


def test_demo_ratio_band_and_contour_dependence(data):
    # The benchmark made visible: the ratio rises monotonically toward deeper contours, the mid
    # contours land in the cited band, and the realistic device junction is computed (a touch higher).
    ratios = data["ratios"]
    assert all(a < b for a, b in zip(ratios, ratios[1:]))          # contour-dependence
    lo, hi = RATIO_BAND
    in_band = [(lo - 0.03) <= r <= (hi + 0.03) for r in ratios]
    assert any(in_band)                                            # the mid contours sit in the band
    assert 0.7 < data["device"].ratio < 0.95
    assert data["device"].N_B == N_B_DEVICE


def test_demo_lateral_is_sub_vertical_everywhere(data):
    # Every contour: a real lateral encroachment, always less than the vertical depth.
    assert np.all(data["laterals"] > 0.0)
    assert np.all(data["laterals"] < data["verticals"])


def test_lateral_diffusion_figure_builds(data):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import lateral_diffusion_figure

    fig = lateral_diffusion_figure(data)
    assert len(fig.axes) >= 2                     # the field panel + the ratio panel (+ colorbar)
    plt.pyplot.close(fig)
