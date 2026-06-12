"""Validation triad for the 2-D MOSFET cross-section (Chip v1.11 — :mod:`chip.device_2d`).

A **validation deepening**: the module wires the v1.8 2-D engine into the Phase-4 device read and
its job is to *confirm*, independently, the textbook effective-channel relation ``L_eff = L_drawn −
2·ΔL`` and the punchthrough limit at ``L_drawn ≈ 2·ΔL``. The legs, billed honestly:

* **Seam (by-construction exact).** ``lateral=False`` (no lateral correction) recovers the plain
  Phase-4 device **bit-for-bit** — the σ=0/z=0/K=0 degenerate-seam pattern.
* **The independent cross-check (the real anchor).** The two-window half-cell solve (``L_eff_true``,
  read junction-to-junction) agrees with the isolated-edge subtraction ``L_drawn − 2·ΔL`` to ~grid
  precision **across the open range, persisting as the gate narrows toward the knee** — not merely at
  a wide gate (where it agrees almost by construction). Different BC topology (two windows + a
  symmetry plane vs one semi-infinite edge), so it would fail on a config/topology bug or if superposition
  broke. (The front-interaction effect that would split the two near the knee is below the resolved
  scale here — checked, not asserted.)
* **Punchthrough.** The two-window solve floors hard at ``L_eff = 0`` when the S/D fronts merge, and
  the subtraction **agrees on the threshold** ``≈ 2·ΔL``; ``mosfet_cross_section`` refuses there.
* **Boundary guards (by-construction — billed as guards, not anchors).** ``V_t`` never depends on the
  channel length (no short-channel rolloff / DIBL — the named tar pit stays out), and the only place
  ``L`` couples to a device number is the purely geometric drive current ``I_Dsat ∝ W/L``.

The 2-D solver machinery itself is the engine's (``engines/diffusion/tests/test_diffusion2d.py``);
the single-edge ΔL inherits v1.8's tight erfc-window-column anchor (``test_diffusion_2d.py``).
"""
import math

import numpy as np
import pytest

from chip import device_2d as d2
from chip import device

# A coherent ~0.5 µm-node n-MOSFET (long-channel V_t honestly valid): p-channel 1e17, 12 nm gate
# oxide, n⁺-P S/D at 1000 °C / 6 min → x_j ≈ 0.12 µm, ΔL ≈ 0.10 µm. Shared across the module.
# SD = the S/D-diffusion knobs (what effective_channel_um needs); DEV adds the gate oxide (the device).
SD = dict(channel_N_A=1.0e17, sd_dopant="P", sd_T_celsius=1000.0, sd_t_min=6.0)
T_OX_UM = 0.012
DEV = {**SD, "t_ox_um": T_OX_UM}
GATE, WIDTH_UM, OVERDRIVE_V = "n+poly", 10.0, 1.0


@pytest.fixture(scope="module")
def headline():
    """The representative device: a 0.5 µm drawn gate."""
    return d2.mosfet_cross_section(L_drawn_um=0.5, gate=GATE, width_um=WIDTH_UM,
                                   overdrive_V=OVERDRIVE_V, **DEV)


@pytest.fixture(scope="module")
def sweep(headline):
    """``L_eff_true`` (two-window) vs the subtraction across the open range and into punchthrough.

    Computed once with the cheap :func:`effective_channel_um` (two-window solve only); the subtraction
    uses the single ΔL from the headline (same S/D process → ΔL is ``L_drawn``-independent), so both
    sides share the grid — any residual gap is physics, not resolution.
    """
    two_dL = 2.0 * headline.delta_L_um
    rows = []
    for L in (0.70, 0.60, 0.50, 0.40, 0.30, 0.25, 0.20, 0.18):
        true = d2.effective_channel_um(L_drawn_um=L, **SD)
        rows.append((L, true, L - two_dL))                 # (L_drawn, L_eff_true, L_eff_approx)
    return {"two_delta_L": two_dL, "rows": rows}


# --------------------------------------------------------------------------- #
# Seam — lateral=False recovers Phase 4 bit-for-bit
# --------------------------------------------------------------------------- #
def test_seam_no_lateral_is_phase4_bit_for_bit():
    m = d2.mosfet_cross_section(L_drawn_um=0.5, gate=GATE, width_um=WIDTH_UM,
                                overdrive_V=OVERDRIVE_V, lateral=False, **DEV)
    ref = device.threshold_voltage(SD["channel_N_A"], T_OX_UM, GATE, channel_length_um=0.5)
    assert m.mos == ref                                    # the whole MOSDevice, field-for-field
    assert m.L_eff_true_um == 0.5 and m.delta_L_um == 0.0
    assert m.i_dsat == device.saturation_current(ref, ref.V_t + OVERDRIVE_V, WIDTH_UM)
    assert m.N is None                                     # no 2-D solve was run


# --------------------------------------------------------------------------- #
# The independent cross-check — two-window ≡ subtraction, down toward the knee
# --------------------------------------------------------------------------- #
def test_two_window_confirms_subtraction_toward_the_knee(sweep):
    # The non-trivial content: agreement persists as the gate narrows toward punchthrough (~2ΔL),
    # not just at a wide gate. ~2 grid cells of tolerance so it is not flaky. Restricted to the open
    # rows (L_eff_true well above one cell); the punchthrough rows are checked separately.
    open_rows = [(L, true, approx) for (L, true, approx) in sweep["rows"] if true > 0.03]
    assert open_rows[-1][0] <= 0.25                        # we really do reach toward the knee (~2ΔL)
    for L, true, approx in open_rows:
        assert abs(true - approx) < 0.012, (L, true, approx)   # agree to ~grid precision


def test_two_window_agrees_with_subtraction_is_a_real_crosscheck(headline):
    # Sanity that the agreement is meaningful (not a degenerate 0≈0): the headline device shortens
    # by a healthy amount, and the two independent routes land on the same L_eff.
    assert headline.L_eff_true_um < headline.L_drawn_um              # a real shortening
    assert abs(headline.L_eff_true_um - headline.L_eff_approx_um) < 0.012


# --------------------------------------------------------------------------- #
# Punchthrough — the hard L_eff=0 floor, the subtraction agreeing on the threshold
# --------------------------------------------------------------------------- #
def test_punchthrough_floor_and_threshold(sweep):
    two_dL = sweep["two_delta_L"]
    # The two-window solve floors at exactly 0 once the fronts merge; the open rows stay positive.
    open_L = [L for (L, true, _) in sweep["rows"] if true > 0.0]
    pt_L = [L for (L, true, _) in sweep["rows"] if true == 0.0]
    assert pt_L, "expected punchthrough at the narrowest gates"
    assert min(open_L) > max(pt_L)                         # a clean open→punchthrough transition
    # The subtraction agrees on *where*: 2·ΔL sits in the open→punchthrough window.
    assert max(pt_L) <= two_dL <= min(open_L) + 0.02


def test_mosfet_cross_section_refuses_punchthrough():
    with pytest.raises(ValueError, match="punchthrough"):
        d2.mosfet_cross_section(L_drawn_um=0.18, gate=GATE, **DEV)


# --------------------------------------------------------------------------- #
# Boundary guards (by-construction) — L never leaks into V_t; current coupling is geometric
# --------------------------------------------------------------------------- #
def test_guard_Vt_independent_of_channel_length(headline):
    # The named tar pit stays out: V_t is long-channel, so a different L_drawn (→ different L_eff)
    # gives a *bit-for-bit identical* V_t. A regression guard, not an anchor (it holds by construction
    # — device.py never puts L into V_t; this fails only if someone wires it in).
    other = d2.mosfet_cross_section(L_drawn_um=0.6, gate=GATE, width_um=WIDTH_UM,
                                    overdrive_V=OVERDRIVE_V, **DEV)
    assert other.mos.V_t == headline.mos.V_t               # bit-for-bit
    assert headline.mos.V_t == headline.mos_drawn.V_t      # L_eff vs L_drawn device: same V_t


def test_guard_current_gain_is_purely_geometric(headline):
    # The only way L moves a device number: I_Dsat ∝ W/L (same V_t, same overdrive), so the boost is
    # exactly L_drawn / L_eff_true.
    assert math.isclose(headline.current_gain,
                        headline.L_drawn_um / headline.L_eff_true_um, rel_tol=1e-12)
    assert headline.current_gain > 1.0                     # a shorter channel drives more current


# --------------------------------------------------------------------------- #
# Composition sanity — a genuinely 2-D S/D curving under the gate
# --------------------------------------------------------------------------- #
def test_headline_is_a_coherent_shortened_device(headline):
    h = headline
    assert 0.0 < h.L_eff_true_um < h.L_drawn_um
    assert 0.0 < h.shortening_frac < 1.0
    assert h.sd_xj_um > 0.0 and h.delta_L_um > 0.0
    assert 0.7 < h.delta_L_um / h.sd_xj_um < 0.95          # the lateral/vertical ratio (v1.8 band-ish)


def test_field_is_2d_channel_under_the_gate(headline):
    # The genuinely-2-D content: along the surface the dopant rises from the gate centre (still
    # p-channel, below N_A) to the open S/D window (n⁺, at the solubility limit).
    surface = headline.N[:, 0]
    assert surface[0] < headline.channel_N_A < surface[-1]
    assert surface[-1] > 0.5 * headline.sd_N_surface       # the far cell is saturated S/D (n⁺)
    assert np.all(np.diff(surface) >= -1e-9 * surface.max())   # rises monotonically toward the S/D
