"""Device targets, slice 1 — "good is relative": the two gates, the re-grade bookkeeping, the seam.

The spine of ``docs/plans/device-targets.md``. Two **empirical gates** must hold before the mechanic
teaches anything (the plan §"the two empirical gates"), and they are asserted *first*:

1. **The target windows genuinely cross** — partially disjoint, not nested: a V_t that is low-power-good is
   logic-reject and vice-versa, with a real crossing region between. (Construction-level — pure spec maths.)
2. **The up-front declaration moves the recipe optimum** — the *same* physical wafer's best SKU flips with
   the recipe: a thin gate oxide strictly favours fast-logic, a thick one strictly favours low-power. The
   curves **cross** (the tie-proof form of "the optimum moved"). (Empirical — runs the real line.)

Then the re-grade **bookkeeping** (the disposition revenue closes; an irreversible assembly scrap stays
dead under every target) and the **seam** (declaring ``FAST_LOGIC`` reproduces the pre-targets game
bit-for-bit). All dollar amounts / window bands are flagged house numbers (ADR 0005 §5) — only the
*relationships* are asserted, never the magnitudes.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from fab_game.game import GameConfig, new_session, play
from fab_game.pipeline import run_line
from fab_game.recipe import DEFAULT_RECIPE
from fab_game.scoring import BIN_PRICES
from fab_game.spec import DEFAULT_SPECS
from fab_game.state import Die, Verdict, WaferState
from fab_game.targets import (
    FAST_LOGIC,
    LOW_POWER,
    MARKET_BINS,
    MOSFET_FLAVORS,
    disposition,
    grade_for,
    regrade,
)
from fab_game.variation import Variation


def _die(v_t: float, *, i_dsat_mA: float = 3.3, cd_nm: float = 167.0, nils: float = 4.6,
         **kw) -> Die:
    """A synthetic *finished* die with everything but ``V_t`` parked in **both** targets' windows.

    CD/NILS/I_Dsat sit in the intersection of the fast-logic and low-power windows, so ``V_t`` is provably
    the **sole** discriminator (the plan's anti-nesting guard, advisor). ``resolved`` so the functional
    gates pass; ``i_dsat`` is amps (the spec reads the mA property)."""
    return Die(site=(0, 0), radius_frac=0.0, V_t=v_t, cd_nm=cd_nm, nils=nils,
               i_dsat=i_dsat_mA * 1.0e-3, resolved=True, **kw)


def _passes(target, die: Die) -> bool:
    return target.specs.verdict(die, None).passed


# --------------------------------------------------------------------------- #
# Gate 1 — the windows genuinely CROSS (partially disjoint, not nested)
# --------------------------------------------------------------------------- #
def test_gate1_v_t_windows_cross_not_nested():
    fl, lp = FAST_LOGIC.specs.v_t, LOW_POWER.specs.v_t
    # A real crossing region exists ([0.60, 0.68]) — the overlap is non-empty …
    overlap_lo, overlap_hi = max(fl.lo, lp.lo), min(fl.hi, lp.hi)
    assert overlap_lo < overlap_hi, "the V_t windows must overlap (a shared crossing region)"
    # … and neither window nests the other: each has an EXCLUSIVE region (logic-only below, low-power-only
    # above). If logic ⊂ low-power the re-grade would be trivial and teach nothing (the plan's warning).
    assert fl.lo < lp.lo and fl.hi < lp.hi, "the windows must be partially disjoint, not nested"


def test_gate1_same_v_t_is_a_feature_for_one_target_and_a_fail_for_the_other():
    # A low V_t (0.50): fast-logic-GOOD (fast switching) but low-power-REJECT (too leaky for a mobile part).
    low = _die(0.50)
    assert _passes(FAST_LOGIC, low) and not _passes(LOW_POWER, low)
    # A high V_t (0.75): low-power-GOOD (low-leakage premium) but fast-logic-REJECT (too slow).
    high = _die(0.75)
    assert _passes(LOW_POWER, high) and not _passes(FAST_LOGIC, high)
    # The crossing region (0.65): good for BOTH (this is the overlap, not a contradiction).
    both = _die(0.65)
    assert _passes(FAST_LOGIC, both) and _passes(LOW_POWER, both)


# --------------------------------------------------------------------------- #
# Gate 2 — the declaration MOVES the optimum: the score curves cross
# --------------------------------------------------------------------------- #
def _oxide_wafer(minutes: float) -> WaferState:
    """A full wafer fabbed at a gate-oxide time (the physics is target-independent — grade it after)."""
    recipe = replace(DEFAULT_RECIPE, oxidation=replace(DEFAULT_RECIPE.oxidation, minutes=minutes))
    return run_line(recipe, seed=0, variation=Variation(), specs=FAST_LOGIC.specs, grid_n=7)


def test_gate2_thin_oxide_favours_fast_logic_thick_favours_low_power():
    # The SAME physical wafer is re-graded against each target (disposition, not re-fab). A thin oxide →
    # low V_t / high drive → fast-logic ships, low-power rejects (V_t under its floor). A thick oxide →
    # high V_t / starved drive → low-power ships, fast-logic rejects (V_t over its ceiling + I_Dsat under
    # its floor). The best SKU FLIPS with the recipe → the declaration moves the optimum.
    thin, thick = _oxide_wafer(18.0), _oxide_wafer(26.0)
    fl_thin, lp_thin = grade_for(thin, FAST_LOGIC), grade_for(thin, LOW_POWER)
    fl_thick, lp_thick = grade_for(thick, FAST_LOGIC), grade_for(thick, LOW_POWER)
    assert fl_thin.revenue > lp_thin.revenue, "a thin oxide must strictly favour fast-logic"
    assert lp_thick.revenue > fl_thick.revenue, "a thick oxide must strictly favour low-power"
    # The crossing is what proves the optimum moved (no reliance on a unique argmax): the winner is
    # different at the two ends, and each end's loser earns strictly less than its winner.
    assert lp_thin.revenue < fl_thin.revenue and fl_thick.revenue < lp_thick.revenue


# --------------------------------------------------------------------------- #
# The disposition headline — harvest the off-target tail (whole-wafer re-grade)
# --------------------------------------------------------------------------- #
def _deep_cut_wafer(slice_z: float = 0.85) -> WaferState:
    """A wafer cut deep down the boule: the Scheil drift walks V_t UP past fast-logic's ceiling."""
    recipe = replace(DEFAULT_RECIPE, czochralski=replace(DEFAULT_RECIPE.czochralski, slice_z=slice_z))
    return run_line(recipe, seed=0, variation=Variation(), specs=FAST_LOGIC.specs, grid_n=7)


def test_disposition_harvests_an_off_target_lot_to_the_sibling_flavor():
    wafer = _deep_cut_wafer()
    # As declared (fast-logic) the deep-cut lot is a near-total loss — V_t walked over the ceiling.
    assert grade_for(wafer, FAST_LOGIC).revenue == 0.0
    menu = disposition(wafer)
    assert tuple(g.target.name for g in menu)[0] == "low-power"   # best SKU first
    assert menu[0].revenue > 0.0 and menu[0].yield_ > 0.5         # the tail is harvested, not scrapped
    # The menu carries every flavor (whole-wafer re-grade, not die-cherry-picking across products).
    assert {g.target.name for g in menu} == {t.name for t in MOSFET_FLAVORS}


def test_disposition_keeps_an_on_target_lot_on_its_declared_flavor():
    # A shallow cut stays in the fast-logic window → fast-logic is (at least tied for) the best SKU.
    wafer = run_line(DEFAULT_RECIPE, seed=0, variation=Variation(), specs=FAST_LOGIC.specs, grid_n=7)
    menu = disposition(wafer)
    fl = next(g for g in menu if g.target.name == "fast-logic")
    assert fl.revenue == max(g.revenue for g in menu)


# --------------------------------------------------------------------------- #
# Re-grade bookkeeping — revenue closes; an irreversible assembly scrap stays dead
# --------------------------------------------------------------------------- #
def test_regrade_bookkeeping_closes():
    wafer = _deep_cut_wafer()
    for target in MOSFET_FLAVORS:
        sc = grade_for(wafer, target, wafer_cost=80.0)
        # revenue = Σ price[bin]·count over the shipped dies; profit = revenue − the (sunk) wafer cost.
        assert sc.revenue == sum(target.prices[b] * n for b, n in sc.bin_counts.items())
        assert sc.profit == sc.revenue - 80.0
        # Every counted die is a shipped (passed) die of the re-graded wafer.
        rg = regrade(wafer, target)
        assert sc.n_good == sum(d.verdict.passed for d in rg.dies if d.verdict is not None)


def test_regrade_preserves_the_irreversible_assembly_scrap():
    # A die whose parameters sit inside low-power's windows but that was physically scrapped in assembly
    # (assembled=False, a cracked die) must stay dead under every target — re-grading cannot un-crack it.
    scrapped = _die(0.70, i_dsat_mA=2.8, assembled=False,
                    verdict=Verdict(False, ("assembly scrap",)))
    w = WaferState(wafer_id="T", channel_N_A=1e17, dies=(scrapped,))
    rg = regrade(w, LOW_POWER)
    assert rg.dies[0].verdict.failed and grade_for(w, LOW_POWER).revenue == 0.0
    # The CONTRAST: the same parameters on a die that DID reach assembly (survived, or front-end-failed the
    # declared target so it never drew a survival — assembled None) ship under low-power (exact at the
    # default lossless back end). This is the harvest path the assembly scrap is correctly excluded from.
    survived = replace(scrapped, assembled=True, verdict=Verdict(True, ()))
    never_assembled = replace(scrapped, assembled=None, verdict=Verdict(False, ("V_t 0.70 > 0.68 (high)",)))
    for d in (survived, never_assembled):
        wd = WaferState(wafer_id="T", channel_N_A=1e17, dies=(d,))
        assert grade_for(wd, LOW_POWER).revenue > 0.0


def test_regrade_preserves_a_functional_kill_under_every_target():
    # A killer particle defect is a functional kill (no working transistor) — re-grading cannot revive it,
    # whatever the target's windows (it short-circuits before the parametrics in SpecSet.verdict). LP-good
    # params, but a dead die.
    killed = _die(0.70, i_dsat_mA=2.8, killed_by_defect=True,
                  verdict=Verdict(False, ("killer particle defect",)))
    w = WaferState(wafer_id="T", channel_N_A=1e17, dies=(killed,))
    rg = regrade(w, LOW_POWER)
    assert rg.dies[0].verdict.failed and grade_for(w, LOW_POWER).revenue == 0.0


# --------------------------------------------------------------------------- #
# The seam — declaring FAST_LOGIC reproduces the pre-targets game bit-for-bit
# --------------------------------------------------------------------------- #
def test_seam_fast_logic_is_value_equal_to_todays_specs_and_prices():
    # Frozen dataclasses / dicts compare by value, so value-equality GUARANTEES identical verdicts, bins,
    # and revenue — the tightest possible seam proof (advisor).
    assert FAST_LOGIC.specs == replace(DEFAULT_SPECS, speed_bins=MARKET_BINS)
    assert FAST_LOGIC.prices == BIN_PRICES


def test_seam_default_gameconfig_target_is_fast_logic():
    cfg = GameConfig()
    assert cfg.target is FAST_LOGIC
    assert cfg.specs == replace(DEFAULT_SPECS, speed_bins=MARKET_BINS)
    assert cfg.prices == BIN_PRICES


def test_seam_a_full_play_is_unchanged_by_declaring_fast_logic_explicitly():
    # The whole session path (run_line → score_wafer → budget) is byte-for-byte identical whether the
    # target is defaulted or declared explicitly — the GameConfig refactor changed nothing for fast-logic.
    decisions = [DEFAULT_RECIPE, DEFAULT_RECIPE, DEFAULT_RECIPE]
    default = play(new_session(GameConfig(n_wafers=4, grid_n=3), seed=1), decisions)
    explicit = play(new_session(GameConfig(n_wafers=4, grid_n=3, target=FAST_LOGIC), seed=1), decisions)
    assert default.budget == explicit.budget
    assert default.score == explicit.score
    assert [r.scorecard.revenue for r in default.history] == [r.scorecard.revenue for r in explicit.history]


def test_declaring_low_power_changes_the_session_score():
    # The flip side of the seam: declaring a DIFFERENT target genuinely re-scores the run (a fast-logic
    # recipe down the boule scores differently as low-power) — declaration is strategy, not a relabel.
    decisions = [DEFAULT_RECIPE] * 5
    fl = play(new_session(GameConfig(n_wafers=6, z_max=0.9, grid_n=3, target=FAST_LOGIC), seed=0), decisions)
    lp = play(new_session(GameConfig(n_wafers=6, z_max=0.9, grid_n=3, target=LOW_POWER), seed=0), decisions)
    assert fl.score != lp.score
