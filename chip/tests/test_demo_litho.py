"""Integration test for the lithography demo (Chip Phase 3 — the demo IS the integration test).

The litho demo wires the whole Fourier-optics chain — ``litho.grating_orders`` (the mask spectrum) →
``coherent_image`` partial sums (the assembling-orders mechanism) → ``abbe_image``/``expose_grating``
(the partially-coherent contrast sweep + printed CD) → ``plots``. Its ``compute`` pipeline is the
end-to-end check that they compose, asserted on the *robust* thesis (contrast and NILS fall toward the
cutoff; the image goes flat below the σ-source limit; the orders assemble onto the full image), not
brittle exact numbers (those are pinned in ``test_litho.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from projects.chip import litho
from projects.chip.demo_litho import (
    compute, PITCH_SWEEP, TABLE_PITCHES, WAVELENGTH_NM, NA, SIGMA,
)


def test_demo_contrast_sweep_falls_toward_the_cutoff():
    data = compute()
    pitches, contrasts = data["pitches"], data["contrasts"]
    # The sweep spans the requested pitch range.
    assert pitches[0] == pytest.approx(PITCH_SWEEP[0])
    assert pitches[-1] == pytest.approx(PITCH_SWEEP[1])
    # Contrast rises with pitch (coarser pitch images better): high at the coarse end, ~0 at the fine
    # end (below the σ-source limit the pattern stops resolving). Broadly monotone — small (<1%) ripples
    # are expected from the discrete-source hard-pupil model (orders pop through the pupil at discrete
    # source points), so allow a small tolerance rather than asserting strict monotonicity.
    assert np.all(np.diff(contrasts) >= -0.01)
    assert contrasts[-1] > 0.9
    assert contrasts[0] < 1e-6


def test_demo_exposure_table_contrast_nils_cd_fall_with_pitch():
    data = compute()
    table = data["table"]
    rows = [table[p] for p in TABLE_PITCHES]            # coarse → fine
    # Contrast and NILS both decrease as the pitch shrinks toward the resolution limit.
    assert all(a.contrast >= b.contrast - 1e-9 for a, b in zip(rows, rows[1:]))
    assert all(a.nils >= b.nils - 1e-9 for a, b in zip(rows, rows[1:]))
    # The coarsest pitch is comfortably printable (NILS above the robust band); the finest is unresolved.
    assert rows[0].nils > litho.NILS_PRINTABLE
    assert rows[0].resolved
    assert not rows[-1].resolved and rows[-1].cd_nm == 0.0
    # "Resolves but isn't robustly printable": at least one row has contrast > 0 yet NILS below the band
    # (the teaching point that resolution and printability are different thresholds).
    assert any(r.resolved and r.nils < litho.NILS_PRINTABLE for r in rows)


def test_demo_orders_assemble_near_the_resolution_limit():
    # The mechanism leg surfaced in the demo, NEAR the resolution limit (plan §3): the pupil collects
    # only {0, ±1}, so the assembly is one step — the 0th-order DC partial is a flat field, and adding
    # the ±1 orders (the full image) turns it into a strongly-modulated single cos fringe. The shortness
    # is the point: no higher orders survive to sharpen the line.
    data = compute()
    partials, full = data["partials"], data["full"]
    assert len(partials) == 1 and "DC" in partials[0][0]
    dc = partials[0][1]
    assert np.ptp(dc) < 1e-9                            # 0th order alone = a flat field
    assert litho.image_contrast(dc) < 1e-9             # flat → zero contrast
    assert litho.image_contrast(full) > 0.5            # adding the ±1 orders → a strong fringe


def test_demo_printed_line_centred_and_sane():
    # The constant-threshold CD readout on the assembled image: a printed dark line of positive width,
    # centred at p/2 (the dark fringe), reported via cd_span.
    data = compute()
    cd, span, p = data["cd"], data["cd_span"], data["pitch_assemble"]
    assert cd > 0 and span is not None
    assert span[1] - span[0] == pytest.approx(cd)
    assert (span[0] + span[1]) / 2 == pytest.approx(p / 2, rel=1e-6)


def test_demo_rayleigh_limits_ordered():
    # The two Rayleigh limits the figure marks: the two-beam floor (λ/2NA) is half the coherent limit
    # (λ/NA) — the 50% resolution gain. Both derived from the system, not hardcoded.
    data = compute()
    assert data["pitch_two_beam"] == pytest.approx(data["pitch_coherent"] / 2.0)
    assert data["pitch_two_beam"] == pytest.approx(WAVELENGTH_NM / (2 * NA))


def test_litho_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from projects.chip.plots import litho_figure

    data = compute()
    fig = litho_figure(
        x_nm=data["x"], image=data["full"], partials=data["partials"], mask=data["mask"],
        threshold=data["threshold"], cd_span=data["cd_span"], pitch_nm=data["pitch_assemble"],
        pitches_nm=data["pitches"], contrasts=data["contrasts"],
        pitch_coherent=data["pitch_coherent"], pitch_two_beam=data["pitch_two_beam"],
        wavelength_nm=WAVELENGTH_NM, NA=NA, sigma=SIGMA,
    )
    assert len(fig.axes) == 2                            # assembly panel + contrast-vs-pitch panel
    plt.pyplot.close(fig)
