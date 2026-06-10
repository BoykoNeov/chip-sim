"""Microchip fabrication simulator — *process recipe in, device out*.

Project #2 of the BigSim program (plan: ``docs/plans/microchip-fabrication.md``).
The **first consumer of the frozen diffusion/heat spine** (``engines.diffusion``):
it builds *no* new shared engine, it proves the spine reuses — dopant profiles
**are** the carbon-diffusion code Steel froze, in **mass mode** (ARCHITECTURE.md §4.2).

Phase 1a public API — dopant diffusion & the pn junction:

    from chip.diffusion_dopant import (
        DOPANTS, diffusivity, predeposit, drive_in, two_step,
        analytic_predep_erfc, analytic_drivein_gaussian, predep_dose,
    )
    from chip.junction import junction_depth, sheet_resistance, mobility

> **UNIT SYSTEM — semiconductor-conventional CGS.** Unlike Steel (SI metres), the
> chip modules work in **cm / cm²·s⁻¹ / cm⁻³ / cm²·V⁻¹·s⁻¹** — the *native* units of
> the cited dopant data (Fair ``D₀``, Trumbore ``N_s``, Masetti ``μ``), so no
> load-bearing constant is converted on the way in, and sheet resistance falls out in
> Ω/sq directly. The frozen engine is unit-agnostic (it solves the PDE in whatever
> consistent length/time the consumer supplies); we feed it **cm and seconds**.
> Lengths are reported in **µm** at the boundary. See ``diffusion_dopant`` for the
> full banner.
"""
