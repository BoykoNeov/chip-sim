"""LOCOS isolation & the bird's beak — the 2-D oxidation regime's historical consumer (historical-modes B5).

The **backward axis** (``docs/plans/historical-modes.md``), *isolation* rung, and the one chunk that
finally gives the engine's **2-D regime** (:class:`engines.diffusion.Diffusion2D`, v1.8/v1.11) a
*second* consumer beside the lateral-S/D cross-section. **LOCOS** — LOCal Oxidation of Silicon, the
period isolation scheme (≈1970s→early-1990s) — grows a thick **field oxide** between devices by masking
the **active** areas with silicon nitride (Si₃N₄), which blocks the oxidant. But oxidant that enters at
the open field **diffuses laterally under the nitride edge** and grows oxide there too, lifting the
nitride into the classic **bird's beak** that encroaches into the active area. Below a minimum drawn
active width the two beaks from opposite edges **merge** and the active island pinches off — the
isolation-density wall that motivated **shallow-trench isolation (STI)** (F7 in ``future-steps.md``,
deferred there for want of a consumer — B5 is its *historical/displayable* form). Like the other
history modes (:mod:`chip.doping_history` A1, :mod:`chip.oxidation_history` A3,
:mod:`chip.litho_history` A2, :mod:`chip.resist_history` A4, :mod:`chip.metallization_history` B6) this
is a **pure additive consumer** — it changes *no* existing behaviour and adds no physics to
:mod:`chip.oxidation` or the engine. The **third** Tier-2 mode after H0/A2/A4.

What the 2-D engine carries here — the honest call (the A4 discriminator, applied)
-----------------------------------------------------------------------------------
This is framed as :mod:`chip.device_2d`'s pattern — **a validation deepening**, *not* a new-physics
contour finding. Running the A4 test ("delete the 2-D solve — does the headline change?"):

* The **encroachment magnitude** (the beak length, and hence the min active width ``= 2·L_beak``) is
  **geometric / flagged** — it is set by a calibrated lateral length, not produced by the engine. The
  plan (§236) already flags "the bird's-beak encroachment ratio vs field-oxide thickness." Presenting
  that number as an engine output would be the A4 free-contour trap in a new suit: calling a tuned
  length "emergent." It is owned as **flagged calibration** (:data:`BEAK_DIFFUSION_FACTOR`).
* The **topology** — the two beaks *merging* as the drawn active width shrinks, and the resulting
  **pinch-off** of the active island — **does** change if you delete the solve, and *that* is what the
  2-D engine earns (the :mod:`chip.device_2d` two-window pattern): a **different BC topology** (two field
  windows + a symmetry plane vs one semi-infinite edge) that at **wide stripes** independently
  cross-checks the encroachment (``active ≈ W − 2·L_beak`` to grid precision), and — the finding the
  engine earns — reveals that as the stripe narrows the two opposing beaks' oxidant fields **overlap**,
  pinching the island off at a drawn width *larger* than the single-edge ``2·L_beak``: LOCOS is *worse*
  than the isolated-edge estimate predicts. The *direction* of that interaction is robust; its exact
  merge *width* is model-sensitive (it rides the flagged ``L_D``), so only the direction is asserted.

So the 2-D solve produces a **normalized lateral oxidant-availability modulation** ``m(x) ∈ [0, 1]``
(1 in the open field, decaying toward 0 under the nitride), and the absolute field-oxide thickness is
:mod:`chip.oxidation`'s Deal–Grove ``grow_oxide`` **times** that modulation::

    t_ox(x) = grow_oxide(recipe).t_ox · m(x)

Deal–Grove stays the thickness source (√(B·t), the tight/seam leg); the engine supplies only the beak
*geometry*. This resolves the seam landmine: a transient linear scalar in :class:`Diffusion2D`
penetrates as ``√(D·t)`` (erfc), **not** Deal–Grove's ``√(B·t)`` — so the 2-D field must **not** set the
thickness, only modulate it. In the open field the surface is a Dirichlet oxidant source, so ``m ≡ 1``
there *by construction* (``m = 1`` on every open-mask cell, the diffused value only under the nitride) —
which makes the planar seam **exact**, not tolerance-bound.

Why the normalized diffusion length is not "extracted physics"
--------------------------------------------------------------
A first-principles oxidant diffusivity would need the oxide solubility ``C*`` and ``N₁`` (the constants
Deal–Grove folds into ``B``) — unvalidated here, an over-build. Instead the lateral length is set to
``L_D = BEAK_DIFFUSION_FACTOR · t_field_ox`` (a **flagged** dimensionless factor times the field-oxide
thickness), so the beak/field-oxide **ratio** lands on the cited value (~0.8–1×) and stays roughly
recipe-robust (as real LOCOS does) — *transparently a calibration*, not a claimed emergence. The engine
then produces the beak **shape** and the **merge** with that length as its scale.

The headline (the wall STI cleared): the two-beak merge
-------------------------------------------------------
For a drawn active stripe of width ``W`` (nitride) flanked by field on both sides, the surviving active
width narrows to ``≈ W − 2·L_beak`` while the stripe is wide, but as it shrinks the two beaks' oxidant
fields **overlap** and the surviving width pinches to **zero** at a drawn width *larger* than
``2·L_beak`` (the interaction makes LOCOS worse than the isolated-edge estimate; the exact merge width
rides the flagged ``L_D`` and is not asserted). The robust, **coefficient-free** claim: the **minimum
isolable active pitch scales with the field-oxide thickness** (the beak ∝ t_field), so a thick field
oxide sets a hard floor on how closely active areas can pack. STI (vertical trench walls etched, then
filled — no lateral oxidant path) has *no* beak, so its active width equals the drawn width down to the
litho floor — the successor that cleared the wall.

The honesty ladder (per the ``historical-modes.md`` triad)
----------------------------------------------------------
* **Tight.** (1) The **planar seam**: with no nitride (all-open surface) ``m ≡ 1`` and the field-oxide
  thickness is :func:`chip.oxidation.grow_oxide` **bit-for-bit**; even *with* a mask the field plateau
  (open-mask cells) is ``grow_oxide`` exactly. (2) The **sign/topology**: the beak only ever grows
  *inward* from the field edge (``m ≥ 0`` adds oxide), so the active width shrinks **monotonically** as
  the drawn width shrinks and, past the floor, pinches off — sign-robust; the maximum principle keeps
  ``m ∈ [0, 1]``. (3) The independent **two-window cross-check at wide stripes** (``W`` ≳ several µm):
  the direct two-field solve reproduces the single-edge subtraction ``W − 2·L_beak`` to grid precision
  there — a *different* BC topology confirming the encroachment. It does **not** agree near the knee
  (the interaction below) — that is the earned finding, not a defect.
* **The earned 2-D finding (qualitative — direction, not coefficient).** Delete the two-window solve and
  you would predict a minimum active pitch of ``2·L_beak``; *with* it, the opposing beaks' oxidant
  fields **overlap** and the island pinches off at a *larger* drawn width — the interaction a single
  isolated edge structurally cannot see. Its **direction** (LOCOS worse than the isolated estimate) is
  what the engine earns; its **width coefficient** is flagged (see below).
* **Flagged — the magnitudes.** :data:`BEAK_DIFFUSION_FACTOR` (the beak length ÷ field-oxide thickness,
  set to the cited ~0.8–1× LOCOS rule); :data:`ACTIVE_MODULATION_THRESHOLD` (the ``m`` level dividing
  "field oxide" from "active silicon"); and the **merge coefficient** (the pinch-off width ÷ ``2·L_beak``)
  — driven by ``L_D ≈ 3×`` the beak, uncalibrated, no cited value either way. Named, not asserted exact.

Named scope edges (honest ceilings, stated so the omission isn't silent)
------------------------------------------------------------------------
* **A linear-diffusion caricature — no moving boundary, no stress.** The real bird's beak is driven by
  the *moving* Si/SiO₂ interface and the **volume-expansion stress** of the growing oxide (the beak
  physically lifts the nitride); this models only a static, linear normalized-oxidant field. No stress,
  no nitride lift, no field-oxide thinning ("white-ribbon"/Kooi effect).
* **Pinch-off is read as a per-stripe cliff (active width ≤ 0).** The surviving width approaches zero
  continuously (the graded quantity), but the "island lost" is taken at ``width = 0``; a graded
  *fraction of islands lost* under active-edge non-uniformity would smear that cliff (the
  ``gradual-failure-preferred`` move) — named here, not built.
* **The merge width is model-sensitive (only its direction is asserted).** Unlike :mod:`chip.device_2d`
  — whose contour sits in the deep exponential tail, so its two-window ≡ subtraction to grid precision
  even near the knee — here the beaks interact well *above* the resolved scale: the pinch-off is real
  and its *direction* robust (LOCOS worse than ``2·L_beak``), but its exact *width* rides the flagged
  ``L_D`` of this linear-availability caricature, so the coefficient is flagged, not asserted.
* **Deal–Grove supplies only a scalar field-oxide thickness.** The modulation ``t_ox = grow_oxide·m`` is
  a linear lateral weighting, not a 2-D Deal–Grove solve of oxide thickness (that would need the
  moving-boundary machinery above); the *vertical* thickness is the existing closed form.

Units — µm-native (the :mod:`chip.oxidation` cross-module length currency)
--------------------------------------------------------------------------
All lengths (field-oxide thickness, beak length, active/drawn width, the lateral ``x`` grid, the beak
diffusion length ``L_D``) in **µm**; the modulation ``m`` and the threshold are dimensionless. The
normalized diffusion is run with ``D = 1`` and ``t = L_D²`` so ``√(D·t) = L_D`` — a purely geometric
solve whose only scale is ``L_D`` (µm), no physical time.

Validation boundary
-------------------
The 2-D solver machinery (conservation, monotonicity, the M-matrix maximum principle that keeps
``m ∈ [0, 1]``) is the engine's, validated in ``engines/diffusion/tests/test_diffusion2d.py``. This
module's tests validate the **composition**: the exact planar seam (field plateau ≡ ``grow_oxide``), the
monotone inward encroachment + pinch-off (sign/topology), the two-window ≡ subtraction agreement at a
wide stripe and its hard departure at merge (the independent cross-check), ``m ∈ [0, 1]`` (the maximum
principle in use), and the cited beak/field-oxide ratio (the flagged benchmark).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engines.diffusion import Diffusion2D, uniform_grid_2d, Neumann, MaskedSurface
from . import oxidation as ox

UM_PER_NM = ox.UM_PER_NM          # 1 nm = 1e-3 µm (report thin beaks/oxides in nm too)

# --------------------------------------------------------------------------- #
# The flagged calibration — the beak's lateral scale and the "active" contour
# --------------------------------------------------------------------------- #
# The bird's-beak length is, to first order, comparable to the field-oxide thickness — the standard
# LOCOS rule of thumb (beak encroachment ≈ 0.8–1× the field oxide for conventional pad-oxide/nitride
# stacks; Wolf, "Silicon Processing for the VLSI Era" Vol. 2 §7; Plummer–Deal–Griffin §9). Modelled by
# tying the normalized-oxidant lateral diffusion length L_D to the field-oxide thickness through a
# FLAGGED dimensionless factor, so the beak/field-oxide ratio lands on that cited value and is roughly
# recipe-robust (as real LOCOS is). This is a calibration, NOT a claimed emergence — the magnitude is
# the flagged leg; the engine carries the beak SHAPE and the two-beak MERGE (the tight topology).
BEAK_DIFFUSION_FACTOR = 3.0       # FLAGGED — L_D = factor·t_field_ox; sets beak ÷ field-oxide ≈ 0.9 (cited)
ACTIVE_MODULATION_THRESHOLD = 0.5  # FLAGGED — m < this ⇒ active silicon (little oxide); ≥ ⇒ field oxide

# A representative modern field-oxidation recipe (wet, the field/masking-oxide regime) — used as the
# default the demo and the bundled cross-section grow the field oxide with. Flagged as a demo scale.
FIELD_AMBIENT = "wet"
FIELD_T_CELSIUS = 1000.0
FIELD_T_MINUTES = 90.0
FIELD_ORIENTATION = "100"


def field_oxide_thickness_um(
    ambient: str = FIELD_AMBIENT, T_celsius: float = FIELD_T_CELSIUS,
    t_minutes: float = FIELD_T_MINUTES, orientation: str = FIELD_ORIENTATION,
) -> float:
    """The planar field-oxide thickness (µm) — :func:`chip.oxidation.grow_oxide` verbatim (the seam).

    This is the *absolute* thickness the lateral modulation scales; in the open field ``m = 1`` so the
    field plateau equals this exactly (the tight/seam leg). Wet by default — the thick field/masking
    oxide regime LOCOS grows.
    """
    return ox.grow_oxide(ambient, T_celsius, t_minutes, orientation).t_ox


# --------------------------------------------------------------------------- #
# Surface contour readers — the oxide grows at the surface (y=0 → row j=0)
# --------------------------------------------------------------------------- #
def _first_crossing_x(x: np.ndarray, m: np.ndarray, level: float) -> float:
    """Smallest ``x`` where an *increasing* ``m(x)`` reaches ``level`` (linear-interp).

    For the two-field half-cell the surface modulation rises with ``x`` from the stripe centre (low —
    still active silicon) toward the open field (``m = 1``); the surviving active edge is the first
    ``x`` at which ``m`` reaches the "active" threshold. Returns **0.0** if the stripe centre is itself
    already oxidized (``m[0] ≥ level`` → the two beaks have merged → pinch-off), or ``x[-1]`` if it
    never reaches ``level``.
    """
    above = m >= level
    if above[0]:
        return 0.0                                # centre already field-oxide → beaks merged (pinch-off)
    if not above.any():
        return float(x[-1])
    i = int(np.where(above)[0][0])
    f = (level - m[i - 1]) / (m[i] - m[i - 1])
    return float(x[i - 1] + f * (x[i] - x[i - 1]))


def _last_crossing_x(x: np.ndarray, m: np.ndarray, level: float) -> float:
    """Largest ``x`` where a *decreasing* ``m(x)`` is still ≥ ``level`` (linear-interp).

    For the isolated single edge the surface modulation falls with ``x`` from the open field
    (``m = 1``) under the nitride toward 0; the beak tip is the furthest ``x`` still above the "active"
    threshold. Returns ``x[0]`` if it is never above ``level``.
    """
    above = m >= level
    if not above.any():
        return float(x[0])
    i = int(np.where(above)[0][-1])
    if i == m.size - 1:
        return float(x[i])                        # contour runs off the domain edge
    f = (m[i] - level) / (m[i] - m[i + 1])
    return float(x[i] + f * (x[i + 1] - x[i]))


# --------------------------------------------------------------------------- #
# The normalized 2-D oxidant-availability solve (the engine call)
# --------------------------------------------------------------------------- #
def _surface_modulation(
    open_mask: np.ndarray, *, Lx_um: float, Ly_um: float, L_D_um: float,
    nx: int, ny: int, n_steps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve the normalized oxidant availability ``m(x, y) ∈ [0, 1]`` under a nitride-masked surface.

    The surface ``y=0`` is a Dirichlet oxidant source (``value = 1``) where ``open_mask`` is ``True``
    (the **field**, nitride absent) and no-flux under the nitride (``open_mask`` ``False``); the other
    three faces are no-flux. Purely geometric: ``D = 1``, ``t = L_D²`` so ``√(D·t) = L_D`` — the only
    scale is the beak diffusion length. Backward-Euler's M-matrix keeps ``m ∈ [0, 1]`` (the maximum
    principle). Returns ``(x, y, m_field)`` in µm; read the **surface row** ``m_field[:, 0]`` (forcing
    open cells to exactly 1 — see :func:`_surface_line`).
    """
    grid = uniform_grid_2d(Lx_um, Ly_um, nx, ny)
    solver = Diffusion2D(
        grid, 1.0,
        bc_xlo=Neumann(0.0), bc_xhi=Neumann(0.0),
        bc_ylo=MaskedSurface(1.0, open_mask),         # field: oxidant Dirichlet | nitride: no-flux
        bc_yhi=Neumann(0.0),
    )
    t_end = L_D_um ** 2                                # D = 1 → √(D·t) = L_D
    m = solver.solve(np.zeros(grid.shape), t_end, t_end / n_steps)
    return grid.x.centers, grid.y.centers, m


def _surface_line(open_mask: np.ndarray, m: np.ndarray) -> np.ndarray:
    """The surface modulation ``m(x)`` with **open (field) cells forced to exactly 1** (the seam).

    In the open field the oxidant is a Dirichlet source, so ``m = 1`` there *by construction* — pinning
    it exactly (rather than reading the finite-``t`` transient) makes the field plateau equal
    ``grow_oxide`` bit-for-bit. The diffused value is used only under the nitride (the beak).
    """
    return np.where(open_mask, 1.0, m[:, 0])


# --------------------------------------------------------------------------- #
# 1. The isolated nitride edge → the bird's-beak encroachment length
# --------------------------------------------------------------------------- #
def birds_beak_length_um(
    field_ox_um: float, *,
    beak_factor: float = BEAK_DIFFUSION_FACTOR,
    threshold: float = ACTIVE_MODULATION_THRESHOLD,
    nx: int = 220, ny: int = 120, n_steps: int = 120,
) -> float:
    """The bird's-beak encroachment ``L_beak`` (µm) at a single isolated field/nitride edge.

    Runs the normalized solve for a semi-infinite field (``x < x_edge``, oxidant open) meeting a
    semi-infinite nitride (``x ≥ x_edge``, no-flux), and reads how far under the nitride the ``m =``
    ``threshold`` contour reaches beyond the edge — the width of the encroached (oxidized) strip that
    eats into the active area. The lateral scale is ``L_D = beak_factor · field_ox_um`` (the flagged
    calibration); the domain auto-sizes to ``L_D`` so the beak is always contained.
    """
    if field_ox_um <= 0.0:
        raise ValueError(f"field_ox_um must be > 0, got {field_ox_um}")
    L_D = beak_factor * field_ox_um
    x_edge = 4.0 * L_D                                 # field occupies x < x_edge (well clear of x=0)
    Lx = x_edge + 6.0 * L_D                            # nitride extends far enough to contain the beak
    Ly = 4.0 * L_D
    grid_x = uniform_grid_2d(Lx, Ly, nx, ny).x.centers
    open_mask = grid_x < x_edge                        # field open where the nitride is absent
    x, _, m = _surface_modulation(open_mask, Lx_um=Lx, Ly_um=Ly, L_D_um=L_D,
                                  nx=nx, ny=ny, n_steps=n_steps)
    m_surf = _surface_line(open_mask, m)
    tip = _last_crossing_x(x, m_surf, threshold)
    return max(tip - x_edge, 0.0)


# --------------------------------------------------------------------------- #
# 2. The two-field half-cell → the surviving active width (and its pinch-off)
# --------------------------------------------------------------------------- #
def _active_width_solve(
    drawn_active_um: float, field_ox_um: float, *,
    beak_factor: float, threshold: float, nx: int, ny: int, n_steps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Half of the symmetric two-field cell → ``m(x, y)`` and the surviving active width (µm).

    The nitride active stripe is centred at ``x=0`` (a no-flux symmetry plane = the mirror between the
    two field edges); the field is **open for ``x ≥ W/2``** (oxidant Dirichlet) and the nitride seals
    ``x < W/2`` (no-flux). The surviving active half-width is the first ``x`` (from the centre) at which
    ``m`` reaches ``threshold``; the full active width is twice that (``0`` ⇒ the two beaks have merged
    → pinch-off). Returns ``(x, y, m, active_width_um)``.
    """
    L_D = beak_factor * field_ox_um
    gate_half = 0.5 * drawn_active_um
    Lx = gate_half + 4.0 * L_D                          # enough open field beyond the stripe
    Ly = 4.0 * L_D
    grid_x = uniform_grid_2d(Lx, Ly, nx, ny).x.centers
    open_mask = grid_x >= gate_half                     # field open outside the nitride stripe
    x, y, m = _surface_modulation(open_mask, Lx_um=Lx, Ly_um=Ly, L_D_um=L_D,
                                  nx=nx, ny=ny, n_steps=n_steps)
    m_surf = _surface_line(open_mask, m)
    active_half = _first_crossing_x(x, m_surf, threshold)
    return x, y, m, 2.0 * active_half


def active_width_um(
    drawn_active_um: float, field_ox_um: float, *,
    beak_factor: float = BEAK_DIFFUSION_FACTOR,
    threshold: float = ACTIVE_MODULATION_THRESHOLD,
    nx: int = 220, ny: int = 120, n_steps: int = 120,
) -> float:
    """The surviving active width (µm) of a drawn nitride stripe after LOCOS — the two-field solve alone.

    The cheap path for sweeping ``drawn_active_um`` (the wall figure): runs only the two-field half-cell
    and reads the surviving active width directly. Returns **0.0** at pinch-off (the two bird's beaks
    have merged under the nitride and the active island is fully consumed).
    """
    if field_ox_um <= 0.0:
        raise ValueError(f"field_ox_um must be > 0, got {field_ox_um}")
    _, _, _, w = _active_width_solve(
        drawn_active_um, field_ox_um,
        beak_factor=beak_factor, threshold=threshold, nx=nx, ny=ny, n_steps=n_steps,
    )
    return w


# --------------------------------------------------------------------------- #
# 3. A field-oxide cross-section profile (for the beak figure)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FieldOxideProfile:
    """A LOCOS oxide cross-section: the field-oxide thickness ``t_ox(x)`` across field | nitride | field.

    ``x_um`` the lateral coordinate (µm, ``0`` at the active-stripe centre, mirrored to both field
    edges); ``t_ox_um`` the local field-oxide thickness ``grow_oxide · m(x)`` (µm) — thick in the field,
    tapering through the **bird's beak** to ~0 over the surviving active area. ``field_ox_um`` the
    planar plateau (the ``grow_oxide`` seam); ``drawn_active_um`` the nitride width; ``active_width_um``
    the surviving active width (``0`` ⇒ pinched off). Plain arrays/scalars — the loose-coupling currency.
    """

    x_um: np.ndarray
    t_ox_um: np.ndarray
    field_ox_um: float
    drawn_active_um: float
    active_width_um: float

    @property
    def pinched_off(self) -> bool:
        """Whether the two beaks merged and the active island was fully consumed (``active_width ≤ 0``)."""
        return self.active_width_um <= 0.0


def field_oxide_profile(
    drawn_active_um: float, field_ox_um: float, *,
    beak_factor: float = BEAK_DIFFUSION_FACTOR,
    threshold: float = ACTIVE_MODULATION_THRESHOLD,
    nx: int = 220, ny: int = 120, n_steps: int = 120,
) -> FieldOxideProfile:
    """The full field | nitride | field oxide cross-section — the classic bird's-beak profile.

    Solves the two-field half-cell (active-stripe centre at ``x=0``) and mirrors it to produce the full
    symmetric cross-section: thick field oxide (``= grow_oxide`` in the plateau, the seam), tapering
    through the beak into the thin/zero active region. ``t_ox(x) = grow_oxide · m(x)`` with the open
    field pinned to ``m = 1``.
    """
    x, _, m, active_w = _active_width_solve(
        drawn_active_um, field_ox_um,
        beak_factor=beak_factor, threshold=threshold, nx=nx, ny=ny, n_steps=n_steps,
    )
    gate_half = 0.5 * drawn_active_um
    open_mask = x >= gate_half
    m_surf = _surface_line(open_mask, m)               # exact 1 in the field, diffused under the nitride
    # Mirror the right half [0, Lx] about x=0 into a full cross-section [-Lx, Lx].
    x_full = np.concatenate([-x[::-1], x])
    m_full = np.concatenate([m_surf[::-1], m_surf])
    t_ox_full = field_ox_um * m_full
    return FieldOxideProfile(
        x_um=x_full, t_ox_um=t_ox_full, field_ox_um=field_ox_um,
        drawn_active_um=drawn_active_um, active_width_um=active_w,
    )


# --------------------------------------------------------------------------- #
# 4. The bundled LOCOS cross-section (the two ways to the surviving active width)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LocosCrossSection:
    """A LOCOS isolation read two ways: the single-edge subtraction and the honest two-field solve.

    Geometry (all **µm**): ``drawn_active`` the drawn nitride width; ``field_ox`` the planar field-oxide
    thickness (the ``grow_oxide`` seam); ``beak`` the single-edge bird's-beak encroachment;
    ``active_approx = drawn_active − 2·beak`` (the textbook subtraction, floored at 0) and ``active_true``
    the two-field junction-to-junction solve; ``sti_active = drawn_active`` (the successor — no beak).
    ``pinched_off`` whether the beaks merged (``active_true ≤ 0``). Plain scalars — loose-coupling
    currency (ADR 0002)."""

    drawn_active_um: float
    field_ox_um: float
    beak_um: float
    active_approx_um: float
    active_true_um: float

    @property
    def sti_active_um(self) -> float:
        """The STI successor's active width — the drawn width itself (vertical walls, no beak)."""
        return self.drawn_active_um

    @property
    def pinched_off(self) -> bool:
        """Whether LOCOS pinched the active island off (the two beaks merged, ``active_true ≤ 0``)."""
        return self.active_true_um <= 0.0

    @property
    def shortening_frac(self) -> float:
        """Fractional active-width loss ``(drawn − active_true) / drawn`` — what the beak costs."""
        return (self.drawn_active_um - self.active_true_um) / self.drawn_active_um


def locos_cross_section(
    drawn_active_um: float, *,
    ambient: str = FIELD_AMBIENT, T_celsius: float = FIELD_T_CELSIUS,
    t_minutes: float = FIELD_T_MINUTES, orientation: str = FIELD_ORIENTATION,
    beak_factor: float = BEAK_DIFFUSION_FACTOR,
    threshold: float = ACTIVE_MODULATION_THRESHOLD,
    nx: int = 220, ny: int = 120, n_steps: int = 120,
) -> LocosCrossSection:
    """Assemble a LOCOS cross-section: field oxidation → bird's beak → the surviving active width.

    Grows the field oxide with :func:`chip.oxidation.grow_oxide` (the recipe, unchanged), reads the
    beak two ways — the textbook ``drawn − 2·L_beak`` (single isolated edge) and the honest two-field
    ``active_true`` (which the merge drives to zero) — and bundles both. The two agree at **wide
    stripes** (the independent cross-check on the encroachment); as the stripe narrows the two-field
    solve pinches off *earlier* than the subtraction, because the opposing beaks' oxidant fields overlap
    (the genuinely-2-D merge) — its direction robust, the exact width flagged.
    """
    field_ox = field_oxide_thickness_um(ambient, T_celsius, t_minutes, orientation)
    beak = birds_beak_length_um(field_ox, beak_factor=beak_factor, threshold=threshold,
                                nx=nx, ny=ny, n_steps=n_steps)
    active_approx = max(drawn_active_um - 2.0 * beak, 0.0)
    active_true = active_width_um(drawn_active_um, field_ox, beak_factor=beak_factor,
                                  threshold=threshold, nx=nx, ny=ny, n_steps=n_steps)
    return LocosCrossSection(
        drawn_active_um=drawn_active_um, field_ox_um=field_ox, beak_um=beak,
        active_approx_um=active_approx, active_true_um=active_true,
    )
