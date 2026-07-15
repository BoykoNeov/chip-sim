---
name: high-k-dielectric-source
description: "F3: cited EOT identity + κ/φ_B table (Robertson EPJ AP 28:265) and the FLAGGED tunnelling masses; the κ↔gap inverse correlation is the load-bearing bit"
metadata:
  type: reference
---

Cited constants behind `chip/high_k.py` (F3 slice 1). **Web-verified 2026-07-15**; the recalled anchors in
`docs/plans/high-k-metal-gate-f3.md` were partly wrong, which is why the search-don't-recall rule exists.

**Primary source — one coherent set.** J. Robertson, "High dielectric constant oxides", *Eur. Phys. J.
Appl. Phys.* **28**, 265–291 (2004). (The plan named **Wilk/Wallace/Anthony JAP 89:5243 (2001)** — not
reachable; Robertson is the *better* fit anyway because it carries the κ↔gap correlation below.)

- **The EOT identity, eq. (2), verbatim:** `t_ox = EOT = (3.9/K)·t_HiK`. Capacitance eq. (1): `C = ε₀KA/t`.
  → Feeding EOT into a SiO₂-permittivity capacitance gives `ε₀·K/t_phys` = **the true physical C**. So the
  EOT route is an **identity with no barrier physics in it** — this is *why* `device.py` needs no change.
- **Table 2** (K / gap eV / **consensus CB offset to Si** eV) — the offset is the tunnelling barrier `φ_B`:
  SiO₂ **3.9 / 9 / 3.2** · Si₃N₄ 7 / 5.3 / 2.4 · Al₂O₃ 9 / 8.8 / 2.8 · HfSiO₄ 11 / 6.5 / 1.8 ·
  Y₂O₃ 15 / 6 / 2.3 · Ta₂O₅ 22 / 4.4 / 0.35 · **ZrO₂ 25 / 5.8 / 1.5** · **HfO₂ 25 / 5.8 / 1.4** ·
  La₂O₃ 30 / 6 / 2.3 · **TiO₂ 80 / 3.5 / 0** · **SrTiO₃ 2000 / 3.2 / 0**.
- **THE LOAD-BEARING BIT — κ and band gap are INVERSELY correlated** (Table 2 + Fig. 5). Buying κ *costs*
  barrier. Robertson's **requirement 4: band offsets over 1 eV**; K "should be over 10, preferably 25–30.
  There is a trade off with the band offset condition." Inverting this claim would make "more κ is better"
  true and destroy the slice's headline. TiO₂/SrTiO₃ (φ_B = **0**) are the counterexamples — and they need
  no `m*`, since `α = 0` for any mass.
- **The wall:** abstract — SiO₂ "so thin (**1.4 nm**) that its leakage current is too large"; body —
  "under 2 nm … exceeding **1 A/cm² at 1 V**"; low-standby-power needs **< 1.5e-2 A/cm²**. (Plan recalled
  ~1.2 nm; other sources say 1.3. Treat as a **~1.2–1.5 nm band**, not a constant.) HfO₂ chosen ~2001,
  shipped at 45 nm in 2007. Yeo et al.'s leakage figure of merit combines **barrier height, tunnelling
  mass AND K** — the three-term structure the model follows.

**FLAGGED — the tunnelling masses `m*` (NOT from Robertson; NOT the same evidence class).** Unlike κ and
φ_B these are **extracted by fitting J–V data**, with wide spreads:
- **SiO₂ ≈ 0.5 m₀** — classic value, agrees with photon-assisted-tunnelling data at a ~3.15 eV barrier;
  reported range ~0.29–0.6 (commonly 0.35–0.5). Pairing it with Robertson's 3.2 eV (vs its native 3.15) is
  a 1.5% barrier difference → **<1% in α** (it enters under a √). Immaterial; noted for coherent-set honesty.
- **HfO₂ ≈ 0.11 m₀** — 0.11 ± 0.03 from MOS/MOSFET determination; reported **range 0.08–0.2** across film
  composition/deposition/fitting method. **This spread is the model's dominant uncertainty**: it bands the
  HfO₂ win at EOT=1 nm to **3.9–9.5 decades** (central 0.11 → **5.6**; literature ~3–5).
- Al₂O₃/ZrO₂/La₂O₃ `m*` **not separately sourceable** → deliberately NOT in the registry (a `Dielectric`
  without a cited `(φ_B, m*)` pair could only carry an invented exponent).

**The non-circular cross-check (why fully-explicit beat a calibrated λ).** `α = 2√(2m*φ_B)/ħ` with the
above — sourced from band-offset/effective-mass work, **never fitted to a leakage curve** — *predicts* the
textbook **~1 decade per ~2 Å** SiO₂ slope (model: **1.78 Å**; the 0.42 m₀/3.1 eV pairing → 1.97 Å). A
per-material λ calibrated *from* leakage data cannot make this check. Same spirit as
[[irvin-sheet-resistance-source]] vs [[dopant-mobility-source]].

**Prefactor = FLAGGED house lump** (`J0_REFERENCE ≈ 2.8e8 A/cm²`), pinned at SiO₂/1.5 nm → 1 A/cm² @1 V,
and **shared across materials** — deliberately, so it **cancels exactly** in fixed-EOT ratios, leaving
`leakage_decades_saved` free of any calibrated constant. Named scope edges: no trapezoidal/field-lowering
or image-force correction (rectangular barrier at fixed bias, direct-tunnelling regime `V_g < φ_B`); no
QM/poly-depletion EOT correction; no trap-assisted/stress-induced leakage.

Consumer: [[high-k-gate-f3]]. Cousin sources: [[deal-grove-oxidation-source]] (the *physical* oxide this
never touches), [[mos-threshold-voltage-source]] (the `C_ox` path EOT feeds).
