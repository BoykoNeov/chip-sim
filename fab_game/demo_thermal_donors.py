"""The C1 banked artifact: crucible oxygen → thermal donors → the substrate's ELECTRICAL drift.

The crystal-growth deepening on the **electrical** axis (the scope-edge backlog C1), a G2/CG follow-on.
CG-1/2/3 deepened the boule on the *doping-profile* (Scheil k_eff), *defect* (Voronkov), and *interface*
(Stefan) axes; this one adds the missing **electrical** consequence of **crucible oxygen**. A Czochralski
boule dissolves interstitial oxygen ``[O_i]`` from the quartz crucible, and a low-temperature **~450 °C
donor anneal** nucleates **thermal donors** — n-type oxygen clusters that **compensate** the p-type
boron substrate, dropping the net doping → a lower ``V_t`` (and a higher resistivity). It rides the same
**net-doping → V_t** chain as the G4a residual-dopant story (a contaminant net doping *can* carry).

The honesty ladder (the repo's bar): the one **cited** claim is the **Kaiser–Frisch–Reiss (Phys. Rev.
112, 1546, 1958) fourth-power initial rate** ``dN_TD/dt|₀ ∝ [O_i]⁴``; the saturating form, the cube-law
saturation, and **every magnitude** are flagged house numbers (ADR 0005 §5). Three panels:

1. **The kinetics (N_TD vs anneal time at three oxygen levels).** Saturating exponentials rising from 0
   (no anneal — the seam) toward the (flagged) ceiling; more oxygen → faster *and* higher (the steep
   cube-law saturation). The initial slope carries the cited fourth power (panel 3).
2. **The consequence (V_t vs anneal time, the real pipeline) with the spec window.** The donors
   compensate the substrate down, so ``V_t`` walks **down** with anneal time; a **high**-oxygen boule
   exits the **bottom** of its window (a scrap), a **typical** one only dips, a **low** one barely moves
   — without inverting the type (the demo stays p-type; over-compensation is a guarded named edge).
3. **The cited power laws (log–log vs [O_i]).** The **initial formation rate ∝ [O_i]⁴** (the cited KFR
   fourth power — a four-oxygen donor core) and the **saturation ceiling ∝ [O_i]³** (the flagged cube
   law): two clean power-law slopes, the signature that *oxygen control matters* steeply.

This is the **physics consequence**, not a strategy/score (like the CG demos): the lever is "control the
crucible oxygen / the donor anneal," and the cost is a substrate that drifts n-ward. Opt-in and
seam-safe — no oxygen or no anneal ⇒ ``N_TD = 0`` exactly ⇒ the G1–G7 banked demos byte-for-byte unchanged.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_thermal_donors
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.czochralski import (
    OXYGEN_BANDS,
    TD_OXYGEN_REFERENCE_CM3,
    TD_RATE_OXYGEN_EXPONENT,
    TD_SAT_OXYGEN_EXPONENT,
    thermal_donor_density,
    thermal_donor_formation_rate,
    thermal_donor_saturation,
)

from .pipeline import run_line, wafer_yield
from .recipe import CzochralskiKnobs, Recipe
from .spec import DEFAULT_SPECS
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
SUBSTRATE_N_A = 1.0e17                              # the boron substrate the donors compensate (= N_seed)
# The representative incorporated-oxygen levels (the cited band, excluding the seam "none").
DEMO_OXYGEN: tuple[tuple[str, float], ...] = (
    ("low", OXYGEN_BANDS["low"]),
    ("typical", OXYGEN_BANDS["typical"]),
    ("high", OXYGEN_BANDS["high"]),
)
ANNEAL_SWEEP_MIN = tuple(float(t) for t in np.linspace(0.0, 360.0, 13))   # the V_t / yield pipeline points
ANNEAL_FINE_MIN = tuple(float(t) for t in np.linspace(0.0, 360.0, 80))    # the smooth N_TD kinetics curves
OXYGEN_SWEEP_CM3 = tuple(float(o) for o in np.logspace(17.0, 18.2, 60))   # the log–log power-law panel

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-c1.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-c1.png"


@dataclass(frozen=True)
class DemoResult:
    """The donor kinetics + the V_t walk down the anneal + the cited power laws (no score)."""

    substrate_N_A: float
    oxygen_labels: tuple[str, ...]
    oxygen_levels: tuple[float, ...]
    # Panel 1 — the kinetics N_TD(t):
    anneal_fine: tuple[float, ...]
    n_td_by_oxygen: dict                            # label → N_TD(t) (cm⁻³) over anneal_fine
    saturation_by_oxygen: dict                      # label → N_sat (the flagged ceiling) per oxygen level
    # Panel 2 — the consequence V_t(t) (the real pipeline) + yield:
    anneal_sweep: tuple[float, ...]
    vt_by_oxygen: dict                              # label → V_t(t) down the anneal (the pipeline)
    yield_by_oxygen: dict                           # label → wafer yield(t)
    v_t_lo: float
    v_t_hi: float
    # Panel 3 — the cited power laws (log–log vs [O_i]):
    oxygen_sweep: tuple[float, ...]
    formation_rate_sweep: tuple[float, ...]         # dN_TD/dt|₀ ∝ [O_i]⁴ (the cited KFR fourth power)
    saturation_sweep: tuple[float, ...]             # N_sat ∝ [O_i]³ (the flagged cube law)
    rate_exponent: float
    sat_exponent: float
    oxygen_ref: float


def _recipe(oxygen: float, anneal_min: float) -> Recipe:
    return Recipe(czochralski=CzochralskiKnobs(
        N_seed=SUBSTRATE_N_A, oxygen_conc_cm3=oxygen, thermal_donor_anneal_min=anneal_min))


def compute() -> DemoResult:
    """Build the donor kinetics, the V_t walk down the anneal (real pipeline), and the cited power laws."""
    t_fine = np.asarray(ANNEAL_FINE_MIN)
    n_td_by_oxygen: dict = {}
    saturation_by_oxygen: dict = {}
    vt_by_oxygen: dict = {}
    yield_by_oxygen: dict = {}
    for label, O in DEMO_OXYGEN:
        n_td_by_oxygen[label] = tuple(float(thermal_donor_density(O, t)) for t in t_fine)
        saturation_by_oxygen[label] = float(thermal_donor_saturation(O))
        vts, ys = [], []
        for t in ANNEAL_SWEEP_MIN:
            w = run_line(_recipe(O, t), seed=SEED, variation=NO_VARIATION, grid_n=1)
            vts.append(float(w.dies[0].V_t))
            ys.append(wafer_yield(w))
        vt_by_oxygen[label] = tuple(vts)
        yield_by_oxygen[label] = tuple(ys)

    rate_sweep = tuple(float(thermal_donor_formation_rate(o)) for o in OXYGEN_SWEEP_CM3)
    sat_sweep = tuple(float(thermal_donor_saturation(o)) for o in OXYGEN_SWEEP_CM3)
    return DemoResult(
        substrate_N_A=SUBSTRATE_N_A,
        oxygen_labels=tuple(lab for lab, _ in DEMO_OXYGEN),
        oxygen_levels=tuple(O for _, O in DEMO_OXYGEN),
        anneal_fine=ANNEAL_FINE_MIN, n_td_by_oxygen=n_td_by_oxygen,
        saturation_by_oxygen=saturation_by_oxygen,
        anneal_sweep=ANNEAL_SWEEP_MIN, vt_by_oxygen=vt_by_oxygen, yield_by_oxygen=yield_by_oxygen,
        v_t_lo=DEFAULT_SPECS.v_t.lo, v_t_hi=DEFAULT_SPECS.v_t.hi,
        oxygen_sweep=OXYGEN_SWEEP_CM3, formation_rate_sweep=rate_sweep, saturation_sweep=sat_sweep,
        rate_exponent=TD_RATE_OXYGEN_EXPONENT, sat_exponent=TD_SAT_OXYGEN_EXPONENT,
        oxygen_ref=TD_OXYGEN_REFERENCE_CM3,
    )


def print_summary(r: DemoResult) -> None:
    """Print the kinetics → V_t walk → cited power-law story — the demo's payoff in text (no score)."""
    print("\nCrystal growth C1: crucible oxygen → thermal donors → the substrate's electrical drift\n")

    print(f"  Thermal donors (Kaiser–Frisch–Reiss, Phys. Rev. 112, 1546, 1958): a ~450 °C anneal nucleates")
    print(f"  oxygen-cluster donors that COMPENSATE the p-substrate (N_A={r.substrate_N_A:.0e} cm⁻³) → V_t down.\n")

    print(f"  Saturation thermal-donor density N_sat (flagged cube law ∝[O_i]³):")
    for label, O in zip(r.oxygen_labels, r.oxygen_levels):
        print(f"     [O_i]={O:.1e} ({label:7s}): N_sat ≈ {r.saturation_by_oxygen[label]:.2e} cm⁻³")

    print(f"\n  V_t down the ~450 °C anneal (spec [{r.v_t_lo:.2f}, {r.v_t_hi:.2f}] V), real pipeline:")
    print(f"     {'anneal (min)':>12}" + "".join(f"  {lab:>10}" for lab in r.oxygen_labels))
    for i, t in enumerate(r.anneal_sweep):
        if t in (0.0, 120.0, 240.0, 360.0):
            row = "".join(f"  {r.vt_by_oxygen[lab][i]:>10.3f}" for lab in r.oxygen_labels)
            print(f"     {t:>12.0f}{row}")
    finals = {lab: r.yield_by_oxygen[lab][-1] for lab in r.oxygen_labels}
    print(f"  → at the longest anneal: " + ", ".join(
        f"{lab} yield {finals[lab]:.0%}" for lab in r.oxygen_labels))
    print(f"     no oxygen OR no anneal ⇒ N_TD=0 exactly (the seam); a HIGH-oxygen boule walks V_t out the")
    print(f"     bottom of its window (a scrap), a typical one only dips — all staying p-type.\n")

    print(f"  The cited power laws (log–log vs [O_i], ref {r.oxygen_ref:.0e}):")
    print(f"     initial formation rate ∝ [O_i]^{r.rate_exponent:.0f}  (the CITED KFR fourth power — a four-oxygen core)")
    print(f"     saturation ceiling     ∝ [O_i]^{r.sat_exponent:.0f}  (the FLAGGED cube law)")
    print(f"  → oxygen control matters STEEPLY; only the fourth-power rate is cited, the rest is house.\n")

    print("  New: the cited KFR fourth-power kinetics (chip.czochralski, triad-tested); the oxygen +")
    print("  donor-anneal knobs are opt-in (default = no donors → the G1–G7 banked demos byte-for-byte unchanged).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the C1 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import thermal_donor_figure

    fig = thermal_donor_figure(r)
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
