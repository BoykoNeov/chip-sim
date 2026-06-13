"""The G6 banked artifact: the back end — assembly-yield funnel + speed binning (sand → binned chip).

The fab-line game's sixth demonstrable thing (plan §6 G6, §5 step 9). G1–G5 carried a wafer from the
boule through the front end to a *tested* die map (pass/fail at wafer sort); **G6 runs the back end** —
*dice → die-attach → wire-bond → encapsulate → final test → bin* — the last leg of "sand to a binned,
packaged chip." Three things shown, the cited funnel + the binning + the full outcome:

1. **The assembly-yield funnel (the cited physics).** A packaged part must survive **every** back-end
   operation, so the assembly yield is the **product** of the per-step survival yields
   (:func:`chip.packaging.assembly_yield` — the cumulative funnel). Degrade the busiest step (the
   wire-bond) and the funnel narrows step-by-step; the realized per-die survival hugs the cited product
   ``Π yᵢ`` (the convergence proven in ``fab_game/tests/test_packaging.py``).

2. **Speed binning (the value distribution).** Working parts are sorted by drive current (``I_Dsat`` as
   a **speed proxy** — clock speed ∝ drive current) into value grades. The pedagogy is **process
   control**: a *tight* process (good CD control) puts almost everything in the premium bin; a *loose*
   one (poor line-width control) spreads the drive current across grades and spills a tail **out** the
   bottom — a **bin-out** (a working but too-slow part that does not ship). Binning is a house grading
   policy (ADR 0005 §1), so it lives in the game layer; only the partition is asserted.

3. **The packaged wafer (the full outcome).** One wafer's die map colored by final outcome —
   premium / typical / value grades, plus the three ways to die (front-end fail, back-end **assembly
   scrap**, final-test **bin-out**) — with the failure trail naming a back-end death (a part with a
   perfect front end that still never shipped). The "sand → binned chip" payoff.

The assembly funnel is cited + triad-tested (``chip/tests/test_packaging.py``); the per-step yields, the
bin edges, and the process σ's are **flagged house numbers**; the wiring (the stochastic assembly kill,
the binning partition) is the game-layer mechanics invariant (``fab_game/tests/test_packaging.py``).
Default knobs (perfect assembly, one open bin) are the seam.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_packaging
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from chip import packaging as pkg

from .pipeline import diagnose, run_line
from .recipe import PackagingKnobs, Recipe
from .spec import DEFAULT_SPECS, SpeedBin, SpeedBins
from .state import WaferState
from .variation import NO_VARIATION, Variation

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
GRID_N = 11                                       # a big die map (~95 dies) → a real I_Dsat sample for the histogram

# A back end with a degraded wire-bond (the busiest, lossiest step) — a visible funnel narrowing.
FUNNEL_KNOBS = PackagingKnobs(dice_yield=0.995, attach_yield=0.997, bond_yield=0.85, encapsulate_yield=0.998)

# The process-control contrast: tight vs loose CD control (line-width roughness on the printed CD).
TIGHT_SIGMA = 1.5                                 # nm — the default well-controlled process
LOOSE_SIGMA = 7.0                                 # nm — a poorly-controlled process (wide I_Dsat spread)

# Speed bins on I_Dsat (mA), house grades around the nominal ~3.30 mA part (nominal → "typical").
SPEED_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=3.38),              # fast — the highest-drive parts
    SpeedBin("typical", lo_mA=3.21, hi_mA=3.38),  # the nominal grade
    SpeedBin("value", lo_mA=3.10, hi_mA=3.21),    # slow — still sellable
))                                                # < 3.10 mA → reject (too slow to sell — a bin-out)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g6.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g6.png"


@dataclass(frozen=True)
class DemoResult:
    """The assembly funnel + the tight/loose bin histograms + the packaged outcome map — the bundle."""

    # 1. The funnel — the cumulative assembly yield, step by step, + the realized single-wafer point.
    funnel_labels: tuple[str, ...]                # ["front-end good", "+ dice", "+ attach", …]
    funnel_cumulative: tuple[float, ...]          # the cited running product Π (as a fraction)
    funnel_n_front_end: int                       # front-end-good dies entering the back end
    funnel_n_packaged: int                        # dies that survived assembly (realized)
    funnel_assembly_yield: float                  # the cited Π yᵢ
    funnel_empirical: float                        # the realized survivors / front-end-good
    # 2. The bin histograms — tight vs loose process (perfect assembly, isolate binning).
    bin_labels: tuple[str, ...]                   # the grade labels + "reject"
    tight_sigma: float
    loose_sigma: float
    tight_idsat: tuple[float, ...]                # the I_Dsat (mA) sample, tight process
    loose_idsat: tuple[float, ...]                # the I_Dsat (mA) sample, loose process
    tight_hist: dict                              # bin label → count, tight process
    loose_hist: dict                              # bin label → count, loose process
    bin_edges_mA: tuple[float, ...]               # the sellable-bin edges drawn on the histogram
    # 3. The packaged outcome map (loose process + degraded bond) + a back-end death's trail.
    outcome_wafer: WaferState
    dead_trail: str


def _bin_recipe(cd_sigma_nm: float, packaging: PackagingKnobs = PackagingKnobs()) -> tuple[Recipe, Variation]:
    """A recipe + variation for the binning runs: a given CD-control σ (process tightness), given back end."""
    return Recipe(packaging=packaging), Variation(cd_sigma_nm=cd_sigma_nm)


def compute() -> DemoResult:
    """Run the assembly funnel, the tight/loose binning, and the packaged outcome map (no plotting)."""
    specs = replace(DEFAULT_SPECS, speed_bins=SPEED_BINS)

    # 1. The funnel — a tight-process wafer (front-end ~all good) with the degraded back end. The cited
    #    cumulative product narrows step by step; the realized survivors hug Π yᵢ.
    recipe, var = _bin_recipe(TIGHT_SIGMA, packaging=FUNNEL_KNOBS)
    funnel_wafer = run_line(recipe, seed=SEED, variation=var, specs=specs, grid_n=GRID_N)
    n_front_end = sum(d.assembled is not None for d in funnel_wafer.dies)   # dies that entered the back end
    n_packaged = sum(d.assembled is True for d in funnel_wafer.dies)
    steps = (("dice", FUNNEL_KNOBS.dice_yield), ("attach", FUNNEL_KNOBS.attach_yield),
             ("bond", FUNNEL_KNOBS.bond_yield), ("encapsulate", FUNNEL_KNOBS.encapsulate_yield))
    labels = ["front-end\ngood"]
    cumulative = [1.0]
    running = 1.0
    for name, y in steps:
        running *= y
        labels.append(f"+ {name}")
        cumulative.append(running)
    Y = pkg.assembly_yield(*FUNNEL_KNOBS.step_yields)

    # 2. Binning — tight vs loose process (perfect assembly, so the histogram is the binning alone).
    def _bin_run(sigma: float):
        rcp, v = _bin_recipe(sigma)                            # perfect default packaging
        w = run_line(rcp, seed=SEED, variation=v, specs=specs, grid_n=GRID_N)
        idsat = tuple(d.i_dsat_mA for d in w.dies if d.i_dsat_mA is not None)
        hist = {label: 0 for label in SPEED_BINS.labels}
        for d in w.dies:
            if d.bin is not None:
                hist[d.bin] = hist.get(d.bin, 0) + 1
        return idsat, hist

    tight_idsat, tight_hist = _bin_run(TIGHT_SIGMA)
    loose_idsat, loose_hist = _bin_run(LOOSE_SIGMA)

    # 3. The packaged outcome map — a loose process AND the degraded back end (every outcome present).
    recipe3, var3 = _bin_recipe(LOOSE_SIGMA, packaging=FUNNEL_KNOBS)
    outcome_wafer = run_line(recipe3, seed=SEED, variation=var3, specs=specs, grid_n=GRID_N)
    dead = next((d for d in outcome_wafer.dies if d.assembled is False), None)
    if dead is None:                                            # fall back to a bin-out if no scrap landed
        dead = next((d for d in outcome_wafer.dies if d.bin == "reject"), outcome_wafer.dies[0])
    dead_trail = diagnose(dead)

    bin_edges = tuple(b.lo_mA for b in SPEED_BINS.bins if b.lo_mA is not None)
    return DemoResult(
        funnel_labels=tuple(labels), funnel_cumulative=tuple(cumulative),
        funnel_n_front_end=n_front_end, funnel_n_packaged=n_packaged,
        funnel_assembly_yield=Y, funnel_empirical=n_packaged / n_front_end if n_front_end else 0.0,
        bin_labels=SPEED_BINS.labels, tight_sigma=TIGHT_SIGMA, loose_sigma=LOOSE_SIGMA,
        tight_idsat=tight_idsat, loose_idsat=loose_idsat,
        tight_hist=tight_hist, loose_hist=loose_hist, bin_edges_mA=bin_edges,
        outcome_wafer=outcome_wafer, dead_trail=dead_trail,
    )


def print_summary(r: DemoResult) -> None:
    """Print the funnel → binning → packaged-outcome story — the demo's payoff in text."""
    print("\nThe fab line (G6): the back end — assembly-yield funnel + speed binning (sand → binned chip)\n")

    print(f"  1. The assembly-yield funnel — a part must survive every step (cited Π yᵢ):")
    for label, cum in zip(r.funnel_labels, r.funnel_cumulative):
        bar = "█" * int(round(cum * 40))
        print(f"     {label.replace(chr(10), ' '):16s} {cum:6.1%}  {bar}")
    print(f"     → cited assembly yield Π yᵢ = {r.funnel_assembly_yield:.1%}; realized this wafer "
          f"{r.funnel_n_packaged}/{r.funnel_n_front_end} = {r.funnel_empirical:.1%} "
          f"(the wire-bond is the narrow neck).\n")

    print(f"  2. Speed binning — drive current sorts working parts into value grades "
          f"(bins: {', '.join(b for b in r.bin_labels)}):")
    print(f"     process control     " + "  ".join(f"{lab:>8s}" for lab in r.bin_labels))
    for tag, hist in (("tight (σ=%.0f nm)" % r.tight_sigma, r.tight_hist),
                      ("loose (σ=%.0f nm)" % r.loose_sigma, r.loose_hist)):
        print(f"     {tag:18s}  " + "  ".join(f"{hist[lab]:8d}" for lab in r.bin_labels))
    print("     → a tight process fills the premium bin; a loose one spreads the grades and bins a tail")
    print("       OUT the bottom (working, but too slow to sell) — process control is the bin mix.\n")

    print("  3. The packaged wafer (loose process + a degraded bond) — every outcome on one map:")
    print("     " + r.dead_trail.replace("\n", "\n     ") + "\n")
    print("  New: the cited cumulative assembly-yield funnel (chip.packaging, triad-tested); the binning")
    print("  partition + the stochastic back-end kill are the game layer. Default knobs = the seam.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the G6 packaging artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import packaging_figure

    fig = packaging_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ², µ, →, █ on legacy codepages

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
