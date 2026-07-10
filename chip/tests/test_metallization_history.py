"""Historical-modes B6 — aluminium junction spiking (``chip.metallization_history``).

The triad, per ``docs/plans/historical-modes.md``:

  * **tight — the seam:** ``scheme="barrier"`` → ``d_spike ≡ 0`` → ``f_short ≡ 0`` → the aggregate
    leakage is :func:`chip.lifetime.generation_leakage_density` **byte-for-byte** (a structural
    ``(1−0)·J = J``, not a small number);
  * **tight — the sign / topology (the discriminator):** ``f_short`` rises as ``x_j`` falls (spiking
    shorts the *shallower* junction), as the sinter ``T`` rises, and as ``t_Al`` rises; ``→ 1`` as
    ``d_spike ≫ x_j`` and ``→ 0`` as ``x_j ≫ d_spike``; scheme order Al > Al–Si > barrier;
  * **flagged:** the Si-in-Al solubility curve, the spike-concentration κ, the exponential spike-depth
    shape, and the ohmic-short density — asserted only by shape/sign, not as exact numbers.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import math

import pytest

from chip import lifetime as lt
from chip import metallization_history as mh


# --------------------------------------------------------------------------- #
# The seam — byte-for-byte (tight)
# --------------------------------------------------------------------------- #
def test_barrier_leakage_is_bit_for_bit_lifetime_baseline():
    """The default barrier scheme reproduces lifetime's intact leakage byte-for-byte (the seam)."""
    for N_A in (1e16, 1e17, 5e17):
        for x_j in (0.1, 0.2, 0.5):
            r = mh.metal_spiking(x_j, N_A=N_A)                 # default scheme = "barrier"
            base = lt.device_leakage(None, N_A).j_leak
            assert r.f_short == 0.0
            assert r.d_spike_um == 0.0
            assert r.j_leak == base                            # byte-identical, not approx


def test_barrier_seam_holds_at_any_temperature_and_thickness():
    """A barrier getters no Si at any sinter T / film thickness → spike depth identically 0."""
    for T in (300.0, 450.0, 577.0, 650.0):
        for t_al in (0.2, 0.8, 2.0):
            assert mh.spike_depth(T, t_al, "barrier") == 0.0


def test_spiked_leakage_seam_and_full_short():
    """spiked_leakage: f=0 returns the intact value byte-for-byte; f=1 returns the short density."""
    intact = 3.2e-12
    assert mh.spiked_leakage(0.0, intact) == intact
    assert mh.spiked_leakage(1.0, intact, j_short=1.0) == 1.0
    # linear blend at f = 0.5
    assert mh.spiked_leakage(0.5, intact, j_short=1.0) == pytest.approx(0.5 * intact + 0.5, rel=1e-12)


# --------------------------------------------------------------------------- #
# The discriminator — shallower junction is worse (tight sign)
# --------------------------------------------------------------------------- #
def test_shorted_fraction_rises_as_junction_gets_shallower():
    """Pure Al: the shorted-area fraction increases monotonically as x_j shrinks (the coupling)."""
    xjs = [0.1, 0.2, 0.3, 0.5, 1.0, 1.5]
    f = [mh.metal_spiking(xj, scheme="Al", T_celsius=500.0).f_short for xj in xjs]
    assert all(a > b for a, b in zip(f, f[1:]))               # strictly decreasing in x_j
    assert f[0] > 0.5 and f[-1] < 0.05                        # shallow shorts hard, deep barely


def test_shorted_fraction_limits():
    """f_short → 1 as d_spike ≫ x_j, → 0 as x_j ≫ d_spike, and is exactly 0 at d_spike = 0."""
    assert mh.shorted_area_fraction(0.0, 0.2) == 0.0          # perfect barrier — exact seam
    assert mh.shorted_area_fraction(1.0e4, 0.2) == pytest.approx(1.0, abs=1e-3)   # deep spikes → fully shorted
    assert mh.shorted_area_fraction(0.01, 5.0) < 1e-100       # shallow spikes, deep junction
    assert mh.shorted_area_fraction(0.2, 0.2) == pytest.approx(math.exp(-1.0))    # the exp form


def test_shorted_fraction_rises_with_temperature_and_thickness():
    """More Si dissolves at higher sinter T and a thicker Al sink → deeper spikes → more shorting."""
    f_T = [mh.metal_spiking(0.2, scheme="Al", T_celsius=T).f_short for T in (350.0, 450.0, 550.0)]
    assert all(a < b for a, b in zip(f_T, f_T[1:]))           # rises with T
    f_t = [mh.metal_spiking(0.2, scheme="Al", T_celsius=450.0, al_thickness_um=t).f_short
           for t in (0.3, 0.8, 1.5)]
    assert all(a < b for a, b in zip(f_t, f_t[1:]))           # rises with t_Al


def test_scheme_ordering_al_worse_than_alsi_worse_than_barrier():
    """At a shallow junction the wall is worst for pure Al, suppressed by Al–Si, cleared by the barrier."""
    f = {s: mh.metal_spiking(0.15, scheme=s, T_celsius=500.0).f_short for s in ("Al", "Al-Si", "barrier")}
    assert f["Al"] > f["Al-Si"] > f["barrier"] == 0.0
    # and the leakage follows: a shorted contact leaks far above the barrier's clean baseline
    j = {s: mh.metal_spiking(0.15, scheme=s, T_celsius=500.0).j_leak for s in ("Al", "Al-Si", "barrier")}
    assert j["Al"] > j["Al-Si"] > j["barrier"]


# --------------------------------------------------------------------------- #
# The flagged solubility curve — cited direction + eutectic clamp
# --------------------------------------------------------------------------- #
def test_solubility_rises_with_temperature_and_clamps_at_the_eutectic():
    """Si-in-Al solubility increases with T toward the cited ~1.5 wt % eutectic ceiling, then clamps."""
    s = [mh.silicon_solubility_in_al(T) for T in (300.0, 400.0, 500.0, 577.0)]
    assert all(a < b for a, b in zip(s, s[1:]))               # monotone up to the eutectic
    assert s[-1] == pytest.approx(mh.SI_IN_AL_EUTECTIC_WT)    # ~1.5 wt % at 577 °C (the cited anchor)
    assert mh.silicon_solubility_in_al(700.0) == mh.SI_IN_AL_EUTECTIC_WT   # clamped above the eutectic


def test_spike_depth_scales_with_uptake_thickness_and_solubility():
    """d_spike = κ·si_uptake·t_Al·S_vol — linear in thickness, zero uptake ⇒ zero, proportional to S_vol."""
    d1 = mh.spike_depth(500.0, 0.4, "Al")
    d2 = mh.spike_depth(500.0, 0.8, "Al")
    assert d2 == pytest.approx(2.0 * d1, rel=1e-12)          # linear in t_Al
    # Al–Si draws exactly si_uptake× the pure-Al spike (same T, same sink)
    ratio = mh.SCHEMES["Al-Si"].si_uptake / mh.SCHEMES["Al"].si_uptake
    assert mh.spike_depth(500.0, 0.8, "Al-Si") == pytest.approx(ratio * d2, rel=1e-12)


# --------------------------------------------------------------------------- #
# Guards (the established idiom)
# --------------------------------------------------------------------------- #
def test_guards_reject_bad_inputs():
    """The consumer guards its physical ranges."""
    with pytest.raises(ValueError, match="si_uptake"):
        mh.MetalScheme("bad", 1.5)
    with pytest.raises(ValueError, match="x_j_um"):
        mh.shorted_area_fraction(0.3, 0.0)
    with pytest.raises(ValueError, match="al_thickness_um"):
        mh.spike_depth(450.0, -0.1, "Al")
    with pytest.raises(ValueError, match="shorted_fraction"):
        mh.spiked_leakage(1.5, 1e-12)
