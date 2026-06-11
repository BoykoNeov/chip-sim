"""Root pytest configuration.

Currently one job: cap pytest-xdist's worker count. With `-n auto` (or `-n logical`) xdist
would otherwise spawn one worker per *logical* core (16 on this box); this hook redefines
`auto` to **half the logical cores** (8). See ADR 0003's xdist amendment for the full rationale.

The cap exists for **Amdahl, full stop**: the suite floors on one ~3.9 s module
(`diffusion_highconc`), so the speedup already plateaus by ~8 workers — the back half of the cores
buys ~nothing. That is the *only* reason for the cap; it governs fast-lane throughput alone.

It is explicitly **not** a knob for the slow notebook test. This hook fires only for the
`-n auto` / `-n logical` sentinels — i.e. the **fast lane**, where the notebook is deselected. The
full gate is bare serial `pytest` (no `-n`), so the hook never fires and the notebook never runs
alongside an xdist worker in *any* blessed command. The notebook is safe because it is **serial by
construction**, not because idle cores shield its kernel: reducing the cap to n/4 (4 workers, 12
idle cores) still flaked the co-scheduled notebook 2-in-6 (2026-06-11) — idle cores do not protect
it (chip-notebook flake).

Adaptive on purpose (`os.cpu_count() // 2`), so it does the right thing on CI runners and dev
boxes alike without a hardcoded number. `-n <N>` with an explicit count still overrides this;
the hook only fires for the `auto` / `logical` sentinels.

The hook is defined ONLY when pytest-xdist is importable: it implements an xdist hookspec, and
pytest raises ``PluginValidationError`` at collection for an "unknown hook" if the spec's plugin
is absent. xdist is in the ``[test]`` extra, so this only matters in a bare ``pytest`` env.
"""
import os

try:
    import xdist  # noqa: F401  — only to gate the hook below; see module docstring.

    def pytest_xdist_auto_num_workers(config):
        return max(1, (os.cpu_count() or 2) // 2)

except ImportError:
    pass
