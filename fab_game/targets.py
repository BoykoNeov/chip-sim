"""Device targets — "good is application-relative": re-score the *same* wafer against multiple specs.

Today every wafer is judged against **one** notion of "good" (``DEFAULT_SPECS`` — a fast-logic MOSFET:
tight low-ish ``V_t``, high drive, thin oxide). This module adds the central DTCO lesson
(``docs/plans/device-targets.md``, slice 1): the *same* physical property that ruins a part for one product
is a *feature* for another. A high ``V_t`` is slow logic (reject) but a low-leakage low-power part
(premium); the *same* drifted wafer can be the wrong SKU for one target and the right SKU for its sibling.

This is the **zero-new-physics spine** (slice 1). It adds no device output and no new window *kind* — it
re-uses the existing :class:`~fab_game.spec.SpecSet` / :class:`~fab_game.spec.SpeedBins` machinery — and the
only "physics" it touches is **grading**: a finished wafer's already-computed dies are re-scored against a
different :class:`DeviceTarget`'s windows + bins (:func:`regrade`), never re-fabricated.

The two-level declaration (the design's backbone, ``docs/plans/device-targets.md`` §"the real-world line")
----------------------------------------------------------------------------------------------------------
1. **Device family** — the mask / structure, **committed up front, never salvaged across.** A logic wafer is
   not a power rectifier; the mask set commits the device from lithography on. (The power-device family is a
   later slice — its own declared run, never a harvest of a logic wafer.)
2. **Flavor within a family** — ``fast-logic`` ↔ ``low-power`` share a base flow and differ only by where
   their windows sit. An off-target lot **can** be dispositioned to a sibling flavor (real *engineering
   disposition* / material-review-board: "use-as-is or re-grade rather than scrap"). This is where
   "harvest the tail" honestly lives, and it is what :func:`disposition` surfaces.

:data:`MOSFET_FLAVORS` is that one family's flavor set; re-grading **across** families is *not* offered (it
is not real). The dollar amounts and the window bands are **flagged house numbers** (ADR 0005 §5) — the
tests assert the *mechanics* (the windows genuinely **cross**; a declaration **moves** the recipe optimum;
the disposition bookkeeping closes), never the magnitudes.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .scoring import BIN_PRICES, WAFER_COST, ScoreCard, score_wafer
from .spec import DEFAULT_SPECS, SpecSet, SpecWindow, SpeedBin, SpeedBins
from .state import Die, Verdict, WaferState

# --------------------------------------------------------------------------- #
# The market — the multi-grade speed bins parts are graded into (FLAGGED house numbers).
# Positioned around the nominal fast-logic I_Dsat (~3.30 mA → typical); a thinned-oxide / short-channel
# wafer drives I_Dsat up into premium, a slow part down into value. The value floor sits at the front-end
# I_Dsat spec floor (2.8 mA), so a working fast-logic part is always sellable. (Lived in game.py through G7;
# moved here so a DeviceTarget can own its bins without a game↔targets import cycle.)
# --------------------------------------------------------------------------- #
MARKET_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=3.55),               # fast parts (a thinned-oxide / short-channel wafer)
    SpeedBin("typical", lo_mA=3.15, hi_mA=3.55),   # the nominal grade
    SpeedBin("value", lo_mA=2.80, hi_mA=3.15),     # slow but sellable (down to the I_Dsat spec floor)
))


@dataclass(frozen=True)
class DeviceTarget:
    """A named product target — a spec window set (with its speed bins) + a price curve + an optimum hint.

    A *target* is one notion of "good": its :attr:`specs` carries the per-die acceptance windows **and** the
    final-test speed bins (``specs.speed_bins``), and :attr:`prices` is the per-bin revenue curve. Two
    targets of the **same device family** differ only by where their windows sit — the *same* wafer scores
    differently against each (the "good is relative" lesson). :attr:`optimum_hint` is human guidance (which
    knob direction this target rewards) for the educational guide / disposition readout; it is **not** read
    by any scoring path (the optimum is proven empirically, not declared — see the slice-1 gates).

    All numbers are flagged house values (ADR 0005 §5): only the *relationships* between targets (the
    windows cross; the optimum moves) carry meaning, never the bands or the dollars.
    """

    name: str
    specs: SpecSet
    prices: dict[str, float]
    optimum_hint: str = ""


# --------------------------------------------------------------------------- #
# The MOSFET family's flavors — same mask/structure, dispositionable between (FLAGGED bands + prices).
# The windows deliberately **cross** (the slice-1 gate): logic V_t [0.45, 0.68], low-power V_t [0.60, 0.85]
# overlap only on [0.60, 0.68]. A V_t = 0.50 wafer is logic-good / low-power-reject (too low → leaky for a
# mobile part); a V_t = 0.75 wafer is low-power-premium / logic-reject (too slow). The non-V_t windows
# (CD/NILS) and the I_Dsat ceiling are held common so V_t is the *sole* discriminator on the crossing axis;
# low-power lowers only the I_Dsat *floor* (a thick-oxide low-power part runs at lower drive — a feature,
# not a fail), so the V_t-band thick-oxide / deep-cut parts land in a sellable low-power bin, not a bin-out.
# --------------------------------------------------------------------------- #
FAST_LOGIC = DeviceTarget(
    name="fast-logic",
    specs=replace(DEFAULT_SPECS, speed_bins=MARKET_BINS),   # == today's specs (the seam: declaring this
    #                                                          reproduces the pre-targets game bit-for-bit)
    prices=BIN_PRICES,
    optimum_hint="thin gate oxide + shallow cut → low V_t, high drive (fast switching)",
)

# Low-power speed bins — positioned BELOW the fast-logic market: a low-power part trades drive for a high,
# low-leakage V_t, so its grades sit at lower I_Dsat (floor 2.0 mA, well under the thick-oxide drive) and a
# V_t-band part is always sellable. Same labels as the fast-logic market (so the price-curve keys match),
# different thresholds. FLAGGED.
LOW_POWER_BINS = SpeedBins(bins=(
    SpeedBin("premium", lo_mA=2.70),               # the cleanest low-power parts
    SpeedBin("typical", lo_mA=2.40, hi_mA=2.70),
    SpeedBin("value", lo_mA=2.00, hi_mA=2.40),     # slow but sellable (down to the low-power I_Dsat floor)
))
LOW_POWER_PRICES: dict[str, float] = {              # FLAGGED house $ — only the ordering + bookkeeping matter
    "premium": 9.0,
    "typical": 6.0,
    "value": 3.0,
    "reject": 0.0,
}
LOW_POWER = DeviceTarget(
    name="low-power",
    specs=replace(
        DEFAULT_SPECS,
        v_t=SpecWindow("V_t (V)", lo=0.60, hi=0.85),        # crosses fast-logic's [0.45, 0.68]
        i_dsat_mA=SpecWindow("I_Dsat (mA)", lo=2.0, hi=4.2),  # lower FLOOR only (low drive is a feature)
        speed_bins=LOW_POWER_BINS,
    ),
    prices=LOW_POWER_PRICES,
    optimum_hint="thick gate oxide + deeper cut → high V_t, low leakage (the fast-logic reject corner)",
)

# The MOSFET family's dispositionable flavor set (fast-logic declared by default, the incumbent first). A
# lot may re-grade between these (same mask); it may NOT re-grade to a different *family* (a power
# rectifier) — that is a later slice's own declared run, never a harvest of a logic wafer.
MOSFET_FLAVORS: tuple[DeviceTarget, ...] = (FAST_LOGIC, LOW_POWER)


# --------------------------------------------------------------------------- #
# Re-grading — score a FINISHED wafer against a different target (zero new physics)
# --------------------------------------------------------------------------- #
def _regrade_die(die: Die, target: DeviceTarget, geometry_reason: str | None) -> Die:
    """Re-grade one finished die against ``target`` — its physics is fixed; only the windows/bins change.

    Mirrors the pipeline's front-end verdict (:meth:`SpecSet.verdict`) **then** the back-end packaging
    (:func:`fab_game.steps.packaging_step`) — but reads the die's **already-computed** parameters
    (``V_t``/``I_Dsat``/CD/NILS/leakage) and its **irreversible** back-end state, never re-running a step:

    * A functional kill (particle / unresolved / void / bridge / geometry) and the parametric windows are
      re-evaluated by ``target.specs.verdict`` — so a die's *parametric* verdict is genuinely target-relative
      (the whole point), while a physical functional kill stays dead under every target (it short-circuits).
    * An **assembly scrap** (``assembled is False`` — a cracked/lifted-bond die) is irreversible: it stays
      dead under every target (re-grading cannot un-crack a die).
    * A die that the *declared* target front-end-failed (so it never reached assembly, ``assembled is None``)
      but **passes** this sibling's front end is treated as having **survived** assembly. This is **exact**
      at the default lossless back end (``assembly_yield = 1`` ⇒ every front-end-good die assembles); only a
      deliberately-lossy back end (the G6 demo corner) would have drawn it a survival it never made — a real
      but legitimately deferred edge (re-drawing here would add RNG, breaking "zero new physics").
    * A surviving part is re-binned by ``target.specs.speed_bins`` on its ``I_Dsat``; a part below the
      slowest sellable bin is a **bin-out** (a working but out-of-grade reject, ``verdict`` flips to fail).

    The append-only history gains one ``disposition`` record (the ``WaferState`` discipline). The new
    ``verdict``/``bin`` are what :func:`fab_game.scoring.score_wafer` reads to price the re-graded wafer.
    """
    knobs_in = {"target": target.name}
    verdict = target.specs.verdict(die, geometry_reason)
    if verdict.failed:                                       # front-end fail under this target — not shipped
        return die.record("disposition", knobs_in, {"target": target.name, "passed": False, "bin": None},
                          verdict=verdict, bin=None)
    if die.assembled is False:                              # irreversible assembly scrap — dead everywhere
        v = Verdict(False, ("assembly scrap — back-end functional kill (cracked die = scrap, irreversible)",))
        return die.record("disposition", knobs_in, {"target": target.name, "assembled": False},
                          verdict=v, bin=None)
    label = target.specs.speed_bins.assign(die.i_dsat_mA)   # re-bin the (would-)survived part
    if target.specs.speed_bins.is_reject(label):
        v = Verdict(False, (f"binned out — I_Dsat {die.i_dsat_mA:.2f} mA below {target.name}'s slowest "
                            f"sellable bin (a working but out-of-grade part)",))
        return die.record("disposition", knobs_in, {"target": target.name, "bin": label}, verdict=v, bin=label)
    return die.record("disposition", knobs_in, {"target": target.name, "passed": True, "bin": label},
                      verdict=verdict, bin=label)


def regrade(wafer: WaferState, target: DeviceTarget) -> WaferState:
    """Re-grade a **finished** wafer against ``target`` → a new :class:`WaferState` (zero new physics).

    The wafer is *physically fixed* — every die keeps its computed ``V_t``/``I_Dsat``/CD/leakage and its
    irreversible back-end state. Only the **grading** changes: each die is re-scored against ``target``'s
    windows + speed bins (:func:`_regrade_die`). This is the "same wafer, different spec" core of "good is
    relative" — the wafer is never re-fabricated (re-running the line would shift the assembly RNG order and
    change *physics-irrelevant* outcomes). Score the result with ``target.prices`` (see :func:`grade_for`).
    """
    geometry_reason = target.specs.geometry.check(wafer.geometry)
    dies = tuple(_regrade_die(d, target, geometry_reason) for d in wafer.dies)
    return replace(wafer, dies=dies)


def grade_for(wafer: WaferState, target: DeviceTarget, *, wafer_cost: float = WAFER_COST) -> ScoreCard:
    """Re-grade ``wafer`` against ``target`` and score it with ``target``'s price curve → a :class:`ScoreCard`.

    ``wafer_cost`` is the **already-sunk** fab cost (the same for every target — the wafer is built once), so
    across a disposition menu only the **revenue** differs; the cost is carried only so ``profit`` closes.
    """
    return score_wafer(regrade(wafer, target), prices=target.prices, wafer_cost=wafer_cost)


# --------------------------------------------------------------------------- #
# Disposition — the "which SKU?" readout over a finished, possibly off-target wafer
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TargetGrade:
    """How a finished wafer grades against one :class:`DeviceTarget` — the target + its :class:`ScoreCard`."""

    target: DeviceTarget
    scorecard: ScoreCard

    @property
    def revenue(self) -> float:
        return self.scorecard.revenue

    @property
    def yield_(self) -> float:
        return self.scorecard.yield_

    @property
    def line(self) -> str:
        """A one-line human readout — ``"<target>: <yield> yield, $<revenue> (<bin mix>)"``."""
        mix = ", ".join(f"{n}×{lbl}" for lbl, n in self.scorecard.bin_counts.items()) or "nothing sellable"
        return f"{self.target.name}: {self.yield_:.0%} yield, ${self.revenue:.0f} ({mix})"


def disposition(
    wafer: WaferState,
    targets: tuple[DeviceTarget, ...] = MOSFET_FLAVORS,
    *,
    wafer_cost: float = WAFER_COST,
) -> tuple[TargetGrade, ...]:
    """Grade a finished wafer against every flavor in the family, **best revenue first** — the SKU menu.

    The disposition readout: a lot that drifted off its declared target is re-scored against its sibling
    flavors (whole-wafer — the honest re-grade unit, not die-cherry-picking across products), and the player
    picks the SKU. Ranked by **revenue** (the fab cost is sunk and identical across targets, so revenue is
    the live lever); ties keep the input order (the declared flavor listed first, so an on-target lot reads
    naturally). Returns one :class:`TargetGrade` per target — ``result[0]`` is the best SKU for this wafer.
    """
    grades = tuple(TargetGrade(t, grade_for(wafer, t, wafer_cost=wafer_cost)) for t in targets)
    return tuple(sorted(grades, key=lambda g: g.revenue, reverse=True))
