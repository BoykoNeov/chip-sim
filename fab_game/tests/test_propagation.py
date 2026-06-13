"""Propagation is actually wired (ADR 0005 §5) — the device reads the inherited fields.

The plan's pedagogy is that damage propagates because each downstream step *reads the inherited
field*, not via a scripted dependency graph. The device step's reads are the testable wiring, and
the directions are **guaranteed by the validated** :mod:`chip.device` **physics**:

* a thicker inherited ``t_ox`` → a **larger** ``V_t`` (the depletion term grows as ``C_ox`` falls);
* a longer inherited ``CD`` (channel length) → a **smaller** ``I_Dsat`` (``∝ W/L``), and — the
  device model's named scope edge — ``CD`` **never** moves ``V_t`` (long-channel);
* an upstream functional fail (the litho image did not resolve) → the device **refuses** (no
  ``V_t``/``I_Dsat``), so the dead state propagates rather than fabricating a transistor.

A strictly-worse inherited field never yields a strictly-better downstream observable here — and
if a wire were cut (the device ignoring ``t_ox`` or ``cd``), these monotonic checks would break.
"""
from __future__ import annotations

from chip.purification import Contamination

from fab_game.recipe import DeviceKnobs
from fab_game.state import Die
from fab_game.steps import device_step


_DEV = DeviceKnobs()
_N_A = 1.0e17


def _die_with(t_ox_um: float, cd_nm: float, resolved: bool = True) -> Die:
    return Die(site=(0, 0), radius_frac=0.0, t_ox_um=t_ox_um, cd_nm=cd_nm,
               nils=4.0, resolved=resolved)


def test_thicker_oxide_raises_vt():
    """A thicker inherited gate oxide → a strictly larger V_t (the device reads t_ox)."""
    thin = device_step(_die_with(0.012, 167.0), _DEV, _N_A)
    thick = device_step(_die_with(0.020, 167.0), _DEV, _N_A)
    assert thick.V_t > thin.V_t


def test_longer_channel_lowers_idsat_but_not_vt():
    """A longer inherited CD → strictly less I_Dsat (∝ 1/L), and V_t is unchanged (scope edge)."""
    short = device_step(_die_with(0.014, 150.0), _DEV, _N_A)
    long_ = device_step(_die_with(0.014, 185.0), _DEV, _N_A)
    assert long_.i_dsat < short.i_dsat                       # I_Dsat ∝ W/L
    assert long_.V_t == short.V_t                            # CD never leaks into V_t (long-channel)


def test_unresolved_image_refuses_the_device():
    """An upstream functional fail (resolved=False) → the device refuses (the dead state propagates)."""
    dead = device_step(_die_with(0.014, 167.0, resolved=False), _DEV, _N_A)
    assert dead.V_t is None and dead.i_dsat is None
    refused = dead.history[-1]
    assert refused.step == "device" and "refused" in refused.outputs


def test_missing_upstream_refuses_the_device():
    """No inherited t_ox/CD (a step never ran) → the device refuses rather than inventing a number."""
    bare = Die(site=(0, 0), radius_frac=0.0)
    out = device_step(bare, _DEV, _N_A)
    assert out.V_t is None and out.i_dsat is None


# --------------------------------------------------------------------------- #
# G4 — the contamination reads (Na → Q_ox → V_t; residual dopant → net doping → V_t)
# --------------------------------------------------------------------------- #
def test_sodium_contamination_drives_vt_down():
    """More inherited mobile-ion Na → a larger Q_ox → a strictly smaller V_t (the lifted oxide edge).

    The G4 propagation wire: positive Na⁺ oxide charge shifts the flat-band voltage down. A clean
    contamination (or None) leaves V_t at the ideal-oxide value (the seam); only Na moves it (the
    metals ride along with no V_t effect — the named G4b gap)."""
    clean = device_step(_die_with(0.014, 167.0), _DEV, _N_A, contamination=None)
    dirty = device_step(_die_with(0.014, 167.0), _DEV, _N_A, contamination=Contamination(Na=1.0e16))
    dirtier = device_step(_die_with(0.014, 167.0), _DEV, _N_A, contamination=Contamination(Na=2.0e16))
    assert dirty.V_t < clean.V_t                             # Na drives V_t down
    assert dirtier.V_t < dirty.V_t                           # monotone in Na
    # A clean (all-zero) contamination is byte-for-byte the no-contamination V_t (the seam).
    clean_obj = device_step(_die_with(0.014, 167.0), _DEV, _N_A, contamination=Contamination())
    assert clean_obj.V_t == clean.V_t
    # Deep-level metals ride along with NO V_t consequence (the named G4b gap — net doping can't carry it).
    metal = device_step(_die_with(0.014, 167.0), _DEV, _N_A, contamination=Contamination(Fe=1.0e18))
    assert metal.V_t == clean.V_t


def test_residual_acceptor_raises_vt_via_net_doping():
    """A higher effective channel doping (residual acceptor folded in by the caller) → a larger V_t.

    The residual-dopant net shift is applied to ``channel_N_A`` *before* device_step (the
    ``effective_channel_N_A`` path), so here it shows as the device's monotone V_t-vs-N_A response —
    the same validated :func:`chip.device.threshold_voltage` doping dependence."""
    base = device_step(_die_with(0.014, 167.0), _DEV, _N_A)
    doped = device_step(_die_with(0.014, 167.0), _DEV, _N_A + 5.0e16)   # + residual acceptor
    assert doped.V_t > base.V_t
