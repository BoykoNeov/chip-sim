"""Integration test for the C1 demo (the demo IS the integration check).

The C1 demo shows crucible oxygen → thermal donors → the substrate's electrical drift: the donor
density saturates with the ~450 °C anneal, the device V_t walks down (a high-oxygen boule scraps via the
floor), and the cited Kaiser–Frisch–Reiss fourth-power initial rate (with the flagged cube-law ceiling)
shows as two clean log–log slopes. Asserted on the robust, **honest** theses — the *direction* and the
power-law slopes, not brittle numbers (the physics is pinned in ``chip/tests/test_czochralski.py`` and
the wiring in ``test_thermal_donors.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is a "builds without error" smoke
test only, skipped where the optional viz extra is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

from fab_game.demo_thermal_donors import compute


@pytest.fixture(scope="module")
def r():
    """The demo result, computed once and shared (the per-(oxygen, anneal) pipeline runs are the cost)."""
    return compute()


def test_demo_kinetics_saturate_from_zero_at_no_anneal(r):
    """Panel 1: N_TD rises from 0 at no anneal (the seam) toward the flagged ceiling, monotone, and
    bounded by N_sat — more oxygen → a higher ceiling (the steep cube law)."""
    for label in r.oxygen_labels:
        n_td = list(r.n_td_by_oxygen[label])
        assert n_td[0] == 0.0                                    # no anneal ⇒ no donors (the seam)
        assert n_td == sorted(n_td)                              # monotone rising with anneal time
        assert max(n_td) <= r.saturation_by_oxygen[label] + 1.0  # bounded by the (flagged) ceiling
    # More oxygen → a higher saturation ceiling (low < typical < high).
    sats = [r.saturation_by_oxygen[lab] for lab in r.oxygen_labels]
    assert sats == sorted(sats)


def test_demo_vt_walks_down_and_high_oxygen_scraps(r):
    """Panel 2: V_t falls with anneal time (donors compensate the substrate), more steeply at higher
    oxygen; the high-oxygen boule exits the spec floor (a scrap), the low one barely moves (stays good)."""
    for label in r.oxygen_labels:
        vt = list(r.vt_by_oxygen[label])
        assert vt[-1] <= vt[0] + 1e-9                            # V_t walks DOWN with the anneal
    # At the longest anneal, more oxygen → a lower V_t (a steeper drift).
    finals = [r.vt_by_oxygen[lab][-1] for lab in r.oxygen_labels]
    assert finals == sorted(finals, reverse=True)               # low > typical > high
    # The consequence: the high-oxygen boule scraps (yield → 0), the low-oxygen one survives.
    assert r.yield_by_oxygen["high"][-1] == 0.0
    assert r.yield_by_oxygen["low"][-1] == 1.0
    assert min(finals) >= r.v_t_lo - 1.0                        # still p-type (no inversion crash)


def test_demo_cited_fourth_power_and_flagged_cube_slopes(r):
    """Panel 3: the cited initial rate is a [O_i]⁴ power law and the flagged saturation a [O_i]³ one —
    the log–log slopes recover the exponents (the KFR fourth power is the load-bearing anchor)."""
    o = np.log(np.asarray(r.oxygen_sweep))
    rate_slope = np.polyfit(o, np.log(np.asarray(r.formation_rate_sweep)), 1)[0]
    sat_slope = np.polyfit(o, np.log(np.asarray(r.saturation_sweep)), 1)[0]
    assert rate_slope == pytest.approx(r.rate_exponent, abs=1e-6)   # ∝ [O_i]⁴ — the cited KFR fourth power
    assert sat_slope == pytest.approx(r.sat_exponent, abs=1e-6)     # ∝ [O_i]³ — the flagged cube law


def test_thermal_donor_figure_builds(r):
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from fab_game.plots import thermal_donor_figure

    fig = thermal_donor_figure(r)
    assert len(fig.axes) >= 3                                    # kinetics / V_t walk / power-law panels
    plt.pyplot.close(fig)
