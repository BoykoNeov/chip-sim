"""The seam test (ADR 0005 §5) — the harness does not change the physics.

The load-bearing G1 invariant: at the **nominal recipe with zero variation**, the single centre
die reproduces :func:`chip.demo_device.compute` **bit-for-bit**, field by field. `demo_device` is
the oracle (so the test is self-maintaining — it tracks the demo, never a hard-coded number). If
this ever breaks, a harness change leaked into the physics; nothing else in G1 is allowed to.

This is built and kept green *first* (the advisor's order: deterministic single-die path before a
die map, stochastic layer, yield, or rework exists), and it stays green through every later layer.
"""
from __future__ import annotations

from chip import demo_device

from fab_game import DEFAULT_RECIPE, NO_VARIATION, run_line
from fab_game.steps import device_step, diffusion_step, litho_step, oxidation_step
from fab_game.state import Die
from fab_game.variation import DiePerturbation


def _center_die_full_line():
    """One nominal, zero-variation wafer with a single centre die (grid_n=1, radius_frac=0)."""
    wafer = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=1)
    assert wafer.n_dies == 1
    return wafer.dies[0]


def test_seam_full_line_matches_demo_device_bit_for_bit():
    """The whole pipeline, nominal + no variation, reproduces demo_device's device exactly."""
    flow = demo_device.compute()
    die = _center_die_full_line()

    # Each process output is bit-for-bit the demo's (== , not approx — the seam is exact).
    assert die.x_j_um == flow.sd_junction.x_j_um
    assert die.t_ox_um == flow.gate_oxide.t_ox
    assert die.cd_nm == flow.gate_feature.cd_nm
    assert die.cd_um == flow.gate_feature.cd_um
    assert die.V_t == flow.mos.V_t
    assert die.i_dsat == flow.i_dsat


def test_seam_step_functions_match_demo_device():
    """The per-die step functions (the canonical units) also reproduce demo_device bit-for-bit.

    Pins the *steps* directly (not just the assembled line) so a regression localizes to the step.
    """
    flow = demo_device.compute()
    pert = DiePerturbation()                                   # the identity perturbation
    d = Die(site=(0, 0), radius_frac=0.0)

    d = diffusion_step(d, DEFAULT_RECIPE.diffusion, DEFAULT_RECIPE.channel_N_A)
    assert d.x_j_um == flow.sd_junction.x_j_um

    d = oxidation_step(d, DEFAULT_RECIPE.oxidation, pert)
    assert d.t_ox_um == flow.gate_oxide.t_ox

    d = litho_step(d, DEFAULT_RECIPE.litho, pert)
    assert d.cd_nm == flow.gate_feature.cd_nm

    d = device_step(d, DEFAULT_RECIPE.device, DEFAULT_RECIPE.channel_N_A)
    assert d.V_t == flow.mos.V_t
    assert d.i_dsat == flow.i_dsat


def test_seam_no_variation_does_not_touch_rng():
    """NO_VARIATION yields the identity perturbation without consuming the RNG (focus stays nominal)."""
    import numpy as np

    rng = np.random.default_rng(123)
    die = Die(site=(0, 0), radius_frac=1.0)                    # even an edge die: no trend when disabled
    pert = NO_VARIATION.perturbation(die, rng)
    assert pert == DiePerturbation()
    # The stream is untouched — the first draw equals a fresh generator's first draw.
    assert rng.normal() == np.random.default_rng(123).normal()
