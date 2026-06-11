---
name: chip-highconc-v13
description: Microchip v1.3 — concentration-dependent diffusivity D(N), the high-concentration box, BUILT 2026-06-10; the decisive finding = D(N) fits WITHIN the frozen engine (no amendment) via a consumer-side stateful-closure lagged-coefficient hook
metadata:
  node_type: memory
  type: project
  originSessionId: c438a374-74f6-4a68-a971-19a793538ac4
---

> **SUPERSEDED (numerics) 2026-06-10 by the v1.5 promotion — see [[engine-unfrozen]].** With the
> engine **unfrozen**, `D(N)` was promoted off the consumer-side lag onto the engine's **native
> nonlinear `D(u)` path** (`StateDependent` + Picard). So the now-FALSE bits below are: the
> consumer-side **holder/lagged-coefficient** mechanism (`_diffuse_dn` is now a thin step-loop over a
> `StateDependent` solver — no holder), the **`picard_iters` knob** (removed — the engine converges the
> step), "`CONTRACT.md` left untouched / the engine has no native nonlinear path" (it was **amended**:
> invariant 6, the `Not in v1` line flipped), and "no amendment / engine seal 18/18" (the engine seal is
> now 27, +9 in `test_nonlinear_d.py`). The **physics, the model, the validated/calibrated split, the
> demo numbers (0.34→0.76µm, ×42/×486), and the three advisor calls below remain accurate** — only the
> numerical *home* moved (engine, not consumer). The v1.3 narrative is kept as the build record.

Microchip **v1.3 — concentration-dependent diffusivity `D(N)` (the high-concentration box)** — BUILT
2026-06-10 (`chip/diffusion_highconc.py` + `demo_diffusion_highconc.py` + `plots.highconc_figure`;
14-test triad; chip fast lane 156 / whole-repo 163). The Phase-1 `D(N)` scope edge of
[[dopant-diffusivity-source]], **promoted** (the steel-ferrite-bay / Massoud / [[chip-coupling-v12]]
move). Microchip was already "complete" (4 phases + v1.1 Massoud + v1.2 coupling); this is the next
promotable scope edge.

**The decisive finding — `D(N)` fits WITHIN the frozen engine, NO amendment (the v1.x thesis intact).**
`D(N)` was the case **both `CONTRACT.md` ("nonlinear `D(u)` is v1.1, not built") and the plan** flagged
as needing a deliberate frozen-engine amendment + re-seal. **It needed none.** My premise "`D(N)`
requires touching the engine" was *asserted, not shown*, and the advisor's **gating** call was to spike
the cheap path first. It worked: the consumer's `_diffuse` already drives the solver **one `step()` at a
time**, so a `D(t)` callable **closing over a mutable holder of the evolving field, updated AFTER each
step**, is a **lagged-coefficient `D(N)`** entirely within the public API — when `step()` assembles its
operator at `t₁` the holder still holds `Nⁿ` (the old level), so `D` is frozen at the old state (one
tridiagonal solve/step, zero engine edits). The 20-line spike pinned it before any build: degenerate
seam `0.0` bit-for-bit, dose conserved `2e-15`, Boltzmann collapse `2e-3`. And it is **not merely a
lag**: an optional **Picard** iteration converges the within-step coefficient to a fixed point — the
**fully-implicit nonlinear backward-Euler solve** — in **~2 iterations** (pinned `2 == 6`, dt-stable).
**No ADR, no engine re-seal** (the finding obviated both); `CONTRACT.md` was deliberately **left
untouched** (its "`D(u)` not built" line stays accurate — the engine has no native nonlinear path; the
*consumer* got the lag). Engine seal re-confirmed intact 18/18. Contrast [[chip-coupling-v12]]'s OED, a
`D(t)` of *oxidation rate*; here `D` is a genuine function of the **unknown** `N`, still expressible via
the step-loop lag.

**The model (cited).** Fair charge-state diffusivity `D⁰+D⁻(n/n_i)+D⁼(n/n_i)²` (the `D⁼` `n²` term
drives the box). The full form, the B/P/As/Sb coefficient table, `n_i(T)`, the active-carrier plateau
cap, the lineage (P/Sb `D⁰` == Phase-1a intrinsic, **B the exception** at `D⁰+D⁺≈1.0/3.5` vs
`0.76/3.46`) and the Plummer Ch. 7 eqn 7.18/7.19 + **Fair & Tsai JECS 124:1107 (1977)** citations now
live in their own source note **[[dopant-charge-state-diffusivity-source]]** (split out 2026-06-10 — the
conc-enhanced counterpart of the intrinsic [[dopant-diffusivity-source]], one Fair/Plummer lineage).
Banked demo (P predep 1000°C/30min @ solubility 1.2e21): box `x_j` into 1e15 goes **0.34µm (constant D)
→ 0.76µm capped (×2.2)**, surface `D` **×42 capped**.

**Validated/calibrated split (held).** *Tight (amplitude-independent — hold for ANY `D(N)`):* the
**degenerate seam** (constant `D` through the closure == scalar engine bit-for-bit — the hook IS the
engine), **Boltzmann similarity** (`x/√t` collapse, model-independent, holds for the stiff `n²`), and
**dose conservation** with `D(N)` active. *Calibrated/approximated (flagged):* **full activation `n=N`**
(the `(n/n_i)²` magnitude is an upper bound — uncapped ×486; the active-carrier **plateau cap**
`n_active_max≈3.4e20` from Velichko gives the physical ×42 *and* the flat-top plateau shape — a
scope-edge turned feature), and the omitted built-in-**field** factor `h=1+N/√(N²+4n_i²)`.

**Three durable advisor calls (all adopted):**
1. **The gating correction (the decisive one):** spike the closure BEFORE writing the amendment the plan
   anticipated. The cheap path worked → no amendment → a more interesting finding than "amended as
   planned." Don't write an amendment until the cheap path is shown to fail.
2. **Conservation is a MACHINERY check, not physics** (the finite-volume telescoping is `D`-independent,
   so it confirms the closure didn't break structure — says NOTHING about whether `D(N)` magnitude is
   right); and Boltzmann similarity belongs on the constant-source **predep**.
3. **Don't over-claim monotonicity** — each *linear* sub-step is monotone (M-matrix, `D≥0`), but the
   *lagged nonlinear* scheme is not guaranteed monotone at a steep front (empirically no overshoot,
   `max N ≤ N_surface`; lag error first-order in dt, Picard tightens). And **benchmark honesty**:
   deliver the box **front** + deeper `x_j`; the anomalous **tail/kink is the named scope edge** —
   non-equilibrium P–V dissociation / I-injection / clustering (**Velichko arXiv:1905.10667**;
   Fair–Tsai emitter-dip; Plummer slide 22), NOT an equilibrium-`D(n)` claim. Don't ship ×486 unqualified.

**Follow-up surfaced here — now RESOLVED (commit `db79f6b`, 2026-06-10):** the standalone-flatten had
left the six sibling `chip/demo_*.py` carrying a stale `parents[2]` repo-root → they mis-saved their
banked figures one level ABOVE the repo (`M:\claud_projects\docs\figures` instead of the repo's; the
committed figures predate the flatten so it went unnoticed; README references them). Fixed all six to
`parents[1]` (matching v1.3's demo, the depth that was already correct). NOTE: `chip/tests/test_chip_notebook.py`
keeps `parents[2]` deliberately — a file in `chip/tests/` genuinely has the repo root there (commit `9bbd411`).

**Logged deferral (conscious):** `chip.ipynb` gained **no** v1.3 section (consistent with v1.1/v1.2 not
adding one). The module + 14-test triad + banked figure are the deliverable.

Part of [[bigsim-program]]; promoted per [[end-of-batch-ritual]]. The Fair charge-state pin
([[dopant-charge-state-diffusivity-source]]) extends the Phase-1a Fair `D(T)` pin
([[dopant-diffusivity-source]]) — one Fair/Plummer lineage, the `D⁰` components literally the Phase-1a
intrinsic values for P/Sb.
