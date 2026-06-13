"""Deep-level-metal lifetime/leakage validation — the SRH triad (plan §7 / §5a Tier 2, G4b).

No engine underneath — the SRH lifetime and the generation leakage are closed forms (like Deal–Grove /
Scheil / the compact ``V_t`` / Pfann) — so these tests carry the whole triad:

* **Analytical limit (tight) — the low-injection reduction of the full SRH statistics.** The full
  :func:`chip.lifetime.srh_rate` ``U(n, p)``, in the p-type low-injection limit, reduces to the single
  minority-electron lifetime ``τ = τ_n0 = 1/(σ_n·v_th·N_t)`` — with the hole cross-section ``σ_p`` *and*
  the trap energy ``E_t`` **dropping out** (the content of the leg). The clean limit ``N_metal = 0`` →
  ``τ = τ_bulk`` is bit-for-bit (the seam). Rate-additivity is true *by construction* → a regression guard.
* **Conservation (tight) — detailed balance.** ``U = 0`` **exactly** at equilibrium (``p·n = n_i²``),
  for *any* ``σ_n``, ``σ_p``, ``E_t`` — that parameter-independence is what makes it a real check.
* **Benchmark (loose) — the cited capture data + the textbook order.** Clean FZ silicon ``τ ~ ms`` /
  ``L ~ mm``; ``[Fe] ~ 1e12 cm⁻³`` → ``τ ~ few µs``; more metal → shorter ``τ`` → higher leakage. The
  cross-sections (Sze; Graff) and the calibration are **flagged**, not asserted tight.

Non-circularity: the SRH machinery (detailed balance + the low-injection reduction) is universal
statistics independent of the loose ``σ`` magnitudes; the magnitudes are flagged, never anchored.
"""
import math

import numpy as np
import pytest

from chip import lifetime as life
from chip.device import NI_300K, thermal_voltage
from chip.purification import Contamination


# --------------------------------------------------------------------------- #
# Benchmark (loose): the cited σ order + the textbook lifetime/leakage scaling
# --------------------------------------------------------------------------- #
def test_capture_cross_sections_are_order_of_magnitude_metal_data():
    # FLAGGED literature values (Sze; Graff): Fe_i a strong recombination centre, Cu weaker per atom;
    # both in the deep-level metal range. Only the contrast/scale is asserted (the loose leg).
    assert life.CAPTURE_SIGMA_N["Fe"] > life.CAPTURE_SIGMA_N["Cu"]
    for sp in ("Fe", "Cu"):
        assert 1.0e-16 < life.CAPTURE_SIGMA_N[sp] < 1.0e-13


def test_textbook_lifetime_and_leakage_order():
    # Clean float-zone silicon: τ ~ 1 ms, L ~ mm.
    tau_clean = life.srh_lifetime(None)
    assert tau_clean == life.TAU_BULK                                  # clean → τ_bulk exactly
    assert life.diffusion_length(tau_clean) * 1.0e4 > 1.0e3            # L > 1 mm (in µm)
    # An interstitial-iron level ~1e12 cm⁻³ drags τ down to a few µs (the classic Fe lifetime order).
    tau_fe = life.srh_lifetime(Contamination(Fe=1.0e12))
    assert 1.0 < tau_fe * 1.0e6 < 10.0                                 # τ ~ few µs
    # More metal → shorter lifetime → higher generation leakage (the device-killer direction).
    j_clean = life.generation_leakage_density(tau_clean, N_A=1.0e17)
    j_fe = life.generation_leakage_density(tau_fe, N_A=1.0e17)
    assert j_fe > j_clean


# --------------------------------------------------------------------------- #
# Analytical limit (tight): the clean seam + the full-SRH low-injection reduction
# --------------------------------------------------------------------------- #
def test_clean_limit_is_tau_bulk_bit_for_bit():
    # No metals (None or all-zero) → τ = τ_bulk exactly (the seam: a clean feed never moves lifetime).
    assert life.srh_lifetime(None) == life.TAU_BULK
    assert life.srh_lifetime(Contamination()) == life.TAU_BULK
    assert life.srh_lifetime({}) == life.TAU_BULK
    assert life.recombination_rate(None) == 0.0


def test_low_injection_reduces_full_srh_to_tau_n0():
    # The honest analytic leg: the full U(n,p) in the p-type low-injection limit → τ = τ_n0 = 1/(σ_n v_th N_t).
    N_A, N_t, sigma_n = 1.0e17, 1.0e12, life.CAPTURE_SIGMA_N["Fe"]
    n0 = NI_300K**2 / N_A                                   # equilibrium minority electrons
    dn = 1.0e10                                             # excess ≪ N_A (low injection)
    n, p = n0 + dn, N_A + dn
    tau_n0 = 1.0 / (sigma_n * life.V_TH * N_t)
    # midgap trap, σ_p = σ_n: τ = Δn/U recovers τ_n0 essentially exactly.
    U = life.srh_rate(n, p, N_t, sigma_n=sigma_n, sigma_p=sigma_n, E_t_minus_Ei_eV=0.0)
    assert dn / U == pytest.approx(tau_n0, rel=1e-4)


def test_sigma_p_and_trap_energy_drop_out_of_the_lifetime():
    # The CONTENT of the analytic leg: in low injection σ_p and E_t drop out → σ_n is the sole
    # governing cross-section. Vary both over orders/levels; τ stays τ_n0 to a fraction of a percent.
    N_A, N_t, sigma_n = 1.0e17, 1.0e12, life.CAPTURE_SIGMA_N["Fe"]
    n0 = NI_300K**2 / N_A
    dn = 1.0e10
    n, p = n0 + dn, N_A + dn
    tau_n0 = 1.0 / (sigma_n * life.V_TH * N_t)
    for sigma_p in (sigma_n / 10.0, sigma_n, sigma_n * 10.0):
        for E_t in (-0.1, 0.0, 0.1):
            U = life.srh_rate(n, p, N_t, sigma_n=sigma_n, sigma_p=sigma_p, E_t_minus_Ei_eV=E_t)
            assert dn / U == pytest.approx(tau_n0, rel=1e-2)


def test_rate_additivity_is_a_regression_guard():
    # 1/τ is affine in the metal concentrations BY CONSTRUCTION (the rates add) — a guard, not an anchor.
    base = life.recombination_rate(Contamination())
    only_fe = life.recombination_rate(Contamination(Fe=3.0e13))
    only_cu = life.recombination_rate(Contamination(Cu=7.0e13))
    both = life.recombination_rate(Contamination(Fe=3.0e13, Cu=7.0e13))
    assert both - base == pytest.approx((only_fe - base) + (only_cu - base))


# --------------------------------------------------------------------------- #
# Conservation (tight): detailed balance — U = 0 at equilibrium, parameter-independent
# --------------------------------------------------------------------------- #
def test_detailed_balance_U_is_zero_at_equilibrium():
    # At p·n = n_i² (thermal equilibrium) the SRH net rate vanishes EXACTLY — generation balances
    # recombination — for ANY σ_n, σ_p, E_t (the parameter-independence that makes it a real check).
    n_i = NI_300K
    equilibria = [(n_i, n_i), (1.0e16, n_i**2 / 1.0e16), (1.0e4, n_i**2 / 1.0e4)]  # power-of-ten ⇒ pn=n_i² exact
    for n, p in equilibria:
        for sigma_n in (1.0e-14, 5.0e-14):
            for sigma_p in (1.0e-16, 1.0e-14):
                for E_t in (-0.2, 0.0, 0.3):
                    U = life.srh_rate(n, p, N_t=1.0e12, sigma_n=sigma_n, sigma_p=sigma_p,
                                      E_t_minus_Ei_eV=E_t)
                    assert U == 0.0                          # bit-for-bit zero (numerator p·n − n_i² = 0)


def test_srh_rate_recombines_above_and_generates_below_equilibrium():
    # The sign convention behind the two regimes the triad uses: pn > n_i² ⇒ net recombination (U>0);
    # a depleted region (n, p → 0 ≪ n_i²) ⇒ net generation (U<0, the leakage source).
    n_i = NI_300K
    U_rec = life.srh_rate(1.0e15, 1.0e15, N_t=1.0e12, sigma_n=5.0e-14, sigma_p=5.0e-14)
    U_gen = life.srh_rate(1.0, 1.0, N_t=1.0e12, sigma_n=5.0e-14, sigma_p=5.0e-14)
    assert U_rec > 0.0 and U_gen < 0.0


# --------------------------------------------------------------------------- #
# The lifetime / diffusion-length / leakage trends (the wired directions)
# --------------------------------------------------------------------------- #
def test_more_metal_shortens_lifetime_and_diffusion_length():
    taus = [life.srh_lifetime(Contamination(Fe=N)) for N in (0.0, 1.0e11, 1.0e12, 1.0e13)]
    assert all(t1 < t0 for t0, t1 in zip(taus, taus[1:]))             # τ falls monotonically with [Fe]
    Ls = [life.diffusion_length(t) for t in taus]
    assert all(l1 < l0 for l0, l1 in zip(Ls, Ls[1:]))                 # …so does L = √(Dτ)


def test_leakage_rises_with_metal_and_depletion_width_tracks_doping():
    # J_gen ∝ 1/τ: dirtier feed → shorter τ → more leakage.
    clean = life.device_leakage(Contamination(), N_A=1.0e17)
    dirty = life.device_leakage(Contamination(Fe=1.0e13), N_A=1.0e17)
    assert dirty.j_leak > clean.j_leak
    assert dirty.tau < clean.tau and dirty.L_diff < clean.L_diff
    # W = √(2εV/qN_A): heavier doping → thinner depletion width → slightly less generation leakage.
    assert life.depletion_width(1.0e18) < life.depletion_width(1.0e16)


def test_device_leakage_clean_is_the_seam_baseline():
    # The clean wafer reads τ_bulk and the tiny baseline leakage — comfortably inside the spec window
    # (the seam: clean feedstock ⇒ no leakage consequence). Bundle units echo correctly.
    b = life.device_leakage(None, N_A=1.0e17)
    assert b.tau == life.TAU_BULK
    assert b.tau_us == pytest.approx(life.TAU_BULK * 1.0e6)
    assert b.j_leak_nA_cm2 == pytest.approx(b.j_leak * 1.0e9)
    assert b.j_leak_nA_cm2 < 1.0                                      # baseline ≪ the nA/cm² window


# --------------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------------- #
def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        life.depletion_width(-1.0e17)                                  # N_A must be positive
    with pytest.raises(ValueError):
        life.depletion_width(1.0e17, V_J=0.0)                          # V_J must be positive
    with pytest.raises(ValueError):
        life.generation_leakage_density(0.0, N_A=1.0e17)              # τ must be positive
    with pytest.raises(ValueError):
        life.diffusion_length(-1.0e-6)                                 # τ must be ≥ 0
