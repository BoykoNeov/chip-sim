"""The S5 banked artifact: one carrier lifetime ``τ``, read two opposite ways — the LIFETIME inversion.

The richest, last "good is relative" slice (``docs/plans/device-targets.md`` slice 5). G4b
(:mod:`fab_game.demo_lifetime`) made the deep-level metals (Fe/Cu) destroy minority-carrier lifetime ``τ``
and, through it, raise the junction reverse **leakage** ``J_gen ∝ 1/τ`` — *the* device killer for a logic
part. This is the **same ``τ`` read in the opposite direction**: a power rectifier cannot switch off until
its stored minority charge recombines, so its reverse-recovery time ``t_rr ∝ τ`` (the charge-control storage
time, :mod:`chip.reverse_recovery`). A **short** ``τ`` — a leaky, low-lifetime wafer that *ruins* a logic
part — is exactly what makes a **fast** rectifier. The lifetime killer is the feature. (Real fast/soft
rectifiers are made this way: gold/platinum doping or electron irradiation *deliberately* kills lifetime to
speed switching — Sze, Baliga.) One cited output (``t_rr``); the inversion adds **no new lifetime physics**.

Three panels, telling the inversion:

1. **The two faces of one ``τ``.** Over a lifetime sweep, the junction leakage ``J_gen(τ) ∝ 1/τ`` (the logic
   killer, rising as ``τ`` falls) and the recovery time ``t_rr(τ) ∝ τ`` (the rectifier feature, falling as
   ``τ`` falls). The logic leakage ceiling and the rectifier ``t_rr`` ceiling carve out **disjoint** pass
   bands on the *same* axis — logic wants a **long** ``τ``, the rectifier a **short** one.
2. **The declaration moves the optimum.** On the high-res substrate, sweeping the purification (more zone
   passes → cleaner feed → longer ``τ``): the native-MOSFET revenue **rises** with passes (it wants the
   clean feed) while the power-rectifier revenue **falls** (it wants the lifetime-killed feed). The best SKU
   flips — declaring the target moves the recipe optimum.
3. **The rectifier needs the light boule too.** ``BV(N_substrate)`` crossing the blocking-voltage floor: a
   short ``τ`` is necessary but not sufficient — a power part also needs the lighter (high-res) substrate for
   its reverse blocking voltage (the slice-3 substrate commit), so it is its own **declared run**, never a
   harvest of a heavy logic wafer.

The cited claim is the proportionality ``t_rr ∝ τ`` (charge-control); the switching operating point is
flagged. Opt-in and seam-safe: ``t_rr`` is a purely additive device output (it never moves ``V_t``/``I_Dsat``
and only the power-rectifier target scores it), so the G1–G7 banked demos are byte-for-byte unchanged.

Run::

    python -m fab_game.demo_reverse_recovery
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from chip.lifetime import generation_leakage_density
from chip.reverse_recovery import reverse_recovery_time

from .pipeline import run_line
from .recipe import DEFAULT_RECIPE, CzochralskiKnobs, PurificationKnobs, Recipe
from .spec import DEFAULT_SPECS
from .targets import HIGH_RES, HIGH_RES_BV_FLOOR_V, POWER_RECTIFIER, POWER_T_RR_CEILING_NS, grade_for
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SUBSTRATE_N_A = 1.0e16                              # the light (high-res) substrate the rectifier is grown on
FEED_GRADE = "metal"                                # the lifetime killer (Fe/Cu) — Na-/dopant-clean (τ only)
LEAK_CEIL = DEFAULT_SPECS.leakage.hi                # the logic leakage ceiling (nA/cm²)
T_RR_CEIL = POWER_T_RR_CEILING_NS                   # the rectifier reverse-recovery ceiling (ns)
# Panel 1 — the fine τ sweep (direct chip functions, the two faces).
TAU_FINE_S = tuple(float(t) for t in np.logspace(-9.0, -3.0, 240))
# Panel 2 — the purification sweep (real pipeline): more passes → cleaner feed → longer τ.
ZONE_PASSES = tuple(float(p) for p in np.linspace(0.8, 2.6, 19))
# Panel 3 — the substrate sweep (real pipeline): lighter boule → higher BV.
N_SEED_SWEEP = tuple(float(n) for n in np.logspace(15.3, 17.2, 16))

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-s5.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-s5.png"


@dataclass(frozen=True)
class DemoResult:
    """The two faces of one τ + the moving optimum + the substrate commit (no score)."""

    substrate_N_A: float
    feed_grade: str
    leak_ceil: float
    t_rr_ceil: float
    bv_floor: float
    # Panel 1 — the two faces (fine, direct chip functions):
    tau_fine_s: tuple[float, ...]
    leak_fine: tuple[float, ...]                    # J_gen(τ) ∝ 1/τ (nA/cm²) — the logic killer
    t_rr_fine_ns: tuple[float, ...]                 # t_rr(τ) ∝ τ (ns) — the rectifier feature
    tau_leak_edge_s: float                          # τ where leakage = the logic ceiling (logic wants τ above)
    tau_trr_edge_s: float                           # τ where t_rr = the rectifier ceiling (rect wants τ below)
    # Panel 2 — the optimum moves (real pipeline, high-res substrate):
    zone_passes: tuple[float, ...]
    tau_pipe_us: tuple[float, ...]                  # the τ each feed cleanliness reaches (µs)
    native_rev: tuple[float, ...]                   # high-res native-MOSFET revenue (rises with passes)
    rectifier_rev: tuple[float, ...]               # power-rectifier revenue (falls with passes)
    # Panel 3 — the substrate commit (real pipeline):
    n_seed_sweep: tuple[float, ...]
    bv_sweep: tuple[float, ...]                     # BV(N_substrate) (V) — crosses the floor at the light boule
    n_seed_bv_edge: float                           # the N_substrate where BV = the floor (rect needs lighter)


def _pipe_die(n_seed: float, grade: str, passes: float):
    recipe = replace(
        DEFAULT_RECIPE,
        czochralski=replace(DEFAULT_RECIPE.czochralski, N_seed=n_seed),
        purification=PurificationKnobs(grade=grade, zone_passes=passes),
    )
    return run_line(recipe, variation=NO_VARIATION, grid_n=1).dies[0], recipe


def _crossing(xs, ys, target: float) -> float:
    """The x (log-interpolated) where the monotone curve ``ys`` crosses ``target`` (NaN if it never does)."""
    xs, ys = np.asarray(xs), np.asarray(ys)
    lx = np.log(xs)
    # ys may rise or fall; interpolate on the monotone-sorted (ys → lx) relation.
    order = np.argsort(ys)
    if not (ys[order][0] <= target <= ys[order][-1]):
        return float("nan")
    return float(np.exp(np.interp(target, ys[order], lx[order])))


def compute() -> DemoResult:
    """Build the two faces (fine, direct) + the moving optimum + the substrate commit (the real pipeline)."""
    # Panel 1 — the two faces of one τ (direct chip functions, the light substrate the rectifier lives on).
    leak_fine = tuple(float(generation_leakage_density(t, SUBSTRATE_N_A) * 1.0e9) for t in TAU_FINE_S)
    t_rr_fine = tuple(float(reverse_recovery_time(t) * 1.0e9) for t in TAU_FINE_S)
    tau_leak_edge = _crossing(TAU_FINE_S, leak_fine, LEAK_CEIL)     # logic: τ ABOVE this passes leakage
    tau_trr_edge = _crossing(TAU_FINE_S, t_rr_fine, T_RR_CEIL)      # rectifier: τ BELOW this passes t_rr

    # Panel 2 — the optimum moves (high-res substrate, sweep the feed cleanliness).
    tau_pipe, nat_rev, rec_rev = [], [], []
    for p in ZONE_PASSES:
        d, recipe = _pipe_die(SUBSTRATE_N_A, FEED_GRADE, p)
        tau_pipe.append(float(d.tau_us))
        w = run_line(recipe, variation=NO_VARIATION, grid_n=1)
        nat_rev.append(float(grade_for(w, HIGH_RES).revenue))
        rec_rev.append(float(grade_for(w, POWER_RECTIFIER).revenue))

    # Panel 3 — the substrate commit (BV crosses the floor only at the light boule).
    bv_sweep = []
    for n in N_SEED_SWEEP:
        d, _ = _pipe_die(n, FEED_GRADE, 1.0)
        bv_sweep.append(float(d.bv_V))
    n_seed_bv_edge = _crossing(N_SEED_SWEEP, bv_sweep, HIGH_RES_BV_FLOOR_V)

    return DemoResult(
        substrate_N_A=SUBSTRATE_N_A, feed_grade=FEED_GRADE, leak_ceil=LEAK_CEIL, t_rr_ceil=T_RR_CEIL,
        bv_floor=HIGH_RES_BV_FLOOR_V,
        tau_fine_s=TAU_FINE_S, leak_fine=leak_fine, t_rr_fine_ns=t_rr_fine,
        tau_leak_edge_s=tau_leak_edge, tau_trr_edge_s=tau_trr_edge,
        zone_passes=ZONE_PASSES, tau_pipe_us=tuple(tau_pipe), native_rev=tuple(nat_rev),
        rectifier_rev=tuple(rec_rev),
        n_seed_sweep=N_SEED_SWEEP, bv_sweep=tuple(bv_sweep), n_seed_bv_edge=n_seed_bv_edge,
    )


def print_summary(r: DemoResult) -> None:
    """Print the lifetime inversion — the two faces of one τ, the moving optimum, the substrate commit."""
    print("\nDevice targets S5: one carrier lifetime τ, read two OPPOSITE ways — the lifetime inversion\n")

    print(f"  The SAME minority-carrier τ feeds two scored outputs that pull in opposite directions:")
    print(f"    • junction leakage  J_gen ∝ 1/τ  → a logic part wants τ LONG  (a clean feed, low leakage)")
    print(f"    • reverse recovery  t_rr  ∝ τ    → a rectifier wants τ SHORT (a lifetime-killed feed, fast)")
    print(f"  So the leakage that KILLS a logic part is exactly what a fast rectifier needs.\n")

    print(f"  On the light (high-res, N_A={r.substrate_N_A:.0e}) substrate the two pass bands are DISJOINT on τ:")
    print(f"    logic  ships at τ ≳ {r.tau_leak_edge_s * 1e6:.2f} µs  (leakage ≤ {r.leak_ceil:.0f} nA/cm²)")
    print(f"    rectifier ships at τ ≲ {r.tau_trr_edge_s * 1e6:.2f} µs  (t_rr ≤ {r.t_rr_ceil:.0f} ns)")
    print(f"    → mutual rejection: a clean wafer is logic-good / rectifier-reject, a metal feed the reverse.\n")

    print(f"  Declaring the target moves the purification optimum (high-res, '{r.feed_grade}' feed):")
    print(f"     {'passes':>6}  {'τ (µs)':>9}  {'native $':>9}  {'rect $':>7}   best")
    for p, t, nv, rv in zip(r.zone_passes, r.tau_pipe_us, r.native_rev, r.rectifier_rev):
        if p in (r.zone_passes[0], r.zone_passes[-1]) or abs(nv - rv) < 13.0:
            best = "native" if nv > rv else ("rectifier" if rv > nv else "tie/neither")
            print(f"     {p:>6.2f}  {t:>9.3g}  {nv:>8.0f}  {rv:>7.0f}   {best}")
    print(f"     → more passes → cleaner feed → longer τ → native rises, rectifier falls (the optimum flips).\n")

    print(f"  But a short τ is not enough — the rectifier needs the LIGHT boule for blocking voltage:")
    print(f"     BV crosses the {r.bv_floor:.0f} V floor at N_substrate ≈ {r.n_seed_bv_edge:.1e} cm⁻³ "
          f"(lighter → higher BV).")
    print(f"     So a power rectifier is its OWN declared run (light substrate + killed lifetime), never a "
          f"disposition of a logic wafer.\n")

    print("  New: chip.reverse_recovery.reverse_recovery_time (t_rr = τ·ln(1+I_F/I_R), derived from the "
          "charge-control")
    print("  ODE — triad-tested); the cited claim is t_rr ∝ τ, the operating point is flagged. Additive "
          "(the seam holds).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the S5 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import reverse_recovery_figure

    fig = reverse_recovery_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # τ, →, ≈, µ on legacy codepages

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
