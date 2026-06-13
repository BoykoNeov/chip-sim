"""CG-1 wiring — the pull-rate knob flows recipe → k_eff → boule → channel_N_A; the default is the seam.

The physics (the Burton–Prim–Slichter ``k_eff``) is pinned in ``chip/tests/test_czochralski.py``; this
localizes the **fab_game wiring** (so a future regression points at the knob, not the demo): the default
knob reproduces G2's equilibrium ``k₀`` (the seam the G2/G7 boule demos ride), and a set pull rate uses
the BPS ``k_eff`` and flattens the axial doping end-to-end.
"""
from __future__ import annotations

from chip.czochralski import (
    SEGREGATION_K,
    effective_segregation_coefficient,
    normalized_growth_velocity,
)

from fab_game.recipe import CzochralskiKnobs, Recipe


def test_default_pull_rate_is_the_equilibrium_k0_seam():
    """No pull rate set (the default) → the boule uses the equilibrium Trumbore ``k₀`` — CG-1 is off, so
    the G2/G7 boule path is byte-for-byte the pre-CG-1 one (the seam, pinned at the fab_game layer)."""
    r = Recipe()
    assert r.czochralski.pull_rate_mm_min is None
    assert r.czochralski.k_eff is None                       # None → the boule falls back to k₀
    assert r.boule.k == SEGREGATION_K["B"]                   # the cited equilibrium value, unchanged
    assert r.channel_N_A == 1.0e17                           # the default substrate doping (the seam value)


def test_pull_rate_uses_bps_keff_and_flattens_the_doping():
    """A set pull rate flows recipe → k_eff → boule: the boule's ``k`` is the BPS ``k_eff``, and a deeper
    slice is less heavily doped than the equilibrium boule (the drift flattened) — the wiring end-to-end."""
    v = 8.0
    k0 = SEGREGATION_K["B"]
    expected = effective_segregation_coefficient(k0, normalized_growth_velocity(v))
    r = Recipe(czochralski=CzochralskiKnobs(pull_rate_mm_min=v))
    assert r.czochralski.k_eff == expected                   # recipe → k_eff
    assert r.boule.k == expected and expected > k0           # k_eff → boule (and a faster pull lifts k)
    # The seed is pinned for any k (the seam); the tail is flatter than the equilibrium boule.
    default = Recipe()
    assert r.boule.axial_doping(0.0) == default.boule.axial_doping(0.0)
    assert r.boule.axial_doping(0.8) < default.boule.axial_doping(0.8)
