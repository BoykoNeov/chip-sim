"""Chip v1.2 validation: the Phase 1↔2 back-coupling — OED + dopant segregation.

This carries the plan's v1.2 triad (:mod:`coupling`). The coupling is built *entirely on* the frozen
:mod:`engines.diffusion` (OED is its already-frozen variable-``D(t)`` callable; segregation a
``Neumann(flux(t))`` BC) — so unlike Phase 2/3/4 there *is* a spine underneath, and these tests
validate the **coupling instantiation**, not the solver machinery (sealed in
``engines/diffusion/tests``):

* **Analytical limit (tight).** (a) the **unified degenerate seam** — zero oxidation rate collapses
  both effects to plain :func:`diffusion_dopant.drive_in`, bit-for-bit; (b) **OED ≡ the engine's
  ``τ = ∫D dt`` time substitution** — a warm-started analytic Gaussian under OED reproduces the
  analytic Gaussian at the effective age (OED's *real* analytic leg, not just degenerate recovery).
* **Conservation — genuine for OED-alone, an accounting identity for the coupled case.** OED-alone-
  sealed conserves dose to machine precision (a real check). The coupled ``Si_dose + oxide_uptake``
  identity also closes to machine precision — but ``oxide_uptake`` is *defined* from the same flux
  bookkeeping, so it closes for any flux (catches a leak, not a magnitude). The **``m → ∞`` inert-
  oxide diagnostic** exposes what the identity hides: a spurious silicon-dose *gain* — the named
  swept-sliver double-count (the moving-interface ``0.44·R`` term applied on a non-moving grid).
* **Benchmark (loose / cited-form).** The cited ``f_I`` (B 0.30, P 0.38, Sb 0.015) reproduces
  **enhanced (B, P) vs un-enhanced (Sb)**; the cited ``m`` (B 0.3, P 10) sets **depletion (B) vs
  pile-up (P)** — *directions*, asserted; the phosphorus pile-up *magnitude* is ~2× inflated by the
  swept-sliver edge (boron, oxide-uptake-dominated, is the robust device-relevant case). The OED
  *amplitude* is calibrated (flagged); the cited constants are pinned exactly (citation-fidelity).

The validated-vs-calibrated split (the standing discipline): the tight legs (degenerate, effective-
``∫D dt``, conservation) exercise *machinery* and hold for **any** OED amplitude; the loose legs lean
on the pinned cited constants. So the calibrated amplitude never wounds a tight leg.
"""
import numpy as np
import pytest

from engines.diffusion import uniform_grid

from projects.chip import coupling as cp
from projects.chip import diffusion_dopant as dd

# A standard depth grid + a starting profile shared across the cases (a boron predep seed).
GRID = uniform_grid(3.0 * dd.CM_PER_UM, 600)


def _boron_seed():
    return dd.predeposit(GRID, "B", 950.0, 15.0 * 60.0).N


# --------------------------------------------------------------------------- #
# Analytical limit (tight) — the unified degenerate seam + the OED time-substitution
# --------------------------------------------------------------------------- #
def test_zero_oxidation_collapses_to_plain_drive_in_bit_for_bit():
    # The unified degenerate anchor: with no oxidation there are no injected interstitials (OED → 1)
    # and no moving interface (segregation flux → 0), so the coupled solve IS a sealed inert drive-in.
    # The flag-off path (oed=False, segregation=False) is exactly that — assert it equals
    # diffusion_dopant.drive_in to the last bit (the same defaults-recover-v1 seam as Massoud K=0).
    seed = _boron_seed()
    di = dd.drive_in(GRID, seed, "B", 1000.0, 20.0 * 60.0, n_steps=600)
    co = cp.oxidize_couple(GRID, seed, "B", "dry", 1000.0, 20.0,
                           oed=False, segregation=False, n_steps=600)
    assert np.max(np.abs(co.N - di.N)) == 0.0


def test_enhancement_and_flux_vanish_at_zero_oxidation_rate():
    # The unit-level seam (the reason the above holds physically): at dx_ox/dt = 0 the OED factor is
    # exactly 1 for EVERY dopant (1 + f_I·0), and the segregation flux is exactly 0 — for any m.
    for dop in ("B", "P", "Sb"):
        assert cp.oed_enhancement_factor(dop, 0.0) == 1.0
    assert cp.segregation_flux(1.0e20, 0.0, 0.3) == 0.0
    assert cp.segregation_flux(1.0e20, 0.0, 10.0) == 0.0


def test_oed_is_the_engine_effective_integral_D_dt():
    # OED's REAL analytic leg (not mere degenerate recovery): a sealed-surface OED solve depends on
    # the history only through ∫D_eff dt (the frozen variable-D τ-substitution, test_variable_d). So
    # a warm-started analytic Gaussian propagated under OED equals the analytic Gaussian at the
    # effective age a0 + ∫D_eff dt. This exercises the enhancement *through the engine*, end to end.
    D_inert = dd.diffusivity("B", 1000.0)
    a0 = D_inert * 600.0                         # warm-start "age" a0 = D·t (some pre-diffusion)
    dose = 5.0e15
    N0 = dd.analytic_drivein_gaussian(GRID.centers, a0 / D_inert, D_inert, dose)
    co = cp.oxidize_couple(GRID, N0, "B", "dry", 1000.0, 20.0,
                           oed=True, segregation=False, n_steps=600)
    age = a0 + co.effective_Dt
    N_analytic = dose / np.sqrt(np.pi * age) * np.exp(-GRID.centers**2 / (4.0 * age))
    rel = np.max(np.abs(co.N - N_analytic)) / N_analytic[0]
    assert rel < 2.0e-3                           # discretization-limited (the warm-start truncation)
    # And OED genuinely enhanced: the effective age exceeds the inert age D_inert·t.
    assert co.effective_Dt > 1.5 * D_inert * co.t_seconds


# --------------------------------------------------------------------------- #
# Conservation (tight) — attached to its scenario
# --------------------------------------------------------------------------- #
def test_oed_alone_sealed_surface_conserves_dose_machine_exact():
    # OED changes D, not the amount: with the surface sealed (segregation off) the dose ∫N dx is
    # conserved to machine precision EVEN with a time-varying D — the engine's structural no-flux
    # guarantee, here exercised on the variable-D array. (The claim attached to THIS scenario.)
    seed = _boron_seed()
    co = cp.oxidize_couple(GRID, seed, "B", "dry", 1000.0, 20.0,
                           oed=True, segregation=False, n_steps=600)
    assert co.si_dose == pytest.approx(co.si_dose_initial, rel=1e-10)
    assert co.oxide_uptake == 0.0                 # sealed surface → no reservoir transfer


def test_coupled_silicon_plus_oxide_accounting_closes():
    # The Si_dose + oxide_uptake = si_dose_initial identity closes to machine precision — but this is
    # an ACCOUNTING identity (oxide_uptake is DEFINED as −Σ dt·flux(left), the same bookkeeping the
    # engine guarantees), so it closes for ANY flux. It catches an accounting leak; it does NOT
    # validate the segregation magnitude (the swept-sliver edge below means the magnitude is NOT
    # exact). Asserted as such, not dressed up as physical conservation.
    for dop in ("B", "P"):
        seed = dd.predeposit(GRID, dop, 950.0, 15.0 * 60.0).N
        co = cp.oxidize_couple(GRID, seed, dop, "dry", 1000.0, 20.0,
                               oed=True, segregation=True, n_steps=600)
        assert co.conservation_residual / co.si_dose_initial < 1e-12
        assert co.oxide_uptake != 0.0             # the surface is genuinely exchanging dopant


def test_inert_oxide_reveals_swept_sliver_artifact():
    # The decisive diagnostic for the named scope edge. An INERT oxide (m → ∞) can only snowplow —
    # it accepts NO dopant — so the silicon dopant MUST be conserved. The fixed-grid model instead
    # spuriously GAINS dopant: the segregation flux's 0.44·R term ("freed by consumed silicon") is
    # the interface recession, but the grid keeps the swept region AND re-injects its dopant, so the
    # sliver is double-counted. Pin the artifact bound so the scope edge is a test, not just prose.
    seed = dd.predeposit(GRID, "P", 950.0, 15.0 * 60.0).N
    co = cp.oxidize_couple(GRID, seed, "P", "dry", 1000.0, 30.0,
                           oed=True, segregation=True, segregation_m=1.0e9, n_steps=600)
    spurious_gain = (co.si_dose - co.si_dose_initial) / co.si_dose_initial
    # An inert oxide should conserve (≈0); the model gains a few-to-~15% of the dose — the named
    # swept-sliver artifact. Assert it is POSITIVE (the wrong sign — gain, not the slight loss a
    # consistent moving boundary gives) and bounded (a regression guard on the edge's size).
    assert 0.02 < spurious_gain < 0.20
    # The gain is ≈ the swept-sliver dose N_surf·0.44·x_ox (m-independent — the m-dependence lives in
    # the oxide-uptake term, which → 0 here): it equals the m=10 case's gain to within the evolving
    # surface value. This is WHY phosphorus pile-up (×~1.17) is ~2× inflated; boron is robust.
    co10 = cp.oxidize_couple(GRID, seed, "P", "dry", 1000.0, 30.0,
                             oed=True, segregation=True, n_steps=600)
    assert (co10.si_dose - co10.si_dose_initial) > 0.0      # phosphorus dose spuriously rises too


def test_conservation_is_exact_at_any_step_count():
    # Conservation is machine-exact at ANY n_steps (the engine applies the handed flux exactly);
    # n_steps buys fidelity, never closure. Pin it at a coarse step count too.
    seed = _boron_seed()
    co = cp.oxidize_couple(GRID, seed, "B", "dry", 1000.0, 20.0,
                           oed=True, segregation=True, n_steps=40)
    assert co.conservation_residual / co.si_dose_initial < 1e-12


# --------------------------------------------------------------------------- #
# Benchmark (loose / cited-form) — the f_I and m directions, constants pinned
# --------------------------------------------------------------------------- #
def test_oed_enhances_boron_and_phosphorus_ordered_by_interstitialcy():
    # Both interstitialcy diffusers are enhanced (factor > 1); P (f_I 0.38) more than B (f_I 0.30) at
    # the same oxidation rate — the cited ordering. (Direction + ordering asserted, NOT the magnitude.)
    R = cp.oxidation_rate_um_per_hr("dry", 1000.0)(60.0)
    fB = cp.oed_enhancement_factor("B", R)
    fP = cp.oed_enhancement_factor("P", R)
    assert fB > 1.0 and fP > 1.0
    assert fP > fB


def test_sb_essentially_unenhanced_ord_retardation_is_a_named_scope_edge():
    # Sb (f_I 0.015, near-pure vacancy) → factor ≈ 1: the form correctly does NOT enhance antimony.
    # It also does NOT claim retardation (factor < 1) — true ORD needs the unmodeled vacancy-
    # undersaturation term, the named scope edge. So Sb sits within a few % of 1, far below B/P.
    R = cp.oxidation_rate_um_per_hr("dry", 1000.0)(60.0)
    fSb = cp.oed_enhancement_factor("Sb", R)
    assert 1.0 <= fSb < 1.10                       # un-enhanced, not a retardation number
    assert fSb < cp.oed_enhancement_factor("B", R)  # far below the interstitialcy diffusers


def test_faster_oxidation_gives_stronger_oed():
    # The rate dependence: a faster oxidation (higher T, or wet vs dry) injects more interstitials →
    # bigger supersaturation → bigger enhancement. The half-power law's monotonicity.
    slow = cp.oxidation_rate_um_per_hr("dry", 1000.0)(60.0)
    fast = cp.oxidation_rate_um_per_hr("wet", 1100.0)(60.0)
    assert fast > slow
    assert cp.oed_enhancement_factor("B", fast) > cp.oed_enhancement_factor("B", slow)


def test_boron_depletes_phosphorus_piles_up():
    # The segregation signatures (the cited m sets the sign). Compare the surface concentration with
    # vs without segregation (OED on in both, so the only difference is the surface BC):
    #   boron (m 0.3 < 1): oxide takes boron → surface DEPLETES → N_surf falls, oxide_uptake > 0;
    #   phosphorus (m 10 > 1): oxide rejects → surface PILES UP → N_surf rises, oxide_uptake < 0.
    seed_B = dd.predeposit(GRID, "B", 950.0, 15.0 * 60.0).N
    base_B = cp.oxidize_couple(GRID, seed_B, "B", "dry", 1000.0, 20.0, oed=True, segregation=False)
    seg_B = cp.oxidize_couple(GRID, seed_B, "B", "dry", 1000.0, 20.0, oed=True, segregation=True)
    assert seg_B.surface_concentration < base_B.surface_concentration
    assert seg_B.oxide_uptake > 0.0

    seed_P = dd.predeposit(GRID, "P", 950.0, 15.0 * 60.0).N
    base_P = cp.oxidize_couple(GRID, seed_P, "P", "dry", 1000.0, 20.0, oed=True, segregation=False)
    seg_P = cp.oxidize_couple(GRID, seed_P, "P", "dry", 1000.0, 20.0, oed=True, segregation=True)
    assert seg_P.surface_concentration > base_P.surface_concentration
    assert seg_P.oxide_uptake < 0.0


def test_segregation_flux_sign_follows_the_mass_balance():
    # The flux J = N_surf·(0.44 − 1/m)·rate: sign is set by (0.44 − 1/m). m<1 (boron) → negative
    # (out of silicon); m>1 (phosphorus) → positive (into silicon). The 0.44 is oxidation's Si/SiO₂
    # ratio (no free transport coefficient — the coefficient is the cited m and the cited 0.44).
    N_surf, rate = 1.0e20, 1.0e-7
    jB = cp.segregation_flux(N_surf, rate, cp.SEGREGATION_COEFFICIENT["B"])
    jP = cp.segregation_flux(N_surf, rate, cp.SEGREGATION_COEFFICIENT["P"])
    assert jB < 0.0 < jP
    assert jB == pytest.approx(N_surf * (0.44 - 1.0 / 0.3) * rate)
    assert jP == pytest.approx(N_surf * (0.44 - 1.0 / 10.0) * rate)


def test_cited_constants_are_pinned():
    # The citation-fidelity guard (the test_oxidation pattern — these are load-bearing, so pin them
    # like the Deal–Grove table). f_I from the dual I/V quantification paper; m = solubility_Si/
    # solubility_SiO₂ from Hollauer §4.1 Table 4.1 (the SAME dissertation as the Massoud pin). The
    # m DEFINITION (Si/SiO₂, not the inverse) is the load-bearing call — inverting flips depletion↔pile-up.
    assert cp.FRACTIONAL_INTERSTITIALCY["B"] == 0.30
    assert cp.FRACTIONAL_INTERSTITIALCY["P"] == 0.38
    assert cp.FRACTIONAL_INTERSTITIALCY["Sb"] == 0.015
    assert cp.FRACTIONAL_INTERSTITIALCY["As"] == 0.35      # cited (mixed I/V) — doc only, not a demo dopant
    assert cp.SEGREGATION_COEFFICIENT["B"] == 0.3          # m < 1 → boron depletion
    assert cp.SEGREGATION_COEFFICIENT["P"] == 10.0         # m > 1 → phosphorus pile-up
    assert cp.OED_RATE_EXPONENT == 0.5                     # the cited half-power law
    # The amplitude is CALIBRATED (flagged) — pin it so the demo numbers don't drift silently, but it
    # is the knob the validated legs are independent of.
    assert cp.OED_SUPERSATURATION_AT_REF == 5.0


def test_massoud_thin_dry_path_drives_the_coupling():
    # The coupling accepts the v1.1 Massoud thin-dry rate (dry, 800–1000 °C) — the realistic gate-
    # oxide regime. It runs and conserves; the Massoud rate is higher than plain Deal–Grove early
    # (the thin-dry burst), so it drives a stronger early OED.
    seed = _boron_seed()
    co = cp.oxidize_couple(GRID, seed, "B", "dry", 1000.0, 20.0,
                           oed=True, segregation=True, model="massoud", n_steps=600)
    assert co.conservation_residual / co.si_dose_initial < 1e-12
    r_massoud = cp.oxidation_rate_um_per_hr("dry", 1000.0, model="massoud")(60.0)
    r_dealgrove = cp.oxidation_rate_um_per_hr("dry", 1000.0, model="deal-grove")(60.0)
    assert r_massoud > r_dealgrove                # the thin-dry burst → faster early oxidation


def test_unknown_dopant_segregation_refuses():
    # No cited segregation coefficient for Sb → refuse rather than invent one (refuse-don't-extrapolate,
    # the Massoud-range discipline). OED is fine for Sb (f_I cited); segregation is not.
    seed = dd.predeposit(GRID, "Sb", 950.0, 15.0 * 60.0).N
    with pytest.raises(ValueError, match="segregation coefficient"):
        cp.oxidize_couple(GRID, seed, "Sb", "dry", 1000.0, 20.0, oed=True, segregation=True)
    # but OED-only Sb runs (and is ~un-enhanced):
    co = cp.oxidize_couple(GRID, seed, "Sb", "dry", 1000.0, 20.0, oed=True, segregation=False)
    assert co.si_dose == pytest.approx(co.si_dose_initial, rel=1e-10)
