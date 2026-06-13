"""State bookkeeping (ADR 0005 §5) — good+bad=total, provenance append-only, rework closes.

The harness's accounting must be airtight: every die is binned exactly once (no die lost or
double-counted), provenance only ever **grows** (the failure trail is never rewritten), and a
rework event's recovery count reconciles against the yield change.
"""
from __future__ import annotations

from fab_game import DEFAULT_RECIPE, Variation, run_line, wafer_yield
from fab_game.pipeline import rework_deposition, rework_litho
from fab_game.recipe import EtchDepositionKnobs, LithoKnobs, Recipe


def test_good_plus_bad_equals_total():
    """Every die is binned exactly once: passed + failed == n_dies, and yield matches the count."""
    w = run_line(Recipe(litho=LithoKnobs(defocus_nm=90.0)), seed=0, variation=Variation(), grid_n=5)
    good = sum(d.verdict.passed for d in w.dies)
    bad = sum(d.verdict.failed for d in w.dies)
    assert good + bad == w.n_dies
    assert wafer_yield(w) == good / w.n_dies


def test_provenance_is_append_only():
    """The wafer provenance and every die history grow by exactly the run's steps, in order."""
    w = run_line(DEFAULT_RECIPE, seed=0, variation=Variation(), grid_n=3)
    steps = [r.step for r in w.provenance]
    # Purification (G4) is a *wafer-level* front-of-line step — its contamination vector is wafer-wide
    # and surfaces per-die only at the device read (Q_ox), so it has no per-die record.
    assert steps == ["purification", "wafer_prep", "diffusion", "oxidation", "litho",
                     "etch_deposition", "device", "test"]
    per_die_steps = ["wafer_prep", "diffusion", "oxidation", "litho", "etch_deposition", "device", "test"]
    for d in w.dies:
        # Each die saw every per-die step once, in the same order (append-only, never rewritten).
        assert [r.step for r in d.history] == per_die_steps


def test_rework_accounting_closes():
    """Rework recovers exactly (good_after − good_before); the die total and provenance never shrink."""
    bad = Recipe(litho=LithoKnobs(defocus_nm=90.0))
    var = Variation()
    w = run_line(bad, seed=0, variation=var, grid_n=5)
    good_before = sum(d.verdict.passed for d in w.dies)

    # Strip & re-expose the failed dies with the focus error corrected back to nominal.
    w2 = rework_litho(w, bad, variation=var, focus_correction_nm=-90.0)
    good_after = sum(d.verdict.passed for d in w2.dies)

    assert w2.n_dies == w.n_dies                             # rework creates/destroys no dies
    assert len(w2.rework_log) == len(w.rework_log) + 1       # one rework event logged
    rec = w2.rework_log[-1]
    assert rec.n_recovered == good_after - good_before       # the accounting reconciles
    assert good_after >= good_before                         # rework never makes yield worse
    assert good_after > good_before                          # and here it actually recovers dies
    # Provenance is append-only: a reworked die's history only grew.
    for d0, d1 in zip(w.dies, w2.dies):
        assert len(d1.history) >= len(d0.history)


def test_partial_rework_recovers_only_what_it_fixes():
    """A *partial* focus correction recovers some dies but not all — the accounting still closes, and
    the dies the correction doesn't rescue stay failed (rework is physically realistic, not a reset)."""
    bad = Recipe(litho=LithoKnobs(defocus_nm=90.0))
    var = Variation()
    w = run_line(bad, seed=0, variation=var, grid_n=7)
    good_before = sum(d.verdict.passed for d in w.dies)
    failed_before = sum(d.verdict.failed for d in w.dies)

    # A small correction: the persistent focus bowl keeps the worst edge dies out of focus.
    w2 = rework_litho(w, bad, variation=var, focus_correction_nm=-5.0)
    good_after = sum(d.verdict.passed for d in w2.dies)
    rec = w2.rework_log[-1]
    assert rec.n_recovered == good_after - good_before       # the accounting reconciles
    assert 0 < rec.n_recovered < failed_before               # recovered some, but not all (still some dead)
    assert sum(d.verdict.failed for d in w2.dies) > 0        # the un-rescued dies stay failed


def test_deposition_rework_recovers_voids_but_not_irreversible_overetch():
    """A depo void is strippable (re-deposit conformally → recovers); an over-etched CD is irreversible
    (a perfect re-fill can't bring it back) — the plan's reworkable-vs-irreversible contrast, and the
    accounting still closes."""
    from fab_game import NO_VARIATION

    # A poor PVD coverage voids the whole wafer functionally — but the etch CD is fine.
    voided = run_line(Recipe(etch_deposition=EtchDepositionKnobs(conformality=0.3)),
                      seed=0, variation=NO_VARIATION, grid_n=5)
    good_before = sum(d.verdict.passed for d in voided.dies)
    assert good_before == 0                                    # all voided
    rw = rework_deposition(voided, conformality=0.9)           # re-deposit conformally (CVD)
    good_after = sum(d.verdict.passed for d in rw.dies)
    rec = rw.rework_log[-1]
    assert rec.step == "deposition"
    assert rec.n_recovered == good_after - good_before         # accounting closes
    assert good_after > good_before                            # the voids are recovered
    assert rw.n_dies == voided.n_dies                          # creates/destroys no dies
    for d0, d1 in zip(voided.dies, rw.dies):
        assert len(d1.history) >= len(d0.history)              # provenance append-only

    # An over-etched, CD-collapsed wafer: re-depositing cannot recover it (the etch is irreversible —
    # those dies were never voided, so the depo rework leaves them as the same object).
    overetched = run_line(Recipe(etch_deposition=EtchDepositionKnobs(anisotropy=0.8, over_etch_frac=0.8)),
                          seed=0, variation=NO_VARIATION, grid_n=5)
    assert wafer_yield(overetched) == 0.0                      # CD out of window
    rw2 = rework_deposition(overetched, conformality=0.9)
    assert wafer_yield(rw2) == 0.0                             # still dead — the etch cannot be undone
    assert rw2.rework_log[-1].n_recovered == 0


def test_rework_leaves_passing_dies_untouched():
    """Rework re-processes only the failed dies; the survivors are returned identical."""
    bad = Recipe(litho=LithoKnobs(defocus_nm=90.0))
    var = Variation()
    w = run_line(bad, seed=0, variation=var, grid_n=5)
    w2 = rework_litho(w, bad, variation=var, focus_correction_nm=-90.0)
    for d0, d1 in zip(w.dies, w2.dies):
        if d0.verdict.passed:
            assert d1 is d0                                  # untouched (same object)
