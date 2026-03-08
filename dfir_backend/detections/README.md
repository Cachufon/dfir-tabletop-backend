# Detection Execution (Phase 1)

Detection execution consumes normalized datasets produced under `dfir_backend/custom/<case_id>/normalized/` and runs detection content from both `dfir_backend/rules/` and `dfir_backend/custom/<case_id>/` for case-specific rules.

Execution outputs standardized hit artifacts under `dfir_backend/custom/<case_id>/analysis/detections/` to support consistent triage and reporting across engines. The process is vendor-agnostic and supports multiple detection types, including Sigma, YARA, IOC sweeps, and MAPS for Model 5.

## Per-case output layout

```
analysis/
  detections/<scope_area>/
    hits.json
    hits_summary.md
  detections_rollup.md
```

- `hits.json` follows the contract defined in `execution_contract.md`.
- `hits_summary.md` provides a human-readable summary for analysts.
- `detections_rollup.md` aggregates detections across scope areas for quick reporting.
