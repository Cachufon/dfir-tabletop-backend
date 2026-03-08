# Triage Workflow Scaffolding

This triage area standardizes how analysts convert detection outputs into storylines and findings for compromise assessments.

- Triage consumes standardized detection outputs from `dfir_backend/custom/<case_id>/analysis/detections/`.
- Analysts cluster and validate hits into storylines.
- Storylines become findings using `dfir_backend/reporting/finding_template.md`.
- Outputs are stored under `dfir_backend/custom/<case_id>/analysis/triage/` and `dfir_backend/custom/<case_id>/analysis/findings/`.

Use the accompanying contract, runbook, and templates to keep cases consistent and repeatable.
