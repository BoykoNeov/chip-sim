"""Integration test for the 2-D MOSFET cross-section demo (Chip v1.11 — the demo IS the integration).

The demo wires the v1.11 chain — ``device_2d.mosfet_cross_section`` (the two-window 2-D solve + the
Phase-4 device read) + the ``L_drawn`` sweep → ``plots`` — and its ``compute`` pipeline is the
end-to-end check that they compose. Asserted on the *robust* thesis (the device is a coherent
shortened MOSFET; the two L_eff routes agree across the open sweep and punch through together; V_t is
flat — the boundary), not brittle numbers (those are pinned in ``test_device_2d.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_device_2d import compute, L_DRAWN_HEADLINE_UM


@pytest.fixture(scope="module")
def data():
    return compute()


def test_demo_headline_is_a_coherent_shortened_device(data):
    # The payoff surfaced in the demo: a real MOSFET whose channel is shortened by lateral S/D
    # diffusion, with the two independent L_eff routes agreeing.
    d = data.device
    assert d.L_drawn_um == L_DRAWN_HEADLINE_UM
    assert 0.0 < d.L_eff_true_um < d.L_drawn_um
    assert abs(d.L_eff_true_um - d.L_eff_approx_um) < 0.012      # two-window ≡ subtraction
    assert d.current_gain > 1.0                                 # a shorter channel drives more current


def test_demo_sweep_routes_agree_then_punch_through(data):
    # The mechanism made visible: across the open range the two-window solve lies on the subtraction;
    # both reach punchthrough at the narrowest gates (~2ΔL).
    true, approx = data.L_eff_true_sweep, data.L_eff_approx_sweep
    open_ = true > 0.03
    np.testing.assert_allclose(true[open_], approx[open_], atol=0.012)
    assert np.any(true == 0.0)                                  # punchthrough reached at small L_drawn
    # the punchthrough threshold the subtraction predicts sits where the two-window solve closes
    pt_L = data.L_drawn_sweep[true == 0.0]
    assert pt_L.max() <= data.two_delta_L_um <= pt_L.max() + 0.04


def test_demo_Vt_is_flat_the_boundary(data):
    # The honest boundary: V_t is long-channel — one scalar across the whole L_drawn sweep (no DIBL).
    assert data.V_t == data.device.mos.V_t
    assert data.device.mos.V_t == data.device.mos_drawn.V_t     # L_eff vs L_drawn device: same V_t


def test_device_2d_figure_builds(data):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import device_2d_figure

    fig = device_2d_figure(data)
    assert len(fig.axes) >= 2                                   # the cross-section + the mechanism (+ twin/cbar)
    plt.pyplot.close(fig)
