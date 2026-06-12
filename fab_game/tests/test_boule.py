"""G2 mechanics invariants (ADR 0005 §5) — the boule wired into the line.

The G2 build adds the first new front-of-line physics (:mod:`chip.czochralski`, Scheil
segregation) under the harness. These tests are the **mechanics** side of the split (the cited
physics is validated in ``chip/tests/test_czochralski.py``); they check that the boule is wired
correctly, not the magnitudes:

* **Seam** — the seed slice (``slice_z=0``) reproduces ``demo_device``'s ``CHANNEL_N_A`` *exactly*,
  so growing the substrate from a boule does not move the physics at the default knobs.
* **Propagation** — down the boule the rising Scheil ``N_A`` flows to a rising ``V_t`` (and falling
  resistivity); a strictly-worse-resolved field (more doping → higher V_t) never produces a
  better downstream observable. If the wire were cut (device ignoring ``channel_N_A``), V_t would
  not move.
* **Determinism / no new RNG** — Scheil is a closed form, so the boule adds no randomness: a batch
  is reproducible and (under no variation) seed-independent.
* **Bookkeeping** — each wafer bins good+bad=total; the batch sweeps exactly ``n_wafers`` slices and
  yield is monotone non-increasing down the boule (once V_t leaves the window it stays out).
"""
from __future__ import annotations

import numpy as np

from chip import demo_device

from fab_game import DEFAULT_RECIPE, NO_VARIATION, Variation, run_batch, run_line, wafer_yield
from fab_game.recipe import CzochralskiKnobs, Recipe


# --------------------------------------------------------------------------- #
# Seam — the seed slice reproduces demo_device exactly (the harness adds no physics)
# --------------------------------------------------------------------------- #
def test_seed_slice_is_the_demo_channel_doping_bit_for_bit():
    """At slice_z=0 the boule hands back demo_device's CHANNEL_N_A exactly (1e17 > 2**53 → identity)."""
    assert DEFAULT_RECIPE.czochralski.slice_z == 0.0
    assert DEFAULT_RECIPE.channel_N_A == demo_device.CHANNEL_N_A == 1.0e17
    assert DEFAULT_RECIPE.boule.slice(0.0).N_A == 1.0e17


def test_seed_wafer_carries_the_substrate_characterization():
    """The grown wafer records its slice + resistivity (the new G2 substrate fields), seed exact."""
    w = run_line(DEFAULT_RECIPE, seed=0, variation=NO_VARIATION, grid_n=1)
    assert w.slice_z == 0.0
    assert w.channel_N_A == 1.0e17
    assert 0.1 < w.resistivity_ohm_cm < 0.5            # ~0.2 Ω·cm for 1e17 boron (the textbook band)


def test_a_deeper_slice_changes_the_substrate():
    """Off the seed end the substrate is more doped and lower-resistivity (k<1 → solute piles up)."""
    deep = Recipe(czochralski=CzochralskiKnobs(slice_z=0.8))
    assert deep.channel_N_A > DEFAULT_RECIPE.channel_N_A
    assert deep.substrate_resistivity_ohm_cm < DEFAULT_RECIPE.substrate_resistivity_ohm_cm


# --------------------------------------------------------------------------- #
# Propagation — the boule's rising N_A flows to a rising V_t (the wire is live)
# --------------------------------------------------------------------------- #
def _mean_vt(wafer) -> float:
    return float(np.mean([d.V_t for d in wafer.dies if d.V_t is not None]))


def test_scheil_doping_rises_monotonically_down_the_boule():
    """The wired substrate doping is the Scheil profile sampled down the boule — strictly rising (k<1)."""
    b = run_batch(DEFAULT_RECIPE, n_wafers=8, z_max=0.85)
    na = np.array(b.channel_N_As)
    rho = np.array(b.resistivities)
    assert np.all(np.diff(na) > 0.0)                   # solute piles up toward the tail
    assert np.all(np.diff(rho) < 0.0)                  # more doping → lower resistivity


def test_rising_substrate_doping_raises_vt():
    """Down the boule the device V_t rises strictly — the substrate the boule handed it reaches V_t.

    This is the propagation wire: if device_step ignored channel_N_A, V_t would be flat across the
    batch. The direction is guaranteed by chip.device (dV_t/dN_A > 0).
    """
    b = run_batch(DEFAULT_RECIPE, n_wafers=8, z_max=0.85)
    vts = np.array([_mean_vt(w) for w in b.wafers])
    assert np.all(np.diff(vts) > 0.0)


# --------------------------------------------------------------------------- #
# Determinism — Scheil is a closed form, so the boule adds no RNG
# --------------------------------------------------------------------------- #
def test_batch_is_reproducible():
    """A batch under a fixed (seed, recipe) reproduces exactly (the determinism contract)."""
    a = run_batch(DEFAULT_RECIPE, n_wafers=6, z_max=0.85, seed=3, variation=Variation())
    c = run_batch(DEFAULT_RECIPE, n_wafers=6, z_max=0.85, seed=3, variation=Variation())
    assert a.channel_N_As == c.channel_N_As
    assert a.yields == c.yields
    assert [list(w.dies) for w in a.wafers] == [list(w.dies) for w in c.wafers]


def test_boule_path_consumes_no_rng():
    """Under NO_VARIATION the batch is seed-independent — the Scheil/boule path draws no randomness."""
    a = run_batch(DEFAULT_RECIPE, n_wafers=6, z_max=0.85, seed=1, variation=NO_VARIATION)
    c = run_batch(DEFAULT_RECIPE, n_wafers=6, z_max=0.85, seed=999, variation=NO_VARIATION)
    assert a.channel_N_As == c.channel_N_As
    assert [_mean_vt(w) for w in a.wafers] == [_mean_vt(w) for w in c.wafers]


# --------------------------------------------------------------------------- #
# Bookkeeping — the batch sweep accounts cleanly
# --------------------------------------------------------------------------- #
def test_batch_bins_every_die_and_sweeps_every_slice():
    """Each wafer bins good+bad=total; the batch holds exactly n_wafers slices in z order."""
    n = 7
    b = run_batch(DEFAULT_RECIPE, n_wafers=n, z_max=0.85)
    assert len(b.wafers) == len(b.z_positions) == n
    assert list(b.z_positions) == sorted(b.z_positions)      # in axial order
    for w in b.wafers:
        good = sum(d.verdict.passed for d in w.dies)
        bad = sum(d.verdict.failed for d in w.dies)
        assert good + bad == w.n_dies
        assert wafer_yield(w) == good / w.n_dies


def test_yield_is_monotone_non_increasing_down_the_boule():
    """Once the rising V_t leaves the upper spec it stays out → yield never recovers toward the tail."""
    b = run_batch(DEFAULT_RECIPE, n_wafers=10, z_max=0.9)
    ys = np.array(b.yields)
    assert np.all(np.diff(ys) <= 0.0)
    assert ys[0] == 1.0 and ys[-1] < 1.0                     # seed passes; the tail is scrapped
