"""Historical-modes A1 — the dose-control wall (``chip.doping_history``).

The triad, per ``docs/plans/historical-modes-a1.md``:

  * **tight** — the constant sources' surface concentration IS the species' solid solubility *by
    reference* (the pinning cannot drift); the predep dose identity; and the **seam** (a constant source
    at solubility reproduces :func:`chip.diffusion_dopant.predeposit` bit-for-bit);
  * **flagged** — the dose-control wall, asserted by **sign across an explicit ``(T_predep, t_min)`` box**
    (``t_min``/``T_predep`` are house inputs, NOT a structural law).

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import math

import numpy as np
import pytest

from chip import diffusion_dopant as dd
from chip import doping_history as dh

_CONSTANT_SOURCES = [k for k, s in dh.SOURCES.items() if s.source_type == "constant"]


# --------------------------------------------------------------------------- #
# Tight legs
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("key", _CONSTANT_SOURCES)
def test_constant_surface_conc_is_solubility_by_reference(key):
    """A constant source's surface_conc IS the species' Trumbore solubility (same float — cannot drift)."""
    src = dh.SOURCES[key]
    assert src.surface_conc == dd.DOPANTS[src.species].N_solid_solubility


def test_limited_source_surface_conc_is_none():
    """A limited source is dose-set, not solubility-pinned — no fixed surface concentration."""
    assert dh.SOURCES["SOG"].surface_conc is None


def test_predep_dose_identity():
    """run_source's constant-source grid dose matches the analytic predep dose 1.128·N_s·√(Dt)."""
    grid = dd.uniform_grid(3.0 * dd.CM_PER_UM, 600)
    src = dh.SOURCES["BBr3"]
    t_s = 900.0
    sp = dh.run_source(grid, src, T_predep_celsius=950.0, t_predep_s=t_s)
    analytic = dd.predep_dose(src.surface_conc, dd.diffusivity(src.species, 950.0), t_s)
    assert sp.dose == pytest.approx(analytic, rel=0.02)   # grid vs analytic (discretization only)


@pytest.mark.parametrize("key", _CONSTANT_SOURCES)
def test_seam_constant_source_reproduces_predeposit_bit_for_bit(key):
    """The seam: a constant source at solubility == the default predeposit, byte-identical (no drift)."""
    grid = dd.uniform_grid(3.0 * dd.CM_PER_UM, 600)
    src = dh.SOURCES[key]
    sp = dh.run_source(grid, src, T_predep_celsius=950.0, t_predep_s=900.0)
    ref = dd.predeposit(grid, src.species, 950.0, 900.0)   # default N_surface = solubility
    assert np.array_equal(sp.N, ref.N)


def test_limited_source_conserves_dose_and_undercuts_solubility():
    """The limited source meters its dose exactly and floods BELOW solubility (the workaround's reach)."""
    grid = dd.uniform_grid(3.0 * dd.CM_PER_UM, 600)
    Q = 5.0e12
    lp = dh.run_source(grid, dh.SOURCES["SOG"], T_predep_celsius=950.0, t_predep_s=900.0, dose=Q)
    assert lp.dose == pytest.approx(Q, rel=1e-3)
    assert lp.surface_conc < dd.DOPANTS["B"].N_solid_solubility


# --------------------------------------------------------------------------- #
# Flagged leg — the dose-control wall (sign across an explicit box, NOT a bare magnitude)
# --------------------------------------------------------------------------- #
# The box is FLAGGED house inputs: t_min = the smallest reproducible predep time on the steep √t curve,
# T_predep = the predep-temperature range. The wall is the claim that the constant-source dose FLOOR sits
# above the light V_t-adjust target ACROSS this whole box — a sign-robust-across-a-stated-box claim, not a
# structural law. (Asserting a single floor > 5e11 would bake a house t_min in as physics — avoided here.)
_BOX_T_CELSIUS = (800.0, 900.0)
_BOX_T_MIN_S = (0.1, 1.0)


@pytest.mark.parametrize("key", _CONSTANT_SOURCES)
@pytest.mark.parametrize("T", _BOX_T_CELSIUS)
@pytest.mark.parametrize("t_min", _BOX_T_MIN_S)
def test_dose_control_wall_sign_holds_across_the_box(key, T, t_min):
    """Every constant source's controllable-dose floor stays ABOVE the V_t-adjust target across the box."""
    src = dh.SOURCES[key]
    floor = dh.predep_dose_floor(src, T_predep_celsius=T, t_min_s=t_min)
    assert floor > dh.VT_ADJUST_DOSE           # the wall: predep cannot reproducibly reach the light dose


def test_implant_reaches_below_the_constant_floor():
    """Implant meters the V_t-adjust dose electrically — below every constant floor in the box (the point)."""
    floor_min = min(
        dh.predep_dose_floor(dh.SOURCES[k], T_predep_celsius=T, t_min_s=t)
        for k in _CONSTANT_SOURCES for T in _BOX_T_CELSIUS for t in _BOX_T_MIN_S
    )
    implant = dh.implant_reach(dh.VT_ADJUST_DOSE, energy_keV=15.0, species="B")
    assert implant.dose == dh.VT_ADJUST_DOSE
    assert implant.dose < floor_min            # the decoupled knob reaches where predep cannot


def test_dose_control_margin_matches_floor_over_target():
    """dose_control_margin is exactly the floor/target ratio (and > 1 = the wall)."""
    src = dh.SOURCES["BBr3"]
    T, t_min = 900.0, 1.0
    margin = dh.dose_control_margin(src, T_predep_celsius=T, t_min_s=t_min)
    floor = dh.predep_dose_floor(src, T_predep_celsius=T, t_min_s=t_min)
    assert margin == pytest.approx(floor / dh.VT_ADJUST_DOSE)
    assert margin > 1.0


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def test_predep_dose_floor_rejects_limited_source():
    """A floor is meaningless for a dose-metered limited source — it raises rather than fabricate one."""
    with pytest.raises(ValueError, match="constant source"):
        dh.predep_dose_floor(dh.SOURCES["SOG"], T_predep_celsius=900.0, t_min_s=1.0)


def test_limited_source_requires_explicit_dose():
    """run_source on a limited source without a dose raises (the dose IS the source)."""
    grid = dd.uniform_grid(3.0 * dd.CM_PER_UM, 600)
    with pytest.raises(ValueError, match="explicit deposited dose"):
        dh.run_source(grid, dh.SOURCES["SOG"], T_predep_celsius=900.0, t_predep_s=900.0)


def test_source_validation_rejects_bad_species_and_type():
    """The dataclass guards its species and source_type (the established __post_init__ idiom)."""
    with pytest.raises(ValueError, match="species"):
        dh.DopingSource("bogus", "Xx", "constant")
    with pytest.raises(ValueError, match="source_type"):
        dh.DopingSource("bogus", "B", "sputtered")
