"""G5 mechanics — the etch/deposition step is wired, propagates, and stays deterministic.

The physics (etch bias, the void criterion) is pinned in ``chip/tests/test_etch_deposition.py``; these
are the **game** invariants (ADR 0005 §5): the etched CD overwrites the currency the device reads (so a
worse etch knob ripples to ``I_Dsat``, never the resist CD); a non-conformal deposition voids a die
**functionally**; the etch step degrades gracefully on an unresolved image; and the optional etch-rate
non-uniformity is deterministic under a seed *and* draws no RNG when off (the byte-identity that keeps
the G1–G4 banked demos unchanged — the seam side of it is in ``test_seam.py``).
"""
from __future__ import annotations

import numpy as np

from fab_game import (
    DEFAULT_RECIPE,
    NO_VARIATION,
    EtchDepositionKnobs,
    Variation,
    run_line,
    wafer_yield,
)
from fab_game.recipe import LithoKnobs, Recipe
from fab_game.state import Die
from fab_game.steps import etch_deposition_step
from fab_game.variation import DiePerturbation


def _center(wafer):
    return wafer.dies[0]


# --------------------------------------------------------------------------- #
# The seam at the step level: default knobs are the identity transfer
# --------------------------------------------------------------------------- #
def test_default_etch_is_identity_on_the_cd():
    """At the default knobs (perfectly anisotropic, conformal) the etch leaves the CD bit-for-bit and
    voids nothing — the step is the identity the seam relies on."""
    d = Die(site=(0, 0), radius_frac=0.0, cd_nm=167.3, resolved=True)
    out = etch_deposition_step(d, EtchDepositionKnobs(), pitch_nm=300.0, pert=DiePerturbation())
    assert out.cd_nm == 167.3                                   # == , not approx — the seam is exact
    assert out.voided is False


# --------------------------------------------------------------------------- #
# Propagation: the etched CD (not the resist CD) is what the device reads
# --------------------------------------------------------------------------- #
def test_overetch_shrinks_cd_and_raises_idsat():
    """A non-anisotropic + over-etched recipe shrinks the gate CD below the printed CD → a shorter
    channel → strictly more I_Dsat (∝ W/L). The device reads the *etched* CD, so the wire carries."""
    base = run_line(DEFAULT_RECIPE, variation=NO_VARIATION, grid_n=1)
    biased = run_line(
        Recipe(etch_deposition=EtchDepositionKnobs(anisotropy=0.9, over_etch_frac=0.4)),
        variation=NO_VARIATION, grid_n=1)
    assert _center(biased).cd_nm < _center(base).cd_nm         # the etch bias shrank the gate CD
    assert _center(biased).i_dsat > _center(base).i_dsat       # shorter channel → more drive current
    # The resist CD is preserved in the etch record (provenance), distinct from the etched cd_nm.
    etch_rec = next(r for r in _center(biased).history if r.step == "etch_deposition")
    assert etch_rec.outputs["resist_cd_nm"] > _center(biased).cd_nm


def test_extreme_overetch_collapses_cd_out_of_window():
    """Enough over-etch drives the gate CD below the CD floor → a parametric fail on the centre die."""
    w = run_line(
        Recipe(etch_deposition=EtchDepositionKnobs(anisotropy=0.8, over_etch_frac=0.8)),
        variation=NO_VARIATION, grid_n=1)
    d = _center(w)
    assert d.cd_nm < 150.0                                      # below the DEFAULT_SPECS CD floor
    assert d.verdict.failed and any("CD" in r for r in d.verdict.reasons)


# --------------------------------------------------------------------------- #
# The deposition void — a functional kill (parallel to a killer particle)
# --------------------------------------------------------------------------- #
def test_poor_step_coverage_voids_the_die_functionally():
    """A poor PVD step coverage cannot fill the gate gap (AR ≈ 1.13 > AR_crit ≈ 0.43) → the die fails
    **functionally** (a void), not parametrically — its V_t/I_Dsat may read fine."""
    w = run_line(
        Recipe(etch_deposition=EtchDepositionKnobs(conformality=0.3)),
        variation=NO_VARIATION, grid_n=1)
    d = _center(w)
    assert d.voided is True
    assert d.verdict.failed and any("void" in r.lower() for r in d.verdict.reasons)
    assert wafer_yield(w) == 0.0
    # A conformal CVD fills the same gap → no void → the die is good (the contrast).
    good = run_line(Recipe(etch_deposition=EtchDepositionKnobs(conformality=0.9)),
                    variation=NO_VARIATION, grid_n=1)
    assert _center(good).voided is False and wafer_yield(good) == 1.0


def test_void_is_named_in_the_diagnosis():
    """The failure trail names the void as a non-conformal-fill kill (the 'why did this die?')."""
    from fab_game import diagnose

    w = run_line(Recipe(etch_deposition=EtchDepositionKnobs(conformality=0.3)),
                 variation=NO_VARIATION, grid_n=1)
    text = diagnose(_center(w))
    assert "VOID" in text and "aspect ratio" in text


# --------------------------------------------------------------------------- #
# Graceful degradation: an unresolved image passes through to a device refusal
# --------------------------------------------------------------------------- #
def test_unresolved_image_passes_through_etch_to_a_refusal():
    """If litho did not resolve, the etch passes through (voided stays None) and the device refuses —
    the dead state propagates rather than the etch step crashing on a missing CD."""
    dead = Die(site=(0, 0), radius_frac=0.0, cd_nm=None, resolved=False)
    out = etch_deposition_step(dead, EtchDepositionKnobs(), pitch_nm=300.0, pert=DiePerturbation())
    assert out.voided is None                                  # a gap, not a fake False
    rec = out.history[-1]
    assert rec.step == "etch_deposition" and "skipped" in rec.outputs


def test_runaway_overetch_is_a_functional_kill_not_a_crash():
    """An over-etch that would consume the whole gate line is a functional kill (voided), not a raise —
    the harness degrades like litho's resolved=False."""
    thin = Die(site=(0, 0), radius_frac=0.0, cd_nm=40.0, resolved=True)
    out = etch_deposition_step(
        thin, EtchDepositionKnobs(anisotropy=0.0, over_etch_frac=1.0, film_thickness_nm=200.0),
        pitch_nm=300.0, pert=DiePerturbation())
    assert out.voided is True
    assert "functional_fail" in out.history[-1].outputs


# --------------------------------------------------------------------------- #
# Etch-rate non-uniformity: deterministic under a seed, conditional on its σ
# --------------------------------------------------------------------------- #
def test_etch_variation_is_reproducible_under_a_seed():
    """Switching on the etch-rate σ spreads the CD across the die map, reproducibly (a roguelike seed)."""
    var = Variation(etch_bias_sigma_frac=0.05)
    recipe = Recipe(etch_deposition=EtchDepositionKnobs(anisotropy=0.9))
    a = run_line(recipe, seed=7, variation=var, grid_n=5)
    b = run_line(recipe, seed=7, variation=var, grid_n=5)
    cds_a = [d.cd_nm for d in a.dies]
    cds_b = [d.cd_nm for d in b.dies]
    assert cds_a == cds_b                                      # bit-for-bit reproducible
    # The etch jitter actually spreads the CD (a non-ideal etch + σ → die-to-die CD variation).
    assert np.std(cds_a) > 0.0


def test_etch_sigma_off_draws_no_rng():
    """With the default etch σ = 0, the 4th draw never fires — so the RNG stream is byte-identical to a
    run without the etch channel (the byte-identity that keeps the G1–G4 banked demos unchanged)."""
    var = Variation()                                         # etch_bias_sigma_frac defaults to 0.0
    die = Die(site=(0, 0), radius_frac=0.5)
    rng_a = np.random.default_rng(99)
    rng_b = np.random.default_rng(99)
    # Drawing a perturbation consumes exactly the 3 pre-G5 normals; a 4th draw on each generator must
    # then agree (i.e. the perturbation drew the same count from both).
    var.perturbation(die, rng_a)
    # Reproduce the 3 pre-G5 draws by hand on the second generator.
    rng_b.normal(); rng_b.normal(); rng_b.normal()
    assert rng_a.normal() == rng_b.normal()                  # streams still aligned → no 4th draw fired
    # And turning σ on DOES consume a 4th draw (the channel is real when enabled).
    var_on = Variation(etch_bias_sigma_frac=0.05)
    rng_c = np.random.default_rng(99)
    rng_d = np.random.default_rng(99)
    var_on.perturbation(die, rng_c)
    for _ in range(4):
        rng_d.normal()
    assert rng_c.normal() == rng_d.normal()                  # 4 draws consumed when the channel is on


# --------------------------------------------------------------------------- #
# D1 — under-etch: an incomplete clear leaves residual film that bridges the gate
# lines into a functional short (the mirror of the deposition void's open).
# --------------------------------------------------------------------------- #
def test_default_under_etch_frac_is_the_seam():
    """At the default ``under_etch_frac=0`` (a full clear) nothing bridges and the CD is unchanged — the
    step is the identity the seam relies on (byte-for-byte the pre-D1 etch)."""
    d = Die(site=(0, 0), radius_frac=0.0, cd_nm=167.3, resolved=True)
    out = etch_deposition_step(d, EtchDepositionKnobs(), pitch_nm=300.0, pert=DiePerturbation())
    assert out.cd_nm == 167.3                                   # == , not approx — the seam is exact
    assert out.bridged is False


def test_under_etch_bridge_is_a_functional_kill():
    """A large under-etch leaves residual film that bridges the gate lines → the die fails **functionally**
    (a short), not parametrically — its V_t/I_Dsat may read fine (parallel to the deposition void)."""
    w = run_line(Recipe(etch_deposition=EtchDepositionKnobs(under_etch_frac=0.3)),
                 variation=NO_VARIATION, grid_n=1)
    d = _center(w)
    assert d.bridged is True
    assert d.verdict.failed and any("bridge" in r.lower() or "short" in r.lower() for r in d.verdict.reasons)
    assert wafer_yield(w) == 0.0
    # A small under-etch (residual below the threshold) is harmless → the die is good (the contrast).
    good = run_line(Recipe(etch_deposition=EtchDepositionKnobs(under_etch_frac=0.1)),
                    variation=NO_VARIATION, grid_n=1)
    assert _center(good).bridged is False and wafer_yield(good) == 1.0


def test_under_etch_bridge_is_named_in_the_diagnosis():
    """The failure trail names the under-etch bridge as an incomplete-clear short (the 'why did this die?')."""
    from fab_game import diagnose

    w = run_line(Recipe(etch_deposition=EtchDepositionKnobs(under_etch_frac=0.3)),
                 variation=NO_VARIATION, grid_n=1)
    text = diagnose(_center(w))
    assert "BRIDGE" in text and "residual" in text


def test_over_and_under_etch_are_mutually_exclusive():
    """Setting both over- and under-etch is a recipe misconfiguration (one etch cannot do both) → raises
    at knob construction (like CzochralskiKnobs' two-``G`` guard)."""
    import pytest

    with pytest.raises(ValueError):
        EtchDepositionKnobs(over_etch_frac=0.2, under_etch_frac=0.2)
