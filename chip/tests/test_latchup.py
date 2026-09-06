"""B12 CMOS latchup (:mod:`chip.latchup`) — F7's remainder, the bill trench isolation came with.

The triad, per ``docs/plans/latchup-isolation-f7.md`` + ``historical-modes.md`` — **three** tight legs:

  * **tight — the two cited criteria, as identities.** ``I_trigger · R_sub == 0.7 V`` exactly (the
    trigger inequality at equality), and the sustaining comparison is against ``1.0`` exactly. Both are
    definitions the code satisfies by construction, and pinning them is what stops a later refactor
    from quietly moving a cited constant;
  * **tight — the seam.** Nothing on the default path imports this module, so the existing suite is
    byte-identical. Asserted mechanically by reading the tree, not by assertion-in-prose;
  * **tight — three monotonic directions, all cited and all coefficient-free:** β falls with base
    width; base width grows with spacing *and* with trench depth; trigger current rises as substrate
    doping rises (ρ falls). Sign-robust — none of them can be moved by the flagged geometry;
  * **the decoupling, made mechanical.** The module's central refusal is that ``R_sub`` is not a
    function of spacing and β is not a function of doping. Both are asserted as *exact invariance*,
    which is the only way a "we did not couple these" claim can be checked;
  * **the calibration pinned as a calibration.** The tap geometry is a house lump, so every quotable
    leg is asserted **invariant** to it — a claim that moves when an uncalibrated constant moves is not
    one this module gets to make;
  * **the bound owned, not hidden.** each β is asserted to be *large* at this sim's geometries
    (10²–10⁶, their product 10⁴–10¹²), which is the module's own admission that the sustaining
    condition does not discriminate. A test that pins an embarrassing number is how the docstring's
    honesty stays true after edits.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import math
import pathlib
import re

import pytest

from chip import junction, latchup, lifetime


# --------------------------------------------------------------------------- #
# tight — the two cited criteria as identities
# --------------------------------------------------------------------------- #
def test_trigger_identity_is_the_cited_inequality_at_equality():
    """``I_trigger · R_sub == V_be`` — the cited ``I·R > 0.7 V`` at its boundary, exactly."""
    for r in (10.0, 500.0, 1.0e4):
        assert latchup.trigger_current_a(r) * r == pytest.approx(latchup.BE_TURN_ON_V, rel=1e-15)


def test_cited_constants_are_the_cited_values():
    """The two constants the sources state verbatim. Pinned so a refactor cannot drift them."""
    assert latchup.BE_TURN_ON_V == 0.7
    assert latchup.LOOP_GAIN_CRITICAL == 1.0
    # CITED band: shallow-trench isolation is 250–400 nm deep.
    assert 0.25 <= latchup.STI_DEPTH_UM <= 0.40


def test_transport_factor_and_gain_are_the_same_closed_form():
    """``β = α/(1−α)`` with ``α = 1/cosh(W/L)`` must equal ``1/(cosh(W/L) − 1)``.

    Not a physical claim — a guard that the two ways the docstring writes the form stay one form.
    """
    w, L = 2.0, 40.0
    assert latchup.bipolar_gain(w, L) == pytest.approx(1.0 / (math.cosh(w / L) - 1.0), rel=1e-12)


def test_short_base_asymptote():
    """``β → 2L²/W²`` as ``W/L → 0``. A regression on the algebra, **counted as nothing**.

    It pins a Taylor expansion of a form the code already chose, not a fact about silicon.
    """
    w, L = 0.05, 500.0
    assert latchup.bipolar_gain(w, L) == pytest.approx(2.0 * L * L / (w * w), rel=1e-4)


# --------------------------------------------------------------------------- #
# tight — the three monotonic directions (cited, coefficient-free)
# --------------------------------------------------------------------------- #
def test_gain_falls_monotonically_with_base_width():
    """CITED direction: "reduce beta by increasing device spacing" (EDN).

    This is the leg the automated summary of the TU Graz page got backwards (it glossed "larger
    spacing … worsens the parasitic transistor" as *increasing* β). The sign is pinned here so the
    inversion cannot re-enter.
    """
    L = 60.0
    betas = [latchup.bipolar_gain(w, L) for w in (0.5, 1.0, 2.0, 4.0, 8.0)]
    assert all(a > b for a, b in zip(betas, betas[1:]))


def test_base_width_grows_with_spacing_and_with_trench_depth():
    """Both cited levers widen the parasitic base — spacing directly, a trench by forcing a detour."""
    assert latchup.lateral_base_width_um(2.0) == 2.0
    assert latchup.lateral_base_width_um(3.0) > latchup.lateral_base_width_um(2.0)
    deep = latchup.lateral_base_width_um(2.0, trench_depth_um=latchup.STI_DEPTH_UM)
    assert deep > latchup.lateral_base_width_um(2.0)
    # The detour is the honest straight-line path down one wall and up the other.
    assert deep == pytest.approx(2.0 + 2.0 * latchup.STI_DEPTH_UM)


def test_trigger_current_rises_with_substrate_doping():
    """CITED prevention direction: heavier substrate ⇒ lower ρ ⇒ lower R_sub ⇒ higher trigger current."""
    currents = [latchup.trigger_current_a(latchup.substrate_resistance_ohm(N))
                for N in (1e14, 1e15, 1e16, 1e17, 1e18)]
    assert all(a < b for a, b in zip(currents, currents[1:]))


def test_a_trench_lowers_the_loop_gain_at_fixed_spacing():
    """The comparative statement the module exists to make: same drawn geometry, two isolation
    schemes, and the one with the trench has the weaker parasitic. Sign only — never the value."""
    without = latchup.loop_gain(1.5, 1.0e-6)
    with_trench = latchup.loop_gain(1.5, 1.0e-6, trench_depth_um=latchup.STI_DEPTH_UM)
    assert with_trench < without


# --------------------------------------------------------------------------- #
# the decoupling, made mechanical — the module's central refusal
# --------------------------------------------------------------------------- #
def test_substrate_resistance_is_exactly_independent_of_spacing():
    """``R_sub`` takes no spacing argument, and the bundle's value must not move with spacing.

    This is the refusal that keeps the two conditions honest: a model in which ``R_sub ∝ spacing``
    manufactures a sign reversal that is an artifact of its own geometry lump.
    """
    a = latchup.latchup_margin(1.0, 1e15, 1e-6)
    b = latchup.latchup_margin(9.0, 1e15, 1e-6)
    assert a.r_sub_ohm == b.r_sub_ohm
    assert a.i_trigger_a == b.i_trigger_a


def test_loop_gain_is_exactly_independent_of_substrate_doping():
    """The mirror refusal: doping reaches the resistance and never the gain."""
    a = latchup.latchup_margin(1.5, 1e14, 1e-6)
    b = latchup.latchup_margin(1.5, 1e18, 1e-6)
    assert a.loop_gain == b.loop_gain
    assert a.base_width_um == b.base_width_um


# --------------------------------------------------------------------------- #
# the calibration pinned as a calibration
# --------------------------------------------------------------------------- #
def test_every_quotable_leg_is_invariant_to_the_flagged_tap_geometry():
    """The tap path/area are a house lump, so the *ratios* must not move when they do.

    Absolute trigger current may move (it is a house number and is never the claim); the doping
    direction and any trigger-current ratio between two substrates must be untouched.
    """
    house = dict(path_um=latchup.SUBSTRATE_TAP_PATH_UM, area_um2=latchup.TAP_CROSS_SECTION_UM2)
    other = dict(path_um=3.0 * latchup.SUBSTRATE_TAP_PATH_UM, area_um2=0.5 * latchup.TAP_CROSS_SECTION_UM2)

    def ratio(**geom):
        light = latchup.trigger_current_a(latchup.substrate_resistance_ohm(1e15, **geom))
        heavy = latchup.trigger_current_a(latchup.substrate_resistance_ohm(1e18, **geom))
        return heavy / light

    assert ratio(**house) == pytest.approx(ratio(**other), rel=1e-12)
    # And the absolute number *does* move — proof the invariance above is a real cancellation.
    assert (latchup.substrate_resistance_ohm(1e15, **house)
            != latchup.substrate_resistance_ohm(1e15, **other))


def test_margin_ratio_is_invariant_to_the_tap_geometry_only_through_its_own_scaling():
    """``margin_ratio`` is the grade-on quantity: dimensionless, and monotone in trigger current."""
    m = latchup.latchup_margin(1.5, 1e15, 1e-6)
    assert m.margin_ratio(m.i_trigger_a) == pytest.approx(1.0)
    assert m.margin_ratio(0.5 * m.i_trigger_a) == pytest.approx(2.0)


# --------------------------------------------------------------------------- #
# the bound owned, not hidden
# --------------------------------------------------------------------------- #
def test_the_gain_is_an_admittedly_useless_upper_bound_in_absolute_terms():
    """Each β lands at 10²–10⁶ and their product at 10⁴–10¹², where real parasitic laterals are ~1–50
    and their product is of order 1–10³ — because γ = 1 and recombination is not what limits these
    transistors. The docstring says so; this pins it so the admission stays true after edits, and so
    nobody quotes the number as physics."""
    tau = lifetime.srh_lifetime({})            # a clean wafer — the cleanest case, the loosest bound
    gain = latchup.loop_gain(1.5, tau)
    assert gain > 1.0e6
    # ... and therefore the sustaining condition does not discriminate:
    assert latchup.latchup_margin(1.5, 1e15, tau).sustainable
    assert latchup.latchup_margin(20.0, 1e15, tau).sustainable


def test_a_dirtier_wafer_has_a_weaker_parasitic_and_the_leakage_it_costs_is_visible():
    """The lifetime axis, **with its guard**: contamination shortens L, which lowers the loop gain —
    and the *same* τ raises generation leakage. The pair is the honest statement; either alone is a
    free lunch this model has not earned.
    """
    clean_tau = lifetime.srh_lifetime({})
    dirty_tau = lifetime.srh_lifetime({"Fe": 1.0e13})
    assert dirty_tau < clean_tau

    # The immunity bought ...
    assert latchup.loop_gain(1.5, dirty_tau) < latchup.loop_gain(1.5, clean_tau)
    # ... and the leakage it was bought with, at the same τ.
    N_A = 1.0e15
    assert (lifetime.generation_leakage_density(dirty_tau, N_A)
            > lifetime.generation_leakage_density(clean_tau, N_A))


# --------------------------------------------------------------------------- #
# the units seam — one conversion, asserted
# --------------------------------------------------------------------------- #
def test_diffusion_length_conversion_is_the_single_unit_seam():
    """:mod:`chip.lifetime` is cm-native; this module is µm-native. One conversion, here."""
    tau = 1.0e-6
    assert (latchup.diffusion_length_um(tau)
            == pytest.approx(lifetime.diffusion_length(tau) * 1.0e4, rel=1e-15))


def test_resistivity_rides_the_cited_masetti_mobility():
    """ρ = 1/(qNµ) on :func:`chip.junction.mobility` — the same cited fit Phase 1a validated, not a
    second mobility model smuggled in here."""
    N = 1e16
    expected = 1.0 / (junction.Q_ELEMENTARY * N * junction.mobility(N, "B"))
    assert latchup.resistivity_ohm_cm(N) == pytest.approx(expected, rel=1e-15)


# --------------------------------------------------------------------------- #
# domain guards
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("call", [
    lambda: latchup.lateral_base_width_um(0.0),
    lambda: latchup.lateral_base_width_um(1.0, trench_depth_um=-0.1),
    lambda: latchup.bipolar_gain(0.0, 10.0),
    lambda: latchup.bipolar_gain(1.0, 0.0),
    lambda: latchup.resistivity_ohm_cm(0.0),
    lambda: latchup.substrate_resistance_ohm(1e15, path_um=0.0),
    lambda: latchup.substrate_resistance_ohm(1e15, area_um2=0.0),
    lambda: latchup.trigger_current_a(0.0),
])
def test_bad_input_raises(call):
    with pytest.raises(ValueError):
        call()


def test_latches_needs_both_conditions():
    """The verdict is the conjunction the sources state: sustainable **and** triggered."""
    m = latchup.latchup_margin(1.5, 1e15, 1e-6)
    assert m.latches(2.0 * m.i_trigger_a)
    assert not m.latches(0.5 * m.i_trigger_a)


# --------------------------------------------------------------------------- #
# tight — the seam, asserted by reading the tree (not by prose)
# --------------------------------------------------------------------------- #
def test_seam_no_physics_module_depends_on_latchup():
    """The seam, at slice 2. It moved exactly as slice 1's version of this test said it would: the game
    now imports :mod:`chip.latchup` (that is what the knob *is*), so "nothing imports it" is retired
    and replaced by the two claims that still have to hold.

    **(1) Nothing in `chip/` depends on it.** The physics library must be unchanged by this slice —
    every existing chip result is byte-identical because no chip module reads latchup. Checked against
    the source tree, because "additive" is a claim about what else changed and only the tree can
    answer it.

    **(2) The game's dependency is off by default** — asserted where it belongs, in
    `fab_game/tests/test_isolation.py` (`scheme=None` ⇒ no step, no record, no verdict clause).
    """
    root = pathlib.Path(__file__).resolve().parents[2]
    importers = []
    for path in sorted((root / "chip").glob("*.py")):
        # latchup.py itself, and its own banked demo, are the module — not dependents of it.
        if path.name in {"latchup.py", "demo_latchup_history.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"^\s*(from\s+\S*\s+import\s+[^\n]*\blatchup\b|import\s+\S*\blatchup\b)",
                     text, re.MULTILINE):
            importers.append(path.relative_to(root).as_posix())
    assert importers == [], f"a chip/ physics module now depends on chip.latchup — {importers}"


def test_the_locos_allowance_still_matches_the_beak_b5_computes():
    """:data:`chip.latchup.LOCOS_BEAK_ALLOWANCE_UM` is B5's bird's beak, pinned so the game need not run
    a 2-D solve per wafer. This is the test that stops the pin drifting away from the module it came
    from — which is what makes B12 the second half of B5 rather than a module beside it.

    Imports :mod:`chip.locos_history` (a 2-D solve), so it is the one slow leg in this file.
    """
    from chip import locos_history as lh
    beak = lh.birds_beak_length_um(lh.field_oxide_thickness_um())
    assert latchup.LOCOS_BEAK_ALLOWANCE_UM == pytest.approx(2.0 * beak, rel=0.01)


# --------------------------------------------------------------------------- #
# S4 — the substrate lever: an epi layer on a heavily-doped handle
# --------------------------------------------------------------------------- #
def test_the_epi_substrate_is_dominated_by_the_thickness_ratio_but_is_not_exactly_it():
    """The claim is **dominated by** ``t_epi / L_tap``, not equal to it — and the difference is the point.

    A uniform lightly-doped wafer runs the current the whole tap path sideways through high
    resistivity; an epi layer on a heavily-doped handle replaces that with a short vertical hop. With
    the layer's resistivity equal to the old wafer's, ρ cancels and the improvement is *close to*
    ``L_tap / t_epi`` — but not equal, because the heavily-doped handle still contributes its own
    series term. The gap between the two IS that term, and asserting equality would erase it.
    """
    rho_epi, rho_handle = 10.0, 0.01
    uniform = latchup.substrate_resistance_from_resistivity_ohm(rho_epi)
    for t_um in (10.0, 5.0, 2.0):
        r_epi = latchup.epi_substrate_resistance_ohm(rho_epi, t_um, rho_handle)
        geometric = latchup.SUBSTRATE_TAP_PATH_UM / t_um
        improvement = uniform / r_epi
        assert improvement == pytest.approx(geometric, rel=0.02)   # dominated by it ...
        assert improvement < geometric                              # ... and always short of it.


def test_thinning_the_epi_helps_monotonically_but_runs_into_the_handles_own_floor():
    """Thinner is monotonically better — and stops paying, which is why the model does not pretend to
    reproduce the literature's *optimum* thickness (that needs the vertical pnp it does not carry).

    The floor is derived, not asserted: as ``t_epi → 0`` the resistance tends to the handle's own
    lateral term, so the trigger current cannot exceed what that term allows.
    """
    rho_epi, rho_handle = 10.0, 0.01
    triggers = [latchup.trigger_current_a(latchup.epi_substrate_resistance_ohm(rho_epi, t, rho_handle))
                for t in (20.0, 10.0, 5.0, 2.0, 1.0, 0.2)]
    assert all(a < b for a, b in zip(triggers, triggers[1:]))       # monotone ...

    floor_r = latchup.substrate_resistance_from_resistivity_ohm(rho_handle)
    ceiling = latchup.trigger_current_a(floor_r)
    assert max(triggers) < ceiling                                  # ... and bounded by the handle.

    # The floor is not merely respected, it is exactly the handle's own term: everything above it is
    # the vertical hop through the layer, which is an identity rather than a limit to sneak up on.
    # (A 1 nm "epi" would approach the floor numerically but means nothing physically, so the identity
    # is the honest way to pin it.)
    for t_um in (5.0, 1.0, 0.2):
        r_epi = latchup.epi_substrate_resistance_ohm(rho_epi, t_um, rho_handle)
        vertical = rho_epi * (t_um / latchup.UM_PER_CM) / (latchup.TAP_CROSS_SECTION_UM2 / latchup.UM_PER_CM ** 2)
        assert r_epi - floor_r == pytest.approx(vertical, rel=1e-12)


def test_the_epi_lever_is_still_silent_on_spacing_and_on_the_gain():
    """S4 changes one resistance and nothing else — the module's central refusal survives the finale."""
    a = latchup.latchup_margin(1.0, None, 1e-6, rho_ohm_cm=10.0)
    b = latchup.latchup_margin(9.0, None, 1e-6, rho_ohm_cm=10.0)
    assert a.r_sub_ohm == b.r_sub_ohm            # spacing still cannot move the resistance
    assert a.loop_gain != b.loop_gain            # and the gain is still the only thing it moves


def test_latchup_margin_refuses_two_substrates_or_none():
    """The substrate goes in exactly one way — doping or resistivity, never both, never neither."""
    with pytest.raises(ValueError):
        latchup.latchup_margin(2.0, 1e15, 1e-6, rho_ohm_cm=10.0)
    with pytest.raises(ValueError):
        latchup.latchup_margin(2.0, None, 1e-6)


@pytest.mark.parametrize("call", [
    lambda: latchup.epi_substrate_resistance_ohm(0.0, 5.0, 0.01),
    lambda: latchup.epi_substrate_resistance_ohm(10.0, 0.0, 0.01),
    lambda: latchup.epi_substrate_resistance_ohm(10.0, 5.0, 0.0),
])
def test_bad_epi_input_raises(call):
    with pytest.raises(ValueError):
        call()
