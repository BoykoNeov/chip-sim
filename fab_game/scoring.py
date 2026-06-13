"""Scoring — turn a packaged wafer's bins into revenue, cost, and profit (the roguelike payoff, G7).

The economics layer of the game shell (plan §6 G7, §9; ADR 0005). G1–G6 carried a wafer from sand to a
*binned* die map; G7 turns that map into a **score**: each shipped part earns its bin's price, each
wafer started (and each rework) costs money, and profit = revenue − cost. This is **pure game policy**,
not physics — every number here is a **flagged house value** (ADR 0005 §5: the game is scored on
mechanics, not magnitudes), so the tests assert *bookkeeping* (revenue = the dot product of prices and
bin counts; profit closes) and *monotonicity* (a better bin mix never earns less), never the dollar
amounts.

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

from .state import WaferState

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
) -> ScoreCard:
    """Score a packaged wafer → its :class:`ScoreCard` (revenue − cost = profit).

    Revenue is the sum of ``prices[die.bin]`` over the **shipped** dies (``verdict.passed`` — which by
    construction carry a sellable bin; an unpriced/unknown bin earns ``0``). The cost is ``wafer_cost +
    rework_cost``. Pure bookkeeping: a die that did not ship (front-end fail / assembly scrap / bin-out)
    contributes nothing, so ``revenue`` is monotone in bin upgrades and ``profit = revenue − cost``.
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
        cost=wafer_cost + rework_cost,
        bin_counts=bin_counts,
        n_good=n_good,
        n_total=wafer.n_dies,
    )
