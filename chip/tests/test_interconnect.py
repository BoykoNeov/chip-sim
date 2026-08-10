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
  * **consistency check (deliberately NOT billed as non-circular — it is weaker than F3's):** the cited
    bulk resistivities reproduce IBM's independently reported **~40%** resistance reduction for the 1997
    Al→Cu swap. At a fixed geometry ``R_Al/R_Cu`` **is** ``ρ_Al/ρ_Cu`` identically, so this checks the
    *inputs* against the report, not a structural form;
  * **tight — slice 4's two impossibility results, on cited constants only:** the size effect alone can
    **never** flip the Cu→Ru sign (the no-barrier ratio asymptotes to ``ρ₀λ(Ru)/ρ₀λ(Cu)`` = 1.179 > 1 and
    approaches it monotonically from 4.23 above), and the barrier alone on bulk ``ρ`` flips it only below
    **5.2 nm** — a nanometre above the **4.0 nm** width at which copper has no conductor at all. Both are
    asserted as closed forms *and* against the numeric model;
  * **tight — the geometric conductor floor:** ``W = 2·t_b``, for any ``ρ``, ``L``, ``C`` or aspect ratio
    (F3's "``EOT > t_IL`` for any κ", in the wire's currency);
  * **honesty guards (claims about where the model may speak, not physics):** the game knob refuses Ru
    (:data:`chip.interconnect.BULK_ERA_METALS` — a 250 nm bulk answer for Ru is *correct* and reads as a
    false verdict), the narrow-wire reads refuse Al (its flattering ``ρ₀λ`` is unsupportable while its
    disqualifier is a currency this module lacks), and the bulk model's ``W ≫ λ`` validity bound is
    explicit — slice 4 adds a second path beside it rather than retiring it;
  * **flagged:** ``GLOBAL_WIRE_LENGTH_UM``, ``ELMORE_FACTOR``, ``V_DD_HOUSE``, the Al ``ρ₀``,
    ``SIZE_EFFECT_C`` — asserted by shape/sign/ratio/band, **never as absolute picoseconds or as a
    predicted crossing width**.

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


def test_cited_resistivities_are_consistent_with_ibms_reported_40_percent_win():
    """CONSISTENCY check on the constants — deliberately NOT billed as non-circular (it is weaker than F3's).

    IBM reported the 1997 Al→Cu swap as "~40% less resistance" (→ ~15% chip speed; PowerPC 300→400 MHz).
    The registry's cited ρ₀ pair gives ~37% for PURE Al — and real Al interconnect was an Al–Cu alloy at
    ρ ≈ 3.0–3.2 µΩ·cm, which lands ~44–47%, so the reported figure is bracketed by constants this model
    never tuned. **Honest status:** at a fixed geometry ``R_Al/R_Cu`` *is* ``ρ_Al/ρ_Cu`` identically, so
    this validates the *inputs*, not a structural form. F3's (φ_B, m*)-predicts-the-2 Å-slope check ran
    through the **exponential** — cited inputs predicting a different functional form's slope — which is
    a genuinely stronger claim than this one. Do not quote this as F3-grade.
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
def test_copper_beats_aluminium_in_the_bulk_and_ruthenium_loses_there_which_is_why_the_knob_refuses_it():
    """The S4 gate, **migrated not dropped**: Ru is in the registry now, and still not a bulk-era option.

    Slices 1–3 kept Ru out of :data:`chip.interconnect.METALS` entirely, because a bulk-only model ranks
    it LAST and "Ru is the worst wire metal" is the F4 sign error inverted. Slice 4 gives Ru a regime, so
    it joins the registry — but the *bulk* answer did not become less misleading. It is worse than that:
    at 250 nm the bulk answer is **correct** (Ru really is ~4× worse there) and would still read as a
    verdict on the metal. So the guard moves from "not in the registry" to "not offered where it would be
    misread": :data:`chip.interconnect.BULK_ERA_METALS`, which the game knob validates against.
    """
    assert ic.METALS["Cu"].rho0_uohm_cm < ic.METALS["Al"].rho0_uohm_cm    # the real, cited bulk win
    assert "Ru" in ic.METALS                                              # slice 4 gave it a regime...
    assert ic.BULK_ERA_METALS == ("Al", "Cu")                             # ...but not this one
    assert "Ru" not in ic.BULK_ERA_METALS

    # The bulk read still *works* for Ru — nothing raises — which is exactly why the knob must gate it:
    # the number is true at 250 nm and false as a claim about the metal. It is also the ladder's rung 1.
    geom = ic.WireGeometry()
    ru = ic.delay(geom, 3.3e-3, 2.3e-14, metal="Ru").tau_wire_s
    cu = ic.delay(geom, 3.3e-3, 2.3e-14, metal="Cu").tau_wire_s
    assert ru / cu == pytest.approx(ic.METALS["Ru"].rho0_uohm_cm / ic.METALS["Cu"].rho0_uohm_cm, rel=1e-12)
    assert ru > cu                                                        # ~4.2× worse, and true at 250 nm


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


def test_where_the_guard_fires_is_a_statement_about_the_LOAD_not_a_property_of_the_slice():
    """Whether Cu's crossover is inside the bulk regime depends on ``C_load`` — **corrected at slice 2**.

    Slice 1 asserted "the guard fires on copper's own crossover (~0.167 µm), which is why S4 is not a
    Ru-only slice" — but that rested on the **test-local** 23 fF load below (a *1 µm* channel), not on
    any operating point the sim runs. When slice 2 wired the **real** chain, the fan-out-1 load off the
    game's own device (``t_ox`` ≈ 14 nm, W = 10 µm, L = the printed ~167 nm CD ⇒ ``C_load`` ≈ 4.1 fF)
    put the crossover at ~0.395 µm — **comfortably inside** the bulk regime. Both are pinned here: the
    load is what moves the crossover, so neither is "the" operating point.

    The **S4 motivation survives and is unchanged**, because it never needed this: the size-effect
    correction grows without bound as W scales below ~0.19 µm, and the size effect became a **copper**
    problem at sub-200 nm (cited history) long before ruthenium was an option. What died is only the
    claim that *this* slice already sits outside its own model's competence — it does not.
    """
    cu = ic.METALS["Cu"]
    # The game's real fan-out-1 load (channel = the printed CD) — the crossover is INSIDE the bulk regime.
    game_load = ic.gate_load_capacitance(device.oxide_capacitance(0.0141), 10.0, 0.167)
    w_game = ic.crossover_width_um(3.3e-3, game_load, metal="Cu")
    assert 0.35 < w_game < 0.45                             # ~0.395 µm
    assert cu.bulk_regime_ok(w_game)                        # ...and the bulk model may speak there

    # A HEAVIER load (a 1 µm channel / fan-out > 1) pushes the crossover down, and there the guard fires.
    heavy_load = ic.gate_load_capacitance(device.oxide_capacitance(0.015), 10.0, 1.0)
    w_heavy = ic.crossover_width_um(3.3e-3, heavy_load, metal="Cu")
    assert 0.15 < w_heavy < 0.19                            # ~0.167 µm
    assert not cu.bulk_regime_ok(w_heavy)                   # outside — the size effect is ~20% there
    assert 0.15 < cu.mfp_nm / (w_heavy * 1e3) < 0.35

    # The direction is the invariant, not either number: a heavier load ⇒ a slower gate ⇒ the wire only
    # takes over at a NARROWER line. W_x ∝ 1/√τ_gate ∝ 1/√C_load.
    assert w_heavy < w_game
    assert w_game / w_heavy == pytest.approx(math.sqrt(heavy_load / game_load), rel=1e-9)


# --------------------------------------------------------------------------- #
# The damping law — ∂ln f/∂ln I_Dsat = 1 − wire_share (the consumer's payload, verified numerically)
# --------------------------------------------------------------------------- #
def test_drive_sensitivity_equals_the_numerical_log_derivative_of_the_real_clock_rate():
    """``drive_sensitivity`` is not a restatement — the analytic ``1 − wire_share`` matches a finite
    difference of the model's own ``f = 1/τ_total``, at every drive current.

    This is the slice-2 payload's engine: it says exactly how much a better transistor is still worth.
    Asserting it against a numerical derivative (rather than against ``1 − wire_share`` again) is what
    makes it a *check* — the property claims an analytic identity, and the model has to honour it.
    """
    geom = ic.WireGeometry()
    load = 4.0e-15
    for i in (5.0e-4, 1.0e-3, 3.3e-3, 1.0e-2, 5.0e-2):
        d = ic.delay(geom, i_dsat_A=i, c_load_farad=load)
        h = i * 1.0e-6                                       # a central difference in ln-space
        f_hi = 1.0 / ic.delay(geom, i + h, load).tau_total_s
        f_lo = 1.0 / ic.delay(geom, i - h, load).tau_total_s
        numeric = (math.log(f_hi) - math.log(f_lo)) / (math.log(i + h) - math.log(i - h))
        assert d.drive_sensitivity == pytest.approx(numeric, rel=1e-5)
        assert 0.0 < d.drive_sensitivity < 1.0               # the wire always damps, never inverts


def test_drive_sensitivity_is_one_without_a_wire_and_collapses_to_zero_as_the_wire_takes_over():
    """The two limits that bracket the era: ``1`` = the pre-1997 premise, ``→ 0`` = the wire wall.

    A zero-length wire has no ``τ_wire``, so ``∂ln f/∂ln I = 1`` **exactly** — a 3%-faster transistor is
    a 3%-faster part, which is precisely what :class:`fab_game.spec.SpeedBin` assumes. As the wire term
    grows the same transistor improvement buys monotonically less, → 0: the transistor stops setting
    speed. Nothing here is calibrated — the limits are structural.
    """
    load = 4.0e-15
    no_wire = ic.delay(ic.WireGeometry(length_um=0.0), 3.3e-3, load)
    assert no_wire.tau_wire_s == 0.0
    assert no_wire.drive_sensitivity == 1.0                  # exact — the pre-1997 premise, recovered
    assert no_wire.wire_share == 0.0

    # Lengthen the wire (τ_wire ∝ L²): the sensitivity falls monotonically toward zero.
    sens = [ic.delay(ic.WireGeometry(length_um=L), 3.3e-3, load).drive_sensitivity
            for L in (0.0, 100.0, 1000.0, 10_000.0)]
    assert sens == sorted(sens, reverse=True)                # monotone decreasing
    assert sens[-1] < 0.01                                   # a 1 cm global wire: the drive is worth ~nothing
    # ...and a WORSE metal damps harder at the same geometry (Al's τ_wire is 1.58× Cu's).
    al = ic.delay(ic.WireGeometry(), 3.3e-3, load, metal="Al")
    cu = ic.delay(ic.WireGeometry(), 3.3e-3, load, metal="Cu")
    assert al.drive_sensitivity < cu.drive_sensitivity


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
        ic.Metal("bad", rho0_uohm_cm=1.68, mfp_nm=20.0, barrier_nm=-1.0)
    with pytest.raises(ValueError):
        ic.WireGeometry(width_um=0.0)


# --------------------------------------------------------------------------- #
# SLICE 4 — the narrow-wire era: the two impossibility results, the floor, and the band
#
# The slice's conclusion is a SIGN (a metal with 4× copper's bulk ρ wins), so these tests are organised
# around what could invert it: a mechanism credited with more than it does, a deep-limit shortcut taken
# outside its domain, a flattering number printed for a metal that is disqualified elsewhere, and a
# crossing width quoted as a point when the cited inputs only support a band.
# --------------------------------------------------------------------------- #
def test_the_size_effect_ALONE_can_never_flip_the_sign_at_any_width():
    """**Impossibility result (a)** — cited constants only, and it is a limit, not an approximation.

    "Ruthenium wins because its mean free path is short" is the sign error the F4 plan exists to prevent,
    and this is the test that kills it: with the barrier off, R(Ru)/R(Cu) falls monotonically from the
    bulk ratio 4.23 toward ``ρ₀λ(Ru)/ρ₀λ(Cu)`` = **1.179** — and never reaches 1. The cited FOM buys
    ruthenium *parity*; parity is necessary and is not sufficient.
    """
    limit = ic.size_effect_ratio_limit("Ru", "Cu")
    assert limit == pytest.approx(ic.METALS["Ru"].rho0_lambda / ic.METALS["Cu"].rho0_lambda, rel=1e-12)
    assert limit == pytest.approx(1.179, abs=5e-4)
    assert limit > 1.0                                       # THE claim: the FOM ranks Ru second

    # ...and the numeric model agrees at every width, over eight decades, monotonically.
    widths = [100.0, 10.0, 1.0, 0.1, 0.02, 0.01, 1e-3, 1e-4, 1e-5, 1e-6]             # 100 µm → 1 pm
    ratios = [ic.resistance_ratio("Ru", "Cu", w, barrier=False) for w in widths]
    assert all(r > 1.0 for r in ratios)                      # never flips — not once, anywhere
    assert all(a > b for a, b in zip(ratios, ratios[1:]))    # monotone: it is approaching the limit
    assert ratios[0] == pytest.approx(4.226, abs=2e-3)       # the wide end IS the bulk ratio
    assert ratios[-1] == pytest.approx(limit, rel=1e-4)      # the narrow end IS the FOM ratio
    assert ratios[-1] > limit                                # approached from above, never crossing it
    # The 20 nm rung is the one to read: even where the size effect is severe, Ru is still 2.2× worse.
    assert ratios[widths.index(0.02)] == pytest.approx(2.217, abs=2e-3)
    # C cancels in the limit, which is why the limit needs no flagged input.
    for c in (0.375, 1.0, 5.0):
        assert ic.resistance_ratio("Ru", "Cu", 1e-6, c=c, barrier=False) == pytest.approx(limit, rel=1e-3)


def test_the_barrier_ALONE_on_bulk_rho_flips_only_below_a_width_with_no_conductor_left():
    """**Impossibility result (b)** — the mirror of (a), and the reason "Ru wins on the liner" is wrong too.

    ``W < 2t_b/(1 − ρ₀Cu/ρ₀Ru)`` = 5.2 nm at the cited ``t_b`` = 2 nm, while copper's conductor floor is
    4.0 nm. A **1.2 nm** window, immediately above the width at which copper is all barrier: the barrier
    acting on bulk resistivity has never had anywhere to act.
    """
    flip_nm = ic.barrier_only_flip_width_um("Ru", "Cu") * 1e3
    floor_nm = ic.conductor_floor_width_um("Cu") * 1e3
    assert flip_nm == pytest.approx(5.24, abs=0.01)
    assert floor_nm == pytest.approx(4.0, abs=1e-9)
    assert floor_nm < flip_nm < 1.5 * floor_nm               # the window exists and is ~1 nm wide

    # The closed form agrees with the numeric model on both sides of that width.
    assert ic.resistance_ratio("Ru", "Cu", (flip_nm - 0.3) * 1e-3, size_effect=False) < 1.0
    assert ic.resistance_ratio("Ru", "Cu", (flip_nm + 0.3) * 1e-3, size_effect=False) > 1.0
    # ...and at every width a fab has ever printed, the barrier on bulk ρ leaves Ru losing — by a lot,
    # and by more the wider the line, since a fixed liner is a shrinking fraction of a growing budget.
    losses = [ic.resistance_ratio("Ru", "Cu", w * 1e-3, size_effect=False) for w in (7.0, 12.0, 20.0, 50.0)]
    assert all(r > 1.8 for r in losses)
    assert all(a < b for a, b in zip(losses, losses[1:]))    # 1.81 → 2.82 → 3.38 → 3.90, toward 4.23

    # A challenger that already has the lower bulk ρ has no deficit to overcome — the read refuses.
    with pytest.raises(ValueError):
        ic.barrier_only_flip_width_um("Cu", "Ru")


def test_the_three_rung_ladder_is_what_gets_the_sign_right_and_neither_rung_alone_does():
    """The payload: 4.23 → 1.90 → 0.92 at a 12 nm line, with the barrier-only rung at 2.82 as the control.

    This is F3's IL structure in the wire's currency — two currencies, additive, and *neither one alone
    gets the sign right*. Pinned as a table so a later "simplification" to one mechanism fails loudly.
    """
    W = 0.012                                                # 12 nm drawn linewidth
    bulk = ic.resistance_ratio("Ru", "Cu", W, size_effect=False, barrier=False)
    sized = ic.resistance_ratio("Ru", "Cu", W, size_effect=True, barrier=False)
    barred = ic.resistance_ratio("Ru", "Cu", W, size_effect=False, barrier=True)
    both = ic.resistance_ratio("Ru", "Cu", W, size_effect=True, barrier=True)

    assert bulk == pytest.approx(4.226, abs=2e-3)            # ruthenium is hopeless on bulk ρ
    assert sized == pytest.approx(1.901, abs=2e-3)           # the size effect closes most of it...
    assert barred == pytest.approx(2.817, abs=2e-3)          # ...and so does the barrier, separately...
    assert both == pytest.approx(0.917, abs=2e-3)            # ...and only TOGETHER do they flip it

    assert sized > 1.0 and barred > 1.0 and both < 1.0       # THE claim, in one line
    assert bulk == pytest.approx(ic.METALS["Ru"].rho0_uohm_cm / ic.METALS["Cu"].rho0_uohm_cm, rel=1e-12)


def test_the_narrow_wire_ratio_is_prefactor_free():
    """L, H, the aspect ratio, c_pul, the Elmore factor and V_dd all cancel — as in every F4 headline."""
    W = 0.012
    expected = ic.resistance_ratio("Ru", "Cu", W)
    for length in (1.0, 1000.0, 5.0e4):
        for thick in (0.006, 0.024, 1.0):
            geom = ic.WireGeometry(length_um=length, width_um=W, thickness_um=thick)
            ru = ic.narrow_line_resistance("Ru", geom)
            cu = ic.narrow_line_resistance("Cu", geom)
            assert ru / cu == pytest.approx(expected, rel=1e-12)


def test_the_crossing_is_a_BAND_over_the_cited_barrier_range_not_a_point():
    """Where ruthenium wins is set by the thickness of the layer that stopped scaling — that IS the finding.

    The cited ``t_b`` = 2–3 nm range alone moves the crossing 12.9 → 17.1 nm (about a node), so quoting a
    point would fabricate a precision the cited inputs do not carry. The flagged ``C`` widens it further.
    Status: the IBM ~40% consistency check's, never a prediction.
    """
    lo_tb, hi_tb = ic.BARRIER_NM_CITED_RANGE
    w_lo = ic.equal_resistance_width_nm("Ru", "Cu", barrier_nm=lo_tb)
    w_hi = ic.equal_resistance_width_nm("Ru", "Cu", barrier_nm=hi_tb)
    assert w_lo == pytest.approx(12.88, abs=0.05)
    assert w_hi == pytest.approx(17.13, abs=0.05)
    assert w_lo < w_hi                                       # a thicker liner ⇒ Ru wins EARLIER (wider)

    # The band sits inside the literature's <~20 nm, and the whole flagged-C span stays bracketed there.
    for c in (0.375, 1.0, 2.0):
        assert 9.0 < ic.equal_resistance_width_nm("Ru", "Cu", c=c) < 21.5

    # It is a genuine root of the model, not a table: the ratio brackets 1 across it.
    assert ic.resistance_ratio("Ru", "Cu", (w_lo - 1.0) * 1e-3) < 1.0
    assert ic.resistance_ratio("Ru", "Cu", (w_lo + 1.0) * 1e-3) > 1.0


def test_the_FOM_ranks_metals_but_does_NOT_locate_the_crossing():
    """The deep-limit shortcut is wrong here by ~4×, and the test exists so nobody "simplifies" to it.

    ``ρ_eff → C·ρ₀λ/d`` for **both** metals would put Cu→Ru at ~50 nm. The full form says ~13. The reason
    is the same short mean free path that makes ruthenium viable at all: at the crossing ``C·λ/W`` ≈ 0.84
    for Ru — it is **not in its own deep limit**, so the FOM's domain of validity does not contain the
    width where the sign flips. The FOM is a *screening* metric; treating it as a locator is an error.
    """
    t_b = ic.METALS["Cu"].barrier_nm
    fom = ic.size_effect_ratio_limit("Ru", "Cu")
    deep_nm = 2.0 * t_b / (1.0 - 1.0 / math.sqrt(fom))       # the tempting closed form — R ∝ ρ₀λ/W_eff²
    full_nm = ic.equal_resistance_width_nm("Ru", "Cu")

    assert deep_nm == pytest.approx(50.5, abs=0.5)
    assert full_nm == pytest.approx(12.88, abs=0.05)
    assert deep_nm > 3.5 * full_nm                           # not a rounding difference — a wrong domain

    ru = ic.METALS["Ru"]
    assert ic.SIZE_EFFECT_C * ru.mfp_nm / full_nm == pytest.approx(0.84, abs=0.02)   # ≉ ≫ 1
    assert ic.SIZE_EFFECT_C * ic.METALS["Cu"].mfp_nm / (full_nm - 2 * t_b) > 4.0     # Cu, by contrast, IS


def test_the_conductor_floor_is_geometric_and_the_read_refuses_to_extrapolate_through_it():
    """``W = 2·t_b``: below it a copper line is all barrier — for ANY ρ, L, C or aspect ratio.

    F3's "``EOT > t_IL`` for any κ" in the wire's currency, and prefactor-free the same way. The read
    raises rather than returning a zero or a negative width (the F3 magnitude trap).
    """
    for t_b in (2.0, 2.5, 3.0):
        assert ic.conductor_floor_width_um("Cu", barrier_nm=t_b) * 1e3 == pytest.approx(2.0 * t_b)
    assert ic.conductor_floor_width_um("Ru") == 0.0          # barrierless ⇒ no floor at all

    assert ic.conductor_width_um(0.012, "Cu") * 1e3 == pytest.approx(8.0, abs=1e-9)
    for bad_nm in (4.0, 3.0, 0.5):                           # at the floor and below it
        with pytest.raises(ValueError):
            ic.conductor_width_um(bad_nm * 1e-3, "Cu")
    with pytest.raises(ValueError):
        ic.narrow_line_resistance("Cu", ic.WireGeometry(width_um=0.003, thickness_um=0.006))


def test_the_narrow_wire_reads_refuse_aluminium_and_the_refusal_is_load_bearing():
    """Al's ρ₀λ ≈ 58 screens BETTER than copper's 65 — and this module may not say so.

    Aluminium's real disqualifier is electromigration, a reliability currency F4 does not carry, so a
    narrow-wire comparison including Al would be a claim with no support behind it. S3's "the cap is
    binding, not cosmetic", applied to a metal instead of a width — and the number is checked here so the
    refusal is understood to be *hiding something*, not merely absent data.
    """
    al, cu = ic.METALS["Al"], ic.METALS["Cu"]
    assert al.rho0_lambda < cu.rho0_lambda                   # the flattering number really is flattering
    assert al.barrier_nm is None and not al.narrow_wire_candidate
    assert ic.NARROW_WIRE_METALS == ("Cu", "Ru")             # derived from METALS, never hand-maintained

    geom = ic.WireGeometry(width_um=0.012, thickness_um=0.024)
    for call in (lambda: ic.narrow_line_resistance("Al", geom),
                 lambda: ic.resistance_ratio("Al", "Cu", 0.012),
                 lambda: ic.resistance_ratio("Ru", "Al", 0.012),
                 lambda: ic.effective_resistivity("Al", 0.012),
                 lambda: ic.conductor_floor_width_um("Al"),
                 lambda: ic.size_effect_ratio_limit("Al", "Cu")):
        with pytest.raises(ValueError, match="electromigration"):
            call()


def test_the_size_effect_coefficient_errs_AGAINST_the_ruthenium_conclusion():
    """``C`` = 1.0 is round and unfitted, and the direction of its error is the thing to pin.

    It puts copper at ~6.3 µΩ·cm in an 18 nm line where the measurement is ~9 (a ~5× bulk degradation),
    i.e. it **understates** copper's narrow-line penalty and makes ruthenium's win harder to earn. Along
    with the width-only ``W_eff``, that is why the crossing band lands *inside* the literature's ~20 nm
    rather than being tuned onto it. A future re-source may raise ``C``; this test says which way that
    moves the conclusion (it strengthens it) so the change cannot be mistaken for a fix.
    """
    rho_18 = ic.effective_resistivity("Cu", ic.conductor_width_um(0.018, "Cu"))
    assert rho_18 == pytest.approx(6.32, abs=0.02)
    assert rho_18 < 9.0                                      # the measured value — we are BELOW it
    assert rho_18 / ic.METALS["Cu"].rho0_uohm_cm > 3.0       # ...though still a large, real degradation

    # Raising C toward the measurement moves the crossing WIDER, i.e. Ru wins EARLIER: the default is the
    # conservative end of its own sensitivity, not the middle of it.
    assert (ic.equal_resistance_width_nm("Ru", "Cu", c=1.6)
            > ic.equal_resistance_width_nm("Ru", "Cu", c=ic.SIZE_EFFECT_C))
    assert ic.SIZE_EFFECT_C == 1.0                           # unfitted, and pinned as such


def test_the_featured_rung_survives_the_scattering_dimension_convention():
    """The fourth simplification, priced: ``d`` = the conductor **width**, not a cross-section.

    Real scattering sees both surface pairs and the rates add, so the standard rectangular form is
    ``1/d = 1/W_eff + 1/H``. This module uses ``d = W_eff`` for two reasons, and a test is the right place
    for them because the slice's conclusion is a **sign**:

      1. it **errs against ruthenium** — the standard form makes Ru win by *more*, so the published
         crossing is the conservative one; and
      2. bringing ``H`` in would put the flagged aspect ratio into :func:`resistance_ratio`, which is
         prefactor-free precisely because ``H`` cancels.

    Both are checked here against a hand-rolled standard-form calculation, so a future change of
    convention has to confront the direction rather than discover it.
    """
    W, t_b, C = 0.012, 2.0, ic.SIZE_EFFECT_C
    H = 2.0 * W                                              # the demo's flagged aspect ratio

    def standard_form_ratio() -> float:
        out = []
        for name in ("Ru", "Cu"):
            m = ic.METALS[name]
            w = W - 2.0 * (m.barrier_nm / 1e3)
            d = 1.0 / (1.0 / w + 1.0 / H)                    # additive surface-scattering rates
            rho = m.rho0_uohm_cm * (1.0 + C * m.mfp_nm / (d * 1e3))
            out.append(rho / (w * H))
        return out[0] / out[1]

    ours = ic.resistance_ratio("Ru", "Cu", W)
    standard = standard_form_ratio()
    assert ours == pytest.approx(0.917, abs=2e-3)
    assert standard == pytest.approx(0.889, abs=2e-3)
    assert standard < ours < 1.0                             # BOTH say Ru wins; ours by the smaller margin

    # (2) the reason we keep the width-only form: H and the aspect ratio cancel out of OUR ratio exactly,
    # and would not out of the standard one. That cancellation is what makes the headline prefactor-free.
    for thick in (0.006, 0.024, 0.5):
        geom = ic.WireGeometry(width_um=W, thickness_um=thick)
        assert (ic.narrow_line_resistance("Ru", geom) / ic.narrow_line_resistance("Cu", geom)
                == pytest.approx(ours, rel=1e-12))


def test_narrow_line_resistance_reduces_to_the_bulk_read_with_both_mechanisms_off():
    """The seam: both switches off ⇒ byte-for-byte :func:`wire_resistance` at the bulk ρ₀.

    The additive discipline every F4 slice has kept — a new mechanism must have an off position that
    reproduces the old model exactly, not approximately.
    """
    geom = ic.WireGeometry(width_um=0.012, thickness_um=0.024)
    for name in ic.NARROW_WIRE_METALS:
        m = ic.METALS[name]
        assert (ic.narrow_line_resistance(m, geom, size_effect=False, barrier=False)
                == ic.wire_resistance(m.rho0_uohm_cm, geom.length_um, geom.width_um, geom.thickness_um))


def test_slice_4_adds_a_second_path_and_does_not_retire_the_bulk_guard():
    """``bulk_regime_ok`` still marks the same boundary — it just now has somewhere to point.

    Stated because slices 1 and 3 both wrote "slice 4 removes the need for the guard", and that is not
    what happened: :func:`delay` and :func:`crossover_width_um` are still bulk-only, so their validity
    bound is unchanged. What slice 4 added is a *second* read that is valid where the first is not.
    """
    cu = ic.METALS["Cu"]
    assert cu.bulk_regime_ok(0.25)                           # the Al→Cu era — the bulk path speaks
    assert not cu.bulk_regime_ok(0.012)                      # the Ru era — it does not

    # ...and there, the narrow path does, with a materially different answer than the bulk one would give.
    bulk_ratio = ic.wire_delay_ratio("Ru", "Cu")             # 4.23 — the bulk path's verdict at any width
    narrow_ratio = ic.resistance_ratio("Ru", "Cu", 0.012)    # 0.92 — the narrow path's, at 12 nm
    assert bulk_ratio > 1.0 > narrow_ratio                   # opposite signs: the regime is the claim
