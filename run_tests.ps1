#!/usr/bin/env pwsh
# Test runner. Args pass through to pytest, so the tiered gate (ADR 0003) is one flag away:
#   ./run_tests.ps1 -m "not slow"    # routine fast lane (the always-on suite)
#   ./run_tests.ps1                  # full suite — adds the slow notebook smoke-test (CI / release)
#   ./run_tests.ps1 chip             # scope to the simulator
#   ./run_tests.ps1 -k erfc          # filter by name
$ErrorActionPreference = "Stop"
python -m pytest @args
exit $LASTEXITCODE
