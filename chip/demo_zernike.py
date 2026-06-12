"""The v1.10 anchor demo: lithographic **Zernike aberrations** — coma, astigmatism & spherical.

Phase 3's §-named "aberration-free pupil apart from defocus" scope edge, **promoted**. v1.4 showed how
focus runs out; this shows the *shape* errors a real lens adds on top — and like defocus each is a pure
**phase** on the pupil (:func:`litho.zernike_phase`), so the same Fourier-optics machinery images through
them with no new path. Three panels, one per aberration — each its *named signature*, the thing that
makes it that aberration and not another:

  * **Coma → pattern placement error (left).** The ODD ``3u³−2u`` phase gives the diffraction orders
    *opposite*-sign delays, so the printed fringe **shifts sideways** — a feature lands off its design
    position. The unaberrated image (centred) vs the comatic image (displaced); the shift Δx grows
    linearly with the coma coefficient (inset). This is *overlay* error, not a contrast loss.
  * **Astigmatism → the H↔V best-focus split (middle).** The EVEN ``u²·cos2φ_g`` phase flips sign
    between horizontal (``φ_g=0``) and vertical (``φ_g=90°``) lines, so the two orientations reach best
    focus at **opposite defocus planes**. The through-focus fundamental peaks straddle ``z=0`` — a plain
    defocus offset would move both the same way, so this split is what tells astigmatism *from* a focus
    error (and why you cannot focus H and V features at once).
  * **Spherical → pitch-dependent best focus (right).** The EVEN ``6u⁴−6u²`` phase carries a built-in
    ``−6u²`` defocus that weights the orders by *where* they ride the pupil — so best focus **drifts with
    pitch**. Best-focus ``z`` vs pitch slopes under spherical but is pinned flat at ``z=0`` unaberrated:
    you cannot focus a mix of feature sizes simultaneously.

System: **193 nm ArF**, **NA 0.85** (dry), on-axis coherent imaging of a {0, ±1} three-beam pitch (so the
exact three-beam closed form holds and the signatures are clean). Aberration coefficients are in **waves**
of wavefront error; for scale, the Maréchal "diffraction-limited" criterion is an RMS wavefront error
below ≈ λ/14 ≈ 0.07 waves (cited, ``[[litho-aerial-image-source]]`` — not asserted as a Strehl number the
1-D slice model cannot honestly resolve). Reference facts (Mack / Born & Wolf / Noll, cited not
redistributed): the balanced low-order Zernike polynomials and their litho signatures.

Run headless (saves the figure, prints the table):

    python -m chip.demo_zernike
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import litho

# The demo system — the demo_litho / demo_defocus 193 nm ArF (dry) stepper, now imaged through a
# Zernike-aberrated pupil. On-axis coherent (σ=0) keeps the three-beam closed form, so each signature
# is the clean mechanism, not a partial-coherence average.
WAVELENGTH_NM = 193.0          # ArF excimer (DUV)
NA = 0.85                      # dry ArF projection-lens numerical aperture
PITCH_NM = 350.0               # a {0, ±1} three-beam pitch (λ/NA = 227 nm < 350 < 3λ/NA = 681 nm)
DUTY = 0.5
C0, C1 = 0.5, 1.0 / np.pi      # the 50%-duty grating's DC and 1st-order amplitudes

# Representative aberration coefficients (waves) — a few × the Maréchal λ/14 ≈ 0.07-wave floor, so each
# signature is visible. Illustrative magnitudes, not a real lens spec.
COMA_DEMO = 0.15               # the placement-error panel coefficient
COMA_SWEEP = np.linspace(0.0, 0.25, 26)   # placement error grows linearly with coma
ASTIG_DEMO = 0.25              # the H↔V split coefficient
SPHERICAL_DEMO = 0.08          # the pitch-dependent-focus coefficient (kept small: best focus stays in window)

# The defocus sweep (astigmatism / spherical best-focus search).
DEFOCUS_RANGE_NM = 220.0
N_DEFOCUS = 441
# Three {0,±1} three-beam pitches (all < 3λ/NA = 681 nm) for the spherical through-focus family — fine to
# coarse, so their best-focus planes are visibly different (the pitch-dependent-focus signature).
SPHERICAL_PITCHES_NM = (290.0, 340.0, 390.0)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-zernike.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-zernike.png"


def _on_axis(img: "litho.Imaging"):
    return litho.on_axis_source()


def _placement_error_nm(img: "litho.Imaging", coma: float) -> float:
    """The lateral fringe shift (nm) of the three-beam image under x-coma — the pattern-placement error.

    The comatic image fundamental is ``cos(2πx/p + φ_c)`` with ``φ_c`` the +1 order's coma phase, so the
    fringe (and the printed feature) shifts by ``Δx = −φ_c·p/2π`` — read straight off the complex
    fundamental's phase (:func:`litho.fundamental_complex`), the quadrature signal coma carries and
    defocus does not.
    """
    x = np.linspace(0.0, PITCH_NM, 256, endpoint=False)
    orders = litho.grating_orders(PITCH_NM, duty=DUTY)
    I = litho.abbe_image(x, orders, img, source_fs=_on_axis(img),
                         aberrations=litho.Aberrations(coma=coma))
    phi_c = float(np.angle(litho.fundamental_complex(x, I, PITCH_NM)))
    return -phi_c * PITCH_NM / (2.0 * np.pi)


def _fundamental_through_focus(img: "litho.Imaging", ab_for: "callable", zabs: np.ndarray,
                               pitch_nm: float = PITCH_NM) -> np.ndarray:
    """|fundamental| vs defocus for an aberration built per-z by ``ab_for`` (None ⇒ unaberrated)."""
    x = np.linspace(0.0, pitch_nm, 256, endpoint=False)
    orders = litho.grating_orders(pitch_nm, duty=DUTY)
    return np.array([abs(litho.fundamental_complex(
        x, litho.abbe_image(x, orders, img, source_fs=_on_axis(img), defocus_nm=z,
                            aberrations=ab_for(z)), pitch_nm)) for z in zabs])


def _signed_fundamental_through_focus(img: "litho.Imaging", aberration, pitch_nm: float,
                                      zabs: np.ndarray) -> np.ndarray:
    """The *signed* fundamental (real part = 4c₀c₁cos φ_tot) vs defocus — the principal focus lobe is its
    positive peak (clean for the EVEN spherical, whose image is symmetric so there is no quadrature)."""
    x = np.linspace(0.0, pitch_nm, 256, endpoint=False)
    orders = litho.grating_orders(pitch_nm, duty=DUTY)
    return np.array([litho.fundamental_amplitude(
        x, litho.abbe_image(x, orders, img, source_fs=_on_axis(img), defocus_nm=z,
                            aberrations=aberration), pitch_nm) for z in zabs])


def compute():
    """Run the demo: the coma placement error, the astigmatism H↔V split, the spherical pitch drift.

    Returns a dict of plain arrays/scalars the figure and the summary consume (ADR 0002 — no live object).
    """
    img = litho.Imaging(WAVELENGTH_NM, NA, sigma=0.0)
    zabs = np.linspace(-DEFOCUS_RANGE_NM, DEFOCUS_RANGE_NM, N_DEFOCUS)
    x = np.linspace(0.0, PITCH_NM, 256, endpoint=False)
    orders = litho.grating_orders(PITCH_NM, duty=DUTY)

    # --- coma: the placement error ------------------------------------------------------
    image_clean = litho.abbe_image(x, orders, img, source_fs=_on_axis(img))
    image_coma = litho.abbe_image(x, orders, img, source_fs=_on_axis(img),
                                  aberrations=litho.Aberrations(coma=COMA_DEMO))
    placement_demo = _placement_error_nm(img, COMA_DEMO)
    placement_sweep = np.array([_placement_error_nm(img, c) for c in COMA_SWEEP])

    # --- astigmatism: the H↔V best-focus split -----------------------------------------
    fund_h = _fundamental_through_focus(
        img, lambda z: litho.Aberrations(astigmatism=ASTIG_DEMO, grating_azimuth_deg=0.0), zabs)
    fund_v = _fundamental_through_focus(
        img, lambda z: litho.Aberrations(astigmatism=ASTIG_DEMO, grating_azimuth_deg=90.0), zabs)
    bf_h = float(zabs[int(np.argmax(fund_h))])
    bf_v = float(zabs[int(np.argmax(fund_v))])

    # --- spherical: best focus shifts with pitch (a through-focus family) --------------
    sph = litho.Aberrations(spherical=SPHERICAL_DEMO)
    sph_curves, sph_bf, flat_bf = {}, {}, {}
    for pp in SPHERICAL_PITCHES_NM:
        c = _signed_fundamental_through_focus(img, sph, pp, zabs)
        sph_curves[pp] = c
        sph_bf[pp] = float(zabs[int(np.argmax(c))])
        flat = _signed_fundamental_through_focus(img, None, pp, zabs)
        flat_bf[pp] = float(zabs[int(np.argmax(flat))])

    return dict(
        img=img, x=x, zabs=zabs, pitch=PITCH_NM,
        image_clean=image_clean, image_coma=image_coma,
        coma_demo=COMA_DEMO, placement_demo=placement_demo,
        coma_sweep=COMA_SWEEP, placement_sweep=placement_sweep,
        astig_demo=ASTIG_DEMO, fund_h=fund_h, fund_v=fund_v, bf_h=bf_h, bf_v=bf_v,
        spherical_demo=SPHERICAL_DEMO, spherical_pitches=SPHERICAL_PITCHES_NM,
        sph_curves=sph_curves, sph_bf=sph_bf, flat_bf=flat_bf,
        marechal_waves=1.0 / 14.0,
    )


def print_summary(data) -> None:
    """Print the three-aberration story — the demo's payoff in text."""
    print(f"\nLithographic Zernike aberrations — λ = {WAVELENGTH_NM:.0f} nm (ArF), NA = {NA:.2f}, "
          f"on-axis, pitch = {PITCH_NM:.0f} nm\n")
    print(f"  (scale: the Maréchal diffraction-limit floor is RMS wavefront ≈ λ/14 ≈ "
          f"{data['marechal_waves']:.3f} waves)\n")

    print(f"  Coma  ({data['coma_demo']:.2f} waves)  → pattern PLACEMENT error (the fringe shifts):")
    print(f"    Δx = {data['placement_demo']:+.1f} nm  ({data['placement_demo']/PITCH_NM*100:+.1f} % of "
          f"pitch) — overlay error, not contrast loss\n")

    print(f"  Astigmatism  ({data['astig_demo']:.2f} waves)  → the H↔V best-focus SPLIT:")
    print(f"    horizontal (φ_g=0°)  best focus z = {data['bf_h']:+.0f} nm")
    print(f"    vertical   (φ_g=90°) best focus z = {data['bf_v']:+.0f} nm")
    print(f"    split = {abs(data['bf_h'] - data['bf_v']):.0f} nm — opposite planes (a defocus offset "
          f"cannot do this)\n")

    print(f"  Spherical  ({data['spherical_demo']:.2f} waves)  → PITCH-dependent best focus:")
    for pp in data["spherical_pitches"]:
        print(f"    pitch {pp:.0f} nm:  best focus z = {data['sph_bf'][pp]:+.0f} nm   "
              f"(unaberrated: {data['flat_bf'][pp]:+.0f} nm)")
    bfs = [data["sph_bf"][pp] for pp in data["spherical_pitches"]]
    print(f"    → best focus moves {max(bfs)-min(bfs):.0f} nm across the pitch range; unaberrated it is "
          f"pinned at z=0 (pitch-independent)\n")
    print(f"  → coma moves features sideways, astigmatism and spherical move best FOCUS — by orientation")
    print(f"    and by pitch respectively. All three are pure pupil phase (power conserved, unitary).\n")


def save_figure(data) -> Path:
    """Render and save the Zernike artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                                # headless
    from .plots import zernike_figure

    fig = zernike_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, pitch_nm=PITCH_NM)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")         # λ, σ, φ, →, ₂, Maréchal on legacy codepages

    data = compute()
    print_summary(data)
    try:
        saved = save_figure(data)
        print(f"Figure saved → {saved.relative_to(_REPO_ROOT)}")
    except ImportError:
        print("(matplotlib not installed — install the viz extra to render the figure: "
              "pip install -e .[viz])")


if __name__ == "__main__":
    main()
