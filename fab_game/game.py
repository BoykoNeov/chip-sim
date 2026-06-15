"""The roguelike session — one boule, one run: process wafers down its length, scored, on a budget (G7).

The game shell over the proven sim (plan §6 G7, §1; ADR 0005). G1–G6 built a headless line that turns a
recipe into a binned, packaged wafer; G7 frames that as a **roguelike**: a *run* is a journey down **one
boule**, each wafer a **turn**. The difficulty curve is **physics, not invention** — the G2 Scheil
segregation walks the substrate doping (and so the device ``V_t``) up the boule, so early slices are easy
and the **tail forces a decision**: adapt the recipe (thin the gate oxide to pull ``V_t`` back into spec),
**scrap** the doomed wafer (cut the loss), or process it and **eat** the loss. Consequences stick; the
boule is finite; in roguelike mode a bankrupt budget ends the run.

This is **purely additive game policy** (ADR 0005): it consumes the existing :func:`run_line` per wafer and
the existing rework paths — it touches no physics, no ``run_line``, no ``WaferState``/``Die`` field — so it
adds no seam and the physics tests are unaffected. The session is **immutable** (a frozen dataclass; each
action returns a new session, matching the ``WaferState`` discipline) and **deterministic**: every wafer
draws ``seed + wafer_index`` from one session seed, so a ``(seed, recipe-sequence, actions)`` triple
reproduces the whole playthrough (a roguelike "seed").

The **TUI is the deliberately-deferred follow-on** (plan §9): "roguelike framing" is a *session model*, not
a UI — everything here is headless and testable. A Textual front-end would be a thin driver of this session,
added only when wanted.

Validation (ADR 0005 §5 — mechanics, not magnitudes)
----------------------------------------------------
* **Determinism:** a fixed ``(seed, recipe-sequence, actions)`` reproduces the final session
  (budget, score, history) bit-for-bit.
* **Bookkeeping closes:** ``budget = starting_budget + Σ run profits``; ``score`` is the cumulative
  profit; the history is **append-only** (one :class:`RunRecord` per turn, never rewritten); no money is
  created or destroyed.
* **Sandbox vs roguelike** is one mode flag: roguelike ends on a bankrupt budget; sandbox never does
  (explore freely). The boule is finite in both (``n_wafers`` slices).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .pipeline import rework_deposition, rework_litho, rework_polish, run_line
from .recipe import DEFAULT_RECIPE, Recipe
from .scoring import REWORK_COSTS, SCRAP_COST, WAFER_COST, ScoreCard, score_wafer
from .spec import SpecSet
from .state import WaferState
from .targets import FAST_LOGIC, DeviceTarget
from .variation import Variation


@dataclass(frozen=True)
class ReworkSpec:
    """A rework action to fold into a turn — which path + its parameters (the existing pipeline reworks)."""

    kind: str = "litho"                            # "litho" | "polish" | "deposition"
    focus_correction_nm: float = 0.0               # litho: re-expose focus offset
    extra_removal_um: float = 40.0                 # polish: extra CMP removal
    conformality: float = 0.9                      # deposition: re-deposit step coverage


@dataclass(frozen=True)
class GameConfig:
    """The run's fixed setup: the declared target, the boule recipe, the line costs, the budget, and the mode.

    ``target`` the **declared device target** (the up-front flavor declaration — its windows + speed bins +
    price curve are what every wafer is scored against; defaults to :data:`~fab_game.targets.FAST_LOGIC`, the
    incumbent, so the pre-targets game is reproduced bit-for-bit); ``base_recipe`` the default process (the
    player overrides per turn); ``wafer_cost``/``scrap_cost`` the line economics (:mod:`fab_game.scoring`,
    flagged house numbers); ``starting_budget`` the bank; ``n_wafers`` the slices down the boule and
    ``z_max`` the deepest axial fraction (the difficulty curve); ``variation`` the within-wafer spread;
    ``sandbox`` removes the bankrupt gate (explore freely). The per-turn slice position is the session's,
    not the recipe's — the player chooses the *process*, the boule dictates *where* on it you are.
    """

    base_recipe: Recipe = DEFAULT_RECIPE
    target: DeviceTarget = FAST_LOGIC
    wafer_cost: float = WAFER_COST
    scrap_cost: float = SCRAP_COST
    starting_budget: float = 200.0
    n_wafers: int = 8
    z_max: float = 0.9
    variation: Variation = field(default_factory=Variation)
    grid_n: int = 5
    sandbox: bool = False

    @property
    def specs(self) -> SpecSet:
        """The declared target's acceptance test (the front-end windows + its speed grades)."""
        return self.target.specs

    @property
    def prices(self) -> dict[str, float]:
        """The declared target's per-bin price curve (the revenue side of the economics)."""
        return self.target.prices

    def slice_z(self, wafer_index: int) -> float:
        """The axial fraction-solidified for the ``wafer_index``-th turn (0 → ``z_max`` across the boule)."""
        if self.n_wafers <= 1:
            return 0.0
        return wafer_index * self.z_max / (self.n_wafers - 1)


@dataclass(frozen=True)
class RunRecord:
    """One turn's outcome: the slice, its score card, and how the turn was played (the append-only trail).

    ``scrapped`` the player bailed before processing (only the scrap cost, no revenue); ``reworked`` a
    rework was folded into the turn; ``note`` a short human tag. ``scorecard.profit`` is the turn's
    budget change.
    """

    wafer_index: int
    slice_z: float
    scorecard: ScoreCard
    scrapped: bool = False
    reworked: bool = False
    note: str = ""


@dataclass(frozen=True)
class GameSession:
    """An immutable roguelike session: the config, the seed, the running budget, and the turn history.

    Each action (:func:`process_wafer`, :func:`scrap_wafer`) returns a **new** session with one
    :class:`RunRecord` appended (append-only). ``budget`` is the live bank; ``score`` the cumulative
    profit (``budget − starting_budget``); ``wafer_index`` how far down the boule you are
    (``len(history)``). The run is :attr:`done` when the boule is exhausted, or (roguelike only) the
    budget goes negative.
    """

    config: GameConfig
    seed: int
    budget: float
    history: tuple[RunRecord, ...] = ()

    @property
    def wafer_index(self) -> int:
        return len(self.history)

    @property
    def score(self) -> float:
        """Cumulative profit so far (``budget − starting_budget``)."""
        return self.budget - self.config.starting_budget

    @property
    def bankrupt(self) -> bool:
        """The budget has gone negative (ends a roguelike run; never trips in sandbox)."""
        return (not self.config.sandbox) and self.budget < 0.0

    @property
    def boule_exhausted(self) -> bool:
        return self.wafer_index >= self.config.n_wafers

    @property
    def done(self) -> bool:
        return self.bankrupt or self.boule_exhausted

    @property
    def next_slice_z(self) -> float:
        """The axial position of the next wafer to process (the boule dictates it, not the recipe)."""
        return self.config.slice_z(self.wafer_index)


def new_session(config: GameConfig = GameConfig(), *, seed: int = 0) -> GameSession:
    """A fresh run: the starting budget, no turns played."""
    return GameSession(config=config, seed=seed, budget=config.starting_budget)


def _apply_rework(wafer: WaferState, recipe: Recipe, spec: ReworkSpec,
                  specs: SpecSet, variation: Variation) -> WaferState:
    """Dispatch a :class:`ReworkSpec` to the matching (already-tested) pipeline rework path."""
    if spec.kind == "litho":
        return rework_litho(wafer, recipe, specs=specs, variation=variation,
                            focus_correction_nm=spec.focus_correction_nm)
    if spec.kind == "polish":
        return rework_polish(wafer, specs=specs, extra_removal_um=spec.extra_removal_um)
    if spec.kind == "deposition":
        return rework_deposition(wafer, recipe, specs=specs, conformality=spec.conformality)
    raise ValueError(f"unknown rework kind {spec.kind!r} (expected litho/polish/deposition)")


def process_wafer(
    session: GameSession,
    recipe: Recipe | None = None,
    *,
    rework: ReworkSpec | None = None,
) -> GameSession:
    """Play one turn: process the next slice with ``recipe`` (optionally reworked), score it, bank the profit.

    The wafer is run at the session's :attr:`~GameSession.next_slice_z` (the boule position is the
    session's; ``recipe`` is the player's *process* choice — its ``czochralski.slice_z`` is overridden)
    with seed ``session.seed + wafer_index`` (the determinism contract). An optional ``rework`` folds a
    costly second pass into the turn before scoring. Returns a new session with the profit banked and a
    :class:`RunRecord` appended. Raises if the run is already over (boule exhausted / bankrupt).
    """
    if session.done:
        raise ValueError("the run is over (boule exhausted or bankrupt) — no turn to play")
    cfg = session.config
    z = session.next_slice_z
    base = recipe if recipe is not None else cfg.base_recipe
    recipe_at_z = replace(base, czochralski=replace(base.czochralski, slice_z=z))
    wafer = run_line(recipe_at_z, seed=session.seed + session.wafer_index,
                     variation=cfg.variation, specs=cfg.specs, grid_n=cfg.grid_n,
                     wafer_id=f"W{session.wafer_index}_z{z:04.2f}")
    rework_cost = 0.0
    if rework is not None:
        wafer = _apply_rework(wafer, recipe_at_z, rework, cfg.specs, cfg.variation)
        rework_cost = REWORK_COSTS[rework.kind]
    sc = score_wafer(wafer, prices=cfg.prices, wafer_cost=cfg.wafer_cost, rework_cost=rework_cost)
    rec = RunRecord(wafer_index=session.wafer_index, slice_z=z, scorecard=sc,
                    scrapped=False, reworked=rework is not None,
                    note=(f"{rework.kind} rework" if rework is not None else ""))
    return replace(session, budget=session.budget + sc.profit, history=session.history + (rec,))


def scrap_wafer(session: GameSession, *, note: str = "scrapped — substrate out of spec") -> GameSession:
    """Play one turn by **scrapping** the next slice unprocessed: pay only the scrap cost, no revenue.

    The roguelike "cut your losses" move — when the boule tail will fail anyway, scrapping costs the sunk
    substrate (``scrap_cost``) but avoids the full wafer cost of processing a doomed die. Advances down
    the boule and appends a :class:`RunRecord` (``scrapped=True``). Raises if the run is already over.
    """
    if session.done:
        raise ValueError("the run is over (boule exhausted or bankrupt) — no turn to play")
    cfg = session.config
    sc = ScoreCard(revenue=0.0, cost=cfg.scrap_cost, bin_counts={}, n_good=0, n_total=0)
    rec = RunRecord(wafer_index=session.wafer_index, slice_z=session.next_slice_z, scorecard=sc,
                    scrapped=True, reworked=False, note=note)
    return replace(session, budget=session.budget - cfg.scrap_cost, history=session.history + (rec,))


def play(session: GameSession, decisions) -> GameSession:
    """Run a scripted sequence of decisions (a list of recipes / :class:`ReworkSpec` / ``"scrap"``).

    A convenience driver for the demo and tests: each decision is either ``"scrap"`` (scrap the slice), a
    :class:`Recipe` (process it), or a ``(recipe, ReworkSpec)`` tuple (process + rework). Stops early if
    the run ends (bankrupt). Returns the final session.
    """
    for decision in decisions:
        if session.done:
            break
        if decision == "scrap":
            session = scrap_wafer(session)
        elif isinstance(decision, tuple):
            recipe, rework = decision
            session = process_wafer(session, recipe, rework=rework)
        else:
            session = process_wafer(session, decision)
    return session
