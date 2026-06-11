---
name: chip-notebook-flake
description: "chip.ipynb slow smoke-test hangs ~80% in CI — an nbclient<->ipykernel message race during EXECUTION (NOT startup, NOT chip content). Pinning ipykernel<7 does NOT fix it (6.31.0 hangs too — re-confirmed CI run 27299430919, 2026-06-10); the teardown-skip fix also FAILED (still 8/10). skipif(CI) stays; root cause solid, robust fix still open. Re-test lever: CHIP_NOTEBOOK_FORCE_CI=1. ALSO flakes LOCALLY under load (2026-06-11: timed out once when launched right after a parallel `-n auto` bulk; 4/4 in isolation) → motivated the pytest-xdist PIN (ADR 0003 amend): -n auto rides only the fast lane, full gate stays serial."
metadata:
  node_type: memory
  type: project
  originSessionId: 1d49d915-1c78-4254-aa64-b817b4a2940a
---

The `slow`-marked notebook smoke test `chip/tests/test_chip_notebook.py` (runs `chip.ipynb` headless
in a fresh child process via nbclient, asserts every cell executes clean) **hung in GitHub full-gate CI**
(Ubuntu, Python 3.12.13) — blew the subprocess wall-clock — while passing locally in ~8 s. A CI-only
`@pytest.mark.skipif(os.environ.get("CI"))` was landed first (2026-06-10, d6e4f79) to stop the red while
deferring the root cause.

**ROOT-CAUSED 2026-06-10 (re-investigation, on the standalone chip-sim repo).** The decisive chain:

1. **NOT chip-specific, NOT content.** Earlier framing ("chip-specific kernel-startup wedge", "steel/planet
   pass in CI") was **wrong** — `test_steel_notebook.py` / `test_planet_notebook.py` carry the *identical*
   `skipif(CI)` (they skip too, no asymmetry); chip's modules don't fork; `chip.ipynb` is benign
   (`%matplotlib inline` + fast compute + `interact` rendered once) and **executes clean in ~11 s** even on
   the runner. The BigSim monorepo's surviving CI log shows the *steel* notebook hung identically — the wedge
   lives in the **shared nbclient/ipykernel notebook-execution harness**, common to all three.

2. **It is kernel TEARDOWN, not startup, not a stuck cell.** The linchpin: the test wraps the child in
   `subprocess.run(timeout=…)` and nbclient has its own per-cell `timeout`. The original failures **always
   blew the *subprocess* wall-clock and NEVER raised an nbclient `CellTimeoutError`** — so no *cell* was ever
   stuck (a stuck cell trips the per-cell timeout first). Measured on the runner (10× loop, no diagnostics):
   **PASS=2, HANG=8 / 10 (~80 %)**. `py-spy` on a genuine hang: the **kernel is fully idle** (MainThread parked
   in `kernelapp.start`→tornado→`select`, every channel thread idle), while the **nbclient parent is stuck
   inside `NotebookClient.execute()`** (`run_until_complete`→`select`). I.e. **every cell ran, the kernel went
   idle, and nbclient's graceful kernel teardown raced and never completed** — ipykernel 7.x moved IOPub/Shell/
   Control to separate threads; the teardown handshake (likely with pending iopub from the inline-figure PNG
   payloads) deadlocks. Eliminated along the way: a startup wedge (cells execute fine); the IPython
   `HistoryManager` SQLite-lock (nbclient already launches with `--HistoryManager.hist_file=:memory:`);
   fork-in-kernel (no multiprocessing in chip's code). My first diagnostic run's "wedged at cell 5" was a
   DEBUG-logging **artifact** (the huge base64 `display_data` payload buffered, so visible output lagged the
   real position) — corrected once measured properly.

3. **Version surface.** CI stack (fresh latest): Python 3.12.13, **ipykernel 7.3.0**, ipython 9.14.1,
   jupyter_client 8.9.1, pyzmq 27.1.0, nbclient 0.11.0, ipywidgets 8.1.8. Local-pass: Python 3.14.3, ipykernel
   7.2.0, else identical. Version-pinning is a **rabbit hole** — 7.3.0 hangs ~80 % *inside* `execute()`; pinning
   `ipykernel<7` (6.31.0) instead hangs at *interpreter teardown* (printed "executed clean" then blocked). So
   the fix targets the teardown itself, not a "good version."

**Correction to point 2 (my "teardown" call was WRONG).** The reasoning "per-cell `timeout` never fired →
no cell stuck → must be teardown" was flawed: nbclient's per-cell `timeout` bounds the **shell execute_reply**
wait, NOT the **iopub idle-status drain** — so "no `CellTimeoutError`, blew the subprocess wall" is also
consistent with a hang *during* a cell, waiting on a lost/raced **iopub idle** message. The figure-producing
cell (cell 5, `junction_figure` + `plt.show()`) emits a large base64 `display_data` payload, and with
ipykernel 7.x's threaded IOPub the idle status races and is lost ~80 % of the time → nbclient waits in
`execute_cell` forever. The py-spy "kernel idle, parent in `execute()`" snapshot fits this just as well as
teardown.

**THE FIX ATTEMPT FAILED (do not bring to main).** The teardown-skip — explicit cell loop
(`with client.setup_kernel(): for i,cell: client.execute_cell(cell,i)`) then `os._exit(0)` — verified locally
(no hang on Win/Py3.14) but on the runner gave **PASS=2 / FAIL=8 of 10, identical to the 80 % baseline**
(throwaway `nb-diag.yml`, looped un-skipped `pytest -m slow`). Zero effect on the rate. **Honest framing (an
elimination, not a direct observation — my verify's `timeout -k 5 90` killed pytest before the child's output
surfaced, so I never *saw* whether "executed clean" printed):** the hang is bounded by **neither** the per-cell
`timeout` (steel's 90 s never fired → not the shell execute_reply wait) **nor** removed by skipping teardown →
it is an **unbounded wait in nbclient's per-cell iopub / message-drain, racing ipykernel 7.x's threaded
channels** (~80 %). Not startup, not teardown, not content.

**Why no harness trick rescues it (load-bearing):** when nbclient stalls draining cell N, cells N+1…end are
never dispatched — so the kernel goes idle with the notebook only *partly* executed, and no `os._exit` /
sentinel / per-cell watchdog can truthfully assert "executed clean" past the stall. The only real options are
**(a) prevent the race** — a version/config hunt, and both 7.3.0 (in-loop) and 6.31.0 (interpreter-teardown)
fail, so it's a genuine hunt, not a one-liner — or **(b) keep the skip.**

**RE-CONFIRMED IN A CLEAN CI RUN (2026-06-10, standalone repo).** Prompted by steel-sim's handoff
`docs/handoffs/notebook-kernel-wedge.md` (its Windows-Proactor lost-`execute_reply` bug + retry-on-wedge
fix), re-checked whether any of it transfers. It does NOT resolve chip's skip: steel §6 itself says the
Windows root-cause does not explain a **Linux** CI hang and to keep the skip. The one chip-specific lead —
pin `ipykernel<7` — was **re-tested live** on a throwaway branch (`experiment/ipykernel-pin-nb-wedge`,
since deleted): full-gate CI run **27299430919** installed **ipykernel 6.31.0** and forced the notebook test
10× via a new `CHIP_NOTEBOOK_FORCE_CI=1` escape hatch → **hung the 240 s subprocess wall on attempt 1/10**
(SIGKILL, -9). So pinning `<7` is a **re-confirmed dead end** (matches point 3 above — 6.31.0 blocks at a
different stage but still hangs), now durably recorded in Actions history (the old `nb-diag`/`debug` evidence
was deleted). Also de-staled the in-repo comments (`test_chip_notebook.py`, was: "kernel-startup hang →
force a SelectorEventLoop" — wrong: it's mid-execution, and Linux CI is already on a selector loop, so that
"candidate" is a no-op here / steel §4's Windows trap there). The `CHIP_NOTEBOOK_FORCE_CI=1` lever now lives
on `main` for the next re-test. retry-on-wedge (steel's fix) is a poor fit: chip's clean run is ~8–11 s so no
tight per-attempt cutoff is possible, and ~80 % needs ~15 attempts. `main` still carries the skip.

**RECOMMENDATION (advisor-backed): keep the `skipif(CI)`.** The notebook is a *reach layer, not correctness*
(its own docstring) — the physics is validated behind the module triads, and the content is verified clean
(local, the 20 % that pass, the explicit run). Removal is blocked on an **upstream nbclient↔ipykernel-7.x bug**,
which is a finding, not a failure. The debug-branch fix is **NOT** main-bound; `main` is untouched (skip still
active). **DECISION (user, 2026-06-10): keep the documented skip; the throwaway `debug/nb-ci-wedge` branch
was deleted (local + origin).** The four `nb-diag` runs remain in the chip-sim Actions history as the evidence
trail. Reopen only with a version/config hunt if the upstream nbclient↔ipykernel-7.x combo is ever worth
defeating. Mirrors steel-sim/planet-sim (same harness + skip) — the same finding applies there.

**NOT only a CI infra hang — load-sensitive LOCALLY too (2026-06-11).** While wiring up `pytest-xdist`
(`-n auto`, fast lane 188 tests 26 s→11 s; commit `fa56f81`), the notebook timed out **locally** (a cell
blew the 120 s nbclient per-cell `timeout`) **once** — specifically when its `pytest -m slow` leg launched
*immediately after* a parallel `-n auto` bulk had just saturated 16 cores, on a box already hammered by
~10 rapid full-suite runs. In isolation it stayed reliable (4/4, ~7–8 s). So the same race that hangs ~80 %
in CI also bites under enough local CPU contention — the earlier "reliable locally" framing was an
under-load blind spot. This is the load-bearing reason for **THE PIN** (ADR 0003 amendment 2026-06-11): the
notebook must never run under xdist alongside the 188 CPU-bound tests, so `-n auto` rides ONLY the fast lane
(notebook deselected) + CI (notebook self-skips); the **local full gate stays bare serial `pytest`** — the
notebook never touches xdist in any blessed command (a parallel two-command full gate was tried and rejected
on this evidence: 1 timeout / 1 pass). **Re-confirmed same day (commit `25b6433`):** even with workers
**capped at half the logical cores** (8 on the 16-logical box, via a `conftest.py`
`pytest_xdist_auto_num_workers` hook) **plus** `--dist loadgroup` grouping, a fully co-scheduled full gate
still flaked the notebook **1-in-4** (3 pass / 1 timeout); the notebook stays off the concurrent path,
full gate serial. **n/4 tested next (2026-06-11): 2/6 co-scheduled flake at 4 workers (12 idle cores)** —
fewer workers is NOT a fix and idle cores do not protect the notebook, so do NOT re-explore reducing the
worker count. (The cap never governs the notebook at all: the hook fires only on the fast lane, where the
notebook is deselected → the notebook is safe by being **serial**, not by idle headroom. Earlier "idle
half is headroom" framing in conftest/pyproject/README/ADR was corrected to "Amdahl knob only" same day.)
CI green throughout (notebook self-skips there → 188 pass under capped `-n auto`, run 27316667628). See
[[engine-unfrozen]] for the broader engine/test-infra context.
