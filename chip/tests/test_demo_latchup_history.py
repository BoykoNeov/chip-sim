"""Integration test for the B12 latchup history demo — the F7-remainder payload, end-to-end.

``test_latchup.py`` exercises :mod:`chip.latchup` with hardcoded inputs and never calls the demo: it
already pins the two cited criteria, the decoupling, the monotone directions and the calibration
quarantine, and none of that is re-asserted here. This test guards what only the demo can break — the
**chaining** and the **words**:

  * **LOCOS's spacing is B5's beak, computed here and not assumed** — the demo calls
    :mod:`chip.locos_history` for it, which is the whole reason B12 reads as the second half of B5
    rather than a module beside it. If that chain breaks, the figure silently becomes two house
    numbers being compared;
  * **the three era points are the ones the caption names**, in the order the caption claims (STI's
    bare gain above LOCOS, the trench pulling it back down, and not all the way);
  * **the payback is a genuine fraction** — strictly between 0 and 1, which is the claim "partly, and
    no more". A payback ≥ 1 would mean the trench undid the density penalty entirely and the rung
    would have no bill to be about;
  * **the right panel's curve actually crosses** the drawn disturbance inside the swept range, so the
    "LATCHES" shading is not an empty region — while never asserting *where*, since that rides the
    flagged tap geometry;
  * **the figure's words**, which the fast lane otherwise cannot check (the golden gallery tests
    confirm the prose did not *change*, never that it is still *true*).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
from pathlib import Path

import numpy as np
import pytest

from chip import latchup as lu
from chip import demo_latchup_history as demo
from chip import locos_history as lh


@pytest.fixture(scope="module")
def r():
    return demo.compute()


# --------------------------------------------------------------------------- #
# the chaining — B12 is the second half of B5, and this is where that is true
# --------------------------------------------------------------------------- #
def test_locos_spacing_is_the_beak_b5_computes_not_a_house_number(r):
    """The demo must *call* :mod:`chip.locos_history`, not restate a constant that resembles it."""
    field_ox = lh.field_oxide_thickness_um()
    beak = lh.birds_beak_length_um(field_ox)
    assert r.field_ox_um == field_ox
    assert r.beak_um == beak
    assert r.locos_spacing_um == pytest.approx(demo.DRAWN_SPACING_UM + 2.0 * beak)
    # ... and that is strictly more spacing than STI needs — the packing floor B5 ended on.
    assert r.locos_spacing_um > r.sti_spacing_um


def test_sti_base_is_the_drawn_spacing_plus_the_cited_trench_detour(r):
    """STI keeps the drawn width; its trench then lengthens the parasitic base by the detour."""
    assert r.sti_spacing_um == demo.DRAWN_SPACING_UM
    assert r.sti_base_um == pytest.approx(demo.DRAWN_SPACING_UM + 2.0 * lu.STI_DEPTH_UM)


# --------------------------------------------------------------------------- #
# the era points, in the order the caption claims
# --------------------------------------------------------------------------- #
def test_the_three_era_points_are_ordered_the_way_the_caption_says(r):
    """Bare STI is the worst, LOCOS the best, and as-built STI sits between them — closer to LOCOS.

    Every clause of the left panel's story in one assertion chain; if any inverts, the caption is a
    lie and this fails rather than the figure quietly telling the wrong era.
    """
    assert r.gain_locos < r.gain_sti_trench < r.gain_sti_bare
    assert r.density_penalty > r.as_built_penalty > 1.0


def test_the_trench_payback_is_a_real_fraction(r):
    """Strictly between 0 and 1 — "partly, and no more".

    ``payback ≥ 1`` would mean the trench fully undid the density penalty and the rung would have no
    bill to be about; ``≤ 0`` would mean it made things worse. Both would invalidate the caption.
    """
    assert 0.0 < r.trench_payback < 1.0


def test_the_quoted_ratios_are_the_geometric_ones(r):
    """The caption quotes the ratios *because* they are coefficient-free: β ≈ 2L²/W_B², so a ratio is
    the inverse square of the base widths and the diffusion length cancels. Asserted against pure
    geometry — no gain call on the right-hand side."""
    assert r.density_penalty == pytest.approx((r.locos_spacing_um / r.sti_spacing_um) ** 2, rel=1e-4)
    assert r.as_built_penalty == pytest.approx((r.locos_spacing_um / r.sti_base_um) ** 2, rel=1e-4)


# --------------------------------------------------------------------------- #
# the right panel — the condition that decides
# --------------------------------------------------------------------------- #
def test_the_trigger_curve_crosses_the_drawn_disturbance_inside_the_swept_range(r):
    """The "LATCHES" shading must be a real region, not an empty one — otherwise the panel draws a
    wall nobody can hit. Asserts only that a crossing exists in range, never *where*: the location
    rides the flagged tap geometry and is not a result."""
    assert r.trigger_ma.max() > r.injected_ma > r.trigger_ma.min()


def test_the_trigger_curve_falls_monotonically_with_resistivity(r):
    """Lighter substrate ⇒ higher R_sub ⇒ lower trigger current. The cited prevention direction, on
    the demo's own swept array rather than on the module's."""
    assert np.all(np.diff(r.trigger_ma) < 0.0)


def test_the_simulators_own_boule_sits_on_the_safe_side(r):
    """The band the figure draws is not tuned to fail: this line's own wafers clear the disturbance by
    a wide margin, and the era point is made by the *curve*, not by this sim being in danger."""
    for rho in (demo.BOULE_RHO_SEED_OHM_CM, demo.BOULE_RHO_TAIL_OHM_CM):
        ma = lu.trigger_current_a(lu.substrate_resistance_from_resistivity_ohm(rho)) * 1.0e3
        assert ma > r.injected_ma


def test_the_boule_band_runs_the_direction_the_caption_claims():
    """Boron's k < 1 ⇒ concentration rises down the boule ⇒ resistivity FALLS ⇒ the trigger RISES, so
    the seed end is the vulnerable one. The caption's "later wafers are SAFER" arrow depends on this
    ordering of the two banded constants."""
    assert demo.BOULE_RHO_TAIL_OHM_CM < demo.BOULE_RHO_SEED_OHM_CM


# --------------------------------------------------------------------------- #
# the figure builds
# --------------------------------------------------------------------------- #
def test_figure_builds(r, tmp_path, monkeypatch):
    pytest.importorskip("matplotlib")
    monkeypatch.setattr(demo, "DOCS_FIGURE", Path(tmp_path) / "b12.png")
    saved = demo.save_figure(r)
    assert saved.exists() and saved.stat().st_size > 0


def test_summary_prints(r, capsys):
    """The summary must name the rung's two conditions and its own admission — a smoke test on the
    words the figure's caption is derived from."""
    demo.print_summary(r)
    out = capsys.readouterr().out
    assert "SUSTAINING" in out and "TRIGGERING" in out
    assert "coefficient-free" in out
    assert "upper bound" in out
