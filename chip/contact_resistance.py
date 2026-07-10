"""Silicide / contact resistance — the two-term series-R the diffusion consumer flattened (F2).

The **backward axis** (``docs/plans/silicide-contact-f2.md``): the parasitic source series resistance
``R_series`` the journey feeds :func:`chip.device.saturation_current` as source degeneration is **two
terms with different exponents in the sheet resistance ``R_sh``**, and *no single scalar can move both*:

  * **Access** (the diffused sheet the current runs through from contact to channel):
    ``R_access = R_sh · n_□`` — **linear in ``R_sh``** (``n_□ = L_access/W`` the square count). This is
    exactly what the diffusion consumer already models (``die.R_s · sd_contact_squares``).
  * **Contact** (the metal↔silicon interface, the transfer-length model):
    ``R_contact = √(ρ_c·R_sh)/W · coth(L_c/L_T)``, ``L_T = √(ρ_c/R_sh)`` — **strictly sublinear in
    ``R_sh``** (exponent ≤ ½; see below).

Self-aligned silicide (salicide) shunts the source/drain with a low-resistivity film, dropping the
effective sheet ``R_sh`` ~10–20×. Because access is *linear* and contact is *sublinear*, the shunt
collapses access far faster than contact — so **silicide solves the access resistance so thoroughly that
the *contact* becomes the new bottleneck** (the historical reason contact engineering — lower ``ρ_c``,
more contacts, later Ni over Ti/Co — became the next-era frontier). That crossover is the discriminating
observable this module exists for; a pure "multiply ``R_series`` by 0.3" sheet shunt cannot produce it.

The exponent gap is the discriminator (why a scalar can't fake it)
-----------------------------------------------------------------
``L_c/L_T = L_c·√(R_sh/ρ_c)``, so the contact term's ``R_sh`` exponent *depends on the contact length*:

  * **Long contact** ``L_c ≫ L_T`` (``coth → 1``): ``R_contact → √(ρ_c·R_sh)/W`` — exponent **½** (the
    textbook transfer-limited limit).
  * **Short contact** ``L_c ≪ L_T`` (``coth ≈ L_T/L_c``): ``R_contact → ρ_c/(W·L_c)`` — exponent **0**,
    ``R_sh``-**independent** (the current crowds into the leading edge; the sheet under the contact no
    longer matters — only ``ρ_c`` and the contact *area* do). This is the regime scaled sub-micron
    contacts live in, and it is exactly where "lower ``ρ_c`` is the next frontier" lives.

Either way the contact exponent is **≤ ½ < 1 = the access exponent**. The robust, ``ρ_c``-independent
consequence — the tight leg — is that **the contact's *share* of ``R_series`` rises monotonically as
``R_sh`` falls** (access ∝ ``R_sh``, contact ∝ ``R_sh^p`` with ``p ≤ ½``, so ``R_contact/R_access ∝
R_sh^{p−1}`` strictly increases as ``R_sh`` decreases — for *any* ``ρ_c``, contact length, or width).
Silicide's low-sheet shunt therefore *always* shifts the bottleneck toward contact. Whether that share
crosses 50% at a given operating point (the "flip") is a **calibrated** magnitude, not a universal claim.

The seam — the byte-for-byte anchor is the ρ_c-free computation, NOT an era
--------------------------------------------------------------------------
Today's ``R_series = R_s · n_□`` has **no contact term at all**. So *both* eras are departures from
today; :func:`access_resistance` alone reproduces today's value **byte-for-byte** (it *is* the same
``R_sh·n_□``). :func:`series_resistance` adds the contact term on top — a departure the moment a scheme
is chosen. The consumer (:func:`fab_game.steps.device_step`) keeps its ``R_series`` off by default (the
scheme knob absent ⇒ today's access-only value), so the game's banked demos are unchanged.

  * **Direct Al** — a contact term on the *diffused* sheet (``sheet = None`` ⇒ inherit ``die.R_s``): the
    high-``ρ_c`` interface a bare-metal contact adds to today's access.
  * **Salicide (TiSi₂)** — the film shunts the sheet (a low ``sheet``) *and* the contact rides that lower
    sheet with a modestly better ``ρ_c``: access collapses, contact lingers → the bottleneck flips.

The honesty ladder (per the F2 plan + the ``historical-modes.md`` triad)
-----------------------------------------------------------------------
* **Tight — the seam.** :func:`access_resistance` is today's ``R_sh·n_□`` byte-for-byte; the consumer's
  scheme-off branch returns it unchanged.
* **Tight — the sign / topology (the discriminator).** Access linear, contact sublinear (exponent ≤ ½,
  → ½ at ``coth→1``, → 0 / ``R_sh``-independent at short contacts); so the contact share of ``R_series``
  rises monotonically as ``R_sh`` falls, for any ``ρ_c``. Robust regardless of the flagged magnitudes.
* **Flagged — the magnitudes.** The house contact length :data:`CONTACT_LENGTH_UM` (no contact-length
  input exists in the journey geometry — the analogue of B6's ``SPIKE_CONCENTRATION`` lump), the
  per-scheme ``ρ_c`` and silicide sheet :data:`SCHEMES` (cited to sanity bounds, calibrated so a wide
  access run flips access-limited direct-Al to contact-limited salicide — the stated operating point),
  and the single-contact-length TLM (no distributed via array). Re-checked against the cited bounds.

Named scope edge (honest ceiling, stated so the omission isn't silent)
----------------------------------------------------------------------
* **The TiSi₂ C49→C54 narrow-line resistivity wall** (why the industry moved Ti→Co→Ni salicide) is a
  real era-transition observable but is **not** modelled here — the module carries one silicide (TiSi₂,
  the period-correct 1980s salicide) and names the CoSi₂/NiSi ladder as the ``ρ_c``/line-width frontier
  the contact-limited regime motivates. Build it only if we later want the CoSi₂/NiSi arc.

Units — inherited from the consumed modules (no new currency)
-------------------------------------------------------------
Specific contact resistivity ``ρ_c`` in **Ω·cm²** (the materials-datasheet unit); sheet resistance
``R_sh`` in **Ω/□**; contact width ``W`` and length ``L_c`` in **µm** (the cross-module length currency,
converted to cm internally for the ``ρ_c`` product); square count ``n_□`` dimensionless; all resistances
in **Ω** (the ``R_series_ohm`` currency :func:`chip.device.saturation_current` already consumes).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

_UM_PER_CM = 1.0e4                     # µm per cm (ρ_c is per cm² → lengths must enter in cm)

# --------------------------------------------------------------------------- #
# Cited constants + flagged calibration (the honesty ladder — see the module docstring)
# --------------------------------------------------------------------------- #
# Specific contact resistivity ρ_c (Ω·cm²) — CITED to sanity bounds (Schroder, *Semiconductor Material
# and Device Characterization* §3; Sze–Ng, *Physics of Semiconductor Devices* §3; Plummer, *Silicon VLSI
# Technology* contacts): direct Al–Si ρ_c ≈ 1e-6 Ω·cm²; self-aligned TiSi₂ ρ_c ≈ 1e-7–3e-7 Ω·cm² on a
# well-doped (~1e20) n⁺/p⁺ junction (Maex, *Silicides for VLSI*; the CoSi₂/NiSi ladder is the deferred
# narrow-line frontier). The direct-Al ρ_c is taken ~3× the salicide's here — the salicide interface is
# modestly better AND rides a far lower sheet; the *decisive* salicide win is the sheet shunt, not ρ_c.
RHO_C_DIRECT_AL = 1.0e-6               # CITED bound — Al–Si contact specific resistivity (Ω·cm²)
RHO_C_SALICIDE = 3.0e-7               # CITED bound — TiSi₂/n⁺ contact specific resistivity (Ω·cm²)

# Silicide film sheet resistance (Ω/□) — CITED: TiSi₂ salicide films run ~5–7 Ω/□ (Maex; the diffused
# S/D sheet it shunts is ~50–100 Ω/□, the journey's inherited die.R_s). The ~10–20× shunt is the
# access-collapsing lever.
R_SH_SALICIDE = 5.0                    # CITED bound — TiSi₂ salicide film sheet resistance (Ω/□)

# House contact length L_c (µm) — FLAGGED. The TLM needs a contact length; the journey geometry carries
# only the *access* run (``sd_contact_squares = n_□ = L_access/W``), NOT the contact dimension, so this is
# a house lump (the analogue of B6's SPIKE_CONCENTRATION). 0.3 µm is a scaled sub-micron contact — small
# vs the ~1–2.5 µm transfer length L_T, so the contact sits in the ρ_c/area-limited regime where the
# silicide sheet shunt barely helps the contact term (the point). Calibrated with the schemes below so a
# wide access run (n_□ ≈ 1) is access-limited for direct Al and contact-limited for salicide.
CONTACT_LENGTH_UM = 0.3                # FLAGGED — house contact length for the TLM coth (µm)


# --------------------------------------------------------------------------- #
# 1. The two terms — access (linear) and the TLM contact (sublinear)
# --------------------------------------------------------------------------- #
def access_resistance(R_sh_ohm_sq: float, n_squares: float) -> float:
    """The diffused-sheet **access** resistance ``R_access = R_sh · n_□`` (Ω) — **linear in ``R_sh``**.

    Byte-for-byte today's ``die.R_s · sd_contact_squares``: the current runs ``n_□ = L_access/W`` squares
    of the sheet the contact sits on. This is the term the diffusion consumer already models; the seam
    (scheme off) returns exactly this. Zero squares ⇒ 0 (the ideal-contact edge).
    """
    if R_sh_ohm_sq < 0.0:
        raise ValueError(f"R_sh_ohm_sq must be ≥ 0, got {R_sh_ohm_sq}")
    if n_squares < 0.0:
        raise ValueError(f"n_squares must be ≥ 0, got {n_squares}")
    return R_sh_ohm_sq * n_squares


def transfer_length(rho_c_ohm_cm2: float, R_sh_ohm_sq: float) -> float:
    """The current transfer length ``L_T = √(ρ_c/R_sh)`` (µm) — how far current crowds into the contact.

    Sets the contact term's regime: a contact longer than ``L_T`` buys nothing past it (``coth → 1``, the
    √-limited transfer regime); a contact shorter than ``L_T`` is ``ρ_c``/area-limited. Landing point for
    the cited numbers is ~1–2.5 µm.
    """
    if rho_c_ohm_cm2 <= 0.0:
        raise ValueError(f"rho_c_ohm_cm2 must be > 0, got {rho_c_ohm_cm2}")
    if R_sh_ohm_sq <= 0.0:
        raise ValueError(f"R_sh_ohm_sq must be > 0, got {R_sh_ohm_sq}")
    l_t_cm = math.sqrt(rho_c_ohm_cm2 / R_sh_ohm_sq)      # √(Ω·cm² / (Ω/□)) = cm
    return l_t_cm * _UM_PER_CM


def contact_resistance(
    rho_c_ohm_cm2: float, R_sh_ohm_sq: float, width_um: float,
    contact_length_um: float = CONTACT_LENGTH_UM,
) -> float:
    """The transfer-length-model **contact** resistance ``R_c = √(ρ_c·R_sh)/W · coth(L_c/L_T)`` (Ω).

    The metal↔silicon interface, with current crowding into the leading ``L_T`` of the contact captured
    by the ``coth(L_c/L_T)`` factor (Schroder §3; Sze–Ng §3; Berger 1972). **Sublinear in ``R_sh``**: it
    tends to ``√(ρ_c·R_sh)/W`` (exponent ½) for a long contact ``L_c ≫ L_T`` and to ``ρ_c/(W·L_c)``
    (exponent 0, ``R_sh``-independent) for a short one — see the module docstring. Lengths enter in cm
    (``ρ_c`` is per cm²); the ``coth`` is unitless in ``L_c/L_T``.
    """
    if width_um <= 0.0:
        raise ValueError(f"width_um must be > 0, got {width_um}")
    if contact_length_um <= 0.0:
        raise ValueError(f"contact_length_um must be > 0, got {contact_length_um}")
    l_t_um = transfer_length(rho_c_ohm_cm2, R_sh_ohm_sq)  # validates ρ_c, R_sh > 0
    W_cm = width_um / _UM_PER_CM
    sheet_transfer_ohm = math.sqrt(rho_c_ohm_cm2 * R_sh_ohm_sq) / W_cm    # √(ρ_c·R_sh)/W  (Ω)
    return sheet_transfer_ohm * (1.0 / math.tanh(contact_length_um / l_t_um))


# --------------------------------------------------------------------------- #
# 2. The contact-scheme registry (period texture — the ρ_c interface + the sheet the current rides)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ContactScheme:
    """A historical S/D contact: the interface ``ρ_c`` and the effective sheet the access + contact ride.

    ``rho_c_ohm_cm2`` the specific contact resistivity of the metal↔silicon interface.
    ``sheet_resistance_ohm_sq`` the effective sheet the current runs through *and* transfers into:

      * ``None`` — the contact sits on the bare **diffused** S/D, so it rides the inherited ``die.R_s``
        (direct aluminium): the contact term is *added on top of* today's access with no sheet change.
      * a number — a **silicide** film shunts the S/D to this (low) sheet, so both access and the TLM
        contact ride the shunted sheet (salicide): access collapses, the contact term barely follows.
    """

    name: str
    rho_c_ohm_cm2: float
    sheet_resistance_ohm_sq: float | None = None      # None ⇒ inherit the diffused die.R_s

    def __post_init__(self) -> None:
        if self.rho_c_ohm_cm2 <= 0.0:
            raise ValueError(f"rho_c_ohm_cm2 must be > 0, got {self.rho_c_ohm_cm2}")
        if self.sheet_resistance_ohm_sq is not None and self.sheet_resistance_ohm_sq <= 0.0:
            raise ValueError(
                f"sheet_resistance_ohm_sq must be > 0 or None, got {self.sheet_resistance_ohm_sq}")

    def effective_sheet(self, diffused_R_sh_ohm_sq: float) -> float:
        """The sheet the current rides: the silicide film's (if shunted) else the inherited diffused sheet."""
        return diffused_R_sh_ohm_sq if self.sheet_resistance_ohm_sq is None else self.sheet_resistance_ohm_sq


# The two contact eras. Direct Al (a high-ρ_c contact term on the diffused sheet) → self-aligned TiSi₂
# (the film shunts the sheet ~10–20× and the interface is modestly better) — the access-to-contact
# bottleneck flip. CoSi₂/NiSi are the deferred narrow-line ρ_c frontier (the C49→C54 wall, out of scope).
SCHEMES: dict[str, ContactScheme] = {
    "direct-Al": ContactScheme("direct aluminium contact", RHO_C_DIRECT_AL, sheet_resistance_ohm_sq=None),
    "salicide": ContactScheme("self-aligned TiSi₂ (salicide)", RHO_C_SALICIDE,
                              sheet_resistance_ohm_sq=R_SH_SALICIDE),
}


# --------------------------------------------------------------------------- #
# 3. The bundled series-resistance reading (the R_series_ohm currency the consumer/demo read)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SeriesResistance:
    """The decomposed source series resistance: access + contact, the shares, and the sheet each rode.

    ``scheme`` the contact metallization; ``R_sh_ohm_sq`` the effective sheet the current rode (the
    silicide film's, or the inherited diffused sheet); ``n_squares`` the access square count;
    ``rho_c_ohm_cm2`` the interface resistivity; ``transfer_length_um`` ``L_T``; ``R_access_ohm`` /
    ``R_contact_ohm`` the two terms; ``R_series_ohm`` their sum (the source-degeneration currency
    :func:`chip.device.saturation_current` consumes). Plain scalars — the loose-coupling currency."""

    scheme: str
    R_sh_ohm_sq: float
    n_squares: float
    rho_c_ohm_cm2: float
    transfer_length_um: float
    R_access_ohm: float
    R_contact_ohm: float
    R_series_ohm: float

    @property
    def contact_share(self) -> float:
        """The contact term's fraction of ``R_series`` — the graded bottleneck readout (rises as R_sh falls)."""
        return self.R_contact_ohm / self.R_series_ohm if self.R_series_ohm > 0.0 else 0.0

    @property
    def contact_limited(self) -> bool:
        """Whether the contact term is the majority of ``R_series`` (the post-salicide bottleneck)."""
        return self.contact_share > 0.5


def series_resistance(
    diffused_R_sh_ohm_sq: float,
    n_squares: float,
    width_um: float,
    *,
    scheme: ContactScheme | str = "salicide",
    contact_length_um: float = CONTACT_LENGTH_UM,
) -> SeriesResistance:
    """Decompose the source series resistance ``R_series = R_access + R_contact`` for a contact ``scheme``.

    ``diffused_R_sh_ohm_sq`` is the inherited diffused S/D sheet (``die.R_s``); the scheme decides the
    *effective* sheet the current rides (the diffused sheet for direct Al, the shunted silicide film for
    salicide — :meth:`ContactScheme.effective_sheet`). Both the access term
    (:func:`access_resistance`, linear) and the TLM contact term (:func:`contact_resistance`, sublinear)
    ride that effective sheet. Returns the decomposed :class:`SeriesResistance`.

    **Not** the seam: this always adds a contact term (both eras depart from today). The byte-for-byte
    seam is :func:`access_resistance` alone (today's ``R_sh·n_□``), which the consumer returns when no
    scheme is engaged.
    """
    sch = SCHEMES[scheme] if isinstance(scheme, str) else scheme
    R_sh = sch.effective_sheet(diffused_R_sh_ohm_sq)
    r_access = access_resistance(R_sh, n_squares)
    r_contact = contact_resistance(sch.rho_c_ohm_cm2, R_sh, width_um, contact_length_um)
    return SeriesResistance(
        scheme=sch.name, R_sh_ohm_sq=R_sh, n_squares=n_squares, rho_c_ohm_cm2=sch.rho_c_ohm_cm2,
        transfer_length_um=transfer_length(sch.rho_c_ohm_cm2, R_sh),
        R_access_ohm=r_access, R_contact_ohm=r_contact, R_series_ohm=r_access + r_contact,
    )
