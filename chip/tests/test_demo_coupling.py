"""Integration test for the back-coupling demo (Chip v1.2 — the demo IS the integration test).

The demo wires the whole coupling chain — ``diffusion_dopant.predeposit`` (the seed) →
``coupling.oxidize_couple`` (inert / +OED / +OED+segregation) → ``plots`` — for boron and
phosphorus. Its compute pipeline is the end-to-end check that they compose, asserted on the
*robust* theses (OED deepens; boron depletes, phosphorus piles up; conservation closes), not on the
calibrated OED magnitude (which the per-leg tests already frame as flagged/illustrative).

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds
without error", and skipped where the optional viz extra is absent.
"""
import pytest

from chip.demo_coupling import compute, DOPANT_CASES


def test_demo_pipeline_runs_both_dopants():
    cases = compute()
    assert [c["dopant"] for c in cases] == list(DOPANT_CASES)
    for c in cases:
        # Each case carries the three variants over one shared grid + the cited constants.
        assert {"seed", "inert", "oed", "coupled", "f_I", "m", "sign"} <= set(c)
        assert c["inert"].x.shape == c["coupled"].N.shape


def test_demo_oed_enhances_and_conserves():
    # OED deepens the profile (effective ∫D dt exceeds the inert age) for both interstitialcy
    # diffusers; OED-alone (sealed) conserves dose to machine precision.
    for c in compute():
        oed = c["oed"]
        assert oed.effective_Dt > 1.3 * oed.D_inert * oed.t_seconds
        assert oed.si_dose == pytest.approx(oed.si_dose_initial, rel=1e-10)


def test_demo_boron_depletes_phosphorus_piles_up():
    # The headline signatures (the cited m sets the sign), read as the segregation step proper —
    # coupled vs OED-only (NOT vs inert): OED spreads the profile and drops the surface peak for
    # BOTH dopants, so segregation must be isolated from it (coupled-vs-inert would hide phosphorus
    # pile-up behind the OED drop — the demo's own physics subtlety). The Si + oxide-reservoir
    # balance closes to machine precision.
    by = {c["dopant"]: c for c in compute()}
    b, p = by["B"], by["P"]
    assert b["sign"] == "depletion" and b["m"] < 1.0
    assert b["coupled"].surface_concentration < b["oed"].surface_concentration
    assert p["sign"] == "pile-up" and p["m"] > 1.0
    assert p["coupled"].surface_concentration > p["oed"].surface_concentration
    for c in (b, p):
        assert c["coupled"].conservation_residual / c["coupled"].si_dose_initial < 1e-12


def test_coupling_figure_builds():
    # Viz smoke test only (never a correctness check): skip cleanly without the extra.
    plt = pytest.importorskip("matplotlib")
    plt.use("Agg")
    from chip.plots import coupling_figure

    fig = coupling_figure(compute())
    assert len(fig.axes) == 2                          # one panel per dopant (boron, phosphorus)
    plt.pyplot.close(fig)
