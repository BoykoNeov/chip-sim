"""F8 slice 2 — the CMP knob wired, and the wire that finally has a spread of its own.

:mod:`chip.cmp`'s own tests assert the physics in isolation (the forced-overpolish law, the window collapse,
the kinematic identity, the scale refusal). **These** tests assert what only the consumer can show: that
F4's law ``∂ln f/∂ln I_Dsat = 1 − wire_share`` was true of the tree **because nothing upstream could make a
wire differ from die to die** — and that once a polish sits upstream of it, the chip-delay histogram gains a
component the transistor histogram cannot explain.

The structural point every test below turns on:

  * F4's ``τ_wire`` was **common-mode** — the same picoseconds on every die — because ``steps.py`` read a
    *default-constructed* :class:`chip.interconnect.WireGeometry`. That was an artifact of the flow, not a
    finding about wires;
  * CMP is the step that sets a copper wire's thickness, and sets it **per die** (the pressure hot spot at
    the wafer edge; Preston linear in ``P``; ``V`` barred from carrying any signature). So ``τ_wire``
    becomes per-die and F4's law loses the clause it was derived under — **F8 modifies F4's premise
    rather than decorating it**;
  * the two failure directions read the *same* removal number: too short and the slow centre keeps residual
    copper bridging the trenches (a **functional short, graded by radius** — a centre disc of dies, never
    the whole wafer), too long and the fast rim is over-polished into a **slower part, not a dead one**.

The seam ladder: ``polish_s = None`` → **no step runs at all** (no record anywhere, the device reads the house
line, byte-for-byte F4) → engaged, uniform (``s = 0``) and set to the clear time → every die's thickness is
nominal and the delay is byte-for-byte F4 on every die (the two-sided window's seam, *inside* the engaged
run) → engaged and non-uniform (the payload). Import + numeric only, so it rides the fast lane.
"""
from __future__ import annotations

import math
from dataclasses import replace

import pytest

from chip import cmp
from chip import interconnect as ic

from fab_game.pipeline import diagnose, rework_litho, run_line
from fab_game.recipe import CmpKnobs, DeviceKnobs, LithoKnobs, Recipe
from fab_game.spec import DEFAULT_SPECS, DelayBins, SpeedBin, SpeedBins
from fab_game.state import Die
from fab_game.steps import cmp_step, device_step
from fab_game.variation import NO_VARIATION, Variation

_GRID = 11                       # the G6 die map (~89 dies) — enough radii to grade a disc by
_SEED = 0
_S = 0.10                        # the house radial amplitude (FLAGGED — a test knob, never a claim)

# The G6 market ladder in shape, around the nominal ~3.29 mA part (the F4/F5 tests' construction).
_SPEED_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=3.38),
    SpeedBin("typical", lo_mA=3.21, hi_mA=3.38),
    SpeedBin("value", lo_mA=3.10, hi_mA=3.21),
))


def _clear_time(s: float = _S, **kw) -> float:
    """The clear-everywhere polish time at spread ``s`` — the window's lower edge, in the knob's unit."""
    return CmpKnobs(polish_s=1.0, nonuniformity=s, **kw).clear_time_s


def _polished(polish_s: float | None, s: float = _S, metal: str | None = "Cu", **kw) -> Recipe:
    return Recipe(cmp=CmpKnobs(polish_s=polish_s, nonuniformity=s, **kw),
                  device=DeviceKnobs(interconnect=metal))


def _run(recipe: Recipe, *, variation=NO_VARIATION, specs=DEFAULT_SPECS, grid_n: int = _GRID):
    return run_line(recipe, seed=_SEED, variation=variation, specs=specs, grid_n=grid_n)


def _rec(die: Die, step: str):
    return next(r for r in die.history if r.step == step)


def _by_site(wafer) -> dict:
    return {d.site: d for d in wafer.dies}


def _histogram(wafer) -> dict:
    hist: dict = {}
    for d in wafer.dies:
        if d.bin is not None:
            hist[d.bin] = hist.get(d.bin, 0) + 1
    return hist


# --------------------------------------------------------------------------- #
# 1. The seam — no knob, no step, no record: byte-for-byte F4
# --------------------------------------------------------------------------- #
def test_the_default_recipe_runs_no_cmp_step_at_all():
    """``polish_s = None`` ⇒ the step is absent from the flow, not present-and-inert."""
    assert Recipe().cmp.engaged is False
    w = _run(Recipe(device=DeviceKnobs(interconnect="Cu")), grid_n=5)
    assert "cmp" not in [r.step for r in w.provenance]
    for d in w.dies:
        assert "cmp" not in [r.step for r in d.history]
        assert d.metal_thickness_nm is None and d.shorted is None and d.polished_out is None
        dev = _rec(d, "device")
        assert "metal_thickness_um" not in dev.knobs_in
        assert "wire_R_factor" not in dev.outputs


def test_without_cmp_the_wire_is_common_mode_which_is_f4s_premise():
    """The clause F8 exists to end, pinned as it stood: one τ_wire on every die, however the transistor spreads."""
    w = _run(Recipe(device=DeviceKnobs(interconnect="Cu")), variation=Variation(cd_sigma_nm=7.0))
    wires = {_rec(d, "device").outputs["tau_wire_ps"] for d in w.dies if d.delay is not None}
    drives = {d.i_dsat for d in w.dies if d.i_dsat is not None}
    assert len(wires) == 1 and len(drives) > 1


# --------------------------------------------------------------------------- #
# 2. The refusal — CMP defines a damascene wire, and only a damascene wire
# --------------------------------------------------------------------------- #
def test_the_knob_refuses_a_line_with_no_metal_level_to_polish():
    with pytest.raises(ValueError, match="interconnect is None"):
        _run(_polished(_clear_time(), metal=None), grid_n=3)


def test_the_knob_refuses_aluminium_because_it_is_subtractively_etched():
    """The source's own first paragraph: copper cannot be plasma-etched, so damascene + CMP defines the
    copper line. On an Al line the polish planarizes the dielectric and never sets the wire — the
    observable this step exists for does not exist there, so the number is refused, not returned."""
    with pytest.raises(ValueError, match="subtractively etched"):
        _run(_polished(_clear_time(), metal="Al"), grid_n=3)
    assert "Al" in ic.BULK_ERA_METALS and "Al" not in cmp.DAMASCENE_METALS   # the refusal is the registry's


# --------------------------------------------------------------------------- #
# 3. Where the step sits, and what it records
# --------------------------------------------------------------------------- #
def test_the_step_runs_after_the_etch_and_before_the_device_reads_the_wire():
    w = _run(_polished(_clear_time()), grid_n=5)
    assert [r.step for r in w.provenance] == [
        "purification", "wafer_prep", "diffusion", "oxidation", "litho", "etch_deposition", "cmp",
        "device", "test", "packaging"]
    for d in w.dies:
        steps = [r.step for r in d.history]
        assert steps.index("etch_deposition") < steps.index("cmp") < steps.index("device")


def test_the_wafer_record_carries_the_headline_with_no_house_constant_in_it():
    """``s/(1−s)`` and the clear time are the record's spec-free numbers; both are chip.cmp's, re-derived here."""
    t = _clear_time()
    w = _run(_polished(t), grid_n=5)
    rec = next(r for r in w.provenance if r.step == "cmp")
    k = CmpKnobs(polish_s=t, nonuniformity=_S)
    assert rec.summary["forced_overpolish_ratio"] == _S / (1.0 - _S)
    assert rec.summary["clear_time_s"] == pytest.approx(k.overburden_um / ((1.0 - _S) * k.removal_rate_um_s))
    assert rec.summary["clear_time_s"] == pytest.approx(t)
    assert rec.summary["shorted_radius_frac"] == 0.0 and rec.summary["n_shorted"] == 0
    assert rec.summary["nominal_thickness_nm"] == ic.WireGeometry().thickness_um * 1.0e3


def test_the_per_die_removal_is_preston_linear_in_the_radial_pressure_factor():
    """The chain radius → pressure → removal, with no exponent to soften it: removal ratios ARE pressure ratios."""
    k = CmpKnobs(polish_s=_clear_time(), nonuniformity=_S)
    w = _run(_polished(k.polish_s), grid_n=5)
    centre = _by_site(w)[(2, 2)]
    assert centre.radius_frac == 0.0
    r0 = _rec(centre, "cmp").knobs_in["removal_um"]
    for d in w.dies:
        c = _rec(d, "cmp").knobs_in
        assert c["pressure_factor"] == cmp.radial_pressure_factor(d.radius_frac, _S)
        assert c["removal_um"] / r0 == pytest.approx(c["pressure_factor"] / (1.0 - _S))
    # …and the profile is the cited SIGN: the centre is the slow site, the rim the fast one.
    assert min(_rec(d, "cmp").knobs_in["removal_um"] for d in w.dies) == r0


# --------------------------------------------------------------------------- #
# 4. The payload — a delay spread the transistor cannot explain
# --------------------------------------------------------------------------- #
def test_the_transistor_cannot_explain_the_delay_spread():
    """**The assertion that earns the slice.** Zero variation ⇒ every transistor on the wafer is the SAME
    transistor (one I_Dsat, one τ_gate) — and the chip delay still spreads, monotonically in radius,
    because the wire under it was polished thinner toward the rim. No existing per-die number is upstream
    of this; ``∂τ_wire/∂I_Dsat = 0`` and it moved anyway."""
    w = _run(_polished(_clear_time()))
    devs = {d.site: _rec(d, "device").outputs for d in w.dies}
    assert len({d.i_dsat for d in w.dies}) == 1                          # one transistor
    assert len({o["tau_gate_ps"] for o in devs.values()}) == 1           # …with one gate delay
    wires = sorted((d.radius_frac, devs[d.site]["tau_wire_ps"]) for d in w.dies)
    assert len({tw for _, tw in wires}) > 1                              # …and MANY wire delays
    for (r_a, tw_a), (r_b, tw_b) in zip(wires, wires[1:]):
        assert tw_a <= tw_b                                              # slower toward the rim, never faster
    assert len({d.delay for d in w.dies}) > 1                            # the histogram the transistor can't explain


def test_f4s_law_loses_the_clause_it_was_derived_under():
    """``1 − wire_share`` was ONE number on the wafer because τ_wire was; now it is a per-die number."""
    off = _run(Recipe(device=DeviceKnobs(interconnect="Cu")))
    on = _run(_polished(_clear_time()))
    assert len({_rec(d, "device").outputs["drive_sensitivity"] for d in off.dies}) == 1
    assert len({_rec(d, "device").outputs["drive_sensitivity"] for d in on.dies}) > 1


def test_the_centre_die_at_the_clear_time_is_byte_for_byte_f4():
    """The seam INSIDE the engaged run: at the clear-everywhere time the slowest site (the centre) removes
    exactly the overburden — no residual, no overpolish — so its wire is the house line and its delay is
    F4's number exactly. The forced overpolish lands on every OTHER die: that is the s/(1−s) law seen from
    the wafer."""
    off = _by_site(_run(Recipe(device=DeviceKnobs(interconnect="Cu"))))
    on = _by_site(_run(_polished(_clear_time())))
    centre = (_GRID // 2, _GRID // 2)
    assert on[centre].radius_frac == 0.0
    assert on[centre].metal_thickness_nm == ic.WireGeometry().thickness_um * 1.0e3
    assert on[centre].delay == off[centre].delay
    assert _rec(on[centre], "device").outputs["tau_wire_ps"] == _rec(off[centre], "device").outputs["tau_wire_ps"]
    rim = max(on.values(), key=lambda d: d.radius_frac)
    assert rim.metal_thickness_nm < on[centre].metal_thickness_nm
    assert rim.delay > off[rim.site].delay


def test_a_uniform_polish_at_the_clear_time_reproduces_f4_on_every_die():
    """``s = 0`` ⇒ the forced overpolish is exactly zero ⇒ every die keeps the nominal thickness ⇒ the
    engaged wafer is byte-for-byte the unpolished one in every delay. The window's seam, wafer-wide."""
    off = _by_site(_run(Recipe(device=DeviceKnobs(interconnect="Cu"))))
    on = _run(_polished(_clear_time(0.0), s=0.0))
    for d in on.dies:
        assert d.shorted is False and d.polished_out is False
        assert d.metal_thickness_nm == ic.WireGeometry().thickness_um * 1.0e3
        assert d.delay == off[d.site].delay


def test_a_polished_die_keeps_its_transistor_bit_for_bit():
    """CMP touches the wire and nothing else: V_t, I_Dsat, C_ox, leakage are byte-identical with the knob on."""
    var = Variation(cd_sigma_nm=4.0)
    off = _by_site(_run(Recipe(device=DeviceKnobs(interconnect="Cu")), variation=var))
    on = _run(_polished(3.0 * _clear_time()), variation=var)
    for d in on.dies:
        o = off[d.site]
        assert (d.V_t, d.i_dsat, d.j_leak, d.bv_V, d.cd_nm, d.t_ox_um) == (o.V_t, o.i_dsat, o.j_leak, o.bv_V, o.cd_nm, o.t_ox_um)
        assert _rec(d, "device").outputs["C_ox"] == _rec(o, "device").outputs["C_ox"]


# --------------------------------------------------------------------------- #
# 5. Under-polish — a short, graded by radius (gradual, never a cliff)
# --------------------------------------------------------------------------- #
def test_under_polish_shorts_a_centre_disc_whose_edge_is_the_closed_form():
    """Too short a polish leaves residual copper where removal fell short — the SLOW centre — and the set of
    shorted dies is exactly ``{r < r*}`` with ``r*`` chip.cmp's closed form. The shorted trench is untouched
    (nominal thickness): the failure is copper left standing BETWEEN the lines, not copper lost from them."""
    k = CmpKnobs(polish_s=0.9 * _clear_time(), nonuniformity=_S)
    w = _run(_polished(k.polish_s))
    r_star = k.shorted_radius_frac
    assert 0.0 < r_star < 1.0
    shorted = {d.site for d in w.dies if d.shorted}
    assert shorted == {d.site for d in w.dies if d.radius_frac < r_star}
    assert 0 < len(shorted) < w.n_dies
    for d in w.dies:
        if d.shorted:
            assert d.verdict.passed is False
            assert any("CMP under-polish" in r for r in d.verdict.reasons)
            assert d.metal_thickness_nm == ic.WireGeometry().thickness_um * 1.0e3
            assert "under-polish SHORT" in diagnose(d)
        else:
            assert d.verdict.passed is True
    rec = next(r for r in w.provenance if r.step == "cmp")
    assert rec.summary["n_shorted"] == len(shorted) and rec.summary["shorted_radius_frac"] == r_star


def test_the_short_is_gradual_in_the_polish_time_not_a_cliff():
    """Shorten the polish step by step: the shorted disc grows ring by ring, never nothing→everything. The
    gradual-failure discipline, delivered by spatial non-uniformity of the offending quantity (removal)."""
    t = _clear_time()
    counts = []
    for frac in (1.00, 0.98, 0.96, 0.94, 0.92, 0.90, 0.88, 0.86):
        w = _run(_polished(frac * t))
        counts.append(sum(1 for d in w.dies if d.shorted))
    assert counts[0] == 0
    assert counts == sorted(counts)                                      # monotone as the polish shortens
    assert len({c for c in counts if 0 < c < _GRID * _GRID}) >= 3       # several partial rings, not one jump
    assert counts[-1] < w.n_dies                                         # …and even 0.86·t has not killed the rim


def test_a_polish_that_clears_nowhere_shorts_everything():
    k = CmpKnobs(polish_s=0.5 * _clear_time(), nonuniformity=_S)
    assert k.shorted_radius_frac == 1.0
    w = _run(_polished(k.polish_s), grid_n=5)
    assert all(d.shorted for d in w.dies)
    assert all(d.verdict.passed is False for d in w.dies)


# --------------------------------------------------------------------------- #
# 6. Over-polish — a slower part, not a dead one
# --------------------------------------------------------------------------- #
def test_over_polish_thins_the_rim_and_slows_it_without_killing_it():
    """A long polish over-thins every die (the rim most), the wire's R rises by exactly H₀/H, and τ_wire
    rises by exactly that factor (C never read H) — and the wafer still yields 100 %: dishing is a
    grading currency, not a yield one."""
    off = _by_site(_run(Recipe(device=DeviceKnobs(interconnect="Cu"))))
    w = _run(_polished(3.0 * _clear_time()))
    H0 = ic.WireGeometry().thickness_um
    assert all(d.verdict.passed for d in w.dies)
    by_r = sorted(w.dies, key=lambda d: d.radius_frac)
    for a, b in zip(by_r, by_r[1:]):
        assert a.metal_thickness_nm >= b.metal_thickness_nm             # thinner toward the rim
    for d in w.dies:
        assert d.shorted is False and d.metal_thickness_nm < H0 * 1.0e3
        dev, pol = _rec(d, "device"), _rec(d, "cmp")
        assert dev.knobs_in["metal_thickness_um"] == pytest.approx(pol.outputs["thickness_um"])
        assert dev.outputs["wire_R_factor"] == pytest.approx(pol.outputs["resistance_factor"])
        assert dev.outputs["wire_R_factor"] == pytest.approx(H0 / d.metal_thickness_um)
        tw_off = _rec(off[d.site], "device").outputs["tau_wire_ps"]
        assert dev.outputs["tau_wire_ps"] / tw_off == pytest.approx(dev.outputs["wire_R_factor"])
        assert dev.outputs["tau_gate_ps"] == _rec(off[d.site], "device").outputs["tau_gate_ps"]


def test_at_the_house_pitch_the_loss_is_erosion_and_dishing_is_exactly_zero():
    """chip.cmp's second finding, seen from the game: the 250 nm line on a 0.5 µm pitch is below the cited
    dishing trend's zero crossing, so every nanometre the rim loses is oxide erosion."""
    w = _run(_polished(3.0 * _clear_time()), grid_n=5)
    assert Recipe().cmp.pattern.sub_micron
    for d in w.dies:
        o = _rec(d, "cmp").outputs
        assert o["dish_loss"] == 0.0
        assert o["erosion_loss"] == o["loss_fraction"]
    assert max(_rec(d, "cmp").outputs["erosion_loss"] for d in w.dies) > 0.0


def test_over_polish_is_named_in_the_trail_only_when_it_cost_thickness():
    w = _by_site(_run(_polished(3.0 * _clear_time()), grid_n=5))
    from fab_game.state import Verdict
    rim = replace(max(w.values(), key=lambda d: d.radius_frac), verdict=Verdict(False, ("forced",)))
    assert "over-polish" in diagnose(rim) and "slower part" in diagnose(rim)
    exact = _by_site(_run(_polished(_clear_time(0.0), s=0.0), grid_n=5))
    centre = replace(exact[(2, 2)], verdict=Verdict(False, ("forced",)))
    assert "CMP" not in diagnose(centre)                                  # exactly cleared: nothing to say


def test_a_runaway_polish_polishes_the_trench_out_and_emits_no_delay():
    """No conductor ⇒ no thickness, no resistance, no delay — a functional kill, not a divide-by-zero."""
    w = _run(_polished(2000.0), grid_n=5)
    assert all(d.polished_out for d in w.dies)
    for d in w.dies:
        assert d.metal_thickness_nm is None and d.delay is None
        assert any("polished out" in r for r in d.verdict.reasons)
        assert "tau_total_ps" not in _rec(d, "device").outputs
        assert "POLISHED OUT" in diagnose(d)


# --------------------------------------------------------------------------- #
# 7. What the market sees — grading by position
# --------------------------------------------------------------------------- #
def test_delay_binning_now_grades_the_same_transistor_by_where_it_sat_on_the_polisher():
    """F4's binning inversion, with F8 under it: anchor the market ladder on the centre part, run a wafer of
    IDENTICAL transistors, and the grades still spread — outward, monotone in radius — because the wire
    under the rim was polished thinner. The I_Dsat histogram is a single value throughout."""
    s = 0.20
    t = _clear_time(s)
    anchor = _by_site(_run(_polished(t, s=s), grid_n=_GRID))[(_GRID // 2, _GRID // 2)]
    bins = DelayBins.from_speed_bins(_SPEED_BINS, anchor.i_dsat_mA, anchor.delay_ps)
    specs = replace(DEFAULT_SPECS, speed_bins=_SPEED_BINS, delay_bins=bins)
    w = _run(_polished(t, s=s), specs=specs)
    assert len({d.i_dsat for d in w.dies}) == 1
    hist = _histogram(w)
    assert len(hist) >= 2, hist
    rank = {label: i for i, label in enumerate(("premium", "typical", "value", "reject"))}
    by_r = sorted(w.dies, key=lambda d: d.radius_frac)
    for a, b in zip(by_r, by_r[1:]):
        assert rank[a.bin] <= rank[b.bin]                                 # a grade never IMPROVES outward
    assert _by_site(w)[anchor.site].bin == "typical"                      # the anchor is 'typical' by construction


# --------------------------------------------------------------------------- #
# 8. The determinism contract, and the rework paths
# --------------------------------------------------------------------------- #
def test_cmp_consumes_no_randomness():
    """A knob-level radial profile (like the OSF ring): deterministic, so the RNG stream is untouched and a
    no-variation run stays seed-independent with the knob on."""
    var = Variation()
    off = run_line(Recipe(device=DeviceKnobs(interconnect="Cu")), seed=3, variation=var, grid_n=7)
    on = run_line(_polished(_clear_time()), seed=3, variation=var, grid_n=7)
    assert [d.cd_nm for d in on.dies] == [d.cd_nm for d in off.dies]
    a = run_line(_polished(_clear_time()), seed=1, variation=NO_VARIATION, grid_n=5)
    b = run_line(_polished(_clear_time()), seed=999, variation=NO_VARIATION, grid_n=5)
    assert a == b


def test_litho_rework_keeps_the_polished_wire():
    """A strip-and-re-expose re-runs litho → etch → device on the failed dies; the polished thickness is die
    state, so the re-read device sees the SAME wire it had (rework does not re-polish)."""
    bad = replace(_polished(3.0 * _clear_time()), litho=LithoKnobs(defocus_nm=90.0))
    var = Variation()
    w = run_line(bad, seed=0, variation=var, grid_n=7)
    w2 = rework_litho(w, bad, variation=var, focus_correction_nm=-90.0)
    assert len(w2.rework_log) == len(w.rework_log) + 1
    for d0, d1 in zip(w.dies, w2.dies):
        assert d1.metal_thickness_nm == d0.metal_thickness_nm
        if len(d1.history) > len(d0.history):                            # a reworked die
            assert _rec(d1, "device").knobs_in["metal_thickness_um"] == pytest.approx(d1.metal_thickness_um)


# --------------------------------------------------------------------------- #
# 9. The step function on its own
# --------------------------------------------------------------------------- #
def test_the_step_polishes_a_die_whose_transistor_never_formed():
    """The wafer is polished whole: an unresolved litho image still has copper to clear."""
    k = CmpKnobs(polish_s=_clear_time(), nonuniformity=_S)
    d = cmp_step(Die(site=(0, 0), radius_frac=1.0, resolved=False), k)
    assert d.metal_thickness_nm is not None and d.shorted is False
    d = device_step(d, DeviceKnobs(interconnect="Cu"), 1.0e17)
    assert "refused" in _rec(d, "device").outputs                         # …and the device still refuses


def test_the_knob_validates_its_ranges_and_its_pattern():
    with pytest.raises(ValueError):
        CmpKnobs(nonuniformity=1.0)
    with pytest.raises(ValueError):
        CmpKnobs(polish_s=-1.0)
    with pytest.raises(ValueError, match="pitch_um must exceed"):
        CmpKnobs(pitch_um=ic.WireGeometry().width_um)
    with pytest.raises(ValueError, match="not engaged"):
        CmpKnobs().removal_at(0.5)
    k = CmpKnobs()
    assert k.pattern.density == pytest.approx(ic.WireGeometry().width_um / k.pitch_um)
    assert k.trench_depth_um == ic.WireGeometry().thickness_um
    assert math.isclose(k.removal_rate_um_s * 60.0, 0.5, rel_tol=0.05)    # the house rate: ≈0.5 µm/min (FLAGGED)
