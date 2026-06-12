"""The v1.9 anchor demo: **CAR reaction–diffusion PEB** — amplification vs diffusion + loss.

Phase 3's §8-named "constant D (no CAR reaction–diffusion)" scope edge, **promoted** — and where v1.7
found the bake *is* the engine's pure linear PDE, the realistic chemically-amplified bake is a coupled
**two-field** reaction–diffusion system (acid ``h`` + blocked-site fraction ``m``) that does not fit
the single-field engine natively, so it rides the engine **consumer-side by operator splitting**: the
engine carries only the acid-diffusion sub-step (``Neumann(0)`` sealed faces), while the local reaction
(acid-catalyzed deprotection + first-order acid loss) is integrated in closed form. Two stories on one
figure:

  * **The latent image developing (left) — amplification sharpens.** The dose-normalized latent acid
    image at 240 nm pitch and the **deprotection profiles** ``1−m`` it grows over a bake-time series:
    the superlinear ``hⁿ`` deprotection map is *steeper at the edge than the acid* (the signature that
    makes CAR high-resolution — the NILS rises above the acid's), and development clips the deprotection
    (the chemically-faithful resist) where v1.7 clipped the acid image.
  * **The PEB process window (right) — CD is acutely bake-sensitive.** At fixed exposure dose the
    developed CD swings steeply with bake time (the cited "control of the PEB is extremely critical"):
    too short → underdeveloped (the deprotection never reaches the develop threshold), too long →
    over-amplified (the line collapses). The narrow band that holds CD near nominal is the PEB latitude.
    Overlaid: the acid is a **pure catalyst** — ``∫h`` decays *exactly* ``e^{−k_loss·t}`` (engine points
    on the analytic decay — the conservation leg made visible), the slow fade that degrades the latent
    image over the bake.

System: **193 nm ArF**, **NA 0.85** (dry), **σ 0.5** conventional — the same DUV stepper as
`demo_litho`/`demo_defocus`/`demo_peb` — imaging a **240 nm** line/space; resist = the cited IBM
**APEX-E @ 90 °C** CAR (``k_amp = 2.0/s``, ``k_loss = 0.0033/s``, ``n = 1.8``, ``D_h,0 = 0.0933 nm²/s``;
``[[peb-acid-diffusion-source]]``). The **exposure dose** (peak latent acid) and **bake times** are
illustrative recipe knobs (flagged) chosen so the nominal 120 nm CD lands at a realistic ~60 s bake —
only the four reaction–diffusion constants are cited.

Run headless (saves the figure, prints the table):

    python -m chip.demo_car
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import litho

# The demo system — the demo_litho/demo_defocus/demo_peb 193 nm ArF (dry) stepper, now a CAR resist.
WAVELENGTH_NM = 193.0          # ArF excimer (DUV)
NA = 0.85                      # dry ArF projection-lens numerical aperture
SIGMA_SRC = 0.5                # conventional partial-coherence factor
PITCH_NM = 240.0               # dense-but-resolved line/space (nominal CD = 120 nm), the demo pitch
DUTY = 0.5
N_X = 512

# Illustrative recipe knobs (flagged — only the four APEX-E reaction–diffusion constants are cited):
# the photoacid is a small fraction of the blocked-site density, so the peak latent acid is ≪ 1; this
# dose + the bake series put the nominal 120 nm CD at a realistic ~60 s bake (a 1 dose:knob calibration,
# the same discipline as demo_peb's N_RESIST / RIPPLE_SWING).
ACID_DOSE = 0.13               # peak latent acid (normalized to the initial blocked-site density)
DEVELOP_THRESHOLD = 0.5        # the dissolution contour — develop where deprotection 1−m exceeds this
FAMILY_TIMES_S = (30.0, 60.0, 90.0)   # the left-panel bake series (under / near / over the nominal)
NOMINAL_CD_NM = 120.0          # the target half-pitch CD (the process-window centre)
WINDOW_CD_TOL = 0.10           # the process window = bakes holding CD within ±10 % of nominal

# The bake-time sweep for the right panel (the CD-sensitivity curve + the acid-loss decay).
T_BAKE_MAX_S = 130.0
N_TIME = 53

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-car.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-car.png"


def _offset_grid(pitch_nm: float, n_x: int) -> np.ndarray:
    """One period sampled at half-offset cell centers — the half-period bake grid (faces at 0 and p/2)."""
    return (np.arange(n_x) + 0.5) * (pitch_nm / n_x)


def _latent_acid(img: "litho.Imaging", pitch_nm: float, n_x: int = N_X):
    """The dose-normalized latent acid image (∝ the aerial image — the linear-exposure idealization)."""
    x = _offset_grid(pitch_nm, n_x)
    aerial = litho.abbe_image(x, litho.grating_orders(pitch_nm, duty=DUTY), img,
                              source_fs=litho.conventional_source(img))
    return x, ACID_DOSE * aerial / float(aerial.max())


def _bake(h0: np.ndarray, pitch_nm: float, t_bake_s: float) -> np.ndarray:
    """The expose_grating_car bake pipeline, bare: half-period reaction–diffusion, mirrored back."""
    half = h0.size // 2
    depro_half, _ = litho.car_peb(h0[:half], pitch_nm / 2.0, litho.CARBake(t_bake_s=t_bake_s))
    return np.concatenate([depro_half, depro_half[::-1]])


def compute():
    """Run the demo: the developing latent image (left) and the PEB process window (right).

    Returns a dict of plain arrays/scalars the figure and the summary consume (ADR 0002 — no live object).
    """
    img = litho.Imaging(WAVELENGTH_NM, NA, sigma=SIGMA_SRC)
    x, acid = _latent_acid(img, PITCH_NM)
    edge_nm, linewidth_nm = DUTY * PITCH_NM / 2.0, (1.0 - DUTY) * PITCH_NM
    acid_nils = litho.nils(x, acid, edge_nm, linewidth_nm)         # the flat reference (no bake)

    # Left panel: the deprotection family + the developed features over the bake series.
    family = {t: _bake(acid, PITCH_NM, t) for t in FAMILY_TIMES_S}
    features = {t: litho.expose_grating_car(img, PITCH_NM, litho.CARBake(t_bake_s=t),
                                            acid_dose=ACID_DOSE, develop_threshold=DEVELOP_THRESHOLD)
                for t in FAMILY_TIMES_S}

    # Right panel: the CD-vs-bake sensitivity, the deprotection NILS, and the exact acid-loss decay.
    times = np.linspace(T_BAKE_MAX_S / N_TIME, T_BAKE_MAX_S, N_TIME)
    feats = [litho.expose_grating_car(img, PITCH_NM, litho.CARBake(t_bake_s=t),
                                      acid_dose=ACID_DOSE, develop_threshold=DEVELOP_THRESHOLD)
             for t in times]
    cd_of_t = np.array([f.cd_nm for f in feats])
    nils_of_t = np.array([f.nils for f in feats])
    # Acid loss: ∫h(t)/∫h(0) — engine points on the analytic e^{−k_loss·t} (the catalyst leg made
    # visible; sampled every few times so the figure shows discrete engine checks on the exact curve).
    half = acid.size // 2
    sample_t = times[::8]
    acid_loss_engine = np.array([litho.car_peb(acid[:half], PITCH_NM / 2.0,
                                               litho.CARBake(t_bake_s=t))[1].sum() / acid[:half].sum()
                                 for t in sample_t])
    acid_loss_analytic = np.exp(-litho.CAR_K_LOSS_APEX_E * times)

    # The PEB process window: the bake range holding CD within ±tol of nominal (CD falls monotonically
    # through nominal, so interpolate the two crossings of the band edges).
    lo, hi = (1.0 - WINDOW_CD_TOL) * NOMINAL_CD_NM, (1.0 + WINDOW_CD_TOL) * NOMINAL_CD_NM
    valid = cd_of_t > 1.0
    t_nominal = float(np.interp(-NOMINAL_CD_NM, -cd_of_t[valid], times[valid]))  # CD decreasing → negate
    t_win_lo = float(np.interp(-hi, -cd_of_t[valid], times[valid]))
    t_win_hi = float(np.interp(-lo, -cd_of_t[valid], times[valid]))
    f_nominal = litho.expose_grating_car(img, PITCH_NM, litho.CARBake(t_bake_s=t_nominal),
                                         acid_dose=ACID_DOSE, develop_threshold=DEVELOP_THRESHOLD)

    return dict(
        img=img, x=x, acid=acid, acid_nils=acid_nils, family=family, family_times=FAMILY_TIMES_S,
        features=features, times=times, cd_of_t=cd_of_t, nils_of_t=nils_of_t,
        sample_t=sample_t, acid_loss_engine=acid_loss_engine, acid_loss_analytic=acid_loss_analytic,
        t_nominal=t_nominal, t_win_lo=t_win_lo, t_win_hi=t_win_hi, f_nominal=f_nominal,
        nominal_cd=NOMINAL_CD_NM, window_lo=lo, window_hi=hi, develop_threshold=DEVELOP_THRESHOLD,
    )


def print_summary(data) -> None:
    """Print the CAR bake story — the demo's payoff in text."""
    print(f"\nCAR reaction–diffusion PEB — λ = {WAVELENGTH_NM:.0f} nm (ArF), NA = {NA:.2f}, "
          f"σ_src = {SIGMA_SRC:.2f}, pitch = {PITCH_NM:.0f} nm")
    print(f"  resist: IBM APEX-E @ 90 °C (cited) — k_amp = {litho.CAR_K_AMP_APEX_E}/s, "
          f"k_loss = {litho.CAR_K_LOSS_APEX_E}/s, n = {litho.CAR_REACTION_ORDER_APEX_E}, "
          f"D_h,0 = {litho.CAR_D_H0_APEX_E} nm²/s")
    print(f"  exposure dose (peak latent acid) = {ACID_DOSE:.2f}, develop at "
          f"{DEVELOP_THRESHOLD:.0%} deprotection  (both illustrative recipe knobs)\n")
    print("  The developed feature vs bake time (fixed dose):")
    print("    {:>10} {:>10} {:>10} {:>8} {:>10}".format(
        "t (s)", "CD (nm)", "contrast", "NILS", "peak 1−m"))
    for t in data["family_times"]:
        f = data["features"][t]
        print(f"    {t:>10.0f} {f.cd_nm:>10.1f} {f.contrast:>10.3f} {f.nils:>8.2f} "
              f"{f.peak_deprotection:>10.3f}")
    print()
    fn = data["f_nominal"]
    print(f"  Amplification sharpens: the acid edge NILS = {data['acid_nils']:.2f}, but the "
          f"deprotection edge NILS = {fn.nils:.2f}")
    print(f"  at the nominal bake (t = {data['t_nominal']:.0f} s → CD {fn.cd_nm:.0f} nm) — the "
          f"superlinear hⁿ map steepens the edge (why CAR resolves).")
    print(f"  PEB latitude (the cited 'control is critical'): CD within ±{WINDOW_CD_TOL:.0%} of "
          f"{data['nominal_cd']:.0f} nm")
    print(f"  needs the bake in [{data['t_win_lo']:.0f}, {data['t_win_hi']:.0f}] s — a "
          f"{data['t_win_hi'] - data['t_win_lo']:.0f} s window.")
    lost = 1.0 - float(np.exp(-litho.CAR_K_LOSS_APEX_E * data["t_nominal"]))
    print(f"  Acid is a catalyst: ∫h decays exactly e^(−k_loss·t) → {lost:.0%} lost by the "
          f"nominal bake (the slow fade of the latent image).\n")


def save_figure(data) -> Path:
    """Render and save the CAR artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                                # headless
    from .plots import car_figure

    fig = car_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, sigma_src=SIGMA_SRC,
                     pitch_nm=PITCH_NM, acid_dose=ACID_DOSE)
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
