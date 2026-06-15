"""Device targets, slice 3 — the high-resistivity NATIVE part: the SUBSTRATE-resistivity axis.

The slice-3 spine of ``docs/plans/device-targets.md``: ``BV``'s *other* knob — the **substrate doping**
itself (``BV ∝ N_B^(−3/4)``, set at growth) — for a genuinely high-breakdown part, where slice 2 turned
the junction **depth** ``x_j`` on the fixed substrate. **Zero new physics** (Option B, advisor): the plan's
two empirical gates are re-proven on the **substrate-resistivity axis**, asserted *first*:

1. **The windows genuinely cross — on BOTH axes at once.** THE structural finding (advisor, mirroring slice
   2's "x_j decouples BV from V_t"): in this single-doping model the substrate doping moves ``BV`` and
   ``V_t`` with **opposite signs, coupled** (lighter substrate → higher BV, *lower* V_t together; ``I_Dsat``
   is ``N_A``-independent, so they are the *only* axes that move). So a light substrate gives a high ``BV``
   **and** a near-zero ``V_t`` — a logic **reject** whose low V_t is the **feature** of the native part. The
   V_t windows are **disjoint** (logic vs native) and the native ``BV`` floor is **above the low-R plane-
   parallel ceiling** → unreachable on the logic substrate by *any* drive-in. Two declared runs show the
   crossing as **mutual rejection** across substrates.
2. **The declaration moves the recipe optimum — on the growth substrate doping.** Declaring fast-logic →
   the best ``N_seed`` is **heavy** (low-R); declaring high-res → **light** (high-res). The curves cross
   (the tie-proof form of "the optimum moved").

Then the **substrate-class guard** (the substrate is committed at growth, so disposition is within one
class — a low-R wafer is *not* a high-res part) and the **seam** (adding the native part + the ``substrate``
field leaves the slice-1/2 low-R family byte-for-byte). All bands/prices are flagged house numbers
(ADR 0005 §5) — only the *relationships* are asserted, never the magnitudes.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from chip.breakdown import plane_parallel_breakdown
from fab_game.pipeline import run_line
from fab_game.recipe import DEFAULT_RECIPE
from fab_game.spec import DEFAULT_SPECS
from fab_game.state import Die, WaferState
from fab_game.targets import (
    FAST_LOGIC,
    HIGH_RES,
    HIGH_RES_BV_FLOOR_V,
    HIGH_RES_FAMILY,
    HV_IO,
    LOW_POWER,
    MOSFET_FLAVORS,
    disposition,
    grade_for,
    regrade,
)
from fab_game.variation import Variation

# The substrate-resistivity lever (the boule seed-end doping). The low-R (~1e17) logic substrate vs a light
# high-res (~1e16) substrate: lighter → higher BV, lower (native) V_t. FLAGGED recipe corners.
LOW_R_N_SEED = 1.0e17     # the incumbent low-resistivity logic substrate (the recipe default)
HIGH_RES_N_SEED = 1.0e16  # a ~10× lighter (higher-resistivity) substrate → high BV + native low V_t


def _wafer_at(n_seed: float) -> WaferState:
    """A full wafer grown at substrate seed-end doping ``n_seed`` — the only knob changed (grade it after).

    The physics is target-independent (re-graded against each target downstream); ``Variation()`` + grid_n=7
    match the slice-1/2 gate harness. ``N_A`` enters only ``V_t`` and ``BV`` (``I_Dsat`` is ``N_A``-
    independent), so a lighter substrate is the clean two-axis (BV↑ / V_t↓) signal."""
    recipe = replace(DEFAULT_RECIPE, czochralski=replace(DEFAULT_RECIPE.czochralski, N_seed=n_seed))
    return run_line(recipe, seed=0, variation=Variation(), specs=FAST_LOGIC.specs, grid_n=7)


def _mean(field: str, w: WaferState) -> float:
    vals = [getattr(d, field) for d in w.dies if getattr(d, field) is not None]
    return sum(vals) / len(vals)


# --------------------------------------------------------------------------- #
# Gate 1 — the windows cross on BOTH axes; the BV floor is unreachable on the low-R substrate
# --------------------------------------------------------------------------- #
def test_gate1_native_v_t_window_is_disjoint_below_the_logic_family():
    # The native part's V_t window sits BELOW — and disjoint from — every low-R logic flavor's window: a low
    # V_t that is a logic reject is the high-res FEATURE (not nested, not overlapping — a clean inversion).
    hr = HIGH_RES.specs.v_t
    for flavor in MOSFET_FLAVORS:
        assert hr.hi < flavor.specs.v_t.lo, f"high-res V_t must sit disjoint below {flavor.name}"


def test_gate1_bv_floor_is_unreachable_on_the_low_R_substrate():
    # THE substrate gate (not a tunable drive-in one): the native BV floor sits ABOVE the plane-parallel
    # ceiling of the low-R substrate, so NO junction depth can clear it on a logic wafer (BV ≤ BV_pp always),
    # while the light high-res substrate has a far higher ceiling. A hard, substrate-committed gate.
    assert plane_parallel_breakdown(LOW_R_N_SEED) < HIGH_RES_BV_FLOOR_V, \
        "the BV floor must exceed the low-R plane-parallel ceiling (unreachable by any drive-in)"
    assert HIGH_RES_BV_FLOOR_V < plane_parallel_breakdown(HIGH_RES_N_SEED), \
        "the light substrate's ceiling must clear the floor (the part is reachable on high-res)"
    # Only the native part carries the floor — the logic flavors leave BV open (the slice-2 seam holds).
    assert HIGH_RES.specs.bv.lo == HIGH_RES_BV_FLOOR_V and HIGH_RES.specs.bv.optional
    for flavor in (FAST_LOGIC, LOW_POWER):
        assert flavor.specs.bv.lo is None


def test_gate1_lighter_substrate_raises_bv_and_craters_v_t_together():
    # THE finding (advisor): the substrate doping moves BV and V_t with OPPOSITE signs, coupled — the reason
    # resistivity cannot give slice 2's high-V_t hv-io its BV (x_j was slice 2's lever precisely because it
    # raises BV WITHOUT touching V_t). I_Dsat is N_A-independent, so V_t and BV are the only axes that move.
    low_r, high_res = _wafer_at(LOW_R_N_SEED), _wafer_at(HIGH_RES_N_SEED)
    assert _mean("bv_V", high_res) > _mean("bv_V", low_r)      # lighter substrate → HIGHER breakdown
    assert _mean("V_t", high_res) < _mean("V_t", low_r)        # … and LOWER (native) threshold — coupled
    assert _mean("i_dsat_mA", high_res) == pytest.approx(_mean("i_dsat_mA", low_r), rel=1e-9)  # drive unchanged


def test_gate1_crossing_is_mutual_rejection_across_substrates():
    # The crossing on the line (two DECLARED runs — the substrate is committed at growth): the low-R wafer is
    # logic-good / high-res-reject, the high-res wafer is high-res-good / logic-reject. Mutual rejection — the
    # strongest form of "the windows cross, not nested".
    low_r, high_res = _wafer_at(LOW_R_N_SEED), _wafer_at(HIGH_RES_N_SEED)
    assert grade_for(low_r, FAST_LOGIC).revenue > 0.0 and grade_for(low_r, HIGH_RES).revenue == 0.0
    assert grade_for(high_res, HIGH_RES).revenue > 0.0 and grade_for(high_res, FAST_LOGIC).revenue == 0.0
    # The high-res wafer's actual breakdown clears the floor (the BV gate is met, not just the ceiling).
    assert _mean("bv_V", high_res) > HIGH_RES_BV_FLOOR_V


# --------------------------------------------------------------------------- #
# Gate 2 — declaring high-res moves the optimum onto the growth substrate doping
# --------------------------------------------------------------------------- #
def test_gate2_declaration_moves_the_growth_substrate_optimum():
    # The SAME line, two declared targets: fast-logic wants the HEAVY (low-R) substrate, high-res wants the
    # LIGHT one. The winner flips between the substrate ends → the declaration moves the optimum (the
    # tie-proof crossing form: each end's winner strictly out-earns the other target there).
    low_r, high_res = _wafer_at(LOW_R_N_SEED), _wafer_at(HIGH_RES_N_SEED)
    # Heavy substrate: fast-logic strictly out-earns high-res.
    assert grade_for(low_r, FAST_LOGIC).revenue > grade_for(low_r, HIGH_RES).revenue
    # Light substrate: high-res strictly out-earns fast-logic.
    assert grade_for(high_res, HIGH_RES).revenue > grade_for(high_res, FAST_LOGIC).revenue


# --------------------------------------------------------------------------- #
# The substrate-class guard — the substrate is committed at growth (no cross-substrate disposition)
# --------------------------------------------------------------------------- #
def test_disposition_refuses_to_mix_substrate_classes():
    # A disposition menu mixing the low-R family and the high-res part is a misconfiguration — you cannot
    # re-grade a finished wafer across substrate classes (the boule is committed at growth). It raises (like
    # the recipe's two-G / over-and-under-etch guards), naming the substrate commit.
    wafer = _wafer_at(LOW_R_N_SEED)
    with pytest.raises(ValueError, match="substrate"):
        disposition(wafer, MOSFET_FLAVORS + HIGH_RES_FAMILY)
    # Within ONE class disposition still works (the default low-R menu, and the high-res menu of one).
    assert disposition(wafer)[0].target.substrate == "low-res"
    assert disposition(_wafer_at(HIGH_RES_N_SEED), HIGH_RES_FAMILY)[0].target.name == "high-res"


def test_physics_enforces_the_substrate_boundary_cross_grade_yields_nothing():
    # Even setting the guard aside, the physics makes cross-substrate re-grade worthless: a low-R wafer
    # re-graded to high-res ships ~0 (V_t too high AND BV unreachable) and a high-res wafer re-graded to a
    # logic flavor ships ~0 (native V_t too low) — so high-res is genuinely a DECLARED RUN, not a salvage.
    low_r, high_res = _wafer_at(LOW_R_N_SEED), _wafer_at(HIGH_RES_N_SEED)
    assert grade_for(low_r, HIGH_RES).revenue == 0.0
    assert all(grade_for(high_res, f).revenue == 0.0 for f in MOSFET_FLAVORS)


# --------------------------------------------------------------------------- #
# Bookkeeping — the high-res revenue closes (the native part is fully wired)
# --------------------------------------------------------------------------- #
def test_high_res_regrade_bookkeeping_closes():
    wafer = _wafer_at(HIGH_RES_N_SEED)
    sc = grade_for(wafer, HIGH_RES, wafer_cost=80.0)
    assert sc.revenue == sum(HIGH_RES.prices[b] * n for b, n in sc.bin_counts.items())
    assert sc.profit == sc.revenue - 80.0
    rg = regrade(wafer, HIGH_RES)
    assert sc.n_good == sum(d.verdict.passed for d in rg.dies if d.verdict is not None)


# --------------------------------------------------------------------------- #
# The seam — the native part + the substrate field leave the slice-1/2 low-R family unchanged
# --------------------------------------------------------------------------- #
def test_seam_low_r_family_is_unchanged_and_tagged():
    # MOSFET_FLAVORS is still exactly the three low-R flavors (the native part is NOT a disposition sibling),
    # and they all carry substrate="low-res" (so the default disposition menu is single-class).
    assert MOSFET_FLAVORS == (FAST_LOGIC, LOW_POWER, HV_IO)
    assert all(f.substrate == "low-res" for f in MOSFET_FLAVORS)
    assert HIGH_RES not in MOSFET_FLAVORS and HIGH_RES.substrate == "high-res"


def test_seam_a_negative_v_t_window_scores_correctly():
    # The native window dips below 0 (a near-zero / slightly-negative native V_t is in spec). The scorer
    # must handle a negative V_t and a negative window bound: a V_t inside [−0.15, 0.35] passes, one below
    # the floor fails (nothing assumes V_t > 0). A high BV (over the floor) keeps the part shippable.
    in_band = Die(site=(0, 0), radius_frac=0.0, V_t=-0.05, i_dsat=3.3e-3, cd_nm=167.0, nils=4.6,
                  resolved=True, bv_V=HIGH_RES_BV_FLOOR_V + 1.0)
    assert HIGH_RES.specs.verdict(in_band, None).passed
    too_low = replace(in_band, V_t=-0.30)
    v = HIGH_RES.specs.verdict(too_low, None)
    assert v.failed and any("V_t" in r for r in v.reasons)
