# Module Maps

Module maps define category sequencing and profile-specific timing/completeness rules.

Each map file is expected at:
- `dfir_backend/ttx/library/module_maps/<category_slug>.yaml`

Required profile keys:
- `EXEC_90`
- `HALF_DAY`
- `FULL_DAY`

All module map YAML files are validated against:
- `dfir_backend/ttx/schemas/ttx_module_map.schema.json`
