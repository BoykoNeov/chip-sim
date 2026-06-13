---
name: fab-game-cg3
description: "fab-game CG-3 BUILT — Stefan interface heat balance in chip/czochralski.py supplies CG-2's gradient G; ξ=V/G_s saturates at ξ_max=k_s/(Lρ); closed-form, NO engine amendment/ADR; all 3 CG deepenings now built"
metadata: 
  node_type: memory
  type: project
  originSessionId: af9f62ce-8ebb-4040-af52-740987896b9f
---

**project (2026-06-13):** **CG-3 BUILT** — the third & **last** Czochralski crystal-growth deepening
(plan §6a; the "Stefan moving-interface" item). New cited physics `chip/czochralski.py` §1d (additive
— Scheil/CG-1/CG-2 tests untouched): `stefan_interface_gradient(V, G_l) = (L·ρ·V + k_l·G_l)/k_s` (the
**Stefan condition** for a quasi-steady front at the pull rate `V`) + `max_voronkov_ratio() = k_s/(L·ρ)`.
Supplies the interface gradient `G` that CG-2 ([[fab-game-cg2]]) took as a flagged knob.

**THE scope decision (advisor-affirmed, the load-bearing call):** built **closed-form, NO engine
amendment, NO ADR** — *deviating from the plan's tentative "genuine engine physics / likely an ADR"
line, invoking the plan's OWN anti-over-build clause.* Rationale: the only named consumer (CG-2's `G`)
needs the **algebraic quasi-steady interface balance**, NOT the transient free-boundary front `X(t)`;
nothing reads `X(t)`; the v1.2 oxide **receding-mesh** precedent ([[chip-coupling-v12]]) already does
moving boundaries consumer-side; and the engine's only deferred regime is **3-D**, not Stefan ([[engine-unfrozen]]).

**THE finding:** `ξ = V/G_s = V·k_s/(L·ρ·V + k_l·G_l)` **SATURATES** at `ξ_max = k_s/(L·ρ) ≈ 0.32
mm²/(K·min)` (≈**2.4× ξ_t**) as `V→∞` (or `G_l→0`) — latent heat steepens `G_s` in lock-step with `V`,
so the vacancy supersaturation is **capped**. This *corrects* CG-2's unbounded fixed-`G` `ξ=V/G`: the
in-model cost of fast pull is **bounded, not a cliff**. The melt-side gradient `G_l` (hot-zone superheat)
is the physical lever behind CG-2's hand-waved "engineer the hot zone."

**Triad (advisor — SAME honesty tier as CG-2, NO conservation law):** tight = the **two analytic
LIMITS** — V→0 (`G_s=k_l·G_l/k_s`, latent vanishes, pure conduction-matching) + V→∞ saturation (the
headline, the CG-1 `Δ=0→k₀` analogue) — + cited Si **melt-point** constants (`k_s≈22` W/m·K at `T_m`,
**NOT** the RT ~150 — the load-bearing distinction; `L≈1.79e6`, `ρ≈2330`; `k_l≈64` **flagged**, lit.
spread ~50–67, and `k_l` does NOT enter `ξ_max`). **THE TRAP (advisor caught it, my confidence was the
tell — the CG-2/[[chip-device-2d-v111]] by-construction pattern):** I proposed asserting
`k_s·G_s−k_l·G_l == L·ρ·V` as a "conservation law" — but that's the defining equation read backwards
from a `G_s` computed *by* it → a round-trip **guard, NOT an independent check**. Dropped the
"strongest triad / real conservation" overclaim. **Also dropped (advisor):** the Neumann √t transient
similarity solution — a *different* (transient half-space) scenario nothing computes against, so citing
it = decoration, not a triad leg. **Honest framing:** `G_l` is **still a house number**; CG-3 adds the
*coupling* `G_s(V)` + the *cap*, NOT first-principles `G`.

**Wired (opt-in, seam-safe):** `CzochralskiKnobs.melt_gradient_K_per_mm` → new
`interface_gradient_K_per_mm` property resolves **melt-set → Stefan `G_s` (needs pull rate); elif
thermal_gradient set → CG-2 direct; else None (off)**; **both set → raises** (two competing `G` sources).
`voronkov_ratio`/`grown_in_defect_density` route through it. Default `None` ⇒ CG-2/CG-3 off ⇒ **G1–G7 +
`demo_voronkov` byte-for-byte unchanged** (CG-2 direct-`G` path byte-identical). **Demo analytic**
(`demo_stefan`, the CG-2 discipline): 3 panels — ξ-saturation vs CG-2 runaway; the **linear** `G_s(V)`
coupling vs frozen `G`; the **bounded cost** (`poisson_yield(void(ξ), A)` *floors* under Stefan ≈0.46 vs
*collapses* to 0 under fixed `G`, the CG-2 yield consumer). `fab-game-cg3.png`. Fast lane 522→**539**
(+17: czochralski +7, `test_stefan` 6, `test_demo_stefan` 4). No engine touch, no ADR. **Deferred:**
facets/interface curvature (1-D), `G_l`'s own `V`-dependence (saturation assumes `G_l ⊥ V`), the
transient free-boundary solve. **ALL THREE CG deepenings now BUILT** — the [[fab-game]] crystal-growth
arc is complete. [[fab-game-cg1]] [[fab-game-cg2]] [[fab-game-g2]]
