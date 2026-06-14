"""Dopant diffusion: the spine in mass mode → the predep/drive-in chain (Chip Phase 1a).

The *same* sealed :mod:`engines.diffusion` solver that cooled Steel's Jominy bar (heat
mode) and carburized its gear tooth (carbon mass mode) now diffuses **dopant atoms** into
silicon — the chip face of the program spine. Two classic fab steps, both straight
instantiations of the contract:

  * **Predeposition** — a constant-source step. The wafer surface is held at the dopant's
    **solid-solubility limit** ``N_s`` (a fixed atmosphere/glass source), so the surface is
    a :class:`~engines.diffusion.Dirichlet` boundary and the profile is the **error
    function** ``N(x) = N_s·erfc(x / 2√(Dt))`` — the program's headline analytical limit,
    here laying down a thin, dose-controlled layer.
  * **Drive-in** (a.k.a. *redistribution*) — the surface is then **sealed** (the source
    removed, an oxide cap grown), so it becomes a :class:`~engines.diffusion.Neumann` ``(0)``
    no-flux boundary. The fixed dose ``Q`` deposited by the predep redistributes deeper, the
    profile morphing from ``erfc`` toward a **Gaussian** ``N(x) = (Q/√(πDt))·exp(−x²/4Dt)``
    (exact for a delta-function initial dose). Total dose is conserved (no-flux both ends).

Chain the two and a **pn junction** emerges where the diffused profile crosses the wafer's
opposite-type background doping ``N_B`` (read by :mod:`junction`). *Recipe in — times,
temperatures, dopant — junction out.* This is the cheapest proof of the program thesis: the
spine reuses verbatim. Carburizing already exercised the identical Dirichlet/Neumann mass
mode, so Phase 1a is low-risk spine reuse, not new solver work.

The exact-anchor vs realistic-demo split (the project's standing discipline)
----------------------------------------------------------------------------
The exact ``erfc`` and ``Gaussian`` forms hold only for a **single idealized step** with
**constant D**:

  * the ``erfc`` is exact for a constant Dirichlet surface into a semi-infinite uniform solid;
  * the ``Gaussian`` is exact only for a **delta-function** initial dose at a sealed surface.

The **realistic two-step demo** (:func:`two_step`) runs predep(``erfc``) → drive-in starting
from *that actual* ``erfc`` profile — which is therefore only **near-Gaussian**, not the exact
delta-IC Gaussian. So the demo is **not** asserted against the exact Gaussian (that would let a
realistic approximation wound the exact analytic leg); the exact forms are validated on their
*idealizations* (:func:`analytic_predep_erfc`, :func:`analytic_drivein_gaussian`, warm-started),
and the demo's job is the **junction**. This mirrors Steel's exact-anchor-separate-from-
realistic-demo split (carburize's erfc anchor vs its predep→quench demo).

The named scope edge (bites the predep leg specifically — sharper than carburize's)
-----------------------------------------------------------------------------------
The exact forms assume **constant, intrinsic D**. The honest ceiling, named not hidden:

  * Real high-concentration diffusion is **concentration-enhanced** ``D(N)`` — the wrinkle
    carburize did *not* have: a **predep runs *at* the solid-solubility limit** = maximum
    concentration = **precisely where constant-D erfc is weakest**. So the constant-D-vs-``D(N)``
    edge (carburize's Tibbetts analogue) bites the *predep leg* hardest. The exact erfc/Gaussian legs
    are validated on their idealizations; the realistic predep→drive-in demo's job is the junction,
    not the exact form. **BUILT in v1.3** (:mod:`diffusion_highconc`): the Fair charge-state ``D(N)``
    and its **box** profile — and the decisive finding is that it needed **no** engine
    amendment (``CONTRACT.md`` flags nonlinear ``D(u)`` as unbuilt, and it *stays* unbuilt **in the
    engine**): a lagged-coefficient ``D(N)`` is reachable from the *consumer's* step-loop via a
    stateful ``D(t)`` closure, Picard-converging to the fully-implicit solve. The box **front** +
    deeper junction are captured; the anomalous phosphorus **tail/kink** (non-equilibrium) remains the
    named scope edge there.
  * The dopants diffuse by **different mechanisms** (B, P interstitial-assisted; Sb vacancy),
    so a single intrinsic Arrhenius is a reduction — the literature spread in ``D₀/Ea`` *is*
    this content, not an error to resolve.

Units — semiconductor-conventional CGS (the deliberate departure from Steel's SI)
---------------------------------------------------------------------------------
=====================  ==============  =====================================================
quantity               unit           note
=====================  ==============  =====================================================
length ``x``           **cm**          reported in **µm** at the API boundary (``*1e4``)
time ``t``             **s**           minutes accepted at the entry points (process unit)
diffusivity ``D``      **cm²/s**       Fair ``D₀`` is *native* cm²/s — no conversion
concentration ``N``    **cm⁻³**        Trumbore ``N_s`` is *native* cm⁻³ — no conversion
dose ``Q = ∫N dx``     **cm⁻²**        (atoms per cm² of wafer)
temperature            **°C**          → kelvin internally for the Arrhenius
=====================  ==============  =====================================================
The engine is unit-agnostic (no physical constant is baked in — verified; it solves
the PDE in whatever consistent length/time the consumer feeds it), so we run it in **cm and
seconds**. This keeps every cited constant in the exact units its source states (best for
verifiability) and lets :mod:`junction` integrate ``R_s`` in Ω/sq directly. **One unit system
throughout the module — never split m-for-diffusion / cm-for-R_s.**

Validation boundary
-------------------
The solver machinery is the engine's, validated in ``engines/diffusion/tests``. This
module's tests validate the **dopant instantiation**: the erfc/Gaussian forms (constant-D),
the dose conservation + predep flux-bookkeeping identity, and (with :mod:`junction`) the
junction-depth / sheet-resistance benchmark vs Irvin. The diffusivity *values* (``D₀, Ea``)
are cited Fair data, **not** fit to junction depth — what makes that benchmark a cross-check.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.special import erfc, erfcinv

from engines.diffusion import Diffusion1D, uniform_grid, Grid, Dirichlet, Neumann

# --------------------------------------------------------------------------- #
# Physical constants (eV system for the Arrhenius — the dopant-data convention)
# --------------------------------------------------------------------------- #
K_BOLTZMANN_EV = 8.617333262e-5   # eV/K — Boltzmann constant (Arrhenius uses kT in eV)
ABS_ZERO = 273.15                 # 0 °C in kelvin
CM_PER_UM = 1.0e-4                # 1 µm = 1e-4 cm  (report depths as x_cm / CM_PER_UM)


# --------------------------------------------------------------------------- #
# 1. The dopant registry — cited Arrhenius D(T) + solid solubility (eV, cm²/s, cm⁻³)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Dopant:
    """A dopant species: its Arrhenius diffusivity, type, and predep solubility ceiling.

    All in **native** semiconductor units (no conversion at use): ``D0`` (cm²/s) and ``Ea``
    (eV) are the Fair intrinsic-diffusivity constants ``D(T) = D0·exp(−Ea/kT)``; ``kind`` is
    ``"n"`` (donor, P/As/Sb) or ``"p"`` (acceptor, B), which :mod:`junction` reads to pick the
    carrier mobility; ``N_solid_solubility`` (cm⁻³) is the representative Trumbore maximum
    solubility — the **predeposition Dirichlet surface value** (the source atmosphere holds the
    surface at this thermodynamic ceiling, *not* a free knob).
    """

    name: str
    D0: float                  # cm²/s  (Fair intrinsic pre-exponential)
    Ea: float                  # eV     (Fair intrinsic activation energy)
    kind: str                  # "n" (donor) | "p" (acceptor)
    N_solid_solubility: float  # cm⁻³   (representative Trumbore solubility @ predep temps)


# Fair (1981) intrinsic diffusivities, reproduced in Plummer–Deal–Griffin (the same standard
# text Phase 2's Deal–Grove constants cite — one coherent lineage). eV + cm²/s. B & P (the
# pn-junction-demo pair) are confirmed; see the dopant-diffusivity-source memory note. Solid
# solubilities are representative Trumbore (1960, BSTJ 39:205) values over the ~950–1100 °C
# predep range (dopant-solid-solubility-source memory note) — used as the predep surface N_s.
DOPANTS: dict[str, Dopant] = {
    "B": Dopant("B", D0=0.76, Ea=3.46, kind="p", N_solid_solubility=3.0e20),
    "P": Dopant("P", D0=3.85, Ea=3.66, kind="n", N_solid_solubility=1.2e21),
    # n-type companions, present for completeness / the scope-edge discussion (not demo dopants):
    "Sb": Dopant("Sb", D0=0.214, Ea=3.65, kind="n", N_solid_solubility=6.0e19),
}


def diffusivity(dopant: Dopant | str, T_celsius: float) -> float:
    """Intrinsic dopant diffusivity ``D = D0·exp(−Ea/kT)`` (**cm²/s**), ``T`` in **°C**.

    The cited Fair value (``D0`` cm²/s, ``Ea`` eV; ``k = 8.617e-5 eV/K``), converted to
    kelvin internally (Arrhenius needs absolute ``T``). For boron at 1100 °C ≈ 1.5e-13 cm²/s,
    giving ``2√(Dt) ≈ 0.47 µm`` over 1 h — a sane junction-depth scale. Constant in ``x``
    (concentration-independent — the erfc reduction; real ``D(N)`` is the named scope edge).
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    T_K = T_celsius + ABS_ZERO
    if T_K <= 0.0:
        raise ValueError(f"temperature must be above absolute zero, got {T_celsius} °C")
    return d.D0 * math.exp(-d.Ea / (K_BOLTZMANN_EV * T_K))


# --------------------------------------------------------------------------- #
# 2. The analytic profiles + the predep dose identity (the analytical-limit legs)
# --------------------------------------------------------------------------- #
def analytic_predep_erfc(x: np.ndarray, t: float, D: float, N_surface: float) -> np.ndarray:
    """Predeposition profile ``N(x) = N_s·erfc(x / 2√(Dt))`` (cm⁻³) — the constant-source erfc.

    Exact for a constant surface concentration ``N_s`` diffusing into a semi-infinite uniform
    (here zero-doped) solid with constant ``D``. ``x`` (cm, from the surface), ``t`` (s),
    ``D`` (cm²/s). The analytical limit the numeric :func:`predeposit` is validated against.
    """
    x = np.asarray(x, dtype=float)
    if t <= 0.0:
        raise ValueError(f"time must be > 0, got {t}")
    return N_surface * erfc(x / (2.0 * math.sqrt(D * t)))


def analytic_drivein_gaussian(x: np.ndarray, t: float, D: float, dose: float) -> np.ndarray:
    """Drive-in profile ``N(x) = (Q/√(πDt))·exp(−x²/4Dt)`` (cm⁻³) — the limited-source Gaussian.

    Exact for a **delta-function** initial dose ``Q`` (cm⁻²) at a sealed (no-flux) surface,
    constant ``D``. The even Gaussian has zero slope at ``x=0`` so it satisfies the no-flux
    surface BC automatically — which is why warm-starting the numeric solver with this field
    and propagating it forward is an exact-solution test (:func:`drive_in`). ``x`` (cm), ``t``
    (s), ``D`` (cm²/s). Surface concentration is ``N(0) = Q/√(πDt)``.
    """
    x = np.asarray(x, dtype=float)
    if t <= 0.0:
        raise ValueError(f"time must be > 0, got {t}")
    return (dose / math.sqrt(math.pi * D * t)) * np.exp(-(x**2) / (4.0 * D * t))


def predep_dose(N_surface: float, D: float, t: float) -> float:
    """Predeposition dose ``Q(t) = (2/√π)·N_s·√(Dt) ≈ 1.128·N_s·√(Dt)`` (cm⁻²).

    The flux-bookkeeping identity: ``∫₀^∞ N_s·erfc(x/2√(Dt)) dx``. This is the dopant the
    predep step lays down — the seed the drive-in then redistributes (and the conservation
    leg's analytic target; the carburize Dirichlet flux analogue, exact for the erfc profile).
    """
    if D <= 0.0 or t <= 0.0:
        raise ValueError("D and t must be positive")
    return (2.0 / math.sqrt(math.pi)) * N_surface * math.sqrt(D * t)


# --------------------------------------------------------------------------- #
# 3. The engine wrapper + the two fab steps → DopantProfile
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DopantProfile:
    """A 1-D dopant profile ``N(x)`` from one fab step, plus its dose bookkeeping.

    ``x`` are cell-centre depths from the surface (**cm**); ``N`` the dopant profile (**cm⁻³**);
    ``t``/``D`` the step (s, cm²/s); ``stage`` is ``"predeposition"`` or ``"drive-in"``.
    ``dose`` is ``∫N dx`` (cm⁻², the engine's ``total``); ``surface_flux_dose`` is the
    independent integral ``Σ dt·flux(left)`` of the surface flux — for the **predep** (Dirichlet
    surface, no-flux far field) the two grow together and equal ``1.128·N_s·√(Dt)`` to the
    engine's exact backward-Euler precision (the conservation leg); for the **drive-in** (no-flux
    both ends) the surface flux is ~0 and ``dose`` is conserved. The ``(x, N)`` pair is the plain
    array :mod:`junction` consumes — the loose-coupling currency every chip module exchanges.
    """

    x: np.ndarray
    N: np.ndarray
    t: float
    D: float
    stage: str
    N_surface: float
    dose: float
    surface_flux_dose: float
    length: float
    method: str
    effective_Dt: float | None = None  # ∫D(T(t))dt of a transient (spike) anneal; None = isothermal step

    def erfc_profile(self) -> np.ndarray:
        """The analytic predep ``erfc`` profile at this step's ``x``, ``t``, ``D`` (cm⁻³)."""
        return analytic_predep_erfc(self.x, self.t, self.D, self.N_surface)

    def gaussian_profile(self) -> np.ndarray:
        """The analytic drive-in ``Gaussian`` for this step's dose at its ``x``, ``t``, ``D``."""
        return analytic_drivein_gaussian(self.x, self.t, self.D, self.dose)


def _diffuse(
    grid: Grid, D: float, N0: np.ndarray, bc_left, bc_right,
    t_seconds: float, n_steps: int, method: str,
) -> tuple[np.ndarray, float, float]:
    """Thin engine wrapper: march ``N0`` for ``t_seconds`` → ``(N, dose, surf_flux)``.

    The single place the engine is called. ``dose`` is the final ``∫N dx``; ``surf_flux`` is the
    accumulated ``Σ dt·flux(left)`` — the surface flux integrated over the march, the
    conservation diagnostic. Backward Euler (default) makes the flux identity machine-exact.
    """
    solver = Diffusion1D(grid, D, bc_left, bc_right, method=method)
    N = np.array(N0, dtype=float)
    dt = t_seconds / n_steps
    surf_flux = 0.0
    t = 0.0
    for _ in range(n_steps):
        N = solver.step(N, dt, t0=t)
        t += dt
        surf_flux += dt * solver.flux(N, "left", t=t)
    return N, solver.total(N), surf_flux


def predeposit(
    grid: Grid,
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    N_surface: float | None = None,
    n_steps: int = 600,
    method: str = "backward_euler",
) -> DopantProfile:
    """Constant-source predeposition → the ``erfc`` profile (engine, **Dirichlet** surface).

    Holds the surface at ``N_surface`` (default = the dopant's solid-solubility limit) and
    diffuses into an initially un-doped wafer; the far end is no-flux (semi-infinite, provided
    ``length ≳ 3√(Dt)``). The accumulated surface flux is the dose laid down, comparable to the
    analytic ``predep_dose`` (the conservation/flux-bookkeeping leg).

    Parameters
    ----------
    grid : Grid
        The depth grid (``engines.diffusion.uniform_grid(length_cm, n_cells)``).
    dopant, T_celsius, t_seconds
        Species, predep temperature (°C → :func:`diffusivity`), and time (s).
    N_surface : float, optional
        Surface (Dirichlet) concentration in cm⁻³; defaults to ``dopant.N_solid_solubility``.
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    Ns = d.N_solid_solubility if N_surface is None else float(N_surface)
    D = diffusivity(d, T_celsius)
    N0 = np.zeros(grid.centers.size)
    N, dose, surf_flux = _diffuse(
        grid, D, N0, Dirichlet(Ns), Neumann(0.0), t_seconds, n_steps, method,
    )
    return DopantProfile(
        x=grid.centers, N=N, t=t_seconds, D=D, stage="predeposition",
        N_surface=Ns, dose=dose, surface_flux_dose=surf_flux,
        length=grid.length, method=method,
    )


def drive_in(
    grid: Grid,
    N_initial: np.ndarray,
    dopant: Dopant | str,
    T_celsius: float,
    t_seconds: float,
    n_steps: int = 600,
    method: str = "backward_euler",
) -> DopantProfile:
    """Sealed-surface drive-in → redistribute a fixed dose (engine, **Neumann(0)** both ends).

    Takes an existing profile ``N_initial`` (e.g. a predep ``erfc``, or a warm-started analytic
    Gaussian) and redistributes it deeper at ``T_celsius`` for ``t_seconds`` with the surface
    **sealed** (no source) — so the total dose ``∫N dx`` is conserved to machine precision (no-flux
    both ends), and the profile relaxes from ``erfc`` toward ``Gaussian``. The surface flux is ~0
    (the sealed-surface check). ``N_surface`` on the returned profile is the (evolved) surface
    cell value, *not* a Dirichlet condition.
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    D = diffusivity(d, T_celsius)
    N, dose, surf_flux = _diffuse(
        grid, D, np.asarray(N_initial, float), Neumann(0.0), Neumann(0.0),
        t_seconds, n_steps, method,
    )
    return DopantProfile(
        x=grid.centers, N=N, t=t_seconds, D=D, stage="drive-in",
        N_surface=float(N[0]), dose=dose, surface_flux_dose=surf_flux,
        length=grid.length, method=method,
    )


def two_step(
    dopant: Dopant | str = "B",
    *,
    T_predep: float = 950.0,
    t_predep_min: float = 15.0,
    T_drivein: float = 1100.0,
    t_drivein_min: float = 30.0,
    drivein_program: "ThermalProgram | None" = None,
    N_surface: float | None = None,
    length_um: float = 3.0,
    n_cells: int = 600,
    n_steps: int = 600,
) -> tuple[DopantProfile, DopantProfile]:
    """The realistic two-step diffusion: predep → drive-in → ``(predep, drivein)`` profiles.

    A short, hot **predeposition** lays down a thin ``erfc`` dose at the solubility limit; a
    longer, hotter sealed-surface **drive-in** redistributes it deeper toward a (near-)Gaussian.
    The defaults give ``D_drive·t_drive ≫ D_predep·t_predep`` (≈70×) so the profile spreads
    well beyond the predep and the ``erfc`` → ``Gaussian`` **morph reads clearly** — the
    teaching point. Both steps share one grid (the drive-in continues the predep profile).

    This is the **banked-demo chain**, *not* an exact-Gaussian test: the drive-in starts from the
    actual ``erfc`` (not a delta), so its profile is only **near-Gaussian** and is **not**
    asserted against :func:`analytic_drivein_gaussian` — the demo's job is the junction (see the
    module docstring's exact-anchor-vs-demo split). Times are in **minutes** (the process unit).

    ``drivein_program`` (E1, optional) replaces the isothermal drive-in with a **transient**
    (spike/RTA) anneal :class:`ThermalProgram` ``T(t)`` (:func:`drive_in_program`). When set,
    ``T_drivein``/``t_drivein_min`` are **bypassed** — the program governs both the temperature
    schedule *and* the duration (``program.duration``). ``None`` (default) is the isothermal step,
    bit-for-bit unchanged (the seam).
    """
    grid = uniform_grid(length_um * CM_PER_UM, n_cells)
    predep = predeposit(grid, dopant, T_predep, t_predep_min * 60.0,
                        N_surface=N_surface, n_steps=n_steps)
    if drivein_program is None:
        drivein = drive_in(grid, predep.N, dopant, T_drivein, t_drivein_min * 60.0,
                           n_steps=n_steps)
    else:
        drivein = drive_in_program(grid, predep.N, dopant, drivein_program, n_steps=n_steps)
    return predep, drivein


# --------------------------------------------------------------------------- #
# 4. Transient thermal budget — the spike/RTA anneal (E1: the D(T(t)) path)
# --------------------------------------------------------------------------- #
# E1 (scope-edge backlog). A spike / rapid-thermal anneal (RTA) ramps the wafer through a
# temperature schedule T(t) rather than holding one setpoint, so the diffusivity is the
# time-varying ``D(T(t))``. The verify-at-build gate ("is T emergent or just the setpoint?")
# resolves to **setpoint**: in silicon the dopant/thermal diffusivity ratio √(D/α) ≈ 1.2e-6, so
# at a junction's length scale the thermal field is always flat — T(t) is spatially uniform over
# the diffusion domain. So this is NOT a heat-mode engine consumer (that premise is falsified,
# the same way Robin-G was; heat-mode stays Steel-program-only). It is the engine's already-
# shipped **time-dependent D(t)** path — the exact twin of OED's ``coupling.effective_Dt``: a
# ``D(T(t))`` closure marched by the engine, the run depending on history only through the
# integrated budget ``∫D dt`` (the τ-substitution, ``engines.diffusion test_variable_d``).
@dataclass(frozen=True)
class ThermalProgram:
    """A transient anneal temperature schedule ``T(t)`` (°C) — the spike/RTA profile.

    A piecewise-linear spike: a heating ramp from ``T_base`` to ``T_peak`` at ``ramp_up_C_per_s``,
    an optional ``hold_s`` dwell at the peak, then a cooling ramp back to ``T_base`` at
    ``ramp_down_C_per_s``. ``__call__(t)`` returns the temperature (°C) at time ``t`` (s); before
    ``0`` and after :attr:`duration` it reads ``T_base`` (where ``D`` is negligible). All rates are
    magnitudes (``|dT/dt|`` > 0). The degenerate :meth:`isothermal` constructor (``T_base ==
    T_peak``) is the seam — a flat schedule that reproduces the isothermal :func:`drive_in`.
    """

    T_peak: float                  # °C — the peak (anneal) temperature
    ramp_up_C_per_s: float         # °C/s — heating rate to the peak (magnitude > 0)
    ramp_down_C_per_s: float       # °C/s — cooling rate from the peak (magnitude > 0)
    hold_s: float = 0.0            # s — dwell at the peak (0 = a pure spike, no plateau)
    T_base: float = 600.0          # °C — ramp endpoints; below this D is negligible (Arrhenius)

    def __post_init__(self) -> None:
        if self.ramp_up_C_per_s <= 0.0 or self.ramp_down_C_per_s <= 0.0:
            raise ValueError("ramp rates must be positive magnitudes (°C/s)")
        if self.hold_s < 0.0:
            raise ValueError("hold_s must be ≥ 0")
        if self.T_peak < self.T_base:
            raise ValueError("T_peak must be ≥ T_base")

    @classmethod
    def isothermal(cls, T_celsius: float, duration_s: float) -> "ThermalProgram":
        """A flat schedule ``T(t) = T_celsius`` over ``[0, duration_s]`` — the degenerate seam.

        ``T_base == T_peak`` collapses both ramps to zero width, so :meth:`__call__` returns
        ``T_celsius`` everywhere and the duration is ``duration_s``. Fed to :func:`drive_in_program`
        it reproduces :func:`drive_in` at ``T_celsius`` **bit-for-bit** (the engine's
        constant-callable-``D`` == scalar-``D`` guarantee).
        """
        return cls(T_peak=T_celsius, ramp_up_C_per_s=1.0, ramp_down_C_per_s=1.0,
                   hold_s=float(duration_s), T_base=T_celsius)

    @property
    def ramp_up_s(self) -> float:
        """Duration of the heating ramp (s)."""
        return (self.T_peak - self.T_base) / self.ramp_up_C_per_s

    @property
    def ramp_down_s(self) -> float:
        """Duration of the cooling ramp (s)."""
        return (self.T_peak - self.T_base) / self.ramp_down_C_per_s

    @property
    def duration(self) -> float:
        """Total anneal time ``ramp_up + hold + ramp_down`` (s) — the drive-in step length."""
        return self.ramp_up_s + self.hold_s + self.ramp_down_s

    def __call__(self, t: float) -> float:
        """Temperature (°C) at time ``t`` (s): ramp up → hold at peak → ramp down → ``T_base``."""
        t = float(t)
        up = self.ramp_up_s
        hold_end = up + self.hold_s
        if t <= 0.0:
            return self.T_base
        if t < up:
            return self.T_base + self.ramp_up_C_per_s * t
        if t <= hold_end:
            return self.T_peak
        if t < self.duration:
            return self.T_peak - self.ramp_down_C_per_s * (t - hold_end)
        return self.T_base


def thermal_budget(dopant: Dopant | str, program: ThermalProgram, *, n_steps: int = 600) -> float:
    """The integrated diffusion budget ``∫₀^duration D(T(t)) dt`` (cm²) of a transient anneal.

    The diffusion age the schedule deposits — the direct analogue of OED's
    :func:`coupling.effective_Dt` (an oxidation-driven ``∫D_eff dt``), here driven by the anneal's
    ``T(t)`` instead. A sealed-surface profile depends on the schedule **only through** this integral
    (the engine's ``τ = ∫D dt`` time-substitution guarantee), so it is *the* characterization of a
    spike anneal. Trapezoidal over the same ``n_steps`` sub-grid :func:`drive_in_program` marches, so
    the budget and the solve see one integral.
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    t_grid = np.linspace(0.0, program.duration, n_steps + 1)
    D = np.array([diffusivity(d, program(t)) for t in t_grid])
    return float(np.trapezoid(D, t_grid))


def equivalent_isothermal_time(dopant: Dopant | str, T_peak_celsius: float, budget: float) -> float:
    """The isothermal time at ``T_peak`` giving the same ``budget`` — ``t_eq = budget / D(T_peak)`` (s).

    The inverse of :func:`thermal_budget`: how long a *constant-``T_peak``* drive-in would take to
    deposit the spike's ``∫D dt``. For a spike this is **far less** than the total ramp duration —
    Arrhenius ``D`` collapses away from the peak, so only a narrow window near ``T_peak`` contributes
    (see :func:`spike_budget_time_laplace`). That is *why* RTA gives shallow junctions: the budget,
    not the clock time, sets the depth. (``D0``-independent: ``budget ∝ D0`` and ``D(T_peak) ∝ D0``.)
    """
    D_peak = diffusivity(dopant, T_peak_celsius)
    if D_peak <= 0.0:
        raise ValueError("D(T_peak) must be positive")
    return budget / D_peak


def spike_budget_time_laplace(dopant: Dopant | str, program: ThermalProgram) -> float:
    """Closed-form (Laplace-asymptotic) equivalent isothermal time of a spike — the *finding* leg.

    Expanding the Arrhenius exponent linearly about the peak, ``D(T(t)) ≈ D(T_peak)·exp(−s/s₀)`` on
    each ramp shoulder with thermal width ``s₀ = k·T_peak²/(Ea·β)`` (``β = |dT/dt|``, ``T_peak`` in
    **K**). Integrating each shoulder (ramps that span ``≫ s₀`` so the exponential tail is captured)
    and adding the hold gives

        ``t_eq ≈ hold + (k·T_peak²/Ea)·(1/β_up + 1/β_down)``        (s),

    a clean closed form **independent of ``D0``** (units ``eV·K²/eV / (K/s) = s``). It quantifies the
    collapse :func:`equivalent_isothermal_time` measures: e.g. ramping a 50 °C/s spike from 600 → 1050 °C
    (a ~9 s shoulder) contributes only ~1 s of peak-equivalent budget — the top ~50 °C is all that counts.
    The asymptotic match to the exact (trapezoid) :func:`thermal_budget` is the tight, cited leg.
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    T_peak_K = program.T_peak + ABS_ZERO
    s0 = K_BOLTZMANN_EV * T_peak_K ** 2 / d.Ea          # thermal width of the peak (K)
    shoulder = s0 / program.ramp_up_C_per_s + s0 / program.ramp_down_C_per_s
    return program.hold_s + shoulder


def drive_in_program(
    grid: Grid,
    N_initial: np.ndarray,
    dopant: Dopant | str,
    program: ThermalProgram,
    *,
    n_steps: int = 600,
    method: str = "backward_euler",
) -> DopantProfile:
    """Sealed-surface drive-in under a **transient** anneal ``T(t)`` → a :class:`DopantProfile`.

    The spike/RTA twin of :func:`drive_in`: redistributes a fixed dose with the surface sealed
    (:class:`~engines.diffusion.Neumann` ``(0)`` both ends, dose conserved to machine precision)
    while the diffusivity follows the schedule — ``D(t) = D(T(t))``, the engine's already-supported
    time-dependent-``D`` callable (no engine amendment; E1's heat-mode premise is falsified — see the
    §4 banner). The step runs for ``program.duration``. The reported ``D`` is the **time-averaged**
    diffusivity ``∫D dt / duration``, so ``D·t = effective_Dt`` (the budget) and
    :meth:`DopantProfile.gaussian_profile` stays self-consistent; for the
    :meth:`ThermalProgram.isothermal` seam ``D`` reduces to ``D(T)`` exactly, reproducing
    :func:`drive_in` bit-for-bit.
    """
    d = DOPANTS[dopant] if isinstance(dopant, str) else dopant
    t_seconds = program.duration

    def D_of_t(ts: float) -> float:
        return diffusivity(d, program(ts))

    N, dose, surf_flux = _diffuse(
        grid, D_of_t, np.asarray(N_initial, float), Neumann(0.0), Neumann(0.0),
        t_seconds, n_steps, method,
    )
    budget = thermal_budget(d, program, n_steps=n_steps)
    D_avg = budget / t_seconds if t_seconds > 0.0 else 0.0
    return DopantProfile(
        x=grid.centers, N=N, t=t_seconds, D=D_avg, stage="drive-in",
        N_surface=float(N[0]), dose=dose, surface_flux_dose=surf_flux,
        length=grid.length, method=method, effective_Dt=budget,
    )
