"""The stochastic defect placement — killer particles scattered on the die map (G3, plan §4).

The deterministic core (the cited yield law ``Y = exp(−D₀·A)``, :mod:`chip.wafer_prep`) says *how
many* killer defects a die catches on average; this layer draws the actual **realization** — where
the particles land — from the one seeded RNG, so a run is reproducible (the roguelike "seed"). A die
that catches ≥1 killer defect is dead **functionally**.

Why per-die Poisson is the *global* wafer process (and why that matters)
-----------------------------------------------------------------------
A wafer-wide Poisson defect process at density ``D₀`` restricted to one die's cell is itself Poisson
with mean ``D₀·A_die`` (the **superposition / restriction** property of a Poisson process), with the
points uniform inside the cell. So drawing, per die in fixed order, ``n_i ~ Poisson(D₀·A_die)``
particles placed uniformly in that die's cell **is** a valid realization of the global wafer scatter
— and it makes two things exact:

* the per-die survival probability is ``exp(−D₀·A_die)`` against the **byte-identical** area
  (:func:`fab_game.state.die_area_cm2`) the closed form uses — the convergence the mechanics test
  checks (the placement is *wired* to the cited law); and
* it sidesteps the off-wafer / edge-excluded discard bookkeeping a global (x, y) scatter would need
  (we only ever draw inside kept dies), so the area assumption stays consistent.

**Determinism contract.** Particles are drawn in **fixed die order** (the same order the per-die
perturbations use), each die drawing one Poisson count then ``2·n`` uniforms for the positions. When
``enabled`` is False the scatter returns empty **without touching the RNG** — so a zero-variation
run places no defects (the seam survives, and ``run_batch``'s ``NO_VARIATION`` isolates the Scheil
signal). ``D₀`` is a recipe knob (how dirty the line is); *whether* to realize the scatter is the
stochastic layer's ``enabled`` switch — both off ⇒ no defects.

The density magnitudes are **house, flagged** (ADR 0005 §5: ``fab_game`` is mechanics, not
magnitudes); the *law* the placement obeys is the cited Murphy/Poisson form.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from .state import DefectEvent, Die, die_area_cm2, die_cell_bounds


def scatter_defects(
    dies: tuple[Die, ...],
    *,
    defect_density: float,
    grid_n: int,
    wafer_diameter_mm: float,
    rng: np.random.Generator,
    enabled: bool = True,
    density_fn: Callable[[Die], float] | None = None,
) -> dict[tuple[int, int], tuple[DefectEvent, ...]]:
    """Draw the killer-defect realization per die → ``{site: (DefectEvent, …)}`` (fixed die order).

    Each die catches ``n ~ Poisson(D₀·A_die)`` killer particles (``A_die`` the single
    :func:`fab_game.state.die_area_cm2`), placed uniformly inside its cell
    (:func:`fab_game.state.die_cell_bounds`). With ``enabled=False`` returns an empty map for every die
    and **does not consume the RNG** (the seam, and a clean line stays byte-identical).

    ``density_fn`` (the A2/OSF-ring radial path) makes the killer density **per die** — ``density_fn(d)``
    in place of the scalar ``defect_density`` (so a radial ``D₀(r)`` keyed on ``d.radius_frac`` scatters
    a vacancy core / clean rim). When ``density_fn is None`` the **uniform scalar path** is taken,
    *byte-identical* to before: a non-positive ``defect_density`` returns empty without touching the RNG.
    A per-die ``λ ≤ 0`` draws nothing (no RNG) — so the radial map is self-consistent and a clean die
    stays clean. Consuming the RNG in the given ``dies`` order is the determinism contract (unchanged).
    """
    if not enabled:
        return {d.site: () for d in dies}

    area = die_area_cm2(grid_n, wafer_diameter_mm)
    if density_fn is None:
        if defect_density <= 0.0:
            return {d.site: () for d in dies}     # the uniform seam — no RNG, byte-identical
        density_fn = lambda _d: defect_density    # noqa: E731 — uniform density for every die

    out: dict[tuple[int, int], tuple[DefectEvent, ...]] = {}
    for d in dies:
        lam = density_fn(d) * area
        n = int(rng.poisson(lam)) if lam > 0.0 else 0
        x_lo, x_hi, y_lo, y_hi = die_cell_bounds(d.site, grid_n)
        events = tuple(
            DefectEvent(x=float(rng.uniform(x_lo, x_hi)),
                        y=float(rng.uniform(y_lo, y_hi)), killer=True)
            for _ in range(n)
        )
        out[d.site] = events
    return out
