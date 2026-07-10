"""Historical-modes A2 — the wavelength/lens ladder & proximity-gap printing (``chip.litho_history``).

The triad, per ``docs/plans/historical-modes.md`` (sharpened per the build note):

  * **tight — §A:** the modern ArF node reproduces :func:`chip.litho.expose_grating` **bit-for-bit** (the
    seam), and ``R = k₁·λ/NA`` is strictly **monotone in the ratio λ/NA** (a formula property, sign-robust);
  * **tight — §B:** ``gap = 0`` (contact) returns the unblurred band-limited grating to machine precision
    (the seam), the blur **conserves the image mean** (DC) at every gap, and contrast/NILS fall
    **monotonically** with gap (the ``√(λg)`` sign);
  * **flagged (kept SEPARATE from the tight legs):** the per-node NA table — so the *historical ladder's*
    λ/NA ordering g→EUV is a table consequence, not asserted as a law — and the Fresnel prefactor ``k``.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import numpy as np
import pytest

from chip import litho
from chip import litho_history as lh


# --------------------------------------------------------------------------- #
# §A the wavelength/lens ladder — tight (seam + formula-monotonicity)
# --------------------------------------------------------------------------- #
def test_default_node_is_bit_for_bit_expose_grating():
    """The modern ArF node forwards straight to expose_grating on demo_litho's Imaging (the seam)."""
    node = lh.NODES[lh.DEFAULT_NODE]
    assert (node.wavelength_nm, node.NA, node.sigma) == (193.0, 0.85, 0.5)   # demo_litho's stepper
    for pitch in (250.0, 400.0, 600.0):
        a = lh.image_at_node(node, pitch)
        b = litho.expose_grating(litho.Imaging(193.0, 0.85, 0.5), pitch)
        assert a.cd_nm == b.cd_nm and a.contrast == b.contrast and a.nils == b.nils


def test_resolution_is_monotone_in_lambda_over_NA():
    """R = k₁·λ/NA strictly decreases as the ratio λ/NA decreases — a formula property (sign-robust)."""
    # a synthetic sweep of the ratio, independent of the historical table (the TIGHT claim)
    ratios = [(400.0, 0.3), (400.0, 0.6), (200.0, 0.6), (200.0, 1.2), (13.5, 0.33)]
    seen = sorted(ratios, key=lambda wl_na: wl_na[0] / wl_na[1])
    res = [litho.rayleigh_resolution(wl, na) for wl, na in seen]
    assert all(a < b for a, b in zip(res, res[1:]))            # finer λ/NA ⇒ finer resolvable half-pitch


def test_finer_node_resolves_a_feature_a_coarser_one_cannot():
    """The A2 headline: the same pitch is flat at g-line and modulates at ArF (the era contrast)."""
    pitch = 400.0            # nm — below g/i-line's reach, within ArF's
    g = lh.image_at_node("g-line", pitch)
    arf = lh.image_at_node("ArF", pitch)
    assert not g.resolved and arf.resolved
    assert arf.contrast > g.contrast


# --------------------------------------------------------------------------- #
# §A the historical NODE TABLE — flagged (kept separate from the tight formula leg)
# --------------------------------------------------------------------------- #
def test_historical_ladder_lambda_over_NA_decreases_but_this_rests_on_the_table():
    """A FLAGGED consequence of the representative NA table (not the tight law): g→EUV λ/NA falls."""
    ladder = ["g-line", "i-line", "KrF", "ArF", "ArFi", "EUV"]
    ratios = [lh.NODES[key].wavelength_nm / lh.NODES[key].NA for key in ladder]
    assert all(a > b for a, b in zip(ratios, ratios[1:]))      # rests on NODES, documented as flagged


# --------------------------------------------------------------------------- #
# §B proximity gap-diffraction blur — tight (seam + conservation + sign)
# --------------------------------------------------------------------------- #
def test_contact_gap_zero_is_the_unblurred_mask_bit_for_bit():
    """gap = 0 → σ = 0 → peb_blur returns the sharp binary mask untouched (the degenerate seam)."""
    blurred = lh.proximity_image(500.0, 365.0, 0.0)
    mask = lh.binary_mask(lh.proximity_grid(500.0, 512), 500.0, 0.5)
    assert np.array_equal(blurred, mask)                       # bit-for-bit: no engine touched at σ=0
    assert set(np.unique(blurred)) <= {0.0, 1.0}               # still a sharp 0/1 shadow
    assert lh.fresnel_blur_length(365.0, 0.0) == 0.0


def test_blur_conserves_the_image_mean_at_every_gap():
    """The no-flux diffusion blur preserves the total (mask clear fraction / mean) exactly (conservation)."""
    mean0 = float(lh.proximity_image(500.0, 365.0, 0.0).mean())
    for gap in (2.0, 10.0, 40.0):
        mean = float(lh.proximity_image(500.0, 365.0, gap).mean())
        assert mean == pytest.approx(mean0, rel=1e-9)          # total untouched: duty (=0.5) preserved
    assert mean0 == pytest.approx(0.5, abs=1e-9)               # 50% duty ⇒ mean 0.5


def test_contrast_and_nils_fall_monotonically_with_gap():
    """Larger gap ⇒ larger σ ⇒ lower contrast and NILS — the √(λg) wall (the live discriminators)."""
    # a realistic multi-micron proximity feature (√(λg) resolves microns, not sub-micron)
    gaps = [0.0, 2.0, 8.0, 20.0, 40.0]
    prints = [lh.proximity_print(8000.0, g, wavelength_nm=365.0) for g in gaps]
    contrast = [p.contrast for p in prints]
    nils = [p.nils for p in prints]
    assert all(a > b for a, b in zip(contrast, contrast[1:]))  # contrast strictly falls
    assert all(a > b for a, b in zip(nils, nils[1:]))          # NILS strictly falls
    assert prints[0].blur_length_nm == 0.0                     # contact is sharp


def test_blurred_intensity_stays_non_negative():
    """Band-limiting the grating (not a raw step) keeps the blur ring-free — no negative 'intensity'."""
    for gap in (0.0, 5.0, 20.0, 80.0):
        img = lh.proximity_image(600.0, 365.0, gap)
        assert img.min() >= -1e-9                              # Trap-1 guard: no CN-style ringing


def test_proximity_resolution_gap_is_where_sigma_meets_the_half_pitch():
    """The √(λg) limit inverted: at proximity_resolution_gap, σ equals the feature half-pitch."""
    pitch, wl = 600.0, 365.0
    gap = lh.proximity_resolution_gap(pitch, wl)
    assert lh.fresnel_blur_length(wl, gap) == pytest.approx(pitch / 2.0, rel=1e-9)
    # and the grating is deeply degraded there (contrast well below the resolved floor)
    p = lh.proximity_print(pitch, gap, wavelength_nm=wl)
    assert p.contrast < 0.1


def test_finer_pitch_hits_the_wall_at_a_smaller_gap():
    """√(λg): a finer feature tolerates less proximity gap before it stops resolving."""
    fine = lh.proximity_resolution_gap(300.0, 365.0)
    coarse = lh.proximity_resolution_gap(900.0, 365.0)
    assert fine < coarse


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def test_guards_reject_bad_inputs():
    """The consumer guards its physical ranges (the established idiom)."""
    with pytest.raises(ValueError, match="gap_um"):
        lh.fresnel_blur_length(365.0, -1.0)
    with pytest.raises(ValueError, match="wavelength_nm"):
        lh.fresnel_blur_length(0.0, 5.0)
    with pytest.raises(KeyError):
        lh.get_node("no-such-node")
