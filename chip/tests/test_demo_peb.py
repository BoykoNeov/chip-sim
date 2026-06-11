"""Integration test for the PEB demo (Chip v1.7 — the demo IS the integration test).

The PEB demo wires the v1.7 chain — ``litho.peb_blur`` (the engine in acid mode, lateral *and*
depth domains) + ``expose_grating(..., peb_diffusion_length_nm=σ)`` (the baked feature) →
``plots``. Its ``compute`` pipeline is the end-to-end check that they compose, asserted on the
*robust* thesis (the engine retentions ride the analytic heat kernels; the window is open at the
demo pitch and closed where the lens out-resolves the bake; the bake conserves the dose), not
brittle exact numbers (those are pinned in ``test_peb.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_peb import compute, KEEP_FLOOR, PITCH_NM, WAVELENGTH_NM, NA, N_RESIST


def test_demo_engine_points_ride_the_analytic_heat_kernels():
    # The tight anchor surfaced in the demo: both engine-computed retention curves (the lateral
    # fundamental along x, the standing-wave ripple along z) lie on their closed-form Gaussian
    # heat-kernel envelopes across the whole σ sweep — the same one engine, two domains.
    data = compute()
    np.testing.assert_allclose(data["keep_engine"], data["keep_analytic"], atol=2e-3)
    np.testing.assert_allclose(data["ripple_engine"], data["ripple_analytic"], atol=2e-3)


def test_demo_window_is_open_at_the_demo_pitch():
    # The PEB window exists and is finite: the cited smoothing floor (λ/4n) sits BELOW the
    # keep-the-image ceiling at 240 nm — and at the floor the ripple is erased (<2% left) while
    # most of the fundamental survives (>70%). Both edges derive from the system, not hardcoded.
    data = compute()
    assert 0.0 < data["sigma_rule"] < data["sigma_keep"]
    assert data["sigma_rule"] == pytest.approx(WAVELENGTH_NM / (4.0 * N_RESIST))
    i_rule = int(np.argmin(np.abs(data["sigmas"] - data["sigma_rule"])))
    assert data["ripple_engine"][i_rule] < 0.02
    assert data["keep_engine"][i_rule] > 0.70
    # The closure pitch is where the floor meets the ceiling — between the demo pitch and the rule.
    assert data["sigma_rule"] < data["sigma_keep"]
    assert 100.0 < data["p_close"] < PITCH_NM


def test_demo_dense_pitch_is_optically_alive_but_bake_dead():
    # The punchline: at NA 0.93 the 145 nm pitch still images (the aerial fundamental is alive),
    # but the rule-abiding bake keeps less than the window floor — the lens out-resolves the bake.
    data = compute()
    assert data["dense_alive"] > 0.01
    assert data["keep_dense"] < KEEP_FLOOR


def test_demo_bake_conserves_the_dose_and_degrades_the_feature():
    # Conservation made visible: every baked family member keeps the aerial image's mean (the
    # blur-invariant dose), while the printed feature degrades monotonically over the cited series
    # and the CD walks onto the pure-fundamental p/2 readout.
    data = compute()
    mean0 = float(np.asarray(data["aerial"]).mean())
    for s, image in data["family"].items():
        assert float(np.asarray(image).mean()) == pytest.approx(mean0, rel=1e-11), f"σ={s}"
    feats = [data["features"][s] for s in data["family_sigmas"]]
    assert all(a.contrast > b.contrast for a, b in zip(feats, feats[1:]))
    gaps = [abs(f.cd_nm - PITCH_NM / 2.0) for f in feats]
    assert all(a > b for a, b in zip(gaps, gaps[1:]))


def test_peb_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import peb_figure

    data = compute()
    fig = peb_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, sigma_src=data["img"].sigma,
                     pitch_nm=PITCH_NM, n_resist=N_RESIST, keep_floor=KEEP_FLOOR)
    assert len(fig.axes) == 2                    # latent-image panel + PEB-window panel
    plt.pyplot.close(fig)
