"""Integration test for the F8-S4 grading demo — the second F4 clause, measured on a wafer.

``test_cmp_knob.py`` already pins the CMP step itself (the seam, the refusal, the radial removal chain,
the short's closed form, and S2's "grades spread outward on identical transistors"), and none of that is
re-asserted here. This test guards what only *this* demo can break:

  * **the clause, as an ordering of three measured yields** — the drive-current policy loses parts, F4's
    true currency loses none (it *rescues* the tail), and the polished wire loses more than either;
  * **the composition** — neither the transistor tail nor the polisher costs a part on its own at the
    spread shown, so the loss cannot be attributed to either alone;
  * **the direction** — every part lost was a below-nominal transistor out past the first-lost radius, and
    the polisher reverses the wafer's speed gradient rather than adding to it;
  * **the anchor**, which ``DelayBins.from_speed_bins`` warns is exactly where a collapse can be
    manufactured: the ladder is G6's, anchored on the nominal part, and at the clear-everywhere time that
    part *is* this wafer's centre die;
  * **the sweep's shortcut is exact** — the curve is computed from each die's recorded ``τ_gate``/``τ_wire``
    at a polished thickness rather than by re-running the line, so it is pinned against the real pipeline;
  * **the figure's words**, which the fast lane otherwise cannot check.

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
from dataclasses import replace

import pytest

from fab_game import demo_cmp_grading, demo_packaging
from fab_game.demo_cmp_grading import (
    GRID_N, LOOSE_SIGMA, S_HOUSE, S_SHOWN, SPEED_BINS, TIGHT_SIGMA, compute,
)
from fab_game.pipeline import run_line, wafer_yield
from fab_game.spec import DEFAULT_SPECS
from fab_game.variation import Variation


@pytest.fixture(scope="module")
def r():
    return compute()


def test_the_grade_ladder_and_the_two_process_sigmas_are_g6s_by_value():
    """No grading number is invented here: the market ladder and both CD σ's are demo_packaging's own."""
    assert SPEED_BINS == demo_packaging.SPEED_BINS
    assert (TIGHT_SIGMA, LOOSE_SIGMA) == (demo_packaging.TIGHT_SIGMA, demo_packaging.LOOSE_SIGMA)


def test_the_anchor_is_the_nominal_part_and_at_the_clear_time_that_is_the_centre_die(r):
    """The one place a collapse could be manufactured (DelayBins.from_speed_bins' own warning): here the
    two candidate anchors are the SAME part, because the centre is the slowest site and exactly clears."""
    assert r.anchor_is_the_polished_centre is True
    # …and the ladder is the market promise mapped through the old premise, not hand-picked ps edges.
    typical = next(b for b in r.ladder.bins if b.label == "typical")
    speed_typical = next(b for b in SPEED_BINS.bins if b.label == "typical")
    assert typical.hi_ps == pytest.approx(r.tau_nom_ps * r.i_dsat_nom_mA / speed_typical.lo_mA)
    assert typical.lo_ps == pytest.approx(r.tau_nom_ps * r.i_dsat_nom_mA / speed_typical.hi_mA)


def test_it_is_one_wafer_of_silicon_graded_three_ways(r):
    """The maps and the bars are the same dies — CMP consumes no randomness, so the transistors are
    identical across the three runs and the I_Dsat histogram cannot explain the grade differences."""
    def drives(w):
        return [d.i_dsat for d in sorted(w.dies, key=lambda d: d.site)]
    assert drives(r.wafer_idsat) == drives(r.wafer_f8) == drives(r.wafer_f4)
    assert r.hist_idsat != r.hist_f8                                   # …and yet they grade differently


def test_f4s_true_currency_rescues_the_slow_tail_and_the_polisher_takes_it_back(r):
    """The clause, as three measured yields: F4's common-mode wire can only pull a die TOWARD typical (it
    rescues both drive-current bin-outs); the per-die wire adds a strictly positive, uncompensated term
    and pushes parts off the bottom of the ladder."""
    assert r.hist_idsat["reject"] > 0                                  # the old policy loses parts
    assert r.hist_f4["reject"] == 0                                    # F4 rescues every one of them
    assert r.hist_f8["reject"] > r.hist_idsat["reject"]                # the polisher loses MORE than either
    assert r.yield_f4 == 1.0 > r.yield_idsat > r.yield_f8              # and a bin-out IS a yield loss here


def test_neither_mechanism_alone_loses_a_part(r):
    """The F4-S4 shape one slice on: the transistor tail alone loses nothing (F4 rescues it), the polisher
    alone loses nothing (the tight process is flat at this spread), and together they lose parts."""
    i_shown = r.s_sweep.index(S_SHOWN)
    assert r.rejects_loose_no_cmp == r.rejects_tight_no_cmp == 0       # no polisher: nothing lost
    assert r.rejects_tight[i_shown] == 0                               # tight transistors: nothing lost
    assert r.rejects_loose[i_shown] == r.n_lost > 0                    # both: parts lost


def test_the_polisher_never_rejects_a_fast_die_it_withdraws_a_rescue(r):
    """Every part lost was already below the nominal transistor AND out past the first-lost radius — and
    neither condition selects them on its own (both counts are far larger than the loss)."""
    lost = [d for d in r.wafer_f8.dies if d.bin == "reject"]
    assert len(lost) == r.n_lost
    for d in lost:
        assert d.i_dsat_mA < r.i_dsat_nom_mA                           # never a fast die
        assert d.radius_frac >= r.first_reject_radius                  # always out at the rim
    assert r.n_below_nominal > r.n_lost and r.n_outside_first_reject_radius > r.n_lost


def test_the_polisher_reverses_the_wafers_speed_gradient(r):
    """Not extra spread on top of the transistor's: the transistor's own radial trend leaves the rim
    marginally FASTER, so the unpolished wafer is faster outward; polished, the sign flips."""
    assert r.corr_r_idsat > 0.0                                        # the rim's transistors are faster
    assert r.corr_r_tau_f4 < 0.0 < r.corr_r_tau_f8                     # …and the delay gradient inverts
    assert abs(r.corr_r_tau_f8) > abs(r.corr_r_tau_f4)


def test_the_threshold_is_reported_as_a_house_number_not_hidden(r):
    """At the knob's own default spread the polisher still costs NO part — the finding is the sign, and
    where it starts to bite rides the flagged radial amplitude (so the demo draws the whole curve)."""
    i_house = min(range(len(r.s_sweep)), key=lambda i: abs(r.s_sweep[i] - S_HOUSE))
    assert r.rejects_loose[i_house] == 0
    assert r.first_loss_s_loose > S_HOUSE                              # the default is inside the safe side
    assert r.first_loss_s_tight > r.first_loss_s_loose                 # a tighter process pushes it further
    assert r.rejects_loose[0] == r.rejects_tight[0] == 0               # s = 0: a uniform polish costs nothing


def test_the_sweep_is_monotone_in_the_polish_spread(r):
    """A wider spread thins the rim further, so it can only cost more parts — never fewer."""
    for tag in (r.rejects_loose, r.rejects_tight):
        assert all(b >= a for a, b in zip(tag, tag[1:])), tag


def test_the_sweeps_closed_form_equals_the_real_pipeline_at_the_shown_spread(r):
    """The curve re-reads each die's recorded τ_gate/τ_wire at a polished thickness instead of re-running
    ~60 wafers. That is legitimate only because τ_wire is linear in R and C never reads H (F4's cited
    geometry-invariance) — pinned here against the pipeline itself, which is what the maps are drawn from."""
    assert r.rejects_loose[r.s_sweep.index(S_SHOWN)] == r.n_lost

    # …and independently at a second spread, through the real line rather than the demo's own run.
    s = 0.24
    specs = replace(DEFAULT_SPECS, speed_bins=SPEED_BINS, delay_bins=r.ladder)
    w = run_line(demo_cmp_grading._recipe(demo_cmp_grading._clear_time(s), s), seed=demo_cmp_grading.SEED,
                 variation=Variation(cd_sigma_nm=LOOSE_SIGMA), specs=specs, grid_n=GRID_N)
    assert r.rejects_loose[r.s_sweep.index(s)] == sum(1 for d in w.dies if d.bin == "reject")
    assert wafer_yield(w) < r.yield_f8


def test_the_trail_names_the_currency_that_graded_not_the_transistor(r):
    """The live finding this slice fixed: `diagnose` hardcoded 'I_Dsat too low' for every bin-out, which
    under delay binning credits the transistor with a failure the WIRE caused — the inverse of the thesis."""
    assert "τ_total" in r.story_trail
    assert "I_Dsat too low" not in r.story_trail
    assert "CMP: over-polish" in r.story_trail                         # the cause is named above it


def test_the_figure_says_what_is_structural_and_what_is_a_house_number(r):
    """The words test — the golden pages confirm the prose did not CHANGE, never that it is still TRUE."""
    pytest.importorskip("matplotlib")
    from fab_game.plots import cmp_grading_figure

    fig = cmp_grading_figure(r)
    text = fig._suptitle.get_text()
    assert "SIGN IS STRUCTURAL" in text and "HOUSE NUMBER" in text
    assert "anchored on the nominal part" in text


def test_figure_builds(r):
    pytest.importorskip("matplotlib")
    from fab_game.plots import cmp_grading_figure

    assert cmp_grading_figure(r) is not None
