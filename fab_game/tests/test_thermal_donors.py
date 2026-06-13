"""C1 wiring — crucible oxygen + the ~450 °C anneal flow recipe → N_TD → net N_A → V_t; default is the seam.

The physics (the Kaiser–Frisch–Reiss fourth-power rate + the flagged saturating form) is pinned in
``chip/tests/test_czochralski.py``; this localizes the **fab_game wiring** (so a future regression points
at the knob, not the demo): the default knobs reproduce the pre-C1 substrate (oxygen off OR no anneal →
``N_TD=0`` → the seam), and a set oxygen + donor anneal compensates the substrate down end-to-end →
a lower ``V_t`` (and higher resistivity) on the real pipeline. Mutual with the residual-dopant (G4a)
shift — both ride the one ``effective_channel_N_A`` net-doping currency.
"""
from __future__ import annotations

import pytest

from chip.czochralski import thermal_donor_density
from fab_game import DEFAULT_RECIPE, NO_VARIATION, diagnose, run_line, wafer_yield
from fab_game.recipe import CzochralskiKnobs, Recipe


def _center(wafer):
    return wafer.dies[0]


def test_default_no_oxygen_is_the_seam():
    """No oxygen set (the default) → no thermal donors regardless of anneal → ``effective_channel_N_A`` is
    the boule slice exactly (the seam the G2–G7 demos ride, byte-for-byte the pre-C1 substrate)."""
    r = Recipe()
    assert r.czochralski.oxygen_conc_cm3 is None
    assert r.czochralski.thermal_donor_density == 0.0
    assert r.effective_channel_N_A == 1.0e17                    # exact — the seed-slice substrate, unchanged
    assert r.effective_channel_N_A == DEFAULT_RECIPE.effective_channel_N_A


def test_oxygen_without_anneal_is_the_seam():
    """Oxygen incorporated but NO donor anneal → ``N_TD=0`` exactly (donors form at the anneal, not during
    growth) → the substrate is unchanged (the second seam path)."""
    r = Recipe(czochralski=CzochralskiKnobs(oxygen_conc_cm3=1.2e18, thermal_donor_anneal_min=0.0))
    assert r.czochralski.thermal_donor_density == 0.0
    assert r.effective_channel_N_A == 1.0e17                    # exact seam — oxygen alone does nothing


def test_oxygen_plus_anneal_compensates_the_substrate_and_lowers_vt():
    """Oxygen + a ~450 °C anneal flows recipe → N_TD → net N_A → V_t: the donors compensate the substrate
    (lower net N_A) and the device V_t drops below the clean baseline (the wiring end-to-end)."""
    O, t = 8.0e17, 120.0
    expected_ntd = thermal_donor_density(O, t)
    r = Recipe(czochralski=CzochralskiKnobs(oxygen_conc_cm3=O, thermal_donor_anneal_min=t))
    assert r.czochralski.thermal_donor_density == expected_ntd          # recipe → N_TD
    assert r.effective_channel_N_A == pytest.approx(1.0e17 - expected_ntd)  # N_TD → net N_A (exact compensation)
    clean = run_line(DEFAULT_RECIPE, variation=NO_VARIATION, grid_n=1)
    doped = run_line(r, variation=NO_VARIATION, grid_n=1)
    assert _center(doped).V_t < _center(clean).V_t                       # donors push V_t down
    # The substrate resistivity rises (less net acceptor) — coherent with the doping the device sees.
    assert r.substrate_resistivity_ohm_cm > DEFAULT_RECIPE.substrate_resistivity_ohm_cm


def test_high_oxygen_long_anneal_scraps_via_the_vt_floor():
    """A high [O_i] + a long anneal walks V_t out the BOTTOM of its window → a scrap — without inverting
    the type (the demo's scrap path; the device stays p-type, the guarded inversion edge untouched)."""
    r = Recipe(czochralski=CzochralskiKnobs(oxygen_conc_cm3=1.2e18, thermal_donor_anneal_min=240.0))
    assert r.effective_channel_N_A > 0.0                                # still p-type (no inversion)
    w = run_line(r, variation=NO_VARIATION, grid_n=1)
    d = _center(w)
    assert d.verdict.failed and any("V_t" in reason for reason in d.verdict.reasons)
    assert wafer_yield(w) == 0.0


def test_diagnosis_names_the_thermal_donors():
    """The failure trail names the thermal-donor compensation as the V_t root cause (the C1 fingerprint —
    the 'why did this die?'), and a clean run does NOT mention donors."""
    r = Recipe(czochralski=CzochralskiKnobs(oxygen_conc_cm3=1.2e18, thermal_donor_anneal_min=240.0))
    text = diagnose(_center(run_line(r, variation=NO_VARIATION, grid_n=1)))
    assert "thermal donor" in text.lower()
    clean_text = diagnose(_center(run_line(DEFAULT_RECIPE, variation=NO_VARIATION, grid_n=1)))
    assert "thermal donor" not in clean_text.lower()           # no donor line on a clean (passing) die


def test_overcompensation_inversion_raises_the_guarded_edge():
    """Driving the donors past the substrate doping (type inversion) raises — the compact p-substrate
    device does not model an n-channel device (keep oxygen/anneal in the p-type range)."""
    r = Recipe(czochralski=CzochralskiKnobs(N_seed=1.0e16, oxygen_conc_cm3=1.2e18,
                                            thermal_donor_anneal_min=600.0))
    with pytest.raises(ValueError):
        _ = r.effective_channel_N_A
