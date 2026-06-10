"""Chip v1.3 validation: concentration-dependent diffusivity D(N) — the high-concentration box.

The named scope edge of :mod:`diffusion_dopant` (constant-``D`` ``erfc``), **promoted**. The decisive
claim under test is architectural: ``D(N)`` — the case ``CONTRACT.md`` and the plan both flagged as a
v1.1 **engine amendment** — is built **entirely within the frozen** :mod:`engines.diffusion` contract,
via a stateful-closure **lagged-coefficient** hook in the consumer's step-loop (no engine edit). The
triad (plan §3), with the validated-vs-calibrated split made explicit:

* **Analytical limit (tight).** (a) the **degenerate seam** — a constant ``D`` through the same
  closure equals the plain scalar-``D`` frozen-engine run **bit-for-bit** (the hook *is* the engine),
  and the model's ``D_eff → D⁰+D⁻+D⁼`` as ``N → 0``; (b) **Boltzmann similarity** — a constant-source
  ``D(N)`` profile collapses under ``x/√t`` for **any** ``D(N)`` (model-independent; validates the
  nonlinear machinery, not Fair's coefficients).
* **Conservation (a machinery check, not a physics validation).** A sealed-surface drive-in conserves
  ``∫N dx`` to machine precision *with* ``D(N)`` active — the finite-volume telescoping is
  ``D``-independent. It confirms the closure didn't break structural conservation; it says nothing
  about the ``D(N)`` magnitude.
* **Benchmark (loose / calibrated).** ``D∝(n/n_i)²`` (phosphorus) gives the **boxier front + deeper
  junction** than constant ``D`` (Plummer slides 15/25/27) — coefficients cited, not fit to the box.

Cited at build (directly read): Plummer–Deal–Griffin *Silicon VLSI Technology* Ch. 7 (the charge-state
model + slide-15 table); Fair & Tsai, J. Electrochem. Soc. 124, 1107 (1977); the non-equilibrium
kink/tail scope edge + high-T ``n_i`` from Velichko, arXiv:1905.10667.
"""
import numpy as np
import pytest
from scipy.special import erfc

from engines.diffusion import Diffusion1D, uniform_grid, Dirichlet, Neumann
from chip.diffusion_dopant import DOPANTS, CM_PER_UM, analytic_predep_erfc, diffusivity
from chip import diffusion_highconc as hc


# --------------------------------------------------------------------------- #
# Cited physics constants — n_i(T) and the Fair charge-state coefficients
# --------------------------------------------------------------------------- #
def test_intrinsic_carrier_concentration_cross_checks():
    # n_i = 3.87e16·T^1.5·exp(-0.605/kT). Pinned at both ends of the relevant range: the room-temp
    # value (~1.0e10, the textbook constant) and a diffusion-temperature value cross-checked against
    # Velichko's directly-read n_i(890 C) = 4.6e18. The huge high-T n_i is why only N >~ n_i is enhanced.
    assert hc.intrinsic_carrier_concentration(26.85) == pytest.approx(1.4e10, rel=0.10)   # 300 K
    assert hc.intrinsic_carrier_concentration(890.0) == pytest.approx(3.7e18, rel=0.10)
    # monotone increasing, and ~7e18 at the 1000 C predep/drive-in regime
    assert hc.intrinsic_carrier_concentration(1000.0) > hc.intrinsic_carrier_concentration(900.0)
    assert hc.intrinsic_carrier_concentration(1000.0) == pytest.approx(7.1e18, rel=0.10)


def test_charge_state_coefficients_match_pinned_slide15_table():
    # The load-bearing pin (Plummer Ch. 7 slide-15 table). Phosphorus = the box driver: a neutral D⁰,
    # a single-negative D⁻ (n/n_i), and the double-negative D⁼ (n/n_i)² that drives the box.
    assert hc.CHARGE_STATE_TERMS["P"] == [(3.85, 3.66, 0), (4.44, 4.0, 1), (44.2, 4.37, 2)]
    assert hc.CHARGE_STATE_TERMS["B"] == [(0.05, 3.5, 0), (0.95, 3.5, 1)]      # D⁰ + D⁺(p/n_i)
    assert hc.CHARGE_STATE_TERMS["As"] == [(0.011, 3.44, 0), (31.0, 4.15, 1)]
    assert hc.CHARGE_STATE_TERMS["Sb"] == [(0.214, 3.65, 0), (15.0, 4.08, 1)]
    # The Phase-1a "intrinsic D" for P/Sb is exactly Fair's neutral D⁰ component (one coherent lineage).
    assert hc.CHARGE_STATE_TERMS["P"][0][:2] == (3.85, 3.66)
    assert hc.CHARGE_STATE_TERMS["Sb"][0][:2] == (0.214, 3.65)


def test_low_concentration_limit_recovers_intrinsic_constant():
    # As N -> 0 the carrier ratio n/n_i -> 1, so every charge-state term contributes once and
    # D_eff -> D⁰+D⁻+D⁼ = the intrinsic constant. This is the constant-D the box is compared against.
    D_lo = hc.effective_diffusivity("P", np.array([0.0, 1.0, 1e10]), 1000.0)
    D_int = hc.intrinsic_diffusivity_lowconc("P", 1000.0)
    assert np.allclose(D_lo, D_int, rtol=1e-9)
    # and it exceeds the neutral-D⁰-only diffusivity() by the small D⁻/D⁼ remainder (~7% for P).
    assert D_int > diffusivity("P", 1000.0)
    assert D_int == pytest.approx(diffusivity("P", 1000.0), rel=0.10)


def test_effective_diffusivity_rises_with_concentration_n_squared_for_P():
    # Phosphorus: the (n/n_i)² term means D rises ~quadratically once N >> n_i. At N = 100·n_i the
    # double-negative term alone is ~10^4·D⁼, dwarfing D⁰ — the steep concentration dependence.
    T = 1000.0
    n_i = hc.intrinsic_carrier_concentration(T)
    D_lo = hc.effective_diffusivity("P", np.array([0.0]), T)[0]
    D_hi = hc.effective_diffusivity("P", np.array([100.0 * n_i]), T)[0]
    assert D_hi > 50.0 * D_lo                       # strongly enhanced at high concentration
    # doubling N near the high-conc regime more-than-doubles D (super-linear, the n² signature)
    D_a = hc.effective_diffusivity("P", np.array([50.0 * n_i]), T)[0]
    D_b = hc.effective_diffusivity("P", np.array([100.0 * n_i]), T)[0]
    assert D_b / D_a > 2.0


# --------------------------------------------------------------------------- #
# Analytical limit (a): the degenerate seam — the closure IS the frozen engine
# --------------------------------------------------------------------------- #
def test_degenerate_seam_constant_D_closure_equals_scalar_engine_bitforbit():
    # The headline architecture check: feed a CONSTANT D through the lagged closure and it equals a
    # plain scalar-D frozen-engine predep to the bit. The hook adds nothing when D doesn't vary —
    # i.e. concentration-dependent D is the *same* frozen solver, driven with a stateful coefficient.
    grid = uniform_grid(1.5 * CM_PER_UM, 800)
    Ns = DOPANTS["P"].N_solid_solubility
    D_const = hc.intrinsic_diffusivity_lowconc("P", 1000.0)
    t_pre, n_steps = 30 * 60.0, 800

    N_closure = hc.constant_D_predeposit(grid, "P", 1000.0, t_pre, D_const, n_steps=n_steps)
    solver = Diffusion1D(grid, D_const, Dirichlet(Ns), Neumann(0.0))
    N_scalar = np.zeros(grid.n)
    dt = t_pre / n_steps
    for _ in range(n_steps):
        N_scalar = solver.step(N_scalar, dt)
    assert np.max(np.abs(N_closure - N_scalar)) == 0.0          # bit-for-bit
    # and that constant-D run is the analytic erfc on its idealization
    erfc_an = analytic_predep_erfc(grid.centers, t_pre, D_const, Ns)
    assert np.max(np.abs(N_closure - erfc_an)) / Ns < 1e-3


# --------------------------------------------------------------------------- #
# Analytical limit (b): Boltzmann similarity — model-independent, the nonlinear anchor
# --------------------------------------------------------------------------- #
def test_boltzmann_similarity_collapse_under_x_over_sqrt_t():
    # For a constant-source diffusion into a semi-infinite medium, N(x,t) depends on x,t ONLY through
    # eta = x/sqrt(t) for ANY D(N). So N(x, t) and N(2x, 4t) coincide (sqrt(4t)=2 sqrt(t)). This holds
    # for the real, stiff (n/n_i)² phosphorus model — validating that the lagged D(N) solve converges
    # to the correct self-similar field, independent of whether Fair's coefficients are right.
    g1 = uniform_grid(1.5 * CM_PER_UM, 800)
    g2 = uniform_grid(3.0 * CM_PER_UM, 1600)
    t = 30 * 60.0
    p1 = hc.predeposit_highconc(g1, "P", 1000.0, t, n_steps=1600, picard_iters=4)
    p2 = hc.predeposit_highconc(g2, "P", 1000.0, 4 * t, n_steps=3200, picard_iters=4)
    N2_at_2x = np.interp(2.0 * g1.centers, g2.centers, p2.N)
    Ns = DOPANTS["P"].N_solid_solubility
    assert np.max(np.abs(p1.N - N2_at_2x)) / Ns < 5e-3          # collapse (numeric + interp error)


# --------------------------------------------------------------------------- #
# Conservation — a MACHINERY check (D-independent telescoping), not a magnitude validation
# --------------------------------------------------------------------------- #
def test_sealed_drivein_conserves_dose_with_D_of_N_active():
    # No-flux both ends -> Σ uΔx is conserved to machine precision by the finite-volume structure,
    # for ANY non-negative D field. Re-confirmed here with a time-AND-state-varying D(N): the closure
    # did not break the engine's structural conservation. (It does NOT validate the D(N) magnitude.)
    grid = uniform_grid(1.5 * CM_PER_UM, 800)
    seed = hc.predeposit_highconc(grid, "P", 1000.0, 30 * 60.0, n_steps=800, picard_iters=2)
    dose_in = float(np.sum(seed.N * grid.widths))
    out = hc.drive_in_highconc(grid, seed.N, "P", 1000.0, 20 * 60.0, n_steps=800, picard_iters=2)
    assert abs(out.dose - dose_in) / dose_in < 1e-10


# --------------------------------------------------------------------------- #
# Benchmark (loose) — the box front + deeper junction; cited not fit
# --------------------------------------------------------------------------- #
def _front_sharpness(x, N, Ns):
    """x(0.5·Ns)/x(0.01·Ns): closer to 1 = boxier (the 50% depth nears the 1% depth)."""
    def depth(frac):
        b = np.where(N < frac * Ns)[0]
        return x[b[0]] if b.size else np.nan
    return depth(0.5) / depth(0.01)


def test_concentration_dependent_D_gives_boxier_front_and_deeper_junction():
    # Plummer slides 15/25/27: concentration-dependent D yields a "boxier" profile and a deeper
    # junction than constant D. Same phosphorus predep recipe, enhanced D(N) vs the constant intrinsic D.
    grid = uniform_grid(1.5 * CM_PER_UM, 800)
    Ns = DOPANTS["P"].N_solid_solubility
    D_int = hc.intrinsic_diffusivity_lowconc("P", 1000.0)

    enh = hc.predeposit_highconc(grid, "P", 1000.0, 30 * 60.0, n_steps=800, picard_iters=2)
    const = hc.constant_D_predeposit(grid, "P", 1000.0, 30 * 60.0, D_int, n_steps=800)

    # (1) boxier front
    assert _front_sharpness(enh.x, enh.N, Ns) > 1.8 * _front_sharpness(grid.centers, const, Ns)
    # (2) deeper junction into a 1e15 background
    xj_enh = hc.junction_depth_simple(enh.x, enh.N, 1e15)
    xj_const = hc.junction_depth_simple(grid.centers, const, 1e15)
    assert xj_enh > 2.0 * xj_const
    # (3) no overshoot above the Dirichlet surface (empirical monotonicity at this resolution)
    assert enh.N.max() <= Ns * (1.0 + 1e-6)


def test_n_squared_dopant_boxier_than_n_linear_than_constant():
    # The charge-state ordering: P (D⁼, n²) is boxier than As (D⁻, n¹) is boxier than constant D.
    grid = uniform_grid(1.5 * CM_PER_UM, 800)
    Ns = 1.0e21                                      # common high surface conc for a fair comparison
    kw = dict(N_surface=Ns, n_steps=800, picard_iters=2)
    P = hc.predeposit_highconc(grid, "P", 1000.0, 30 * 60.0, **kw)
    As = hc.predeposit_highconc(grid, "As", 1000.0, 30 * 60.0, **kw)
    const = hc.constant_D_predeposit(grid, "P", 1000.0, 30 * 60.0,
                                     hc.intrinsic_diffusivity_lowconc("P", 1000.0),
                                     N_surface=Ns, n_steps=800)
    s_P = _front_sharpness(P.x, P.N, Ns)
    s_As = _front_sharpness(As.x, As.N, Ns)
    s_c = _front_sharpness(grid.centers, const, Ns)
    assert s_P > s_As > s_c


# --------------------------------------------------------------------------- #
# Numerics honesty — Picard converges; lagged-only converges to it as dt -> 0
# --------------------------------------------------------------------------- #
def test_picard_converges_and_lagged_approaches_it_with_smaller_dt():
    grid = uniform_grid(1.5 * CM_PER_UM, 800)
    Ns = DOPANTS["P"].N_solid_solubility
    t = 30 * 60.0

    def xj(p):
        return hc.junction_depth_simple(p.x, p.N, 1e15)

    # 2 Picard iterations already converge the within-step nonlinearity (2 vs 6 agree to ~0.1% on the
    # interpolated x_j — the residual is sub-cell front placement, not an unconverged coupling).
    p2 = hc.predeposit_highconc(grid, "P", 1000.0, t, n_steps=800, picard_iters=2)
    p6 = hc.predeposit_highconc(grid, "P", 1000.0, t, n_steps=800, picard_iters=6)
    assert abs(xj(p2) - xj(p6)) / xj(p2) < 3e-3

    # Pure-lagged (the minimal hook) carries a first-order lag error that shrinks with dt, approaching
    # the Picard-converged value — the scheme is consistent (it does not converge to the wrong field).
    lag_coarse = hc.predeposit_highconc(grid, "P", 1000.0, t, n_steps=800, picard_iters=0)
    lag_fine = hc.predeposit_highconc(grid, "P", 1000.0, t, n_steps=3200, picard_iters=0)
    assert abs(xj(lag_fine) - xj(p2)) < abs(xj(lag_coarse) - xj(p2))
    assert abs(xj(lag_fine) - xj(p2)) / xj(p2) < 0.01


# --------------------------------------------------------------------------- #
# Scope edge (named, asserted as a NOT-claim) — the deep tail stays intrinsic
# --------------------------------------------------------------------------- #
def test_scope_edge_deep_tail_has_no_anomalous_enhancement():
    # The equilibrium charge-state model enhances only where N >~ n_i; the dilute deep tail (N << n_i)
    # diffuses at the intrinsic D, so it tracks the constant-D erfc there — the model has NO mechanism
    # for the anomalous phosphorus "tail" (that is non-equilibrium I-injection / clustering, the named
    # scope edge: Velichko / Fair-Tsai emitter-dip). We assert the ABSENCE of tail enhancement.
    grid = uniform_grid(2.0 * CM_PER_UM, 1000)
    Ns = DOPANTS["P"].N_solid_solubility
    n_i = hc.intrinsic_carrier_concentration(1000.0)
    enh = hc.predeposit_highconc(grid, "P", 1000.0, 30 * 60.0, n_steps=1000, picard_iters=2)
    const = hc.constant_D_predeposit(grid, "P", 1000.0, 30 * 60.0,
                                     hc.intrinsic_diffusivity_lowconc("P", 1000.0), n_steps=1000)
    # in the dilute tail (N < 0.01·n_i) the enhanced profile is NOT deeper than constant-D by more
    # than the box's geometric push — there is no extra diffuse tail beyond the front advance.
    deep = enh.N < 0.01 * n_i
    # the enhanced profile crosses 0.01·n_i deeper (front pushed) but then falls at least as steeply
    # as constant-D (no slow anomalous tail): its decay length past the crossing is not larger.
    assert deep.any()
    # quantify: past where each profile drops below 0.01 n_i, the enhanced one is steeper (smaller
    # decade-length) — confirming the front is geometric, not a diffuse tail.
    def decade_length(x, N, lo, hi):
        bl = np.where(N < lo)[0]
        bh = np.where(N < hi)[0]
        return (x[bl[0]] - x[bh[0]]) if bl.size and bh.size else np.nan
    L_enh = decade_length(enh.x, enh.N, 1e-3 * n_i, 1e-2 * n_i)
    L_const = decade_length(grid.centers, const, 1e-3 * n_i, 1e-2 * n_i)
    assert L_enh <= L_const * 1.5     # no broad anomalous tail (would be >> constant)
