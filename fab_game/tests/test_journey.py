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
    DEFAULT_OXIDE_MIN,
    DIFFUSION_SD_CONTACT_SQUARES,
    GROWTH_G_CENTER_K_PER_MM,
    GROWTH_RADIAL_BOOST,
    JourneyState,
    StageForecast,
    boule_profile,
    consequence_band,
    diffusion_trajectory,
    finish,
    forecast,
    new_journey,
    oxidation_trajectory,
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
# Phase 4 — the S/D diffusion stage (the predep dose → R_s → I_Dsat series-R consumer)
# --------------------------------------------------------------------------- #
def _diffused(predep_C: float, *, predep_min: float = 10.0, grade: str = "clean",
              pull: float = 2.0, z: float = 0.5, seed: int = 0) -> JourneyState:
    """A grown-cut-and-diffused state on a *clean* feed at the optimum pull / mid-cut — so the consequence
    is the diffusion dose, not residual Na or the Scheil drift."""
    return JourneyState(grade=grade, pull_rate=pull, slice_z=z, predep_C=predep_C, predep_min=predep_min,
                        seed=seed)


def test_diffuse_sets_the_predep_and_engages_the_series_r_consumer():
    """``diffuse`` sets the predep dose **and** turns on the series-R consumer (``sd_contact_squares``) —
    the wire that makes the dose a scored decision (without it ``R_s`` feeds nothing)."""
    d = new_journey("clean").grow(2.0).commit().cut(0.5).commit().diffuse(900.0, 5.0).current_recipe.diffusion
    assert d.T_predep_C == 900.0 and d.t_predep_min == 5.0
    assert d.sd_contact_squares == DIFFUSION_SD_CONTACT_SQUARES   # consumer engaged → R_s now bites I_Dsat


def test_diffusion_trajectory_raises_rs_and_lowers_idsat_as_dose_drops():
    """The 'watch the dose set the junction' view: a shorter predep lays down less dose → ``R_s`` rises,
    ``x_j`` shrinks, and (through the series-R consumer) the clean ``I_Dsat`` walks down toward the floor."""
    traj = diffusion_trajectory(_diffused(900.0))               # the sweep is over predep TIME (descending)
    ts = [t for t, _, _, _ in traj]
    rs = [r for _, r, _, _ in traj]
    xj = [x for _, _, x, _ in traj]
    idsat = [i for _, _, _, i in traj]
    assert ts == sorted(ts, reverse=True)                       # shortening predep (less dose)
    assert rs == sorted(rs)                                     # R_s rises as the dose drops
    assert xj == sorted(xj, reverse=True)                       # x_j shrinks (less dose, shallower)
    assert idsat == sorted(idsat, reverse=True)                 # I_Dsat falls (more series R starves drive)


def test_diffusion_window_is_graded_clean_to_ring_to_dead():
    """THE policy check (gradual-failure): a nominal predep is clean, a cooler/shorter one walks through a
    **graded** I_Dsat centre core (the radial t_ox non-uniformity grades it — the thicker-oxide centre
    crosses the I_Dsat floor first), then dead — not an all-or-nothing flip."""
    clean = forecast(_diffused(950.0, predep_min=10.0))
    ring = forecast(_diffused(885.0, predep_min=4.0))
    dead = forecast(_diffused(850.0, predep_min=3.0))
    assert clean.band == "clean"
    assert ring.band == "ring" and 0.0 < ring.yield_ < clean.yield_   # a partial centre core (rework territory)
    assert dead.band == "dead" and dead.yield_ < ring.yield_


def test_diffusion_channel_names_the_series_resistance_root():
    """An under-diffused junction fails on ``I_Dsat`` **low** via S/D series resistance — named distinctly
    from a defocus/over-etch over-current (``I_Dsat`` *high*); direction discriminates the root."""
    f = forecast(_diffused(885.0, predep_min=4.0))
    assert f.band != "clean" and f.channel is not None
    assert "i_dsat" in f.channel.lower() and "series resistance" in f.channel.lower()


def test_diffusion_is_one_sided_more_dose_never_fails():
    """Honest one-sidedness (no faked over-diffusion failure): a *hotter/longer* predep only lowers ``R_s``,
    so it stays clean — the over-diffusion harm (short-channel rolloff) is the device model's omitted scope
    edge, not manufactured here (the ``gradual-failure`` 'inflate an unrelated variable' fudge avoided)."""
    over = forecast(_diffused(1000.0, predep_min=15.0))
    assert over.band == "clean"


def test_diffuse_folds_into_the_recipe_on_commit():
    """``commit`` bakes the diffusion decision (predep + the series-R consumer) into the accumulator,
    preserving the grown + cut boule."""
    s = new_journey("clean").grow(2.0).commit().cut(0.6).commit().diffuse(900.0, 5.0).commit()
    assert s.recipe.diffusion.T_predep_C == 900.0 and s.recipe.diffusion.t_predep_min == 5.0
    assert s.recipe.diffusion.sd_contact_squares == DIFFUSION_SD_CONTACT_SQUARES
    assert s.recipe.czochralski.slice_z == 0.6 and s.recipe.czochralski.pull_rate_mm_min == 2.0  # priors survive


def test_no_diffuse_is_a_seam():
    """A journey that never diffuses leaves the series-R consumer **off** (``sd_contact_squares`` at the
    recipe default 0.0) — the device reads the ideal-contact I_Dsat, byte-for-byte the pre-phase-4 line."""
    grown_cut = JourneyState(grade="clean", pull_rate=2.0, slice_z=0.5)
    assert grown_cut.predep_C is None
    assert grown_cut.current_recipe.diffusion.sd_contact_squares == 0.0     # consumer off — the seam


def test_diffuse_rejects_a_nonpositive_predep():
    with pytest.raises(ValueError):
        new_journey("clean").diffuse(0.0)
    with pytest.raises(ValueError):
        new_journey("clean").diffuse(950.0, 0.0)


# --------------------------------------------------------------------------- #
# Phase 5 — the oxidation stage (two-sided, no economics; graded by its own t_ox non-uniformity)
# --------------------------------------------------------------------------- #
def _oxidized(minutes: float, *, grade: str = "clean", pull: float = 2.0, z: float = 0.5,
              predep_C: float | None = None, seed: int = 0) -> JourneyState:
    """A grown-cut-and-oxidized state on a *clean* feed at the optimum pull / mid-cut — so the consequence
    is the gate-oxide thickness, not residual Na or the Scheil drift. ``predep_C`` engages the diffusion
    series-R consumer too (for the full-journey channel-collision test)."""
    return JourneyState(grade=grade, pull_rate=pull, slice_z=z, predep_C=predep_C, oxide_min=minutes,
                        seed=seed)


def _pass_rate(fc: StageForecast, *, inner_half: bool) -> float:
    """Pass-rate over the inner (``radius_frac < 0.5``) or outer half of the wafer map — the radial signature."""
    sel = [d for d in fc.result.wafer.dies if (d.radius_frac < 0.5) == inner_half]
    return sum(d.verdict.passed for d in sel) / len(sel)


def test_oxidize_sets_the_oxide_time_and_keeps_T_ambient_default():
    """``oxidize`` overlays the gate-oxide **time** onto the recipe; ``T``/ambient/orientation stay at the
    recipe default (time is the only lever — a single monotone knob, no second temperature knob)."""
    ox = new_journey("clean").oxidize(24.0).current_recipe.oxidation
    assert ox.minutes == 24.0
    assert ox.ambient == "dry" and ox.T_celsius == 1000.0    # untouched — the lever is time alone


def test_oxidation_window_is_two_sided_and_graded_on_both_sides():
    """THE policy check (the cleanest two-sided stage — like crystal growth, no economics): grow **too
    little** oxide → fails (low V_t / over-current), the nominal grows **clean**, grow **too much** → fails
    (high V_t / starved drive); and *both* sides are **graded** (a ring band, not an all-or-nothing flip) by
    the oxidation step's own radial ``t_ox`` non-uniformity."""
    thin_dead = forecast(_oxidized(14.0))
    thin_ring = forecast(_oxidized(16.5))
    clean = forecast(_oxidized(20.0))
    thick_ring = forecast(_oxidized(23.0))
    thick_dead = forecast(_oxidized(24.5))
    assert clean.band == "clean"
    # thin side: dead → a partial graded ring as the oxide thickens toward the window
    assert thin_dead.band == "dead" and 0.0 < thin_ring.yield_ < clean.yield_
    # thick side: a partial graded ring → dead as the oxide thickens past the window
    assert 0.0 < thick_ring.yield_ < clean.yield_ and thick_dead.band == "dead"


def test_oxidation_sides_fail_at_opposite_radii():
    """THE phase-5 signature (the only stage whose two sides fail at *opposite radii*): under-oxidized →
    the thinnest **rim** crosses the thin-side bounds first → an **edge ring** (the outer half fails harder,
    echoing stage-1's Na ring); over-oxidized → the thickest **centre** crosses the thick-side bounds first →
    a **centre core** (the inner half fails harder, echoing the slice/diffusion cores).

    Isolated on a **non-grown** wafer (no pull → no Voronkov void core, no killer particles) so the only
    radial structure is the oxidation step's own ``t_ox`` non-uniformity — the growth optimum still scatters
    a small centre void core (capping its yield ~96 %) that would confound the inner/outer pass-rate split."""
    under = forecast(JourneyState(grade="clean", oxide_min=17.5, seed=0))   # too thin → edge ring
    over = forecast(JourneyState(grade="clean", oxide_min=24.0, seed=0))    # too thick → centre core
    assert under.band == "ring" and over.band == "ring"
    assert _pass_rate(under, inner_half=True) > _pass_rate(under, inner_half=False)   # edge ring (rim fails)
    assert _pass_rate(over, inner_half=True) < _pass_rate(over, inner_half=False)     # centre core (centre fails)


def test_oxidation_trajectory_raises_vt_and_lowers_idsat_with_time():
    """The 'watch the oxide set the device' view: a longer oxidation grows a thicker ``t_ox`` → ``V_t``
    rises (``Q_dep/C_ox``) **and** ``I_Dsat`` falls (``C_ox`` down) — the two-sided consequence, read off one
    clean die down the oxide-time sweep."""
    traj = oxidation_trajectory(_oxidized(20.0))
    ms = [m for m, _, _, _ in traj]
    tox = [t for _, t, _, _ in traj]
    vt = [v for _, _, v, _ in traj]
    idsat = [i for _, _, _, i in traj]
    assert ms == sorted(ms)                                  # ascending oxide time
    assert tox == sorted(tox)                                # thicker oxide with time
    assert vt == sorted(vt)                                  # V_t rises with thickness
    assert idsat == sorted(idsat, reverse=True)              # I_Dsat falls (lower C_ox)


def test_oxidation_channel_names_the_gate_oxide_on_a_full_journey():
    """THE load-bearing channel test (advisor): the oxidation failure collides with **every** parametric
    root — over-oxidation's V_t-high looks like the Scheil cut, under-oxidation's V_t-low like mobile-ion Na,
    its I_Dsat-low like the S/D series resistance. On a **full journey** (committed cut + the diffusion
    series-R consumer ON) the oxide death must still be named the **gate oxide** — discriminated on the
    inherited ``t_ox`` (the V_t/I_Dsat sign is *not* unique: a deep Scheil cut also raises V_t and drags
    I_Dsat down) — never silently mis-attributed to the cut or the diffusion."""
    over = forecast(_oxidized(24.0, predep_C=950.0))         # over-oxidized, diffusion consumer engaged
    under = forecast(_oxidized(15.0, predep_C=950.0))        # under-oxidized, diffusion consumer engaged
    assert over.band != "clean" and "too thick" in over.channel and "oxide" in over.channel.lower()
    assert under.band != "clean" and "too thin" in under.channel and "oxide" in under.channel.lower()
    # …and NOT the colliding roots the sign pattern would otherwise grab:
    assert "scheil" not in over.channel.lower() and "series resistance" not in over.channel.lower()
    assert "mobile-ion" not in under.channel.lower()


def test_oxidation_window_tightens_with_a_deeper_cut():
    """The phase-3 → phase-5 **coupling** (the V_t budget is shared): a deeper cut → higher ``N_A`` → higher
    baseline ``V_t`` → less headroom to the ``V_t`` ceiling → over-oxidation bites **sooner**. The same thick
    oxide that is clean on a shallow cut is over the ceiling on a deep one — 'how much oxide you can grow is
    set by how deep you cut' (the cut↔pull coupling's sibling, zero new physics)."""
    thick = 22.5
    shallow = forecast(_oxidized(thick, z=0.0))
    deep = forecast(_oxidized(thick, z=0.85))
    assert shallow.band == "clean"                           # clean on a shallow (low-N_A) cut
    assert deep.yield_ < shallow.yield_ and deep.band != "clean"   # the deep cut ate the V_t headroom


def test_oxidize_folds_into_the_recipe_on_commit():
    """``commit`` bakes the oxidation decision (the oxide time) into the accumulator, preserving the priors."""
    s = new_journey("clean").grow(2.0).commit().cut(0.5).commit().oxidize(22.0).commit()
    assert s.recipe.oxidation.minutes == 22.0
    assert s.recipe.czochralski.slice_z == 0.5 and s.recipe.czochralski.pull_rate_mm_min == 2.0  # priors survive


def test_nominal_oxide_is_a_seam():
    """A journey that never oxidizes leaves ``oxidation.minutes`` at the recipe nominal — the lever AT
    NOMINAL is the identity (you cannot make a MOSFET with no gate oxide, so the seam is nominal-oxide, not
    an off switch): an explicit ``oxidize(DEFAULT_OXIDE_MIN)`` reproduces the no-oxidize forecast bit-for-bit."""
    grown_cut = JourneyState(grade="clean", pull_rate=2.0, slice_z=0.5)
    assert grown_cut.oxide_min is None
    assert grown_cut.current_recipe.oxidation.minutes == DEFAULT_OXIDE_MIN          # the recipe nominal, untouched
    assert forecast(grown_cut).yield_ == forecast(grown_cut.oxidize(DEFAULT_OXIDE_MIN)).yield_


def test_diagnose_names_the_oxide_not_series_resistance_on_over_oxidation():
    """The line's per-die trail (:func:`fab_game.pipeline.diagnose`) has the **same** I_Dsat-low collision as
    ``_dominant_channel``: an over-oxidized death with the diffusion series-R consumer engaged must name the
    **gate oxide** (too thick), not the S/D series resistance — closed by the same ``t_ox``-off-nominal check
    (before the series-R fingerprint). The journey surfaces ``_dominant_channel``, but a user can ``diagnose``
    a deliberately over-oxidized finished wafer, so the trail is kept honest too."""
    from fab_game.pipeline import diagnose
    over = forecast(_oxidized(24.0, predep_C=950.0))         # over-oxidized, the series-R consumer engaged
    dead = [d for d in over.result.wafer.dies if d.verdict.failed
            and any("i_dsat" in r.lower() and "(low)" in r.lower() for r in d.verdict.reasons)]
    assert dead, "expected an I_Dsat-low over-oxidation death to diagnose"
    trail = diagnose(dead[0])
    assert "oxidation" in trail and "too THICK" in trail
    assert "series resistance" not in trail                  # the series-R fingerprint is suppressed (oxide claimed it)


def test_oxidize_rejects_a_nonpositive_time():
    with pytest.raises(ValueError):
        new_journey("clean").oxidize(0.0)


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


# --------------------------------------------------------------------------- #
# The cost side — the Goldilocks half (the fab-journey's #1 open item)
# --------------------------------------------------------------------------- #
# Mechanics, not magnitudes (ADR 0005 §5): these assert the *shape* (an interior profit maximum — the
# yield band penalizes under-doing a stage, the cost penalizes over-doing it) and the seam (the cost is
# 0 by default / when a stage is not engaged), never the dollar amounts. The interior-maximum tests are
# the load-bearing analogue of the growth window's two-sidedness — they are what proves the Goldilocks
# half is actually wired (a cost *field* on the forecast would be display, not proof).
def _net_profit(state: JourneyState) -> float:
    """The net profit of the finished journey — revenue − (wafer + process) cost, the Goldilocks payoff."""
    return finish(state)[1].profit


def test_refining_has_an_interior_profit_maximum():
    """THE policy check (purification's cost side): refining yield SATURATES (the Na ring clears ~1 pass),
    so past saturation the marginal pass is pure cost → net profit is non-monotone in effort with an
    **interior** maximum. profit(under) < profit(opt) > profit(over): under-refine → an Na ring eats yield,
    over-refine → pay for passes that buy no more yield. (The yield-only forecast would call everything
    from ~1 pass up equally 'clean'; the cost side is what picks the *stopping* point.)"""
    under = _net_profit(JourneyState(grade="solar", effort=0.75))   # an Na ring — yield not yet saturated
    opt = _net_profit(JourneyState(grade="solar", effort=1.0))      # just clean — the saturation knee
    over = _net_profit(JourneyState(grade="solar", effort=2.0))     # clean but over-refined — pure cost
    assert under < opt > over
    # The over side is pure cost (yield is saturated, so revenue is identical) — it declines monotonically.
    assert _net_profit(JourneyState(grade="solar", effort=3.0)) < over


def test_predep_dose_has_an_interior_profit_maximum():
    """THE policy check (the S/D predep's cost side): the dose lowers R_s → lifts I_Dsat until it clears
    the floor (yield saturates), past which more thermal budget (∫D dt) is pure cost → an **interior**
    profit maximum in the predep time. profit(under) < profit(opt) > profit(over): under-dose → a high-R_s
    I_Dsat starve eats yield, over-dose → pay budget for drive the part already has. Swept at the cooler
    operating regime (900 °C), where the under-dose ring is graded (the recipe-default 950 °C is already
    over-dosed for the floor — the cost side's lesson)."""
    base = JourneyState(grade="solar", effort=1.5)                  # a clean feed, so diffusion is the lever
    under = _net_profit(base.diffuse(predep_C=900.0, predep_min=3.0))   # I_Dsat starved — yield not saturated
    opt = _net_profit(base.diffuse(predep_C=900.0, predep_min=5.0))     # just clears the floor — the knee
    over = _net_profit(base.diffuse(predep_C=900.0, predep_min=10.0))   # saturated but over-dosed — pure cost
    assert under < opt > over
    assert _net_profit(base.diffuse(predep_C=900.0, predep_min=15.0)) < over   # the over side keeps declining


def test_forecast_surfaces_the_cost_side():
    """The forecast carries the :class:`~fab_game.scoring.ProcessCost` so the player sees *both* halves of
    the decision before committing — the yield band (under-doing) and the cost (over-doing). The refine
    cost rises with effort; the diffusion cost is 0 until the stage is engaged (it co-engages with the
    I_Dsat consumer)."""
    from fab_game.scoring import ProcessCost
    f_low = forecast(JourneyState(grade="solar", effort=1.0))
    f_high = forecast(JourneyState(grade="solar", effort=2.0))
    assert isinstance(f_low.cost, ProcessCost)
    assert f_high.cost.refine > f_low.cost.refine                   # more passes cost more
    assert f_low.cost.diffusion == 0.0                             # diffusion not engaged → no cost yet
    engaged = forecast(JourneyState(grade="solar", effort=1.0).diffuse(predep_C=900.0, predep_min=5.0))
    assert engaged.cost.diffusion > 0.0                            # engaging the predep turns its cost on


def test_process_cost_is_gated_and_zero_at_the_seam():
    """The cost model's seam: a recipe that engages no decision pays no process cost (so :func:`score_wafer`
    with its ``process_cost=0`` default — what the roguelike passes — is the byte-identical baseline)."""
    from fab_game.recipe import DEFAULT_RECIPE
    from fab_game.scoring import REFINE_COST_PER_PASS, process_cost
    # The default recipe has no S/D series-R consumer engaged → diffusion cost is exactly 0 (not the
    # over-dosed nominal predep's budget — that bites only when the stage is an engaged decision).
    pc = process_cost(DEFAULT_RECIPE)
    assert pc.diffusion == 0.0
    assert pc.refine == REFINE_COST_PER_PASS * DEFAULT_RECIPE.purification.zone_passes
    assert pc.total == pc.refine + pc.diffusion                    # the breakdown closes
    # A fresh journey (effort 0, no diffusion) pays nothing — only the passes/dose it chooses cost.
    fresh = JourneyState(grade="solar", effort=0.0)
    assert process_cost(fresh.current_recipe).total == 0.0
