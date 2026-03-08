# INTERNAL - TTX Exercise Package Checklist (CISA-style Packaging)

This checklist defines the standard artifacts that make up a **complete tabletop exercise package** for delivery.
It supports consistent delivery today and future automation tomorrow.

**Critical rule:** Client-specific materials MUST be stored in secure project storage (outside git). This repo contains reusable templates and generalized scenarios only.

---

## 1) Package contents (delivery standard)

### A) Pre-exercise
- [ ] Intake notes (filled from dfir_backend/ttx/intake_template.md) — stored outside git
- [ ] Participant invitation (tailored) — stored outside git
- [ ] Participant guide (tailored) — stored outside git
- [ ] Scenario YAML (tailored) — stored outside git
- [ ] Facilitator guide (tailored) — stored outside git
- [ ] Situation Manual (SitMan) (optional; tailored) — stored outside git
- [ ] Logistics plan (meeting link/room, inject delivery method, roster roles)

### B) During exercise
- [ ] Scribe logs (inject execution log, decision log, action items)
- [ ] Communications log (optional)

### C) Post-exercise
- [ ] Scoring worksheet (internal; optional to share)
- [ ] After-Action Report (AAR) + Improvement Plan (0/30/90)
- [ ] Executive readout (1-page) (optional)
- [ ] Participant feedback form + collected responses (optional)

---

## 2) Repo assets that support each package item

Reusable templates (in git):
- Intake template: dfir_backend/ttx/intake_template.md
- Participant invitation template: dfir_backend/ttx/participant_invitation_template.md
- Participant guide template: dfir_backend/ttx/participant_guide_template.md
- Facilitator guide template: dfir_backend/ttx/facilitator_guide_template.md
- Inject drafting template: dfir_backend/ttx/inject_template.md
- Scoring model: dfir_backend/ttx/scoring_model.md
- AAR template: dfir_backend/ttx/after_action_report_template.md
- Executive readout template: dfir_backend/ttx/executive_readout_template.md
- Feedback form template: dfir_backend/ttx/participant_feedback_form_template.md
- SitMan template: dfir_backend/ttx/situation_manual_template.md
- Taxonomy: dfir_backend/ttx/scenario_taxonomy.md
- Schema: dfir_backend/ttx/schemas/ttx_scenario.schema.json
- Generalized scenario library: dfir_backend/ttx/scenarios/

Workflow/runbooks (in git):
- Workflow: dfir_backend/workflows/ttx_workflow.md
- Playbook: dfir_backend/playbooks/tabletop_exercise_playbook.md
- Engagement runbook: dfir_backend/runbooks/ttx_engagement_runbook.md

AI-assist prompts (in git; optional, client-approved):
- Scenario YAML generation: dfir_backend/ai_assist/prompts/ttx_scenario_yaml_from_ir_plan.md
- AAR draft generation: dfir_backend/ai_assist/prompts/ttx_aar_from_scribe_notes.md

Validation (in git):
- Scenario validator: dfir_backend/ttx/scripts/validate_ttx_scenarios.py
- CI workflow: .github/workflows/validate_ttx_scenarios.yml

Packaging automation (in git):
- Package builder: dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py

---

## 3) Secure storage packaging (outside git)

For each engagement/case ID, store client-tailored artifacts outside git:
- <secure_storage>/ttx/<case_id>/
  - 00_admin/
  - 10_inputs/
  - 20_delivery/
  - 30_outputs/
  - 90_internal/

(See dfir_backend/runbooks/ttx_engagement_runbook.md)

---

## 4) Quality gates (before delivery)

Pre-exercise:
- [ ] Objectives are decision-focused and observable (not “review tooling”)
- [ ] Inject ladder fits duration (typical 6–8 injects for 90 min)
- [ ] Each inject forces a decision / surfaces a gap / validates governance
- [ ] Constraints/redlines captured and agreed
- [ ] Participant roster includes required roles for the scenario category

During:
- [ ] Decision log captures owners (roles) and timeframes
- [ ] Action items captured with owner + timeframe (0/30/90)

Post:
- [ ] AAR recommendations map directly to observed gaps
- [ ] AAR avoids audit language (discussion-based; no proof claims)
- [ ] Any numeric scoring preference honored (internal-only vs client-facing)
- [ ] Executive readout (if requested) aligns with AAR and does not introduce new claims
- [ ] Client identifiers/PII minimized as appropriate

---

## 5) Promotion rule (client-tailored -> generalized)

If a scenario proves reusable:
- Create a generalized, de-identified version for dfir_backend/ttx/scenarios/
- Ensure it conforms to schema and taxonomy
- Validate with dfir_backend/ttx/scripts/validate_ttx_scenarios.py
- Do NOT copy client identifiers or unique incident facts into git

---

End of checklist.
