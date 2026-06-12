"""Integration test for the CAR demo (Chip v1.9 — the demo IS the integration test).

The CAR demo wires the v1.9 chain — ``litho.car_peb`` (the engine carrying the acid-diffusion
sub-step of the operator split) + ``expose_grating_car`` (the developed deprotection feature) →
``plots``. Its ``compute`` pipeline is the end-to-end check that they compose, asserted on the
*robust* thesis (amplification sharpens the edge above the acid; the acid-loss decay is the exact
catalyst law; the CD tracks the bake through a finite process window), not brittle exact numbers
(those are pinned in ``test_car.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_car import compute, PITCH_NM, WAVELENGTH_NM, NA, ACID_DOSE
from chip import litho


def test_demo_acid_loss_rides_the_exact_catalyst_decay():
    # The conservation leg surfaced in the demo: acid is a pure catalyst, so the engine-computed
    # ∫h(t)/∫h(0) points lie exactly on the closed-form e^{−k_loss·t} decay (sampled across the sweep)
    # — the dose is only ever *lost*, never consumed by the deprotection it drives.
    data = compute()
    expected = np.exp(-litho.CAR_K_LOSS_APEX_E * data["sample_t"])
    np.testing.assert_allclose(data["acid_loss_engine"], expected, rtol=1e-9)


def test_demo_amplification_sharpens_above_the_acid_edge():
    # The headline (tight-ish): at the nominal bake the deprotection edge is STEEPER than the latent
    # acid edge it came from — NILS(deprotection) > NILS(acid) — the superlinear hⁿ map at work, the
    # reason CAR resolves. (And the nominal bake really lands on the target CD.)
    data = compute()
    assert data["f_nominal"].nils > data["acid_nils"]
    assert data["f_nominal"].cd_nm == pytest.approx(data["nominal_cd"], abs=2.0)


def test_demo_cd_tracks_the_bake_through_a_finite_window():
    # The PEB process window exists and is finite: the developed CD falls monotonically with bake time
    # (fixed dose — over-amplification shrinks the line), passing through nominal, so the ±tol window
    # is a bounded bake interval bracketing the nominal bake.
    data = compute()
    cd = np.asarray(data["cd_of_t"])
    alive = cd > 1.0
    assert np.all(np.diff(cd[alive]) < 0.0)                       # CD strictly decreasing where developed
    assert 0.0 < data["t_win_lo"] < data["t_nominal"] < data["t_win_hi"]
    assert data["window_lo"] < data["nominal_cd"] < data["window_hi"]


def test_demo_deprotection_family_develops_and_stays_bounded():
    # The left-panel family: every baked profile is a valid deprotection field (0 ≤ 1−m ≤ 1) and the
    # series develops monotonically (more bake → more deprotection → smaller printed line).
    data = compute()
    for t, image in data["family"].items():
        img = np.asarray(image)
        assert img.min() >= -1e-12 and img.max() <= 1.0 + 1e-12, f"t={t}"
    feats = [data["features"][t] for t in data["family_times"]]
    assert all(a.cd_nm > b.cd_nm for a, b in zip(feats, feats[1:]))
    assert all(a.peak_deprotection < b.peak_deprotection for a, b in zip(feats, feats[1:]))


def test_car_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import car_figure

    data = compute()
    fig = car_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, sigma_src=data["img"].sigma,
                     pitch_nm=PITCH_NM, acid_dose=ACID_DOSE)
    assert len(fig.axes) == 3                    # latent-image panel + window panel + acid-loss twin
    plt.pyplot.close(fig)
