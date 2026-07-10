"""Period lithography — the wavelength/tool ladder & proximity-gap printing (historical-modes A2).

The **backward axis** (``docs/plans/historical-modes.md``): the simulator's pattern-transfer step, run in
two *period* configurations, so the limitations that motivated their successors become visible on the CD /
contrast / NILS observables :mod:`chip.litho` already computes. Like :mod:`chip.doping_history` (A1) and
:mod:`chip.oxidation_history` (A3), this is a **pure consumer** — it changes *no* existing behaviour and adds
no physics to ``litho.py``. Two orthogonal modes in one chunk (orthogonal because §A is the *projection*
model re-parameterised while §B is a *different* optical regime — shadow printing):

The two modes and their observables
-----------------------------------
* **§A — the wavelength / lens ladder → the Rayleigh CD floor (pure reuse).** g-line 436 → i-line 365 → KrF
  248 → ArF 193 → ArF-immersion (193i) → EUV 13.5: each generation moves the resolvable half-pitch
  ``R = k₁·λ/NA`` the sim already computes. The contrast is the *same feature imaged at each era's λ/NA* —
  from unresolved (a fat, flat g-line image) to crisp (ArF/EUV). This mode is **the existing projection
  model, re-parameterised**: :func:`image_at_node` is literally :func:`chip.litho.expose_grating` at that
  node's :class:`chip.litho.Imaging`. The **modern default node is ArF ``(193 nm, NA 0.85, σ 0.5)``** — the
  representative DUV stepper :mod:`chip.demo_litho` already uses — so "run A2 at the modern node" reproduces
  today's litho **bit-for-bit** (the seam is a real reduction, not a wrapper artefact).

* **§B — contact / proximity / projection printing → the gap-diffraction blur (the one small new model).**
  Before projection steppers, masks were printed in **contact** or held a small **proximity gap** ``g`` from
  the wafer — *shadow printing*, no lens. Near-field (Fresnel) diffraction over the gap blurs the shadow on a
  characteristic length ``≈ √(λ·g)`` (the cited proximity resolution limit — Levinson, *Principles of
  Lithography* §1; Madou), so the printable half-pitch cannot go below ``~√(λg)``. Modelled consumer-side as
  a **Gaussian blur of the binary mask shadow** of length ``σ = √(λg)`` — and, like the v1.7 PEB bake, that
  blur *rides the diffusion engine*: :func:`proximity_image` diffuses the true 0/1 mask through
  :func:`chip.litho.peb_blur` in **backward-Euler** mode, whose discrete maximum principle keeps the blurred
  shadow ``≥ 0`` (a sharp binary step is **not** band-limited, so a Crank–Nicolson kernel would ring negative
  — the honest reason for BE here; magnitudes are flagged anyway). A *second* optical reason litho leans on
  the program's PDE. **Contact (``g = 0``) → ``σ = 0`` → the sharp binary shadow bit-for-bit** (the
  degenerate seam); a proximity gap blurs it, and the wall is the monotone **contrast / NILS** collapse (the
  CD stays symmetry-pinned at the mean-clip until it abruptly stops resolving — so the live discriminators
  are contrast/NILS, not CD; Trap 2 of the build note). Projection (a lens with a pupil, §A) is the successor
  that broke the ``√(λg)`` floor.

The honesty ladder (per ``historical-modes.md`` triad)
------------------------------------------------------
* **Tight — §A.** (1) The seam: :func:`image_at_node` at the default ArF node **is**
  :func:`chip.litho.expose_grating` (byte-identical). (2) A **formula property**: ``R = k₁·λ/NA`` is strictly
  monotone in the ratio ``λ/NA`` — a smaller ``λ/NA`` always resolves a finer half-pitch (sign-robust, no
  table needed).
* **Tight — §B.** (1) The seam: ``gap = 0`` (contact) returns the unblurred binary mask shadow bit-for-bit
  (:func:`chip.litho.peb_blur` never touches the engine at ``σ = 0``). (2) **Conservation:** the diffusion
  blur preserves the total (the mask's clear fraction / image mean) exactly at every gap — no-flux faces
  neither add nor remove light. (3) The **sign/monotonicity**: a larger gap ⇒ larger ``σ`` ⇒ lower
  contrast/NILS (the ``√(λg)`` wall), and the blurred shadow stays ``≥ 0`` (the BE max-principle).
* **Flagged — the magnitudes.** (a) The **per-node NA table** (:data:`NODES`) — representative historical
  values, not a law; so "the *historical ladder's* ``λ/NA`` decreases g→EUV" is a **flagged** consequence of
  that table, kept separate from the tight formula-monotonicity above. (b) The **Fresnel prefactor**
  ``k ≈ 1`` in ``σ = k·√(λg)`` (:data:`FRESNEL_K`) — house-set, well-founded (the grating dies right where
  the half-pitch ≈ ``√(λg)``, the cited limit), but named not asserted exact.

Named scope edges (honest ceilings, stated so the omission isn't silent)
------------------------------------------------------------------------
* **§B — a blur envelope, not the Talbot near-field.** The Fresnel near-field of a *periodic* mask self-images
  (the Talbot effect); its contrast oscillates with gap. This module models the **monotone blur envelope**
  ``√(λg)`` — the teaching resolution scaling — not the oscillatory ``|E(x,g)|²`` field. And it blurs the
  binary *intensity* transmission (the incoherent shadow-print stand-in), not the coherent amplitude; the
  BE diffusion is a Gaussian-envelope stand-in (~6× the CN kernel error, but ring-free — the flagged-magnitude
  trade the §B honesty ladder already names).
* **§B — contact's real wall is defectivity, not blur.** Contact printing (``g = 0``) images sharply here; its
  historical failure was **mask wear / defect printing** from touching the wafer — a defectivity effect (cf.
  the G3 yield map), not an image-blur one, and not modelled. The gap-diffraction wall is the *proximity* one.
* **§A — the scalar model overstates immersion & EUV.** ``litho.py`` is scalar diffraction (its own named
  edge); immersion (NA > 1) needs the vector/polarised treatment and EUV is reflective optics in vacuum with
  its own resist. The 193i and EUV nodes here carry only their **λ/NA point on the scalar curve** — a
  representative resolution floor, not a faithful image of those systems.
* **§A — the node carries only λ/NA/σ.** Resist generation (A4), mask type (binary vs PSM), OPC, and off-axis
  illumination all moved per era too; a node abstracts none of them — it is the exposure optics only.

Units — inherited from :mod:`chip.litho` (nm-native)
----------------------------------------------------
Wavelength λ, pitch, position, resolution, blur length σ all **nm** (litho-native); the proximity **gap** is
quoted in **µm** at the recipe boundary (aligner gaps are microns) and converted to nm internally for
``√(λg)``. CD is reported in nm (and µm via :attr:`chip.litho.PrintedFeature.cd_um`). NA, σ, contrast, NILS
are dimensionless.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import litho

UM_PER_NM = litho.UM_PER_NM
NM_PER_UM = 1.0e3

# --------------------------------------------------------------------------- #
# §A. The wavelength / lens ladder — the projection model, re-parameterised
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LithoNode:
    """One rung of the exposure-tool ladder: a wavelength + lens NA + partial coherence + its era.

    ``wavelength_nm`` the exposure λ (436 g-line … 13.5 EUV); ``NA`` the projection-lens numerical
    aperture; ``sigma`` the partial-coherence factor. :attr:`imaging` is the :class:`chip.litho.Imaging`
    the projection model runs on, so a node *is* a recipe knob-set the existing engine already consumes.
    The NA values are **representative historical** numbers (flagged, :data:`NODES`), not a law.
    """

    name: str
    wavelength_nm: float
    NA: float
    era: str
    sigma: float = 0.5

    @property
    def imaging(self) -> litho.Imaging:
        """The :class:`chip.litho.Imaging` this node feeds the projection model (recipe → engine)."""
        return litho.Imaging(self.wavelength_nm, self.NA, self.sigma)

    def resolution(self, k1: float = litho.K1_COHERENT) -> float:
        """Rayleigh resolvable half-pitch ``R = k₁·λ/NA`` (nm) at this node (default conventional k₁=0.5)."""
        return litho.rayleigh_resolution(self.wavelength_nm, self.NA, k1)


# The historical exposure-tool ladder, in era order. NA/σ are REPRESENTATIVE period values (flagged —
# real tools spanned a range at each node); the tight leg is the R = k₁λ/NA formula-monotonicity, not
# these numbers. ArF is the DEFAULT/modern node and matches chip.demo_litho's stepper exactly
# (193 nm, NA 0.85, σ 0.5) so "A2 at the modern node" = today's litho bit-for-bit (the seam).
NODES: dict[str, LithoNode] = {
    "g-line": LithoNode("g-line (Hg)", 436.0, 0.28, "≈1978"),
    "i-line": LithoNode("i-line (Hg)", 365.0, 0.45, "≈1990"),
    "KrF":    LithoNode("KrF (DUV)", 248.0, 0.60, "≈1998"),
    "ArF":    LithoNode("ArF (DUV)", 193.0, 0.85, "≈2003"),          # ← modern default (demo_litho's stepper)
    "ArFi":   LithoNode("ArF immersion", 193.0, 1.35, "≈2007"),
    "EUV":    LithoNode("EUV", 13.5, 0.33, "≈2019"),
}
DEFAULT_NODE = "ArF"                                                  # the modern/seam node


def get_node(node: LithoNode | str) -> LithoNode:
    """Resolve a node key (or pass a :class:`LithoNode` through) — the string-or-object idiom."""
    return node if isinstance(node, LithoNode) else NODES[node]


def image_at_node(
    node: LithoNode | str,
    pitch_nm: float,
    *,
    source_fs=None,
    n_source: int = 21,
    n_orders: int = 15,
    duty: float = 0.5,
    threshold: float | None = None,
    n_x: int = 512,
) -> litho.PrintedFeature:
    """Image a line/space grating at ``node``'s exposure optics — **is** :func:`chip.litho.expose_grating`.

    The §A workhorse: project the same grating through each era's λ/NA and read the printed feature
    (contrast, NILS, CD). Because it forwards straight to :func:`chip.litho.expose_grating` on
    ``node.imaging``, the **default ArF node reproduces :mod:`chip.demo_litho` bit-for-bit** (the seam) —
    no new physics, just the recipe knob-set of a different era. Sweep ``node`` at fixed ``pitch_nm`` for
    the "same feature, different generation" contrast; sweep ``pitch_nm`` at fixed ``node`` for that
    era's contrast-vs-pitch resolution wall.
    """
    n = get_node(node)
    return litho.expose_grating(
        n.imaging, pitch_nm, source_fs=source_fs, n_source=n_source,
        n_orders=n_orders, duty=duty, threshold=threshold, n_x=n_x,
    )


# --------------------------------------------------------------------------- #
# §B. Contact / proximity printing — the Fresnel gap-diffraction blur (√(λg))
# --------------------------------------------------------------------------- #
# The cited proximity resolution limit: the smallest printable half-pitch in shadow printing scales as
# √(λ·g) (Levinson, Principles of Lithography §1.4; Madou). Modelled here as a periodic Gaussian blur of
# the mask of length σ = k·√(λg) — well-founded because the grating fundamental dies right when the
# half-pitch ≈ √(λg) (so k ≈ 1), but the prefactor is FLAGGED house calibration, not asserted exact.
FRESNEL_K = 1.0                    # FLAGGED — the σ = k·√(λg) prefactor (grating dies at half-pitch ≈ √(λg))


def fresnel_blur_length(wavelength_nm: float, gap_um: float, k: float = FRESNEL_K) -> float:
    """Proximity gap-diffraction blur length ``σ = k·√(λ·g)`` (nm) — the cited near-field scale.

    ``gap_um`` is the mask-to-wafer proximity gap in **µm** (aligner gaps are microns), converted to nm
    for the ``√(λ·g)`` (both lengths nm → σ nm). ``gap_um = 0`` (contact) → ``σ = 0`` (no blur — the
    seam). The blur *grows as √gap*, so the printable feature ``~√(λg)`` degrades slowly but never
    beats the near-field floor: the reason contact/proximity aligners hit a resolution wall.
    """
    if wavelength_nm <= 0.0:
        raise ValueError(f"wavelength_nm must be > 0, got {wavelength_nm}")
    if gap_um < 0.0:
        raise ValueError(f"gap_um must be ≥ 0, got {gap_um}")
    return k * math.sqrt(wavelength_nm * gap_um * NM_PER_UM)


def proximity_resolution_gap(pitch_nm: float, wavelength_nm: float, k: float = FRESNEL_K) -> float:
    """The proximity gap (µm) at which ``σ`` reaches the feature half-pitch — the ``√(λg)`` limit, inverted.

    Setting the blur length ``σ = k·√(λg)`` equal to the half-pitch ``p/2`` and solving for the gap:
    ``g = (p/2k)² / λ`` (µm). Beyond this gap the blur exceeds the feature and the grating stops
    resolving — the cited proximity-printing resolution limit as a *maximum usable gap* for a given pitch.
    """
    half_pitch_nm = pitch_nm / 2.0
    gap_nm = (half_pitch_nm / k) ** 2 / wavelength_nm
    return gap_nm / NM_PER_UM


def proximity_grid(pitch_nm: float, n_x: int) -> np.ndarray:
    """The cell-center sampling of one period ``[0, pitch]`` — ``x_i = (i+½)·Δx`` (the peb_blur domain)."""
    return (np.arange(n_x) + 0.5) * (pitch_nm / n_x)


def binary_mask(x_nm, pitch_nm: float, duty: float = 0.5) -> np.ndarray:
    """The ideal binary line/space shadow: 1 in the clear opening (centered on the lattice), 0 in chrome.

    The clear opening of width ``duty·pitch`` is centered on each lattice point ``0, p, 2p, …`` (so the
    pattern is even about both ``x = 0`` and ``x = pitch`` — the no-flux mirror planes the blur needs). A
    plain 0/1 array — the *true* mask, not a truncated Fourier series (which is why the blur below cannot
    ring). ``duty = 0.5`` gives equal lines and spaces.
    """
    if not 0.0 < duty < 1.0:
        raise ValueError(f"duty must be in (0, 1), got {duty}")
    x = np.asarray(x_nm, dtype=float) % pitch_nm
    dist_to_lattice = np.minimum(x, pitch_nm - x)          # distance to the nearest clear-center (0 or p)
    return (dist_to_lattice < duty * pitch_nm / 2.0).astype(float)


def proximity_image(
    pitch_nm: float,
    wavelength_nm: float,
    gap_um: float,
    *,
    duty: float = 0.5,
    n_x: int = 512,
    k: float = FRESNEL_K,
    n_steps: int = 200,
) -> np.ndarray:
    """The shadow-printed image of a line/space mask at proximity gap ``gap_um`` — the ``√(λg)`` blur.

    Builds the true binary mask (:func:`binary_mask`) on the cell-center grid (:func:`proximity_grid`) and
    diffuses it through :func:`chip.litho.peb_blur` in **backward-Euler** mode over one period ``[0, pitch]``
    (no-flux faces = the mask's mirror planes), with diffusion length ``σ = k·√(λg)``
    (:func:`fresnel_blur_length`). BE's discrete maximum principle keeps the blurred shadow ``≥ 0`` — a
    sharp binary step is not band-limited, so a Crank–Nicolson kernel would ring negative. The result is a
    real, even, periodic image the same metrics (:func:`chip.litho.image_contrast`, :func:`chip.litho.nils`,
    :func:`chip.litho.print_cd`) read. ``gap_um = 0`` → ``σ = 0`` → the sharp binary shadow **bit-for-bit**
    (:func:`chip.litho.peb_blur` returns its input untouched — the contact seam). Scope edge: a monotone
    blur envelope, not the Talbot oscillation (see the module docstring).
    """
    x = proximity_grid(pitch_nm, n_x)
    mask = binary_mask(x, pitch_nm, duty)
    sigma = fresnel_blur_length(wavelength_nm, gap_um, k)
    return litho.peb_blur(mask, pitch_nm, sigma, n_steps=n_steps, method="backward_euler")


@dataclass(frozen=True)
class ProximityPrint:
    """The line/space readout from one shadow-printed image at a proximity gap — *recipe → feature*.

    ``gap_um`` the mask-to-wafer gap; ``blur_length_nm`` the ``√(λg)`` diffraction blur σ; ``contrast``/
    ``nils`` the (live) image-quality discriminators that collapse with gap; ``cd_nm`` the constant-clip
    CD (symmetry-pinned at the mean until it stops resolving — the resolves/doesn't binary, not the live
    curve); ``resolved`` whether the image modulates at all. Plain scalars — the loose-coupling currency.
    """

    pitch_nm: float
    gap_um: float
    wavelength_nm: float
    blur_length_nm: float
    contrast: float
    nils: float
    cd_nm: float
    resolved: bool

    @property
    def cd_um(self) -> float:
        """Printed CD in micrometres (``cd_nm·1e-3``)."""
        return self.cd_nm * UM_PER_NM


def proximity_print(
    pitch_nm: float,
    gap_um: float = 0.0,
    *,
    wavelength_nm: float = 365.0,
    duty: float = 0.5,
    threshold: float | None = None,
    n_x: int = 512,
    k: float = FRESNEL_K,
) -> ProximityPrint:
    """Shadow-print a line/space grating at proximity gap ``gap_um`` → contrast / NILS / CD.

    The §B entry mirroring :func:`chip.litho.expose_grating`, but for the pre-projection **shadow-printing**
    regime: the near-field image is :func:`proximity_image` (a ``√(λg)`` Gaussian blur of the mask), and the
    same litho metrics read it. Defaults to **i-line (365 nm)** — a representative contact/proximity aligner
    wavelength — and ``gap_um = 0`` (**contact**, the sharp seam). Sweep ``gap_um`` at fixed pitch to watch
    contrast/NILS collapse toward the :func:`proximity_resolution_gap` wall. ``threshold`` defaults to the
    image mean (a balanced clip); the CD is symmetry-pinned there (Trap 2) so read the wall off contrast/NILS.
    """
    x = proximity_grid(pitch_nm, n_x)
    intensity = proximity_image(pitch_nm, wavelength_nm, gap_um, duty=duty, n_x=n_x, k=k)
    contrast = litho.image_contrast(intensity)
    edge_nm = duty * pitch_nm / 2.0
    linewidth_nm = (1.0 - duty) * pitch_nm
    image_nils = litho.nils(x, intensity, edge_nm, linewidth_nm)
    clip = float(intensity.mean()) if threshold is None else threshold
    cd = litho.print_cd(x, intensity, clip, polarity="dark")
    return ProximityPrint(
        pitch_nm=pitch_nm, gap_um=gap_um, wavelength_nm=wavelength_nm,
        blur_length_nm=fresnel_blur_length(wavelength_nm, gap_um, k),
        contrast=contrast, nils=image_nils, cd_nm=cd, resolved=contrast > 1.0e-3,
    )
