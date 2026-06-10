"""BigSim shared solver toolkit (ARCHITECTURE.md §5).

Each engine is a standalone, separately-tested library, validated behind a passing
suite (open + test-gated) before any project reuses it. The first engine is
``engines.diffusion`` — the 1-D conservative parabolic (diffusion/heat) spine.
"""
