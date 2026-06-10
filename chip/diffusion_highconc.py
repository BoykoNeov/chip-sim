"""Concentration-dependent dopant diffusivity D(N): the high-concentration box profile (Chip v1.3).

The named scope edge of :mod:`diffusion_dopant`, **promoted** (the steel-ferrite-bay / Massoud /
v1.2 move: yesterday's honest ceiling becomes today's phase). Phase 1a diffused dopants with a
**constant, intrinsic** ``D`` — exact for the ``erfc``/Gaussian forms, but weakest *exactly* where a
predeposition runs: **at the solid-solubility limit**, the maximum concentration. There, real dopant
diffusion is **concentration-enhanced**: at ``N ≫ n_i`` the diffusivity rises with the local carrier
concentration, the high-concentration front steepens into a near-vertical **"box"**, and the junction
pushes deeper than the constant-``D`` ``erfc`` predicts. This module builds that physics.

The native engine path (promoted from the v1.3 consumer-side lag)
----------------------------------------------------------------
``D(N)`` is a genuine **nonlinear** diffusivity — ``D`` is a function of the *unknown* field ``N`` —
the one regime ``CONTRACT.md`` long listed as deferred ("nonlinear ``D(u)`` is v1.1, **not built**").
It is now built **into the engine**: ``D(N)`` is wrapped in
:class:`~engines.diffusion.StateDependent` and handed to the solver, which solves each implicit step
**nonlinearly by Picard** — assemble the operator with ``D`` frozen at the current iterate, do the one
tridiagonal solve, re-evaluate ``D`` at the result, repeat to a fixed point (= the fully-implicit
nonlinear backward-Euler solve). This is the **first exercise of the engine unfreeze** (ADR 0004):
the surface is now open + test-gated, so the deferred nonlinear regime grows *into* the engine by an
ordinary, suite-gated edit rather than being routed around it.

*Historical note (the v1.3 build, now superseded).* v1.3 originally built ``D(N)`` **without** an
engine edit, because the engine was frozen at the time: the consumer drove the solver one ``step()``
at a time and a ``D(t)`` callable closing over a mutable holder of the evolving field — updated *after*
each step — gave a **lagged-coefficient** ``D(N)`` entirely within the public API, with an optional
in-consumer Picard corrector converging it to the fully-implicit solve. That was a real result (the
frozen engine was more expressive than it looked), but with the unfreeze the honest home for the
nonlinear solve is the engine itself: :func:`_diffuse_dn` is now a thin step-loop over a
``StateDependent`` solver — no holder, no consumer-side correctors, the engine converges the step.
(Contrast v1.2's OED, a ``D(t)`` of *oxidation rate* — a position/time-dependent diffusivity that
still fits the **linear** ``D(t)`` path; ``D(N)`` is the genuinely nonlinear case, and it is the one
that motivated the native path.)

The model — Fair's charge-state diffusivity (cited, the box driver)
-------------------------------------------------------------------
At high doping the diffusivity is the sum over the charge states of the vacancy/interstitialcy the
dopant pairs with (Plummer–Deal–Griffin eqn 7.18; each component Arrhenius, eqn 7.19)::

    D_eff(n) = D⁰ + D⁻·(n/n_i) + D⁼·(n/n_i)²          (n-type: P, As, Sb)
    D_eff(p) = D⁰ + D⁺·(p/n_i)                         (p-type: B)

with ``Dˣ = Dˣ₀·exp(−Eˣ/kT)`` (:data:`CHARGE_STATE_TERMS`, slide-15 table). The carrier
concentration follows from charge neutrality, ``n = N/2 + √((N/2)² + n_i²)`` — so ``n → n_i`` as
``N → 0`` (the diffusivity smoothly recovers its **intrinsic** value ``D⁰+D⁻+D⁼``) and ``n → N`` as
``N ≫ n_i``. **Phosphorus is the showcase:** its doubly-negative-vacancy ``D⁼`` term gives the
strong ``(n/n_i)²`` dependence that drives the **boxiest** profile (slide 15; "no coupling produces a
'boxier' profile because of concentration dependent diffusion," slide 25). The intrinsic ``n_i(T)``
matters because it sets *where* the enhancement bites: at diffusion temperatures it is enormous
(``n_i(1000 °C) ≈ 7×10¹⁸ cm⁻³``, eight orders above the room-temperature ``10¹⁰``), so only the
near-surface ``N ≳ n_i`` region is enhanced and the deep tail stays intrinsic.

Validation triad (plan §3) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit (tight, two legs).**
  (a) *Degenerate seam.* A constant ``D`` fed through the **native nonlinear path**
  (:func:`constant_D_predeposit` → a constant ``StateDependent``) equals the plain scalar-``D`` engine
  run **bit-for-bit** (``0`` difference) — Picard converges in the first iterate when ``D`` does not
  vary, i.e. the nonlinear hook *is* the engine. This is now an **engine** invariant
  (``engines/diffusion/tests/test_nonlinear_d.py``); the chip leg keeps the physics corollary that as
  ``N → 0`` the model's own ``D_eff → D⁰+D⁻+D⁼`` (a constant), so the low-concentration profile is the
  constant-``D`` ``erfc``.
  (b) *Boltzmann similarity (model-independent).* A constant-source diffusion into a semi-infinite
  medium with **any** ``D(N)`` has a profile depending on ``x, t`` only through ``η = x/√t`` — a free,
  exact, *form-independent* anchor for the nonlinear path. Run at ``t`` and ``4t``; ``N(x, t)`` and
  ``N(2x, 4t)`` collapse (:func:`predeposit_highconc`, the similarity test). It validates the
  **machinery** (the nonlinear ``D(N)`` solve converges to the right self-similar field), independent
  of whether Fair's *coefficients* are right. (The engine carries the model-independent version of
  this anchor too — ``test_nonlinear_d.py`` — for a generic ``D(u)``.)
* **Conservation — a machinery check, not a physics validation.** Under a **sealed (no-flux)
  surface** drive-in, ``∫N dx`` is conserved to machine precision *even with* ``D(N)`` active — the
  finite-volume telescoping is **``D``-independent** (it holds for any non-negative ``D`` field, per
  Picard iterate), so this confirms the nonlinear path did not break the engine's structural
  conservation. It says **nothing** about whether the ``D(N)`` magnitude is right (stated plainly, the
  v1.2 honesty).
* **Benchmark (loose / calibrated split).**
  - *Cited (the form + the box trend):* the charge-state model and its coefficients
    (Plummer–Deal–Griffin Ch. 7 / Fair & Tsai 1977), and the qualitative result that ``D∝(n/n_i)²``
    yields the **box-shaped high-concentration profile + a deeper junction** than constant ``D``
    (slides 15/25/27). Reproduced as a *non-circular* cross-check — the coefficients are cited
    diffusion data, not fit to the box.
  - *Calibrated / approximated (flagged):* the assumption of **full electrical activation**
    (``n = N``, no solubility/clustering cap on the active carriers) and the omission of the
    built-in-**field** factor ``h = 1 + N/√(N²+4n_i²)`` (a further ≤2× enhancement, slide 14) — both
    are within the model's honest approximation, and the *tight* legs (degenerate seam, Boltzmann
    similarity, conservation) hold regardless.

The scope edge — the kink and the tail (named, **not** modeled)
---------------------------------------------------------------
This is an **equilibrium charge-state** model: it delivers the high-concentration enhancement, the
steep box **front** (the "kink" side), and the deeper junction. It does **not** reproduce the
anomalous extended **tail** of a phosphorus profile, nor the concentration **plateau**: those arise
from **non-equilibrium** point-defect physics — phosphorus-vacancy pair dissociation injecting
silicon self-interstitials, dopant clustering/precipitation, and the resulting buried-layer enhanced
diffusion (Velichko, *arXiv*:1905.10667; Fair & Tsai's "emitter-dip"; Plummer slide 22's I-release
tail / "emitter push"). Equilibrium ``D(n)`` has no term for them. So the honest reading is: **the
box front is captured, the tail is the named ceiling** — the same exact-anchor-vs-scope-edge
discipline as Phase 1a's constant-``D`` and v1.1's thin-dry anomaly. The plateau (active carriers
saturate below the chemical ``N`` once clustering sets in) is why the full-activation ``n = N`` above
is the flagged approximation.

The nonlinear solve — honest numerics
-------------------------------------
Each Picard **iterate** is a linear, monotone backward-Euler solve (an M-matrix for any ``D ≥ 0``),
so it inherits the engine's discrete maximum principle bounded by the data ``[0, N_surface]`` — and
the converged fixed point therefore stays in those bounds too. This is asserted **empirically**, not
claimed as a theorem about the nonlinear scheme (the box front stays ``≤ N_surface``, no negatives;
the v1.3 "don't over-claim monotonicity" discipline). The engine converges the within-step
coefficient to its fixed point automatically (default ``picard_tol``/``picard_max_iter``); the
consumer no longer carries a lag or a corrector count. The validated content is the *form* of the
box, not a step count.

Units — semiconductor-conventional CGS, identical to :mod:`diffusion_dopant`
----------------------------------------------------------------------------
**cm / cm²·s⁻¹ / cm⁻³**; ``n_i`` in cm⁻³ (so ``n/n_i`` is dimensionless), depths reported in **µm** at
the boundary. The engine is fed cm and seconds, as in Phase 1a. The ``(x, N)`` arrays are the
plain loose-coupling currency :mod:`junction` consumes — a box profile reads its (deeper) ``x_j`` and
(lower) ``R_s`` with no change to the junction reader.

Sources (pinned at build — the ``[[…-source]]`` discipline, all directly read)
------------------------------------------------------------------------------
* **Model + coefficients + box benchmark** — Plummer, Deal & Griffin, *Silicon VLSI Technology*
  (Prentice Hall, 2000), Ch. 7 (eqns 7.18/7.19, the slide-15 charge-state table; the box-profile
  slides 15/25/27); primary: **R. B. Fair & J. C. C. Tsai, J. Electrochem. Soc. 124, 1107 (1977)**
  (the phosphorus charge-state model + emitter-dip). The *same* Plummer text already cited for the
  Phase-1a Fair ``D(T)`` and the Phase-2 Deal–Grove constants — one coherent lineage.
* **The non-equilibrium kink/tail scope edge + a high-T ``n_i`` cross-check** — O. I. Velichko,
  "A comprehensive model of high-concentration phosphorus diffusion in silicon," *arXiv*:1905.10667
  (2019): the plateau/kink/tail decomposition, and ``n_i(890 °C) = 4.6×10¹⁸ cm⁻³``.
* **``n_i(T)``** — the standard process-simulation form ``n_i = 3.87×10¹⁶·T^{3/2}·exp(−0.605 eV/kT)``
  (Plummer Ch. 7), cross-checked numerically: ``1.4×10¹⁰`` at 300 K and ``3.7×10¹⁸`` at 890 °C
  (vs Velichko's directly-read ``4.6×10¹⁸``). Enters only through the ratio ``n/n_i``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np

from engines.diffusion import Diffusion1D, uniform_grid, Grid, Dirichlet, Neumann, StateDependent
from chip.diffusion_dopant import (
    DOPANTS,
    Dopant,
    K_BOLTZMANN_EV,
    ABS_ZERO,
    CM_PER_UM,
    diffusivity,
    analytic_predep_erfc,
)

# --------------------------------------------------------------------------- #
# 1. Intrinsic carrier concentration n_i(T) — sets where the enhancement bites
# --------------------------------------------------------------------------- #
NI_PREFACTOR = 3.87e16   # cm⁻³ K^−1.5 — standard process-simulation prefactor (Plummer Ch. 7)
NI_GAP_EV = 0.605        # eV — the effective half-gap in the n_i Arrhenius


def intrinsic_carrier_concentration(T_celsius: float) -> float:
    """Silicon intrinsic carrier concentration ``n_i(T) = 3.87e16·T^1.5·exp(−0.605/kT)`` (**cm⁻³**).

    ``T`` in **°C** (→ kelvin internally). At diffusion temperatures ``n_i`` is enormous — ``≈ 7e18``
    at 1000 °C, eight orders above the room-temperature ``1e10`` — which is *why* only the near-surface
    high-concentration region (``N ≳ n_i``) is diffusivity-enhanced while the deep tail stays intrinsic.
    Cross-checked: ``1.4e10`` at 300 K, ``3.7e18`` at 890 °C (Velichko's directly-read ``4.6e18``).
    """
    T_K = T_celsius + ABS_ZERO
    if T_K <= 0.0:
        raise ValueError(f"temperature must be above absolute zero, got {T_celsius} °C")
    return NI_PREFACTOR * T_K**1.5 * math.exp(-NI_GAP_EV / (K_BOLTZMANN_EV * T_K))


# --------------------------------------------------------------------------- #
# 2. Fair charge-state diffusivity components (Plummer Ch. 7 slide-15 table)
# --------------------------------------------------------------------------- #
# Per dopant: a list of (D0 [cm²/s], Ea [eV], power) charge-state terms, where ``power`` is the
# exponent on the carrier ratio (n/n_i) — 0 = neutral D⁰, 1 = single (D⁻ donor / D⁺ acceptor),
# 2 = double D⁼. Each component is Arrhenius D = D0·exp(−Ea/kT) (eqn 7.19). The neutral D⁰ for P
# (3.85, 3.66) and Sb (0.214, 3.65) match the Phase-1a intrinsic values in DOPANTS exactly — the
# Phase-1a "intrinsic D" was Fair's neutral component all along. NOTE the exception: boron's
# charge-state sum D⁰+D⁺ ≈ 1.0 (3.5 eV) is ~30 % above the Phase-1a B value (0.76, 3.46 eV) — a
# different Fair fit, not a transcription error — so a boron box uses this slide-15 set, not DOPANTS.
CHARGE_STATE_TERMS: dict[str, list[tuple[float, float, int]]] = {
    "B":  [(0.05, 3.5, 0), (0.95, 3.5, 1)],            # D⁰ + D⁺(p/n_i)
    "P":  [(3.85, 3.66, 0), (4.44, 4.0, 1), (44.2, 4.37, 2)],  # D⁰ + D⁻(n/n_i) + D⁼(n/n_i)²
    "As": [(0.011, 3.44, 0), (31.0, 4.15, 1)],         # D⁰ + D⁻(n/n_i)
    "Sb": [(0.214, 3.65, 0), (15.0, 4.08, 1)],         # D⁰ + D⁻(n/n_i)
}

# Representative active-carrier ceiling for phosphorus at diffusion temperatures: the **electrically
# active** electron concentration saturates well below the chemical solubility once clustering /
# precipitation sets in (the "plateau"). Velichko (arXiv:1905.10667) reads n_e,max ≈ 3.4e20 cm⁻³.
# Passing this as ``n_active_max`` caps the carrier that drives D — the flagged full-activation
# (n = N) approximation made adjustable — which both tames the (n/n_i)² magnitude to a physical value
# and produces the flat-topped plateau. ``None`` = uncapped (full activation, the raw equilibrium model).
N_ACTIVE_MAX_P = 3.4e20


def _dopant_name(dopant: Dopant | str) -> str:
    name = dopant if isinstance(dopant, str) else dopant.name
    if name not in CHARGE_STATE_TERMS:
        raise KeyError(f"no charge-state coefficients for {name!r}; have {sorted(CHARGE_STATE_TERMS)}")
    return name


def _default_surface_concentration(name: str, N_surface: float | None) -> float:
    """The predep Dirichlet surface value: explicit ``N_surface``, else the dopant's solubility.

    The solid-solubility default comes from :data:`DOPANTS` (B/P/Sb). A charge-state-only dopant
    (As — present for the n²-vs-n¹ comparison but not in the Phase-1a solubility registry) must pass
    ``N_surface`` explicitly.
    """
    if N_surface is not None:
        return float(N_surface)
    if name not in DOPANTS:
        raise ValueError(f"{name!r} has no solid-solubility default; pass N_surface explicitly")
    return DOPANTS[name].N_solid_solubility


def intrinsic_diffusivity_lowconc(dopant: Dopant | str, T_celsius: float) -> float:
    """The model's low-concentration limit ``D⁰+D⁻+D⁼`` (**cm²/s**) — the constant-``D`` box baseline.

    As ``N → 0`` the carrier ratio ``n/n_i → 1`` and every charge-state term contributes once, so the
    full charge-state ``D_eff`` collapses to this constant. It is the **honest constant-``D``
    reference** for the box-front comparison (same dopant, the diffusivity the model itself reduces to
    in the dilute tail) — distinct from :func:`diffusion_dopant.diffusivity`, which is the **neutral
    ``D⁰`` component only** (~93 % of this for P; the ``D⁻/D⁼`` terms add the small remainder).
    """
    name = _dopant_name(dopant)
    T_K = T_celsius + ABS_ZERO
    return float(sum(D0 * math.exp(-Ea / (K_BOLTZMANN_EV * T_K)) for D0, Ea, _ in CHARGE_STATE_TERMS[name]))


def effective_diffusivity(
    dopant: Dopant | str, N: np.ndarray, T_celsius: float, n_active_max: float | None = None,
) -> np.ndarray:
    """Concentration-dependent diffusivity ``D_eff(N)`` (**cm²/s**), Fair charge-state model (eqn 7.18).

    ``N`` (cm⁻³) the local dopant concentration, ``T`` in °C. The carrier concentration is taken from
    charge neutrality ``n = N/2 + √((N/2)² + n_i²)`` (majority carrier; ``n → n_i`` at low ``N``,
    ``n → N`` at high ``N``), and ``D_eff = Σ_k Dₖ(T)·(n/n_i)^{power_k}``. Vectorized over ``N``.
    Returns a length-``N`` array (the engine's cell-centered ``D(x)`` form). For boron the same form
    holds with the hole concentration ``p`` (its D⁰/D⁺ terms); the carrier-from-``N`` map is identical.

    ``n_active_max`` (cm⁻³, optional) **caps the active carrier** that drives ``D`` — the flagged
    full-activation (``n = N``) approximation made adjustable (see :data:`N_ACTIVE_MAX_P`). ``None`` is
    full activation, the raw equilibrium model whose ``(n/n_i)²`` magnitude is an upper bound; a cap at
    the active-carrier plateau gives a ~10× smaller, more physical enhancement (and the flat-top shape).
    The cap is a function of ``N`` at fixed ``T``, so it preserves the Boltzmann-similarity property.
    """
    name = _dopant_name(dopant)
    N = np.asarray(N, dtype=float)
    n_i = intrinsic_carrier_concentration(T_celsius)
    T_K = T_celsius + ABS_ZERO
    # majority carrier from charge neutrality (|net active dopant|); smooth n_i floor.
    half = 0.5 * np.clip(N, 0.0, None)
    carrier = half + np.sqrt(half * half + n_i * n_i)
    if n_active_max is not None:
        carrier = np.minimum(carrier, float(n_active_max))   # activation/plateau cap
    ratio = carrier / n_i
    D = np.zeros_like(N)
    for D0, Ea, power in CHARGE_STATE_TERMS[name]:
        D += D0 * math.exp(-Ea / (K_BOLTZMANN_EV * T_K)) * ratio**power
    return D


# --------------------------------------------------------------------------- #
# 3. The native-engine nonlinear-D(N) driver
# --------------------------------------------------------------------------- #
def _diffuse_dn(
    grid: Grid,
    D_of_N: Callable[[np.ndarray], np.ndarray],
    N0: np.ndarray,
    bc_left,
    bc_right,
    t_seconds: float,
    n_steps: int,
) -> tuple[np.ndarray, float, float]:
    """March ``N0`` for ``t_seconds`` with a concentration-dependent ``D(N)`` — the engine's native
    nonlinear path.

    ``D_of_N`` is wrapped in :class:`~engines.diffusion.StateDependent` and handed straight to the
    solver, which solves each implicit step **nonlinearly by Picard** — the fully-implicit nonlinear
    backward-Euler solve the v1.3 consumer-side lag was an approximation to (module docstring). No
    coefficient holder, no manual correctors: the engine evaluates ``D(N)`` against each Picard
    iterate and converges within the step. The step-loop is retained only to accumulate the per-step
    surface-flux dose (the conservation diagnostic), exactly as :func:`diffusion_dopant._diffuse`.

    Returns ``(N, dose, surface_flux_dose)`` — the final profile, its ``∫N dx``, and the accumulated
    ``Σ dt·flux(left)``.
    """
    solver = Diffusion1D(grid, StateDependent(D_of_N), bc_left, bc_right)
    N = np.array(N0, dtype=float)
    dt = t_seconds / n_steps
    surf_flux = 0.0
    t = 0.0
    for _ in range(n_steps):
        N = solver.step(N, dt, t0=t)
        t += dt
        surf_flux += dt * solver.flux(N, "left", t=t)
    return N, solver.total(N), surf_flux


# --------------------------------------------------------------------------- #
# 4. The fab steps with concentration-dependent D → HighConcProfile
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class HighConcProfile:
    """A concentration-dependent-``D`` dopant profile ``N(x)`` from one fab step + its dose bookkeeping.

    Same plain ``(x, N)`` loose-coupling currency :mod:`junction` consumes (depths **cm**, ``N``
    **cm⁻³**). ``dopant``/``T_celsius``/``t``/``stage`` record the step; ``dose`` is ``∫N dx`` (cm⁻²),
    ``surface_flux_dose`` the accumulated ``Σ dt·flux(left)``; ``D_intrinsic`` is the model's
    low-concentration constant (:func:`intrinsic_diffusivity_lowconc`) — the constant-``D`` baseline a
    box profile is compared against.
    """

    x: np.ndarray
    N: np.ndarray
    dopant: str
    T_celsius: float
    t: float
    stage: str
    N_surface: float
    dose: float
    surface_flux_dose: float
    D_intrinsic: float
    length: float


def predeposit_highconc(
    grid: Grid,
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    N_surface: float | None = None,
    n_steps: int = 800,
    n_active_max: float | None = None,
) -> HighConcProfile:
    """Constant-source predeposition with concentration-dependent ``D(N)`` (engine, Dirichlet surface).

    Holds the surface at ``N_surface`` (default the dopant's solid-solubility limit) and diffuses into
    an un-doped wafer with ``D = D_eff(N)`` (the box driver), solved by the engine's native nonlinear
    ``StateDependent`` path (Picard per step). Far end no-flux (semi-infinite). The near-surface
    ``N ≫ n_i`` region diffuses fast and steepens into the box; the dilute tail stays at the intrinsic
    ``D``. Compare against a constant-``D`` :func:`diffusion_dopant.predeposit` (or the ``erfc`` at
    ``D_intrinsic``) to read the enhancement.

    ``N_surface`` defaults to the dopant's solid-solubility limit when it is in :data:`DOPANTS`
    (B/P/Sb); for a charge-state-only dopant (e.g. As) it must be passed explicitly. ``n_active_max``
    caps the active carrier driving ``D`` (the flagged full-activation approximation; see
    :func:`effective_diffusivity` / :data:`N_ACTIVE_MAX_P`) — pass it for the physical plateau magnitude.
    """
    name = _dopant_name(dopant)
    Ns = _default_surface_concentration(name, N_surface)
    N0 = np.zeros(grid.centers.size)
    N, dose, surf_flux = _diffuse_dn(
        grid, lambda N: effective_diffusivity(name, N, T_celsius, n_active_max), N0,
        Dirichlet(Ns), Neumann(0.0), t_seconds, n_steps,
    )
    return HighConcProfile(
        x=grid.centers, N=N, dopant=name, T_celsius=T_celsius, t=t_seconds, stage="predeposition",
        N_surface=Ns, dose=dose, surface_flux_dose=surf_flux,
        D_intrinsic=intrinsic_diffusivity_lowconc(name, T_celsius), length=grid.length,
    )


def drive_in_highconc(
    grid: Grid,
    N_initial: np.ndarray,
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    n_steps: int = 800,
    n_active_max: float | None = None,
) -> HighConcProfile:
    """Sealed-surface drive-in with concentration-dependent ``D(N)`` (engine, Neumann(0) both ends).

    Redistributes a fixed dose with ``D = D_eff(N)`` (the engine's native nonlinear ``StateDependent``
    path) and the surface **sealed** — so ``∫N dx`` is conserved to machine precision *even with*
    ``D(N)`` (the finite-volume telescoping is ``D``-independent, a conservation machinery-check that
    holds per Picard iterate). The high-concentration core relaxes faster than its tail, so a box
    flattens differently than a constant-``D`` Gaussian would. ``n_active_max`` caps the active
    carrier driving ``D`` (see :func:`effective_diffusivity`).
    """
    name = _dopant_name(dopant)
    N, dose, surf_flux = _diffuse_dn(
        grid, lambda N: effective_diffusivity(name, N, T_celsius, n_active_max), np.asarray(N_initial, float),
        Neumann(0.0), Neumann(0.0), t_seconds, n_steps,
    )
    return HighConcProfile(
        x=grid.centers, N=N, dopant=name, T_celsius=T_celsius, t=t_seconds, stage="drive-in",
        N_surface=float(N[0]), dose=dose, surface_flux_dose=surf_flux,
        D_intrinsic=intrinsic_diffusivity_lowconc(name, T_celsius), length=grid.length,
    )


def constant_D_predeposit(
    grid: Grid,
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    D_const: float,
    N_surface: float | None = None,
    n_steps: int = 800,
) -> np.ndarray:
    """The same predep recipe at a **constant** ``D_const`` through the same native path → ``N(x)``.

    The constant-``D`` companion for the box-front comparison: a constant ``D_of_N`` fed through the
    native ``StateDependent`` path converges in the first Picard iterate and so equals a plain
    scalar-``D`` engine predep **bit-for-bit** (the degenerate seam, now an engine invariant —
    ``engines/diffusion/tests/test_nonlinear_d.py``). Pass ``D_const = intrinsic_diffusivity_lowconc(...)``
    for the honest constant baseline.
    """
    name = _dopant_name(dopant)
    Ns = _default_surface_concentration(name, N_surface)
    N0 = np.zeros(grid.centers.size)
    N, _, _ = _diffuse_dn(
        grid, lambda N: np.full(grid.n, D_const), N0,
        Dirichlet(Ns), Neumann(0.0), t_seconds, n_steps,
    )
    return N


def junction_depth_simple(x: np.ndarray, N: np.ndarray, N_background: float) -> float:
    """First depth (**cm**) where ``N(x)`` falls below ``N_background`` — the box vs constant-D x_j.

    A light local reader for the demo/tests (the full Irvin reading lives in :mod:`junction`); linear
    interpolation across the crossing cell. Returns ``nan`` if the profile never crosses.
    """
    x = np.asarray(x, float)
    N = np.asarray(N, float)
    below = np.where(N < N_background)[0]
    if below.size == 0 or below[0] == 0:
        return float("nan")
    i = below[0]
    # linear interpolation in x for N == N_background between cells i-1 and i
    frac = (N[i - 1] - N_background) / (N[i - 1] - N[i])
    return float(x[i - 1] + frac * (x[i] - x[i - 1]))
