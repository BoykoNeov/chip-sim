"""F4 BEOL interconnect RC (``chip.interconnect``) — the delay the transistor does not set.

The triad, per ``docs/plans/beol-interconnect-f4.md`` + ``historical-modes.md``:

  * **tight — the discriminator (structural, not asserted):** ``∂τ_wire/∂I_Dsat = 0`` **exactly** while
    ``τ_gate ∝ 1/I_Dsat``, so the wire share rises monotonically as the transistor improves — for *any*
    geometry, metal, or house constant. This is the leg that survives every flagged magnitude, and it is
    the one the slice-2 binning consumer will ride;
  * **tight — the cited ``c_pul`` invariance:** :func:`chip.interconnect.wire_capacitance` **cannot** read
    ``W``/``H`` (they are not in its signature), while ``R ∝ 1/(W·H)`` does — hence the crossover is an
    **R** story, and it exists;
  * **tight — the prefactor-free ratios:** every house constant (``L``, ``c_pul``, ``V_dd``, ``C_load``,
    the aspect ratio, the Elmore factor) **cancels exactly** in
    :func:`chip.interconnect.wire_delay_ratio` and :func:`chip.interconnect.crossover_width_ratio` — the
    F3 ``leakage_decades_saved`` discipline, and the module's only licensed headline;
  * **cross-check (non-circular):** the cited bulk resistivities — handbook values, **never fitted to a
    delay curve** — reproduce IBM's independently reported **~40%** resistance reduction for the 1997
    Al→Cu swap;
  * **honesty guards (claims about where the model may speak, not physics):** Ru is absent from the
    registry until slice 4 carries the size-effect physics, and the bulk model's ``W ≫ λ`` validity bound
    is explicit;
  * **flagged:** ``GLOBAL_WIRE_LENGTH_UM``, ``ELMORE_FACTOR``, ``V_DD_HOUSE``, the Al ``ρ₀`` — asserted by
    shape/sign/ratio, **never as absolute picoseconds**.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import math

import pytest

from chip import device, interconnect as ic


# --------------------------------------------------------------------------- #
# The discriminator — ∂τ_wire/∂I_Dsat = 0, structurally (the tight leg)
# --------------------------------------------------------------------------- #
def test_wire_delay_is_blind_to_the_transistor_bit_for_bit():
    """The payload: I_Dsat moves τ_gate and leaves τ_wire BYTE-for-byte identical.

    Not "approximately independent" — the drive current does not enter the wire term at all, so a 100×
    swing in I_Dsat must reproduce the same float. This is what no scalar "wires are slow" can fake.
    """
    geom = ic.WireGeometry()
    taus = [ic.delay(geom, i_dsat_A=i, c_load_farad=2.3e-14) for i in (1e-4, 1e-3, 3.3e-3, 1e-2)]
    for d in taus[1:]:
        assert d.tau_wire_s == taus[0].tau_wire_s          # byte-identical, not approx
        assert d.R_wire_ohm == taus[0].R_wire_ohm
        assert d.C_wire_F == taus[0].C_wire_F
    # ...while the gate term really did move (else the test would pass vacuously).
    assert taus[0].tau_gate_s > taus[-1].tau_gate_s * 50


def test_gate_delay_is_inverse_in_i_dsat_exactly():
    """τ_gate = C·V/I — doubling the drive current exactly halves the gate delay (the CV/I metric)."""
    t1 = ic.gate_delay(2.3e-14, i_dsat_A=1.0e-3)
    t2 = ic.gate_delay(2.3e-14, i_dsat_A=2.0e-3)
    assert t1 == pytest.approx(2.0 * t2, rel=1e-12)


def test_wire_share_rises_monotonically_as_the_transistor_improves():
    """The graded readout: a better transistor makes the WIRE the bottleneck — for any geometry/metal.

    The gradual-failure discipline (no cliff): the share is continuous in I_Dsat, and its monotonicity is
    the ρ/geometry-independent leg — τ_gate falls while τ_wire does not move at all.
    """
    for metal in ("Al", "Cu"):
        for width in (0.15, 0.25, 0.6):
            geom = ic.WireGeometry(width_um=width, thickness_um=2.0 * width)
            shares = [ic.delay(geom, i_dsat_A=i, c_load_farad=2.3e-14, metal=metal).wire_share
                      for i in (5e-4, 1e-3, 3e-3, 1e-2, 3e-2)]
            assert shares == sorted(shares)
            assert all(0.0 < s < 1.0 for s in shares)


def test_the_transistor_stops_setting_speed_past_the_crossover():
    """The headline made assertable: past the crossover, halving gate delay LESS than halves chip delay.

    Below the crossover (a wide wire) the transistor is still in charge, so the same doubling of I_Dsat
    buys much more. That contrast — not the absolute delay — is the F4 payload.
    """
    load, i_lo, i_hi = 2.3e-14, 3.0e-3, 6.0e-3       # a 2× better transistor

    narrow = ic.WireGeometry(width_um=0.08, thickness_um=0.16)      # wire-limited
    wide = ic.WireGeometry(width_um=3.0, thickness_um=6.0)          # gate-limited
    assert ic.delay(narrow, i_lo, load).wire_limited
    assert not ic.delay(wide, i_lo, load).wire_limited

    def speedup(geom):
        return ic.delay(geom, i_lo, load).tau_total_s / ic.delay(geom, i_hi, load).tau_total_s

    # A 2× transistor buys ~2× when the gate is in charge (1.96×), and ~nothing when the wire is: at an
    # ~80% wire share it returns **1.11×** — double the transistor, gain 11%. That gap IS the F4 payload.
    assert speedup(wide) > 1.8
    assert speedup(narrow) < 1.15
    assert speedup(narrow) < 0.6 * speedup(wide)


# --------------------------------------------------------------------------- #
# The cited c_pul invariance — C does not scale, R does (why the crossover is an R story)
# --------------------------------------------------------------------------- #
def test_capacitance_ignores_the_cross_section_but_resistance_does_not():
    """The cited invariance, structural: C cannot read W/H (not in its signature); R ∝ 1/(W·H)."""
    C_ref = ic.wire_capacitance(1000.0)
    assert ic.wire_capacitance(1000.0) == C_ref                    # no W/H to pass — the point

    R_wide = ic.wire_resistance(1.68, 1000.0, 1.0, 2.0)
    R_narrow = ic.wire_resistance(1.68, 1000.0, 0.5, 1.0)          # both dims halved ⇒ area ÷4
    assert R_narrow == pytest.approx(4.0 * R_wide, rel=1e-12)


def test_capacitance_is_linear_in_length_and_matches_the_cited_2pf_per_cm():
    """C = c_pul·L: 1 cm of wire at the cited 2 pF/cm is 2 pF, and C is exactly linear in L."""
    assert ic.wire_capacitance(1.0e4) == pytest.approx(2.0e-12, rel=1e-12)   # 1 cm → 2 pF
    assert ic.wire_capacitance(500.0) == pytest.approx(0.5 * ic.wire_capacitance(1000.0), rel=1e-12)
    assert ic.wire_capacitance(0.0) == 0.0


def test_wire_delay_grows_as_the_cross_section_shrinks_at_fixed_length():
    """The scaling scenario that produces the crossover: a GLOBAL wire's τ_wire explodes as W·H falls.

    Halving both cross-section dims quadruples R and leaves C alone ⇒ τ_wire ×4. This is the cited
    "global wires stopped scaling" statement, and the reason the crossover is a global-wire claim.
    """
    load, i = 2.3e-14, 3.3e-3
    d_wide = ic.delay(ic.WireGeometry(width_um=0.5, thickness_um=1.0), i, load)
    d_narrow = ic.delay(ic.WireGeometry(width_um=0.25, thickness_um=0.5), i, load)
    assert d_narrow.tau_wire_s == pytest.approx(4.0 * d_wide.tau_wire_s, rel=1e-12)
    assert d_narrow.C_wire_F == d_wide.C_wire_F                     # C sat still — byte-for-byte


def test_a_local_wire_that_scales_with_the_pitch_has_a_flat_wire_delay():
    """The cited counter-scenario: scale L WITH the cross-section and τ_wire is CONSTANT — no crossover.

    "If the interconnect length and interconnect pitch scale identically, the wire delay will remain
    constant with technology scaling." R ∝ L/(W·H) rises ∝ 1/s while C ∝ L falls ∝ s, so RC is invariant.
    This is the honesty guard on the crossover: it is a *global*-wire statement, and stating the scenario
    is what keeps it from being an artifact.
    """
    base = ic.WireGeometry(length_um=1000.0, width_um=0.5, thickness_um=1.0)
    taus = []
    for s in (1.0, 0.5, 0.25, 0.1):                                 # shrink EVERYTHING together
        geom = ic.WireGeometry(length_um=1000.0 * s, width_um=0.5 * s, thickness_um=1.0 * s)
        taus.append(ic.delay(geom, 3.3e-3, 2.3e-14).tau_wire_s)
    for t in taus[1:]:
        assert t == pytest.approx(taus[0], rel=1e-12)


# --------------------------------------------------------------------------- #
# The prefactor-free ratios — the module's only licensed headline
# --------------------------------------------------------------------------- #
def test_wire_delay_ratio_cancels_every_house_constant():
    """τ_wire(Al)/τ_wire(Cu) = ρ_Al/ρ_Cu for ANY L, c_pul, cross-section, or Elmore factor.

    The F3 decades-saved discipline: the era win is stated as a ratio precisely because L is a lump.
    """
    expected = ic.METALS["Al"].rho0_uohm_cm / ic.METALS["Cu"].rho0_uohm_cm
    assert ic.wire_delay_ratio("Al", "Cu") == pytest.approx(expected, rel=1e-12)

    for length in (10.0, 1000.0, 5.0e4):
        for width, thick in ((0.05, 0.1), (0.25, 0.5), (2.0, 1.0)):
            for c_pul in (1.5, 2.0, 3.0):
                for elmore in (0.38, 0.69, 1.0):
                    geom = ic.WireGeometry(length_um=length, width_um=width, thickness_um=thick)
                    kw = dict(c_load_farad=2.3e-14, c_pul_pf_cm=c_pul, elmore=elmore)
                    al = ic.delay(geom, 3.3e-3, metal="Al", **kw).tau_wire_s
                    cu = ic.delay(geom, 3.3e-3, metal="Cu", **kw).tau_wire_s
                    assert al / cu == pytest.approx(expected, rel=1e-12)


def test_crossover_width_ratio_is_the_sqrt_and_is_prefactor_free():
    """W_x(Al)/W_x(Cu) = √(ρ_Al/ρ_Cu), free of L, c_pul, V_dd, C_load, AR and the Elmore factor."""
    expected = math.sqrt(ic.wire_delay_ratio("Al", "Cu"))
    assert ic.crossover_width_ratio("Al", "Cu") == pytest.approx(expected, rel=1e-12)

    for length in (200.0, 1000.0, 1.0e4):
        for ar in (1.0, 2.0, 3.5):
            for v_dd in (1.8, 3.3, 5.0):
                for load in (5e-15, 2.3e-14, 1e-13):
                    kw = dict(length_um=length, aspect_ratio=ar, v_dd=v_dd)
                    al = ic.crossover_width_um(3.3e-3, load, metal="Al", **kw)
                    cu = ic.crossover_width_um(3.3e-3, load, metal="Cu", **kw)
                    assert al / cu == pytest.approx(expected, rel=1e-12)


def test_copper_buys_roughly_one_node_of_scaling():
    """The honest size of the 1997 escape: Cu pushes the crossover ~21% down in linewidth (~one node).

    Banded, not pinned — the Al ρ₀ is flagged, so this asserts the *scale* of the win (a node, not a
    decade and not nothing), which is the claim the demo may make.
    """
    r = ic.crossover_width_ratio("Al", "Cu")
    assert 1.2 < r < 1.35                                # Cu's crossover is ~1/1.26 of Al's
    assert 0.7 < 1.0 / r < 0.85


def test_cited_resistivities_reproduce_ibms_reported_40_percent_win():
    """NON-CIRCULAR: handbook ρ₀ values, never fitted to a delay curve, predict IBM's reported ~40%.

    IBM reported the 1997 Al→Cu swap as "~40% less resistance" (→ ~15% chip speed; PowerPC 300→400 MHz).
    The registry's cited ρ₀ pair gives ~37% for PURE Al — and real Al interconnect was an Al–Cu alloy at
    ρ ≈ 3.0–3.2 µΩ·cm, which lands ~44–47%. The reported figure sits inside that band, from constants
    this model never tuned. Same spirit as Irvin-vs-Masetti and F3's (φ_B, m*)-predicts-the-2 Å-slope.
    """
    reduction = 1.0 - 1.0 / ic.wire_delay_ratio("Al", "Cu")
    assert 0.34 < reduction < 0.40                       # pure-Al leg: ~37%, just under the reported ~40%

    alloy = ic.Metal("Al–Cu alloy line", rho0_uohm_cm=3.1, mfp_nm=22.0)   # the real 1997-era metal
    alloy_reduction = 1.0 - 1.0 / ic.wire_delay_ratio(alloy, "Cu")
    assert 0.40 < alloy_reduction < 0.50                 # ~46% — the reported ~40% is bracketed


# --------------------------------------------------------------------------- #
# The crossover — existence, closed form, and the direction of every knob
# --------------------------------------------------------------------------- #
def test_crossover_is_the_width_where_the_two_terms_cross():
    """The closed form is the real root: at W_x the two delays are equal, and the sides are ordered."""
    load, i, ar = 2.3e-14, 3.3e-3, 2.0
    for metal in ("Al", "Cu"):
        w_x = ic.crossover_width_um(i, load, metal=metal, aspect_ratio=ar)
        at = ic.delay(ic.WireGeometry(width_um=w_x, thickness_um=ar * w_x), i, load, metal=metal)
        assert at.tau_wire_s == pytest.approx(at.tau_gate_s, rel=1e-9)      # τ_wire = τ_gate ⇒ the root
        assert at.wire_share == pytest.approx(0.5, rel=1e-9)                # ...i.e. exactly the boundary

        narrower = ic.delay(ic.WireGeometry(width_um=0.5 * w_x, thickness_um=ar * 0.5 * w_x),
                            i, load, metal=metal)
        wider = ic.delay(ic.WireGeometry(width_um=2.0 * w_x, thickness_um=ar * 2.0 * w_x),
                         i, load, metal=metal)
        assert narrower.wire_limited and not wider.wire_limited


def test_crossover_moves_the_right_way_with_every_knob():
    """Signs: a better transistor pushes the crossover UP (wires bite sooner); a better metal pushes it DOWN."""
    load, ar = 2.3e-14, 2.0
    # A faster transistor (higher I_Dsat) ⇒ smaller τ_gate ⇒ the wire wins at a WIDER line.
    fast = ic.crossover_width_um(1.0e-2, load, aspect_ratio=ar)
    slow = ic.crossover_width_um(1.0e-3, load, aspect_ratio=ar)
    assert fast > slow
    # A lower-ρ metal ⇒ the wire is cheaper ⇒ it only wins at a NARROWER line.
    assert ic.crossover_width_um(3.3e-3, load, metal="Cu") < \
           ic.crossover_width_um(3.3e-3, load, metal="Al")
    # A longer wire ⇒ τ_wire ∝ L² ⇒ the crossover moves up (∝ L).
    assert ic.crossover_width_um(3.3e-3, load, length_um=2000.0) == \
           pytest.approx(2.0 * ic.crossover_width_um(3.3e-3, load, length_um=1000.0), rel=1e-9)


def test_the_house_operating_point_lands_the_crossover_in_the_historical_era():
    """The stated OPERATING POINT — a calibration landing, **not** a prediction (the F2 discipline).

    At the representative 1 mm global wire and the real device.py gate load, the crossover falls at
    ~0.21 µm (Al) / ~0.17 µm (Cu) — adjacent to the cited history (gate ≈ wire by the mid-1990s; Cu +
    low-κ introduced at the **250 nm** node). Honest status: ``GLOBAL_WIRE_LENGTH_UM`` is a **flagged
    lump** and ``W_x ∝ L`` exactly (see the test below), so this landing is *not* evidence the model
    predicts the era — a 2 mm wire would double it. It is the **stated operating point**, pinned here so
    that anyone who retunes ``L`` is forced to notice they moved the whole crossover with it, exactly as
    F2 pins the access→contact flip. What IS a claim is the *ratio* between the two metals (above).
    """
    load = ic.gate_load_capacitance(device.oxide_capacitance(0.015), 10.0, 1.0)
    w_al = ic.crossover_width_um(3.3e-3, load, metal="Al")
    w_cu = ic.crossover_width_um(3.3e-3, load, metal="Cu")
    assert 0.15 < w_al < 0.30                      # the sub-micron era, where the wire wall really landed
    assert w_cu < w_al
    assert 0.10 < w_cu < 0.25


def test_crossover_scales_linearly_with_the_flagged_wire_length():
    """The honesty guard on the lump: W_x ∝ L exactly, so the ABSOLUTE crossover is not a claim.

    Pinned deliberately — it is the reason the module headlines ratios. If someone later "calibrates" L to
    hit a node, this test is where they must notice they moved the whole crossover with it.
    """
    ratios = [ic.crossover_width_um(3.3e-3, 2.3e-14, length_um=L) / L for L in (250.0, 1000.0, 4000.0)]
    for r in ratios[1:]:
        assert r == pytest.approx(ratios[0], rel=1e-12)


# --------------------------------------------------------------------------- #
# The registry + the S4 gate (honesty guards, not physics guards)
# --------------------------------------------------------------------------- #
def test_copper_beats_aluminium_in_the_bulk_but_ruthenium_is_not_in_the_registry_yet():
    """The S4 gate, pinned: Ru MUST NOT be plottable before the size-effect physics exists.

    A bulk-only model ranks Ru LAST (its ρ₀ is ~4× copper's), which is the F4 sign error inverted. Ru's
    constants only mean something once slice 4 carries ρ_eff(d) and the barrier fraction. This guard is a
    claim about where the model may speak — the F3 ladder-cap discipline — not a claim about physics.
    """
    assert ic.METALS["Cu"].rho0_uohm_cm < ic.METALS["Al"].rho0_uohm_cm    # the real, cited bulk win
    assert "Ru" not in ic.METALS
    with pytest.raises(KeyError):
        ic.delay(ic.WireGeometry(), 3.3e-3, 2.3e-14, metal="Ru")


def test_the_scaling_fom_ordering_is_not_the_bulk_ordering():
    """ρ₀λ is the narrow-wire FOM, and it does NOT rank metals the way bulk ρ₀ does — the F3 κ↔gap echo.

    Cu wins on bulk ρ₀ but its λ is ~1.8× aluminium's, so the two are far closer on ρ₀λ than on ρ₀ alone.
    Asserted as the *compression* (the structural claim), not as an Al-beats-Cu headline — the Al numbers
    are flagged and that claim needs re-sourcing before it may be stated anywhere user-facing.
    """
    al, cu = ic.METALS["Al"], ic.METALS["Cu"]
    assert al.rho0_lambda == pytest.approx(al.rho0_uohm_cm * al.mfp_nm, rel=1e-12)
    bulk_gap = al.rho0_uohm_cm / cu.rho0_uohm_cm            # ~1.58 — the wide-wire ordering
    fom_gap = al.rho0_lambda / cu.rho0_lambda               # ~0.90 — the narrow-wire ordering
    assert bulk_gap > 1.5
    assert fom_gap < bulk_gap                              # the gap COMPRESSES: the metric changed
    assert 0.8 < fom_gap < 1.1                             # ...to rough parity


def test_bulk_regime_guard_marks_where_this_slice_may_speak():
    """The bulk ρ_eff = ρ₀ model is valid only for W ≫ λ — explicit, since slice 1 has no size effect."""
    cu = ic.METALS["Cu"]
    assert cu.bulk_regime_ok(0.25)              # a 250 nm line ≫ Cu's 39 nm λ — the Al→Cu era. Valid.
    assert not cu.bulk_regime_ok(0.05)          # a 50 nm line — the size effect rules. Slice 4's job.
    assert not cu.bulk_regime_ok(0.003)         # 3 nm — wildly outside; the Ru era.


# --------------------------------------------------------------------------- #
# Loose coupling — the real device.py chain feeds τ_gate, and device.py is untouched
# --------------------------------------------------------------------------- #
def test_gate_load_rides_the_real_device_oxide_capacitance():
    """C_load = C_ox·W·L reads the REAL chip.device C_ox — plain scalars across the boundary (F2/F3)."""
    c_ox = device.oxide_capacitance(0.015)                  # the MIT 15 nm gate ⇒ ~2.3e-7 F/cm²
    c_load = ic.gate_load_capacitance(c_ox, width_um=10.0, channel_length_um=1.0)
    assert c_load == pytest.approx(c_ox * 1.0e-3 * 1.0e-4, rel=1e-12)   # µm→cm on both dims
    assert c_load > 0.0
    # A thinner oxide ⇒ larger C_ox ⇒ larger load ⇒ SLOWER gate. The wire term cannot notice.
    thin_load = ic.gate_load_capacitance(device.oxide_capacitance(0.005), 10.0, 1.0)
    assert thin_load > c_load
    geom = ic.WireGeometry()
    assert ic.delay(geom, 3.3e-3, thin_load).tau_gate_s > ic.delay(geom, 3.3e-3, c_load).tau_gate_s
    assert ic.delay(geom, 3.3e-3, thin_load).tau_wire_s == ic.delay(geom, 3.3e-3, c_load).tau_wire_s


def test_delay_lands_in_a_physically_sane_picosecond_range():
    """A sanity floor, NOT a claim: the house lumps must at least produce a believable-order delay.

    Deliberately a wide band — absolute picoseconds are not a claim this module makes (L is a lump). This
    catches a unit slip (a 1e4 error would blow the band), nothing more.
    """
    geom = ic.WireGeometry()                                # 1 mm global wire, 0.25 × 0.5 µm
    d = ic.delay(geom, i_dsat_A=3.3e-3, c_load_farad=2.3e-14)
    assert 1.0 < d.tau_total_ps < 1000.0
    assert d.tau_total_ps == pytest.approx(d.tau_total_s * 1e12, rel=1e-12)
    assert d.tau_total_s == pytest.approx(d.tau_gate_s + d.tau_wire_s, rel=1e-12)
    assert d.metal == ic.METALS["Cu"].name


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("kwargs", [
    dict(rho_uohm_cm=0.0, length_um=100.0, width_um=0.2, thickness_um=0.4),
    dict(rho_uohm_cm=1.68, length_um=-1.0, width_um=0.2, thickness_um=0.4),
    dict(rho_uohm_cm=1.68, length_um=100.0, width_um=0.0, thickness_um=0.4),
    dict(rho_uohm_cm=1.68, length_um=100.0, width_um=0.2, thickness_um=-0.4),
])
def test_wire_resistance_rejects_unphysical_inputs(kwargs):
    with pytest.raises(ValueError):
        ic.wire_resistance(**kwargs)


def test_delay_terms_reject_unphysical_inputs():
    with pytest.raises(ValueError):
        ic.gate_delay(2.3e-14, i_dsat_A=0.0)                # a dead transistor has no CV/I delay
    with pytest.raises(ValueError):
        ic.gate_delay(2.3e-14, i_dsat_A=3.3e-3, v_dd=0.0)
    with pytest.raises(ValueError):
        ic.wire_capacitance(100.0, c_pul_pf_cm=0.0)
    with pytest.raises(ValueError):
        ic.wire_delay(100.0, 1e-13, elmore=0.0)
    with pytest.raises(ValueError):
        ic.crossover_width_um(3.3e-3, 2.3e-14, aspect_ratio=0.0)
    with pytest.raises(ValueError):
        ic.Metal("bad", rho0_uohm_cm=-1.0, mfp_nm=20.0)
    with pytest.raises(ValueError):
        ic.Metal("bad", rho0_uohm_cm=1.68, mfp_nm=0.0)
    with pytest.raises(ValueError):
        ic.WireGeometry(width_um=0.0)
