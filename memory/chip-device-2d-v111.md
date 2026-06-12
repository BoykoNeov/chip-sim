---
name: chip-device-2d-v111
description: Microchip v1.11 — the 2-D MOSFET cross-section (lateral S/D diffusion → effective channel length), a VALIDATION deepening wiring the v1.8 2-D engine into the Phase-4 device
metadata:
  type: project
---

**Microchip v1.11 — the 2-D MOSFET cross-section: BUILT 2026-06-12** (`chip/device_2d.py`, 13-test
triad [9 module + 4 demo], whole-repo fast lane **273→286**). The composition that wires the engine's
2-D regime ([[lateral-diffusion-2d]], `diffusion_2d`) into the **process→device** payoff (Phase 4,
`device`) — **no engine edit, no new ADR** (chip-local composition of two validated modules). User asked
"what more can we do"; picked the 2-D-device-cross-section direction over vector litho / small edges /
polish.

**Physics:** a self-aligned MOSFET forms its S/D with **the gate as the mask**, so the n⁺ S/D diffuses
*down and sideways under the gate edges*; the lateral encroachment `ΔL` shrinks the channel to an
**effective** length `L_eff = L_drawn − 2·ΔL`. `L_eff` feeds the drive current (`I_Dsat ∝ W/L`) while
**`V_t` stays long-channel** — short-channel rolloff / DIBL is the inherently-2-D electrostatics tar pit
(plan §5 / Phase-4 scope edge), left out.

**THE decisive finding (advisor-framed, after 3 advisor passes): this is a *VALIDATION* deepening, not
new-physics.** The independent **two-window half-cell** solve (gate centre `x=0` = a no-flux symmetry
plane, S/D window *outside* the gate `x≥L_drawn/2` sealed under the gate — exactly the right half of the
symmetric two-S/D device) reads the channel **directly**, junction-to-junction (`L_eff_true = 2·x_j`,
surface row), and **confirms** the textbook subtraction across the open range *and* the **punchthrough**
limit at `L_drawn ≈ 2·ΔL`. Its worth over "subtraction + clamp" = **physical grounding** (a real
`N = N_channel` crossing → a hard `L_eff = 0` floor at front-merge) + **independence** (a *different BC
topology* — two windows + a symmetry plane vs one semi-infinite v1.8 edge — so the agreement fails on a
config/topology bug or if superposition broke).

**Three advisor corrections that shaped it (all load-bearing):**
1. **My first two "conservation" legs were BY-CONSTRUCTION, not anchors.** `device.threshold_voltage`
   takes `channel_length_um` but never puts it in `V_t`, and `saturation_current` is literally `∝W/L` —
   so "V_t invariant to L" / "I_Dsat ratio = L_drawn/L_eff" assert unused-parameter-is-unused / a division
   restated. Reframed as **regression guards** (the device.py "Gauss leg is a self-consistency check; the
   Poisson solve is the anchor" framing; the v1.2/v1.3 "tautological" reframe). Kept (the V_t guard *is*
   the boundary-stays-clean test — fails only if someone wires DIBL in) but **billed as guards**.
2. **Build the two-window solve as the real independent anchor** (the upgrade that made it a deepening) —
   AND **don't oversell punchthrough either**: `L_drawn − 2·ΔL` with a `max(·,0)` clamp ALSO predicts
   punchthrough at `2·ΔL`, and the two-window solve lands there too → *they agree on the threshold*; the
   direct solve adds grounding + independence, NOT a different number.
3. **The advisor's predicted "smooth divergence" (true `L_eff` < subtraction near the knee) was GRID-NOISE
   empirically** (matched `nx=180`: gap ±1–3 nm, *both* signs — wrong sign for the reflection effect). I
   surfaced the data in a 3rd advisor call; advisor: *adopt the reframe, ignore my guess, don't chase a
   sub-nm number with a finer grid.* The front-interaction effect is **below the resolved scale** → named
   as the **isolated-edge/superposition approximation** scope edge, **not featured**. (Also: needs an
   **exact ΔL=0 seam**, not "negligible diffusion" — added `lateral=False`.)

**API:** `mosfet_cross_section(...)` (headline: isolated-edge ΔL + two-window solve + the device; the
exact **`lateral=False`** seam → Phase 4 **bit-for-bit**; **refuses** at punchthrough `L_eff_true ≤ 0`),
`effective_channel_um(...)` (the cheap two-window-only sweep, returns 0.0 on punchthrough), `MOSFET2D`
dataclass. Surface junction reader `_first_crossing_x` returns **0.0** when the gate centre is itself
inverted (the punchthrough detector — the earlier bug was flooring `x_j` at one cell). Isolated edge
reuses v1.8 `lateral_diffusion`; **surface** lateral reach (not v1.8's max-over-depth — the channel
inverts at the surface).

**Numbers (coherent ~0.5 µm node):** p-channel `N_A=1e17`, dry gate oxide ~11 nm, n⁺-P S/D 1000 °C/6 min →
`x_j` 0.12 µm, `ΔL` 0.10 µm (ratio 0.86); headline `L_drawn` 0.50 µm → **`L_eff` 0.29 µm (42 % shorter)**,
`I_Dsat` **×1.72**, `V_t` **0.38 V flat**; punchthrough ~0.21 µm. Grids: `nx=180/ny=140/n_steps=150`
(~0.5 s/solve); two-window L_eff accurate, punchthrough robust (a concentration crossing); the few-nm
open-regime gap is sub-grid (and not claimed).

**13-test triad:** *analytic* = exact `lateral=False` seam + two-window≡subtraction **down toward the
knee** (the genuine cross-check); *conservation* = the two by-construction **guards**; *benchmark (loose)*
= the cited lateral ratio shortening + punchthrough `≈2·ΔL`. Banked: `demo_device_2d.py` +
`plots.device_2d_figure` → `docs/figures/chip-device-2d.png` (the n⁺ S/D **curving under the gate**, the
half-cell mirrored, beside `L_eff`-vs-`L_drawn` with `V_t` flat). Cited: `L_eff = L_drawn − 2·L_{D,lateral}`
(Sze / Plummer / Taur–Ning) + [[lateral-diffusion-source]] (the lateral ratio) + [[mos-threshold-voltage-source]]
(the Phase-4 `V_t`). Plan = `docs/plans/peppy-chasing-conway.md`.
