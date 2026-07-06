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
    implant: "Implant | None" = None,
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

    ``implant`` (§5, optional) swaps the **initial condition**: instead of the surface-peaked predep
    ``erfc``, the drive-in starts from a **buried Gaussian** :func:`implant_ic` at the projected range
    (the observable predep cannot make). When set, ``T_predep``/``t_predep_min``/``N_surface`` are
    **bypassed** (there is no predep — the implant *is* the source), and the returned first element is
    the athermal as-implanted IC (``stage="implant"``) rather than a predep. ``None`` (default) runs the
    predep path **bit-for-bit** — the entire existing suite is byte-identical (the seam, cf.
    ``drivein_program``/``Q_ox=0``/``boost=None``). The same sealed drive-in redistributes either IC.
    """
    grid = uniform_grid(length_um * CM_PER_UM, n_cells)
    if implant is None:
        source = predeposit(grid, dopant, T_predep, t_predep_min * 60.0,
                            N_surface=N_surface, n_steps=n_steps)
    else:
        source = implant_ic(grid, implant)
    predep = source
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


# --------------------------------------------------------------------------- #
# 5. Ion implantation — the buried initial condition (the peak predep cannot make)
# --------------------------------------------------------------------------- #
# The thermal predep of §2/§3 lays a **surface-peaked** ``erfc`` — its maximum is *at* the surface, and
# it is physically incapable of putting the dopant peak below it. Ion implantation embeds ions at a
# **controlled depth** ``R_p`` (the projected range), producing a **buried** Gaussian peak (zero-slope-
# then-rising concentration near the surface). That buried peak is the observable predep cannot produce
# at all — the discriminator that licenses this regime (a real V_t-adjust implant, a retrograde well),
# *not* a redundant second route to the same junction. Historically it is the step (production Si, early
# 1970s) that modernised the ~1968 planar predep line this simulator otherwise is.
#
# The model is LSS range theory reduced to its **first two moments** — projected range ``R_p(E)`` and
# straggle ``ΔR_p(E)`` — tabulated in Gibbons–Johnson–Mylroie *Projected Range Statistics* (the
# range-statistics-source memory note; the µm anchors are web-corroborated, flagged ~10%). The as-
# implanted profile is the **symmetric Gaussian** ``N(x) = (Q/√(2π)ΔR_p)·exp(−(x−R_p)²/2ΔR_p²)`` — the
# slice-1 default (``shape="gaussian"``); the **Pearson-IV skew is built in §5b (slice 2)** as the opt-in
# ``shape="pearson"``, while the channeling tail (slice 3) and damage→leakage (slice 4) remain named
# scope edges. **No new solver:**
# implant produces the *initial condition*, and the **identical** sealed-surface :func:`drive_in`
# redistributes and (slice-1 assumption) activates it — the implant slots in as an alternative IC where
# the predep ``erfc`` would go.

# Cited Gibbons–Johnson–Mylroie projected-range anchors (µm) — B & P into Si, web-corroborated across
# independent sources (gtuttle range/straggle table, TRIM/SRIM, textbook worked examples). The FLAGGED
# benchmark leg: a log-log power law ``R_p = C·E^m`` is least-squares fit to these, reproducing them to
# ~10% over 10→200 keV. The tight/sign content is monotone ``R_p(E)`` (energy→depth) and the species
# ordering — B (lighter) penetrates DEEPER than P at equal energy — not the absolute µm.
_RP_ANCHORS_UM: dict[str, tuple[tuple[float, float], ...]] = {
    "B": ((10.0, 0.0333), (30.0, 0.10), (80.0, 0.24), (100.0, 0.30)),
    "P": ((10.0, 0.0139), (100.0, 0.12), (200.0, 0.255)),
}
_DRP_ANCHORS_UM: dict[str, tuple[tuple[float, float], ...]] = {
    "B": ((10.0, 0.0171), (80.0, 0.063), (100.0, 0.067)),
    "P": ((10.0, 0.0069), (200.0, 0.0837)),
}


def _fit_power_law(anchors: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    """Least-squares ``y = C·E^m`` fit in log-space → ``(C, m)`` (``E`` keV, ``y`` µm)."""
    E = np.array([a[0] for a in anchors], dtype=float)
    y = np.array([a[1] for a in anchors], dtype=float)
    m, log_C = np.polyfit(np.log(E), np.log(y), 1)
    return float(math.exp(log_C)), float(m)


_RP_FIT: dict[str, tuple[float, float]] = {s: _fit_power_law(a) for s, a in _RP_ANCHORS_UM.items()}
_DRP_FIT: dict[str, tuple[float, float]] = {s: _fit_power_law(a) for s, a in _DRP_ANCHORS_UM.items()}


def range_statistics(species: str, energy_keV: float) -> tuple[float, float]:
    """LSS first two moments ``(R_p, ΔR_p)`` in **cm** for ``species`` at ``energy_keV`` (the Gibbons fit).

    ``R_p`` (projected range) and ``ΔR_p`` (straggle) from the flagged log-log power law over the cited
    Gibbons anchors (:data:`_RP_ANCHORS_UM` / :data:`_DRP_ANCHORS_UM`). Monotone in energy (deeper implant
    at higher energy — the game's teaching lever) and species-ordered (B deeper than P at equal energy).
    Returned in **cm** (the module's length unit; report as ``/CM_PER_UM`` for µm). Absolute values are
    coefficient-flagged (~10% vs the tables); the trends/signs are cited.
    """
    if energy_keV <= 0.0:
        raise ValueError(f"implant energy must be > 0 keV, got {energy_keV}")
    if species not in _RP_FIT:
        raise ValueError(f"no range-statistics data for {species!r} (have {sorted(_RP_FIT)})")
    C_rp, m_rp = _RP_FIT[species]
    C_dr, m_dr = _DRP_FIT[species]
    R_p_um = C_rp * energy_keV ** m_rp
    dRp_um = C_dr * energy_keV ** m_dr
    return R_p_um * CM_PER_UM, dRp_um * CM_PER_UM


@dataclass(frozen=True)
class Implant:
    """An ion-implant step: dose ``Q`` (cm⁻²) of ``species`` at ``energy_keV`` → a **buried Gaussian** IC.

    The alternative initial condition to a thermal predep: instead of a surface-peaked ``erfc``, ions
    embed at the projected range ``R_p(energy)`` with straggle ``ΔR_p`` (:func:`range_statistics`),
    giving a **buried** peak — the observable predep physically cannot make. ``species`` is a
    :data:`DOPANTS` key (B is the canonical V_t-adjust / retrograde implant; P a donor implant). The
    **same** sealed-surface :func:`drive_in` then redistributes and (slice-1 assumption: full)
    activates it — *no new solver*.

    ``shape`` (slice 2, opt-in) picks the profile family. ``"gaussian"`` (default) is the slice-1
    **symmetric two-moment** Gaussian — the seam: the whole existing suite is byte-identical.
    ``"pearson"`` is the **four-moment Pearson-IV** (skewness γ, kurtosis β via :func:`skew_kurtosis`) —
    the real, *skewed* as-implanted profile (boron backscatters to a surface tail, its peak deeper than
    R_p). Pearson skew is tabulated for boron only (the cited light-ion case); ``"pearson"`` for a
    species without skew data raises here.

    ``channel`` (slice 3, opt-in) adds a :class:`Channeling` **deep exponential tail** — the fraction of
    the dose that channels along the low-index axes and penetrates *far* past ``R_p`` (§5c). It applies to
    **either** shape (it partitions whichever primary), and its ``tilt`` suppresses it (the 7° convention).
    ``None`` (default) is the seam: the profile is the exact slice-1/2 primary, bit-for-bit. Damage→leakage
    remains a named scope edge (slice 4), deliberately absent rather than half-built.
    """

    dose: float          # cm⁻² — implanted areal dose Q (∫N dx of the as-implanted profile)
    energy_keV: float    # keV — sets R_p, ΔR_p via LSS range statistics (deeper at higher energy)
    species: str = "B"   # dopant (a DOPANTS key); B = the canonical V_t-adjust implant
    shape: str = "gaussian"   # "gaussian" (slice-1 seam) | "pearson" (slice-2 Pearson-IV skew)
    channel: "Channeling | None" = None   # slice-3 deep channeling tail (None = seam: no tail)

    def __post_init__(self) -> None:
        if self.dose <= 0.0:
            raise ValueError(f"implant dose must be > 0 cm⁻², got {self.dose}")
        if self.energy_keV <= 0.0:
            raise ValueError(f"implant energy must be > 0 keV, got {self.energy_keV}")
        if self.species not in DOPANTS:
            raise ValueError(f"unknown implant species {self.species!r} (have {sorted(DOPANTS)})")
        if self.shape not in ("gaussian", "pearson"):
            raise ValueError(f"implant shape must be 'gaussian' or 'pearson', got {self.shape!r}")
        if self.shape == "pearson" and self.species not in _SKEW_KURTOSIS:
            raise ValueError(f"no Pearson-IV skew data for {self.species!r} "
                             f"(have {sorted(_SKEW_KURTOSIS)}); use shape='gaussian'")
        if self.channel is not None and not isinstance(self.channel, Channeling):
            raise ValueError(f"channel must be a Channeling or None, got {type(self.channel).__name__}")

    def range_statistics(self) -> tuple[float, float]:
        """This implant's ``(R_p, ΔR_p)`` in **cm** (:func:`range_statistics` at its species/energy)."""
        return range_statistics(self.species, self.energy_keV)

    def moments(self) -> tuple[float, float, float, float]:
        """This implant's four Pearson moments ``(R_p, ΔR_p, γ, β)`` (:func:`range_moments`; needs skew data)."""
        return range_moments(self.species, self.energy_keV)


def implant_profile(x: np.ndarray, implant: Implant) -> np.ndarray:
    """As-implanted **buried** IC ``N(x)`` (cm⁻³) — a Gaussian (``shape="gaussian"``) or Pearson-IV (``"pearson"``).

    ``shape="gaussian"`` (slice-1 default, the seam) is the symmetric two-moment (LSS) profile
    ``N(x) = (Q/√(2π)ΔR_p)·exp(−(x−R_p)²/2ΔR_p²)``: peak ``Q/(√(2π)·ΔR_p)`` **at the projected range**
    ``R_p``, 1σ half-width ``ΔR_p`` (:func:`range_statistics`). ``shape="pearson"`` (slice 2) is the
    four-moment **skewed** :func:`pearson4_profile` (adds skewness γ, kurtosis β via
    :func:`skew_kurtosis`) — boron's peak then sits *deeper* than R_p with a surface tail.

    ``x`` (cm) from the surface. **Not** renormalized on the grid — this is the *analytic* form, so
    ``∫₀^∞ N dx = Q`` only to truncation: for the Gaussian just the **surface** ``x<0`` tail (negligible
    when ``R_p ≳ 4·ΔR_p``, flagged shallow), for Pearson-IV **both** tails (the power law is heavier —
    the two-sided flagged leg). The **buried-peak topology** (maximum at ``x > 0``, ``dN/dx > 0``
    shallower) is the sign-robust discriminator vs the surface-peaked predep ``erfc`` (max at ``x = 0``).

    ``implant.channel`` (slice 3, §5c) partitions the primary: ``N = (1−f)·primary + f·dose·tail`` with
    ``f`` the tilt-suppressed channeled fraction (:func:`channeled_fraction`) and ``tail`` the unit-area
    deep exponential (:func:`channeling_tail`). The split **conserves ∫N dx = Q analytically** (the
    channeled ions come *out* of the primary, not on top); a longer, flatter deep tail is what pushes the
    annealed junction ``x_j`` **deeper** — the punchthrough failure mode. ``None`` ⇒ the exact primary.
    This is the field :func:`drive_in` consumes in place of the predep.
    """
    x = np.asarray(x, dtype=float)
    R_p, dRp = range_statistics(implant.species, implant.energy_keV)
    if implant.shape == "gaussian":
        primary = (implant.dose / (math.sqrt(2.0 * math.pi) * dRp)) * np.exp(-((x - R_p) ** 2) / (2.0 * dRp ** 2))
    else:
        gamma, beta = skew_kurtosis(implant.species, implant.energy_keV)
        primary = pearson4_profile(x, implant.dose, R_p, dRp, gamma, beta)
    if implant.channel is None:
        return primary                              # seam: no channeling → the exact slice-1/2 primary
    f = channeled_fraction(implant.channel.fraction, implant.channel.tilt_deg)
    tail = implant.dose * channeling_tail(x, R_p, implant.channel.length_cm)
    return (1.0 - f) * primary + f * tail


def implant_ic(grid: Grid, implant: Implant) -> DopantProfile:
    """Place an :class:`Implant` on ``grid`` → the athermal as-implanted :class:`DopantProfile` (stage ``"implant"``).

    The buried IC (:func:`implant_profile` — Gaussian or Pearson-IV per ``implant.shape``) as a profile
    object, its ``dose`` the **grid integral** ``Σ N·Δx`` (the engine's
    :meth:`~engines.diffusion.Diffusion1D.total` convention, so it is directly comparable to the
    drive-in's conserved dose). ``t``/``D`` are ``0`` — the implant is athermal (the placement, before any
    anneal); the subsequent :func:`drive_in` supplies the thermal step. This is the profile that slots
    into :func:`two_step` where the predep ``erfc`` would be.
    """
    N = implant_profile(grid.centers, implant)
    dose = float(np.sum(N * grid.widths))
    return DopantProfile(
        x=grid.centers, N=N, t=0.0, D=0.0, stage="implant",
        N_surface=float(N[0]), dose=dose, surface_flux_dose=0.0,
        length=grid.length, method="implant",
    )


# --------------------------------------------------------------------------- #
# 5b. Pearson-IV skew — the tightened (asymmetric) as-implanted profile (slice 2)
# --------------------------------------------------------------------------- #
# The slice-1 profile is the SYMMETRIC two-moment Gaussian (peak exactly at R_p, mirror-image tails).
# Real as-implanted profiles are SKEWED: a light ion like boron **backscatters toward the surface**
# (Plummer, Deal & Griffin, *Silicon VLSI Technology* §8: "light ions backscatter to skew the profile
# up; heavy ions scatter deeper"), so boron carries a **longer tail toward the surface** and its **peak
# sits DEEPER than R_p** — a NEGATIVE skewness γ (sign convention: a *positive* γ puts the peak *closer*
# to the surface than R_p, so boron's surface-tail is the negative branch), growing more negative with
# energy. The four-moment (R_p, ΔR_p, skewness γ, kurtosis β) **Pearson-IV** distribution is the
# workhorse branch for this asymmetry in implanted dopants (the Pearson-IV-for-implant-profiles
# literature, e.g. *Radiation Effects* 46 (1980) 3-4).
#
# Pearson-IV is the CLOSED-FORM solution of the Pearson ODE  d(ln p)/ds = (s − a)/(b0 + b1 s + b2 s²)
# (s = x − R_p, a = b1), whose coefficients are fixed by the four moments (σ ≡ ΔR_p):
#     D  = 10β − 12γ² − 18
#     b0 = −σ²(4β − 3γ²)/D,    b1 = a = −γσ(β + 3)/D,    b2 = −(2β − 3γ² − 6)/D
# integrating to  p(s) = |b0 + b1 s + b2 s²|^(1/2b2) · exp[(2c/W)·arctan((2 b2 s + b1)/W)]  with
# c = −b1(2 b2 + 1)/(2 b2) and W = √(4 b0 b2 − b1²). The construction reproduces the first two moments
# **exactly** (mean = R_p, variance = σ² — the tight test legs), and γ, β by design; the **mode** sits at
# s = b1 (deeper than R_p for boron's γ < 0). The **type-IV** branch requires complex denominator roots
# (b2 < 0 AND 4 b0 b2 − b1² > 0); :func:`pearson4_profile` raises outside it rather than take a
# negative-base power. That is the honest cost of the clean branch: real boron kurtosis sits near the
# Gaussian β ≈ 3, but staying in type IV pins β into the ≳ 4 band, so β (and the γ magnitude) are
# **house-calibrated, FLAGGED** — the SIGN and energy TREND are cited, the numbers are not table anchors
# like R_p. Two truncation edges now (vs the Gaussian's one): the power-law |s|^(1/b2) tail loses dose at
# BOTH ends, so the analytic ``∫N dx = Q`` is a flagged, two-sided leg — the TIGHT dose leg is structural
# and shape-independent (the sealed no-flux :func:`drive_in` conserves whatever grid-dose it is handed).

# Boron skew/kurtosis — house-calibrated, FLAGGED magnitudes (NOT tabulated anchors like R_p/ΔR_p). The
# CITED content is the SIGN and TREND: boron γ < 0 at device energies, more negative with energy (Plummer
# §8; the profile "skewed up" toward the surface). β is a constant pinned into the type-IV band. Only
# boron is tabulated — the well-documented light-ion case the plan/demo name; other species raise rather
# than carry a fabricated skew. γ_B(E) = γ0 + γ1·log10(E/E0) (small negative near 10 keV → ≈ −0.44 by
# 200 keV, staying safely inside type IV for β = 4.5).
_SKEW_KURTOSIS: dict[str, dict[str, float]] = {
    "B": {"gamma0": -0.05, "gamma1": -0.30, "E0_keV": 10.0, "beta": 4.5},
}


def skew_kurtosis(species: str, energy_keV: float) -> tuple[float, float]:
    """Flagged Pearson-IV 3rd/4th moments ``(γ, β)`` for ``species`` at ``energy_keV`` (skewness, kurtosis).

    Boron only (the cited light-ion case): γ < 0 (surface tail, peak *deeper* than R_p), growing more
    negative with energy; β pinned into the type-IV band (≳ 4). **House-calibrated magnitudes** — the
    SIGN and energy TREND are cited (Plummer §8, "light ions backscatter to skew the profile up"); the
    numbers are not table anchors (unlike :func:`range_statistics`). Raises for a species without skew
    data rather than fabricating one, and for a non-positive energy.
    """
    if energy_keV <= 0.0:
        raise ValueError(f"implant energy must be > 0 keV, got {energy_keV}")
    if species not in _SKEW_KURTOSIS:
        raise ValueError(f"no Pearson-IV skew data for {species!r} (have {sorted(_SKEW_KURTOSIS)})")
    p = _SKEW_KURTOSIS[species]
    gamma = p["gamma0"] + p["gamma1"] * math.log10(energy_keV / p["E0_keV"])
    return gamma, p["beta"]


def range_moments(species: str, energy_keV: float) -> tuple[float, float, float, float]:
    """The four moments ``(R_p, ΔR_p, γ, β)`` — :func:`range_statistics` (2, cited) + :func:`skew_kurtosis` (2, flagged)."""
    R_p, dRp = range_statistics(species, energy_keV)
    gamma, beta = skew_kurtosis(species, energy_keV)
    return R_p, dRp, gamma, beta


# Grid-independent auxiliary axis (in units of σ) for the full-line normalization ∫p ds = Q. The
# power-law tail |s|^(1/b2) (1/b2 ≈ −9 for the boron band) decays fast, so ±60σ over-covers both tails.
_PEARSON_NORM_HALF_WIDTH_SIGMA = 60.0
_PEARSON_NORM_POINTS = 240001


def _pearson4_coeffs(sigma: float, gamma: float, beta: float) -> tuple[float, float, float]:
    """The Pearson coefficients ``(b0, b1, b2)`` from the moments (σ, γ, β) — ``b1`` is the mode offset ``a``."""
    D = 10.0 * beta - 12.0 * gamma ** 2 - 18.0
    if D == 0.0:
        raise ValueError(f"degenerate Pearson denominator (10β−12γ²−18 = 0) at γ={gamma}, β={beta}")
    b0 = -sigma ** 2 * (4.0 * beta - 3.0 * gamma ** 2) / D
    b1 = -gamma * sigma * (beta + 3.0) / D
    b2 = -(2.0 * beta - 3.0 * gamma ** 2 - 6.0) / D
    return b0, b1, b2


def _pearson4_logshape(s: np.ndarray, b0: float, b1: float, b2: float, W: float, c: float) -> np.ndarray:
    """Un-normalized log-density ``ln p(s)`` of the Pearson-IV shape (``s`` centred at R_p)."""
    denom = b0 + b1 * s + b2 * s ** 2                 # < 0 everywhere for type IV (complex roots)
    return (1.0 / (2.0 * b2)) * np.log(np.abs(denom)) + (2.0 * c / W) * np.arctan((2.0 * b2 * s + b1) / W)


def pearson4_profile(x: np.ndarray, dose: float, R_p: float, sigma: float,
                     gamma: float, beta: float) -> np.ndarray:
    """As-implanted **Pearson-IV** (four-moment, skewed) IC ``N(x)`` (cm⁻³), normalized to ``dose`` over the full line.

    The skewed generalisation of the Gaussian branch of :func:`implant_profile`: the profile's mean is
    ``R_p`` and variance ``σ² = ΔR_p²`` **exactly** (by construction — the tight legs), with skewness γ
    and kurtosis β by design, and its **mode** at ``x = R_p + b1`` (deeper than R_p when γ < 0, boron).
    Requires the **type-IV** region — ``b2 < 0`` and ``4 b0 b2 − b1² > 0`` (complex denominator roots) —
    and **raises** otherwise (no negative-base power taken silently). Normalized so
    ``∫_{−∞}^{∞} N dx = dose`` on a grid-independent σ-scaled axis; evaluated on ``x`` (cm, from the
    surface) it loses dose to BOTH surface and deep-tail truncation (the two-sided flagged leg — the
    power-law tail is heavier than the Gaussian's).
    """
    b0, b1, b2 = _pearson4_coeffs(sigma, gamma, beta)
    disc = 4.0 * b0 * b2 - b1 ** 2
    if not (b2 < 0.0 and disc > 0.0):
        raise ValueError(f"(γ={gamma:.4g}, β={beta:.4g}) is outside the Pearson-IV region "
                         f"(need b2 < 0 and 4·b0·b2 − b1² > 0; got b2={b2:.4g}, disc={disc:.4g})")
    W = math.sqrt(disc)
    c = -b1 * (2.0 * b2 + 1.0) / (2.0 * b2)
    # full-line normalization ∫shape ds on the auxiliary axis (max-subtracted for numerical stability)
    s_norm = np.linspace(-_PEARSON_NORM_HALF_WIDTH_SIGMA * sigma,
                         _PEARSON_NORM_HALF_WIDTH_SIGMA * sigma, _PEARSON_NORM_POINTS)
    ln_norm = _pearson4_logshape(s_norm, b0, b1, b2, W, c)
    ln_max = float(ln_norm.max())
    Z = float(np.trapezoid(np.exp(ln_norm - ln_max), s_norm))    # ∫shape ds = Z · e^{ln_max}
    x = np.asarray(x, dtype=float)
    ln_x = _pearson4_logshape(x - R_p, b0, b1, b2, W, c)
    return (dose / Z) * np.exp(ln_x - ln_max)


# --------------------------------------------------------------------------- #
# 5c. Channeling tail — the deep exponential a monocrystalline lattice adds (slice 3)
# --------------------------------------------------------------------------- #
# Slices 1–2 give the primary as-implanted peak (Gaussian, then Pearson-IV skew) — the ions that stop by
# random nuclear+electronic collisions. In a **single-crystal** target a fraction of the beam instead
# steers **down the open low-index channels** (⟨110⟩, ⟨100⟩), where the atomic rows shadow the nuclei so
# stopping collapses — those ions penetrate **far past R_p** and pile a **deep exponential tail** onto the
# profile (Plummer, Deal & Griffin §8; Campbell §5). It is not a knob for hitting a target — it is a
# **failure mode**: the tail drags the annealed junction ``x_j`` DEEPER than the recipe intends → source-
# drain **punchthrough**. The production countermeasures are all "break the channel": tilt the wafer off
# the axis (the **7° convention**), a **screen oxide** to randomize entry, or **pre-amorphization** to
# destroy the lattice before the dose. We carry the **tilt** lever (the dominant, always-present one);
# screen-oxide / pre-amorphization are the same suppression named as scope edges.
#
# The model is a **two-population partition** (the standard channeling split), NOT an add-on: a fraction
# ``f`` of the dose channels into a unit-area deep exponential ``tail(x) = (1/λ)·e^(−(x−R_p)/λ)`` (x ≥ R_p),
# the remaining ``1−f`` stays in the primary — so ``N = (1−f)·primary + f·Q·tail`` conserves ``∫N dx = Q``
# **analytically** (the channeled ions come *out* of the peak, not on top; adding-on-top would violate
# dose). ``f`` is the tilt-suppressed ``f = f0·e^(−tilt/τ)``: on-axis (0°) channels maximally at the
# flagged amplitude ``f0``; the 7° convention knocks it down by ``τ`` (:data:`_CHANNEL_TILT_SUPPRESSION_DEG`).
#
# Triad. **Tight (sign-robust):** (a) the SEAM — ``channel=None`` returns the exact slice-1/2 primary,
# bit-for-bit; (b) dose — the partition ``∫N dx = Q`` analytically, and the sealed no-flux drive-in
# conserves whatever grid-dose it is handed to machine precision (structural, shape-independent);
# (c) the **deeper-junction** discriminator — a long tail (λ ≫ ΔR_p) dominates the super-exponential
# Gaussian *in the deep-tail region where the junction lives*, so the annealed ``x_j`` moves DEEPER than
# the no-channel case (constant-D drive-in linearity carries the as-implanted ordering through the anneal);
# (d) **tilt monotonicity** — more tilt ⇒ smaller ``f`` ⇒ shallower ``x_j`` (the cited suppression sign).
# **Flagged (house-calibrated magnitude):** the on-axis fraction ``f0``, the tail length ``λ``, and the
# suppression rate ``τ`` — the SIGN (channeling deepens; tilt suppresses) is cited, the numbers are not
# table anchors. **Single tail suffices** — the deferred *dual-Pearson* (channel + primary as two full
# Pearson populations) is a named scope edge, NOT this: one exponential deep tail is the honest first cut.
# The single-exponential deep tail is anchored at R_p (a Heaviside deep side) — a phenomenological form,
# not a fitted channeling-fraction-vs-orientation table.

# The tilt (degrees) over which channeling suppresses by 1/e — house-calibrated so the 7° convention
# knocks the on-axis fraction down to ~1/5 (e^(−7/4.5) ≈ 0.21). FLAGGED: the SIGN (tilt suppresses) is
# cited; the rate is a calibrated constant, not a measured one.
_CHANNEL_TILT_SUPPRESSION_DEG = 4.5


@dataclass(frozen=True)
class Channeling:
    """A channeling deep tail on an :class:`Implant`: a fraction of the dose penetrates far past ``R_p``.

    The **failure-mode** slice-3 add-on (§5c): in a single-crystal target a fraction ``fraction`` (=``f0``,
    the **on-axis / 0°** channeled fraction) steers down the open lattice channels and stops in a **deep
    exponential tail** of decay length ``length_um`` (``λ ≫ ΔR_p``, the flagged tail depth). ``tilt_deg``
    is the wafer tilt off the axis — the **7° convention** (default) suppresses channeling by
    ``e^(−tilt/τ)`` (:func:`channeled_fraction`). Applied via :func:`implant_profile` as the two-population
    partition ``N = (1−f)·primary + f·Q·tail`` (dose-conserving). The flagged magnitudes are ``f0``, ``λ``
    and ``τ``; the cited content is the SIGN — channeling deepens the junction, tilt suppresses it.
    """

    fraction: float          # f0 — the ON-AXIS (0° tilt) channeled dose fraction, 0 < f0 < 1
    length_um: float         # λ — deep-tail 1/e decay length in µm (≫ ΔR_p; the flagged tail depth)
    tilt_deg: float = 7.0    # wafer tilt off-axis (deg); the 7° convention suppresses channeling

    def __post_init__(self) -> None:
        if not (0.0 < self.fraction < 1.0):
            raise ValueError(f"channeled fraction f0 must be in (0, 1), got {self.fraction}")
        if self.length_um <= 0.0:
            raise ValueError(f"channeling tail length must be > 0 µm, got {self.length_um}")
        if self.tilt_deg < 0.0:
            raise ValueError(f"tilt must be ≥ 0°, got {self.tilt_deg}")

    @property
    def length_cm(self) -> float:
        """The tail decay length ``λ`` in **cm** (the module's length unit)."""
        return self.length_um * CM_PER_UM


def channeled_fraction(fraction: float, tilt_deg: float) -> float:
    """Effective channeled dose fraction ``f = f0·e^(−tilt/τ)`` (tilt suppresses channeling).

    ``fraction`` is the on-axis (0°) fraction ``f0``; ``tilt_deg`` the wafer tilt off the low-index axis.
    At ``tilt=0`` the full ``f0`` channels; the 7° convention knocks it down by
    :data:`_CHANNEL_TILT_SUPPRESSION_DEG` (``τ``). Monotone **decreasing** in tilt (the cited suppression
    sign) and always ``< f0 < 1`` (a valid partition weight). Magnitudes flagged; the sign is cited.
    """
    if not (0.0 < fraction < 1.0):
        raise ValueError(f"channeled fraction f0 must be in (0, 1), got {fraction}")
    if tilt_deg < 0.0:
        raise ValueError(f"tilt must be ≥ 0°, got {tilt_deg}")
    return fraction * math.exp(-tilt_deg / _CHANNEL_TILT_SUPPRESSION_DEG)


def channeling_tail(x: np.ndarray, R_p: float, length_cm: float) -> np.ndarray:
    """Unit-area deep-side channeling tail ``(1/λ)·e^(−(x−R_p)/λ)`` for ``x ≥ R_p``, else ``0`` (``x``, ``λ`` in cm).

    The deep exponential the channeled population piles past the projected range — anchored at ``R_p`` (a
    Heaviside deep side; the surface side is the primary's business). Normalized so
    ``∫_{R_p}^{∞} tail dx = 1``, i.e. scaling it by the dose ``Q`` puts exactly ``Q`` under the tail — the
    partition in :func:`implant_profile` then weights the two populations by ``f`` and ``1−f`` and
    conserves ``∫N dx = Q``. A longer ``λ`` (flatter tail) is what drags the annealed junction deeper.
    """
    x = np.asarray(x, dtype=float)
    return np.where(x >= R_p, np.exp(-(x - R_p) / length_cm) / length_cm, 0.0)
