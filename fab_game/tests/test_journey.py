"""The staged sand→chip journey, phase 1 — the purification stage (``fab_game.journey``).

Mechanics, not magnitudes (ADR 0005 §5). The journey builds one wafer's recipe stage by stage; phase 1
makes **purification** the live decision (pick a feedstock, refine it step by step) and every later stage
runs at its default. What is asserted: the refining **trajectory** scrubs the impurity vector with the
cited segregation contrast (Na/Fe/Cu fall, boron barely moves); the **forecast** bands the recipe-so-far
on the ok→rework→fail spectrum (``dead`` → ``ring`` → ``clean``) and **names the channel** (mobile-ion
``V_t`` vs deep-level-metal leakage — so a feed that looks fine on threshold can still die on leakage);
the accumulator (``current_recipe`` overlay + ``commit`` fold) carries the decision; the state is
immutable, the log append-only, the forecast deterministic; and ``finish`` runs + scores end-to-end.

Zero new physics — the journey composes :func:`run_line` + :func:`score_wafer` (the line and economics are
tested elsewhere). The live UI is the deferred next increment; this is the headless core.
"""
from __future__ import annotations

import pytest

from fab_game.journey import (
    GROWTH_G_CENTER_K_PER_MM,
    GROWTH_RADIAL_BOOST,
    JourneyState,
    StageForecast,
    boule_profile,
    consequence_band,
    finish,
    forecast,
    new_journey,
    refining_trajectory,
)
from fab_game.pipeline import LineResult
from fab_game.scoring import ScoreCard


# --------------------------------------------------------------------------- #
# The band map (pure)
# --------------------------------------------------------------------------- #
def test_consequence_band_thresholds():
    """The ok→rework→fail spectrum with a margin so a boundary forecast doesn't flicker."""
    assert consequence_band(1.0) == "clean"
    assert consequence_band(0.97) == "clean"
    assert consequence_band(0.66) == "ring"
    assert consequence_band(0.30) == "ring"
    assert consequence_band(0.0) == "dead"
    assert consequence_band(0.02) == "dead"


# --------------------------------------------------------------------------- #
# The refining trajectory — the cited segregation contrast
# --------------------------------------------------------------------------- #
def test_refining_trajectory_scrubs_metals_hardest_and_boron_least():
    """Na/Fe/Cu fall by ``k^n`` (Fe fastest, tiny k), boron barely moves (k≈0.8) — the teachable contrast."""
    traj = refining_trajectory("MGS", max_effort=2.0, step=0.5)
    efforts = [e for e, _ in traj]
    assert efforts[0] == 0.0 and efforts[-1] == 2.0          # spans raw → 2 passes
    nas = [c.Na for _, c in traj]
    fes = [c.Fe for _, c in traj]
    bs = [c.B for _, c in traj]
    assert nas == sorted(nas, reverse=True)                  # Na monotone down with effort
    assert fes[-1] / fes[0] < nas[-1] / nas[0]               # Fe scrubbed harder than Na (tinier k)
    assert bs[-1] / bs[0] > nas[-1] / nas[0]                 # boron barely moves vs Na (k≈0.8)
    assert bs[-1] / bs[0] > 0.5                              # …still over half its feed value after 2 passes


def test_trajectory_rejects_an_unknown_grade():
    with pytest.raises(ValueError):
        refining_trajectory("unobtainium")


# --------------------------------------------------------------------------- #
# The consequence forecast — the band + the channel it fails on
# --------------------------------------------------------------------------- #
def test_forecast_walks_dead_to_ring_to_clean_as_the_feed_is_refined():
    """The showcase arc on a solar feed: raw → dead, a fractional refine → the graded V_t ring, more → clean."""
    dead = forecast(JourneyState(grade="solar", effort=0.0))
    ring = forecast(JourneyState(grade="solar", effort=0.75))
    clean = forecast(JourneyState(grade="solar", effort=1.5))
    assert dead.band == "dead" and dead.yield_ == 0.0
    assert ring.band == "ring" and 0.0 < ring.yield_ < 1.0   # the partial edge ring (rework territory)
    assert clean.band == "clean" and clean.yield_ == 1.0


def test_forecast_names_the_vt_channel_for_a_sodium_feed():
    """A solar (Na-bearing) feed in the ring band fails on the mobile-ion ``V_t`` channel — named, not just
    a number (the consequence the player watches propagate)."""
    f = forecast(JourneyState(grade="solar", effort=0.75))
    assert f.channel is not None and "V_t" in f.channel
    assert "ring" in f.headline and "%" in f.headline


def test_forecast_names_the_leakage_channel_for_a_metal_feed():
    """The metal grade is **clean on threshold** (Na = 0 → V_t fine) yet dies on junction **leakage** (Fe/Cu)
    — a different channel from the Na ring (the metal-grade finding, surfaced by the forecast)."""
    f = forecast(JourneyState(grade="metal", effort=0.0))
    assert f.band == "dead"
    assert f.channel is not None and "leakage" in f.channel.lower()


def test_clean_feed_forecasts_clean_with_no_channel():
    """A clean feed → full yield, the ``clean`` band, no failing channel (the seam)."""
    f = forecast(new_journey("clean"))
    assert f.band == "clean" and f.channel is None and f.yield_ == 1.0
    assert isinstance(f, StageForecast) and isinstance(f.result, LineResult)


def test_forecast_is_deterministic_in_seed():
    """A fixed (seed, grade, effort) reproduces the forecast (the roguelike 'seed' — same here)."""
    a = forecast(JourneyState(grade="solar", effort=0.75, seed=3))
    b = forecast(JourneyState(grade="solar", effort=0.75, seed=3))
    assert a.yield_ == b.yield_ and a.band == b.band


# --------------------------------------------------------------------------- #
# The accumulator — choose / refine / commit, immutable + append-only
# --------------------------------------------------------------------------- #
def test_current_recipe_overlays_the_in_progress_decision():
    """``current_recipe`` folds the working grade + effort into the recipe before it is committed."""
    s = new_journey("solar").refine(0.25).refine(0.25)
    assert s.effort == 0.5
    assert s.current_recipe.purification.grade == "solar"
    assert s.current_recipe.purification.zone_passes == 0.5
    # …but the *accumulator* recipe is untouched until commit (still the default clean feed).
    assert s.recipe.purification.grade == "clean"


def test_commit_folds_the_decision_into_the_accumulator():
    """``commit`` bakes the purification decision into ``recipe`` so the next stage builds on it."""
    s = new_journey("MGS").refine(0.5).refine(0.5).commit()
    assert s.recipe.purification.grade == "MGS"
    assert s.recipe.purification.zone_passes == 1.0


def test_choose_grade_resets_effort_and_actions_are_immutable():
    """Picking a feedstock resets the refining effort; every action returns a new state (the original is
    untouched) and the log only grows (append-only)."""
    s0 = new_journey("solar")
    s1 = s0.refine(0.5)
    assert s0.effort == 0.0 and s1.effort == 0.5            # s0 untouched — immutability
    s2 = s1.choose_grade("MGS")
    assert s2.effort == 0.0 and s2.grade == "MGS"           # a fresh, unrefined charge
    assert len(s2.log) > len(s1.log) > len(s0.log)          # append-only trail


def test_refine_rejects_a_nonpositive_step():
    with pytest.raises(ValueError):
        new_journey("solar").refine(0.0)


def test_unknown_grade_rejected_at_construction():
    with pytest.raises(ValueError):
        new_journey("unobtainium")


# --------------------------------------------------------------------------- #
# Phase 2 — the crystal growth stage (the two-sided Voronkov window, graded both ways)
# --------------------------------------------------------------------------- #
def _grown(pull: float, *, grade: str = "clean", seed: int = 0) -> JourneyState:
    """A growth-stage state on a *clean* feed (so the consequence is the boule, not residual Na)."""
    return JourneyState(grade=grade, pull_rate=pull, seed=seed)


def test_grow_sets_the_pull_at_the_radial_hot_zone():
    """``grow`` sets the pull rate and engages the **radial** hot zone (so both consequences grade)."""
    cz = new_journey("clean").grow(2.0).current_recipe.czochralski
    assert cz.pull_rate_mm_min == 2.0
    assert cz.thermal_gradient_K_per_mm == GROWTH_G_CENTER_K_PER_MM
    assert cz.radial_gradient_boost == GROWTH_RADIAL_BOOST     # radial → graded core+rim, not a cliff


def test_growth_window_is_two_sided_and_graded_on_both_sides():
    """THE policy check (gradual-failure): pull too slow → a **graded** leakage rim, the optimum → clean,
    too fast → a **graded** void core — neither side is an all-or-nothing cliff (the radial hot zone grades
    them). This is the whole reason the growth stage uses the radial profile, not a uniform gradient."""
    slow_a, slow_b = forecast(_grown(0.75)), forecast(_grown(1.5))
    opt = forecast(_grown(2.0))
    fast_a, fast_b = forecast(_grown(2.5)), forecast(_grown(4.0))
    assert opt.band == "clean"                                # the optimum clears (~96 %)
    # slow side: partial and CLIMBING toward the optimum — graded, not a 0↔1 flip
    assert 0.0 < slow_a.yield_ < slow_b.yield_ < opt.yield_
    # fast side: partial and FALLING away from the optimum — graded
    assert opt.yield_ > fast_a.yield_ > fast_b.yield_ > 0.0


def test_growth_channels_name_dislocations_when_slow_and_voids_when_fast():
    """The two grown-in channels, named: slow pull → dislocation **leakage** (rim), fast pull → **voids**
    (core) — the same wafer's two failure modes, distinguished from the purification roots."""
    slow = forecast(_grown(0.75)).channel.lower()
    fast = forecast(_grown(4.0)).channel.lower()
    assert "leakage" in slow and "dislocation" in slow
    assert "void" in fast


def test_boule_profile_drifts_up_the_boule_and_faster_pull_flattens_it():
    """The 'watch it develop' view: Scheil walks V_t up the boule (seed → tail); a faster pull (CG-1's
    k_eff → 1) **flattens** that drift — a smaller seed→tail swing."""
    slow, fast = boule_profile(_grown(0.5)), boule_profile(_grown(3.0))
    assert slow[-1][1] > slow[0][1]                           # V_t rises seed → tail (the drift)
    swing = lambda p: p[-1][1] - p[0][1]
    assert swing(fast) < swing(slow)                          # faster pull → flatter boule (CG-1)


def test_grow_folds_into_the_recipe_on_commit():
    """``commit`` bakes the growth decision (pull + the radial hot zone) into the accumulator recipe."""
    s = new_journey("clean").grow(2.0).commit()
    assert s.recipe.czochralski.pull_rate_mm_min == 2.0
    assert s.recipe.czochralski.radial_gradient_boost == GROWTH_RADIAL_BOOST


def test_grow_rejects_a_nonpositive_pull():
    with pytest.raises(ValueError):
        new_journey("clean").grow(0.0)


# --------------------------------------------------------------------------- #
# Phase 3 — the slice/cut stage (reads the boule drift; coupled to the phase-2 pull)
# --------------------------------------------------------------------------- #
def _grown_cut(pull: float, z: float, *, grade: str = "clean", seed: int = 0) -> JourneyState:
    """A grown-and-cut state on a *clean* feed — the consequence is the Scheil drift, not residual Na."""
    return JourneyState(grade=grade, pull_rate=pull, slice_z=z, seed=seed)


def test_cut_sets_the_slice_position_and_composes_with_the_growth_overlay():
    """``cut`` sets the axial cut position and overlays it onto the recipe — *composing* with the growth
    overlay (the pull + the radial hot zone survive the cut)."""
    cz = new_journey("clean").grow(2.0).cut(0.6).current_recipe.czochralski
    assert cz.slice_z == 0.6
    assert cz.pull_rate_mm_min == 2.0                          # the growth overlay is not clobbered
    assert cz.radial_gradient_boost == GROWTH_RADIAL_BOOST


def test_slice_window_is_graded_clean_to_ring_to_dead_down_the_boule():
    """THE policy check (gradual-failure): cutting near the seed is clean, cutting deeper walks through a
    **graded** V_t centre core (the radial t_ox non-uniformity grades the cliff — the centre dies, highest
    V_t, cross the spec ceiling first; the rim's thinner oxide → lower V_t survives longest), then dead at
    the tail. Not an all-or-nothing flip. (The ``"ring"`` band token is the generic ok→rework→fail middle
    band — for the *cut* that band is spatially a centre core, not an edge ring; cf. stage-1's Na rim.)"""
    clean = forecast(_grown_cut(2.0, 0.75))
    ring = forecast(_grown_cut(2.0, 0.88))
    dead = forecast(_grown_cut(2.0, 0.93))
    assert clean.band == "clean"
    assert ring.band == "ring" and 0.0 < ring.yield_ < clean.yield_   # a partial centre core (rework territory)
    assert dead.band == "dead" and dead.yield_ < ring.yield_


def test_slice_consequence_is_coupled_to_the_phase2_pull():
    """THE journey payoff — the slice stage *reads a prior committed decision*: the SAME deep cut is clean
    on a flat boule (a fast phase-2 pull flattened the Scheil drift) but dead on a slow-pulled one (already
    lost to its interstitial dislocation leakage rim before the cut). A bad pull can't be sliced away."""
    deep = 0.85
    fast = forecast(_grown_cut(2.0, deep))      # flat boule (optimum pull) — cuts deep, stays in spec
    slow = forecast(_grown_cut(0.5, deep))      # slow pull — the leakage rim already killed it
    assert fast.band == "clean"
    assert slow.yield_ < fast.yield_ and slow.band in ("ring", "dead")
    # the worst die dies on the dislocation *leakage* rim (the growth decision), not the cut — the existing
    # worst-die heuristic resolves the multi-channel wafer without new priority logic (advisor).
    assert "leakage" in (slow.channel or "").lower()


def test_slice_channel_names_the_scheil_drift_when_cut_too_deep():
    """A clean feed cut too deep fails on V_t **high** (Scheil-walked substrate doping) — named distinctly
    from the purification V_t-*low* mobile-ion Na channel (the direction discriminates the root)."""
    f = forecast(_grown_cut(2.0, 0.90))
    assert f.band != "clean"
    assert f.channel is not None
    assert "scheil" in f.channel.lower() and "v_t" in f.channel.lower()


def test_cut_folds_into_the_recipe_on_commit():
    """``commit`` bakes the cut (the slice position) into the accumulator — preserving the grown boule."""
    s = new_journey("clean").grow(2.0).commit().cut(0.6).commit()
    assert s.recipe.czochralski.slice_z == 0.6
    assert s.recipe.czochralski.pull_rate_mm_min == 2.0       # the prior growth commit survives


def test_cut_rejects_an_out_of_range_position():
    """The cut is an axial fraction ∈ [0, 1) — the seed end inclusive, the tail end open."""
    with pytest.raises(ValueError):
        new_journey("clean").cut(1.0)
    with pytest.raises(ValueError):
        new_journey("clean").cut(-0.1)


def test_no_cut_is_a_seam():
    """A journey that never cuts leaves ``slice_z`` at the recipe default (0.0) — the new lever is a true
    seam: an explicit cut at the seed reproduces the no-cut forecast bit-for-bit."""
    grown = JourneyState(grade="clean", pull_rate=2.0)
    assert grown.slice_z is None
    assert grown.current_recipe.czochralski.slice_z == 0.0           # the recipe default, untouched
    assert forecast(grown).yield_ == forecast(grown.cut(0.0)).yield_  # cut(0) is the identity (the seam)


# --------------------------------------------------------------------------- #
# finish — run + score the whole line, end to end
# --------------------------------------------------------------------------- #
def test_finish_runs_and_scores_a_refined_feed():
    """End-to-end: a refined-clean solar feed runs the full line → a full wafer → a scored card."""
    result, sc = finish(JourneyState(grade="solar", effort=1.5))
    assert isinstance(result, LineResult) and isinstance(sc, ScoreCard)
    assert result.yield_ == 1.0                              # refined clean → full front-end yield
    assert sc.n_good > 0 and isinstance(sc.profit, float)


def test_forecast_and_finish_agree_on_front_end_yield():
    """The forecast (``DEFAULT_SPECS``) and finish (market-bin specs) **bin** differently but must agree on
    the front-end pass/fail **yield** — speed binning is a grading policy on the passers, not a second
    acceptance test. Pinned at a non-trivial ring effort (not a trivial all-pass)."""
    s = JourneyState(grade="solar", effort=0.75)
    assert 0.0 < forecast(s).yield_ < 1.0                    # a partial ring (a meaningful number to match)
    assert forecast(s).yield_ == finish(s)[0].yield_


def test_finish_a_dead_feed_is_a_loss():
    """A raw (dead) feed finishes scrapped: no shipped dies → only cost → a negative profit (the loss the
    player avoids by refining or scrapping)."""
    result, sc = finish(JourneyState(grade="solar", effort=0.0))
    assert result.yield_ == 0.0
    assert sc.n_good == 0 and sc.profit < 0.0
