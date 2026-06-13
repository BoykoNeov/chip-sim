"""Etch / deposition: pattern-transfer etch bias + deposition step-coverage voids (mid-line).

The mid-line operations of the fab line proper (plan §5 step 7, §7; ADR 0005), and the physics the
fab-line game's **G5** consumes — *the missing mid-line operations between litho and the device,
phenomenological but honest.* This module is the plan's **flagged-phenomenology** tier (§7): unlike
Czochralski/Scheil or the SRH machinery, there is **no detailed-balance / only-possible-law
invariant** here. The honest ladder is therefore:

* the **bit-for-bit seam** is the one genuinely tight leg — a perfectly anisotropic, perfectly
  conformal process changes *nothing* (``anisotropy = 1`` ⇒ zero etch bias ⇒ the CD passes through
  unchanged; ``step_coverage = 1`` ⇒ no void), and that is structural (``(1 − A) = 0`` exactly), not
  a small number;
* the **algebra** (etch-bias geometry, over-etch underlayer bookkeeping, the gap aspect ratio) is
  **exact machinery** — asserted as *regression guards*, **not** dressed up as conservation anchors
  (there is nothing here like wafer-prep's area-additivity or SRH's ``pn = n_i²``);
* every **magnitude** (anisotropy, selectivity, step coverage, the pinch-off aspect ratio) is a
  **flagged house number** — only the *forms* are cited (Wolf & Tauber, *Silicon Processing for the
  VLSI Era* Vol. 1, etch/CVD chapters; Plummer–Deal–Griffin, *Silicon VLSI Technology* Ch. 10/9;
  Campbell, *Fabrication Engineering*). The game is scored on mechanics, not magnitudes (ADR 0005 §5).

Two sections, laddered honestly:

1. **Pattern-transfer etch — anisotropy → etch bias → CD (the cited form, the device consumer).** A
   plasma/RIE etch transfers the resist pattern into the gate film. The etch is **directional**: it
   removes material vertically at a rate, but a finite *lateral* component undercuts the mask. With
   **anisotropy** ``A = 1 − (lateral rate / vertical rate)`` ∈ ``[0, 1]`` (``A = 1`` perfectly
   anisotropic, ``A = 0`` fully isotropic / wet-like), a film of thickness ``h`` etched with an
   **over-etch** fraction ``OE`` (extra etch past endpoint, to clear residue despite non-uniformity —
   the etch is ``rate × time``, so ``OE`` *is* the fractional extra time) sees an equivalent vertical
   etch ``d = h·(1 + OE)``, a lateral undercut ``u = (1 − A)·d`` **per side**, and so an **etch bias**
   that shrinks an etched line::

       bias = 2·(1 − A)·h·(1 + OE)        CD_out = CD_in − bias                 (nm)

   At ``A = 1`` the bias is **0** for any depth — pattern transfer is exact (the seam). With ``A < 1``,
   *more over-etch deepens the etch and so widens the undercut* → the printed CD shrinks → a shorter
   channel → the device's ``I_Dsat ∝ W/L`` rises (the "over-etch → CD out of spec" failure of plan
   §5). Over-etch also **consumes the underlayer**: the excess ``OE·h`` divided by the etch
   **selectivity** ``S`` (film-rate / underlayer-rate) is the underlayer lost (``loss = OE·h/S``).

2. **Deposition step coverage — conformality vs aspect ratio → keyhole void (the yield consumer).**
   After the gate is etched it stands ``h`` tall on a ``pitch``; the gaps between gate lines (width
   ``pitch − CD``) must be filled by a later deposition (spacer / dielectric). A deposition's **step
   coverage** ``SC = sidewall-thickness / top-thickness`` ∈ ``[0, 1]`` decides whether it fills the
   gap or **pinches off** at the top, sealing a **keyhole void**. The gap's **aspect ratio**
   ``AR = h / (pitch − CD)`` is *derived from the inherited gate geometry* (a tighter pitch or a
   taller gate raises AR — a genuine propagation, not a free knob), and a non-conformal process voids
   once the aspect ratio exceeds what its coverage can fill::

       AR_crit(SC) = SC / (1 − SC)         void ⇔ AR > AR_crit                   (dimensionless)

   ``SC = 1`` (perfectly conformal CVD) → ``AR_crit = ∞`` → never voids (the seam); a poor
   line-of-sight PVD (``SC ≈ 0.3``) → ``AR_crit ≈ 0.43`` → voids any but the shallowest gap. The
   ``SC/(1 − SC)`` form is a **flagged illustrative** pinch-off rule (chosen for the right limits:
   ∞ as ``SC → 1``, 0 as ``SC → 0``), not a derived criterion — the magnitude is house, the *void
   when the top pinches before the bottom fills* mechanism is the cited physics. A void is a
   **functional** kill (an open / unfillable gap), wired in the game as a die that fails functionally
   — like a killer particle — *not* a parametric shift.

**CMP planarization — a named edge, deliberately not built here.** The plan titles this step "Etch &
deposition (+ CMP planarization)", but CMP has **no device consumer** in the 1-D-depth compact model:
its real consequences (dishing → metal opens; planarity → the *next* litho's depth-of-focus budget)
are unwired, and the TTV→focus budget is *already* a named scope edge in :mod:`chip.wafer_prep`.
Building a CMP physics module here would be physics for its own sake (the repo's anti-over-build bar —
the "build explicit, not 2-D" lesson). So CMP planarization is **named and deferred**, to land only
when the focus-budget wire it would feed is built. (Wafer-prep CMP — slicing flatness — is a separate,
already-built geometry step.)

Validation triad (plan §7) — what is asserted tight vs loose
------------------------------------------------------------
* **Analytical limit / seam (the one genuinely tight leg).** ``anisotropy = 1`` ⇒ ``bias = 0``
  **bit-for-bit** (``(1 − A) = 0`` exactly, so ``CD_out == CD_in`` to the last bit, for any film /
  over-etch); and ``step_coverage = 1`` ⇒ ``AR_crit = ∞`` ⇒ **no void** at any aspect ratio. This is
  the structural seam the whole G5 game wiring rides (the etch step is the identity at the default
  recipe), exactly as Czochralski's ``k → 1`` and the SRH ``N_metal = 0`` limits anchor their modules.
* **Machinery (regression guards — exact algebra, *not* a conservation anchor).** ``bias =
  2·(1 − A)·h·(1 + OE)``, the underlayer loss ``OE·h/S``, the gap aspect ratio ``h/(pitch − CD)``, and
  the monotonicities (more over-etch / less anisotropy → more CD loss; less step coverage / higher AR
  → a void) are all exact bookkeeping. They are framed as **regression guards** — there is no
  "only-possible-law" content here (unlike wafer-prep area-additivity or SRH detailed balance), so they
  are honest machinery checks, not asserted physics anchors (cf. G4b's "rate-additivity true by
  construction").
* **Benchmark (loose) — cited forms, flagged magnitudes.** The etch-bias / anisotropy / selectivity
  and the step-coverage / keyhole-void *forms* are the textbook ones (Wolf & Tauber; Plummer–Deal–
  Griffin; Campbell). The :data:`ETCH_ANISOTROPY` and :data:`STEP_COVERAGE` bands (RIE vs wet; CVD vs
  PVD) are **flagged illustrative** process levels — only the *ordering* (RIE ≫ wet anisotropy; CVD ≫
  PVD coverage) and the limits are asserted, never the numbers.

Named scope edge (the honest ceiling)
-------------------------------------
* **Under-etch is named, not modelled.** Plan §5 step 7 lists "over/under-etch"; this module builds the
  **over**-etch leg (``over_etch_frac ≥ 0`` → the film always clears, the undercut/CD story). The
  symmetric **under**-etch failure — an *incomplete clear* leaving residue / sidewall stringers that
  **bridge** adjacent gate lines into a functional short — is a **deferred scope edge** (it would land
  as a second functional kill, parallel to the deposition void, gated by an etch-completeness knob), not
  yet built. Named here so the plan's mechanism is accounted for, per the repo's anti-over-build bar.
* **Phenomenological, not a profile simulator.** No etch-profile / facet / RIE-lag / aspect-ratio-
  dependent-etch (ARDE) model, no Monte-Carlo deposition; the etch is a single scalar bias and the
  deposition a single void verdict. The cited forms set the *direction*; the magnitudes are house.
* **CMP planarization deferred** (above) — named, awaiting the focus-budget consumer.
* **The void is a binary verdict, not a partial fill.** A real keyhole is a continuum (seam → keyhole
  → full open); here it is pass/fail at the pinch-off aspect ratio. Resistance/open-circuit grading is
  out (no interconnect-resistance model in the compact device).

Units
-----
Lengths (film thickness, CD, pitch, bias, undercut, underlayer loss) in **nm**; anisotropy / step
coverage / over-etch fraction dimensionless; aspect ratio dimensionless. (The game converts the etched
CD to µm at the device boundary, as elsewhere.)

Validation boundary
-------------------
No shared engine — etch bias and the void criterion are closed forms (like Deal–Grove / Scheil / the
yield law), so this module's tests carry the whole triad: the ``A = 1`` / ``SC = 1`` seams (analytic),
the bias / underlayer / aspect-ratio algebra + monotonicities (machinery guards), and the cited forms
+ flagged process bands (benchmark). The stochastic etch-rate non-uniformity lives in the game layer
(:mod:`fab_game.variation`, a mechanics invariant), where the randomness belongs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Flagged process bands — illustrative house levels, NOT cited fab numbers.
# Only the *ordering* and the limits (A=1 / SC=1 = idealized seam) are asserted; the magnitudes are
# house (the game's etch/depo knob presets), exactly as wafer_prep's DEFECT_DENSITY_BANDS and
# purification's FEEDSTOCK_GRADES. The *forms* (anisotropy, step coverage) are the cited physics.
# --------------------------------------------------------------------------- #
ETCH_ANISOTROPY: dict[str, float] = {
    "ideal": 1.0,    # perfectly anisotropic — vertical-only etch (the idealized seam baseline)
    "RIE": 0.92,     # reactive-ion etch — highly directional, a small undercut
    "plasma": 0.7,   # a less-directional plasma etch — a noticeable bias
    "wet": 0.0,      # wet / fully isotropic — equal lateral & vertical (undercuts a masked line badly)
}

STEP_COVERAGE: dict[str, float] = {
    "ideal": 1.0,    # perfectly conformal — fills any gap (the idealized seam baseline)
    "CVD": 0.9,      # conformal CVD — near-perfect step coverage (high-AR fill)
    "LPCVD": 0.8,    # low-pressure CVD — good but finite coverage
    "PVD": 0.3,      # sputter / PVD — poor, line-of-sight coverage (voids all but shallow gaps)
}


# --------------------------------------------------------------------------- #
# 1. Pattern-transfer etch — anisotropy → etch bias → the transferred CD
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EtchResult:
    """The outcome of transferring a resist CD into a gate film by an anisotropic etch.

    ``cd_out_nm`` the etched (final, gate) CD the device reads; ``etch_bias_nm`` the total line-width
    loss (``2× undercut``); ``lateral_undercut_nm`` the per-side undercut; ``etch_depth_nm`` the
    equivalent vertical etch ``h·(1 + OE)``; ``underlayer_loss_nm`` the underlayer consumed by the
    over-etch; ``gate_height_nm`` the standing gate height (== the etched film thickness — what the
    deposition step's gap aspect ratio reads). All nm. At ``anisotropy = 1`` the bias is exactly 0 and
    ``cd_out_nm == cd_in_nm`` (the seam).
    """

    cd_out_nm: float
    etch_bias_nm: float
    lateral_undercut_nm: float
    etch_depth_nm: float
    underlayer_loss_nm: float
    gate_height_nm: float


def etch_feature(
    cd_in_nm: float,
    *,
    film_thickness_nm: float = 150.0,
    anisotropy: float = 1.0,
    over_etch_frac: float = 0.0,
    selectivity: float = 20.0,
    bias_factor: float = 1.0,
) -> EtchResult:
    """Transfer a resist line of width ``cd_in_nm`` into a gate film → the etched :class:`EtchResult`.

    The etch removes ``film_thickness_nm`` of film plus an **over-etch** ``over_etch_frac`` past the
    endpoint (the equivalent vertical etch is ``d = h·(1 + OE)`` — the etch is rate×time, so the
    over-etch is the fractional extra time). With **anisotropy** ``A`` ∈ ``[0, 1]`` the per-side
    lateral undercut is ``(1 − A)·d`` and the **etch bias** ``2·(1 − A)·d`` shrinks the line:
    ``cd_out = cd_in − bias``. The over-etch's excess ``OE·h`` consumes ``OE·h/selectivity`` of the
    underlayer. ``bias_factor`` (default 1.0) scales the undercut for the game's per-die etch-rate
    non-uniformity — a *consumer* hook, identity here (so the physics seam is untouched).

    At ``A = 1`` (perfectly anisotropic) the bias is **0** for any film / over-etch and ``cd_out ==
    cd_in`` **bit-for-bit** (the seam). Raises on a non-physical anisotropy / over-etch / selectivity
    or an etch that would consume the whole line (``bias ≥ cd_in`` — the gates would vanish).
    """
    if not 0.0 <= anisotropy <= 1.0:
        raise ValueError(f"anisotropy must be in [0, 1], got {anisotropy}")
    if over_etch_frac < 0.0:
        raise ValueError(f"over_etch_frac must be ≥ 0, got {over_etch_frac}")
    if selectivity <= 0.0:
        raise ValueError(f"selectivity must be > 0, got {selectivity}")
    if film_thickness_nm <= 0.0:
        raise ValueError(f"film_thickness_nm must be > 0, got {film_thickness_nm}")

    etch_depth = film_thickness_nm * (1.0 + over_etch_frac)
    lateral_undercut = (1.0 - anisotropy) * etch_depth * bias_factor
    bias = 2.0 * lateral_undercut
    cd_out = cd_in_nm - bias
    if cd_out <= 0.0:
        raise ValueError(
            f"etch bias {bias:.1f} nm ≥ CD {cd_in_nm:.1f} nm — the etch consumed the whole line "
            "(lower the over-etch or raise the anisotropy)")
    underlayer_loss = film_thickness_nm * over_etch_frac / selectivity
    return EtchResult(
        cd_out_nm=cd_out,
        etch_bias_nm=bias,
        lateral_undercut_nm=lateral_undercut,
        etch_depth_nm=etch_depth,
        underlayer_loss_nm=underlayer_loss,
        gate_height_nm=film_thickness_nm,
    )


# --------------------------------------------------------------------------- #
# 2. Deposition step coverage — conformality vs aspect ratio → keyhole void
# --------------------------------------------------------------------------- #
def gap_aspect_ratio(gate_height_nm: float, pitch_nm: float, cd_nm: float) -> float:
    """The aspect ratio ``AR = gate_height / (pitch − CD)`` of the gap between etched gate lines.

    Derived from the *inherited* gate geometry (height from the etch, the gap from pitch and the
    etched CD) — so a tighter pitch or a taller gate raises the aspect ratio the next deposition must
    fill (the propagation). Raises if the gap is non-positive (``CD ≥ pitch`` — the gate lines touch,
    there is no gap to fill).
    """
    gap = pitch_nm - cd_nm
    if gap <= 0.0:
        raise ValueError(
            f"gap width {gap:.1f} nm ≤ 0 (CD {cd_nm:.1f} nm ≥ pitch {pitch_nm:.1f} nm) — "
            "the gate lines touch, there is no gap to fill")
    return gate_height_nm / gap


def critical_aspect_ratio(step_coverage: float) -> float:
    """The maximum void-free aspect ratio ``AR_crit = SC / (1 − SC)`` for a deposition of coverage ``SC``.

    A **flagged illustrative** pinch-off rule (the form chosen for the right limits — ``∞`` as a
    perfectly conformal ``SC → 1``, ``0`` as a directionless ``SC → 0`` — not a derived criterion;
    the magnitude is house, the *void-when-the-top-pinches* mechanism is the cited physics). ``SC = 1``
    returns ``inf`` (a conformal CVD never voids — the seam). Raises on a non-physical coverage.
    """
    if not 0.0 <= step_coverage <= 1.0:
        raise ValueError(f"step_coverage must be in [0, 1], got {step_coverage}")
    if step_coverage >= 1.0:
        return math.inf
    return step_coverage / (1.0 - step_coverage)


@dataclass(frozen=True)
class DepositionResult:
    """The outcome of filling the gate gaps by a deposition of a given step coverage.

    ``aspect_ratio`` the gap AR the fill must cover; ``critical_aspect_ratio`` the most a coverage of
    ``step_coverage`` can fill void-free; ``voided`` True iff the gap pinches off into a keyhole
    (``AR > AR_crit``) — a **functional** kill. At ``step_coverage = 1`` (conformal) ``voided`` is
    always False (the seam).
    """

    aspect_ratio: float
    critical_aspect_ratio: float
    step_coverage: float
    voided: bool


def deposit_fill(
    gate_height_nm: float,
    pitch_nm: float,
    cd_nm: float,
    *,
    step_coverage: float = 1.0,
) -> DepositionResult:
    """Fill the gate gaps and decide whether the deposition **voids** → the :class:`DepositionResult`.

    Computes the gap aspect ratio from the inherited gate geometry (:func:`gap_aspect_ratio`) and
    compares it to what the coverage can fill (:func:`critical_aspect_ratio`): a void forms when the
    gap pinches off at the top before the bottom fills (``AR > AR_crit``). ``step_coverage = 1``
    (perfectly conformal) never voids (the seam). The void is a binary functional verdict (named scope
    edge: not a partial-fill / resistance grade).
    """
    ar = gap_aspect_ratio(gate_height_nm, pitch_nm, cd_nm)
    ar_crit = critical_aspect_ratio(step_coverage)
    return DepositionResult(
        aspect_ratio=ar,
        critical_aspect_ratio=ar_crit,
        step_coverage=step_coverage,
        voided=ar > ar_crit,
    )
