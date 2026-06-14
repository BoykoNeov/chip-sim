"""The edge-loaded Na ring (the gradual-failure policy) — a marginal feed kills a RING, not the wafer.

The honest *slope* under the Na→Q_ox→V_t **cliff**. A uniform Na shift drives every die's ``V_t``
together → an all-or-nothing flip (decade-spaced grades / ~``1/k``-per-pass refining leap right over
the partial band); modelling mobile-ion sodium as **edge-loaded**
(:meth:`fab_game.variation.Variation.na_factor` ``= 1 + na_edge_boost·r²`` — the real handling / edge-bead
/ furnace radial gradient) makes a marginal feedstock fail an **outboard ring** — the graded
ok→rework→fail band the design wants.

Mechanics, not magnitudes (ADR 0005 §5): ``na_edge_boost`` is a flagged house number (the steepness is
illustrative; the direction/mechanism is real). What is asserted is the **shape** — the factor is 1 at
center and rises to the rim, a marginal feed yields a *partial* wafer whose kills sit *outboard* and trace
to ``Q_ox``, the cliff *returns* when the trend is gated off (the seam), a clean ``Na = 0`` feed is
*untouched*, the ring grows *inward* monotonically as the feed dirties, and a **fractional** refining pass
(the continuous lever) can place the residual *in* the band that integer passes skip.

Runs use the within-wafer ``Variation`` **on** (unlike ``test_contamination.py``, which uses
``NO_VARIATION`` to read the uniform cliff): the ring is *the* point here. The feed is a **Na-only probe**
(injected via ``monkeypatch``) so the mobile-ion channel is isolated — a real grade's residual B/P would
also shift ``V_t`` and muddy the attribution.
"""
from __future__ import annotations

import pytest

from chip import purification as _purif
from chip.purification import Contamination

from fab_game import (
    DEFAULT_RECIPE, NO_VARIATION, PurificationKnobs, Recipe, run_line, wafer_yield,
)
from fab_game.pipeline import diagnose, rework_litho
from fab_game.variation import Variation

# A center Na in the partial band: the uniform threshold is ≈4.5e15, the rim sees 3.5× (boost 2.5) → the
# rim fails while the center holds. (Verified: seed-0 grid_n=9 → ~0.44 yield, the kills an outboard ring.)
MARGINAL_NA = 2.0e15


# --------------------------------------------------------------------------- #
# The radial factor itself — pure, deterministic (no run needed)
# --------------------------------------------------------------------------- #
def test_na_factor_is_one_at_center_and_rises_to_the_rim():
    """``1 + boost·r²``: the wafer-mean Na at the center, ``(1 + boost)`` at the rim, monotone between."""
    v = Variation(na_edge_boost=2.5)
    assert v.na_factor(0.0) == 1.0                       # center die sees the wafer-mean Na
    assert v.na_factor(1.0) == pytest.approx(3.5)        # rim die sees (1 + boost)×
    assert v.na_factor(0.4) < v.na_factor(0.7) < v.na_factor(1.0)   # rises monotonically with radius


def test_na_factor_is_gated_off_when_variation_is_disabled():
    """Disabled variation → factor 1.0 everywhere → uniform Na → the cliff (the seam; even a huge boost)."""
    assert NO_VARIATION.na_factor(1.0) == 1.0
    assert Variation(enabled=False, na_edge_boost=9.0).na_factor(1.0) == 1.0


# --------------------------------------------------------------------------- #
# A marginal feed → a ring, not a flip
# --------------------------------------------------------------------------- #
@pytest.fixture
def marginal_recipe(monkeypatch):
    """A **Na-only** probe feed at the marginal level (isolates the mobile-ion channel) — no refining."""
    monkeypatch.setitem(_purif.FEEDSTOCK_GRADES, "_marginal", Contamination(Na=MARGINAL_NA))
    return Recipe(purification=PurificationKnobs(grade="_marginal", zone_passes=0))


def test_marginal_feed_kills_an_outboard_ring_not_the_whole_wafer(marginal_recipe):
    """The headline: variation on, a marginal Na → a *partial* wafer whose kills are an **outboard ring**
    traced to mobile-ion contamination (Q_ox → V_t) — the graded failure, not an all-or-nothing flip."""
    w = run_line(marginal_recipe, seed=0, variation=Variation(), grid_n=9)
    assert 0.0 < wafer_yield(w) < 1.0                    # PARTIAL — some live, some die (the slope)
    passed = [d.radius_frac for d in w.dies if d.verdict.passed]
    failed = [d.radius_frac for d in w.dies if d.verdict.failed]
    assert passed and failed                             # a ring, not a uniform flip
    assert sum(failed) / len(failed) > sum(passed) / len(passed)   # the kills sit, on average, outboard
    # …and the cause is the contamination (gate-oxide charge), not defocus — the trail names it.
    worst = max((d for d in w.dies if d.verdict.failed), key=lambda d: d.radius_frac)
    trail = diagnose(worst)
    assert "purification" in trail and "Q_ox" in trail
    assert any("V_t" in r for r in worst.verdict.reasons)


def test_the_same_marginal_feed_is_all_pass_without_the_edge_trend(marginal_recipe):
    """Gate the trend off (``NO_VARIATION``) → uniform Na → no ring: at this marginal level the *uniform*
    wafer is fully in spec. So the edge-loading isn't just redistributing existing kills — it **creates**
    failures the wafer-mean Na alone would never show (the rim, at 3.5× the mean, crosses the threshold the
    mean sits under). That is the whole honest point: a graded ring where a uniform model sees a clean pass."""
    w = run_line(marginal_recipe, seed=0, variation=NO_VARIATION, grid_n=9)
    assert wafer_yield(w) == 1.0                          # uniform 2e15 < threshold ⇒ every die passes


def test_clean_feed_is_untouched_by_the_boost():
    """A clean ``Na = 0`` feed → ``0·factor = 0`` → no ring even with variation on and a large boost (the
    clean seam — the gradual-failure trend only bites a feed that actually carries sodium)."""
    w = run_line(DEFAULT_RECIPE, seed=0, variation=Variation(na_edge_boost=9.0), grid_n=9)
    assert w.contamination.is_clean
    assert wafer_yield(w) == 1.0


def test_the_ring_grows_inward_as_the_feed_dirties(monkeypatch):
    """Monotone: a dirtier center pushes the failing ring inward → yield falls — the graded lever (the
    knob the player turns), strictly falling from a clean-enough full wafer down toward a dead one."""
    ys = []
    for na in (1.0e15, 2.0e15, 3.0e15, 4.0e15):
        monkeypatch.setitem(_purif.FEEDSTOCK_GRADES, "_m", Contamination(Na=na))
        rec = Recipe(purification=PurificationKnobs(grade="_m", zone_passes=0))
        ys.append(wafer_yield(run_line(rec, seed=0, variation=Variation(), grid_n=9)))
    assert ys[0] == 1.0                                  # clean-enough center ⇒ full wafer
    assert ys[0] > ys[1] > ys[2] > ys[3]                 # the ring eats inward as Na rises


# --------------------------------------------------------------------------- #
# The continuous refining lever — a fractional pass reaches the band integers skip
# --------------------------------------------------------------------------- #
def test_a_fractional_pass_lands_the_band_integer_passes_leap_over(monkeypatch):
    """The continuous lever (``front_purity``'s ``k^n`` is smooth in ``n``): a dirty feed is *dead* raw and
    *clean* after one full pass — integer passes leap from 0 % to 100 % (~``1/k`` per pass) — but a
    **fractional** pass places the residual Na *in* the marginal band → the partial ring."""
    monkeypatch.setitem(_purif.FEEDSTOCK_GRADES, "_dirty", Contamination(Na=5.0e16))

    def yield_at(passes: float) -> float:
        rec = Recipe(purification=PurificationKnobs(grade="_dirty", zone_passes=passes))
        return wafer_yield(run_line(rec, seed=0, variation=Variation(), grid_n=9))

    assert yield_at(0.0) == 0.0                           # raw dirty feed: every die dead
    assert yield_at(1.0) == 1.0                           # one full pass: scrubbed clean
    assert 0.0 < yield_at(0.7) < 1.0                      # a fractional pass: the marginal ring in between


# --------------------------------------------------------------------------- #
# The Na ring is its own channel — composes with the focus bowl, immune to litho rework
# --------------------------------------------------------------------------- #
def test_na_ring_composes_with_the_focus_bowl_without_double_counting(marginal_recipe):
    """The Na ring (Q_ox→V_t) and the focus bowl (CD→NILS) are **different spec channels**, so they stack
    rather than double-count. A small defocus that is harmless on a clean feed neither rescues nor
    spuriously amplifies the Na ring — its yield is unchanged and its kills still trace to ``Q_ox``."""
    from dataclasses import replace

    var = Variation()
    na_alone = wafer_yield(run_line(marginal_recipe, seed=0, variation=var, grid_n=9))
    # 40 nm of global defocus is harmless on its own (even with the bowl, the rim stays above the NILS floor):
    clean_defocus = Recipe(litho=replace(DEFAULT_RECIPE.litho, defocus_nm=40.0))
    assert wafer_yield(run_line(clean_defocus, seed=0, variation=var, grid_n=9)) == 1.0
    # …so adding it to the marginal feed cannot rescue, and does not amplify (no shared draw / channel):
    both = replace(marginal_recipe, litho=replace(marginal_recipe.litho, defocus_nm=40.0))
    w = run_line(both, seed=0, variation=var, grid_n=9)
    assert wafer_yield(w) <= na_alone                     # defocus never rescues the Na ring
    worst = max((d for d in w.dies if d.verdict.failed), key=lambda d: d.radius_frac)
    assert "Q_ox" in diagnose(worst)                      # the kill is still the Na channel, not the bowl


def test_litho_rework_does_not_rescue_a_contamination_fail(marginal_recipe):
    """The honest "only purification fixes sodium" story: litho rework strips & re-exposes the failed dies,
    but the mobile-ion Na (and its radial edge-loading) rides on the wafer — re-imaging re-applies the same
    ``Q_ox`` → the ring is **not** recovered. (Contrast the focus-error rework, which a focus correction
    *does* rescue: the cure has to match the cause — purify harder, don't re-expose.)"""
    var = Variation()
    w = run_line(marginal_recipe, seed=0, variation=var, grid_n=9)
    reworked = rework_litho(w, marginal_recipe, variation=var, focus_correction_nm=0.0)
    assert wafer_yield(reworked) == wafer_yield(w)        # re-exposure cannot remove sodium → no recovery
