"""Root pytest configuration.

Currently one job: cap pytest-xdist's worker count. With `-n auto` (or `-n logical`) xdist
would otherwise spawn one worker per *logical* core (16 on this box); this hook redefines
`auto` to **half the logical cores** (8). See ADR 0003's xdist amendment for the full rationale —
the short version:

  * The suite floors on one ~3.9 s module (`diffusion_highconc`), not on worker count: the
    speedup already plateaus by ~8 workers, so the back half of the cores buys ~nothing.
  * Leaving half the cores idle keeps headroom for the slow notebook test's live Jupyter kernel
    subprocess. That kernel polls zmq over asyncio and *races when the box is starved*
    (chip-notebook flake); 16 workers of saturation is exactly the perturbation that trips it,
    8 leaves it room. This is what lets the notebook ride a grouped parallel full gate at all.

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
