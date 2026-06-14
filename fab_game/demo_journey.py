"""The journey demo (phases 1–3): a three-stage playthrough — purify a feed, grow the boule, cut a wafer.

The staged sand→chip journey, played start to finish (plan ``docs/plans/fab-journey.md``;
:mod:`fab_game.journey`). Three stages so far:

**Stage 1 — purification.** Begin with a dirty **solar** feedstock and **refine it step by step**; at each
step a forecast runs the whole line and reports the consequence **band** and the **channel** it would fail
on. The arc walks **dead** (residual mobile-ion Na → ``V_t`` out of spec) → a graded **ring** (only the
edge-loaded rim fails — the rework signal) → **clean**.

**Stage 2 — crystal growth.** On the now-clean feed, set the boule **pull rate**. Riding a fixed *radial*
hot zone, the pull rate is a genuinely **two-sided** decision (no economics needed) where *both* failures
are graded (the gradual-failure policy): too **slow** → an interstitial dislocation **leakage rim**, too
**fast** → a vacancy **void core**, with a clean **OSF ring** between — pull rate moves the ring. The arc
walks **ring** (slow, leakage) → **clean** (the optimum ~``V*``) → **ring** (fast, voids), and the boule's
axial ``V_t`` drift (Scheil) **flattens** as the pull speeds up (CG-1).

**Stage 3 — slice/cut.** On the committed boule, choose **where down it to cut** this wafer. The cut reads
the boule's axial Scheil drift (stage 2): boron's k<1 walks ``V_t`` up toward the tail, so a wafer cut too
deep lands above spec — failing the **centre** dies first (a graded ``V_t`` **core**: the radial t_ox
non-uniformity grades the cliff, the rim's thinner oxide gives it a lower ``V_t`` so it survives the high
ceiling longest — the *inverse* of stage-1's Na edge ring), then the whole wafer. It is the first stage
that **reads a prior
committed decision** — the **coupling**: a flat boule (fast phase-2 pull) can be cut **deep** and stay in
spec, while a slow-pulled boule is already lost to its dislocation leakage rim *before* the cut, so cut
depth can't rescue it. Cutting at the seed is always safest; "use more of the boule" is the same deferred
economics as purification's refining effort (the cost side).

Then **commit** each decision into the recipe and **finish** — run the line and score the wafer (the
:mod:`fab_game.game` economics, reused). A second feed (**metal**, Na-free but iron-laden) shows the other
purification channel: it reads fine on ``V_t`` yet dies on junction **leakage** (deep-level metals).

Zero new physics (it composes :func:`~fab_game.journey.forecast` / :func:`~fab_game.journey.finish` /
:func:`~fab_game.journey.boule_profile`). The live UI is the deferred next increment — this banked demo is
the *watch-a-playthrough* artifact over the headless core.

Run headless (saves the figure, prints the playthrough):

    python -m fab_game.demo_journey
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .journey import (
    JourneyState,
    StageForecast,
    boule_profile,
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
GROWTH_PULLS = (0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)   # the pull-rate sweep (coarse — the suite runs this)
SLOW_PULL = 0.5                  # the steep-drift / leakage-rim contrast pull (boule drift + the stage-3 coupling)
SLICE_ZS = (0.0, 0.3, 0.55, 0.75, 0.85, 0.88, 0.90, 0.93)   # the cut sweep down the boule (clean → ring → dead)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-journey.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-journey.png"


@dataclass(frozen=True)
class JourneyDemoResult:
    """The two-stage playthrough bundle — the purification arc, the growth window, the finish, the contrast."""

    grade: str
    # Stage 1 — purification:
    trajectory: tuple                       # (effort, Contamination) — the impurity vector vs effort
    efforts: tuple[float, ...]
    yields: tuple[float, ...]               # forecast yield at each effort (the consequence arc)
    bands: tuple[str, ...]
    channels: tuple
    arc: tuple[StageForecast, ...]
    ring_effort: float
    ring_forecast: StageForecast
    # Stage 2 — crystal growth:
    growth_pulls: tuple[float, ...]
    growth_yields: tuple[float, ...]        # forecast yield at each pull (the two-sided window)
    growth_bands: tuple[str, ...]
    growth_channels: tuple
    growth_arc: tuple[StageForecast, ...]
    growth_optimum_pull: float              # the best-yield pull (the clean ring)
    growth_optimum_forecast: StageForecast
    boule_slow: tuple                       # axial (z, V_t) at a slow pull — the steep Scheil drift
    boule_opt: tuple                        # axial (z, V_t) at the optimum pull — flattened (CG-1)
    # Stage 3 — slice/cut (reads the boule drift; coupled to the phase-2 pull):
    slow_pull: float                        # the leakage-rim contrast pull (the coupling base)
    slice_zs: tuple[float, ...]
    slice_yields: tuple[float, ...]         # forecast yield vs cut depth at the optimum pull (clean→ring→dead)
    slice_bands: tuple[str, ...]
    slice_channels: tuple
    slice_arc: tuple[StageForecast, ...]
    slice_ring_z: float                     # the marginal (ring-band) cut — the V_t centre core for the map
    slice_ring_forecast: StageForecast
    slice_commit_z: float                   # the deepest clean cut — "use as much boule as spec allows"
    slice_yields_slow: tuple[float, ...]    # the SAME cut sweep on a slow-pulled boule (already lost to its rim)
    # End to end:
    finish_result: LineResult
    finish_score: ScoreCard
    metal_forecast: StageForecast           # the leakage-channel purification contrast
    log: tuple[str, ...]


def _arc(states):
    forecasts = [forecast(s) for s in states]
    return forecasts


def compute() -> JourneyDemoResult:
    """Play both stages: refine a solar feed (arc), grow the clean boule (two-sided window), commit + finish."""
    # --- Stage 1: purification (refine the solar feed across the arc) ---
    n = int(round(MAX_EFFORT / STEP))
    pur_states = [JourneyState(grade=GRADE, effort=round(i * STEP, 6), seed=SEED) for i in range(n + 1)]
    arc = _arc(pur_states)
    efforts = tuple(s.effort for s in pur_states)
    yields = tuple(f.yield_ for f in arc)
    bands = tuple(f.band for f in arc)
    channels = tuple(f.channel for f in arc)
    ring_i = next((i for i, b in enumerate(bands) if b == "ring"), len(arc) // 2)

    # Play + commit the purification (the clean feed the growth stage grows on).
    pur = new_journey(GRADE, seed=SEED)
    for _ in range(int(round(CLEAN_EFFORT / STEP))):
        pur = pur.refine(STEP)
    pur = pur.commit()

    # --- Stage 2: crystal growth (on the committed clean feed — sweep the pull rate) ---
    growth_states = [pur.grow(p) for p in GROWTH_PULLS]
    g_arc = _arc(growth_states)
    growth_yields = tuple(f.yield_ for f in g_arc)
    growth_bands = tuple(f.band for f in g_arc)
    growth_channels = tuple(f.channel for f in g_arc)
    opt_i = max(range(len(growth_yields)), key=lambda i: growth_yields[i])
    growth_optimum_pull = GROWTH_PULLS[opt_i]

    # The boule axial drift (CG-1 flattening): a slow pull vs the optimum.
    boule_slow = boule_profile(pur.grow(SLOW_PULL))
    boule_opt = boule_profile(pur.grow(growth_optimum_pull))

    # Commit the growth (the clean, optimally-grown boule the slice stage cuts from).
    grown = pur.grow(growth_optimum_pull).commit()

    # --- Stage 3: slice/cut (on the committed boule — sweep the cut depth down the boule) ---
    slice_states = [grown.cut(z) for z in SLICE_ZS]
    s_arc = _arc(slice_states)
    slice_yields = tuple(f.yield_ for f in s_arc)
    slice_bands = tuple(f.band for f in s_arc)
    slice_channels = tuple(f.channel for f in s_arc)
    ring_si = next((i for i, b in enumerate(slice_bands) if b == "ring"), len(s_arc) // 2)
    clean_is = [i for i, b in enumerate(slice_bands) if b == "clean"]
    commit_si = clean_is[-1] if clean_is else 0      # the deepest clean cut — use as much boule as spec allows

    # The phase-2 → phase-3 coupling: the SAME cut sweep on a slow-pulled boule, already lost to its
    # interstitial dislocation leakage rim — so cut depth can't rescue it (a flat boule cuts deep; a slow
    # one is dead before the cut). This is the journey's "watch the consequence propagate" payoff.
    slow_grown = pur.grow(SLOW_PULL).commit()
    slice_yields_slow = tuple(forecast(slow_grown.cut(z)).yield_ for z in SLICE_ZS)

    # Commit the cut decision + finish (run + score the whole line).
    played = grown.cut(SLICE_ZS[commit_si]).commit()
    finish_result, finish_score = finish(played)

    metal_forecast = forecast(new_journey("metal", seed=SEED))

    return JourneyDemoResult(
        grade=GRADE,
        trajectory=refining_trajectory(GRADE, max_effort=MAX_EFFORT, step=STEP),
        efforts=efforts, yields=yields, bands=bands, channels=channels, arc=tuple(arc),
        ring_effort=efforts[ring_i], ring_forecast=arc[ring_i],
        growth_pulls=GROWTH_PULLS, growth_yields=growth_yields, growth_bands=growth_bands,
        growth_channels=growth_channels, growth_arc=tuple(g_arc),
        growth_optimum_pull=growth_optimum_pull, growth_optimum_forecast=g_arc[opt_i],
        boule_slow=boule_slow, boule_opt=boule_opt,
        slow_pull=SLOW_PULL, slice_zs=SLICE_ZS, slice_yields=slice_yields, slice_bands=slice_bands,
        slice_channels=slice_channels, slice_arc=tuple(s_arc),
        slice_ring_z=SLICE_ZS[ring_si], slice_ring_forecast=s_arc[ring_si],
        slice_commit_z=SLICE_ZS[commit_si], slice_yields_slow=slice_yields_slow,
        finish_result=finish_result, finish_score=finish_score,
        metal_forecast=metal_forecast, log=played.log,
    )


def print_summary(r: JourneyDemoResult) -> None:
    """Print the two-stage playthrough — purify (dead→ring→clean), grow (the two-sided window), finish."""
    print("\nThe journey — a two-stage playthrough: purify the feed, then grow the boule\n")

    print(f"  STAGE 1 — purification. Start with a {r.grade} feed (solar-grade: an intermediate, already")
    print("  partly-refined feed; raw 'sand' MGS is dirtier) and refine it step by step:\n")
    print(f"     {'effort':>6}  {'Na (cm⁻³)':>11}  {'yield':>6}  {'band':<5}  channel")
    for e, f in zip(r.efforts, r.arc):
        print(f"     {e:6.2f}  {f.contamination['Na']:11.2e}  {f.yield_:6.0%}  {f.band:<5}  {f.channel or '—'}")
    print(f"  → dead (Na) → a graded RING at effort {r.ring_effort:g} ({r.ring_forecast.yield_:.0%}) → clean.\n")

    print("  STAGE 2 — crystal growth. On the clean feed, set the boule pull rate (a fixed radial hot zone):\n")
    print(f"     {'pull':>5}  {'yield':>6}  {'band':<5}  channel")
    for p, f in zip(r.growth_pulls, r.growth_arc):
        print(f"     {p:5.2f}  {f.yield_:6.0%}  {f.band:<5}  {f.channel or '—'}")
    print(f"  → too slow → a graded dislocation LEAKAGE rim; the optimum ~{r.growth_optimum_pull:g} mm/min →")
    print(f"    a clean OSF ring ({r.growth_optimum_forecast.yield_:.0%}); too fast → a graded void CORE.")
    print(f"    Both sides graded (the radial hot zone) — no cliff. The boule's axial V_t drift also flattens")
    print(f"    with a faster pull: seed→tail swing {r.boule_slow[-1][1] - r.boule_slow[0][1]:+.3f} V "
          f"(slow) vs {r.boule_opt[-1][1] - r.boule_opt[0][1]:+.3f} V (optimum) — CG-1.\n")

    print("  STAGE 3 — slice/cut. On the committed boule, choose where down it to cut this wafer (the Scheil")
    print("  drift walks V_t up the boule — cut too deep and it lands above spec):\n")
    print(f"     {'cut z':>5}  {'yield':>6}  {'band':<5}  channel")
    for z, f in zip(r.slice_zs, r.slice_arc):
        print(f"     {z:5.2f}  {f.yield_:6.0%}  {f.band:<5}  {f.channel or '—'}")
    print(f"  → clean near the seed; cut past z≈{r.slice_ring_z:g} → a graded V_t CORE "
          f"({r.slice_ring_forecast.yield_:.0%}; the centre dies cross the high ceiling first, the rim's "
          f"thinner oxide survives) → dead at the tail.")
    print(f"    The decision is set by the phase-2 pull (the COUPLING): a flat boule (fast pull) can be cut")
    print(f"    deep — at z={r.slice_commit_z:g} the optimum pull yields "
          f"{r.slice_yields[r.slice_zs.index(r.slice_commit_z)]:.0%} but a slow pull only "
          f"{r.slice_yields_slow[r.slice_zs.index(r.slice_commit_z)]:.0%}")
    print(f"    (lost to its dislocation leakage rim before the cut). A bad pull can't be sliced away.\n")

    print("  Commit all three decisions and finish — run the whole line and score the wafer:")
    sc = r.finish_score
    print(f"     finish: yield {r.finish_result.yield_:.0%}  ·  {sc.n_good}/{sc.n_total} shipped  ·  "
          f"profit {sc.profit:+.0f}  ·  cut at z={r.slice_commit_z:g}\n")

    mf = r.metal_forecast
    print(f"  Contrast — a metal feed (Na-free, iron-laden) reads fine on V_t yet is {mf.band.upper()} on")
    print(f"    {mf.channel} (the deep-level-metal consequence net doping can't carry).\n")

    print("  New: the journey's third stage — the slice/cut (where down the boule to take the wafer). The")
    print("  first stage that READS a prior committed decision: how deep you can cut is set by the phase-2")
    print("  pull. Zero new physics — it composes the validated line.\n")


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
        sys.stdout.reconfigure(encoding="utf-8")     # cm⁻³, →, ·, ξ on legacy codepages

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
