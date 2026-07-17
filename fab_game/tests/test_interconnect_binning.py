"""F4 slice 2 — the BEOL wire wired into the device step, and the binning premise it overturns.

:mod:`chip.interconnect`'s own triad asserts the physics in isolation. **These** tests assert the thing
only the consumer can show: that the sim's ``I_Dsat``-is-speed premise — stated verbatim in
:class:`fab_game.spec.SpeedBin`'s docstring ("clock speed ∝ drive current"), and *era-appropriate and
false* — **breaks on the same wafer it was written for**.

The payload, and why it needs the consumer to be provable at all:

  * ``τ_total = τ_gate(I_Dsat) + τ_wire``, and ``τ_wire`` is **common-mode** — the same ps on every die,
    because it reads the metal and the geometry and *nothing about that die's transistor*. So it adds a
    **level**, and contributes **no spread**;
  * therefore the across-wafer ``I_Dsat`` spread maps to a speed spread damped by exactly
    ``1 − wire_share`` — with the **transistor histogram bit-for-bit unchanged**;
  * so the *same silicon*, graded on the *same market promise*, stops sorting into speed grades. The
    premium bin collapses toward typical — and, symmetrically, the bin-out tail is **rescued**. The wire
    costs the premium **grade**, not the die count: a grading loss, never a yield loss.

**Why re-binning is not, by itself, a finding** (the trap these tests are built around): ``τ_total`` is
strictly monotone in ``I_Dsat``, so binning on it with edges mapped through *that same function* gives a
**byte-identical partition**. The collapse must come from the market's promise, not from a threshold
choice — see :meth:`fab_game.spec.DelayBins.from_speed_bins`, and the ``τ_wire = 0`` identity below that
proves the construction adds no thumb on the scale.

The seam ladder: ``interconnect=None`` (nothing emitted, byte-for-byte today) → ``"Cu"`` with
``delay_bins=None`` (the delay is emitted and **read by no one** — still byte-for-byte) → ``"Cu"`` +
delay binning (the inversion). Import + numeric only, so it rides the fast lane.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from chip import interconnect as ic

from fab_game.pipeline import run_line
from fab_game.recipe import DeviceKnobs, PackagingKnobs, Recipe
from fab_game.spec import DEFAULT_SPECS, DelayBins, SpeedBin, SpeedBins
from fab_game.state import Die, Verdict
from fab_game.steps import device_step, packaging_step
from fab_game.variation import Variation

_N_A = 1.0e17
_GRID = 11                       # the G6 die map (~89 dies) — a real I_Dsat sample to grade
_SEED = 0
_TIGHT_SIGMA = 1.5               # nm — the well-controlled process (the G6 contrast)
_LOOSE_SIGMA = 7.0               # nm — the poorly-controlled one

# The G6 market ladder, verbatim in shape: grades around the nominal ~3.29 mA part.
_SPEED_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=3.38),
    SpeedBin("typical", lo_mA=3.21, hi_mA=3.38),
    SpeedBin("value", lo_mA=3.10, hi_mA=3.21),
))


def _die(t_ox_um: float = 0.0141) -> Die:
    return Die(site=(0, 0), radius_frac=0.0, t_ox_um=t_ox_um, cd_nm=167.0, nils=4.0, resolved=True)


def _wired(metal: str | None) -> Recipe:
    return replace(Recipe(), device=DeviceKnobs(interconnect=metal))


def _nominal(metal: str = "Cu") -> Die:
    """The zero-variation centre die — the market ladder's anchor part (nominal ≡ 'typical')."""
    return run_line(_wired(metal), seed=_SEED, grid_n=1).dies[0]


def _histogram(wafer) -> dict:
    hist: dict = {}
    for d in wafer.dies:
        if d.bin is not None:
            hist[d.bin] = hist.get(d.bin, 0) + 1
    return hist


def _graded(sigma: float, delay_bins: DelayBins | None, metal: str = "Cu"):
    """One wafer at CD-control ``sigma``, graded on ``I_Dsat`` (``delay_bins=None``) or on ``τ_total``."""
    specs = replace(DEFAULT_SPECS, speed_bins=_SPEED_BINS, delay_bins=delay_bins)
    return run_line(_wired(metal), seed=_SEED, variation=Variation(cd_sigma_nm=sigma),
                    specs=specs, grid_n=_GRID)


# --------------------------------------------------------------------------- #
# 1. The seam ladder — absent, then engaged-but-unread
# --------------------------------------------------------------------------- #
def test_interconnect_absent_emits_nothing_at_all():
    """No wire knob → **no delay is emitted** and no record key appears (the seam, gap-not-fake-zero)."""
    out = device_step(_die(), DeviceKnobs(interconnect=None), _N_A)
    assert out.delay is None
    assert out.delay_ps is None
    rec = out.history[-1]
    assert "interconnect" not in rec.knobs_in            # fingerprint discipline: a bare record
    for key in ("tau_total_ps", "tau_wire_ps", "tau_gate_ps", "wire_share", "drive_sensitivity"):
        assert key not in rec.outputs


def test_engaging_the_wire_alone_changes_nothing_scored_the_delay_is_read_by_no_one():
    """``interconnect="Cu"`` with no ``delay_bins`` → the delay is emitted and **nothing observable moves**.

    The additive discipline (``bv_V``/``t_rr``'s, and F3's ``j_gate``'s): a new output must not perturb a
    scored one. It is the **pair** — the knob *plus* delay binning — that inverts the premise, so this is
    the line between "the sim can read a wire" and "the wire re-grades the wafer".
    """
    off = run_line(_wired(None), seed=_SEED, variation=Variation(cd_sigma_nm=_LOOSE_SIGMA), grid_n=_GRID)
    on = run_line(_wired("Cu"), seed=_SEED, variation=Variation(cd_sigma_nm=_LOOSE_SIGMA), grid_n=_GRID)
    for a, b in zip(off.dies, on.dies):
        assert a.V_t == b.V_t                            # byte-for-byte, not approx
        assert a.i_dsat == b.i_dsat
        assert a.bin == b.bin
        assert a.verdict == b.verdict
        assert a.delay is None and b.delay is not None    # ...and the only difference is the new channel
    assert off.dies[0].history[-1].outputs == on.dies[0].history[-1].outputs   # the packaging record too


def test_i_dsat_keeps_its_meaning_the_delay_is_never_written_back():
    """``τ_gate`` is computed *at the delay read* and never fed back (the F2 ``R_s`` / F3 ``t_ox`` rule)."""
    off = device_step(_die(), DeviceKnobs(interconnect=None), _N_A)
    on = device_step(_die(), DeviceKnobs(interconnect="Cu"), _N_A)
    assert on.i_dsat == off.i_dsat
    assert on.V_t == off.V_t
    assert on.history[-1].outputs["C_ox"] == off.history[-1].outputs["C_ox"]


# --------------------------------------------------------------------------- #
# 2. The two terms, end to end — the wire is blind to the transistor
# --------------------------------------------------------------------------- #
def test_tau_wire_is_common_mode_identical_on_every_die_despite_a_spread_in_i_dsat():
    """The claim the whole payload rests on: ``∂τ_wire/∂I_Dsat = 0``, **through the real pipeline**.

    A loose process spreads ``I_Dsat`` across the wafer. Every die's ``τ_gate`` moves; every die's
    ``τ_wire`` is **the same number** — it depends on the metal and the geometry, never on that die's
    transistor. That is what makes it a *floor* and not a *spread*, and it is why grading on it damps.
    """
    w = _graded(_LOOSE_SIGMA, None)
    recs = [next(r for r in d.history if r.step == "device") for d in w.dies]
    wires = {r.outputs["tau_wire_ps"] for r in recs}
    gates = {r.outputs["tau_gate_ps"] for r in recs}
    assert len(wires) == 1                               # ONE value — bit-for-bit, across ~89 dies
    assert len(gates) > 1                                # ...while the transistor term genuinely spreads
    # And the total moved by exactly the gate term's movement — the wire added a level, no spread.
    spread_gate = max(r.outputs["tau_gate_ps"] for r in recs) - min(r.outputs["tau_gate_ps"] for r in recs)
    spread_tot = max(r.outputs["tau_total_ps"] for r in recs) - min(r.outputs["tau_total_ps"] for r in recs)
    assert spread_tot == pytest.approx(spread_gate, rel=1e-12)


def test_tau_gate_is_a_real_cv_over_i_read_of_the_device_not_a_house_lump():
    """``τ_gate = C_load·V_dd/I_Dsat`` with ``C_load`` the **real** ``C_ox·W·L`` off this die's own chain.

    The "consume the real number" move (F2's ``die.R_s``, F3's ``die.t_ox_um``): the gate term is a
    genuine CV/I read of the device just computed, so a *better transistor* really does move it — which
    is what makes the wire term's refusal to move meaningful rather than trivial.
    """
    out = device_step(_die(), DeviceKnobs(interconnect="Cu"), _N_A)
    rec = out.history[-1]
    c_load = ic.gate_load_capacitance(rec.outputs["C_ox"], 10.0, 0.167)
    expected = ic.gate_delay(c_load, out.i_dsat) * 1.0e12
    assert rec.outputs["tau_gate_ps"] == pytest.approx(expected, rel=1e-12)
    # A thinner oxide → more C_ox AND more drive; the point is only that the read is the device's own.
    assert rec.outputs["tau_total_ps"] == pytest.approx(
        rec.outputs["tau_gate_ps"] + rec.outputs["tau_wire_ps"], rel=1e-12)


def test_a_worse_metal_damps_harder_at_the_same_geometry():
    """Al's ``τ_wire`` is 1.58× Cu's (the prefactor-free ``ρ`` ratio) ⇒ a lower drive sensitivity.

    The 1997 escape, seen from the consumer: copper does not make the transistor better, it makes the
    transistor **matter more**.
    """
    al = device_step(_die(), DeviceKnobs(interconnect="Al"), _N_A).history[-1].outputs
    cu = device_step(_die(), DeviceKnobs(interconnect="Cu"), _N_A).history[-1].outputs
    assert al["tau_gate_ps"] == cu["tau_gate_ps"]         # the transistor is untouched by the metal choice
    assert al["tau_wire_ps"] / cu["tau_wire_ps"] == pytest.approx(
        ic.wire_delay_ratio("Al", "Cu"), rel=1e-12)
    assert al["drive_sensitivity"] < cu["drive_sensitivity"]
    assert al["wire_share"] > cu["wire_share"]


# --------------------------------------------------------------------------- #
# 3. The mapping — and the identity that proves it puts no thumb on the scale
# --------------------------------------------------------------------------- #
def test_from_speed_bins_flips_the_bounds_the_fast_edge_moves_from_lo_mA_to_hi_ps():
    """The ordering trap, pinned: higher mA = faster = **lower** ps, so ``lo_mA`` → ``hi_ps``.

    A silent flip here would not show in a histogram — it would mis-grade every part and still look like
    a partition. Premium is open on the *fast* side in both currencies.
    """
    dbins = DelayBins.from_speed_bins(_SPEED_BINS, i_dsat_nom_mA=3.3, tau_nom_ps=10.0)
    premium, typical, value = dbins.bins
    assert premium.label == "premium"
    assert premium.lo_ps is None                         # open on the fast side (was `hi_mA is None`)
    assert premium.hi_ps == pytest.approx(10.0 * 3.3 / 3.38)
    assert typical.lo_ps == premium.hi_ps                # the ladder tiles with no gap and no overlap
    assert typical.hi_ps == pytest.approx(10.0 * 3.3 / 3.21)
    assert value.lo_ps == typical.hi_ps
    assert value.hi_ps == pytest.approx(10.0 * 3.3 / 3.10)
    assert dbins.labels == _SPEED_BINS.labels            # the same grades, and the same reject tail


def test_with_no_wire_delay_binning_reproduces_i_dsat_binning_grade_for_grade():
    """**The identity that licenses the whole slice.** ``τ_wire = 0`` ⇒ the two policies are the *same*.

    With no wire, ``τ_total = τ_gate = A/I`` — a pure inverse — so grading on delay against edges mapped
    through the old premise's own arithmetic must return **each part's original grade**. If it did not,
    :meth:`DelayBins.from_speed_bins` would be smuggling in a threshold change, and every collapse below
    would be an artifact of *that* rather than of the wire. This is the control.

    Probes bracket every edge from **both sides** (±1 ppb — far above float noise, far below any physical
    resolution), which is what catches the real trap: the bound **swap**. Map ``lo_mA`` to ``lo_ps``
    instead of ``hi_ps`` and every probe here mis-grades loudly.

    A part landing *exactly* on an edge is deliberately **not** probed: ``(A/i_nom)·(i_nom/i_edge)`` and
    ``A/i_edge`` are equal algebraically but ~1 ulp apart in float, so an exact tie resolves arbitrarily
    under **any** bound convention. It is unobservable (no simulated die sits on an edge) and asserting
    it would be testing float, not the model. The ``(lo_ps, hi_ps]`` mirror of ``[lo_mA, hi_mA)`` is kept
    because it is the principled reading — "premium = *at least* 2.6% faster" is ``≤`` — not because a
    test can distinguish it.
    """
    A = 40.0                                             # τ_gate·I (ps·mA) — any positive constant works
    i_nom = 3.3
    dbins = DelayBins.from_speed_bins(_SPEED_BINS, i_nom, tau_nom_ps=A / i_nom)
    eps = 1.0e-9
    probes = [3.6, 3.5, 3.30, 3.25, 3.15, 2.9, 2.5]      # ordinary parts, every grade
    for edge in (3.38, 3.21, 3.10):                      # ...and both sides of every edge
        probes += [edge * (1.0 + eps), edge * (1.0 - eps)]
    for i_mA in probes:
        by_drive = _SPEED_BINS.assign(i_mA)
        by_delay = dbins.assign(A / i_mA)                # the same part, the delay it truly switches at
        assert by_delay == by_drive, f"{i_mA} mA: {by_delay!r} != {by_drive!r}"


def test_delay_binning_with_no_delay_read_is_a_misconfiguration_not_a_slow_part():
    """``delay_bins`` set but the ``interconnect`` knob off ⇒ every part bins to reject, and says why.

    Mirrors :meth:`SpeedBins.assign`'s rule for a missing ``I_Dsat``: a part cannot be graded on a
    currency it does not carry. The reason names the knob rather than blaming the silicon.
    """
    dbins = DelayBins.from_speed_bins(_SPEED_BINS, 3.3, 10.0)
    assert dbins.assign(None) == "reject"
    # A front-end-good die that was never wired — it reaches final test with no delay to grade.
    unwired = replace(device_step(_die(), DeviceKnobs(interconnect=None), _N_A),
                      verdict=Verdict(True, ()))
    out = packaging_step(unwired, PackagingKnobs(), True, _SPEED_BINS, dbins)
    assert out.bin == "reject"
    assert out.verdict.failed
    assert "interconnect" in out.verdict.reasons[0]      # names the knob, not the part
    assert "tau_total_ps" not in out.history[-1].outputs  # nothing to fingerprint


# --------------------------------------------------------------------------- #
# 4. The payload — the same wafer, the same transistors, the grades gone
# --------------------------------------------------------------------------- #
def test_the_premium_bin_collapses_while_the_i_dsat_histogram_is_bit_for_bit_unchanged():
    """**The discriminator, end to end.** Same silicon, same drive currents, the speed grades evaporate.

    This is what a scalar "wires are slow" cannot produce: the transistor histogram is *identical*
    (asserted bit-for-bit, not approximately) and the grading still changes — because the two terms
    respond to different inputs and only one of them carries spread.
    """
    dbins = DelayBins.from_speed_bins(_SPEED_BINS, _nominal().i_dsat_mA, _nominal().delay_ps)
    by_drive = _graded(_TIGHT_SIGMA, None)
    by_delay = _graded(_TIGHT_SIGMA, dbins)

    # The transistors are the same transistors — bit-for-bit, die by die.
    assert [d.i_dsat for d in by_drive.dies] == [d.i_dsat for d in by_delay.dies]
    assert [d.V_t for d in by_drive.dies] == [d.V_t for d in by_delay.dies]

    hi, hd = _histogram(by_drive), _histogram(by_delay)
    assert hi.get("premium", 0) > 20                     # a tight process earns a real premium share...
    assert hd.get("premium", 0) == 0                     # ...and grading in the true currency, none of it
    assert sum(hi.values()) == sum(hd.values())          # still a partition — nobody was lost


def test_the_compression_is_symmetric_the_slow_tail_is_rescued_as_the_fast_tail_is_lost():
    """The wire costs the **grade**, not the die count — it pulls *both* tails toward typical.

    The framing that keeps this honest: ``τ_wire`` is a level, so a part that was too slow to sell is
    now *also* only common-mode-slower than typical — it comes **back into grade**. Reading the collapse
    as "wires cost yield" would be exactly backwards: the bin-out tail **shrinks**.
    """
    dbins = DelayBins.from_speed_bins(_SPEED_BINS, _nominal().i_dsat_mA, _nominal().delay_ps)
    hi = _histogram(_graded(_LOOSE_SIGMA, None))
    hd = _histogram(_graded(_LOOSE_SIGMA, dbins))

    assert hd["premium"] < hi["premium"]                 # the fast tail is pulled in...
    assert hd.get("reject", 0) < hi.get("reject", 0)     # ...and the slow tail is pushed back into grade
    assert hi.get("reject", 0) > 0                       # (the I_Dsat policy really did bin parts out)
    assert hd.get("reject", 0) == 0
    assert hd["typical"] > hi["typical"]                 # both tails end up in the middle
    assert sum(hi.values()) == sum(hd.values())          # a grading loss, NEVER a yield loss


def test_tightening_cd_control_stops_buying_speed_grades():
    """The G6 lesson, inverted — the reason this consumer is the right one.

    G6's whole point is that tightening the process buys premium parts. Past the crossover it stops
    doing so: the *same* σ improvement that nearly triples the premium share under ``I_Dsat`` grading
    buys **nothing** under delay grading, because the transistor spread it tightened is damped by
    ``1 − wire_share`` before it reaches a grade.
    """
    dbins = DelayBins.from_speed_bins(_SPEED_BINS, _nominal().i_dsat_mA, _nominal().delay_ps)
    loose_drive = _histogram(_graded(_LOOSE_SIGMA, None)).get("premium", 0)
    tight_drive = _histogram(_graded(_TIGHT_SIGMA, None)).get("premium", 0)
    loose_delay = _histogram(_graded(_LOOSE_SIGMA, dbins)).get("premium", 0)
    tight_delay = _histogram(_graded(_TIGHT_SIGMA, dbins)).get("premium", 0)

    # Under the drive proxy the premium share is a real, sizeable prize either way.
    assert loose_drive > 0 and tight_drive > 0
    # Under the true currency the tight process — the *better* process — earns no premium at all.
    assert tight_delay == 0
    assert tight_delay < tight_drive
    assert loose_delay < loose_drive


def test_the_wafer_is_deep_past_the_crossover_at_the_house_geometry_so_the_wire_sets_the_speed():
    """The operating point the payload above sits at, stated rather than implied (all FLAGGED).

    ``wire_share ≈ 0.71`` at the house 250 nm-era line: the wire already owns ~70% of the delay, so a
    drive improvement is worth only ``1 − 0.71 ≈ 0.29`` of itself. The *magnitude* rides the flagged
    ``L`` (τ_wire ∝ L²) and is **not** a claim; the damping **law** is exact for any share, and the
    grading consequence follows from the law, not from this number.
    """
    rec = next(r for r in _nominal().history if r.step == "device")
    assert 0.6 < rec.outputs["wire_share"] < 0.8
    assert rec.outputs["drive_sensitivity"] == pytest.approx(1.0 - rec.outputs["wire_share"], rel=1e-12)
    assert rec.outputs["tau_wire_ps"] > rec.outputs["tau_gate_ps"]     # wire-limited: the transistor lost
