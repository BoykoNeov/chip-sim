"""Integration test for the thin-oxide demo (Chip v1.1 — the demo IS the integration test).

The thin-oxide demo wires the promoted Massoud correction across the chain — ``oxidation``'s
§5 closed form (the cited time-decay model) against the v1 plain-Deal–Grove path, then feeds
both gate oxides to the Phase-4 ``device.threshold_voltage`` to surface the V_t consequence.
Asserted on the *robust* theses (the burst is real and ~1.5×, it bites the gate recipe, it is
V_t-sized downstream, and it saturates), not brittle exact numbers (those are pinned in
``test_oxidation.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for
"builds without error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_thin_oxide import compute, GATE_MIN, T_GATE, T_RANGE_MIN


def test_demo_pipeline_massoud_before_after():
    t_min, curves, rates, gate, vt = compute()
    # The sweep spans the requested window, ascending; all three thickness curves are monotone.
    assert t_min[0] == pytest.approx(T_RANGE_MIN[0]) and t_min[-1] == pytest.approx(T_RANGE_MIN[1])
    for name in ("massoud", "plain_same_ba", "v1_dg1965"):
        assert np.all(np.diff(curves[name]) > 0)
    # The headline gate point: the Massoud oxide lands in the cited neighbourhood (~23 nm) and
    # meaningfully above the v1 prediction (~14 nm) — the before/after the artifact banks.
    g_m, g_v1 = gate["massoud"], gate["v1"]
    assert 0.021 < g_m.t_ox < 0.026
    assert g_m.t_ox > 1.4 * g_v1.t_ox
    assert g_m.model == "massoud" and g_v1.model == "deal-grove"


def test_demo_burst_is_positive_and_saturating():
    # The enhancement is positive everywhere (Massoud ≥ the same-B,A baseline) and FINITE: by the
    # end of the sweep (t ≫ τ₂) the extra thickness has stopped growing (the saturated dose).
    t_min, curves, rates, _, _ = compute()
    extra = curves["massoud"] - curves["plain_same_ba"]
    assert np.all(extra[1:] > 0)
    late = extra[t_min > 4.0 * rates.tau2]
    assert late.size > 3 and np.all(np.diff(late) < 0)   # past the burst the gap is closing
    # And the rate curves converge (mechanism panel): final ratio ≈ 1.
    ratio = curves["rate_massoud"][-1] / curves["rate_plain"][-1]
    assert ratio == pytest.approx(1.0, abs=0.05)


def test_demo_vt_consequence_is_device_sized():
    # The payoff: the thicker (honest) gate oxide moves the Phase-4 threshold voltage by a
    # device-sized step (hundreds of mV), in the right direction (thicker oxide → higher V_t).
    _, _, _, gate, vt = compute()
    dv = vt["massoud"].V_t - vt["v1"].V_t
    assert 0.2 < dv < 0.8
    # Coherence: both readouts share the channel; only t_ox differs.
    assert vt["massoud"].phi_F == pytest.approx(vt["v1"].phi_F)


def test_demo_recipe_is_inside_the_cited_range():
    # Guard the demo recipe itself: the gate-oxide point must stay inside the cited Massoud fit
    # window (800–1000 °C, the refuse-don't-extrapolate edge) and inside the plotted sweep.
    from chip import oxidation as ox
    lo, hi = ox.MASSOUD_T_RANGE_C
    assert lo <= T_GATE <= hi
    assert T_RANGE_MIN[0] <= GATE_MIN <= T_RANGE_MIN[1]


def test_thin_oxide_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import thin_oxide_figure

    t_min, curves, rates, gate, _ = compute()
    fig = thin_oxide_figure(
        t_min, curves, rates, gate_t_min=GATE_MIN,
        gate_massoud_nm=gate["massoud"].t_ox_nm, gate_v1_nm=gate["v1"].t_ox_nm,
    )
    assert len(fig.axes) == 2                          # thickness panel + mechanism panel
    plt.pyplot.close(fig)
