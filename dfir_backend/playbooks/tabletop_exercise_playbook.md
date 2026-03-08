# Tabletop Exercise Playbook

## Purpose
This playbook guides analysts/facilitators through executing a **discussion-based** Tabletop Exercise (TTX) to test incident response readiness, decision-making, escalation authority, and communications across technical and executive stakeholders.

This playbook is aligned to the canonical workflow:
- dfir_backend/workflows/ttx_workflow.md

## Service Mapping
- Service: Tabletop Exercises

---

## Scope boundaries (critical)
A Tabletop Exercise is **not** hands-on incident response or a live-fire simulation.
- No customer systems are touched.
- No forensic analysis is performed during the exercise.
- Findings are based on observed discussion and stated actions, not proof of control effectiveness.

---

## Canonical assets (source of truth)
Reusable TTX content lives under:
- dfir_backend/ttx/

Key references:
- Scenario taxonomy: dfir_backend/ttx/scenario_taxonomy.md
- Scenario drafting worksheet: dfir_backend/ttx/scenario_template.md
- Inject drafting worksheet: dfir_backend/ttx/inject_template.md
- Facilitator guide template: dfir_backend/ttx/facilitator_guide_template.md
- Scoring model: dfir_backend/ttx/scoring_model.md
- AAR template: dfir_backend/ttx/after_action_report_template.md
- Scenario schema: dfir_backend/ttx/schemas/ttx_scenario.schema.json
- Scenario library: dfir_backend/ttx/scenarios/

---

## Data handling rule (do not violate)
This repo must contain **non-client-specific** reusable content only.

Do NOT commit:
- client IR plans, org charts, contact lists,
- client-tailored scenarios,
- any client incident details, logs, exports, tickets, screenshots, or PII.

Client-specific materials must be stored in approved secure project storage and referenced by case/engagement ID.

---

## Prerequisites

### Inputs (minimum viable)
- Exercise duration (60/90/120 minutes) and format (virtual/in-person)
- Target audience(s) and roles represented
- Business context: crown jewels, critical services, top operational risks
- Constraints/redlines (recording policy, topics to avoid)
- Existing IR plan and escalation guidance (optional; stored outside git)

### Tools required
- Facilitation platform (Zoom/Teams/in-person room)
- Shared notes or scribe document (internal)
- Timing mechanism (timer) for inject cadence
- Optional: slides or email/chat simulation method for inject delivery

### Permissions / approvals
- Approval to run the tabletop with required stakeholders
- Consent for recording if requested (and documented storage location)
- Agreement on confidentiality and distribution of the After-Action Report

---

## Workflow Steps

### 1) Define objectives and scope
- Confirm objectives (3–5) and success criteria.
- Confirm audiences (roles) and decision-makers (who can authorize key actions).
- Confirm constraints/redlines and recording policy.
- Select a scenario category from dfir_backend/ttx/scenario_taxonomy.md.

**Output:** Scoped exercise definition (internal notes).

---

### 2) Develop scenario and inject ladder
- Draft scenario using:
  - dfir_backend/ttx/scenario_template.md
- Draft injects using:
  - dfir_backend/ttx/inject_template.md
- Ensure inject ladder escalates impact progressively and forces decisions.

Author final scenario in YAML:
- Generalized (reusable) scenarios may be stored in: dfir_backend/ttx/scenarios/
- Client-tailored scenarios must be stored outside git (secure project storage)

**Output:** Scenario YAML + facilitation plan.

---

### 3) Prepare facilitation artifacts
- Populate facilitator guide:
  - dfir_backend/ttx/facilitator_guide_template.md
- Prepare scribe logs:
  - Inject execution log
  - Decision log
  - Communications log (optional)
  - Action items list
- Review scoring dimensions:
  - dfir_backend/ttx/scoring_model.md

**Output:** Facilitator run-sheet + scribe-ready logs.

---

### 4) Pre-exercise coordination
- Confirm roster (roles only), timing, and logistics.
- Send participant pre-read (1 page max):
  - objectives, constraints, “state assumptions” rule, and session format
- Confirm how injects will be delivered (verbal, email, chat, slides).

**Output:** Confirmed session readiness.

---

### 5) Conduct the tabletop (facilitation)
Recommended structure:
- Opening (5 min): rules of engagement (no-fault learning, time-boxed decisions)
- Context (5 min): scenario framing and assumptions
- Inject cycles (majority): deliver inject prompts verbatim, force decisions, capture owners/timeframes
- Hotwash (10–15 min): what worked, what slowed down, unclear decision rights, top improvements

**Output:** Completed inject/decision/action logs.

---

### 6) Score and synthesize observations
- Score dimensions using:
  - dfir_backend/ttx/scoring_model.md
- Record 2–4 concrete examples per dimension.
- Flag priority gaps:
  - any score of 2 or below becomes an improvement plan priority.

**Output:** Scoring worksheet + prioritized gaps.

---

### 7) Draft After-Action Report (AAR) and improvement plan
- Draft AAR using:
  - dfir_backend/ttx/after_action_report_template.md
- Ensure improvement plan is:
  - owned (role), time-boxed (0/30/90), and realistic
- Internal QA:
  - remove unnecessary names/PII
  - confirm each recommendation maps to an observed gap

**Output:** Final AAR + improvement plan.

---

### 8) Deliver customer readout and closeout
- Present executive summary first, then key decisions, then prioritized improvements.
- Provide a clear next-step path (optional):
  - targeted tabletop follow-on for a specific audience, or
  - compromise assessment recommendation based on observed visibility gaps.

**Output:** Readout completed; deliverables delivered per agreed distribution.

---

## Readiness signals to observe (during exercise)
- Whether an incident commander/owner is identified early
- How quickly participants time-box and make decisions
- Whether escalation thresholds and decision rights are clear
- Whether communications governance is defined (who approves, what is said, when)
- Whether Legal/PR is engaged appropriately for notification decisions
- Whether participants can articulate what evidence/logs they would request and why
- Whether action items are captured with owners and timeframes

---

## Common Pitfalls
- Scenario is too complex for the allotted time (no decisions captured).
- Missing key roles (Exec, Legal/PR, Finance) leading to unrealistic outcomes.
- Facilitator over-supplies technical details instead of asking what info is needed.
- No time-boxing; discussion drifts and inject cadence collapses.
- Insufficient scribing; decisions and owners are not recorded.
- Deliverable inflation: AAR becomes a general security roadmap instead of exercise-driven improvements.

---

## Output Artifacts
- Scenario YAML (client-tailored version stored outside git)
- Facilitator guide (run-sheet)
- Inject execution log + decision log (+ communications log optional)
- After-Action Report (AAR) + prioritized improvement plan (0/30/90 days)
- Optional: executive readout summary (1 page)
