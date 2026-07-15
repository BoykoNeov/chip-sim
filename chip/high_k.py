"""High-κ gate dielectric — the one thickness that feeds two currencies (F3).

The **backward axis** (``docs/plans/high-k-metal-gate-f3.md``): the gate dielectric's thickness feeds
**two device quantities with different functional dependence**, and *no single scalar can move both*:

  * **Capacitance** ``C_ox = ε₀·K/t_phys`` — equivalently ``ε_SiO₂/EOT`` with the **electrical**
    thickness ``EOT = t_phys·(3.9/K)``. **Linear in EOT, blind to K and ``t_phys`` separately.** This is
    what :func:`chip.device.oxide_capacitance` already computes, and an EOT *is* the number that belongs
    there **by definition** — see the identity note below.
  * **Direct gate tunnelling** ``J_g = J₀·exp(−α·t_phys)`` — set by the **physical** thickness.
    **Exponential in ``t_phys``, blind to EOT.**

At **fixed EOT**, swapping SiO₂ (K=3.9) for HfO₂ (K=25) multiplies the physical thickness by ``K/3.9``
≈ 6.4× while leaving ``C_ox``, ``V_t`` and ``I_Dsat`` **exactly where they were** — the gate is
electrically identical and the tunnelling current, exponential in that thickness, collapses by orders of
magnitude. That is the historical reason SiO₂ stopped scaling (~1.4 nm: leakage over 1 A/cm² at 1 V,
Robertson) and 45 nm went to HfO₂ in 2007. **High-κ splits one thickness into two currencies, and that
split is the payload** — a scalar "high-κ cuts leakage 1000×" would be decoration, not this.

Why the ``C_ox`` invariance is an *identity*, not a fit (the tight leg)
----------------------------------------------------------------------
``EOT ≡ t_phys·(3.9/K)`` (Robertson eq. 2), so feeding EOT into the SiO₂-permittivity capacitance gives

    C_ox = ε_SiO₂/EOT = (3.9·ε₀)/(t_phys·3.9/K) = ε₀·K/t_phys

— which is **exactly** the physical capacitance of the high-κ layer (Robertson eq. 1, ``C = ε₀KA/t``).
The EOT route is therefore not an approximation: it computes the true ``C_ox`` of the real stack with
**zero barrier physics involved**. Hence ``V_t``/``I_Dsat`` invariance at fixed EOT is *unconditional*,
for any material — the assertable anchor, and the reason :mod:`chip.device` needs no change at all.

The barrier is *not* free — why a single decay constant would be a lie
----------------------------------------------------------------------
The naive story ("6.4× thicker ⇒ 6.4× the exponent") **overstates the win**, because K and the band gap
are **inversely correlated** (Robertson Fig. 5 / Table 2): the high-κ oxides that buy thickness *also*
have a lower tunnelling barrier ``φ_B`` (CB offset to Si) **and** a lower tunnelling mass ``m*``, and
both enter the exponent as ``α ∝ √(m*·φ_B)``. SiO₂ (φ_B=3.2 eV, m*≈0.5) decays ~3.2× faster *per nm*
than HfO₂ (φ_B=1.4 eV, m*≈0.11), so HfO₂'s 6.4× thickness gain nets out to only ~2× in the exponent.
The model therefore carries ``φ_B`` **and** ``m*`` per material (never a universal ``α``, and never a
half-consistent per-material ``φ_B`` with a shared ``m*`` — both terms move together or neither does).

This is also why "more K is better" is **false**, and it falls out of the cited table for free rather
than being modelled: TiO₂ has K=80 (20× SiO₂) but a CB offset of **0** — no barrier at any thickness, so
``α = 0`` and the thickness buys *nothing*. Robertson's requirement is an offset **over 1 eV**; the
industry took K=25/φ_B=1.4 (HfO₂), not K=80/φ_B=0. See :data:`DIELECTRICS`.

The seam — the K=3.9 identity
-----------------------------
``EOT = t_phys·(3.9/K)``, so **at K=3.9, EOT == t_phys** and every existing number is byte-for-byte
today's: :func:`eot` at SiO₂ is the identity on its input. The consumer keeps the dielectric knob absent
by default (today's ``t_ox`` flows through untouched, no leakage emitted), so banked demos are unchanged.

The honesty ladder (per the F3 plan + the ``historical-modes.md`` triad)
-----------------------------------------------------------------------
* **Tight — the seam.** :func:`eot` at K=3.9 returns its input **exactly** (``EOT == t_phys``).
* **Tight — the identity (the discriminator).** ``C_ox`` at fixed EOT is material-**independent** by
  construction (see above): the electrical gate is untouched while ``t_phys`` moves by ``K/3.9``.
* **Tight — the ratio (prefactor-free).** The flagged prefactor ``J₀`` is **shared across materials**, so
  it **cancels exactly** in any leakage *ratio* at fixed EOT: :func:`leakage_decades_saved` is pure
  cited-exponent physics (``φ_B``, ``m*``, ``K``) with **no calibrated constant in it**.
* **Cross-check (non-circular).** The cited constants — sourced from band-offset/effective-mass work,
  **never fitted to a leakage curve** — reproduce the textbook SiO₂ slope of **~1 decade per ~2 Å**
  (this model: 1.78 Å at φ_B=3.2/m*=0.5). The slope is *predicted*, not calibrated. See the tests.
* **Flagged — the magnitudes.** The absolute prefactor :data:`J0_REFERENCE` (a house lump calibrated at
  one SiO₂ point, see below) and the tunnelling masses (HfO₂'s ``m*`` is *fit-extracted* in the
  literature with a wide spread, 0.08–0.2 — which propagates to a 3.9–9.5-decade band on the HfO₂ win at
  EOT=1 nm; the central 0.11 gives ~5.6). Asserted by shape/sign/ratio, never as exact currents.

Named scope edges (honest ceilings, stated so the omission isn't silent)
------------------------------------------------------------------------
* **The interfacial SiO₂ layer** (``EOT = t_IL + t_hk·3.9/K``) — the real reason EOT scaling *also*
  stalled (you cannot get below the IL). **Deferred to its own slice, deliberately:** now that the
  barrier is in the model, an IL is a **series tunnel barrier**, not merely a series capacitance —
  carrying it on the ``C_ox`` side only would be exactly the half-physical middle this module rejects.
* **Metal gate** — rode in *with* high-κ in 2007 but for a **different** discriminator (poly-depletion +
  Fermi-level pinning → work-function ``V_t`` tuning). Its own slice if wanted.
* **Bias dependence.** The barrier is treated as **rectangular at a fixed reference bias**: no
  field-lowering / trapezoidal (Fowler–Nordheim) correction, no image-force lowering. ``J₀`` is quoted at
  :data:`J0_REFERENCE_VG`. Valid for the direct-tunnelling regime (``V_g < φ_B``), which is the regime
  the 1.2–2 nm gate stacks of the era actually live in.
* **No quantum-mechanical / poly-depletion EOT corrections** (inversion-layer capacitance thickening).
* **Trap-assisted / stress-induced leakage** — HfO₂'s real defect-driven leakage is not modelled.

Units — the boundary currency is µm (the cross-module length), current density A/cm²
-------------------------------------------------------------------------------------
Thicknesses in **µm** in and out (so :func:`eot` feeds :func:`chip.device.oxide_capacitance`'s
``t_ox_um`` directly — the seam); barrier heights in **eV**; tunnelling masses **relative to m₀**;
leakage current density in **A/cm²** (the gate-dielectric datasheet unit, and the repo's CGS-cm
convention). The WKB is evaluated in SI internally and converted at the boundary.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .junction import Q_ELEMENTARY          # C — also the eV→J conversion factor

# --------------------------------------------------------------------------- #
# Physical constants (SI — the WKB exponent is evaluated in SI, converted at the boundary)
# --------------------------------------------------------------------------- #
HBAR = 1.054571817e-34                 # J·s — reduced Planck constant (CODATA)
M_ELECTRON = 9.1093837015e-31          # kg — free electron rest mass m₀ (CODATA)
_M_PER_UM = 1.0e-6                     # m per µm

# The SiO₂ dielectric constant — the EOT reference. Matches chip.device.EPS_OX = 3.9·EPS0 (the same 3.9);
# kept as a named scalar here because EOT is defined *as a ratio to it* (Robertson eq. 2).
K_SIO2 = 3.9                           # CITED — static dielectric constant of SiO₂ (the EOT reference)


# --------------------------------------------------------------------------- #
# 1. The EOT identity — the electrical thickness (Robertson eq. 2)
# --------------------------------------------------------------------------- #
def eot(t_phys_um: float, kappa: float) -> float:
    """Equivalent oxide thickness ``EOT = t_phys·(3.9/K)`` (µm) — the **electrical** thickness.

    The thickness of SiO₂ that would give the *same capacitance* as ``t_phys`` of a material with
    dielectric constant ``kappa`` (Robertson, Eur. Phys. J. Appl. Phys. **28**, 265 (2004), eq. 2). This
    is the number :func:`chip.device.oxide_capacitance` wants: feeding it EOT yields ``ε₀·K/t_phys``, the
    true physical capacitance of the stack (see the module docstring) — an identity, not an approximation.

    **The seam:** at ``kappa == K_SIO2`` this is the **identity** on ``t_phys_um`` (byte-for-byte), which
    is what keeps today's numbers unchanged.
    """
    if t_phys_um <= 0.0:
        raise ValueError(f"t_phys_um must be positive, got {t_phys_um} µm")
    if kappa <= 0.0:
        raise ValueError(f"kappa must be positive, got {kappa}")
    if kappa == K_SIO2:
        return t_phys_um                            # the seam: exact identity, no float round-trip
    return t_phys_um * (K_SIO2 / kappa)


def physical_thickness_for_eot(eot_um: float, kappa: float) -> float:
    """Invert :func:`eot`: the physical thickness ``t_phys = EOT·(K/3.9)`` (µm) hitting a target EOT.

    The **matched-EOT** constructor — the historical move itself: hold the electrical gate fixed (so
    ``C_ox``/``V_t``/``I_Dsat`` do not budge) and let the physical layer grow by ``K/3.9``. At
    ``kappa == K_SIO2`` this is the identity, the exact inverse of the :func:`eot` seam.
    """
    if eot_um <= 0.0:
        raise ValueError(f"eot_um must be positive, got {eot_um} µm")
    if kappa <= 0.0:
        raise ValueError(f"kappa must be positive, got {kappa}")
    if kappa == K_SIO2:
        return eot_um                               # the seam: exact identity
    return eot_um * (kappa / K_SIO2)


# --------------------------------------------------------------------------- #
# 2. The WKB tunnelling decay — where φ_B and m* enter (the exponent: cited, not fitted)
# --------------------------------------------------------------------------- #
def tunnel_decay(barrier_eV: float, tunnel_mass_rel: float) -> float:
    """The WKB decay constant ``α = 2·√(2·m*·φ_B)/ħ`` (per **µm**) — the exponent's whole content.

    Rectangular-barrier WKB transmission ``T ~ exp(−α·t)`` for an electron at the emitter band edge
    tunnelling through a barrier of height ``barrier_eV`` with in-barrier effective mass
    ``tunnel_mass_rel``·m₀. Both factors enter under the **same square root** — which is why they must be
    supplied as a *pair* per material (see the module docstring on the half-physical middle).

    **The barrier-collapse edge:** at ``barrier_eV == 0`` this returns **0** for *any* mass — the
    dielectric is transparent at every thickness. That is the honest statement of Robertson's
    requirement that a gate oxide have a CB offset over 1 eV, and it is what disqualifies TiO₂ (K=80)
    despite its huge K. The counterexample is therefore **mass-independent**.
    """
    if barrier_eV < 0.0:
        raise ValueError(f"barrier_eV must be ≥ 0, got {barrier_eV} eV")
    if tunnel_mass_rel <= 0.0:
        raise ValueError(f"tunnel_mass_rel must be > 0, got {tunnel_mass_rel}")
    phi_joule = barrier_eV * Q_ELEMENTARY                       # eV → J
    alpha_per_m = 2.0 * math.sqrt(2.0 * tunnel_mass_rel * M_ELECTRON * phi_joule) / HBAR
    return alpha_per_m * _M_PER_UM                              # per m → per µm


def decade_thickness_um(barrier_eV: float, tunnel_mass_rel: float) -> float:
    """The physical thickness buying **one decade** of leakage, ``ln(10)/α`` (µm) — the scaling slope.

    The industry's rule-of-thumb currency ("gate leakage rises ~1 decade per ~2 Å of SiO₂ removed"). For
    SiO₂'s cited pair this returns ≈1.78 Å — **predicted** from band-offset/effective-mass constants that
    were never fitted to a leakage curve, which is this module's non-circular cross-check. Infinite at
    ``barrier_eV == 0`` (no barrier ⇒ thickness buys nothing).
    """
    alpha = tunnel_decay(barrier_eV, tunnel_mass_rel)
    return math.inf if alpha == 0.0 else math.log(10.0) / alpha


# --------------------------------------------------------------------------- #
# 3. The dielectric registry — cited K / φ_B (one coherent set) + flagged m*
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Dielectric:
    """A candidate gate dielectric: the K that buys thickness, and the (φ_B, m*) pair that spends it.

    ``kappa`` static dielectric constant (sets EOT); ``barrier_eV`` the conduction-band offset to Si (the
    tunnelling barrier); ``tunnel_mass_rel`` the in-barrier electron effective mass in units of m₀.

    ``barrier_eV`` and ``tunnel_mass_rel`` are a **pair** — see :func:`tunnel_decay`. When
    ``barrier_eV == 0`` the mass is *immaterial* (α vanishes for any mass), which is exactly the
    situation of the huge-K/zero-offset oxides.
    """

    name: str
    kappa: float
    barrier_eV: float
    tunnel_mass_rel: float

    def __post_init__(self) -> None:
        if self.kappa <= 0.0:
            raise ValueError(f"kappa must be > 0, got {self.kappa}")
        if self.barrier_eV < 0.0:
            raise ValueError(f"barrier_eV must be ≥ 0, got {self.barrier_eV}")
        if self.tunnel_mass_rel <= 0.0:
            raise ValueError(f"tunnel_mass_rel must be > 0, got {self.tunnel_mass_rel}")

    @property
    def decay_per_um(self) -> float:
        """This material's WKB decay constant ``α`` (per µm) — :func:`tunnel_decay` on its own pair."""
        return tunnel_decay(self.barrier_eV, self.tunnel_mass_rel)

    def eot_um(self, t_phys_um: float) -> float:
        """This material's EOT for a physical thickness (µm) — :func:`eot` on its own ``kappa``."""
        return eot(t_phys_um, self.kappa)

    def thickness_for_eot_um(self, eot_um_target: float) -> float:
        """The physical thickness (µm) hitting a target EOT — :func:`physical_thickness_for_eot`."""
        return physical_thickness_for_eot(eot_um_target, self.kappa)


# --- Cited constants -------------------------------------------------------- #
# K and the CB offset φ_B are taken as ONE COHERENT SET from Robertson, "High dielectric constant
# oxides", Eur. Phys. J. Appl. Phys. 28, 265–291 (2004), Table 2 (K / band gap / consensus CB offset on
# Si) — the same table that carries the K↔gap inverse correlation (his Fig. 5) this module's headline
# rests on. Robertson's requirement 4: a gate oxide needs band offsets over 1 eV.
#
# The tunnelling masses m* come from the tunnelling literature and are **FLAGGED** — unlike K and φ_B
# they are *extracted by fitting* J–V data, and the reported spreads are wide:
#   * SiO₂  m* ≈ 0.5 m₀   (classic value, in agreement with photon-assisted tunnelling data at a
#                          ~3.15 eV barrier; reported range ~0.29–0.6, commonly 0.35–0.5)
#   * HfO₂  m* ≈ 0.11 m₀  (0.11 ± 0.03 from MOS/MOSFET determination; reported range ~0.08–0.2 across
#                          film composition/deposition/fitting method — the dominant uncertainty here)
# Robertson's φ_B(SiO₂)=3.2 eV is paired with a mass sourced at ~3.15 eV — a 1.5% barrier difference,
# i.e. <1% in α (it enters under a √). Immaterial; noted for coherent-set honesty.
SIO2 = Dielectric("thermal SiO₂", kappa=K_SIO2, barrier_eV=3.2, tunnel_mass_rel=0.50)
HFO2 = Dielectric("HfO₂ (high-κ)", kappa=25.0, barrier_eV=1.4, tunnel_mass_rel=0.11)

# The counterexample — huge K, ZERO barrier. Robertson Table 2 gives TiO₂ K=80, gap 3.5 eV, CB offset 0:
# it fails requirement 4 outright. Its mass is NOT sourced and does not need to be — at φ_B = 0 the decay
# constant vanishes for any mass, so the "K=80 buys 20× the thickness and *still* leaks" conclusion is
# mass-independent. The placeholder below is never load-bearing (asserted in the tests).
TIO2 = Dielectric("TiO₂ (huge-κ, no barrier)", kappa=80.0, barrier_eV=0.0, tunnel_mass_rel=0.50)

DIELECTRICS: dict[str, Dielectric] = {"SiO2": SIO2, "HfO2": HFO2, "TiO2": TIO2}

# Robertson Table 2 also lists Si₃N₄ (K=7, offset 2.4), Al₂O₃ (K=9, offset 2.8), ZrO₂ (K=25, offset 1.5),
# La₂O₃ (K=30, offset 2.3), HfSiO₄ (K=11, offset 1.8), SrTiO₃ (K=2000, offset 0). They are **not** in the
# registry: their tunnelling masses are not separately sourceable here, and a Dielectric without a cited
# (φ_B, m*) pair could only carry an invented exponent. HfO₂ is the 2007/45 nm-correct choice and SiO₂ is
# the incumbent it replaced — the two the history arc needs. (SrTiO₃ would merely repeat TiO₂'s lesson.)

# --- The flagged prefactor -------------------------------------------------- #
# J₀ is a HOUSE LUMP (the analogue of F2's CONTACT_LENGTH_UM): the tunnelling supply/attempt prefactor,
# calibrated at ONE cited SiO₂ point and then SHARED ACROSS MATERIALS. Calibration anchor — Robertson:
# SiO₂ under 2 nm leaks "exceeding 1 A/cm² at 1 V", and the ~1.4 nm layer is the one whose leakage is too
# large. We pin J(SiO₂, 1.5 nm, 1 V) = 1 A/cm², giving J₀ = exp(α_SiO₂·1.5 nm) A/cm² ≈ 2.8e8.
#
# Sharing J₀ across materials is the *honest* choice, not a shortcut: any per-material prefactor would be
# invented, and sharing makes it **cancel exactly** in every fixed-EOT ratio, so the decades-saved figure
# is pure cited-exponent physics (see :func:`leakage_decades_saved`). The prefactor sets only the absolute
# A/cm² scale — flagged, never asserted as an exact current.
J0_REFERENCE_VG = 1.0                  # V — the reference bias J₀ is quoted at (rectangular-barrier)
_J0_ANCHOR_T_UM = 1.5e-3               # µm — the 1.5 nm SiO₂ calibration point
_J0_ANCHOR_J = 1.0                     # A/cm² — Robertson's "exceeding 1 A/cm² at 1 V" scale
J0_REFERENCE = _J0_ANCHOR_J * math.exp(SIO2.decay_per_um * _J0_ANCHOR_T_UM)   # A/cm² — FLAGGED lump


# --------------------------------------------------------------------------- #
# 4. The leakage reading — J₀·exp(−α·t) and the prefactor-free ratio
# --------------------------------------------------------------------------- #
def gate_leakage(t_phys_um: float, dielectric: Dielectric | str, *, J0: float = J0_REFERENCE) -> float:
    """Direct-tunnelling gate leakage ``J_g = J₀·exp(−α·t_phys)`` (A/cm²) at the reference bias.

    The **physical** thickness is what tunnels — this is the currency ``EOT`` is blind to, and the whole
    reason high-κ works. ``α`` is :func:`tunnel_decay` on the material's cited ``(φ_B, m*)`` pair; ``J0``
    is the **flagged** shared prefactor (:data:`J0_REFERENCE`, quoted at :data:`J0_REFERENCE_VG`).

    **Flagged:** the absolute value carries the house prefactor. The *ratio* between two stacks does not
    — use :func:`leakage_decades_saved` for the assertable comparison. At ``φ_B = 0`` (TiO₂) this returns
    ``J₀`` at every thickness: no barrier, no benefit from any amount of physical thickness.
    """
    if t_phys_um <= 0.0:
        raise ValueError(f"t_phys_um must be positive, got {t_phys_um} µm")
    if J0 <= 0.0:
        raise ValueError(f"J0 must be positive, got {J0}")
    diel = DIELECTRICS[dielectric] if isinstance(dielectric, str) else dielectric
    return J0 * math.exp(-diel.decay_per_um * t_phys_um)


def leakage_decades_saved(
    eot_um: float, dielectric: Dielectric | str, *, reference: Dielectric | str = SIO2,
) -> float:
    """Decades of gate leakage saved by ``dielectric`` vs ``reference`` **at the same EOT** — the payload.

    ``log₁₀(J_ref/J_new)`` with both stacks built to the *same electrical thickness* ``eot_um`` (so
    ``C_ox``/``V_t``/``I_Dsat`` are **identical** — the identity in the module docstring). Because the
    prefactor is shared it **cancels exactly**, leaving

        decades = (α_new·t_new − α_ref·t_ref)/ln(10),   t = EOT·K/3.9

    — a function of the **cited** constants only (``K``, ``φ_B``, ``m*``): **no flagged magnitude enters**.
    This is the assertable form of the F3 discriminator: the same electrical gate, orders of magnitude
    less leakage, bought purely with physical thickness.

    Positive ⇒ the new stack leaks less. Note it is **not** ``log₁₀(K/3.9)``-shaped: the thickness gain
    (``K/3.9``, linear) is partly spent back by the lower barrier and mass (``α ∝ √(m*φ_B)``) — with
    Robertson's K↔gap inverse correlation, that is the physics that makes "more K" stop paying (TiO₂ ⇒
    negative: K=80 buys 20× the thickness and still leaks, because α = 0).
    """
    if eot_um <= 0.0:
        raise ValueError(f"eot_um must be positive, got {eot_um} µm")
    new = DIELECTRICS[dielectric] if isinstance(dielectric, str) else dielectric
    ref = DIELECTRICS[reference] if isinstance(reference, str) else reference
    exponent_new = new.decay_per_um * new.thickness_for_eot_um(eot_um)
    exponent_ref = ref.decay_per_um * ref.thickness_for_eot_um(eot_um)
    return (exponent_new - exponent_ref) / math.log(10.0)


# --------------------------------------------------------------------------- #
# 5. The bundled gate-stack reading (the record the consumer/demo read)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GateStack:
    """A built gate stack: what it is physically, what it looks like electrically, and what it leaks.

    ``material``/``kappa`` the dielectric; ``t_phys_um`` what was physically deposited; ``eot_um`` the
    **electrical** thickness (the number :func:`chip.device.oxide_capacitance` consumes — the seam);
    ``gate_leakage_A_cm2`` the direct-tunnelling current density (**flagged** absolute scale);
    ``decades_saved_vs_sio2`` the prefactor-free comparison at matched EOT (**cited-only**). Plain
    scalars — the loose-coupling currency.
    """

    material: str
    kappa: float
    t_phys_um: float
    eot_um: float
    gate_leakage_A_cm2: float
    decades_saved_vs_sio2: float

    @property
    def thickness_gain(self) -> float:
        """``t_phys/EOT = K/3.9`` — the physical thickness the high-κ bought at fixed electrical gate."""
        return self.t_phys_um / self.eot_um


def gate_stack(eot_um: float, dielectric: Dielectric | str, *, J0: float = J0_REFERENCE) -> GateStack:
    """Build the stack that hits a target ``eot_um`` in ``dielectric`` — the matched-EOT historical move.

    Holds the **electrical** gate fixed at ``eot_um`` (so every :mod:`chip.device` number is unchanged by
    construction) and reports the physical thickness that requires, the leakage it tunnels, and the
    prefactor-free decades saved vs SiO₂. This is the demo's unit of comparison.
    """
    diel = DIELECTRICS[dielectric] if isinstance(dielectric, str) else dielectric
    t_phys = diel.thickness_for_eot_um(eot_um)      # validates eot_um > 0
    return GateStack(
        material=diel.name, kappa=diel.kappa, t_phys_um=t_phys, eot_um=eot_um,
        gate_leakage_A_cm2=gate_leakage(t_phys, diel, J0=J0),
        decades_saved_vs_sio2=leakage_decades_saved(eot_um, diel, reference=SIO2),
    )
