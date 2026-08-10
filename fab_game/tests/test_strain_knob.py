"""F5 slice 2 — the strain knob wired, and the first knob that re-grades the wafer on its own.

:mod:`chip.strain`'s own tests assert the physics in isolation (the registry, the elasticity *definition*,
the refusal). **These** tests assert what only the consumer can show: that ``µ`` — the one factor in
``I_Dsat = ½·µ·C_ox·(W/L)·(V_GS − V_t)²`` that no step in this line had ever moved — now moves, and that
what it moves is a currency the game **already grades**.

The structural break this slice makes, stated up front because every test below turns on it:

  * ``bv_V`` (slice 2), ``t_rr`` (slice 5), ``j_gate`` (F3) and ``τ_total`` (F4) are all **additive** — a
    new output bolted onto an unchanged device, so engaging one *alone* changes nothing scored. F4 needed
    the **pair** (the wire knob *plus* delay binning) before an outcome moved;
  * strain is not additive. It moves ``I_Dsat`` itself, which :class:`fab_game.spec.SpeedBins` has graded
    on since G6 — so the knob **alone** re-grades the wafer, with **no new scoring surface at all**. That
    is a property of strain being a *process* change to a *device term*, not a new reading beside one.

**And the gain it delivers is the optimistic one, by construction.** On the ideal-contact path (the
default ``sd_contact_squares = 0``) the long-channel form carries ``I ∝ µ`` exactly, so the mobility
factor reaches ``I_Dsat`` **unattenuated** — a µ→I elasticity of 1, where the cited 90 nm devices measured
≈0.5. The tests pin that as an *upper bound with its direction named*, not as a result: the record carries
the cited ``drive_factor`` and ``drive_overstatement`` beside the realized number, and the one mechanism
the model *does* carry that pushes the other way (source degeneration) is pinned to show it sub-linearizes
on its own.

The seam ladder: ``strain=None`` → factor exactly ``1.0`` → ``mu_eff == MU_N_EFF`` → byte-for-byte today's
device (and, because the knob **passes** the seam value rather than branching around it, every default run
exercises :mod:`chip.strain`'s seam on every die). Import + numeric only, so it rides the fast lane.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from chip import device as dev
from chip import strain as st

from fab_game.pipeline import run_line
from fab_game.recipe import DeviceKnobs, Recipe
from fab_game.spec import DEFAULT_SPECS, SpeedBin, SpeedBins
from fab_game.state import Die
from fab_game.steps import device_step
from fab_game.variation import Variation

_N_A = 1.0e17
_T_OX_UM = 0.0141
_CD_NM = 167.0
_GRID = 11                       # the G6 die map (~89 dies) — a real I_Dsat sample to grade
_SEED = 0
_SIGMA = 7.0                     # nm — the loose CD control that spreads the histogram across grades
_WIRED = "tensile_cesl"          # the only mechanism this n-channel device can be built with

# The G6 market ladder in shape, around the nominal ~3.29 mA unstrained part. DEFAULT_SPECS carries a
# single open bin, so a default run would grade everything "pass" and a migration test would pass
# vacuously — the ladder has to be supplied (the F4 test's construction).
_SPEED_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=3.38),
    SpeedBin("typical", lo_mA=3.21, hi_mA=3.38),
    SpeedBin("value", lo_mA=3.10, hi_mA=3.21),
))


def _die(R_s: float | None = None) -> Die:
    return Die(site=(0, 0), radius_frac=0.0, t_ox_um=_T_OX_UM, cd_nm=_CD_NM, nils=4.0, resolved=True,
               R_s=R_s)


def _strained(mechanism: str | None, **kw) -> Recipe:
    return replace(Recipe(), device=DeviceKnobs(strain=mechanism, **kw))


def _histogram(wafer) -> dict:
    hist: dict = {}
    for d in wafer.dies:
        if d.bin is not None:
            hist[d.bin] = hist.get(d.bin, 0) + 1
    return hist


# --------------------------------------------------------------------------- #
# 1. The seam — and it is the *passed* value, not a skipped argument
# --------------------------------------------------------------------------- #
def test_the_seam_is_the_default_argument_so_passing_it_is_the_identity():
    """``mu_eff = MU_N_EFF`` passed explicitly **is** ``saturation_current``'s own default — bit-for-bit.

    The knob resolves through :func:`chip.strain.strained_channel` unconditionally and passes the result,
    rather than branching around the call. That is only legitimate if the seam value is *exactly* the
    default: ``MU_N_EFF · 1.0 == MU_N_EFF`` in binary, so the two calls are the same call. The payoff is
    that the default game path exercises the strain module's seam on **every die of every run** —
    ``test_seam.py``'s ``d.i_dsat == demo_device.compute().i_dsat`` is now standing proof of it.
    """
    mos = dev.threshold_voltage(_N_A, _T_OX_UM, gate="n+poly", channel_length_um=_CD_NM * 1.0e-3)
    V_GS = mos.V_t + 1.0
    assert st.strained_channel(dev.MU_N_EFF, None).mu_strained_cm2_Vs == dev.MU_N_EFF
    assert (dev.saturation_current(mos, V_GS, 10.0)
            == dev.saturation_current(mos, V_GS, 10.0, mu_eff=dev.MU_N_EFF))


def test_strain_absent_emits_no_key_at_all():
    """No strain knob → no record key appears (the fingerprint discipline: a bare record stays bare)."""
    rec = device_step(_die(), DeviceKnobs(strain=None), _N_A).history[-1]
    assert "strain" not in rec.knobs_in and "mu_eff" not in rec.knobs_in
    for key in ("mu_factor", "drive_factor_cited", "drive_overstatement"):
        assert key not in rec.outputs


def test_a_refused_die_carries_no_strain_keys_either():
    """An unresolved image / a bare die refuses **before** the mobility is resolved — no half-record."""
    unresolved = device_step(replace(_die(), resolved=False), DeviceKnobs(strain=_WIRED), _N_A)
    assert unresolved.i_dsat is None
    assert "strain" not in unresolved.history[-1].knobs_in

    bare = device_step(Die(site=(0, 0), radius_frac=0.0), DeviceKnobs(strain=_WIRED), _N_A)
    assert bare.i_dsat is None
    assert "strain" not in bare.history[-1].knobs_in


# --------------------------------------------------------------------------- #
# 2. What moves, what does not — and by exactly how much
# --------------------------------------------------------------------------- #
def test_strain_moves_the_drive_current_and_nothing_else_about_the_device():
    """Mobility is not in the threshold. ``V_t`` and ``C_ox`` are **bit-for-bit** unchanged; ``I_Dsat`` is not.

    The orthogonality that makes strain a clean observable: every other lever in this line that raises
    ``I_Dsat`` (a thinner oxide, a shorter CD, the adjust implant) drags ``V_t`` or ``C_ox`` with it. A
    mechanical state does not — which is why F5 is the first slice whose device number moves without a
    dopant, a thickness or a length changing.
    """
    off = device_step(_die(), DeviceKnobs(strain=None), _N_A)
    on = device_step(_die(), DeviceKnobs(strain=_WIRED), _N_A)
    assert on.V_t == off.V_t
    assert on.history[-1].outputs["C_ox"] == off.history[-1].outputs["C_ox"]
    assert on.i_dsat > off.i_dsat


def test_the_ideal_contact_path_delivers_the_whole_factor_which_is_why_it_is_a_bound():
    """+20% µ → **+20%** drive, exactly. Elasticity 1 *by construction* — and the cited devices got 0.5.

    This is the model's optimism made numeric at the game boundary, not a result to celebrate: the
    long-channel closed form has no other option (``I ∝ µ``), and the 90 nm device the mechanism is cited
    from was velocity-saturated (named, not built). So the realized gain here is the **upper bound**, loose
    by ``drive_overstatement`` ≈ 2 at 90 nm and looser as ``L`` shrinks.
    """
    off = device_step(_die(), DeviceKnobs(strain=None), _N_A)
    on = device_step(_die(), DeviceKnobs(strain=_WIRED), _N_A)
    factor = st.MECHANISMS[_WIRED].mobility_factor
    assert on.i_dsat / off.i_dsat == pytest.approx(factor, rel=1e-12)
    # ...and that is strictly more than the mechanism's own cited drive gain, which is the whole point.
    assert factor > st.MECHANISMS[_WIRED].drive_factor


def test_source_degeneration_sub_linearizes_the_gain_on_its_own():
    """With ``R_series > 0`` the realized gain falls **below** the factor — the model's own damping.

    The elasticity-1 claim is scoped to the ideal-contact path, and the game can show why: the F2/journey
    series resistance feeds the source-degeneration quadratic, which sub-linearizes µ→I without anything
    from F5. It moves in the *same direction* as the velocity saturation the model does not carry — so the
    bound is loosest exactly where the model is most idealized, and never the other way.
    """
    squares = 4.0
    off = device_step(_die(R_s=120.0), DeviceKnobs(strain=None), _N_A, sd_contact_squares=squares)
    on = device_step(_die(R_s=120.0), DeviceKnobs(strain=_WIRED), _N_A, sd_contact_squares=squares)
    ratio = on.i_dsat / off.i_dsat
    assert 1.0 < ratio < st.MECHANISMS[_WIRED].mobility_factor
    # The degeneration is real, not a rounding artefact: it costs a visible slice of the win.
    assert off.i_dsat < device_step(_die(), DeviceKnobs(strain=None), _N_A).i_dsat


# --------------------------------------------------------------------------- #
# 3. The refusal — the era's teaching point at the game boundary
# --------------------------------------------------------------------------- #
def test_the_knob_refuses_the_hole_leg_because_this_device_is_n_channel():
    """``"sige_sd"`` raises rather than returning 1.50 for an electron channel — the sign would invert.

    The refusal is the payload, not a guard rail (the mirror of the wire knob refusing ruthenium). SiGe
    source/drain is the *pMOS* half of the strain era: compressive strain, which helps holes and hurts
    electrons. The simulator has no p-MOSFET to be right about, so a knob that quietly accepted it would
    print a **wrong-signed** number that reads as a result. That the two carriers need opposite strain is
    the era's actual answer — the strain era needed two different processes.
    """
    assert "sige_sd" in st.MECHANISMS and "sige_sd" not in st.WIRED_MECHANISMS
    with pytest.raises(ValueError, match="n-channel"):
        device_step(_die(), DeviceKnobs(strain="sige_sd"), _N_A)

    # Every wired mechanism resolves (the list is derived from the registry, never hand-maintained), and
    # an unknown key still fails the registry lookup rather than silently doing nothing.
    for mechanism in st.WIRED_MECHANISMS:
        assert device_step(_die(), DeviceKnobs(strain=mechanism), _N_A).i_dsat is not None
    with pytest.raises((KeyError, ValueError)):
        device_step(_die(), DeviceKnobs(strain="unobtanium"), _N_A)


# --------------------------------------------------------------------------- #
# 4. The record carries the bound beside the number
# --------------------------------------------------------------------------- #
def test_the_record_reports_the_headline_and_the_bound_together():
    """``mu_factor`` (the headline) sits beside the **cited** drive factor and the overstatement.

    S1 stores both drive currencies on the mechanism precisely so the model's inference and the real
    devices' measurement cannot be read apart; this is that discipline reaching the game record. Note what
    ``drive_overstatement`` is **not**: it is the mechanism's cited ratio, not a correction applied to this
    die. ``i_dsat`` above already moved by the *full* mobility factor — the key says by how much that read
    overstates what silicon did.
    """
    mech = st.MECHANISMS[_WIRED]
    rec = device_step(_die(), DeviceKnobs(strain=_WIRED), _N_A).history[-1]
    assert rec.knobs_in["strain"] == _WIRED
    assert rec.knobs_in["mu_eff"] == pytest.approx(dev.MU_N_EFF * mech.mobility_factor, rel=1e-12)
    assert rec.outputs["mu_factor"] == mech.mobility_factor
    assert rec.outputs["drive_factor_cited"] == mech.drive_factor
    assert rec.outputs["drive_overstatement"] == pytest.approx(2.0, rel=1e-12)
    # The bound is a fact about the mechanism, so it must not depend on the die: a degenerated device
    # realizes *less* of the win, and the reported overstatement is unchanged.
    degenerated = device_step(_die(R_s=120.0), DeviceKnobs(strain=_WIRED), _N_A,
                              sd_contact_squares=4.0).history[-1]
    assert degenerated.outputs["drive_overstatement"] == rec.outputs["drive_overstatement"]


# --------------------------------------------------------------------------- #
# 5. The structural break — the knob alone re-grades the wafer
# --------------------------------------------------------------------------- #
def test_the_knob_alone_regrades_the_wafer_with_no_new_scoring_surface():
    """Strain moves ``I_Dsat``, which G6 already grades — so **no** second ingredient is needed.

    Every knob before this one was additive: ``bv_V``, ``t_rr``, ``j_gate``, ``τ_total`` each emit a new
    output beside an unchanged device, and F4's inversion needed the *pair* (the wire knob plus delay
    binning) before a single grade moved. F5 needs neither a new spec window nor a new bin currency — the
    same ladder, the same silicon everywhere else, and the histogram walks up it. At the G6 ladder the
    walk is **complete**: every graded part sorts premium.
    """
    specs = replace(DEFAULT_SPECS, speed_bins=_SPEED_BINS)
    unstrained = run_line(_strained(None), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA),
                          specs=specs, grid_n=_GRID)
    strained = run_line(_strained(_WIRED), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA),
                        specs=specs, grid_n=_GRID)

    before, after = _histogram(unstrained), _histogram(strained)
    assert set(before) == {"premium", "typical", "value", "reject"}      # a real spread across the ladder
    assert set(after) == {"premium"}                                     # ...and it lands entirely on top
    # The physical process is untouched: the same dies, the same CD histogram, the same thresholds. Only
    # the mobility the drive read uses changed.
    assert [d.cd_nm for d in strained.dies] == [d.cd_nm for d in unstrained.dies]
    assert [d.V_t for d in strained.dies] == [d.V_t for d in unstrained.dies]


def test_strain_is_a_common_mode_multiplier_so_it_moves_the_level_and_not_the_sorting():
    """Every die by the **same factor** — the relative spread is unchanged, and nobody is re-ranked.

    This is the sharp form of the test above, and the mirror of F4's finding. ``τ_wire`` was common-mode
    and **additive**: it added a level and no spread, which *compressed* the relative spread and collapsed
    the premium grade. Strain is common-mode and **multiplicative**: it scales every die by the mechanism's
    factor, so the coefficient of variation is unchanged to floating-point rounding and the rank order is
    exactly preserved. Nothing about *which* die is fastest moves — what re-grades the wafer is purely the
    level shifting under a fixed market ladder.

    Which is why "strain promoted every part" is a statement about the **ladder**, not about the process
    learning to sort better — a claim :func:`test_recentring_the_line_on_the_strained_part_restores_the_wafer_exactly`
    turns into the control it deserves rather than leaving in prose.
    """
    unstrained = run_line(_strained(None), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA), grid_n=_GRID)
    strained = run_line(_strained(_WIRED), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA), grid_n=_GRID)
    factor = st.MECHANISMS[_WIRED].mobility_factor

    pairs = [(s.i_dsat, u.i_dsat) for s, u in zip(strained.dies, unstrained.dies)
             if s.i_dsat is not None and u.i_dsat is not None]
    assert len(pairs) > _GRID * _GRID // 2                               # a real sample, not two stragglers
    for s_i, u_i in pairs:
        assert s_i / u_i == pytest.approx(factor, rel=1e-12)             # one factor, not a per-die effect

    def _cv(values: list[float]) -> float:
        mean = sum(values) / len(values)
        return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5 / mean

    assert _cv([s for s, _ in pairs]) == pytest.approx(_cv([u for _, u in pairs]), rel=1e-9)
    assert ([i for i, _ in sorted(enumerate(s for s, _ in pairs), key=lambda p: p[1])]
            == [i for i, _ in sorted(enumerate(u for _, u in pairs), key=lambda p: p[1])])


def test_the_wire_keeps_its_share_of_the_strain_win():
    """F5's win arrives on a chip whose clock F4 showed the **wire** partly sets — one sentence, not a panel.

    Asserted as the structural identities rather than as F4's ``∂ln f/∂ln I = 1 − wire_share`` (an exact
    *derivative*, so a finite +20% step would need a tolerance and prove less): ``τ_wire`` reads no device
    quantity, so it is byte-identical; ``τ_gate = C_load·V_dd/I_Dsat`` and ``C_load`` has no mobility in
    it, so the gate term scales by exactly the inverse drive ratio; and therefore the switching-speed gain
    is **strictly smaller** than the drive gain. The era that made transistors faster arrived after wires
    had started setting the clock.
    """
    off = device_step(_die(), DeviceKnobs(interconnect="Cu"), _N_A)
    on = device_step(_die(), DeviceKnobs(interconnect="Cu", strain=_WIRED), _N_A)
    off_out, on_out = off.history[-1].outputs, on.history[-1].outputs

    assert on_out["tau_wire_ps"] == off_out["tau_wire_ps"]            # common-mode: no device in it
    drive_ratio = on.i_dsat / off.i_dsat
    assert on_out["tau_gate_ps"] / off_out["tau_gate_ps"] == pytest.approx(1.0 / drive_ratio, rel=1e-12)
    speed_ratio = off.delay / on.delay                                # f ∝ 1/τ_total
    assert 1.0 < speed_ratio < drive_ratio


def test_recentring_the_line_on_the_strained_part_restores_the_wafer_exactly():
    """The control: scale the windows *and* the ladder by the same factor and **nothing has happened**.

    Both of the game-level effects this slice produces — every part promoting, and the upper tail clipping
    the ``I_Dsat`` ceiling — are consequences of a **level shift under fixed edges**, and this is the test
    that proves there is nothing else in them. Re-centre the line on the strained nominal (multiply the
    spec window and every bin edge by the mechanism's factor, which is what a fab does when it qualifies a
    new process) and the wafer comes back **grade for grade and verdict for verdict identical** to the
    unstrained run.

    It is the ``τ_wire = 0`` control of F4's slice 2, in F5's currency: proof that the construction puts no
    thumb on the scale, so the finding is the shift itself and never a threshold choice. And it names the
    fix without applying it — re-centring is a **market/spec** decision, not a physics one, and this
    project does not make it silently on the slice's own behalf.
    """
    factor = st.MECHANISMS[_WIRED].mobility_factor
    base = replace(DEFAULT_SPECS, speed_bins=_SPEED_BINS)
    recentred = replace(
        base,
        i_dsat_mA=replace(base.i_dsat_mA, lo=base.i_dsat_mA.lo * factor, hi=base.i_dsat_mA.hi * factor),
        speed_bins=SpeedBins(bins=tuple(
            SpeedBin(b.label,
                     lo_mA=None if b.lo_mA is None else b.lo_mA * factor,
                     hi_mA=None if b.hi_mA is None else b.hi_mA * factor)
            for b in _SPEED_BINS.bins)),
    )
    unstrained = run_line(_strained(None), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA),
                          specs=base, grid_n=_GRID)
    strained = run_line(_strained(_WIRED), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA),
                        specs=recentred, grid_n=_GRID)

    assert _histogram(strained) == _histogram(unstrained)
    assert [d.bin for d in strained.dies] == [d.bin for d in unstrained.dies]
    assert ([d.verdict.passed for d in strained.dies if d.verdict is not None]
            == [d.verdict.passed for d in unstrained.dies if d.verdict is not None])


def test_the_win_costs_yield_against_a_spec_ceiling_written_for_the_unstrained_line():
    """The uncomfortable half, pinned rather than tuned away: a 100%-yielding wafer loses 12 of 89 parts.

    ``DEFAULT_SPECS``'s ``I_Dsat`` window has a **house** upper edge (4.2 mA) whose documented purpose is
    catching *CD-collapse over-current* — a failure mode of an unstrained 1990s line, where the only way
    to be 20% over-current was for the geometry to be wrong. Strain lifts the whole histogram by exactly
    that much while the geometry is bit-for-bit correct, so the upper tail walks straight into a window
    that was never asked about it: the same wafer goes from **89/89 passing to 77/89**, every loss a
    parametric ``I_Dsat`` **high** fail.

    That is a spec artefact, not a physical consequence of strain — but it is a *real* game consequence,
    and the honest move is to record it and name whose call the fix is. Re-centring the window on the
    strained line is a **market/spec** decision (the same class as F4's binning edges), and re-centring it
    quietly so the slice reads better is exactly the fudge shape this project rejects.
    """
    assert DEFAULT_SPECS.i_dsat_mA.hi is not None
    unstrained = run_line(_strained(None), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA), grid_n=_GRID)
    strained = run_line(_strained(_WIRED), seed=_SEED, variation=Variation(cd_sigma_nm=_SIGMA), grid_n=_GRID)

    def _passed(wafer) -> int:
        return sum(1 for d in wafer.dies if d.verdict is not None and d.verdict.passed)

    assert _passed(unstrained) == len(unstrained.dies)          # the unstrained line clears its own window
    assert _passed(strained) < _passed(unstrained)              # ...and the strained one does not
    # Every loss is the ceiling, and nothing else: no new failure mode was introduced.
    for d in strained.dies:
        if d.verdict is not None and not d.verdict.passed:
            assert all("I_Dsat" in reason and "high" in reason for reason in d.verdict.reasons)
            assert d.i_dsat * 1.0e3 > DEFAULT_SPECS.i_dsat_mA.hi
    # The nominal part is comfortably inside — this is a tail clipping, not a wholesale kill.
    assert run_line(_strained(_WIRED), seed=_SEED, grid_n=1).dies[0].i_dsat * 1.0e3 \
        < DEFAULT_SPECS.i_dsat_mA.hi
