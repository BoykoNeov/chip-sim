---
name: historical-modes-b7
description: "project (2026-07-10): F2 silicide/contact-resistance BUILT as historical-mode B7 — two-term series-R (access linear + TLM contact sublinear) → I_Dsat; bottleneck flips access→contact"
metadata:
  node_type: project
  type: project
---

**F2 silicide / contact resistance BUILT** — landed as **historical-mode B7** (plan
`docs/plans/silicide-contact-f2.md`; the F-series roadmap `docs/plans/future-steps.md` F2). New physics
module `chip/contact_resistance.py` + `chip/demo_silicide_history.py` + `test_contact_resistance.py` (10
tests); gallery rung `hist·B7` (8th history mode, first **Contacts** stage); `chip-silicide-history.png`.
The **cheapest promotable step**: it feeds a *better-modelled* `R_series` into the **already-wired**
`R_series_ohm` source-degeneration seam — `device.py` is **untouched**. Sibling of [[historical-modes-b6]]
(the other metallization-stage mode, Al spiking). Cited constants → [[silicide-contact-source]].

**The discriminating observable (the build's licence):** `R_series` is **two terms with different sheet-
resistance exponents**, and no scalar can move both. **Access** `R_sh·n_□` = **linear**. **Contact** (TLM)
`√(ρ_c·R_sh)/W·coth(L_c/L_T)`, `L_T=√(ρ_c/R_sh)` = **sublinear** (exponent ≤ ½). Salicide shunts the sheet
~12× → access collapses, contact barely follows → **the bottleneck flips access→contact** (why lower-ρ_c
contacts Ti→Co→Ni became the next frontier). A "multiply R_series by 0.3" scalar can't reproduce two
exponents — this is what cleared the repo's *no-regime-without-a-discriminating-consumer* bar.

**Advisor reframes that changed the build (all load-bearing):**
1. **Per-scheme ρ_c is FREE honesty** — the discriminator is the *exponent gap* (1 vs ≤½), independent of
   ρ_c's value. So carry per-scheme ρ_c (direct-Al 1e-6, salicide 3e-7) AND show the clean exponent by
   *holding ρ_c and sweeping R_sh* (the demo's right panel). Not a dichotomy — two demonstrations.
2. **The coth MOVES the exponent** (I half-missed this): `L_c/L_T = L_c·√(R_sh/ρ_c)`. Long contact
   `L_c≫L_T` → exponent **½**; short contact `L_c≪L_T` → `R_c→ρ_c/(W·L_c)`, exponent **0**,
   R_sh-**independent**. At scaled sub-µm contacts (L_T~1–2.5 µm, house `CONTACT_LENGTH_UM=0.3`) we're in
   the ρ_c/area regime — so claim **sublinear**, test literal √ only at coth→1 (L_c=100 µm: contact ratio
   = √10 exactly). That ρ_c/area regime IS where "lower ρ_c is the next frontier" lives — a feature.
3. **The robust tight leg is NOT the flip magnitude** — it's that **contact's share of R_series rises
   monotonically as R_sh falls, for ANY ρ_c** (access linear, contact sublinear ⇒ ratio ∝ R_sh^(p−1)).
   The flip crossing 50% is a **calibrated operating point** (B6-style), not universal.

**Calibrated operating point** (stated, flagged): wide access run n_□=1, diffused R_sh=60 Ω/□, TiSi₂
sheet 5 Ω/□, W=10 µm, L_c=0.3 µm → direct-Al **36% contact (access-limited)**, salicide **67% contact
(contact-limited)**; access ÷12, contact ÷3.4, R_series ÷6.2, I_Dsat recovers ~1.2× (lopsided).

**The seam (advisor correction, carried from the plan):** the byte-for-byte anchor is the **ρ_c-free
computation** (`access_resistance(R_sh,n_□)` = today's `die.R_s·sd_contact_squares`), **NOT the Al era** —
*both* eras add a contact term and depart from today (direct-Al R_series HIGHER than today, salicide
LOWER). Consumer: `DeviceKnobs.contact_scheme` (None default = access-only seam) threaded through
`device_step`; **both `pipeline.py` call sites (240, 618) needed ZERO change** (they already pass
`recipe.device`), so the seam is airtight — verified end-to-end (`run_line`: scheme-off R_series =
R_s·n_□ to 1e-12, no `contact_scheme`/extra key in the record; fingerprint emitted only when engaged).
`die.R_s` stays access-only; contact is additive downstream (no double-count).

**Scope edge** (named, not silent): the **TiSi₂ C49→C54 narrow-line resistivity wall** (why Ti→Co→Ni) —
one silicide carried (TiSi₂, period-correct 1980s salicide); CoSi₂/NiSi arc deferred. Next F-series steps
(future-steps.md): **F3 high-κ/metal-gate** or **F4 BEOL/Cu-damascene RC** — the first genuinely *new
output*. See [[fab-game-e1]] (`R_series_ohm` first appeared as the diffusion consumer), [[historical-modes-h0]]
(the era display surface this rung joins).
