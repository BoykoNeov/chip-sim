# Visuals & performance — what shipped, what is left, and how to do the rest

*Written 2026-09-05. The first batch is committed; the "Next" section is a work order a
less-experienced engineer (or a smaller model) can execute item by item. Every item names the file,
the exact change, the test that proves it, and the number to re-measure.*

## 1. What shipped in the first batch (2026-09-05)

Measured on the dev box (16 logical cores, `-n auto` → 8 workers). "Before" is commit `d5fb09a`.

| Measure | Before | After | How measured |
|---|---|---|---|
| Fast lane wall (`pytest -m "not slow" -n auto`) | 115 s | ~48–64 s | `date` around the run, `M:\claud_projects\temp\chip-sim-perf\*.txt` |
| `fab_game.demo_journey.compute()` | 33.5 s | 6.2 s | `time.perf_counter()` around one call |
| `fab_game.demo_voronkov.compute()` | 17 s | 2.6 s | same |
| `fab_game.demo_game.compute()` | 12 s | 2.4 s | same |
| One engine step (400 cells, backward Euler) | ~60 µs | ~7 µs | 600-step march, see `test_fast_path.py` header |
| One Abbe image (21 source pts, 31 orders, 512 px) | 5.4 ms | 0.5 ms (0.05 ms cached carrier) | `timeit` in a shell |
| Physics-gallery image bytes for one page load | 3.3 MB | ~0.55 MB | `performance.getEntriesByType('resource')` in Chrome |
| Cumulative layout shift while the gallery loads | visible (cards collapse then jump) | 0 | `layout-shift` PerformanceObserver total |

### 1a. Engine — the autonomous fast path (`engines/diffusion/diffusion1d.py`)

When nothing in the operator depends on time or on the field (numeric `D`, numeric BC parameters,
numeric/absent source) the tridiagonal operator is assembled **once** and the implicit matrix
`(I − θ·dt·A)` is **factorized once per dt** (LAPACK `gttrf`), each step then being one `gttrs`
back-solve. It is **bit-identical** to the old per-step `solve_banded` (same partial-pivoting
elimination) — `engines/diffusion/tests/test_fast_path.py` asserts `array_equal` against the general
path for every scheme × BC family. Anything time- or field-dependent (`D(t)`, `StateDependent`,
ramped BCs, `S(t)`) takes the old path untouched. Cached arrays are read-only.

### 1b. Lithography — the vectorized Abbe image (`chip/litho.py`)

`abbe_image` used to loop over source points and, inside, over orders, one `np.exp` per pair.
It now builds the carrier matrix `exp(2πi·f_m·x)` once (memoized on the bytes of `f_m` and `x`,
`_carrier`, LRU 64) and forms every source point's coherent field as one matrix product. Max
relative deviation from the old loop: 1.2e-15 (summation order). The bit-for-bit *seams* the
tests pin (z=0 vs no defocus, `Aberrations()` vs `None`) compare two calls of the **same** new code,
so they still hold exactly.

### 1c. Test hygiene that the speed-up exposed

* `fab_game/tests/test_tui.py` — Textual's `Button` ignores a click while its 0.2 s pressed
  animation is on. A turn used to take seconds, hiding this; once the line got fast, the second
  back-to-back click on *Process* was silently dropped. The test now waits for the `-active` class
  to clear between clicks (a helper inside the test).
* `conftest.py` — for `test_demo_*` modules, every `*FIGURE*` path of every imported demo module is
  redirected to `tmp_path`, so the suite no longer rewrites committed `docs/figures/*.png` (it did:
  `chip-cmp-history.png` came back different after every run).
* `chip/tests/test_demo_{highk,beol,strain}_history.py` — `compute()` once per module (fixture `r`),
  matching the cmp/voronkov/game modules.

### 1d. Visuals — thumbnails, declared image boxes, page metadata

* `chip/thumbnails.py` — `python -m chip.thumbnails` cuts a 760-px WebP (q=80) of every
  `docs/figures/*.png` into `docs/figures/thumbs/` and writes `manifest.json` (source hash + pixel
  size). Pillow (matplotlib's own dependency) is used only to *build*; reading is pure Python.
* All four pages (`chip/gallery.py`'s `figure_img`) now display the thumbnail with
  `width`/`height` declared and link the full PNG. `head_meta` adds `description`, `color-scheme`,
  `theme-color`, and (public editions only) Open Graph tags with a representative figure.
* Guards: `chip/tests/test_thumbnails.py` (physics / era / roadmap pages) and
  `fab_game/tests/test_thumbnails.py` (the game page) — missing, stale (re-banked PNG), oversized,
  or wrong-aspect thumbnails fail the fast lane. Split across the two trees because `chip` may
  never import `fab_game` (ADR 0005 §2; `test_import_direction.py` enforces it).

**Workflow change for maintainers:** after re-banking any figure, run `python -m chip.thumbnails`
and commit `docs/figures/thumbs/` alongside the PNG (the guard tells you so).

### 1e. The second batch (2026-09-06) — the journey demo, and two items closed by measurement

Working N1 and N2 top-down produced one optimization and **two negative results**, all three written
back into §2 in place rather than deleted:

* **N1 shipped** — `abbe_image` and `junction_breakdown` are memoized on their exact arguments. The
  journey demo does **1.43× less CPU work** (22.5 → 15.7 s cpu, interleaved). Both are bit-identical
  by construction and guarded by tests. The plan's two named targets were *not* the top two, and its
  ≤ 3 s goal is retired as unreachable without changing what the demo computes.
* **N2 was already done** — the 2-D engine has cached its operator and its per-`dt` factorization
  since v1.8. 97% of its wall is the sparse back-solve itself. *This is the fourth gate in this repo
  found already-released by someone going to build it* (`future-steps.md` records the other three) —
  and, as with those, no test would ever have told us; only reading the file did.
* **N6 is not worth building** — the `march()` ceiling is 19%, not the ~70% the item assumed.

The lesson worth keeping: **a work order written from a profile is a hypothesis, not a task list.**
Every number in §2 that was carried over rather than re-measured turned out to be wrong, in both
directions. Re-measure the item before you build it.

## 2. Next — the remaining work, in priority order

Each item: *why → what → where → test → measure*. Work them top-down; each is independent.

### N1. The journey demo is still the slowest thing in the suite — **DONE 2026-09-06 (1.43× less CPU work), and the plan's two named targets were the wrong two**

*Why:* `fab_game/tests/test_demo_journey.py`'s module fixture runs `demo_journey.compute()` — 103
full line runs (`pipeline.run_line`) plus 56 `journey.forecast` calls. It is the fast lane's Amdahl
floor now.

**What the profile actually said.** The two entries this item named — `dataclasses._replace` (61 k
calls) and the breakdown root-find (95 k `_ionization_integral` calls) — are real, but they are not
the top two. Ranked by cumulative time in `cProfile` on `compute()`:

| | cumtime | calls |
|---|---|---|
| `chip/litho.py::abbe_image` | **2.05 s** | 6 527 |
| `engines/diffusion` `step` + `flux` | 2.51 s | 152 400 |
| `dataclasses._replace` | 1.08 s | 61 394 |
| the breakdown `brentq` solve | ~0.73 s | 95 037 integrals |

The engine's share turned out to have almost no headroom (see the closed N6 below — 19%, measured),
so the whole of the win is in the **first** row, which this item never mentioned.

**The finding under it: the journey asks the same questions over and over.** Instrumenting the run:

```
abbe_image          6527 calls ->  694 distinct argument sets   (9.4x redundancy)
junction_breakdown  6527 calls ->   37 distinct argument sets   (176x redundancy)
```

Both are **pure functions**: the line is run 103 times over one wafer's dies, and most dies re-ask
for an image of the same grating through the same lens, and for a breakdown reading at one of a
handful of doping/depth pairs. Nothing was wrong with either computation — they were simply being
recomputed.

*What shipped:*

* `chip/litho.py` — `abbe_image` is memoized on its **exact** arguments (bytes for the two arrays, the
  frozen `Imaging`/`Aberrations` dataclasses as themselves, `orders` normalized to a tuple of
  `(float, complex)`), LRU 1024. The cached master is read-only and **every call returns a fresh
  copy**, so a consumer that normalizes its image in place (`litho.py` §9 does exactly that) cannot
  reach another caller's hit. `abbe_image.cache_clear()` / `.cache_info()` are exposed on the public
  name. Guarded by `chip/tests/test_abbe_cache.py`: bit-identity against the uncached body on every
  keyed axis, the in-place-mutation isolation test, and that the v1.4/v1.10 degenerate seams (`z=0`,
  `aberrations=None`) still land on the *same* cache entry as the plain call.
* `chip/breakdown.py` — `junction_breakdown` is `lru_cache`d on its exact `(N_B, x_j_um)` floats
  (**not** rounded; rounding would make a hit a different root-find). `JunctionBreakdown` is a frozen
  dataclass, so the shared instance needs no copy. Three tests added to `test_breakdown.py`.

*Measure.* Wall clock on this box is unusable right now — the machine sat at 100% CPU from other
processes, and the same unchanged `compute()` measured anywhere from 6.2 s to 23 s. **CPU time is the
machine-state-independent number**, taken interleaved (base / cached / base / cached in one process,
so drift cancels):

```
base (both caches bypassed)      22.5 s cpu   1.00x
+ abbe_image memoized            16.6 s cpu   1.36x
+ junction_breakdown memoized    15.7 s cpu   1.43x
```

Reproduce with `M:\claud_projects\temp\chip-sim-perf\ab4.py`. Scaled onto the 6.2 s wall this demo
showed on a quiet box, that is **~4.3 s**.

**The ≤ 3 s target is retired, not met.** It assumed one or two dominant costs; after the caches the
run has no dominant cost left — the largest remaining single line is the engine march at ~15% with a
measured 19% ceiling (N6). Getting materially below ~4 s means changing *what the demo computes*
(fewer line runs, fewer forecast points), which is a content decision, not a performance one.

*Left on the table, deliberately:* `dataclasses._replace` (61 k calls, ~1.08 s cumulative in the
profile ⇒ well under 1 s real). The plan's suggestion — batch the per-die updates into one `replace`
per wafer, or hold per-die scalars in NumPy arrays and build the dataclasses at the end — is a
refactor of `fab_game/pipeline.py` + `state.py`, i.e. game logic, for a fraction of a second. Not
worth the regression risk against the two caches already banked; revisit only if the die count grows.

### ~~N2. The 2-D engine has no fast path yet~~ — **PREMISE FALSE (checked 2026-09-06). Nothing to do.**

This item was written from the assumption that `diffusion2d.py` repeats the 1-D module's
rebuild-and-solve-per-step pattern. **It never did.** The 2-D engine has had the whole of item 1a
since it was built (v1.8), by construction rather than as an optimization:

* `Diffusion2D.__init__` assembles the sparse 5-point operator **once** into `self._A` — it is
  backward-Euler-only with a time-independent `D`, so there is no per-step operator to rebuild and no
  autonomy test to write. Only the inhomogeneous `b` (Dirichlet values, Neumann fluxes, source) is
  rebuilt per step, which is what a time-dependent BC requires.
* `_factor(dt)` already caches `splu(I − dt·A)` in `self._lu_cache`, keyed by `dt` — exactly the
  "factorize once per dt, back-solve per step" shape 1a added to the 1-D module.

So there is no cache to add. Where the time actually goes (`cProfile` on
`chip.demo_device_2d.compute()`, 180×140 grid, 150 steps × 14 solver instances = 2100 steps):

| | tottime | calls |
|---|---|---|
| `SuperLU.solve` (the back-solve itself) | **4.56 s** | 2100 |
| `_superlu.gstrf` (the 14 factorizations) | 0.93 s | 14 |
| all engine Python (`step`, `_b_vector`, `_edge_cells`, …) | **0.19 s** | — |

The Python overhead this item wanted to remove is **3% of the wall**. The cost is the sparse
back-solve, which is real numerical work.

**The one lever that is left, and why it is not taken here.** `splu` defaults to `permc_spec="COLAMD"`,
a fill-reducing ordering for *unsymmetric* matrices; this matrix has a symmetric sparsity pattern.
Measured on the demo's own operator:

```
COLAMD          factor  48.6 ms   solve  1.51 ms   nnz(L+U) 2,029,664   (today)
MMD_AT_PLUS_A   factor  30.6 ms   solve  0.93 ms   nnz(L+U) 1,096,444   (1.6x, 1.85x less fill)
MMD_ATA         factor  50.7 ms   solve  1.44 ms   nnz(L+U) 1,953,632
NATURAL         factor 310.4 ms   solve  9.29 ms   nnz(L+U) 7,067,478
```

`MMD_AT_PLUS_A` would take the demo from ~5.9 s to ~4.5 s. It is **not** bit-identical — a different
elimination order is a different rounding — and the 2-D consumers carry tight absolute tolerances
(`test_diffusion2d.py` asserts the x/y isotropy of a spreading blob to `1e-12`, and the 2-D↔1-D
reduction to `1e-12`). Those are *physics* pins, not cache pins, so loosening them to buy 1.4 s is a
bad trade and this plan does not authorize it. If someone wants the 1.4 s: change the ordering, run
`engines/diffusion/tests/`, and if a `1e-12` trips, the honest move is to leave the ordering alone —
not to widen the tolerance.

*Status:* closed, no code change. The 4.2 s quoted below was a `--durations` line, not a
`compute()` wall; measured directly the demo is ~5.9 s (min of 3), on a box that was 100% busy.

### N3. Blurbs on the later gallery cards are paragraphs

*Why:* the B9/B10/B11 blurbs in `chip/gallery.py` `DEEPENINGS` run 6–10 lines inside a 330-px card
(see `docs/index.html`, the last three cards). They are kept verbatim with the README catalog on
purpose, so do not shorten the text.
*What:* clamp visually — in `_STYLE` add `.blurb { display:-webkit-box; -webkit-line-clamp: 5;
-webkit-box-orient: vertical; overflow: hidden; }` and wrap each long blurb in a `<details>` whose
`<summary>` shows the clamped text and whose open state shows all of it (pure HTML/CSS, no JS).
Apply the same in `fab_game/gallery.py` (it reuses `_card`, so the change lands automatically) and
check `chip/history_gallery.py`'s `.story .v` cells, which have the same problem for B11.
*Test:* regenerate all eight HTML files (`python -m chip.gallery && python -m fab_game.gallery &&
python -m chip.history_gallery && python -m chip.roadmap_gallery`); the golden tests then pass;
add an assertion in `test_gallery.py` that every blurb text is still present verbatim in the page.
*Measure:* open `docs/index.html` in a browser at 1280 px wide — every card row aligns.

### N4. `srcset` for high-density displays and narrow phones

*Why:* the 760-px thumbnail is 2× the desktop card width, but on a phone at full width and 3× DPR
it is upscaled.
*What:* in `chip/thumbnails.py` cut a second size (1140 px) and in `figure_img` emit
`srcset="…-760.webp 760w, …-1140.webp 1140w" sizes="(max-width: 700px) 100vw, 364px"`. Keep the
manifest schema backward compatible (add a `variants` list). Update both `test_thumbnails.py`.
*Measure:* image bytes per page load stays under 1 MB on desktop (Chrome DevTools → Network → Img).

### N5. Figure banking costs one full matplotlib font-cache warm-up per fresh process

*Why:* the first figure in a fresh interpreter can take seconds (once observed at 100 s in a serial
run while the machine was busy — a font-cache rebuild). Every demo pays it; xdist pays it per
worker.
*What:* check `~/.matplotlib/fontlist-*.json` exists and is current on the CI runner (cache the
`~/.matplotlib` directory in the workflow with `actions/cache`), and in `chip/plots.py` pin the
font family to one that ships with matplotlib (`DejaVu Sans`) so the font manager never scans
system fonts for a fallback.
*Test:* none needed; *Measure:* `python -X importtime -c "import matplotlib.pyplot"` and the time
of the first `fig.savefig` in a fresh process (`chip/demo_junction` end to end).

### ~~N6. `engines/diffusion` step overhead for tiny grids is now Python, not LAPACK~~ — **NOT WORTH BUILDING (measured 2026-09-06).**

The premise was "a 400-cell step is ~7 µs, of which ~5 µs is Python", so a `march()` that hoists the
validation and the per-step `flux()` out of the loop would recover most of it. The 7 µs is right; the
**5 µs is not**. Measured against a hand-hoisted loop that keeps only the three lines that do work
(`rhs = u + dt·b`; the `gttrs` back-solve; the closed-form Dirichlet flux), on 600 steps × 400 cells:

```
step() + flux() loop, as _diffuse runs it     7.24 us/step
step() only (flux removed entirely)           6.34 us/step
fully hoisted (the march() ceiling)           5.85 us/step   -> 19%, bit-identical
```

**19% is the entire ceiling**, and half of it is deleting the `flux()` call that the consumer actually
needs (`_diffuse` returns `Σ dt·flux(left)` as `surface_flux_dose` — the conservation diagnostic the
predep dose identity is checked against, so it is load-bearing, not a diagnostic that can be dropped).
The remaining ~1.4 µs/step is `np.asarray`, the shape check and the cache lookups. What the 7 µs
mostly *is*: the `rhs` allocation and the f2py call into `gttrs` — real work and scipy's own call
overhead, neither of which a `march()` removes.

On the fab-line journey (152,400 engine steps, the largest call count in the profile) 19% of the
engine's share is **~0.25 s of a ~6 s wall**. That does not pay for a new public engine method whose
signature has to carry the flux accumulation. *Closed: measured, negative, no code change.*

### N7. Gallery pages — small polish items (do in one pass)

* `docs/*.html` have no favicon; add an inline SVG data-URI `<link rel="icon">` in `head_meta`
  (a wafer disc in the accent colour).
* The dark theme shows figures as bright white tiles (`--shot-bg` is white in both themes). Leave
  the figures white (they are PNGs with white backgrounds) but soften the tile: give `.shot` a 1-px
  inner border of `var(--line)` and 4-px radius so the white reads as a framed image, not a hole.
* Add `<link rel="canonical">` to the public editions pointing at
  `https://boikoneov.github.io/chip-sim/<page>.html` (the local editions get none — keep the
  "local has no remote reference" tests green).
*Test:* regenerate the eight pages; golden tests. Check both themes in a browser.

### ~~N8. Retire the `outputs/` duplicate write~~ — **DONE 2026-09-06, and the second write was costing more than this item claimed**

*Why:* every demo wrote each figure twice — `DOCS_FIGURE` (committed, displayed by the galleries) and
`OUTPUT_FIGURE` under the git-ignored `outputs/`, which **nothing reads**: no test, no gallery, no
notebook, no README. The duplicate was a leftover from before `docs/figures/` became the bank.

**What it actually cost.** This item estimated "~0.4 s per figure for the larger ones". Timed on the
`savefig` calls alone (the figure build excluded, matplotlib warm), one write of the larger figures is:

| figure | one write | size |
|---|---|---|
| `fab-journey.png` | 0.89 s | 583 kB |
| `chip-cmp-history.png` | 1.37 s | 437 kB |
| `chip-beol-history.png` | 1.05 s | 472 kB |
| `chip-junction.png` (a small one) | 0.37 s | 135 kB |

and the second write costs **the same again** — repeated `savefig` of the *same* `Figure` object
measured 0.46–1.8 s per call with no downward trend, because `savefig` re-renders the canvas through
the Agg backend every time. It is not a file copy, so there was no caching to make the duplicate cheap.
The estimate was low by roughly 2–3× on the big figures; the honest figure is **~0.4 s (small) to
~1.4 s (large) per demo**, paid by every demo run and every figure re-bank.

*What was done:* 48 `OUTPUT_FIGURE*` constants and their 48 two-target save loops removed across 45
demo modules (`chip/demo_*.py`, `fab_game/demo_*.py`), each loop collapsed to the single write it was
already returning. `chip/demo_implant.py` carries **four** figures and was checked individually. All 48
loops were byte-identical in shape and every `savefig` used `dpi=130`, so the collapse is mechanical
with nothing per-file to decide.

*What was deliberately left alone:*
* `conftest.py`'s `_bank_test_figures_in_tmp` matches attribute names by the **pattern** `"FIGURE" in
  attr`, not by a list of names, so it needed no change — only its docstring, which named the retired
  constant. That pattern is why the removal could not silently un-protect the committed PNGs.
* `.gitignore`'s `outputs/` line stays: the directory is still git-ignored local state, and an ignore
  rule for a path nothing writes costs nothing.
* `docs/plans/historical-modes-a1.md` mentions `outputs/` twice — a **historical plan record** of what
  A1 did at the time. Left verbatim; this repo annotates its history rather than rewriting it.
* No ADR or README named `outputs/` (grepped), so nothing else moved.

*Test:* the `test_demo_*` figure tests pass (215 selected by `-k demo_`). The discriminating check is `git status` afterwards
showing **no** `docs/figures/*.png` — the demos were never run by hand, only under the conftest
redirect, so no committed PNG was rewritten and the thumbnail drift guard stayed green.

## 3. Numbers to keep honest

Re-measure after each item and update §1's table (the numbers are the point of the plan):

```
# fast lane wall
python -m pytest -m "not slow" -n auto -p no:cacheprovider --durations=15
# the three game computes
python -c "import time; from fab_game.demo_journey import compute; t=time.perf_counter(); compute(); print(time.perf_counter()-t)"
# page weight: serve docs/ and read the Network panel, or in the console:
#   performance.getEntriesByType('resource').filter(e=>e.initiatorType==='img').reduce((a,e)=>a+e.encodedBodySize,0)
```

**Measure CPU time, interleaved, when the box is not idle.** Every wall number above is only
meaningful on a quiet machine. During the 2026-09-06 batch the box sat at 100% CPU from unrelated
processes and the *same unchanged* `compute()` measured 6.2 s, 11.9 s and 23.3 s across the session —
a spread far larger than any optimization being evaluated, which briefly made a real 1.36× win look
like 1.03×. Two rules that made the numbers trustworthy again:

1. **`time.process_time()`, not `time.perf_counter()`.** CPU time counts the work this process did,
   so a busy neighbour no longer lands in the measurement. (It is not perfectly immune — a downclocked
   core inflates it too — which is why rule 2 matters.)
2. **Interleave A and B in one process** (`base, cached, base, cached, …`, `min` over reps) rather
   than timing two separate runs. Drift then cancels between neighbouring samples instead of being
   attributed to the change. `M:\claud_projects\temp\chip-sim-perf\ab4.py` is the harness; it patches
   the cache off and on and prints wall and cpu side by side, which is also how you *see* that the box
   is lying to you (wall and cpu disagreeing by 2× is the tell).

Before trusting any before/after in this document, check `(Get-CimInstance Win32_Processor).LoadPercentage`.
