---
name: fab-game-cg1
description: "fab-game CG-1 BUILT — Burton–Prim–Slichter k_eff(pull rate) in chip/czochralski.py; pull rate flattens the Scheil boule; opt-in, seam-safe"
metadata: 
  node_type: memory
  type: project
  originSessionId: af9f62ce-8ebb-4040-af52-740987896b9f
---

**project (2026-06-13):** **CG-1 BUILT** — the first Czochralski **crystal-growth deepening** (a G2
follow-on, plan §6a; [[fab-game-g2]]'s #1 named scope edge). New cited physics in
`chip/czochralski.py` §1b (**additive** — the Scheil tests untouched):
`effective_segregation_coefficient(k₀, Δ) = k₀/[k₀+(1−k₀)·e^(−Δ)]` (**Burton–Prim–Slichter**, J. Chem.
Phys. 21:1987 1953) + `normalized_growth_velocity(pull_rate_mm_min) → Δ = v·δ/D` (flagged `δ`/`D`
module constants `BPS_BOUNDARY_LAYER_CM`/`BPS_MELT_DIFFUSIVITY_CM2_S`). A diffusion boundary layer at
the freezing interface makes the **effective** segregation rise toward 1 with **pull rate**, so
*pulling faster flattens the Scheil drift* down the boule.

**Triad (advisor-affirmed — the two LIMITS are the tight legs; NO independent conservation law, the
etch/packaging honesty tier):** tight = `Δ=0 ⇒ k_eff=k₀` **bit-exact** (the well-mixed Scheil seam) +
`Δ→∞ ⇒ k_eff→1` (complete solute trapping) + `k₀=1 ⇒ k_eff=1` ∀Δ; machinery (regression guards) =
monotone, bounded `[k₀,1]`, and the structural identity `1/k_eff − 1 = (1/k₀−1)·e^(−Δ)` (the
segregation deficit decays exponentially — NOT a conservation law); benchmark = the cited BPS *form*,
`k₀` the tight Trumbore anchor, the `δ`/`D` `v`-dependence the **calibrated/flagged** leg. The Scheil
mass-balance with `k→k_eff` is **not** a CG-1 leg (circular — re-tests `scheil_cumulative`).

**Wired (ONE knob, opt-in, seam-safe):** `fab_game` `CzochralskiKnobs.pull_rate_mm_min: float | None =
None` + a `k_eff` property; `Recipe.boule` passes `k=k_eff` when a pull rate is set, else `k=None` →
the boule falls back to the equilibrium Trumbore `k₀`. **Default None = the well-mixed idealization =
G2's `k₀`** → the seed slice is exact anyway, but the **binding seam is `demo_boule`'s z>0 batch sweep**
(advisor) — `k=None` keeps it byte-identical. Fast lane 492→**504** (+12 all new: `test_czochralski.py`
+8, `test_demo_crystal_growth.py` 4). No engine touch, no ADR. The roguelike-turn/`GameConfig` wiring is
a separate optional integration — **deferred** (standalone demo, [[fab-game-g7]] session untouched).

**THE load-bearing honesty (advisor magnitude check, run BEFORE designing the demo — same discipline as
G7's oxide lever):** boron's `k₀=0.80` **barely segregates already**, so BPS barely moves it at realistic
Δ. At **realistic Si pull (~0.5–2 mm/min → Δ≈0.07–0.28)** `k_eff` only reaches ≈0.81–0.84 → a **modest**
flattening (the V_t walk shrinks +0.20→+0.155 V, not to flat). The near-flat boule (`k_eff≳0.99`, walk
+0.01) needs Δ≳3 ⇒ pull **~10–20 mm/min, beyond realistic Si growth** — drawn in the demo but **labelled
illustrative**. Shipping an unflagged "pull faster → flat boron boule" would be quantitatively false for
Si (the flagged-magnitude trap). (Sb's strong segregation is *not* a better axial-flattening illustration
either — it stays far from 1 at realistic Δ; dropped.)

**NOT a score-war (advisor, the G7 over-claim lesson applied):** CG-1 is one-sided **in-model** — raising
`k_eff` only flattens doping → only helps yield. There is **no in-model brake** (unlike G7, where the
I_Dsat ceiling turned out to brake the oxide lever). So the demo shows the **physics consequence only**
(`k_eff(v)`, `N_A(z)`/`V_t(z)` flattening, the V_t spec window) — *not* a "fast-pull strategy beats
slow-pull, higher score" comparison. The real cost of fast pull — the **V/G microvoid criterion (CG-2)**,
**striations**, dislocation/max-pull — is named **loudly as the deferred next deepening**, not modelled.
Banked `demo_crystal_growth`/`fab-game-cg1.png` (3 panels). **CG-2/CG-3 remain deferred.** [[fab-game-g2]]
[[fab-game-g7]] [[dopant-solid-solubility-source]]
