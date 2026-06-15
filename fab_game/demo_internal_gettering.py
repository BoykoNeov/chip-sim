"""The S4 banked artifact: crucible oxygen's DUAL-USE — donors-bad vs internal-gettering-good, one device.

C1 (:mod:`fab_game.demo_thermal_donors`) gave crucible oxygen its *liability* face: the ~450 °C thermal
donors that compensate the p-substrate → ``V_t`` down. This is the *asset* face of the **same**
incorporated ``[O_i]``: bulk oxygen **precipitates** trap the deep-level metals (Fe/Cu) out of the
device region — **internal gettering** (Tan–Gardner–Tice, Phys. Rev. Lett. 64, 196, 1990) — so the same
oxygen that costs threshold *buys back* junction leakage. The lesson is the **trade-off, not one
optimum**: this is a *process-trade-off within one device*, distinct from the multi-target market
segmentation (S1–S3) — there is no second SKU here, just one knob with two opposite consequences.

The wafer is a **trace-metal** feed (moderately Fe/Cu-laden — internal gettering's actual regime, a few×
over the leakage window, not the 10× a purification pass is for). Three panels, all off the real line:

1. **The two faces of oxygen.** The gettering efficiency η([O_i]) (0 below the cited ~12 ppma
   precipitation threshold, then rising toward its flagged <1 ceiling) and the thermal-donor density
   N_TD([O_i]) (the C1 KFR kinetics at the forming-gas sinter) — the same oxygen drives both.
2. **The Goldilocks (the headline).** Leakage([O_i]) falls (gettering) while V_t([O_i]) falls (donors);
   the band where BOTH pass their spec (leakage ≤ 10 nA/cm², V_t ≥ 0.45 V) is the dual-use sweet spot —
   too little oxygen leaks, too much craters V_t.
3. **The yield window.** The wafer yield([O_i]) as a single hump: 0 on the low-oxygen (leakage) side, 0
   on the high-oxygen (V_t) side, the two-sided window in between.

A real secondary coupling falls out of wiring it honestly (named, not hidden): the donors lower the net
``N_A``, which widens the junction depletion width ``W ∝ 1/√N_A`` and so nudges generation leakage
``J ∝ W`` *up* — so below the gettering threshold oxygen makes the diode marginally leakier, and once
gettering saturates (the cap) leakage U-turns back up. Both lie deep in already-failed territory (the
low side is ≫ the leakage spec anyway; the high side is past the V_t crater), so the **verdict-relevant**
leakage is monotone — gettering only helps where it can still matter. (This is *not* the deferred
over-precipitation U-shape — it is the donor↔depletion-width coupling, real and kept.)

Opt-in and seam-safe: no oxygen (or below the precipitation threshold) ⇒ no gettering AND no donors ⇒
the G1–G7 banked demos byte-for-byte unchanged.

Run::

    python -m fab_game.demo_internal_gettering
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.czochralski import (
    IG_CRITICAL_OXYGEN_CM3,
    internal_gettering_efficiency,
    thermal_donor_density,
)

from .pipeline import run_line, wafer_yield
from .recipe import CzochralskiKnobs, PurificationKnobs, Recipe
from .spec import DEFAULT_SPECS
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SUBSTRATE_N_A = 1.0e17                              # the boron substrate the donors compensate
FEED_GRADE = "trace-metal"                          # the moderate-contamination wafer (IG's regime)
FORMING_GAS_MIN = 30.0                              # the universal final ~450 °C sinter (the donor budget)
# The oxygen axis: the fine grid for the η / N_TD curves, and the (same) pipeline points for V_t/leak/yield.
OXYGEN_FINE_CM3 = tuple(float(o) for o in np.linspace(3.0e17, 1.4e18, 80))
OXYGEN_PIPE_CM3 = tuple(float(o) for o in np.linspace(3.0e17, 1.4e18, 23))

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-s4.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-s4.png"


@dataclass(frozen=True)
class DemoResult:
    """The two faces of oxygen + the Goldilocks leakage/V_t window + the yield hump (no score)."""

    substrate_N_A: float
    feed_grade: str
    critical_oxygen: float
    leak_hi: float
    v_t_lo: float
    v_t_hi: float
    base_leak: float                                # the no-oxygen (un-gettered) leakage of the feed
    # Panel 1 — the two faces (fine curves):
    oxygen_fine: tuple[float, ...]
    efficiency_fine: tuple[float, ...]              # η([O_i]) — internal gettering (0 below the threshold)
    donor_fine: tuple[float, ...]                   # N_TD([O_i]) at the forming-gas sinter (the C1 kinetics)
    # Panels 2 & 3 — the real-pipeline consequences:
    oxygen_pipe: tuple[float, ...]
    leak_pipe: tuple[float, ...]                    # leakage([O_i]) (nA/cm²) — falls (gettering)
    vt_pipe: tuple[float, ...]                      # V_t([O_i]) (V) — falls (donors)
    yield_pipe: tuple[float, ...]                   # wafer yield([O_i]) — the two-sided hump
    pass_lo: float | None                           # the PASS band edges on [O_i] (None if empty)
    pass_hi: float | None


def _recipe(oxygen: float | None) -> Recipe:
    return Recipe(
        purification=PurificationKnobs(grade=FEED_GRADE, zone_passes=1),
        czochralski=CzochralskiKnobs(
            N_seed=SUBSTRATE_N_A, oxygen_conc_cm3=oxygen, forming_gas_anneal_min=FORMING_GAS_MIN),
    )


def _center(oxygen: float | None):
    return run_line(_recipe(oxygen), variation=NO_VARIATION, grid_n=1).dies[0]


def compute() -> DemoResult:
    """Build the two oxygen faces (fine) + the V_t/leakage/yield consequences (the real pipeline)."""
    eff = tuple(float(internal_gettering_efficiency(o)) for o in OXYGEN_FINE_CM3)
    ntd = tuple(float(thermal_donor_density(o, FORMING_GAS_MIN)) for o in OXYGEN_FINE_CM3)

    leak, vt, ys = [], [], []
    for o in OXYGEN_PIPE_CM3:
        d = _center(o)
        leak.append(float(d.j_leak_nA_cm2))
        vt.append(float(d.V_t))
        ys.append(float(wafer_yield(run_line(_recipe(o), variation=NO_VARIATION, grid_n=1))))

    # The PASS band on [O_i] (where BOTH windows pass) — the contiguous region (for shading + the headline).
    leak_hi, v_lo, v_hi = DEFAULT_SPECS.leakage.hi, DEFAULT_SPECS.v_t.lo, DEFAULT_SPECS.v_t.hi
    passing = [o for o, lk, v in zip(OXYGEN_PIPE_CM3, leak, vt) if lk <= leak_hi and v_lo <= v <= v_hi]
    pass_lo = min(passing) if passing else None
    pass_hi = max(passing) if passing else None

    base_leak = float(_center(None).j_leak_nA_cm2)

    return DemoResult(
        substrate_N_A=SUBSTRATE_N_A, feed_grade=FEED_GRADE, critical_oxygen=IG_CRITICAL_OXYGEN_CM3,
        leak_hi=leak_hi, v_t_lo=v_lo, v_t_hi=v_hi, base_leak=base_leak,
        oxygen_fine=OXYGEN_FINE_CM3, efficiency_fine=eff, donor_fine=ntd,
        oxygen_pipe=OXYGEN_PIPE_CM3, leak_pipe=tuple(leak), vt_pipe=tuple(vt), yield_pipe=tuple(ys),
        pass_lo=pass_lo, pass_hi=pass_hi,
    )


def print_summary(r: DemoResult) -> None:
    """Print the dual-use story — the two faces, the Goldilocks band — in text (no score)."""
    print("\nDevice targets S4: crucible oxygen's DUAL-USE — donors-bad vs internal-gettering-good (one device)\n")

    print(f"  A {r.feed_grade} wafer (moderate Fe/Cu) leaks {r.base_leak:.1f} nA/cm² un-gettered "
          f"(spec ≤ {r.leak_hi:.0f}) → it needs gettering.")
    print(f"  Internal gettering (Tan–Gardner–Tice, PRL 64, 196, 1990): bulk oxygen precipitates trap the")
    print(f"  metals out of the device region — but ONLY above the ~12 ppma precipitation threshold "
          f"([O_i] ≈ {r.critical_oxygen:.1e} cm⁻³).")
    print(f"  The SAME oxygen makes thermal donors (C1) at the forming-gas sinter → V_t down. The trade-off:\n")

    print(f"     {'[O_i] cm⁻³':>11}  {'leakage':>9}  {'V_t':>6}  {'yield':>6}   verdict")
    for o, lk, v, y in zip(r.oxygen_pipe, r.leak_pipe, r.vt_pipe, r.yield_pipe):
        if o in (r.oxygen_pipe[0], r.pass_lo, r.pass_hi) or abs(o - 1.0e18) < 3e16 or o == r.oxygen_pipe[-1]:
            ok = (lk <= r.leak_hi and r.v_t_lo <= v <= r.v_t_hi)
            tag = "PASS" if ok else ("leak" if lk > r.leak_hi else "V_t")
            print(f"     {o:>11.2e}  {lk:>7.2g}  {v:>6.3f}  {y:>5.0%}   {tag}")

    if r.pass_lo is not None:
        print(f"\n  → the Goldilocks band: [O_i] ≈ {r.pass_lo:.2e} … {r.pass_hi:.2e} cm⁻³ passes BOTH "
              f"(leakage ≤ {r.leak_hi:.0f}, V_t ≥ {r.v_t_lo:.2f}).")
    print(f"     too little oxygen → un-gettered metals leak; too much → donors crater V_t. One knob, two faces.\n")

    print("  New: internal gettering (chip.czochralski.internal_gettering_efficiency + "
          "chip.purification.getter_metals, triad-tested);")
    print("  the cited claim is the precipitation threshold, the efficiency magnitude is flagged. Opt-in "
          "(no oxygen → the seam).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the S4 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import internal_gettering_figure

    fig = internal_gettering_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # [O_i], →, ≈ on legacy codepages

    r = compute()
    print_summary(r)
    try:
        saved = save_figure(r)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
