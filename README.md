# chip-sim — a microchip-fabrication simulator

[![full-gate](https://github.com/BoykoNeov/chip-sim/actions/workflows/full-gate.yml/badge.svg)](https://github.com/BoykoNeov/chip-sim/actions/workflows/full-gate.yml)

*Process recipe in, device out.* An educational simulator that walks a wafer through the
front-end process flow — dopant diffusion, junction formation, thermal oxidation,
lithography, and the resulting MOS device — each step validated against cited
semiconductor-process references.

It is built on a **separately-validated diffusion/heat solver engine**
(`engines/diffusion`): the dopant-profile physics *is* a 1-D diffusion solve in **mass
mode**, so the simulator adds no new numerical core — it proves the engine reuses. The
engine carries its own contract (`engines/diffusion/CONTRACT.md`) and its own test suite.

## Layout

```
engines/diffusion/   # the 1-D diffusion/heat solver (+ its own tests)
chip/                # the simulator: diffusion_dopant, junction, oxidation, litho, device,
                     #   coupling (Phase 1↔2 OED + segregation), diffusion_highconc (v1.3 D(N) box),
                     #   plots, demos, chip.ipynb
fab_game/            # the fab-line game layered on chip (ADR 0005): sand → a binned chip + a scored
                     #   roguelike; demos, tui.py (Textual UI), fab_game.ipynb, gallery
docs/decisions/      # ADRs 0001–0005 (language/perf, visualization/UX, test policy, engine unfreeze,
                     #   fab-game layering)
docs/plans/          # microchip-fabrication.md — the full build plan;
                     #   fab-game.md — the gamified full-line simulator (a new direction, on top of chip-sim)
docs/figures/        # banked figures (chip-*.png)
```

## Quickstart

```powershell
pip install -e ".[viz]"                 # compute + figures
python -m chip.demo_oxidation           # any demo prints its validation table + banks a figure
jupyter lab chip/chip.ipynb             # the teaching notebook (needs .[viz,notebook])
python -m fab_game.tui                  # …or play the fab-line game (TUI; needs .[tui]) — see below
```

**Run the tests** (the tiered gate — [ADR 0003](docs/decisions/0003-test-execution-policy.md)):

```powershell
./run_tests.ps1 -m "not slow" -n auto     # routine fast lane — 423 tests, PARALLEL (~22 s vs ~78 s serial)
./run_tests.ps1                           # full gate — 424 tests, SERIAL (adds the slow notebook smoke-test)
```

`-n auto` (pytest-xdist) fans the 423 CPU-bound tests across cores — **capped at half the logical
cores** (`conftest.py`: the suite floors on one module, so the back half buys ~nothing; the cap is
an Amdahl throughput knob, not notebook headroom), and **only on the fast lane.**
The one `slow` test executes `chip.ipynb` in a fresh kernel over a zmq/asyncio comms layer that
races under load, so parallelism is applied *only* where it is already deselected (the fast lane,
and CI — where it self-skips). The full gate stays **serial**, so the notebook never runs under
xdist (the pin is structural, not a convention). It also self-skips under CI (a known infra hang
on the GitHub runner — the kernel goes idle but `nbclient` never returns, not a content failure).
`-n auto` is the blessed *command*, not baked into config, so single-test `-s`/pdb stays serial.
The suite is **424 tests** (423 fast + 1 slow), all green; optional stacks are importorskip-gated,
so a headless checkout skips rather than errors.

## Demonstrations

Every fab step ships a **self-contained demo**: run it and it prints a cited validation table and
banks its figure to `docs/figures/`. The twelve figures are already committed there, so you can
browse the gallery on GitHub without running anything; the table below maps each one to the demo
that produced it. Run from the repo root after `pip install -e ".[viz]"`:

```powershell
python -m chip.demo_junction            # → prints the table, saves docs/figures/chip-junction.png
```

> Use the `python -m chip.demo_*` form, **not** `python chip/demo_*.py` — the demos are package
> modules (relative imports), so the bare-path form fails with *"attempted relative import."*

**Prefer to click?** A self-contained **interactive gallery** of all twelve — thumbnails linking to
the full figures, each with its run command and source — is generated to
[`docs/index.html`](docs/index.html) by `python -m chip.gallery`. Enable GitHub Pages (*Settings →
Pages → `main` / `/docs`*) to serve it at `https://boikoneov.github.io/chip-sim/`. The page is
generated from the demo modules (figure paths introspected, never hand-typed) and guarded by a
fast-lane test (`chip/tests/test_gallery.py`), so it can't drift: add a demo and the gate stays red
until the page is rebuilt.

**The spine — the four process phases, in build order (start here):**

| Run (`python -m …`) | Shows | Figure |
|---|---|---|
| `chip.demo_junction` | **Phase 1a** — a pn junction from a two-step boron diffusion: junction depth `x_j` + sheet resistance `R_s` | [chip-junction.png](docs/figures/chip-junction.png) |
| `chip.demo_oxidation` | **Phase 2** — Deal–Grove thermal oxide, wet vs dry, the linear→parabolic bend | [chip-oxidation.png](docs/figures/chip-oxidation.png) |
| `chip.demo_litho` | **Phase 3** — the aerial image assembling from its diffraction orders + contrast-vs-pitch | [chip-litho.png](docs/figures/chip-litho.png) |
| `chip.demo_device` | **Phase 4** — the whole process→device chain → MOS threshold voltage `V_t` | [chip-device.png](docs/figures/chip-device.png) |

**The deepenings — optional depth, each promoting a named scope edge of its phase:**

| Run (`python -m …`) | Shows | Figure |
|---|---|---|
| `chip.demo_thin_oxide` | **v1.1** — Massoud thin-dry oxide correction (gate-oxide before/after, the `V_t` shift) | [chip-thin-oxide.png](docs/figures/chip-thin-oxide.png) |
| `chip.demo_coupling` | **v1.2** — Phase 1↔2 back-coupling: OED deepening + segregation (boron depletes / phosphorus piles up) | [chip-oed-segregation.png](docs/figures/chip-oed-segregation.png) |
| `chip.demo_diffusion_highconc` | **v1.3** — concentration-dependent diffusivity `D(N)`, the high-concentration box | [chip-highconc.png](docs/figures/chip-highconc.png) |
| `chip.demo_defocus` | **v1.4** — lithographic defocus, the depth of focus & the Bossung curve | [chip-defocus.png](docs/figures/chip-defocus.png) |
| `chip.demo_peb` | **v1.7** — PEB acid-diffusion blur: the latent image dissolving + the PEB window | [chip-peb.png](docs/figures/chip-peb.png) |
| `chip.demo_lateral_diffusion` | **v1.8** — 2-D lateral diffusion under a mask edge (the junction curving under the mask) | [chip-lateral-diffusion.png](docs/figures/chip-lateral-diffusion.png) |
| `chip.demo_car` | **v1.9** — CAR reaction–diffusion PEB (the chemically-amplified bake) | [chip-car.png](docs/figures/chip-car.png) |
| `chip.demo_zernike` | **v1.10** — Zernike aberrations (coma / astigmatism / spherical), a pupil phase | [chip-zernike.png](docs/figures/chip-zernike.png) |
| `chip.demo_device_2d` | **v1.11** — 2-D MOSFET cross-section: lateral S/D diffusion shortens the channel (`L_eff`), not `V_t` | [chip-device-2d.png](docs/figures/chip-device-2d.png) |

*(v1.5–v1.6 are engine-internal amendments — native nonlinear `D(u)` and explicit stepping — with no
chip demo of their own; they surface through `engines/diffusion`'s own test suite.)*

**The full writeup** for any demo — cited references, the headline numbers, the scope edges and the
design findings — lives in [`chip/README.md`](chip/README.md#status)'s *Status* section, keyed by the
same phase/version label. This catalog is the launch-pad; that section is the depth.

**The guided interactive tour:** [`chip/chip.ipynb`](chip/chip.ipynb) is the single notebook — one
section per phase, each with `ipywidgets` sliders re-running a validated module live, ending on the
coherent process→device flow. `pip install -e ".[viz,notebook]"`, then `jupyter lab chip/chip.ipynb`.

## The fab-line game (a second entry point)

Layered **on top of** this physics is a gamified full-production-line simulator
([`fab_game/`](fab_game/README.md); the layering decision is
[ADR 0005](docs/decisions/0005-fab-game-layering.md)): *recipe in → **yield** out, and you can see
**why** a die died.* It runs the whole line **sand → a binned, packaged chip** — Czochralski boule,
wafer prep, purification, the validated diffusion/oxidation/litho/device back end, etch & deposition,
packaging — and scores it as a roguelike (one boule = one run, each wafer a turn). The validated
physics stays in `chip/` + `engines/` (cited triads); `fab_game/` owns only what *cannot* be
physics-validated — the stochastic spread, the spec windows, the yield, the rework — enforced by a
one-way `fab_game → chip/engines` import.

```powershell
pip install -e ".[viz]"                 # compute + figures (add ,tui for the TUI / ,notebook for the notebook)
python -m fab_game.demo_game            # the roguelike payoff: three strategies down one boule
python -m fab_game.tui                  # play it — the Textual TUI (dashboard + roguelike screen; needs .[tui])
jupyter lab fab_game/fab_game.ipynb     # the interactive skin + the §9 guided dashboard
```

**Prefer to click?** A separate **interactive gallery** of the game-layer artifacts is at
[`docs/fab-game.html`](docs/fab-game.html) (`python -m fab_game.gallery`), cross-linked from the chip
gallery. The full writeup — every milestone G1–G7, the crystal-growth deepenings, and the scope-edge
promotions — lives in [`fab_game/README.md`](fab_game/README.md).

## Provenance

chip-sim was developed inside the **BigSim** monorepo — an educational program of three
simulators (steel, microchip, planet) sharing two separately-validated solver engines —
then extracted into a standalone repo with its history. The diffusion engine and the
cross-project pedagogy (it was first validated by the steel simulator's carburizing model)
are documented in the plan and ADRs; the sibling simulators live in their own repos. The
archive: [github.com/BoykoNeov/BigSim](https://github.com/BoykoNeov/BigSim).
