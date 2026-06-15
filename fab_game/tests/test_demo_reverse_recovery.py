"""Integration test for the S5 demo (the demo IS the integration check).

The S5 demo shows the **lifetime axis** read two opposite ways: junction leakage ``J_gen ∝ 1/τ`` (the logic
killer, the G4b channel) and reverse-recovery ``t_rr ∝ τ`` (the rectifier feature). The capstone of the
whole device-targets plan: on one τ axis the pass bands are **disjoint** — short τ ships a rectifier, long τ
ships logic, and a dead zone between is good as **neither**. Asserted on the robust, **honest** theses — the
two faces, the disjoint bands / dead zone, the moving optimum, the substrate commit — not brittle numbers
(the physics is pinned in ``chip/tests/test_reverse_recovery.py`` and the target wiring in
``test_targets_power.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke test
only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from fab_game.demo_reverse_recovery import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the per-knob pipeline runs are the cost)."""
    return compute()


def test_demo_two_faces_of_one_tau(r):
    """Panel 1: over a τ sweep the junction leakage ``∝ 1/τ`` falls while the recovery time ``∝ τ`` rises —
    the same lifetime, two opposite consequences."""
    leak = np.asarray(r.leak_fine)
    t_rr = np.asarray(r.t_rr_fine_ns)
    # τ increases across the sweep (logspace), so leakage falls and t_rr rises — strictly, opposite signs.
    assert np.all(np.diff(leak) < 0.0)                          # leakage ∝ 1/τ: strictly decreasing
    assert np.all(np.diff(t_rr) > 0.0)                          # t_rr ∝ τ: strictly increasing


def test_demo_bands_are_disjoint_with_a_dead_zone(r):
    """The capstone: the rectifier ships BELOW its τ edge, logic ships ABOVE its (higher) τ edge, so the
    bands are disjoint and a non-empty dead zone — good as NEITHER — sits between them."""
    assert math.isfinite(r.tau_trr_edge_s) and math.isfinite(r.tau_leak_edge_s)
    # rectifier edge (t_rr ceiling) is below the logic edge (leakage ceiling) → the bands do not touch.
    assert r.tau_trr_edge_s < r.tau_leak_edge_s
    # the dead zone is the open interval between them — a mediocre lifetime serves neither product.
    assert r.tau_leak_edge_s - r.tau_trr_edge_s > 0.0


def test_demo_optimum_moves_with_the_declaration(r):
    """Panel 2: more zone passes → cleaner feed → longer τ; the native-MOSFET revenue rises (it wants the
    clean feed) while the rectifier revenue falls (it wants the lifetime-killed feed) — the best SKU flips."""
    tau = np.asarray(r.tau_pipe_us)
    native = np.asarray(r.native_rev)
    rectifier = np.asarray(r.rectifier_rev)
    assert np.all(np.diff(tau) > 0.0)                           # cleaner feed → strictly longer τ
    assert list(native) == sorted(native)                       # native revenue non-decreasing in passes
    assert list(rectifier) == sorted(rectifier, reverse=True)   # rectifier revenue non-increasing
    # The optimum genuinely flips: rectifier wins the dirty (low-pass) end, native the clean (high-pass) end.
    assert rectifier[0] > native[0]
    assert native[-1] > rectifier[-1]
    # And there is at least one feed cleanliness good as NEITHER (the dead zone, on the pipeline this time).
    assert np.any((native == 0.0) & (rectifier == 0.0))


def test_demo_substrate_commit_gates_breakdown(r):
    """Panel 3: a short τ is necessary but not sufficient — the rectifier also needs the light (high-res)
    boule for its blocking voltage. BV rises as the substrate lightens and crosses the floor only there."""
    bv = np.asarray(r.bv_sweep)
    assert np.all(np.diff(bv) < 0.0)                            # heavier substrate (rising N) → lower BV
    assert math.isfinite(r.n_seed_bv_edge)                      # the BV floor is crossed somewhere in the sweep
    # The lightest boule clears the floor; the heaviest does not — a hard substrate gate (the S3 commit).
    assert bv[0] > r.bv_floor > bv[-1]


def test_reverse_recovery_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import reverse_recovery_figure

    fig = reverse_recovery_figure(r)
    assert len(fig.axes) >= 3                                    # two-faces / optimum / substrate panels
    plt.pyplot.close(fig)
