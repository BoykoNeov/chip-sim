"""CMOS latchup — the bill trench isolation came with (historical mode B12, F7's remainder, slice 1).

The **backward axis** (``docs/plans/historical-modes.md``), *isolation* rung, second half. B5
(:mod:`chip.locos_history`) built the LOCOS bird's beak and the wall it set: the beak eats into the
drawn active stripe from both sides, so a thick field oxide puts a **floor under how closely active
areas can be packed**. Shallow-trench isolation cleared that wall — vertical etched walls have no
lateral oxidant path, so the active width *is* the drawn width. That successor is **already in the
tree**: :attr:`chip.locos_history.LocosCrossSection.sti_active_um`.

This module is what the successor **cost**. Packing devices closer packs the *parasitic* devices
closer too: between an n-channel device in the p-substrate and its neighbouring n-well sits a
four-layer pnpn structure — a parasitic npn (n⁺ source / p-substrate / n-well) cross-coupled with a
parasitic pnp (p⁺ / n-well / p-substrate) — which can latch into a self-sustaining low-impedance short
from supply to ground and destroy the part. The density STI bought is the parasitic npn's base width.

**No new device structure is added here.** There is no pMOS in this simulator, no well, and no bipolar
device model, and this module adds none. It evaluates the two **lumped criteria** the literature
states, against geometry and material properties the sim already computes. That is the whole scope,
and §"What this refuses to do" below is where it stops.

The two conditions — independent, and moved by different processes
-------------------------------------------------------------------
Latchup needs **both**, and this is the module's spine (the shape of F3's "one thickness, two
currencies"):

**(A) Sustaining — the loop gain.** *CITED verbatim* (TU Graz, Hadley, *Latch-Up*): "The product of
the gains of the two parasitic transistors in the feedback loop, β₁×β₂, has to be greater than one to
make latch-up possible." Corroborated (EDN/Planet Analog): "The transistor current gain product of Qn
and Qp must be greater than 1."

**(B) Triggering — the resistive drop.** *CITED verbatim* (TU Graz): latch-up initiates when
"sufficient current flows through R_p to turn on the npn-transistor (``I*Rp > 0.7 V``)." Corroborated
(EDN): "The holding current has been shown to be strongly dependent on Rwell and Rsub … a low Rwell or
Rsub means a higher current has to flow to maintain forward bias on the base-emitter junctions."

**These are not the same length, and this module refuses to couple them.** ``R_sub`` is the resistance
from the injection point to the nearest **substrate tap**; the spacing that sets the parasitic npn's
**base width** is n⁺-to-well. Both sources treat them as separate design levers — EDN lists "reduce
beta by increasing device spacing" and "increase well and substrate doping concentrations to reduce
Rwell and Rsub" as two different items. A model in which ``R_sub ∝ spacing`` would manufacture a sign
reversal between the two conditions that is an artifact of its own geometry lump, not physics — the
calibration-wearing-a-physics-hat trap :mod:`chip.locos_history` names. So, stated as a property of
this module: **the resistance term is silent on spacing, and the gain term is silent on doping.**

Direction with spacing — CITED, and a reading trap recorded
-------------------------------------------------------------
TU Graz: "Larger spacing of source/drain areas to the well-borders will increase the base width and
worsens the parasitic transistor." *Worsens the parasitic transistor* = makes it a worse transistor =
**lower β** = more immune. An automated summary of that same page glossed this as "thereby increasing
β", which **inverts the sign**. EDN settles it — "Reduce beta by increasing device spacing" — and that
is the direction implemented here. The inversion is recorded because it is the kind of error that
survives review: it is a plausible-sounding sentence about a real quantity, pointing the wrong way.

What the gain term can and cannot say (read this before using ``loop_gain``)
------------------------------------------------------------------------------
β is built from the **standard base-transport closed form** with emitter efficiency γ = 1::

    α_T = 1 / cosh(W_B / L)        β = α_T / (1 − α_T) = 1 / (cosh(W_B / L) − 1)

with ``L = √(D·τ)`` the minority-carrier diffusion length **the sim already computes**
(:func:`chip.lifetime.diffusion_length`, whose τ already falls with metal contamination, dislocations
and implant damage). There is **no fitted prefactor** in that form.

But it is an **upper bound so loose it does not discriminate in absolute terms**, and saying so is part
of the slice. At this sim's geometries ``W_B ≪ L`` by two to four orders (a µm-scale base against a
diffusion length of ~27 µm on a contaminated wafer and ~1900 µm on a clean one), so each β lands at
10²–10⁶ — and their **product** at 10⁴–10¹² — where real parasitic laterals are ~1–50 and their product
is of order 1–10³. The reason is physical, not numerical: **recombination in the base is not what limits these
transistors** — geometry is. Most of the carrier injected at the n⁺ goes *down* into the substrate
rather than laterally to the well, and that collection efficiency needs a 2-D solve of a structure
this module does not have. γ = 1 then removes the other limiter.

So:

* **Usable:** the *sign* and the *ratio*. β falls monotonically with base width; the ratio between two
  isolation schemes at the same τ is the comparative statement this module exists to make.
* **Not usable:** the absolute value, and any pass/fail built on it. In bulk silicon the sustaining
  condition is satisfied at every geometry this model spans — which is **not a finding of the model**,
  it is what an unbounded β must give. It happens to agree with why the literature's prevention
  measures are all about the *other* condition (epi substrates, guard rings, substrate taps: every one
  of them a resistance or collection measure), but this module claims the agreement, not a derivation.

**Therefore the discriminating condition here is (B), the trigger.** :class:`LatchupMargin` reports
both, and its verdict rests on the trigger current.

Where each number comes from (and what is flagged)
----------------------------------------------------
* **CITED** — ``BE_TURN_ON_V = 0.7`` (the trigger inequality's own constant); ``LOOP_GAIN_CRITICAL =
  1.0``; ``STI_DEPTH_UM`` within the cited 0.25–0.40 µm band for 0.25/0.18 µm-generation STI.
* **EXISTING, VALIDATED** — ``L = √(D·τ)`` (:mod:`chip.lifetime`); substrate resistivity from the
  Masetti mobility (:func:`chip.junction.mobility`, cited); the spacing itself, from
  :mod:`chip.locos_history`.
* **DERIVED** — the transport factor, with no free coefficient (γ = 1 named above).
* **FLAGGED** — :data:`WELL_DEPTH_UM` (the vertical pnp's base width; there is no well in this sim);
  :data:`SUBSTRATE_TAP_PATH_UM` and :data:`TAP_CROSS_SECTION_UM2` (a lumped tap geometry, chosen so
  ``R_sub`` lands in the hundreds-of-Ω–kΩ band real substrates show, which is a **calibration**);
  the trench's ``2 ×`` detour contribution to base width (the honest straight-line path under a
  trench, named not fitted).

**Because the tap geometry is a calibration, every headline built on this module must be a ratio in
which it cancels.** An absolute trigger current in mA is reportable and is never the claim.

The guard that rides with the lifetime axis
---------------------------------------------
Because ``L = √(D·τ)``, a **dirtier wafer has a weaker parasitic transistor** — real (lifetime-killing
was historically used to suppress latchup) and a genuine composition with the existing contamination
chain. But the *same* τ feeds :func:`chip.lifetime.generation_leakage_density`: immunity bought that
way **is paid for in leakage**. Any read of latchup against τ — test, figure or game grade — must
report the leakage at the same τ beside it. Shown alone it would be a free lunch this model has not
earned; the honest statement is the pair, that lifetime-killing trades one failure for another.

What this refuses to do (honest ceilings, stated so the omission is not silent)
--------------------------------------------------------------------------------
* **No pMOS, no well, no bipolar device model** — the parasitic pair is a lumped two-transistor
  criterion. ``β_pnp`` rides :data:`WELL_DEPTH_UM`, a house number standing in for a structure that
  does not exist here.
* **No holding voltage or holding current.** Cited as the thing that decides whether latchup is
  *destructive* ("any structure with a latchup holding voltage higher than its supply voltage will be
  immune"), and not computed — it needs the on-state I–V of the latched thyristor.
* **No guard rings, no tap density, no well taps.** Cited as the other prevention families; the model
  carries one lumped tap path, so "add more taps" is not a knob here.
* **No trench process.** The trench enters as a **depth** that lengthens the parasitic base and as the
  absence of a beak. Etch profile, liner, fill and STI-induced channel stress are not modelled.
* **No injection source.** Real latchup is triggered by an I/O overshoot or a radiation event. The
  injected current is taken as **given**; this module reports margin against it.

Units — µm-native at the boundary, CGS inside
-----------------------------------------------
Lengths in **µm** (spacing, base width, trench depth, well depth, tap path) — the
:mod:`chip.oxidation`/:mod:`chip.locos_history` cross-module currency. :mod:`chip.lifetime` works in
**cm** (``D_MINORITY`` in cm²/s, so its ``diffusion_length`` returns cm); that conversion happens
**once**, in :func:`diffusion_length_um`, and is asserted in a test. Doping cm⁻³; resistivity Ω·cm;
resistance Ω; current A; voltage V; β and loop gain dimensionless.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import junction, lifetime

# --------------------------------------------------------------------------- #
# 0. Constants — cited, and flagged, kept apart
# --------------------------------------------------------------------------- #
UM_PER_CM = 1.0e4                 # 1 cm = 1e4 µm — the one unit seam (see diffusion_length_um)

Q_ELEMENTARY = junction.Q_ELEMENTARY   # C — reuse, don't redeclare

# CITED — the trigger inequality's own constant: latch-up initiates when I·R_sub > 0.7 V (TU Graz).
BE_TURN_ON_V: float = 0.7

# CITED — the sustaining criterion: β_npn·β_pnp > 1 (TU Graz; corroborated EDN/Planet Analog).
LOOP_GAIN_CRITICAL: float = 1.0

# CITED — shallow-trench isolation depth, 250–400 nm for 0.25/0.18 µm-generation STI. Mid-band.
STI_DEPTH_UM: float = 0.35

# DERIVED FROM B5, pinned as a constant — twice the bird's-beak length chip.locos_history computes at
# its reference field-oxidation recipe (2 × birds_beak_length_um(field_oxide_thickness_um()) = 0.926 µm,
# the beak eating active area from BOTH edges of the isolation region). It is a *pinned* number rather
# than a live call because the beak costs a 2-D solve and the game would pay it per wafer; a test asserts
# it still matches chip.locos_history, so the two modes cannot drift apart silently.
#
# This is what makes B12 the second half of B5 rather than a module beside it: the spacing LOCOS gives
# up is not a house guess, it is the beak B5 already computed.
LOCOS_BEAK_ALLOWANCE_UM: float = 0.926

# FLAGGED — the vertical pnp's base width is the well depth, and this sim has no well. A period
# n-well is a few µm deep; this stands in for the structure. Enters β_pnp only.
WELL_DEPTH_UM: float = 3.0

# FLAGGED (a calibration, and named as one) — a lumped substrate-tap geometry. R_sub is the resistance
# from the injection point to the nearest tap; the path length and the spreading cross-section are a
# house lump exactly like chip.interconnect's wire length and chip.contact_resistance's contact length.
# Chosen so R_sub lands in the hundreds-of-Ω-to-kΩ band real substrates show (≈1 kΩ at 1e15 cm⁻³).
# EVERY HEADLINE BUILT ON THIS MODULE MUST BE A RATIO IN WHICH THESE CANCEL.
SUBSTRATE_TAP_PATH_UM: float = 25.0
TAP_CROSS_SECTION_UM2: float = 3600.0        # ≈ 60 µm × 60 µm of spreading area

# The substrate is p-type; the Masetti fit is keyed by dopant.
SUBSTRATE_DOPANT: str = "B"


# --------------------------------------------------------------------------- #
# 1. Geometry — the parasitic npn's base width, and what a trench does to it
# --------------------------------------------------------------------------- #
def lateral_base_width_um(spacing_um: float, *, trench_depth_um: float = 0.0) -> float:
    """The parasitic lateral npn's base width (µm) — the n⁺-to-well spacing, plus any trench detour.

    With no trench the base is the spacing itself. A trench between the two devices blocks the direct
    lateral path, so an injected carrier must go **down one wall and up the other**: the honest
    straight-line detour is ``+2 · trench_depth`` (FLAGGED as a geometric statement, not a fit).

    Wider base ⇒ lower gain ⇒ more immune — the cited direction ("larger spacing … worsens the
    parasitic transistor", TU Graz; "reduce beta by increasing device spacing", EDN).
    """
    if spacing_um <= 0.0:
        raise ValueError(f"spacing_um must be > 0, got {spacing_um}")
    if trench_depth_um < 0.0:
        raise ValueError(f"trench_depth_um must be ≥ 0, got {trench_depth_um}")
    return spacing_um + 2.0 * trench_depth_um


def diffusion_length_um(tau_s: float, D: float = lifetime.D_MINORITY) -> float:
    """The minority-carrier diffusion length in **µm** — the module's single unit seam.

    :func:`chip.lifetime.diffusion_length` returns **cm** (its module's CGS currency). This module is
    µm-native, so the conversion happens here, once, and nowhere else. Asserted in a test.
    """
    return lifetime.diffusion_length(tau_s, D) * UM_PER_CM


# --------------------------------------------------------------------------- #
# 2. Gain — the base-transport closed form (no fitted prefactor; γ = 1, an upper bound)
# --------------------------------------------------------------------------- #
def base_transport_factor(base_width_um: float, diffusion_length_um_: float) -> float:
    """The base transport factor ``α_T = 1/cosh(W_B/L)`` — the fraction of injected carriers that
    cross the base without recombining. Standard bipolar closed form; no free coefficient."""
    if base_width_um <= 0.0:
        raise ValueError(f"base_width_um must be > 0, got {base_width_um}")
    if diffusion_length_um_ <= 0.0:
        raise ValueError(f"diffusion length must be > 0, got {diffusion_length_um_}")
    return 1.0 / math.cosh(base_width_um / diffusion_length_um_)


def bipolar_gain(base_width_um: float, diffusion_length_um_: float) -> float:
    """Parasitic common-emitter gain ``β = α_T/(1−α_T) = 1/(cosh(W_B/L) − 1)``, with γ = 1.

    **An upper bound, and a loose one** — see the module docstring. At this sim's geometries
    ``W_B ≪ L``, so this returns 10³–10⁶ where real parasitic laterals are ~1–50, because
    recombination is not what limits them (geometry is, and that needs a 2-D structure this module
    does not have). **Use the sign and the ratio; never the absolute value, and never a pass/fail.**
    """
    alpha = base_transport_factor(base_width_um, diffusion_length_um_)
    return alpha / (1.0 - alpha)


def loop_gain(spacing_um: float, tau_s: float, *, trench_depth_um: float = 0.0,
              well_depth_um: float = WELL_DEPTH_UM, D: float = lifetime.D_MINORITY) -> float:
    """The sustaining criterion's quantity ``β_npn · β_pnp`` (dimensionless) — **comparative only**.

    ``β_npn`` rides the lateral base (spacing, plus any trench detour); ``β_pnp`` rides the vertical
    base (the well depth, FLAGGED). Both use the same diffusion length, so contamination moves them
    together. Compare two isolation schemes with this; do **not** test it against
    :data:`LOOP_GAIN_CRITICAL` and report the boolean as a finding (module docstring says why).
    """
    L = diffusion_length_um(tau_s, D)
    beta_npn = bipolar_gain(lateral_base_width_um(spacing_um, trench_depth_um=trench_depth_um), L)
    beta_pnp = bipolar_gain(well_depth_um, L)
    return beta_npn * beta_pnp


# --------------------------------------------------------------------------- #
# 3. Resistance and trigger — the condition that actually discriminates
# --------------------------------------------------------------------------- #
def resistivity_ohm_cm(N_sub: float, dopant: str = SUBSTRATE_DOPANT) -> float:
    """Substrate resistivity ``ρ = 1/(q·N·µ(N))`` (Ω·cm), on the **cited** Masetti mobility.

    Not new physics: :func:`chip.junction.mobility` is the same fit the sheet-resistance integral has
    used since Phase 1a, evaluated here at a single bulk concentration.
    """
    if N_sub <= 0.0:
        raise ValueError(f"N_sub must be > 0, got {N_sub}")
    return 1.0 / (Q_ELEMENTARY * N_sub * junction.mobility(N_sub, dopant))


def substrate_resistance_from_resistivity_ohm(rho_ohm_cm: float, *,
                                              path_um: float = SUBSTRATE_TAP_PATH_UM,
                                              area_um2: float = TAP_CROSS_SECTION_UM2) -> float:
    """``R_sub = ρ · path / area`` (Ω) from a resistivity that has **already been computed**.

    The entry point for a consumer that already holds ρ — the fab line derives
    ``Recipe.substrate_resistivity_ohm_cm`` from its own Scheil doping, and recomputing it here from
    ``N`` would be a second, silently-divergent path to the same number.
    :func:`substrate_resistance_ohm` is the doping-side convenience that delegates to this.
    """
    if rho_ohm_cm <= 0.0:
        raise ValueError(f"rho_ohm_cm must be > 0, got {rho_ohm_cm}")
    if path_um <= 0.0:
        raise ValueError(f"path_um must be > 0, got {path_um}")
    if area_um2 <= 0.0:
        raise ValueError(f"area_um2 must be > 0, got {area_um2}")
    path_cm = path_um / UM_PER_CM
    area_cm2 = area_um2 / (UM_PER_CM ** 2)
    return rho_ohm_cm * path_cm / area_cm2


def substrate_resistance_ohm(N_sub: float, *, path_um: float = SUBSTRATE_TAP_PATH_UM,
                             area_um2: float = TAP_CROSS_SECTION_UM2,
                             dopant: str = SUBSTRATE_DOPANT) -> float:
    """``R_sub`` (Ω) — injection point to the nearest substrate tap, on a **lumped** tap geometry.

    ``R = ρ · path / area``. The path and area are FLAGGED house numbers (module docstring); they
    cancel in every ratio this module is meant to produce. Doping is the physical lever: heavier
    substrate ⇒ lower ρ ⇒ lower ``R_sub`` ⇒ higher trigger current — the cited prevention direction.

    **Silent on spacing by construction** (see the module docstring): no argument here is the
    device-to-well spacing, and that is deliberate.
    """
    return substrate_resistance_from_resistivity_ohm(
        resistivity_ohm_cm(N_sub, dopant), path_um=path_um, area_um2=area_um2)


def epi_substrate_resistance_ohm(rho_epi_ohm_cm: float, t_epi_um: float,
                                 rho_substrate_ohm_cm: float, *,
                                 path_um: float = SUBSTRATE_TAP_PATH_UM,
                                 area_um2: float = TAP_CROSS_SECTION_UM2) -> float:
    """``R_sub`` (Ω) for a lightly-doped **epitaxial layer on a heavily-doped substrate** — the lever.

    The cited prevention measure (TU Graz: *"EPI layer is more lightly doped than the substrate that is
    highly doped"*), as the only thing it is in this model: a **resistance in two series pieces**.

    A uniform lightly-doped wafer makes the current run the whole tap path *sideways* through high
    resistivity. Grow a thin lightly-doped layer on a heavily-doped substrate and the current instead
    hops **straight down** through the thin layer into what is nearly a short, then travels the tap path
    through the low-resistivity substrate::

        R = ρ_epi·t_epi/A   (down through the layer)  +  ρ_sub·path/A   (sideways underneath)

    Both terms are kept. Dropping the second would make the resistance fall without limit as the layer
    thins, and it does not: the heavily-doped substrate's own term is a **floor**, which is why thinning
    the layer stops helping. That floor is derived here, not asserted.

    **What this is not.** It is not an epitaxy *process* and it is not F6's retrograde-well leg. Nothing about the doping
    profile the device sees changes — no buried layer, no retrograde well, no ``V_t`` shift. This
    function changes one resistance. The cited **optimum** epi thickness (a real effect) is **not**
    reproduced: it involves the vertical pnp this model does not carry, so what is supportable here is
    only that thinner is monotonically better down to the floor.

    **And that floor does not bind (F6 re-check, 2026-09-06).** Setting the two terms equal puts it at
    ``t_epi = rho_handle*path/rho_epi`` = **0.025 um** at the era numbers -- 12x below the thinnest layer
    :mod:`chip.demo_latchup_history` sweeps, where the trigger is still only 7.7 % of the floor-limited
    value. So "monotonically better down to the floor" is true and *operationally vacuous*: across every
    thickness anyone actually grows, the reward for thinning is unopposed **in this model**. What stops
    it in a real fab is the handle's dopant **out-diffusing up into the growing layer**
    (``sqrt(Dt) ~ 0.05-0.7 um``) -- a doping-profile effect with a resistance consumer, which is why it
    belongs to neither leg named above and is the promotable third leg of the split F6 card. See
    ``docs/plans/future-steps.md`` -> "The F6 re-check". **Not built here.**
    """
    if rho_epi_ohm_cm <= 0.0:
        raise ValueError(f"rho_epi_ohm_cm must be > 0, got {rho_epi_ohm_cm}")
    if t_epi_um <= 0.0:
        raise ValueError(f"t_epi_um must be > 0, got {t_epi_um}")
    if rho_substrate_ohm_cm <= 0.0:
        raise ValueError(f"rho_substrate_ohm_cm must be > 0, got {rho_substrate_ohm_cm}")
    area_cm2 = area_um2 / (UM_PER_CM ** 2)
    vertical = rho_epi_ohm_cm * (t_epi_um / UM_PER_CM) / area_cm2
    lateral = substrate_resistance_from_resistivity_ohm(
        rho_substrate_ohm_cm, path_um=path_um, area_um2=area_um2)
    return vertical + lateral


def trigger_current_a(R_sub_ohm: float, *, v_be: float = BE_TURN_ON_V) -> float:
    """The substrate current that forward-biases the parasitic base–emitter: ``I = V_be / R_sub`` (A).

    The cited inequality ``I·R_sub > 0.7 V`` at equality — a **definition**, satisfied by
    construction, and asserted as an identity in the tests.
    """
    if R_sub_ohm <= 0.0:
        raise ValueError(f"R_sub_ohm must be > 0, got {R_sub_ohm}")
    return v_be / R_sub_ohm


# --------------------------------------------------------------------------- #
# 4. The bundle — both conditions, reported together, verdict on the trigger
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LatchupMargin:
    """A latchup evaluation: both cited conditions, with the verdict resting on the trigger.

    ``spacing_um`` / ``base_width_um`` the device-to-well spacing and the parasitic base it implies;
    ``loop_gain`` the sustaining quantity β_npn·β_pnp (**comparative only** — an upper bound, see
    :func:`bipolar_gain`); ``r_sub_ohm`` the lumped tap resistance; ``i_trigger_a`` the substrate
    current that forward-biases the junction. Plain scalars — the loose-coupling currency (ADR 0002).
    """

    spacing_um: float
    base_width_um: float
    loop_gain: float
    r_sub_ohm: float
    i_trigger_a: float

    @property
    def i_trigger_ma(self) -> float:
        """The trigger current in mA — the readable unit for a figure axis."""
        return self.i_trigger_a * 1.0e3

    @property
    def sustainable(self) -> bool:
        """Whether the loop gain clears the cited criterion.

        **True at every geometry this model spans**, and that is a property of an unbounded β, not a
        finding — :func:`bipolar_gain` says why. Exposed because the criterion is cited and the number
        should be visible, *not* as a discriminator.
        """
        return self.loop_gain > LOOP_GAIN_CRITICAL

    def latches(self, injected_current_a: float) -> bool:
        """Whether an injected substrate current triggers latchup — the discriminating verdict.

        Both cited conditions, in the order they apply: the loop must be able to sustain, and the
        injected current must clear the trigger. The injection source is **given**, not modelled.
        """
        return self.sustainable and injected_current_a >= self.i_trigger_a

    def margin_ratio(self, injected_current_a: float) -> float:
        """``I_trigger / I_injected`` — headroom as a dimensionless ratio (> 1 is safe).

        The ratio form is the one to grade on: the FLAGGED tap geometry scales ``i_trigger_a``, so a
        *relative* margin between two lines is meaningful where an absolute mA number is a house
        number.
        """
        if injected_current_a <= 0.0:
            raise ValueError(f"injected_current_a must be > 0, got {injected_current_a}")
        return self.i_trigger_a / injected_current_a


def latchup_margin(spacing_um: float, N_sub: float | None, tau_s: float, *,
                   rho_ohm_cm: float | None = None,
                   trench_depth_um: float = 0.0, well_depth_um: float = WELL_DEPTH_UM,
                   path_um: float = SUBSTRATE_TAP_PATH_UM,
                   area_um2: float = TAP_CROSS_SECTION_UM2,
                   dopant: str = SUBSTRATE_DOPANT,
                   D: float = lifetime.D_MINORITY) -> LatchupMargin:
    """Evaluate both latchup conditions for one geometry / substrate / lifetime.

    The two chains stay separate all the way down, which is the module's point: ``spacing`` (and the
    trench) reach only the gain; the substrate reaches only the resistance; ``tau_s`` reaches only the
    gain (via ``L = √(D·τ)``). Nothing couples them.

    Give the substrate **either** way, not both: ``N_sub`` (doping, resistivity derived here) or
    ``rho_ohm_cm`` (a resistivity the caller already holds — the fab line's route, so the game's own
    Scheil-derived number is not silently recomputed by a second path).
    """
    if (N_sub is None) == (rho_ohm_cm is None):
        raise ValueError("give exactly one of N_sub or rho_ohm_cm (the substrate, one way only)")
    base_w = lateral_base_width_um(spacing_um, trench_depth_um=trench_depth_um)
    gain = loop_gain(spacing_um, tau_s, trench_depth_um=trench_depth_um,
                     well_depth_um=well_depth_um, D=D)
    r_sub = (substrate_resistance_from_resistivity_ohm(rho_ohm_cm, path_um=path_um, area_um2=area_um2)
             if rho_ohm_cm is not None
             else substrate_resistance_ohm(N_sub, path_um=path_um, area_um2=area_um2, dopant=dopant))
    return LatchupMargin(
        spacing_um=spacing_um, base_width_um=base_w, loop_gain=gain,
        r_sub_ohm=r_sub, i_trigger_a=trigger_current_a(r_sub),
    )
