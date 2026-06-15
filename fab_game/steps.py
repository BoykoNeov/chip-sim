"""The pipeline steps — thin, deterministic wrappers over the **validated** back end (G1).

Each step is ``step(die, knobs, perturbation, …) → die``: a pure function of the inherited die
state, the per-die effective knobs, and the drawn perturbation — *zero new physics*, every number
comes from a ``chip/`` module that already passes its triad. The wiring is the work: each step
fills the die field its physics produces, and the **device** step *reads the inherited fields*
(``t_ox``, ``cd``) — that read is how damage propagates, not a scripted dependency graph.

The dramatic-win chain lives here: :func:`litho_step` turns the defocus knob into a printed CD
through the real Bossung optics; :func:`device_step` turns that CD into ``I_Dsat`` (∝ W/L) —
**never** into ``V_t`` (the device model's named scope edge: ``V_t`` has no channel-length term).
A too-defocused image stops resolving — :func:`litho_step` records ``resolved=False`` and
:func:`device_step` then **refuses** (no device), which the test step scores a *functional* fail.

The seam: at the nominal recipe with the identity perturbation, every call reduces to the exact
:mod:`chip.demo_device` call (same args), so the outputs match bit-for-bit.
"""
from __future__ import annotations

import math

from chip import breakdown as bd
from chip import diffusion_dopant as dd
from chip import etch_deposition as ed
from chip import oxidation as ox
from chip import litho
from chip import device as dev
from chip import lifetime as life
from chip.junction import analyze_junction
from chip.purification import Contamination, sodium_oxide_charge
from chip.wafer_prep import WaferGeometry

from .recipe import (
    DeviceKnobs,
    DiffusionKnobs,
    EtchDepositionKnobs,
    LithoKnobs,
    OxidationKnobs,
    PackagingKnobs,
)
from .spec import SpeedBins
from .state import DefectEvent, Die, Verdict
from .variation import DiePerturbation


def wafer_prep_step(die: Die, geometry: WaferGeometry, defects: tuple[DefectEvent, ...]) -> Die:
    """Wafer prep on one die (G3) — record the wafer geometry + the killer particles it caught.

    The first step of the line (front-of-line). ``geometry`` is the wafer-level prepped flatness
    (the same object for every die — it gates the *wafer*, scored at test); ``defects`` are the
    killer particles the stochastic scatter placed on **this** die. A die that caught any is marked
    ``killed_by_defect`` → a functional fail (its parametric device may still read fine). Adds only
    orthogonal fields (geometry/defects), so at no variation it places no defects and the device seam
    is untouched. ``killed_by_defect`` is always set (``False`` when clean) — an un-run step leaves it
    ``None``, a clean prep leaves it ``False`` (the gap-vs-zero distinction the state keeps).
    """
    killed = len(defects) > 0
    return die.record(
        "wafer_prep",
        knobs_in={"ttv_um": geometry.ttv_um, "bow_um": geometry.bow_um,
                  "thickness_um": geometry.thickness_um},
        outputs={"n_defects": len(defects), "killed_by_defect": killed},
        defects=defects, killed_by_defect=killed,
    )


def diffusion_junction(knobs: DiffusionKnobs, channel_N_A: float) -> tuple[dict, dict]:
    """The S/D two-step diffusion compute → ``(knobs_in, outputs)`` dicts (``x_j_um``, ``R_s``).

    The one engine solve of the line (:func:`chip.diffusion_dopant.two_step` predep → drive-in,
    then the junction against the channel doping). Factored out of :func:`diffusion_step` because
    G1 has **no per-die diffusion variation** — the result is die-independent, so the driver runs
    it **once** and broadcasts it across the die map (the rest is a cheap engine solve avoided per
    die). Matches :mod:`chip.demo_device`'s S/D diffusion exactly.
    """
    _, drivein = dd.two_step(
        knobs.dopant,
        T_predep=knobs.T_predep_C, t_predep_min=knobs.t_predep_min,
        T_drivein=knobs.T_drivein_C, t_drivein_min=knobs.t_drivein_min,
        drivein_program=knobs.drivein_program,
        length_um=knobs.length_um,
    )
    junc = analyze_junction(drivein, knobs.dopant, channel_N_A)
    knobs_in = {"dopant": knobs.dopant, "T_drivein_C": knobs.T_drivein_C,
                "t_drivein_min": knobs.t_drivein_min}
    if knobs.drivein_program is not None:  # E1: a spike anneal bypasses the isothermal T/t knobs
        prog = knobs.drivein_program
        knobs_in["drivein_spike_peak_C"] = prog.T_peak
        knobs_in["drivein_spike_duration_s"] = prog.duration
    outputs = {"x_j_um": junc.x_j_um, "R_s": junc.R_s}
    return knobs_in, outputs


def diffusion_step(die: Die, knobs: DiffusionKnobs, channel_N_A: float) -> Die:
    """S/D two-step diffusion on one die → the junction depth ``x_j`` and sheet resistance ``R_s``.

    Thin per-die wrapper over :func:`diffusion_junction` (the canonical unit the seam test exercises
    directly). Deterministic given the knobs; no variation in G1.
    """
    knobs_in, outputs = diffusion_junction(knobs, channel_N_A)
    return die.record(
        "diffusion", knobs_in=knobs_in, outputs=outputs,
        x_j_um=outputs["x_j_um"], R_s=outputs["R_s"],
    )


def oxidation_step(die: Die, knobs: OxidationKnobs, pert: DiePerturbation) -> Die:
    """Gate-oxide growth → the local ``t_ox`` (with the output-level thickness non-uniformity).

    Runs :func:`chip.oxidation.grow_oxide`; the die-to-die thickness jitter / center-to-edge
    thinning is applied as ``t_ox·t_ox_factor`` (``factor == 1.0`` → the seam). ``t_ox`` feeds the
    device ``V_t`` (thicker oxide → larger ``V_t``).
    """
    g = ox.grow_oxide(knobs.ambient, knobs.T_celsius, knobs.minutes, orientation=knobs.orientation)
    t_ox_um = g.t_ox * pert.t_ox_factor
    return die.record(
        "oxidation",
        knobs_in={"ambient": knobs.ambient, "T_celsius": knobs.T_celsius, "minutes": knobs.minutes,
                  "t_ox_factor": pert.t_ox_factor},
        outputs={"t_ox_um": t_ox_um, "regime": g.regime},
        t_ox_um=t_ox_um,
    )


def litho_step(die: Die, knobs: LithoKnobs, pert: DiePerturbation) -> Die:
    """Gate lithography → the printed CD (the dramatic-win chain's first link).

    The per-die **effective focus** is ``defocus_nm + defocus_nm_delta`` (the systematic focus tilt
    + scatter, both routed *through* the Bossung optics of :func:`chip.litho.expose_grating`); the
    output ``cd_nm_delta`` adds line-width roughness. Records ``cd``, ``nils``, and ``resolved`` —
    when defocus blurs the image flat, ``resolved`` goes False and the device step refuses (a
    functional fail), rather than the run crashing on a degenerate CD. Identity perturbation +
    ``defocus_nm = 0`` ⇒ the exact ``demo_device`` call.
    """
    imaging = litho.Imaging(wavelength_nm=knobs.wavelength_nm, NA=knobs.NA, sigma=knobs.sigma)
    eff_defocus = knobs.defocus_nm + pert.defocus_nm_delta
    feat = litho.expose_grating(imaging=imaging, pitch_nm=knobs.pitch_nm, defocus_nm=eff_defocus)
    cd_nm = feat.cd_nm + pert.cd_nm_delta
    return die.record(
        "litho",
        knobs_in={"defocus_nm": eff_defocus, "pitch_nm": knobs.pitch_nm,
                  "NA": knobs.NA, "sigma": knobs.sigma, "cd_nm_delta": pert.cd_nm_delta},
        outputs={"cd_nm": cd_nm, "nils": feat.nils, "contrast": feat.contrast,
                 "resolved": bool(feat.resolved)},
        cd_nm=cd_nm, nils=feat.nils, resolved=bool(feat.resolved),
    )


def etch_deposition_step(
    die: Die, knobs: EtchDepositionKnobs, pitch_nm: float, pert: DiePerturbation,
) -> Die:
    """Etch & deposition on one die (G5) — transfer the resist CD → the etched gate CD, gate the gap-fill.

    The mid-line step between litho and the device. The **etch** transfers the printed (resist) CD into
    the gate film through the real anisotropy → etch-bias geometry of
    :func:`chip.etch_deposition.etch_feature` (a less-anisotropic or over-etched recipe undercuts the
    mask → the CD shrinks → a shorter channel → the device's ``I_Dsat ∝ W/L`` rises — the "over-etch →
    CD out of spec" failure of plan §5); the etched CD **overwrites** ``cd_nm`` (the cross-module length
    the device reads — so the propagation needs *no* device-step change), with the resist CD kept in the
    record. The **deposition** then fills the gaps between the gate lines: a poor step coverage voids a
    high-aspect-ratio gap (:func:`chip.etch_deposition.deposit_fill`, the aspect ratio derived from the
    inherited gate height + ``pitch − CD``) → ``voided`` → a **functional** kill (like a killer particle,
    distinct from a parametric shift). (D1) An **under-etch** (``under_etch_frac > 0`` — an incomplete
    clear) leaves residual film that **bridges** the gate lines into a functional short
    (:func:`chip.etch_deposition.under_etch`) → ``bridged`` → a second **functional** kill (a *short*,
    the mirror of the void's *open*); at the default ``under_etch_frac = 0`` nothing bridges (the seam).

    The per-die etch-rate non-uniformity rides ``pert.etch_factor`` through the ``bias_factor`` hook (so
    it only moves the CD where the etch is non-ideal, ``anisotropy < 1``). Two graceful degradations
    (degrade, don't crash — like litho's ``resolved=False``): if the litho image did not resolve / no CD
    was produced upstream, the etch **passes through** untouched (``voided`` stays ``None``) so the
    device step still refuses; and if a runaway over-etch would consume the whole gate line, the die is
    marked a **functional** kill (``voided=True``) rather than raising. At the default knobs
    (``anisotropy = 1`` ⇒ zero bias, ``conformality = 1`` ⇒ no void) the CD passes through
    **bit-for-bit** and no die voids (the seam).
    """
    if die.cd_nm is None or die.resolved is False:
        reason = ("litho image not resolved" if die.resolved is False else "missing upstream CD")
        return die.record(
            "etch_deposition",
            knobs_in={"anisotropy": knobs.anisotropy, "over_etch_frac": knobs.over_etch_frac},
            outputs={"skipped": reason},
        )
    try:
        etch = ed.etch_feature(
            die.cd_nm,
            film_thickness_nm=knobs.film_thickness_nm, anisotropy=knobs.anisotropy,
            over_etch_frac=knobs.over_etch_frac, selectivity=knobs.selectivity,
            bias_factor=pert.etch_factor,
        )
        depo = ed.deposit_fill(
            etch.gate_height_nm, pitch_nm, etch.cd_out_nm, step_coverage=knobs.conformality,
        )
    except ValueError as exc:
        # A degenerate gate geometry — a runaway over-etch consumed the whole line, or the etched lines
        # touch (no gap to fill). No working gate → a functional kill (not a crash), like litho's refusal.
        return die.record(
            "etch_deposition",
            knobs_in={"anisotropy": knobs.anisotropy, "over_etch_frac": knobs.over_etch_frac,
                      "etch_factor": pert.etch_factor},
            outputs={"functional_fail": str(exc)},
            voided=True,
        )
    # D1 under-etch: an incomplete clear leaves residual film (UE·h) that bridges the gate lines into a
    # functional short once it exceeds the (flagged) threshold. Independent of the over-etch/void path
    # (over- and under-etch are mutually exclusive, guarded in the knobs); at the default UE=0 the
    # residual is 0 and nothing bridges (the seam — byte-for-byte the pre-D1 etch).
    ue = ed.under_etch(knobs.film_thickness_nm, knobs.under_etch_frac)
    outputs = {"resist_cd_nm": die.cd_nm, "cd_nm": etch.cd_out_nm, "etch_bias_nm": etch.etch_bias_nm,
               "gate_height_nm": etch.gate_height_nm, "underlayer_loss_nm": etch.underlayer_loss_nm,
               "aspect_ratio": depo.aspect_ratio, "critical_aspect_ratio": depo.critical_aspect_ratio,
               "voided": depo.voided, "bridged": ue.bridged}
    if ue.residual_nm > 0.0:                                 # only record the residual detail when under-etching
        outputs["residual_nm"] = ue.residual_nm
        outputs["bridge_threshold_nm"] = ue.bridge_threshold_nm
    return die.record(
        "etch_deposition",
        knobs_in={"anisotropy": knobs.anisotropy, "over_etch_frac": knobs.over_etch_frac,
                  "under_etch_frac": knobs.under_etch_frac,
                  "film_thickness_nm": knobs.film_thickness_nm, "conformality": knobs.conformality,
                  "etch_factor": pert.etch_factor},
        outputs=outputs,
        cd_nm=etch.cd_out_nm, gate_height_nm=etch.gate_height_nm, voided=depo.voided, bridged=ue.bridged,
    )


def device_step(
    die: Die, knobs: DeviceKnobs, channel_N_A: float, contamination: Contamination | None = None,
    thermal_donor_density: float = 0.0, dislocation_density: float = 0.0,
    sd_contact_squares: float = 0.0,
) -> Die:
    """Device extraction → ``V_t``, ``I_Dsat`` *and* lifetime/leakage, *reading the inherited* ``t_ox``, ``cd``, *contamination*.

    Three propagation reads: :func:`chip.device.threshold_voltage` consumes the local oxide thickness
    (sets ``V_t``) and the printed CD (the channel length — geometry only, ``I_Dsat ∝ W/L``, **not**
    ``V_t``); (G4a) the wafer's purified ``contamination`` drives the gate-oxide charge ``Q_ox =``
    :func:`chip.purification.sodium_oxide_charge` ``(Na)`` → a flat-band/``V_t`` shift (positive Na⁺
    pushes ``V_t`` **down**); and (G4b) the contamination's **deep-level metals** (Fe/Cu) drive the
    minority-carrier SRH lifetime → junction reverse leakage (:func:`chip.lifetime.device_leakage`) —
    the device output net doping cannot carry, so a metal-laden feed leaves ``V_t``/``I_Dsat`` fine but
    the diode **leaky**. The residual-dopant net shift is already folded into ``channel_N_A`` by the
    caller (``effective_channel_N_A``), so it is *not* re-applied here. If the litho image did not
    resolve (or no ``t_ox``/``cd`` was produced upstream), the device does not exist → the step
    **refuses** (leaves ``V_t``/``I_Dsat``/leakage ``None``) and records why; the test step scores that
    a functional fail. A clean/absent ``contamination`` ⇒ ``Q_ox = 0`` and ``τ = τ_bulk`` (baseline
    leakage) ⇒ the exact ``demo_device`` device call (``V_t``, ``I_Dsat`` bit-for-bit — the seam; the
    leakage is purely additive and never moves ``V_t``/``I_Dsat``).

    ``thermal_donor_density`` (cm⁻³, C1) is the wafer's crucible-oxygen → ~450 °C thermal-donor density
    already **subtracted** from ``channel_N_A`` by the caller (``effective_channel_N_A``), so ``V_t`` is
    not re-shifted here — it is recorded only so the failure trail can name the donor compensation as a
    ``V_t`` root cause (the C1 fingerprint, like ``Q_ox`` for Na). Defaults to ``0.0`` (no donors → the
    seam — the record key is added only when donors are present, so a clean device record is unchanged).

    ``dislocation_density`` (cm⁻², A1) is this die's grown-in interstitial-side dislocation population
    (a too-slow Czochralski pull, ``ξ < ξ_t`` — :meth:`CzochralskiKnobs.interstitial_dislocation_density_at`,
    keyed on the die's ``radius_frac`` so the A2 radial **rim** is leaky per die). It is a *second
    contributor* to the same SRH leakage channel as the deep-level metals (``1/τ += K·ρ_disl``) and, like
    them, **never moves** ``V_t``/``I_Dsat`` — slow pull makes the diode leaky, not the threshold wrong.
    Defaults to ``0.0`` (vacancy/boundary growth or CG-2 off → the seam; the ``rho_disl`` record key is
    added only when dislocations are present, so a vacancy/clean device record is byte-for-byte unchanged).

    ``sd_contact_squares`` (the diffusion-journey consumer) is the S/D series-resistance geometry
    ``n_□ = L_access/W``: combined with the **inherited** junction sheet resistance ``die.R_s`` (set by the
    diffusion step) it gives the parasitic **source** series resistance ``R_series = R_s·n_□`` fed to
    :func:`chip.device.saturation_current` as source degeneration — so a shallow, under-diffused junction
    (high ``R_s``) **starves** ``I_Dsat`` (the fourth propagation read, after ``t_ox``/CD/contamination).
    It **never** touches ``V_t`` (series resistance degrades drive, not threshold). Defaults to ``0.0`` →
    ``R_series = 0`` → the ideal-contact closed form, byte-for-byte the prior ``I_Dsat`` (the seam; the
    ``R_series_ohm`` record key is added only when engaged, so a clean device record is unchanged).

    **Junction avalanche breakdown (slice 2)** — the drain–body junction's reverse breakdown ``BV``
    (:func:`chip.breakdown.junction_breakdown`), read off the body doping ``channel_N_A`` (the lighter-doped
    side) and the **inherited** S/D junction depth ``die.x_j_um`` (the curvature radius). It is the consumer
    that finally makes the diffusion **depth** a device number (``x_j`` fed nothing scored before): a shallow
    junction crowds the field at its cylindrical edge → a **low** ``BV``, a deeper one relaxes toward the
    plane-parallel ceiling. ``BV`` is a *purely additive* output — like the leakage it **never moves**
    ``V_t``/``I_Dsat``, and it is scored only by the HV-I/O target's optional ``bv`` window (fast-logic /
    low-power leave it open), so the seam and the G1–G7 banked demos are byte-for-byte unchanged (the
    ``bv_V`` field/record key is set only when the junction was resolved upstream; a die with no ``x_j`` —
    a bare/hand-built die — carries ``bv_V = None`` and no key)."""
    if die.t_ox_um is None or die.cd_um is None or die.resolved is False:
        reason = ("litho image not resolved" if die.resolved is False
                  else "missing upstream t_ox/CD")
        return die.record(
            "device",
            knobs_in={"gate": knobs.gate, "width_um": knobs.width_um, "overdrive_V": knobs.overdrive_V},
            outputs={"refused": reason},
        )
    Q_ox = 0.0 if contamination is None else sodium_oxide_charge(contamination.Na)
    mos = dev.threshold_voltage(
        channel_N_A, die.t_ox_um, gate=knobs.gate, channel_length_um=die.cd_um, Q_ox=Q_ox,
    )
    # S/D series resistance (the diffusion-dose consumer): R_series = inherited R_s × the contact-square
    # count. 0 when off (n_□ = 0 the seam) or before the junction is read (die.R_s is None) → the ideal
    # saturation_current. Source degeneration then degrades only the drive current, never V_t.
    R_series_ohm = die.R_s * sd_contact_squares if (sd_contact_squares > 0.0 and die.R_s is not None) else 0.0
    i_dsat = dev.saturation_current(
        mos, mos.V_t + knobs.overdrive_V, knobs.width_um, R_series_ohm=R_series_ohm)
    # G4b/A1: the SRH lifetime → junction reverse leakage. Two contributors on the same channel — the
    # deep-level metals (G4b) and a slow-pull grown-in dislocation population (A1, ξ < ξ_t) — both add to
    # 1/τ; clean feed grown on the vacancy side ⇒ τ_bulk + baseline (the seam, dislocation_density = 0).
    leak = life.device_leakage(contamination, channel_N_A, dislocation_density=dislocation_density)
    # Junction avalanche breakdown (slice 2): the drain–body BV off the body doping + the inherited S/D
    # junction depth. Only when the junction was **resolved** upstream — a bare die (x_j None) OR an
    # unresolved junction (x_j nan, when the profile never crosses N_B) carries bv_V = None (the gap-vs-zero
    # distinction; nan must be screened too — it slips past breakdown's r_j>0 guard). Purely additive: never
    # moves V_t/I_Dsat.
    bv_V = (bd.junction_breakdown(channel_N_A, die.x_j_um).bv
            if die.x_j_um is not None and math.isfinite(die.x_j_um) else None)
    knobs_in = {"gate": knobs.gate, "width_um": knobs.width_um, "overdrive_V": knobs.overdrive_V,
                "Q_ox": Q_ox, "N_A": channel_N_A}
    if thermal_donor_density > 0.0:                          # C1 fingerprint — only when donors are present
        knobs_in["N_TD"] = thermal_donor_density            # (so a clean device record is byte-unchanged)
    if dislocation_density > 0.0:                            # A1 fingerprint — only on the interstitial side
        knobs_in["rho_disl"] = dislocation_density           # (so a vacancy/clean device record is byte-unchanged)
    if R_series_ohm > 0.0:                                   # diffusion fingerprint — only when the consumer is on
        knobs_in["R_series_ohm"] = R_series_ohm              # (so an ideal-contact device record is byte-unchanged)
    outputs = {"V_t": mos.V_t, "i_dsat": i_dsat, "C_ox": mos.C_ox,
               "tau_us": leak.tau_us, "j_leak_nA_cm2": leak.j_leak_nA_cm2}
    if bv_V is not None:                                     # slice-2 BV — only when the junction was resolved
        outputs["bv_V"] = bv_V                              # (so a no-x_j device record is byte-unchanged)
    return die.record(
        "device",
        knobs_in=knobs_in,
        outputs=outputs,
        V_t=mos.V_t, i_dsat=i_dsat, tau=leak.tau, j_leak=leak.j_leak, bv_V=bv_V,
    )


def packaging_step(die: Die, knobs: PackagingKnobs, survived: bool, bins: SpeedBins) -> Die:
    """Back-end packaging & final test on one die (G6) — assemble, then bin by speed (the funnel's end).

    The line's last step, run **after** wafer sort (the ``test`` step's per-die verdict). Only a
    **front-end-good** die is packaged; a die that already failed (parametric / functional) is **not**
    re-processed (it carries no assembly outcome — its verdict and bin stay as the front-end left them,
    so the funnel never double-counts it as an assembly scrap). For a good die:

    * **Assembly** (dice → attach → wire-bond → encapsulate): ``survived`` is the pre-drawn per-die
      Bernoulli outcome against the cumulative :attr:`PackagingKnobs.assembly_yield` (the funnel,
      :func:`chip.packaging.assembly_yield`); a part that does **not** survive is a back-end
      **functional kill** (``assembled=False``, the verdict flips to a fail) — irreversible (a cracked /
      lifted-bond die is scrap, the plan's "cracked die = scrap").
    * **Binning** (final test): a surviving part is sorted by its drive current (``I_Dsat`` as the
      **speed proxy**) into a :class:`SpeedBins` grade. A part below the slowest sellable bin is a
      **bin-out** — a *working but out-of-grade* reject (the verdict flips to a fail, ``bin="reject"``),
      distinct from a front-end parametric fail.

    At the default knobs (``assembly_yield = 1`` ⇒ ``survived`` always True; one open bin ⇒ no reject)
    the step is the **identity**: every front-end-good die packages, bins to the single ``"pass"`` grade,
    and its verdict is untouched — so the seam and the G1–G5 banked demos are byte-for-byte unchanged.
    Records the outcome on the append-only history regardless (every die saw every step).
    """
    knobs_in = {"assembly_yield": knobs.assembly_yield, "step_yields": knobs.step_yields}
    # A front-end-failed (or untested) die is not packaged — it carries no assembly outcome.
    if die.verdict is None or die.verdict.failed:
        return die.record("packaging", knobs_in=knobs_in,
                          outputs={"packaged": False, "reason": "front-end fail — not assembled"})
    # Assembly: a non-surviving part is a back-end functional kill (irreversible scrap).
    if not survived:
        v = Verdict(False, ("assembly scrap — back-end functional kill (dice/bond); cracked die = scrap",))
        return die.record("packaging", knobs_in=knobs_in,
                          outputs={"packaged": True, "assembled": False, "verdict": "assembly scrap"},
                          assembled=False, verdict=v)
    # Final test: bin the surviving part by I_Dsat (the speed proxy); a too-slow part bins out.
    label = bins.assign(die.i_dsat_mA)
    if bins.is_reject(label):
        v = Verdict(False, (f"binned out — I_Dsat {die.i_dsat_mA:.2f} mA below the slowest sellable bin "
                            f"(a working but out-of-grade part)",))
        return die.record("packaging", knobs_in=knobs_in,
                          outputs={"packaged": True, "assembled": True, "bin": label,
                                   "i_dsat_mA": die.i_dsat_mA},
                          assembled=True, bin=label, verdict=v)
    return die.record("packaging", knobs_in=knobs_in,
                      outputs={"packaged": True, "assembled": True, "bin": label,
                               "i_dsat_mA": die.i_dsat_mA},
                      assembled=True, bin=label)
