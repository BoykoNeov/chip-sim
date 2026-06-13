---
name: fab-game-c1
description: "project (2026-06-14): C1 BUILT — crucible oxygen → thermal donors (czochralski.py §1e); cited KFR fourth-power initial rate ∝[O_i]⁴, donors compensate p-substrate → net N_A → V_t down via the G4a chain; the crystal-growth ELECTRICAL deepening"
metadata: 
  node_type: memory
  type: project
  originSessionId: e06638ba-b41b-4350-a5e3-109ddf86c5ad
---

**C1 BUILT (2026-06-14)** — crucible oxygen → **thermal donors**, the first **scope-edge-backlog**
promotion ([[scope-edge-backlog]]) and the crystal-growth story's **electrical** axis (CG-1/2/3 covered
the doping-profile, defect, and interface axes). Bundled with [[fab-game-d1]] as "two quick, high-confidence
deepenings." Advisor-gated build.

**The cited claim (the ONE anchor, web-verified before pinning):** the **initial** thermal-donor formation
rate ∝ the **FOURTH power** of interstitial oxygen, `dN_TD/dt|₀ ∝ [O_i]⁴` — **Kaiser–Frisch–Reiss, Phys.
Rev. 112, 1546 (1958)** (the fourth power ⇒ a four-oxygen donor core), for ~450 °C anneals. Confirmed the
volume:page via WebSearch (APS DOI 10.1103/PhysRev.112.1546) — advisor flagged "fairly confident about a
volume:page IS the coin-flip zone, don't pin from memory." Typical CZ [O_i] ~1e17–1e18 cm⁻³ (≈1e18 common).

**New physics `chip/czochralski.py` §1e** (closed-form, NO engine, NO ADR — like Scheil/Deal–Grove):
- `thermal_donor_density(O, anneal_min) = N_sat·(1−e^(−t/τ))` — saturating exponential; `τ ∝ 1/[O_i]`.
- `thermal_donor_formation_rate(O)` = the t→0 slope `= N_sat/τ ∝ [O_i]⁴` — **exposed as its own fn** so the
  fourth power is asserted DIRECTLY (advisor: a fixed-t finite diff understates the high-O ratio once it
  saturates, since τ∝1/O).
- `thermal_donor_saturation(O) ∝ [O_i]³` — the **flagged cube law** (reported but more literature-variable
  than the rate's fourth power → NOT an anchor, framed like G5's `AR_crit=SC/(1−SC)`).
- `net_doping_after_donors(N_A, N_TD) = N_A − N_TD` — the EXACT compensation algebra; **raises on type
  inversion** (`N_TD ≥ N_A` → n-type — a guarded named edge, the compact p-device can't model n-channel).

**Triad shape = the flagged-phenomenology tier (NO conservation law), advisor-calibrated:**
- **tight** = the SEAM (no oxygen OR no anneal ⇒ `N_TD=0` **exact, by BOTH paths** — donors form at the
  anneal, not during growth) + the exact `N_A−N_TD` compensation;
- **cited direction** = the KFR fourth-power rate (the only thing borrowing a citation);
- **flagged** = the saturating form, the cube exponent, EVERY magnitude (`TD_SAT_AT_REF≈4e16`,
  `τ_ref≈60min`, the [O_i] band) — the double-donor ≤2 e⁻/cluster factor folded into the flagged coeff so
  `N_TD` is the active CARRIER concentration (unit-consistent with G4a's `net_doping_shift`). Does NOT
  borrow Scheil's anchors (the boule docstring's standing honesty rule). `test_czochralski.py` +10.

**`fab_game` wiring:** `CzochralskiKnobs(oxygen_conc_cm3, thermal_donor_anneal_min)` (both opt-in → the
seam) → `thermal_donor_density` property → `Recipe.effective_channel_N_A` SUBTRACTS donors (via
`net_doping_after_donors`) → fed to BOTH junction and device (coherent), so resistivity rises too. Rides the
**existing G4a net-doping→V_t chain** ([[fab-game-g4]]) — NO device-step physics change. `device_step` gains
a recorded-only `thermal_donor_density` (NOT re-subtracted — advisor checked no double-count; the key is
added only when >0 so a clean record is byte-unchanged); `diagnose` names the donor V_t root cause.

**Seam (hard, advisor gate #2):** `oxygen=None` OR `anneal=0` → `N_TD=0` exact → `DEFAULT_RECIPE` reproduces
`demo_device`; all G1–G7 banked demos byte-for-byte. The MAGNITUDE ladder (1e17 boron substrate): low
[O_i]=5e17 barely moves V_t (0.547→0.528, in spec), typical 8e17 dips (→0.46, in spec near floor), high
1.2e18 + long anneal scraps (V_t→0.20 < 0.45 floor) — **without inverting** (N_sat<1e17 at high O, so the
demo can't accidentally hit the inversion guard).

**Banked `demo_thermal_donors`/`fab-game-c1.png`** (3 panels): N_TD(t) kinetics at 3 oxygen levels | V_t
walk down the anneal (high O scraps) | the cited power laws log–log (rate slope 4, sat slope 3).
`test_thermal_donors.py` (6) + `test_demo_thermal_donors.py` (4). Full suite 572 green. **Still deferred:**
[O_i]=f(pull/rotation/melt), higher-T "new donor"/precipitation regimes, type inversion. [[fab-game]]
[[scope-edge-backlog]] [[fab-game-g4]] [[mos-threshold-voltage-source]]
