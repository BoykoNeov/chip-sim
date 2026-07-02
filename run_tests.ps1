#!/usr/bin/env pwsh
# Test runner. Args pass through to pytest, so the tiered gate (ADR 0003) is one flag away:
#   ./run_tests.ps1 -m "not slow" -n auto    # routine fast lane (~850 tests), PARALLEL
#   ./run_tests.ps1                          # full gate, SERIAL — adds the slow notebook test (always safe)
#   ./run_tests.ps1 chip                     # scope to the simulator
#   ./run_tests.ps1 -k erfc                  # filter by name (serial — no -n, so -s / pdb work)
#
# THE PIN (ADR 0003 amendment): `-n auto` rides ONLY the fast lane (where the slow notebook test
# is deselected). Never run the notebook under `-n auto` alongside the CPU-bound tests — that
# contention trips its zmq/asyncio kernel race (chip-notebook flake). The full gate stays serial,
# so the notebook never touches xdist; `-n auto` is on the command line, not addopts, so single-
# test `-s`/pdb debugging stays serial.
$ErrorActionPreference = "Stop"
python -m pytest @args
exit $LASTEXITCODE
