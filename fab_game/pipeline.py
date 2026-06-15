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
from .steps import (
    device_step,
    diffusion_junction,
    etch_deposition_step,
    litho_step,
    oxidation_step,
    packaging_step,
    wafer_prep_step,
)
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
    """A fresh wafer: the die map + the boule-sliced substrate doping/resistivity + the purified
    contamination vector, no steps run yet. ``channel_N_A`` is the **effective** doping (the boule slice
    plus any residual-dopant net shift from imperfect purification); a clean feed leaves it the boule
    slice (the seam)."""
    return WaferState(
        wafer_id=wafer_id,
        channel_N_A=recipe.effective_channel_N_A,
        slice_z=recipe.czochralski.slice_z,
        resistivity_ohm_cm=recipe.substrate_resistivity_ohm_cm,
        contamination=recipe.contamination,
        dies=build_die_map(grid_n=grid_n, edge_exclusion=edge_exclusion),
    )


# --------------------------------------------------------------------------- #
# The driver
# --------------------------------------------------------------------------- #
def _aggregate(dies: tuple[Die, ...], attr: str) -> dict:
    """A cheap wafer-level summary of one die field (mean over the dies that have it)."""
    vals = [getattr(d, attr) for d in dies if getattr(d, attr) is not None]
    return {f"mean_{attr}": float(np.mean(vals)) if vals else None, "n": len(vals)}


def _die_contamination(contamination, na_factor: float):
    """The wafer contamination vector with its mobile-ion ``Na`` scaled by this die's radial edge-loading
    factor (:meth:`~fab_game.variation.Variation.na_factor`).

    Returns the wafer vector **unchanged** when the factor is ``1.0`` — variation off, ``na_edge_boost = 0``,
    or a clean ``Na = 0`` feed — so the seam is byte-identical and only a marginal feed under variation
    allocates a per-die vector (the edge ring of ``V_t`` kills). Only ``Na`` is non-uniform (the modeled
    edge-loading channel); the other species ride uniform (the named scope edge, now lifted only for Na)."""
    if na_factor == 1.0:
        return contamination
    return replace(contamination, Na=contamination.Na * na_factor)


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

    # 0a. Purification (front-of-line, G4): the feedstock grade zone-refined → the wafer-level
    #     contamination vector (baked into initial_wafer's channel_N_A + contamination). A wafer-level
    #     provenance record only — its per-die effect surfaces at the device step (Q_ox). Clean feed ⇒
    #     a clean vector ⇒ no consequence (the seam).
    cont = recipe.contamination
    wafer = wafer.with_step(
        StepRecord("purification",
                   {"grade": recipe.purification.grade, "zone_passes": recipe.purification.zone_passes},
                   {"Na": cont.Na, "Fe": cont.Fe, "net_doping_shift": cont.net_doping_shift,
                    "channel_N_A": recipe.effective_channel_N_A}),
        wafer.dies)

    # 0b. Wafer prep (front-of-line): the prepped geometry (deterministic) + the killer-particle
    #    scatter (stochastic, fixed die order). Drawn before the per-die perturbations.
    prep = recipe.wafer_prep
    geometry = prep_geometry(
        incoming_thickness_um=prep.incoming_thickness_um, slice_ttv_um=prep.slice_ttv_um,
        slice_bow_um=prep.slice_bow_um, removal_um=prep.cmp_removal_um,
        ttv_improvement=prep.cmp_ttv_improvement)
    # The killer-defect density the line scatters is the wafer-prep particle level PLUS any CG-2
    # grown-in COP/void density (vacancy-rich Czochralski growth) — two Poisson processes superpose,
    # so the grown-in voids ride the same cited G3 defect map. At the default (no thermal gradient
    # set) the grown-in term is 0, so this is prep.defect_density exactly (the G3 seam).
    cz = recipe.czochralski
    grown_in = cz.grown_in_defect_density       # uniform CG-2 density (the CENTRE/worst value when radial)
    if cz.is_osf_radial:
        # A2 OSF ring: the grown-in density is RADIAL — per die D₀(r) = wafer-prep particles +
        # grown_in_defect_density_at(radius_frac). The vacancy core (small r) catches COPs; the
        # interstitial rim (large r) is clean (0 at/beyond the ring) → an edge-vs-centre yield
        # non-uniformity. The uniform scalar effective_defect_density is NOT used on this branch.
        base = prep.defect_density
        defect_map = scatter_defects(
            wafer.dies, defect_density=base, grid_n=grid_n,
            wafer_diameter_mm=prep.wafer_diameter_mm, rng=rng, enabled=variation.enabled,
            density_fn=lambda d: base + cz.grown_in_defect_density_at(d.radius_frac))
    else:
        defect_map = scatter_defects(
            wafer.dies, defect_density=recipe.effective_defect_density, grid_n=grid_n,
            wafer_diameter_mm=prep.wafer_diameter_mm, rng=rng, enabled=variation.enabled)
    dies = tuple(wafer_prep_step(d, geometry, defect_map[d.site]) for d in wafer.dies)
    # Provenance: when CG-2 is engaged, record the grown-in split + the Voronkov regime at the
    # WAFER level — so the killer density is not silently read as a fab-floor particle level (the
    # per-die failure trail still names a caught particle; attributing each particle to grown-in vs
    # process needs a second Poisson draw and is a named deferred edge).
    prep_summary = {"ttv_um": geometry.ttv_um, "bow_um": geometry.bow_um,
                    "n_defects": sum(len(v) for v in defect_map.values())}
    if cz.is_osf_radial:
        # The OSF ring is radial — record the ring location + the centre/edge topology + the centre/edge
        # density (the boundary where the vacancy-core kills stop), so the map's non-uniformity is legible.
        # The vacancy COPs (centre) feed yield (here); the interstitial dislocations (rim/edge, A1) feed
        # the device-step LEAKAGE channel — record the rim density too so the leaky rim is legible.
        prep_summary["osf_ring_radius"] = cz.osf_ring_radius
        prep_summary["osf_zone_regimes"] = cz.osf_zone_regimes
        prep_summary["grown_in_density_center"] = cz.grown_in_defect_density_at(0.0)
        prep_summary["grown_in_density_edge"] = cz.grown_in_defect_density_at(1.0)
        prep_summary["dislocation_density_edge"] = cz.interstitial_dislocation_density_at(1.0)
        prep_summary["dislocation_density_center"] = cz.interstitial_dislocation_density_at(0.0)
    elif grown_in > 0.0:
        prep_summary["grown_in_defect_density"] = grown_in
        prep_summary["voronkov_ratio"] = cz.voronkov_ratio
        prep_summary["grown_in_regime"] = cz.grown_in_defect_regime
    elif cz.interstitial_dislocation_density > 0.0:
        # A1: an interstitial-side growth (ξ < ξ_t) seeds NO voids (grown_in = 0) but a uniform
        # dislocation population that feeds the device-step leakage channel — record it at the wafer
        # level so a slow-pull leakage scrap is not read as a fab-floor metal contamination.
        prep_summary["dislocation_density"] = cz.interstitial_dislocation_density
        prep_summary["voronkov_ratio"] = cz.voronkov_ratio
        prep_summary["grown_in_regime"] = cz.grown_in_defect_regime
    wafer = replace(wafer, geometry=geometry).with_step(
        StepRecord("wafer_prep",
                   {"ttv_um": geometry.ttv_um, "bow_um": geometry.bow_um,
                    "defect_density": prep.defect_density,
                    "grown_in_defect_density": grown_in,
                    "effective_defect_density": recipe.effective_defect_density},
                   prep_summary), dies)

    # One perturbation per die, drawn in fixed die order (the determinism contract).
    perts = {d.site: variation.perturbation(d, rng) for d in wafer.dies}

    # 1. Diffusion — die-independent in G1: compute once, broadcast. Reads the *effective* channel
    #    doping (boule slice + residual-dopant net shift) so the junction stays coherent with the device.
    diff_knobs_in, diff_outputs = diffusion_junction(recipe.diffusion, recipe.effective_channel_N_A)
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

    # 3b. Etch & deposition (G5) — per die: transfer the resist CD → the etched gate CD (anisotropy →
    #     etch bias overwrites cd_nm, which the device reads next), and gate the gap-fill on conformality
    #     vs the gate aspect ratio (a void → a functional fail). At default knobs (perfectly anisotropic,
    #     conformal) the CD passes through bit-for-bit and no die voids (the seam).
    dies = tuple(
        etch_deposition_step(d, recipe.etch_deposition, recipe.litho.pitch_nm, perts[d.site])
        for d in wafer.dies
    )
    wafer = wafer.with_step(
        StepRecord("etch_deposition",
                   {"anisotropy": recipe.etch_deposition.anisotropy,
                    "over_etch_frac": recipe.etch_deposition.over_etch_frac,
                    "conformality": recipe.etch_deposition.conformality},
                   _aggregate(dies, "cd_nm")), dies)

    # 4. Device — per die, reading the inherited t_ox + cd + the wafer contamination (the propagation:
    #    Na → Q_ox → V_t; the residual-dopant net shift is already in effective_channel_N_A).
    dies = tuple(
        device_step(d, recipe.device, recipe.effective_channel_N_A,
                    contamination=_die_contamination(recipe.contamination, variation.na_factor(d.radius_frac)),
                    thermal_donor_density=recipe.czochralski.thermal_donor_density,
                    dislocation_density=recipe.czochralski.interstitial_dislocation_density_at(d.radius_frac),
                    sd_contact_squares=recipe.diffusion.sd_contact_squares,
                    gettering_efficiency=recipe.czochralski.internal_gettering_efficiency)
        for d in wafer.dies
    )
    wafer = wafer.with_step(
        StepRecord("device", {"gate": recipe.device.gate, "width_um": recipe.device.width_um},
                   _aggregate(dies, "V_t")), dies)

    # 5. Test — apply the spec windows → the front-end (wafer-sort) verdicts + the running yield.
    wafer = _test_wafer(wafer, specs)

    # 6. Packaging & final test (G6, back-end) — dice/attach/bond/encapsulate the front-end-good dies
    #    (a stochastic per-die back-end survival against the assembly-yield funnel) then bin the
    #    survivors by I_Dsat (the speed proxy). The assembly kill draws from the RNG **last** (after every
    #    per-die perturbation) and **only** when the back end is lossy AND the stochastic layer is on, so a
    #    perfect back end (the default) consumes no randomness and leaves every good die packaged — the
    #    seam, and the G1–G5 banked demos byte-for-byte unchanged.
    return _package_wafer(wafer, recipe.packaging, specs.speed_bins, rng, variation.enabled)


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
# Packaging & final test (G6) — the back-end yield funnel + the speed binning
# --------------------------------------------------------------------------- #
def _package_wafer(wafer, knobs, bins, rng, variation_enabled: bool) -> WaferState:
    """Run the back-end assembly + final-test binning over the tested wafer → the packaged wafer.

    A per-die Bernoulli back-end survival is drawn (in fixed die order, **after** every per-die
    perturbation) against the cumulative assembly yield — but **only** when the back end is lossy
    (``assembly_yield < 1``) *and* the stochastic layer is on, so a perfect back end / disabled
    variation consumes no RNG and packages every good die (the seam). The packaging step then assembles
    + bins each die; the ``packaging`` provenance summary carries the **funnel** (front-end → final
    yield) and the bin histogram (the demo artifact).
    """
    Y = knobs.assembly_yield
    draw = variation_enabled and Y < 1.0
    new_dies = []
    for d in wafer.dies:
        survived = True
        if draw and d.verdict is not None and d.verdict.passed:
            survived = bool(rng.random() < Y)
        new_dies.append(packaging_step(d, knobs, survived, bins))
    new_dies = tuple(new_dies)

    n_total = len(new_dies)
    n_good = sum(d.verdict.passed for d in new_dies if d.verdict is not None)
    histogram = {label: 0 for label in bins.labels}
    for d in new_dies:
        if d.bin is not None:
            histogram[d.bin] = histogram.get(d.bin, 0) + 1
    summary = {"assembly_yield": Y, "final_yield": n_good / n_total if n_total else 0.0,
               "n_good": n_good, "n_total": n_total, "bins": histogram}
    return wafer.with_step(
        StepRecord("packaging", {"assembly_yield": Y, "step_yields": knobs.step_yields}, summary),
        new_dies)


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
    # Walk the trail for the litho focus (the dramatic-win root cause), the etch/depo transfer, and
    # the device read.
    litho = next((r for r in die.history if r.step == "litho"), None)
    etch = next((r for r in die.history if r.step == "etch_deposition"), None)
    device = next((r for r in die.history if r.step == "device"), None)
    if litho is not None:
        eff = litho.knobs_in.get("defocus_nm")
        lines.append(f"    ↳ litho: effective defocus {eff:+.0f} nm → "
                     f"CD {litho.outputs.get('cd_nm', float('nan')):.1f} nm, "
                     f"NILS {litho.outputs.get('nils', float('nan')):.2f}, "
                     f"resolved={litho.outputs.get('resolved')}")
    # The etch/deposition fingerprint (G5): an etch bias that shrank the resist CD into the gate CD
    # (over-etch / a non-anisotropic etch → I_Dsat over its ceiling), or a deposition void (a poor step
    # coverage that failed to fill the gate gap → a functional kill).
    if etch is not None:
        if etch.outputs.get("voided") is True:
            ar = etch.outputs.get("aspect_ratio", float("nan"))
            ar_c = etch.outputs.get("critical_aspect_ratio", float("nan"))
            lines.append(f"    ↳ etch/depo: deposition VOID — gap aspect ratio {ar:.2f} > the "
                         f"step-coverage limit {ar_c:.2f} (non-conformal fill → keyhole; a functional "
                         f"kill — deposit more conformally / open the pitch)")
        elif etch.outputs.get("bridged") is True:
            res = etch.outputs.get("residual_nm", float("nan"))
            thr = etch.outputs.get("bridge_threshold_nm", float("nan"))
            lines.append(f"    ↳ etch/depo: under-etch BRIDGE — residual film {res:.1f} nm > the "
                         f"{thr:.1f} nm short threshold (incomplete clear → the gate lines short; a "
                         f"functional kill — etch to completion / add over-etch margin)")
        elif etch.outputs.get("functional_fail"):
            lines.append(f"    ↳ etch/depo: functional fail — {etch.outputs['functional_fail']} "
                         f"(no working gate — back off the over-etch / raise the anisotropy)")
        elif etch.outputs.get("etch_bias_nm", 0.0) > 0.0:
            # Only name the etch when it actually shrank the CD (a real bias) — a default, perfectly
            # anisotropic etch is the identity (bias 0) and has no transfer story to tell, so it is not
            # mentioned in the trail (else a back-end-killed die with a clean etch would print a
            # self-contradictory "etch bias 0.0 nm shrank the CD" line — G6 surfaced this).
            bias = etch.outputs["etch_bias_nm"]
            lines.append(f"    ↳ etch/depo: etch bias {bias:.1f} nm shrank the resist CD "
                         f"{etch.outputs.get('resist_cd_nm', float('nan')):.1f} → gate CD "
                         f"{etch.outputs.get('cd_nm', float('nan')):.1f} nm (over-etch / low anisotropy)")
    if device is not None and "refused" in device.outputs:
        lines.append(f"    ↳ device: refused ({device.outputs['refused']}) — no working transistor")
    elif device is not None:
        lines.append(f"    ↳ device: V_t {device.outputs.get('V_t', float('nan')):.3f} V, "
                     f"I_Dsat {device.outputs.get('i_dsat', float('nan')) * 1e3:.2f} mA, "
                     f"leakage {device.outputs.get('j_leak_nA_cm2', float('nan')):.2g} nA/cm²")
        # The contamination fingerprint (G4a): a non-zero gate-oxide charge means mobile-ion (Na)
        # contamination from imperfect purification shifted V_t — name it as the root cause.
        Q_ox = device.knobs_in.get("Q_ox", 0.0)
        if Q_ox:
            lines.append(f"    ↳ purification: gate-oxide charge Q_ox {Q_ox:.2e} C/cm² (mobile-ion Na "
                         f"contamination) → V_FB/V_t driven down (purify harder — more zone passes)")
        # The thermal-donor fingerprint (C1): crucible oxygen + the ~450 °C donor anneal nucleated n-type
        # thermal donors that compensated the p-substrate (lower net N_A → V_t down) — name it as the root.
        N_TD = device.knobs_in.get("N_TD")
        if N_TD:
            lines.append(f"    ↳ crystal growth: thermal donors {N_TD:.2e} cm⁻³ (crucible oxygen + ~450 °C "
                         f"anneal) compensated the substrate → net N_A down → V_t down (lower the oxygen / "
                         f"shorten the donor anneal)")
        # The leakage fingerprint: a leakage failure traces to SRH recombination shortening the
        # minority-carrier lifetime. Two contributors on the same channel — name the one responsible:
        # a grown-in DISLOCATION population (A1, the rho_disl fingerprint — a too-slow interstitial-side
        # pull) vs the deep-level METALS (G4b, residual Fe/Cu) — the device output net doping cannot carry.
        if any("leakage" in r for r in die.verdict.reasons):
            tau_us = device.outputs.get("tau_us", float("nan"))
            rho_disl = device.knobs_in.get("rho_disl")
            if rho_disl:
                lines.append(f"    ↳ crystal growth: junction leakage from grown-in DISLOCATIONS "
                             f"(interstitial-side Voronkov, ρ_disl {rho_disl:.2e} cm⁻²; ξ < ξ_t — too "
                             f"slow a pull / over-steep hot zone) → SRH recombination shortens τ "
                             f"({tau_us:.2g} µs) → a leaky diode (pull faster / lower G toward the ξ_t window)")
            else:
                getter_eff = device.knobs_in.get("getter_eff")
                if getter_eff:
                    # S4 dual-use: oxygen IS gettering, but the [O_i] is too low to scrub the metals enough.
                    lines.append(f"    ↳ gettering: junction leakage — the deep-level metals are only "
                                 f"{getter_eff:.0%} gettered by the oxygen precipitates (τ {tau_us:.2g} µs); "
                                 f"raise [O_i] to getter more — but the same oxygen makes thermal donors that "
                                 f"pull V_t down, so this is a trade-off (or purify harder instead)")
                else:
                    lines.append(f"    ↳ purification: junction leakage from deep-level-metal SRH recombination "
                                 f"(minority-carrier lifetime τ {tau_us:.2g} µs) "
                                 f"→ a leaky diode (purify harder — zone refining scrubs the metals fast, tiny k)")
        # The oxidation fingerprint (phase-5 journey): a V_t/I_Dsat parametric death with the die's gate
        # oxide off the nominal thickness is an over/under-oxidation root — checked BEFORE the series-R
        # fingerprint because an over-oxidized I_Dsat-LOW death (thick oxide → low C_ox) otherwise reads as
        # series resistance (the same I_Dsat-low sign). Discriminated on the inherited t_ox itself, not the
        # V_t/I_Dsat sign (a deep Scheil cut also drags I_Dsat down — the sign is not unique; this mirrors
        # the journey's journey._oxidation_root). Nominal = the DEFAULT_RECIPE oxide (the canonical ~14 nm),
        # the same 6 % band; a nominal-oxide V_t/I_Dsat death stays attributed to its real root.
        oxide_named = False
        if (die.t_ox_um is not None
                and any(("v_t" in r.lower() or "i_dsat" in r.lower()) for r in die.verdict.reasons)):
            from chip.oxidation import grow_oxide
            ox = DEFAULT_RECIPE.oxidation
            nominal_nm = grow_oxide(ox.ambient, ox.T_celsius, ox.minutes, orientation=ox.orientation).t_ox_nm
            t_ox_nm = die.t_ox_um * 1.0e3
            if t_ox_nm > nominal_nm * 1.06:
                lines.append(f"    ↳ oxidation: gate oxide too THICK ({t_ox_nm:.1f} nm vs ~{nominal_nm:.1f} nm "
                             f"nominal) → V_t up + C_ox down starves I_Dsat (grow less oxide — shorten the bake)")
                oxide_named = True
            elif t_ox_nm < nominal_nm * 0.94:
                lines.append(f"    ↳ oxidation: gate oxide too THIN ({t_ox_nm:.1f} nm vs ~{nominal_nm:.1f} nm "
                             f"nominal) → V_t down + C_ox up over-drives I_Dsat (grow more oxide — longer bake)")
                oxide_named = True
        # The diffusion fingerprint (phase-4 journey): an I_Dsat-LOW failure with the S/D series-R consumer
        # engaged traces to an under-diffused junction — the high sheet resistance R_s (a cool/short predep
        # dose) becomes a parasitic series resistance that starves the drive current (source degeneration).
        # Suppressed when the oxidation fingerprint already claimed the death (an over-oxidized I_Dsat-low).
        R_series = device.knobs_in.get("R_series_ohm")
        if (not oxide_named and R_series
                and any("i_dsat" in r.lower() and "(low)" in r.lower() for r in die.verdict.reasons)):
            lines.append(f"    ↳ diffusion: S/D series resistance {R_series:.0f} Ω (an under-diffused junction "
                         f"→ high sheet resistance R_s {die.R_s:.0f} Ω/sq) starves I_Dsat via source "
                         f"degeneration → drive too weak (lay down more predep dose — hotter/longer predep)")
    # The back-end fingerprint (G6): a part can die in *packaging* even with a perfect front end — a
    # stochastic assembly scrap (dice/bond) or a final-test bin-out (works, but too slow to sell).
    if die.assembled is False:
        lines.append(f"    ↳ packaging: assembly scrap — a back-end functional kill "
                     f"(dicing/wire-bond; cracked die = scrap, irreversible)")
    elif die.bin is not None and any("binned out" in r for r in die.verdict.reasons):
        lines.append(f"    ↳ final test: binned out — I_Dsat too low for the slowest sellable speed bin "
                     f"(a working but out-of-grade part — tighten the process spread)")
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
        # Leave untouched: passing dies, and dies that died in the **back end** (an assembly scrap or a
        # bin-out — ``assembled is not None`` means the die reached packaging). Litho rework is a
        # front-end strip-and-re-expose: it cannot un-crack a packaged die or un-bin a shipped part
        # ("cracked die = scrap", G6), so a back-end death must stay dead and is **not** re-attempted or
        # counted as recovered. Only a front-end (litho/parametric) fail (``assembled is None``) is
        # re-exposed. (A particle kill / geometry scrap also has ``assembled is None`` — it re-tests the
        # same way and litho rework cannot remove a defect.)
        if d.verdict is not None and (d.verdict.passed or d.assembled is not None):
            new_dies.append(d)
            continue
        n_attempted += 1
        # Re-expose at the corrected focus + the persistent focus bowl (no fresh scatter), re-etch the
        # refreshed resist CD into the gate (so the device reads the re-etched CD — the same mid-line
        # transfer the run applied), re-run the device, and re-score.
        red = litho_step(d, corrected, variation.systematic_perturbation(d))
        red = etch_deposition_step(red, recipe.etch_deposition, recipe.litho.pitch_nm,
                                   variation.systematic_perturbation(d))
        red = device_step(red, recipe.device, wafer.channel_N_A,
                          contamination=_die_contamination(wafer.contamination, variation.na_factor(red.radius_frac)),
                          thermal_donor_density=recipe.czochralski.thermal_donor_density,
                          dislocation_density=recipe.czochralski.interstitial_dislocation_density_at(red.radius_frac),
                          sd_contact_squares=recipe.diffusion.sd_contact_squares,
                          gettering_efficiency=recipe.czochralski.internal_gettering_efficiency)
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
    # A **back-end death** (assembly scrap / bin-out — ``assembled is not None``) is also left untouched:
    # re-polishing fixes wafer flatness, it cannot un-crack a packaged die or un-bin a shipped part
    # ("cracked die = scrap", G6) — so it stays dead and is not counted as recovered.
    n_attempted = 0
    new_dies: list[Die] = []
    for d in reworked.dies:
        if d.verdict is not None and (d.verdict.passed or d.assembled is not None):
            new_dies.append(d)
            continue
        n_attempted += 1
        new_dies.append(_verdict_die(d, specs, geometry_reason))
    after = sum(d.verdict.passed for d in new_dies if d.verdict is not None)
    record = ReworkRecord("polish", n_attempted=n_attempted, n_recovered=after - before,
                          note=f"re-CMP −{extra_removal_um:.0f} µm → TTV {repolished.ttv_um:.3f} µm")
    return replace(reworked, dies=tuple(new_dies), rework_log=reworked.rework_log + (record,))


def rework_deposition(
    wafer: WaferState,
    recipe: Recipe = DEFAULT_RECIPE,
    *,
    specs: SpecSet = DEFAULT_SPECS,
    conformality: float = 0.9,
) -> WaferState:
    """Strip & **re-deposit** the voided dies at a more conformal step coverage, then re-test.

    The plan's depo-reworkable path ("depo sometimes strippable; over-etch irreversible"): a keyhole
    void is stripped and re-filled by a more conformal deposition (``conformality``, a CVD by default)
    — recovering the die *iff* its parametrics are otherwise in spec. The **etch is irreversible**: the
    gate CD is already cut, so a die failed on an over-etched (collapsed) CD stays dead even after a
    perfect re-fill — the teachable irreversible-vs-reworkable contrast. Only **voided** dies are
    re-deposited (read back the gate height + etched CD each carries and re-fill at the new coverage);
    passing dies and parametrically-failed (non-voided) dies are returned untouched. Provenance/die
    total never shrink and the accounting closes (``n_recovered = good_after − good_before``).
    """
    from chip import etch_deposition as ed

    before = sum(d.verdict.passed for d in wafer.dies if d.verdict is not None)
    geometry_reason = specs.geometry.check(wafer.geometry)
    pitch_nm = recipe.litho.pitch_nm
    n_attempted = 0
    new_dies: list[Die] = []
    for d in wafer.dies:
        # Re-deposit only the voided dies; a void needs a gate height + etched CD to re-fill.
        if d.voided is not True or d.gate_height_nm is None or d.cd_nm is None:
            new_dies.append(d)
            continue
        n_attempted += 1
        depo = ed.deposit_fill(d.gate_height_nm, pitch_nm, d.cd_nm, step_coverage=conformality)
        red = d.record(
            "etch_deposition_rework",
            knobs_in={"conformality": conformality},
            outputs={"aspect_ratio": depo.aspect_ratio,
                     "critical_aspect_ratio": depo.critical_aspect_ratio, "voided": depo.voided},
            voided=depo.voided,
        )
        new_dies.append(_verdict_die(red, specs, geometry_reason))
    after = sum(d.verdict.passed for d in new_dies if d.verdict is not None)
    record = ReworkRecord("deposition", n_attempted=n_attempted, n_recovered=after - before,
                          note=f"re-deposit at step coverage {conformality:.2f}")
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
