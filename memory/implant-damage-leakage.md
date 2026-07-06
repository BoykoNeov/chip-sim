---
name: implant-damage-leakage
description: "ion-implant slice 4 (LAST — plan COMPLETE) — displacement damage → residual-after-anneal traps → junction leakage; NRT/Kinchin–Pease N_d; the discriminator is RECOVERY (anneals out, unlike metals/dislocations)"
metadata: 
  node_type: memory
  type: project
  originSessionId: cb843bf0-397f-480d-88f5-e50f18c874f7
---

Ion-implantation **slice 4 = damage → leakage** BUILT (2026-07-06) — the **LAST** slice; the
`docs/plans/ion-implantation.md` four-slice plan is now **COMPLETE**. Builds on slice 1
([[range-statistics-source]]) / 2 ([[implant-pearson-skew]]) / 3 ([[implant-channeling-tail]]); wires the
implant into the existing SRH leakage channel ([[fab-game-g4b]]).

**The physics.** The ions don't just dope — they **smash the lattice** (nuclear collisions → Frenkel
pairs). Displacement count = modified **Kinchin–Pease / NRT** `N_d = 0.8·E_n/(2·E_d)`, `E_n = ν·E`
(nuclear-stopping fraction; the rest is electronic stopping, displaces nothing), `E_d ≈ 15 eV` the Si
threshold, `0.8` the NRT efficiency (Norgett–Robinson–Torrens 1975; Sze; Plummer §8 — **web-corroborated**).
Characteristic residual trap density `N_dam = Q·N_d/(√(2π)·ΔR_p)`.

**THE discriminator = RECOVERY (the load-bearing point, advisor).** Damage would otherwise be a
*redundant* third recombination centre on the `1/τ` channel next to the G4b metals and A1 dislocations.
What makes it a distinct regime that clears the "must discriminate" bar: implant damage **ANNEALS OUT** —
a real implant is *always* annealed (**the drive-in IS the anneal**), and the **residual AFTER anneal** is
what bites. So the chain is dose→damage→(anneal recovers)→residual→leakage; the **failure mode is an
INCOMPLETE anneal**. Metals don't anneal out; dislocations are grown-in. The demo centers this: leakage vs
anneal-T recovery curve, pass ≈ 920 °C at a 1 nA/cm² spec.

**Recovery is a SEPARATE Arrhenius — NOT the dopant ∫D dt budget (advisor, load-bearing).** Damage
annealing has its own activation energy; conflating it with the dopant-diffusion budget is physically
wrong even where monotone. `r(T,t) = exp(−k0·e^(−Ea/kT)·t)`, monotone-decreasing in both T and t. Tuned
`Ea = 1.5 eV` (in the cited ~1–2 eV point-defect-migration band); `k0 = 2.3e4` is a FLAGGED *effective
lumped first-order* rate calibrated to spread the recovery across ~550–850 °C (NOT a phonon attempt
frequency). First cliff-like at Ea=1.8/k0=1e7 → retuned for a graded curve (cf. [[gradual-failure-preferred]]).

**The seam / architecture.** Damage is a **read off** the implant, **NOT** a profile field — `implant_profile`
`N(x)` is untouched (profile seam trivially intact; no new `Implant` field). Mirrors the **A1 dislocation
pattern exactly**: source in `diffusion_dopant.py §5d` (`displacements_per_ion`, `damage_residual_fraction`,
`implant_damage_density`), consumer in `lifetime.py` (new `damage_trap_density` kwarg on `srh_lifetime`/
`device_leakage`, `implant_damage_recombination_rate`, `DAMAGE_SIGMA_N=1e-16`). No import cycle
(`diffusion_dopant` never imports `lifetime`). The bite-seam: `damage_trap_density=0` → `τ_bulk` bit-for-bit
(whole existing suite byte-identical). Chip-side only — **no fab_game stage** (slices 2–4 all stayed
chip-side; the `device_leakage` kwarg is *exposed* for the game, not wired).

**Triad.** Tight/sign-robust: seam (`=0` → τ_bulk bit-for-bit); `N_d` monotone in energy + **heavier ion
(P) damages more than lighter (B)** (same physics as B-penetrates-deeper); dose monotonicity (`N_dam ∝ Q`,
leakage ∝ Q); **anneal recovery** (`N_dam` falls monotonically with anneal T — the discriminator);
recovery `r` monotone-decreasing in T *and* t; `t=0 → r=1` (as-implanted). Flagged: `ν(species)` (B 0.10 /
P 0.25), `σ_damage`, recovery `Ea/k0`; CITED = NRT form + `E_d≈15 eV` + all the SIGNs.

**Consumer:** `chip.lifetime.device_leakage.j_leak` (the leaky diode). Demo = `chip-implant-damage.png`
(recovery vs anneal-T with shaded pass window + dose ∝ Q log-log). 8 new tests in `test_implant.py`, 4 in
`test_lifetime.py`. Amorphization threshold + SPE regrowth kinetics stay the named deferred edge.
[[range-statistics-source]] [[implant-channeling-tail]] [[fab-game-g4b]] [[fab-game-a1]]
