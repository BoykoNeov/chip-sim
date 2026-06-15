"""The wafer state — what flows between steps (the plan §3, G1-minimal shape).

A wafer is **not** a scalar: it is an across-wafer **die map** (a coarse lateral grid of die
*sites*), each site carrying its own local process outputs that accumulate as the line runs.
The state is **immutable** — every step returns a *new* :class:`WaferState`; provenance is
**append-only** (the failure trail, "why did this die?").

G1 scope (deliberately minimal — ADR 0005 §3, rule-of-three): the state holds *only* what the
existing back end consumes and produces — gate oxide ``t_ox``, printed ``CD``, the S/D
junction ``x_j``/``R_s``, and the device read ``V_t``/``I_Dsat`` — plus the per-die history and
verdict. **No contamination / geometry / defect machinery yet**: those arrive with their named
consumers (oxygen→donors at G2, particles at G3, metals→lifetime at G4), so the schema does not
guess an API the game has not exercised.

Units mirror the physics layer at the boundary: ``t_ox``/``x_j``/``cd`` in **µm**/nm, ``N_A`` in
cm⁻³, ``V_t`` in V, ``I_Dsat`` in A.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable

import numpy as np

from chip.purification import Contamination
from chip.wafer_prep import WaferGeometry

# --------------------------------------------------------------------------- #
# Per-step provenance — the "why did this die?" trail
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DieStepRecord:
    """One step's contribution to one die: the **effective** knobs in, the outputs out.

    ``knobs_in`` is the per-die effective recipe slice *after* the variation layer (so a die's
    actual focus/thickness, not just the nominal); ``outputs`` is what the physics produced.
    Walking a failed die's ``history`` (newest last) reconstructs the causal chain — the banked
    artifact's "the failure trail names defocus as the cause."
    """

    step: str
    knobs_in: dict
    outputs: dict


@dataclass(frozen=True)
class StepRecord:
    """One step's wafer-level record — the nominal recipe slice + an aggregate summary.

    Append-only on :attr:`WaferState.provenance`; ``summary`` carries cheap aggregates (mean of
    the produced field, running yield) for the line-level narrative, never per-die detail.
    """

    step: str
    knobs: dict
    summary: dict


@dataclass(frozen=True)
class DefectEvent:
    """One killer particle defect placed on the across-wafer map (G3 — the die map made physical).

    ``x``/``y`` are the defect's location in **wafer-radius units** (``∈ [-1, 1]``, the same frame
    the die-map plot draws in); ``killer`` marks it fatal to the die it lands on (G3 places only
    killers — ``D₀`` is the *killer*-defect density — and keeps the flag for future cosmetic
    particles). A die that catches one or more is dead **functionally** (its parametric device may
    still read fine — distinct from a litho image that never resolved, where the device *refuses*).
    """

    x: float
    y: float
    killer: bool = True


@dataclass(frozen=True)
class Verdict:
    """A die's pass/fail against the spec windows. ``reasons`` names every failing check (empty if passed)."""

    passed: bool
    reasons: tuple[str, ...] = ()

    @property
    def failed(self) -> bool:
        return not self.passed


# --------------------------------------------------------------------------- #
# A die site and its accumulating local state
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Die:
    """One die *site* on the wafer and the local process state it accumulates.

    ``site`` is the integer grid index; ``radius_frac`` ∈ [0, 1] is its normalized distance from
    wafer centre (0 = centre, 1 = the edge-exclusion boundary) — the handle the center-to-edge
    variation trend reads. Every process output starts ``None`` and is filled by its producing
    step (so an un-run or refused step is visible as a gap, not a fake zero). ``history`` is the
    append-only per-die :class:`DieStepRecord` trail; ``verdict`` is set by the test step.
    """

    site: tuple[int, int]
    radius_frac: float
    t_ox_um: float | None = None
    cd_nm: float | None = None
    nils: float | None = None
    resolved: bool | None = None
    x_j_um: float | None = None
    R_s: float | None = None
    gate_height_nm: float | None = None         # standing gate height after the etch (G5; the gap-fill AR reads it)
    V_t: float | None = None
    i_dsat: float | None = None
    tau: float | None = None                    # minority-carrier SRH lifetime (s) — deep-level metals (G4b)
    j_leak: float | None = None                 # junction reverse-leakage density (A/cm²) — the metal killer (G4b)
    bv_V: float | None = None                   # drain–body junction avalanche breakdown (V) — set by the device step (slice 2)
    defects: tuple[DefectEvent, ...] = ()       # killer particles caught at wafer prep (G3)
    killed_by_defect: bool | None = None        # set by wafer prep; True ⇒ a functional fail
    voided: bool | None = None                  # set by etch/depo (G5); True ⇒ a depo void → functional fail
    bridged: bool | None = None                 # set by etch/depo (D1); True ⇒ an under-etch residual short → functional fail
    assembled: bool | None = None               # set by packaging (G6); False ⇒ a back-end assembly scrap
    bin: str | None = None                      # speed/value bin assigned at final test (G6); "reject" ⇒ binned out
    verdict: Verdict | None = None
    history: tuple[DieStepRecord, ...] = ()

    @property
    def cd_um(self) -> float | None:
        """Printed CD in micrometres (``cd_nm·1e-3``) — the cross-module length currency the device reads."""
        return None if self.cd_nm is None else self.cd_nm * 1.0e-3

    @property
    def i_dsat_mA(self) -> float | None:
        """Saturation drive current in **mA** (the spec-window / readout unit)."""
        return None if self.i_dsat is None else self.i_dsat * 1.0e3

    @property
    def tau_us(self) -> float | None:
        """Minority-carrier SRH lifetime in **µs** (the deep-level-metal readout, G4b)."""
        return None if self.tau is None else self.tau * 1.0e6

    @property
    def j_leak_nA_cm2(self) -> float | None:
        """Junction reverse-leakage density in **nA/cm²** (the leakage spec-window unit, G4b)."""
        return None if self.j_leak is None else self.j_leak * 1.0e9

    def record(self, step: str, knobs_in: dict, outputs: dict, **updates) -> "Die":
        """Return a new die with ``updates`` applied and a :class:`DieStepRecord` appended (append-only)."""
        rec = DieStepRecord(step=step, knobs_in=knobs_in, outputs=outputs)
        return replace(self, history=self.history + (rec,), **updates)


# --------------------------------------------------------------------------- #
# The wafer — an immutable snapshot of the whole die map + provenance
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class WaferState:
    """An immutable snapshot of the wafer: its die map, substrate doping, and append-only provenance.

    ``channel_N_A`` (cm⁻³) is the **effective** p-type substrate doping the device sees. As of G2 its
    baseline is the **Scheil slice of the boule** at this wafer's axial position ``slice_z`` (the
    fraction solidified, ``[0, 1)``); as of G4 it includes any **residual-dopant net shift** from
    imperfect purification (so it is the boule slice + ``contamination.net_doping_shift``).
    ``resistivity_ohm_cm`` is the substrate resistivity that doping implies (the fab characterization
    currency). ``contamination`` (G4) is the wafer-level purified **impurity vector** — ``Na`` drives
    the gate-oxide ``Q_ox`` (the device ``V_t`` shift) and the deep-level **metals** (Fe/Cu) drive the
    SRH lifetime → junction leakage (G4b, :mod:`chip.lifetime`; the gap G4a named, now wired). All
    are wafer-level: ``slice_z`` and the contamination are constant across the die map (the axial boule
    + contamination stories compose orthogonally with the radial die-map story). They default to
    ``None`` so a bare G1-style wafer is still constructible. ``dies`` is the die map (fixed order — the
    determinism contract); ``provenance`` is the append-only wafer-level :class:`StepRecord` trail;
    ``rework_log`` accumulates rework events (see :mod:`fab_game.pipeline`).
    """

    wafer_id: str
    channel_N_A: float
    dies: tuple[Die, ...]
    slice_z: float | None = None                             # axial fraction solidified (G2 boule slice)
    resistivity_ohm_cm: float | None = None                  # substrate resistivity at this slice (Ω·cm)
    geometry: WaferGeometry | None = None                    # prepped thickness/TTV/bow (G3, wafer-level)
    contamination: Contamination | None = None               # purified impurity vector (G4, wafer-level)
    provenance: tuple[StepRecord, ...] = ()
    rework_log: tuple = ()                                    # tuple[ReworkRecord, ...] (avoids an import cycle)

    @property
    def n_dies(self) -> int:
        return len(self.dies)

    def map_dies(self, fn: Callable[[Die], Die]) -> "WaferState":
        """Return a new wafer with ``fn`` applied to every die **in order** (the determinism contract)."""
        return replace(self, dies=tuple(fn(d) for d in self.dies))

    def with_step(self, record: StepRecord, dies: tuple[Die, ...]) -> "WaferState":
        """Return a new wafer with updated ``dies`` and ``record`` appended to provenance (append-only)."""
        return replace(self, dies=dies, provenance=self.provenance + (record,))


# --------------------------------------------------------------------------- #
# The die map geometry — a circular wafer's sites on a square grid
# --------------------------------------------------------------------------- #
def build_die_map(grid_n: int = 5, edge_exclusion: float = 0.95) -> tuple[Die, ...]:
    """Lay out the across-wafer die map: a ``grid_n × grid_n`` lattice clipped to the wafer circle.

    Sites sit at the cell centres of a ``grid_n × grid_n`` square grid spanning the wafer diameter;
    a site is kept only if its centre lies within ``edge_exclusion`` of the wafer radius (the usual
    fab edge-exclusion ring). ``radius_frac`` is the site's distance from centre **normalized so the
    boundary is 1.0**, so the center-to-edge variation trend reads a clean 0→1 ramp. An **odd**
    ``grid_n`` puts one die exactly at the centre (``radius_frac = 0``) — the site the seam test and
    the single-die path use.

    Returns the dies in row-major site order (the fixed iteration order the determinism contract
    relies on).
    """
    if grid_n < 1:
        raise ValueError(f"grid_n must be ≥ 1, got {grid_n}")
    # Cell centres on [-1, 1] in units of the wafer radius.
    coords = (np.arange(grid_n) + 0.5) * (2.0 / grid_n) - 1.0
    dies: list[Die] = []
    for i, gx in enumerate(coords):
        for j, gy in enumerate(coords):
            r = float(np.hypot(gx, gy))
            if r <= edge_exclusion:
                dies.append(Die(site=(i, j), radius_frac=min(r / edge_exclusion, 1.0)))
    if not dies:
        raise ValueError("die map is empty — loosen edge_exclusion or raise grid_n")
    return tuple(dies)


# --------------------------------------------------------------------------- #
# The die map made *physical* (G3) — one definition of cell geometry + die area
# --------------------------------------------------------------------------- #
# These are THE single source of a die's footprint and area: the defect placement
# (fab_game.defects) draws against ``die_area_cm2`` and positions inside ``die_cell_bounds``, and the
# closed-form yield (the demo / the convergence test) feeds ``die_area_cm2`` to ``poisson_yield`` —
# so the stochastic kill rate and the analytic ``exp(−D₀·A)`` use a *byte-identical* area (the G3
# analogue of G2's "parameterize by N_seed so the seam is exact"). Both live in wafer-radius units:
# a die occupies a square cell of edge ``cell_fraction = 2/grid_n`` (the build_die_map lattice spacing),
# centred at ``die_cell_center``; its physical edge is ``cell_fraction · wafer_radius``.
def cell_fraction(grid_n: int) -> float:
    """A die cell's edge length in wafer-radius units — the ``2/grid_n`` lattice spacing of the map."""
    return 2.0 / grid_n


def die_cell_center(site: tuple[int, int], grid_n: int) -> tuple[float, float]:
    """The (x, y) centre of die ``site``'s cell in wafer-radius units ``[-1, 1]`` (the map frame)."""
    cf = cell_fraction(grid_n)
    return ((site[0] + 0.5) * cf - 1.0, (site[1] + 0.5) * cf - 1.0)


def die_cell_bounds(site: tuple[int, int], grid_n: int) -> tuple[float, float, float, float]:
    """Die ``site``'s cell as ``(x_lo, x_hi, y_lo, y_hi)`` in wafer-radius units — the placement box."""
    cx, cy = die_cell_center(site, grid_n)
    h = cell_fraction(grid_n) / 2.0
    return (cx - h, cx + h, cy - h, cy + h)


def die_area_cm2(grid_n: int, wafer_diameter_mm: float) -> float:
    """A die's critical area (cm²) — ``(cell_fraction · wafer_radius)²`` — the ONE area definition.

    The coarse map makes this an **illustrative** area (a 5×5 grid over a 200 mm wafer gives ~16 cm²
    dies — far larger than a real die), but it is *consistent*: the same value drives both the Poisson
    placement and the ``exp(−D₀·A)`` closed form, so the empirical kill rate converges to the law.
    """
    radius_cm = wafer_diameter_mm / 2.0 / 10.0           # mm → cm
    edge_cm = cell_fraction(grid_n) * radius_cm
    return edge_cm * edge_cm
