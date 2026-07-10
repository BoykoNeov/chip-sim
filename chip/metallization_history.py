"""Aluminium junction spiking — the shallow-junction short (historical-modes B6).

The **backward axis** (``docs/plans/historical-modes.md``): the simulator's contact metallization, run
in its pre-barrier *period* mode (pure evaporated aluminium), so the limitation that motivated **Al–Si
alloys, then barrier metals (Ti/TiN, Ti–W), then Cu damascene** becomes visible on an observable the sim
already computes — the reverse-junction leakage :mod:`chip.lifetime` owns. Like :mod:`chip.doping_history`
(A1) and :mod:`chip.oxidation_history` (A3), this is a **pure consumer**: it adds *no* physics to and
changes *no* behaviour in the modules it reads (:mod:`chip.lifetime`, :mod:`chip.junction`).

The payload coupling (the discriminator — *the shallower the junction, the worse the spike*)
-------------------------------------------------------------------------------------------
Aluminium and silicon form a eutectic at **577 °C** (Al–Si binary; Murray & McAlister, *Bull. Alloy
Phase Diagrams* 5(1):74, 1984). Even during a **sub-eutectic sinter** (~400–500 °C, to form the ohmic
contact), silicon **dissolves into the aluminium up to its solid solubility ``S(T)``** — which rises from
a fraction of a percent at 400 °C to the maximum **~1.5 wt %** at the 577 °C eutectic. The aluminium film
(thickness ``t_Al``) is the sink; a thick line over a small contact is a large reservoir, so it keeps
drawing silicon from the contact. Crucially the dissolution is **not uniform**: it concentrates at
grain-boundary / crystallographic spots, so instead of the contact receding uniformly by the small
*average* consumed depth, a few localized **spikes** of aluminium penetrate **far deeper**. When a spike
reaches past the junction depth ``x_j``, the aluminium filament **shorts the junction** → a leaky/dead
diode. Ion implantation made junctions *shallower* (``x_j`` down to tenths of a µm) — which is exactly
what makes spiking worse, and why the shallow-junction era forced Al–Si alloys and diffusion barriers.

The graded failure — a *shorted-area fraction*, not a cliff (``gradual-failure-preferred``)
-------------------------------------------------------------------------------------------
The honest failure mode is **spatial**: spike depths are non-uniform (grain statistics), so as the
characteristic spike depth ``d_spike`` approaches ``x_j`` the **fraction of the junction area a spike
penetrates rises smoothly from 0 to 1** — some contacts short, then more, a *yield* gradient — rather
than the whole wafer flipping at ``d_spike = x_j``. Modelling spike depths as exponentially distributed
(mean ``d_spike``) gives the shorted-area fraction

    f_short(x_j, d_spike) = exp(−x_j / d_spike)                       ∈ [0, 1]

— monotone: **↑ as ``x_j`` falls** (the coupling), **↑ as ``T`` / ``t_Al`` rise** (deeper spikes),
``→ 1`` when ``d_spike ≫ x_j`` (fully shorted), and **≡ 0 when ``d_spike = 0``** (a perfect barrier — the
seam, no division). That shorted-area fraction is the graded observable (the analogue of the edge-loaded
Na ring's outboard-die kills); a *shorted contact itself* leaks catastrophically (an ~ohmic Al–Si path,
many decades above the generation floor), so the aggregate reverse leakage is

    J_eff = (1 − f_short)·J_intact + f_short·J_short                  (A/cm²)

with ``J_intact`` the intact-junction generation leakage :func:`chip.lifetime.generation_leakage_density`
already computes (so a clean, un-spiked junction returns that value **bit-for-bit**) and ``J_short`` a
flagged ohmic-short density whose *exact magnitude is deliberately not load-bearing* — any appreciable
shorted fraction fails the nA/cm² leakage window by many decades.

The metallization registry (period texture — one real physics axis: how much Si the metal still draws)
------------------------------------------------------------------------------------------------------
Mirroring A1's ``DopingSource``, :class:`MetalScheme` carries the one discriminating axis, ``si_uptake``
∈ [0, 1] — the fraction of the solid-solubility Si budget the metal still pulls from the contact:

  * ``"Al"`` — pure evaporated aluminium (the period metal): ``si_uptake = 1`` → full spiking (**the
    wall**).
  * ``"Al-Si"`` — aluminium **pre-alloyed** with ~1 % Si (saturated at deposition, so it draws little
    more from the contact): a small flagged ``si_uptake`` → strongly suppressed spiking (the *first*
    historical fix).
  * ``"barrier"`` — a diffusion barrier (Ti/TiN, Ti–W) blocks Si transport entirely: ``si_uptake = 0``
    → ``d_spike ≡ 0`` → ``f_short ≡ 0`` → ``J_eff = J_intact`` **bit-for-bit** (the modern default, the
    seam). Cu damascene (F4-forward) is the successor beyond this module's scope.

The default scheme is ``"barrier"`` (the modern result); the *opt-in* enables the period wall (the A1
polarity — the flag turns on the older, limited mode). Sources: Al–Si eutectic / max solubility from the
phase diagram (Murray & McAlister 1984); the spiking mechanism and the alloy/barrier fixes are textbook
(Sze, *VLSI Technology*; Ghandhi, *VLSI Fabrication Principles*; Murarka, *Silicides for VLSI*).

The honesty ladder (per ``historical-modes.md`` triad)
------------------------------------------------------
* **Tight — the seam.** ``si_uptake = 0`` (the default barrier) makes ``d_spike`` *identically* 0, so
  ``f_short`` is *identically* 0 and :func:`spiked_leakage` returns :func:`chip.lifetime.
  generation_leakage_density` **byte-for-byte** — a structural ``(1 − f)·J = J`` at ``f = 0``, not a
  small number.
* **Tight — the sign / topology (the discriminator).** ``f_short`` rises monotonically as ``x_j`` falls
  (spiking shorts the *shallower* junction), as the sinter ``T`` rises (``S(T)`` up), and as ``t_Al``
  rises (bigger sink); and ``→ 1`` as ``d_spike ≫ x_j``. Sign-robust regardless of the flagged
  magnitudes.
* **Flagged — the magnitudes.** The Si-in-Al solubility curve :func:`silicon_solubility_in_al` (its
  *direction* and the ~1.5 wt % eutectic value are cited; the Arrhenius ``S₀, Eₐ`` are house-fitted to a
  couple of phase-diagram anchors), the spike-concentration lump :data:`SPIKE_CONCENTRATION` (lateral
  reservoir × 1/localized-area-fraction), the exponential spike-depth distribution *shape*, and the
  ohmic-short density :data:`SHORT_LEAKAGE_A_CM2`. Calibrated so that at the stated operating point
  (``t_Al = 0.8 µm`` line, ~450–500 °C sinter) **pure Al shorts a ~0.2 µm implant-era junction while a
  ~0.5–1 µm predep-era junction and the barrier stay safe** — the on-the-record validity box (cf. A1's
  ``(T_predep, t_min)`` box).

Named scope edges (honest ceilings, stated so the omission isn't silent)
------------------------------------------------------------------------
* **Pure-consumer wiring (a deliberate divergence from the plan).** ``historical-modes.md`` sketched B6
  as writing *through* :mod:`chip.lifetime` "mirror of the A1 dislocation / G4b metal plugs" — those add
  a term to the ``1/τ`` recombination sum. Junction spiking is a **geometric ohmic short, not an SRH
  recombination centre**, so routing it through ``1/τ`` would be physically wrong (it does not shorten
  the minority-carrier lifetime; it bridges the junction). Instead this module lands on the **same
  ``j_leak`` observable** at the *current* level — reusing lifetime's intact baseline and blending an
  ohmic-short density — and, like A1/A3, edits nothing it consumes.
* **Solubility-saturated worst case (dropped the anneal *time*).** The plan named spiking as
  ``f(anneal T, time)``; this module takes the aluminium as having reached its equilibrium Si solubility
  at the sinter ``T`` (the saturated worst case) and carries the sink size as ``t_Al`` instead. Anneal
  *time* enters only as time-to-saturation, taken as reached — a named edge, not modelled kinetically.
* **Sub-eutectic regime.** ``S(T)`` is clamped at the eutectic maximum (:data:`SI_IN_AL_EUTECTIC_WT`
  above 577 °C); above the eutectic the contact *melts/alloys* (a different regime), not modelled.
* **Aggregate leakage, catastrophic per shorted contact.** The graded quantity is the shorted-area /
  yield fraction ``f_short``; a shorted contact's own leakage is taken ohmic-catastrophic (a fixed
  flagged ``J_short``), not a gently-rising per-contact current — so ``J_eff`` sits far above spec at
  even small ``f_short`` (that *is* the point: a spiked contact is dead).

Units — inherited from the consumed modules (no new currency)
-------------------------------------------------------------
Junction depth and aluminium thickness in **µm** (the cross-module length currency); temperature **°C**;
solubility a dimensionless weight fraction; leakage **A/cm²** (reported nA/cm², as :mod:`chip.lifetime`);
``f_short`` dimensionless (reported %).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import lifetime as lt

# --------------------------------------------------------------------------- #
# Cited constants + flagged calibration (the honesty ladder — see the module docstring)
# --------------------------------------------------------------------------- #
# Al–Si eutectic temperature (°C) and the maximum solid solubility of Si in Al there (weight fraction):
# CITED from the Al–Si binary phase diagram (Murray & McAlister 1984). Silicon dissolves into solid
# aluminium up to ~1.5 wt % at the 577 °C eutectic — the ceiling the sinter approaches from below.
AL_SI_EUTECTIC_CELSIUS = 577.0
SI_IN_AL_EUTECTIC_WT = 0.015          # CITED — ~1.5 wt % max solid solubility at the eutectic

# Arrhenius Si-in-Al solid-solubility curve S(T) = S₀·exp(−Eₐ/kT) (weight fraction). FLAGGED house fit:
# the DIRECTION (rises with T) and the eutectic anchor are cited; S₀/Eₐ are fitted to two phase-diagram
# anchors (~1.5 wt % at 577 °C, ~0.5 wt % at 450 °C ⇒ Eₐ ≈ 0.46 eV), so the CURVE is flagged, not exact.
SI_IN_AL_S0 = 7.84                    # FLAGGED — solubility prefactor (weight fraction)
SI_IN_AL_EA_EV = 0.458                # FLAGGED — solubility activation energy (eV)
K_BOLTZMANN_EV = 8.617333262e-5       # Boltzmann constant (eV/K) — the only new physical constant

# Densities (g/cm³) — to convert the weight-fraction solubility to the VOLUME fraction of Si the Al can
# hold (Si volume consumed per Al volume = w · ρ_Al/ρ_Si). Standard handbook values.
RHO_AL = 2.70
RHO_SI = 2.33

# Spike-concentration lump κ (dimensionless) — FLAGGED. Localized grain-boundary dissolution + the
# lateral Al reservoir make the deepest spikes reach ``κ ×`` the area-averaged consumed depth. Lumps the
# reservoir ratio × 1/localized-area-fraction into one house number; calibrated so pure Al shorts a
# ~0.2 µm junction (0.8 µm line, ~450–500 °C) while a ~0.5–1 µm junction and the barrier stay safe.
SPIKE_CONCENTRATION = 40.0            # FLAGGED — deepest-spike / average-recession ratio

# Ohmic-short leakage density (A/cm²) of a spiked (shorted) junction area — FLAGGED, and deliberately
# NOT load-bearing: an Al–Si filament bridging the junction conducts ~ohmically, orders above the
# generation floor, so any appreciable shorted fraction fails the nA/cm² spec by many decades. The exact
# value only sets *how far past* spec a dead contact sits, not whether it fails.
SHORT_LEAKAGE_A_CM2 = 1.0             # FLAGGED — ~ohmic shorted-area leakage density


# --------------------------------------------------------------------------- #
# 1. Si solid solubility in Al — the T-driven Si budget (FLAGGED curve, cited direction)
# --------------------------------------------------------------------------- #
def silicon_solubility_in_al(T_celsius: float) -> float:
    """Solid solubility of Si in Al at ``T_celsius`` — weight fraction, Arrhenius, clamped at the eutectic.

    ``S(T) = min(S₀·exp(−Eₐ/kT), S_eutectic)`` — rises with temperature (more Si dissolves into the
    aluminium the hotter the sinter) toward the cited **~1.5 wt %** ceiling at the 577 °C eutectic
    (:data:`SI_IN_AL_EUTECTIC_WT`), above which the contact would melt/alloy (a different regime — the
    clamp). The *direction* and the eutectic value are cited (the Al–Si phase diagram); the ``S₀, Eₐ``
    fit is a FLAGGED house calibration to a couple of phase-diagram anchors.
    """
    T_kelvin = T_celsius + 273.15
    if T_kelvin <= 0.0:
        raise ValueError(f"T_celsius must be above absolute zero, got {T_celsius}")
    s = SI_IN_AL_S0 * math.exp(-SI_IN_AL_EA_EV / (K_BOLTZMANN_EV * T_kelvin))
    return min(s, SI_IN_AL_EUTECTIC_WT)


# --------------------------------------------------------------------------- #
# 2. The metallization registry (period texture — one axis: how much Si the metal still draws)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetalScheme:
    """A historical contact metallization: how much Si it still draws from the contact (``si_uptake``).

    ``si_uptake`` ∈ [0, 1] is the **one real physics axis** — the fraction of the solid-solubility Si
    budget the metal pulls from the silicon contact during the sinter:

      * ``1.0`` — pure aluminium (the period metal), full spiking;
      * a small value — Al **pre-alloyed** with Si (``"Al-Si"``), saturated at deposition so it draws
        little more (a FLAGGED partial suppression, the first historical fix);
      * ``0.0`` — a diffusion **barrier** (Ti/TiN, Ti–W) that blocks Si transport, so ``d_spike ≡ 0``
        (the modern default — the exact seam).
    """

    name: str
    si_uptake: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.si_uptake <= 1.0):
            raise ValueError(f"si_uptake must be in [0, 1], got {self.si_uptake}")


# The three period schemes. Pure Al (the wall) → Al–Si alloy (partial fix) → barrier metal (modern seam);
# Cu damascene is the F4-forward successor beyond this module. si_uptake is the discriminator; the rest is
# period flavour. "Al-Si" 0.08 is FLAGGED (a pre-saturated film still draws a little from the contact).
SCHEMES: dict[str, MetalScheme] = {
    "Al": MetalScheme("pure aluminium (period metal)", 1.0),
    "Al-Si": MetalScheme("aluminium pre-alloyed with ~1 % Si", 0.08),
    "barrier": MetalScheme("Ti/TiN diffusion barrier (modern)", 0.0),
}


# --------------------------------------------------------------------------- #
# 3. Spike depth + the graded shorted-area fraction (the discriminator)
# --------------------------------------------------------------------------- #
def spike_depth(
    T_celsius: float,
    al_thickness_um: float,
    scheme: MetalScheme | str = "barrier",
    *,
    concentration: float = SPIKE_CONCENTRATION,
) -> float:
    """Characteristic aluminium spike depth ``d_spike`` (µm) into the contact after the sinter.

    ``d_spike = κ · si_uptake · t_Al · S_vol(T)``, where ``S_vol = S_wt · ρ_Al/ρ_Si`` is the *volume*
    fraction of Si the aluminium can hold (:func:`silicon_solubility_in_al`), ``t_Al`` the film thickness
    (the sink size — the saturated worst case, see the module scope edge), and ``κ`` the FLAGGED
    spike-concentration lump (:data:`SPIKE_CONCENTRATION`). **Exactly 0** for the barrier scheme
    (``si_uptake = 0``) — the seam. Rises with ``T`` (more Si dissolves) and with ``t_Al`` (bigger sink).
    """
    if al_thickness_um < 0.0:
        raise ValueError(f"al_thickness_um must be ≥ 0, got {al_thickness_um}")
    sch = SCHEMES[scheme] if isinstance(scheme, str) else scheme
    s_vol = silicon_solubility_in_al(T_celsius) * (RHO_AL / RHO_SI)
    return concentration * sch.si_uptake * al_thickness_um * s_vol


def shorted_area_fraction(spike_depth_um: float, x_j_um: float) -> float:
    """Fraction of the junction area a spike penetrates past ``x_j`` — ``f = exp(−x_j/d_spike)`` ∈ [0, 1].

    The graded (spatial-non-uniformity) failure: spike depths are exponentially distributed with mean
    ``d_spike``, so the shorted-area fraction is ``exp(−x_j/d_spike)`` — **↑ as ``x_j`` falls** (the
    shallow-junction coupling), **↑ as ``d_spike`` grows**, ``→ 1`` when ``d_spike ≫ x_j``. **Exactly 0
    when ``d_spike = 0``** (the barrier seam — handled without dividing). The exponential *shape* is a
    FLAGGED teaching choice; the *sign/monotonicity* is the tight leg.
    """
    if x_j_um <= 0.0:
        raise ValueError(f"x_j_um must be > 0, got {x_j_um}")
    if spike_depth_um < 0.0:
        raise ValueError(f"spike_depth_um must be ≥ 0, got {spike_depth_um}")
    if spike_depth_um == 0.0:
        return 0.0                                   # perfect barrier — no spikes, the exact seam
    return math.exp(-x_j_um / spike_depth_um)


def spiked_leakage(
    shorted_fraction: float, intact_j_leak: float, j_short: float = SHORT_LEAKAGE_A_CM2,
) -> float:
    """Aggregate reverse leakage ``J_eff = (1−f)·J_intact + f·J_short`` (A/cm²) of a partly-spiked junction.

    Blends the intact-junction generation leakage ``intact_j_leak`` (from :func:`chip.lifetime.
    generation_leakage_density`) over the un-shorted area with the ohmic-short density ``j_short`` over
    the shorted area ``f`` (:func:`shorted_area_fraction`). **Seam:** ``f = 0`` returns ``intact_j_leak``
    **byte-for-byte** (a structural ``(1−0)·J = J``). ``j_short`` is a FLAGGED, deliberately
    non-load-bearing magnitude — any appreciable ``f`` blows the nA/cm² leakage window.
    """
    if not (0.0 <= shorted_fraction <= 1.0):
        raise ValueError(f"shorted_fraction must be in [0, 1], got {shorted_fraction}")
    return (1.0 - shorted_fraction) * intact_j_leak + shorted_fraction * j_short


# --------------------------------------------------------------------------- #
# 4. The bundled spiking reading (the loose-coupling currency the demo/game read)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetalSpiking:
    """One contact's spiking consequence: spike depth, shorted-area fraction, and the leaky-diode j_leak.

    ``scheme`` the metallization; ``T_celsius`` the sinter temperature; ``al_thickness_um`` the film
    (sink); ``x_j_um`` the junction it sits on; ``S_wt`` the Si-in-Al solubility that drove it;
    ``d_spike_um`` the characteristic spike depth; ``f_short`` the shorted-area fraction (the graded
    observable); ``intact_j_leak`` the un-spiked generation leakage; ``j_leak`` the aggregate leakage
    (A/cm²). Plain scalars — the loose-coupling currency (the analogue of
    :class:`chip.lifetime.DiodeLeakage`)."""

    scheme: str
    T_celsius: float
    al_thickness_um: float
    x_j_um: float
    S_wt: float
    d_spike_um: float
    f_short: float
    intact_j_leak: float
    j_leak: float

    @property
    def f_short_percent(self) -> float:
        """Shorted-area (yield-loss) fraction in percent — the graded readout."""
        return self.f_short * 100.0

    @property
    def j_leak_nA_cm2(self) -> float:
        """Aggregate reverse leakage in nA/cm² (the spec-window unit, as :mod:`chip.lifetime`)."""
        return self.j_leak * 1.0e9


def metal_spiking(
    x_j_um: float,
    *,
    scheme: MetalScheme | str = "barrier",
    T_celsius: float = 450.0,
    al_thickness_um: float = 0.8,
    N_A: float = 1.0e17,
    metals=None,
    concentration: float = SPIKE_CONCENTRATION,
    j_short: float = SHORT_LEAKAGE_A_CM2,
    V_J: float = lt.JUNCTION_VOLTAGE_V,
) -> MetalSpiking:
    """Read the spiking consequence off a junction ``x_j_um`` metallized with ``scheme``.

    Wires :func:`spike_depth` → :func:`shorted_area_fraction` → :func:`spiked_leakage`, with the intact
    baseline taken from :func:`chip.lifetime.device_leakage` (so ``metals`` — a
    :class:`chip.purification.Contamination`/dict/``None`` — composes the deep-level-metal leakage under
    the spiking, and a clean wafer gives lifetime's clean floor). **Seam:** the default ``scheme =
    "barrier"`` yields ``d_spike = 0`` → ``f_short = 0`` → ``j_leak`` **equal to** the intact
    :func:`chip.lifetime.device_leakage` value byte-for-byte. *Pure Al on a shallow junction* in, a
    shorted, leaky diode out — the device consequence the modern barrier removes.
    """
    d_spike = spike_depth(T_celsius, al_thickness_um, scheme, concentration=concentration)
    f_short = shorted_area_fraction(d_spike, x_j_um)
    intact = lt.device_leakage(metals, N_A, V_J=V_J).j_leak
    j_leak = spiked_leakage(f_short, intact, j_short)
    sch = SCHEMES[scheme] if isinstance(scheme, str) else scheme
    return MetalSpiking(
        scheme=sch.name, T_celsius=T_celsius, al_thickness_um=al_thickness_um, x_j_um=x_j_um,
        S_wt=silicon_solubility_in_al(T_celsius), d_spike_um=d_spike, f_short=f_short,
        intact_j_leak=intact, j_leak=j_leak,
    )
