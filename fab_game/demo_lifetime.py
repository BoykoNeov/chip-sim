"""The G4b banked artifact: deep-level metals → killed lifetime → a leaky diode (the consequence net doping can't carry).

The fab-line game's G4b — the Tier-2 follow-on G4a named (plan §5a / §6 G4). G4a wired the mobile-ion
**Na → gate-oxide Q_ox → V_t** story; the deep-level **metals** (Fe/Cu) rode along, scrubbed by zone
refining but with *no device consequence* — because their effect is **not** doping. G4b lands it: a
metal is an **SRH recombination centre** (:mod:`chip.lifetime`), so it destroys minority-carrier
lifetime and raises **junction reverse leakage** — *a leaky, low-lifetime diode is how a metal
contaminant kills yield*, the device output net doping cannot carry. Three things shown:

1. **The lifetime/leakage scaling (pure physics — the cited order).** Sweeping the dissolved iron from
   clean to dirty: clean float-zone silicon reads ``τ ~ 1 ms`` / diffusion length ``~ mm`` / a pA-class
   junction leakage; an interstitial-iron level ``[Fe] ~ 1e12 cm⁻³`` drags ``τ`` to a few µs and the
   leakage up orders of magnitude — the textbook ``1/τ = σ_n·v_th·N_t`` scaling.

2. **The isolated metal kill (the dramatic win — what V_t can't see).** A **metal-laden but
   Na/dopant-clean** feed (the ``"metal"`` grade), refined once: the threshold voltage ``V_t`` reads
   **fine** (the metals never touch doping or oxide charge) — yet the junction leakage blows out the
   top of its spec window → the whole wafer is scrapped on **leakage**, and the failure trail names the
   deep-level-metal SRH recombination (not Na, not defocus). Contrast G4a: there the dirty feed walked
   *V_t* out the bottom; here *V_t* is a bystander and the leaky diode is the sole cause.

3. **The rework (purify harder).** The metals' segregation coefficient is tiny (Fe ``k ≈ 8e-6``), so
   zone refining scrubs them ferociously: **one extra pass** (``k²`` at the leading end) drops the
   residual metal orders of magnitude → lifetime recovers to the bulk value → the leakage falls back
   under spec → yield recovers. (Unlike G4a's boron, ``k ≈ 0.8``, which barely scrubs.)

The SRH lifetime/leakage law is cited and triad-tested (``chip/tests/test_lifetime.py``); the
**magnitudes** (capture cross-sections, the clean-bulk lifetime, the leakage calibration) are the
flagged **loose tier** (plan §7) — never asserted with the segregation anchors. The wiring is the
game-layer mechanics invariant (``fab_game/tests/test_leakage.py``). A clean feed is the seam.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_lifetime
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip import lifetime as life
from chip.purification import Contamination

from .pipeline import diagnose, run_line, wafer_yield
from .recipe import PurificationKnobs, Recipe
from .spec import DEFAULT_SPECS
from .state import WaferState
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
GRID_N = 5
N_A = 1.0e17                                   # the substrate doping the leakage depletion width reads
FE_SWEEP = np.logspace(10.0, 14.0, 40)         # dissolved-iron sweep (cm⁻³) — clean → dirty (the scaling)
LADDER = ("clean", "EGS", "solar", "metal")    # the leakage ladder (one pass each) — only "metal" blows the window
METAL_GRADE = "metal"                          # the G4b isolation feed: metal-laden, Na/dopant-clean
METAL_PASSES = (1, 2, 3, 4)                     # the zone-pass rework sweep on the metal feed

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g4b.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g4b.png"


@dataclass(frozen=True)
class DemoResult:
    """The lifetime/leakage scaling + the isolated metal kill + the zone-pass rework — the bundle."""

    fe_sweep: tuple[float, ...]
    tau_us_sweep: tuple[float, ...]            # SRH lifetime (µs) vs [Fe]
    L_um_sweep: tuple[float, ...]              # diffusion length (µm) vs [Fe]
    leak_sweep: tuple[float, ...]              # junction leakage (nA/cm²) vs [Fe]
    leak_spec_hi: float
    v_t_lo: float
    v_t_hi: float
    ladder: tuple[str, ...]                    # the leakage ladder of feed grades (one pass)
    leak_by_grade: tuple[float, ...]           # leakage (nA/cm²) down the ladder
    vt_by_grade: tuple[float, ...]             # V_t down the ladder — flat across the metal feed (the point)
    yield_by_grade: tuple[float, ...]
    metal_passes: tuple[int, ...]
    leak_by_pass: tuple[float, ...]            # leakage (nA/cm²) vs zone passes (metal) — the rework recovery
    tau_us_by_pass: tuple[float, ...]
    yield_by_pass: tuple[float, ...]
    clean_vt: float
    dead_wafer: WaferState                     # metal, one pass — scrapped on LEAKAGE (V_t fine)
    dead_trail: str                            # the failure trail naming the deep-level-metal SRH
    recovered_wafer: WaferState                # metal, two passes — recovered


def _recipe(grade: str, passes: int) -> Recipe:
    return Recipe(purification=PurificationKnobs(grade=grade, zone_passes=passes))


def _single_die(grade: str, passes: int):
    """One representative (uniform) die for a grade/pass count — no variation."""
    w = run_line(_recipe(grade, passes), seed=SEED, variation=NO_VARIATION, grid_n=1)
    return w.dies[0]


def _wafer_yield(grade: str, passes: int) -> float:
    w = run_line(_recipe(grade, passes), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    return wafer_yield(w)


def compute() -> DemoResult:
    """Run the lifetime/leakage scaling, the leakage ladder, and the zone-pass rework (no plotting)."""
    # Panel 1 — the cited physics scaling (straight from chip.lifetime, no game layer).
    bundles = [life.device_leakage(Contamination(Fe=float(f)), N_A=N_A) for f in FE_SWEEP]
    tau_us_sweep = tuple(b.tau_us for b in bundles)
    L_um_sweep = tuple(b.L_diff_um for b in bundles)
    leak_sweep = tuple(b.j_leak_nA_cm2 for b in bundles)

    # Panel 2 — the leakage ladder (one pass): only the metal feed blows the window; V_t stays put.
    ladder_dies = [_single_die(g, 1) for g in LADDER]
    leak_by_grade = tuple(d.j_leak_nA_cm2 for d in ladder_dies)
    vt_by_grade = tuple(d.V_t for d in ladder_dies)
    yield_by_grade = tuple(_wafer_yield(g, 1) for g in LADDER)

    # Panel 3 — the rework: more zone passes scrub the tiny-k metals → leakage recovers under spec.
    pass_dies = [_single_die(METAL_GRADE, n) for n in METAL_PASSES]
    leak_by_pass = tuple(d.j_leak_nA_cm2 for d in pass_dies)
    tau_us_by_pass = tuple(d.tau_us for d in pass_dies)
    yield_by_pass = tuple(_wafer_yield(METAL_GRADE, n) for n in METAL_PASSES)

    dead_wafer = run_line(_recipe(METAL_GRADE, 1), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    dead_die = next(d for d in dead_wafer.dies if d.verdict.failed)
    dead_trail = diagnose(dead_die)
    recovered_wafer = run_line(_recipe(METAL_GRADE, 2), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)

    return DemoResult(
        fe_sweep=tuple(float(f) for f in FE_SWEEP),
        tau_us_sweep=tau_us_sweep, L_um_sweep=L_um_sweep, leak_sweep=leak_sweep,
        leak_spec_hi=DEFAULT_SPECS.leakage.hi, v_t_lo=DEFAULT_SPECS.v_t.lo, v_t_hi=DEFAULT_SPECS.v_t.hi,
        ladder=LADDER, leak_by_grade=leak_by_grade, vt_by_grade=vt_by_grade, yield_by_grade=yield_by_grade,
        metal_passes=METAL_PASSES, leak_by_pass=leak_by_pass, tau_us_by_pass=tau_us_by_pass,
        yield_by_pass=yield_by_pass,
        clean_vt=float(_single_die("clean", 1).V_t),
        dead_wafer=dead_wafer, dead_trail=dead_trail, recovered_wafer=recovered_wafer,
    )


def print_summary(r: DemoResult) -> None:
    """Print the scaling → isolated-metal kill → rework story — the demo's payoff in text."""
    print("\nThe fab line: deep-level metals → killed lifetime → a leaky diode "
          "(the consequence net doping can't carry)\n")

    print("  1. The cited SRH scaling (1/τ = σ_n·v_th·N_t) — clean FZ silicon vs an iron-laden bulk:")
    for f in (1.0e10, 1.0e12, 1.0e14):
        b = life.device_leakage(Contamination(Fe=f), N_A=N_A)
        print(f"     [Fe] = {f:.0e} cm⁻³:  τ = {b.tau_us:8.3g} µs   L = {b.L_diff_um:7.3g} µm   "
              f"leakage = {b.j_leak_nA_cm2:8.3g} nA/cm²")
    print("     → clean silicon ~ms lifetime / mm diffusion length / pA leakage; metals destroy all three.\n")

    print(f"  2. The isolated metal kill — V_t is a bystander (leakage spec ≤ {r.leak_spec_hi:.0f} nA/cm²):")
    print("     feed (1 pass)   V_t (V)      leakage (nA/cm²)   verdict")
    for g, vt, lk, y in zip(r.ladder, r.vt_by_grade, r.leak_by_grade, r.yield_by_grade):
        vflag = "ok" if r.v_t_lo <= vt <= r.v_t_hi else "OUT"
        lflag = "ok" if lk <= r.leak_spec_hi else "OUT"
        print(f"     {g:8s}      {vt:.3f}[{vflag}]   {lk:12.3g}[{lflag}]    yield {y:.0%}")
    print(f"\n     The '{METAL_GRADE}' feed (1 pass) → V_t {r.clean_vt:.3f} V (in spec!) but the diode is leaky:")
    print("     " + r.dead_trail.replace("\n", "\n     ") + "\n")

    print("  3. Rework — purify harder (the metals' tiny k scrubs fast):")
    for n, lk, tau, y in zip(r.metal_passes, r.leak_by_pass, r.tau_us_by_pass, r.yield_by_pass):
        lflag = "ok" if lk <= r.leak_spec_hi else "OUT"
        print(f"     {n} pass(es): leakage = {lk:9.3g} nA/cm² [{lflag}]   τ = {tau:8.3g} µs   yield {y:.0%}")
    print(f"     → one extra pass drops the residual metal orders of magnitude (k² at the leading end) "
          f"→ lifetime recovers → leakage back under spec ({wafer_yield(r.dead_wafer):.0%} → "
          f"{wafer_yield(r.recovered_wafer):.0%}).\n")
    print("  New: the cited SRH lifetime + generation-leakage law (chip.lifetime, triad-tested) — the")
    print("  device output the deep-level metals needed. The metals→τ→leakage wiring is the game layer.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the G4b lifetime/leakage artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import lifetime_figure

    fig = lifetime_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ², µ, τ, → on legacy codepages

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
