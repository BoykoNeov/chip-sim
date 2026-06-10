"""The Phase 1↔2 back-coupling: oxidation-enhanced diffusion + dopant segregation (Chip v1.2).

Phases 1–2 were deliberately **forward-only**: Phase 4 consumed a Phase-1 dopant profile *and* a
Phase-2 oxide as if they were independent. They are not. Thermal oxidation **back-reacts** on the
underlying dopant profile two ways, and this module — the named §3 deferral of both
:mod:`oxidation` and the plan, now promoted (the steel-ferrite-bay / Massoud move: yesterday's named
deferral becomes today's phase) — builds them:

  * **Oxidation-enhanced diffusion (OED).** The oxidizing Si/SiO₂ interface injects silicon
    **self-interstitials** into the substrate. Dopants that diffuse with a significant
    **interstitialcy** component (B, P, As) have their diffusivity *enhanced* by the resulting
    interstitial supersaturation; a near-pure **vacancy** diffuser (Sb) is instead *retarded*
    (oxidation-retarded diffusion, ORD). The enhancement tracks the **oxidation rate** ``dx_ox/dt``
    (fast oxidation → more interstitials → more enhancement).
  * **Dopant segregation.** At the moving Si/SiO₂ interface, dopant **partitions** between silicon
    and the growing oxide by its segregation coefficient ``m``. **Boron (m < 1)** prefers the oxide
    → the silicon surface **depletes**; **phosphorus (m > 1)** is rejected by the oxide → it
    **piles up** at the silicon surface ("snowplow").

Both are expressible **entirely within the ** :mod:`engines.diffusion` **contract** — the
decisive architecture finding, and *why* this was reachable without an engine amendment:

  * OED is a **position/time-dependent diffusivity** ``D(x, t)`` (it depends on the oxidation rate
    and depth, **not** on the concentration ``N``), so it is the engine's already-supported
    *variable-D callable* ``D(t)`` case (CONTRACT.md / ``test_variable_d``) — **not** the unbuilt
    nonlinear ``D(N)`` case (that one *would* need a v1.1 contract amendment, and is the separate
    named scope edge of :mod:`diffusion_dopant`). Here OED is a clean ``D(t)`` the engine already
    promises.
  * Segregation is a **time-dependent surface flux** at the interface, i.e. a ``Neumann(flux(t))``
    boundary — also supported (BC parameters accept callables).

The unified degenerate anchor (the seam the whole module recovers v1 through)
-----------------------------------------------------------------------------
**Zero oxidation rate (``dx_ox/dt → 0``) collapses *both* effects to plain Phase-1 drive-in,
bit-for-bit.** With no oxidation there are no injected interstitials (OED enhancement → 0,
``D_eff → D_inert``) and no moving interface (segregation flux → 0, the surface re-seals), so
:func:`oxidize_couple` reduces *exactly* to :func:`diffusion_dopant.drive_in`. This is the same
"defaults-recover-v1" discipline as the Massoud ``K = 0`` seam and the planet exoplanet knobs — and
it is the **only** correct sealed limit. (A tempting alternative anchor — "``m → ∞`` re-seals the
surface" — is *wrong*: ``m → ∞`` means the oxide accepts *no* dopant, so *all* the consumed-silicon
dopant is rejected back into the silicon = **maximum pile-up**, not a sealed surface. The sealed
limit is ``dx_ox/dt → 0``, the shared OED/segregation seam.)

Validation triad (plan §3) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight, two legs on their idealizations).**
  (a) *Degenerate recovery.* ``dx_ox/dt = 0`` → :func:`oxidize_couple` equals
  :func:`diffusion_dopant.drive_in` to machine precision (both effects vanish — the unified seam).
  (b) *OED ≡ the engine's time-substitution.* A sealed-surface OED solve depends on the diffusion
  history **only through** ``∫ D_eff(t) dt`` (the variable-D ``τ = ∫D dt`` guarantee,
  ``test_variable_d``): warm-started from an analytic Gaussian it reproduces
  :func:`diffusion_dopant.analytic_drivein_gaussian` at the *effective* age
  ``a₀ + ∫ D_eff dt`` (:func:`effective_Dt`) — OED's **real** analytic leg, not merely degenerate
  recovery. **Scope edge, named:** the OED enhancement is taken **uniform in depth** (the
  interstitial recombination length ≫ a shallow junction, so the supersaturation is ~flat across
  the profile) — the depth-decay / lateral OED is the unmodeled regime; and the fixed grid neglects
  **interface recession** (see conservation).
* **Conservation — an accounting identity for the coupled case, NOT a magnitude validation
  (the honest downgrade).**
  - *OED alone, sealed surface (genuinely tight):* dose ``∫N dx`` conserved to **machine precision**
    (no-flux both ends — the engine's structural guarantee, here exercised with a *time-varying*
    ``D``). This one *is* a real conservation check.
  - *OED + segregation (an identity, not a check):* ``Si_dose + oxide_uptake`` closes to machine
    precision — but ``oxide_uptake ≡ −Σ dt·flux(left)`` is *defined* from the same flux bookkeeping
    the engine guarantees (``Δ Si_dose = Σ dt·flux(left)``), so the sum closes for **any** surface
    flux, even a wrong one. It catches an accounting *leak*; it does **not** validate the
    segregation *magnitude*. Stated plainly because the magnitude is **not** exact — see the
    swept-sliver edge.
  - *Scope edge — the swept-sliver double-count (the dominant honesty caveat).* The segregation flux
    ``N_surf·(0.44 − 1/m)·R`` is a **moving-interface** mass balance: the ``0.44·R`` term is dopant
    *freed by consumed silicon*, which physically exists **only if** the swept region ``[0, 0.44·x_ox]``
    *leaves* the silicon. The fixed grid keeps that region in the domain **and** re-injects its
    dopant as the surface flux → the swept sliver is **counted twice**. Pinned by the ``m → ∞``
    inert-oxide diagnostic (:func:`test_inert_oxide_reveals_swept_sliver_artifact`): an inert oxide
    can only snowplow, so silicon dopant must be *conserved* — yet the model spuriously **gains**
    ≈ ``∫N_surf·0.44·R dt`` (~10 % of the dose at the demo conditions). Consequences, owned not
    hidden: **surface enhancement — especially phosphorus pile-up — is overstated by
    O(recession/profile-width) ≈ 2×** (the *direction* is real and *needs* the ``0.44`` term; the
    *magnitude* is inflated), while **boron depletion is robust** because it is oxide-uptake-
    dominated (``1/m = 3.3`` vs the ``0.44`` double-count ≈ 13 %). That is why **boron — the
    device-relevant MOS channel — is the trustworthy case**, and phosphorus is the qualitative sign-
    contrast. The real fix (advance the interface, remap the ~1-cell swept region each step) is a
    Stefan-problem treatment the pure-diffusion engine cannot express; for an educational tool the
    edge is named, not silently carried.
* **Benchmark (loose / calibrated — the honest split).** What is *cited* vs *calibrated*:
  - *Cited (the form + the sign pattern):* the **half-power law** ``Δ ∝ (dx_ox/dt)^0.5`` (IUE-Vienna
    OEDS / Antoniadis & Moskowitz 1982), the per-dopant **fractional interstitialcy** ``f_I`` (B
    0.30, P 0.38, Sb 0.015 — the dual I–V quantification paper) which reproduces **enhanced (B, P)
    vs essentially-un-enhanced (Sb)** as a *non-circular* cross-check (``f_I`` is measured in a
    different domain than OED), and the **segregation coefficients** ``m`` (B 0.3, P 10 — Hollauer,
    the *same* dissertation the Massoud pin cites) which set **depletion (B) vs pile-up (P)**.
  - *Calibrated (flagged):* the supersaturation **amplitude** :data:`OED_SUPERSATURATION_AT_REF`
    (and the reference-rate normalization) — the magnitude carries the large OED literature spread
    (factors of ~2–10), so it is a transparently calibrated knob, *not* asserted tight. The
    **validated** legs above hold for *any* enhancement amplitude (they exercise machinery, not the
    constant), which is exactly why the calibration does not wound them.

  **Sb ORD is a *qualitative* scope edge, never a number.** A positive ``(dx_ox/dt)^n`` enhancement
  with ``f_I = 0.015`` yields ``D_eff/D_inert ≈ 1.05`` — a *small spurious residual-``f_I``
  enhancement*, **not** a clean 1 and (crucially) the **wrong sign** for antimony: true ORD is a
  *retardation* (``D_eff/D_inert < 1``) driven by **vacancy under-saturation**, the opposite-sign
  companion this module does **not** model. So the honest reading is "Sb is *not* enhanced (within a
  few % of 1, far below B/P)" — the framework's sign-discrimination — while its actual retardation
  magnitude is named-not-claimed (the advisor's blocking call: no Sb number from a B/P-calibrated
  form). Sb is **not** a demo dopant; it is the scope-edge illustration.

The segregation boundary condition (a moving-interface mass balance, on a non-moving grid)
------------------------------------------------------------------------------------------
As the interface advances into silicon at ``v_Si = 0.44·dx_ox/dt`` (the :data:`oxidation.SI_SIO2_RATIO`
the Phase-2 conservation leg already pins), of the dopant *freed* by the consumed silicon
(``N_surf·0.44·dx_ox``) the oxide takes up only ``C_ox·dx_ox = (N_surf/m)·dx_ox`` (segregation
equilibrium ``C_Si/C_ox = m``); the remainder fluxes **back into the silicon**::

    J_surface = N_surf(t) · (0.44 − 1/m) · (dx_ox/dt)        [+x = into silicon]

— negative (net **depletion**) for boron ``m < 1`` (``0.44 − 3.3 < 0``), positive (net **pile-up**)
for phosphorus ``m > 1`` (``0.44 − 0.1 > 0``). **No free transport coefficient**: the coefficient is
fixed by the cited ``m`` and the ``0.44`` already in :mod:`oxidation`. The exact closed-interface-
equilibrium form is the cited segregation BC (Hollauer §4.1 / Plummer–Deal–Griffin), and the robust
fact ``m → ∞ ≠ sealed`` (an inert oxide *snowplows*, it does not re-seal) holds across formulations.
**But the ``0.44`` term is the interface *recession***, and the grid does not recede: the swept
region is kept in the domain *and* its dopant re-injected at the surface, double-counting it (the
swept-sliver scope edge above — direction right, surface magnitude ~2× high; boron robust because it
is oxide-uptake-dominated). So this BC is the correct *interface balance* applied to a fixed grid: an
educational reduction whose error is **named, not erased**. Because ``J_surface`` depends on the
*evolving* surface value ``N_surf(t)``
(which the engine does not expose to a BC), it is applied **explicitly (lagged one sub-step)**: an
``O(dt)`` accuracy choice that leaves conservation **machine-exact** (the engine applies whatever
flux it is handed, exactly) — refine ``n_steps`` for fidelity, never for closure.

Units — semiconductor CGS-cm (the diffusion side; the oxidation rate converted at the boundary)
-----------------------------------------------------------------------------------------------
This is fundamentally a **diffusion** modification, so it lives in :mod:`diffusion_dopant`'s native
**CGS-cm / s / cm⁻³** (``D`` cm²/s, ``N`` cm⁻³, depth cm → µm at the boundary, dose cm⁻²) — *not*
:mod:`oxidation`'s µm-hr. The one cross-module quantity, the oxidation rate ``dx_ox/dt``, is consumed
**at the boundary**: as a **dimensionless ratio** ``R/R_ref`` for the (unit-free) supersaturation,
and converted to **cm/s** for the segregation flux (a real ``cm⁻²/s``). One unit system within the
module; the per-module native-units rule (each chip module computes in its cited data's native
units) honored.

Validation boundary
-------------------
The solver machinery is the engine's (``engines/diffusion/tests``); the constants are cited
(the OED/segregation source notes). This module's tests validate the **coupling instantiation**: the
unified degenerate seam, the OED effective-``∫D dt`` leg, the per-scenario conservation, and the
cited-``f_I``/``m`` direction benchmarks. The OED *amplitude* is calibrated (flagged), so the
benchmark leg leans on **citation fidelity** (the form, the exponent, the ``f_I``/``m`` values) plus
the tight machinery legs — never on the amplitude.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engines.diffusion import Diffusion1D, Grid, Neumann, uniform_grid

from .diffusion_dopant import (
    CM_PER_UM,
    DOPANTS,
    Dopant,
    analytic_drivein_gaussian,
    diffusivity,
)
from .oxidation import (
    MIN_PER_HOUR,
    SI_SIO2_RATIO,
    UM_PER_NM,
    growth_rate,
    massoud_growth_rate,
    massoud_rate_constants,
    oxide_rate_constants,
    oxide_thickness,
    oxide_thickness_massoud,
)

SEC_PER_HOUR = 3600.0


# --------------------------------------------------------------------------- #
# 1. Cited constants — OED point-defect factors + segregation coefficients
# --------------------------------------------------------------------------- #
# Fractional interstitialcy f_I: the fraction of a dopant's diffusion carried by the
# interstitialcy (vs vacancy) mechanism — the per-dopant factor that scales the OED
# enhancement and discriminates enhanced (B, P, As) from ORD (Sb). Cited values at ~1000–1100 °C
# from the dual interstitialcy–vacancy quantification of B/P/As/Sb in Si (see the
# oed-source memory note: IEEE, "Quantification of Diffusion Mechanisms…"). B/P interstitialcy-
# significant → enhanced; Sb ≈ pure vacancy (f_I ≈ 0.015) → NOT enhanced by this form (true ORD
# retardation needs the unmodeled vacancy-undersaturation term — the named Sb scope edge).
FRACTIONAL_INTERSTITIALCY: dict[str, float] = {
    "B": 0.30,
    "P": 0.38,
    "As": 0.35,   # mixed I/V — present for the scope-edge discussion (not a demo dopant)
    "Sb": 0.015,  # near-pure vacancy → essentially un-enhanced (ORD is the named scope edge)
}

# The OED interstitial supersaturation Δ = (C_I/C_I* − 1) ∝ (dx_ox/dt)^n. The half-power exponent
# n ≈ 0.5 is cited (IUE-Vienna OEDS analytical model; Antoniadis & Moskowitz, J. Appl. Phys.
# 53(10):6788, 1982 — literature spread 0.3–0.5, the named exponent uncertainty). The amplitude is
# CALIBRATED (flagged): the magnitude carries the large OED literature spread, so it is set to give
# representative enhancements (boron ~2× at a typical dry-gate-oxidation rate), NOT asserted tight.
# The validated legs (degenerate recovery, effective-∫D dt, conservation) hold for ANY amplitude.
OED_RATE_EXPONENT = 0.5                  # n — cited half-power law (dimensionless)
OED_REFERENCE_RATE_UM_PER_HR = 0.1       # R_ref — a documented normalization (NOT physics)
OED_SUPERSATURATION_AT_REF = 5.0         # Δ at R_ref — CALIBRATED (the flagged amplitude knob)

# Dopant segregation coefficient m = (solubility in Si)/(solubility in SiO₂) — Hollauer, TU Wien
# diss. (2007) §4.1 Table 4.1 (the SAME dissertation the Massoud thin-dry pin cites — one coherent
# lineage). m < 1 → dopant prefers the oxide → surface DEPLETES (boron); m > 1 → rejected by the
# oxide → surface PILES UP (phosphorus). The definition (Si/SiO₂, not the inverse) is pinned with
# the source: inverting it would flip depletion↔pile-up (the Massoud-τ-sign-typo discipline).
SEGREGATION_COEFFICIENT: dict[str, float] = {
    "B": 0.3,    # m = 0.1–0.3 cited; 0.3 the representative value → boron depletion
    "P": 10.0,   # m ≈ 10 cited → phosphorus pile-up
}


# --------------------------------------------------------------------------- #
# 2. The oxidation-rate provider — dx_ox/dt(t) from Phase 2 (boundary conversion)
# --------------------------------------------------------------------------- #
def oxidation_rate_um_per_hr(
    ambient, T_celsius: float, orientation: str = "100",
    *, model: str = "deal-grove", x_initial: float = 0.0,
):
    """Build ``R(t_seconds) → dx_ox/dt`` (µm/hr) for the oxidation that drives the coupling.

    Returns a callable of **diffusion-native seconds** giving the instantaneous oxide growth rate
    in **oxidation-native µm/hr** — the cross-module quantity, evaluated at the boundary. ``model``
    is ``"deal-grove"`` (the Phase-2 closed form, any ambient) or ``"massoud"`` (the v1.1 thin-dry
    correction — **dry O₂ only**, the rate that actually matters for a gate oxide). The rate is
    high early (thin oxide, linear regime) and decays as the film thickens — so OED is strongest at
    the start of the step, the correct physics.
    """
    if model == "deal-grove":
        rates = oxide_rate_constants(ambient, T_celsius, orientation)

        def R(t_seconds: float) -> float:
            t_hr = t_seconds / SEC_PER_HOUR
            x = oxide_thickness(t_hr, rates.B, rates.A, x_initial=x_initial)
            return float(growth_rate(x, rates.B, rates.A))

        return R

    if model == "massoud":
        mrates = massoud_rate_constants(T_celsius, orientation)

        def R(t_seconds: float) -> float:
            t_min = t_seconds / 60.0
            x_um = oxide_thickness_massoud(t_min, mrates, x_initial=x_initial)
            rate_nm_min = float(massoud_growth_rate(x_um, t_min, mrates))
            return rate_nm_min * UM_PER_NM * MIN_PER_HOUR  # nm/min → µm/hr

        return R

    raise ValueError(f"model must be 'deal-grove' or 'massoud', got {model!r}")


# --------------------------------------------------------------------------- #
# 3. OED — the interstitial supersaturation and the enhancement factor
# --------------------------------------------------------------------------- #
def interstitial_supersaturation(rate_um_per_hr) -> float:
    """Interstitial supersaturation ``Δ = (C_I/C_I* − 1)`` at oxidation rate ``dx_ox/dt`` (µm/hr).

    The cited **half-power law** ``Δ = Δ_ref·(R/R_ref)^n`` with ``n`` :data:`OED_RATE_EXPONENT`
    (≈ 0.5) and the calibrated amplitude :data:`OED_SUPERSATURATION_AT_REF` at the reference rate.
    A ratio of rates → **dimensionless**, so it does not matter that ``R`` is in oxidation-native
    µm/hr. ``Δ = 0`` at zero oxidation rate (the degenerate seam).
    """
    R = np.asarray(rate_um_per_hr, dtype=float)
    if np.any(R < 0.0):
        raise ValueError("oxidation rate must be ≥ 0")
    return OED_SUPERSATURATION_AT_REF * (R / OED_REFERENCE_RATE_UM_PER_HR) ** OED_RATE_EXPONENT


def oed_enhancement_factor(dopant: Dopant | str, rate_um_per_hr) -> float:
    """OED diffusivity enhancement ``D_eff/D_inert = 1 + f_I·Δ`` at oxidation rate ``dx_ox/dt``.

    ``f_I`` is the cited :data:`FRACTIONAL_INTERSTITIALCY` of the dopant and ``Δ`` the
    :func:`interstitial_supersaturation`. Returns the dimensionless multiplier on the intrinsic
    diffusivity:

      * **B, P** (``f_I`` 0.30 / 0.38) → factor **> 1**, oxidation-*enhanced* diffusion;
      * **Sb** (``f_I`` 0.015) → factor **≈ 1**, essentially un-enhanced (NOT a retardation claim —
        true ORD is the named vacancy-undersaturation scope edge);
      * **rate → 0** → factor **= 1** for *every* dopant (the unified degenerate seam).
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    f_I = FRACTIONAL_INTERSTITIALCY.get(d.name, 0.0)
    return 1.0 + f_I * interstitial_supersaturation(rate_um_per_hr)


# --------------------------------------------------------------------------- #
# 4. Segregation — the moving-boundary surface flux (the conserving BC)
# --------------------------------------------------------------------------- #
def segregation_flux(N_surface: float, rate_cm_per_s: float, m: float) -> float:
    """Dopant flux across the moving interface ``J = N_surf·(0.44 − 1/m)·(dx_ox/dt)`` (cm⁻²/s, +x).

    The moving-boundary mass balance (module docstring): of the dopant freed by consumed silicon
    (``N_surf·0.44·dx_ox``) the oxide takes ``N_surf/m·dx_ox``; the rest fluxes back into silicon.
    Sign in the engine's **+x = into-silicon** convention at the left boundary:

      * **m < 1** (boron) → ``0.44 − 1/m < 0`` → **negative** (out of silicon → depletion);
      * **m > 1** (phosphorus) → ``0.44 − 1/m > 0`` → **positive** (into silicon → pile-up);
      * **rate = 0** → ``0`` (the surface re-seals — the degenerate seam).

    ``rate_cm_per_s`` is ``dx_ox/dt`` converted to CGS at the boundary (a *real* flux, unlike the
    unit-free supersaturation ratio). No free transport coefficient — the coefficient is the cited
    ``m`` and the ``0.44`` :data:`oxidation.SI_SIO2_RATIO`.
    """
    if m <= 0.0:
        raise ValueError(f"segregation coefficient m must be positive, got {m}")
    return N_surface * (SI_SIO2_RATIO - 1.0 / m) * rate_cm_per_s


# --------------------------------------------------------------------------- #
# 5. The effective ∫D dt — the OED analytic-leg anchor
# --------------------------------------------------------------------------- #
def effective_Dt(
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    rate_provider,
    *,
    oed: bool = True,
    n_steps: int = 600,
) -> float:
    """The effective diffusion length-squared ``∫₀ᵗ D_eff(t') dt'`` (cm²) over an oxidizing anneal.

    The engine's variable-D guarantee is that a sealed-surface profile depends on the
    diffusion history **only through** this integral (the ``τ = ∫D dt`` time substitution,
    ``test_variable_d``). So a warm-started analytic Gaussian propagated under OED reproduces the
    analytic Gaussian at the effective age ``a₀ + effective_Dt`` — OED's real analytic leg. With
    ``oed=False`` this is just ``D_inert·t`` (the plain drive-in age). Trapezoidal over the same
    sub-steps :func:`oxidize_couple` marches, so the test and the solve see one integral.
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    D_inert = diffusivity(d, T_celsius)
    if not oed:
        return D_inert * t_seconds
    t_grid = np.linspace(0.0, t_seconds, n_steps + 1)
    D_eff = D_inert * np.array([oed_enhancement_factor(d, rate_provider(t)) for t in t_grid])
    return float(np.trapezoid(D_eff, t_grid))


# --------------------------------------------------------------------------- #
# 6. The coupled solve — OED + segregation during an oxidizing anneal
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CoupledResult:
    """The dopant profile after an oxidizing anneal, with its silicon/oxide dose bookkeeping.

    ``x``/``N`` are the cell-centre depths (**cm**) and the evolved profile (**cm⁻³**) — the plain
    ``(x, N)`` pair :mod:`junction` consumes downstream. ``dopant``/``T_celsius``/``t_seconds`` echo
    the step; ``oed``/``segregation`` which effects were active; ``model`` the oxidation law.
    ``D_inert`` (cm²/s) is the unenhanced diffusivity; ``effective_Dt`` (cm²) the ``∫D_eff dt`` the
    OED solve actually integrated. The accounting (cm⁻²): ``si_dose`` is the final ``∫N dx``;
    ``oxide_uptake`` the reservoir ``−Σ dt·flux(left)`` (positive = dopant taken **into** the oxide
    → depletion; negative = **rejected toward** silicon → pile-up); ``si_dose_initial`` the starting
    dose. ``si_dose + oxide_uptake = si_dose_initial`` closes to machine precision — but this is an
    **accounting identity** (``oxide_uptake`` is *defined* from the same flux bookkeeping), not a
    magnitude check: the reservoir carries the swept-sliver double-count (module docstring), so the
    *phosphorus* surface magnitude is ~2× high (direction real). The *boron* case is robust.
    """

    x: np.ndarray
    N: np.ndarray
    dopant: str
    T_celsius: float
    t_seconds: float
    oed: bool
    segregation: bool
    model: str
    D_inert: float
    effective_Dt: float
    si_dose_initial: float
    si_dose: float
    oxide_uptake: float
    length: float

    @property
    def surface_concentration(self) -> float:
        """The evolved surface cell value ``N(0)`` (cm⁻³) — depleted (B) or piled-up (P)."""
        return float(self.N[0])

    @property
    def conservation_residual(self) -> float:
        """``|si_dose + oxide_uptake − si_dose_initial|`` (cm⁻²) — the accounting-leak check.

        Machine-zero by construction (``oxide_uptake`` is defined from the engine's flux bookkeeping,
        so the sum closes for *any* flux). It catches an accounting leak, **not** the segregation
        magnitude — the reservoir carries the named swept-sliver double-count (class docstring).
        """
        return abs(self.si_dose + self.oxide_uptake - self.si_dose_initial)


def oxidize_couple(
    grid: Grid,
    N_initial: np.ndarray,
    dopant: Dopant | str,
    ambient,
    T_celsius: float,
    t_minutes: float,
    *,
    orientation: str = "100",
    oed: bool = True,
    segregation: bool = True,
    segregation_m: float | None = None,
    model: str = "deal-grove",
    x_initial_oxide: float = 0.0,
    n_steps: int = 600,
) -> CoupledResult:
    """Diffuse ``N_initial`` through an **oxidizing** anneal — OED + segregation, the back-coupling.

    The Phase-1↔2 coupled step: a furnace anneal that **grows oxide and redistributes dopant at the
    same time**. Unlike :func:`diffusion_dopant.drive_in` (a sealed inert anneal), here the oxidizing
    interface (i) **enhances** the diffusivity via OED (the time-varying ``D_eff(t)`` callable the
    engine accepts) and (ii) **segregates** dopant across the moving boundary (a lagged
    ``Neumann(flux(t))`` surface BC). The far end stays no-flux (semi-infinite).

    Parameters
    ----------
    grid, N_initial
        The depth grid and the starting profile (e.g. a Phase-1 predep/drive-in ``N``, cm⁻³).
    dopant, ambient, T_celsius, t_minutes
        Species, oxidizing ambient (``"dry"``/``"wet"``), temperature (°C), and anneal time (min).
    orientation, model, x_initial_oxide
        Passed to the oxidation-rate provider (``"deal-grove"``/``"massoud"``; ``massoud`` is dry-
        only thin-oxide; an initial oxide shifts the rate via Phase-2's ``τ``/seed machinery).
    oed, segregation
        Toggle each effect (both on by default). ``oed=False, segregation=False`` ⇒ a plain inert
        drive-in (and ``dx_ox/dt → 0`` makes the two *physically* coincide — the degenerate anchor).
    segregation_m
        Override the cited segregation coefficient ``m`` (default: the registry value for the
        dopant). Lets a learner explore the partition — and drives the ``m → ∞`` inert-oxide
        diagnostic that exposes the named swept-sliver double-count.
    n_steps
        Sub-steps of the explicit (lagged) segregation coupling; refine for fidelity (conservation
        is machine-exact at any ``n_steps`` — the engine applies the handed flux exactly).
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    D_inert = diffusivity(d, T_celsius)
    t_seconds = t_minutes * 60.0
    N = np.array(N_initial, dtype=float)
    if N.shape != (grid.n,):
        raise ValueError(f"N_initial must have length {grid.n}, got {N.shape}")

    R_um_hr = oxidation_rate_um_per_hr(
        ambient, T_celsius, orientation, model=model, x_initial=x_initial_oxide,
    )
    f_I = FRACTIONAL_INTERSTITIALCY.get(d.name, 0.0)
    m = SEGREGATION_COEFFICIENT.get(d.name) if segregation_m is None else float(segregation_m)
    if segregation and m is None:
        raise ValueError(
            f"no cited segregation coefficient for {d.name!r} "
            f"(have {sorted(SEGREGATION_COEFFICIENT)}) — pass segregation=False or segregation_m=…")

    # OED diffusivity as the engine's D(t) callable (scalar → broadcast; uniform in depth,
    # the named recombination-length-≫-junction reduction). oed=False ⇒ the bare intrinsic D.
    def D_of_t(t_seconds_: float) -> float:
        if not oed:
            return D_inert
        return D_inert * (1.0 + f_I * float(interstitial_supersaturation(R_um_hr(t_seconds_))))

    si_dose_initial = float(np.sum(N * grid.widths))
    oxide_uptake = 0.0
    dt = t_seconds / n_steps
    t = 0.0
    for _ in range(n_steps):
        # Lagged segregation flux from the CURRENT surface value (explicit coupling): O(dt) in
        # fidelity, machine-exact in conservation (the engine applies this flux exactly).
        if segregation:
            R_cm_s = R_um_hr(t) * CM_PER_UM / SEC_PER_HOUR
            J_left = segregation_flux(float(N[0]), R_cm_s, m)
            left_bc = Neumann(J_left)
        else:
            J_left = 0.0
            left_bc = Neumann(0.0)
        solver = Diffusion1D(grid, D_of_t, left_bc, Neumann(0.0))
        N = solver.step(N, dt, t0=t)
        # Reservoir = dopant that left silicon across the surface. Neumann flux(left) is exactly the
        # prescribed J_left, so Si_dose change = dt·J_left and oxide_uptake = −dt·J_left closes the
        # balance to machine precision (the engine's flux-bookkeeping identity).
        oxide_uptake += -dt * J_left
        t += dt

    si_dose = float(np.sum(N * grid.widths))
    eff_Dt = effective_Dt(d, T_celsius, t_seconds, R_um_hr, oed=oed, n_steps=n_steps)
    return CoupledResult(
        x=grid.centers, N=N, dopant=d.name, T_celsius=T_celsius, t_seconds=t_seconds,
        oed=oed, segregation=segregation, model=model, D_inert=D_inert, effective_Dt=eff_Dt,
        si_dose_initial=si_dose_initial, si_dose=si_dose, oxide_uptake=oxide_uptake,
        length=grid.length,
    )
