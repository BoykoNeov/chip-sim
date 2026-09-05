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

## 2. Next — the remaining work, in priority order

Each item: *why → what → where → test → measure*. Work them top-down; each is independent.

### N1. The journey demo is still the slowest thing in the suite (~6 s; 25–33 s before)

*Why:* `fab_game/tests/test_demo_journey.py`'s module fixture runs `demo_journey.compute()` — 103
full line runs (`pipeline.run_line`) plus 56 `journey.forecast` calls. It is the fast lane's Amdahl
floor now.
*What:* profile with
```
python -c "import cProfile,pstats; from fab_game.demo_journey import compute; cProfile.run('compute()','p'); pstats.Stats('p').sort_stats('tottime').print_stats(15)"
```
and attack the top two entries, which today are (a) `dataclasses._replace` — 61 k calls from
per-die state updates in `fab_game/pipeline.py` / `state.py` (batch the per-die updates into one
`replace` per wafer, or keep per-die scalars in NumPy arrays and build the dataclasses once at the
end); (b) `chip/breakdown.py::_ionization_integral` — 95 k calls through `scipy.optimize.brentq`
(`f_raise`): the breakdown voltage is solved per die although the die's doping is one of a handful
of distinct values per wafer — memoize `breakdown_voltage` on its float inputs (`functools.lru_cache`
on a thin wrapper, keyed on rounded inputs is NOT acceptable — key on the exact floats).
*Test:* the whole `fab_game/tests/` tree; nothing may change numerically (compare
`demo_journey.compute()` results before/after with `array_equal` on every array field).
*Measure:* `demo_journey.compute()` wall; target ≤ 3 s.

### N2. The 2-D engine has no fast path yet (`engines/diffusion/diffusion2d.py`)

*Why:* the same rebuild-and-solve-per-step pattern; consumers are `chip/device_2d.py` (the 4.2 s
`test_demo_device_2d` fixture), `chip/lateral_diffusion*`, `chip/locos_history.py`.
*What:* mirror 1a — detect autonomy in `__init__`, cache the assembled sparse operator, and cache
the factorization per `dt` (`scipy.sparse.linalg.splu` on the 5-point matrix; keep the current
solver for the general path). Verify bit-identity is NOT guaranteed here (a different sparse
solver reorders); if `splu` is not what the current path uses, assert `allclose(rtol=1e-12)` and
say so in the test docstring, mirroring `test_fast_path.py`.
*Test:* `engines/diffusion/tests/test_diffusion2d.py` + a new `test_fast_path_2d.py`; the v1.8/v1.11/B5
chip tests.
*Measure:* `chip.demo_device_2d.compute()` wall (4.2 s today).

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

### N6. `engines/diffusion` step overhead for tiny grids is now Python, not LAPACK

*Why:* after 1a a 400-cell step is ~7 µs, of which ~5 µs is Python (`np.asarray`, shape checks,
the `flux()` diagnostic that `chip.diffusion_dopant._diffuse` calls every step).
*What (only if N1/N2 are done and the lane still floors on diffusion):* add
`Diffusion1D.march(state, dt, n_steps)` that runs the loop in one call, accumulating the boundary
flux without re-validating per step, and switch `_diffuse` to it. Same bit-identity test pattern
as `test_fast_path.py`.
*Measure:* `chip.demo_junction.compute()` wall.

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

### N8. Retire the `outputs/` duplicate write

*Why:* every demo writes each figure twice (`DOCS_FIGURE` and `OUTPUT_FIGURE` under the git-ignored
`outputs/`); the second write costs ~0.4 s per figure for the larger ones and nothing reads it.
*What:* grep `OUTPUT_FIGURE` across `chip/demo_*.py`, `fab_game/demo_*.py`; drop the second target
and the constant; update `docs/decisions/0002-visualization-and-ux.md` if it names `outputs/`.
Check `.gitignore` and the READMEs for `outputs/` mentions.
*Test:* the `test_demo_*` figure tests (they assert `save_figure(...)` returns an existing file).

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
