# INTERNAL - Tabletop Exercises (TTX)

This directory contains **reusable, non-client-specific** assets for designing and delivering cybersecurity tabletop exercises (TTX).

TTX are **discussion-based simulations**:
- No systems are touched.
- No forensic analysis is performed during the exercise.
- Outputs focus on decisions, escalation/authority, communications, and improvement planning.

---

## Critical data handling rule

This repo contains reusable content only. Do NOT commit:
- client IR plans, org charts, contact lists
- client-tailored scenarios or deliverables
- any client logs, exports, tickets, screenshots, incident facts, or PII
- any credentials, tokens, or secrets

Client-tailored artifacts must be stored in approved **secure project storage** outside git and referenced by engagement/case ID.

---

## Directory layout

- scenario_taxonomy.md
  - Canonical scenario categories (authoritative list for scenario.category)

- scenario_template.md
  - Drafting worksheet + YAML skeleton for new scenarios

- inject_template.md
  - Drafting worksheet for a single inject

- facilitator_guide_template.md
  - Facilitator run-sheet + scribe tables (inject/decision/comms/action logs)

- scoring_model.md
  - Readiness scoring dimensions and behavioral anchors

- after_action_report_template.md
  - After-Action Report (AAR) + improvement plan template

- executive_readout_template.md
  - 1-page executive readout template (copy and tailor outside git)

- intake_template.md
  - Intake questions (copy into secure storage and fill there)

- participant_invitation_template.md
  - Email/calendar invite text (copy into secure storage and tailor there)

- participant_guide_template.md
  - Short participant pre-read (shareable; tailor outside git)

- participant_feedback_form_template.md
  - Post-exercise feedback form template (responses stored outside git)

- situation_manual_template.md
  - Situation Manual (SitMan) template (participant-facing; tailor outside git)

- exercise_package_checklist.md
  - Checklist for a complete “exercise package” (CISA-style packaging)

- schemas/
  - ttx_scenario.schema.json
    - JSON schema used to validate scenario YAML files

- scenarios/
  - Generalized (non-client-specific) scenario YAML library

- scripts/
  - validate_ttx_scenarios.py
    - Validates scenario YAML files against schema + policy checks
  - build_ttx_package_from_yaml.py
    - Generates a delivery “package” (SitMan, facilitator packet, scribe logs, participant guide) from a scenario YAML
  - requirements.txt
    - Python dependencies for scripts
  - README.md
    - How to run scripts safely

---

## Scenario format (YAML)

All scenario YAML files should conform to:
- schemas/ttx_scenario.schema.json

Conventions:
- scenario.id: stable identifier (e.g., ttx-saas-identity-001)
- inject.id: i01, i02, i03...
- t_plus_min: integer minutes from exercise start
- participant_prompt: exact text participants receive
- facilitator_notes: details not shown to participants (branching, “if asked” info)
- evidence_refs: optional references to simulated artifacts (safe, synthetic)

---

## Quickstart (internal)

### 1) Validate scenario YAML files (recommended before use)
From repo root:
- python3 dfir_backend/ttx/scripts/validate_ttx_scenarios.py

This checks:
- JSON schema validity
- scenario.category matches scenario_taxonomy.md
- inject ordering and basic inject ID conventions

### 2) Build a delivery package from a scenario YAML
Use for client-tailored scenarios stored outside git.

Example:
- python3 dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py --input <path_to_scenario.yaml> --out-dir <secure_output_dir>

Safety guardrail:
- The build script refuses to write outputs inside the git repo by default.
- Use --allow-in-repo ONLY for synthetic examples.

---


## Demo / Examples

Use the synthetic end-to-end demo runner to generate complete example case outputs outside git:
- Script: `dfir_backend/ttx/scripts/seed_example_cases_and_run_end_to_end.py`
- Details: `dfir_backend/ttx/examples/README.md`

Default output root:
- `~/ttx_cases/examples`

## AI assistance (optional; client-approved only)

Reusable prompts live in:
- dfir_backend/ai_assist/prompts/

TTX prompts:
- ttx_scenario_yaml_from_ir_plan.md
- ttx_aar_from_scribe_notes.md

Rule:
- Generated client-tailored outputs must be stored outside git.
