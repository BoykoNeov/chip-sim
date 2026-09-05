---
name: visuals-performance-batch
description: "2026-09-05 visuals/perf batch — engine gttrf fast path (bit-identical), vectorized Abbe image, WebP thumbnails + manifest guard, tests no longer rewrite docs/figures; plan for the rest in docs/plans/visuals-performance.md"
metadata: 
  node_type: memory
  type: project
  originSessionId: c954b899-9bc2-4731-a857-24091adcd92d
  modified: 2026-09-05T15:12:03.862Z
---

**Shipped 2026-09-05** (one commit on `main`): fast lane 115 s → ~48 s wall; `demo_journey.compute()` 33.5 → 6.2 s.

- **Engine autonomous fast path** (`engines/diffusion/diffusion1d.py`): numeric D/BC/source ⇒ operator
  assembled once, `(I−θdtA)` factorized once per dt (LAPACK `gttrf`/`gttrs`). **Bit-identical** to
  `solve_banded` (same partial-pivoting elimination) — `test_fast_path.py` asserts `array_equal`
  vs the general path (reached by passing the same constant as `D(t)`). 2-D engine NOT done (plan N2).
- **Litho `abbe_image` vectorized** + `_carrier` LRU on bytes of (f_m, x); 1.2e-15 vs the old loop.
  The exact-equality "seams" in tests compare two calls of the same code, so they survive.
- **Thumbnails**: `python -m chip.thumbnails` → `docs/figures/thumbs/*.webp` + `manifest.json`
  (sha256[:16] of the source PNG + px size). Galleries emit `<img width height>` from the manifest
  (CLS 0, ~6× lighter). Guard split across `chip/tests/` and `fab_game/tests/` because **chip may
  never import fab_game** (`test_import_direction.py` — I tripped it once).
- **Speed exposed two latent test bugs**: Textual `Button` drops a click during its 0.2 s `-active`
  animation (test now waits for the class to clear); `test_demo_*` figure tests were rewriting
  committed PNGs (`chip-cmp-history.png` differs from committed on every run) — root `conftest.py`
  autouse fixture redirects `*FIGURE*` paths to tmp for `test_demo_*` modules only.

**Why:** the user asked to "improve project visuals/performance"; the honest wins were the per-step
rebuild in the engine, the Python double loop in litho, and full-size PNGs served as thumbnails.

**How to apply:** after re-banking any figure run `python -m chip.thumbnails` and commit
`docs/figures/thumbs/`. Remaining work order (N1–N8, prioritized, with commands) lives in
`M:\claud_projects\chip-sim\docs\plans\visuals-performance.md` — N1 (journey demo: `dataclasses.replace`
churn + `breakdown` brentq per die) and N2 (2-D engine fast path) are the next real wins. Measurement
files: `M:\claud_projects\temp\chip-sim-perf\`. Related: [[chip-notebook-flake]], [[engine-unfrozen]],
[[gallery-local-edition]].
