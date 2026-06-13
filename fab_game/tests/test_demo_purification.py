"""Integration test for the G4 purification demo (the demo IS the integration check).

The purification demo wires the new zone-refining segregation physics (:mod:`chip.purification`) +
the device's lifted ``Q_ox`` edge through the harness into the contamination artifact. Its
``compute`` is the end-to-end check that the scrub → contamination → ``Q_ox`` → ``V_t`` → yield chain
holds together — asserted on the robust thesis (the scrubbing contrast; a dirty feed scraps the wafer
on V_t; more passes recover it), not brittle exact numbers (the segregation law is pinned in
``chip/tests/test_purification.py``, the wiring in ``test_contamination.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game import wafer_yield
from fab_game.demo_purification import compute


def test_demo_one_pass_scrubs_metals_far_harder_than_boron():
    """The scrubbing contrast: one zone pass cuts Fe ~5 orders, boron barely (the verifiable win)."""
    r = compute()
    fe_factor = r.refined_vector["Fe"] / r.feed_vector["Fe"]
    b_factor = r.refined_vector["B"] / r.feed_vector["B"]
    assert fe_factor < 1e-4                                  # metal scrubbed ~5 orders
    assert b_factor > 0.5                                    # boron barely touched
    assert fe_factor < b_factor                              # the contrast


def test_demo_grade_ladder_walks_vt_down_and_scraps_mgs():
    """Dirtier feed → V_t walks down; clean passes, MGS (one pass) falls out the bottom on V_t."""
    r = compute()
    by_grade = dict(zip(r.grades, r.vt_by_grade))
    # The clean/EGS/solar grades are in spec; MGS (one pass) is below the floor. (clean ≈ EGS to ~mV —
    # EGS's trace residual dopant just outweighs its trace Na — so the *meaningful* walk-down is the
    # dirty end: solar sits below clean, MGS below the V_t floor.)
    for g in ("clean", "EGS", "solar"):
        assert r.v_t_lo <= by_grade[g] <= r.v_t_hi
    assert by_grade["solar"] < by_grade["clean"]             # Na (solar) shifts V_t down, in spec
    assert by_grade["MGS"] < by_grade["solar"] < r.v_t_hi    # MGS walks furthest down…
    assert by_grade["MGS"] < r.v_t_lo                        # …out the bottom of the window
    assert wafer_yield(r.dead_wafer) == 0.0                  # the dirty wafer is scrapped on V_t
    # The failure trail names the contamination root cause (not defocus).
    assert "purification" in r.dead_trail and "Q_ox" in r.dead_trail


def test_demo_more_passes_recover_the_wafer():
    """Purify harder: a second zone pass scrubs the Na → V_t back in spec → yield recovers (the rework)."""
    r = compute()
    assert wafer_yield(r.dead_wafer) == 0.0                  # one pass: dead
    assert wafer_yield(r.recovered_wafer) == 1.0             # two passes: recovered
    # V_t-vs-passes climbs from out-of-spec (1 pass) into spec and stays there.
    assert r.vt_by_pass[0] < r.v_t_lo                        # 1 pass: below floor
    assert all(r.v_t_lo <= v <= r.v_t_hi for v in r.vt_by_pass[1:])   # ≥2 passes: in spec
    # The residual boron persists across passes (k≈0.8 — un-refinable by segregation).
    assert r.recovered_wafer.contamination.B > 0.0


def test_purification_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import purification_figure

    r = compute()
    fig = purification_figure(r)
    assert len(fig.axes) >= 3                               # scrubbing / grade-ladder / rework panels
    plt.pyplot.close(fig)
