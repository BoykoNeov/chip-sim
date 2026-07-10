"""Period photoresist generations — negative-resist swelling & the CD floor (historical-modes A4).

The **backward axis** (``docs/plans/historical-modes.md``): the simulator's *develop* step, run with a
**period resist chemistry** (negative, solvent-swelling) beside the modern ones (positive DQN/novolak,
and the DUV chemically-amplified successor), so the swelling limitation becomes visible on the CD / space
:mod:`chip.litho` already computes. Like :mod:`chip.doping_history` (A1), :mod:`chip.oxidation_history`
(A3) and :mod:`chip.litho_history` (A2), this is a **pure consumer** — it changes *no* existing behaviour
and adds no physics to ``litho.py``. Three resist generations developed on the **same aerial image**:

* **Negative (Kodak KTFR — the period resist, ≈1960s).** The *exposed* region **crosslinks** into the
  resist line (negative tone → the line prints where the image is *bright*); solvent development then makes
  that crosslinked network **absorb developer and swell**. The swollen line dilates outward, the space
  between lines shrinks, and below a pitch floor adjacent lines **bridge** — the cited negative-resist
  resolution wall. This is the one period mode.
* **Positive (DQN / novolak — the successor, ≈1975→) — the DEFAULT/modern chemistry.** The exposed region
  *dissolves* (no crosslink, no swell): the develop is exactly :func:`chip.litho.expose_grating`
  (``polarity="dark"`` — the resist line is the *un*-exposed dark fringe), so "develop with the modern
  resist" reproduces today's litho **bit-for-bit** (the seam).
* **CAR (chemically-amplified — the DUV successor, ≈1990s).** Delegated straight to the already-built
  :func:`chip.litho.expose_grating_car` (v1.9) — shown, not reimplemented.

Why the swelling is GEOMETRIC, not an engine ride (the honest call, per the build note)
----------------------------------------------------------------------------------------
A diffusion solve is **conservative and symmetric**; swelling **adds volume** (solvent uptake) and
**dilates** the line — non-conservative and asymmetric. Forcing swelling onto :mod:`engines.diffusion`
(blur the developed line, then re-threshold below the midpoint to make it grow) needs a *free contour
level* that silently absorbs the calibration — a fudge dressed as an engine ride, exactly the
``gradual-failure-preferred`` trap ("the fudge = inflating an unrelated variable"). Unlike A2 §B, where
the ``√(λg)`` blur *was* the physics, here the diffusion solve would carry nothing: **delete it and the CD
floor is unchanged**, because the floor is set by a fixed swelling length, not a blur. So the swelling
dilation is modelled as a **geometric edge displacement** ``s = swelling_factor · thickness`` (a fixed
length *per feature*, ∝ film thickness, **not** ∝ CD), and "reuse of the PEB/CAR machinery" is the
develop/metric path (:func:`chip.litho.print_cd`, :func:`chip.litho.image_contrast`, :func:`chip.litho.nils`)
plus the CAR successor — not a decorative solve.

The headline observable: an **optics-independent** floor (orthogonal to A2)
---------------------------------------------------------------------------
Because ``s ∝ thickness`` and nothing else, the swelling resolution floor ``≈ film thickness`` does **not**
move with λ or NA. A2 walked the Rayleigh floor ``k₁·λ/NA`` down the wavelength ladder; A4 shows a floor
the wavelength race **cannot touch** — sharpen the optics all you like and a negative line still bridges
near the film thickness. Only *changing the resist* (positive → CAR) removes it. The demo isolates the two
floors by developing the **same** fine aerial image as positive and negative: positive resolves to the
optical floor, negative bridges at the much coarser (thickness-set) swelling floor.

The honesty ladder (per ``historical-modes.md`` triad)
------------------------------------------------------
* **Tight.** (1) The **seam**: ``chemistry="positive"`` develops the aerial image with
  :func:`chip.litho.print_cd` (``polarity="dark"``) at the same mean clip as
  :func:`chip.litho.expose_grating` → the CD / contrast / NILS are **byte-identical**. (2) The
  **sign/topology of the limitation**: swelling only ever *grows* the negative line (``s ≥ 0``), so the
  space shrinks **monotonically** and, past the floor, bridges — the discriminator, sign-robust. (3) The
  **CAR delegation** is literally :func:`chip.litho.expose_grating_car` (no reimplementation). (4) The
  floor's **``∝ thickness`` law** and its **independence of λ/NA** (a property of the geometric model).
* **Flagged — the magnitude.** The swelling coefficient :data:`SWELLING_FACTOR` (``s = factor · thickness``)
  — house-set so the half-pitch floor lands near one film thickness (the cited KTFR rule of thumb —
  a negative line distorts once its width approaches the film thickness), named not asserted exact; and the
  representative :data:`RESIST_THICKNESS_NM`.

Named scope edges (honest ceilings, stated so the omission isn't silent)
------------------------------------------------------------------------
* **Swelling is a uniform lateral dilation, not a profile solve.** Real swelling is a differential
  volume uptake (the lower-crosslink line edge swells more than the core → the classic serpentine
  distortion); this models only the net outward edge displacement onto the CD/space observable. No 2-D
  resist volume, no aspect-ratio (thickness/CD) collapse beyond the ``∝ thickness`` floor.
* **Bridging is read as a per-feature cliff (space ≤ 0), with a named graded edge.** The *space width*
  approaches zero continuously (the graded quantity), but the short itself is taken at ``space = 0``. With
  line-edge non-uniformity the *fraction of features bridged* would smear that cliff (the
  ``gradual-failure-preferred`` move) — named here, not built (no swelling-length distribution knob).
* **The optical develop is the existing constant-threshold resist.** No Dill exposure kinetics, no Mack
  dissolution-rate development — those stay :mod:`chip.litho`'s own named edges; A4 only adds the
  post-develop *geometric* swelling of the negative line.

Units — inherited from :mod:`chip.litho` (nm-native)
----------------------------------------------------
Wavelength λ, pitch, CD, space, swelling length ``s``, film thickness all **nm** (litho-native); CD/space
are also reported in **µm** (the cross-module length currency). Contrast, NILS, duty are dimensionless.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import litho

UM_PER_NM = litho.UM_PER_NM

# --------------------------------------------------------------------------- #
# The swelling magnitude — a FIXED lateral edge displacement ∝ film thickness
# --------------------------------------------------------------------------- #
# The negative-resist resolution rule of thumb: a crosslinked line distorts / bridges once its width
# approaches the film thickness (Kodak KTFR and the rubber/bis-azide negatives — Thompson/Willson/Bowden,
# "Introduction to Microlithography"; Levinson §1). Modelled as a lateral swelling s = factor·thickness
# added to EACH edge of the developed line, so a 50%-duty half-pitch bridges at ≈ one film thickness with
# SWELLING_FACTOR = 0.5 (half_pitch_floor = 2·s/(... ) = thickness — see swelling_resolution_floor). The
# coefficient is FLAGGED house calibration to that cited rule, not asserted exact; the SIGN (swelling
# grows the line, shrinks the space) is the tight leg.
SWELLING_FACTOR = 0.5             # FLAGGED — s = factor·thickness per edge (half-pitch floor ≈ thickness)
RESIST_THICKNESS_NM = 1000.0      # ~1 µm — a representative era resist film (FLAGGED, a demo scale)

# CAR successor defaults — a partial-regime bake (small acid dose for a real bake, per the v1.9 note that
# acid_dose=1.0 saturates every pixel). Only used when chemistry="car" delegates to expose_grating_car.
CAR_BAKE_T_S = 30.0               # a representative CAR post-exposure bake time (s)
CAR_ACID_DOSE = 0.13              # photoacid as a small fraction of the blocked-site density (v1.9)


@dataclass(frozen=True)
class Resist:
    """One rung of the photoresist ladder: a chemistry, its develop tone, and whether it swells.

    ``tone`` selects the develop polarity — ``"positive"`` (exposed dissolves → the resist line is the
    *dark* fringe, :func:`chip.litho.expose_grating`'s tone; the modern default/seam), ``"negative"``
    (exposed crosslinks → the line is the *bright* fringe, and it **swells**), or ``"car"`` (delegated to
    :func:`chip.litho.expose_grating_car`). ``swells`` is the one physics axis: only the negative resist
    dilates its line in solvent develop. The NA/era are period texture, flagged.
    """

    name: str
    tone: str            # "positive" | "negative" | "car"
    swells: bool
    era: str
    note: str


# The photoresist generations, in era order. The one real physics axis is `swells` (only the negative
# resist). Positive is the DEFAULT/modern chemistry and reproduces litho.expose_grating bit-for-bit (seam).
RESISTS: dict[str, Resist] = {
    "positive": Resist("DQN / novolak (positive)", "positive", False, "≈1975→",
                       "exposed dissolves — no swell (the successor; the modern default)"),
    "negative": Resist("Kodak KTFR (negative)", "negative", True, "≈1960s",
                       "exposed crosslinks, then solvent-swells → the line dilates & bridges"),
    "car":      Resist("chemically-amplified (CAR)", "car", False, "≈1990s DUV",
                       "acid-amplified deprotection — the DUV successor (litho.expose_grating_car)"),
}
DEFAULT_RESIST = "positive"       # the modern/seam chemistry


def get_resist(resist: Resist | str) -> Resist:
    """Resolve a resist key (or pass a :class:`Resist` through) — the string-or-object idiom."""
    return resist if isinstance(resist, Resist) else RESISTS[resist]


# --------------------------------------------------------------------------- #
# The swelling geometry — a fixed edge displacement and the floor it sets
# --------------------------------------------------------------------------- #
def swell_length(thickness_nm: float = RESIST_THICKNESS_NM,
                 swelling_factor: float = SWELLING_FACTOR) -> float:
    """Lateral swelling per line edge ``s = swelling_factor · thickness`` (nm) — the FLAGGED magnitude.

    A **fixed length per feature**, proportional to the film thickness and independent of the CD (that
    independence is what makes the resolution floor ∝ thickness and *optics-independent*). ``factor = 0``
    (or a positive/CAR chemistry) → ``s = 0`` → no swelling (the seam). The swollen negative line grows by
    ``2·s`` (one ``s`` on each edge).
    """
    if thickness_nm < 0.0:
        raise ValueError(f"thickness_nm must be ≥ 0, got {thickness_nm}")
    if swelling_factor < 0.0:
        raise ValueError(f"swelling_factor must be ≥ 0, got {swelling_factor}")
    return swelling_factor * thickness_nm


def swelling_resolution_floor(thickness_nm: float = RESIST_THICKNESS_NM,
                              swelling_factor: float = SWELLING_FACTOR,
                              duty: float = 0.5) -> float:
    """The pitch below which a negative line/space **bridges** — the swelling wall (nm), optics-independent.

    The developed negative line (the exposed *clear* opening) is ``duty·pitch`` wide; swelling grows it to
    ``duty·pitch + 2·s``, so the space ``(1−duty)·pitch − 2·s`` vanishes at ``pitch = 2·s/(1−duty)``. Below
    that pitch the swollen lines touch → a short. The **half-pitch** floor is ``s/(1−duty)`` → exactly one
    film thickness at ``duty = 0.5`` and ``swelling_factor = 0.5`` (the cited "resolution ≈ thickness"
    rule). Depends only on ``s`` (∝ thickness) — **not** on λ or NA, the A4 headline.
    """
    if not 0.0 < duty < 1.0:
        raise ValueError(f"duty must be in (0, 1), got {duty}")
    return 2.0 * swell_length(thickness_nm, swelling_factor) / (1.0 - duty)


# --------------------------------------------------------------------------- #
# The develop readout — one aerial image, three resist chemistries
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ResistFeature:
    """The line/space readout from developing one aerial image in a given resist — *recipe → feature*.

    ``cd_nm`` the printed **resist-line** width (the *swollen* line for a negative resist); ``space_nm``
    the remaining gap between lines (``pitch − cd``, negative once bridged); ``contrast`` / ``nils`` the
    aerial-image quality (the *same* across tone at a given pitch — the swelling difference lives in
    ``cd``/``space``, not the optics); ``swell_length_nm`` the ``s`` added per edge (0 for positive/CAR);
    ``bridged`` whether the swollen lines have touched (``space ≤ 0`` — a negative-resist short);
    ``resolved`` whether a usable line/space survives. Plain scalars — the loose-coupling currency.
    """

    pitch_nm: float
    chemistry: str
    cd_nm: float
    space_nm: float
    contrast: float
    nils: float
    swell_length_nm: float
    bridged: bool
    resolved: bool

    @property
    def cd_um(self) -> float:
        """Printed resist-line CD in micrometres (``cd_nm·1e-3``) — the cross-module length currency."""
        return self.cd_nm * UM_PER_NM

    @property
    def space_um(self) -> float:
        """Remaining space between lines in micrometres."""
        return self.space_nm * UM_PER_NM


def _aerial(imaging: litho.Imaging, pitch_nm: float, duty: float, n_x: int,
            source_fs, n_source: int, n_orders: int):
    """The aerial image over one period — the exact non-PEB path of :func:`chip.litho.expose_grating`.

    Replicates ``expose_grating``'s in-focus, unaberrated construction (``grating_orders`` → ``abbe_image``
    on ``linspace(0, pitch, n_x, endpoint=False)``) so a positive develop off this image is byte-identical
    to ``expose_grating`` (the seam). Returns ``(x, intensity)``.
    """
    orders = litho.grating_orders(pitch_nm, n_orders=n_orders, duty=duty)
    x = np.linspace(0.0, pitch_nm, n_x, endpoint=False)
    intensity = litho.abbe_image(x, orders, imaging, source_fs=source_fs, n_source=n_source)
    return x, intensity


def develop_resist(
    imaging: litho.Imaging,
    pitch_nm: float,
    chemistry: Resist | str = DEFAULT_RESIST,
    *,
    thickness_nm: float = RESIST_THICKNESS_NM,
    swelling_factor: float = SWELLING_FACTOR,
    duty: float = 0.5,
    threshold: float | None = None,
    source_fs=None,
    n_source: int = 21,
    n_orders: int = 15,
    n_x: int = 512,
) -> ResistFeature:
    """Develop one aerial image in ``chemistry`` → the printed line/space (with negative-resist swelling).

    The A4 workhorse. **Positive** (default) develops the aerial image with :func:`chip.litho.print_cd`
    (``polarity="dark"``) at the image-mean clip — byte-identical to :func:`chip.litho.expose_grating`
    (the seam). **Negative** develops the *bright* (exposed, crosslinked) line, then adds the geometric
    swelling ``2·s`` (``s =`` :func:`swell_length`) to its width — the line dilates, the space shrinks, and
    once ``space ≤ 0`` the lines **bridge**. **CAR** delegates straight to
    :func:`chip.litho.expose_grating_car` (the DUV successor, shown not reimplemented). Sweep ``pitch_nm``
    at a fixed fine ``imaging`` to watch the negative line bridge at the thickness-set swelling floor while
    the positive line still resolves to the (much finer) optical floor — the A4 contrast.
    """
    resist = get_resist(chemistry)

    if resist.tone == "car":
        bake = litho.CARBake(t_bake_s=CAR_BAKE_T_S)
        car = litho.expose_grating_car(imaging, pitch_nm, bake, source_fs=source_fs, n_source=n_source,
                                       n_orders=n_orders, duty=duty, acid_dose=CAR_ACID_DOSE, n_x=n_x)
        return ResistFeature(
            pitch_nm=pitch_nm, chemistry="car", cd_nm=car.cd_nm, space_nm=pitch_nm - car.cd_nm,
            contrast=car.contrast, nils=car.nils, swell_length_nm=0.0, bridged=False,
            resolved=car.resolved,
        )

    x, intensity = _aerial(imaging, pitch_nm, duty, n_x, source_fs, n_source, n_orders)
    contrast = litho.image_contrast(intensity)
    edge_nm = duty * pitch_nm / 2.0
    linewidth_nm = (1.0 - duty) * pitch_nm
    image_nils = litho.nils(x, intensity, edge_nm, linewidth_nm)
    clip = float(intensity.mean()) if threshold is None else threshold

    # The dark (unexposed) line width — the positive resist's printed line, and litho.expose_grating's
    # own readout (the seam). The bright (exposed) line is its complement at a single clip: exactly two
    # crossings partition the period, so bright + dark = pitch (and the bright feature straddles the period
    # boundary, so it can't be read directly by print_cd's "interior feature" contract — the complement is).
    dark_cd = litho.print_cd(x, intensity, clip, polarity="dark")
    if resist.tone == "negative":
        # The exposed (bright) region crosslinks into the line; then it swells outward by 2·s per edge.
        base_cd = (pitch_nm - dark_cd) if dark_cd > 0.0 else 0.0
        s = swell_length(thickness_nm, swelling_factor)
        cd = base_cd + 2.0 * s if base_cd > 0.0 else 0.0
    else:  # positive — the seam: exactly expose_grating's dark-line develop, no swell
        cd = dark_cd
        s = 0.0

    space = pitch_nm - cd
    bridged = resist.swells and cd > 0.0 and space <= 0.0
    resolved = contrast > 1.0e-3 and cd > 0.0 and not bridged
    return ResistFeature(
        pitch_nm=pitch_nm, chemistry=resist.tone, cd_nm=cd, space_nm=space,
        contrast=contrast, nils=image_nils, swell_length_nm=s, bridged=bridged, resolved=resolved,
    )
