# Normalization

Normalization converts raw telemetry and artifacts into a stable, vendor-agnostic schema so downstream detections and reporting stay consistent even when sources change. The canonical schema is defined in `normalized_data_contract.md` and should be treated as the contract for all pipelines.

Normalized outputs are consumed by detection rules, investigative playbooks, and reporting. Implement normalization per scope area (identity, saas, cloud, endpoint) plus AI artifacts for Model 5, producing outputs that align to the contract.

Suggested per-case folder layout (guidance, not enforcement):

```
dfir_backend/custom/<case_id>/
  raw/{identity,saas,cloud,endpoint,ai}/
  normalized/
  analysis/
```
