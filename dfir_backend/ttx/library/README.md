# Scenario Library

This directory contains reusable scenario composition inputs for deterministic TTX scenario generation.

## Contents
- `reference_catalog.yaml`: Stable evidence reference ID catalog.
- `inject_bank/`: Reusable inject definitions, split by common/core and category packs.
- `module_maps/`: Category module sequencing and profile-specific inject slot maps.

## Deterministic flow
1. Validate library assets:
   - `python3 dfir_backend/ttx/scripts/validate_ttx_library.py`
2. Compile scenario for a case:
   - `python3 dfir_backend/ttx/scripts/compile_ttx_scenario_from_library.py --case-dir <case_dir>`

The compiler assembles a scenario from:
- module map profile (`EXEC_90`, `HALF_DAY`, `FULL_DAY`)
- inject banks (`core_common.yaml` + category bank)
- intake metadata placeholder substitutions
