"""F7/B12 isolation & latchup in the game (`IsolationKnobs` → the isolation step → the wafer verdict).

The slice's shape **is** its finding, and these tests pin that shape:

  * **the seam** — ``scheme=None`` (the default) ⇒ no step, no record, no verdict clause: the line is
    byte-identical to the one that existed before this slice;
  * **latchup is a WAFER property, not a die one** — the only discriminating condition (the trigger
    current) rides the substrate resistivity, one number per wafer, so it is all dies or none. Pinned
    two ways: every die shares the verdict, and the per-die spread that *does* exist grades nothing;
  * **the per-die gain spread is real and inert** — the printed CD varies, so the spacing and the loop
    gain vary; the yield does not. A test that the number moves *and* changes no outcome;
  * **the era result** — STI's loop gain is **higher** than LOCOS's, because the density it bought is
    the parasitic base width, and the trench only buys part of it back;
  * **the decoupling, end-to-end** — the isolation scheme cannot move the trigger current, and the
    substrate cannot move the loop gain, through the whole pipeline and not just in `chip.latchup`;
  * **the drift inverts the house pattern** — boron's k < 1 ⇒ resistivity falls down the boule ⇒ the
    trigger rises, so the **first** wafers off the boule are the vulnerable ones.

Not tuned to fail: the default recipe sits at a ~26× margin and stays there. The tests that need a
latched wafer raise the *injected disturbance* (a spec on the environment), never the house geometry.
"""
from dataclasses import replace

import pytest

from chip import latchup
from fab_game.pipeline import run_line
from fab_game.recipe import IsolationKnobs, Recipe
from fab_game.variation import Variation

SEED = 3


def _run(scheme=None, **iso):
    recipe = Recipe()
    if scheme is not None or iso:
        recipe = replace(recipe, isolation=IsolationKnobs(scheme=scheme, **iso))
    return run_line(recipe, seed=SEED, variation=Variation())


def _iso_summary(wafer):
    return next(r for r in wafer.provenance if r.step == "isolation").summary


def _yield(wafer):
    return sum(d.verdict.passed for d in wafer.dies) / len(wafer.dies)


# --------------------------------------------------------------------------- #
# the seam
# --------------------------------------------------------------------------- #
def test_seam_default_runs_no_isolation_step_at_all():
    """``scheme=None`` ⇒ no step, no provenance record, no die record, nothing to read."""
    assert IsolationKnobs().engaged is False
    wafer = _run()
    assert not any(r.step == "isolation" for r in wafer.provenance)
    assert not any(rec.step == "isolation" for d in wafer.dies for rec in d.history)


def test_seam_engaging_the_knob_changes_no_die_measurement():
    """Engaging isolation adds a record and a verdict clause — it must not perturb the device chain.

    Every physical per-die number the line already produced is identical with the step on and off; the
    isolation step reads the line, it does not modify it.
    """
    off, on = _run(), _run("sti")
    for a, b in zip(off.dies, on.dies):
        assert (a.cd_nm, a.V_t, a.i_dsat, a.tau, a.j_leak) == (b.cd_nm, b.V_t, b.i_dsat, b.tau, b.j_leak)


# --------------------------------------------------------------------------- #
# latchup is a wafer property — the slice's shape
# --------------------------------------------------------------------------- #
def test_a_latched_wafer_loses_every_die_and_a_safe_one_loses_none():
    """All dies or none — the flatness-scrap precedent. The disturbance is raised, not the geometry."""
    safe = _run("sti")
    assert _iso_summary(safe)["latched"] is False
    assert all(d.verdict.passed for d in safe.dies)

    trigger_ma = _iso_summary(safe)["i_trigger_ma"]
    latched = _run("sti", injected_current_a=2.0 * trigger_ma * 1e-3)
    assert _iso_summary(latched)["latched"] is True
    assert not any(d.verdict.passed for d in latched.dies)
    assert all("latchup" in " ".join(d.verdict.reasons) for d in latched.dies)


def test_the_per_die_loop_gain_spread_is_real_and_grades_nothing():
    """The printed CD varies, so the spacing and the gain vary — and the yield does not move.

    This is the honest statement of the slice: the isolation change moves a genuine per-die quantity
    which **cannot bin out a die**. Recorded rather than hidden, so no reader assumes it matters.
    """
    wafer = _run("sti")
    s = _iso_summary(wafer)
    assert s["loop_gain_max"] > s["loop_gain_min"]          # a real spread ...
    assert s["loop_gain_grades_nothing"] is True
    gains = [rec.outputs["loop_gain"] for d in wafer.dies
             for rec in d.history if rec.step == "isolation"]
    assert len(set(gains)) > 1                              # ... die by die ...
    assert _yield(wafer) == 1.0                             # ... and it costs nothing.


def test_every_die_carries_the_same_verdict_regardless_of_its_own_gain():
    """The die with the highest parasitic gain fares exactly as well as the one with the lowest."""
    wafer = _run("locos")
    per_die = {d.site: rec.outputs["loop_gain"] for d in wafer.dies
               for rec in d.history if rec.step == "isolation"}
    worst = max(per_die, key=per_die.get)
    best = min(per_die, key=per_die.get)
    verdicts = {d.site: d.verdict.passed for d in wafer.dies}
    assert verdicts[worst] == verdicts[best]


# --------------------------------------------------------------------------- #
# the era result
# --------------------------------------------------------------------------- #
def test_sti_has_the_higher_loop_gain_because_the_density_it_bought_is_the_parasitic_base():
    """The bill for clearing B5's packing floor: LOCOS must leave room for the beak, STI need not, and
    the spacing STI saves is the parasitic npn's base width. The trench buys some of it back — but not
    all of it, which is why the loop gain still ends up higher."""
    locos = _iso_summary(_run("locos"))["loop_gain_max"]
    sti = _iso_summary(_run("sti"))["loop_gain_max"]
    assert sti > locos


def test_the_trench_buys_back_part_of_what_the_density_costs():
    """Same STI spacing with and without the trench: the trench lowers the gain (it lengthens the
    base), but not by enough to get back under LOCOS. Both halves asserted — the partial payback is
    the point, and either half alone would misrepresent it."""
    knobs = IsolationKnobs(scheme="sti")
    tau = 1.0e-3
    with_trench = latchup.loop_gain(knobs.nominal_spacing_um, tau,
                                    trench_depth_um=knobs.trench_depth_um)
    without = latchup.loop_gain(knobs.nominal_spacing_um, tau, trench_depth_um=0.0)
    locos = latchup.loop_gain(IsolationKnobs(scheme="locos").nominal_spacing_um, tau,
                              trench_depth_um=0.0)
    assert with_trench < without          # the trench helps ...
    assert with_trench > locos            # ... and does not undo the density it was bought with.


# --------------------------------------------------------------------------- #
# the decoupling, end-to-end through the pipeline
# --------------------------------------------------------------------------- #
def test_the_isolation_scheme_cannot_move_the_trigger_current():
    """`chip.latchup` refuses to couple spacing to `R_sub`; this asserts the refusal survives the
    whole pipeline, not just the module."""
    locos, sti = _iso_summary(_run("locos")), _iso_summary(_run("sti"))
    assert locos["r_sub_ohm"] == sti["r_sub_ohm"]
    assert locos["i_trigger_ma"] == sti["i_trigger_ma"]


def test_the_substrate_cannot_move_the_loop_gain():
    """The mirror: two boule slices with different substrate doping, identical parasitic gains."""
    def at(z):
        r = Recipe()
        r = replace(r, isolation=IsolationKnobs(scheme="sti"),
                    czochralski=replace(r.czochralski, slice_z=z))
        return _iso_summary(run_line(r, seed=SEED, variation=Variation()))
    a, b = at(0.0), at(0.9)
    assert a["i_trigger_ma"] != b["i_trigger_ma"]           # the substrate really did change ...
    assert a["loop_gain_max"] == b["loop_gain_max"]         # ... and the gain did not notice.


def test_the_first_wafers_off_the_boule_are_the_vulnerable_ones():
    """The drift inverts the house pattern. Boron's k < 1 ⇒ concentration rises down the boule ⇒
    resistivity falls ⇒ `R_sub` falls ⇒ the trigger current RISES. Later slices are *safer* here,
    where every other knob in this game makes them worse."""
    triggers = []
    for z in (0.0, 0.3, 0.6, 0.9):
        r = Recipe()
        r = replace(r, isolation=IsolationKnobs(scheme="sti"),
                    czochralski=replace(r.czochralski, slice_z=z))
        triggers.append(_iso_summary(run_line(r, seed=SEED, variation=Variation()))["i_trigger_ma"])
    assert all(a < b for a, b in zip(triggers, triggers[1:]))


# --------------------------------------------------------------------------- #
# the knob's own guards
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("kwargs", [
    dict(scheme="trench"),                 # not one of the two schemes B12 contrasts
    dict(scheme="sti", drawn_spacing_um=0.0),
    dict(scheme="sti", beak_allowance_um=-1.0),
    dict(scheme="sti", injected_current_a=0.0),
])
def test_bad_knobs_raise(kwargs):
    with pytest.raises(ValueError):
        IsolationKnobs(**kwargs)


def test_the_default_line_is_not_tuned_to_fail():
    """A ~26× margin at the default recipe, and it stays. The sign of this slice is structural; the
    threshold rides a flagged house calibration (the tap geometry), so a default that latched would be
    a tuned number masquerading as a result."""
    assert _iso_summary(_run("sti"))["margin_ratio"] > 10.0


def test_the_between_scheme_gain_ratio_is_coefficient_free():
    """The one **quotable number** the gain condition can produce, and why it is quotable.

    In the short-base limit ``β ≈ 2L²/W_B²``, so a *ratio* of two schemes' loop gains is the inverse
    square of their base-width ratio — squared once per parasitic transistor, and only the lateral one
    changes between schemes. ``L`` cancels, which means the ratio is independent of the lifetime, of
    ``D``, of the γ=1 idealization, and of the flagged tap geometry (which is not in it at all).

    So where the absolute loop gain is a useless upper bound (10⁴–10¹²), this ratio is pure geometry.
    LOCOS's spacing is not a house guess — it is the drawn 2.0 µm plus the bird's beak B5 computes
    (0.926 µm, both edges), so 2.926 µm. STI without a trench would be (2.926/2.0)² = **2.14×** LOCOS,
    and the trench brings it to (2.926/2.7)² = **1.174×** — the trench paying back ~85 % of the density
    penalty and no more.

    The cancellation is exact only in the **short-base limit**, and the second assertion below pins it
    at the precision it is really true rather than the one that sounds better: across four orders of
    magnitude in lifetime the ratio drifts by < 0.05 %, not by nothing.
    """
    tau = 1.0e-3
    locos_w = IsolationKnobs(scheme="locos").nominal_spacing_um
    sti = IsolationKnobs(scheme="sti")
    sti_w = latchup.lateral_base_width_um(sti.nominal_spacing_um,
                                          trench_depth_um=sti.trench_depth_um)

    def gain(width):
        return latchup.bipolar_gain(width, latchup.diffusion_length_um(tau))

    assert gain(sti_w) / gain(locos_w) == pytest.approx((locos_w / sti_w) ** 2, rel=1e-5)

    # ... and it barely moves when the lifetime does — which is what "L cancels" means, stated at the
    # precision it is actually true. The cancellation is EXACT only in the short-base limit; at
    # τ = 1e-7 s the diffusion length is ~19 µm against a 3 µm base, so the cosh corrections no longer
    # vanish and the ratio drifts. Across four orders of magnitude of lifetime that drift is < 0.05 %,
    # which is the honest claim: near-invariant, not invariant.
    def ratio(tau_s):
        L = latchup.diffusion_length_um(tau_s)
        return latchup.bipolar_gain(sti_w, L) / latchup.bipolar_gain(locos_w, L)
    assert ratio(1.0e-3) == pytest.approx(ratio(1.0e-7), rel=1.0e-3)
    assert abs(ratio(1.0e-3) / ratio(1.0e-7) - 1.0) < 5.0e-4


# --------------------------------------------------------------------------- #
# S4 — the substrate is the lever the isolation cannot be
# --------------------------------------------------------------------------- #
def test_the_epi_substrate_rescues_a_wafer_the_isolation_could_not_save():
    """The finale, as a composition: **the same wafer, the same disturbance, the same isolation.**

    Only the substrate changes — a uniform wafer becomes a thin lightly-doped layer on a heavily-doped
    handle — and the part that was scrapped survives. Nothing about the isolation scheme could have
    done this, which is the rung's whole claim.
    """
    trigger_ma = _iso_summary(_run("sti"))["i_trigger_ma"]
    hit = 2.0 * trigger_ma * 1e-3                     # a disturbance this line cannot take

    doomed = _run("sti", injected_current_a=hit)
    assert _iso_summary(doomed)["latched"] is True
    assert not any(d.verdict.passed for d in doomed.dies)

    rescued = _run("sti", injected_current_a=hit, epi_thickness_um=2.0)
    assert _iso_summary(rescued)["latched"] is False
    assert all(d.verdict.passed for d in rescued.dies)


def test_the_rescue_is_the_substrate_and_provably_not_the_geometry():
    """The rescue moves the resistance and leaves the gain **exactly** untouched — so it cannot be
    mistaken for the isolation change doing the work."""
    hit = dict(injected_current_a=0.1)
    uniform = _iso_summary(_run("sti", **hit))
    epi = _iso_summary(_run("sti", epi_thickness_um=2.0, **hit))
    assert epi["r_sub_ohm"] < uniform["r_sub_ohm"]
    assert epi["i_trigger_ma"] > uniform["i_trigger_ma"]
    assert epi["loop_gain_max"] == uniform["loop_gain_max"]      # the gain did not move at all
    assert epi["loop_gain_min"] == uniform["loop_gain_min"]


def test_the_substrate_lever_changes_no_device_measurement():
    """It is one resistance, not an epitaxy process. Every per-die number the transistor produces is
    identical — which is exactly why this slice is **not** F6 (that would change the profile the
    device sits in, and this does not)."""
    off = _run("sti")
    on = _run("sti", epi_thickness_um=2.0)
    for a, b in zip(off.dies, on.dies):
        assert (a.cd_nm, a.V_t, a.i_dsat, a.tau, a.j_leak) == (b.cd_nm, b.V_t, b.i_dsat, b.tau, b.j_leak)


def test_thinner_epi_is_monotonically_safer_through_the_whole_pipeline():
    """The module's direction, asserted end-to-end rather than in isolation."""
    triggers = [_iso_summary(_run("sti", epi_thickness_um=t))["i_trigger_ma"]
                for t in (20.0, 10.0, 5.0, 2.0)]
    assert all(a < b for a, b in zip(triggers, triggers[1:]))


@pytest.mark.parametrize("kwargs", [
    dict(scheme="sti", epi_thickness_um=0.0),
    dict(scheme="sti", epi_thickness_um=-1.0),
    dict(scheme="sti", handle_resistivity_ohm_cm=0.0),
])
def test_bad_substrate_knobs_raise(kwargs):
    with pytest.raises(ValueError):
        IsolationKnobs(**kwargs)


def test_the_seam_still_holds_with_the_substrate_lever_present():
    """``epi_thickness_um=None`` is the default: the uniform wafer the rest of the sim models."""
    assert IsolationKnobs().epi_thickness_um is None
    assert IsolationKnobs(scheme="sti").substrate_resistance_ohm(10.0) == \
        latchup.substrate_resistance_from_resistivity_ohm(10.0)
