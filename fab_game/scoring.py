"""Scoring — turn a packaged wafer's bins into revenue, cost, and profit (the roguelike payoff, G7).

The economics layer of the game shell (plan §6 G7, §9; ADR 0005). G1–G6 carried a wafer from sand to a
*binned* die map; G7 turns that map into a **score**: each shipped part earns its bin's price, each
wafer started (and each rework) costs money, and profit = revenue − cost. This is **pure game policy**,
not physics — every number here is a **flagged house value** (ADR 0005 §5: the game is scored on
mechanics, not magnitudes), so the tests assert *bookkeeping* (revenue = the dot product of prices and
bin counts; profit closes) and *monotonicity* (a better bin mix never earns less), never the dollar
amounts.

The process-cost side — the Goldilocks half of a decision (the fab-journey's #1 open item)
-------------------------------------------------------------------------------------------
:func:`process_cost` is the **cost side** of a recipe decision — the half that turns a *one-sided*
journey stage into a two-sided Goldilocks. Three journey stages (:mod:`fab_game.journey`) penalize only
*under*-doing the stage (the forecast yield bands: too little refining → an Na ring, too little dose →
an ``I_Dsat`` starve), so absent a cost the optimal play is "do it forever." :func:`process_cost` prices
*over*-doing it:

* **refining** — a per-pass cost ∝ ``zone_passes`` (more passes, cleaner feed, but each costs money);
* **the S/D predep** — a thermal-budget cost ∝ the predep's diffusion budget ``∫D dt`` (the real E1
  quantity, :func:`chip.diffusion_dopant.thermal_budget`'s isothermal case — so the cost rises with the
  same dose the ``I_Dsat`` yield responds to, and a hotter predep is priced, not just a longer one).

The **slice/cut** stage's missing cost — the value of cutting deeper (more wafers per boule = throughput)
— is **deferred, not built here** (advisor): per-wafer boule amortization depends on how many *in-spec*
wafers the boule yields, which is set by the **pull rate** (the CG-1 Scheil flattening), not by where a
*single* wafer is cut. The two-sidedness is inherently **multi-wafer** — and that model already exists as
the roguelike (:mod:`fab_game.game`, ``n_wafers`` down one boule). Crediting one wafer with boule-level
throughput would attribute to the *cut* an economics actually driven by the *pull* — the "inflate an
unrelated variable" shape the repo refuses. So the cut stays one-sided in single-wafer ``finish`` by
design; its throughput cost is a roguelike/boule-level concept.

Each side has a clean **interior** profit maximum because the yield it unlocks **saturates** (refine
until clean → 1.0; dose until ``I_Dsat`` clears the floor → 1.0): past saturation the marginal revenue is
~0, so any positive marginal cost creates a stop-point. The load-bearing test (``test_journey``) is that
**net profit is non-monotone in the lever** — ``profit(under) < profit(opt) > profit(over)`` — the
economic image of "the Goldilocks half is wired", the analogue of the growth window's two-sidedness.

**Where the cost is charged (an honest divergence, named).** ``score_wafer`` takes ``process_cost`` as a
flat add-on (default ``0.0``, mirroring ``rework_cost``), so the **roguelike** (:mod:`fab_game.game`,
which passes nothing) is byte-for-byte unchanged — its difficulty is the Scheil ``V_t`` drift + the oxide
adapt lever, not these three stages. Only the **journey's** :func:`fab_game.journey.finish` is the
consumer: it computes :func:`process_cost` from the committed recipe and threads ``.total`` in. This is a
deliberate divergence from the journey's "reuse the ``GameConfig`` economics, don't fork" rule (the
revenue side *is* reused); it is consumer-driven (the journey is where the one-sided stages live), and
:func:`process_cost` lives **here** so the roguelike can adopt the cost side later without a second
implementation.

The market — bin prices
-----------------------
Parts are graded by drive current (``I_Dsat`` as the speed proxy — G6 binning) into value grades;
faster parts sell for more. A front-end fail / assembly scrap / bin-out earns **nothing** (an
unshipped part). Only a die the line passed (``verdict.passed`` — which by construction carries a
sellable bin) earns its grade's price.

Validation (ADR 0005 §5 — mechanics, not magnitudes)
----------------------------------------------------
* **Bookkeeping closes.** ``revenue = Σ price[bin]·count`` over the shipped dies; ``profit = revenue −
  cost``; no money is created or destroyed. The cost is the wafer cost plus any rework cost.
* **Monotonicity (the propagation analogue).** Upgrading any die to a higher-priced bin (others fixed)
  never lowers the revenue; a wafer with a strictly-better bin mix scores ``≥``. This is what makes a
  better-run wafer worth more — the economic image of "propagation actually wired."

Units: all prices/costs are dimensionless **house dollars** ($), flagged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .state import WaferState

if TYPE_CHECKING:
    from .recipe import Recipe

# --------------------------------------------------------------------------- #
# The market + the line costs — FLAGGED house numbers, NOT cited (ADR 0005 §5).
# Faster parts (premium speed bin) sell for more; an unshipped part earns nothing. Only the *ordering*
# (premium > typical > value > reject = 0) and the bookkeeping are asserted; the dollars are house.
# --------------------------------------------------------------------------- #
BIN_PRICES: dict[str, float] = {
    "premium": 10.0,   # the fastest parts — the premium speed bin
    "typical": 6.0,    # the nominal grade
    "value": 3.0,      # slow but still sellable
    "reject": 0.0,     # binned out — a working but out-of-grade part does not ship
}

WAFER_COST: float = 80.0       # $ to grow/slice/process one wafer through the line (materials + run)
SCRAP_COST: float = 20.0       # $ sunk in a wafer the player scraps before processing (the substrate is gone)
REWORK_COSTS: dict[str, float] = {  # $ per rework action (a costly second pass)
    "litho": 12.0,             # strip resist & re-expose
    "polish": 10.0,            # re-CMP (eats thickness)
    "deposition": 11.0,        # strip & re-deposit a voided film
}

# --------------------------------------------------------------------------- #
# The process-cost side — FLAGGED house numbers (ADR 0005 §5), the Goldilocks half of a recipe decision.
# Calibrated (against the measured yield-vs-lever curves) so each one-sided journey stage has a clean
# INTERIOR profit maximum: enough cost that over-doing the stage past yield-saturation loses money, little
# enough that doing it *to* saturation pays for itself. The tests assert the interior-maximum *mechanic*,
# never these dollars (only the ordering/shape is a claim — the magnitudes are house).
# --------------------------------------------------------------------------- #
REFINE_COST_PER_PASS: float = 30.0    # $ per zone-refining pass (effort) — the purification per-pass cost.
#                                       More passes scrub the feed cleaner (the Na ring shrinks → yield up),
#                                       but each pass costs money, so "refine until clean" stops AT clean
#                                       (yield saturates ~1 pass; past it the marginal pass is pure cost).
DIFFUSION_BUDGET_COST_PER_CM2: float = 1.14e14  # $ per cm² of predep diffusion budget ∫D dt — the S/D
#                                       predep thermal-budget (cycle-time / furnace) cost. Tied to the
#                                       real ∫D dt (E1's quantity) so it rises with the same dose the
#                                       I_Dsat yield responds to AND prices a *hotter* predep, not just a
#                                       longer one (raising T to get dose for free is not a loophole).
#                                       Calibrated so a just-saturated predep (~900 °C/5 min, ∫D dt ≈
#                                       2.2e-13 cm²) costs ≈ $25; note the recipe-default 950 °C/10 min
#                                       predep is ~9× over-dosed for the I_Dsat floor and so costs ≈ $220
#                                       — the cost side *revealing* the textbook default over-diffuses
#                                       (the lesson), and why the journey/demo operate the cooler regime.


@dataclass(frozen=True)
class ScoreCard:
    """One wafer's economics: revenue from the shipped parts, the cost incurred, and the bin breakdown.

    ``bin_counts`` is the per-grade count of **shipped** (``verdict.passed``) dies; ``n_good`` their
    total, ``n_total`` the die map size (so ``n_total − n_good`` is the unshipped count — front-end
    fails + assembly scraps + bin-outs, all earning nothing). ``revenue`` is the dot product of
    :data:`BIN_PRICES` and ``bin_counts``; ``cost`` the wafer cost plus any rework; ``profit`` the
    difference.
    """

    revenue: float
    cost: float
    bin_counts: dict[str, int]
    n_good: int
    n_total: int

    @property
    def profit(self) -> float:
        return self.revenue - self.cost

    @property
    def yield_(self) -> float:
        return self.n_good / self.n_total if self.n_total else 0.0


def score_wafer(
    wafer: WaferState,
    *,
    prices: dict[str, float] = BIN_PRICES,
    wafer_cost: float = WAFER_COST,
    rework_cost: float = 0.0,
    process_cost: float = 0.0,
) -> ScoreCard:
    """Score a packaged wafer → its :class:`ScoreCard` (revenue − cost = profit).

    Revenue is the sum of ``prices[die.bin]`` over the **shipped** dies (``verdict.passed`` — which by
    construction carry a sellable bin; an unpriced/unknown bin earns ``0``). The cost is ``wafer_cost +
    rework_cost + process_cost``. Pure bookkeeping: a die that did not ship (front-end fail / assembly
    scrap / bin-out) contributes nothing, so ``revenue`` is monotone in bin upgrades and ``profit =
    revenue − cost``.

    ``process_cost`` (default ``0.0``, mirroring ``rework_cost``) is the recipe-decision cost side
    (:func:`process_cost` — the per-pass refining + predep thermal-budget costs). It is **0 by default**
    so the roguelike (:mod:`fab_game.game`, which passes nothing) is byte-for-byte unchanged; only the
    journey's :func:`fab_game.journey.finish` threads it in. Like ``rework_cost`` it raises the cost
    without touching the revenue (so the front-end **yield** is unchanged — the seam the journey's
    yield-agreement test relies on).
    """
    bin_counts: dict[str, int] = {}
    revenue = 0.0
    n_good = 0
    for d in wafer.dies:
        if d.verdict is not None and d.verdict.passed:
            n_good += 1
            label = d.bin if d.bin is not None else "reject"
            bin_counts[label] = bin_counts.get(label, 0) + 1
            revenue += prices.get(label, 0.0)
    return ScoreCard(
        revenue=revenue,
        cost=wafer_cost + rework_cost + process_cost,
        bin_counts=bin_counts,
        n_good=n_good,
        n_total=wafer.n_dies,
    )


# --------------------------------------------------------------------------- #
# The process-cost side — the Goldilocks half of a one-sided recipe decision
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ProcessCost:
    """The cost side of a recipe's one-sided decisions — the per-stage breakdown + the total.

    ``refine`` the zone-refining per-pass cost (∝ ``zone_passes``); ``diffusion`` the S/D predep
    thermal-budget cost (∝ the predep ``∫D dt``, charged only when the diffusion stage is engaged as a
    decision — ``sd_contact_squares > 0`` — so cost and the ``I_Dsat`` consequence co-engage). The
    **cut/throughput** cost is deliberately absent (a multi-wafer/roguelike concept — see the module
    docstring). All in flagged house dollars; :attr:`total` is what :func:`score_wafer` consumes.
    """

    refine: float
    diffusion: float

    @property
    def total(self) -> float:
        return self.refine + self.diffusion


def _predep_budget_cm2(recipe: "Recipe") -> float:
    """The S/D predep's diffusion budget ``∫D dt = D(T_predep)·t_predep`` (cm²) — the cost basis.

    The isothermal case of E1's :func:`chip.diffusion_dopant.thermal_budget` (a predep holds one
    setpoint), computed from the same :func:`chip.diffusion_dopant.diffusivity` the dose uses — so the
    dollar cost is the *real* diffusion age the predep deposits, monotone in both ``T_predep`` and
    ``t_predep`` (the dose is ∝ ``√(∫D dt)``).
    """
    from chip.diffusion_dopant import diffusivity
    d = recipe.diffusion
    return diffusivity(d.dopant, d.T_predep_C) * d.t_predep_min * 60.0


def process_cost(recipe: "Recipe") -> ProcessCost:
    """The :class:`ProcessCost` of a recipe — the cost side of its one-sided journey decisions.

    * **refine** = :data:`REFINE_COST_PER_PASS` × ``zone_passes`` (zero at no refining — a fresh journey
      starts at effort 0, so it pays only for the passes it chooses).
    * **diffusion** = :data:`DIFFUSION_BUDGET_COST_PER_CM2` × the predep ``∫D dt`` — **gated** on the
      diffusion stage being an engaged decision (``diffusion.sd_contact_squares > 0``, the same flag that
      turns on the ``I_Dsat`` series-R consumer), so cost and consequence appear together and a journey
      that never diffuses is charged ``0`` (the recipe always *has* a default predep, but it is not this
      journey's decision until engaged). A predep engaged at the over-dosed recipe nominal (950 °C/10 min)
      is the most expensive choice — the cost side revealing the default over-diffuses.

    Only the journey's :func:`fab_game.journey.finish` calls this (the roguelike passes ``process_cost=0``
    to :func:`score_wafer`); it lives here so the roguelike can adopt the cost side later without a fork.
    """
    refine = REFINE_COST_PER_PASS * float(recipe.purification.zone_passes)
    if recipe.diffusion.sd_contact_squares > 0.0:
        diffusion = DIFFUSION_BUDGET_COST_PER_CM2 * _predep_budget_cm2(recipe)
    else:
        diffusion = 0.0
    return ProcessCost(refine=refine, diffusion=diffusion)
