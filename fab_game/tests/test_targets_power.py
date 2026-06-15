"""Device targets, slice 5 — the power-rectifier family: the LIFETIME axis (short τ = fast switching).

The richest, last inversion of ``docs/plans/device-targets.md``. G4b's deep-level metals destroy
minority-carrier lifetime ``τ`` → junction **leakage** ``J_gen ∝ 1/τ`` (the logic killer); the power
rectifier reads the **same ``τ`` in the opposite direction** — reverse recovery ``t_rr ∝ τ``
(:mod:`chip.reverse_recovery`), so a **short** ``τ`` (a leaky logic reject) is a **fast** rectifier. The
lifetime killer is the feature. **One cited output** (``t_rr``); the inversion itself adds no new lifetime
physics (``τ`` is the G4b reading). The plan's two empirical gates are re-proven on the **lifetime axis**,
asserted *first*:

1. **The windows cross — on the lifetime axis (mutual rejection, same substrate).** On the *same* high-res
   substrate, a clean feed is native-MOSFET-good / rectifier-reject (slow ``t_rr``) and a metal-laden feed is
   rectifier-good / native-reject (leaky). The metals are Na-/dopant-clean → they move ``τ`` (→ leakage,
   → ``t_rr``) **without** touching ``V_t``/``BV``, so it is a clean single-axis cross. And — the leakage
   inversion made literal — the *same* leakage that fails the logic part is **open** for the rectifier.
2. **The declaration moves the optimum — on the purification feed.** Declaring the native part wants a clean
   feed; declaring the rectifier wants a metal (lifetime-killed) feed. The best SKU flips → the optimum moved.

Then the **family guard** (the rectifier is a different DEVICE FAMILY — committed at the mask, never a
disposition of a MOSFET wafer, even though it *shares* the light high-res substrate), the **substrate/BV
commit** (the rectifier needs the light boule for blocking voltage — a short-``τ`` low-R wafer is still a
rectifier-reject on ``BV``), the **REQUIRED ``t_rr``/``BV`` guards**, the **bookkeeping**, and the **seam**
(the open ``t_rr`` window leaves the MOSFET targets byte-for-byte). All bands/prices are flagged house
numbers (ADR 0005 §5) — only the *relationships* are asserted, never the magnitudes.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from fab_game.pipeline import run_line
from fab_game.recipe import DEFAULT_RECIPE, PurificationKnobs
from fab_game.state import Die, WaferState
from fab_game.targets import (
    FAST_LOGIC,
    HIGH_RES,
    HIGH_RES_BV_FLOOR_V,
    HIGH_RES_FAMILY,
    MOSFET_FLAVORS,
    POWER_FAMILY,
    POWER_RECTIFIER,
    POWER_T_RR_CEILING_NS,
    disposition,
    grade_for,
    regrade,
)
from fab_game.variation import Variation

# The two declared-run levers: the substrate (the light boule for BV) and the feed (the lifetime killer).
LOW_R_N_SEED = 1.0e17       # the incumbent low-resistivity logic substrate (BV too low for a power part)
HIGH_RES_N_SEED = 1.0e16    # the light substrate a power part needs (BV above the floor)
CLEAN_FEED = "clean"        # a clean feed → long τ → slow rectifier (native-MOSFET-good)
METAL_FEED = "metal"        # a lifetime-killed feed → short τ → fast rectifier (logic leakage reject)


def _wafer(n_seed: float, grade: str) -> WaferState:
    """A full wafer grown at substrate ``n_seed`` with feed ``grade`` — the two declared-run levers.

    The substrate sets ``BV``; the feed metals set ``τ`` (→ leakage → ``t_rr``) and are Na-/dopant-clean, so
    ``V_t``/``BV`` do not move with the feed — a clean lifetime axis. ``Variation()`` + grid_n=7 mirror the
    slice-1/2/3 gate harness (defect_density defaults to 0 → the contamination story is wafer-uniform)."""
    recipe = replace(
        DEFAULT_RECIPE,
        czochralski=replace(DEFAULT_RECIPE.czochralski, N_seed=n_seed),
        purification=PurificationKnobs(grade=grade, zone_passes=1),
    )
    return run_line(recipe, seed=0, variation=Variation(), specs=FAST_LOGIC.specs, grid_n=7)


def _mean(field: str, w: WaferState) -> float:
    vals = [getattr(d, field) for d in w.dies if getattr(d, field) is not None]
    return sum(vals) / len(vals)


def _power_die(**kw) -> Die:
    """A synthetic finished die parked so the rectifier's REQUIRED axes (t_rr, BV) are the only discriminators.

    BV over the floor, t_rr under the ceiling, and the MOSFET parametrics set to *native-window* values so a
    comparison against the high-res native MOSFET isolates whichever axis the test moves."""
    base = dict(site=(0, 0), radius_frac=0.0, V_t=0.0, i_dsat=3.3e-3, cd_nm=167.0, nils=4.6, resolved=True,
                bv_V=HIGH_RES_BV_FLOOR_V + 2.0, t_rr=100.0e-9)
    base.update(kw)
    return Die(**base)


# --------------------------------------------------------------------------- #
# Gate 1 — the windows cross on the LIFETIME axis (mutual rejection, same substrate)
# --------------------------------------------------------------------------- #
def test_gate1_t_rr_tracks_lifetime_clean_is_slow_metal_is_fast():
    # THE slice-5 reading on the line: a clean feed → long τ → t_rr ABOVE the ceiling (rectifier-reject); a
    # metal feed → short τ → t_rr BELOW it (rectifier-good). The lifetime killer makes the fast rectifier.
    clean, metal = _wafer(HIGH_RES_N_SEED, CLEAN_FEED), _wafer(HIGH_RES_N_SEED, METAL_FEED)
    assert _mean("t_rr_ns", clean) > POWER_T_RR_CEILING_NS      # clean → slow → rejected
    assert _mean("t_rr_ns", metal) < POWER_T_RR_CEILING_NS      # metal → fast → accepted
    # The feed moves τ/t_rr/leakage but NOT V_t or BV (the metals are Na-/dopant-clean) — a clean single axis.
    assert _mean("V_t", clean) == pytest.approx(_mean("V_t", metal), rel=1e-9)
    assert _mean("bv_V", clean) == pytest.approx(_mean("bv_V", metal), rel=1e-9)
    assert _mean("t_rr_ns", metal) < _mean("t_rr_ns", clean)    # … only the lifetime axis moved


def test_gate1_crossing_is_mutual_rejection_on_the_feed_axis():
    # The crossing on the line (same high-res substrate, two declared runs): the CLEAN wafer is
    # native-MOSFET-good / rectifier-reject, the METAL wafer is rectifier-good / native-reject. Mutual
    # rejection on the lifetime axis — the strongest form of "the windows cross, not nested".
    clean, metal = _wafer(HIGH_RES_N_SEED, CLEAN_FEED), _wafer(HIGH_RES_N_SEED, METAL_FEED)
    assert grade_for(clean, HIGH_RES).revenue > 0.0 and grade_for(clean, POWER_RECTIFIER).revenue == 0.0
    assert grade_for(metal, POWER_RECTIFIER).revenue > 0.0 and grade_for(metal, HIGH_RES).revenue == 0.0


def test_gate1_the_same_leakage_fails_logic_but_is_open_for_the_rectifier():
    # The leakage inversion made literal (the focused unit): a die with leakage OVER the logic ceiling but an
    # in-window t_rr/BV SHIPS the rectifier (leakage is not its axis) and FAILS the native MOSFET on leakage
    # ALONE — the same physical quantity, opposite verdicts.
    leaky = _power_die(j_leak=50.0e-9)                          # 50 nA/cm² — over the logic 10 ceiling
    assert POWER_RECTIFIER.specs.verdict(leaky, None).passed    # rectifier: leakage open → ships
    v = HIGH_RES.specs.verdict(leaky, None)
    assert v.failed and len(v.reasons) == 1 and "leak" in v.reasons[0].lower()   # native: leakage the SOLE fail


def test_gate1_a_die_fails_the_rectifier_on_t_rr_alone():
    # The defining axis in isolation: a die inside every other rectifier gate but with a SLOW t_rr (over the
    # ceiling) fails the rectifier on t_rr alone — the switching-speed acceptance the slice adds.
    slow = _power_die(t_rr=1.0e-3)                              # 1e6 ns — a clean-feed-grade slow diode
    v = POWER_RECTIFIER.specs.verdict(slow, None)
    assert v.failed and len(v.reasons) == 1 and "t_rr" in v.reasons[0]
    # A fast-enough recovery ships the same die.
    assert POWER_RECTIFIER.specs.verdict(_power_die(t_rr=100.0e-9), None).passed


def test_gate1_rectifier_needs_the_light_substrate_too_short_tau_is_not_enough():
    # "Good is relative" needs BOTH declared-run commits: a low-R wafer with the SAME metal feed (a short τ /
    # fast t_rr) is STILL a rectifier-reject — its BV (~5 V on the heavy substrate) is under the floor. The
    # lifetime axis is the cross, but the substrate/BV commit is the gate (the part needs the light boule).
    low_r_metal = _wafer(LOW_R_N_SEED, METAL_FEED)
    assert _mean("t_rr_ns", low_r_metal) < POWER_T_RR_CEILING_NS    # the lifetime is right (fast)…
    assert _mean("bv_V", low_r_metal) < HIGH_RES_BV_FLOOR_V         # … but BV is unreachable on the heavy boule
    assert grade_for(low_r_metal, POWER_RECTIFIER).revenue == 0.0   # → still rejected (the substrate commit)


# --------------------------------------------------------------------------- #
# Gate 2 — declaring the rectifier moves the purification (feed) optimum
# --------------------------------------------------------------------------- #
def test_gate2_declaration_moves_the_feed_optimum():
    # The SAME high-res line, two declared targets: the native MOSFET wants the CLEAN feed, the rectifier wants
    # the METAL (lifetime-killed) one. The winner flips between the feed ends → the declaration moves the
    # optimum (the tie-proof crossing form: each end's winner strictly out-earns the other target there).
    clean, metal = _wafer(HIGH_RES_N_SEED, CLEAN_FEED), _wafer(HIGH_RES_N_SEED, METAL_FEED)
    assert grade_for(clean, HIGH_RES).revenue > grade_for(clean, POWER_RECTIFIER).revenue   # clean → native
    assert grade_for(metal, POWER_RECTIFIER).revenue > grade_for(metal, HIGH_RES).revenue   # metal → rectifier


# --------------------------------------------------------------------------- #
# The family guard — the rectifier is a different DEVICE FAMILY (committed at the mask)
# --------------------------------------------------------------------------- #
def test_disposition_refuses_to_mix_device_families():
    # A menu mixing a MOSFET family and the power rectifier is a misconfiguration — the structure/mask is
    # committed up front, so a finished wafer cannot be re-graded across device families. It raises (naming
    # the family commit), like the substrate guard.
    wafer = _wafer(HIGH_RES_N_SEED, METAL_FEED)
    with pytest.raises(ValueError, match="device famil"):
        disposition(wafer, MOSFET_FLAVORS + POWER_FAMILY)
    # THE binding case: the high-res native MOSFET and the rectifier SHARE the substrate (both high-res), so
    # the substrate guard would NOT catch them — the FAMILY guard is what keeps the two declared runs apart.
    assert all(t.substrate == "high-res" for t in HIGH_RES_FAMILY + POWER_FAMILY)
    with pytest.raises(ValueError, match="device famil"):
        disposition(wafer, HIGH_RES_FAMILY + POWER_FAMILY)
    # Within ONE family disposition still works (the power family is a menu of one — declared up front).
    assert disposition(wafer, POWER_FAMILY)[0].target.name == "power-rectifier"


def test_physics_enforces_the_family_boundary_cross_grade_yields_nothing():
    # Even setting the guard aside, the physics makes cross-family re-grade worthless: a clean low-R logic
    # wafer re-graded to the rectifier ships ~0 (BV under the floor AND a slow t_rr), and a high-res metal
    # rectifier wafer re-graded to a logic flavor ships ~0 (V_t wrong / leaky) — a genuine declared run.
    logic = _wafer(LOW_R_N_SEED, CLEAN_FEED)
    rect = _wafer(HIGH_RES_N_SEED, METAL_FEED)
    assert grade_for(logic, POWER_RECTIFIER).revenue == 0.0
    assert all(grade_for(rect, f).revenue == 0.0 for f in MOSFET_FLAVORS)


# --------------------------------------------------------------------------- #
# The REQUIRED t_rr / BV guards — both are defining properties of a power part
# --------------------------------------------------------------------------- #
def test_t_rr_and_bv_are_required_not_optional():
    # t_rr and BV are the rectifier's DEFINING axes, so both are REQUIRED (not optional like the MOSFET BV):
    # a die with NO t_rr reading (an unresolved junction → no τ) or NO BV must FAIL, not ship unrated (the
    # advisor's S3 pattern, the mirror of S2's nan-guard). Not reachable on the line (a resolved device always
    # sets τ and BV), a guard.
    assert POWER_RECTIFIER.specs.t_rr_ns.hi == POWER_T_RR_CEILING_NS and not POWER_RECTIFIER.specs.t_rr_ns.optional
    assert POWER_RECTIFIER.specs.bv.lo == HIGH_RES_BV_FLOOR_V and not POWER_RECTIFIER.specs.bv.optional
    no_trr = POWER_RECTIFIER.specs.verdict(_power_die(t_rr=None), None)
    assert no_trr.failed and any("t_rr" in r for r in no_trr.reasons)
    no_bv = POWER_RECTIFIER.specs.verdict(_power_die(bv_V=None), None)
    assert no_bv.failed and any("BV" in r for r in no_bv.reasons)


# --------------------------------------------------------------------------- #
# Bookkeeping — the rectifier revenue closes
# --------------------------------------------------------------------------- #
def test_power_regrade_bookkeeping_closes():
    wafer = _wafer(HIGH_RES_N_SEED, METAL_FEED)
    sc = grade_for(wafer, POWER_RECTIFIER, wafer_cost=80.0)
    assert sc.revenue == sum(POWER_RECTIFIER.prices[b] * n for b, n in sc.bin_counts.items())
    assert sc.profit == sc.revenue - 80.0
    rg = regrade(wafer, POWER_RECTIFIER)
    assert sc.n_good == sum(d.verdict.passed for d in rg.dies if d.verdict is not None)
    # The single-bin policy: every shipped part lands in the one "pass" grade (no t_rr/current sub-grade).
    assert set(sc.bin_counts) <= {"pass"}


# --------------------------------------------------------------------------- #
# The seam — the rectifier + the t_rr window leave the MOSFET targets unchanged
# --------------------------------------------------------------------------- #
def test_seam_mosfet_targets_are_tagged_mosfet_and_t_rr_is_open_for_them():
    # Every MOSFET-family target (the low-R flavors + the high-res native part) carries structure="mosfet"
    # and leaves the t_rr window OPEN — so a die with ANY t_rr scores them exactly as before the slice (a
    # switching speed is not a transistor's acceptance axis). The rectifier is the only "rectifier" structure.
    for t in MOSFET_FLAVORS + HIGH_RES_FAMILY:
        assert t.structure == "mosfet"
        assert t.specs.t_rr_ns.lo is None and t.specs.t_rr_ns.hi is None   # open → never rejects a MOSFET die
    assert POWER_RECTIFIER.structure == "rectifier"
    assert POWER_RECTIFIER not in MOSFET_FLAVORS and POWER_RECTIFIER not in HIGH_RES_FAMILY
    # A die with a (logic-irrelevant) huge t_rr still passes a MOSFET flavor on its real axes (t_rr open).
    slow_logic_die = Die(site=(0, 0), radius_frac=0.0, V_t=0.55, i_dsat=3.3e-3, cd_nm=167.0, nils=4.6,
                         resolved=True, t_rr=1.0e-3)
    assert FAST_LOGIC.specs.verdict(slow_logic_die, None).passed
