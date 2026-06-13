"""Killer-defect placement (G3) — determinism, area-consistency, and convergence to the cited law.

The stochastic side of the defect-limited yield: :mod:`fab_game.defects` scatters killer particles
on the die map, and these mechanics invariants (ADR 0005 §5) pin it without asserting magnitudes:

* **Determinism** — a fixed (seed, density) reproduces the defect map exactly; a different seed
  moves it; the disabled / clean-line cases place nothing (the seam, covered in ``test_seam``).
* **Propagation actually wired (the load-bearing G3 leg)** — the empirical kill fraction over many
  realizations **converges to the cited closed form** ``1 − exp(−D₀·A_die)`` (:mod:`chip.wafer_prep`),
  against the **byte-identical** :func:`fab_game.state.die_area_cm2`. This ties the game's random
  placement to the validated physics — if the area were inconsistent, or the placement weren't
  Poisson, this fails. (Per [[chip-notebook-flake]] the repo is flake-sensitive, so this lives in
  **one** seeded, tolerance-checked place — not scattered RNG tests.)
* **Killer defect → functional fail** — a die that caught a particle is dead functionally (its
  parametric device may read fine), distinct from a litho image that never resolved.
"""
from __future__ import annotations

import numpy as np

from chip import wafer_prep as wp

from fab_game import DEFAULT_RECIPE, NO_VARIATION, Variation, run_line, wafer_yield
from fab_game.defects import scatter_defects
from fab_game.recipe import Recipe, WaferPrepKnobs
from fab_game.spec import DEFAULT_SPECS
from fab_game.state import Die, build_die_map, die_area_cm2


_GRID = 7
_DIAM = 200.0


def _dies():
    return build_die_map(grid_n=_GRID)


# --------------------------------------------------------------------------- #
# Determinism of the placement
# --------------------------------------------------------------------------- #
def test_scatter_is_reproducible_under_seed():
    dies = _dies()
    a = scatter_defects(dies, defect_density=0.1, grid_n=_GRID, wafer_diameter_mm=_DIAM,
                        rng=np.random.default_rng(4), enabled=True)
    b = scatter_defects(dies, defect_density=0.1, grid_n=_GRID, wafer_diameter_mm=_DIAM,
                        rng=np.random.default_rng(4), enabled=True)
    assert a == b                                             # same seed → identical map (positions too)
    c = scatter_defects(dies, defect_density=0.1, grid_n=_GRID, wafer_diameter_mm=_DIAM,
                        rng=np.random.default_rng(5), enabled=True)
    assert a != c                                             # a different seed moves the defects


def test_defects_land_inside_their_die_cell():
    # Every placed particle sits within the cell of the die it was assigned to (the placement box).
    from fab_game.state import die_cell_bounds
    dies = _dies()
    out = scatter_defects(dies, defect_density=0.4, grid_n=_GRID, wafer_diameter_mm=_DIAM,
                          rng=np.random.default_rng(0), enabled=True)
    for site, events in out.items():
        x_lo, x_hi, y_lo, y_hi = die_cell_bounds(site, _GRID)
        for e in events:
            assert x_lo <= e.x <= x_hi and y_lo <= e.y <= y_hi
            assert e.killer is True


# --------------------------------------------------------------------------- #
# Area consistency + convergence to the cited Poisson law (propagation wired)
# --------------------------------------------------------------------------- #
def test_die_area_is_the_single_consistent_definition():
    # The ONE area: (cell_fraction · wafer_radius_cm)². Both placement and the closed form use it.
    A = die_area_cm2(_GRID, _DIAM)
    radius_cm = _DIAM / 2.0 / 10.0
    edge_cm = (2.0 / _GRID) * radius_cm
    assert A == edge_cm * edge_cm


def test_mean_defects_per_die_matches_density_times_area():
    # The placement's effective rate is D₀·A_die (the Poisson mean) — area-consistency, directly.
    dies = _dies()
    D0 = 0.15
    A = die_area_cm2(_GRID, _DIAM)
    rng = np.random.default_rng(0)
    counts = []
    for _ in range(400):
        out = scatter_defects(dies, defect_density=D0, grid_n=_GRID, wafer_diameter_mm=_DIAM,
                              rng=rng, enabled=True)
        counts.extend(len(v) for v in out.values())
    assert np.mean(counts) == approx_loose(D0 * A, tol=0.03)   # mean count → λ = D₀·A


def test_empirical_kill_rate_converges_to_the_poisson_law():
    # THE G3 propagation-wired leg: the empirical zero-defect (survival) fraction over many seeded
    # realizations → exp(−D₀·A_die), the cited Murphy/Poisson closed form, against the byte-identical
    # die area. Seeded + tolerance-checked (the value below was verified to sit well inside tol).
    dies = _dies()
    D0 = 0.15
    A = die_area_cm2(_GRID, _DIAM)
    survival_closed = wp.poisson_yield(D0, A)                 # exp(−D₀·A)
    rng = np.random.default_rng(20260613)
    survived = total = 0
    for _ in range(400):
        out = scatter_defects(dies, defect_density=D0, grid_n=_GRID, wafer_diameter_mm=_DIAM,
                              rng=rng, enabled=True)
        for events in out.values():
            total += 1
            survived += len(events) == 0
    empirical = survived / total
    assert empirical == approx_loose(survival_closed, tol=0.02)


def test_higher_density_kills_more_on_average():
    # Propagation direction: a dirtier line (higher D₀) gives a not-better functional yield. Averaged
    # over seeds (the expectation is monotone; a single realization may wiggle).
    dies = _dies()
    A = die_area_cm2(_GRID, _DIAM)

    def mean_kill_fraction(D0):
        rng = np.random.default_rng(7)
        killed = total = 0
        for _ in range(120):
            out = scatter_defects(dies, defect_density=D0, grid_n=_GRID, wafer_diameter_mm=_DIAM,
                                  rng=rng, enabled=True)
            for events in out.values():
                total += 1
                killed += len(events) > 0
        return killed / total

    fractions = [mean_kill_fraction(D0) for D0 in (0.02, 0.1, 0.3)]
    assert fractions == sorted(fractions)                    # more density → more kills


# --------------------------------------------------------------------------- #
# Killer defect → functional fail (the wiring), and the clean-line seam
# --------------------------------------------------------------------------- #
def test_no_variation_run_places_no_defects():
    w = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=5)
    assert all(d.defects == () and d.killed_by_defect is False for d in w.dies)


def test_killer_defect_is_a_functional_fail_in_the_verdict():
    # A die that caught a particle fails functionally — short-circuits before the parametric windows,
    # even with an otherwise in-spec device (the transistor exists but is killed).
    from fab_game.state import DefectEvent
    healthy = Die(site=(0, 0), radius_frac=0.0, t_ox_um=0.014, cd_nm=167.0, nils=4.6,
                  resolved=True, V_t=0.55, i_dsat=3.3e-3, killed_by_defect=False)
    assert DEFAULT_SPECS.verdict(healthy).passed
    hit = replace_die(healthy, defects=(DefectEvent(0.1, 0.1),), killed_by_defect=True)
    v = DEFAULT_SPECS.verdict(hit)
    assert v.failed and any("killer particle" in r for r in v.reasons)


def test_dirty_line_drops_yield_with_defect_reasons():
    # End to end: a dirty line scatters killers → some dies fail functionally with the defect reason.
    dirty = Recipe(wafer_prep=WaferPrepKnobs(defect_density=0.3))
    w = run_line(dirty, seed=1, variation=Variation(), grid_n=7)
    assert wafer_yield(w) < 1.0
    dead = [d for d in w.dies if d.verdict.failed]
    assert any(d.killed_by_defect and any("killer particle" in r for r in d.verdict.reasons)
               for d in dead)


# --------------------------------------------------------------------------- #
# Small helpers (kept local — not worth a conftest)
# --------------------------------------------------------------------------- #
def approx_loose(value, tol):
    import pytest
    return pytest.approx(value, abs=tol)


def replace_die(die, **updates):
    from dataclasses import replace
    return replace(die, **updates)
