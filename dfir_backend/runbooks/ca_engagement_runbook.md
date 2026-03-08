# Compromise Assessment Engagement Runbook (v1)

## 0. Preconditions
- Confirm the assessment model (Model 1–5)
- Confirm selected scope areas (Identity, SaaS, Cloud, Endpoint, AI)
- Confirm time window
- Confirm customer POCs
- Create a case ID

Reference:
- dfir_backend/workflows/ca_models.md
- dfir_backend/workflows/ca_workflow.md
- dfir_backend/workflows/ai_safety_prompt_assessment_workflow.md (Model 5 only)

## 1. Create Case Workspace
- Create dfir_backend/custom/<case_id>/
- Optional (outside git): run dfir_backend/ca/scripts/init_ca_case.py to initialize a CA case workspace in a non-repo path
- Ensure intel/summary.md and detection_plan.yaml exist
- Ensure raw/ and normalized/ and analysis/ folders exist (as described in normalization README)

Reference:
- dfir_backend/custom/README.md (if present)
- dfir_backend/normalization/README.md
- dfir_backend/ca/scripts/init_ca_case.py

## 2. Data Intake Checklist (by Scope Area)
For each selected scope area, list:
- Minimum required inputs (from scope area data_sources.md)
- Optional inputs

Provide subsections:
- Identity scope area intake checklist
- SaaS scope area intake checklist
- Cloud scope area intake checklist
- Endpoint scope area intake checklist
- AI scope area intake checklist (Model 5 artifacts)

Reference:
- dfir_backend/scope_areas/identity/data_sources.md
- dfir_backend/scope_areas/saas/data_sources.md
- dfir_backend/scope_areas/cloud/data_sources.md
- dfir_backend/scope_areas/endpoint/data_sources.md
- dfir_backend/scope_areas/ai/data_sources.md
- dfir_backend/ca/templates/data_request_template.md
- dfir_backend/ca/templates/telemetry_completeness_matrix.template.csv

## 3. Normalize Data
- Place raw inputs under dfir_backend/custom/<case_id>/raw/<scope_area>/
- Run normalization scripts stubs (or document manual normalization steps)
- Write outputs into dfir_backend/custom/<case_id>/normalized/
- Run validate_normalized.py and write validation report to analysis/validation_report.md

Reference:
- dfir_backend/normalization/normalized_data_contract.md
- dfir_backend/normalization/runbook.md
- dfir_backend/normalization/validation_rules.md

## 4. Execute Detections
- Select baseline packs for the selected scope areas
- For Models 2 and 3, add case-specific rules/IOCs under dfir_backend/custom/<case_id>/
- Run detection stubs (or document manual execution and then produce hits.json according to contract)
- Ensure outputs exist under analysis/detections/<scope_area>/

Reference:
- dfir_backend/detections/runbook.md
- dfir_backend/detections/execution_contract.md
- dfir_backend/rules/ (global rules)
- dfir_backend/custom/<case_id>/ (case-specific rules/IOCs)

For Model 5 (AI Safety):
- Use ai artifacts and MAPS workflow
- Generate MAPS outputs into analysis/detections/ai/

Reference:
- dfir_backend/detections/packs/ai_model5_maps.md
- dfir_backend/workflows/ai_safety_prompt_assessment_workflow.md

## 5. Triage and Storylines
- Review detections_rollup.md and per-scope hits_summary.md
- Cluster hits into storylines using the triage templates
- Write storyline_candidates.md and triage_notes.md

Reference:
- dfir_backend/triage/runbook.md
- dfir_backend/triage/triage_contract.md
- dfir_backend/triage/templates/

## 6. Create Findings
- Promote validated storylines to findings
- Create analysis/findings/finding_ID-###.md using the finding template
- Maintain analysis/findings/findings_index.md

Reference:
- dfir_backend/reporting/finding_template.md
- dfir_backend/reporting/finding_taxonomy.md
- dfir_backend/triage/templates/findings_index_template.md

## 7. Assemble Reports
- Technical report: use technical_report_template.md
- Executive summary: use executive_summary_template.md
- For Model 5: use ai_safety_report_template.md

Reference:
- dfir_backend/reporting/technical_report_template.md
- dfir_backend/reporting/executive_summary_template.md
- dfir_backend/reporting/ai_safety_report_template.md

## 8. Internal QA Checklist
- Scope matches model and selected scope areas
- Data gaps recorded
- Severity and confidence consistent with taxonomy
- Evidence summaries include timestamps and sources
- Recommendations present for 0–7 / 30 / 90 days
- No contradictory language between exec summary and technical report

## 9. Delivery Checklist
- Confirm deliverables
- Schedule readout
- Record follow-up actions and next steps

Ensure the runbook is concise, uses checklists and headings, and references the repo paths explicitly.
