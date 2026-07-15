"""F3 high-κ gate dielectric (``chip.high_k``) — the one thickness that feeds two currencies.

The triad, per ``docs/plans/high-k-metal-gate-f3.md`` + ``historical-modes.md``:

  * **tight — the seam:** :func:`chip.high_k.eot` at K=3.9 is the **identity** on its input
    (``EOT == t_phys``), so today's ``t_ox`` numbers are byte-for-byte unchanged;
  * **tight — the identity (the discriminator):** at fixed EOT, ``C_ox`` — and therefore ``V_t`` and
    ``I_Dsat`` — are **material-independent by construction** (``ε_SiO₂/EOT ≡ ε₀·K/t_phys``), while the
    physical thickness moves by ``K/3.9``. Asserted here *against the real* :mod:`chip.device`, which is
    the proof that F3 needs no change there;
  * **tight — the ratio:** the flagged prefactor is shared, so it **cancels exactly** in
    :func:`chip.high_k.leakage_decades_saved` — the decades-saved figure is pure cited-exponent physics;
  * **cross-check (non-circular):** the cited (φ_B, m*) pairs — never fitted to a leakage curve —
    reproduce the textbook SiO₂ "~1 decade per ~2 Å" slope;
  * **flagged:** the absolute prefactor ``J0_REFERENCE`` and the tunnelling masses (HfO₂'s spread
    0.08–0.2 dominates) — asserted by shape/sign/band, never as exact currents.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import math

import pytest

from chip import device, high_k as hk
from chip.diffusion_dopant import CM_PER_UM


# --------------------------------------------------------------------------- #
# The seam — at K=3.9 the EOT is the identity (tight, byte-for-byte)
# --------------------------------------------------------------------------- #
def test_eot_at_sio2_is_the_bit_for_bit_identity():
    """eot(t, 3.9) == t exactly — the seam that keeps today's t_ox numbers unchanged."""
    for t in (1.0e-3, 1.5e-3, 2.0e-3, 0.02, 0.1):
        assert hk.eot(t, hk.K_SIO2) == t                       # byte-identical, not approx
        assert hk.physical_thickness_for_eot(t, hk.K_SIO2) == t
        assert hk.SIO2.eot_um(t) == t


def test_eot_matches_the_cited_definition_and_inverts():
    """EOT = t_phys·(3.9/K) (Robertson eq. 2), and physical_thickness_for_eot is its exact inverse."""
    for kappa in (7.0, 9.0, 25.0, 80.0):
        for t in (1.0e-3, 5.0e-3):
            assert hk.eot(t, kappa) == pytest.approx(t * (hk.K_SIO2 / kappa), rel=1e-12)
            assert hk.physical_thickness_for_eot(hk.eot(t, kappa), kappa) == pytest.approx(t, rel=1e-12)


def test_hfo2_buys_kappa_over_3_9_times_the_physical_thickness():
    """At matched EOT the physical layer grows by exactly K/3.9 — ~6.4× for HfO₂. The whole lever."""
    stack = hk.gate_stack(1.0e-3, hk.HFO2)                     # EOT = 1 nm
    assert stack.thickness_gain == pytest.approx(25.0 / 3.9, rel=1e-12)
    assert stack.t_phys_um == pytest.approx(1.0e-3 * 25.0 / 3.9, rel=1e-12)
    assert 6.0 < stack.thickness_gain < 6.5                    # ~6.4×


# --------------------------------------------------------------------------- #
# The identity — C_ox/V_t/I_Dsat are material-INDEPENDENT at fixed EOT (the discriminator).
# Asserted against the REAL chip.device: this is the proof that F3 touches nothing there.
# --------------------------------------------------------------------------- #
def test_eot_into_device_computes_the_true_physical_capacitance():
    """device.oxide_capacitance(EOT) ≡ ε₀·K/t_phys — the real stack's C (Robertson eq. 1), not a proxy.

    The EOT route is an identity, not an approximation: this is why feeding EOT into the existing SiO₂
    capacitance path is *correct physics* for a high-κ stack and device.py needs no change.
    """
    for diel in (hk.SIO2, hk.HFO2, hk.TIO2):
        for t_phys in (1.0e-3, 4.0e-3, 0.02):
            c_via_eot = device.oxide_capacitance(diel.eot_um(t_phys))
            c_physical = device.EPS0 * diel.kappa / (t_phys * CM_PER_UM)
            assert c_via_eot == pytest.approx(c_physical, rel=1e-12)


def test_C_ox_is_identical_across_materials_at_fixed_EOT():
    """The electrical gate is untouched by the swap — C_ox at fixed EOT is material-independent."""
    eot_um = 1.0e-3
    caps = [device.oxide_capacitance(hk.gate_stack(eot_um, d).eot_um) for d in (hk.SIO2, hk.HFO2, hk.TIO2)]
    assert caps[0] == caps[1] == caps[2]                       # byte-identical: the input IS the same EOT


def test_V_t_and_I_Dsat_do_not_move_when_swapping_to_high_k_at_matched_EOT():
    """The payload's other half: swap SiO₂→HfO₂ at matched EOT and *every device number stands still*.

    Unconditional (an identity), for any N_A/bias — no barrier physics involved. The leakage collapse
    (below) is therefore bought for *free* in device terms, which is exactly why the industry did it.
    """
    eot_um, N_A, V_GS, W, L = 1.0e-3, 5.0e16, 1.8, 10.0, 0.045
    sio2 = hk.gate_stack(eot_um, hk.SIO2)
    hfo2 = hk.gate_stack(eot_um, hk.HFO2)
    assert hfo2.t_phys_um > 6.0 * sio2.t_phys_um               # physically a *very* different layer …

    mos_sio2 = device.threshold_voltage(N_A, sio2.eot_um, channel_length_um=L)
    mos_hfo2 = device.threshold_voltage(N_A, hfo2.eot_um, channel_length_um=L)
    assert mos_hfo2.V_t == mos_sio2.V_t                        # … electrically the same transistor
    assert device.saturation_current(mos_hfo2, V_GS, W) == device.saturation_current(mos_sio2, V_GS, W)


# --------------------------------------------------------------------------- #
# The WKB exponent — the cited leg (φ_B and m* move together)
# --------------------------------------------------------------------------- #
def test_tunnel_decay_matches_the_wkb_definition():
    """α = 2·√(2 m* φ_B)/ħ, returned per µm."""
    phi, m = 3.2, 0.5
    expected = 2.0 * math.sqrt(2.0 * m * hk.M_ELECTRON * phi * 1.602176634e-19) / hk.HBAR * 1e-6
    assert hk.tunnel_decay(phi, m) == pytest.approx(expected, rel=1e-9)


def test_decay_rises_with_both_barrier_and_mass_under_a_shared_sqrt():
    """α ∝ √(m*·φ_B): quadrupling either factor doubles α — they enter identically. Neither is optional."""
    base = hk.tunnel_decay(1.0, 0.1)
    assert hk.tunnel_decay(4.0, 0.1) == pytest.approx(2.0 * base, rel=1e-9)
    assert hk.tunnel_decay(1.0, 0.4) == pytest.approx(2.0 * base, rel=1e-9)


def test_leakage_falls_exponentially_with_physical_thickness():
    """J_g = J₀·exp(−α·t): equal thickness *increments* give equal leakage *ratios* (the exponential)."""
    t0 = 1.5e-3
    step = 0.2e-3
    r1 = hk.gate_leakage(t0 + step, hk.SIO2) / hk.gate_leakage(t0, hk.SIO2)
    r2 = hk.gate_leakage(t0 + 2 * step, hk.SIO2) / hk.gate_leakage(t0 + step, hk.SIO2)
    assert r1 == pytest.approx(r2, rel=1e-9)
    assert r1 < 1.0                                            # thicker ⇒ less leakage


# --------------------------------------------------------------------------- #
# The non-circular cross-check — cited constants PREDICT the textbook SiO₂ slope
# --------------------------------------------------------------------------- #
def test_sio2_slope_reproduces_the_textbook_decade_per_2_angstrom():
    """SiO₂'s cited (φ_B=3.2 eV, m*=0.5) predicts ~1 decade of gate leakage per ~2 Å — *not* fitted to it.

    The band offset and the tunnelling mass come from band-structure/photon-assisted-tunnelling work, not
    from a J–V leakage curve; that they reproduce the industry's rule of thumb is this module's
    independent validation of the exponent (the same non-circular spirit as Irvin vs Masetti elsewhere).
    """
    decade_A = hk.decade_thickness_um(hk.SIO2.barrier_eV, hk.SIO2.tunnel_mass_rel) * 1e4  # µm → Å
    assert 1.5 < decade_A < 2.5                                # the textbook ~2 Å
    assert decade_A == pytest.approx(1.78, abs=0.05)           # this model's landing point


def test_sio2_leakage_lands_on_the_cited_scale_across_the_wall():
    """One flagged prefactor + the cited exponent reproduce SiO₂'s leakage across ~6 orders of magnitude.

    FLAGGED (the prefactor is a house lump pinned at 1.5 nm), but the *shape* across the wall is cited:
    Robertson has SiO₂ under 2 nm "exceeding 1 A/cm² at 1 V" and ~1.4 nm as the too-leaky node, while a
    ~2 nm oxide sits down in the mA/cm² range. Bounds, not exact currents.
    """
    assert hk.gate_leakage(1.5e-3, hk.SIO2) == pytest.approx(1.0, rel=1e-9)   # the calibration anchor
    assert hk.gate_leakage(1.2e-3, hk.SIO2) > 10.0                            # the wall: runaway
    assert hk.gate_leakage(2.0e-3, hk.SIO2) < 1.0e-2                          # 2 nm: quiet
    assert 1e7 < hk.J0_REFERENCE < 1e10                                       # a plausible supply prefactor


# --------------------------------------------------------------------------- #
# The payload — decades saved at matched EOT, and the fact that it is prefactor-FREE
# --------------------------------------------------------------------------- #
def test_decades_saved_is_independent_of_the_flagged_prefactor():
    """The house prefactor cancels exactly in the ratio — the payload carries no calibrated constant."""
    eot_um = 1.0e-3
    decades = hk.leakage_decades_saved(eot_um, hk.HFO2)
    for J0 in (1.0, 1e5, hk.J0_REFERENCE, 1e12):               # any prefactor at all …
        t_ref = hk.SIO2.thickness_for_eot_um(eot_um)
        t_new = hk.HFO2.thickness_for_eot_um(eot_um)
        ratio_decades = math.log10(hk.gate_leakage(t_ref, hk.SIO2, J0=J0)
                                   / hk.gate_leakage(t_new, hk.HFO2, J0=J0))
        assert ratio_decades == pytest.approx(decades, rel=1e-9)   # … gives the same decades


def test_hfo2_saves_orders_of_magnitude_at_matched_eot():
    """The headline: same electrical gate, orders of magnitude less leakage. Sign is tight; size flagged."""
    decades = hk.leakage_decades_saved(1.0e-3, hk.HFO2)
    assert decades > 3.0                                       # "orders of magnitude" — the tight sign
    assert decades == pytest.approx(5.6, abs=0.3)              # this model's central landing point


def test_the_barrier_spends_back_part_of_the_thickness_gain():
    """The naive thickness-only story overstates: HfO₂'s 6.4× thickness nets only ~2× in the exponent.

    Because K and the band gap are inversely correlated (Robertson Fig. 5), HfO₂'s lower φ_B *and* lower
    m* make it decay ~3.2× slower per nm than SiO₂ — so the exponent gain is 6.4/3.2 ≈ 2, not 6.4. This
    is what a universal decay constant would have got wrong.
    """
    slow_factor = hk.SIO2.decay_per_um / hk.HFO2.decay_per_um
    assert slow_factor == pytest.approx(3.2, abs=0.2)          # HfO₂ decays ~3.2× slower per nm

    eot_um = 1.0e-3
    exp_sio2 = hk.SIO2.decay_per_um * hk.SIO2.thickness_for_eot_um(eot_um)
    exp_hfo2 = hk.HFO2.decay_per_um * hk.HFO2.thickness_for_eot_um(eot_um)
    thickness_gain = 25.0 / 3.9
    assert exp_hfo2 / exp_sio2 == pytest.approx(thickness_gain / slow_factor, rel=1e-9)
    assert exp_hfo2 / exp_sio2 < thickness_gain               # strictly less than the naive estimate
    assert exp_hfo2 / exp_sio2 == pytest.approx(2.0, abs=0.2)


def test_hfo2_mass_spread_is_the_dominant_flagged_uncertainty():
    """The literature m* spread (0.08–0.2) bands the HfO₂ win at ~3.9–9.5 decades — flagged, not exact."""
    band = [hk.leakage_decades_saved(1.0e-3, hk.Dielectric("HfO₂", 25.0, 1.4, m)) for m in (0.08, 0.20)]
    assert band[0] == pytest.approx(3.9, abs=0.3)
    assert band[1] == pytest.approx(9.5, abs=0.4)
    assert band[0] < hk.leakage_decades_saved(1.0e-3, hk.HFO2) < band[1]   # the central value sits inside
    assert band[0] > 0.0                                       # even the pessimistic end still wins big


# --------------------------------------------------------------------------- #
# The counterexample — "more K is better" is FALSE, and it falls out of the cited table for free
# --------------------------------------------------------------------------- #
def test_zero_barrier_gives_zero_decay_for_any_mass():
    """At φ_B = 0 the barrier is transparent at every thickness — and the conclusion is mass-INDEPENDENT.

    This is why TiO₂'s unsourced mass is not load-bearing (:data:`chip.high_k.TIO2`).
    """
    for m in (0.01, 0.1, 0.5, 1.0, 10.0):
        assert hk.tunnel_decay(0.0, m) == 0.0
    assert hk.decade_thickness_um(0.0, 0.5) == math.inf


def test_tio2_huge_kappa_buys_thickness_and_still_leaks():
    """K=80 buys 20× the physical thickness — and saves *nothing*, because its CB offset is 0.

    Robertson's requirement 4 (band offsets over 1 eV) as a computed consequence rather than an assertion:
    the industry chose K=25/φ_B=1.4 over K=80/φ_B=0, and this is why.
    """
    stack = hk.gate_stack(1.0e-3, hk.TIO2)
    assert stack.thickness_gain == pytest.approx(80.0 / 3.9, rel=1e-12)     # 20.5× thicker …
    assert stack.gate_leakage_A_cm2 == pytest.approx(hk.J0_REFERENCE, rel=1e-12)   # … and leaks flat out
    assert stack.decades_saved_vs_sio2 < 0.0                                # strictly *worse* than SiO₂
    # thickness is irrelevant to it: 10× thicker TiO₂ leaks exactly the same
    assert hk.gate_leakage(1.0, hk.TIO2) == pytest.approx(hk.gate_leakage(0.1, hk.TIO2), rel=1e-12)


def test_more_kappa_is_not_monotonically_better():
    """The trade-off, stated as a test: HfO₂ (K=25) beats *both* SiO₂ (K=3.9) and TiO₂ (K=80)."""
    eot_um = 1.0e-3
    d_hfo2 = hk.leakage_decades_saved(eot_um, hk.HFO2)
    d_tio2 = hk.leakage_decades_saved(eot_um, hk.TIO2)
    assert d_hfo2 > 0.0 > d_tio2                               # the interior optimum, non-monotone in K


# --------------------------------------------------------------------------- #
# Registry + guards
# --------------------------------------------------------------------------- #
def test_registry_carries_the_cited_robertson_table_values():
    """The registry's K/φ_B are Robertson Table 2 verbatim (one coherent set)."""
    assert (hk.SIO2.kappa, hk.SIO2.barrier_eV) == (3.9, 3.2)
    assert (hk.HFO2.kappa, hk.HFO2.barrier_eV) == (25.0, 1.4)
    assert (hk.TIO2.kappa, hk.TIO2.barrier_eV) == (80.0, 0.0)
    assert hk.DIELECTRICS["HfO2"] is hk.HFO2
    assert hk.SIO2.kappa == hk.K_SIO2                          # SiO₂ *is* the EOT reference
    # the registry's K matches device.py's oxide permittivity — the same 3.9, not a second opinion
    assert device.EPS_OX == pytest.approx(hk.K_SIO2 * device.EPS0, rel=1e-12)


def test_string_lookup_matches_object_form():
    """The registry accepts a name or the Dielectric itself (the F2 scheme-lookup convention)."""
    assert hk.gate_leakage(2.0e-3, "HfO2") == hk.gate_leakage(2.0e-3, hk.HFO2)
    assert hk.leakage_decades_saved(1.0e-3, "HfO2", reference="SiO2") == \
        hk.leakage_decades_saved(1.0e-3, hk.HFO2, reference=hk.SIO2)


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_non_positive_thicknesses_and_kappa_are_rejected(bad):
    """Guards — a zero/negative thickness or K is a recipe bug, not a limit to extrapolate into."""
    with pytest.raises(ValueError):
        hk.eot(bad, 25.0)
    with pytest.raises(ValueError):
        hk.eot(1.0e-3, bad)
    with pytest.raises(ValueError):
        hk.physical_thickness_for_eot(bad, 25.0)
    with pytest.raises(ValueError):
        hk.gate_leakage(bad, hk.SIO2)
    with pytest.raises(ValueError):
        hk.leakage_decades_saved(bad, hk.HFO2)


def test_negative_barrier_and_non_positive_mass_are_rejected():
    """φ_B < 0 is unphysical here (a well, not a barrier); m* ≤ 0 is a bug. φ_B = 0 is *allowed* — TiO₂."""
    with pytest.raises(ValueError):
        hk.tunnel_decay(-0.1, 0.5)
    with pytest.raises(ValueError):
        hk.tunnel_decay(3.2, 0.0)
    with pytest.raises(ValueError):
        hk.Dielectric("bad", 25.0, -1.0, 0.1)
    assert hk.tunnel_decay(0.0, 0.5) == 0.0                    # the barrier-collapse edge is legal
