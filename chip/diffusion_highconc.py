"""Concentration-dependent dopant diffusivity D(N): the high-concentration box profile (Chip v1.3).

The named scope edge of :mod:`diffusion_dopant`, **promoted** (the steel-ferrite-bay / Massoud /
v1.2 move: yesterday's honest ceiling becomes today's phase). Phase 1a diffused dopants with a
**constant, intrinsic** ``D`` — exact for the ``erfc``/Gaussian forms, but weakest *exactly* where a
predeposition runs: **at the solid-solubility limit**, the maximum concentration. There, real dopant
diffusion is **concentration-enhanced**: at ``N ≫ n_i`` the diffusivity rises with the local carrier
concentration, the high-concentration front steepens into a near-vertical **"box"**, and the junction
pushes deeper than the constant-``D`` ``erfc`` predicts. This module builds that physics.

The decisive architecture finding (why this needed **no** frozen-engine amendment)
-----------------------------------------------------------------------------------
Both ``CONTRACT.md`` ("nonlinear ``D(u)`` is v1.1, **not built**") and the plan flagged ``D(N)`` as
the one case that would force a **deliberate v1.1 contract amendment** — a re-opening of the frozen
``engines.diffusion`` seal. **It does not.** The frozen contract already promises a callable
``D(t)`` (the case Steel uses for carbon-during-cooling, ``test_variable_d``), and the consumer
already drives the solver **one ``step()`` at a time** in a Python loop (:func:`diffusion_dopant._diffuse`).
A ``D(t)`` callable that *closes over a mutable holder of the evolving field*, updated **after** each
step, is therefore a **lagged-coefficient ``D(N)``** entirely within the public API: when ``step()``
assembles its implicit operator at ``t₁`` the holder still holds ``Nⁿ`` (the *old* level), so ``D`` is
frozen at the old state — the textbook **semi-implicit / frozen-coefficient** scheme, one tridiagonal
solve per step, **zero engine edits** (:func:`_diffuse_dn`). The contract blesses "``D(t)`` when the
consumer closes over a schedule"; closing over the evolving *state* is the **same mechanism**, named
not hidden — a deliberate frozen-coefficient hook, not a ``D`` that secretly reads state behind the
engine's back. And it is not merely a *lag*: an optional **Picard** iteration (re-evaluate ``D`` at the
new estimate, re-solve from ``Nⁿ``, repeat) converges the within-step coefficient to a fixed point —
which *is* the **fully-implicit nonlinear backward-Euler solve** — in ~2 iterations (the triad pins
``2 == 6``, dt-stable). So the precise claim: **``D(N)`` — the edge both docs flagged for a v1.1
amendment — is recovered as a lagged-coefficient scheme that Picard-converges to the fully-implicit
nonlinear solve, entirely within the frozen engine, no amendment.** (Contrast v1.2's OED, a ``D(t)`` of
*oxidation rate*; here ``D`` is a genuine function of the unknown ``N`` — still expressible, via the
step-loop lag.)

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
  (a) *Degenerate seam.* A constant ``D`` fed through the **same closure machinery**
  (:func:`_diffuse_dn` with a constant ``D_of_N``) equals the plain scalar-``D`` frozen-engine run
  **bit-for-bit** (``0`` difference) — the closure adds nothing when ``D`` does not vary, i.e. the
  hook *is* the frozen engine. As ``N → 0`` the model's own ``D_eff → D⁰+D⁻+D⁼`` (a constant), so the
  low-concentration profile is the constant-``D`` ``erfc``.
  (b) *Boltzmann similarity (model-independent).* A constant-source diffusion into a semi-infinite
  medium with **any** ``D(N)`` has a profile depending on ``x, t`` only through ``η = x/√t`` — a free,
  exact, *form-independent* anchor for the nonlinear path. Run at ``t`` and ``4t``; ``N(x, t)`` and
  ``N(2x, 4t)`` collapse (:func:`predeposit_highconc`, the similarity test). It validates the
  **machinery** (the lagged ``D(N)`` solve converges to the right self-similar field), independent of
  whether Fair's *coefficients* are right.
* **Conservation — a machinery check, not a physics validation.** Under a **sealed (no-flux)
  surface** drive-in, ``∫N dx`` is conserved to machine precision *even with* ``D(N)`` active — the
  finite-volume telescoping is **``D``-independent** (it holds for any non-negative ``D`` field), so
  this confirms the closure did not break the engine's structural conservation. It says **nothing**
  about whether the ``D(N)`` magnitude is right (stated plainly, the v1.2 honesty).
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

The lagged-coefficient scheme — honest numerics
-----------------------------------------------
Each implicit sub-step is linear and monotone (an M-matrix for any ``D ≥ 0``), but the **lagged
nonlinear** scheme is *not* guaranteed monotone at a steep front — it can in principle overshoot the
Dirichlet surface value. Empirically it does **not** at the resolutions used here (the box front
stays ``≤ N_surface``, no negatives), and the lag error is **first-order in ``dt``** and controlled by
refinement; an optional **Picard** corrector (``picard_iters > 0``: re-evaluate ``D`` at the new
estimate and re-solve, within the same step) tightens the front at fixed ``dt``. The tight legs above
hold for either; the validated content is the *form*, not a specific step count.

Units — semiconductor-conventional CGS, identical to :mod:`diffusion_dopant`
----------------------------------------------------------------------------
**cm / cm²·s⁻¹ / cm⁻³**; ``n_i`` in cm⁻³ (so ``n/n_i`` is dimensionless), depths reported in **µm** at
the boundary. The frozen engine is fed cm and seconds, as in Phase 1a. The ``(x, N)`` arrays are the
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

from engines.diffusion import Diffusion1D, uniform_grid, Grid, Dirichlet, Neumann
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
# 3. The stateful-closure lagged-coefficient driver (the frozen-engine hook)
# --------------------------------------------------------------------------- #
def _diffuse_dn(
    grid: Grid,
    D_of_N: Callable[[np.ndarray], np.ndarray],
    N0: np.ndarray,
    bc_left,
    bc_right,
    t_seconds: float,
    n_steps: int,
    picard_iters: int = 0,
) -> tuple[np.ndarray, float, float]:
    """March ``N0`` for ``t_seconds`` with a concentration-dependent ``D(N)`` — via the frozen engine.

    The hook (module docstring): a ``D(t)`` callable closes over ``holder["N"]``, updated **after**
    each :meth:`Diffusion1D.step`, so the operator assembled inside ``step`` reads the **old** level
    ``Nⁿ`` — a lagged-coefficient (frozen-coefficient) ``D(N)`` solve, one tridiagonal solve per step,
    **no engine edits**. ``picard_iters`` > 0 adds corrector solves within each step (re-evaluate
    ``D`` at the new estimate, re-solve from ``Nⁿ``) to tighten the nonlinear front at fixed ``dt``.

    Returns ``(N, dose, surface_flux_dose)`` — the final profile, its ``∫N dx``, and the accumulated
    ``Σ dt·flux(left)`` (the conservation diagnostic), exactly as :func:`diffusion_dopant._diffuse`.
    """
    holder = {"N": np.array(N0, dtype=float)}
    solver = Diffusion1D(grid, lambda t: D_of_N(holder["N"]), bc_left, bc_right)
    N = np.array(N0, dtype=float)
    dt = t_seconds / n_steps
    surf_flux = 0.0
    t = 0.0
    for _ in range(n_steps):
        N_old = N
        N_new = solver.step(N_old, dt, t0=t)        # D from holder == N_old (lagged predictor)
        for _ in range(picard_iters):                # optional Picard correctors at the new estimate
            holder["N"] = N_new
            N_new = solver.step(N_old, dt, t0=t)
        N = N_new
        holder["N"] = N                              # commit the new level for the next step's lag
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
    box profile is compared against. ``picard_iters`` records the scheme used.
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
    picard_iters: int


def predeposit_highconc(
    grid: Grid,
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    N_surface: float | None = None,
    n_steps: int = 800,
    picard_iters: int = 0,
    n_active_max: float | None = None,
) -> HighConcProfile:
    """Constant-source predeposition with concentration-dependent ``D(N)`` (frozen engine, Dirichlet surface).

    Holds the surface at ``N_surface`` (default the dopant's solid-solubility limit) and diffuses into
    an un-doped wafer with ``D = D_eff(N)`` (the box driver). Far end no-flux (semi-infinite). The
    near-surface ``N ≫ n_i`` region diffuses fast and steepens into the box; the dilute tail stays at
    the intrinsic ``D``. Compare against a constant-``D`` :func:`diffusion_dopant.predeposit` (or the
    ``erfc`` at ``D_intrinsic``) to read the enhancement.

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
        Dirichlet(Ns), Neumann(0.0), t_seconds, n_steps, picard_iters,
    )
    return HighConcProfile(
        x=grid.centers, N=N, dopant=name, T_celsius=T_celsius, t=t_seconds, stage="predeposition",
        N_surface=Ns, dose=dose, surface_flux_dose=surf_flux,
        D_intrinsic=intrinsic_diffusivity_lowconc(name, T_celsius), length=grid.length,
        picard_iters=picard_iters,
    )


def drive_in_highconc(
    grid: Grid,
    N_initial: np.ndarray,
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    n_steps: int = 800,
    picard_iters: int = 0,
    n_active_max: float | None = None,
) -> HighConcProfile:
    """Sealed-surface drive-in with concentration-dependent ``D(N)`` (frozen engine, Neumann(0) both ends).

    Redistributes a fixed dose with ``D = D_eff(N)`` and the surface **sealed** — so ``∫N dx`` is
    conserved to machine precision *even with* ``D(N)`` (the finite-volume telescoping is
    ``D``-independent: the conservation machinery-check). The high-concentration core relaxes faster
    than its tail, so a box flattens differently than a constant-``D`` Gaussian would. ``n_active_max``
    caps the active carrier driving ``D`` (see :func:`effective_diffusivity`).
    """
    name = _dopant_name(dopant)
    N, dose, surf_flux = _diffuse_dn(
        grid, lambda N: effective_diffusivity(name, N, T_celsius, n_active_max), np.asarray(N_initial, float),
        Neumann(0.0), Neumann(0.0), t_seconds, n_steps, picard_iters,
    )
    return HighConcProfile(
        x=grid.centers, N=N, dopant=name, T_celsius=T_celsius, t=t_seconds, stage="drive-in",
        N_surface=float(N[0]), dose=dose, surface_flux_dose=surf_flux,
        D_intrinsic=intrinsic_diffusivity_lowconc(name, T_celsius), length=grid.length,
        picard_iters=picard_iters,
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
    """The same predep recipe at a **constant** ``D_const`` through the same closure machinery → ``N(x)``.

    The constant-``D`` companion for the box-front comparison and the **degenerate-seam** test: with a
    constant ``D_of_N`` the lagged closure adds nothing, so this equals a plain scalar-``D`` frozen-
    engine predep bit-for-bit. Pass ``D_const = intrinsic_diffusivity_lowconc(...)`` for the honest
    constant baseline.
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
