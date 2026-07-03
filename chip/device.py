"""Process → device: the compact MOS threshold voltage (Chip Phase 4).

The payoff phase — where the three preceding process steps **become a working device parameter**.
Phase 1a diffused dopant (the channel doping ``N_A``), Phase 2 grew the gate oxide (its thickness
``t_ox`` → ``C_ox``), Phase 3 printed the gate (its CD → channel length ``L``); this module reads the
**threshold voltage** ``V_t`` off them — the chip analogue of Steel's structure→properties map, and a
**compact closed form**, the *consequence* of the process, **not** a meshed device solve (plan §4/§5).

The model (textbook long-channel n-MOSFET, p-type substrate)
------------------------------------------------------------
At the onset of strong inversion the surface potential is pinned at ``2·φ_F`` and the gate must supply
the flat-band offset, that band bending, and the depletion charge below it::

    V_t = V_FB + 2·φ_F + Q_dep / C_ox
        = V_FB + 2·φ_F + (1/C_ox)·√(2·q·ε_Si·N_A·(2·φ_F))            (V)

with ``φ_F = (kT/q)·ln(N_A/n_i)`` the bulk Fermi potential (magnitude), ``C_ox = ε_ox/t_ox`` the oxide
capacitance per area, and ``V_FB = −(φ_gate − φ_bulk)`` the flat-band voltage for an **ideal** oxide
(no fixed charge ``Q_ox = 0`` — named below). For a p-substrate the bulk potential is ``φ_bulk = −φ_F``,
so ``V_FB = −(φ_gate + φ_F)``; the degenerate poly gate sits at a band edge (``φ_gate = +E_g/2 ≈
+0.55 V`` for **n⁺-poly**, ``−0.55 V`` for **p⁺-poly**).

**Body effect (the √-law).** Reverse-biasing the source–body junction by ``V_SB`` widens the depletion
charge, raising ``V_t``::

    V_t(V_SB) = V_FB + 2·φ_F + (1/C_ox)·√(2·q·ε_Si·N_A·(2·φ_F + V_SB))
              = V_t0 + γ·(√(2·φ_F + V_SB) − √(2·φ_F)),     γ ≡ √(2·q·ε_Si·N_A)/C_ox

— the two forms are **algebraically identical** (factor out ``√(2qε_Si N_A)/C_ox``); the second is the
Shichman–Hodges body-effect parameter ``γ``. (That identity is therefore a *consistency* check on ``γ``,
**not** an independent anchor — see the triad note.)

Validation triad (plan §4) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight) — an *independent* depletion-Poisson integration, not the √-law.** The
  closed form here *is* the model (like Phase 2's Deal–Grove, there is no solver underneath), so the
  honest analytic leg is an **independent** recomputation — the analogue of Phase 2's ``solve_ivp``
  recovering the oxide closed form. We solve Poisson in the depletion approximation,
  ``d²ψ/dx² = q·N_A/ε_Si`` on ``[0, W]`` with ``ψ(W) = ψ'(W) = 0``, numerically (``solve_ivp``) and
  **root-find the depletion width** ``W`` at which the surface potential ``ψ(0)`` reaches ``2·φ_F``;
  then ``Q_dep = q·N_A·W`` reproduces ``√(2·q·ε_Si·N_A·2·φ_F)`` to ~1e-9 (:func:`depletion_charge_poisson`
  vs :func:`depletion_charge`). The body-effect √-law (:func:`threshold_voltage` vs ``γ`` form) is kept
  only as a **cheap γ-consistency check** — it catches a ``γ`` typo but anchors no physics (it is the
  same formula rearranged), so it is *not* billed as the anchor.
* **Conservation — MOS charge neutrality / Gauss's law.** The gate charge balances the
  semiconductor charge, ``Q_g = −(Q_dep + Q_inv)`` (:func:`gate_charge`, :func:`inversion_charge`):
  above threshold every extra volt of ``V_GB − V_t`` goes entirely into inversion charge,
  ``Q_inv = −C_ox·(V_GB − V_t)``, and Gauss's law sets the oxide field ``E_ox = Q_g/ε_ox``. This leg is
  the model's **own charge accounting** — neutrality and Gauss hold *by construction*, so it is a
  self-consistency check (the genuinely-independent verification is the Poisson anchor above). What it
  externally anchors is the MIT P2b,c arithmetic: ``V_GB ≈ 4.9 V`` for ``Q_inv = −1e-6 C/cm²``, and
  ``1e-6/ε_ox ≈ 2.9e6 V/cm`` — which mainly re-check the already-pinned ``C_ox``/``ε_ox``.
* **Benchmark (loose) — V_t vs process knobs, vs the cited worked example.** The reference is **MIT
  6.012 PS3 (Spring 2007), Problem 2** ([[mos-threshold-voltage-source]]): an n⁺-poly / p-substrate
  ``N_A = 1e17`` / ``t_ox = 15 nm`` device gives ``V_FB = −0.97 V``, ``C_ox = 2.3e-7 F/cm²``,
  ``V_t ≈ 0.58 V`` — and (its parts b,c) ``Q_inv = −1e-6 C/cm²`` at ``V_GB = 4.9 V`` with
  ``E_ox = 2.9e6 V/cm``, which double as the conservation cross-check. ``V_t`` rises with ``N_A`` and
  with ``t_ox`` (thicker oxide → smaller ``C_ox`` → larger depletion term).

Why the benchmark is a genuine cross-check (non-circularity)
------------------------------------------------------------
Every constant in ``V_t`` is an **independent physical fact**, none fit to a threshold voltage: ε_Si,
ε_ox, q, n_i are universal constants; ``φ_gate = 0.55 V`` is the poly band-edge offset; and the *inputs*
``N_A`` (Phase-1 diffusion, cited Fair ``D``) and ``t_ox`` (Phase-2 Deal–Grove, cited rate constants)
arrive from upstream process modules with their own cited data. So reproducing MIT's 0.58 V is a
cross-check of the assembled formula, not a refit.

Named scope edge (the honest ceiling)
-------------------------------------
* **Long-channel only — no short-channel V_t rolloff.** ``V_t`` here has **no channel-length term**;
  the litho CD sets the *geometry* (channel length ``L``, and the optional drive-current readout's
  ``W/L``) but does **not** perturb ``V_t``. Short-channel rolloff (charge-sharing / DIBL) is an
  inherently **2-D** effect — exactly the plan §5 tar pit — so it is left outside the line; a
  charge-sharing patch would destroy the exact closed-form anchor. This is *why* CD is geometry-only.
* **Ideal oxide by default / uniform channel.** ``Q_ox`` (fixed/mobile oxide charge) defaults to ``0``
  → the ideal oxide; it is now an **optional** input (``ΔV_FB = −Q_ox/C_ox``) that the G4 purification
  module drives with mobile-ion (Na) contamination — but **interface traps** ``D_it`` remain out (a
  separate, capacitance-dispersion effect). The channel is a **uniform** substrate doping ``N_A`` —
  **but** a real **V_t-adjust implant** is now an honest, optional input (``implant_dose``/``implant_kind``
  → :func:`vt_adjust_shift`, ``ΔV_t = ±q·Q/C_ox``): a shallow ion-implanted sheet (the buried
  :class:`~chip.diffusion_dopant.Implant` an ``erfc`` predep cannot make) shifts the threshold, replacing
  the old **faked** uniform offset. Its **shallow-sheet** approximation (dose within the depletion region,
  peak-depth-independent) is the scope edge: a **deep / retrograde** implant, where the profile centroid
  matters and the formula takes an effective ``N_A`` integrated over the depletion width, is the deferred
  refinement (the retrograde-well slice). Full dopant activation, and ``n_i = 1.0e10 cm⁻³`` at 300 K (the
  value that reproduces the MIT example; ``1.45e10`` shifts ``φ_F`` ~10 mV — a small calibration choice,
  named).
* **Degenerate poly gate** pinned at the band edge (``φ_gate = ±0.55 V``); a metal gate would need a
  work-function table (out of v1).
* **Forward coupling only.** As Phase 2 noted, oxidation's back-reaction on the profile (segregation /
  OED) is deferred — Phase 4 consumes an ``N_A`` and a ``t_ox`` that were computed independently.

Units — semiconductor-conventional CGS (as :mod:`diffusion_dopant` / :mod:`junction`)
------------------------------------------------------------------------------------
=====================  ==============  =====================================================
quantity               unit           note
=====================  ==============  =====================================================
permittivity ε         **F/cm**        ε_Si = 11.7·ε₀, ε_ox = 3.9·ε₀, ε₀ = 8.854e-14 F/cm
capacitance C_ox       **F/cm²**       ``= ε_ox / t_ox``
charge Q (sheet)       **C/cm²**       depletion / inversion charge per unit area
oxide thickness t_ox   **µm** in       converted µm→cm at the boundary (Phase-2 currency)
channel doping N_A     **cm⁻³**        the Phase-1 substrate doping (cross-module currency)
potential / voltage    **V**           φ_F, V_FB, V_t, V_SB
=====================  ==============  =====================================================
``t_ox`` enters in **µm** (the cross-module length currency) and ``N_A`` in **cm⁻³** (Phase-1's unit);
everything else is CGS so ``C_ox`` is F/cm² and the charge integrals are C/cm² directly. One unit system
throughout this module; µm/cm⁻³ are the inputs the upstream modules speak.

Validation boundary
-------------------
There is no shared engine here — this module *is* the compact model, so its tests carry the whole triad:
the independent depletion-Poisson recovery (analytic), the charge-neutrality / Gauss bookkeeping
(conservation), and the cited MIT worked example + the V_t-vs-knobs trends (benchmark). The constants
are pinned to the cited source ([[mos-threshold-voltage-source]]), *not* carried from memory.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .diffusion_dopant import K_BOLTZMANN_EV, ABS_ZERO, CM_PER_UM
from .junction import Q_ELEMENTARY

# --------------------------------------------------------------------------- #
# Physical constants (CGS — F/cm, C, cm⁻³), cited [[mos-threshold-voltage-source]]
# --------------------------------------------------------------------------- #
EPS0 = 8.8541878128e-14            # F/cm — vacuum permittivity (CGS-cm)
EPS_SI = 11.7 * EPS0               # F/cm — silicon (1.036e-12)
EPS_OX = 3.9 * EPS0                # F/cm — SiO₂ (3.453e-13)
NI_300K = 1.0e10                   # cm⁻³ — intrinsic carrier conc. @300 K (MIT value; 1.45e10 ↔ φ_F+~10mV)
ROOM_T_CELSIUS = 27.0              # °C — 300.15 K (kT/q ≈ 0.0259 V, the worked-example temperature)
EG_HALF = 0.55                     # V — degenerate-poly gate band-edge offset (≈ E_g/2 ≈ 0.56 V; MIT 0.55)

# Gate-material potential φ_gate (V, relative to intrinsic): degenerate poly sits at a band edge.
GATE_POTENTIAL: dict[str, float] = {"n+poly": +EG_HALF, "p+poly": -EG_HALF}


def thermal_voltage(T_celsius: float = ROOM_T_CELSIUS) -> float:
    """Thermal voltage ``kT/q`` (V) at ``T_celsius``. ``k`` in eV/K → ``kT`` in eV = volts·q, so kT/q = k·T.

    At 27 °C (300.15 K) this is ≈ 0.0259 V — the value the MIT worked example uses.
    """
    T_K = T_celsius + ABS_ZERO
    if T_K <= 0.0:
        raise ValueError(f"temperature must be above absolute zero, got {T_celsius} °C")
    return K_BOLTZMANN_EV * T_K


# --------------------------------------------------------------------------- #
# 1. The building blocks: Fermi potential, oxide capacitance, flat-band voltage
# --------------------------------------------------------------------------- #
def fermi_potential(N_A: float, T_celsius: float = ROOM_T_CELSIUS, n_i: float = NI_300K) -> float:
    """Bulk Fermi potential ``φ_F = (kT/q)·ln(N_A/n_i)`` (V, magnitude), substrate doping ``N_A`` (cm⁻³).

    Positive magnitude (the depth of the bulk Fermi level below intrinsic for a p-substrate). For
    ``N_A = 1e17`` at 300 K, ``φ_F ≈ 0.42 V`` so ``2·φ_F ≈ 0.84 V`` (the surface potential pinned at
    the onset of strong inversion). ``n_i`` defaults to the MIT 1.0e10 (the named calibration pin).
    """
    if N_A <= 0.0:
        raise ValueError(f"N_A must be positive, got {N_A}")
    return thermal_voltage(T_celsius) * math.log(N_A / n_i)


def oxide_capacitance(t_ox_um: float) -> float:
    """Oxide capacitance per area ``C_ox = ε_ox / t_ox`` (F/cm²); ``t_ox_um`` in **µm** (Phase-2 currency).

    Converts µm→cm at the boundary. For ``t_ox = 15 nm = 0.015 µm``, ``C_ox ≈ 2.3e-7 F/cm²`` (the MIT
    value). Thinner oxide → larger ``C_ox`` → smaller depletion term → smaller ``V_t``.
    """
    if t_ox_um <= 0.0:
        raise ValueError(f"t_ox must be positive, got {t_ox_um} µm")
    return EPS_OX / (t_ox_um * CM_PER_UM)


def flatband_voltage(
    N_A: float, gate: str = "n+poly", T_celsius: float = ROOM_T_CELSIUS, n_i: float = NI_300K,
    Q_ox: float = 0.0, C_ox: float | None = None,
) -> float:
    """Flat-band voltage ``V_FB = −(φ_gate − φ_bulk) − Q_ox/C_ox`` (V).

    p-substrate bulk potential ``φ_bulk = −φ_F``, so the ideal-oxide part is ``−(φ_gate + φ_F)``. For an
    n⁺-poly gate (``φ_gate = +0.55 V``) on ``N_A = 1e17`` (``φ_F ≈ 0.42 V``): ``−0.97 V`` (the MIT value).

    **Oxide charge (lifting the named ``Q_ox = 0`` edge).** A fixed/mobile oxide charge per area
    ``Q_ox`` (C/cm²) shifts the flat-band voltage by ``−Q_ox/C_ox`` (the standard MOS relation):
    **positive** oxide charge (e.g. mobile Na⁺ ions, :func:`chip.purification.sodium_oxide_charge`)
    drives ``V_FB`` — and hence ``V_t`` — **down**. ``Q_ox`` defaults to ``0`` → the ideal-oxide value,
    byte-for-byte unchanged (the term is skipped entirely, so ``C_ox`` is not needed); when
    ``Q_ox ≠ 0`` the oxide capacitance ``C_ox`` (F/cm², ``= ε_ox/t_ox``) is required.
    """
    if gate not in GATE_POTENTIAL:
        raise ValueError(f"gate must be one of {sorted(GATE_POTENTIAL)}, got {gate!r}")
    V_FB = -(GATE_POTENTIAL[gate] + fermi_potential(N_A, T_celsius, n_i))
    if Q_ox != 0.0:
        if C_ox is None or C_ox <= 0.0:
            raise ValueError(f"a non-zero Q_ox needs a positive C_ox, got C_ox={C_ox}")
        V_FB -= Q_ox / C_ox
    return V_FB


def depletion_charge(N_A: float, phi_F: float, V_SB: float = 0.0) -> float:
    """Max depletion charge per area ``Q_dep = √(2·q·ε_Si·N_A·(2·φ_F + V_SB))`` (C/cm²).

    The ionized-acceptor charge in the surface depletion region at the onset of strong inversion (the
    charge the gate must support before inversion begins). ``V_SB`` (source–body reverse bias, V) widens
    it — the body-effect handle. This is the **closed form** the independent Poisson integration
    (:func:`depletion_charge_poisson`) is checked against.
    """
    psi = 2.0 * phi_F + V_SB
    if psi < 0.0:
        raise ValueError(f"2·φ_F + V_SB must be ≥ 0, got {psi}")
    return math.sqrt(2.0 * Q_ELEMENTARY * EPS_SI * N_A * psi)


def body_effect_coefficient(N_A: float, t_ox_um: float) -> float:
    """Body-effect coefficient ``γ = √(2·q·ε_Si·N_A) / C_ox`` (V^½) — the √-law slope.

    The Shichman–Hodges body factor: ``V_t(V_SB) = V_t0 + γ·(√(2φ_F+V_SB) − √(2φ_F))``. Typically
    0.3–0.5 V^½ for modern processes. (A *derived* convenience — the same ``√(2qε_Si N_A)`` that appears
    in :func:`depletion_charge`, divided by ``C_ox``.)
    """
    return math.sqrt(2.0 * Q_ELEMENTARY * EPS_SI * N_A) / oxide_capacitance(t_ox_um)


# --------------------------------------------------------------------------- #
# 2. The independent depletion-Poisson solve (the analytical-limit anchor)
# --------------------------------------------------------------------------- #
def depletion_width_poisson(N_A: float, phi_F: float, V_SB: float = 0.0) -> float:
    """Depletion width ``W`` (cm) from an **independent** numerical Poisson solve + root-find.

    The genuine analytic anchor (the Phase-2 ``solve_ivp`` analogue, *not* the √-law rearrangement):
    integrate Poisson ``d²ψ/dx² = q·N_A/ε_Si`` from the depletion edge ``x = W`` (where ``ψ = ψ' = 0``)
    back to the surface with :func:`scipy.integrate.solve_ivp`, and **root-find** the width ``W`` at
    which the surface potential ``ψ(0)`` equals the threshold band bending ``2·φ_F + V_SB``
    (:func:`scipy.optimize.brentq`). This inverts the electrostatics numerically — no closed-form ``√``
    is used — so ``Q_dep = q·N_A·W`` is an independent recomputation of :func:`depletion_charge`.
    """
    from scipy.integrate import solve_ivp
    from scipy.optimize import brentq

    psi_target = 2.0 * phi_F + V_SB
    if psi_target <= 0.0:
        raise ValueError(f"2·φ_F + V_SB must be > 0, got {psi_target}")
    rho_over_eps = Q_ELEMENTARY * N_A / EPS_SI            # ψ'' = q·N_A/ε_Si (constant in depletion approx)

    def surface_psi(W: float) -> float:
        # Integrate ψ''=const from x=W back to x=0 with ψ(W)=ψ'(W)=0; read ψ(0).
        sol = solve_ivp(
            lambda x, y: (y[1], rho_over_eps), (W, 0.0), (0.0, 0.0),
            rtol=1e-11, atol=1e-16,
        )
        return float(sol.y[0, -1])

    W_guess = math.sqrt(2.0 * EPS_SI * psi_target / (Q_ELEMENTARY * N_A))   # analytic seed, only to bracket
    return brentq(lambda W: surface_psi(W) - psi_target, 0.05 * W_guess, 20.0 * W_guess, xtol=1e-12, rtol=1e-12)


def depletion_charge_poisson(N_A: float, phi_F: float, V_SB: float = 0.0) -> float:
    """Depletion charge ``Q_dep = q·N_A·W`` (C/cm²) from the independent Poisson width (the anchor).

    Recomputes :func:`depletion_charge` through :func:`depletion_width_poisson` — a numerical Poisson
    integration + root-find rather than the closed-form ``√`` — so the two agreeing certifies the
    depletion term independently (the tight analytic leg).
    """
    return Q_ELEMENTARY * N_A * depletion_width_poisson(N_A, phi_F, V_SB)


# --------------------------------------------------------------------------- #
# 3. The threshold voltage + the bundled device result
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MOSDevice:
    """A compact MOS device read off the process: its threshold voltage and the charge decomposition.

    ``V_t`` (V) is the threshold voltage at this ``V_SB``; ``V_t0`` the zero-bias value; ``V_FB``,
    ``phi_F`` (V), ``C_ox`` (F/cm²), ``Q_dep`` (C/cm²) and ``gamma`` (V^½) the building blocks; ``two_phi_F``
    the surface potential at threshold. ``N_A`` (cm⁻³), ``t_ox_um`` (µm), ``gate`` and ``V_SB`` (V) echo
    the recipe. ``channel_length_um`` (µm, optional) is the Phase-3 litho CD — *geometry only*, it does
    **not** enter ``V_t``. Plain scalars — the loose-coupling currency.
    """

    N_A: float
    t_ox_um: float
    gate: str
    V_SB: float
    V_t: float
    V_t0: float
    V_FB: float
    phi_F: float
    C_ox: float
    Q_dep: float
    gamma: float
    channel_length_um: float | None = None
    Q_ox: float = 0.0                 # oxide charge per area (C/cm²); 0 = ideal oxide (the default seam)
    implant_dose: float = 0.0         # V_t-adjust implant areal dose (cm⁻²); 0 = no adjust implant (the seam)
    implant_kind: str | None = None   # "p" (acceptor, raises V_t) | "n" (donor, lowers V_t) | None
    vt_adjust: float = 0.0            # ΔV_t from the adjust implant (V); +for acceptor, −for donor (n-MOS)

    @property
    def two_phi_F(self) -> float:
        """Surface potential at the onset of strong inversion ``2·φ_F`` (V)."""
        return 2.0 * self.phi_F

    @property
    def body_term(self) -> float:
        """The depletion-charge contribution to ``V_t``: ``Q_dep / C_ox`` (V)."""
        return self.Q_dep / self.C_ox


# Sign of the V_t-adjust implant shift for an n-MOS (p-substrate): an **acceptor** (p-type, e.g. boron)
# sheet raises V_t (more negative depletion charge to invert); a **donor** (n-type) sheet lowers it.
_IMPLANT_VT_SIGN: dict[str, float] = {"p": +1.0, "n": -1.0}


def vt_adjust_shift(dose: float, kind: str, C_ox: float) -> float:
    """Shallow V_t-adjust implant threshold shift ``ΔV_t = ±q·Q/C_ox`` (V) for an n-MOS (p-substrate).

    The honest, first-order source of the threshold adjust the ``device.py`` model previously **faked**
    with a uniform substrate offset: a shallow implanted sheet of areal dose ``Q`` (cm⁻²) sitting inside
    the surface depletion region acts as an extra fixed charge, shifting ``V_t`` by ``±q·Q/C_ox`` — the
    textbook ``V_t``-adjust formula (Plummer/Sze). **``+``** for an **acceptor** (p-type, e.g. a boron
    :class:`~chip.diffusion_dopant.Implant`) — it raises ``V_t``; **``−``** for a **donor** (n-type) — it
    lowers it. The buried :class:`~chip.diffusion_dopant.Implant` profile is the physical *source* of the
    dose (the observable predep cannot make), but this shift depends **only on dose and type**, not on the
    peak depth — see the named scope edge (deep/retrograde implants, where the centroid depth matters,
    are the deferred effective-``N_A`` refinement). ``C_ox`` (F/cm²) is the gate-oxide capacitance.
    """
    if dose < 0.0:
        raise ValueError(f"implant dose must be ≥ 0 cm⁻², got {dose}")
    if kind not in _IMPLANT_VT_SIGN:
        raise ValueError(f"implant kind must be one of {sorted(_IMPLANT_VT_SIGN)}, got {kind!r}")
    if C_ox <= 0.0:
        raise ValueError(f"C_ox must be positive, got {C_ox}")
    return _IMPLANT_VT_SIGN[kind] * Q_ELEMENTARY * dose / C_ox


def threshold_voltage(
    N_A: float,
    t_ox_um: float,
    gate: str = "n+poly",
    V_SB: float = 0.0,
    channel_length_um: float | None = None,
    T_celsius: float = ROOM_T_CELSIUS,
    n_i: float = NI_300K,
    Q_ox: float = 0.0,
    implant_dose: float = 0.0,
    implant_kind: str | None = None,
) -> MOSDevice:
    """Compute the MOS threshold voltage from the process knobs → :class:`MOSDevice`.

    Assembles ``V_t = V_FB + 2·φ_F + Q_dep/C_ox`` from the channel doping ``N_A`` (cm⁻³, a Phase-1
    profile's substrate doping), the gate oxide ``t_ox_um`` (µm, a Phase-2 thickness), and the gate
    material. ``V_SB`` (V) applies the body effect (widening ``Q_dep``); ``channel_length_um`` (µm, a
    Phase-3 CD) is recorded as device geometry but does **not** affect ``V_t`` (long-channel, plan §4 /
    the named scope edge). ``Q_ox`` (C/cm², the fixed/mobile **oxide charge** — e.g. mobile-ion
    contamination from imperfect purification, :mod:`chip.purification`) enters through the flat-band
    voltage (``ΔV_FB = −Q_ox/C_ox``); it defaults to ``0`` → the ideal oxide, byte-for-byte the prior
    ``V_t``.

    **V_t-adjust implant (§5, the honest de-fake).** ``implant_dose`` (cm⁻²) + ``implant_kind`` (``"p"``
    acceptor / ``"n"`` donor) apply a shallow ion-implant threshold shift ``ΔV_t = ±q·Q/C_ox``
    (:func:`vt_adjust_shift`) — the real, dose-controlled source of the adjust the old comment flagged as
    faked by a uniform substrate offset. The physical dose comes from a buried
    :class:`~chip.diffusion_dopant.Implant` (an observable predep cannot make); the *shift* needs only
    dose+type. Defaults ``0`` / ``None`` ⇒ no adjust implant, byte-for-byte the prior ``V_t`` (the seam).
    *Process in, device parameter out* — the chip's structure→properties map.
    """
    phi_F = fermi_potential(N_A, T_celsius, n_i)
    C_ox = oxide_capacitance(t_ox_um)
    V_FB = flatband_voltage(N_A, gate, T_celsius, n_i, Q_ox=Q_ox, C_ox=C_ox)
    gamma = math.sqrt(2.0 * Q_ELEMENTARY * EPS_SI * N_A) / C_ox
    Q_dep = depletion_charge(N_A, phi_F, V_SB)
    dV_t = vt_adjust_shift(implant_dose, implant_kind, C_ox) if implant_dose > 0.0 else 0.0
    V_t = V_FB + 2.0 * phi_F + Q_dep / C_ox + dV_t
    V_t0 = V_FB + 2.0 * phi_F + depletion_charge(N_A, phi_F, 0.0) / C_ox + dV_t
    return MOSDevice(
        N_A=N_A, t_ox_um=t_ox_um, gate=gate, V_SB=V_SB, V_t=V_t, V_t0=V_t0,
        V_FB=V_FB, phi_F=phi_F, C_ox=C_ox, Q_dep=Q_dep, gamma=gamma,
        channel_length_um=channel_length_um, Q_ox=Q_ox,
        implant_dose=implant_dose, implant_kind=implant_kind, vt_adjust=dV_t,
    )


def threshold_voltage_body_effect(mos: MOSDevice, V_SB) -> np.ndarray | float:
    """Threshold voltage vs source–body bias via the **√-law**: ``V_t0 + γ·(√(2φ_F+V_SB) − √(2φ_F))`` (V).

    The Shichman–Hodges body-effect form, evaluated at scalar or array ``V_SB`` (for the body-effect
    curve). Algebraically identical to re-running :func:`threshold_voltage` at each ``V_SB`` — kept as
    the cheap closed-form sweep (and the γ-consistency check), *not* an independent anchor.
    """
    V_SB = np.asarray(V_SB, dtype=float)
    if np.any(2.0 * mos.phi_F + V_SB < 0.0):
        raise ValueError("2·φ_F + V_SB must be ≥ 0")
    out = mos.V_t0 + mos.gamma * (np.sqrt(2.0 * mos.phi_F + V_SB) - math.sqrt(2.0 * mos.phi_F))
    return float(out) if out.ndim == 0 else out


# --------------------------------------------------------------------------- #
# 4. MOS charge neutrality / Gauss's law (the conservation leg)
# --------------------------------------------------------------------------- #
def inversion_charge(V_GB: float, mos: MOSDevice) -> float:
    """Inversion-layer charge per area ``Q_inv = −C_ox·(V_GB − V_t)`` (C/cm²), above threshold.

    Above strong inversion the surface potential is pinned at ``2·φ_F``, so every extra volt of gate
    drive (``V_GB − V_t``) is supported by inversion charge (MIT 6.012 P2b). Returns 0 below threshold
    (``V_GB ≤ V_t`` — no inversion layer). Negative (electrons) for the n-MOS.
    """
    if V_GB <= mos.V_t:
        return 0.0
    return -mos.C_ox * (V_GB - mos.V_t)


def gate_charge(V_GB: float, mos: MOSDevice) -> float:
    """Gate charge per area ``Q_g`` (C/cm²) — by charge neutrality ``Q_g = −(Q_dep + Q_inv)``.

    Above threshold the gate charge balances the depletion **and** inversion charge in the
    semiconductor. Equivalently ``Q_g = C_ox·(V_GB − V_FB − 2·φ_F)`` (the gate drive past the band
    bending); the two agree — that closure is the conservation check. Positive for the n-MOS (electrons
    on the gate mirror the negative semiconductor charge).
    """
    return -(mos.Q_dep + inversion_charge(V_GB, mos))


def oxide_field(V_GB: float, mos: MOSDevice) -> float:
    """Oxide electric field ``E_ox = Q_g / ε_ox`` (V/cm) — Gauss's law across the oxide.

    The gate charge terminates the field in the oxide (MIT 6.012 P2c): ``E_ox = Q_g/ε_ox``, equivalently
    ``(V_GB − V_FB − 2·φ_F)/t_ox``. The physical Gauss-law leg of conservation.
    """
    return gate_charge(V_GB, mos) / EPS_OX


# --------------------------------------------------------------------------- #
# 5. Optional honest long-channel drive current (makes the litho CD non-inert)
# --------------------------------------------------------------------------- #
MU_N_EFF = 450.0                   # cm²/V·s — representative effective n-channel surface mobility (illustrative)


def saturation_current(
    mos: MOSDevice, V_GS: float, width_um: float, mu_eff: float = MU_N_EFF,
    R_series_ohm: float = 0.0,
) -> float:
    """Long-channel saturation drain current ``I_Dsat = ½·μ·C_ox·(W/L)·(V_GS − V_t)²`` (A).

    The **honest** way the Phase-3 litho CD moves a device number: the channel length ``L`` (= the CD on
    :attr:`MOSDevice.channel_length_um`) sets ``W/L``, so a shorter gate drives more current — *without*
    faking short-channel ``V_t`` rolloff (the named scope edge). ``mu_eff`` is a representative effective
    **channel** mobility (surface-scattering-reduced, illustrative — not a validated transport value).
    Returns 0 below threshold (``V_GS ≤ V_t``). Requires :attr:`channel_length_um` to be set.

    **Source series resistance (lifting the ``R_series = 0`` ideal-contact edge).** A parasitic **source**
    access resistance ``R_series_ohm`` (Ω — the diffused *source* sheet resistance times its
    contact-to-channel square count, plus contact resistance)
    degrades the drive by **source degeneration**: the IR drop ``I_D·R_S`` across the source raises the
    source potential and eats into the gate overdrive, so the device self-consistently solves the implicit
    textbook relation

        ``I_D = ½·μ·C_ox·(W/L)·(V_GS − V_t − I_D·R_S)²``        (the source-degeneration quadratic)

    — a shallow, under-diffused junction (high S/D ``R_s``) **starves** ``I_Dsat``. It is the **source**
    side specifically: in saturation the *drain* access resistance drops ``V_DS`` but (the device staying in
    saturation) does **not** reduce ``I_Dsat`` (Sze–Ng), so only the source IR drop enters here. This is
    *why* the S/D diffusion dose is a real process decision (it sets that ``R_s``); the consumer is
    :mod:`fab_game`'s diffusion-journey stage. ``R_series_ohm`` defaults to ``0`` → the ideal-contact value, returned
    **bit-for-bit** by the closed form (the quadratic is skipped entirely — the seam, so ``demo_device``
    and the 2-D device are byte-for-byte unchanged). The standard small-signal consequence is the
    extrinsic transconductance ``g_m = g_m0/(1 + g_m0·R_S)`` (any device text, e.g. Sze–Ng) — the
    tight benchmark leg.
    """
    if mos.channel_length_um is None:
        raise ValueError("channel_length_um (the Phase-3 CD) must be set for the drive-current readout")
    if V_GS <= mos.V_t:
        return 0.0
    W_over_L = width_um / mos.channel_length_um           # ratio — units cancel
    beta = 0.5 * mu_eff * mos.C_ox * W_over_L             # the device transconductance factor (A/V²)
    V_ov = V_GS - mos.V_t
    if R_series_ohm <= 0.0:
        return beta * V_ov ** 2                           # ideal contact — the closed form (the seam)
    # Source degeneration: solve I_D = β·(V_ov − I_D·R_S)² for the physical root. Expanding gives the
    # quadratic β·R_S²·I² − (2·β·R_S·V_ov + 1)·I + β·V_ov² = 0; the physical branch is the smaller root
    # (I_D ≤ β·V_ov², and → β·V_ov² as R_S → 0 — continuous with the ideal-contact seam above).
    a = beta * R_series_ohm ** 2
    b = -(2.0 * beta * R_series_ohm * V_ov + 1.0)
    c = beta * V_ov ** 2
    return (-b - math.sqrt(b * b - 4.0 * a * c)) / (2.0 * a)
