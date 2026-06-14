"""The journey demo (phase 1): watch a purification-stage playthrough — refine a dirty feed until it clears.

The staged sand→chip journey's first stage, played start to finish (plan ``docs/plans/fab-journey.md``;
:mod:`fab_game.journey`). You begin with a dirty **solar** feedstock and **refine it step by step**; at
each step a forecast runs the whole line and reports the consequence **band** and the **channel** it would
fail on. The arc is the showcase for the gradual-failure policy:

* raw (effort 0) → **DEAD** — residual mobile-ion Na drives ``V_t`` out of spec, the whole wafer scrapped;
* a fractional pass → **RING** — Na drops into the marginal band, so only the edge-loaded rim fails
  (a graded yield, the rework signal — refine harder);
* one full pass → **CLEAN** — the feed is pure enough, full yield.

Then **commit** the decision into the recipe and **finish** — run the line and score the wafer (the
:mod:`fab_game.game` economics, reused). A second feed (**metal**, Na-free but iron-laden) shows the *other*
channel: it reads fine on ``V_t`` yet dies on junction **leakage** — the consequence net doping can't carry.

Zero new physics (it composes :func:`~fab_game.journey.forecast` / :func:`~fab_game.journey.finish`); the
segregation + the contamination→device chain are tested elsewhere. The live UI (a notebook ``interact`` /
a Textual journey screen) is the deferred next increment — this banked demo is the *watch-a-playthrough*
artifact over the headless core.

Run headless (saves the figure, prints the playthrough):

    python -m fab_game.demo_journey
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .journey import (
    JourneyState,
    StageForecast,
    finish,
    forecast,
    new_journey,
    refining_trajectory,
)
from .pipeline import LineResult
from .scoring import ScoreCard

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
GRADE = "solar"                  # the showcase feed: walks dead → ring → clean as you refine
MAX_EFFORT = 1.5                 # the refining sweep (zone passes)
STEP = 0.25                      # one refine() increment
CLEAN_EFFORT = 1.5               # commit + finish here (refined clean)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-journey.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-journey.png"


@dataclass(frozen=True)
class JourneyDemoResult:
    """The purification-stage playthrough bundle — the refining arc, the ring, the finish, the contrast."""

    grade: str
    trajectory: tuple                       # (effort, Contamination) — the impurity vector vs effort
    efforts: tuple[float, ...]
    yields: tuple[float, ...]               # forecast yield at each effort (the consequence arc)
    bands: tuple[str, ...]                  # "dead" / "ring" / "clean" at each effort
    channels: tuple                          # the failing channel at each effort (or None)
    arc: tuple[StageForecast, ...]          # the full forecast at each effort
    ring_effort: float                      # the effort whose band is "ring" (the graded wafer map)
    ring_forecast: StageForecast
    finish_result: LineResult               # the committed, refined feed run + scored end-to-end
    finish_score: ScoreCard
    metal_forecast: StageForecast           # the leakage-channel contrast (Na-free, Fe-laden)
    log: tuple[str, ...]                    # the playthrough's append-only trail


def compute() -> JourneyDemoResult:
    """Play the purification stage: refine a solar feed across the arc, commit + finish, the metal contrast."""
    n = int(round(MAX_EFFORT / STEP))
    efforts: list[float] = []
    yields: list[float] = []
    bands: list[str] = []
    channels: list = []
    arc: list[StageForecast] = []
    for i in range(n + 1):
        st = JourneyState(grade=GRADE, effort=round(i * STEP, 6), seed=SEED)
        f = forecast(st)
        efforts.append(st.effort)
        yields.append(f.yield_)
        bands.append(f.band)
        channels.append(f.channel)
        arc.append(f)

    ring_i = next((i for i, b in enumerate(bands) if b == "ring"), len(arc) // 2)
    ring_effort, ring_forecast = efforts[ring_i], arc[ring_i]

    # The multi-step playthrough (builds the append-only log), then commit + finish at a refined-clean effort.
    played = new_journey(GRADE, seed=SEED)
    for _ in range(int(round(CLEAN_EFFORT / STEP))):
        played = played.refine(STEP)
    played = played.commit()
    finish_result, finish_score = finish(played)

    metal_forecast = forecast(new_journey("metal", seed=SEED))

    return JourneyDemoResult(
        grade=GRADE,
        trajectory=refining_trajectory(GRADE, max_effort=MAX_EFFORT, step=STEP),
        efforts=tuple(efforts), yields=tuple(yields), bands=tuple(bands),
        channels=tuple(channels), arc=tuple(arc),
        ring_effort=ring_effort, ring_forecast=ring_forecast,
        finish_result=finish_result, finish_score=finish_score,
        metal_forecast=metal_forecast, log=played.log,
    )


def print_summary(r: JourneyDemoResult) -> None:
    """Print the purification-stage playthrough — the dead → ring → clean arc, the finish, the contrast."""
    print("\nThe journey — stage 1: silicon purification (refine a dirty feed until it clears)\n")
    print(f"  You start with a {r.grade} feedstock (solar-grade — an intermediate feed, already partly")
    print("  refined; the raw 'sand' grade MGS is dirtier and needs more passes) and refine it step by")
    print("  step. At each step the forecast runs the whole line and reports the band + the channel:\n")
    print(f"     {'effort':>6}  {'Na (cm⁻³)':>11}  {'yield':>6}  {'band':<5}  channel")
    for e, f in zip(r.efforts, r.arc):
        ch = f.channel or "—"
        print(f"     {e:6.2f}  {f.contamination['Na']:11.2e}  {f.yield_:6.0%}  {f.band:<5}  {ch}")
    print(f"\n  → dead (Na out of spec) → a graded RING at effort {r.ring_effort:g} "
          f"({r.ring_forecast.yield_:.0%} yield — the rework band) → clean. The continuous refining")
    print("    effort is the lever; a fractional pass lands the ring that whole passes leap over.\n")

    print("  Commit the decision and finish — run the whole line and score the wafer:")
    sc = r.finish_score
    print(f"     finish: yield {r.finish_result.yield_:.0%}  ·  {sc.n_good}/{sc.n_total} shipped  ·  "
          f"profit {sc.profit:+.0f}\n")

    mf = r.metal_forecast
    print(f"  Contrast — a metal feed (Na-free, iron-laden) reads fine on V_t yet is {mf.band.upper()} on")
    print(f"    a different channel: {mf.channel}.")
    print("    (the deep-level-metal consequence net doping can't carry — purify harder to scrub it.)\n")

    print("  New: the staged journey scaffold + the purification stage (decision → multi-step refine →")
    print("  consequence forecast → commit → finish). Zero new physics — it composes the validated line.\n")


def save_figure(r: JourneyDemoResult) -> Path:
    """Render and save the journey artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import journey_figure

    fig = journey_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # cm⁻³, →, · on legacy codepages

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
