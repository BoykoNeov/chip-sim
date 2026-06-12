"""Integration test for the Zernike demo (Chip v1.10 — the demo IS the integration test).

The Zernike demo wires the v1.10 chain — ``litho.abbe_image(..., aberrations=...)`` +
``fundamental_complex`` (the coma placement error, the astigmatism H↔V best-focus split, the spherical
pitch-dependent best focus) → ``plots``. Its ``compute`` pipeline is the end-to-end check that they
compose, asserted on the *robust* thesis (coma shifts the fringe ∝ its coefficient; astig splits best
focus by orientation; spherical drifts best focus with pitch), not brittle exact numbers (those are
pinned in ``test_zernike.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_zernike import compute, WAVELENGTH_NM, NA, PITCH_NM


def test_demo_coma_shifts_the_image_linearly_with_coefficient():
    # Coma's signature: the comatic image is the unaberrated one TRANSLATED (a placement error), and the
    # shift grows linearly with the coma coefficient — 0 at zero coma, monotone, sign-consistent.
    data = compute()
    assert data["placement_sweep"][0] == pytest.approx(0.0, abs=1e-9)        # no coma → no shift
    seq = data["placement_sweep"]
    assert np.all(np.diff(seq) > -1e-9) or np.all(np.diff(seq) < 1e-9)       # monotone in coma
    assert abs(data["placement_demo"]) > 5.0                                 # a visible overlay error
    # …and it is a SHIFT, not a contrast loss: the comatic image keeps the unaberrated modulation depth.
    from chip import litho as L
    assert L.image_contrast(data["image_coma"]) == pytest.approx(
        L.image_contrast(data["image_clean"]), abs=1e-6)


def test_demo_astigmatism_splits_best_focus_by_orientation():
    # Astig's signature: horizontal (φ_g=0) and vertical (φ_g=90°) lines reach best focus at OPPOSITE
    # defocus planes straddling z=0 — the split a plain defocus offset cannot produce.
    data = compute()
    assert data["bf_h"] * data["bf_v"] < 0                                   # opposite signs
    assert data["bf_h"] == pytest.approx(-data["bf_v"], abs=3.0)             # symmetric about focus
    assert abs(data["bf_h"] - data["bf_v"]) > 30.0                           # a meaningful split


def test_demo_spherical_drifts_best_focus_with_pitch():
    # Spherical's signature: best focus DRIFTS across the pitch family (different feature sizes focus at
    # different planes), while the unaberrated baseline is pinned at z=0 for every pitch. Best focus also
    # moves monotonically (fine → coarse pitch), each curve peaking inside the search window.
    data = compute()
    pitches = list(data["spherical_pitches"])
    bf = [data["sph_bf"][p] for p in pitches]
    assert max(bf) - min(bf) > 30.0                                          # best focus moves with pitch
    assert all(b2 > b1 for b1, b2 in zip(bf, bf[1:]))                        # monotone fine → coarse
    assert all(abs(data["flat_bf"][p]) <= 2.0 for p in pitches)              # unaberrated: pitch-independent


def test_zernike_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import zernike_figure

    data = compute()
    fig = zernike_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, pitch_nm=PITCH_NM)
    assert len(fig.axes) >= 3                                                # coma + astig + spherical panels
    plt.pyplot.close(fig)
