# Tabletop Exercise Engagement Runbook (v1)

## 0. Preconditions
- Confirm exercise format: Virtual or In-person
- Confirm duration: 60 / 90 / 120 minutes
- Confirm target audience(s) and required roles (Exec, IT, Security, Legal/PR, etc.)
- Confirm objectives (3–5) and success criteria
- Confirm constraints/redlines (topics to avoid, boundaries, “discussion only”)
- Confirm recording policy (Yes/No) and where recordings/notes will be stored (if Yes)
- Confirm confidentiality expectations and deliverable distribution list
- Confirm customer POC(s) and scheduling
- Create an engagement/case ID (recommended): TTX-YYYYMMDD-<CLIENT>-<SHORTDESC>

Reference:
- dfir_backend/workflows/ttx_workflow.md
- dfir_backend/playbooks/tabletop_exercise_playbook.md
- dfir_backend/ttx/facilitator_guide_template.md
- dfir_backend/ttx/scoring_model.md
- dfir_backend/ttx/after_action_report_template.md
- dfir_backend/ttx/scenario_taxonomy.md
- dfir_backend/ttx/schemas/ttx_scenario.schema.json

## 1. Create Engagement Workspace (OUTSIDE GIT)
Client-specific materials must be stored in approved secure project storage (NOT in this repo).

Create a folder:
- <secure_storage>/ttx/<case_id>/

Recommended structure:
- 00_admin/
  - scope_and_assumptions.md
  - stakeholder_roles.md (roles only)
  - meeting_logistics.md
- 10_inputs/
  - client_docs/ (IR plan, escalation guides, etc.)
  - intake_notes.md
- 20_delivery/
  - scenario.yaml (client-tailored)
  - facilitator_guide.md
  - scribe_logs.md (inject log, decision log, action items)
- 30_outputs/
  - after_action_report.md
  - improvement_plan.md (or included in AAR)
  - executive_readout.md (optional)
- 90_internal/
  - qa_notes.md
  - internal_scoring.md (if numeric scores are not shared externally)

Critical data handling rule:
- Do NOT commit client IR plans, org charts, contact lists, incident details, or tailored scenarios to git.

Reference:
- dfir_backend/ttx/README.md
- SECURITY.md

## 2. Intake & Scoping Checklist
Capture only what is needed to tailor the scenario and force high-quality decisions.

Minimum intake:
- Business context:
  - top 3 critical services
  - crown jewels (data, systems, revenue pathways)
  - operational constraints (uptime, client commitments)
- Stakeholder roles present (roles only; avoid names in drafts)
- Existing IR governance:
  - incident commander role (or who would act as IC)
  - escalation thresholds (if any)
  - communications approval process (who can speak externally)
- Constraints/redlines:
  - topics to avoid (e.g., law enforcement discussion)
  - “no-fault learning” confirmation
  - recording policy

Optional intake (high value):
- Known high-risk threats for their industry (high level)
- Top concerns from leadership (e.g., brand impact, client notification)
- Third parties that would be involved (MSSP, key vendors)

Output:
- <secure_storage>/ttx/<case_id>/10_inputs/intake_notes.md
- <secure_storage>/ttx/<case_id>/00_admin/scope_and_assumptions.md

## 3. Scenario Selection & Tailoring
1) Select scenario category from:
- dfir_backend/ttx/scenario_taxonomy.md

2) Choose a starting scenario:
- If a generalized scenario exists in dfir_backend/ttx/scenarios/, copy it into secure project storage and tailor there.
- If no suitable scenario exists, author a new scenario in secure project storage first; later promote a generalized version to git (after review and de-identification).

3) Tailoring rules (do not violate):
- Do not include real client names, domains, emails, system hostnames, or incident facts in any scenario committed to git.
- Keep scenarios decision-focused (avoid technical rabbit holes).
- Ensure inject ladder escalates impact progressively.

4) Ensure scenario YAML is complete and consistent:
- scenario.objectives are observable and decision-focused
- scenario.assumptions allow discussion to proceed without deep technical work
- each inject forces a decision, surfaces a gap, or validates governance/comms/legal triggers
- inject cadence supports time-boxing (typically every 10–15 minutes for a 90-min session)

Output:
- <secure_storage>/ttx/<case_id>/20_delivery/scenario.yaml

Reference:
- dfir_backend/ttx/scenario_template.md
- dfir_backend/ttx/inject_template.md
- dfir_backend/ttx/schemas/ttx_scenario.schema.json

## 4. Prepare Facilitation Artifacts
1) Create facilitator guide (copy template into secure storage and fill):
- dfir_backend/ttx/facilitator_guide_template.md

Save as:
- <secure_storage>/ttx/<case_id>/20_delivery/facilitator_guide.md

2) Prepare scribe logs (in the facilitator guide or a separate scribe doc):
- Inject execution log
- Decision log
- Communications log (optional)
- Action items list

3) Plan inject delivery method:
- Verbal (recommended baseline)
- Chat/Email (optional, increases realism)
- Slides (optional)

4) Internal dry run (recommended):
- Read inject prompts aloud and verify they force decisions and fit the timeline.

Output:
- <secure_storage>/ttx/<case_id>/20_delivery/facilitator_guide.md
- <secure_storage>/ttx/<case_id>/20_delivery/scribe_logs.md (if separate)

## 5. Conduct the Exercise
Follow:
- dfir_backend/ttx/facilitator_guide_template.md (as the run-sheet)

Facilitation requirements:
- Read participant prompts verbatim
- Time-box decisions (force binary choices if needed)
- Capture: decision, owner (role), rationale, info requested, follow-up actions with timeframe
- Keep the room out of technical rabbit holes:
  - Ask what information they would request and why, instead of providing details

Outputs captured live:
- Inject execution log
- Decision log
- Action items list
- Communications log (optional)

Save to:
- <secure_storage>/ttx/<case_id>/20_delivery/scribe_logs.md

## 6. Scoring & Synthesis (Post-Session)
1) Score using:
- dfir_backend/ttx/scoring_model.md

2) For each dimension:
- assign a 1–5 score
- record 2–4 concrete examples

3) Apply priority gap rule:
- any score of 2 or below becomes a required improvement plan priority

Save internal scoring notes to:
- <secure_storage>/ttx/<case_id>/90_internal/internal_scoring.md

## 7. After-Action Report (AAR) & Improvement Plan
1) Draft AAR using:
- dfir_backend/ttx/after_action_report_template.md

2) Ensure improvement plan items are:
- specific and actionable
- owned (role)
- time-boxed (0/30/90)
- mapped directly to observed gaps

3) Keep deliverable clean:
- avoid unnecessary names/PII
- avoid speculation; clearly label assumptions
- do not claim technical control effectiveness

Save to:
- <secure_storage>/ttx/<case_id>/30_outputs/after_action_report.md

## 8. Internal QA Checklist
Before delivering:
- Scope, constraints, and assumptions are explicit
- Executive summary is readable standalone (1 page)
- Every major recommendation maps to an observed gap
- Priority gaps (score <= 2) are included in the improvement plan
- No sensitive client identifiers are included unnecessarily
- Language avoids audit claims (discussion-based)

Save QA notes (optional) to:
- <secure_storage>/ttx/<case_id>/90_internal/qa_notes.md

## 9. Delivery Checklist
- Confirm distribution list and confidentiality handling
- Deliver AAR + improvement plan
- Conduct a readout (exec summary first)
- Capture follow-up actions and owners
- Propose follow-on validation (optional):
  - targeted TTX for a specific audience (Exec-only, Legal/PR, IT/Security)
  - compromise assessment recommendation based on observed visibility gaps

End of runbook.
