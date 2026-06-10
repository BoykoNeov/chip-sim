"""The Phase-3 anchor demo: the lithography aerial image — recipe in, printed feature out.

The chip's **one genuinely-new module** and its risk phase: pattern transfer by **Fourier optics**.
Where Phase 1a diffused dopant (the frozen PDE spine) and Phase 2 grew oxide (a closed-form ODE), this
forms the **aerial image** — the light intensity a projection lens casts onto the resist — and clips it
to a printed **critical dimension** (CD). Two stories on one figure:

  * **The mechanism (left)** — *why a pitch stops resolving.* The aerial image of a grating **near the
    resolution limit** assembles from its diffraction orders — but the projection lens (the **pupil**)
    collects only the orders inside ``|f| ≤ NA/λ``, and near the limit that is just the **0th and ±1st**.
    So the image goes from a flat DC field to a **single cos fringe** when the ±1 orders are added, and it
    *cannot sharpen further* — the 3rd and higher orders that would square the line up are already cut.
    A little finer and even the ±1 are cut → nothing modulates → the pattern vanishes. (Shown under
    coherent on-axis illumination; the ideal square-wave mask is drawn for reference — the gap between it
    and the rounded image is exactly the high orders the pupil discarded.)
  * **The benchmark (right)** — *where the pattern stops resolving.* Image **contrast vs pitch** for a
    realistic partially-coherent (σ) source, falling to ~0 at the pupil cutoff, with the two **Rayleigh
    limits** marked: λ/NA (half-pitch ``k₁=0.5``, conventional coherent) and λ/2NA (``k₁=0.25``, the
    two-beam physical floor). Note the σ source already resolves *below* the coherent λ/NA limit — partial
    coherence buys resolution.

System: **193 nm ArF**, **NA 0.85** (dry), **σ 0.5** conventional — a representative DUV stepper.
Reference facts (cited, not redistributed — the ``[[litho-aerial-image-source]]`` note: Mack /
lithoguru): ``k₁=0.25`` is the two-beam floor, today's best ≈ 0.28; ``NILS ≳ 2`` for a robust process.
The ``k₁`` values are *derived from the pupil arithmetic here*, not fit — so the agreement is a
cross-check, not a tautology.

Run headless (saves the figure, prints the table):

    python -m chip.demo_litho
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import litho

# The demo system — a representative 193 nm ArF (dry) projection stepper.
WAVELENGTH_NM = 193.0          # ArF excimer (DUV)
NA = 0.85                      # dry ArF projection-lens numerical aperture
SIGMA = 0.5                    # conventional partial-coherence factor

# Left panel (the mechanism): a grating NEAR the resolution limit (plan §3), imaged under COHERENT
# on-axis illumination. Near the limit the pupil collects only the 0th and ±1st orders — so the image
# assembles in one step (DC flat field → add the ±1 orders → a single cos fringe) and cannot sharpen
# further: the 3rd and higher orders that would square the line up are already cut by the pupil, and a
# little finer even the ±1 are cut → flat → unresolved. The shortness of the assembly IS the lesson.
PITCH_ASSEMBLE = 280.0         # nm ≈ 1.23·(λ/NA) — near the coherent limit; only 0, ±1 collected
N_X = 600

# Right panel (the benchmark): contrast vs pitch for the realistic σ source, spanning the cutoff.
PITCH_SWEEP = (110.0, 900.0)   # nm — from below the two-beam floor (113 nm) to coarse
N_PITCH = 140

# The printed-exposure table: coarse → near-limit → sub-resolution (σ conventional).
TABLE_PITCHES = (600.0, 350.0, 240.0, 180.0, 150.0)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURE = _REPO_ROOT / "docs" / "figures" / "chip-litho.png"
OUTPUT_FIGURE = _REPO_ROOT / "outputs" / "chip-litho.png"


def _assembling_orders():
    """Left-panel data: the coherent aerial image near the resolution limit, assembling from its orders.

    Returns ``(x, mask, partials, full, threshold, cd, cd_span)`` for ``PITCH_ASSEMBLE`` under coherent
    on-axis illumination. Near the limit the pupil collects only ``{0, ±1}``, so the assembly is one
    step: ``partials`` is just the 0th-order DC (a flat field), and the bold ``full`` image adds the ±1
    orders — a single cos fringe (the 3rd+ orders that would sharpen the line are cut by the pupil).
    ``mask`` is the ideal square-wave transmission, drawn for reference — the gap between the sharp mask
    and the rounded cos image *is* the high orders the pupil threw away. The collected-order count is
    asserted (so a future edit that pushes the pitch off "near the limit" is caught).
    """
    coh = litho.Imaging(WAVELENGTH_NM, NA, sigma=0.0)     # coherent → partial sums = truncated series
    p = PITCH_ASSEMBLE
    x = np.linspace(0.0, p, N_X)
    f_cut = coh.f_cut * (1.0 + 1e-9)
    collected = [(f, c) for (f, c) in litho.grating_orders(p, n_orders=9) if abs(f) <= f_cut]
    n_nonzero = sum(1 for (f, c) in collected if abs(c) > 1e-12)
    assert n_nonzero == 3, f"expected only {{0, ±1}} collected near the limit, got {n_nonzero} orders"

    dc = litho.coherent_image(x, [(f, c) for (f, c) in collected if round(f * p) == 0])
    full = litho.coherent_image(x, collected)              # DC + the ±1 orders = a single cos fringe
    partials = [("0th order (DC) — a flat field", dc)]
    mask = np.where(np.abs((x % p) - p / 2) < p / 4, 0.0, 1.0)   # clear at 0/p, dark line at p/2
    threshold = float(full.mean())                               # = transmitted power (the DC level)
    cd = litho.print_cd(x, full, threshold, polarity="dark")
    cd_span = (p / 2 - cd / 2, p / 2 + cd / 2) if cd > 0 else None
    return x, mask, partials, full, threshold, cd, cd_span


def compute():
    """Run the demo: the left-panel assembly + the right-panel contrast sweep + the exposure table.

    Returns a dict of plain arrays/scalars the figure and the summary consume (ADR 0002 — no live object).
    """
    img = litho.Imaging(WAVELENGTH_NM, NA, sigma=SIGMA)
    x, mask, partials, full, threshold, cd, cd_span = _assembling_orders()

    pitches = np.linspace(PITCH_SWEEP[0], PITCH_SWEEP[1], N_PITCH)
    contrasts = np.array([litho.expose_grating(img, p).contrast for p in pitches])

    table = {p: litho.expose_grating(img, p) for p in TABLE_PITCHES}
    return dict(
        img=img, x=x, mask=mask, partials=partials, full=full, threshold=threshold, cd=cd,
        cd_span=cd_span, pitch_assemble=PITCH_ASSEMBLE, pitches=pitches, contrasts=contrasts,
        pitch_coherent=img.pitch_min_coherent, pitch_two_beam=img.pitch_min_two_beam, table=table,
    )


def print_summary(data) -> None:
    """Print the recipe → resolution → printed-feature story — the demo's payoff in text."""
    img = data["img"]
    print(f"\nLithography aerial image — λ = {WAVELENGTH_NM:.0f} nm (ArF), NA = {NA:.2f}, σ = {SIGMA:.2f}\n")
    print(f"  Rayleigh resolution R = k₁·λ/NA  (R = resolvable half-pitch):")
    print(f"    k₁ = 0.50 (coherent)  → R = {img.resolution(0.5):.1f} nm  (min pitch λ/NA  = {img.pitch_min_coherent:.0f} nm)")
    print(f"    k₁ = 0.25 (two-beam)  → R = {img.resolution(0.25):.1f} nm  (min pitch λ/2NA = {img.pitch_min_two_beam:.0f} nm)")
    print(f"    today's best k₁ ≈ 0.28; NILS ≳ {litho.NILS_PRINTABLE:.0f} for a robust process\n")
    print(f"  Printed line/space (σ = {SIGMA:.2f} conventional, mean-intensity clip):")
    print(f"    {'pitch':>7}  {'contrast':>9}  {'NILS':>6}  {'CD':>8}   resolved")
    for p in TABLE_PITCHES:
        pf = data["table"][p]
        cd = f"{pf.cd_nm:.0f} nm" if pf.resolved else "—"
        flag = "yes" if pf.resolved else "NO (flat image)"
        print(f"    {p:>5.0f} nm  {pf.contrast:>9.3f}  {pf.nils:>6.2f}  {cd:>8}   {flag}")
    print()
    print(f"  → contrast and NILS fall as the pitch shrinks toward the pupil cutoff; below the σ-source")
    print(f"    limit (~{WAVELENGTH_NM / ((1 + SIGMA) * NA):.0f} nm pitch here) the image goes flat and the pattern stops resolving.\n")


def save_figure(data) -> Path:
    """Render and save the aerial-image artifact (needs the optional ``viz`` extra)."""
    import matplotlib
    matplotlib.use("Agg")                                # headless
    from .plots import litho_figure

    fig = litho_figure(
        x_nm=data["x"], image=data["full"], partials=data["partials"], mask=data["mask"],
        threshold=data["threshold"], cd_span=data["cd_span"], pitch_nm=data["pitch_assemble"],
        pitches_nm=data["pitches"], contrasts=data["contrasts"],
        pitch_coherent=data["pitch_coherent"], pitch_two_beam=data["pitch_two_beam"],
        wavelength_nm=WAVELENGTH_NM, NA=NA, sigma=SIGMA,
    )
    for target in (DOCS_FIGURE, OUTPUT_FIGURE):
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=130)
    return DOCS_FIGURE


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")         # λ, σ, ≳, →, ₁ on legacy codepages

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
