"""Deep-level metals → minority-carrier lifetime + junction leakage (Chip / fab-game **G4b**, Tier 2).

The consequence model net doping **cannot** carry. Phase-1 dopant and G4a's mobile-ion Na both reach a
device number through the *doping/oxide-charge* channels (:mod:`chip.junction`, :mod:`chip.device`), but
a **deep-level transition metal** (Fe, Cu — :class:`chip.purification.Contamination`) is electrically a
**recombination centre**, not a dopant: it leaves the net doping essentially untouched and instead
*destroys minority-carrier lifetime* and *raises junction reverse leakage*. Zone refining scrubs these
metals superbly (their ``k`` is tiny — :mod:`chip.purification`), but whatever survives needs a **new
device output** to bite. This module is that output (plan §5a Tier 2, §6 G4 — the deferred "G4b" the
G4a build named): the metals finally become a *device* consequence — *a leaky, low-lifetime diode is how
a metal contaminant kills yield.*

This is the **loose tier**, by design (plan §7): the segregation purification of G4a is the verifiable
win, while the metal device-degradation **magnitudes** here (capture cross-sections, the clean-bulk
lifetime, the leakage calibration) are cited-but-loose — flagged, never asserted with the segregation
anchors. What *is* tight is the SRH machinery that frames them.

The Shockley–Read–Hall recombination centre
-------------------------------------------
A single trap level at ``N_t`` (cm⁻³) recombines carriers at the steady-state SRH net rate::

    U(n, p) = (p·n − n_i²) / [ τ_p0·(n + n_1) + τ_n0·(p + p_1) ]                 (cm⁻³ s⁻¹)

with ``τ_n0 = 1/(σ_n·v_th·N_t)``, ``τ_p0 = 1/(σ_p·v_th·N_t)`` the fundamental electron/hole capture
lifetimes (``σ`` the capture cross-section, ``v_th`` the carrier thermal velocity), and
``n_1 = n_i·e^{(E_t−E_i)/kT}``, ``p_1 = n_i·e^{−(E_t−E_i)/kT}`` the trap-occupancy factors
(``n_1·p_1 = n_i²``). In the **p-type bulk under low injection** (the channel/body of our n-MOS) this
collapses to a single minority-electron lifetime — the model the game consumes::

    1/τ = 1/τ_bulk + Σ_i σ_n,i·v_th·N_i        (the deep-level metals add their recombination rates)

— the **electron** capture cross-section governs (p-type ⇒ electrons are the minority carrier); ``τ_bulk``
is the clean-material baseline. The minority-carrier **diffusion length** ``L = √(D·τ)`` falls out of it.

The reverse junction leakage (the device killer)
------------------------------------------------
The same trap **generates** carriers where the junction is depleted (``n, p ≪ n_i``), giving the
generation-limited reverse leakage that dominates a silicon diode at room temperature::

    J_gen = q·n_i·W / (2·τ_g)              (A/cm²),   W = √(2·ε_Si·V_J/(q·N_A))  the depletion width

— ``∝ 1/τ ∝ N_metal``, so dirtier feedstock ⇒ shorter lifetime ⇒ **higher** leakage. ``W`` is the
one-sided abrupt S/D-junction depletion width at a reference junction voltage ``V_J`` (built-in +
reverse), reusing :mod:`chip.device`'s ``ε_Si``/``n_i`` and :mod:`chip.junction`'s ``q``. (We take the
generation lifetime ``τ_g ≈ τ`` for the teaching model — rigorously it weights both cross-sections; a
flagged simplification, the loose tier. The diffusion/Shockley ``J_0 ∝ n_i²/L`` component is
sub-dominant at 300 K and named, not modelled.)

Validation triad (plan §7) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight) — the low-injection reduction of the full SRH statistics.** Like
  Czochralski's ``k→1`` or Deal–Grove's closed form, the honest analytic leg is a **limit of a
  generalization**: the full :func:`srh_rate` ``U(n, p)``, evaluated in the p-type low-injection limit
  (``Δn ≪ N_A``, midgap trap), reduces to ``τ = Δn/U → τ_n0 = 1/(σ_n·v_th·N_t)`` — and crucially the
  hole cross-section ``σ_p`` **and** the trap energy ``E_t`` *drop out*, leaving ``σ_n`` as the sole
  governing cross-section. That is the content of the leg (not solver-grade independence — there is no
  solve underneath SRH; it *is* the model). The clean limit ``N_metal = 0 ⇒ τ = τ_bulk`` is recovered
  **bit-for-bit** (the seam). Rate-additivity (``1/τ`` affine in the ``N_i``) is true *by construction*
  — a regression guard, not an anchor.
* **Conservation (tight) — detailed balance.** At thermal equilibrium ``p·n = n_i²`` the SRH numerator
  vanishes, so ``U = 0`` **exactly** — generation balances recombination — *for any* ``σ_n``, ``σ_p``,
  ``E_t``. That parameter-independence is precisely what makes it a genuine check (it cannot be fit) and
  what certifies the full-``U`` machinery the analytic reduction also rides.
* **Benchmark (loose) — the cited capture data + the textbook order.** Electron capture cross-sections
  ``σ_n`` (:data:`CAPTURE_SIGMA_N`) and the thermal velocity ``v_th`` are order-of-magnitude literature
  values (Sze, *Physics of Semiconductor Devices*; Graff, *Metal Impurities in Silicon-Device
  Fabrication*); they reproduce the **textbook scaling** — clean float-zone silicon ``τ ~ ms`` /
  ``L ~ mm``, an interstitial-iron level ``[Fe] ~ 1e12 cm⁻³`` dragging ``τ`` to a few µs — but the
  numbers are **flagged**, not asserted tight. ``τ_bulk``, ``V_J`` and the leakage calibration are
  house numbers (ADR 0005 §5).

Named scope edge (the honest ceiling)
-------------------------------------
* **Generation-limited leakage only.** ``J_gen = q·n_i·W/(2τ)`` is the room-temperature dominant term;
  the diffusion (Shockley) ``J_0`` component and any trap-assisted tunnelling are named, not modelled.
* **A single effective midgap recombination centre.** The simple ``1/τ`` uses ``σ_n`` and treats the
  metal as midgap-efficient; the full :func:`srh_rate` carries ``E_t``, but the lifetime/leakage the
  game reads assume the most-efficient (midgap) case. Real Fe_i sits off midgap — folded into the
  flagged ``σ_n``.
* **Point-defect metals, fully active.** The whole dissolved metal is taken as an active recombination
  centre. Its real fate — **precipitation / gettering at junctions** (often the actual device-killer) —
  is the named **Tier-3** edge (plan §5a), *not* modelled. This is the same active-vs-chemical ceiling
  the repo carries elsewhere ([[dopant-charge-state-diffusivity-source]]).
* **Low injection.** The single-lifetime collapse assumes ``Δn ≪ N_A`` (the off-state body); high-level
  injection (``τ → τ_n0 + τ_p0``) is out.

Units — semiconductor-conventional CGS (as :mod:`chip.device` / :mod:`chip.junction`)
------------------------------------------------------------------------------------
``N`` in **cm⁻³**; ``σ`` in **cm²**; ``v_th`` in **cm/s** → recombination rate in **s⁻¹** and lifetime
``τ`` in **s**; ``D`` in **cm²/s** → diffusion length ``L`` in **cm** (reported µm); depletion width
``W`` in **cm**; leakage ``J_gen`` in **A/cm²** (reported nA/cm²). One unit system throughout; the same
``ε_Si``/``n_i``/``q`` the device and junction modules already use.

Validation boundary
-------------------
No shared engine — the SRH lifetime/leakage are closed forms (like Deal–Grove / Scheil / the compact
``V_t`` / Pfann), so this module's tests carry the whole triad: the low-injection reduction of the full
``U(n, p)`` (analytic), detailed balance ``U = 0`` at equilibrium (conservation), and the cited capture
cross-sections + textbook lifetime/leakage order (benchmark). The cross-sections are pinned to the cited
sources, *not* carried from memory; the calibration constants are flagged house numbers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .device import EPS_SI, NI_300K, thermal_voltage
from .diffusion_dopant import CM_PER_UM
from .junction import Q_ELEMENTARY

# --------------------------------------------------------------------------- #
# Cited capture data + flagged calibration constants (the loose tier — plan §7)
# --------------------------------------------------------------------------- #
# Carrier thermal velocity (cm/s) — the common textbook round figure (~1e7; the electron value is
# ~2e7 at 300 K). FLAGGED: it rides into σ·v_th as a single product, so it is part of the loose
# capture-rate calibration, not an independently asserted number.
V_TH: float = 1.0e7

# Clean-material baseline minority-carrier lifetime (s) — float-zone-grade silicon, ~1 ms. FLAGGED
# house number (the pristine ceiling a clean feed reaches; sets the clean leakage floor / the seam).
TAU_BULK: float = 1.0e-3

# Electron capture cross-sections σ_n (cm²) for the deep-level metals — order-of-magnitude literature
# values (Sze; Graff, *Metal Impurities in Silicon*). LOOSE/FLAGGED (plan §7): Fe_i is a strong
# recombination centre (~5e-14); Cu is taken an order less efficient per dissolved atom (its real
# device damage is precipitation — the Tier-3 edge). Keyed by the Contamination species name.
CAPTURE_SIGMA_N: dict[str, float] = {
    "Fe": 5.0e-14,
    "Cu": 5.0e-15,
}

# Minority-electron diffusion coefficient in the p-body (cm²/s) — representative (≈ μ_n·kT/q at
# moderate doping). FLAGGED: only feeds the narrative diffusion length L = √(Dτ), never a verdict.
D_MINORITY: float = 36.0

# Reference S/D-junction voltage (V) — built-in + a small reverse bias — for the depletion width the
# generation leakage integrates over. FLAGGED house number (~1 V is V_bi for these dopings).
JUNCTION_VOLTAGE_V: float = 1.0


# --------------------------------------------------------------------------- #
# 1. The full SRH statistics (the shared core of the analytic + conservation legs)
# --------------------------------------------------------------------------- #
def srh_rate(
    n, p, N_t: float, sigma_n: float, sigma_p: float,
    E_t_minus_Ei_eV: float = 0.0, T_celsius: float = 27.0,
    n_i: float = NI_300K, v_th: float = V_TH,
):
    """Full Shockley–Read–Hall net recombination rate ``U(n, p)`` (cm⁻³ s⁻¹) for one trap level.

    ``U = (p·n − n_i²) / [τ_p0·(n + n_1) + τ_n0·(p + p_1)]`` with ``τ_n0 = 1/(σ_n·v_th·N_t)``,
    ``τ_p0 = 1/(σ_p·v_th·N_t)`` and the occupancy factors ``n_1 = n_i·e^{(E_t−E_i)/kT}``,
    ``p_1 = n_i·e^{−(E_t−E_i)/kT}`` (``E_t_minus_Ei_eV`` the trap depth above the intrinsic level;
    ``0`` = midgap). The **shared core** of two triad legs: it is ``0`` exactly at equilibrium
    (``p·n = n_i²``, detailed balance) for any parameters, and its p-type low-injection limit reduces
    to the single minority-electron lifetime :func:`srh_lifetime` uses (``σ_p``, ``E_t`` dropping out).
    Positive ``U`` = net recombination (``pn > n_i²``); negative = net generation (the depleted region).
    """
    kT = thermal_voltage(T_celsius)                      # eV ≡ V (kT/q)
    n_1 = n_i * math.exp(E_t_minus_Ei_eV / kT)
    p_1 = n_i * math.exp(-E_t_minus_Ei_eV / kT)
    tau_n0 = 1.0 / (sigma_n * v_th * N_t)
    tau_p0 = 1.0 / (sigma_p * v_th * N_t)
    return (p * n - n_i**2) / (tau_p0 * (n + n_1) + tau_n0 * (p + p_1))


# --------------------------------------------------------------------------- #
# 2. The low-injection lifetime the game consumes (deep-level metals add their rates)
# --------------------------------------------------------------------------- #
def recombination_rate(metals, sigma: dict[str, float] = CAPTURE_SIGMA_N, v_th: float = V_TH) -> float:
    """Added SRH recombination rate ``Σ_i σ_n,i·v_th·N_i`` (s⁻¹) from the deep-level metals in ``metals``.

    ``metals`` is a :class:`chip.purification.Contamination` (read by attribute), a plain
    ``{species: cm⁻³}`` dict, or ``None`` (→ ``0.0``, the clean baseline — no added recombination).
    Each metal in ``sigma`` contributes ``σ_n·v_th·N`` independently (the rates add); species not in
    ``sigma`` (the shallow dopants, Na) are ignored here — they reach the device through doping/oxide
    charge, not recombination.
    """
    if metals is None:
        return 0.0
    rate = 0.0
    for species, sig in sigma.items():
        N = metals.get(species, 0.0) if isinstance(metals, dict) else getattr(metals, species, 0.0)
        rate += sig * v_th * float(N or 0.0)
    return rate


def srh_lifetime(metals, tau_bulk: float = TAU_BULK, sigma: dict[str, float] = CAPTURE_SIGMA_N,
                 v_th: float = V_TH) -> float:
    """Minority-carrier SRH lifetime ``τ`` (s): ``1/τ = 1/τ_bulk + Σ_i σ_n,i·v_th·N_i``.

    The clean limit is recovered **bit-for-bit** — ``metals = None`` (or all-zero) gives ``τ = τ_bulk``
    exactly (the seam: a clean feed never moves lifetime). A deep-level metal adds its recombination
    rate, so ``τ`` falls monotonically as the feedstock dirties (and recovers as zone refining scrubs
    the metal — :mod:`chip.purification`).
    """
    return 1.0 / (1.0 / tau_bulk + recombination_rate(metals, sigma, v_th))


def diffusion_length(tau: float, D: float = D_MINORITY) -> float:
    """Minority-carrier diffusion length ``L = √(D·τ)`` (cm). The narrative length-scale of the damage."""
    if tau < 0.0:
        raise ValueError(f"lifetime τ must be ≥ 0, got {tau}")
    return math.sqrt(D * tau)


# --------------------------------------------------------------------------- #
# 3. The junction reverse leakage (the spec'd device killer)
# --------------------------------------------------------------------------- #
def depletion_width(N_A: float, V_J: float = JUNCTION_VOLTAGE_V) -> float:
    """One-sided abrupt-junction depletion width ``W = √(2·ε_Si·V_J/(q·N_A))`` (cm).

    The width the generation leakage integrates over (mostly in the lighter-doped p-body, so it reads
    the substrate ``N_A``). Reuses :mod:`chip.device`'s ``ε_Si`` and :mod:`chip.junction`'s ``q``;
    ``V_J`` is the reference built-in-plus-reverse junction voltage (flagged). Heavier doping → thinner
    ``W`` → slightly less generation leakage (a secondary, coherent substrate dependence).
    """
    if N_A <= 0.0:
        raise ValueError(f"N_A must be positive, got {N_A}")
    if V_J <= 0.0:
        raise ValueError(f"junction voltage V_J must be positive, got {V_J}")
    return math.sqrt(2.0 * EPS_SI * V_J / (Q_ELEMENTARY * N_A))


def generation_leakage_density(tau: float, N_A: float, V_J: float = JUNCTION_VOLTAGE_V,
                               n_i: float = NI_300K) -> float:
    """Reverse-junction generation leakage ``J_gen = q·n_i·W/(2·τ)`` (A/cm²) — the room-temp dominant term.

    ``∝ 1/τ`` (taking the generation lifetime ``τ_g ≈ τ`` — the flagged loose-tier simplification), so
    a deep-level metal that shortens ``τ`` raises the leakage proportionally — *the* device consequence
    net doping cannot carry. ``W`` is the depletion width (:func:`depletion_width`). A clean wafer
    (``τ = τ_bulk``) gives the tiny baseline leakage (the seam — comfortably inside the spec window).
    """
    if tau <= 0.0:
        raise ValueError(f"lifetime τ must be positive, got {tau}")
    return Q_ELEMENTARY * n_i * depletion_width(N_A, V_J) / (2.0 * tau)


# --------------------------------------------------------------------------- #
# 4. The bundled lifetime/leakage reading (the loose-coupling currency the game reads)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DiodeLeakage:
    """A wafer's deep-level-metal device consequence: lifetime, diffusion length, and junction leakage.

    ``tau`` (s) the minority-carrier SRH lifetime, ``L_diff`` (cm) its diffusion length, ``j_leak``
    (A/cm²) the reverse-junction generation-leakage density, ``N_A`` (cm⁻³) the substrate the width
    read. Plain scalars — the loose-coupling currency the fab-line game's device step lifts onto the
    die (a new field), the analogue of the :class:`chip.junction.Junction` reading.
    """

    tau: float
    L_diff: float
    j_leak: float
    N_A: float

    @property
    def tau_us(self) -> float:
        """Lifetime in microseconds (the reported unit)."""
        return self.tau * 1.0e6

    @property
    def L_diff_um(self) -> float:
        """Diffusion length in micrometres."""
        return self.L_diff / CM_PER_UM

    @property
    def j_leak_nA_cm2(self) -> float:
        """Reverse leakage in nA/cm² (the spec-window / readout unit)."""
        return self.j_leak * 1.0e9


def device_leakage(
    metals, N_A: float, *, tau_bulk: float = TAU_BULK, V_J: float = JUNCTION_VOLTAGE_V,
    D: float = D_MINORITY, n_i: float = NI_300K, sigma: dict[str, float] = CAPTURE_SIGMA_N,
    v_th: float = V_TH,
) -> DiodeLeakage:
    """Read the deep-level-metal consequence (τ, L, J_gen) off the wafer ``metals`` + substrate ``N_A``.

    Convenience wiring of :func:`srh_lifetime` → :func:`diffusion_length` / :func:`generation_leakage_density`
    for the fab-line game's device step. ``metals`` may be a :class:`chip.purification.Contamination`,
    a dict, or ``None`` (clean) — clean gives ``τ = τ_bulk`` and the baseline leakage (the seam). *Bad
    purification in, a leaky low-lifetime diode out* — the metals' device consequence.
    """
    tau = srh_lifetime(metals, tau_bulk, sigma, v_th)
    return DiodeLeakage(
        tau=tau, L_diff=diffusion_length(tau, D),
        j_leak=generation_leakage_density(tau, N_A, V_J, n_i), N_A=N_A,
    )
