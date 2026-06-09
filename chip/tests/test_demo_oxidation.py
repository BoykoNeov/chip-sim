"""Integration test for the oxidation demo (Chip Phase 2 — the demo IS the integration test).

The oxidation demo wires the whole Deal–Grove chain — ``oxidation.oxide_rate_constants`` (cited
Arrhenius B, B/A) → ``oxide_thickness`` (the closed-form sweep) → ``grow_oxide`` (the 1-hour table
point + bookkeeping) → ``plots``. Its compute pipeline is the end-to-end check that they compose,
asserted on the *robust* thesis (wet ≫ dry, sub-µm in an hour, the linear→parabolic bend, the 0.44
silicon balance), not brittle exact numbers (those are pinned in ``test_oxidation.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from projects.chip.demo_oxidation import (
    compute, T_RANGE_HOURS, PUBLISHED_DRY_UM, PUBLISHED_WET_UM,
)


def test_demo_pipeline_wet_dry_oxide_growth():
    t_hours, curves, table = compute()
    # The sweep spans the requested time range, ascending.
    assert t_hours[0] == pytest.approx(T_RANGE_HOURS[0])
    assert t_hours[-1] == pytest.approx(T_RANGE_HOURS[1])
    # Two ambients; each curve grows monotonically with time and sits in a sane sub-µm-to-µm band.
    labels = [c[0] for c in curves]
    assert any("dry" in s for s in labels) and any("wet" in s for s in labels)
    for _, x_ox, B, A, _ in curves:
        assert np.all(np.diff(x_ox) > 0)              # monotone growth
        assert x_ox[0] < x_ox[-1] < 10.0              # bounded, ascending

    # The headline 1-hour table point: wet ≫ dry, both in the published neighbourhood.
    dry, wet = table["dry"], table["wet"]
    assert wet.t_ox > 5.0 * dry.t_ox
    assert 0.07 < dry.t_ox < 0.13 and 0.55 < wet.t_ox < 0.75


def test_demo_curves_show_linear_then_parabolic_bend():
    # The teaching point: early in the sweep the oxide is thin (linear/reaction-limited regime);
    # late it is thick (parabolic/diffusion-limited). The slope on log-log falls from ~1 to ~½.
    t_hours, curves, _ = compute()
    for _, x_ox, _, _, _ in curves:
        logslope = np.diff(np.log(x_ox)) / np.diff(np.log(t_hours))
        assert logslope[0] == pytest.approx(1.0, abs=0.15)     # thin end ≈ linear (slope 1)
        assert logslope[-1] < 0.75                              # thick end bending toward parabolic (½)


def test_demo_silicon_bookkeeping_closes():
    # The conservation leg surfaced in the demo: consumed Si + oxide above surface = total oxide.
    _, _, table = compute()
    for g in table.values():
        assert g.si_consumed + g.oxide_above_original_surface == pytest.approx(g.t_ox, rel=1e-12)


def test_demo_published_points_sane():
    # The artifact carries representative published comparison points (reference facts) — a
    # regression guard that the demo's context numbers stay sane.
    assert 0.05 < PUBLISHED_DRY_UM < 0.2
    assert 0.4 < PUBLISHED_WET_UM < 0.9
    assert PUBLISHED_WET_UM > PUBLISHED_DRY_UM


def test_oxidation_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from projects.chip.plots import oxidation_figure

    t_hours, curves, _ = compute()
    fig = oxidation_figure(t_hours, curves)
    assert len(fig.axes) == 2                          # thickness panel + mechanism panel
    plt.pyplot.close(fig)
