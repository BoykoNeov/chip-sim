"""Device targets, slice 2 — the HV-I/O flavor + junction avalanche breakdown: the two gates again.

The slice-2 spine of ``docs/plans/device-targets.md``: a third MOSFET flavor (``hv-io``) gated on a new
cited device output — the drain–body junction **avalanche breakdown** ``BV`` (:mod:`chip.breakdown`). The
plan's two empirical gates are re-proven for the **junction-depth axis** (the diffusion drive-in), and they
are asserted *first*:

1. **The windows genuinely cross** — and the *new* content (advisor): ``BV`` is an axis **independent of
   ``V_t``**. Two wafers with identical ``V_t`` (same substrate + oxide) but different drive-in have
   different ``BV`` → one HV-good, one HV-reject, purely on breakdown. That decoupling is what makes HV-I/O a
   real flavor rather than a relabel of the thick-oxide low-power corner. (Plus the spec-level crossing: the
   HV ``V_t`` window crosses low-power's from above, un-nesting.)
2. **The declaration moves the recipe optimum** — on the **drive-in** (junction depth). At a thick oxide
   (fast-logic already out on ``V_t``): a *shallow* junction → best SKU is **low-power** (HV rejects on BV);
   a *deep* junction → best SKU flips to **hv-io** (its deep junction clears the BV floor and an I/O part
   commands a premium). The flip is physics-gated, not a relabel — no price ships a shallow-junction part as
   HV.

Then the re-grade **bookkeeping** and the **seam** (the new optional ``bv`` window is OPEN for the logic
flavors, so adding it leaves fast-logic byte-for-byte). All bands/prices are flagged house numbers
(ADR 0005 §5) — only the *relationships* are asserted, never the magnitudes.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from fab_game.pipeline import run_line
from fab_game.recipe import DEFAULT_RECIPE
from fab_game.spec import DEFAULT_SPECS
from fab_game.state import Die, Verdict, WaferState
from fab_game.steps import device_step
from fab_game.targets import (
    FAST_LOGIC,
    HV_IO,
    HV_IO_BV_FLOOR_V,
    LOW_POWER,
    MOSFET_FLAVORS,
    disposition,
    grade_for,
    regrade,
)
from fab_game.variation import Variation

# A thick I/O gate oxide → V_t over fast-logic's ceiling (fast-logic is out, isolating the LP↔HV flip);
# the drive-in time is the BV lever (deeper junction → higher breakdown). FLAGGED recipe corners.
THICK_OXIDE_MIN = 28.0
SHALLOW_DRIVEIN_MIN = 8.0      # the recipe default → a shallow junction → BV below the HV floor
DEEP_DRIVEIN_MIN = 120.0       # a long drive-in → a deep junction → BV above the HV floor


def _wafer(oxide_min: float, drivein_min: float, *, slice_z: float = 0.0) -> WaferState:
    """A full wafer fabbed at a gate-oxide time + an S/D drive-in time (the BV lever) — grade it after.

    Engages the diffusion series-R consumer (``sd_contact_squares``) so the recipe matches the journey's
    diffusion stage; the physics is target-independent (re-graded against each target downstream)."""
    recipe = replace(
        DEFAULT_RECIPE,
        oxidation=replace(DEFAULT_RECIPE.oxidation, minutes=oxide_min),
        diffusion=replace(DEFAULT_RECIPE.diffusion, t_drivein_min=drivein_min, sd_contact_squares=0.15),
        czochralski=replace(DEFAULT_RECIPE.czochralski, slice_z=slice_z),
    )
    return run_line(recipe, seed=0, variation=Variation(), specs=FAST_LOGIC.specs, grid_n=7)


# --------------------------------------------------------------------------- #
# Gate 1 — the windows cross, and BV is an axis independent of V_t
# --------------------------------------------------------------------------- #
def test_gate1_hv_vt_window_crosses_low_power_from_above():
    lp, hv = LOW_POWER.specs.v_t, HV_IO.specs.v_t
    # A real crossing region exists ([0.72, 0.85]) …
    overlap_lo, overlap_hi = max(lp.lo, hv.lo), min(lp.hi, hv.hi)
    assert overlap_lo < overlap_hi, "the HV and low-power V_t windows must overlap (a shared crossing region)"
    # … and HV sits ABOVE low-power (each has an exclusive region — HV-only above, low-power-only below):
    # partially disjoint, not nested. And HV is disjoint from fast-logic (it is the highest-V_t flavor).
    assert hv.lo > lp.lo and hv.hi > lp.hi, "HV must cross low-power from above, not nest"
    assert hv.lo >= FAST_LOGIC.specs.v_t.hi, "HV's V_t floor must sit at/above fast-logic's ceiling (disjoint)"


def test_gate1_only_hv_carries_a_bv_floor():
    # The new axis exists for HV alone: fast-logic and low-power leave the BV window OPEN (no floor), so a
    # shallow-junction part is fine for them; only HV gates on breakdown. (The seam: the logic flavors are
    # byte-for-byte unaffected by the new output — see the seam test below.)
    assert FAST_LOGIC.specs.bv.lo is None and LOW_POWER.specs.bv.lo is None
    assert HV_IO.specs.bv.lo == HV_IO_BV_FLOOR_V and HV_IO.specs.bv.optional


def test_gate1_bv_decouples_from_v_t_same_wafer_different_drivein():
    # THE slice-2 gate (advisor). Two wafers at the SAME oxide (→ the same V_t) but different drive-in (→
    # different junction depth → different BV). BV must be the SOLE discriminator: HV rejects the shallow
    # one and accepts the deep one, while low-power (no BV floor) accepts BOTH.
    shallow = _wafer(THICK_OXIDE_MIN, SHALLOW_DRIVEIN_MIN)
    deep = _wafer(THICK_OXIDE_MIN, DEEP_DRIVEIN_MIN)

    # Same V_t (the oxide is identical; BV does not touch V_t), genuinely different BV (the drive-in did).
    def mean(field, w):
        vals = [getattr(d, field) for d in w.dies if getattr(d, field) is not None]
        return sum(vals) / len(vals)
    assert mean("V_t", shallow) == pytest.approx(mean("V_t", deep), abs=1e-9)
    assert mean("bv_V", shallow) < HV_IO_BV_FLOOR_V < mean("bv_V", deep)

    # HV: the shallow lot is a total reject (BV under the floor), the deep lot ships — purely on breakdown.
    assert grade_for(shallow, HV_IO).revenue == 0.0
    assert grade_for(deep, HV_IO).revenue > 0.0
    # Low-power: BV is irrelevant to it — it ships BOTH (the same V_t/I_Dsat is in its windows either way).
    assert grade_for(shallow, LOW_POWER).revenue > 0.0
    assert grade_for(deep, LOW_POWER).revenue > 0.0


# --------------------------------------------------------------------------- #
# Gate 2 — declaring HV-I/O moves the optimum on the drive-in (junction-depth) axis
# --------------------------------------------------------------------------- #
def test_gate2_deep_drivein_flips_the_best_sku_to_hv():
    # At a thick oxide (fast-logic already out on V_t — assert it), the drive-in alone moves the optimum:
    # a shallow junction → best SKU = low-power (HV rejects on BV); a deep junction → best SKU = hv-io.
    shallow = _wafer(THICK_OXIDE_MIN, SHALLOW_DRIVEIN_MIN)
    deep = _wafer(THICK_OXIDE_MIN, DEEP_DRIVEIN_MIN)
    # Fast-logic is genuinely out at this oxide (V_t over its ceiling) — so the flip is a clean LP↔HV move.
    assert grade_for(shallow, FAST_LOGIC).revenue == 0.0 and grade_for(deep, FAST_LOGIC).revenue == 0.0

    best_shallow = disposition(shallow)[0].target.name
    best_deep = disposition(deep)[0].target.name
    assert best_shallow == "low-power", "a shallow junction must disposition best as low-power (HV rejects on BV)"
    assert best_deep == "hv-io", "a deep junction must flip the best SKU to hv-io"
    # The tie-proof form of 'the optimum moved' (no reliance on a unique argmax): at each end the winner
    # strictly out-earns the OTHER flavor, and the winner is different at the two ends.
    assert grade_for(deep, HV_IO).revenue > grade_for(deep, LOW_POWER).revenue
    assert grade_for(shallow, LOW_POWER).revenue > grade_for(shallow, HV_IO).revenue


# --------------------------------------------------------------------------- #
# Re-grade bookkeeping — the HV revenue closes (the third flavor is fully wired)
# --------------------------------------------------------------------------- #
def test_hv_regrade_bookkeeping_closes():
    wafer = _wafer(THICK_OXIDE_MIN, DEEP_DRIVEIN_MIN)
    sc = grade_for(wafer, HV_IO, wafer_cost=80.0)
    assert sc.revenue == sum(HV_IO.prices[b] * n for b, n in sc.bin_counts.items())
    assert sc.profit == sc.revenue - 80.0
    rg = regrade(wafer, HV_IO)
    assert sc.n_good == sum(d.verdict.passed for d in rg.dies if d.verdict is not None)
    # The disposition menu carries all three flavors (whole-wafer re-grade across the family).
    assert {g.target.name for g in disposition(wafer)} == {t.name for t in MOSFET_FLAVORS}


def test_a_shallow_junction_die_fails_hv_only_on_breakdown():
    # A die parked inside HV's V_t/I_Dsat windows but with a SHALLOW junction (low BV) fails HV on BV alone
    # — and the reason names the breakdown, not the threshold (the trail teaches the junction-depth lesson).
    die = Die(site=(0, 0), radius_frac=0.0, V_t=0.80, i_dsat=2.3e-3, cd_nm=167.0, nils=4.6,
              resolved=True, bv_V=HV_IO_BV_FLOOR_V - 1.0)
    v = HV_IO.specs.verdict(die, None)
    assert v.failed and len(v.reasons) == 1 and "BV" in v.reasons[0]   # BV is the SOLE failing reason
    # The same die with a deep-enough junction (BV over the floor) passes HV.
    assert HV_IO.specs.verdict(replace(die, bv_V=HV_IO_BV_FLOOR_V + 1.0), None).passed


# --------------------------------------------------------------------------- #
# The seam — the new BV output/window leaves the logic flavors byte-for-byte
# --------------------------------------------------------------------------- #
def test_device_step_with_an_unresolved_junction_yields_no_breakdown_not_a_crash():
    # An unresolved junction leaves x_j = nan (the diffusion profile never crossed the body doping). The
    # device step must screen nan (it slips past breakdown's r_j>0 guard) → bv_V = None, no record key, no
    # crash — the same quiet degradation x_j=nan already gives I_Dsat. (No current recipe reaches this — the
    # S/D always resolves against the 1e17 body — so it is a latent-regression guard.)
    die = Die(site=(0, 0), radius_frac=0.0, t_ox_um=0.014, cd_nm=167.0, resolved=True,
              x_j_um=float("nan"), R_s=float("nan"))
    out = device_step(die, DEFAULT_RECIPE.device, DEFAULT_RECIPE.channel_N_A)
    assert out.bv_V is None and "bv_V" not in out.history[-1].outputs


def test_seam_bv_window_is_open_so_logic_flavors_are_unchanged():
    # The bv window is optional + open (no bounds) for fast-logic/low-power → SpecWindow.check returns None
    # for ANY bv value (including None), so the parametric verdict is identical to pre-slice-2. A nominal
    # die with a populated bv_V grades exactly as it would have without the field.
    for target in (FAST_LOGIC, LOW_POWER):
        assert target.specs.bv.check(4.0) is None and target.specs.bv.check(None) is None
    # A finished nominal wafer's fast-logic verdicts are unaffected by the bv field carrying a value.
    wafer = run_line(DEFAULT_RECIPE, seed=0, variation=Variation(), specs=FAST_LOGIC.specs, grid_n=7)
    assert all(d.bv_V is not None for d in wafer.dies if d.resolved)   # BV IS computed (the output exists) …
    for d in wafer.dies:                                              # … but it never changes a logic verdict
        assert FAST_LOGIC.specs.verdict(d, None) == d.verdict          # (the run already used FAST_LOGIC specs)
