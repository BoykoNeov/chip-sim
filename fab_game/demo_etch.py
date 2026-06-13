"""The G5 banked artifact: the mid-line etch/deposition step — CD transfer, voids, and rework.

The fab-line game's fifth demonstrable thing (plan §6 G5, §5 step 7). G1–G4 built the harness, the
boule, the physical die map, and the contamination consequence; **G5 fills the missing mid-line
operations between litho and the device** — *the etch that transfers the printed pattern into the gate,
and the deposition that fills the gaps* — phenomenological but honest (the plan's flagged tier). Three
things shown, the two named failure modes (over-etch; non-conformal step coverage) + the rework:

1. **Etch bias — over-etch shrinks the gate CD (the parametric failure).** A real etch is *directional*
   but not perfectly so: with anisotropy ``A < 1`` it undercuts the mask, and the **over-etch** needed
   to clear residue deepens the etch and *widens* the undercut → the transferred gate CD shrinks below
   the printed CD → a shorter channel → ``I_Dsat ∝ W/L`` rises over its ceiling and the CD drops out
   the bottom of its window. A perfectly anisotropic etch (``A = 1``) is the seam (zero bias).

2. **Deposition step coverage — a non-conformal fill voids the gate gap (the functional failure).** The
   gap between gate lines (``pitch − CD``, aspect ratio ``gate-height / gap``) must be filled by a
   later deposition; a poor line-of-sight **PVD** (step coverage ≈ 0.3) pinches off at the top and
   seals a **keyhole void** where a conformal **CVD** (≈ 0.9) fills cleanly — a *functional* kill (the
   die's V_t/I_Dsat may read fine), distinct from the parametric etch story.

3. **Rework — the reworkable / irreversible contrast.** A deposition void is **strippable**: re-deposit
   the voided dies more conformally and they recover. The etch is **irreversible**: a die whose CD was
   collapsed by over-etch stays dead even after a perfect re-fill (you cannot un-etch the gate). The
   plan's "depo sometimes strippable; over-etch irreversible."

The etch-bias / void physics is cited (forms) + triad-tested (``chip/tests/test_etch_deposition.py``);
the magnitudes (anisotropy, step coverage, the pinch-off aspect ratio) are flagged house numbers; the
wiring is the game-layer mechanics invariant (``fab_game/tests/test_etch.py``). Default knobs (perfectly
anisotropic, conformal) are the seam.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_etch
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip import etch_deposition as ed

from .pipeline import diagnose, rework_deposition, run_line, wafer_yield
from .recipe import EtchDepositionKnobs, Recipe
from .spec import DEFAULT_SPECS
from .state import WaferState
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
GRID_N = 5
PITCH_NM = 300.0                                  # the gate pitch (DEFAULT_RECIPE litho) → gap = pitch − CD
FILM_NM = 150.0                                   # the gate film etched through (sets the gate height)
OVER_ETCH = tuple(float(x) for x in np.linspace(0.0, 1.0, 11))   # the over-etch sweep
ETCH_CURVES = (1.0, 0.95, 0.88)                   # anisotropies: ideal (seam) / a good RIE / a poor plasma
RIE = 0.9                                          # the anisotropy the over-etch dead-wafer scenario uses
PVD = ed.STEP_COVERAGE["PVD"]                      # 0.3 — the voiding step coverage
CVD = ed.STEP_COVERAGE["CVD"]                      # 0.9 — the conformal rework coverage

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-g5.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-g5.png"


@dataclass(frozen=True)
class DemoResult:
    """The etch-bias CD sweep + the void map + the reworkable/irreversible rework — the bundle."""

    # 1. Etch bias — CD (and I_Dsat) vs over-etch, per anisotropy curve (single die, no variation).
    over_etch: tuple[float, ...]
    etch_curves: tuple[float, ...]                # the anisotropies plotted
    cd_by_aniso: dict[float, tuple[float, ...]]   # anisotropy → CD(nm) vs over_etch
    idsat_by_aniso: dict[float, tuple[float, ...]]  # anisotropy → I_Dsat(mA) vs over_etch
    cd_lo: float
    cd_hi: float
    idsat_hi: float
    # 2. Deposition void — the AR_crit(SC) curve + the gate gap + the CVD/PVD points.
    step_coverages: tuple[float, ...]
    ar_crit_curve: tuple[float, ...]
    gate_gap_ar: float
    pvd_sc: float
    cvd_sc: float
    pvd_ar_crit: float                            # max void-free AR at PVD coverage (below the gap → voids)
    cvd_ar_crit: float                            # max void-free AR at CVD coverage (above the gap → fills)
    pvd_voids: bool
    cvd_voids: bool
    # 3. Rework — the void (reworkable) vs over-etch (irreversible) yields.
    void_yield_before: float
    void_yield_after: float
    overetch_yield_before: float
    overetch_yield_after: float
    # The dead wafers + their failure trails.
    void_wafer: WaferState
    void_trail: str
    overetch_wafer: WaferState
    overetch_trail: str


def _single_die(recipe: Recipe):
    """The centre die of a nominal, no-variation run of ``recipe`` (the representative die)."""
    return run_line(recipe, seed=SEED, variation=NO_VARIATION, grid_n=1).dies[0]


def _etch_recipe(anisotropy: float = 1.0, over_etch_frac: float = 0.0, conformality: float = 1.0) -> Recipe:
    return Recipe(etch_deposition=EtchDepositionKnobs(
        film_thickness_nm=FILM_NM, anisotropy=anisotropy,
        over_etch_frac=over_etch_frac, conformality=conformality))


def compute() -> DemoResult:
    """Run the etch-bias sweep, the void map, and the reworkable/irreversible rework (no plotting)."""
    # 1. Etch bias: CD + I_Dsat vs over-etch, for each anisotropy curve.
    cd_by_aniso: dict[float, tuple[float, ...]] = {}
    idsat_by_aniso: dict[float, tuple[float, ...]] = {}
    for A in ETCH_CURVES:
        cds, ids = [], []
        for oe in OVER_ETCH:
            d = _single_die(_etch_recipe(anisotropy=A, over_etch_frac=oe))
            cds.append(float(d.cd_nm))
            ids.append(float(d.i_dsat_mA))
        cd_by_aniso[A] = tuple(cds)
        idsat_by_aniso[A] = tuple(ids)

    # 2. Deposition void: the max void-free aspect ratio vs step coverage + the gate-gap AR.
    scs = tuple(float(x) for x in np.linspace(0.05, 0.97, 40))
    ar_crit = tuple(float(ed.critical_aspect_ratio(s)) for s in scs)
    nominal_cd = float(_single_die(_etch_recipe()).cd_nm)              # the seam CD (≈167 nm)
    gate_gap_ar = float(ed.gap_aspect_ratio(FILM_NM, PITCH_NM, nominal_cd))
    pvd = ed.deposit_fill(FILM_NM, PITCH_NM, nominal_cd, step_coverage=PVD)
    cvd = ed.deposit_fill(FILM_NM, PITCH_NM, nominal_cd, step_coverage=CVD)

    # 3. Rework: a PVD-voided wafer (recovers) vs an over-etched wafer (irreversible).
    void_wafer = run_line(_etch_recipe(conformality=PVD), seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    void_reworked = rework_deposition(void_wafer, conformality=CVD)
    overetch_wafer = run_line(_etch_recipe(anisotropy=RIE, over_etch_frac=0.8),
                              seed=SEED, variation=NO_VARIATION, grid_n=GRID_N)
    overetch_reworked = rework_deposition(overetch_wafer, conformality=CVD)

    void_dead = next(d for d in void_wafer.dies if d.verdict.failed)
    overetch_dead = next(d for d in overetch_wafer.dies if d.verdict.failed)

    return DemoResult(
        over_etch=OVER_ETCH, etch_curves=ETCH_CURVES,
        cd_by_aniso=cd_by_aniso, idsat_by_aniso=idsat_by_aniso,
        cd_lo=DEFAULT_SPECS.cd_nm.lo, cd_hi=DEFAULT_SPECS.cd_nm.hi, idsat_hi=DEFAULT_SPECS.i_dsat_mA.hi,
        step_coverages=scs, ar_crit_curve=ar_crit, gate_gap_ar=gate_gap_ar,
        pvd_sc=PVD, cvd_sc=CVD, pvd_ar_crit=pvd.critical_aspect_ratio,
        cvd_ar_crit=cvd.critical_aspect_ratio, pvd_voids=pvd.voided, cvd_voids=cvd.voided,
        void_yield_before=wafer_yield(void_wafer), void_yield_after=wafer_yield(void_reworked),
        overetch_yield_before=wafer_yield(overetch_wafer),
        overetch_yield_after=wafer_yield(overetch_reworked),
        void_wafer=void_wafer, void_trail=diagnose(void_dead),
        overetch_wafer=overetch_wafer, overetch_trail=diagnose(overetch_dead),
    )


def print_summary(r: DemoResult) -> None:
    """Print the etch-bias → void → rework story — the demo's payoff in text."""
    print("\nThe fab line (G5): the mid-line etch & deposition — CD transfer, voids, and rework\n")

    print(f"  1. Etch bias — over-etch shrinks the gate CD (spec CD ∈ [{r.cd_lo:.0f}, {r.cd_hi:.0f}] nm):")
    print("     over-etch:     " + "  ".join(f"{oe:4.1f}" for oe in r.over_etch))
    for A in r.etch_curves:
        tag = "ideal (seam)" if A == 1.0 else f"A={A:.2f}"
        print(f"     CD {tag:12s}: " + "  ".join(f"{cd:4.0f}" for cd in r.cd_by_aniso[A]))
    print("     → a perfectly anisotropic etch (A=1) is flat at the printed CD; a real etch undercuts,")
    print("       and over-etching to clear residue walks the CD out the bottom (shorter L → I_Dsat ↑).\n")

    fill = lambda v: "VOIDS" if v else "fills"
    print("  2. Deposition step coverage — fill the gate gap or pinch off a void:")
    print(f"     gate-gap aspect ratio ≈ {r.gate_gap_ar:.2f}  (gate height {FILM_NM:.0f} nm / gap)")
    print(f"     PVD  (coverage {r.pvd_sc:.2f}): max void-free AR {ed.critical_aspect_ratio(r.pvd_sc):.2f} "
          f"→ {fill(r.pvd_voids)}")
    print(f"     CVD  (coverage {r.cvd_sc:.2f}): max void-free AR {ed.critical_aspect_ratio(r.cvd_sc):.2f} "
          f"→ {fill(r.cvd_voids)}")
    print("     → the poor PVD voids the same gap the conformal CVD fills (a functional kill):")
    print("     " + r.void_trail.replace("\n", "\n     ") + "\n")

    print("  3. Rework — a depo void is strippable; an over-etched CD is irreversible:")
    print(f"     PVD void wafer : yield {r.void_yield_before:.0%} → re-deposit (CVD) → "
          f"{r.void_yield_after:.0%}   (recovered)")
    print(f"     over-etch wafer: yield {r.overetch_yield_before:.0%} → re-deposit (CVD) → "
          f"{r.overetch_yield_after:.0%}   (the etch cannot be undone)")
    print("     " + r.overetch_trail.replace("\n", "\n     ") + "\n")
    print("  New: the cited etch-bias + step-coverage forms (chip.etch_deposition, triad-tested),")
    print("  flagged magnitudes. The etched CD → device, the void → functional kill: the game layer.\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the G5 etch/deposition artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import etch_figure

    fig = etch_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # °C, ², µ, → on legacy codepages

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
