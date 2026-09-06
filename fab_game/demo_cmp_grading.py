"""The F8-S4 banked artifact: what the market sees when the wire stops being common-mode.

The last CMP slice (`docs/plans/cmp-planarity-f8.md` S4), and the second F4 clause it ends. F8-S2 gave
the wire a per-die thickness and measured a grade map with no transistor behind it; that measurement was
never banked as a figure, and neither was F4's delay binning itself — :class:`fab_game.spec.DelayBins`
has existed since F4 and has never appeared on a page. This demo banks both, and settles the question
they raise together.

**The clause.** F4's :meth:`fab_game.spec.DelayBins.from_speed_bins` proves, in its own docstring, that
switching the grade currency from drive current to the delay the chip actually switches at compresses the
distribution **symmetrically**: a die at a bin edge sits ``τ_wire·(1 − I_nom/I_edge)`` off it — *positive*
above nominal (it misses the premium grade it would have won) and **negative below** (the slow tail is
*rescued* from the bin-out). Hence F4's conclusion: **a grading loss, never a yield loss.** That is
derived under the same premise S2 already ended — that ``τ_wire`` is common-mode. With a polished wire the
rim die carries ``τ_wire·(R/R_nom − 1)``, strictly positive and with **no ``I_Dsat`` in it**, so nothing
compensates it and the rescue can be cancelled outright.

**What one wafer shows (measured, not asserted).** The same 89 dies, the same silicon, three policies:

  ===============================================  =======  ==========
  policy                                           bin-outs wafer yield
  ===============================================  =======  ==========
  drive current (the pre-1997 speed proxy)               2      0.978
  chip delay, ideal wire (F4)                            0      1.000
  chip delay, polished wire (F8, ``s`` = 0.20)           8      0.910
  ===============================================  =======  ==========

and a bin-out is a **verdict fail** in this game's accounting (:func:`fab_game.steps.packaging_step`), so
that last column is the wafer yield the line reports. The wire now costs parts, not just grades.

**Neither mechanism does it alone** — the F4-S4 shape one slice on. A *tight* transistor spread under the
same polish loses nothing (0 bin-outs to ``s`` = 0.22); a *loose* spread with no polisher loses nothing
either (F4 rescues both of its bin-outs). Only the two together lose parts, and every part lost was a
below-nominal transistor sitting out at the rim — though **neither condition selects them**: 37 dies are
below nominal and 60 sit that far out, so the loss lives *inside* that intersection, not at it.

**And it is not only F4's rescue being taken back.** Of the 8 parts lost, **1** was a bin-out under the
drive-current policy too — that one is the rescue withdrawn, and die ``(2, 6)`` carries all three legs
alone: binned out on drive current, rescued to *value* by F4's ideal wire, rejected again by where it sat
on the polisher. The **other 7 were sellable under both prior policies**, and one of them
(site ``(5, 10)``) was graded *typical*. So the polished wire does not merely claw back the margin F4's
wire gave: **it creates bin-outs no grading policy had**, out of parts the old policy called good.

**And it is not extra spread on top of the transistor's — it is the opposite sign.** The transistor has a
weak radial trend of its own here (the focus bowl and the furnace's oxide trend leave the rim marginally
*faster*: radius vs ``I_Dsat`` correlates **+0.25**), so on the unpolished line the wafer's delay is, if
anything, faster outward (**−0.09**). Polished, that becomes **+0.45**: the polisher does not add a
signature alongside the transistor's, it **reverses the wafer's speed gradient**, and the parts it costs
sit exactly where the transistor said the dies were fast.

**The threshold is a house number, and is reported as one.** At the knob's default spread
(``nonuniformity`` = 0.10) *no* part is lost even with the loose process — the first one goes at
``s ≈ 0.14``. The *sign* is structural (a strictly positive, uncompensated term cannot rescue anything);
*where* it starts to bite rides the flagged radial amplitude, so the sweep panel draws the whole curve
rather than quoting a number from one point on it.

**The anchor, stated because it is load-bearing.** ``from_speed_bins`` warns that hand-picking delay
edges can manufacture the collapse out of a threshold choice, so the ladder here is anchored on the
**nominal part** — G6's grade fractions, evaluated at the unpolished nominal device, no new house number.
At the clear-everywhere polish time that anchor is not even a choice: the centre die is byte-for-byte the
F4 part (S2's seam), so anchoring on the nominal part and on this wafer's centre give the *same ladder*.

Run headless (saves the figure, prints the story):

    python -m fab_game.demo_cmp_grading
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from chip import cmp

from .pipeline import diagnose, run_line, wafer_yield
from .recipe import CmpKnobs, DeviceKnobs, Recipe
from .spec import DEFAULT_SPECS, DelayBins, SpeedBin, SpeedBins
from .state import Die, WaferState
from .variation import NO_VARIATION, Variation

# --- The demo settings (FLAGGED house numbers — mechanics, not magnitudes) --- #
SEED = 0
GRID_N = 11                                       # the G6 die map (~89 dies) — enough radii to grade rings on

# G6's market ladder and its two process-control σ's, **by value** (pinned equal to demo_packaging's in
# the test): this slice introduces no grading numbers of its own, the way B11 re-used B9's transistor.
SPEED_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=3.38),              # fast — the highest-drive parts
    SpeedBin("typical", lo_mA=3.21, hi_mA=3.38),  # the nominal grade
    SpeedBin("value", lo_mA=3.10, hi_mA=3.21),    # slow — still sellable
))                                                # < 3.10 mA → a bin-out (works, too slow to sell)
TIGHT_SIGMA = 1.5                                 # nm — well-controlled CD (the default process)
LOOSE_SIGMA = 7.0                                 # nm — poorly-controlled CD (a real slow tail)

METAL = "Cu"                                      # the only damascene metal (chip.cmp.DAMASCENE_METALS)
S_HOUSE = CmpKnobs().nonuniformity                # the knob's own default radial amplitude (FLAGGED)
S_SHOWN = 0.20                                    # the widest spread B11 draws — the maps are cut here
S_SWEEP = tuple(round(float(s), 4) for s in np.linspace(0.0, 0.30, 61))

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "fab-game-f8.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "fab-game-f8.png"


@dataclass(frozen=True)
class DemoResult:
    """The three-policy comparison, the two maps, and the bin-out sweep — the bundle."""

    # The ladder and its anchor (the nominal, unpolished part — no new house number).
    i_dsat_nom_mA: float
    tau_nom_ps: float
    ladder: DelayBins
    anchor_is_the_polished_centre: bool           # at the clear time the centre die IS the nominal part
    # The three policies over ONE wafer (same seed, same silicon; CMP consumes no randomness).
    s_shown: float
    wafer_idsat: WaferState                       # graded on drive current — the pre-1997 proxy
    wafer_f4: WaferState                          # graded on delay, ideal (unpolished) wire
    wafer_f8: WaferState                          # graded on delay, polished wire
    hist_idsat: dict
    hist_f4: dict
    hist_f8: dict
    yield_idsat: float
    yield_f4: float
    yield_f8: float
    # The die that carries the whole story: rejected → rescued → rejected.
    story_site: tuple[int, int] | None
    story_radius: float
    story_i_dsat_mA: float
    story_trail: str
    # The sweep — bin-outs vs the polish spread, for both process tightnesses (closed form, same calls).
    s_sweep: tuple[float, ...]
    tight_sigma_nm: float                         # the two process tightnesses the curves are cut at
    loose_sigma_nm: float
    rejects_loose: tuple[int, ...]
    rejects_tight: tuple[int, ...]
    rejects_loose_no_cmp: int                     # the F4 reference (flat, s-independent)
    rejects_tight_no_cmp: int
    first_loss_s_loose: float | None              # the smallest swept s that costs a part (FLAGGED)
    first_loss_s_tight: float | None
    # The composition, as counts (neither condition alone selects the lost parts).
    n_dies: int
    n_below_nominal: int
    first_reject_radius: float
    n_outside_first_reject_radius: int
    n_lost: int
    n_lost_rescued_then_taken_back: int           # lost parts the drive-current policy had ALSO rejected
    lost_prior_grades: dict                       # the lost parts' grades under the drive-current policy
    best_prior_grade_lost: str                    # the highest grade the polisher took off the ladder
    # The wafer's speed gradient, before and after the polisher (the sign the transistor set).
    corr_r_idsat: float                           # radius vs drive current — the transistor's own trend
    corr_r_tau_f4: float                          # radius vs delay, ideal wire
    corr_r_tau_f8: float                          # radius vs delay, polished wire


# --------------------------------------------------------------------------- #
# The runs
# --------------------------------------------------------------------------- #
def _recipe(polish_s: float | None, s: float = S_HOUSE) -> Recipe:
    """The line with a copper wire, polished (``polish_s``) or not (``None`` — the F8 seam)."""
    return Recipe(cmp=CmpKnobs(polish_s=polish_s, nonuniformity=s),
                  device=DeviceKnobs(interconnect=METAL))


def _clear_time(s: float) -> float:
    """The clear-everywhere polish time at spread ``s`` — the window's lower edge (recipe.CmpKnobs)."""
    return CmpKnobs(polish_s=1.0, nonuniformity=s).clear_time_s


def _run(recipe: Recipe, *, variation=NO_VARIATION, specs=DEFAULT_SPECS) -> WaferState:
    return run_line(recipe, seed=SEED, variation=variation, specs=specs, grid_n=GRID_N)


def _by_site(wafer: WaferState) -> dict:
    return {d.site: d for d in wafer.dies}


def _histogram(wafer: WaferState, labels) -> dict:
    hist = {label: 0 for label in labels}
    for d in wafer.dies:
        if d.bin is not None:
            hist[d.bin] = hist.get(d.bin, 0) + 1
    return hist


def _tau_wire_ps(die: Die) -> float:
    """This die's **nominal** wire term (ps), read off its own device record — F4's common-mode floor."""
    return next(r for r in die.history if r.step == "device").outputs["tau_wire_ps"]


def _tau_gate_ps(die: Die) -> float:
    """This die's transistor term (ps) — the only term ``I_Dsat`` enters (``chip.interconnect.delay``)."""
    return next(r for r in die.history if r.step == "device").outputs["tau_gate_ps"]


def _rejects_at(dies, tau_gate, tau_wire, s: float, ladder: DelayBins) -> int:
    """Bin-outs on this silicon at polish spread ``s``, in closed form — the same ``chip.cmp`` calls the
    step makes, and the exact ``τ_wire ∝ R`` scaling ``chip.interconnect.delay`` already carries.

    Re-running the pipeline for every point of the sweep would cost ~60 wafer runs for a curve whose only
    moving part is one thickness per die; instead the wafer is run **once** (unpolished) and each die's own
    recorded ``τ_gate``/``τ_wire`` are re-read at the polished thickness. The identity that makes this
    legitimate — ``τ_wire`` is linear in ``R`` and ``R ∝ 1/H`` with ``C`` invariant (F4's cited
    geometry-invariance) — is pinned against the real pipeline at ``S_SHOWN`` in the test.
    """
    if s <= 0.0:
        return sum(1 for tg, tw in zip(tau_gate, tau_wire)
                   if ladder.is_reject(ladder.assign(tg + tw)))
    knobs = CmpKnobs(polish_s=_clear_time(s), nonuniformity=s)
    n = 0
    for die, tg, tw in zip(dies, tau_gate, tau_wire):
        p = cmp.polish(knobs.removal_at(die.radius_frac), knobs.overburden_um,
                       knobs.trench_depth_um, knobs.pattern)
        n += ladder.is_reject(ladder.assign(tg + tw * p.resistance_factor))
    return n


def compute() -> DemoResult:
    """Run the three policies over one wafer, then sweep the polish spread (no plotting)."""
    # 1. The ladder's anchor: the nominal, unpolished part — F4's own construction, no new house number.
    nominal = _by_site(_run(_recipe(None)))[(GRID_N // 2, GRID_N // 2)]
    ladder = DelayBins.from_speed_bins(SPEED_BINS, nominal.i_dsat_mA, nominal.delay_ps)
    # …and at the clear-everywhere time that anchor is not a choice: the centre site is the slowest site,
    # so it removes exactly the overburden and its wire is F4's, bit-for-bit (the S2 seam).
    polished_centre = _by_site(_run(_recipe(_clear_time(S_SHOWN), S_SHOWN)))[(GRID_N // 2, GRID_N // 2)]
    anchor_same = polished_centre.delay_ps == nominal.delay_ps

    # 2. One wafer of silicon (loose CD control), graded three ways. CMP consumes no randomness, so the
    #    transistors are identical across all three runs — the histogram that cannot explain the maps.
    loose = Variation(cd_sigma_nm=LOOSE_SIGMA)
    specs_i = replace(DEFAULT_SPECS, speed_bins=SPEED_BINS)
    specs_d = replace(DEFAULT_SPECS, speed_bins=SPEED_BINS, delay_bins=ladder)
    polished = _recipe(_clear_time(S_SHOWN), S_SHOWN)
    w_idsat = _run(polished, variation=loose, specs=specs_i)
    w_f4 = _run(_recipe(None), variation=loose, specs=specs_d)
    w_f8 = _run(polished, variation=loose, specs=specs_d)

    # 3. The die that carries the story alone: binned out on drive current, rescued by F4's ideal wire,
    #    rejected again by where it sat on the polisher.
    b_i, b_4, b_8 = _by_site(w_idsat), _by_site(w_f4), _by_site(w_f8)
    story = next((d for d in sorted(w_f8.dies, key=lambda d: d.radius_frac)
                  if b_8[d.site].bin == "reject" and b_i[d.site].bin == "reject"
                  and b_4[d.site].bin != "reject"), None)
    if story is None:                              # no single die carries all three legs — take a lost part
        story = next((d for d in w_f8.dies
                      if d.bin == "reject" and b_4[d.site].bin != "reject"), w_f8.dies[0])

    # 4. The sweep — bin-outs vs the polish spread, on the SAME silicon, for both process tightnesses.
    sweeps = {}
    for tag, sigma in (("loose", LOOSE_SIGMA), ("tight", TIGHT_SIGMA)):
        w = _run(_recipe(None), variation=Variation(cd_sigma_nm=sigma), specs=specs_d)
        dies = [d for d in w.dies if d.delay_ps is not None]
        tau_gate = [_tau_gate_ps(d) for d in dies]
        tau_wire = [_tau_wire_ps(d) for d in dies]
        sweeps[tag] = (tuple(_rejects_at(dies, tau_gate, tau_wire, s, ladder) for s in S_SWEEP),
                       sum(1 for d in w.dies if d.bin == "reject"))

    def _first_loss(counts) -> float | None:
        return next((s for s, n in zip(S_SWEEP, counts) if n > 0), None)

    # 5. The composition, as counts: neither "below nominal" nor "out past this radius" selects the lost
    #    parts on its own — the intersection does.
    lost = [d for d in w_f8.dies if d.bin == "reject"]
    r_first = min((d.radius_frac for d in lost), default=1.0)
    # …and what the lost parts were worth BEFORE the polisher existed. Only the ones the drive-current
    # policy had also rejected are "F4's rescue, taken back"; the rest are bin-outs no grading policy had.
    prior = {}
    for d in lost:
        prior[b_i[d.site].bin] = prior.get(b_i[d.site].bin, 0) + 1
    order = [b.label for b in SPEED_BINS.bins] + [SPEED_BINS.reject_label]
    best_prior = min((g for g in prior), key=order.index, default=SPEED_BINS.reject_label)

    # 6. The wafer's speed gradient. The transistor has a weak radial trend of its OWN here (the focus
    #    bowl and the oxide trend leave the rim marginally faster), and it points the other way, so on the
    #    unpolished line the delay is very slightly faster outward. The polisher does not merely add
    #    spread on top of that — it reverses the gradient's sign.
    def _corr(xs, ys) -> float:
        return float(np.corrcoef(np.asarray(xs, float), np.asarray(ys, float))[0, 1])

    radii = [d.radius_frac for d in w_f8.dies]
    return DemoResult(
        i_dsat_nom_mA=nominal.i_dsat_mA, tau_nom_ps=nominal.delay_ps, ladder=ladder,
        anchor_is_the_polished_centre=anchor_same,
        s_shown=S_SHOWN, wafer_idsat=w_idsat, wafer_f4=w_f4, wafer_f8=w_f8,
        hist_idsat=_histogram(w_idsat, SPEED_BINS.labels),
        hist_f4=_histogram(w_f4, ladder.labels), hist_f8=_histogram(w_f8, ladder.labels),
        yield_idsat=wafer_yield(w_idsat), yield_f4=wafer_yield(w_f4), yield_f8=wafer_yield(w_f8),
        story_site=story.site, story_radius=story.radius_frac, story_i_dsat_mA=story.i_dsat_mA,
        story_trail=diagnose(story),
        s_sweep=S_SWEEP, tight_sigma_nm=TIGHT_SIGMA, loose_sigma_nm=LOOSE_SIGMA,
        rejects_loose=sweeps["loose"][0], rejects_tight=sweeps["tight"][0],
        rejects_loose_no_cmp=sweeps["loose"][1], rejects_tight_no_cmp=sweeps["tight"][1],
        first_loss_s_loose=_first_loss(sweeps["loose"][0]),
        first_loss_s_tight=_first_loss(sweeps["tight"][0]),
        n_dies=len(w_f8.dies),
        n_below_nominal=sum(1 for d in w_f8.dies
                            if d.i_dsat_mA is not None and d.i_dsat_mA < nominal.i_dsat_mA),
        first_reject_radius=r_first,
        n_outside_first_reject_radius=sum(1 for d in w_f8.dies if d.radius_frac >= r_first),
        n_lost=len(lost),
        n_lost_rescued_then_taken_back=prior.get(SPEED_BINS.reject_label, 0),
        lost_prior_grades=prior, best_prior_grade_lost=best_prior,
        corr_r_idsat=_corr(radii, [d.i_dsat_mA for d in w_f8.dies]),
        corr_r_tau_f4=_corr([d.radius_frac for d in w_f4.dies], [d.delay_ps for d in w_f4.dies]),
        corr_r_tau_f8=_corr(radii, [d.delay_ps for d in w_f8.dies]),
    )


# --------------------------------------------------------------------------- #
# The story, in text
# --------------------------------------------------------------------------- #
def print_summary(r: DemoResult) -> None:
    """Print the three policies → the composition → the sweep — the demo's payoff in text."""
    print("\nF8 (S4): what the market sees once the wire is per-die — the second F4 clause to go\n")

    print(f"  The ladder is anchored on the NOMINAL part (I_Dsat {r.i_dsat_nom_mA:.3f} mA, "
          f"τ_total {r.tau_nom_ps:.2f} ps) — G6's own grade fractions, no new house number.")
    print(f"  At the clear-everywhere time the centre die IS that part, bit-for-bit: "
          f"{r.anchor_is_the_polished_centre} — so the anchor is not a choice here.\n")

    labels = [b.label for b in SPEED_BINS.bins] + [SPEED_BINS.reject_label]
    print(f"  1. ONE wafer ({r.n_dies} dies, loose CD control, s = {r.s_shown:.2f}), graded three ways:")
    print("     policy                              " + "  ".join(f"{l:>8s}" for l in labels) + "    yield")
    for tag, hist, y in (("drive current (pre-1997)", r.hist_idsat, r.yield_idsat),
                         ("chip delay, ideal wire (F4)", r.hist_f4, r.yield_f4),
                         ("chip delay, polished (F8)", r.hist_f8, r.yield_f8)):
        print(f"     {tag:34s}" + "  ".join(f"{hist.get(l, 0):8d}" for l in labels) + f"   {y:6.1%}")
    print("     → the SAME silicon throughout (CMP draws no randomness): one I_Dsat histogram, three")
    print("       outcomes. F4's true currency rescues the slow tail; the polisher takes it back.\n")

    print("  2. Neither mechanism alone loses a part:")
    print(f"     transistor tail, no polisher (F4) : {r.rejects_loose_no_cmp} bin-outs")
    print(f"     polisher, tight transistors       : {r.rejects_tight[r.s_sweep.index(r.s_shown)]} bin-outs "
          f"at s = {r.s_shown:.2f}")
    print(f"     both                              : {r.n_lost} bin-outs")
    print(f"     → every part lost was below nominal AND out past r = {r.first_reject_radius:.2f}, but "
          f"neither condition selects them:")
    print(f"       {r.n_below_nominal} dies are below nominal and {r.n_outside_first_reject_radius} sit "
          f"that far out, so the loss lives INSIDE that intersection.")
    print("       It never rejects a FAST die.\n")

    grades = ", ".join(f"{n}× {g}" for g, n in sorted(r.lost_prior_grades.items(),
                                                      key=lambda kv: -kv[1]))
    print(f"  3. And it is not only F4's rescue being taken back. Under the OLD drive-current policy the "
          f"{r.n_lost} lost parts graded: {grades}.")
    print(f"     → {r.n_lost_rescued_then_taken_back} of them was the rescue withdrawn; the other "
          f"{r.n_lost - r.n_lost_rescued_then_taken_back} were sellable under BOTH prior policies")
    print(f"       (the best of them graded '{r.best_prior_grade_lost}'). The polished wire creates "
          f"bin-outs NO grading policy had.\n")

    print("  4. It is not extra spread on top of the transistor's — it is the OPPOSITE sign:")
    print(f"     radius vs drive current       : {r.corr_r_idsat:+.2f}  (the transistor's own trend — the "
          f"rim is marginally FASTER)")
    print(f"     radius vs delay, ideal wire   : {r.corr_r_tau_f4:+.2f}  (so the unpolished wafer is, if "
          f"anything, faster outward)")
    print(f"     radius vs delay, polished     : {r.corr_r_tau_f8:+.2f}  ← the polisher REVERSES the "
          f"wafer's speed gradient")
    print("     → the parts it costs sit where the transistor said the dies were fast. Two radial")
    print("       signatures, opposite signs, and the one with no transistor in it wins.\n")

    print(f"  5. The one die that carries it alone — site {r.story_site}, r = {r.story_radius:.2f}, "
          f"I_Dsat {r.story_i_dsat_mA:.3f} mA:")
    print("     " + r.story_trail.replace("\n", "\n     ") + "\n")

    loose_first = "none in the sweep" if r.first_loss_s_loose is None else f"s ≈ {r.first_loss_s_loose:.2f}"
    tight_first = "none in the sweep" if r.first_loss_s_tight is None else f"s ≈ {r.first_loss_s_tight:.2f}"
    print(f"  6. Where it starts to bite is a HOUSE NUMBER, so here is the whole curve, not a point:")
    print(f"     loose process — first part lost at {loose_first};  tight process — {tight_first}.")
    print(f"     At the knob's own default (s = {S_HOUSE:.2f}) the polisher still costs NO part. The SIGN")
    print("     is structural (a strictly positive term with no I_Dsat in it cannot rescue anything);")
    print("     the threshold rides the flagged radial amplitude and is reported as riding it.\n")

    print("  New: nothing in chip/ — this slice is the game layer reading F4's DelayBins over F8's per-die")
    print("  wire. device.py and interconnect.py stay untouched (the fifth consecutive slice).\n")


# --------------------------------------------------------------------------- #
# The figure
# --------------------------------------------------------------------------- #
def save_figure(r: DemoResult) -> Path:
    """Render and save the F8-S4 artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                            # headless
    from .plots import cmp_grading_figure

    fig = cmp_grading_figure(r)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # τ, →, ≈, µ on legacy codepages

    r = compute()
    print_summary(r)
    try:
        saved = save_figure(r)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
