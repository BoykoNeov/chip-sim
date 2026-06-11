"""The v1.7 anchor demo: **PEB acid-diffusion blur** — the bake's trade-off and the PEB window.

Phase 3's §-named "constant-threshold resist (no acid diffusion / PEB blur)" scope edge, **promoted** —
and the architecture finding inverts litho's founding line: the post-exposure bake IS a diffusion
solve, so the chip's one module that "does not touch the engine" now runs its resist back-end on
``engines.diffusion`` in **acid mode** (:func:`litho.peb_blur` — ``u`` = latent acid, ``Neumann(0)``
sealed faces, the cited BC). Two stories on one figure:

  * **The banked readout (left) — the latent image dissolving.** The aerial image at 240 nm pitch and
    its post-bake latent images over the cited 20/40/60 nm diffusion-length series (Mack's PEB
    smoothing illustration): the harmonics die as ``exp(−2π²k²σ²/p²)`` (k² — blur is
    harmonic-selective), the profile collapses toward its conserved mean, and the printed CD walks
    onto the pure-fundamental ``p/2`` readout. The clip dose is the image mean — **blur-invariant**
    (the conservation leg made visible: the bake redistributes acid, it never makes or loses it).
  * **The mechanism (right) — the PEB window.** Retention vs σ for the two things one bake must do at
    once: erase the **standing-wave depth ripple** (period ``λ/2n`` — :func:`litho.standing_wave_period`,
    Mack eq. (12); blurred by the *same* ``peb_blur`` along ``z``) and keep the **lateral image
    fundamental** (period ``p``). Engine-computed points ride the two analytic heat-kernel envelopes;
    the cited **half-period rule** (σ ≥ λ/4n, Mack's glossary) marks the smoothing floor, and the
    **window** [erase the ripple, keep ≥½ the fundamental] is shaded. The window **closes near
    ~151 nm pitch** (numerically beside this system's optical cutoff — a coincidence of parameters,
    not a law); at NA 0.93 the lens out-resolves the bake (145 nm images, but cannot survive a
    ridge-erasing bake) — why modern stacks attack reflectivity with a BARC (the cited mitigation
    list: ARC / dye / PEB) instead of leaning harder on the bake.

System: **193 nm ArF**, **NA 0.85** (dry), **σ 0.5** conventional — the same DUV stepper as
`demo_litho`/`demo_defocus` — imaging a **240 nm** line/space; resist index **n = 1.70**
(representative; only ``λ/2n`` is load-bearing). Reference facts (cited, not rederived — the
``[[peb-acid-diffusion-source]]`` note: Mack / Kirchauer): ``σ = √(2Dt)``, the Gaussian-kernel
solution, the sealed-film Neumann BC, the 20/40/60 nm series, the half-period smoothing rule, the
``λ/2n`` ripple period, the ARC/dye/PEB mitigation list.

Run headless (saves the figure, prints the table):

    python -m chip.demo_peb
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import litho

# The demo system — the demo_litho/demo_defocus 193 nm ArF (dry) stepper, now with a baked resist.
WAVELENGTH_NM = 193.0          # ArF excimer (DUV)
NA = 0.85                      # dry ArF projection-lens numerical aperture
SIGMA_SRC = 0.5                # conventional partial-coherence factor
PITCH_NM = 240.0               # dense-but-resolved line/space (CD = 120 nm), the defocus-demo pitch
DUTY = 0.5
N_X = 512

# The resist: a representative ArF-resist refractive index (illustrative — only λ/2n is load-bearing)
# and a film four standing-wave periods thick, so the depth ripple is a clean Neumann eigenmode.
N_RESIST = 1.70
RIPPLE_SWING = 0.4             # illustrative standing-wave modulation (amplitude is substrate-dependent)
N_Z = 512

# The σ sweep: 0 → just past the cited 20/40/60 nm series (the family the left panel draws).
SIGMA_MAX_NM = 60.0
N_SIGMA = 41
KEEP_FLOOR = 0.5               # the illustrative "keep ≥ half the fundamental" window ceiling

# The lens that out-resolves the bake (the closure punchline): the max dry-ArF NA, still scalar-honest.
NA_HI = 0.93
PITCH_DENSE_NM = 145.0

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-peb.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-peb.png"


def _offset_grid(pitch_nm: float, n_x: int) -> np.ndarray:
    """One period sampled at half-offset cell centers — the PEB path's grid (faces at 0 and p/2)."""
    return (np.arange(n_x) + 0.5) * (pitch_nm / n_x)


def _aerial(img: "litho.Imaging", pitch_nm: float, n_x: int = N_X) -> tuple[np.ndarray, np.ndarray]:
    orders = litho.grating_orders(pitch_nm, duty=DUTY)
    x = _offset_grid(pitch_nm, n_x)
    return x, litho.abbe_image(x, orders, img, source_fs=litho.conventional_source(img))


def _bake(aerial: np.ndarray, pitch_nm: float, sigma_nm: float) -> np.ndarray:
    """The expose_grating PEB pipeline, bare: half-period engine blur, mirrored back to the period."""
    half = aerial.size // 2
    blurred = litho.peb_blur(aerial[:half], pitch_nm / 2.0, sigma_nm)
    return np.concatenate([blurred, blurred[::-1]])


def _fundamental_retention(img: "litho.Imaging", pitch_nm: float, sigmas: np.ndarray) -> np.ndarray:
    """Engine-computed lateral-fundamental retention b₁(σ)/b₁(0) at each diffusion length."""
    x, aerial = _aerial(img, pitch_nm)
    b0 = litho.fundamental_amplitude(x, aerial, pitch_nm)
    return np.array([litho.fundamental_amplitude(x, _bake(aerial, pitch_nm, s), pitch_nm) / b0
                     for s in sigmas])


def _ripple_retention(period_nm: float, film_nm: float, sigmas: np.ndarray) -> np.ndarray:
    """Engine-computed standing-wave ripple retention along z (same peb_blur, film-depth domain)."""
    z = (np.arange(N_Z) + 0.5) * (film_nm / N_Z)
    ripple = 1.0 + RIPPLE_SWING * np.cos(2.0 * np.pi * z / period_nm)
    swing0 = ripple.max() - ripple.min()
    out = []
    for s in sigmas:
        baked = litho.peb_blur(ripple, film_nm, s)
        out.append((baked.max() - baked.min()) / swing0)
    return np.array(out)


def compute():
    """Run the demo: the baked-image family (left) and the PEB window (right).

    Returns a dict of plain arrays/scalars the figure and the summary consume (ADR 0002 — no live object).
    """
    img = litho.Imaging(WAVELENGTH_NM, NA, sigma=SIGMA_SRC)
    t_sw = litho.standing_wave_period(WAVELENGTH_NM, N_RESIST)
    sigma_rule = 0.5 * t_sw                                  # the cited half-period smoothing floor
    film_nm = 4.0 * t_sw

    # Left panel: the aerial image + the cited-series baked family, and their printed features.
    x, aerial = _aerial(img, PITCH_NM)
    family_sigmas = (0.0,) + litho.PEB_DIFFUSION_SERIES_NM
    family = {s: (aerial if s == 0.0 else _bake(aerial, PITCH_NM, s)) for s in family_sigmas}
    dose = float(aerial.mean())                              # the mean clip — blur-invariant
    features = {s: litho.expose_grating(img, PITCH_NM, peb_diffusion_length_nm=s)
                for s in family_sigmas}

    # Right panel: engine retention points riding the analytic heat-kernel envelopes.
    sigmas = np.linspace(0.0, SIGMA_MAX_NM, N_SIGMA)
    keep_engine = _fundamental_retention(img, PITCH_NM, sigmas)
    keep_analytic = np.exp(-2.0 * np.pi ** 2 * sigmas ** 2 / PITCH_NM ** 2)
    ripple_engine = _ripple_retention(t_sw, film_nm, sigmas)
    ripple_analytic = np.exp(-2.0 * np.pi ** 2 * sigmas ** 2 / t_sw ** 2)

    # The window: smooth enough (σ ≥ λ/4n) yet keep ≥ KEEP_FLOOR of the fundamental (σ ≤ σ_keep).
    sigma_keep = PITCH_NM * np.sqrt(np.log(1.0 / KEEP_FLOOR) / (2.0 * np.pi ** 2))
    p_close = sigma_rule / np.sqrt(np.log(1.0 / KEEP_FLOOR) / (2.0 * np.pi ** 2))

    # The closure punchline: the NA-0.93 lens images 145 nm, but the rule-abiding bake erases it.
    img_hi = litho.Imaging(WAVELENGTH_NM, NA_HI, sigma=SIGMA_SRC)
    x_d, aerial_d = _aerial(img_hi, PITCH_DENSE_NM)
    b0_d = litho.fundamental_amplitude(x_d, aerial_d, PITCH_DENSE_NM)
    keep_dense = (litho.fundamental_amplitude(
        x_d, _bake(aerial_d, PITCH_DENSE_NM, sigma_rule), PITCH_DENSE_NM) / b0_d)

    return dict(
        img=img, x=x, aerial=aerial, family=family, family_sigmas=family_sigmas, dose=dose,
        features=features, sigmas=sigmas, keep_engine=keep_engine, keep_analytic=keep_analytic,
        ripple_engine=ripple_engine, ripple_analytic=ripple_analytic,
        t_sw=t_sw, sigma_rule=sigma_rule, sigma_keep=sigma_keep, p_close=p_close,
        keep_dense=keep_dense, dense_alive=b0_d, film_nm=film_nm,
    )


def print_summary(data) -> None:
    """Print the bake-trade-off story — the demo's payoff in text."""
    print(f"\nPEB acid-diffusion blur — λ = {WAVELENGTH_NM:.0f} nm (ArF), NA = {NA:.2f}, "
          f"σ_src = {SIGMA_SRC:.2f}, pitch = {PITCH_NM:.0f} nm, resist n = {N_RESIST:.2f}\n")
    print(f"  standing-wave period λ/2n = {data['t_sw']:.1f} nm  →  cited smoothing rule "
          f"σ ≥ λ/4n = {data['sigma_rule']:.1f} nm")
    print(f"  keep ≥ {KEEP_FLOOR:.0%} of the {PITCH_NM:.0f} nm fundamental  →  σ ≤ {data['sigma_keep']:.1f} nm")
    print(f"  → the PEB window: σ ∈ [{data['sigma_rule']:.1f}, {data['sigma_keep']:.1f}] nm "
          f"(closes at pitch ≈ {data['p_close']:.0f} nm)\n")
    print("  The baked feature (mean clip — blur-invariant by conservation):")
    print("    {:>10} {:>10} {:>10} {:>8}".format("σ (nm)", "CD (nm)", "contrast", "NILS"))
    for s in data["family_sigmas"]:
        f = data["features"][s]
        print(f"    {s:>10.0f} {f.cd_nm:>10.1f} {f.contrast:>10.3f} {f.nils:>8.2f}")
    print()
    rule, keep = data["sigma_rule"], data["keep_dense"]
    i_rule = int(np.argmin(np.abs(data["sigmas"] - rule)))
    print(f"  At the smoothing floor σ = {rule:.1f} nm: ripple retention "
          f"{data['ripple_engine'][i_rule]:.3f} (ridges erased), fundamental retention "
          f"{data['keep_engine'][i_rule]:.2f} — the window is open at {PITCH_NM:.0f} nm.")
    print(f"  At NA {NA_HI:.2f} / {PITCH_DENSE_NM:.0f} nm the lens still images (the optics are alive)")
    print(f"  but the same bake keeps only {keep:.2f} of the fundamental — the lens out-resolves")
    print(f"  the bake; the resist blur sets the floor → use a BARC (the cited ARC/dye/PEB list).")
    print(f"  (The {data['p_close']:.0f} nm closure sitting beside this system's optical cutoff "
          f"~151 nm is a numeric coincidence of these parameters, not a law.)\n")


def save_figure(data) -> Path:
    """Render and save the PEB artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                                # headless
    from .plots import peb_figure

    fig = peb_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, sigma_src=SIGMA_SRC,
                     pitch_nm=PITCH_NM, n_resist=N_RESIST, keep_floor=KEEP_FLOOR)
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")         # λ, σ, ², →, ≥ on legacy codepages

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
