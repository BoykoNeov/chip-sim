"""Integration test for the defocus demo (Chip v1.4 — the demo IS the integration test).

The defocus demo wires the v1.4 chain — ``litho.expose_grating(..., defocus_nm=z)`` (the Bossung CD
sweep) + ``abbe_image``/``fundamental_amplitude`` through focus (the mechanism) → ``plots``. Its
``compute`` pipeline is the end-to-end check that they compose, asserted on the *robust* thesis (the
fundamental rides the exact envelope and nulls at the DOF; the Bossung degrades; partial coherence
softens the null), not brittle exact numbers (those are pinned in ``test_defocus.py``).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip.demo_defocus import compute, DOSE_FRACTIONS, PITCH_NM, WAVELENGTH_NM, NA


def test_demo_fundamental_rides_the_exact_envelope():
    # The tight anchor surfaced in the demo: the on-axis coherent fundamental through focus equals the
    # analytic 4·c₀·c₁·cos φ envelope to machine precision (the three-beam closed form), and nulls where
    # the envelope crosses zero (the φ=π/2 DOF event).
    data = compute()
    np.testing.assert_allclose(data["on_axis"], data["envelope"], atol=1e-12)
    i_null = int(np.argmin(np.abs(data["zabs"] - data["z_null"])))
    assert abs(data["envelope"][i_null]) < 0.05                 # envelope ≈ 0 at the null
    assert abs(data["on_axis"][i_null]) < 0.05


def test_demo_partial_coherence_softens_the_null():
    # Partial coherence buys focus latitude (the focus analogue of its resolution gain): at the on-axis
    # null the σ source still carries modulation, so |partial| > |on_axis| (≈0) there — the null is washed
    # out, not sharp.
    data = compute()
    i_null = int(np.argmin(np.abs(data["zabs"] - data["z_null"])))
    assert abs(data["partial"][i_null]) > abs(data["on_axis"][i_null]) + 1e-3


def test_demo_bossung_degrades_and_window_is_finite():
    # The Bossung readout: a finite, best-focus-centred process window, and CD drift growing with |z|.
    data = compute()
    assert data["window"] is not None
    lo, hi = data["window"]
    assert lo < 0 < hi and (hi - lo) > 0                        # the window straddles best focus
    # The nominal-dose CD is most stable near z=0 and drifts away from it (best focus is the CD plateau).
    z, cd = data["zabs"], np.asarray(data["bossung"][0.50])
    i0 = int(np.argmin(np.abs(z)))
    assert abs(cd[i0] - cd[i0 + 5]) < abs(cd[i0] - cd[i0 + 20])  # drift grows with defocus


def test_demo_dof_and_null_share_a_focus_scale():
    # The pitch is chosen at the resolution limit so the Rayleigh DOF (= k₂λ/NA²) and the exact φ=π/2
    # fundamental null sit at the same focus scale — they agree to within the high-NA paraxial gap
    # (a coarser pitch would null much further out). Both derive from the system, not hardcoded.
    data = compute()
    assert data["dof"] == pytest.approx(0.5 * WAVELENGTH_NM / NA ** 2)
    ratio = data["z_null"] / data["dof"]
    assert 0.6 < ratio < 1.4                                    # same order — the resolution-limit budget


def test_defocus_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import defocus_figure

    data = compute()
    fig = defocus_figure(data, wavelength_nm=WAVELENGTH_NM, NA=NA, sigma=data["img"].sigma,
                         pitch_nm=PITCH_NM, dose_fractions=DOSE_FRACTIONS, cd_spec=0.10)
    assert len(fig.axes) == 2                                   # Bossung panel + fundamental-vs-defocus panel
    plt.pyplot.close(fig)
