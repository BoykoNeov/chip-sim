"""Integration test for the BEOL history demo (B9 — the F4 payload, made assertable end-to-end).

``test_interconnect.py`` exercises :mod:`chip.interconnect` with hardcoded inputs and never calls the
demo; this test guards the *chaining* — that the ladder and the crossover really run through the **real**
:mod:`chip.device`, which is what makes "``device.py`` is untouched" a demonstration rather than an
assertion — and, mostly, the **honesty guards** that are the reason the file exists (following B8's
precedent; B7 has no demo test):

  * **the ladder stays in the regime the model is honest in** — the F3 slice-3 trap in F4's currency.
    :mod:`chip.interconnect` is bulk-ρ only, so a ladder walked past ``5λ_Cu`` would fabricate exactly the
    number **slice 4** exists to compute (the size effect). The cap is a claim about where the model may
    speak, so it is pinned here rather than left to a reader's restraint;
  * **the crossover shift is never rounded up into "a node"** — Al→Cu moves ``W_x`` by 0.796×, and a node
    step is 0.70×, so 1997 bought **0.64** of a node. "Roughly one node" rounds a win up, which is the one
    direction this repo never rounds (B8's ``floor_decades`` rule, here in the crossover's currency);
  * **the metal ratios are not inverted** — and this one is not hypothetical: the first run of this demo
    printed silver as buying **−0.08** of a node (i.e. *worse* than copper, which is false) because
    ``crossover_width_ratio`` was called with the incumbent first and then reciprocated. It is the exact
    cousin of slice 2's ``lo_mA`` → ``hi_ps`` bound swap: a direction error that still renders as a
    perfectly plausible figure.

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import math

import numpy as np
import pytest

from chip import device as dev
from chip import interconnect as ic
from chip.demo_beol_history import (
    ASPECT_RATIO, DRIVE_SWEEP, FEATURE_DRIVE_GAIN, FEATURE_W_UM, LADDER_FLOOR_UM, METALS,
    NEXT_NODE_UM, NODE_LADDER_UM, NODE_SHRINK, PERIOD_CHANNEL_L_UM, PERIOD_N_A, PERIOD_T_OX_UM,
    PERIOD_WIDTH_UM, SILVER, W_LADDER_UM, compute, nodes_bought,
)


def test_the_transistor_is_the_real_untouched_device_chain():
    """The period ``τ_gate`` is a genuine CV/I read of the real ``device.py``, not a house lump."""
    r = compute()
    mos = dev.threshold_voltage(PERIOD_N_A, PERIOD_T_OX_UM, channel_length_um=PERIOD_CHANNEL_L_UM)
    assert r.mos.V_t == mos.V_t                                     # the same call reproduces it exactly
    assert r.i_dsat_A == dev.saturation_current(mos, V_GS=ic.V_DD_HOUSE, width_um=PERIOD_WIDTH_UM)
    assert r.c_load_F == ic.gate_load_capacitance(
        dev.oxide_capacitance(PERIOD_T_OX_UM), PERIOD_WIDTH_UM, PERIOD_CHANNEL_L_UM)
    assert r.tau_gate_s == pytest.approx(r.c_load_F * ic.V_DD_HOUSE / r.i_dsat_A)
    # …and the recipe is period-plausible rather than tuned: a mid-90s n-MOS at 3.3 V ran V_t ≈ 0.6 V.
    assert 0.4 < r.mos.V_t < 0.8, f"the period device's V_t ({r.mos.V_t:.3f} V) left the era's range"


def test_the_wire_term_is_blind_to_the_transistor_and_the_gate_term_is_flat():
    """**The discriminator**, end-to-end: the two terms share no variable, so the ladder cannot move τ_gate.

    ``τ_gate`` being a single float in the bundle is already the claim structurally — this pins that the
    wire ladder really is evaluated against *one* unchanging transistor, and that ``I_Dsat`` reaches the
    wire term nowhere (doubling it leaves every ``τ_wire`` bit-for-bit).
    """
    r = compute()
    for m in METALS:
        doubled = np.array([
            ic.delay(ic.WireGeometry(width_um=w, thickness_um=ASPECT_RATIO * w),
                     r.i_dsat_A * 2.0, r.c_load_F, metal=m).tau_wire_s
            for w in W_LADDER_UM
        ])
        assert np.array_equal(doubled, r.tau_wire_s[m]), f"{m}: I_Dsat moved the wire term"


def test_the_wall_is_monotone_and_a_crossing_exists_for_both_metals():
    """The honest payload is the *shape*: τ_wire ∝ 1/W² climbs monotonically and crosses the flat gate."""
    r = compute()
    for m in METALS:
        t = r.tau_wire_s[m]
        assert all(b > a for a, b in zip(t, t[1:])), f"{m}: τ_wire must rise as the wire scales down"
        assert t[0] < r.tau_gate_s < t[-1], f"{m}: the ladder must actually cross the gate's flat line"
        # the crossover the closed form reports is where the ladder really crosses (an independent check
        # of crossover_width_um against the demo's own sampled curve)
        w_x = float(np.interp(r.tau_gate_s, t, r.w_um))     # t rises as w_um falls ⇒ t is the ordered axis
        assert w_x == pytest.approx(r.crossover_um[m], rel=2e-2)
        # τ_wire ∝ 1/W² — the exponent is the shape claim, and it is prefactor-free (H = AR·W, so
        # R ∝ 1/(W·H) ∝ 1/W²). The narrow end over the wide end: (0.20/1.00)^-2 = 25×.
        assert t[-1] / t[0] == pytest.approx((r.w_um[-1] / r.w_um[0]) ** -2, rel=1e-9)
        assert all(b > a for a, b in zip(r.wire_share[m], r.wire_share[m][1:]))
    # copper is the same curve, shifted — NOT a shallower one (the right panel's whole point)
    ratio = r.tau_wire_s["Al"] / r.tau_wire_s["Cu"]
    assert np.allclose(ratio, ic.wire_delay_ratio("Al", "Cu"), rtol=1e-9), "the metals must stay parallel"


def test_the_ladder_stays_inside_the_bulk_regime_the_model_is_honest_in():
    """**The slice-3 magnitude trap, pinned.** The bulk-ρ ladder may not walk where only slice 4 can speak.

    ``chip.interconnect`` models ``ρ_eff = ρ₀``, valid for ``W ≫ λ``. Below ``5λ_Cu`` ≈ 0.194 µm the size
    effect is a large and growing correction this module does not carry, so a ladder walked to the next
    real node (0.18 µm) would report a *fabricated* τ_wire — understating it, and understating exactly the
    wall slice 4 exists to compute. Widen this and the demo starts making datasheet claims.
    """
    for m in METALS:
        assert ic.METALS[m].bulk_regime_ok(LADDER_FLOOR_UM), f"{m}: the ladder floor left the bulk regime"
        assert ic.METALS[m].bulk_regime_ok(min(W_LADDER_UM))
        assert ic.METALS[m].bulk_regime_ok(FEATURE_W_UM), "the featured node must be inside the regime"
    # …and the cap is *binding*, not decorative: the next real node is already off-limits to this model.
    assert not ic.METALS["Cu"].bulk_regime_ok(NEXT_NODE_UM), (
        "the 0.18 µm node must be OUTSIDE the bulk regime — that refusal is the hand-off to slice 4, and "
        "the whole justification for capping the ladder at 0.20 µm"
    )
    assert NEXT_NODE_UM < LADDER_FLOOR_UM <= min(W_LADDER_UM)


def test_the_featured_node_is_the_wire_the_game_actually_runs():
    """The featured rung's geometry **is** ``WireGeometry()``'s default — the line slice 2's knob runs.

    Not decoration: it is what stops this demo and the game's binning inversion from being about two
    different wires. (The ``wire_share`` legitimately differs from slice 2's ≈0.71 — same wire, a
    different transistor — which is why this pins the *geometry* rather than the readout.)
    """
    default = ic.WireGeometry()
    assert (default.width_um, default.thickness_um) == (FEATURE_W_UM, ASPECT_RATIO * FEATURE_W_UM)
    assert FEATURE_W_UM in NODE_LADDER_UM and FEATURE_W_UM == min(NODE_LADDER_UM)


def test_the_damping_law_is_exact_and_the_premise_is_the_diagonal():
    """The payload: ``∂ln f/∂ln I_Dsat = 1 − wire_share``, checked against a **numerical** log-derivative.

    The middle panel's claim is that the premise (``f ∝ I_Dsat`` — a slope of exactly 1, which is what
    ``fab_game.spec.SpeedBin`` still encodes) and reality diverge by precisely ``wire_share``. Checking
    the closed form against the demo's own sampled curve makes this a check rather than a restatement.
    """
    r = compute()
    assert np.array_equal(r.f_ratio["premise"], DRIVE_SWEEP)        # the premise IS the diagonal, exactly
    for m in METALS:
        lo, hi = 90, 110
        slope = ((math.log(r.f_ratio[m][hi]) - math.log(r.f_ratio[m][lo]))
                 / (math.log(r.drive_ratio[hi]) - math.log(r.drive_ratio[lo])))
        at = ic.delay(ic.WireGeometry(), r.i_dsat_A * r.drive_ratio[(lo + hi) // 2], r.c_load_F, metal=m)
        assert slope == pytest.approx(at.drive_sensitivity, rel=2e-2)
        assert 0.0 < at.drive_sensitivity < 1.0                     # strictly damped, never dead
        # the premise overprices a drive improvement at every single point of the sweep
        assert np.all(r.f_ratio[m][r.drive_ratio > 1.0] < r.f_ratio["premise"][r.drive_ratio > 1.0])
    # …and the wire is wire: at the featured node an Al line leaves a +3% transistor worth well under 1%
    worth = (FEATURE_DRIVE_GAIN - 1.0) * r.feature["Al"].drive_sensitivity
    assert worth < 0.01, f"the featured node must actually show the premise dying (got +{worth*100:.2f}%)"


def test_the_crossover_ratio_direction_is_not_inverted():
    """**A sign guard, and it caught a live bug.** ``crossover_width_ratio`` takes the CHALLENGER first.

    The first run of this demo reported silver as buying **−0.08** of a node — i.e. as a *worse* conductor
    than copper, which is false — because the call was made incumbent-first and then reciprocated. For
    Al→Cu that reciprocal happens to be the right number; for Cu→Ag it is the reciprocal of it, so the
    error renders as a perfectly plausible figure and only the *sign* gives it away. This is F4's cousin
    of slice 2's ``lo_mA`` → ``hi_ps`` bound swap, and the reason both are pinned rather than reviewed.
    """
    # ratio(a, b) = W_x(a)/W_x(b) = √(ρ_a/ρ_b): a value < 1 means the challenger `a` is the better wire.
    assert ic.crossover_width_ratio("Cu", "Al") == pytest.approx(math.sqrt(1.68 / 2.65))
    assert ic.crossover_width_ratio("Cu", "Al") < 1.0 < ic.crossover_width_ratio("Al", "Cu")
    # copper is better than aluminium, so it BUYS nodes (positive) …
    assert nodes_bought(ic.crossover_width_ratio("Cu", "Al")) > 0.0
    # … and silver is better than copper, so it buys a (tiny) positive number too — never a negative one.
    ag = nodes_bought(ic.crossover_width_ratio(SILVER, "Cu"))
    assert ag > 0.0, f"silver is a BETTER conductor than copper; it cannot buy {ag:+.2f} of a node"
    assert ag < 0.1, "…and it is a rounding error of a node — that is the ceiling this demo reports"
    # the inverted spelling is what produced the bug — pin that it really does flip the sign
    assert nodes_bought(1.0 / ic.crossover_width_ratio(SILVER, "Cu")) < 0.0


def test_copper_bought_two_thirds_of_a_node_and_is_never_rounded_up_to_one():
    """**The headline claim, floored in the crossover's currency.** 0.796× is NOT "a node".

    ``W_x ∝ √ρ₀``, so Al→Cu's 1.58× in resistivity buys only ``√`` of it — 0.796× — while a node step is
    0.70×. That is 0.64 of a node. Calling it "roughly one node" (as ``chip.interconnect`` originally did)
    overstates the 1997 escape by ~50%, and overstating a win is the one direction this repo never allows.
    """
    shift = ic.crossover_width_ratio("Cu", "Al")
    assert shift == pytest.approx(0.7962, rel=1e-3)
    assert nodes_bought(shift) == pytest.approx(0.639, rel=1e-2)
    assert nodes_bought(shift) < 1.0, "0.796× is not a 0.70× node step — do not round this up"
    # the unit is self-consistent: one node step is exactly one node.
    assert nodes_bought(NODE_SHRINK) == pytest.approx(1.0)
    assert nodes_bought(1.0) == pytest.approx(0.0)                  # a metal that changes nothing buys 0
    assert nodes_bought(NODE_SHRINK**2) == pytest.approx(2.0)
    # the ladder really is the 0.7×-per-generation one it claims to be
    for a, b in zip(NODE_LADDER_UM, NODE_LADDER_UM[1:]):
        assert 0.6 < b / a < 0.75


def test_the_bulk_axis_is_exhausted_and_the_claim_is_scoped_to_that_axis():
    """The right panel: one more node needs ρ ≤ 0.82 µΩ·cm, and the periodic table stops at silver.

    Prefactor-free (a ratio of ρ's — ``L``, ``c_pul``, ``V_dd``, ``C_load``, ``AR`` and the Elmore factor
    all cancel), which is why this panel carries the era claim. **Scoped deliberately to the bulk axis:**
    "no metal beats copper" would be *false* — slice 4 has ruthenium winning at narrow ``W`` with 4×
    copper's bulk ρ. What is exhausted is the **axis**, which is exactly why the axis must change.
    """
    r = compute()
    assert r.rho_for_next_node == pytest.approx(ic.METALS["Cu"].rho0_uohm_cm * NODE_SHRINK**2)
    assert r.rho_for_next_node == pytest.approx(0.823, rel=1e-2)
    # nothing is there: silver, the best elemental conductor, is more than 1.9× above the requirement
    assert SILVER.rho0_uohm_cm > r.rho_for_next_node * 1.9
    assert SILVER.rho0_uohm_cm < ic.METALS["Cu"].rho0_uohm_cm      # …and it IS better than copper, barely
    # the panel's curve is the prefactor-free √ law it claims to be
    assert np.allclose(r.wx_ratio_vs_cu, np.sqrt(r.rho_uohm_cm / ic.METALS["Cu"].rho0_uohm_cm))
    # the scoping, made structural: on the SCALING axis silver is worse than copper — the bulk ordering
    # is not the ρ₀λ ordering, which is the whole reason slice 4 changes axis rather than shopping metals.
    assert SILVER.rho0_lambda > ic.METALS["Cu"].rho0_lambda
    # …and ruthenium must not be plottable here: a bulk-only model ranks it LAST (the sign trap inverted).
    assert "Ru" not in ic.METALS and SILVER.name not in ic.METALS


def test_the_transistors_own_progress_pulls_the_wall_in_by_the_same_root():
    """The arc's deep point, pinned: ``W_x ∝ √I_Dsat`` exactly as ``W_x ∝ √ρ₀`` — they trade one-for-one.

    A 2× better transistor pulls the crossover out to a √2 **wider** wire (an *earlier* node) by the very
    same √2 a 2× better metal pushes it in. Prefactor-free, and it is why "freeze the transistor" is a
    *priced* choice here rather than a hidden one.
    """
    r = compute()
    base = ic.crossover_width_um(r.i_dsat_A, r.c_load_F, aspect_ratio=ASPECT_RATIO)
    doubled = ic.crossover_width_um(r.i_dsat_A * 2.0, r.c_load_F, aspect_ratio=ASPECT_RATIO)
    assert doubled / base == pytest.approx(math.sqrt(2.0))
    # …the same √2 a 2× better metal buys, in the opposite direction
    assert ic.crossover_width_ratio(ic.Metal("half-ρ", ic.METALS["Cu"].rho0_uohm_cm / 2.0, 38.7), "Cu") \
        == pytest.approx(1.0 / math.sqrt(2.0))


def test_figure_builds():
    r = compute()
    pytest.importorskip("matplotlib")               # the figure is not in the correctness path (ADR 0002)
    from chip.demo_beol_history import save_figure
    assert save_figure(r).is_file()
