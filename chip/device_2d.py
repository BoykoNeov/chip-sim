"""The 2-D MOSFET cross-section: lateral S/D diffusion → the effective channel length (Chip v1.11).

The composition that finally wires the engine's **2-D regime** (v1.8, :mod:`diffusion_2d`) into the
**process→device** payoff (Phase 4, :mod:`device`). Every prior device read used a *drawn* channel
length straight from the litho CD. But a real self-aligned MOSFET forms its source/drain by diffusing
dopant with **the gate itself as the mask**: the n⁺ S/D enters through the windows on either side and
spreads not just *down* but **sideways under the gate edges**. That lateral encroachment ``ΔL`` shrinks
the channel from its drawn length to an **effective** length::

    L_eff = L_drawn − 2·ΔL                        (the textbook subtraction)

``L_eff`` is the honest place 2-D geometry moves a device number: it sets the drive current
(``I_Dsat ∝ W/L``) — a shorter channel drives more current — while the **threshold voltage stays
long-channel**. Short-channel ``V_t`` rolloff / DIBL is an inherently 2-D *electrostatic* effect (the
plan §5 / Phase-4 tar pit) and is **not** modelled here: this module moves the channel *length* and the
*current*, never the *threshold*. (A regression guard below asserts exactly that — that ``L`` never
leaks into ``V_t``.)

Two ways to get ``L_eff`` — the cheap approximation and the honest solve
-----------------------------------------------------------------------
* **The textbook approximation** ``L_eff = L_drawn − 2·ΔL`` takes ``ΔL`` from a single **isolated**
  (semi-infinite) gate edge — reusing the v1.8 :func:`diffusion_2d.lateral_diffusion` mask-edge solve
  and reading the *surface* lateral reach. This is the cited ``L_eff = L_drawn − 2·L_{D,lateral}``
  relation (Sze / Plummer / Taur–Ning).
* **The honest direct solve** runs a **two-window half-cell**: the gate centre at ``x=0`` is a no-flux
  symmetry plane and the S/D window is *open outside the gate* (``x ≥ L_drawn/2``, sealed under the
  gate near the centre) — which is *exactly* the right half of the symmetric two-S/D device. The
  metallurgical channel is then read **directly**, junction-to-junction: ``L_eff_true = 2·x_j``, where
  ``x_j`` is the surface ``N = N_channel`` crossing closest to the gate centre. It never uses the
  subtraction.

This is a **validation deepening**, not a new-physics one: the independent two-window solve
**confirms** the textbook subtraction. They agree across the whole open range — to ~grid precision
(a few nm, ~1 %), *persisting as the gate narrows toward the knee*, not merely at a wide gate — and
they agree on the **punchthrough limit** at ``L_drawn ≈ 2·ΔL`` (where the subtraction, ``max``-clamped,
also hits zero). The direct solve's worth over "subtraction + clamp" is (1) **physical grounding** — a
real ``N = N_channel`` concentration crossing yields a hard ``L_eff = 0`` floor at front-merge, where
the subtraction only clamps an unphysical negative — and (2) **independence** — a *different BC
topology* (two windows + a symmetry plane vs one semi-infinite edge), so the agreement is a genuine
cross-check that would fail on a config/topology bug or if superposition broke. The front-interaction effect that
*would* split the two near the knee (the fronts piling up under the no-flux gate) is **below the
resolved scale** here — checked, no resolvable divergence — so it is named as the honest ceiling, not
asserted. At ``L_eff_true ≤ 0`` (punchthrough) the module **refuses** rather than returning a
long-channel device that does not exist.

Units — semiconductor CGS, as the rest of chip
----------------------------------------------
Lengths in **cm** internally (``D`` native Fair cm²/s, ``N_s`` native Trumbore cm⁻³), **µm** at the API
boundary (channel lengths, depths). The S/D Arrhenius ``D(T)`` / solubility come from
:mod:`diffusion_dopant`; the device read is :mod:`device` verbatim — this module adds only the geometry
composition, no new physical constant beyond the cited ``L_eff = L_drawn − 2·L_{D,lateral}`` relation.

Validation boundary
-------------------
The 2-D solver machinery is the engine's (``engines/diffusion/tests/test_diffusion2d.py``); the
single-edge ΔL inherits v1.8's tight erfc-window-column anchor. This module's tests validate the
**composition**: the exact ``lateral=False`` seam back to Phase 4 (bit-for-bit), the two-window ≡
subtraction agreement at a wide gate (the independent anchor), the ``V_t``-invariance / geometric-current
regression guards (boundary, by-construction), and the cited lateral-ratio shortening + its breakdown
near punchthrough (loose benchmark).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engines.diffusion import Diffusion2D, uniform_grid_2d, Neumann, MaskedSurface
from . import diffusion_2d
from . import device
from .diffusion_dopant import DOPANTS, Dopant, diffusivity, CM_PER_UM


# --------------------------------------------------------------------------- #
# Surface junction readers — the channel inverts at the surface (y=0 → row j=0)
# --------------------------------------------------------------------------- #
def _first_crossing_x(x: np.ndarray, values: np.ndarray, level: float) -> float:
    """Smallest ``x`` where an *increasing* ``values(x)`` reaches ``level`` (linear-interp).

    For the two-window half-cell the surface dopant rises with ``x`` from the gate centre (low,
    still p-channel) toward the open S/D window (high, n⁺); the metallurgical junction is the first
    ``x`` at which it reaches the channel doping. Returns **0.0** if the gate centre is itself already
    inverted (the junction is at/inside the centre → the channel has closed → punchthrough), or
    ``x[-1]`` if it never reaches ``level``.
    """
    above = values >= level
    if above[0]:
        return 0.0                               # gate centre already n⁺ → channel closed (punchthrough)
    if not above.any():
        return float(x[-1])                      # never reaches level within the domain
    i = int(np.where(above)[0][0])               # first index at/above level
    f = (level - values[i - 1]) / (values[i] - values[i - 1])
    return float(x[i - 1] + f * (x[i] - x[i - 1]))


def _last_crossing_x(x: np.ndarray, values: np.ndarray, level: float) -> float:
    """Largest ``x`` where a *decreasing* ``values(x)`` is still ≥ ``level`` (linear-interp).

    For the isolated single-edge run the surface dopant falls with ``x`` from the open window (high)
    under the mask (low); the lateral junction reach is the furthest ``x`` still above the channel
    doping. Returns ``x[0]`` if it is never above ``level``.
    """
    above = values >= level
    if not above.any():
        return float(x[0])
    i = int(np.where(above)[0][-1])
    if i == values.size - 1:
        return float(x[i])                       # contour runs off the domain edge
    f = (values[i] - level) / (values[i] - values[i + 1])
    return float(x[i] + f * (x[i + 1] - x[i]))


# --------------------------------------------------------------------------- #
# The two underlying 2-D solves
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class _EdgeResult:
    delta_L_cm: float        # surface lateral encroachment ΔL (isolated edge)
    sd_xj_cm: float          # vertical S/D junction depth (window column)


def _isolated_edge(
    d: Dopant, Ns: float, T_celsius: float, t_min: float, channel_N_A: float,
    *, length_x_um: float, depth_um: float, x_edge_um: float, nx: int, ny: int, n_steps: int,
) -> _EdgeResult:
    """The single *isolated* gate edge (semi-infinite mask) → the textbook ΔL.

    Reuses the v1.8 :func:`diffusion_2d.lateral_diffusion` (window = S/D open for ``x < x_edge``,
    mask = under the gate for ``x ≥ x_edge``); reads the **surface** lateral reach (the device channel
    inverts at the surface) and the vertical S/D junction depth (the validated window column).
    """
    profile = diffusion_2d.lateral_diffusion(
        d, T_celsius=T_celsius, t_min=t_min, N_surface=Ns,
        length_x_um=length_x_um, length_y_um=depth_um, x_edge_um=x_edge_um,
        nx=nx, ny=ny, n_steps=n_steps,
    )
    geom = diffusion_2d.junction_geometry(profile, channel_N_A)         # validated vertical depth
    surface_reach = _last_crossing_x(profile.x, profile.N[:, 0], channel_N_A)
    delta_L_cm = max(surface_reach - profile.x_edge, 0.0)
    return _EdgeResult(delta_L_cm=delta_L_cm, sd_xj_cm=geom.vertical_um * CM_PER_UM)


def _two_window_solve(
    D: float, Ns: float, t_s: float, L_drawn_cm: float, channel_N_A: float,
    *, sd_extent_cm: float, depth_cm: float, nx: int, ny: int, n_steps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Half of the symmetric two-S/D device → the 2-D field ``N(x, y)`` and ``L_eff_true`` (cm).

    Gate centre at ``x=0`` (a no-flux symmetry plane = the mirror plane between the two S/D); the S/D
    window is **open for ``x ≥ L_drawn/2``** (held at ``Ns``) and **sealed under the gate** for
    ``x < L_drawn/2``. The far face ``x=Lx`` (deep in the S/D contact) and ``y=Ly`` (deep bulk) are
    no-flux. The metallurgical channel is read **directly** at the surface (row ``N[:, 0]``):
    ``L_eff_true = 2·x_j``, where ``x_j`` is the ``N = channel_N_A`` crossing closest to the gate
    centre (``0`` ⇒ the fronts have merged → punchthrough). Returns ``(x_cm, y_cm, N, L_eff_true_cm)``.
    """
    gate_half = 0.5 * L_drawn_cm
    Lx = gate_half + sd_extent_cm
    grid = uniform_grid_2d(Lx, depth_cm, nx, ny)
    window = grid.x.centers >= gate_half                  # open in the S/D, sealed under the gate
    solver = Diffusion2D(
        grid, D,
        bc_xlo=Neumann(0.0),                              # gate-centre symmetry plane
        bc_xhi=Neumann(0.0),                              # deep in the S/D contact (far)
        bc_ylo=MaskedSurface(Ns, window),                 # surface: S/D Dirichlet | gate no-flux
        bc_yhi=Neumann(0.0),                              # deep bulk
    )
    N = solver.solve(np.zeros(grid.shape), t_s, t_s / n_steps)
    x_j_cm = _first_crossing_x(grid.x.centers, N[:, 0], channel_N_A)
    return grid.x.centers, grid.y.centers, N, 2.0 * x_j_cm


def effective_channel_um(
    *,
    channel_N_A: float,
    L_drawn_um: float,
    sd_dopant: Dopant | str = "P",
    sd_T_celsius: float = 1000.0,
    sd_t_min: float = 6.0,
    sd_N_surface: float | None = None,
    depth_um: float = 0.7,
    sd_extent_um: float = 0.4,
    nx: int = 180,
    ny: int = 140,
    n_steps: int = 150,
) -> float:
    """The honest effective channel length ``L_eff_true`` (µm) from the two-window solve alone.

    The cheap path for sweeping ``L_drawn`` (the figure / the scope-edge probe): runs only the
    two-window half-cell (no isolated-edge solve) and reads the junction-to-junction channel
    directly. Returns ``0.0`` at **punchthrough** (the S/D fronts have merged under the gate).
    """
    d = DOPANTS[sd_dopant] if isinstance(sd_dopant, str) else sd_dopant
    Ns = d.N_solid_solubility if sd_N_surface is None else float(sd_N_surface)
    _, _, _, L_eff_cm = _two_window_solve(
        diffusivity(d, sd_T_celsius), Ns, sd_t_min * 60.0, L_drawn_um * CM_PER_UM, channel_N_A,
        sd_extent_cm=sd_extent_um * CM_PER_UM, depth_cm=depth_um * CM_PER_UM,
        nx=nx, ny=ny, n_steps=n_steps,
    )
    return L_eff_cm / CM_PER_UM


# --------------------------------------------------------------------------- #
# The bundled 2-D MOSFET cross-section
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MOSFET2D:
    """A MOSFET read off a 2-D S/D cross-section: the effective channel length and what it buys.

    Geometry (all **µm**): ``L_drawn`` the litho gate length, ``delta_L`` the single-edge surface
    encroachment, ``L_eff_approx = L_drawn − 2·ΔL`` (textbook) and ``L_eff_true = 2·x_j`` (the honest
    two-window solve), ``sd_xj`` the vertical S/D depth. ``x``/``y``/``N`` are the two-window field
    (``None`` when ``lateral=False``). ``mos`` is the device built at ``L_eff_true``, ``mos_drawn`` at
    the drawn length (so ``i_dsat`` vs ``i_dsat_drawn`` is what the shortening buys). Plain
    arrays/scalars — the loose-coupling currency (ADR 0002).
    """

    L_drawn_um: float
    delta_L_um: float
    L_eff_approx_um: float
    L_eff_true_um: float
    sd_xj_um: float
    channel_N_A: float
    sd_N_surface: float
    sd_dopant: str
    sd_T_celsius: float
    sd_t_min: float
    t_ox_um: float
    gate: str
    width_um: float
    overdrive_V: float
    mos: device.MOSDevice
    mos_drawn: device.MOSDevice
    i_dsat: float
    i_dsat_drawn: float
    x_um: np.ndarray | None = None
    y_um: np.ndarray | None = None
    N: np.ndarray | None = None

    @property
    def shortening_frac(self) -> float:
        """Fractional channel shortening ``(L_drawn − L_eff_true) / L_drawn`` (the honest value)."""
        return (self.L_drawn_um - self.L_eff_true_um) / self.L_drawn_um

    @property
    def current_gain(self) -> float:
        """Drive-current boost ``I_Dsat(L_eff_true) / I_Dsat(L_drawn)`` — purely geometric (``∝ L⁻¹``)."""
        return self.i_dsat / self.i_dsat_drawn


def mosfet_cross_section(
    *,
    channel_N_A: float,
    t_ox_um: float,
    L_drawn_um: float,
    gate: str = "n+poly",
    sd_dopant: Dopant | str = "P",
    sd_T_celsius: float = 1000.0,
    sd_t_min: float = 6.0,
    sd_N_surface: float | None = None,
    width_um: float = 10.0,
    overdrive_V: float = 1.0,
    lateral: bool = True,
    # grid / domain knobs (the two-window half-cell + the isolated edge share x-resolution)
    depth_um: float = 0.7,
    sd_extent_um: float = 0.4,
    nx: int = 180,
    ny: int = 140,
    n_steps: int = 150,
) -> MOSFET2D:
    """Assemble a 2-D MOSFET cross-section: lateral S/D diffusion → ``L_eff`` → the device.

    Forms the n⁺ S/D by a masked constant-source diffusion (``sd_dopant`` at ``sd_T_celsius`` for
    ``sd_t_min``, surface held at the solubility limit), reads the effective channel length two ways
    (the textbook ``L_drawn − 2·ΔL`` and the honest two-window ``2·x_j``), and builds the
    :class:`~device.MOSDevice` at ``L_eff_true`` with the **existing** Phase-4 model. ``V_t`` stays
    long-channel (``L`` only sets the geometry / ``I_Dsat``); **``lateral=False``** disables the
    correction (``L_eff = L_drawn``) and recovers the plain Phase-4 device **bit-for-bit** (the seam).

    Raises ``ValueError`` on **punchthrough** — when the two-window solve finds the S/D fronts merged
    under the gate (``L_eff_true ≤ 0``), the long-channel device does not exist.
    """
    d = DOPANTS[sd_dopant] if isinstance(sd_dopant, str) else sd_dopant
    Ns = d.N_solid_solubility if sd_N_surface is None else float(sd_N_surface)

    def _build(L_eff_true_um: float, L_eff_approx_um: float, delta_L_um: float, sd_xj_um: float,
               field: tuple | None) -> MOSFET2D:
        mos = device.threshold_voltage(channel_N_A, t_ox_um, gate, channel_length_um=L_eff_true_um)
        mos_drawn = device.threshold_voltage(channel_N_A, t_ox_um, gate, channel_length_um=L_drawn_um)
        i_eff = device.saturation_current(mos, mos.V_t + overdrive_V, width_um)
        i_drawn = device.saturation_current(mos_drawn, mos_drawn.V_t + overdrive_V, width_um)
        x_um = y_um = N = None
        if field is not None:
            x_cm, y_cm, N = field
            x_um, y_um = x_cm / CM_PER_UM, y_cm / CM_PER_UM
        return MOSFET2D(
            L_drawn_um=L_drawn_um, delta_L_um=delta_L_um, L_eff_approx_um=L_eff_approx_um,
            L_eff_true_um=L_eff_true_um, sd_xj_um=sd_xj_um, channel_N_A=channel_N_A,
            sd_N_surface=Ns, sd_dopant=d.name, sd_T_celsius=sd_T_celsius, sd_t_min=sd_t_min,
            t_ox_um=t_ox_um, gate=gate, width_um=width_um, overdrive_V=overdrive_V,
            mos=mos, mos_drawn=mos_drawn, i_dsat=i_eff, i_dsat_drawn=i_drawn,
            x_um=x_um, y_um=y_um, N=N,
        )

    if not lateral:
        # The exact seam: no lateral correction → L_eff = L_drawn → Phase 4 bit-for-bit.
        return _build(L_drawn_um, L_drawn_um, 0.0, 0.0, field=None)

    # 1. The isolated edge → the textbook surface ΔL (and the vertical S/D depth).
    edge = _isolated_edge(
        d, Ns, sd_T_celsius, sd_t_min, channel_N_A,
        length_x_um=L_drawn_um / 2.0 + sd_extent_um, depth_um=depth_um,
        x_edge_um=sd_extent_um, nx=nx, ny=ny, n_steps=n_steps,
    )
    delta_L_um = edge.delta_L_cm / CM_PER_UM
    L_eff_approx_um = L_drawn_um - 2.0 * delta_L_um

    # 2. The two-window half-cell → the honest junction-to-junction L_eff_true (and the field).
    x_cm, y_cm, N, L_eff_true_cm = _two_window_solve(
        diffusivity(d, sd_T_celsius), Ns, sd_t_min * 60.0, L_drawn_um * CM_PER_UM, channel_N_A,
        sd_extent_cm=sd_extent_um * CM_PER_UM, depth_cm=depth_um * CM_PER_UM,
        nx=nx, ny=ny, n_steps=n_steps,
    )
    L_eff_true_um = L_eff_true_cm / CM_PER_UM
    if L_eff_true_um <= 0.0:
        raise ValueError(
            f"punchthrough: the S/D fronts merge under the L_drawn = {L_drawn_um:.3f} µm gate "
            f"(L_eff_true ≤ 0) — the long-channel device model does not apply here"
        )

    return _build(L_eff_true_um, L_eff_approx_um, delta_L_um, edge.sd_xj_cm / CM_PER_UM,
                  field=(x_cm, y_cm, N))
