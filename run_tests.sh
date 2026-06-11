#!/usr/bin/env sh
# Test runner. Args pass through to pytest, so the tiered gate (ADR 0003) is one flag away:
#   ./run_tests.sh -m "not slow" -n auto    # routine fast lane, PARALLEL (~11 s vs ~26 s serial)
#   ./run_tests.sh                          # full gate, SERIAL — adds the slow notebook test (~33 s, always safe)
#   ./run_tests.sh chip                     # scope to the simulator
#   ./run_tests.sh -k erfc                  # filter by name (serial — no -n, so -s / pdb work)
#
# THE PIN (ADR 0003 amendment): `-n auto` rides ONLY the fast lane (where the slow notebook test
# is deselected). Never run the notebook under `-n auto` alongside the 188 CPU-bound tests — that
# contention trips its zmq/asyncio kernel race (chip-notebook flake). The full gate stays serial,
# so the notebook never touches xdist; `-n auto` is on the command line, not addopts, so single-
# test `-s`/pdb debugging stays serial.
exec python -m pytest "$@"
