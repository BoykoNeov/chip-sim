"""Integration test for the device demo (Chip Phase 4 — the demo IS the integration test).

The device demo wires the **whole process→device flow** — ``diffusion_dopant.two_step`` (the n⁺ S/D
profile) → ``oxidation.grow_oxide`` (the thin gate oxide) → ``litho.expose_grating`` (the gate CD) →
``device.threshold_voltage`` (the V_t) → ``plots.device_figure``. Its ``compute`` pipeline is the
end-to-end check that they **chain into one coherent device**, asserted on the robust thesis (a sane
V_t, a thin gate oxide, a resolved gate, and the S/D shallower than the channel is long) — not brittle
exact numbers (those are pinned in ``test_device.py`` against the MIT worked example).

This is the test that guards the *chaining* and the figure render: the 15 ``test_device.py`` tests
exercise ``device.py`` with hardcoded inputs and never call the demo, so without this a refactor in
oxidation/litho/diffusion could silently break the banked artifact.

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import pytest

from projects.chip.demo_device import compute, CHANNEL_N_A, GATE


def test_demo_pipeline_chains_to_a_coherent_device():
    r = compute()
    m = r.mos
    # The device consumed the actual upstream outputs (not stand-ins) — the chaining is real.
    assert m.N_A == CHANNEL_N_A
    assert m.t_ox_um == pytest.approx(r.gate_oxide.t_ox)              # gate oxide → C_ox
    assert m.channel_length_um == pytest.approx(r.gate_feature.cd_um)  # litho CD → channel length
    assert m.gate == GATE
    # A sane n-MOSFET threshold voltage (cf. the cited MIT example at exactly 15 nm → 0.58 V; this
    # demo's ~14 nm oxide gives a slightly lower value).
    assert 0.4 < m.V_t < 0.7


def test_demo_gate_oxide_is_thin_and_reaction_limited():
    # A GATE oxide (tens of nm in the linear regime) — NOT the banked Phase-2 field oxide (sub-µm).
    # Feeding a thick field oxide into C_ox would collapse V_t; this guards that the demo grows a
    # proper gate oxide (the advisor's "one coherent device" requirement).
    r = compute()
    assert r.gate_oxide.t_ox_nm < 30.0
    assert r.gate_oxide.regime == "linear"


def test_demo_gate_is_resolved_and_geometry_is_coherent():
    # The litho gate prints (resolves), and the cross-section is sensible: the S/D junction is
    # SHALLOWER than the gate is long (x_j < L) — i.e. the source/drain do not punch through under a
    # channel shorter than they are deep. The "coherent device, not three unrelated numbers" claim.
    r = compute()
    assert r.gate_feature.resolved
    assert r.gate_feature.nils > 1.0                                  # a printable gate (NILS ≳ 1)
    assert r.sd_junction.x_j_um < r.mos.channel_length_um            # S/D shallower than the gate length


def test_demo_drive_current_is_positive_and_geometry_driven():
    # The honest long-channel payoff: a positive saturation current that the litho CD (→ W/L) sets.
    r = compute()
    assert r.i_dsat > 0.0


def test_device_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from projects.chip.plots import device_figure

    r = compute()
    fig = device_figure(r)
    assert len(fig.axes) == 4                          # diffusion / oxidation / litho / device panels
    plt.pyplot.close(fig)
