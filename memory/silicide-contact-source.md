---
name: silicide-contact-source
description: "F2 / historical-modes B7: cited TLM contact-resistance coth form (Schroder/Berger) + silicide ρ_c / R_sh bounds (TiSi₂ ~1e-7 Ω·cm², ~5 Ω/□; Al–Si ~1e-6)"
metadata:
  node_type: memory
  type: reference
---

**Cited source for F2 silicide / contact resistance** (`chip/contact_resistance.py`, [[historical-modes-b7]]).
The cited legs (the TLM form + the ρ_c / R_sh sanity bounds); the contact length and the calibrated
operating point are flagged house numbers.

* **Transfer-length model (TLM) contact resistance — Schroder, *Semiconductor Material and Device
  Characterization* (TLM/contacts chapter); Berger, *Solid-State Electronics* 15:145 (1972); Sze–Ng
  §3.** `R_c = √(ρ_c·R_sh)/W · coth(L_c/L_T)`, transfer length `L_T = √(ρ_c/R_sh)`
  (web-verified against the Wikipedia "Transfer length method" derivation). The two limits are the whole
  discriminator: **long contact `L_c ≫ L_T`** → `coth→1` → `R_c → √(ρ_c·R_sh)/W` (**exponent ½** in
  R_sh); **short contact `L_c ≪ L_T`** → `coth ≈ L_T/L_c` → `R_c → ρ_c/(W·L_c)` (**exponent 0**,
  R_sh-**independent** — current crowds the leading edge, only ρ_c and contact AREA matter). Access
  `R_access = R_sh·n_□` is **linear**. So contact exponent ≤ ½ < 1 = access exponent ⇒ the contact SHARE
  of R_series rises monotonically as R_sh falls, for ANY ρ_c — the robust, ρ_c-independent tight leg. A
  scalar sheet-shunt cannot reproduce two different exponents (the build's licence).

* **Specific contact resistivity ρ_c (Ω·cm²) — sanity bounds** (Maex, *Silicides for VLSI*; Sze–Ng;
  Plummer contacts, web-searched): direct **Al–Si ρ_c ≈ 1e-6**; self-aligned **TiSi₂ ρ_c ≈ 1e-7–3e-7**
  on a well-doped (~1e20) n⁺/p⁺ junction (best reported ~1e-9 with pre-contact amorphization / Zr — not
  used). Code: `RHO_C_DIRECT_AL=1e-6`, `RHO_C_SALICIDE=3e-7` — the salicide interface is taken only ~3×
  better because the **decisive** salicide win is the sheet shunt, not ρ_c (at the sub-µm contact the
  term is ρ_c/area-limited, so the sheet drop barely helps it — the point of the flip).

* **Sheet resistance R_sh (Ω/□) — cited: TiSi₂ salicide films run ~5–7 Ω/□** (Maex); the diffused S/D
  sheet it shunts is ~50–100 Ω/□ (the journey's inherited `die.R_s`). Code: `R_SH_SALICIDE=5.0`; the ~12×
  shunt is the access-collapsing lever. The **flip** (direct-Al access-limited → salicide contact-limited)
  is a **calibrated operating point** (wide access run n_□≈1, house contact length 0.3 µm), not universal.

* **FLAGGED house numbers.** `CONTACT_LENGTH_UM=0.3` (the TLM needs a contact length; the journey geometry
  carries only the *access* run `sd_contact_squares = n_□`, not the contact dimension — the analogue of
  B6's `SPIKE_CONCENTRATION` lump). Single-contact-length TLM (no distributed via array).

* **The C49→C54 TiSi₂ narrow-line resistivity wall** (why Ti→Co→Ni salicide) is a real era-transition
  observable, named as a **deferred scope edge**, not modelled — the module carries one silicide (TiSi₂,
  period-correct 1980s salicide).

**Seam:** `access_resistance(R_sh, n_□)` alone IS today's `die.R_s · sd_contact_squares` byte-for-byte
(the ρ_c-free anchor — NOT the Al era; both eras add a contact term and depart from today). The consumer
(`fab_game/steps.py` `device_step`, `DeviceKnobs.contact_scheme=None` default) returns exactly that when
no scheme is engaged; `device.py` is untouched (the `R_series_ohm` source-degeneration seam already
consumes it). Cross-refs: [[historical-modes-b7]], [[historical-modes-b6]] (the metallization sibling —
Al spiking), [[mos-threshold-voltage-source]] (the `saturation_current` source-degeneration consumer),
[[irvin-sheet-resistance-source]] (the diffused `R_s` this shunts).
