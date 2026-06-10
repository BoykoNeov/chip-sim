"""Integration test for the high-concentration D(N) demo (Chip v1.3 — the demo IS the integration test).

The demo wires the box pipeline — ``diffusion_highconc.constant_D_predeposit`` (the constant-``D``
baseline) and ``predeposit_highconc`` (the enhanced box, + the ``n¹`` companion) → junction reading →
``plots`` — on one shared grid. Its compute pipeline is the end-to-end check that they compose,
asserted on the *robust* theses (the box is deeper + boxier than constant ``D``; the surface ``D`` is
strongly enhanced), not on a precise magnitude (the benchmark leg is the loose/calibrated one).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_diffusion_highconc import compute


def test_demo_pipeline_produces_box_case():
    case = compute()
    # the shared depth axis + the capped/uncapped boxes + the cited annotations
    assert {"x", "box", "box_uncapped", "const", "enhancement", "xj_box", "xj_const", "n_i"} <= set(case)
    assert case["box"].shape == case["const"].shape == case["x"].shape
    assert case["name"] == "phosphorus"


def test_demo_box_is_deeper_and_more_enhanced_than_constant_D():
    case = compute()
    # the (capped, physical) box junction is markedly deeper than the constant-intrinsic-D erfc
    assert case["xj_box"] > 2.0 * case["xj_const"]
    # the surface diffusivity is strongly enhanced even capped (~×42); the uncapped upper bound is ~10×
    assert case["surface_enhancement"] > 20.0
    assert case["surface_enhancement_uncapped"] > 5.0 * case["surface_enhancement"]
    # the (uncapped) box is the deeper upper bound (full activation drives D harder)
    assert case["xj_box_uncapped"] > case["xj_box"]
    # the enhancement collapses to ~1 in the dilute tail (the box mechanism; no anomalous tail boost)
    assert case["enhancement"][-1] == pytest.approx(1.0, abs=0.2)
    # no overshoot above the surface solubility
    assert case["box"].max() <= case["N_surface"] * (1.0 + 1e-6)


def test_highconc_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import highconc_figure

    fig = highconc_figure(compute())
    assert len(fig.axes) == 2                           # the box panel + the mechanism panel
    plt.pyplot.close(fig)
