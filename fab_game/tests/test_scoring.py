"""G7 scoring mechanics — revenue/cost bookkeeping closes, and a better bin mix never earns less.

Pure game policy (ADR 0005 §5): the dollar amounts are flagged house numbers, so these assert the
**bookkeeping** (revenue is the dot product of prices and shipped-bin counts; profit = revenue − cost;
unshipped parts earn nothing) and the **monotonicity** (the economic image of "propagation actually
wired" — a strictly-better bin mix scores ≥), never the magnitudes.
"""
from __future__ import annotations

from fab_game.scoring import BIN_PRICES, score_wafer
from fab_game.state import Die, Verdict, WaferState


def _wafer(bins_and_pass: list[tuple[str | None, bool]]) -> WaferState:
    """A synthetic packaged wafer: each entry is (bin label, passed) for one die."""
    dies = tuple(
        Die(site=(i, 0), radius_frac=0.0, i_dsat=3.3e-3, bin=b,
            verdict=Verdict(passed, () if passed else ("failed",)))
        for i, (b, passed) in enumerate(bins_and_pass)
    )
    return WaferState(wafer_id="T", channel_N_A=1e17, dies=dies)


# --------------------------------------------------------------------------- #
# Bookkeeping closes
# --------------------------------------------------------------------------- #
def test_revenue_is_the_dot_product_of_prices_and_shipped_bins():
    w = _wafer([("premium", True), ("typical", True), ("typical", True), ("value", True)])
    sc = score_wafer(w, wafer_cost=50.0)
    assert sc.revenue == BIN_PRICES["premium"] + 2 * BIN_PRICES["typical"] + BIN_PRICES["value"]
    assert sc.bin_counts == {"premium": 1, "typical": 2, "value": 1}
    assert sc.n_good == 4 and sc.n_total == 4
    assert sc.profit == sc.revenue - 50.0                      # profit = revenue − cost (closes)


def test_unshipped_parts_earn_nothing():
    # Front-end fails / scraps / bin-outs (verdict.failed) contribute zero revenue, whatever their bin.
    w = _wafer([("premium", True), (None, False), ("reject", False), ("typical", False)])
    sc = score_wafer(w, wafer_cost=50.0)
    assert sc.revenue == BIN_PRICES["premium"]                 # only the one shipped die earns
    assert sc.n_good == 1 and sc.n_total == 4
    # An all-dead wafer earns nothing and loses exactly the cost.
    dead = _wafer([(None, False)] * 5)
    sd = score_wafer(dead, wafer_cost=50.0)
    assert sd.revenue == 0.0 and sd.profit == -50.0


def test_rework_cost_adds_to_the_cost():
    w = _wafer([("typical", True)] * 3)
    base = score_wafer(w, wafer_cost=50.0)
    reworked = score_wafer(w, wafer_cost=50.0, rework_cost=12.0)
    assert reworked.cost == base.cost + 12.0
    assert reworked.revenue == base.revenue                    # rework cost does not change revenue here
    assert reworked.profit == base.profit - 12.0


# --------------------------------------------------------------------------- #
# Monotonicity — a better bin mix never earns less (the propagation analogue)
# --------------------------------------------------------------------------- #
def test_better_bin_mix_never_scores_less():
    n = 6
    all_value = score_wafer(_wafer([("value", True)] * n))
    all_typical = score_wafer(_wafer([("typical", True)] * n))
    all_premium = score_wafer(_wafer([("premium", True)] * n))
    assert all_value.revenue <= all_typical.revenue <= all_premium.revenue
    # Upgrading exactly one die (others fixed) strictly raises revenue.
    base = _wafer([("typical", True)] * n)
    upgraded = _wafer([("premium", True)] + [("typical", True)] * (n - 1))
    assert score_wafer(upgraded).revenue > score_wafer(base).revenue


def test_prices_are_ordered_premium_highest_reject_zero():
    # FLAGGED house ordering (only the ranking is asserted, not the dollars).
    assert BIN_PRICES["reject"] == 0.0
    assert BIN_PRICES["value"] < BIN_PRICES["typical"] < BIN_PRICES["premium"]
