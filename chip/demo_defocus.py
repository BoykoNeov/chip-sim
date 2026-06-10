"""The v1.4 anchor demo: lithographic **defocus** — the Bossung curve & the depth of focus.

Phase 3's §-named "ideal in-focus pupil" scope edge, **promoted**. The resolution demo (`demo_litho`)
showed *how fine* a pitch a lens can print; this shows *how far out of focus* it can print it — the other
half of the litho budget. Defocus is a pure **phase** on the pupil (:func:`litho.defocus_phase`), so the
same Fourier-optics machinery images out of focus with no new path. Two stories on one figure:

  * **The banked readout (left) — the Bossung curve.** Printed **CD vs defocus** at a few fixed doses
    (the classic Bossung "smile" family), for a realistic σ-conventional source. The **process window**
    — the focus range that keeps the CD within ±10 % of target at the nominal dose — is shaded, and the
    Rayleigh ``DOF = k₂·λ/NA²`` marked. *Push NA for resolution (``λ/NA``) and the focus budget
    (``λ/NA²``) shrinks quadratically — the litho squeeze.*
  * **The mechanism (right) — why focus runs out.** The on-axis **three-beam fundamental** (the
    ``cos(2πx/p)`` modulation) vs defocus, lying exactly on the analytic ``4·c₀·c₁·cos φ`` envelope (the
    tight anchor, visualised) and **nulling at φ = π/2** = the depth-of-focus event. Past the null the
    fundamental reverses and the image is a pure **double-frequency** fringe (defocus-induced *frequency
    doubling / contrast reversal*). A partially-coherent (σ) source softens the null — partial coherence
    buys focus latitude, the focus analogue of its resolution gain.

System: **193 nm ArF**, **NA 0.85** (dry), **σ 0.5** conventional — the same DUV stepper as `demo_litho`,
imaging a **350 nm** line/space (a {0, ±1} three-beam pitch, so the exact envelope holds on-axis).
Reference facts (cited, not redistributed — the ``[[litho-aerial-image-source]]`` note: Mack / lithoguru):
``DOF = k₂·λ/NA²``, the Bossung focus-exposure picture, and the through-focus contrast reversal. ``k₂ = 0.5``
is *derived* from the φ=π/2 null at the resolution limit, not fit.

Run headless (saves the figure, prints the table):

    python -m chip.demo_defocus
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import litho

# The demo system — the demo_litho 193 nm ArF (dry) stepper, now imaged through focus.
WAVELENGTH_NM = 193.0          # ArF excimer (DUV)
NA = 0.85                      # dry ArF projection-lens numerical aperture
SIGMA = 0.5                    # conventional partial-coherence factor (the Bossung source)

# The grating: a 240 nm line/space — just above the coherent limit λ/NA (227 nm) and below 3λ/NA (681 nm),
# so on-axis coherent imaging collects EXACTLY {0, ±1} (the three-beam fundamental = the exact 4·c₀·c₁·cos φ
# anchor) AND the pitch is near the resolution limit, where ``DOF = k₂·λ/NA²`` is defined — so the φ=π/2
# fundamental null and the DOF marker sit at the same focus scale (a coarser pitch would tolerate more
# defocus than the resolution-limit DOF — the focus budget is a worst-case at the densest features).
PITCH_NM = 240.0
DUTY = 0.5
C0, C1 = 0.5, 1.0 / np.pi       # the 50%-duty grating's DC and 1st-order amplitudes

# The defocus sweep — symmetric about best focus, spanning ~±1.8·DOF so the null and the reversal show.
DEFOCUS_RANGE_NM = 250.0
N_DEFOCUS = 121

# The Bossung dose family: three fixed clips bracketing the in-focus mean → three target CDs.
DOSE_FRACTIONS = (0.40, 0.50, 0.60)   # clip level as a fraction of the in-focus (I_min, I_max) span
CD_SPEC = 0.10                        # ±10 % of target CD = the process-window edge

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-defocus.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-defocus.png"


def _defocus_axis() -> np.ndarray:
    return np.linspace(-DEFOCUS_RANGE_NM, DEFOCUS_RANGE_NM, N_DEFOCUS)


def _in_focus_levels(img: "litho.Imaging") -> tuple[float, float, dict]:
    """The in-focus image span and the absolute dose levels (from :data:`DOSE_FRACTIONS`)."""
    x = np.linspace(0.0, PITCH_NM, 512, endpoint=False)
    orders = litho.grating_orders(PITCH_NM, duty=DUTY)
    I = litho.abbe_image(x, orders, img, source_fs=litho.conventional_source(img))
    i_min, i_max = float(I.min()), float(I.max())
    doses = {f: i_min + f * (i_max - i_min) for f in DOSE_FRACTIONS}
    return i_min, i_max, doses


def _bossung(img: "litho.Imaging", doses: dict, zabs: np.ndarray) -> dict:
    """Printed CD vs defocus at each fixed dose — the Bossung family (σ source)."""
    out = {}
    for f, level in doses.items():
        out[f] = np.array([litho.expose_grating(img, PITCH_NM, threshold=level, duty=DUTY,
                                                 defocus_nm=z).cd_nm for z in zabs])
    return out


def _process_window(zabs: np.ndarray, cd_curve: np.ndarray) -> tuple[float, float] | None:
    """The contiguous defocus band about z=0 where CD stays within ±CD_SPEC of its best-focus value."""
    cd0 = float(np.interp(0.0, zabs, cd_curve))
    if cd0 <= 0:
        return None
    ok = np.abs(cd_curve - cd0) <= CD_SPEC * cd0
    i0 = int(np.argmin(np.abs(zabs)))               # the best-focus index
    if not ok[i0]:
        return None
    lo = i0
    while lo > 0 and ok[lo - 1]:
        lo -= 1
    hi = i0
    while hi < len(ok) - 1 and ok[hi + 1]:
        hi += 1
    return float(zabs[lo]), float(zabs[hi])


def _fundamental_through_focus(zabs: np.ndarray) -> dict:
    """The three-beam fundamental vs defocus: on-axis data, the analytic envelope, and the σ curve."""
    coh = litho.Imaging(WAVELENGTH_NM, NA, sigma=0.0)
    part = litho.Imaging(WAVELENGTH_NM, NA, sigma=SIGMA)
    x = np.linspace(0.0, PITCH_NM, 256, endpoint=False)
    orders = litho.grating_orders(PITCH_NM, duty=DUTY)
    cos_theta = np.sqrt(1.0 - (WAVELENGTH_NM / PITCH_NM) ** 2)        # the ±1 order's pupil cosθ
    phi = (2.0 * np.pi / WAVELENGTH_NM) * zabs * (1.0 - cos_theta)
    envelope = 4.0 * C0 * C1 * np.cos(phi)                            # the exact 4c₀c₁cos φ anchor
    on_axis = np.array([litho.fundamental_amplitude(
        x, litho.abbe_image(x, orders, coh, source_fs=litho.on_axis_source(), defocus_nm=z), PITCH_NM)
        for z in zabs])
    partial = np.array([litho.fundamental_amplitude(
        x, litho.abbe_image(x, orders, part, source_fs=litho.conventional_source(part), defocus_nm=z),
        PITCH_NM) for z in zabs])
    z_null = (np.pi / 2.0) / ((2.0 * np.pi / WAVELENGTH_NM) * (1.0 - cos_theta))   # the φ=π/2 DOF event
    return dict(on_axis=on_axis, envelope=envelope, partial=partial, z_null=z_null, cos_theta=cos_theta)


def compute():
    """Run the demo: the Bossung family + process window (left) and the fundamental through focus (right).

    Returns a dict of plain arrays/scalars the figure and the summary consume (ADR 0002 — no live object).
    """
    img = litho.Imaging(WAVELENGTH_NM, NA, sigma=SIGMA)
    zabs = _defocus_axis()
    i_min, i_max, doses = _in_focus_levels(img)
    bossung = _bossung(img, doses, zabs)
    window = _process_window(zabs, bossung[0.50])                    # the nominal (mid) dose
    fund = _fundamental_through_focus(zabs)
    dof = img.depth_of_focus()                                       # k₂·λ/NA²
    return dict(
        img=img, zabs=zabs, doses=doses, bossung=bossung, window=window,
        dof=dof, pitch=PITCH_NM, **fund,
    )


def print_summary(data) -> None:
    """Print the resolution-vs-focus story — the demo's payoff in text."""
    img = data["img"]
    print(f"\nLithographic defocus — λ = {WAVELENGTH_NM:.0f} nm (ArF), NA = {NA:.2f}, σ = {SIGMA:.2f}, "
          f"pitch = {PITCH_NM:.0f} nm\n")
    print(f"  Rayleigh depth of focus  DOF = k₂·λ/NA²  (k₂ = {litho.K2_DOF}):")
    print(f"    DOF = {data['dof']:.0f} nm   (resolution R = {img.resolution(0.5):.0f} nm at k₁=0.5 — "
          f"R∝λ/NA, DOF∝λ/NA²: the squeeze)")
    print(f"    exact φ=π/2 fundamental null at z = ±{data['z_null']:.0f} nm  (full cosθ; the DOF event)\n")
    if data["window"] is not None:
        lo, hi = data["window"]
        print(f"  Process window (CD within ±{CD_SPEC*100:.0f} % of target, nominal dose): "
              f"{hi - lo:.0f} nm of usable focus  [{lo:+.0f}, {hi:+.0f}] nm\n")
    print(f"  Bossung — printed CD vs defocus (σ = {SIGMA:.2f}):")
    zmarks = [0.0, 50.0, 100.0, 150.0, 200.0]
    header = "    {:>9}".format("dose\\z(nm)") + "".join(f"{z:>8.0f}" for z in zmarks)
    print(header)
    for f in DOSE_FRACTIONS:
        cds = [np.interp(z, data["zabs"], data["bossung"][f]) for z in zmarks]
        print(f"    {f*100:>7.0f} %  " + "".join(f"{c:>7.0f} " for c in cds))
    print()
    print(f"  → CD drifts and the fundamental fades as |z| grows; at z = ±{data['z_null']:.0f} nm the")
    print(f"    fundamental nulls and the image frequency-doubles (contrast reversal) — focus has run out.\n")


def save_figure(data) -> Path:
    """Render and save the defocus artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                                # headless
    from .plots import defocus_figure

    fig = defocus_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, sigma=SIGMA,
                         pitch_nm=PITCH_NM, dose_fractions=DOSE_FRACTIONS, cd_spec=CD_SPEC)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")         # λ, σ, φ, →, ₂ on legacy codepages

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
