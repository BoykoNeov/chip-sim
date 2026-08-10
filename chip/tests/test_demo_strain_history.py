"""Integration test for the strained-silicon history demo (B10 — the F5 payload, end-to-end).

``test_strain.py`` exercises :mod:`chip.strain` with hardcoded inputs and never calls the demo: it already
pins the registry, the seam, the elasticity **definition** and the hole-leg refusal, and none of that is
re-asserted here. This test guards what only the demo can break — the **chaining** and the **words**:

  * **the two paths really leave one point** — the seam is what makes the left panel a comparison rather
    than two unrelated curves, and it is exercised through the *real* :mod:`chip.device`
    (``strained_channel(MU_N_EFF, None)`` is ``saturation_current``'s own default, so the unstrained rung
    is byte-for-byte today's number);
  * **the orthogonality is structural, not numerical** — the panel's whole claim is that strain's leakage
    column is *zero*, and the reason is that :func:`chip.high_k.gate_leakage` has no mobility argument at
    all. Pinned as a bit-for-bit identity under an arbitrary mobility, B9's ``∂τ_wire/∂I_Dsat = 0`` shape;
  * **the exchange rate is quoted in the direction that does NOT flatter the slice** — the ladder holds
    the channel doping fixed, so ``V_t`` sags and the *oxide* lever looks cheap. Quoting the other
    convention (a re-adjusted ``V_t``, ``I ∝ C_ox``) would roughly double the decades strain is credited
    with avoiding. This is the F4 ``floor_decades`` rule in F5's currency: never round a win up;
  * **the drive read is drawn as a bound, and the bound's direction is on the figure** — the wired path
    *is* the optimistic number, so the only enforcement available is that the cited measurement is drawn
    beside it;
  * **the figure's words**, which the fast lane otherwise cannot check (F3's follow-up lesson: the golden
    tests confirm the prose did not *change*, never that it is still *true*).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import math
from pathlib import Path

import numpy as np
import pytest

from chip import device as dev
from chip import high_k as hk
from chip import strain as st

from chip import demo_strain_history
from chip.demo_strain_history import (
    GATE_DIELECTRIC, MU_FACTOR_AXIS, OXIDE_LADDER_FLOOR_UM, PERIOD_CHANNEL_L_UM, PERIOD_N_A,
    PERIOD_T_OX_UM, PERIOD_VT_ADJUST_DOSE, PERIOD_VT_ADJUST_KIND, PERIOD_WIDTH_UM, T_OX_LADDER_UM,
    V_GS_CITED, WIRED_MECHANISM, compute, decades,
)


def test_the_period_device_is_the_real_untouched_device_chain():
    """The unstrained rung is a genuine ``device.py`` read — which is what "untouched" *demonstrates*."""
    r = compute()
    mos = dev.threshold_voltage(
        PERIOD_N_A, PERIOD_T_OX_UM, channel_length_um=PERIOD_CHANNEL_L_UM,
        implant_dose=PERIOD_VT_ADJUST_DOSE, implant_kind=PERIOD_VT_ADJUST_KIND,
    )
    assert r.mos.V_t == mos.V_t
    assert r.i_dsat_A == dev.saturation_current(mos, V_GS=V_GS_CITED, width_um=PERIOD_WIDTH_UM)
    # …and the recipe is era-plausible rather than tuned: a 90 nm-era n-MOS at 1.2 V ran V_t ≈ 0.3–0.5 V.
    assert 0.25 < r.mos.V_t < 0.60, f"the period device's V_t ({r.mos.V_t:.3f} V) left the era's range"
    assert r.mos.V_t < V_GS_CITED                                   # …and the device actually turns on


def test_both_paths_leave_the_same_point_because_the_seam_is_the_default():
    """**The seam, end-to-end.** No mechanism ⇒ ``mu_eff == MU_N_EFF`` ⇒ the period ``I_Dsat`` bit-for-bit.

    This is what makes the left panel a *comparison*: the strained curve starts on the unstrained point
    rather than beside it. Asserted through the demo's own period read, not through ``chip.strain`` alone.
    """
    r = compute()
    seam = st.strained_channel(dev.MU_N_EFF, None)
    assert seam.mu_strained_cm2_Vs == dev.MU_N_EFF                  # exactly — not approximately
    assert dev.saturation_current(r.mos, V_GS=V_GS_CITED, width_um=PERIOD_WIDTH_UM,
                                  mu_eff=seam.mu_strained_cm2_Vs) == r.i_dsat_A
    assert r.drive_gain_oxide[0] == 1.0                             # the ladder's own first rung is the seam
    assert r.j_gate_oxide[0] == r.j_gate_A_cm2


def test_the_strain_path_leaves_the_leakage_bit_for_bit_and_the_zero_is_STRUCTURAL():
    """**The left panel's whole claim.** ``∂J_g/∂µ = 0`` — mobility is not an argument of the leakage model.

    The B9 shape (``I_Dsat`` reaches the wire term nowhere), in F5's currency. Pinned as an identity under
    an *absurd* mobility rather than the cited one: if any path from µ to the gate stack were ever added,
    "strain costs no leakage" would silently become a numerical coincidence instead of a structural fact,
    and this panel's headline would be wrong without any number visibly moving.
    """
    r = compute()
    assert r.j_gate_strained_A_cm2 == r.j_gate_A_cm2                # bit-for-bit, not pytest.approx
    assert r.strain_decades == 0.0
    for absurd_factor in (1.20, 3.0, 100.0):
        mu = dev.MU_N_EFF * absurd_factor
        assert dev.saturation_current(r.mos, V_GS=V_GS_CITED, width_um=PERIOD_WIDTH_UM,
                                      mu_eff=mu) > r.i_dsat_A       # the drive really does move …
        assert hk.gate_leakage(PERIOD_T_OX_UM, GATE_DIELECTRIC) == r.j_gate_A_cm2   # … and the leakage cannot


def test_the_oxide_lever_moves_BOTH_currencies_and_both_monotonically():
    """The other half of the contrast: one knob, two currencies — B8's wall read from F5's side."""
    r = compute()
    assert all(b > a for a, b in zip(r.drive_gain_oxide, r.drive_gain_oxide[1:]))
    assert all(b > a for a, b in zip(r.j_gate_oxide, r.j_gate_oxide[1:]))
    # the drive rises FASTER than 1/t_ox on this convention, because V_t sags as the oxide thins — which
    # is exactly why this reading is the one favourable to the oxide lever (see the next test).
    ratio_c_ox = PERIOD_T_OX_UM / T_OX_LADDER_UM[-1]
    assert r.drive_gain_oxide[-1] > ratio_c_ox


def test_the_exchange_rate_is_quoted_in_the_direction_that_does_not_flatter_strain():
    """**Never round a win up** (F4's ``floor_decades`` rule, in the leakage currency).

    Two defensible conventions for "what the oxide lever costs to buy the same drive", and they differ by
    ~2×. Holding the channel doping fixed lets ``V_t`` sag, so less thinning suffices and the oxide lever
    looks **cheap**; re-adjusting ``V_t`` at every rung (what a fab does) gives ``I ∝ C_ox`` exactly and
    costs about twice as much. The demo headlines the **cheap** one — the reading least favourable to the
    slice it is selling — and reports the other beside it. Flip these and the figure overstates strain.
    """
    r = compute()
    assert r.oxide_decades_to_match < r.oxide_decades_to_match_fixed_vt, (
        "the headlined exchange rate must be the one that flatters the OXIDE lever, not strain"
    )
    assert r.oxide_decades_to_match_fixed_vt / r.oxide_decades_to_match > 1.5   # …and materially so
    # both are real readouts of the drawn curve, not free parameters
    target = r.channel.drive_factor_long_channel
    assert r.oxide_t_ox_matching_um == pytest.approx(
        float(np.interp(target, r.drive_gain_oxide, T_OX_LADDER_UM)))
    assert PERIOD_T_OX_UM / target < r.oxide_t_ox_matching_um < PERIOD_T_OX_UM
    assert r.oxide_decades_to_match_fixed_vt == pytest.approx(
        decades(hk.gate_leakage(PERIOD_T_OX_UM / target, GATE_DIELECTRIC), r.j_gate_A_cm2))
    # …and the whole comparison stays inside the regime B8's ladder is honest in (direct tunnelling)
    assert min(T_OX_LADDER_UM) >= OXIDE_LADDER_FLOOR_UM
    assert V_GS_CITED < hk.DIELECTRICS[GATE_DIELECTRIC].barrier_eV, (
        "the leakage model is a direct-tunnelling one — the supply must sit below the barrier"
    )


def test_the_wired_leg_reaches_the_real_device_and_reads_exactly_the_mobility_factor():
    """The chain the slice exists for: a cited mechanism → ``mu_eff`` → the real long-channel ``I_Dsat``.

    Elasticity **1 by construction** on the ideal-contact path — which is the *reason* the drive read is a
    bound, so it is pinned here on the demo's own device rather than only on a synthetic one.
    """
    r = compute()
    assert r.channel.mechanism == st.TENSILE_CESL.name and r.channel.carrier == st.ELECTRONS
    assert r.i_dsat_strained_A / r.i_dsat_A == pytest.approx(r.channel.mobility_factor, rel=1e-12)
    assert r.i_dsat_strained_A / r.i_dsat_A == pytest.approx(r.channel.drive_factor_long_channel)
    # …and the number the model produces is strictly above what the devices measured. That gap IS the slice.
    assert r.channel.drive_factor_long_channel > r.channel.drive_factor_cited
    assert r.drive_overstatement == pytest.approx(2.0)


def test_the_bound_panel_draws_the_model_line_without_calling_elasticity():
    """The model's diagonal is ``drive == µ``; the cited lines sit strictly under it, and 25 nm under 90.

    :func:`chip.strain.elasticity` **raises** at ``mobility_factor <= 1``, and the axis starts at exactly
    1.0 — so the panel must be built from ``long_channel_drive_factor`` and the cited elasticities, never
    by sweeping the elasticity function itself.
    """
    r = compute()
    assert MU_FACTOR_AXIS[0] == 1.0
    with pytest.raises(ValueError):
        st.elasticity(MU_FACTOR_AXIS[0], 1.0)                       # the trap the panel must not walk into
    assert np.array_equal(r.drive_model, r.mu_axis)                 # I ∝ µ — elasticity 1, exactly
    gain = r.mu_axis > 1.0
    assert np.all(r.drive_cited_90nm[gain] < r.drive_model[gain])
    assert np.all(r.drive_cited_25nm[gain] < r.drive_cited_90nm[gain])   # the bound loosens with L
    # every cited point sits ON its own line — the data and the lines are the same numbers
    for label, mu, drive, _wired in r.cited_points:
        line = r.drive_cited_25nm if "25 nm" in label else r.drive_cited_90nm
        assert float(np.interp(mu, r.mu_axis, line)) == pytest.approx(drive, rel=2e-3), label


def test_the_hole_leg_is_marked_cited_only_and_is_never_computed_as_a_result():
    """The plan's rejected "decoration" option, guarded at the FIGURE level as well as the API level.

    The refusal itself is ``test_strain.py``'s; what this pins is that the demo *carries the refusal*
    rather than paraphrasing it, and that the hole point is flagged unwired everywhere it is drawn — two
    bars side by side would otherwise read as two results the simulator produced.
    """
    r = compute()
    assert st.SIGE_SD.name in r.hole_leg_refused and "n-channel-only" in r.hole_leg_refused
    assert r.wired == ("tensile_cesl",) == st.WIRED_MECHANISMS
    assert WIRED_MECHANISM in r.wired and "sige_sd" not in r.wired
    wired_flags = {label: wired for label, _mu, _d, wired in r.cited_points}
    assert sum(wired_flags.values()) == 1, "exactly one drawn point may claim to be a wired device read"
    assert all("WIRED" in lab if w else "cited" in lab for lab, w in wired_flags.items())
    # …and no drive CURRENT is ever produced for the hole leg, only its cited factor
    with pytest.raises(ValueError):
        st.nmos_mobility(dev.MU_N_EFF, "sige_sd")


def test_the_figure_says_what_the_bound_and_the_composition_are():
    """**The words, pinned** — the claims the fast lane otherwise cannot check.

    Three statements the figure makes in prose and nothing else can verify: that velocity saturation is
    *named, not built* (without it the drive read reads as a result), that the exchange rate is
    recipe-carrying while strain's zero is not, and that **no** 90 nm ``wire_share`` is quoted — F4's
    bulk path refuses below ~0.194 µm, so a number there would be fabricated (the plan's trap #3).
    """
    src = Path(demo_strain_history.__file__).read_text(encoding="utf-8")
    assert "VELOCITY SATURATION IS NAMED, NOT BUILT" in src        # on the figure's own suptitle
    assert "recipe-carrying" in src and "strain's zero does not" in src
    assert "NO wire_share is quoted" in src
    # And the composition really is stated as the law rather than evaluated at 90 nm. Anchored on the
    # IMPORT, not on call-site spellings: a token list ("interconnect.delay", "crossover_width", …) is
    # evadable by aliasing (B9 itself calls the module `ic`), while "the demo cannot reach the wire model
    # at all" is the fact that makes the claim true and there is exactly one way to spell it.
    assert "1 − wire_share" in src
    imports = [ln.strip() for ln in src.splitlines()
               if ln.strip().startswith(("import ", "from "))]        # incl. any lazy in-function import
    assert not any("interconnect" in ln for ln in imports), (
        "the B10 demo must not import chip.interconnect at all — a 90 nm line is deep inside the bulk "
        "path's refusal, so the F4 composition is stated as the exact law and never evaluated. "
        f"Found: {[ln for ln in imports if 'interconnect' in ln]}"
    )


def test_the_era_ENDING_is_read_off_cited_endpoints_and_never_interpolated():
    """S4 on the page: the delivered gain is a bracket, the treadmill is priced, and the model is blind.

    The demo may report the two cited endpoints and the price of holding a gain fixed between them; what
    it may **not** do is put a value *between* them at some other geometry. That would be an
    ``elasticity(L)`` — the elasticity knob the slice refuses to have (plan trap #1.3) — arriving through
    the display layer, which is exactly how S3's flattering-direction composition got in.
    """
    r = compute()
    low, high = r.channel.delivered_drive_bracket
    assert (low, high) == st.delivered_drive_bracket(WIRED_MECHANISM)      # the module owns the pair
    assert r.channel.drive_factor_long_channel > high > low > 1.0          # model > 90 nm > 25 nm
    # the treadmill, from the module's own inverse — the same win costs more mobility one era later
    need_90 = st.mobility_factor_for_drive(st.TENSILE_CESL.drive_factor, st.TENSILE_CESL.cited_elasticity)
    need_25 = st.mobility_factor_for_drive(st.TENSILE_CESL.drive_factor, st.SHORT_CHANNEL_CROSSCHECK)
    assert need_25 > need_90 == pytest.approx(st.TENSILE_CESL.mobility_factor)

    src = Path(demo_strain_history.__file__).read_text(encoding="utf-8")
    assert "not a curve fitted between them" in src                        # the figure says so, in words
    assert "at EVERY L" in src
    # Code-shaped tokens only — the demo's own prose names `elasticity(L)` in order to reject it, so a
    # blacklist that matched the phrase would fire on the sentence doing the right thing.
    for banned in ("np.interp(st.", "interp(mu_axis", "elasticity_at(", "fit_elasticity"):
        assert banned not in src, f"the demo must not interpolate between the cited endpoints: {banned}"
    # the one np.interp in this demo is B8's OXIDE ladder readout — a curve the demo itself computed —
    # and there must still be exactly one, so a second interpolation cannot arrive unnoticed.
    assert src.count("np.interp(") == 1


def test_figure_builds():
    r = compute()
    pytest.importorskip("matplotlib")               # the figure is not in the correctness path (ADR 0002)
    from chip.demo_strain_history import save_figure
    assert save_figure(r).is_file()
