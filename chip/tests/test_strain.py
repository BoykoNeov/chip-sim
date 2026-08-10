"""F5 strained silicon (``chip.strain``) — the one ``I_Dsat`` factor no process had ever moved.

The triad, per ``docs/plans/strained-silicon-f5.md`` + ``historical-modes.md``:

  * **tight — the seam:** no mechanism ⇒ the factor is exactly ``1.0`` and ``strained_mobility`` is the
    **byte-for-byte identity** on its input, so today's ``MU_N_EFF`` numbers are unchanged;
  * **tight — the model's own elasticity is 1:** asserted **against the real** :mod:`chip.device`, whose
    long-channel ``I_Dsat ∝ µ`` exactly on the ideal-contact path. That is *why* the drive read is an
    upper bound, and it is the reason ``device.py`` needs no change;
  * **tight — the cited elasticity is 0.500 on both carriers:** ``(drive−1)/(µ−1)``, from one paper.
    The tests pin the **definition** too — the ratio of the *factors* (0.917) is a different number, and
    a test written on it would pass while asserting nothing;
  * **cross-check (non-circular):** the cited drive-current enhancements are an independent **measured**
    quantity this module does not compute and has no route to (it would need the velocity saturation F5
    names and does not build) — the leg that bounds the model from outside it;
  * **the fork made mechanical:** the era's two mechanisms want opposite strain signs, so a hole
    mechanism is **refused** on the n-channel device rather than returning an inverted-sign number;
  * **flagged:** the hole mobility is a cited *floor* (">50%"), so its elasticity is an upper bound; and
    the independent 25 nm point sits at **0.35**, i.e. the bound loosens as ``L`` shrinks.

Import + numeric only (no matplotlib), so it rides the fast lane.
"""
import dataclasses

import pytest

from chip import device as dev, strain


# --------------------------------------------------------------------------- #
# The seam — no strain, nothing multiplies (tight, byte-for-byte)
# --------------------------------------------------------------------------- #
def test_no_mechanism_is_the_bit_for_bit_identity():
    """mobility_factor(None) is exactly 1.0 and strained_mobility returns its input unchanged."""
    assert strain.mobility_factor(None) == 1.0                      # exactly, not approx
    for mu in (450.0, dev.MU_N_EFF, 1.0, 1234.5):
        assert strain.strained_mobility(mu, None) == mu             # byte-identical
        assert strain.nmos_mobility(mu, None) == mu


def test_the_seam_record_reports_no_strain_and_leaves_elasticity_undefined():
    """The seam's factors are all exactly 1.0 — and its elasticity is None, not a fake 1.0."""
    ch = strain.strained_channel(dev.MU_N_EFF, None)
    assert not ch.is_strained
    assert ch.mu_strained_cm2_Vs == ch.mu_unstrained_cm2_Vs == dev.MU_N_EFF
    assert ch.mobility_factor == ch.drive_factor_long_channel == ch.drive_factor_cited == 1.0
    # gap, not fake value: with no mobility gain there is no fraction of one that reached the drive
    assert ch.cited_elasticity is None
    assert ch.drive_overstatement is None


def test_the_module_never_writes_back_to_MU_N_EFF():
    """Multiply and pass — the house constant is read, never rebound (a hand-computed β would re-baseline)."""
    before = dev.MU_N_EFF
    strain.strained_mobility(dev.MU_N_EFF, "tensile_cesl")
    strain.strained_channel(dev.MU_N_EFF, strain.TENSILE_CESL)
    assert dev.MU_N_EFF == before == 450.0


# --------------------------------------------------------------------------- #
# The elasticity — its DEFINITION, and the 0.500 both cited carriers land on
# --------------------------------------------------------------------------- #
def test_elasticity_is_the_ratio_of_fractional_gains_not_of_factors():
    """(drive−1)/(µ−1) — the factor ratio is a *different*, plausible-looking number. Pin the definition."""
    assert strain.elasticity(1.20, 1.10) == pytest.approx(0.10 / 0.20, rel=1e-12)
    assert strain.elasticity(2.00, 1.35) == pytest.approx(0.35 / 1.00, rel=1e-12)
    # the trap: the ratio of the stored factors is NOT the elasticity, on either cited mechanism
    for mech in strain.MECHANISMS.values():
        naive = mech.drive_factor / mech.mobility_factor
        assert naive != pytest.approx(mech.cited_elasticity, rel=1e-3)
        assert naive > mech.cited_elasticity                        # and it flatters the model


def test_elasticity_refuses_a_gain_free_input():
    """No mobility gain ⇒ no fraction of one to have reached the drive current. A gap, not 1.0."""
    for factor in (1.0, 0.9, 0.0):
        with pytest.raises(ValueError, match="undefined without a mobility gain"):
            strain.elasticity(factor, 1.10)


def test_both_cited_mechanisms_measure_an_elasticity_of_one_half():
    """0.500 on electrons AND holes, from one paper — the coincidence, reported as a coincidence."""
    for mech in strain.MECHANISMS.values():
        assert mech.cited_elasticity == pytest.approx(0.500, rel=1e-9)
        assert mech.drive_overstatement == pytest.approx(2.0, rel=1e-9)
        assert strain.drive_overstatement(mech) == pytest.approx(2.0, rel=1e-9)


def test_the_hole_mobility_is_a_cited_FLOOR_so_its_elasticity_is_an_upper_bound():
    """">50%" is stored as 1.50 (never round a win up) — which makes 0.5 an upper bound on that leg."""
    assert strain.SIGE_SD.mobility_is_floor is True
    assert strain.SIGE_SD.mobility_factor == 1.50
    # a larger true numerator can only lower the elasticity — the same direction as every other flag
    assert strain.elasticity(1.60, strain.SIGE_SD.drive_factor) < strain.SIGE_SD.cited_elasticity
    assert strain.TENSILE_CESL.mobility_is_floor is False           # the wired leg is point-valued


# --------------------------------------------------------------------------- #
# The model's OWN elasticity is 1 — asserted against the real chip.device (the bound's source)
# --------------------------------------------------------------------------- #
def _mos():
    """A long-channel device with the Phase-3 CD set — the drive-current readout needs one."""
    return dev.threshold_voltage(1e17, 0.015, channel_length_um=0.2)


def test_long_channel_drive_current_is_exactly_proportional_to_mobility():
    """I_Dsat ∝ µ by construction on the ideal-contact closed form: elasticity 1, no other option.

    This is the whole reason the wired drive read is an UPPER BOUND — the model cannot produce the
    measured 0.5, because producing it needs velocity saturation, which F5 names and does not build.
    """
    m, W = _mos(), 10.0
    Vgs = m.V_t + 1.0
    I0 = dev.saturation_current(m, Vgs, width_um=W)                 # the default mu_eff = MU_N_EFF
    for mech in strain.MECHANISMS.values():
        mu = strain.strained_mobility(dev.MU_N_EFF, mech)
        I = dev.saturation_current(m, Vgs, width_um=W, mu_eff=mu)
        assert I / I0 == pytest.approx(mech.mobility_factor, rel=1e-12)
        assert I / I0 == pytest.approx(mech.long_channel_drive_factor, rel=1e-12)
        # ... and that inferred gain is exactly drive_overstatement × the gain the devices measured
        inferred_gain, cited_gain = I / I0 - 1.0, mech.drive_gain
        assert inferred_gain / cited_gain == pytest.approx(mech.drive_overstatement, rel=1e-9)


def test_the_proportionality_is_the_ideal_contact_path_only():
    """With R_series > 0 the source-degeneration quadratic already sub-linearizes µ→I, on its own.

    Not a defect — it is why the elasticity-1 claim is scoped to the seam path (`R_series_ohm = 0`).
    """
    m, W, R_S = _mos(), 10.0, 50.0
    Vgs = m.V_t + 1.0
    I0 = dev.saturation_current(m, Vgs, width_um=W, R_series_ohm=R_S)
    mu = strain.strained_mobility(dev.MU_N_EFF, strain.TENSILE_CESL)
    I = dev.saturation_current(m, Vgs, width_um=W, mu_eff=mu, R_series_ohm=R_S)
    assert 1.0 < I / I0 < strain.TENSILE_CESL.mobility_factor       # degraded, but still a gain


def test_the_short_channel_crosscheck_shows_the_bound_loosening_with_L():
    """Independent 25 nm point: 100% µ → 35% drive, i.e. 0.35 — below the 90 nm 0.50, and far below 1."""
    assert strain.SHORT_CHANNEL_CROSSCHECK == pytest.approx(0.35, rel=1e-9)
    assert strain.SHORT_CHANNEL_L_NM == 25.0
    for mech in strain.MECHANISMS.values():
        assert strain.SHORT_CHANNEL_CROSSCHECK < mech.cited_elasticity < 1.0


# --------------------------------------------------------------------------- #
# The carrier fork — opposite signs, and the refusal that keeps the sign honest
# --------------------------------------------------------------------------- #
def test_the_two_cited_mechanisms_carry_opposite_signs():
    """Electrons want tensile, holes want compressive — the era's answer, and why it needed two processes."""
    assert strain.TENSILE_CESL.carrier == strain.ELECTRONS
    assert strain.TENSILE_CESL.sign == strain.TENSILE
    assert strain.SIGE_SD.carrier == strain.HOLES
    assert strain.SIGE_SD.sign == strain.COMPRESSIVE
    assert strain.TENSILE_CESL.sign != strain.SIGE_SD.sign


def test_only_the_electron_leg_is_wired_and_the_set_is_derived():
    """WIRED_MECHANISMS is derived from the registry, so a hole leg can never silently appear in it."""
    assert strain.WIRED_MECHANISMS == ("tensile_cesl",)
    assert all(strain.MECHANISMS[k].carrier == strain.ELECTRONS for k in strain.WIRED_MECHANISMS)
    assert "sige_sd" not in strain.WIRED_MECHANISMS


def test_the_nmos_read_refuses_the_hole_mechanism_by_name():
    """A pMOS technique on an n-channel device would invert the sign while looking like a result."""
    with pytest.raises(ValueError, match="n-channel-only"):
        strain.nmos_mobility(dev.MU_N_EFF, "sige_sd")
    with pytest.raises(ValueError, match="WRONG SIGN"):
        strain.strained_channel(dev.MU_N_EFF, strain.SIGE_SD)       # nmos=True is the default


def test_the_hole_leg_is_still_readable_as_cited_material_data():
    """An enhancement factor is a material property — no p-MOSFET is needed to state one."""
    mu = strain.strained_mobility(1000.0, "sige_sd")                # carrier-generic: caller owns the base
    assert mu == pytest.approx(1500.0, rel=1e-12)
    ch = strain.strained_channel(1000.0, strain.SIGE_SD, nmos=False)
    assert ch.carrier == strain.HOLES and ch.is_strained
    assert ch.drive_factor_cited == 1.25 and ch.drive_factor_long_channel == 1.50


def test_strained_mobility_requires_its_base_and_never_defaults_it():
    """A hole mechanism inheriting an *electron* surface mobility would be an incoherent pair."""
    with pytest.raises(TypeError):
        strain.strained_mobility("tensile_cesl")                    # type: ignore[call-arg]
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError, match="must be positive"):
            strain.strained_mobility(bad, "tensile_cesl")


# --------------------------------------------------------------------------- #
# The wired reading, and registry hygiene (including the number that must stay ABSENT)
# --------------------------------------------------------------------------- #
def test_the_wired_leg_reads_the_2003_nmos_rung():
    """+20% µ on the n-channel device — the headline, in the currency strain actually buys."""
    ch = strain.strained_channel(dev.MU_N_EFF, "tensile_cesl")
    assert ch.is_strained and ch.carrier == strain.ELECTRONS and ch.sign == strain.TENSILE
    assert ch.mu_strained_cm2_Vs == pytest.approx(dev.MU_N_EFF * 1.20, rel=1e-12)
    assert ch.mobility_factor == 1.20 and ch.drive_factor_cited == 1.10
    assert ch.cited_elasticity == pytest.approx(0.5, rel=1e-9)


def test_no_stress_field_exists_on_the_registry():
    """The GPa figure is FLAGGED-unsourced, so it is ABSENT — an empty field is how it leaks back in."""
    names = {f.name.lower() for f in dataclasses.fields(strain.StrainMechanism)}
    assert not any(("stress" in n) or ("gpa" in n) or ("pascal" in n) for n in names)
    assert strain.SIGE_SD.ge_percent == 17.0                        # cited composition IS carried, as data
    assert strain.TENSILE_CESL.ge_percent is None                   # and absent where no source pins one


def test_the_mechanism_record_validates_its_inputs():
    """Factors below 1 would be a degradation wearing an enhancement's name; bad carriers/signs are typos."""
    kw = dict(name="x", mechanism="y", carrier=strain.ELECTRONS, sign=strain.TENSILE,
              mobility_factor=1.2, drive_factor=1.1)
    with pytest.raises(ValueError, match="carrier must be"):
        strain.StrainMechanism(**{**kw, "carrier": "phonons"})
    with pytest.raises(ValueError, match="sign must be"):
        strain.StrainMechanism(**{**kw, "sign": "sideways"})
    with pytest.raises(ValueError, match="mobility_factor must be"):
        strain.StrainMechanism(**{**kw, "mobility_factor": 1.0})
    with pytest.raises(ValueError, match="drive_factor must be"):
        strain.StrainMechanism(**{**kw, "drive_factor": 0.9})
    with pytest.raises(ValueError, match="ge_percent must be"):
        strain.StrainMechanism(**{**kw, "ge_percent": 120.0})


def test_every_registry_entry_states_its_mechanism_and_is_frozen():
    """Cited data, immutable, and each entry says what physically does the straining."""
    for key, mech in strain.MECHANISMS.items():
        assert mech.mechanism and mech.name
        assert "uniaxial" in mech.mechanism.lower() or "uniaxial" in mech.name.lower()
        with pytest.raises(dataclasses.FrozenInstanceError):
            mech.mobility_factor = 9.9                              # type: ignore[misc]
        assert strain._resolve(key) is mech
