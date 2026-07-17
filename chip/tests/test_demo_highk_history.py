"""Integration test for the high-κ history demo (B8 — the F3 payload, made assertable end-to-end).

``test_high_k.py`` exercises :mod:`chip.high_k` with hardcoded inputs and never calls the demo; this test
guards the *chaining* — that the demo's ladder and its matched-EOT contrast really run through the **real**
:mod:`chip.device`, which is what makes the module's "``device.py`` is untouched" claim a demonstration
rather than an assertion.

Two of these asserts are **honesty guards**, not physics guards, and they are the reason this file exists
at all (B7, the demo-only precedent, has no demo test):

  * **the ladder stays in the regime the model is honest in** — the F3 plan's slice-3 trap. ``decades_saved``
    grows ∝ EOT, so a ladder walked to 2–3 nm EOT would feature a *fabricated* +11–16-decade HfO₂ win
    (real HfO₂ that thick is trap-limited, which this model does not carry). The cap is a claim about
    where the model may speak, so it is pinned here rather than left to a reader's restraint;
  * **the headline is never rounded up** — a "≳ N decades" claim that rounds 5.6 to 6 is not a ≳ claim.

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import math

import pytest

from chip import device as dev
from chip import high_k as hk
from chip.demo_highk_history import (
    CHANNEL_N_A, EOT_LADDER_UM, FEATURE_EOT_UM, MATERIALS, WALL_J_A_CM2, compute,
)


def test_the_device_is_byte_for_byte_identical_across_every_material():
    """The F3 discriminator, through the real ``device.py``: at one EOT, the material never reaches V_t.

    Not ``approx`` — **exactly** equal. The demo feeds each stack's ``eot_um`` (all the same float, by
    construction of the matched-EOT move) into the untouched ``threshold_voltage``, so this is
    "same input → same output". It still earns its keep: had the demo fed ``t_phys`` — the plausible
    mistake, and the one the whole module is built to avoid — every one of these would fail.
    """
    r = compute()
    assert {r.mos[m].V_t for m in MATERIALS} == {r.mos["SiO2"].V_t}, "V_t moved with the material"
    assert {r.mos[m].C_ox for m in MATERIALS} == {r.mos["SiO2"].C_ox}, "C_ox moved with the material"
    # ...and it is the *real* device model, not a stand-in: the same call reproduces it.
    assert r.mos["HfO2"].V_t == dev.threshold_voltage(
        CHANNEL_N_A, FEATURE_EOT_UM, gate=r.mos["HfO2"].gate,
        channel_length_um=r.mos["HfO2"].channel_length_um,
        implant_dose=r.mos["HfO2"].implant_dose, implant_kind=r.mos["HfO2"].implant_kind,
    ).V_t


def test_the_other_currency_moves_while_the_device_does_not():
    """The split that no scalar can fake: same electrical gate, ``t_phys`` and leakage far apart."""
    r = compute()
    sio2, hfo2 = r.stacks["SiO2"], r.stacks["HfO2"]
    assert sio2.t_phys_um == pytest.approx(FEATURE_EOT_UM)          # the κ=3.9 seam: EOT *is* t_phys
    assert hfo2.thickness_gain == pytest.approx(25.0 / 3.9)         # 6.4× the barrier, same gate
    assert hfo2.gate_leakage_A_cm2 < sio2.gate_leakage_A_cm2 * 1e-3
    assert hfo2.decades_saved_vs_sio2 > 0.0


def test_the_wall_is_monotone_and_lands_where_sio2_stopped_scaling():
    """The honest payload is the *shape*: leakage rises monotonically as the electrical gate scales down."""
    r = compute()
    j = r.j_gate["SiO2"]
    assert all(b > a for a, b in zip(j, j[1:])), "SiO₂ leakage must rise monotonically as EOT scales down"
    assert j[-1] > WALL_J_A_CM2 > j[0], "the ladder must actually cross the usability line"
    # The wall is where SiO₂ crosses ~1 A/cm² — the era's ~1.4–1.5 nm, and the model's cited anchor.
    assert 1.2e-3 < r.wall_eot_um < 1.7e-3
    assert hk.gate_leakage(r.wall_eot_um, "SiO2") == pytest.approx(WALL_J_A_CM2, rel=1e-2)


def test_more_kappa_is_not_better_the_counterexample_is_flat():
    """TiO₂ (κ=80, φ_B=0): 20× the physical thickness, and the ladder does not move it at all."""
    r = compute()
    j = r.j_gate["TiO2"]
    assert all(x == j[0] for x in j), "a zero-barrier dielectric must be flat at every EOT"
    assert j[0] == pytest.approx(hk.J0_REFERENCE)                   # it leaks the prefactor, always
    assert r.stacks["TiO2"].decades_saved_vs_sio2 < 0.0             # worse than the layer it 'improves'


def test_the_ladder_stays_inside_the_validated_regime():
    """**The slice-3 magnitude trap, pinned.** The ladder may not walk where the model cannot speak.

    ``decades_saved`` is ∝ EOT, so a thicker ladder inflates the HfO₂ win without bound: at EOT = 2 nm
    the model says +11 decades, versus a literature ~3–5 at 1 nm — and real HfO₂ that physically thick is
    trap-limited, a floor this model explicitly does not carry. The featured EOT therefore stays at the
    thin end (~1–1.5 nm, the direct-tunnelling regime), where the model's SiO₂ ≈ 6.5e2 A/cm² and HfO₂
    ≈ 2e-3 A/cm² both sit on top of published data. Widen this and the demo starts making datasheet claims.
    """
    assert FEATURE_EOT_UM <= 1.5e-3, "the featured EOT must stay in the direct-tunnelling regime"
    assert min(EOT_LADDER_UM) >= 1.0e-3, "the ladder must not walk below the model's honest floor"
    saved = hk.leakage_decades_saved(FEATURE_EOT_UM, "HfO2")
    # Inside the m* spread the constants are flagged with (0.08–0.2 m₀ ⇒ 3.9–9.5 decades) — the honest band.
    assert 3.9 <= saved <= 9.5, f"the featured win ({saved:.1f} dec) escaped the flagged m* band"


def test_the_headline_is_never_rounded_up():
    """A "≳ N decades" claim rounded *up* is not a ≳ claim — the summary must not overstate the win."""
    r = compute()
    saved = r.stacks["HfO2"].decades_saved_vs_sio2
    assert float(f"{saved:.1f}") <= saved or math.isclose(float(f"{saved:.1f}"), saved, abs_tol=0.05)


def test_figure_builds():
    r = compute()
    pytest.importorskip("matplotlib")               # the figure is not in the correctness path (ADR 0002)
    from chip.demo_highk_history import save_figure
    assert save_figure(r).is_file()
