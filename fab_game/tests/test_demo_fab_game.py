"""Integration test for the G1 demo (the demo IS the integration test, as with the chip demos).

Guards the banked artifact's *thesis*, not brittle numbers (the magnitudes are flagged house
defaults — ADR 0005 §5): a good recipe yields high, one bad knob (defocus) kills an **edge ring**,
the failure trail names **defocus**, and a litho rework **recovers** the lost dies. Without this, a
refactor in the harness or an upstream chip module could silently break the dramatic win.
"""
from __future__ import annotations

import pytest

from fab_game.demo_fab_game import BAD_DEFOCUS_NM, compute


def test_good_recipe_yields_high_bad_knob_kills_dies():
    """The dramatic win: in focus → high yield; one bad knob (defocus) → dies die."""
    r = compute()
    assert r.good.yield_ >= 0.9                               # in focus → nearly all good
    assert r.bad.yield_ < r.good.yield_                       # one bad knob lowers yield
    assert len(r.bad.dead_dies) > 0                           # and actually kills dies


def test_failure_is_an_edge_ring():
    """The center-to-edge focus bowl makes the failure spatial: dead dies sit further out."""
    r = compute()
    dead_r = [d.radius_frac for d in r.bad.dead_dies]
    alive_r = [d.radius_frac for d in r.bad.wafer.dies if d.verdict.passed]
    assert sum(dead_r) / len(dead_r) > sum(alive_r) / len(alive_r)   # dead ring is further out


def test_failure_trail_names_defocus():
    """The trail traces the dead die back to its (amplified) effective defocus — the named cause."""
    r = compute()
    assert r.dead_die is not None
    assert "defocus" in r.dead_trail.lower()
    litho = next(rec for rec in r.dead_die.history if rec.step == "litho")
    # The worst die's effective defocus exceeds the knob (the center-to-edge tilt amplified it).
    assert litho.knobs_in["defocus_nm"] > BAD_DEFOCUS_NM
    # It died on the litho printability metric (NILS), the physical defocus signature.
    assert any("NILS" in reason for reason in r.dead_die.verdict.reasons)


def test_extreme_defocus_collapses_cd_and_idsat():
    """The plan §1 *literal* chain: at extreme defocus the CD itself goes out of window AND I_Dsat
    leaves spec — the regime past mere NILS loss (the G1 finding: NILS is the primary signature,
    CD/I_Dsat the extreme-defocus one, with I_Dsat over its *ceiling* as the shorter channel
    over-drives)."""
    r = compute()
    reasons = {reason.split(" (")[0] for d in r.extreme.wafer.dies if d.verdict.failed
               for reason in d.verdict.reasons}
    joined = " ".join(reasons)
    assert "CD" in joined                                    # the CD collapses out of window
    assert "I_Dsat" in joined                                # and I_Dsat leaves spec (over the ceiling)
    assert r.extreme.yield_ < r.bad.yield_                   # worse than the moderate-defocus wafer


def test_rework_recovers_the_lost_dies():
    """Strip & re-expose at corrected focus lifts the yield back up (the rework loop closes)."""
    r = compute()
    assert r.reworked_yield > r.bad.yield_
    assert r.reworked.rework_log[-1].n_recovered > 0


def test_demo_is_deterministic():
    """Same seed → identical story (the roguelike-seed contract, at the demo level)."""
    a, b = compute(), compute()
    assert a.good.yield_ == b.good.yield_
    assert a.bad.yield_ == b.bad.yield_
    assert a.reworked_yield == b.reworked_yield


def test_fab_game_figure_builds():
    """Viz smoke test only (never a correctness check): skip cleanly without the extra."""
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import fab_game_figure

    fig = fab_game_figure(compute())
    assert len(fig.axes) == 4                                 # good map / bad map / NILS / reworked map
    plt.pyplot.close(fig)
