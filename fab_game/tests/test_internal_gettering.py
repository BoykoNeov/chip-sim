"""S4 wiring — internal gettering: crucible oxygen's DUAL-USE (donors-bad vs gettering-good, one device).

The physics is pinned in ``chip/tests/test_{czochralski,purification}.py`` (the gettering efficiency +
``getter_metals``); this localizes the **fab_game wiring** of the dual-use into the device step. The
two empirical gates the slice rests on (verified the way phase-5's two-sided window was):

1. **The two-sided window exists** on the single ``[O_i]`` axis (a finished-wafer Goldilocks): too little
   oxygen → the deep-level metals are not gettered → a **leakage** fail; too much → thermal donors crater
   ``V_t`` → a **V_t** fail; a middle band passes both. The fail *reason* is leakage just below the band
   and V_t just above — not the same reason on both ends (that would be a one-sided window).
2. **The trade-off is real** — the *same* oxygen moves leakage DOWN (gettering) and ``V_t`` DOWN (donors)
   on **orthogonal** channels: gettering touches Fe/Cu only, so with the donors switched off it lowers
   leakage with ``V_t`` byte-for-byte; raising oxygen then costs ``V_t`` through the donors (§1e).

Plus the seams: the master seam (no oxygen ⇒ no gettering, no donors ⇒ byte-for-byte) and the preserved
C1 seam (oxygen with neither anneal ⇒ ``N_TD = 0``), and the non-skippable forming-gas sinter.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from fab_game import DEFAULT_RECIPE, NO_VARIATION, diagnose, run_line
from fab_game.recipe import CzochralskiKnobs, PurificationKnobs, Recipe

FORMING_GAS_MIN = 30.0


def _trace_recipe(oxygen, *, forming_gas=FORMING_GAS_MIN, donor_anneal=0.0):
    """A trace-metal (moderate-contamination) wafer at this incorporated ``[O_i]`` + the forming-gas sinter."""
    return replace(
        DEFAULT_RECIPE,
        purification=PurificationKnobs(grade="trace-metal", zone_passes=1),
        czochralski=replace(DEFAULT_RECIPE.czochralski, oxygen_conc_cm3=oxygen,
                            forming_gas_anneal_min=forming_gas, thermal_donor_anneal_min=donor_anneal),
    )


def _center(recipe):
    return run_line(recipe, variation=NO_VARIATION, grid_n=1).dies[0]


# --------------------------------------------------------------------------- #
# Gate 1 — the two-sided window (leakage below, V_t above; the dual-use Goldilocks)
# --------------------------------------------------------------------------- #
def test_low_oxygen_fails_on_leakage_the_metals_are_not_gettered():
    # Below the band: the trace-metal feed is leaky and the oxygen is too low to precipitate enough to
    # getter it → a LEAKAGE scrap (V_t is comfortably in spec — the metals' device effect net doping
    # cannot carry).
    d = _center(_trace_recipe(8.0e17))
    assert d.verdict.failed
    assert any("leakage" in r for r in d.verdict.reasons)
    assert not any("V_t" in r for r in d.verdict.reasons)        # not a threshold fail down here
    assert 0.45 <= d.V_t <= 0.68


def test_high_oxygen_fails_on_vt_the_donors_crater_the_threshold():
    # Above the band: enough oxygen to getter the metals (leakage now fine), but the same oxygen makes
    # thermal donors at the forming-gas sinter that compensate the substrate → a V_t scrap (the bad face).
    d = _center(_trace_recipe(1.2e18))
    assert d.verdict.failed
    assert any("V_t" in r for r in d.verdict.reasons)
    assert not any("leakage" in r for r in d.verdict.reasons)    # leakage is gettered down here
    assert d.j_leak_nA_cm2 <= 10.0


def test_mid_oxygen_passes_both_the_goldilocks_band():
    # The interior optimum: a middle [O_i] getters the metals (leakage in spec) without yet cratering V_t
    # (donors still modest) — both windows pass. The proof the two-sided window is non-empty.
    d = _center(_trace_recipe(1.0e18))
    assert not d.verdict.failed
    assert 0.45 <= d.V_t <= 0.68 and d.j_leak_nA_cm2 <= 10.0


def test_window_is_genuinely_two_sided_not_one_reason_on_both_ends():
    # The signature of a real Goldilocks (vs a one-sided cliff): the fail reason FLIPS across the band —
    # leakage on the low edge, V_t on the high edge.
    low = _center(_trace_recipe(8.0e17))
    high = _center(_trace_recipe(1.2e18))
    low_leak = any("leakage" in r for r in low.verdict.reasons)
    high_vt = any("V_t" in r for r in high.verdict.reasons)
    assert low_leak and high_vt
    assert {("leak" if low_leak else "vt"), ("vt" if high_vt else "leak")} == {"leak", "vt"}


# --------------------------------------------------------------------------- #
# Gate 2 — the trade-off is real, on orthogonal channels (gettering ⊥ donors)
# --------------------------------------------------------------------------- #
def test_gettering_lowers_leakage_with_vt_byte_for_byte_when_donors_off():
    # The orthogonality (the dual-use's load-bearing claim): with the donor anneals OFF (no forming gas,
    # no donor anneal) so NO donors form, engaging oxygen getters the metals → leakage drops while V_t is
    # bit-for-bit the no-oxygen value (gettering touches Fe/Cu only, never the Na→Q_ox→V_t chain).
    no_o = _center(_trace_recipe(None, forming_gas=0.0))
    getter = _center(_trace_recipe(1.2e18, forming_gas=0.0, donor_anneal=0.0))
    assert getter.V_t == no_o.V_t                                # V_t byte-for-byte under pure gettering
    assert getter.j_leak < no_o.j_leak                           # leakage genuinely fell


def test_more_oxygen_costs_vt_through_the_donors():
    # The other channel: at a fixed forming-gas sinter, more oxygen makes more donors → a LOWER V_t. The
    # cost side of the trade (the gettering benefit is the previous test).
    vts = [_center(_trace_recipe(O)).V_t for O in (8.0e17, 1.0e18, 1.2e18)]
    assert vts == sorted(vts, reverse=True)                      # V_t falls monotonically as oxygen rises


def test_leakage_falls_with_oxygen_across_the_verdict_relevant_range():
    # Across the in-play oxygen levels (no oxygen → the gettering band → the V_t crater) leakage falls
    # monotonically — the gettering benefit. (The over-precipitation U-shape is the explicitly deferred
    # denuded-zone-collapse edge, not modelled; a *separate*, real secondary donor→N_A→depletion-width
    # rise exists but only deep in already-failed territory — see test_demo_internal_gettering.)
    leaks = [_center(_trace_recipe(O)).j_leak for O in (None, 7e17, 8e17, 9e17, 1.0e18, 1.2e18)]
    assert leaks == sorted(leaks, reverse=True)


# --------------------------------------------------------------------------- #
# Seams — the master seam, the preserved C1 seam, and the non-skippable sinter
# --------------------------------------------------------------------------- #
def test_no_oxygen_is_the_master_seam_byte_for_byte():
    # No oxygen ⇒ no gettering AND no donors ⇒ the device is byte-for-byte the pre-S4 run (the trace-metal
    # leakage and V_t both unchanged from the no-oxygen wafer; the getter_eff record key is absent).
    base = _center(_trace_recipe(None))
    again = _center(replace(_trace_recipe(None),
                            czochralski=replace(DEFAULT_RECIPE.czochralski, forming_gas_anneal_min=0.0)))
    assert (again.V_t, again.i_dsat, again.j_leak) == (base.V_t, base.i_dsat, base.j_leak)
    rec = next(r for r in base.history if r.step == "device")
    assert "getter_eff" not in rec.knobs_in                      # no S4 fingerprint when oxygen is off


def test_default_recipe_unchanged_by_the_new_fields():
    # The headline seam: DEFAULT_RECIPE (oxygen None, forming_gas default 0) is byte-for-byte the pre-S4
    # line — the G1–G7 banked demos ride this.
    d0 = run_line(DEFAULT_RECIPE, variation=NO_VARIATION, grid_n=1).dies[0]
    d1 = run_line(replace(DEFAULT_RECIPE,
                          czochralski=replace(DEFAULT_RECIPE.czochralski, forming_gas_anneal_min=0.0)),
                  variation=NO_VARIATION, grid_n=1).dies[0]
    assert (d1.V_t, d1.i_dsat, d1.j_leak, d1.bv_V) == (d0.V_t, d0.i_dsat, d0.j_leak, d0.bv_V)


def test_c1_seam_preserved_oxygen_with_neither_anneal_is_no_donors():
    # The C1 seam still holds exactly: oxygen incorporated but NEITHER the donor anneal NOR the forming-gas
    # sinter (both 0) ⇒ N_TD = 0 (donors form at an anneal, not during growth) — the new field defaults to
    # 0 so it does not silently floor the donor budget.
    r = Recipe(czochralski=CzochralskiKnobs(oxygen_conc_cm3=1.2e18,
                                            thermal_donor_anneal_min=0.0, forming_gas_anneal_min=0.0))
    assert r.czochralski.thermal_donor_density == 0.0
    assert r.effective_channel_N_A == 1.0e17                      # substrate unchanged (exact)


def test_forming_gas_sinter_makes_the_donor_cost_non_skippable():
    # The hatch the design closes: the universal final ~450 °C forming-gas/sinter sits in the thermal-donor
    # window, so engaging oxygen carries donors EVEN with the deliberate donor anneal at 0 — you cannot
    # getter for free (that is what makes the high-oxygen V_t cost real).
    cz = CzochralskiKnobs(oxygen_conc_cm3=1.2e18, thermal_donor_anneal_min=0.0,
                          forming_gas_anneal_min=FORMING_GAS_MIN)
    assert cz.thermal_donor_density > 0.0                         # donors formed at the sinter alone
    assert cz.internal_gettering_efficiency > 0.0                 # and the same oxygen getters


# --------------------------------------------------------------------------- #
# Diagnosis — the dual-use is named in the failure trail
# --------------------------------------------------------------------------- #
def test_diagnosis_names_the_gettering_trade_off_on_a_leaky_under_oxygenated_die():
    # A die just below the band (oxygen on, gettering partial, still leaky) → the trail names the dual-use
    # trade-off (raise [O_i] to getter more, but watch the donor V_t cost), not a bare "purify harder".
    text = diagnose(_center(_trace_recipe(8.0e17))).lower()
    assert "getter" in text
    assert "trade-off" in text or "donor" in text


def test_diagnosis_names_the_donors_on_the_over_oxygenated_vt_scrap():
    # The high-oxygen V_t scrap is the C1 donor fingerprint (the bad face) — the forming-gas donors are
    # named as the V_t root cause.
    text = diagnose(_center(_trace_recipe(1.2e18))).lower()
    assert "thermal donor" in text and "v_t" in text
