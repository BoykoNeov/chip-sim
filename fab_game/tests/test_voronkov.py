"""CG-2 wiring — the Voronkov V/G knob flows recipe → grown-in COP density → the G3 defect map.

The physics (the Voronkov criterion + the flagged void density) is pinned in
``chip/tests/test_czochralski.py``; this localizes the **fab_game wiring** (so a future regression
points at the knob, not the demo): the default (no thermal gradient) adds nothing to the wafer-prep
killer density (the G3 seam), an *interstitial*-regime growth still adds nothing (the criterion
gates the cost), and a *vacancy*-regime growth adds the cited void density to the **same** Poisson
defect map the pipeline scatters.
"""
from __future__ import annotations

import numpy as np
import pytest

from chip.czochralski import (
    VORONKOV_CRITICAL_RATIO,
    void_defect_density,
    voronkov_ratio,
)

from fab_game.pipeline import run_line
from fab_game.recipe import CzochralskiKnobs, Recipe, WaferPrepKnobs
from fab_game.variation import Variation

# An enabled variation with the physics channels zeroed: the ONLY stochastic effect is the killer-
# defect scatter (so a vacancy growth's grown-in COPs actually land), and the device physics is the
# clean nominal — isolating the CG-2 defect wiring.
_DEFECTS_ONLY = Variation(enabled=True, focus_tilt_nm=0.0, t_ox_edge_frac=0.0,
                          focus_sigma_nm=0.0, cd_sigma_nm=0.0, t_ox_sigma_frac=0.0)


def _prep_record(wafer):
    return next(r for r in wafer.provenance if r.step == "wafer_prep")


def test_default_no_thermal_gradient_is_the_cg2_seam():
    """No thermal gradient set (the default) → CG-2 is off: no Voronkov ratio, no grown-in density, and
    the effective killer density is exactly the wafer-prep particle level (``+ 0.0`` — the G3 seam)."""
    r = Recipe()
    assert r.czochralski.thermal_gradient_K_per_mm is None
    assert r.czochralski.voronkov_ratio is None
    assert r.czochralski.grown_in_defect_regime is None
    assert r.czochralski.grown_in_defect_density == 0.0
    assert r.effective_defect_density == r.wafer_prep.defect_density   # + 0.0, byte-for-byte


def test_thermal_gradient_without_pull_rate_raises():
    """A gradient with no pull rate cannot form ``V/G`` — the misconfiguration raises, it does not
    silently treat the pull as zero (CG-1's ``None`` means 'well-mixed', not literally 0 mm/min)."""
    cz = CzochralskiKnobs(thermal_gradient_K_per_mm=4.0)              # pull_rate_mm_min left None
    with pytest.raises(ValueError):
        _ = cz.voronkov_ratio
    with pytest.raises(ValueError):
        _ = cz.grown_in_defect_density


def test_interstitial_growth_adds_nothing_the_criterion_gates_the_cost():
    """CG-2 engaged but in the *interstitial* regime (``V/G < ξ_t`` — a slow pull / hot zone): the
    criterion classifies it, but the vacancy-side void density is 0, so the G3 map is untouched (the
    seam holds even with CG-2 on — the cost is criterion-gated, not merely on/off)."""
    cz = CzochralskiKnobs(pull_rate_mm_min=1.0, thermal_gradient_K_per_mm=20.0)  # V/G = 0.05 < ξ_t
    assert cz.voronkov_ratio < VORONKOV_CRITICAL_RATIO
    assert cz.grown_in_defect_regime == "interstitial"
    assert cz.grown_in_defect_density == 0.0
    r = Recipe(czochralski=cz, wafer_prep=WaferPrepKnobs(defect_density=0.2))
    assert r.effective_defect_density == 0.2                          # unchanged — interstitial adds nothing


def test_vacancy_growth_adds_the_cited_void_density_to_the_defect_map():
    """A *vacancy*-regime growth (``V/G > ξ_t`` — fast pull / cool hot zone) adds the cited void density
    to the wafer-prep killer density, and the pipeline scatters against that summed density (read back
    off the deterministic wafer-prep provenance — the wiring end-to-end)."""
    cz = CzochralskiKnobs(pull_rate_mm_min=3.0, thermal_gradient_K_per_mm=3.5)   # V/G ≈ 0.857 > ξ_t
    expected_ratio = voronkov_ratio(3.0, 3.5)
    expected_density = void_defect_density(expected_ratio)
    assert cz.voronkov_ratio == expected_ratio
    assert cz.grown_in_defect_regime == "vacancy"
    assert cz.grown_in_defect_density == expected_density > 0.0

    r = Recipe(czochralski=cz, wafer_prep=WaferPrepKnobs(defect_density=0.1))
    assert r.effective_defect_density == pytest.approx(0.1 + expected_density)
    # The pipeline consumes the summed density (the G3 defect map) — read off the wafer-prep record.
    wafer = run_line(r, seed=0, variation=_DEFECTS_ONLY)
    rec = _prep_record(wafer)
    assert rec.knobs["effective_defect_density"] == pytest.approx(0.1 + expected_density)
    assert rec.knobs["grown_in_defect_density"] == pytest.approx(expected_density)
    assert rec.summary["grown_in_regime"] == "vacancy"               # the wafer-level provenance note


def test_vacancy_growth_costs_yield_through_the_defect_map():
    """The consequence end-to-end: a heavily vacancy-rich growth (a large grown-in COP density) scatters
    killer defects that kill dies — so the wafer yield is below a clean line's, at the same seed. This is
    the in-model brake CG-1 lacked (pulling too fast → voids → yield down)."""
    base = Recipe(wafer_prep=WaferPrepKnobs(defect_density=0.0))      # a clean line, no particles
    voids = Recipe(czochralski=CzochralskiKnobs(pull_rate_mm_min=8.0, thermal_gradient_K_per_mm=2.0),
                   wafer_prep=WaferPrepKnobs(defect_density=0.0))     # V/G = 4.0 ≫ ξ_t → heavy COPs
    # The grown-in density is the cited void density at this (V, G) — large enough (λ = D·A ≫ 1 at the
    # game die area) that the COP scatter is overwhelmingly likely to kill dies (coefficient-robust).
    assert voids.czochralski.grown_in_defect_density == void_defect_density(voronkov_ratio(8.0, 2.0))
    assert voids.effective_defect_density > 0.5
    clean = run_line(base, seed=1, variation=_DEFECTS_ONLY)
    dirty = run_line(voids, seed=1, variation=_DEFECTS_ONLY)
    n_clean = sum(d.killed_by_defect for d in clean.dies)
    n_dirty = sum(d.killed_by_defect for d in dirty.dies)
    assert n_clean == 0 and n_dirty > 0                              # grown-in COPs kill dies
