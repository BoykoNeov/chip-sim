# chip-sim — a microchip-fabrication simulator

[![full-gate](https://github.com/BoykoNeov/chip-sim/actions/workflows/full-gate.yml/badge.svg)](https://github.com/BoykoNeov/chip-sim/actions/workflows/full-gate.yml)

*Process recipe in, device out.* An educational simulator that walks a wafer through the
front-end process flow — dopant diffusion, junction formation, thermal oxidation,
lithography, and the resulting MOS device — each step validated against cited
semiconductor-process references.

It is built on a **frozen, separately-validated diffusion/heat solver engine**
(`engines/diffusion`): the dopant-profile physics *is* a 1-D diffusion solve in **mass
mode**, so the simulator adds no new numerical core — it proves the engine reuses. The
engine carries its own contract (`engines/diffusion/CONTRACT.md`) and its own test suite.

## Layout

```
engines/diffusion/   # the frozen 1-D diffusion/heat solver (+ its own tests)
chip/                # the simulator: diffusion_dopant, junction, oxidation, litho, device,
                     #   coupling (Phase 1↔2 OED + segregation), plots, demos, chip.ipynb
docs/decisions/      # ADRs 0001–0003 (language/perf, visualization/UX, test policy)
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
./run_tests.ps1 -m "not slow"     # routine fast lane — 149 tests
./run_tests.ps1                   # full suite — 150 tests (adds the slow notebook smoke-test)
```

The suite is **150 tests**, all green. The one `slow` test executes `chip.ipynb` end-to-end in
a fresh kernel; it self-skips under CI (a known kernel-startup wedge on the GitHub runner — an
infra hang, not a content failure) and runs in the local full gate. Optional stacks are
importorskip-gated, so a headless checkout skips rather than errors.

## Provenance

chip-sim was developed inside the **BigSim** monorepo — an educational program of three
simulators (steel, microchip, planet) sharing two separately-validated solver engines —
then extracted into a standalone repo with its history. The diffusion engine and the
cross-project pedagogy (it was first frozen by the steel simulator's carburizing model)
are documented in the plan and ADRs; the sibling simulators live in their own repos. The
archive: [github.com/BoykoNeov/BigSim](https://github.com/BoykoNeov/BigSim).
