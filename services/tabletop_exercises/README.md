# Tabletop Exercises (TTX)

This folder contains **service-level** documentation for the Tabletop Exercises offering (overview, packaging, positioning).

## Delivery backbone (source of truth)
Reusable delivery assets and templates live in:
- dfir_backend/ttx/

Key references:
- Workflow: dfir_backend/workflows/ttx_workflow.md
- Playbook: dfir_backend/playbooks/tabletop_exercise_playbook.md
- Engagement runbook: dfir_backend/runbooks/ttx_engagement_runbook.md
- Scenario taxonomy: dfir_backend/ttx/scenario_taxonomy.md
- Scenario schema: dfir_backend/ttx/schemas/ttx_scenario.schema.json
- Scenario library (generalized): dfir_backend/ttx/scenarios/
- Facilitator guide template: dfir_backend/ttx/facilitator_guide_template.md
- Inject drafting template: dfir_backend/ttx/inject_template.md
- Scoring model: dfir_backend/ttx/scoring_model.md
- After-Action Report template: dfir_backend/ttx/after_action_report_template.md

## Critical data handling rule
Do NOT store or commit client-specific materials in this repo (including this folder), such as:
- IR plans, org charts, contact lists
- client-tailored scenarios
- client incident details, logs, exports, tickets, screenshots, or PII

Client-specific materials must live in approved secure project storage and be referenced by engagement/case ID.

See also:
- SECURITY.md
