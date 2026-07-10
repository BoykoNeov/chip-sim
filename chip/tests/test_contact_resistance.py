"""F2 silicide / contact resistance (``chip.contact_resistance``) — the two-term series-R model.

The triad, per ``docs/plans/silicide-contact-f2.md`` + ``historical-modes.md``:

  * **tight — the seam:** :func:`chip.contact_resistance.access_resistance` is today's ``R_sh·n_□``
    byte-for-byte (the consumer's scheme-off branch returns exactly this);
  * **tight — the sign / topology (the discriminator):** access is **linear** in ``R_sh``, the TLM
    contact is **sublinear** (exponent ≤ ½: → ½ at ``coth→1``, → 0 / ``R_sh``-independent at short
    contacts), so the contact's **share** of ``R_series`` rises monotonically as ``R_sh`` falls — for
    *any* ``ρ_c`` (no single scalar can move both terms). Salicide (low sheet) flips the bottleneck;
  * **flagged:** the house contact length ``CONTACT_LENGTH_UM``, the per-scheme ``ρ_c`` and silicide
    sheet — asserted only by shape/sign and at the stated operating point, not as exact numbers.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import math

import pytest

from chip import contact_resistance as cr


# --------------------------------------------------------------------------- #
# The seam — access_resistance IS today's R_sh·n_□ (tight, byte-for-byte)
# --------------------------------------------------------------------------- #
def test_access_resistance_is_the_bit_for_bit_today_value():
    """access_resistance(R_sh, n_□) == R_sh·n_□ exactly — the ρ_c-free anchor the consumer's seam returns."""
    for R_sh in (50.0, 60.0, 100.0):
        for n_sq in (0.0, 0.15, 1.0, 2.5):
            assert cr.access_resistance(R_sh, n_sq) == R_sh * n_sq      # byte-identical, not approx


# --------------------------------------------------------------------------- #
# The TLM contact term — the coth form and its two limits (tight exponents)
# --------------------------------------------------------------------------- #
def test_transfer_length_matches_the_definition():
    """L_T = √(ρ_c/R_sh), returned in µm — lands ~1–2.5 µm for the cited numbers."""
    lt_cm = math.sqrt(1.0e-6 / 60.0)
    assert cr.transfer_length(1.0e-6, 60.0) == pytest.approx(lt_cm * 1.0e4, rel=1e-12)
    assert 1.0 < cr.transfer_length(cr.RHO_C_DIRECT_AL, 60.0) < 2.5
    assert 1.0 < cr.transfer_length(cr.RHO_C_SALICIDE, cr.R_SH_SALICIDE) < 2.5


def test_contact_resistance_coth_form_and_long_contact_sqrt_limit():
    """R_c = √(ρ_c·R_sh)/W·coth(L_c/L_T); at L_c ≫ L_T coth→1 → R_c → √(ρ_c·R_sh)/W (exponent ½)."""
    rho, W = 1.0e-6, 10.0
    # long contact (100 µm ≫ L_T ~1.3 µm): coth ≈ 1, so the √-limit holds and R_c ∝ √R_sh
    c_hi = cr.contact_resistance(rho, 100.0, W, contact_length_um=100.0)
    c_lo = cr.contact_resistance(rho, 10.0, W, contact_length_um=100.0)
    assert c_hi / c_lo == pytest.approx(math.sqrt(10.0), rel=1e-3)       # exponent ½ (the √R_sh limit)
    # explicit value at the √-limit: √(ρ_c·R_sh)/W with W in cm
    assert c_hi == pytest.approx(math.sqrt(rho * 100.0) / (W * 1e-4), rel=1e-3)


def test_contact_resistance_short_contact_is_rho_c_over_area_and_Rsh_independent():
    """At L_c ≪ L_T the contact → ρ_c/(W·L_c): R_sh-independent (exponent 0), the scaled-contact regime."""
    rho, W, Lc = 1.0e-6, 10.0, 0.3
    # L_T here ~1.3–4.5 µm ≫ 0.3 µm, so we are in the ρ_c/area limit
    area_limit = rho / (W * 1e-4 * Lc * 1e-4)                            # ρ_c/(W·L_c) in Ω
    c_a = cr.contact_resistance(rho, 60.0, W, Lc)
    c_b = cr.contact_resistance(rho, 5.0, W, Lc)                         # 12× lower sheet
    assert c_a == pytest.approx(area_limit, rel=0.05)
    assert c_b == pytest.approx(area_limit, rel=0.05)
    assert c_a == pytest.approx(c_b, rel=0.05)                          # barely moves with R_sh (the point)


def test_contact_resistance_is_strictly_sublinear_in_Rsh():
    """The contact exponent is ≤ ½ < 1: halving nowhere doubles R_c the way the linear access term would."""
    rho, W = 1.0e-6, 10.0
    for Lc in (0.3, 2.0, 100.0):
        c_hi = cr.contact_resistance(rho, 100.0, W, Lc)
        c_lo = cr.contact_resistance(rho, 10.0, W, Lc)
        # access would scale exactly 10×; contact scales ≤ √10 (and → 1× at short contacts)
        assert 1.0 <= c_hi / c_lo <= math.sqrt(10.0) + 1e-9


# --------------------------------------------------------------------------- #
# The discriminator — contact share rises as R_sh falls, for ANY ρ_c (ρ_c-independent, tight)
# --------------------------------------------------------------------------- #
def test_contact_share_rises_monotonically_as_sheet_falls_for_any_rho_c():
    """The robust leg: R_contact/R_access strictly increases as R_sh falls, independent of ρ_c."""
    W, n_sq = 10.0, 1.0
    R_shs = [100.0, 60.0, 30.0, 10.0, 5.0]
    for rho in (1.0e-6, 3.0e-7, 1.0e-7):                                 # any interface resistivity
        ratios = [cr.contact_resistance(rho, R, W) / cr.access_resistance(R, n_sq) for R in R_shs]
        assert all(a < b for a, b in zip(ratios, ratios[1:]))          # strictly rising as R_sh drops


# --------------------------------------------------------------------------- #
# The scheme registry + the era flip (calibrated operating point)
# --------------------------------------------------------------------------- #
def test_direct_al_rides_the_diffused_sheet_salicide_shunts_it():
    """direct-Al inherits the diffused R_s (sheet=None); salicide shunts to the low silicide film sheet."""
    assert cr.SCHEMES["direct-Al"].effective_sheet(60.0) == 60.0        # rides the inherited diffused sheet
    assert cr.SCHEMES["salicide"].effective_sheet(60.0) == cr.R_SH_SALICIDE   # shunted to the film sheet
    assert cr.SCHEMES["salicide"].sheet_resistance_ohm_sq == cr.R_SH_SALICIDE


def test_the_bottleneck_flips_access_to_contact_across_the_era():
    """At the stated operating point: direct-Al is access-limited, salicide is contact-limited (the flip)."""
    diffused_R_sh, n_sq, W = 60.0, 1.0, 10.0
    al = cr.series_resistance(diffused_R_sh, n_sq, W, scheme="direct-Al")
    sil = cr.series_resistance(diffused_R_sh, n_sq, W, scheme="salicide")
    assert not al.contact_limited and al.contact_share < 0.5           # direct-Al: access dominates
    assert sil.contact_limited and sil.contact_share > 0.5             # salicide: contact dominates (flip)
    # the recovery is lopsided — access collapses far more than the contact term
    assert al.R_access_ohm / sil.R_access_ohm > 8.0                    # access drops ~12×
    assert al.R_contact_ohm / sil.R_contact_ohm < 5.0                 # contact drops only ~3×
    assert sil.R_series_ohm < al.R_series_ohm                          # net R_series still recovers


def test_series_resistance_is_access_plus_contact():
    """R_series = R_access + R_contact, and the shares are consistent."""
    s = cr.series_resistance(60.0, 1.0, 10.0, scheme="direct-Al")
    assert s.R_series_ohm == pytest.approx(s.R_access_ohm + s.R_contact_ohm, rel=1e-12)
    assert s.contact_share == pytest.approx(s.R_contact_ohm / s.R_series_ohm, rel=1e-12)


# --------------------------------------------------------------------------- #
# Guards (the established idiom)
# --------------------------------------------------------------------------- #
def test_guards_reject_bad_inputs():
    """The consumer guards its physical ranges."""
    with pytest.raises(ValueError, match="rho_c_ohm_cm2"):
        cr.transfer_length(0.0, 60.0)
    with pytest.raises(ValueError, match="R_sh_ohm_sq"):
        cr.transfer_length(1e-6, 0.0)
    with pytest.raises(ValueError, match="width_um"):
        cr.contact_resistance(1e-6, 60.0, 0.0)
    with pytest.raises(ValueError, match="contact_length_um"):
        cr.contact_resistance(1e-6, 60.0, 10.0, contact_length_um=0.0)
    with pytest.raises(ValueError, match="n_squares"):
        cr.access_resistance(60.0, -0.1)
    with pytest.raises(ValueError, match="rho_c_ohm_cm2"):
        cr.ContactScheme("bad", 0.0)
    with pytest.raises(ValueError, match="sheet_resistance_ohm_sq"):
        cr.ContactScheme("bad", 1e-6, sheet_resistance_ohm_sq=-1.0)
