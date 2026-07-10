# Plan — Chunk A1: pre-implant diffusion doping (the dose-control wall)

## Context

Parent plan: `docs/plans/historical-modes.md` (the **backward axis** — re-running modelled processes in
their period-limited modes so the limitation explains why the modern version won). The user chose **A1
first** (over H0, the display surface) — A1 is a **Tier-1** chunk: it has a *real* consumer already
(contrast with the just-finished ion-implant plan) and, like every physics feature here, ships its own
`chip/demo_*.py`, so it surfaces in the glob-anchored physics gallery **with no history page needed**.
H0 (the era surface) comes later, then debuts justified by *real* content (implant + A1), not one
recycled figure — the anti-over-build ordering the advisor flagged and the user endorsed.

**The discriminating observable (A1's licence), stated first — and it is NOT a repeat of `demo_implant`:**
`demo_implant` shows the same dose laid two ways (surface-peaked erfc vs buried Gaussian) — a *depth/
topology* contrast — and to "match" a light 5e11 V_t-adjust dose by predep it **tunes `N_s` far below the
solid-solubility limit** (`demo_implant.py:122`, `N_s = DOSE/(1.128·√(Dt))`). But `N_s` is **physically
pinned to solid solubility** (`Dopant.N_solid_solubility`, a Trumbore material constant, not a free knob —
`diffusion_dopant.py:110-124`). **A1 is the honest accounting of that cheat:** at the solubility-pinned
surface, thermal predep **cannot reproducibly meter a light, precise dose**. To lay Q = 5e11 cm⁻² of boron
at the true surface N_s = 3e20 needs `√(D·t) = Q/(1.128·N_s)` → a **sub-millisecond predep**
(uncontrollable on the steep √t curve). Ion implantation meters dose electrically (beam charge / Faraday
cup), **decoupled from temperature and from depth** — so the light V_t-adjust / retrograde doping regime
is reachable *only* by implant. That dose-control wall — not depth — is the discriminator, and it is
exactly what modernised the ~1968 predep planar line (the parent plan's era spine: predep → implant).

**Honesty label (corrected — this is the load-bearing claim):** the dose-control wall is a
**FLAGGED-magnitude leg**, *not* a structural/tight one. `predep_dose_floor = 1.128·N_s·√(D(T)·t_min)` is
a **controllability proxy** (the real limit is reproducibility/uniformity on the steep √t curve, not a
hard thermodynamic floor), and its sign against the V_t-adjust dose depends on both `T_predep` and the
house `t_min`. Worked box for boron (N_s = 3e20): 900 °C/1 s → Q_min ≈ 1e13; 800 °C/1 s → ≈ 2e12;
800 °C/0.1 s → ≈ 7e11. Against a **5e11** target the wall holds across that box **with margin**; a 1e12
target or a smaller `t_min` would flip it. So the honest claim is: *sign-robust only across an explicit
(T_predep, t_min) box, stated in the demo* — and the demo must pick its V_t-adjust target (5e11, which has
margin) accordingly. Only the **predep dose identity** and the **seam** are tight legs (below); the wall
is flagged, its sign verified across the stated box at build. (This corrects the parent doc's looser
"dose∝depth can't decouple" framing — the two-step process *can* partly decouple Q from x_j, so depth is
NOT the wall; dose *controllability* is.)

The historical *variations* the user asked for ride along as the **source registry**: the classic predep
sources (POCl₃, BBr₃/BN, spin-on-glass) each establish the surface at (or, for a finite source, below)
solubility — none low enough for a light dose. That is the period texture *and* the limitation in one.

## Approach (recommended)

**Pure additive consumer module — no engine change, no change to any existing behaviour** (the seam is
trivially intact: A1 imports and reuses the predep/drive-in/range-statistics machinery; nothing existing
is touched). Mirrors the precedent of `chip/diffusion_highconc.py` (a separate-concern module over
`diffusion_dopant`) and the `demo_*` idiom (`chip/demo_implant.py`).

### New — `chip/doping_history.py` (the physics/registry, a consumer of `diffusion_dopant`)

- `@dataclass(frozen=True) DopingSource`: `name`, `species` (a `DOPANTS` key), `source_type`
  (`"constant"` = unlimited/Dirichlet → erfc, vs `"limited"` = finite deposited dose → Gaussian
  drive-in), `surface_conc` (cm⁻³ — for constant sources the cited period surface value, ≈ the dopant's
  the species' `Dopant.N_solid_solubility`; for the limited source, `None` — dose-set instead).
  **Constant sources must *reference* `DOPANTS[species].N_solid_solubility` (the same float), never a
  re-typed literal** — otherwise the bit-for-bit seam (below) silently drifts (the same duplicated-
  source-of-truth the gallery's figure-introspection exists to prevent). A small **cited** registry
  `SOURCES`: POCl₃ (P, constant, solubility), BBr₃ or BN (B, constant, solubility), spin-on-glass
  (B or P, limited source). **Honest framing:** the *one* real physics axis is **constant vs limited
  source**; POCl₃ and BBr₃ are both constant-at-solubility and differ *only in species* — the limitation
  is identical. The three entries are period **texture**, not three-way discrimination — say so in the
  module docstring. Validate `source_type`/species in `__post_init__` (the established idiom).
- `predep_dose_floor(source, *, T_predep, t_min_s)`: the **controllability proxy** for the minimum dose a
  constant source can reproducibly lay — `Q_min = 1.128·surface_conc·√(D(T_predep)·t_min)` (reuse
  `diffusion_dopant.predep_dose`). NOT a thermodynamic limit — a stand-in for reproducibility on the steep
  √t curve; `t_min` and `T_predep` are FLAGGED house inputs. The wall (`Q_min >` the V_t-adjust dose)
  holds by *sign across the stated (T_predep, t_min) box*, not as an exact number.
- `implant_dose_reach()`: implant meters any `Q` (electrical), independent of `T`/depth — the register
  of the decoupled knob (dose × energy), reusing `range_statistics`. The A1 discriminator is the pair:
  predep's dose **floor** vs implant's **arbitrary-low** metered dose.
- `run_source(grid, source, recipe)`: lay a source's profile the honest way — constant → `predeposit(...,
  N_surface=source.surface_conc)`; limited → seed a finite dose at the surface and `drive_in` (reuse
  `analytic_drivein_gaussian` / an existing dose-seeded IC). Returns the `DopantProfile` (the loose-
  coupling currency `junction` consumes) so `junction.junction_depth` gives x_j.
- Keep it **lean** — the load-bearing content is the dose-floor wall; the registry is supporting texture
  (constant vs limited source + species delivery), not a decorative pile.

### New — `chip/demo_doping_history.py` (the banked artifact; mirrors `demo_implant.py` structure)

`compute()` / `print_summary()` / `save_figure()` / `main()`, banking `docs/figures/chip-doping-history.png`
(+ `outputs/`), `DOCS_FIGURE` module attr (the gallery introspects it — `gallery.figure_relpath`). The
**modern-vs-period contrast figure**, two panels:
- **Left — the sources at solubility:** each `DopingSource` profile (erfc at its pinned `N_s`; the
  limited source's finite-dose Gaussian), all surface-flooded — the period doping.
- **Right — the dose-control wall:** predep's controllable-dose **floor** (`predep_dose_floor` at the
  demo's stated `T_predep`/`t_min`) vs the implant's metered dose reaching down into the **V_t-adjust
  regime (~5e11, chosen with margin below the floor)** — annotate that `demo_implant`'s "matched" light
  dose only exists by tuning `N_s` below solubility (the cheat A1 makes honest). **Frame spin-on-glass
  deliberately:** the limited source *can* meter a lower dose than a constant source (that is why it was
  the pre-implant workaround) — show it reaching *part-way* down but still **short of implant's precision/
  reproducibility**, so the panel does not argue against its own thesis. Honesty caption: the wall is a
  FLAGGED controllability proxy, sign-robust only across the stated (T_predep, t_min) box printed on the
  figure; the tight legs are the dose identity + the seam.

### New — `chip/tests/test_doping_history.py` (import + numeric only, fast lane; mirrors the repo idiom)

- **Structural limitation (tight):** every constant `SOURCES` entry's `surface_conc` **is** its species
  `DOPANTS[species].N_solid_solubility` (identity, same float — the pinning is real *and* referenced, not
  a re-typed literal that could drift).
- **The predep dose identity (tight):** `run_source` constant-source grid dose matches `predep_dose(N_s,
  D,t)` to the engine's backward-Euler precision (reuses the existing conservation leg).
- **The seam (tight):** a constant `DopingSource` at solubility run through `run_source` reproduces
  `predeposit(...)` (default `N_surface`) **bit-for-bit** — A1 adds no divergence from existing behaviour.
- **The dose-floor wall (FLAGGED — assert sign across the box, NOT a bare magnitude):** parametrize a
  small `(T_predep, t_min)` box and assert `predep_dose_floor > 5e11` for every constant source across
  *that stated box*, while `implant` (via `range_statistics` + arbitrary `Q`) reaches below it. The test
  encodes the box explicitly and comments that `t_min`/`T_predep` are house inputs — it must NOT read as
  a structural law. (Do not assert a single `floor > 5e11` as if physics — that would bake a house `t_min`
  in as truth, the overclaim the advisor flagged.)

### Edit — `chip/gallery.py` (mandatory: the glob forces it)

`assert_manifest_complete()` / `test_gallery.py` require every `chip/demo_*.py` in the manifest — so add
`demo_doping_history` to `DEEPENINGS` with a label (**`"hist·A1"`** — NOT a bare `"A1"`: that collides
with fab_game's A1 and breaks the DEEPENINGS version-tag scheme) + a one-line blurb. Regenerates
`docs/index.html` + `docs/index.local.html` (`python -m chip.gallery`; the golden test then re-passes on
the committed regen). Keep the README *Demonstrations* catalog line in sync (the gallery's stated
blurb-source convention) — add the matching entry to `README.md`.

### Edit — `docs/plans/historical-modes.md` (at build, not in plan mode)

Two reconciliations (both at build): **(1) sequence** — flip to **A1 → … → H0-when-content-justifies-it**
(record A1-first as the chosen, anti-over-build ordering). **(2) content** — the parent doc currently
describes A1 as "the dose∝depth can't-decouple demonstration," which this plan determined is *loose* (the
two-step process partly decouples Q from x_j). Rewrite that A1 description to the **dose-control wall**
(controllability, not depth) so the two plan docs agree on what A1 is. Mark A1 BUILT when done. Also add
an `implant-vs-predep-dose-control` source-memory note (or extend the dopant-solid-solubility one)
capturing the solubility-pinning → dose-floor controllability wall (a FLAGGED proxy, sign-robust across a
stated (T,t) box), so the finding is durable.

## What A1 deliberately does NOT do

- No engine change; no change to `diffusion_dopant.py`'s existing functions or `two_step`/`predeposit`
  behaviour (A1 is a consumer). The seam is trivially intact.
- No new dopant physics beyond reusing the cited erfc/dose/range machinery — the wall is an *accounting*
  of existing physics (solubility pinning + the predep dose identity), which is the point.
- No history page (that is H0, later). A1's figure lands in the physics gallery; H0 curates it in later.

## Verification (end-to-end)

1. `python -m chip.demo_doping_history` → prints the dose-control-wall story, banks
   `docs/figures/chip-doping-history.png` + `outputs/…`. Open the figure; confirm the left panel shows the
   solubility-flooded sources and the right panel shows the predep dose floor sitting *above* the
   V_t-adjust regime that implant reaches.
2. `python -m chip.gallery` → regenerate `docs/index*.html` with the new A1 card; confirm the card renders.
3. Fast lane: `pytest chip/tests/test_doping_history.py chip/tests/test_gallery.py -q` → green (structural
   limitation, dose-floor discriminator, dose identity, seam, gallery currency).
4. Full gate before commit (repo policy): fast lane green first (`-n auto`), then the serial full gate.
5. Commit + push (solo repo — direct `git push origin main`, conventional message + Co-Authored-By), per
   the standing end-of-batch rule.

## Then next (per historical-modes.md)

**A3** (HCl / high-pressure oxidation → the real `Q_ox`→`V_t` and `∫D dt`-budget consumers) or **B6** (Al
junction spiking → `x_j`→leakage) — the other Tier-1 modes — then **H0** (era surface), now justified by
built content, then the Tier-2 trio (A2 litho, A4 resist, B5 LOCOS).
