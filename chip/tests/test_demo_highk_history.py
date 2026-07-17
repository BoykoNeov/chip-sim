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
  * **the headline is never rounded up** — a "≳ N decades" claim is a *lower bound*, so the displayed N may
    only ever sit **below** the computed win. This one caught a live instance: the featured 5.565-decade
    win rendered as "≳5.6" under plain ``.1f``, claiming more than the model supports;
  * **the idealized stack is never presented as the shipped product** (the IL slice's guard) — the no-IL
    win is a *ceiling* no fab can build, and this demo used to feature it under a "2007, 45 nm" label.
    Both HfO₂ stacks are now on the figure and the era label belongs to the as-built one.

The figure is **not** in the correctness path (ADR 0002): rendering is checked only for "builds without
error", and skipped where the optional viz extra is absent.
"""
import numpy as np
import pytest

from chip import device as dev
from chip import high_k as hk
from chip.demo_highk_history import (
    CHANNEL_N_A, EOT_LADDER_UM, FEATURE_EOT_UM, FEATURE_T_IL_UM, IL_SWEEP_UM, MATERIALS, WALL_J_A_CM2,
    compute, floor_decades,
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


def test_the_headline_claim_is_floored_never_rounded_up():
    """A "≳ N decades" claim rounded *up* is not a ≳ claim — the featured win may never be overstated.

    This is not hypothetical: the featured HfO₂ win is **5.565** decades, which plain ``f"{x:.1f}"``
    renders **"5.6"** — asserting "at least 5.6" for a value that is *below* 5.6. Hence
    :func:`chip.demo_highk_history.floor_decades`, and hence this assert being on the **formatted string
    the reader actually sees** rather than on the float behind it.
    """
    saved = compute().stacks["HfO2"].decades_saved_vs_sio2
    assert float(floor_decades(saved)) <= saved, (
        f"the displayed claim ≳{floor_decades(saved)} overstates the computed win ({saved!r})"
    )
    assert float(f"{saved:.1f}") > saved, (
        "regression canary: plain .1f no longer rounds this value UP, so floor_decades is no longer "
        "demonstrably load-bearing here — re-check the featured EOT before relaxing anything"
    )
    # The rule must hold for any value, not just today's — including the ones .1f rounds up.
    assert floor_decades(5.565) == "5.5" and floor_decades(5.99) == "5.9" and floor_decades(6.0) == "6.0"


def test_the_demo_does_not_present_the_idealized_stack_as_the_shipped_product():
    """**An honesty guard.** The figure carries two HfO₂ leakages; the 45 nm one must be the *as-built* one.

    The idealized no-IL win (≳5.5 decades, 1.8e-3 A/cm²) is a **ceiling**, not a product: no fab builds a
    high-κ gate without an interfacial layer. Featuring it under a "2007, 45 nm" label — which is what
    this demo did before the IL was modelled — states the ceiling as the shipped number. Both are now
    plotted, and this pins that the real one exists, is distinct, and is the worse of the two.
    """
    r = compute()
    ideal, real = r.stacks["HfO2"], r.real_stack
    assert real.has_interfacial_layer and real.t_il_um == FEATURE_T_IL_UM
    assert real.eot_um == ideal.eot_um                          # the same electrical gate …
    assert real.gate_leakage_A_cm2 > ideal.gate_leakage_A_cm2   # … and it really does leak more
    assert 0.0 < real.decades_saved_vs_sio2 < ideal.decades_saved_vs_sio2   # still a win, roughly halved
    # both ends of the model's claim sit inside the reported literature spread (~2–6 decades)
    assert 2.0 <= real.decades_saved_vs_sio2 <= 6.0
    assert 2.0 <= ideal.decades_saved_vs_sio2 <= 6.0


def test_the_il_panel_is_prefactor_free_and_linear_to_the_floor():
    """The right panel's payload: the win falls **linearly** to exactly zero at the EOT floor.

    Prefactor-free by construction (a ratio cancels the house J₀), so this panel contains no flagged
    magnitude at all — which is why it is allowed to carry the slice's headline.
    """
    r = compute()
    d = r.decades_saved_vs_t_il
    assert all(b < a for a, b in zip(d, d[1:])), "the IL must monotonically destroy the win"
    steps = np.diff(d)
    assert np.allclose(steps, steps[0], rtol=1e-9), "the cost of the IL must be linear in t_IL"
    assert d[0] == pytest.approx(r.stacks["HfO2"].decades_saved_vs_sio2)   # t_IL=0 is the idealized end
    assert d[-1] > 0.0                                          # the sweep stops just short of the floor
    # …and extrapolating the line to t_IL = EOT lands on zero: the high-κ squeezed out of its own budget
    at_floor = hk.leakage_decades_saved(FEATURE_EOT_UM, "HfO2", t_il_um=FEATURE_EOT_UM * (1 - 1e-9))
    assert at_floor == pytest.approx(0.0, abs=1e-7)


def test_the_eot_floor_is_real_and_the_demo_never_walks_through_it():
    """The floor is a **refusal**, not a curve that keeps going: below t_IL the stack cannot be built."""
    r = compute()
    assert r.real_stack.eot_floor_um == FEATURE_T_IL_UM         # SiO₂ IL ⇒ the floor IS its thickness
    with pytest.raises(ValueError, match="floor"):
        hk.gate_stack(FEATURE_T_IL_UM * 0.9, "HfO2", t_il_um=FEATURE_T_IL_UM)
    assert min(IL_SWEEP_UM) >= 0.0 and max(IL_SWEEP_UM) < FEATURE_EOT_UM, "the sweep must stay buildable"
    # the ladder never dips under the floor either, so the as-built curve is defined the whole way
    assert min(EOT_LADDER_UM) > FEATURE_T_IL_UM
    assert not np.isnan(r.j_gate_real).any()


def test_the_representative_il_is_one_a_fab_could_actually_grow():
    """The featured IL must sit in the range real stacks live in — ~0.4–0.5 nm is the practical limit.

    The model will happily price a 0.1 nm IL; a fab cannot build one (below ~0.4 nm the film stops being
    a film, and scavenging that hard costs work-function control and reliability — a named scope edge).
    Featuring a sub-limit IL would understate the floor exactly the way the idealized stack does.
    """
    assert 0.4e-3 <= FEATURE_T_IL_UM <= 1.0e-3
    assert FEATURE_T_IL_UM < FEATURE_EOT_UM, "the featured stack must be buildable at the featured EOT"


def test_figure_builds():
    r = compute()
    pytest.importorskip("matplotlib")               # the figure is not in the correctness path (ADR 0002)
    from chip.demo_highk_history import save_figure
    assert save_figure(r).is_file()
