"""A2 wiring — the OSF radial gradient flows recipe → per-die D₀(r) → the G3 defect map.

The physics (the radial ``G(r)`` profile + the ring location + the topology signs) is pinned in
``chip/tests/test_czochralski.py``; this localizes the **fab_game wiring** (so a future regression
points at the knob, not the demo): the default (no radial boost) is the CG-2 seam, the radial profile
makes the grown-in killer density **per die** keyed on ``radius_frac`` (a COP-degraded vacancy core /
clean interstitial rim), the pipeline scatters that per-die density through the **same** G3 Poisson map, and
the misconfigurations (radial without a centre ``G`` / a pull, or radial mixed with CG-3) raise.

THE finding under test (the build's headline): the void density is monotone in ξ, so the kills cluster
in the high-ξ **centre** and the rim is provably clean — the OSF ring is the *boundary* where the
vacancy-core kills **stop**, not a ring of kills.
"""
from __future__ import annotations

import pytest

from chip.czochralski import osf_ring_radius as chip_osf_ring_radius
from fab_game.pipeline import run_line
from fab_game.recipe import CzochralskiKnobs, Recipe, WaferPrepKnobs
from fab_game.variation import Variation

# Defects-only variation: the ONLY stochastic effect is the killer-defect scatter (so the radial COPs
# actually land), the device physics is the clean nominal — isolating the A2 wiring (as test_voronkov).
_DEFECTS_ONLY = Variation(enabled=True, focus_tilt_nm=0.0, t_ox_edge_frac=0.0,
                          focus_sigma_nm=0.0, cd_sigma_nm=0.0, t_ox_sigma_frac=0.0)

# A (V, G_center, boost) with the V/I ring ON-wafer: ξ(0)=V/G_center=0.25 > ξ_t > ξ(1) (interstitial).
_V, _GC, _BOOST = 2.0, 8.0, 2.0


def _prep_record(wafer):
    return next(r for r in wafer.provenance if r.step == "wafer_prep")


def test_default_no_radial_boost_is_the_seam():
    """No radial boost (the default) → the OSF ring is off: not radial, no ring, and the per-die density
    falls back to the uniform CG-2 value for every radius (the seam the G1–G7 demos ride)."""
    cz = Recipe().czochralski
    assert cz.radial_gradient_boost is None
    assert cz.is_osf_radial is False
    assert cz.osf_ring_radius is None
    assert cz.osf_zone_regimes is None
    # Per-die density == the uniform scalar (0.0 here) for any radius — radius-independent (the seam).
    for r in (0.0, 0.4, 1.0):
        assert cz.grown_in_defect_density_at(r) == cz.grown_in_defect_density == 0.0


def test_uniform_cg2_unchanged_when_radial_off():
    """A uniform CG-2 growth (thermal gradient set, radial boost OFF) is unchanged: the per-die density
    is the single CG-2 value at every radius (no radial profile) — A2 does not perturb CG-2."""
    cz = CzochralskiKnobs(pull_rate_mm_min=3.0, thermal_gradient_K_per_mm=3.5)   # V/G≈0.857 > ξ_t
    assert cz.is_osf_radial is False
    uniform = cz.grown_in_defect_density
    assert uniform > 0.0
    for r in (0.0, 0.5, 1.0):
        assert cz.grown_in_defect_density_at(r) == uniform                       # radius-independent


def test_radial_requires_center_gradient_and_pull():
    """The radial profile reinterprets ``thermal_gradient_K_per_mm`` as ``G_center`` and forms ξ=V/G(r),
    so it needs both that centre ``G`` and a pull rate — the misconfigurations raise (they do not
    silently treat the gradient/pull as absent)."""
    no_g = CzochralskiKnobs(pull_rate_mm_min=_V, radial_gradient_boost=_BOOST)    # no centre G
    with pytest.raises(ValueError):
        _ = no_g.grown_in_defect_density_at(0.0)
    with pytest.raises(ValueError):
        _ = no_g.osf_ring_radius
    no_v = CzochralskiKnobs(thermal_gradient_K_per_mm=_GC, radial_gradient_boost=_BOOST)  # no pull
    with pytest.raises(ValueError):
        _ = no_v.grown_in_defect_density_at(0.0)


def test_radial_incompatible_with_cg3_melt_gradient():
    """The radial profile is the CG-2 *direct* ``G`` made radial — mixing it with CG-3's Stefan-derived
    ``melt_gradient_K_per_mm`` is a misconfiguration (a Stefan ``G`` is a single number, not a profile),
    so it raises (the two-``G`` guard, like CzochralskiKnobs' existing CG-2↔CG-3 guard)."""
    cz = CzochralskiKnobs(pull_rate_mm_min=_V, thermal_gradient_K_per_mm=_GC,
                          melt_gradient_K_per_mm=3.0, radial_gradient_boost=_BOOST)
    with pytest.raises(ValueError):
        _ = cz.grown_in_defect_density_at(0.0)
    with pytest.raises(ValueError):
        _ = cz.osf_ring_radius


def test_radial_density_is_per_die_vacancy_core_clean_rim():
    """The radial profile makes the grown-in density per die: the vacancy core (small r) catches COPs,
    the interstitial rim (large r) is provably clean (0 at/beyond the ring) → the edge-vs-centre yield
    non-uniformity. The ring radius + topology match the pinned chip physics."""
    cz = CzochralskiKnobs(pull_rate_mm_min=_V, thermal_gradient_K_per_mm=_GC, radial_gradient_boost=_BOOST)
    assert cz.is_osf_radial is True
    ring = cz.osf_ring_radius
    assert ring == chip_osf_ring_radius(_V, _GC, boost=_BOOST)                    # the pinned location
    assert 0.0 < ring < 1.0
    assert cz.osf_zone_regimes == ("vacancy", "interstitial")                     # topology signs
    # Density falls with radius (a by-construction guard, NOT an anchor): centre > 0, rim exactly 0.
    dens = [cz.grown_in_defect_density_at(r) for r in (0.0, 0.25, 0.5, 0.75, 1.0)]
    assert dens[0] > 0.0                                                          # COP-degraded vacancy core
    assert dens[-1] == 0.0                                                        # clean interstitial rim
    assert all(a >= b for a, b in zip(dens, dens[1:]))                            # monotone non-increasing
    # The zero-crossing is the ring: just inside kills, at/outside is clean.
    assert cz.grown_in_defect_density_at(ring * 0.99) > 0.0
    assert cz.grown_in_defect_density_at(ring) == pytest.approx(0.0, abs=1e-12)


def test_radial_scatter_kills_the_core_and_spares_the_rim():
    """The consequence end-to-end on a clean line: a radial growth scatters COPs that kill dies **only in
    the vacancy core** — every killed die sits inside the ring radius (the rim has zero grown-in density,
    so it is never drawn), and kills do happen. The edge-vs-centre non-uniformity made physical."""
    cz = CzochralskiKnobs(pull_rate_mm_min=_V, thermal_gradient_K_per_mm=_GC, radial_gradient_boost=_BOOST)
    r = Recipe(czochralski=cz, wafer_prep=WaferPrepKnobs(defect_density=0.0))     # clean line: COPs only
    ring = cz.osf_ring_radius
    total_core_kills = 0
    for seed in range(10):
        w = run_line(r, seed=seed, variation=_DEFECTS_ONLY, grid_n=7)
        killed = [d for d in w.dies if d.killed_by_defect]
        # The rim is provably clean — no die at/beyond the ring is ever killed by a grown-in COP.
        assert all(d.radius_frac < ring for d in killed), \
            f"a rim die (r ≥ {ring:.3f}) was killed — the interstitial rim must stay clean"
        total_core_kills += len(killed)
    assert total_core_kills > 0                                                   # kills do cluster in the core


def test_radial_provenance_records_the_ring():
    """The wafer-prep provenance carries the radial story (ring radius + centre/edge topology + centre/edge
    density) so the map's non-uniformity is legible — not silently read as a uniform fab-floor level."""
    cz = CzochralskiKnobs(pull_rate_mm_min=_V, thermal_gradient_K_per_mm=_GC, radial_gradient_boost=_BOOST)
    w = run_line(Recipe(czochralski=cz), seed=0, variation=_DEFECTS_ONLY, grid_n=7)
    summary = _prep_record(w).summary
    assert summary["osf_ring_radius"] == pytest.approx(cz.osf_ring_radius)
    assert summary["osf_zone_regimes"] == ("vacancy", "interstitial")
    assert summary["grown_in_density_center"] > summary["grown_in_density_edge"] == 0.0


def test_radial_all_interstitial_is_clean_no_ring():
    """A slow pull / hot zone where even the centre is interstitial (ξ(0) ≤ ξ_t): no ring on-wafer (None),
    both zones interstitial, and zero grown-in density everywhere → the line is clean (the criterion gates
    the cost radially too, the seam holds with A2 on)."""
    cz = CzochralskiKnobs(pull_rate_mm_min=1.0, thermal_gradient_K_per_mm=20.0, radial_gradient_boost=_BOOST)
    assert cz.osf_ring_radius is None
    assert cz.osf_zone_regimes == ("interstitial", "interstitial")
    assert cz.grown_in_defect_density_at(0.0) == 0.0
    r = Recipe(czochralski=cz, wafer_prep=WaferPrepKnobs(defect_density=0.0))
    w = run_line(r, seed=0, variation=_DEFECTS_ONLY, grid_n=7)
    assert sum(d.killed_by_defect for d in w.dies) == 0                           # nothing grown-in kills
