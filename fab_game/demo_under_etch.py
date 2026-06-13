"""The D1 banked artifact: under-etch → residual film → a bridging short (the etch process window).

The mid-line etch deepening that closes G5's named "over/under-etch" pair (the scope-edge backlog D1).
G5 ([[fab-game-g5]]) built the **over**-etch leg (etch past endpoint → undercut → the gate CD collapses,
a parametric/**open** failure) and named under-etch as the unbuilt mirror. D1 builds it: an **incomplete
clear** (``under_etch_frac > 0`` — a slow etch, an early endpoint, a thick non-uniform film) leaves
**residual film** (``residual = UE·film``) in the gaps between gate lines; once the residual exceeds a
(flagged) thickness it forms a continuous conductive stringer that **bridges** adjacent lines into a
functional **short** — the mirror of the deposition void's open. Same flagged-phenomenology tier as G5:
the *forms* are cited (Wolf & Tauber; Plummer–Deal–Griffin), the bridge-threshold *magnitude* is house.

Three panels:

1. **The residual (residual vs under-etch fraction, per film thickness).** A line through the origin
   (UE=0 ⇒ residual 0, the seam) with the (flagged) bridge threshold drawn: a thin residual is
   discontinuous / cleared by the over-etch margin (harmless), a thick one shorts the lines.
2. **The bridging cliff (yield vs under-etch fraction, the real pipeline).** With the CD untouched
   (under-etch is a *functional* kill, not a CD shift), the yield steps 100 % → 0 % the moment the
   residual crosses the bridge threshold — a clean functional cliff (parallel to the deposition void).
3. **The etch process window (yield vs the signed etch axis).** The payoff of having *both* legs: too
   little etch (left) bridges into a **short**, too much (right, at a real anisotropy) collapses the CD
   into an **open** — a Goldilocks **window** in between. Endpoint control is bracketed by a short and
   an open; that bracketing is *why* over-etch margin exists (and why too much of it is its own failure).

The **physics consequence**, not a strategy/score (like the G5 demo): the lever is "etch to completion
(with margin), but not so far the CD collapses." Opt-in and seam-safe — ``under_etch_frac = 0`` ⇒ no
residual, nothing bridges ⇒ the G1–G6 banked demos byte-for-byte unchanged.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_under_etch
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chip.etch_deposition import BRIDGE_RESIDUAL_THRESHOLD_NM, under_etch_residual

from .pipeline import run_line, wafer_yield
from .recipe import EtchDepositionKnobs, Recipe
from .spec import DEFAULT_SPECS
from .variation import NO_VARIATION

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
BRIDGE_THRESHOLD_NM = BRIDGE_RESIDUAL_THRESHOLD_NM             # the flagged short threshold (cited direction)
DEMO_FILMS_NM = (100.0, 150.0, 220.0)                          # representative gate-film thicknesses (panel 1)
UE_SWEEP = tuple(float(u) for u in np.linspace(0.0, 0.5, 26))  # the under-etch fraction sweep (panels 1/2)
NOMINAL_FILM_NM = 150.0                                        # the pipeline film (G5 default — the bridge cliff)
# Panel 3 — the process window: a signed etch axis (under-etch < 0, over-etch > 0) at a near-ideal
# anisotropy chosen so endpoint is in spec but a large over-etch collapses the CD (a real RIE-ish etch).
PROCESS_WINDOW_ANISOTROPY = 0.96
ETCH_AXIS = tuple(float(x) for x in np.linspace(-0.4, 0.8, 49))   # x<0 → under-etch UE=−x; x>0 → over-etch

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-d1.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-d1.png"


@dataclass(frozen=True)
class DemoResult:
    """The residual curve + the bridging cliff + the etch process window (no score)."""

    bridge_threshold_nm: float
    cd_lo: float
    cd_hi: float
    # Panel 1 — residual vs UE per film:
    films_nm: tuple[float, ...]
    ue_sweep: tuple[float, ...]
    residual_by_film: dict                          # film → residual(UE) (nm)
    # Panel 2 — the bridging cliff (yield vs UE, the pipeline):
    nominal_film_nm: float
    yield_vs_ue: tuple[float, ...]
    cd_vs_ue: tuple[float, ...]                      # CD is flat (under-etch is a functional, not CD, kill)
    ue_bridge_onset: float                          # the UE where the residual first crosses the threshold
    # Panel 3 — the etch process window (yield vs the signed etch axis):
    process_anisotropy: float
    etch_axis: tuple[float, ...]
    yield_vs_etch: tuple[float, ...]
    cd_vs_etch: tuple[float, ...]
    bridged_vs_etch: tuple[bool, ...]
    window_lo: float                                # the lowest in-spec signed-etch point (short edge)
    window_hi: float                                # the highest in-spec signed-etch point (open edge)


def _yield_at_ue(under_etch_frac: float) -> tuple[float, float]:
    """(yield, centre CD) for a default-anisotropy run at this under-etch fraction (the bridge cliff)."""
    w = run_line(Recipe(etch_deposition=EtchDepositionKnobs(under_etch_frac=under_etch_frac)),
                 seed=SEED, variation=NO_VARIATION, grid_n=1)
    return wafer_yield(w), float(w.dies[0].cd_nm)


def _run_signed_etch(x: float) -> tuple[float, float, bool]:
    """(yield, centre CD, bridged) at signed etch ``x`` (x<0 → under-etch; x≥0 → over-etch) for panel 3."""
    if x < 0.0:
        knobs = EtchDepositionKnobs(anisotropy=PROCESS_WINDOW_ANISOTROPY, under_etch_frac=-x)
    else:
        knobs = EtchDepositionKnobs(anisotropy=PROCESS_WINDOW_ANISOTROPY, over_etch_frac=x)
    w = run_line(Recipe(etch_deposition=knobs), seed=SEED, variation=NO_VARIATION, grid_n=1)
    d = w.dies[0]
    return wafer_yield(w), float(d.cd_nm), bool(d.bridged)


def compute() -> DemoResult:
    """Build the residual curve, the bridging cliff (pipeline), and the etch process window (pipeline)."""
    residual_by_film = {
        h: tuple(float(under_etch_residual(h, u)) for u in UE_SWEEP) for h in DEMO_FILMS_NM}

    yields, cds = [], []
    for u in UE_SWEEP:
        y, cd = _yield_at_ue(u)
        yields.append(y)
        cds.append(cd)
    ue_onset = BRIDGE_THRESHOLD_NM / NOMINAL_FILM_NM            # residual = UE·film crosses the threshold here

    axis_yields, axis_cds, axis_bridged = [], [], []
    for x in ETCH_AXIS:
        y, cd, br = _run_signed_etch(x)
        axis_yields.append(y)
        axis_cds.append(cd)
        axis_bridged.append(br)
    in_spec = [x for x, y in zip(ETCH_AXIS, axis_yields) if y >= 1.0]

    return DemoResult(
        bridge_threshold_nm=BRIDGE_THRESHOLD_NM,
        cd_lo=DEFAULT_SPECS.cd_nm.lo, cd_hi=DEFAULT_SPECS.cd_nm.hi,
        films_nm=DEMO_FILMS_NM, ue_sweep=UE_SWEEP, residual_by_film=residual_by_film,
        nominal_film_nm=NOMINAL_FILM_NM, yield_vs_ue=tuple(yields), cd_vs_ue=tuple(cds),
        ue_bridge_onset=ue_onset,
        process_anisotropy=PROCESS_WINDOW_ANISOTROPY, etch_axis=ETCH_AXIS,
        yield_vs_etch=tuple(axis_yields), cd_vs_etch=tuple(axis_cds), bridged_vs_etch=tuple(axis_bridged),
        window_lo=min(in_spec), window_hi=max(in_spec),
    )


def print_summary(r: DemoResult) -> None:
    """Print the residual → bridge cliff → process-window story — the demo's payoff in text (no score)."""
    print("\nEtch & deposition D1: under-etch → residual film → a bridging short (the etch process window)\n")

    print(f"  Under-etch (the mirror of G5's over-etch): an incomplete clear leaves residual = UE·film,")
    print(f"  which bridges adjacent gate lines into a SHORT once it exceeds ~{r.bridge_threshold_nm:.0f} nm")
    print(f"  (a FLAGGED house threshold; the cited direction is 'thicker residual → a continuous short').\n")

    print(f"  The bridging cliff (film {r.nominal_film_nm:.0f} nm, the CD untouched — a FUNCTIONAL kill):")
    print(f"     residual crosses the threshold at UE ≈ {r.ue_bridge_onset:.2f} → yield 100% → 0%")
    for u, y in zip(r.ue_sweep, r.yield_vs_ue):
        if u in (0.0, 0.1, 0.2, 0.3):
            print(f"     UE={u:.2f}: residual {u * r.nominal_film_nm:5.1f} nm → yield {y:.0%}")
    print()

    print(f"  The etch PROCESS WINDOW (anisotropy {r.process_anisotropy:.2f}, signed etch axis):")
    print(f"     too little etch → residual BRIDGE (a short);  too much → CD COLLAPSE (an open)")
    print(f"     the in-spec window is roughly [{r.window_lo:+.2f}, {r.window_hi:+.2f}] "
          f"(under-etch ← endpoint → over-etch)")
    print(f"  → endpoint control is bracketed by a short and an open — why an over-etch MARGIN exists,")
    print(f"     and why too much of it is its own (CD-collapse) failure. The window LOCATION rides the")
    print(f"     cited geometry; the bridge-threshold depth is the FLAGGED house number.\n")

    print("  New: the cited under-etch residual/bridge forms (chip.etch_deposition, triad-tested); the")
    print("  under-etch knob is opt-in (default = full clear → the G1–G6 banked demos byte-for-byte unchanged).\n")


def save_figure(r: DemoResult) -> Path:
    """Render and save the D1 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import under_etch_figure

    fig = under_etch_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # →, ≈, ← on legacy codepages

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
