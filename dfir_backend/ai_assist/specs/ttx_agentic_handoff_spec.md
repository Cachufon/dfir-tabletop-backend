# INTERNAL - Agentic TTX Handoff Spec (AI Engineering)

## 0) Purpose
This document defines the implementation contract for an **agentic tabletop exercise (TTX) copilot** that:
- ingests client inputs (IR plan + intake context),
- generates a **schema-valid scenario YAML** (dfir_backend/ttx/schemas/ttx_scenario.schema.json),
- supports facilitator-led delivery (inject pacing, branching guidance, scribing support),
- drafts AAR + improvement plan from scribe logs,
- and enforces strict data-handling guardrails.

This spec is designed so AI engineering can implement a deterministic, testable system without making “product decisions” implicitly.

---

## 1) Non-goals
The system must NOT:
- run a tabletop fully autonomously without a human facilitator,
- make real-world security decisions for the client,
- claim breach confirmation or technical control effectiveness,
- store client-sensitive materials in git,
- retain client data outside approved secure storage policies.

---

## 2) Definitions
- **Generalized scenario**: reusable, de-identified scenario safe to store in git (dfir_backend/ttx/scenarios/).
- **Client-tailored scenario**: customized for a client; must be stored in secure project storage outside git.
- **Scenario YAML**: the canonical format for exercise content; must validate against schema + taxonomy.
- **TTX package**: SitMan + facilitator packet + participant guide + scribe logs + manifest (generated from YAML).

---

## 3) Primary user roles
- **Facilitator (DFIR)**: human owner of exercise delivery; approves scenario; controls pacing; approves outputs.
- **Scribe**: captures inject log, decision log, action items, comms log.
- **Participants**: client stakeholders (roles).
- **Reviewer (internal QA)**: optional; validates outputs are safe, accurate, and aligned to scope.

---

## 4) Inputs (minimum viable)
All inputs must be treated as client-sensitive by default.

### 4.1 Required inputs
- Intake notes (from dfir_backend/ttx/intake_template.md, filled in secure storage)
- Audience roles + duration (60/90/120)
- Constraints/redlines (topics to avoid, recording policy, etc.)
- Industry + region (high level)

### 4.2 Optional inputs (high value)
- Client incident response plan (IR plan), escalation guides, comms policies
- Tooling stack summary (IdP/email/EDR/cloud) – high level only
- Known prior incidents / leadership concerns

### 4.3 Threat intel (optional, controlled)
Threat intel may be used only if:
- sources are approved,
- citations/attribution are captured in internal notes,
- and intel is used to tailor *scenario realism* (not to assert client-specific facts).

---

## 5) Outputs
### 5.1 Required outputs (MVP)
- Scenario YAML conforming to schema:
  - dfir_backend/ttx/schemas/ttx_scenario.schema.json
- Scenario category must match taxonomy exactly:
  - dfir_backend/ttx/scenario_taxonomy.md

### 5.2 Optional outputs (v1)
- Delivery package artifacts (from YAML):
  - sitman.md
  - facilitator_packet.md
  - participant_guide.md
  - scribe_logs.md
  - package_manifest.md
- Draft AAR + improvement plan (from scribe logs):
  - aligned to dfir_backend/ttx/after_action_report_template.md
- Draft executive readout (1 page):
  - aligned to dfir_backend/ttx/executive_readout_template.md

### 5.3 Storage rules
- Client-tailored outputs must be written to secure project storage (outside git).
- Any “example” generated in repo must be synthetic and de-identified.

---

## 6) Guardrails (hard requirements)
### 6.1 Data handling
- No client data in git.
- No secrets/credentials in prompts or outputs.
- Prefer roles over names.
- PII minimization: do not include personal emails/phones, etc.
- Explicit “unknown” instead of fabricated details.

### 6.2 Output truthfulness
- Do not invent client environment details.
- When details are missing, write assumptions in scenario.assumptions.
- Use the phrase (or equivalent) in AAR:
  - “This AAR documents observed discussion and stated actions. It is not an audit and does not prove technical control effectiveness.”

### 6.3 Human approval checkpoints
- Scenario YAML must be reviewed and approved by the facilitator before being marked ready.
- AAR + executive readout must be reviewed and approved before delivery.

### 6.4 Auditability
System must log (internally):
- what inputs were used (filenames/IDs, not full content if avoidable),
- when generation occurred,
- schema validation results,
- and a record of approvals (who approved, when).

---

## 7) System architecture (modular)
Implement as separate components to enable swap/upgrade:

1) **Ingestion + Extraction**
   - Inputs: IR plan + intake notes
   - Output: normalized “governance model” (roles, escalation thresholds, comms approvals, constraints)

2) **Scenario Planner**
   - Inputs: governance model + intake context + audience/duration
   - Output: scenario outline (category choice, objectives, inject ladder plan)

3) **Scenario YAML Generator**
   - Inputs: scenario outline
   - Output: schema-valid YAML

4) **Validator**
   - Runs:
     - schema validation (JSON schema)
     - taxonomy validation (category must match)
     - policy checks (inject ordering, ids, t_plus_min <= duration)
   - Output: pass/fail + errors
   - Must block “ready” state on failure.

5) **Package Builder (optional)**
   - Uses existing logic patterns:
     - dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py
   - Output: sitman, facilitator packet, participant guide, scribe logs, manifest

6) **Scribe → AAR Generator (optional)**
   - Inputs: scribe logs + scenario YAML
   - Output: Markdown AAR aligned to template + improvement plan table

---

## 8) Canonical data model
### 8.1 Scenario YAML (authoritative)
Must conform to:
- dfir_backend/ttx/schemas/ttx_scenario.schema.json

Conventions:
- inject ids: i01, i02, ...
- t_plus_min: integer minutes from start
- prompts are concise and decision-focused

### 8.2 Governance model (internal JSON)
Extraction output should normalize:
- incident commander role (or closest)
- escalation triggers (what triggers exec/legal)
- authority matrix (who approves containment/comms/notifications)
- comms approval workflow
- constraints/redlines
- severity classification (if defined)

This is internal; it should not be committed to git.

---

## 9) API contracts (implementation guidance)
These APIs can be internal functions, a service, or CLI wrappers. The important part is the contract.

### 9.1 Generate scenario outline
Input:
- intake_notes_text
- audience_roles[]
- duration_minutes
- constraints[]
- optional ir_plan_text

Output:
- outline JSON:
  - category
  - objectives[]
  - assumptions[]
  - inject_plan[] (id + t_plus_min + audience + decision_focus)

### 9.2 Generate scenario YAML
Input:
- outline JSON

Output:
- scenario_yaml_text (YAML)
- validation_result (pass/fail + errors)

### 9.3 Generate AAR draft
Input:
- scenario_yaml_text
- scribe_logs_text
- scoring_preference (numeric vs qualitative)

Output:
- aar_markdown_text

---

## 10) Determinism requirements
To keep outputs repeatable and reduce “creative drift”:
- Use schema-guided generation (structured output / function calling or equivalent).
- Use low temperature for generation.
- Validate outputs and re-try generation only if validation fails, with explicit correction prompts.
- Do not freeform modify scenario taxonomy or schema.

---

## 11) Testing & evaluation
### 11.1 Unit tests (minimum)
- Scenario YAML generated validates against JSON schema.
- scenario.category matches taxonomy headings exactly.
- Inject IDs are iNN and times are ordered.
- t_plus_min does not exceed duration_minutes.

### 11.2 Quality tests (human review rubric)
- Each inject forces a decision or surfaces a gap.
- Objectives are observable and decision-focused.
- No technical rabbit holes (“run command X”) in participant prompts.
- Assumptions cover missing details explicitly (no hallucinations).

### 11.3 Safety tests
- No names/emails/PII in outputs when not provided.
- No secrets appear in outputs.
- “Unknown” used instead of fabricated details.

---

## 12) Implementation milestones
### MVP (2–4 weeks engineering time, rough)
- Ingestion + extraction (basic)
- Scenario outline generation
- Scenario YAML generation + validation gate
- Save outputs to secure storage
- Manual facilitator approval flow

### v1
- Package generation
- Scribe-to-AAR draft generation
- Basic UI/CLI for facilitator workflows
- Audit logs + approval tracking

### v2
- Branch-aware inject orchestration (decision-driven pacing)
- Threat intel enrichment (controlled sources)
- Scenario library retrieval (select closest generalized scenario as base)
- Multi-audience exercise programs (Exec-only + technical sessions)

---

## 13) Integration points with this repo
- Schema: dfir_backend/ttx/schemas/ttx_scenario.schema.json
- Taxonomy: dfir_backend/ttx/scenario_taxonomy.md
- Templates: dfir_backend/ttx/*.md
- Validator script pattern: dfir_backend/ttx/scripts/validate_ttx_scenarios.py
- Package builder pattern: dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py
- AI prompts (reference): dfir_backend/ai_assist/prompts/

End of spec.
