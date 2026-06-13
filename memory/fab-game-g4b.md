---
name: fab-game-g4b
description: "project (2026-06-13): G4b BUILT — chip/lifetime.py SRH lifetime + junction leakage; deep-level metals (Fe/Cu) become the device consequence net doping can't carry; isolated metal→leaky-diode (V_t bystander), seam held"
metadata: 
  node_type: memory
  type: project
  originSessionId: 851693df-acfa-4130-b483-26a7c5af54cd
---

**G4b BUILT (2026-06-13)** — the **deferred Tier-2 SRH `lifetime.py`** [[fab-game-g4]] named (plan §5a
Tier 2 / §6 G4). Lands the **deep-level metals'** (Fe/Cu) device consequence net doping **cannot** carry:
the metals "ride along, scrubbed, no consequence" gap is now wired. Fast lane 401→**423** (+22); no
engine amendment, no ADR, no chip gallery card. Advisor **green-lit the architecture up front** (see
below); the one binding calibration he flagged held.

**New cited physics `chip/lifetime.py`** — the **Shockley–Read–Hall** recombination centre (closed form,
no engine — like device/junction/czochralski/purification). Two outputs:
- **lifetime** `1/τ = 1/τ_bulk + Σ σ_n·v_th·N_metal` — the p-type low-injection limit, so the
  **electron** capture cross-section governs (the minority carrier); `diffusion_length L=√(Dτ)`;
- **junction reverse leakage** `J_gen = q·n_i·W/(2τ) ∝ 1/τ ∝ N_metal` (generation-limited, the RT
  dominant term; `W` = one-sided abrupt depletion width from `N_A`, reusing device `ε_Si`/`n_i`).

**The triad (`test_lifetime.py`, 12) — tight = the SRH MACHINERY, magnitudes flagged LOOSE (plan §7):**
- **analytic (tight) — the low-injection reduction of the FULL `srh_rate` `U(n,p)`**: build the full SRH
  statistics `U=(pn−n_i²)/[τ_p0(n+n₁)+τ_n0(p+p₁)]`, show its p-type low-injection limit → `τ=Δn/U=τ_n0`
  — **`σ_p` AND `E_t` drop out, leaving `σ_n`** (a closed-form LIMIT, like czochralski's `k→1`; advisor:
  **NOT** billed as solver-grade independence — there's no solve under SRH). Clean limit `metals=0 →
  τ=τ_bulk` bit-for-bit (the seam). Rate-additivity = **by-construction regression guard, NOT an anchor**
  (advisor, per the [[chip-device-2d-v111]]/[[fab-game-g4]] "by-construction ≠ anchor" rule).
- **conservation (tight) — detailed balance** `U=0` **exactly** at `pn=n_i²`, for **any** `σ_n,σ_p,E_t`
  (the parameter-independence is what makes it a real check + certifies the shared full-`U` machinery).
  Bit-exact at power-of-ten equilibria (`pn−n_i²=0.0` in float).
- **benchmark (loose)** — cited Sze/Graff `σ_n` (Fe 5e-14 > Cu 5e-15) + `v_th` + the textbook order
  (clean FZ `τ~1ms`/`L~mm`/pA leakage; `[Fe]~1e12 → τ~few µs`). `τ_bulk`/`V_J`/leakage calib = flagged.

**THE single binding calibration (advisor-flagged — the one number `new-triad-passes` won't catch):**
`leakage(clean) < leakage(solar-1pass) < WINDOW < leakage(demo)`. **solar @ 1 pass leaves Cu≈2e12**
(Fe≈4e10) → leakage **1.1 nA/cm²**, and `test_intermediate_grade...`/`test_more_zone_passes` assert
solar/MGS-2pass yield 1.0 → both MUST clear the window. Chose `σ_n(Fe)=5e-14, σ_n(Cu)=5e-15, τ_bulk=1ms,
WINDOW hi=10 nA/cm²`: clean 0.009 < EGS 0.009 < MGS-2pass 0.045 < solar-1pass 1.1 < **10** < metal-1pass 91.
**Verified numerically FIRST** (before any module code), then end-to-end.

**Wiring (advisor guardrails honored):** leakage computed **INSIDE `device_step`** (NOT a new pipeline
step) → `test_bookkeeping`'s exact provenance list `[purification,wafer_prep,…,test]` **unchanged**; new
`Die.tau`/`Die.j_leak` fields (+`tau_us`/`j_leak_nA_cm2` props); new **optional** `SpecWindow`
(`optional=True` → a die not scored for leakage isn't failed "missing" — the fix for `test_defects`'
hand-built `healthy` die, the exact-equality risk the advisor said to grep for; all reason-asserts use
`any(...)`/`in`, addition-safe). Metals **never touch `V_t`/`I_Dsat`** (`test_propagation`). `diagnose`
gains a deep-level-metal leakage branch.

**The headline demo (`demo_lifetime`/`fab-game-g4b.png`, 3 panels):** a **new flagged `"metal"`
feedstock grade** (Fe=2e18,Cu=1e17, **Na/dopant-clean**) ISOLATES the story (existing grades couple
Na+metals) — one pass → `V_t=0.547` *in spec* but leakage 91 nA/cm² → wafer scrapped on **LEAKAGE**, the
trail naming deep-level-metal SRH (vs G4a's Na→V_t). **`V_t` is a bystander** = the device effect net
doping can't see. Rework = more passes (tiny `k` scrubs by `k²`/pass → **one extra pass** recovers:
metal-2pass τ 536 µs, leakage 0.017, yield 0%→100%). Panels: τ/leakage-vs-[Fe] scaling | the leakage
ladder (clean/EGS/solar pass, metal blows the window, V_t annotated flat) | the rework recovery.

**Seam (hard, held):** default `grade="clean"` → `τ=τ_bulk` + baseline leakage (0.009 nA/cm² ≪ window) →
`V_t`/`I_Dsat` bit-for-bit `demo_device`; G1–G4a demos byte-unchanged (only non-clean prior wafers =
test_contamination/demo_purification's solar/MGS, all still pass leakage). **Tier-3** (gettering/
precipitation, oxide breakdown) stays the named edge. [[fab-game-g4]] [[fab-game]] [[mos-threshold-voltage-source]]
