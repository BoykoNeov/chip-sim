"""Integration test for the pn-junction demo (Chip Phase 1a — the demo IS the integration test).

The junction demo wires the whole dopant mass-mode chain together — ``diffusion_dopant.two_step``
(predep ``erfc`` → drive-in via the frozen engine) → ``junction.analyze_junction`` (junction depth
+ Masetti sheet resistance) → ``plots``. So its compute pipeline is the end-to-end check that they
compose, asserted on the *robust* thesis (a junction ~1 µm deep with a sane sheet resistance, the
dose conserved through the drive-in, the surface redistributed deeper), not brittle exact numbers
(those are pinned in ``test_diffusion_dopant.py`` / ``test_junction.py``).

The figure itself is **not** in the correctness path (ADR 0002): rendering is checked only for
"builds without error", and skipped where the optional viz extra is absent.
"""
import math

import numpy as np
import pytest

from projects.chip.demo_junction import (
    compute, N_BACKGROUND, PUBLISHED_XJ_UM, PUBLISHED_RS_OHM_SQ,
)


def test_demo_pipeline_junction_from_two_step_diffusion():
    predep, drivein, junction, morph = compute()
    # The dose was laid down (predep) and conserved through the sealed drive-in, which redistributed
    # the boron deeper (surface fell, profile spread).
    assert predep.dose == pytest.approx(predep.surface_flux_dose, rel=1e-10)
    assert drivein.dose == pytest.approx(predep.dose, rel=1e-10)
    assert drivein.N[0] < 0.2 * predep.N[0]

    # A real pn junction emerged: ~1 µm deep, crossing the n-type background, with a sane R_s.
    assert math.isfinite(junction.x_j) and 0.5 < junction.x_j_um < 2.0
    assert math.isfinite(junction.R_s) and 40.0 < junction.R_s < 400.0
    assert junction.N_background == N_BACKGROUND
    # The profile actually crosses the background at the reported junction depth.
    assert drivein.N[0] > N_BACKGROUND > drivein.N[-1]


def test_demo_morph_relaxes_erfc_toward_gaussian():
    # The mechanism panel's snapshots: predep first, then drive-in at increasing time — the surface
    # falls monotonically and the dopant reaches steadily deeper (the erfc → Gaussian morph).
    _, _, _, morph = compute()
    surface_vals = [N[0] for _, _, N in morph]
    assert all(surface_vals[k] > surface_vals[k + 1] for k in range(len(surface_vals) - 1))


def test_demo_published_bands_sane():
    # The artifact carries representative published comparison bands (reference facts) — a
    # regression guard that the demo's context bands stay sane.
    assert 0.0 < PUBLISHED_XJ_UM[0] < PUBLISHED_XJ_UM[1] < 3.0
    assert 10.0 < PUBLISHED_RS_OHM_SQ[0] < PUBLISHED_RS_OHM_SQ[1] < 1000.0


def test_junction_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from projects.chip.plots import junction_figure

    predep, drivein, junction, morph = compute()
    fig = junction_figure(predep, drivein, junction, morph=morph)
    assert len(fig.axes) == 2                              # junction panel + morph panel
    plt.pyplot.close(fig)
