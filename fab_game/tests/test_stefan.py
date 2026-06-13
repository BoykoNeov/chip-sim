"""CG-3 wiring — the melt-gradient knob derives CG-2's interface gradient via the Stefan balance.

The physics (the Stefan interface gradient + the ξ saturation) is pinned in
``chip/tests/test_czochralski.py``; this localizes the **fab_game wiring**: the melt-side gradient
``G_l`` flows recipe → ``stefan_interface_gradient`` → the crystal-side ``G_s`` → CG-2's Voronkov
ratio → the same G3 defect map, the default (no melt gradient) is the CG-2/CG-3 seam, the two gradient
sources are mutually exclusive, and the latent-heat cap bounds the grown-in density a fast pull seeds.
"""
from __future__ import annotations

import pytest

from chip.czochralski import (
    max_voronkov_ratio,
    stefan_interface_gradient,
    void_defect_density,
    voronkov_ratio,
)

from fab_game.recipe import CzochralskiKnobs, Recipe, WaferPrepKnobs


def test_default_no_melt_gradient_is_the_cg3_seam():
    """No melt gradient set (the default) → CG-3 is off: the interface gradient falls back to the
    (also-default-None) CG-2 knob, so a default recipe has no grown-in density (the seam)."""
    r = Recipe()
    assert r.czochralski.melt_gradient_K_per_mm is None
    assert r.czochralski.interface_gradient_K_per_mm is None      # neither knob set → off
    assert r.czochralski.voronkov_ratio is None
    assert r.czochralski.grown_in_defect_density == 0.0
    assert r.effective_defect_density == r.wafer_prep.defect_density


def test_cg2_direct_gradient_path_is_unchanged():
    """The CG-2 direct-gradient path still resolves to the knob value byte-for-byte (CG-3 is purely
    additive — setting only thermal_gradient_K_per_mm reproduces the CG-2 Voronkov ratio exactly)."""
    cz = CzochralskiKnobs(pull_rate_mm_min=2.0, thermal_gradient_K_per_mm=3.5)
    assert cz.interface_gradient_K_per_mm == 3.5                  # the direct house value, unchanged
    assert cz.voronkov_ratio == voronkov_ratio(2.0, 3.5)         # the CG-2 result, identical


def test_melt_gradient_derives_g_from_the_stefan_balance():
    """A melt-side gradient (CG-3) derives the crystal-side ``G_s`` from the Stefan balance and feeds it
    to the Voronkov ratio — the wiring recipe → stefan_interface_gradient → voronkov_ratio end-to-end."""
    v, g_l = 1.0, 0.5
    cz = CzochralskiKnobs(pull_rate_mm_min=v, melt_gradient_K_per_mm=g_l)
    g_s = stefan_interface_gradient(v, g_l)
    assert cz.interface_gradient_K_per_mm == g_s                  # Stefan-derived, not the melt value
    assert g_s > g_l                                             # the latent-heat term lifts G_s above G_l
    assert cz.voronkov_ratio == voronkov_ratio(v, g_s)
    assert cz.grown_in_defect_regime == "vacancy"               # V=1, G_l=0.5 → ξ≈0.22 > ξ_t
    # And it feeds the same G3 defect map (adds to the wafer-prep killer density).
    r = Recipe(czochralski=cz, wafer_prep=WaferPrepKnobs(defect_density=0.1))
    assert r.effective_defect_density == pytest.approx(0.1 + cz.grown_in_defect_density)


def test_setting_both_gradients_raises():
    """The two gradient sources are mutually exclusive (CG-2 direct G vs CG-3 Stefan-derived G) —
    setting both is a misconfiguration that raises rather than silently picking one."""
    cz = CzochralskiKnobs(pull_rate_mm_min=1.0, thermal_gradient_K_per_mm=3.5, melt_gradient_K_per_mm=0.5)
    with pytest.raises(ValueError):
        _ = cz.interface_gradient_K_per_mm
    with pytest.raises(ValueError):
        _ = cz.voronkov_ratio


def test_melt_gradient_without_pull_rate_raises():
    """CG-3's Stefan balance needs the front velocity V — a melt gradient with no pull rate raises."""
    cz = CzochralskiKnobs(melt_gradient_K_per_mm=0.5)            # pull_rate left None
    with pytest.raises(ValueError):
        _ = cz.interface_gradient_K_per_mm


def test_latent_heat_cap_bounds_the_grown_in_density():
    """THE CG-3 consequence at the wiring layer: under the Stefan coupling ξ saturates at ξ_max, so a
    very fast pull seeds only a BOUNDED grown-in density — whereas CG-2's fixed-G ξ=V/G runs away. The
    in-model cost of fast pull is capped, not a cliff."""
    fast = 5000.0
    g_l = 0.5
    cg3 = CzochralskiKnobs(pull_rate_mm_min=fast, melt_gradient_K_per_mm=g_l)
    cap = void_defect_density(max_voronkov_ratio())
    assert cg3.voronkov_ratio < max_voronkov_ratio()             # bounded below the cap
    assert cg3.grown_in_defect_density <= cap + 1e-9            # density bounded by the cap
    # The contrast: a fixed-G (CG-2) growth at the SAME huge pull has a vastly larger density (runaway).
    cg2 = CzochralskiKnobs(pull_rate_mm_min=fast, thermal_gradient_K_per_mm=g_l)
    assert cg2.grown_in_defect_density > 100.0 * cap            # unbounded vs CG-3's cap
