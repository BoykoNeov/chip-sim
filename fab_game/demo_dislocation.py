"""The A1 banked artifact: the interstitial side of Voronkov — slow pull → grown-in dislocations → a leaky diode.

CG-2 (the Voronkov V/G criterion) wired only the **vacancy** side: ``ξ = V/G > ξ_t`` → COP voids → the
G3 Poisson **yield** map. Pulling *slower* (``ξ < ξ_t``) was then free on yield — CG-1 flattened the
doping (a benefit) and the COP cost simply switched off. A1 closes that escape: a too-slow pull (or an
over-steep hot zone) freezes in **interstitial-rich** silicon → grown-in **dislocations**
(:func:`chip.czochralski.dislocation_defect_density`), which are recombination centres → they raise the
junction **reverse leakage** (the G4b :mod:`chip.lifetime` channel, ``1/τ += K·ρ_disl``) — *a different
device output, not a second yield term*. So the criterion becomes **two-sided**: too-fast costs **yield**
(COP voids), too-slow costs **leakage** (dislocations), with the defect-free optimum **at** ``ξ_t``.

THE honest magnitude (lead with it — the CG-2 finding restated). Realistic CZ sits at ``ξ ≈ 0.29 > ξ_t``
— the **vacancy** side — so the dislocation/leakage cost only bites at a *deliberately* slow pull or an
over-steep ``G``. A1 is a **corner**, not the main-line lever: its value is the criterion's symmetry
(slow pull is no longer free) and the radial **rim** it lights up (next paragraph), not a trade-off you
would operate at. The optimum's **location** is the cited ``ξ_t`` (coefficient-robust, the tight leg);
the leakage **depth** is a flagged house number (the density coefficient here × the lifetime ``K`` — only
their product matters), and there is **no conservation law and no engine** (CG-2's tier).

THE radial completion (A1 is A2's deferred consumer). A2's OSF ring left a **vacancy core** (COP voids,
yield) and an interstitial **rim** it could only prove *clean of voids*. A1 reveals the rim is clean of
voids but **dislocation-leaky** — so the wafer is a void-killed core (yield) + a dislocation-leaky rim
(leakage) flanking the **one clean annulus at the ring** (``ξ = ξ_t``, where *both* densities are zero).
The OSF ring is the defect-free band between two *different* failure modes. (And unlike the void/yield
channel — which needs the stochastic scatter — the dislocation leakage is **deterministic per die**, so
the leaky rim shows directly.) Three panels:

1. **The two-sided window.** Sweeping ξ across ξ_t (via G at fixed V): leakage rises as ξ falls below ξ_t
   (interstitial dislocations), the COP void density rises as ξ rises above it (vacancy voids) — the
   defect-free optimum **at** ξ_t, a cost on *both* sides.
2. **The leakage ladder + the V_t bystander (the isolation).** A clean-feed pull ladder — fast (vacancy,
   baseline leakage) · at ξ_t (clean) · mild slow (in-window) · deep slow (scrap on leakage) — with V_t
   reading the **same** value across all (slow pull makes the diode leaky, not the threshold wrong — the
   consequence net doping cannot carry, exactly G4a→G4b's lesson).
3. **The radial wafer map (the A2 completion).** The radial recipe on a clean line: the void-prone
   vacancy core, the dislocation-leaky rim (× = a leakage scrap), and the **clean OSF-ring annulus**
   between — the one band clean of both.

The dislocation density is the cited Voronkov regime split (the same J. Cryst. Growth 59:625, 1982 as
CG-2), mirror-reflected across ξ_t; the leakage **magnitude** is the flagged loose tier. Triad-tested in
``chip/tests/test_{czochralski,lifetime}.py``; the wiring in ``fab_game/tests/test_dislocation.py``. A
vacancy/boundary growth (or CG-2 off) is the seam (``ρ_disl = 0``, baseline leakage, byte-for-byte).

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_dislocation
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip import lifetime as life
from chip.czochralski import (
    VORONKOV_CRITICAL_RATIO,
    dislocation_defect_density,
    osf_ring_radius,
    radial_defect_regime,
    void_defect_density,
    voronkov_ratio,
)

from .pipeline import diagnose, run_line, wafer_yield
from .recipe import CzochralskiKnobs, Recipe, WaferPrepKnobs
from .spec import DEFAULT_SPECS
from .state import WaferState
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
GRID_N = 5
N_A = 1.0e17                                    # the substrate doping the leakage depletion width reads
XI_T = VORONKOV_CRITICAL_RATIO                  # ξ_t = 0.13 mm²/(K·min) (cited Voronkov)
V_MM_MIN = 1.0                                  # the pull rate the panel-1/2 sweeps hold fixed

# Panel 1 — sweep ξ = V/G across ξ_t via the interface gradient G (cool → hot zone).
G_SWEEP = np.linspace(2.0, 50.0, 60)           # K/mm: ξ from ~0.5 (vacancy) down to ~0.02 (deep interstitial)

# Panel 2 — the clean-feed pull ladder (all at V=1, slice_z=0 so V_t is identical across the ladder).
G_STAR = 1.0 / XI_T                             # ≈7.69 K/mm — ξ = ξ_t exactly (the defect-free optimum)
LADDER = (                                      # (label, G K/mm) — vacancy → optimum → mild slow → deep slow
    ("fast\n(vacancy)", 3.5),                   # ξ ≈ 0.29 > ξ_t — pays on YIELD (panel 1/3), leakage baseline
    ("at ξ_t\n(optimum)", G_STAR),              # ξ = ξ_t — both defects zero (the clean optimum)
    ("mild slow\n(interstitial)", 10.0),        # ξ = 0.10 < ξ_t — dislocations, leakage still in-window
    ("deep slow\n(interstitial)", 20.0),        # ξ = 0.05 ≪ ξ_t — leakage out of spec (scrap)
)

# Panel 3 — the radial recipe (the A2 completion): vacancy core + interstitial rim, ring mid-wafer.
RAD_V, RAD_G_CENTER, RAD_BOOST = 2.0, 5.0, 6.0  # ξ(0)=0.40 > ξ_t > ξ(1)=0.057 → ring ≈ 0.59
RAD_GRID_N = 9

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-a1.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-a1.png"


@dataclass(frozen=True)
class DemoResult:
    """The two-sided window + the leakage ladder (V_t bystander) + the radial wafer map (the A2 completion)."""

    xi_t: float
    v: float
    leak_spec_hi: float
    v_t_lo: float
    v_t_hi: float
    # Panel 1 — the analytic two-sided ξ-sweep:
    xi_of_g: tuple[float, ...]                  # ξ = V/G across the sweep (descending with G)
    leak_of_xi: tuple[float, ...]              # junction leakage (nA/cm²) — rises below ξ_t (dislocations)
    void_of_xi: tuple[float, ...]             # COP void density (cm⁻²) — rises above ξ_t (vacancy)
    # Panel 2 — the clean-feed pull ladder (V_t flat across all — the bystander):
    ladder_labels: tuple[str, ...]
    ladder_xi: tuple[float, ...]
    ladder_regime: tuple[str, ...]
    leak_by_step: tuple[float, ...]            # leakage (nA/cm²) down the ladder
    vt_by_step: tuple[float, ...]             # V_t down the ladder — identical (the point)
    yield_by_step: tuple[float, ...]
    clean_vt: float
    dead_trail: str                            # the deep-slow wafer's failure trail (names the dislocations)
    # Panel 3 — the radial wafer map (the A2 completion):
    ring_radius: float
    zones: tuple[str, str]
    wafer: WaferState
    map_seed: int
    void_density_of_die: tuple[float, ...]     # per-die grown-in void density (the vacancy core)
    leak_of_die: tuple[float, ...]            # per-die junction leakage nA/cm² (the interstitial rim)
    core_dies: int
    rim_dies: int
    rim_leak_failed: int


def _ladder_recipe(g_K_per_mm: float) -> Recipe:
    return Recipe(czochralski=CzochralskiKnobs(pull_rate_mm_min=V_MM_MIN, thermal_gradient_K_per_mm=g_K_per_mm))


def _single_die(g_K_per_mm: float):
    """One representative (uniform) die for a pull recipe — no variation (the growth is the only signal)."""
    return run_line(_ladder_recipe(g_K_per_mm), seed=SEED, variation=NO_VARIATION, grid_n=1).dies[0]


def _ladder_yield(g_K_per_mm: float) -> float:
    w = run_line(_ladder_recipe(g_K_per_mm), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    return wafer_yield(w)


def compute() -> DemoResult:
    """Run the two-sided ξ-sweep, the clean-feed pull ladder, and the radial wafer map (no plotting)."""
    # Panel 1 — the analytic two-sided window (straight from chip.czochralski + chip.lifetime).
    xi_of_g = np.array([voronkov_ratio(V_MM_MIN, g) for g in G_SWEEP])
    leak_of_xi = np.array([
        life.device_leakage(None, N_A=N_A, dislocation_density=dislocation_defect_density(x)).j_leak_nA_cm2
        for x in xi_of_g])
    void_of_xi = np.array([void_defect_density(x) for x in xi_of_g])

    # Panel 2 — the clean-feed pull ladder: leakage climbs on the slow side; V_t is identical throughout.
    ladder_dies = [_single_die(g) for _, g in LADDER]
    ladder_xi = tuple(voronkov_ratio(V_MM_MIN, g) for _, g in LADDER)
    from chip.czochralski import grown_in_defect_regime
    ladder_regime = tuple(grown_in_defect_regime(x) for x in ladder_xi)
    leak_by_step = tuple(d.j_leak_nA_cm2 for d in ladder_dies)
    vt_by_step = tuple(d.V_t for d in ladder_dies)
    yield_by_step = tuple(_ladder_yield(g) for _, g in LADDER)
    dead_wafer = run_line(_ladder_recipe(LADDER[-1][1]), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    dead_trail = diagnose(next(d for d in dead_wafer.dies if d.verdict.failed))

    # Panel 3 — the radial wafer map (the A2 completion): clean line, the growth is the only signal.
    cz = CzochralskiKnobs(pull_rate_mm_min=RAD_V, thermal_gradient_K_per_mm=RAD_G_CENTER,
                          radial_gradient_boost=RAD_BOOST)
    rad = run_line(Recipe(czochralski=cz, wafer_prep=WaferPrepKnobs(defect_density=0.0)),
                   seed=SEED, variation=NO_VARIATION, grid_n=RAD_GRID_N, wafer_id="W_a1")
    ring = osf_ring_radius(RAD_V, RAD_G_CENTER, boost=RAD_BOOST)
    zones = (radial_defect_regime(0.0, RAD_V, RAD_G_CENTER, RAD_BOOST),
             radial_defect_regime(1.0, RAD_V, RAD_G_CENTER, RAD_BOOST))
    void_of_die = tuple(cz.grown_in_defect_density_at(d.radius_frac) for d in rad.dies)
    leak_of_die = tuple((d.j_leak_nA_cm2 if d.j_leak is not None else 0.0) for d in rad.dies)
    rim = [d for d in rad.dies if d.radius_frac >= ring]

    return DemoResult(
        xi_t=XI_T, v=V_MM_MIN, leak_spec_hi=DEFAULT_SPECS.leakage.hi,
        v_t_lo=DEFAULT_SPECS.v_t.lo, v_t_hi=DEFAULT_SPECS.v_t.hi,
        xi_of_g=tuple(float(x) for x in xi_of_g), leak_of_xi=tuple(float(x) for x in leak_of_xi),
        void_of_xi=tuple(float(x) for x in void_of_xi),
        ladder_labels=tuple(lab for lab, _ in LADDER), ladder_xi=ladder_xi, ladder_regime=ladder_regime,
        leak_by_step=leak_by_step, vt_by_step=vt_by_step, yield_by_step=yield_by_step,
        clean_vt=float(_single_die(G_STAR).V_t), dead_trail=dead_trail,
        ring_radius=ring, zones=zones, wafer=rad, map_seed=SEED,
        void_density_of_die=void_of_die, leak_of_die=leak_of_die,
        core_dies=len(rad.dies) - len(rim), rim_dies=len(rim),
        rim_leak_failed=sum(1 for d in rim if d.verdict.failed
                            and any("leakage" in r for r in d.verdict.reasons)),
    )


def print_summary(r: DemoResult) -> None:
    """Print the two-sided window → the leakage ladder → the radial map story — the demo's payoff in text."""
    print("\nCrystal growth A1: the interstitial side of Voronkov — slow pull → dislocations → a leaky diode\n")

    print(f"  1. The TWO-SIDED window (V = {r.v:.1f} mm/min; the defect-free optimum is ξ_t = {r.xi_t:.2f}):")
    for x in (0.02, 0.05, 0.10, r.xi_t, 0.29, 0.45):
        rho = dislocation_defect_density(x)
        leak = life.device_leakage(None, N_A=N_A, dislocation_density=rho).j_leak_nA_cm2
        void = void_defect_density(x)
        if x < r.xi_t:
            tag = f"interstitial → leakage {leak:7.3g} nA/cm²" + ("  [SCRAP]" if leak > r.leak_spec_hi else "")
        elif x > r.xi_t:
            tag = f"vacancy → COP void density {void:.3f} cm⁻² (pays on YIELD)"
        else:
            tag = "← ξ_t: BOTH zero (the defect-free optimum)"
        print(f"     ξ = {x:.2f}:  {tag}")
    print("     → too-fast costs yield (COP), too-slow costs leakage (dislocations); clean only at ξ_t.\n")

    print(f"  2. The leakage ladder — V_t is a bystander (leakage spec ≤ {r.leak_spec_hi:.0f} nA/cm²):")
    print("     pull recipe        ξ       regime         V_t (V)      leakage (nA/cm²)   verdict")
    for lab, xi, reg, vt, lk, y in zip(
            r.ladder_labels, r.ladder_xi, r.ladder_regime, r.vt_by_step, r.leak_by_step, r.yield_by_step):
        lflag = "ok" if lk <= r.leak_spec_hi else "OUT"
        print(f"     {lab.replace(chr(10), ' '):24s} {xi:.3f}  {reg:12s}  {vt:.3f}     "
              f"{lk:10.3g}[{lflag}]   yield {y:.0%}")
    print(f"\n     V_t reads {r.clean_vt:.3f} V across the WHOLE ladder (slow pull leaks the diode, it does")
    print("     not move the threshold — the device consequence net doping cannot carry). The deep-slow scrap:")
    print("     " + r.dead_trail.replace("\n", "\n     ") + "\n")

    print(f"  3. The radial map (the A2 completion) — V={RAD_V}, G_center={RAD_G_CENTER}, boost={RAD_BOOST}:")
    print(f"     OSF ring at r_OSF = {r.ring_radius:.2f};  centre = {r.zones[0]}-rich (COP voids), "
          f"edge = {r.zones[1]}-rich (dislocations)")
    print(f"     → a void-prone vacancy CORE (yield) + a dislocation-leaky RIM ({r.rim_leak_failed}/"
          f"{r.rim_dies} rim dies scrapped on leakage)")
    print(f"     + the CLEAN OSF-RING ANNULUS between (ξ = ξ_t → both densities zero) — the one band clean "
          f"of both.\n")

    print("  Honesty (the repo's bar): realistic CZ is vacancy-side (ξ ≈ 0.29), so A1 is a CORNER — its")
    print("  value is the criterion's SYMMETRY (slow pull is no longer free) + A2's rim, not a main-line")
    print("  trade-off. TIGHT = the ξ_t flip (by-construction); FLAGGED = the leakage depth. No engine, no")
    print("  conservation law (CG-2's tier).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the A1 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import dislocation_figure

    fig = dislocation_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # ξ, →, ≈, ² on legacy codepages

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
