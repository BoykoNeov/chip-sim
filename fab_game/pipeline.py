"""The pipeline driver — run the line, score the wafer, trace a failure, rework (the plan §4/§6).

This is the orchestration chip-sim never had (ADR 0005 Context: the chaining lived only inside
``demo_device``). :func:`run_line` threads a wafer through diffusion → oxidation → lithography →
device → test, drawing all randomness from **one seeded RNG in fixed die order** (the determinism
contract), and returns the immutable final :class:`WaferState`. :func:`wafer_yield` scores it;
:func:`diagnose` walks a failed die's append-only history into the "why did this die?" trail;
:func:`rework_litho` is the minimal reworkable path (strip & re-expose) whose accounting closes.

Performance: the **diffusion** solve is die-independent in G1, so it is computed **once** and
broadcast; oxidation/litho/device are cheap per-die (litho is the only per-die optics call,
because the focus differs die-to-die). The seam is preserved either way — at the nominal recipe
with no variation, every die gets the identical nominal physics == :mod:`chip.demo_device`.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .recipe import DEFAULT_RECIPE, Recipe
from .spec import DEFAULT_SPECS, SpecSet
from .state import Die, StepRecord, Verdict, WaferState, build_die_map
from .steps import device_step, diffusion_junction, litho_step, oxidation_step
from .variation import NO_VARIATION, Variation


# --------------------------------------------------------------------------- #
# Build the starting wafer
# --------------------------------------------------------------------------- #
def initial_wafer(
    recipe: Recipe = DEFAULT_RECIPE,
    *,
    grid_n: int = 5,
    edge_exclusion: float = 0.95,
    wafer_id: str = "W1",
) -> WaferState:
    """A fresh wafer: the die map + the substrate doping, no process steps run yet."""
    return WaferState(
        wafer_id=wafer_id,
        channel_N_A=recipe.channel_N_A,
        dies=build_die_map(grid_n=grid_n, edge_exclusion=edge_exclusion),
    )


# --------------------------------------------------------------------------- #
# The driver
# --------------------------------------------------------------------------- #
def _aggregate(dies: tuple[Die, ...], attr: str) -> dict:
    """A cheap wafer-level summary of one die field (mean over the dies that have it)."""
    vals = [getattr(d, attr) for d in dies if getattr(d, attr) is not None]
    return {f"mean_{attr}": float(np.mean(vals)) if vals else None, "n": len(vals)}


def run_line(
    recipe: Recipe = DEFAULT_RECIPE,
    *,
    seed: int = 0,
    variation: Variation = NO_VARIATION,
    specs: SpecSet = DEFAULT_SPECS,
    grid_n: int = 5,
    edge_exclusion: float = 0.95,
    wafer_id: str = "W1",
) -> WaferState:
    """Run a full wafer through the line → the scored final :class:`WaferState`.

    All randomness flows from ``numpy.random.default_rng(seed)`` consumed in **fixed die order**,
    so ``(seed, recipe, variation)`` reproduces the wafer exactly. With ``variation=NO_VARIATION``
    every die gets the nominal physics and the centre die reproduces :mod:`chip.demo_device`
    bit-for-bit (the seam). Steps run diffusion → oxidation → litho → device → test; the device
    step *reads the inherited* ``t_ox``/``cd`` (the propagation), and the test step applies the
    spec windows.
    """
    rng = np.random.default_rng(seed)
    wafer = initial_wafer(recipe, grid_n=grid_n, edge_exclusion=edge_exclusion, wafer_id=wafer_id)
    # One perturbation per die, drawn in fixed die order (the determinism contract).
    perts = {d.site: variation.perturbation(d, rng) for d in wafer.dies}

    # 1. Diffusion — die-independent in G1: compute once, broadcast.
    diff_knobs_in, diff_outputs = diffusion_junction(recipe.diffusion, recipe.channel_N_A)
    dies = tuple(
        d.record("diffusion", diff_knobs_in, diff_outputs,
                 x_j_um=diff_outputs["x_j_um"], R_s=diff_outputs["R_s"])
        for d in wafer.dies
    )
    wafer = wafer.with_step(
        StepRecord("diffusion", diff_knobs_in, _aggregate(dies, "x_j_um")), dies)

    # 2. Oxidation — per die (the t_ox non-uniformity factor differs).
    dies = tuple(oxidation_step(d, recipe.oxidation, perts[d.site]) for d in wafer.dies)
    wafer = wafer.with_step(
        StepRecord("oxidation", {"ambient": recipe.oxidation.ambient,
                                 "T_celsius": recipe.oxidation.T_celsius,
                                 "minutes": recipe.oxidation.minutes},
                   _aggregate(dies, "t_ox_um")), dies)

    # 3. Lithography — per die (the effective focus differs → the Bossung CD response).
    dies = tuple(litho_step(d, recipe.litho, perts[d.site]) for d in wafer.dies)
    wafer = wafer.with_step(
        StepRecord("litho", {"defocus_nm": recipe.litho.defocus_nm,
                             "pitch_nm": recipe.litho.pitch_nm, "NA": recipe.litho.NA},
                   _aggregate(dies, "cd_nm")), dies)

    # 4. Device — per die, reading the inherited t_ox + cd (the propagation).
    dies = tuple(device_step(d, recipe.device, recipe.channel_N_A) for d in wafer.dies)
    wafer = wafer.with_step(
        StepRecord("device", {"gate": recipe.device.gate, "width_um": recipe.device.width_um},
                   _aggregate(dies, "V_t")), dies)

    # 5. Test — apply the spec windows → the verdicts (and the running yield in provenance).
    return _test_wafer(wafer, specs)


def _test_wafer(wafer: WaferState, specs: SpecSet) -> WaferState:
    """Score every die against ``specs`` → verdicts; record the wafer yield in provenance."""
    dies = tuple(_verdict_die(d, specs) for d in wafer.dies)
    n_good = sum(d.verdict.passed for d in dies)
    summary = {"yield": n_good / len(dies), "n_good": n_good, "n_total": len(dies)}
    return wafer.with_step(StepRecord("test", {"specs": repr(specs)}, summary), dies)


def _verdict_die(die: Die, specs: SpecSet) -> Die:
    verdict = specs.verdict(die)
    return die.record("test", {"specs": "applied"},
                      {"passed": verdict.passed, "reasons": verdict.reasons},
                      verdict=verdict)


# --------------------------------------------------------------------------- #
# Scoring + the failure trail
# --------------------------------------------------------------------------- #
def wafer_yield(wafer: WaferState) -> float:
    """Fraction of dies that passed (``good / total``). Requires the test step to have run."""
    scored = [d for d in wafer.dies if d.verdict is not None]
    if not scored:
        raise ValueError("wafer has not been tested — run the line through the test step first")
    return sum(d.verdict.passed for d in scored) / len(scored)


def diagnose(die: Die) -> str:
    """Trace **why this die died** by walking its append-only history — the banked artifact's payoff.

    Reports the verdict reasons, then names the most-deviated *root* knob (here the effective
    defocus — the focus error the systematic tilt + scatter produced), and the offending output it
    drove. For a passing die, says so. This is the harness turning a dead die back into a cause —
    "the failure trail names defocus."
    """
    if die.verdict is None:
        return f"die {die.site}: not yet tested"
    if die.verdict.passed:
        return f"die {die.site}: PASS"

    lines = [f"die {die.site} (r={die.radius_frac:.2f}): FAIL — " + "; ".join(die.verdict.reasons)]
    # Walk the trail for the litho focus (the dramatic-win root cause) and the device read.
    litho = next((r for r in die.history if r.step == "litho"), None)
    device = next((r for r in die.history if r.step == "device"), None)
    if litho is not None:
        eff = litho.knobs_in.get("defocus_nm")
        lines.append(f"    ↳ litho: effective defocus {eff:+.0f} nm → "
                     f"CD {litho.outputs.get('cd_nm', float('nan')):.1f} nm, "
                     f"NILS {litho.outputs.get('nils', float('nan')):.2f}, "
                     f"resolved={litho.outputs.get('resolved')}")
    if device is not None and "refused" in device.outputs:
        lines.append(f"    ↳ device: refused ({device.outputs['refused']}) — no working transistor")
    elif device is not None:
        lines.append(f"    ↳ device: V_t {device.outputs.get('V_t', float('nan')):.3f} V, "
                     f"I_Dsat {device.outputs.get('i_dsat', float('nan')) * 1e3:.2f} mA")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Minimal rework — the strip-and-re-expose path (the bookkeeping invariant)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReworkRecord:
    """One rework event's accounting: which step, how many dies attempted, how many recovered.

    The accounting **closes** by construction: ``n_recovered = n_good_after − n_good_before`` and the
    die total is unchanged (rework re-processes existing dies, it never creates or destroys them).
    """

    step: str
    n_attempted: int
    n_recovered: int
    note: str = ""


def rework_litho(
    wafer: WaferState,
    recipe: Recipe = DEFAULT_RECIPE,
    *,
    specs: SpecSet = DEFAULT_SPECS,
    variation: Variation = NO_VARIATION,
    focus_correction_nm: float = 0.0,
) -> WaferState:
    """Strip resist and **re-expose** the failed dies with a corrected focus, then re-test.

    The plan's reworkable litho path (litho rework is a real fab step: strip, re-coat, re-expose).
    Only dies that **failed** are reworked; each is re-imaged at ``defocus_nm + focus_correction_nm``
    (the player's global correction) **plus the persistent center-to-edge focus bowl** (``variation``
    — the re-exposure is in the same scanner, so the systematic tilt does not vanish; only a fresh,
    well-controlled exposure drops the random scatter). Passing dies are untouched. Provenance stays
    **append-only** and the die total is unchanged — so the bookkeeping invariant (good + bad =
    total, accounting closes) holds. Returns a new :class:`WaferState` with a :class:`ReworkRecord`.

    Because the focus bowl persists, an **insufficient** correction leaves the worst edge dies still
    failed (re-exposing at the same recipe rescues nothing) — rework recovers only what the
    correction actually fixes (physically realistic). Pass the same ``variation`` the run used.
    """
    before = sum(d.verdict.passed for d in wafer.dies if d.verdict is not None)
    corrected = replace(recipe.litho, defocus_nm=recipe.litho.defocus_nm + focus_correction_nm)
    n_attempted = 0
    new_dies: list[Die] = []
    for d in wafer.dies:
        if d.verdict is not None and d.verdict.passed:
            new_dies.append(d)
            continue
        n_attempted += 1
        # Re-expose at the corrected focus + the persistent focus bowl (no fresh scatter),
        # re-run the device on the refreshed CD, and re-score.
        red = litho_step(d, corrected, variation.systematic_perturbation(d))
        red = device_step(red, recipe.device, wafer.channel_N_A)
        red = _verdict_die(red, specs)
        new_dies.append(red)

    after = sum(d.verdict.passed for d in new_dies if d.verdict is not None)
    record = ReworkRecord("litho", n_attempted=n_attempted, n_recovered=after - before,
                          note=f"re-expose at focus correction {focus_correction_nm:+.0f} nm")
    return replace(wafer, dies=tuple(new_dies), rework_log=wafer.rework_log + (record,))


# --------------------------------------------------------------------------- #
# A convenience bundle for the demo / notebook (a single run + its score)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LineResult:
    """A run of the line + its headline score — the loose bundle the demo / notebook consume."""

    label: str
    wafer: WaferState
    yield_: float

    @classmethod
    def of(cls, label: str, wafer: WaferState) -> "LineResult":
        return cls(label=label, wafer=wafer, yield_=wafer_yield(wafer))

    @property
    def dead_dies(self) -> tuple[Die, ...]:
        """The dies that failed (for the failure-trail narrative)."""
        return tuple(d for d in self.wafer.dies if d.verdict is not None and d.verdict.failed)
