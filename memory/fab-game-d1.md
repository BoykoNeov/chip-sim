---
name: fab-game-d1
description: "project (2026-06-14): D1 BUILT — under-etch (etch_deposition.py §3); incomplete clear → residual=UE·film → bridges adjacent gate lines into a functional SHORT (mirror of the deposition void's OPEN); closes G5's named over/under-etch pair"
metadata: 
  node_type: memory
  type: project
  originSessionId: e06638ba-b41b-4350-a5e3-109ddf86c5ad
---

**D1 BUILT (2026-06-14)** — **under-etch**, the second **scope-edge-backlog** promotion ([[scope-edge-backlog]])
and the completion of [[fab-game-g5]]'s named "over/under-etch" pair. Bundled with [[fab-game-c1]] as "two
quick, high-confidence deepenings."

**The model (the MIRROR of over-etch):** G5 built the over-etch leg (etch past endpoint → undercut → CD
shrink, a parametric/**OPEN** failure). D1 builds the mirror: an **incomplete clear** (`under_etch_frac>0`)
leaves **residual film** `residual = UE·film` in the gaps, which **bridges** adjacent gate lines into a
functional **SHORT** once it exceeds a (flagged) thickness threshold — the dual of the deposition void's open.

**New physics `chip/etch_deposition.py` §3** (closed-form, NO engine, same flagged tier as G5 — NO
conservation law):
- `under_etch_residual(film, UE) = film·UE` — exact algebra; `UE=0` ⇒ 0 **bit-for-bit** (the seam).
- `residual_bridges(residual, threshold=BRIDGE_RESIDUAL_THRESHOLD_NM≈20nm)` → `residual > threshold` — a
  **FLAGGED house threshold** (only the direction "thicker residual → continuous short" is cited; thin
  residual is discontinuous / cleared by the over-etch margin → harmless).
- `under_etch(film, UE) → UnderEtchResult(residual_nm, bridge_threshold_nm, bridged)` — the bundle,
  mirroring `deposit_fill`. `test_etch_deposition.py` +5.

**Triad = the G5 flagged-phenomenology tier:** tight = the SEAM (`UE=0` ⇒ residual 0 exact ⇒ no bridge);
machinery = the residual algebra (a regression GUARD, not an anchor); the bridge-threshold magnitude is
house. The forms are cited (Wolf & Tauber / Plummer–Deal–Griffin — already the etch module's basis).

**`fab_game` wiring:** `EtchDepositionKnobs.under_etch_frac` (0 = full clear, the seam) + a **`__post_init__`
mutual-exclusion guard** (setting both `over_etch_frac` and `under_etch_frac` >0 RAISES — one etch can't
over- AND under-shoot endpoint; mirrors CzochralskiKnobs' two-G guard). New `Die.bridged` field (like
`voided`); `spec.verdict` treats `bridged is True` as a functional fail (parallel to the void gate); the
etch step computes residual/bridge **independent** of the over-etch/void path (deterministic — **NO per-die
RNG draw**, so the stream-alignment tests like `test_etch_sigma_off_draws_no_rng` are untouched); `diagnose`
names the under-etch bridge. `cd_nm` is UNCHANGED by under-etch — it is a purely **functional** kill (not a
CD/parametric shift), the contrast with over-etch.

**Seam:** `under_etch_frac=0` (default) → residual 0, nothing bridges → G1–G6 banked demos byte-for-byte.

**Banked `demo_under_etch`/`fab-game-d1.png`** (3 panels): residual vs UE per film (+ threshold) | the
bridging cliff yield 100%→0% at UE≈0.13 (film 150nm, CD flat) | **the etch PROCESS WINDOW** — a signed
etch axis (under-etch ← endpoint → over-etch) at A=0.96, a Goldilocks window `[−0.12, +0.43]` bracketed by
a **short** (left) and an **open** (CD collapse, right) — the payoff of having both legs (why over-etch
margin exists, and why too much is its own failure). `test_etch.py` +4 + `test_demo_under_etch.py` (4).
Full suite 572 green. **Named-deferred (anti-over-build):** under-etch rework (re-etch-to-clear risks the
over-etch CD-shrink — a teachable irreversibility, not built), per-die under-etch non-uniformity.
[[fab-game]] [[fab-game-g5]] [[scope-edge-backlog]]
