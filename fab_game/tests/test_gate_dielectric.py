"""F3 slice 2 — the high-κ gate stack wired into the device step (the two currencies, end to end).

:mod:`chip.high_k`'s own triad asserts the physics in isolation; **these** tests assert the thing only the
consumer can show: that the EOT flows into the *existing* ``t_ox_um`` argument of the **untouched**
:mod:`chip.device`, so that at a fixed electrical gate

  * ``V_t``/``I_Dsat``/``C_ox`` are **identical for every material** (the identity — the tight leg), while
  * ``j_gate`` moves by **orders of magnitude** (the exponential — the payload).

That end-to-end pair *is* the F3 discriminator, and the ``device.py``-is-untouched claim is only provable
here, against the real device model. The seam ladder: ``dielectric=None`` (nothing emitted, byte-for-byte
today) → ``"SiO2"`` (the same device, leakage readout **on**) → ``"HfO2"`` (the same device, leakage gone).
"""
from __future__ import annotations

from chip.high_k import HFO2, K_SIO2

from fab_game.recipe import DeviceKnobs
from fab_game.state import Die
from fab_game.steps import device_step

_N_A = 1.0e17
_T_OX_UM = 0.002                     # 2 nm — the late-SiO₂ era, where the leakage wall bites


def _die(t_ox_um: float = _T_OX_UM) -> Die:
    return Die(site=(0, 0), radius_frac=0.0, t_ox_um=t_ox_um, cd_nm=167.0, nils=4.0, resolved=True)


def _dev(dielectric: str | None = None) -> DeviceKnobs:
    return DeviceKnobs(dielectric=dielectric)


# --------------------------------------------------------------------------- #
# 1. The seam — the knob absent, and the engaged-SiO₂ identity
# --------------------------------------------------------------------------- #
def test_dielectric_absent_is_byte_for_byte_and_emits_nothing():
    """No dielectric knob → today's t_ox flows through untouched and **no leakage is emitted** (the seam)."""
    out = device_step(_die(), _dev(None), _N_A)
    assert out.j_gate is None                                    # the gap, not a fake zero
    rec = out.history[-1]
    assert "dielectric" not in rec.knobs_in                      # fingerprint discipline: a bare record
    assert "t_phys_um" not in rec.knobs_in
    assert "j_gate_A_cm2" not in rec.outputs
    assert "decades_saved" not in rec.outputs


def test_sio2_is_the_engaged_seam_same_device_leakage_readout_on():
    """``"SiO2"`` reproduces the knob-absent device **byte-for-byte** and merely turns the readout on.

    The engaged seam: ``EOT == t_phys`` exactly at K=3.9 (:func:`chip.high_k.eot` is the identity there),
    so the *same* number reaches :func:`chip.device.threshold_voltage` — this is what proves engaging F3
    cannot silently move a scored device number."""
    off = device_step(_die(), _dev(None), _N_A)
    sio2 = device_step(_die(), _dev("SiO2"), _N_A)
    assert sio2.V_t == off.V_t                                   # byte-for-byte, not approx
    assert sio2.i_dsat == off.i_dsat
    assert sio2.history[-1].outputs["C_ox"] == off.history[-1].outputs["C_ox"]
    # ...and the only difference is the new additive channel.
    assert sio2.j_gate is not None and sio2.j_gate > 0.0
    assert sio2.history[-1].knobs_in["t_phys_um"] == _T_OX_UM    # EOT == t_phys: nothing was deposited extra
    assert sio2.history[-1].outputs["decades_saved"] == 0.0      # SiO₂ vs itself


# --------------------------------------------------------------------------- #
# 2. The payload — one thickness, two currencies (the discriminator, end to end)
# --------------------------------------------------------------------------- #
def test_hfo2_holds_the_electrical_gate_exactly_and_collapses_the_leakage():
    """**The F3 discriminator**: at matched EOT, HfO₂ leaves ``V_t``/``I_Dsat``/``C_ox`` *identical* to
    SiO₂ while gate leakage falls orders of magnitude — the one observable no scalar can fake.

    The invariance is an **identity** (``ε_SiO₂/EOT ≡ ε₀K/t_phys``), not a fit, so it is asserted exactly:
    ``device.py`` never learns which material it is looking at."""
    sio2 = device_step(_die(), _dev("SiO2"), _N_A)
    hfo2 = device_step(_die(), _dev("HfO2"), _N_A)
    # The electrical gate: untouched, for free, by construction.
    assert hfo2.V_t == sio2.V_t
    assert hfo2.i_dsat == sio2.i_dsat
    assert hfo2.history[-1].outputs["C_ox"] == sio2.history[-1].outputs["C_ox"]
    # The physical gate: 6.4× thicker (K/3.9), and that is what tunnels.
    assert hfo2.history[-1].knobs_in["t_phys_um"] == _T_OX_UM * (HFO2.kappa / K_SIO2)
    assert hfo2.j_gate < sio2.j_gate / 1.0e3                     # orders down — the cliff
    assert hfo2.history[-1].outputs["decades_saved"] > 3.0       # prefactor-free (cited exponent only)


def test_the_grown_oxide_is_never_written_back():
    """``die.t_ox_um`` keeps its documented meaning — **what the furnace grew** — under every material.

    The EOT is computed *at the device read*; folding it back would make the Phase-2 oxidation record start
    lying about the furnace (the F2 discipline of keeping ``die.R_s`` access-only)."""
    for material in (None, "SiO2", "HfO2", "TiO2"):
        assert device_step(_die(), _dev(material), _N_A).t_ox_um == _T_OX_UM


def test_more_kappa_is_not_better_the_tio2_counterexample():
    """TiO₂ (K=80 — 20× the thickness) **still leaks**: a zero CB offset means no barrier at any thickness.

    Robertson's "offset > 1 eV" requirement falls out **computed**, not asserted — and it is why the
    industry took K=25/φ_B=1.4 over K=80. The electrical gate is *still* identical (the identity holds for
    any material), which is exactly what isolates the barrier as the thing that failed."""
    sio2 = device_step(_die(), _dev("SiO2"), _N_A)
    tio2 = device_step(_die(), _dev("TiO2"), _N_A)
    assert tio2.V_t == sio2.V_t                                  # the identity does not care about φ_B
    assert tio2.j_gate > sio2.j_gate                             # 20× the thickness bought nothing at all
    assert tio2.history[-1].outputs["decades_saved"] < 0.0       # strictly worse than the incumbent


# --------------------------------------------------------------------------- #
# 3. The wall the knob exists to escape (the scaling ladder the demo will walk)
# --------------------------------------------------------------------------- #
def test_thinning_the_oxide_runs_the_leakage_away_but_only_for_sio2():
    """The historical wall: thinning SiO₂ buys ``C_ox`` but the leakage runs away exponentially — and
    HfO₂'s escape is that the *same* EOT ladder leaks far less at every rung."""
    thick, thin = 0.003, 0.0015                                  # 3 nm → 1.5 nm, the era's last SiO₂ rungs
    sio2_thick = device_step(_die(thick), _dev("SiO2"), _N_A)
    sio2_thin = device_step(_die(thin), _dev("SiO2"), _N_A)
    assert sio2_thin.j_gate > sio2_thick.j_gate * 1.0e3          # exponential in t_phys — the wall
    assert sio2_thin.V_t < sio2_thick.V_t                        # what the thinning bought (the temptation)
    # The escape: at each rung the high-κ stack holds that same electrical gate at far less leakage.
    for t_ox in (thick, thin):
        assert device_step(_die(t_ox), _dev("HfO2"), _N_A).j_gate < \
               device_step(_die(t_ox), _dev("SiO2"), _N_A).j_gate


# --------------------------------------------------------------------------- #
# 4. Propagation discipline — the dead state, and the additive channel
# --------------------------------------------------------------------------- #
def test_a_refused_device_carries_no_gate_stack():
    """An upstream functional fail refuses *before* the stack is built — no leakage on a device that
    does not exist (the gap-vs-fake-zero rule)."""
    unresolved = Die(site=(0, 0), radius_frac=0.0, t_ox_um=_T_OX_UM, cd_nm=167.0, nils=4.0, resolved=False)
    dead = device_step(unresolved, _dev("HfO2"), _N_A)
    assert dead.V_t is None and dead.j_gate is None
    assert "refused" in dead.history[-1].outputs
    # ...and a bare die (no oxide grown yet) has no EOT to target — it refuses rather than inventing one.
    bare = device_step(Die(site=(0, 0), radius_frac=0.0), _dev("HfO2"), _N_A)
    assert bare.V_t is None and bare.j_gate is None


def test_gate_leakage_never_touches_the_junction_leakage_channel():
    """Gate tunnelling is a **separate channel** from the SRH junction leakage — additive, never folded in.

    (The same discipline as ``BV``/``t_rr``: a new output must not silently move an existing one.)"""
    off = device_step(_die(), _dev(None), _N_A)
    hfo2 = device_step(_die(), _dev("HfO2"), _N_A)
    assert hfo2.j_leak == off.j_leak                             # tunnelling ≠ generation
    assert hfo2.tau == off.tau
    assert hfo2.t_rr == off.t_rr
