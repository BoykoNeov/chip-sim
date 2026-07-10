"""Historical-modes B5 — LOCOS isolation & the bird's beak (``chip.locos_history``).

The triad, per ``docs/plans/historical-modes.md`` (sharpened per the build note / advisor):

  * **tight — the seam:** with no nitride (all-open surface) the modulation ``m ≡ 1`` and the field-oxide
    thickness is :func:`chip.oxidation.grow_oxide` **bit-for-bit**; even with a mask the field plateau is
    ``grow_oxide`` exactly;
  * **tight — the sign/topology:** the beak only ever grows *inward* (``m ∈ [0, 1]``), so the surviving
    active width shrinks **monotonically** as the drawn width shrinks and, past a floor, pinches off;
  * **tight — the two-window cross-check at wide stripes:** the two-field solve reproduces the single-edge
    subtraction ``W − 2·L_beak`` to grid precision at wide stripes;
  * **earned 2-D finding (direction, not coefficient):** near the merge the two-field solve pinches off
    *earlier* than ``2·L_beak`` — the opposing beaks' oxidant fields overlap;
  * **flagged (kept SEPARATE from the tight legs):** the beak/field-oxide ratio :data:`BEAK_DIFFUSION_FACTOR`,
    the :data:`ACTIVE_MODULATION_THRESHOLD`, and the merge coefficient — magnitudes, not laws.

Import + numeric only (no matplotlib), so it rides the fast lane. Grids are trimmed for speed where the
precision of the leg does not depend on resolution.
"""
import numpy as np
import pytest

from chip import oxidation as ox
from chip import locos_history as lh

# A trimmed grid for the topology/monotonicity legs (their sign is resolution-robust); the cross-check
# leg uses the module defaults (finer) where grid precision is the thing under test.
_FAST = dict(nx=140, ny=90, n_steps=70)


# --------------------------------------------------------------------------- #
# The seam — no nitride ⇒ m ≡ 1 ⇒ grow_oxide bit-for-bit (tight)
# --------------------------------------------------------------------------- #
def test_field_oxide_thickness_is_grow_oxide_bit_for_bit():
    """The absolute field-oxide thickness is oxidation.grow_oxide verbatim (the thickness source / seam)."""
    got = lh.field_oxide_thickness_um()
    ref = ox.grow_oxide(lh.FIELD_AMBIENT, lh.FIELD_T_CELSIUS, lh.FIELD_T_MINUTES, lh.FIELD_ORIENTATION).t_ox
    assert got == ref                                                    # exact, no re-derivation


def test_all_open_surface_gives_unit_modulation():
    """No nitride (open_mask all True) ⇒ the surface modulation is EXACTLY 1 everywhere (the seam)."""
    x = np.linspace(0.0, 3.0, 64)
    open_all = np.ones_like(x, dtype=bool)
    # a dummy diffused field: _surface_line must pin every open (field) cell to exactly 1, ignoring it
    m_dummy = np.zeros((x.size, 5))
    m_surf = lh._surface_line(open_all, m_dummy)
    assert np.all(m_surf == 1.0)                                         # field plateau is exact 1


def test_field_plateau_equals_grow_oxide_exactly():
    """Even WITH a nitride stripe, the open-field plateau of the profile equals grow_oxide bit-for-bit."""
    field = lh.field_oxide_thickness_um()
    p = lh.field_oxide_profile(5.0, field, **_FAST)
    assert p.t_ox_um.max() == field                                     # the plateau is grow_oxide exactly
    assert p.field_ox_um == field


# --------------------------------------------------------------------------- #
# The sign/topology — inward beak, m ∈ [0, 1], monotone shrink, pinch-off (tight)
# --------------------------------------------------------------------------- #
def test_modulation_stays_within_zero_and_one():
    """The maximum principle in use: m = t_ox/field ∈ [0, 1] (the beak only ever ADDS oxide, never over)."""
    field = lh.field_oxide_thickness_um()
    p = lh.field_oxide_profile(4.0, field, **_FAST)
    m = p.t_ox_um / field
    assert m.min() >= -1e-9 and m.max() <= 1.0 + 1e-9


def test_beak_encroaches_inward_active_below_drawn():
    """The beak eats active area: the surviving active width is strictly less than the drawn width."""
    field = lh.field_oxide_thickness_um()
    W = 5.0
    active = lh.active_width_um(W, field, **_FAST)
    assert 0.0 < active < W                                             # some active survives, but < drawn


def test_active_width_shrinks_monotonically_with_drawn_width():
    """Narrowing the drawn stripe monotonically shrinks the surviving active width, down to pinch-off."""
    field = lh.field_oxide_thickness_um()
    widths = [2.0, 3.0, 4.0, 5.0, 6.0]
    active = [lh.active_width_um(w, field, **_FAST) for w in widths]
    assert all(a <= b for a, b in zip(active, active[1:]))             # non-decreasing in drawn width
    assert active[-1] > active[0]                                       # and it genuinely moves


def test_narrow_stripe_pinches_off():
    """Below a minimum drawn width the two beaks merge and the active island is fully consumed (0)."""
    field = lh.field_oxide_thickness_um()
    assert lh.active_width_um(1.0, field, **_FAST) == 0.0               # pinched off
    assert lh.active_width_um(6.0, field, **_FAST) > 0.0               # comfortably isolated


# --------------------------------------------------------------------------- #
# The two-window cross-check + the earned 2-D finding
# --------------------------------------------------------------------------- #
def test_two_window_matches_subtraction_at_wide_stripes():
    """Tight cross-check: at wide stripes the two-field solve == the single-edge W − 2·L_beak (grid prec.)."""
    field = lh.field_oxide_thickness_um()
    beak = lh.birds_beak_length_um(field)                               # module-default grid
    for W in (5.0, 6.5, 8.0):
        true = lh.active_width_um(W, field)                            # default grid — precision under test
        approx = W - 2.0 * beak
        assert abs(true - approx) < 0.08                               # ~1–2 cells, grid precision


def test_two_window_pinches_off_earlier_than_2_beak():
    """The earned 2-D finding: near the merge the beaks overlap → pinch-off BEFORE 2·L_beak (direction)."""
    field = lh.field_oxide_thickness_um()
    beak = lh.birds_beak_length_um(field)
    # a drawn width comfortably ABOVE the single-edge 2·L_beak but where the two-field solve has pinched
    W = 2.0 * beak + 0.6                                                # single-edge says ~0.6 µm survives
    assert W - 2.0 * beak > 0.3                                         # subtraction predicts open active
    assert lh.active_width_um(W, field, **_FAST) == 0.0               # two-field: already pinched (overlap)


def test_cross_section_bundles_both_readings():
    """The bundled cross-section carries the subtraction and the two-field width, and the STI successor."""
    xs = lh.locos_cross_section(5.0, **_FAST)
    assert xs.field_ox_um == lh.field_oxide_thickness_um()             # the seam thickness
    assert xs.beak_um > 0.0 and 0.0 < xs.active_true_um < 5.0
    assert xs.active_approx_um == max(5.0 - 2.0 * xs.beak_um, 0.0)     # the textbook subtraction
    assert xs.sti_active_um == 5.0                                     # STI: no beak, active = drawn
    assert not xs.pinched_off and 0.0 < xs.shortening_frac < 1.0


# --------------------------------------------------------------------------- #
# The flagged magnitude — beak/field-oxide ratio in the cited band
# --------------------------------------------------------------------------- #
def test_beak_ratio_sits_in_the_cited_band():
    """The bird's beak ≈ 0.8–1× the field oxide (the cited LOCOS rule — the flagged calibration)."""
    field = lh.field_oxide_thickness_um()
    beak = lh.birds_beak_length_um(field)
    assert 0.75 <= beak / field <= 1.15                               # cited ~0.8–1×, house-calibrated
    # and it scales with the field oxide: a thicker field oxide ⇒ a proportionally longer beak
    beak_thick = lh.birds_beak_length_um(2.0 * field)
    assert beak_thick == pytest.approx(2.0 * beak, rel=0.03)          # L_beak ∝ t_field (the coeff-free law)


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def test_guards_reject_bad_inputs():
    """The consumer guards its physical ranges (the established idiom)."""
    with pytest.raises(ValueError, match="field_ox_um"):
        lh.birds_beak_length_um(0.0)
    with pytest.raises(ValueError, match="field_ox_um"):
        lh.active_width_um(4.0, -1.0)
