"""The staged sand→chip journey — decide at each fab stage, watch the consequence propagate (phase 1).

The player-facing framing the roguelike (:mod:`fab_game.game`) and the dashboard
(:mod:`fab_game.dashboard`) never gave. Instead of one wafer down a boule (game) or four live sliders
(dashboard), a *journey* builds **one wafer's recipe stage by stage** — pick the feedstock and purify it,
then (later phases) slice, polish, diffuse, oxidize, pattern, etch, package — a real decision at each
stage, watched as it lands downstream: from no-effect, through a graded yield ring, to an outright scrap.

**Phase 1 builds the first stage — silicon purification — only.** Every later stage runs at its recipe
default (the journey just carries them). The scaffold is deliberately thin — an accumulating
:class:`~fab_game.recipe.Recipe` plus the purification decision, **not** a nine-stage state machine — per
the repo's anti-over-build rule: a stage gets built when it has a consumer.

The purification stage is the showcase for the **gradual-failure policy** (the edge-loaded Na ring,
:meth:`fab_game.variation.Variation.na_factor`). You start with a dirty feedstock and **refine it step by
step** — each zone-refining increment scrubs the impurity vector (Na/Fe/Cu fall by ``k^n``, boron barely
moves), and a :func:`forecast` runs the line at the recipe-so-far to show the consequence **band**
(``clean`` → ``ring`` → ``dead``, the ok→rework→fail spectrum) **and the channel it fails on**
(mobile-ion Na → a ``V_t`` ring, or deep-level metal → junction leakage — so a dirty feed that *looks*
fine on threshold can still die on leakage). The continuous refining effort is the lever
(``front_purity``'s ``k^n`` is smooth in ``n``), so you can place the residual in the marginal band where
the graded ring lives — then :meth:`~JourneyState.commit` (fold the decision into the recipe) and
:func:`finish` (run the whole line and score the wafer, reusing the :mod:`fab_game.game` economics).

Discipline (matching :class:`fab_game.game.GameSession`): the state is an **immutable** frozen dataclass
(each action returns a new state), the log is **append-only**, and ``(seed, grade, actions)`` is
**deterministic**. Zero new physics — it composes :func:`run_line` + :func:`score_wafer` (ADR 0005). The
**live UI** (a notebook ``interact`` / a Textual journey screen) is the deferred next increment; this
module is headless and tested, and :mod:`fab_game.demo_journey` is a *watch-a-playthrough* artifact over it.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from chip.purification import Contamination, FEEDSTOCK_GRADES, zone_refine

from .game import GameConfig
from .pipeline import LineResult, run_line
from .recipe import DEFAULT_RECIPE, Recipe
from .scoring import ScoreCard, score_wafer
from .spec import DEFAULT_SPECS
from .variation import Variation

DEFAULT_GRADE = "solar"          # start with an intermediate (dirty) feed — the refining IS the gameplay
DEFAULT_STEP = 0.25              # one refine() increment, in zone-passes (≈ half a decade of Na per step)
DEFAULT_GRID_N = 9               # the forecast map resolution (enough dies to read a ring)

# Consequence bands (the ok → rework → fail spectrum) — yield thresholds with margin so a boundary
# forecast doesn't flicker (ADR 0005 §5: coarse player guidance, not a magnitude claim).
CLEAN_BAND = 0.95                # ≥ this yield: clean — the decision didn't bite
DEAD_BAND = 0.05                 # ≤ this yield: dead — scrap (essentially every die out)


def consequence_band(yield_: float) -> str:
    """Map a forecast yield to the ok→rework→fail band: ``"clean"`` / ``"ring"`` / ``"dead"``."""
    if yield_ >= CLEAN_BAND:
        return "clean"
    if yield_ <= DEAD_BAND:
        return "dead"
    return "ring"


# --------------------------------------------------------------------------- #
# The consequence forecast — run the recipe-so-far, band it, name the channel
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StageForecast:
    """The downstream consequence of the recipe-so-far — the line run at it, banded and channel-named.

    ``band`` the ok→rework→fail spectrum (:func:`consequence_band`); ``channel`` the dominant failure
    mechanism the trail names (``V_t`` mobile-ion / leakage metal / drive current), or ``None`` when clean;
    ``yield_``/``mean_vt`` the readout; ``result`` the wafer (for the map/trail); ``contamination`` the
    current impurity vector (cm⁻³); ``headline`` the one-line human summary.
    """

    band: str
    channel: str | None
    yield_: float
    mean_vt: float | None
    contamination: dict
    result: LineResult
    headline: str


def _mean_vt(result: LineResult) -> float | None:
    vts = [d.V_t for d in result.wafer.dies if d.V_t is not None]
    return sum(vts) / len(vts) if vts else None


def _dominant_channel(result: LineResult) -> str | None:
    """Name the channel the dead dies fail on (the consequence the player watches propagate), or ``None``.

    Reads the worst (outer-most) dead die's verdict reasons — for purification the kill is wafer-level, so
    one die is representative. Distinguishes the mobile-ion ``V_t`` ring from deep-level-metal leakage (the
    "looks fine on threshold but dies on leakage" story the metal grade carries)."""
    dead = result.dead_dies
    if not dead:
        return None
    worst = max(dead, key=lambda d: d.radius_frac)
    reasons = " ".join(worst.verdict.reasons).lower()
    if "v_t" in reasons:
        return "V_t — mobile-ion Na → gate-oxide charge"
    if "leak" in reasons:
        return "junction leakage — deep-level metal (Fe/Cu)"
    if "i_dsat" in reasons or "i_d" in reasons:
        return "drive current (I_Dsat)"
    return worst.verdict.reasons[0] if worst.verdict.reasons else "unknown"


def forecast(state: "JourneyState") -> StageForecast:
    """Run the line at the current recipe (variation **on**, so the ring shows) → the consequence band.

    Reuses :func:`run_line` — zero new physics. Single seed (the journey's), like the dashboard; the bands
    carry a margin so a boundary forecast does not flicker. ``clean`` ⇒ the feed is pure enough; ``ring`` ⇒
    a marginal feed kills an edge ring (rework: refine harder); ``dead`` ⇒ scrapped."""
    recipe = state.current_recipe
    wafer = run_line(recipe, seed=state.seed, variation=Variation(), specs=DEFAULT_SPECS, grid_n=state.grid_n)
    result = LineResult.of(f"{state.grade} · refine ×{state.effort:g}", wafer)
    y = result.yield_
    band = consequence_band(y)
    channel = _dominant_channel(result) if band != "clean" else None
    if band == "clean":
        headline = f"clean — {y:.0%} yield, no consequence (feed pure enough)"
    elif band == "dead":
        headline = f"DEAD — {y:.0%} yield, scrapped on {channel}"
    else:
        headline = f"ring — {y:.0%} yield, an edge ring fails on {channel} (rework: refine harder)"
    return StageForecast(band=band, channel=channel, yield_=y, mean_vt=_mean_vt(result),
                         contamination=state.contamination.as_dict(), result=result, headline=headline)


def refining_trajectory(grade: str, *, max_effort: float = 2.0, step: float = DEFAULT_STEP):
    """The impurity vector at each refining effort ``0..max_effort`` — the multi-step 'watch it develop'.

    Na/Fe/Cu fall by ``k^n`` (the tiny-``k`` metals fastest), boron barely moves (``k ≈ 0.8``) — the
    teachable segregation contrast, straight from the cited ``k`` table. Returns a tuple of
    ``(effort, Contamination)``."""
    if grade not in FEEDSTOCK_GRADES:
        raise ValueError(f"unknown feedstock grade {grade!r} (have {sorted(FEEDSTOCK_GRADES)})")
    feed = FEEDSTOCK_GRADES[grade]
    n = int(round(max_effort / step))
    return tuple((round(i * step, 6), zone_refine(feed, i * step)) for i in range(n + 1))


# --------------------------------------------------------------------------- #
# The journey state — an immutable, accumulating recipe + the purification decision
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class JourneyState:
    """An immutable staged build of one wafer's recipe — make a decision per fab stage (phase 1: purify).

    ``recipe`` the accumulator (committed stages), ``grade``/``effort`` the *in-progress* purification
    decision (folded into :attr:`current_recipe` until :meth:`commit`), ``seed``/``grid_n`` the forecast
    determinism + resolution, ``log`` the append-only trail. Each action returns a **new** state (the
    ``WaferState``/``GameSession`` discipline)."""

    recipe: Recipe = DEFAULT_RECIPE
    grade: str = DEFAULT_GRADE
    effort: float = 0.0
    seed: int = 0
    grid_n: int = DEFAULT_GRID_N
    log: tuple[str, ...] = ()

    @property
    def current_recipe(self) -> Recipe:
        """The accumulator with the in-progress purification decision (grade + refining effort) folded in."""
        return replace(self.recipe, purification=replace(self.recipe.purification,
                                                         grade=self.grade, zone_passes=self.effort))

    @property
    def contamination(self) -> Contamination:
        """The purified impurity vector at the current grade + effort (the seam currency)."""
        return self.current_recipe.contamination

    def choose_grade(self, grade: str) -> "JourneyState":
        """Pick a raw feedstock — resets the refining effort to 0 (a fresh, unrefined charge)."""
        if grade not in FEEDSTOCK_GRADES:
            raise ValueError(f"unknown feedstock grade {grade!r} (have {sorted(FEEDSTOCK_GRADES)})")
        return replace(self, grade=grade, effort=0.0,
                       log=self.log + (f"feedstock: {grade} (raw, unrefined)",))

    def refine(self, step: float = DEFAULT_STEP) -> "JourneyState":
        """Advance the zone-refining by one increment of effort — the multi-step 'watch it develop'."""
        if step <= 0:
            raise ValueError(f"refine step must be > 0, got {step}")
        nxt = replace(self, effort=self.effort + step)
        c = nxt.contamination
        return replace(nxt, log=self.log + (f"refine +{step:g} → effort {nxt.effort:g}: "
                                            f"Na {c.Na:.2e} cm⁻³",))

    def commit(self) -> "JourneyState":
        """Fold the purification decision into the accumulating recipe (the next stage builds on it)."""
        return replace(self, recipe=self.current_recipe,
                       log=self.log + (f"committed purification: {self.grade} × {self.effort:g} passes",))


def new_journey(grade: str = DEFAULT_GRADE, *, seed: int = 0, grid_n: int = DEFAULT_GRID_N,
                recipe: Recipe = DEFAULT_RECIPE) -> JourneyState:
    """A fresh journey at a raw feedstock grade, unrefined (effort 0)."""
    if grade not in FEEDSTOCK_GRADES:
        raise ValueError(f"unknown feedstock grade {grade!r} (have {sorted(FEEDSTOCK_GRADES)})")
    return JourneyState(recipe=recipe, grade=grade, effort=0.0, seed=seed, grid_n=grid_n,
                        log=(f"feedstock: {grade} (raw, unrefined)",))


def finish(state: JourneyState, *, config: GameConfig | None = None) -> tuple[LineResult, ScoreCard]:
    """Run the full accumulated recipe end-to-end and score the wafer — reusing the :mod:`fab_game.game`
    economics (market bins, prices, wafer cost) rather than forking a parallel scoring path.

    Returns the scored :class:`~fab_game.pipeline.LineResult` and its :class:`~fab_game.scoring.ScoreCard`.
    Even with only purification interactive (every later stage at its default), the journey is playable
    start-to-finish: raw feed → committed recipe → binned, packaged, scored wafer."""
    cfg = config if config is not None else GameConfig()
    recipe = state.current_recipe
    wafer = run_line(recipe, seed=state.seed, variation=cfg.variation, specs=cfg.specs, grid_n=state.grid_n)
    result = LineResult.of(f"journey finish: {state.grade} × {state.effort:g}", wafer)
    sc = score_wafer(wafer, prices=cfg.prices, wafer_cost=cfg.wafer_cost, rework_cost=0.0)
    return result, sc
