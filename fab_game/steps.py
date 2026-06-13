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

from chip import diffusion_dopant as dd
from chip import etch_deposition as ed
from chip import oxidation as ox
from chip import litho
from chip import device as dev
from chip import lifetime as life
from chip.junction import analyze_junction
from chip.purification import Contamination, sodium_oxide_charge
from chip.wafer_prep import WaferGeometry

from .recipe import DeviceKnobs, DiffusionKnobs, EtchDepositionKnobs, LithoKnobs, OxidationKnobs
from .state import DefectEvent, Die
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
        length_um=knobs.length_um,
    )
    junc = analyze_junction(drivein, knobs.dopant, channel_N_A)
    knobs_in = {"dopant": knobs.dopant, "T_drivein_C": knobs.T_drivein_C,
                "t_drivein_min": knobs.t_drivein_min}
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
    distinct from a parametric shift).

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
    return die.record(
        "etch_deposition",
        knobs_in={"anisotropy": knobs.anisotropy, "over_etch_frac": knobs.over_etch_frac,
                  "film_thickness_nm": knobs.film_thickness_nm, "conformality": knobs.conformality,
                  "etch_factor": pert.etch_factor},
        outputs={"resist_cd_nm": die.cd_nm, "cd_nm": etch.cd_out_nm, "etch_bias_nm": etch.etch_bias_nm,
                 "gate_height_nm": etch.gate_height_nm, "underlayer_loss_nm": etch.underlayer_loss_nm,
                 "aspect_ratio": depo.aspect_ratio, "critical_aspect_ratio": depo.critical_aspect_ratio,
                 "voided": depo.voided},
        cd_nm=etch.cd_out_nm, gate_height_nm=etch.gate_height_nm, voided=depo.voided,
    )


def device_step(
    die: Die, knobs: DeviceKnobs, channel_N_A: float, contamination: Contamination | None = None,
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
    """
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
    i_dsat = dev.saturation_current(mos, mos.V_t + knobs.overdrive_V, knobs.width_um)
    # G4b: the deep-level metals' SRH lifetime → junction reverse leakage (clean ⇒ τ_bulk + baseline).
    leak = life.device_leakage(contamination, channel_N_A)
    return die.record(
        "device",
        knobs_in={"gate": knobs.gate, "width_um": knobs.width_um, "overdrive_V": knobs.overdrive_V,
                  "Q_ox": Q_ox, "N_A": channel_N_A},
        outputs={"V_t": mos.V_t, "i_dsat": i_dsat, "C_ox": mos.C_ox,
                 "tau_us": leak.tau_us, "j_leak_nA_cm2": leak.j_leak_nA_cm2},
        V_t=mos.V_t, i_dsat=i_dsat, tau=leak.tau, j_leak=leak.j_leak,
    )
