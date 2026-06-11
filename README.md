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
docs/decisions/      # ADRs 0001–0004 (language/perf, visualization/UX, test policy, engine unfreeze)
docs/plans/          # microchip-fabrication.md — the full build plan
docs/figures/        # banked figures (chip-*.png)
```

## Quickstart

```powershell
pip install -e ".[viz]"                 # compute + figures
python chip/demo_oxidation.py           # any demo prints its validation table + banks a figure
jupyter lab chip/chip.ipynb             # the teaching notebook (needs .[viz,notebook])
```

**Run the tests** (the tiered gate — [ADR 0003](docs/decisions/0003-test-execution-policy.md)):

```powershell
./run_tests.ps1 -m "not slow" -n auto     # routine fast lane — 188 tests, PARALLEL (~11–13 s vs ~26 s serial)
./run_tests.ps1                           # full gate — 189 tests, SERIAL (adds the slow notebook smoke-test)
```

`-n auto` (pytest-xdist) fans the 188 CPU-bound tests across cores — **capped at half the logical
cores** (`conftest.py`: the suite floors on one module, so the back half buys ~nothing; the cap is
an Amdahl throughput knob, not notebook headroom), and **only on the fast lane.**
The one `slow` test executes `chip.ipynb` in a fresh kernel over a zmq/asyncio comms layer that
races under load, so parallelism is applied *only* where it is already deselected (the fast lane,
and CI — where it self-skips). The full gate stays **serial**, so the notebook never runs under
xdist (the pin is structural, not a convention). It also self-skips under CI (a known infra hang
on the GitHub runner — the kernel goes idle but `nbclient` never returns, not a content failure).
`-n auto` is the blessed *command*, not baked into config, so single-test `-s`/pdb stays serial.
The suite is **189 tests** (188 fast + 1 slow), all green; optional stacks are importorskip-gated,
so a headless checkout skips rather than errors.

## Provenance

chip-sim was developed inside the **BigSim** monorepo — an educational program of three
simulators (steel, microchip, planet) sharing two separately-validated solver engines —
then extracted into a standalone repo with its history. The diffusion engine and the
cross-project pedagogy (it was first validated by the steel simulator's carburizing model)
are documented in the plan and ADRs; the sibling simulators live in their own repos. The
archive: [github.com/BoykoNeov/BigSim](https://github.com/BoykoNeov/BigSim).
