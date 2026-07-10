"""Historical-modes A4 — photoresist generations: negative-resist swelling (``chip.resist_history``).

The triad, per ``docs/plans/historical-modes.md`` (sharpened per the build note):

  * **tight — the seam:** the modern ``chemistry="positive"`` develops the aerial image byte-identically to
    :func:`chip.litho.expose_grating` (same dark-line clip);
  * **tight — the sign/topology:** swelling only ever *grows* the negative line (``s ≥ 0``), so the space
    shrinks monotonically and, past a floor, bridges — the discriminator, sign-robust;
  * **tight — the floor law:** :func:`chip.resist_history.swelling_resolution_floor` is ``∝ thickness`` and
    takes **no optics** (structurally optics-independent — the A4 headline, orthogonal to A2's ``λ/NA``);
  * **tight — the CAR delegation:** ``chemistry="car"`` is literally :func:`chip.litho.expose_grating_car`;
  * **flagged (kept SEPARATE from the tight legs):** the swelling coefficient :data:`SWELLING_FACTOR` and
    the representative :data:`RESIST_THICKNESS_NM` — magnitudes, not laws.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import numpy as np
import pytest

from chip import litho
from chip import resist_history as rh

_FINE = litho.Imaging(365.0, 0.45, 0.5)      # fine optics: optical floor ≪ the swelling floor


# --------------------------------------------------------------------------- #
# The seam — positive develop IS litho.expose_grating (tight)
# --------------------------------------------------------------------------- #
def test_positive_develop_is_bit_for_bit_expose_grating():
    """The modern positive resist develops the aerial image exactly as expose_grating (the seam)."""
    for pitch in (900.0, 1500.0, 2500.0, 3200.0):
        pos = rh.develop_resist(_FINE, pitch, "positive")
        eg = litho.expose_grating(_FINE, pitch)
        assert pos.cd_nm == eg.cd_nm and pos.contrast == eg.contrast and pos.nils == eg.nils
        assert pos.swell_length_nm == 0.0 and not pos.bridged           # no swelling on the successor


def test_default_chemistry_is_positive():
    """The default resist is the modern/seam chemistry (positive) — default off ⇒ current develop."""
    assert rh.DEFAULT_RESIST == "positive"
    d = rh.develop_resist(_FINE, 1500.0)
    assert d.chemistry == "positive" and d.swell_length_nm == 0.0


# --------------------------------------------------------------------------- #
# The swelling sign/topology — grows the line, shrinks the space, bridges (tight)
# --------------------------------------------------------------------------- #
def test_swelling_grows_the_negative_line_over_the_positive_one():
    """At the same resolved pitch the negative (swollen) line is wider than the positive line by 2·s."""
    pitch = 2600.0            # comfortably resolved for both (above the swelling floor)
    pos = rh.develop_resist(_FINE, pitch, "positive")
    neg = rh.develop_resist(_FINE, pitch, "negative")
    # the negative line = the bright complement (pitch − dark) plus 2·s of swelling
    base = pitch - pos.cd_nm
    assert neg.cd_nm == pytest.approx(base + 2.0 * rh.swell_length(), rel=1e-12)
    assert neg.cd_nm > base and neg.swell_length_nm > 0.0               # swelling only grows the line


def test_negative_space_shrinks_monotonically_with_swelling():
    """More swelling ⇒ a strictly narrower space (the sign of the limitation), until it bridges."""
    pitch = 2600.0
    spaces = [rh.develop_resist(_FINE, pitch, "negative", swelling_factor=f).space_nm
              for f in (0.0, 0.2, 0.4, 0.6)]
    assert all(a > b for a, b in zip(spaces, spaces[1:]))               # strictly falls with swelling
    # factor 0 (no swell) leaves the same space the positive develop has (the complement of the line)
    pos = rh.develop_resist(_FINE, pitch, "positive")
    assert spaces[0] == pytest.approx(pitch - (pitch - pos.cd_nm), rel=1e-12)  # == pos.cd_nm


def test_negative_bridges_at_a_coarser_pitch_than_the_optical_floor():
    """The A4 contrast: the same fine optics resolves finer as positive than the negative can (swelling)."""
    def smallest_resolving(chem):
        return min(p for p in np.arange(600.0, 4000.0, 20.0)
                   if rh.develop_resist(_FINE, float(p), chem).resolved)
    neg_floor = smallest_resolving("negative")
    pos_floor = smallest_resolving("positive")
    assert neg_floor > pos_floor                                       # swelling binds coarser than optics
    # a mid-band pitch: positive resolves, negative has bridged
    mid = 0.5 * (pos_floor + neg_floor)
    assert rh.develop_resist(_FINE, mid, "positive").resolved
    neg_mid = rh.develop_resist(_FINE, mid, "negative")
    assert neg_mid.bridged and not neg_mid.resolved and neg_mid.space_nm <= 0.0


# --------------------------------------------------------------------------- #
# The swelling magnitude & the floor law — ∝ thickness, optics-independent (tight law, flagged coeff)
# --------------------------------------------------------------------------- #
def test_swell_length_is_factor_times_thickness():
    """s = swelling_factor · thickness — a fixed length per feature (the flagged magnitude)."""
    assert rh.swell_length(1000.0, 0.5) == 500.0
    assert rh.swell_length(1000.0, 0.0) == 0.0                         # no swell (the seam)
    assert rh.swell_length(0.0, 0.5) == 0.0


def test_swelling_floor_scales_with_thickness_and_is_optics_independent():
    """The floor ∝ thickness (doubles with thickness) and takes NO optics — the A4 headline, structural."""
    f1 = rh.swelling_resolution_floor(1000.0)
    f2 = rh.swelling_resolution_floor(2000.0)
    assert f2 == pytest.approx(2.0 * f1, rel=1e-12)                    # linear in thickness
    # half-pitch floor ≈ one film thickness at the cited 0.5 factor / 50% duty (the KTFR rule)
    assert f1 / 2.0 == pytest.approx(1000.0, rel=1e-12)
    # optics-independence is structural: the floor is a function of thickness/factor/duty ONLY (no Imaging).
    import inspect
    params = set(inspect.signature(rh.swelling_resolution_floor).parameters)
    assert params == {"thickness_nm", "swelling_factor", "duty"}       # no wavelength/NA anywhere


def test_actual_negative_floor_tracks_the_closed_form_across_optics():
    """The developed bridge pitch sits near the (optics-independent) closed-form floor for two very
    different lenses — the wavelength race can't clear a thickness-set floor."""
    def neg_floor(imaging):
        return min(p for p in np.arange(600.0, 4000.0, 20.0)
                   if rh.develop_resist(imaging, float(p), "negative").resolved)
    closed = rh.swelling_resolution_floor()                             # 2000 nm (no optics)
    coarse = neg_floor(litho.Imaging(436.0, 0.30, 0.5))                 # g-line-class
    fine = neg_floor(litho.Imaging(193.0, 0.85, 0.5))                   # ArF-class, 2.3× finer optics
    # both land within ~15% of the closed form despite a >2× optics change (the optical CD correction only)
    assert abs(coarse - closed) / closed < 0.15
    assert abs(fine - closed) / closed < 0.15


# --------------------------------------------------------------------------- #
# The CAR successor — delegated to litho.expose_grating_car (tight)
# --------------------------------------------------------------------------- #
def test_car_delegates_to_expose_grating_car():
    """chemistry='car' is literally litho.expose_grating_car (the DUV successor, shown not reimplemented)."""
    pitch = 1600.0
    car = rh.develop_resist(_FINE, pitch, "car")
    ref = litho.expose_grating_car(_FINE, pitch, litho.CARBake(t_bake_s=rh.CAR_BAKE_T_S),
                                   acid_dose=rh.CAR_ACID_DOSE)
    assert car.cd_nm == ref.cd_nm and car.contrast == ref.contrast and car.nils == ref.nils
    assert car.resolved == ref.resolved and car.swell_length_nm == 0.0


def test_car_resolves_where_the_negative_resist_bridges():
    """The successor's point: CAR resolves a pitch at which the swelling negative has bridged."""
    pitch = 1600.0
    assert rh.develop_resist(_FINE, pitch, "negative").bridged         # negative is shorted here
    assert rh.develop_resist(_FINE, pitch, "car").resolved             # CAR prints it


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def test_guards_reject_bad_inputs():
    """The consumer guards its physical ranges (the established idiom)."""
    with pytest.raises(ValueError, match="thickness_nm"):
        rh.swell_length(-1.0, 0.5)
    with pytest.raises(ValueError, match="swelling_factor"):
        rh.swell_length(1000.0, -0.1)
    with pytest.raises(ValueError, match="duty"):
        rh.swelling_resolution_floor(1000.0, 0.5, duty=1.0)
    with pytest.raises(KeyError):
        rh.get_resist("no-such-resist")
