"""The historical-modes B10 banked artifact: strained silicon — the factor that had no process owner (F5).

The period channel (**unstrained** silicon, the only channel this simulator has ever had) run against the
observable that ended it — *the drive-current levers all spend a second currency, and the one factor that
spends none was the one no process step could move*. One figure, three panels:

  * **Left — the wall: two currencies, and the term that only has one.**
    ``I_Dsat = ½·µ·C_ox·(W/L)·(V_GS − V_t)²``. Every factor on the right has been a process outcome here
    since Phase 4 — ``C_ox`` from the oxide furnace, ``W/L`` from the litho CD, ``V_t`` from the channel
    doping and the adjust implant — **except ``µ``**, which has been the module constant
    :data:`chip.device.MU_N_EFF` = 450 cm²/V·s since the day it was written. The panel prices the era's
    workhorse lever against the era's bill: walk the gate oxide down from the period 2.0 nm and read the
    drive gain against the gate leakage (:func:`chip.high_k.gate_leakage` — the **B8** rung's own wall, in
    F5's currency). The oxide path *climbs*; the strain path is **horizontal**, and the horizontality is
    the claim: the tunnelling exponent has no mobility in it, so ``∂J_g/∂µ = 0`` **structurally** — the
    same shape as B9's ``∂τ_wire/∂I_Dsat = 0``. One knob, one currency.
  * **Middle — the fork: one node, two processes, opposite signs.** Electrons and holes respond to
    *opposite* stresses, so the 90 nm node shipped **two** strain mechanisms: a tensile silicon-nitride
    capping layer over the nMOS (+20% electron µ) and compressive SiGe source/drain, 17% Ge, under the
    pMOS (>50% hole µ). The simulator is n-channel-only, so **only the electron leg is wired**: the panel
    marks the hole bar **CITED DATA ONLY**, and :func:`chip.strain.nmos_mobility` *refuses* it by name
    rather than returning an inverted-sign number. That refusal is the era's teaching point, not a guard
    rail — the strain era needed two different processes because one sign cannot serve both carriers.
  * **Right — the bound: what a long-channel model infers vs what the devices measured.** The wired path
    is the **optimistic** one and there is no way to make it otherwise: ``mu_eff = MU_N_EFF · factor`` fed
    to a long-channel ``I_Dsat`` carries ``I ∝ µ``, an elasticity of exactly **1** by construction. The
    real 90 nm devices measured **0.500** on *both* carriers, and an independent 25 nm device measures
    **0.35**. The panel draws the model's diagonal, the cited lines under it, and the three cited points —
    so the overstatement (**×2.0** at 90 nm) is a number on the figure rather than a caveat in prose.

The honesty ladder (the ``historical-modes.md`` triad)
--------------------------------------------------------
* **Tight — the seam.** No mechanism ⇒ factor exactly ``1.0`` ⇒ ``mu_eff == MU_N_EFF`` ⇒ the period
  ``I_Dsat`` **byte-for-byte**. The strain path leaves from the period point, it does not start beside it.
* **Tight — the orthogonality, and it is the left panel's whole content.** :func:`chip.high_k.gate_leakage`
  takes a thickness and a dielectric; **mobility is not one of its arguments**, so strain's leakage column
  is exactly zero — a *structural* zero, not a small number. Meanwhile the oxide lever moves both
  currencies at once, which is precisely F3/B8's "one thickness, two currencies" read from the other side.
* **Tight — the model's own elasticity is 1.** Long-channel ``I ∝ µ`` exactly on the ideal-contact form
  (asserted against the real, untouched :mod:`chip.device`), which is *why* the drive read is a bound.
* **Tight — the cited elasticity.** ``(drive−1)/(µ−1)`` = **0.500** on both carriers from one paper, so
  the ×2.0 overstatement is arithmetic on cited numbers rather than an estimate this demo must defend.
* **A CONSISTENCY note, not a claim — the exchange rate.** *How many decades* of gate leakage the oxide
  lever costs to buy strain's +20% is **recipe-carrying**, and it moves by 2× across two equally
  defensible conventions: holding the channel doping fixed (this demo's ladder — ``V_t`` sags as the oxide
  thins, so the drive rises *faster* than ``1/t_ox`` and the oxide lever looks **cheap**) gives ≈0.9
  decades; re-adjusting ``V_t`` at every rung, which is what a fab actually does, gives ``I ∝ C_ox``
  exactly and ≈1.9. **This demo quotes the first — the reading most favourable to the lever strain is
  being compared against** — and reports the other beside it. The *band* is recipe-carrying; the **zero
  in strain's column is not**. Lead with the zero.
* **Flagged — absolute currents are not a claim.** ``MU_N_EFF`` is a house lump this module inherits
  rather than fixes (which is exactly why the headline is an enhancement *factor* — a ratio cancels the
  lump, an absolute µ does not), the leakage prefactor :data:`chip.high_k.J0_REFERENCE` is a house lump
  too (read the decades as "≳ N"), and the long-channel form has no velocity saturation, so the µA/µm it
  prints at a 90 nm gate length is a geometry read and not a datasheet number.

Named ceilings — the axes this figure does not carry
------------------------------------------------------
* **Velocity saturation — the big one, and it is the reason the right panel exists.** The 90 nm device is
  velocity-saturated (``I_Dsat ≈ W·C_ox·v_sat·(V_GS − V_t)``, and ``v_sat`` is nearly strain-independent),
  which is what pulls the real elasticity to 0.5. Building it means replacing the long-channel
  ``I_Dsat`` — a *device-model* change, not a *process* one, and five consecutive slices have left
  :mod:`chip.device` alone. **Named, not built**, exactly as B9 named repeater insertion.
* **The wire's cut of the win — named as a law, deliberately NOT drawn.** F4 proved
  ``∂ln f/∂ln I_Dsat = 1 − wire_share``, exact at every ``I_Dsat``: strain buys drive current, and the
  interconnect keeps a fixed fraction of it. But :mod:`chip.interconnect`'s bulk path refuses below
  ~0.194 µm and a 90 nm line is *deep* inside that refusal, so a 90 nm ``wire_share`` would be a
  fabricated number. The composition is stated as the exact law in :func:`print_summary` and appears on
  no axis.
* **A p-MOSFET: NOT BUILT.** The enhancement-factor design exists precisely so the hole leg needs none.
* **A stress → mobility model (GPa, deformation potentials, band warping): NOT BUILT.** A GPa figure per
  Ge% is not pinned at this project's sourcing bar, so :mod:`chip.strain` carries **no stress field at
  all** rather than an invented one — and this figure therefore has no stress axis to draw.
* **Vertical-field erosion: DELIBERATELY ABSENT.** "Strain enhancement erodes at high vertical field" is a
  **biaxial** result; the cited uniaxial work states the hole enhancement *is* present at large vertical
  fields in nanoscale transistors. Carrying it would be recalling instead of citing.
* **Strain relaxation / misfit dislocations / SiGe critical thickness: NOT BUILT** — a yield and
  reliability currency, not a drive-current one. Run headless:

    python -m chip.demo_strain_history
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import device as dev
from . import high_k as hk
from . import strain as st

# --- Recipe: one period n-MOS, and the two ways to buy drive current out of it --------------------- #
# A 90 nm-era n-MOSFET, read through the REAL, untouched device.py. The supply is the CITED one — the
# Intel 90 nm results this slice is sourced from are quoted at 1.2 V — and the gate length is the node's.
# The long-channel form has no velocity saturation, so the ABSOLUTE µA/µm this recipe prints is a geometry
# read and not a datasheet number (see the docstring's flag); every claim below is a ratio against it.
PERIOD_T_OX_UM = 2.0e-3        # µm — 2.0 nm gate oxide: the period rung the ladder leaves from
PERIOD_N_A = 5.0e17            # cm⁻³ — p-type channel doping
PERIOD_VT_ADJUST_DOSE = 3.0e12  # cm⁻² — the acceptor adjust sheet (§5) that lands V_t ≈ 0.41 V
PERIOD_VT_ADJUST_KIND = "p"    # acceptor ⇒ raises V_t (n-MOS)
PERIOD_CHANNEL_L_UM = 0.09     # µm — the 90 nm node's gate length (geometry; the model stays long-channel)
PERIOD_WIDTH_UM = 1.0          # µm — device width W, so I_Dsat reads directly in A/µm
V_GS_CITED = 1.2               # V — CITED: the supply the 90 nm strain results are quoted at

# The oxide ladder — the era's workhorse drive-current lever, priced in the currency it actually spends.
# Floored at 1.0 nm for B8's reason, unchanged: below that this leakage model leaves the regime it is
# honest in (direct tunnelling, V_g < φ_B — and 1.2 V is comfortably inside it), and real SiO₂ at that
# thickness is defect-limited long before the exponent says so.
OXIDE_LADDER_FLOOR_UM = 1.0e-3
T_OX_LADDER_UM = np.linspace(PERIOD_T_OX_UM, OXIDE_LADDER_FLOOR_UM, 320)
GATE_DIELECTRIC = "SiO2"       # the period gate stack — high-κ is B8's rung, four years later

# The strain path, on the same axes: the wired leg, at the period oxide. The mechanism is the registry's,
# never re-typed here — chip.strain owns the cited factors and this module owns only the recipe.
WIRED_MECHANISM = "tensile_cesl"

# The right panel's axis — a mobility-enhancement sweep wide enough to carry all three cited points
# (the 25 nm cross-check sits at 2.00). The MODEL's line on it is drawn from long_channel_drive_factor
# (drive == µ), NOT from chip.strain.elasticity(), which refuses a gain-free input by design.
MU_FACTOR_AXIS = np.linspace(1.0, 2.10, 200)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-strain-history.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-strain-history.png"


@dataclass(frozen=True)
class StrainHistoryResult:
    """The B10 bundle the figure and summary consume."""

    # the period device — unstrained silicon, through the real, untouched device.py
    mos: dev.MOSDevice
    i_dsat_A: float
    j_gate_A_cm2: float
    # left — the oxide lever: drive bought, leakage spent (both currencies, one knob)
    t_ox_um: np.ndarray
    drive_gain_oxide: np.ndarray                # I_Dsat(t_ox) / I_Dsat(period)
    j_gate_oxide: np.ndarray                    # A/cm² along the same ladder
    oxide_t_ox_matching_um: float               # the thinning that matches strain's long-channel gain
    oxide_decades_to_match: float               # …and what it costs — THIS demo's convention (fixed N_A)
    oxide_decades_to_match_fixed_vt: float      # …the other convention (I ∝ C_ox): ~2× more expensive
    # left — the strain lever: the same drive, and a leakage column that is a STRUCTURAL zero
    channel: st.StrainedChannel                 # the wired read (chip.strain owns the cited factors)
    i_dsat_strained_A: float
    j_gate_strained_A_cm2: float                # == j_gate_A_cm2, bit-for-bit — mobility is not an argument
    strain_decades: float                       # exactly 0.0
    # middle — the fork: both signs, and which one the simulator can actually drive
    mechanisms: dict[str, st.StrainMechanism]
    wired: tuple[str, ...]
    hole_leg_refused: str                       # the message nmos_mobility raises with (the teaching point)
    # right — the bound: the model's inference against the cited measurements
    mu_axis: np.ndarray
    drive_model: np.ndarray                     # I ∝ µ — elasticity 1, by construction
    drive_cited_90nm: np.ndarray                # elasticity 0.500 — both carriers, one paper
    drive_cited_25nm: np.ndarray                # elasticity 0.35 — the independent short-channel point
    cited_points: tuple[tuple[str, float, float, bool], ...]   # (label, µ, drive, wired)
    drive_overstatement: float                  # 1/elasticity = 2.0 at 90 nm


def _period_mos(t_ox_um: float) -> dev.MOSDevice:
    """The period device at gate oxide ``t_ox_um`` — the **real** ``device.py``, nothing intercepted.

    The channel doping and the adjust dose are held **fixed** as the oxide thins, which is this demo's
    stated convention and the one most favourable to the oxide lever: ``V_t`` sags with ``t_ox`` (the
    adjust shift is ``q·Q/C_ox``), so the drive rises *faster* than ``1/t_ox`` and less thinning buys the
    matched gain. See the docstring's consistency note for the other convention.
    """
    return dev.threshold_voltage(
        PERIOD_N_A, t_ox_um, channel_length_um=PERIOD_CHANNEL_L_UM,
        implant_dose=PERIOD_VT_ADJUST_DOSE, implant_kind=PERIOD_VT_ADJUST_KIND,
    )


def _i_dsat(mos: dev.MOSDevice, mu_eff: float = dev.MU_N_EFF) -> float:
    """``I_Dsat`` at the cited supply — the one call site where a strained mobility can enter."""
    return dev.saturation_current(mos, V_GS=V_GS_CITED, width_um=PERIOD_WIDTH_UM, mu_eff=mu_eff)


def decades(j: float, j_reference: float) -> float:
    """``log₁₀(J/J_ref)`` — the leakage bill, in the currency B8 priced the SiO₂ ladder in.

    Read as "**≳ N decades**": the absolute prefactor is a house lump
    (:data:`chip.high_k.J0_REFERENCE`), and it cancels here because this is a ratio — which is why the
    bill is quoted in decades and never in A/cm².
    """
    if j <= 0.0 or j_reference <= 0.0:
        raise ValueError(f"leakage densities must be positive, got {j} and {j_reference}")
    return math.log10(j / j_reference)


def compute() -> StrainHistoryResult:
    """Run the period device → the oxide lever's two currencies → the strain lever's one → the bound."""
    mos = _period_mos(PERIOD_T_OX_UM)
    i_dsat = _i_dsat(mos)
    j_gate = hk.gate_leakage(PERIOD_T_OX_UM, GATE_DIELECTRIC)

    # Left, the oxide path: one knob, and it moves BOTH currencies. Read through the real device.py, so
    # the V_t sag that makes this the lever-favourable convention is in the curve rather than assumed away.
    drive_oxide = np.array([_i_dsat(_period_mos(t)) / i_dsat for t in T_OX_LADDER_UM])
    j_oxide = np.array([hk.gate_leakage(t, GATE_DIELECTRIC) for t in T_OX_LADDER_UM])

    # Left, the strain path: the SAME device, the SAME oxide, a different mobility. chip.strain owns the
    # factor; this module never re-types it. The seam is what makes the two paths leave the same point —
    # strained_channel(MU_N_EFF, None) is MU_N_EFF exactly, which is saturation_current's own default.
    channel = st.strained_channel(dev.MU_N_EFF, WIRED_MECHANISM)
    i_strained = _i_dsat(mos, mu_eff=channel.mu_strained_cm2_Vs)
    # …and its leakage. Not "approximately unchanged": gate_leakage's arguments are a thickness and a
    # dielectric, so there is no path by which a mobility could reach it. A STRUCTURAL zero.
    j_strained = hk.gate_leakage(PERIOD_T_OX_UM, GATE_DIELECTRIC)

    # What the oxide lever would have to spend to buy the same (long-channel) gain. Interpolated on the
    # demo's own ladder — a readout of the curve that is drawn, not a second closed form beside it.
    target = channel.drive_factor_long_channel
    t_match = float(np.interp(target, drive_oxide, T_OX_LADDER_UM))
    d_match = decades(hk.gate_leakage(t_match, GATE_DIELECTRIC), j_gate)
    # The other convention, quoted beside it because the difference IS the recipe-carrying part: re-adjust
    # V_t at every rung (what a fab does) and I ∝ C_ox ∝ 1/t_ox exactly, so the matched thinning is the
    # full 1/factor and costs about twice as much. This demo headlines the CHEAPER one.
    d_match_fixed_vt = decades(
        hk.gate_leakage(PERIOD_T_OX_UM / target, GATE_DIELECTRIC), j_gate
    )

    # Middle, the fork: the registry as it stands, plus the refusal spelled out. Catching the raise here
    # (rather than paraphrasing it) is what keeps the figure's caption and chip.strain's own words one text.
    try:
        st.nmos_mobility(dev.MU_N_EFF, "sige_sd")
        raise AssertionError("chip.strain stopped refusing the hole leg on an n-channel device")
    except ValueError as exc:
        refused = str(exc)

    # Right, the bound. The MODEL's line is drive == µ (long_channel_drive_factor), never elasticity() —
    # which refuses a gain-free input, and the axis starts at exactly 1.0.
    drive_model = MU_FACTOR_AXIS.copy()
    e90 = st.TENSILE_CESL.cited_elasticity                     # 0.500 — and the hole leg agrees exactly
    drive_90 = 1.0 + e90 * (MU_FACTOR_AXIS - 1.0)
    drive_25 = 1.0 + st.SHORT_CHANNEL_CROSSCHECK * (MU_FACTOR_AXIS - 1.0)
    points = (
        ("nMOS tensile cap — WIRED", st.TENSILE_CESL.mobility_factor,
         st.TENSILE_CESL.drive_factor, True),
        ("pMOS SiGe S/D — cited", st.SIGE_SD.mobility_factor,
         st.SIGE_SD.drive_factor, False),
        (f"L = {st.SHORT_CHANNEL_L_NM:.0f} nm — cited",
         st.SHORT_CHANNEL_MOBILITY_FACTOR, st.SHORT_CHANNEL_DRIVE_FACTOR, False),
    )

    return StrainHistoryResult(
        mos=mos, i_dsat_A=i_dsat, j_gate_A_cm2=j_gate,
        t_ox_um=T_OX_LADDER_UM, drive_gain_oxide=drive_oxide, j_gate_oxide=j_oxide,
        oxide_t_ox_matching_um=t_match, oxide_decades_to_match=d_match,
        oxide_decades_to_match_fixed_vt=d_match_fixed_vt,
        channel=channel, i_dsat_strained_A=i_strained, j_gate_strained_A_cm2=j_strained,
        strain_decades=decades(j_strained, j_gate),
        mechanisms=dict(st.MECHANISMS), wired=st.WIRED_MECHANISMS, hole_leg_refused=refused,
        mu_axis=MU_FACTOR_AXIS, drive_model=drive_model,
        drive_cited_90nm=drive_90, drive_cited_25nm=drive_25, cited_points=points,
        drive_overstatement=st.drive_overstatement(WIRED_MECHANISM),
    )


def _wrap(text: str, width: int) -> list[str]:
    """Soft-wrap ``text`` for the summary — used so the refusal message prints its whole *reasoning*.

    Truncating it would show only the first clause ("…is a pMOS technique"), which is the *fact*; the
    part that matters is *why* returning a number would be worse than raising, and that is the tail.
    """
    import textwrap
    return textwrap.wrap(text, width=width) or [""]


def print_summary(r: StrainHistoryResult) -> None:
    """Print the B10 story — the term with no owner, the fork, and the bound the wired path cannot avoid."""
    print("\nHistorical-modes B10: strained silicon (the I_Dsat factor no process step had ever moved)\n")
    print(f"  The period device — UNSTRAINED silicon, through the real, untouched device.py:")
    print(f"    a {PERIOD_CHANNEL_L_UM*1e3:.0f} nm-gate n-MOS, {PERIOD_T_OX_UM*1e3:.1f} nm gate oxide,"
          f" W = {PERIOD_WIDTH_UM:.0f} µm, at the cited V_dd = {V_GS_CITED} V")
    print(f"    → V_t = {r.mos.V_t:.3f} V, I_Dsat = {r.i_dsat_A*1e6:.0f} µA/µm,"
          f" J_gate = {r.j_gate_A_cm2:.2e} A/cm²")
    print(f"    [the long-channel form carries NO velocity saturation, so the absolute µA/µm is a geometry")
    print(f"     read and not a datasheet number — every claim below is a RATIO against it]\n")

    print(f"  The wall — I_Dsat = ½·µ·C_ox·(W/L)·(V_GS − V_t)², and where each factor comes from:")
    print(f"      {'factor':<8} {'set by':<58} {'since'}")
    print(f"      {'C_ox':<8} {'the oxide furnace (P2), then the dielectric (F3/B8)':<58} P2 / F3")
    print(f"      {'W/L':<8} {'the litho CD (P3)':<58} P3")
    print(f"      {'V_t':<8} {'channel doping (P1a), Q_ox (G4a), the adjust implant (F1)':<58} P4 / F1")
    print(f"      {'µ':<8} {'NOTHING — MU_N_EFF = ' + str(dev.MU_N_EFF) + ', a module constant':<58} never")
    print(f"    → strain is a MECHANICAL state, not a chemical one, so this is the first device number in")
    print(f"      the sim that moves without changing a dopant, a thickness or a length.\n")

    ratio = r.oxide_t_ox_matching_um / PERIOD_T_OX_UM
    print(f"  The two currencies — what each lever buys, and what each lever SPENDS:")
    print(f"      {'lever':<48} {'drive gain':>11} {'gate leakage':>16}")
    print(f"      {'thin the gate oxide   ' + f'{PERIOD_T_OX_UM*1e3:.2f} → {r.oxide_t_ox_matching_um*1e3:.2f} nm':<48}"
          f" {r.channel.drive_factor_long_channel:>10.2f}× {'≳ +' + f'{r.oxide_decades_to_match:.2f}' + ' decades':>16}")
    print(f"      {'strain the channel    µ ×' + f'{r.channel.mobility_factor:.2f} ({WIRED_MECHANISM})':<48}"
          f" {r.channel.drive_factor_long_channel:>10.2f}× {'0.00 decades':>16}")
    print(f"    → and the zero is STRUCTURAL, not small: chip.high_k.gate_leakage takes a thickness and a")
    print(f"      dielectric — mobility is not one of its arguments, so ∂J_g/∂µ = 0 exactly. (The same")
    print(f"      shape as B9's ∂τ_wire/∂I_Dsat = 0: two terms that share no variable.) The oxide lever")
    print(f"      moves BOTH currencies at once — which is B8's 'one thickness, two currencies', read from")
    print(f"      the other side: strain is one knob with one currency.\n")
    print(f"    [the DECADES are recipe-carrying and this demo quotes the cheap reading. Holding the channel")
    print(f"     doping fixed lets V_t sag as the oxide thins ({r.mos.V_t:.3f} →"
          f" {_period_mos(r.oxide_t_ox_matching_um).V_t:.3f} V), so the drive rises faster")
    print(f"     than 1/t_ox and a thinning of just {(1-ratio)*100:.0f}% suffices: ≳{r.oxide_decades_to_match:.2f} decades."
          f" Re-adjusting V_t at every rung —")
    print(f"     what a fab actually does — gives I ∝ C_ox exactly and costs"
          f" ≳{r.oxide_decades_to_match_fixed_vt:.2f} decades, about twice as much.")
    print(f"     The BAND is the recipe-carrying part; strain's zero is not, so lead with the zero.]\n")

    print(f"  The fork — one node, two processes, and they want OPPOSITE signs:")
    print(f"      {'mechanism':<44} {'carrier':<10} {'sign':<13} {'µ':>7} {'drive (cited)':>14}")
    for key, m in r.mechanisms.items():
        floor = ">" if m.mobility_is_floor else " "
        mark = "  ← WIRED" if m.wired else "  ← cited data only (no pMOS here)"
        print(f"      {m.name:<44} {m.carrier:<10} {m.sign:<13} {floor}{m.mobility_factor:>6.2f}×"
              f" {m.drive_factor:>13.2f}×{mark}")
    print(f"    → chip.device is n-channel-only, so only {r.wired} is wired. Asking for the hole leg on")
    print(f"      this device does not return a number — it raises, and the REASONING is the point, so")
    print(f"      the message is printed far enough to carry it:")
    for line in _wrap(r.hole_leg_refused, 92):
        print(f"        {line}")
    print(f"      Applying a pMOS technique's COMPRESSIVE strain to an electron channel would degrade it")
    print(f"      while looking like a result. That the two carriers disagree is why the era needed two")
    print(f"      different processes on one die — not an oversight in this model.\n")

    print(f"  The wired leg, through the real device.py — and the bound it cannot avoid:")
    print(f"    µ {r.channel.mu_unstrained_cm2_Vs:.0f} → {r.channel.mu_strained_cm2_Vs:.0f} cm²/V·s"
          f"  ({r.channel.mobility_factor:.2f}×, the HEADLINE — what strain actually buys)")
    print(f"    I_Dsat {r.i_dsat_A*1e6:.0f} → {r.i_dsat_strained_A*1e6:.0f} µA/µm"
          f"  ({r.i_dsat_strained_A/r.i_dsat_A:.3f}× — an UPPER BOUND, and here is its direction)")
    print(f"      the long-channel form carries I ∝ µ: elasticity 1 BY CONSTRUCTION, no other option.")
    print(f"      the cited 90 nm devices measured {st.TENSILE_CESL.drive_factor:.2f}× (nMOS) and"
          f" {st.SIGE_SD.drive_factor:.2f}× (pMOS) — elasticity")
    print(f"      (drive−1)/(µ−1) = {st.TENSILE_CESL.cited_elasticity:.3f} on BOTH carriers, from ONE paper."
          f" ⇒ this model overstates the")
    print(f"      drive win by ×{r.drive_overstatement:.1f}. [report the 0.500-on-both as a COINCIDENCE, not a law —")
    print(f"      two rounded pairs landing on one ratio; the independent {st.SHORT_CHANNEL_L_NM:.0f} nm point is"
          f" {st.SHORT_CHANNEL_CROSSCHECK:.2f}]")
    print(f"    → the elasticity FALLS with L — strain acts increasingly through injection velocity rather")
    print(f"      than mobility in the quasi-ballistic regime — so the long-channel 1 is an upper bound")
    print(f"      whose LOOSENESS GROWS as the era advances. Velocity saturation is NAMED, not built:")
    print(f"      building it means replacing device.py's I_Dsat, and that is a device-model change.\n")

    print(f"    [and the wire takes its cut of whatever is left. F4 proved ∂ln f/∂ln I_Dsat = 1 − wire_share,")
    print(f"     EXACT at every I_Dsat, so the honest chain is: +{r.channel.mobility_factor*100-100:.0f}% mobility"
          f" → at most +{r.channel.drive_factor_long_channel*100-100:.0f}% drive")
    print(f"     (long-channel bound; ~+{r.channel.drive_factor_cited*100-100:.0f}% measured) → ×(1 − wire_share) on chip speed."
          f" NO wire_share is quoted:")
    print(f"     chip.interconnect's bulk path refuses below ~0.194 µm and a 90 nm line is deep inside that")
    print(f"     refusal, so a 90 nm figure would be fabricated. The law is the claim; the number is not.]\n")


def save_figure(r: StrainHistoryResult) -> Path:
    """Render and save the B10 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    import matplotlib.pyplot as plt

    OXIDE_COLOR = "tab:red"
    STRAIN_COLOR = "tab:green"
    MODEL_COLOR = "tab:gray"
    ELECTRON_COLOR = "tab:blue"
    HOLE_COLOR = "tab:purple"

    fig, axes = plt.subplots(1, 3, figsize=(17.6, 6.4))

    # --- Left: two currencies — the oxide lever climbs, the strain lever is horizontal ---------------- #
    ax = axes[0]
    # The ladder runs to a 3.5× gain; the panel shows the window the comparison lives in, because a
    # 5-decade y-axis would render the two paths as one flat pair of lines and hide the whole contrast.
    X_HI = 1.60
    shown = r.drive_gain_oxide <= X_HI
    ax.semilogy(r.drive_gain_oxide[shown], r.j_gate_oxide[shown], "-", color=OXIDE_COLOR, lw=2.4,
                label=f"thin the gate oxide (from {PERIOD_T_OX_UM*1e3:.1f} nm)\n"
                      f"— buys drive, PAYS in gate leakage")
    ax.plot([1.0, r.channel.drive_factor_long_channel], [r.j_gate_A_cm2, r.j_gate_strained_A_cm2],
            "-", color=STRAIN_COLOR, lw=3.2,
            label=f"strain the channel ({r.channel.sign}, {r.channel.mobility_factor:.2f}× µ)\n"
                  f"— buys drive, pays NOTHING: ∂J_g/∂µ = 0")
    ax.annotate("", xy=(r.channel.drive_factor_long_channel, r.j_gate_strained_A_cm2),
                xytext=(1.13, r.j_gate_A_cm2),
                arrowprops=dict(arrowstyle="-|>", color=STRAIN_COLOR, lw=2.8))
    ax.plot([1.0], [r.j_gate_A_cm2], "o", color="k", ms=9, zorder=6)
    ax.annotate(f"the period part — UNSTRAINED silicon,\nµ = {dev.MU_N_EFF:.0f} cm²/V·s"
                f"  (the seam: factor 1.0\nexactly, so both paths leave one point)",
                xy=(1.0, r.j_gate_A_cm2), xytext=(0.040, 0.55), textcoords="axes fraction",
                fontsize=7.0, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color="k", lw=1.0))

    # the cited drive, marked ON the strain path — the bound travels with the number (the right panel)
    ax.plot([r.channel.drive_factor_cited], [r.j_gate_strained_A_cm2], "|", color=STRAIN_COLOR,
            ms=15, mew=2.4, zorder=6)
    ax.annotate(f"cited {r.channel.drive_factor_cited:.2f}×", color="darkgreen",
                xy=(r.channel.drive_factor_cited, r.j_gate_strained_A_cm2), xytext=(0, 9),
                textcoords="offset points", fontsize=6.8, ha="center", va="bottom")

    # the exchange rate — drawn, but labelled as the recipe-carrying consistency note it is
    j_match = hk.gate_leakage(r.oxide_t_ox_matching_um, GATE_DIELECTRIC)
    ax.plot([r.channel.drive_factor_long_channel], [j_match], "o", color=OXIDE_COLOR, ms=9, zorder=6)
    ax.annotate("", xy=(r.channel.drive_factor_long_channel, j_match),
                xytext=(r.channel.drive_factor_long_channel, r.j_gate_A_cm2),
                arrowprops=dict(arrowstyle="<->", color=OXIDE_COLOR, lw=1.4, ls=":"))
    ax.annotate(f"the same drive, the other way:\n{PERIOD_T_OX_UM*1e3:.2f} → "
                f"{r.oxide_t_ox_matching_um*1e3:.2f} nm of oxide, ≳{r.oxide_decades_to_match:.2f} decades\n"
                f"[recipe-carrying: ≳{r.oxide_decades_to_match_fixed_vt:.2f} if V_t is re-adjusted\n"
                f"at every rung. The BAND moves;\nstrain's zero does not — lead with the zero.]",
                xy=(r.channel.drive_factor_long_channel, j_match), xytext=(0.975, 0.965),
                textcoords="axes fraction", fontsize=6.9, color=OXIDE_COLOR, ha="right", va="top",
                arrowprops=dict(arrowstyle="->", color=OXIDE_COLOR, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="lightgray", alpha=0.92))

    ax.set_xlim(0.97, X_HI)
    ax.set_ylim(r.j_gate_A_cm2 * 0.30, r.j_gate_A_cm2 * 4.0e3)
    ax.set_xlabel("drive current  I_Dsat / I_Dsat(period)   [the transistor improving →]")
    ax.set_ylabel("gate leakage  J_g  (A/cm²)   [ratios only — flagged prefactor]")
    ax.set_title("The wall: every period drive lever spends a SECOND currency —\n"
                 "and the mobility term is the one that spends none", fontsize=9.5)
    ax.legend(fontsize=6.9, loc="lower right")
    ax.grid(True, which="both", alpha=0.15)

    # --- Middle: the fork — one node, two processes, opposite signs ----------------------------------- #
    # The bars diverge from a common zero because the SIGNS diverge: a carrier's mechanism is drawn on the
    # side of the stress it needs. The hole bars are labelled CITED DATA ONLY on the panel itself — two
    # bars side by side would otherwise invite the reading that the sim produced both.
    ax = axes[1]
    order = [("sige_sd", HOLE_COLOR, -1.0, 0.0), ("tensile_cesl", ELECTRON_COLOR, +1.0, 1.35)]
    for i, (key, color, direction, y) in enumerate(order):
        m = r.mechanisms[key]
        ax.barh(y + 0.17, direction * m.mobility_gain * 100.0, height=0.30, color=color, alpha=0.85)
        ax.barh(y - 0.17, direction * m.drive_gain * 100.0, height=0.30, color=color, alpha=0.38,
                hatch="//")
        floor = "> " if m.mobility_is_floor else ""
        ax.annotate(f"{floor}+{m.mobility_gain*100:.0f}%", xy=(direction * m.mobility_gain * 100.0, y + 0.17),
                    xytext=(direction * 6, 0), textcoords="offset points", fontsize=8.4,
                    color=color, fontweight="bold", va="center",
                    ha="left" if direction > 0 else "right")
        ax.annotate(f"+{m.drive_gain*100:.0f}%", xy=(direction * m.drive_gain * 100.0, y - 0.17),
                    xytext=(direction * 6, 0), textcoords="offset points", fontsize=7.4,
                    color=color, va="center", ha="left" if direction > 0 else "right")
        status = "WIRED — the sim's carrier" if m.wired else "CITED DATA ONLY (no pMOS)"
        # each mechanism is captioned on ITS OWN side of the zero, so the caption cannot drift across the
        # divide the panel exists to draw (and cannot collide with the legend in the opposite corner)
        ax.annotate(f"{m.name}\n{m.sign} · {m.carrier} · {status}",
                    xy=(direction * 76.0, y + 0.42), fontsize=7.2, va="bottom",
                    ha="right" if direction > 0 else "left", color=color, fontweight="bold")

    ax.axvline(0.0, color="k", lw=1.6)
    ax.set_yticks([])
    ax.set_ylim(-2.25, 2.10)
    ax.set_xlim(-78.0, 78.0)
    ax.annotate("← COMPRESSIVE (holes)", xy=(0.02, 0.025), xycoords="axes fraction",
                fontsize=7.6, color=HOLE_COLOR, fontweight="bold", ha="left")
    ax.annotate("TENSILE (electrons) →", xy=(0.98, 0.025), xycoords="axes fraction",
                fontsize=7.6, color=ELECTRON_COLOR, fontweight="bold", ha="right")
    ax.annotate("chip.strain.nmos_mobility() RAISES on the hole leg rather than\n"
                "returning its factor: compressive strain on an electron channel\n"
                "would DEGRADE it while looking like a result. The refusal is the\n"
                "era's teaching point — one sign cannot serve both carriers, so the\n"
                "90 nm node shipped two different processes on one die.",
                xy=(0.5, 0.42), xycoords="axes fraction", fontsize=7.0, ha="center", va="top",
                style="italic",
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="lightgray", alpha=0.92))
    # the key, inline rather than as a legend box: the panel's four bars all sit near the zero line, so a
    # legend in any corner lands on top of a caption the fork needs on its own side.
    ax.annotate("solid bar = mobility gain µ  (the HEADLINE — what strain buys)\n"
                "hatched bar = drive-current gain, CITED (measured on the same devices)",
                xy=(0.5, 0.145), xycoords="axes fraction", fontsize=6.9, ha="center", va="center")
    ax.set_xlabel("enhancement over unstrained silicon  (%)   [← compressive · tensile →]")
    ax.set_title("The fork: electrons and holes respond to OPPOSITE stresses,\n"
                 "so one node needed two processes — and only one is wired here", fontsize=9.5)
    ax.grid(True, axis="x", alpha=0.15)

    # --- Right: the bound — what the model infers vs what the devices measured ------------------------ #
    ax = axes[2]
    ax.plot(r.mu_axis, r.drive_model, "-", color=MODEL_COLOR, lw=2.4,
            label="what THIS model infers: I ∝ µ\n(long-channel ⇒ elasticity 1, by construction)")
    ax.fill_between(r.mu_axis, r.drive_cited_90nm, r.drive_model, color=MODEL_COLOR, alpha=0.15)
    ax.plot(r.mu_axis, r.drive_cited_90nm, "--", color=STRAIN_COLOR, lw=2.2,
            label=f"what the 90 nm devices measured:\nelasticity {st.TENSILE_CESL.cited_elasticity:.3f} "
                  f"— BOTH carriers, one paper")
    ax.plot(r.mu_axis, r.drive_cited_25nm, ":", color="tab:brown", lw=2.0,
            label=f"…and {st.SHORT_CHANNEL_CROSSCHECK:.2f} at L = {st.SHORT_CHANNEL_L_NM:.0f} nm "
                  f"(independent):\nthe bound LOOSENS as the era advances")

    marks = {True: ("o", ELECTRON_COLOR), False: ("s", HOLE_COLOR)}
    for label, mu, drive, wired in r.cited_points:
        marker, color = marks[wired]
        dx, ha = 10, "left"
        if "25 nm" in label:                          # the rightmost point captions leftward
            color, dx, ha = "tab:brown", -10, "right"
        ax.plot([mu], [drive], marker, color=color, ms=10, zorder=6, mec="k", mew=0.6)
        ax.annotate(label, xy=(mu, drive), xytext=(dx, -7), textcoords="offset points",
                    fontsize=6.9, color=color, fontweight="bold", ha=ha, va="top")

    # the overstatement, read at the wired leg — the number the bound is worth
    mu_w, drive_w = st.TENSILE_CESL.mobility_factor, st.TENSILE_CESL.drive_factor
    ax.annotate("", xy=(mu_w, drive_w), xytext=(mu_w, mu_w),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1.4))
    ax.annotate(f"×{r.drive_overstatement:.1f} — the wired path's overstatement.\n"
                f"It IS the optimistic number, so the bound\n"
                f"lives beside it rather than in place of it.",
                xy=(mu_w, 0.5 * (drive_w + mu_w)), xytext=(0.975, 0.60),
                textcoords="axes fraction", fontsize=7.0, ha="right", va="top",
                arrowprops=dict(arrowstyle="->", color="k", lw=1.0),
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="lightgray", alpha=0.92))
    ax.plot([1.0], [1.0], "o", color="k", ms=7, zorder=6)
    ax.annotate("the seam (factor 1.0 exactly)", xy=(1.0, 1.0), xytext=(9, -8),
                textcoords="offset points", fontsize=6.9, ha="left", va="top")

    ax.set_xlim(0.98, 2.22)
    ax.set_ylim(0.94, 2.22)
    ax.set_xlabel("mobility enhancement  µ / µ(unstrained)   [the HEADLINE]")
    ax.set_ylabel("drive-current enhancement  I_Dsat / I_Dsat(unstrained)")
    ax.set_title("The bound: the wired path reads elasticity 1 and the real\n"
                 "devices measured 0.5 — so the drive read is an UPPER BOUND", fontsize=9.5)
    ax.legend(fontsize=6.8, loc="upper left")
    ax.grid(True, alpha=0.15)

    fig.suptitle("Historical-modes B10 — strained silicon: µ was the one factor in I_Dsat with no process owner, and the only one that spends no second "
                 "currency (∂J_g/∂µ = 0, structurally)\nthe two carriers want opposite strain signs, so the 90 nm node shipped two processes   ·   and a "
                 "long-channel model infers I ∝ µ while the same paper measured half of it\n— VELOCITY SATURATION IS NAMED, NOT BUILT, so the wired drive "
                 "read is an UPPER BOUND",
                 fontsize=10.0)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.905))
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # µ, ₂, →, ∂, ≳ on legacy codepages

    r = compute()
    print_summary(r)
    try:
        saved = save_figure(r)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
