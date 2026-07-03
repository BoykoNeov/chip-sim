---
name: range-statistics-source
description: "ion-implantation slice 1: cited LSS projected-range/straggle Rp(E), ΔRp(E) for B,P in Si — Gibbons–Johnson–Mylroie Projected Range Statistics, web-corroborated anchors, flagged power-law fit; B (lighter) penetrates deeper than P at equal energy"
metadata:
  node_type: memory
  type: reference
---

`chip/diffusion_dopant.py` **§5 (ion implantation, slice 1)** buries the dopant peak at a controlled
depth `R_p` — the observable thermal predep physically **cannot** make (predep is surface-peaked `erfc`).
The buried Gaussian IC needs the first two LSS moments: **projected range `R_p(E)`** and **straggle
`ΔR_p(E)`**. Built 2026-07-03. See [[dopant-diffusivity-source]] (the drive-in that then redistributes the
IC), [[fab-game]], `docs/plans/ion-implantation.md`.

**Canonical source.** Lindhard–Scharff–Schiøtt (LSS) range theory; the tabulated numbers are
**Gibbons, Johnson & Mylroie, *Projected Range Statistics*** (2nd ed., Dowden/Hutchinson/Ross 1975) —
*the* canonical implant range tables, reproduced in Plummer/Deal/Griffin, Campbell, Sze. Scanned PDFs
were unparseable, so anchors below were **web-corroborated** across independent sources (gtuttle
"Range and straggle for implants into silicon" table; TRIM/SRIM-95 predictions; textbook worked
examples) rather than lifted from one scan.

**Cited anchor values (µm), web-corroborated — the flagged benchmark, NOT asserted exact:**

| species | 10 keV | 30 keV | 80 keV | 100 keV | 200 keV |
|---|---|---|---|---|---|
| **B**  Rp   | 0.0333 | ~0.10 | 0.24  | 0.30  | — |
| **B**  ΔRp  | 0.0171 | —     | 0.063 | 0.067 | — |
| **P**  Rp   | 0.0139 | —     | —     | ~0.12 | 0.255 |
| **P**  ΔRp  | 0.0069 | —     | —     | —     | 0.0837 |

(B 100 keV also given as TRIM `Rp≈306 nm / ΔRp≈66.7 nm`.)

**The model — flagged power law over the anchors, not an LSS solver** (advisor: "monotone `R_p(E)` is the
only hard requirement; a flagged power-law over 2–3 anchors is enough"). `R_p = a·E^p`, `ΔR_p = b·E^q`
fit in log-space; reproduces the anchors within **~10 %** across the decade 10→200 keV. Fitted exponents:
B `R_p ∝ E^0.95`, `ΔR_p ∝ E^0.59`; P `R_p ∝ E^0.97`, `ΔR_p ∝ E^0.83`.

**The physics the fit captures (the tight, sign-robust part):** **monotone `R_p(E)`** (energy → depth, the
game's teaching lever) and the **species ordering** — **boron (lighter, Z=5) penetrates DEEPER than
phosphorus (heavier, Z=15) at equal energy** (`R_p_B > R_p_P`): less nuclear stopping per collision.
`ΔR_p/R_p ~ 0.2–0.5`, larger for the lighter ion. These signs are cited; the absolute µm are flagged.

**Scope edges named:** (1) **symmetric Gaussian = first two moments only** — the real as-implanted profile
is **skewed** (Pearson-IV; B skews toward the surface) → slice 2. (2) **channeling tail** (deep exponential
along low-index axes) → slice 3, tilt/screen-oxide suppressed. (3) **surface truncation** — for a shallow
implant (`R_p` not ≫ `ΔR_p`) the Gaussian's `x<0` tail is lost/reflected; dose-`Q` amplitude is checked only
for a **deep** implant (`R_p ≳ 4·ΔR_p`), truncation-flagged (the no-flux drive-in conserves the IC's grid
dose exactly regardless — that's the tight conservation leg). (4) **damage → leakage** → slice 4.
