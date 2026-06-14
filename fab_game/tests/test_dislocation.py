"""A1 wiring — the interstitial side of Voronkov: grown-in dislocations → junction leakage.

The A1 mechanics (ADR 0005 §5, the flagged-phenomenology tier — like CG-2/A2, NO conservation law,
NO engine): a too-slow Czochralski pull (``ξ < ξ_t``) freezes in **interstitial-rich** silicon →
grown-in **dislocations** (:func:`chip.czochralski.dislocation_defect_density`), which are
recombination centres → they raise the junction **leakage** (the G4b :mod:`chip.lifetime` channel,
``1/τ += K·ρ_disl``), **not** the Poisson yield map. So the Voronkov criterion becomes **two-sided**:
too-fast costs yield (CG-2 COP voids), too-slow costs leakage (A1 dislocations), the optimum **at**
``ξ_t``. There is **no new knob** — A1 reads the existing ``(V, G)`` and switches on automatically on
the interstitial side; it is ``0`` (the seam) for any vacancy/boundary growth or with CG-2 off.

Runs use ``NO_VARIATION`` so the growth is the only signal — and unlike the void/yield channel (which
needs the stochastic scatter), the dislocation **leakage** is deterministic per die, so the leaky
interstitial wafer / rim shows directly.
"""
from __future__ import annotations

import pytest

from chip.czochralski import (
    VORONKOV_CRITICAL_RATIO,
    dislocation_defect_density,
    voronkov_ratio,
)

from fab_game import (
    DEFAULT_RECIPE, NO_VARIATION, CzochralskiKnobs, Recipe, run_line, wafer_yield,
)
from fab_game.pipeline import diagnose, rework_litho

# A deliberately slow / over-steep-G pull: ξ = V/G = 1/20 = 0.05 < ξ_t → interstitial (whole wafer).
_SLOW = CzochralskiKnobs(pull_rate_mm_min=1.0, thermal_gradient_K_per_mm=20.0)
# A vacancy-side pull (ξ = 3/3.5 ≈ 0.857 > ξ_t) — the CG-2 side: voids, no dislocations.
_FAST = CzochralskiKnobs(pull_rate_mm_min=3.0, thermal_gradient_K_per_mm=3.5)


def _run(cz: CzochralskiKnobs, gn: int = 3):
    return run_line(Recipe(czochralski=cz), seed=0, variation=NO_VARIATION, grid_n=gn)


# --------------------------------------------------------------------------- #
# The recipe property (the interstitial mirror of grown_in_defect_density)
# --------------------------------------------------------------------------- #
def test_interstitial_density_off_and_vacancy_are_zero_the_seam():
    # No CG-2 (the default) → 0; a vacancy-side growth → 0 (dislocations are the interstitial side only).
    assert DEFAULT_RECIPE.czochralski.interstitial_dislocation_density == 0.0
    assert _FAST.interstitial_dislocation_density == 0.0
    assert _FAST.grown_in_defect_density > 0.0           # …it pays on the VOID/yield side instead


def test_interstitial_density_matches_the_cited_function():
    # The interstitial-side growth reads dislocation_defect_density(ξ) — the chip-layer mirror.
    xi = voronkov_ratio(_SLOW.pull_rate_mm_min, _SLOW.thermal_gradient_K_per_mm)
    assert xi < VORONKOV_CRITICAL_RATIO                  # genuinely interstitial
    assert _SLOW.interstitial_dislocation_density == dislocation_defect_density(xi) > 0.0
    assert _SLOW.grown_in_defect_density == 0.0          # …and pays NOTHING on the void/yield side


# --------------------------------------------------------------------------- #
# The uniform two-sided window — a slow pull leaks the diode (V_t untouched)
# --------------------------------------------------------------------------- #
def test_slow_pull_leaks_the_diode_out_of_spec_and_V_t_is_bitexact():
    clean = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=3)
    slow = _run(_SLOW)
    j_clean = next(d.j_leak_nA_cm2 for d in clean.dies if d.j_leak is not None)
    j_slow = next(d.j_leak_nA_cm2 for d in slow.dies if d.j_leak is not None)
    assert j_slow > j_clean                              # the slow pull raises leakage…
    assert wafer_yield(slow) == 0.0                      # …out of the spec window (uniform wafer)
    assert wafer_yield(slow) < wafer_yield(clean)
    dead = next(d for d in slow.dies if d.verdict.failed)
    assert any("leakage" in r for r in dead.verdict.reasons)        # the parametric cause is leakage…
    assert not any("V_t" in r for r in dead.verdict.reasons)        # …NOT V_t (slow pull doesn't move it)
    # V_t reads the clean value BIT-FOR-BIT — the dislocation leakage is the consequence net doping
    # cannot carry (the same isolation as the deep-level metals, G4b).
    assert dead.V_t == next(d.V_t for d in clean.dies if d.V_t is not None)


def test_failure_trail_names_grown_in_dislocations_not_metals():
    slow = _run(_SLOW)
    dead = next(d for d in slow.dies if d.verdict.failed)
    trail = diagnose(dead)
    assert "leakage" in trail and "DISLOCATION" in trail            # named as a crystal-growth dislocation cause
    assert "interstitial" in trail and "ξ < ξ_t" in trail
    assert "deep-level-metal" not in trail and "Q_ox" not in trail  # NOT the metal/Na story


def test_two_sided_window_vacancy_costs_yield_interstitial_costs_leakage():
    # The A1 payoff: the criterion is now two-sided. The vacancy pull pays on the VOID/yield density
    # (and leaves leakage at baseline); the interstitial pull pays on LEAKAGE (and leaves the void
    # density at zero). At ξ_t both are zero — the defect-free optimum.
    fast = _run(_FAST)
    slow = _run(_SLOW)
    j_fast = next(d.j_leak_nA_cm2 for d in fast.dies if d.j_leak is not None)
    j_slow = next(d.j_leak_nA_cm2 for d in slow.dies if d.j_leak is not None)
    assert _FAST.grown_in_defect_density > 0.0 and _FAST.interstitial_dislocation_density == 0.0
    assert _SLOW.grown_in_defect_density == 0.0 and _SLOW.interstitial_dislocation_density > 0.0
    assert j_fast < 1.0 < j_slow                         # vacancy: baseline leakage; interstitial: high


# --------------------------------------------------------------------------- #
# The radial completion — A2's interstitial RIM is dislocation-leaky (A1 is its consumer)
# --------------------------------------------------------------------------- #
# A radial recipe with the V/I ring on-wafer: vacancy core (voids) + interstitial rim (dislocations).
_RADIAL = CzochralskiKnobs(pull_rate_mm_min=2.0, thermal_gradient_K_per_mm=5.0, radial_gradient_boost=6.0)


def test_radial_rim_is_dislocation_leaky_core_is_clean_of_dislocations():
    cz = _RADIAL
    assert cz.osf_zone_regimes == ("vacancy", "interstitial")       # core vacancy, rim interstitial
    assert cz.interstitial_dislocation_density_at(0.0) == 0.0        # the vacancy CORE has no dislocations
    assert cz.interstitial_dislocation_density_at(1.0) > 0.0         # the interstitial RIM does
    ring = cz.osf_ring_radius
    assert cz.interstitial_dislocation_density_at(ring) == pytest.approx(0.0, abs=1e-6)  # zero AT the ring
    # On the wafer (NO_VARIATION → the void core is not scattered, so only the leaky rim fails): every
    # failed die sits in the interstitial rim (past the ring) and fails on leakage.
    w = run_line(Recipe(czochralski=cz), seed=0, variation=NO_VARIATION, grid_n=7)
    leaked = [d for d in w.dies if d.verdict.failed]
    assert leaked, "the dislocation-leaky rim should fail some dies"
    for d in leaked:
        assert d.radius_frac > ring                                 # only the rim
        assert any("leakage" in r for r in d.verdict.reasons)       # …on leakage
    # The ring annulus is the one clean of BOTH: a die just inside the ring is dislocation-free and a
    # die there passes (baseline leakage), so the kills are the rim, not the boundary.
    inside = [d for d in w.dies if d.radius_frac < ring and d.j_leak is not None]
    assert all(d.j_leak_nA_cm2 < 1.0 for d in inside)               # core/ring: baseline leakage


def test_radial_provenance_records_the_leaky_rim():
    w = run_line(Recipe(czochralski=_RADIAL), seed=0, variation=NO_VARIATION, grid_n=7)
    prep = next(r for r in w.provenance if r.step == "wafer_prep")
    assert prep.summary["dislocation_density_center"] == 0.0        # vacancy core: no dislocations
    assert prep.summary["dislocation_density_edge"] > 0.0           # interstitial rim: dislocations
    assert prep.summary["osf_zone_regimes"] == ("vacancy", "interstitial")


# --------------------------------------------------------------------------- #
# The second device_step site — rework cannot un-grow dislocations
# --------------------------------------------------------------------------- #
def test_rework_cannot_recover_a_dislocation_leaky_die():
    # Grown-in dislocations persist through a front-end re-expose (you cannot rework the crystal), so a
    # leaky die stays leaky after rework — which only holds if the rework device_step also threads the
    # dislocation density (the second call site). A regression guard for that wiring.
    slow = _run(_SLOW)
    assert wafer_yield(slow) == 0.0
    reworked = rework_litho(slow, Recipe(czochralski=_SLOW), variation=NO_VARIATION,
                            focus_correction_nm=0.0)
    assert wafer_yield(reworked) == 0.0                             # still leaky — rework can't fix the pull
    dead = next(d for d in reworked.dies if d.verdict.failed)
    assert any("leakage" in r for r in dead.verdict.reasons)
