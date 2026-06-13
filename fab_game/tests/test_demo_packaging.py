"""Integration test for the G6 packaging demo (the demo IS the integration check).

The packaging demo wires the new cumulative assembly-yield funnel (:mod:`chip.packaging`) and the
binning partition through the harness into the back-end artifact. Its ``compute`` is the end-to-end
check that the funnel narrows step-by-step toward the cited ``Π yᵢ``, that process control sets the
speed-bin mix (a loose process spreads the grades and bins a tail out), and that every back-end outcome
appears on the packaged wafer — asserted on the robust thesis, not brittle numbers (the physics is
pinned in ``chip/tests/test_packaging.py``, the wiring in ``test_packaging.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import pytest

from fab_game.demo_packaging import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed **once** and shared across the smoke tests (the demo's pipeline runs
    are the costly part; the four assertions below are read-only views of one result)."""
    return compute()


def test_demo_funnel_narrows_to_the_cited_assembly_yield(r):
    """The cumulative funnel is monotone non-increasing and ends at the cited Π yᵢ; the realized
    single-wafer survival hugs that product (the wire-bond is the narrow neck)."""
    cum = r.funnel_cumulative
    assert cum[0] == 1.0                                       # the funnel starts at the front-end-good base
    assert all(b <= a for a, b in zip(cum, cum[1:]))          # each step multiplies down (monotone)
    assert cum[-1] == pytest.approx(r.funnel_assembly_yield)  # the funnel ends at Π yᵢ
    assert abs(r.funnel_empirical - r.funnel_assembly_yield) < 0.06   # realized ≈ cited (one wafer)
    # The bond is the dominant loss (the busiest back-end step).
    drops = [a - b for a, b in zip(cum, cum[1:])]
    assert drops[2] == max(drops)                             # the 3rd step (bond) is the biggest drop


def test_demo_loose_process_spreads_the_bins_and_bins_out_a_tail(r):
    """A tight process concentrates parts in the fast grades; a loose one spreads them across grades and
    spills a reject (bin-out) tail — the process-control pedagogy, the binning propagation."""
    # Tight: nothing bins out (good CD control keeps everyone sellable).
    assert r.tight_hist["reject"] == 0
    # Loose: the spread reaches the slow grade AND bins a tail out (working but too slow).
    assert r.loose_hist["value"] > r.tight_hist["value"]
    assert r.loose_hist["reject"] > 0
    # The loose drive-current sample is genuinely wider than the tight one (the spread that sorts).
    import numpy as np
    assert np.std(r.loose_idsat) > np.std(r.tight_idsat)


def test_demo_packaged_wafer_has_a_back_end_death(r):
    """The packaged wafer (loose process + a degraded bond) carries a back-end death — a part with a
    working front end that still never shipped (assembly scrap or bin-out), named in the trail."""
    assert any(d.assembled is False or d.bin == "reject" for d in r.outcome_wafer.dies)
    assert ("assembly scrap" in r.dead_trail) or ("binned out" in r.dead_trail)


def test_packaging_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import packaging_figure

    fig = packaging_figure(r)
    assert len(fig.axes) >= 3                                 # funnel / binning / outcome-map panels
    plt.pyplot.close(fig)
