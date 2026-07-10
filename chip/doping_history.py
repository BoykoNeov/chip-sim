"""Pre-implant diffusion doping — the dose-control wall (historical-modes A1).

The **backward axis** (``docs/plans/historical-modes.md``): the simulator's doping step, run in its
pre-implant *period* mode, so the limitation that motivated ion implantation becomes visible. This
module is a **pure consumer** of :mod:`chip.diffusion_dopant` — it adds *no* physics and changes *no*
existing behaviour; it re-frames the predep machinery already there.

The wall (the discriminating observable — NOT the depth contrast :mod:`chip.demo_implant` already shows)
----------------------------------------------------------------------------------------------------
:mod:`chip.demo_implant` contrasts the same dose laid two ways — a surface-peaked ``erfc`` vs a buried
Gaussian (a *depth/topology* contrast). To "match" a light ``5e11 cm⁻²`` V_t-adjust dose by predep, it
**tunes the surface concentration ``N_s`` far below the solid-solubility limit** (``demo_implant``:
``N_s = DOSE / (1.128·√(Dt))``). But ``N_s`` is **physically pinned to solid solubility** — a Trumbore
material constant (:attr:`chip.diffusion_dopant.Dopant.N_solid_solubility`), *not* a free knob. This
module is the **honest accounting of that cheat**: at the solubility-pinned surface, a thermal predep
**cannot reproducibly meter a light, precise dose**. Laying ``Q = 5e11 cm⁻²`` of boron at the true
surface ``N_s = 3e20`` needs ``√(Dt) = Q/(1.128·N_s)`` → a **sub-millisecond predep**, uncontrollable on
the steep ``√t`` curve. Ion implantation meters dose electrically (beam charge / Faraday cup),
**decoupled from temperature and from depth** — so the light V_t-adjust / retrograde regime is reachable
*only* by implant. That **dose-control wall** — not depth — is what modernised the ~1968 predep planar
line (the era spine: predep → implant).

The honesty label (load-bearing)
--------------------------------
The wall is a **FLAGGED-magnitude leg, not a tight/structural one.** :func:`predep_dose_floor` is a
**controllability proxy** — a stand-in for reproducibility/uniformity on the steep ``√t`` curve, *not* a
hard thermodynamic floor. Its sign against a target dose depends on both ``T_predep`` and the house
``t_min``. For boron (``N_s = 3e20``): 900 °C/1 s → ``Q_min ≈ 1e13``; 800 °C/1 s → ``≈ 2e12``;
800 °C/0.1 s → ``≈ 7e11``. Against a **5e11** target the wall holds across that ``(T_predep, t_min)``
box *with margin*; a ``1e12`` target or a smaller ``t_min`` would flip it. So the honest claim is
**sign-robust only across an explicit box, stated by the caller** (the demo prints it). The *tight* legs
are the predep dose identity (:func:`chip.diffusion_dopant.predep_dose`) and the **seam** (a constant
source at solubility reproduces :func:`chip.diffusion_dopant.predeposit` bit-for-bit).

The source registry (period texture — one real physics axis)
------------------------------------------------------------
The classic predep sources — POCl₃, BBr₃/BN, spin-on-glass — are the historical *variations*. The **one**
genuine physics axis among them is **constant vs limited source**: a constant (unlimited) source holds
the surface at solubility (a Dirichlet ``erfc``, :class:`~chip.diffusion_dopant`); a limited (finite)
source deposits a fixed dose that redistributes to a Gaussian with a surface concentration *below*
solubility. POCl₃ and BBr₃ are *both* constant-at-solubility and differ **only in species** — the
limitation is identical; they are period texture, not three-way discrimination. Spin-on-glass (the
limited source) is the pre-implant *workaround*: it **can** meter a lower dose than a constant source —
which is exactly why it existed — but still falls short of implant's precision/reproducibility. Sources:
Plummer–Deal–Griffin *Silicon VLSI Technology* §7 (predep sources); Trumbore solubilities as in the
dopant-solid-solubility-source note; the ``N_s`` pinning as in :mod:`chip.diffusion_dopant`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import diffusion_dopant as dd

# The V_t-adjust dose the wall is argued against — a light, shallow threshold-adjust implant. Chosen with
# margin below the predep dose floor across the demo's (T_predep, t_min) box (see the honesty label).
VT_ADJUST_DOSE = 5.0e11         # cm⁻² — the canonical light dose predep cannot reproducibly meter


# --------------------------------------------------------------------------- #
# 1. The historical predep-source registry (period texture; one axis = constant vs limited)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DopingSource:
    """A historical predeposition source: how the period doping step established its surface.

    ``species`` is a :data:`chip.diffusion_dopant.DOPANTS` key. ``source_type`` is the **one real physics
    axis**:

      * ``"constant"`` — an unlimited source (gas/liquid/solid: POCl₃, BBr₃, BN) that holds the surface at
        the **solid-solubility limit** → a Dirichlet ``erfc`` predep. Its :attr:`surface_conc` is the
        species' solubility *by reference* (not a re-typed literal), so it cannot drift from
        :mod:`chip.diffusion_dopant`.
      * ``"limited"`` — a finite (dose-metered) source (spin-on-glass) that deposits a fixed dose which
        redistributes to a Gaussian with a surface concentration **below** solubility. :attr:`surface_conc`
        is ``None`` — the surface is set by the deposited dose + drive-in, not pinned.
    """

    name: str
    species: str
    source_type: str    # "constant" (unlimited, Dirichlet erfc) | "limited" (finite dose, Gaussian)

    def __post_init__(self) -> None:
        if self.species not in dd.DOPANTS:
            raise ValueError(f"unknown source species {self.species!r} (have {sorted(dd.DOPANTS)})")
        if self.source_type not in ("constant", "limited"):
            raise ValueError(f"source_type must be 'constant' or 'limited', got {self.source_type!r}")

    @property
    def surface_conc(self) -> float | None:
        """The surface (Dirichlet) concentration a **constant** source establishes — the species'
        solid solubility, **by reference** (``DOPANTS[species].N_solid_solubility``, the same float, so the
        bit-for-bit seam cannot drift). ``None`` for a limited source (its surface is dose-set)."""
        if self.source_type != "constant":
            return None
        return dd.DOPANTS[self.species].N_solid_solubility


# The three classic predep sources. Two constant-at-solubility (differing only in species) + one limited —
# the constant/limited axis is the physics; the rest is period flavour (see the module docstring).
SOURCES: dict[str, DopingSource] = {
    "POCl3": DopingSource("POCl₃ (liquid source, phosphorus)", "P", "constant"),
    "BBr3": DopingSource("BBr₃ (liquid source, boron)", "B", "constant"),
    "SOG": DopingSource("spin-on-glass (boron, finite-dose film)", "B", "limited"),
}


# --------------------------------------------------------------------------- #
# 2. The dose-control wall — the controllability proxy (FLAGGED) + the implant's decoupled reach
# --------------------------------------------------------------------------- #
def predep_dose_floor(source: DopingSource, *, T_predep_celsius: float, t_min_s: float) -> float:
    """Minimum dose a **constant** source can *reproducibly* lay — ``Q_min = 1.128·N_s·√(D·t_min)`` (cm⁻²).

    A **FLAGGED controllability proxy**, NOT a thermodynamic limit: it stands in for the smallest dose a
    constant (solubility-pinned) source can meter reproducibly, given a minimum controllable predep time
    ``t_min`` on the steep ``√t`` curve. ``t_min`` and ``T_predep`` are **house inputs** — the wall
    (``Q_min >`` a light target dose) holds by **sign across a stated ``(T_predep, t_min)`` box**, not as
    an exact number (see the module honesty label). Reuses the exact predep dose identity
    :func:`chip.diffusion_dopant.predep_dose`. Raises for a limited source (which meters dose directly, so
    a floor is meaningless).
    """
    if source.source_type != "constant":
        raise ValueError(
            f"predep_dose_floor is only meaningful for a constant source; {source.name!r} is limited "
            "(a finite source meters its dose directly — that is the whole point of the workaround)"
        )
    if t_min_s <= 0.0:
        raise ValueError(f"t_min_s must be > 0, got {t_min_s}")
    D = dd.diffusivity(source.species, T_predep_celsius)
    return dd.predep_dose(source.surface_conc, D, t_min_s)


def implant_reach(dose: float, energy_keV: float, species: str = "B") -> dd.Implant:
    """The decoupled knob: ion implant meters **any** positive dose electrically, independent of ``T``/depth.

    Returns the :class:`chip.diffusion_dopant.Implant` for ``dose`` (beam charge) at ``energy_keV`` (which
    sets depth via :func:`chip.diffusion_dopant.range_statistics`) — the two levers implant moves
    *independently*, the freedom the solubility-pinned predep lacks. This is the register that a light
    V_t-adjust dose *below* :func:`predep_dose_floor` is reachable at all.
    """
    return dd.Implant(dose=dose, energy_keV=energy_keV, species=species)


def dose_control_margin(
    source: DopingSource, *, T_predep_celsius: float, t_min_s: float, target_dose: float = VT_ADJUST_DOSE
) -> float:
    """How far the predep dose floor sits **above** a light target dose — ``Q_min / target`` (dimensionless).

    ``> 1`` means the constant source's controllable-dose floor exceeds the target (the wall: predep cannot
    reach it; implant can). The demo/tests assert this is ``> 1`` across an explicit ``(T_predep, t_min)``
    box — the FLAGGED, sign-robust-across-the-box claim, not a structural law.
    """
    return predep_dose_floor(source, T_predep_celsius=T_predep_celsius, t_min_s=t_min_s) / target_dose


# --------------------------------------------------------------------------- #
# 3. Laying a source's profile the honest way (the as-deposited period profiles)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SourceProfile:
    """A period source's as-deposited profile ``N(x)`` (the loose-coupling currency, plain arrays).

    ``x`` (cm from the surface), ``N`` (cm⁻³); ``dose`` the grid integral ``Σ N·Δx`` (cm⁻²);
    ``surface_conc`` the surface cell value ``N[0]`` (= solubility for a constant source; **below** it for
    a limited source — the workaround's lower reach)."""

    source: DopingSource
    x: np.ndarray
    N: np.ndarray
    dose: float
    surface_conc: float


def run_source(
    grid: dd.Grid,
    source: DopingSource,
    *,
    T_predep_celsius: float,
    t_predep_s: float,
    dose: float | None = None,
) -> SourceProfile:
    """Lay ``source``'s as-deposited profile on ``grid`` (constant → ``erfc``; limited → finite-dose Gaussian).

    * **constant** — the real Dirichlet predep at the pinned solubility surface
      (:func:`chip.diffusion_dopant.predeposit` with ``N_surface = source.surface_conc``). Because
      ``surface_conc`` *references* the dopant's solubility, this is **bit-for-bit** the default
      :func:`~chip.diffusion_dopant.predeposit` — the seam.
    * **limited** — a finite deposited ``dose`` redistributed to the sealed-surface Gaussian
      (:func:`chip.diffusion_dopant.analytic_drivein_gaussian`), whose surface concentration
      ``Q/√(πDt) <`` solubility — the workaround that meters a lower dose. ``dose`` is required here.
    """
    d = dd.DOPANTS[source.species]
    if source.source_type == "constant":
        p = dd.predeposit(grid, source.species, T_predep_celsius, t_predep_s,
                          N_surface=source.surface_conc)
        return SourceProfile(source, p.x, p.N, p.dose, float(source.surface_conc))
    # limited: a finite dose Q → the sealed-surface Gaussian (surface below solubility)
    if dose is None:
        raise ValueError("a limited source needs an explicit deposited dose (cm⁻²)")
    if dose <= 0.0:
        raise ValueError(f"deposited dose must be > 0, got {dose}")
    D = dd.diffusivity(d, T_predep_celsius)
    N = dd.analytic_drivein_gaussian(grid.centers, t_predep_s, D, dose)
    grid_dose = float(np.sum(N * grid.widths))
    return SourceProfile(source, grid.centers, N, grid_dose, float(N[0]))
