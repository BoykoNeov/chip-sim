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

from chip.czochralski import Boule
from chip.wafer_prep import prep_geometry

from .defects import scatter_defects
from .recipe import DEFAULT_RECIPE, Recipe
from .spec import DEFAULT_SPECS, SpecSet
from .state import Die, StepRecord, Verdict, WaferState, build_die_map
from .steps import device_step, diffusion_junction, litho_step, oxidation_step, wafer_prep_step
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
    """A fresh wafer: the die map + the boule-sliced substrate doping/resistivity, no steps run yet."""
    return WaferState(
        wafer_id=wafer_id,
        channel_N_A=recipe.channel_N_A,
        slice_z=recipe.czochralski.slice_z,
        resistivity_ohm_cm=recipe.substrate_resistivity_ohm_cm,
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
    bit-for-bit (the seam). Steps run wafer-prep → diffusion → oxidation → litho → device → test;
    wafer prep scatters killer particles on the die map and sets the wafer geometry (G3), the device
    step *reads the inherited* ``t_ox``/``cd`` (the propagation), and the test step applies the spec
    windows (a killer-defect or out-of-spec geometry is a functional fail).

    RNG order (the determinism contract): the defect scatter is drawn first (wafer prep is step 1),
    then the per-die perturbations. Both short-circuit without touching the RNG when off (variation
    disabled / zero defect density), so a clean, no-variation run consumes no randomness (the seam).
    """
    rng = np.random.default_rng(seed)
    wafer = initial_wafer(recipe, grid_n=grid_n, edge_exclusion=edge_exclusion, wafer_id=wafer_id)

    # 0. Wafer prep (front-of-line): the prepped geometry (deterministic) + the killer-particle
    #    scatter (stochastic, fixed die order). Drawn before the per-die perturbations.
    prep = recipe.wafer_prep
    geometry = prep_geometry(
        incoming_thickness_um=prep.incoming_thickness_um, slice_ttv_um=prep.slice_ttv_um,
        slice_bow_um=prep.slice_bow_um, removal_um=prep.cmp_removal_um,
        ttv_improvement=prep.cmp_ttv_improvement)
    defect_map = scatter_defects(
        wafer.dies, defect_density=prep.defect_density, grid_n=grid_n,
        wafer_diameter_mm=prep.wafer_diameter_mm, rng=rng, enabled=variation.enabled)
    dies = tuple(wafer_prep_step(d, geometry, defect_map[d.site]) for d in wafer.dies)
    wafer = replace(wafer, geometry=geometry).with_step(
        StepRecord("wafer_prep",
                   {"ttv_um": geometry.ttv_um, "bow_um": geometry.bow_um,
                    "defect_density": prep.defect_density},
                   {"ttv_um": geometry.ttv_um, "bow_um": geometry.bow_um,
                    "n_defects": sum(len(v) for v in defect_map.values())}), dies)

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


# --------------------------------------------------------------------------- #
# The boule → batch sweep (the G2 unit-of-run reconciliation)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BatchResult:
    """A batch of wafers sliced down one boule — the Scheil spread made visible (the G2 artifact).

    ``boule`` the grown crystal; ``z_positions`` the axial fractions sliced; ``wafers`` the scored
    :class:`WaferState` at each (same order). Boron's ``k<1`` raises ``N_A`` (and hence ``V_t``)
    toward the tail, so the tail wafers drift out of the ``V_t`` window — :attr:`yields` falls down
    the boule. The substrate doping is the **only** thing that changes between wafers (same seed,
    same recipe), so the trend is the clean Scheil signal.
    """

    boule: Boule
    z_positions: tuple[float, ...]
    wafers: tuple[WaferState, ...]

    @property
    def yields(self) -> tuple[float, ...]:
        """Per-wafer yield down the boule (``good/total`` at each ``z``)."""
        return tuple(wafer_yield(w) for w in self.wafers)

    @property
    def channel_N_As(self) -> tuple[float, ...]:
        """Per-wafer substrate doping (cm⁻³) — the Scheil profile sampled at ``z_positions``."""
        return tuple(w.channel_N_A for w in self.wafers)

    @property
    def resistivities(self) -> tuple[float, ...]:
        """Per-wafer substrate resistivity (Ω·cm) down the boule."""
        return tuple(w.resistivity_ohm_cm for w in self.wafers)

    def mean_V_t(self, wafer: WaferState) -> float:
        """Mean device ``V_t`` over a wafer's working dies (the Scheil consequence the spec scores)."""
        vts = [d.V_t for d in wafer.dies if d.V_t is not None]
        return float(np.mean(vts)) if vts else float("nan")


def run_batch(
    recipe: Recipe = DEFAULT_RECIPE,
    *,
    z_positions: tuple[float, ...] | None = None,
    n_wafers: int = 6,
    z_max: float = 0.85,
    seed: int = 0,
    variation: Variation = NO_VARIATION,
    specs: SpecSet = DEFAULT_SPECS,
    grid_n: int = 5,
    edge_exclusion: float = 0.95,
) -> BatchResult:
    """Slice a wafer batch down the boule and run each through the line → :class:`BatchResult`.

    The G2 unit-of-run reconciliation (plan §10): a *run* is still one wafer; a **batch** is the same
    boule sliced at several axial positions, each wafer starting at its own Scheil doping. Each wafer
    runs ``recipe`` with ``czochralski.slice_z`` set to its ``z`` (so ``channel_N_A`` differs per
    wafer); within a wafer the substrate is uniform, so G1's "diffusion once, broadcast" survives.

    Defaults to :data:`NO_VARIATION` so the batch isolates the **axial Scheil effect** — the only
    difference between wafers is the substrate doping, so ``V_t`` vs ``z`` is the clean segregation
    signal and yield steps as ``V_t`` crosses the spec window (real within-wafer variation, G1, would
    blur that threshold). All wafers share ``seed``; the Scheil path consumes no RNG.
    """
    if z_positions is None:
        z_positions = tuple(float(z) for z in np.linspace(0.0, z_max, n_wafers))
    else:
        z_positions = tuple(float(z) for z in z_positions)
    wafers = tuple(
        run_line(
            replace(recipe, czochralski=replace(recipe.czochralski, slice_z=z)),
            seed=seed, variation=variation, specs=specs,
            grid_n=grid_n, edge_exclusion=edge_exclusion, wafer_id=f"W_z{z:04.2f}",
        )
        for z in z_positions
    )
    return BatchResult(boule=recipe.boule, z_positions=z_positions, wafers=wafers)


def _test_wafer(wafer: WaferState, specs: SpecSet) -> WaferState:
    """Score every die against ``specs`` → verdicts; record the wafer yield in provenance.

    The wafer-level geometry scrap (TTV/bow out of spec) is computed **once** and applied to every
    die (a flatness reject fails the whole wafer); the per-die functional (defect / unresolved) +
    parametric checks then run for each die.
    """
    geometry_reason = specs.geometry.check(wafer.geometry)
    dies = tuple(_verdict_die(d, specs, geometry_reason) for d in wafer.dies)
    n_good = sum(d.verdict.passed for d in dies)
    summary = {"yield": n_good / len(dies), "n_good": n_good, "n_total": len(dies),
               "geometry_scrap": geometry_reason}
    return wafer.with_step(StepRecord("test", {"specs": repr(specs)}, summary), dies)


def _verdict_die(die: Die, specs: SpecSet, geometry_reason: str | None = None) -> Die:
    verdict = specs.verdict(die, geometry_reason)
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
    # A killer particle defect (G3) is a functional kill at the front of the line — name it and the
    # location(s), the "why did this die?" for a defect death (independent of the defocus chain).
    if die.killed_by_defect:
        locs = ", ".join(f"({d.x:+.2f}, {d.y:+.2f})" for d in die.defects)
        lines.append(f"    ↳ wafer prep: caught {len(die.defects)} killer particle(s) at {locs} "
                     f"(wafer-radius units) — a functional kill, no working die")
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
    geometry_reason = specs.geometry.check(wafer.geometry)   # a scrapped wafer stays scrapped on re-test
    n_attempted = 0
    new_dies: list[Die] = []
    for d in wafer.dies:
        if d.verdict is not None and d.verdict.passed:
            new_dies.append(d)
            continue
        n_attempted += 1
        # Re-expose at the corrected focus + the persistent focus bowl (no fresh scatter),
        # re-run the device on the refreshed CD, and re-score. A die killed by a particle (or a
        # geometry-scrapped wafer) re-tests the same way — litho rework cannot remove a defect.
        red = litho_step(d, corrected, variation.systematic_perturbation(d))
        red = device_step(red, recipe.device, wafer.channel_N_A)
        red = _verdict_die(red, specs, geometry_reason)
        new_dies.append(red)

    after = sum(d.verdict.passed for d in new_dies if d.verdict is not None)
    record = ReworkRecord("litho", n_attempted=n_attempted, n_recovered=after - before,
                          note=f"re-expose at focus correction {focus_correction_nm:+.0f} nm")
    return replace(wafer, dies=tuple(new_dies), rework_log=wafer.rework_log + (record,))


def rework_polish(
    wafer: WaferState,
    *,
    specs: SpecSet = DEFAULT_SPECS,
    extra_removal_um: float = 40.0,
    extra_ttv_improvement: float = 0.5,
) -> WaferState:
    """Re-polish a flatness-scrapped wafer: a second CMP lowers TTV — **at the cost of thickness**.

    The plan's wafer-prep reworkable path (re-polish/re-clean, costly, eats thickness). A re-CMP
    removes ``extra_removal_um`` more silicon (thickness shrinks) and improves the residual TTV by
    ``extra_ttv_improvement`` ∈ ``[0, 1]`` — so a wafer scrapped for TTV can come back **in** spec.
    Bow is unchanged (CMP does not fix bow), so a bow scrap is *not* recoverable this way, and a
    re-polish that would eat the whole wafer **raises** (the physical limit — you can re-polish only
    so far). Re-polish fixes *flatness*; it does **not** remove a killer particle defect (those dies
    stay dead). Provenance/die-total are unchanged; the accounting closes (``n_recovered =
    good_after − good_before``) — the bookkeeping invariant on a wafer-level rework.
    """
    if wafer.geometry is None:
        raise ValueError("wafer has no geometry to re-polish (run wafer prep first)")
    before = sum(d.verdict.passed for d in wafer.dies if d.verdict is not None)
    g = wafer.geometry
    thickness_out = g.thickness_um - extra_removal_um
    if thickness_out <= 0.0:
        raise ValueError(f"re-polish removal {extra_removal_um} µm ≥ wafer thickness "
                         f"{g.thickness_um} µm — nothing left of the wafer")
    if not 0.0 <= extra_ttv_improvement <= 1.0:
        raise ValueError(f"extra_ttv_improvement must be in [0, 1], got {extra_ttv_improvement}")
    repolished = replace(g, thickness_um=thickness_out,
                         ttv_um=g.ttv_um * (1.0 - extra_ttv_improvement))
    reworked = replace(wafer, geometry=repolished)
    geometry_reason = specs.geometry.check(repolished)
    # Re-score only the failed dies (a flatness improvement cannot newly-fail an already-passing die),
    # leaving survivors as the same object — so their history is not double-stamped (cf. rework_litho).
    n_attempted = 0
    new_dies: list[Die] = []
    for d in reworked.dies:
        if d.verdict is not None and d.verdict.passed:
            new_dies.append(d)
            continue
        n_attempted += 1
        new_dies.append(_verdict_die(d, specs, geometry_reason))
    after = sum(d.verdict.passed for d in new_dies if d.verdict is not None)
    record = ReworkRecord("polish", n_attempted=n_attempted, n_recovered=after - before,
                          note=f"re-CMP −{extra_removal_um:.0f} µm → TTV {repolished.ttv_um:.3f} µm")
    return replace(reworked, dies=tuple(new_dies), rework_log=reworked.rework_log + (record,))


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
