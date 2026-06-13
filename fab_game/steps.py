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
from chip import oxidation as ox
from chip import litho
from chip import device as dev
from chip.junction import analyze_junction
from chip.wafer_prep import WaferGeometry

from .recipe import DeviceKnobs, DiffusionKnobs, LithoKnobs, OxidationKnobs
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


def device_step(die: Die, knobs: DeviceKnobs, channel_N_A: float) -> Die:
    """Device extraction → ``V_t`` and ``I_Dsat``, *reading the inherited* ``t_ox`` *and* ``cd``.

    This read is the propagation: :func:`chip.device.threshold_voltage` consumes the local oxide
    thickness (sets ``V_t``) and the printed CD (the channel length — geometry only, ``I_Dsat ∝
    W/L``, **not** ``V_t``). If the litho image did not resolve (or no ``t_ox``/``cd`` was produced
    upstream), the device does not exist → the step **refuses** (leaves ``V_t``/``I_Dsat`` ``None``)
    and records why; the test step scores that a functional fail. Identity perturbation ⇒ the exact
    ``demo_device`` device call (``V_t``, ``I_Dsat`` bit-for-bit).
    """
    if die.t_ox_um is None or die.cd_um is None or die.resolved is False:
        reason = ("litho image not resolved" if die.resolved is False
                  else "missing upstream t_ox/CD")
        return die.record(
            "device",
            knobs_in={"gate": knobs.gate, "width_um": knobs.width_um, "overdrive_V": knobs.overdrive_V},
            outputs={"refused": reason},
        )
    mos = dev.threshold_voltage(
        channel_N_A, die.t_ox_um, gate=knobs.gate, channel_length_um=die.cd_um,
    )
    i_dsat = dev.saturation_current(mos, mos.V_t + knobs.overdrive_V, knobs.width_um)
    return die.record(
        "device",
        knobs_in={"gate": knobs.gate, "width_um": knobs.width_um, "overdrive_V": knobs.overdrive_V},
        outputs={"V_t": mos.V_t, "i_dsat": i_dsat, "C_ox": mos.C_ox},
        V_t=mos.V_t, i_dsat=i_dsat,
    )
