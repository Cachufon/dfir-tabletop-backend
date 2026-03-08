# Normalization Runbook (Phase 1 - Manual)

1. Confirm the case folder exists and raw data is placed under `raw/<scope_area>/` within the case directory.
2. Run the normalization scripts (placeholders) for each relevant scope area, writing outputs under `normalized/`.
3. Execute `validate_normalized.py` to generate a validation report against expected normalized outputs.
4. Store the validation report at `analysis/validation_report.md` inside the case folder.
5. Note: scripts are stubs and may be replaced with tooling; the structure and output locations should remain stable.
