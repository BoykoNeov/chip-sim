"""G6 mechanics — the back-end packaging step is wired, propagates, partitions, and stays deterministic.

The physics (the cumulative assembly-yield funnel ``Y = Π yᵢ``) is pinned in
``chip/tests/test_packaging.py``; these are the **game** invariants (ADR 0005 §5):

* **the seam** — a perfect back end (default knobs) packages every front-end-good die, draws **no** RNG,
  and cannot shift any earlier (front-end) draw (so the G1–G5 banked demos stay byte-identical);
* **propagation** — a lossy assembly yield scraps parts (final yield < front-end yield, monotone in the
  step yields), and the binning sorts by ``I_Dsat`` as a speed proxy (an over-etched, higher-drive die
  bins *faster*);
* **the convergence (the non-circular leg)** — the per-die Bernoulli back-end survival, aggregated over
  many dies, converges to the cited ``Π yᵢ`` (the packaging analogue of G3's placement → ``exp(−D₀A)``);
* **the partition bookkeeping** — every die is exactly one of {front-end fail, assembly scrap, bin-out,
  binned-good}; good + bad = total; the bin histogram sums to the assembled count;
* **determinism** — a fixed (seed, recipe, variation) reproduces the packaged wafer (verdicts + bins).
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from fab_game import (
    DEFAULT_RECIPE,
    DEFAULT_SPECS,
    NO_VARIATION,
    PackagingKnobs,
    Recipe,
    SpeedBin,
    SpeedBins,
    Variation,
    diagnose,
    run_line,
    wafer_yield,
)
from fab_game.recipe import EtchDepositionKnobs, LithoKnobs
from fab_game.spec import SpecSet
from fab_game.state import Die, Verdict
from fab_game.steps import packaging_step


# --------------------------------------------------------------------------- #
# The seam: a perfect back end is the identity, and draws no RNG
# --------------------------------------------------------------------------- #
def test_default_packaging_is_the_identity_on_a_good_die():
    """Default knobs (perfect assembly, one open bin): a front-end-good die packages, bins to the single
    'pass' grade, and its verdict is untouched — the identity the seam relies on."""
    good = Die(site=(0, 0), radius_frac=0.0, i_dsat=3.3e-3, verdict=Verdict(True))
    out = packaging_step(good, PackagingKnobs(), survived=True, bins=SpeedBins())
    assert out.assembled is True
    assert out.bin == "pass"
    assert out.verdict.passed                                  # verdict unchanged


def test_lossy_assembly_does_not_shift_front_end_draws():
    """The assembly kill is drawn **last** — it cannot perturb any earlier per-die draw. So a lossy back
    end leaves every front-end field (CD, I_Dsat) byte-identical to a perfect-back-end run at the same
    seed; only the back-end outcome differs. This is the byte-identity that keeps G1–G5 unchanged."""
    var = Variation()
    perfect = run_line(DEFAULT_RECIPE, seed=3, variation=var, grid_n=5)
    lossy = run_line(Recipe(packaging=PackagingKnobs(bond_yield=0.5)), seed=3, variation=var, grid_n=5)
    assert [d.cd_nm for d in perfect.dies] == [d.cd_nm for d in lossy.dies]
    assert [d.i_dsat for d in perfect.dies] == [d.i_dsat for d in lossy.dies]
    # The perfect run scraps nobody (assembly never drew); the lossy run scraps some.
    assert all(d.assembled is not False for d in perfect.dies)
    assert any(d.assembled is False for d in lossy.dies)


def test_lossy_assembly_under_no_variation_kills_nobody():
    """The assembly kill is a *stochastic* loss (gated on the variation layer, like the killer-particle
    scatter): with NO_VARIATION even a lossy back end packages every good die (no draw)."""
    w = run_line(Recipe(packaging=PackagingKnobs(bond_yield=0.5)),
                 seed=0, variation=NO_VARIATION, grid_n=5)
    assert all(d.assembled is True for d in w.dies if d.verdict.passed)


# --------------------------------------------------------------------------- #
# Propagation: lossy assembly → lower yield (monotone); binning sorts by I_Dsat
# --------------------------------------------------------------------------- #
def test_worse_assembly_yield_lowers_final_yield_monotonically():
    """A worse back-end step (lower yield) packages strictly fewer parts → strictly lower final yield —
    the funnel propagating. Averaged over seeds so the stochastic loss reads as a trend, not noise."""
    var = Variation()
    def mean_yield(bond_yield: float) -> float:
        ys = [wafer_yield(run_line(Recipe(packaging=PackagingKnobs(bond_yield=bond_yield)),
                                   seed=s, variation=var, grid_n=5)) for s in range(20)]
        return float(np.mean(ys))
    y_perfect = mean_yield(1.0)
    y_mild = mean_yield(0.9)
    y_bad = mean_yield(0.6)
    assert y_perfect > y_mild > y_bad                          # a worse back end → a lower final yield


def test_binning_sorts_by_idsat_higher_is_faster():
    """Binning by I_Dsat as the speed proxy: a higher drive current → a higher (faster) bin; a part
    below the slowest sellable bin bins out (reject). The partition is total."""
    bins = SpeedBins(bins=(SpeedBin("fast", lo_mA=3.4),
                           SpeedBin("typical", lo_mA=3.0, hi_mA=3.4),
                           SpeedBin("slow", lo_mA=2.6, hi_mA=3.0)))
    assert bins.assign(3.6) == "fast"
    assert bins.assign(3.1) == "typical"
    assert bins.assign(2.7) == "slow"
    assert bins.assign(2.0) == "reject"                        # below the slowest bin → a bin-out
    assert bins.assign(None) == "reject"                       # no device read → cannot grade


def test_overetch_higher_idsat_bins_faster_end_to_end():
    """The mid-line over-etch raises I_Dsat (shorter channel) → the same bins sort it into a *faster*
    grade than the nominal die — the etch → I_Dsat → speed-bin propagation, through the real pipeline."""
    # Nominal I_Dsat ≈ 3.30 mA; a mild over-etch (CD 167 → 157, still in spec) raises it to ≈ 3.50 mA,
    # so a 3.4 mA edge splits them: nominal → typical, over-etched → fast.
    bins = SpeedBins(bins=(SpeedBin("fast", lo_mA=3.4),
                           SpeedBin("typical", lo_mA=2.8, hi_mA=3.4)))
    specs = replace(DEFAULT_SPECS, speed_bins=bins)
    nominal = run_line(DEFAULT_RECIPE, variation=NO_VARIATION, specs=specs, grid_n=1).dies[0]
    overetched = run_line(
        Recipe(etch_deposition=EtchDepositionKnobs(anisotropy=0.97, over_etch_frac=0.1)),
        variation=NO_VARIATION, specs=specs, grid_n=1).dies[0]
    assert overetched.i_dsat > nominal.i_dsat                  # over-etch raised the drive current
    assert nominal.bin == "typical" and overetched.bin == "fast"   # …which sorts it a grade faster


# --------------------------------------------------------------------------- #
# The convergence (the non-circular leg): Bernoulli survival → Π yᵢ
# --------------------------------------------------------------------------- #
def test_empirical_packaged_yield_converges_to_the_assembly_yield():
    """The per-die back-end survival, aggregated over many dies, converges to the cited cumulative
    yield Π yᵢ — the packaging analogue of G3's placement → exp(−D₀A) (a law-of-large-numbers leg, the
    non-circular validation of the multiplicative funnel)."""
    from chip.packaging import assembly_yield

    knobs = PackagingKnobs(dice_yield=0.97, bond_yield=0.9)    # Y = 0.873
    target = assembly_yield(*knobs.step_yields)
    var = Variation()
    survived = scrapped = 0
    for seed in range(60):                                     # ~1.2k assembly samples → σ_mean ≈ 0.01
        w = run_line(Recipe(packaging=knobs), seed=seed, variation=var, grid_n=5)
        survived += sum(d.assembled is True for d in w.dies)
        scrapped += sum(d.assembled is False for d in w.dies)
    empirical = survived / (survived + scrapped)
    assert abs(empirical - target) < 0.03                     # converges to Π yᵢ (LLN, ~3σ margin)


# --------------------------------------------------------------------------- #
# Partition bookkeeping: every die exactly one outcome; the histogram closes
# --------------------------------------------------------------------------- #
def test_packaging_partitions_every_die_into_exactly_one_outcome():
    """Each die is exactly one of {front-end fail, assembly scrap, bin-out, binned-good}; good+bad=total;
    and the packaging bin histogram sums to the assembled count (the funnel bookkeeping closes)."""
    bins = SpeedBins(bins=(SpeedBin("fast", lo_mA=3.4), SpeedBin("typical", lo_mA=3.0, hi_mA=3.4)))
    specs = replace(DEFAULT_SPECS, speed_bins=bins)            # slow/edge dies bin out (< 3.0 mA)
    recipe = Recipe(packaging=PackagingKnobs(bond_yield=0.6), litho=LithoKnobs(defocus_nm=70.0))
    w = run_line(recipe, seed=0, variation=Variation(), specs=specs, grid_n=7)

    fe_fail = [d for d in w.dies if d.assembled is None and d.verdict.failed]
    scrap = [d for d in w.dies if d.assembled is False]
    binout = [d for d in w.dies if d.assembled is True and d.bin == "reject"]
    binned_good = [d for d in w.dies if d.assembled is True and d.bin != "reject"]
    # Exactly-one partition: the four disjoint buckets tile the die map.
    assert len(fe_fail) + len(scrap) + len(binout) + len(binned_good) == w.n_dies
    # good + bad = total, and binned-good are exactly the passing dies.
    assert sum(d.verdict.passed for d in w.dies) == len(binned_good)
    assert sum(d.verdict.failed for d in w.dies) == len(fe_fail) + len(scrap) + len(binout)
    # The provenance bin histogram sums to the *binned* parts (survivors: binned-good + bin-out);
    # assembly scraps and front-end fails carry no bin, so they are not in it.
    pkg = next(r for r in w.provenance if r.step == "packaging")
    assert sum(pkg.summary["bins"].values()) == len(binout) + len(binned_good)


# --------------------------------------------------------------------------- #
# Determinism + the failure-trail attribution
# --------------------------------------------------------------------------- #
def test_packaging_is_reproducible_under_a_seed():
    """A fixed (seed, recipe, variation) reproduces the packaged wafer bit-for-bit (verdicts + bins)."""
    recipe = Recipe(packaging=PackagingKnobs(bond_yield=0.7))
    var = Variation()
    a = run_line(recipe, seed=5, variation=var, grid_n=5)
    b = run_line(recipe, seed=5, variation=var, grid_n=5)
    assert ([(d.assembled, d.bin, d.verdict.passed) for d in a.dies]
            == [(d.assembled, d.bin, d.verdict.passed) for d in b.dies])


def test_rework_does_not_resurrect_a_back_end_scrap():
    """Litho rework re-exposes front-end fails — it must **not** resurrect a back-end death (an assembly
    scrap or a bin-out): a packaged, cracked die is irreversible ('cracked die = scrap', G6), so it
    stays failed, is never counted as recovered, and the incoherent passed-∧-not-assembled state never
    forms (the invariant the rework guard protects)."""
    from fab_game import rework_litho

    bad = Recipe(packaging=PackagingKnobs(bond_yield=0.4), litho=LithoKnobs(defocus_nm=90.0))
    var = Variation()
    w = run_line(bad, seed=0, variation=var, grid_n=7)
    scrap_sites = [d.site for d in w.dies if d.assembled is False]
    assert scrap_sites                                         # the lossy bond produced ≥1 assembly scrap
    good_before = sum(d.verdict.passed for d in w.dies)

    # Strip & re-expose at corrected focus — recovers front-end (defocus) fails, never the scraps.
    w2 = rework_litho(w, bad, variation=var, focus_correction_nm=-90.0)
    for site in scrap_sites:
        d2 = next(d for d in w2.dies if d.site == site)
        assert d2.verdict.failed and d2.assembled is False     # the scrap stays dead, untouched
    good_after = sum(d.verdict.passed for d in w2.dies)
    assert w2.rework_log[-1].n_recovered == good_after - good_before   # accounting closes, no scrap counted
    # The incoherent "passed but never assembled" state must not exist anywhere.
    assert not any(d.verdict.passed and d.assembled is False for d in w2.dies)


def test_diagnose_names_the_assembly_scrap():
    """A back-end assembly kill is named in the failure trail (the 'why did this die?' for a scrap)."""
    w = run_line(Recipe(packaging=PackagingKnobs(bond_yield=0.4)), seed=0, variation=Variation(), grid_n=7)
    scrapped = next(d for d in w.dies if d.assembled is False)
    assert "assembly scrap" in diagnose(scrapped)


def test_diagnose_names_the_bin_out():
    """A working-but-too-slow part is named a bin-out (distinct from a parametric / functional fail)."""
    # Tight bins above the nominal I_Dsat (~3.3 mA): a perfectly-assembled nominal die bins out.
    bins = SpeedBins(bins=(SpeedBin("premium", lo_mA=4.0),))
    specs = replace(DEFAULT_SPECS, speed_bins=bins)
    w = run_line(DEFAULT_RECIPE, variation=NO_VARIATION, specs=specs, grid_n=1)
    d = w.dies[0]
    assert d.assembled is True and d.bin == "reject"
    assert d.verdict.failed and any("binned out" in r for r in d.verdict.reasons)
    assert "binned out" in diagnose(d)
