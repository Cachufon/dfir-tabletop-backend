# Inject Bank

Expected files:
- `core_common.yaml`: Common injects reusable across categories.
- `<category_slug>.yaml`: Category-specific injects.

All inject bank YAML files are validated against:
- `dfir_backend/ttx/schemas/ttx_inject_bank.schema.json`

Inject IDs must be unique across all loaded banks used in a compile.
