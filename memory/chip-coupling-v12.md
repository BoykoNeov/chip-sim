---
name: chip-coupling-v12
description: Microchip v1.2 — the Phase 1↔2 back-coupling (OED + dopant segregation) BUILT 2026-06-10; both effects fit WITHIN the frozen engine; the swept-sliver scope-edge lesson — **edge RETIRED 2026-06-11 by the consumer-side moving boundary (`moving_boundary=True`); see the UPDATE block**
metadata: 
  node_type: memory
  type: project
  originSessionId: b15dfec1-90c9-4055-b898-964fda138764
---

Microchip **v1.2 — the Phase 1↔2 back-coupling (OED + dopant segregation)** — BUILT 2026-06-10
(`projects/chip/coupling.py` + `demo_coupling.py` + `plots.coupling_figure`; 19-test triad; chip gate
152 green). The named §3 deferral of both `oxidation` and `diffusion_dopant`, **promoted** (the
steel-ferrite-bay / Massoud move — yesterday's deferral becomes today's phase). Microchip was already
"complete" (4 phases + v1.1 Massoud); this is the next promotable scope edge.

**The decisive architecture finding — both effects fit WITHIN the frozen engine, no contract
amendment.** OED is a position/time-dependent `D(x,t)` (tracks oxidation rate + depth, **NOT** the
concentration `N`), so it is the engine's *already-frozen variable-`D(t)` callable* case
(`test_variable_d`) — pointedly **not** the unbuilt nonlinear `D(N)` case (that one WOULD need an
amendment; it stays the named [[dopant-diffusivity-source]] scope edge). Segregation is a time-
dependent `Neumann(flux(t))` BC. The plan said the seam was designed for this; it held.

**The model** (cited basis [[oed-source]] + [[dopant-segregation-source]]): OED
`D_eff/D_inert = 1 + f_I·Δ`, `Δ = Δ_ref·(dx_ox/dt / R_ref)^0.5` (cited half-power law; f_I B 0.30 /
P 0.38 / Sb 0.015 → enhanced B,P vs un-enhanced Sb). Segregation flux `J = N_surf·(0.44 − 1/m)·dx_ox/dt`
(cited m B 0.3 / P 10 → boron depletes, phosphorus piles up). Units = diffusion-side CGS-cm; the
oxidation rate (`oxidation.oxide_thickness`/`growth_rate`, or the v1.1 Massoud rate) consumed at the
boundary.

**Two durable advisor calls (both adopted):**
1. **The degenerate anchor is `dx_ox/dt→0`, NOT `m→∞`.** `m→∞` = oxide accepts nothing = *maximum
   pile-up*, not a sealed surface. The unified seam (both effects → plain `drive_in` bit-for-bit) is
   zero oxidation rate — the Massoud-K=0 / exoplanet-defaults pattern.
2. **The swept-sliver double-count = the named scope edge (the deep lesson).** The segregation flux
   is a **moving-*interface* mass balance run on a *non-moving* grid**: the `0.44·R` recession term
   ("dopant freed by consumed silicon") only exists if the swept region leaves the domain, but the
   fixed grid keeps it AND re-injects its dopant at the surface → **counted twice**. The decisive
   diagnostic (now a test): **`m→∞` inert-oxide** must conserve silicon dopant, yet the model
   spuriously *gains* ~10% of the dose. Consequence, OWNED in code+tests+figure: **boron depletion
   robust** (oxide-uptake-dominated, `1/m=3.3` ≫ the `0.44` double-count ≈13% — the device-relevant
   case), **phosphorus pile-up direction real but magnitude ~2× inflated** (pile-up is intrinsically
   a moving-boundary effect). The coupled "conservation" was reframed from "tight" to an **accounting
   identity** (`Si+oxide` closes for ANY flux because `oxide_uptake` is defined from the same
   bookkeeping — catches a leak, not a magnitude). Sb stays a *qualitative* ORD edge (f_I=0.015 →
   ≈1.05, a small wrong-sign residual, never a retardation number). Real fix (advance the interface /
   remap the ~1-cell swept region) = a Stefan problem the pure-diffusion engine can't express — named.
   **← this "can't express" framing was WRONG; the edge is now BUILT OUT, see the UPDATE block below.**

**UPDATE (2026-06-11) — the swept-sliver edge is RETIRED (v1.2-revision, the moving boundary).** The
"Stefan problem the pure-diffusion engine can't express" was a **consumer-side receding mesh** all
along — `engines/diffusion` **untouched** (CONTRACT/ADRs unchanged → **no new ADR**). The decisive
derivation: `J = N_surf·(0.44 − 1/m)·R` is the **correct diffusive flux at the *moving* interface**
(Leibniz on `Q_Si = ∫_{s(t)}^L N dx`, `v = ds/dt = 0.44·R`: `dQ_Si/dt = J − v·N_surf = −(N_surf/m)·R
= −C_ox·R` — silicon loses exactly the oxide's uptake, conserved); the fixed grid only omitted the
geometric `−v·N_surf` Leibniz term. The fix recedes the silicon domain to `s(t)=0.44·(x_ox − x_initial)`
each sub-step via a **truncated-first-cell `grid_from_edges` active sub-grid `[s,L]`** (deeper cells
untouched → zero bulk interpolation; conservation holds on the non-uniform grid, CONTRACT inv. 2),
keeping the **same flux** — the mesh motion supplies the missing term. Default **`moving_boundary=True`**;
`moving_boundary=False` keeps the legacy fixed-grid path as the documented "before." **Conservation
UPGRADED from the accounting identity to a real magnitude check:** the `m→∞` inert oxide now
**conserves** (gain 0.137 → ~6e-4, **O(dt)** — the lag, not a leak; `Si+oxide` identity stays
machine-exact), and `oxide_uptake` matches an **independent** `∫C_ox·R dt` within a few % (B 1.4%,
P 2.7%) and is **≥ 0 for BOTH dopants** — **phosphorus's `oxide_uptake` sign FLIPPED** (old fixed-grid
`−2.35e14` → `+6.5e13`: the oxide is always a small sink at `C_ox`; phosphorus piles up *locally* while
still ceding a little dopant). So the v1.2 "boron robust / phosphorus 2×-high / conservation-is-an-
identity" framing is **superseded**: both signatures are now quantitative (demo pile-up **×1.17→×1.06**,
boron **×0.33** unchanged; surface **receded 9.1 nm**). `CoupledResult` gains `interface_depth` +
`surface_index` (output `N` full-length, consumed cells zeroed). Tests: the `m→∞` artifact test split
into `…_conserves_with_moving_boundary` (the fix) + `…_fixed_grid_still_shows_swept_sliver_artifact`
(the "before"); +5 new (interface-recedes, moving-conserves-magnitude, uptake-tracks-`m`,
pileup-reduced-vs-fixed, seg-off-no-recession, recession-with-initial-oxide); `oxide_uptake` sign
assertions updated. Coupling suite **19→26**; whole-repo fast lane **188→195**. Advisor **timed out
twice** → proceeded on the Leibniz
derivation, verified empirically in both limits. The OED/Sb/calibrated-amplitude findings above are
unchanged. See [[engine-unfrozen]] (this did NOT use the unfreeze — it's pure consumer-side).

**Why it matters:** the validated/calibrated split held under pressure — the OED amplitude is
calibrated (flagged), and the swept-sliver magnitude error is named, but the *machinery* legs
(degenerate seam, OED ≡ effective-∫D dt, OED-alone conservation) are tight and amplitude-independent.
The honest scope-naming (boron robust, phosphorus 2×-high, conservation-is-an-identity) is the
project's whole value — the advisor's blocking call was a docs/framing fix, not a rebuild.

**Logged deferral (conscious, not silent — advisor flag):** `chip.ipynb` is "one section per phase"
and v1.2 did NOT add a back-coupling section. The module + 19-test triad + banked figure are the
substantive deliverable; a notebook interactive section (sliders: anneal T/time × dopant → the
inert/OED/coupled overlay) is a separate optional pedagogy follow-up. If picked up, the swept-sliver
honesty caveat must travel into the notebook prose too.

Part of [[bigsim-program]]; promoted per [[end-of-batch-ritual]]. Reuses the v1.1 Massoud rate as a
`dx_ox/dt` driver ([[massoud-thin-oxide-source]]) — whose Hollauer dissertation also supplies the v1.2
segregation coefficients ([[dopant-segregation-source]]), one source, two pins.
