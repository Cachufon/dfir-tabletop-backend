# INTERNAL - TTX Scenario Template (Drafting Worksheet)

This document is a **drafting worksheet** for authoring a tabletop exercise (TTX) scenario.
Final scenarios should be stored as **YAML** under:
- dfir_backend/ttx/scenarios/

All scenario YAML files must conform to:
- dfir_backend/ttx/schemas/ttx_scenario.schema.json

---

## 1) Scenario metadata (draft)

- **Scenario ID:** (stable id, e.g., ttx-saas-identity-001)
- **Title:**
- **Category:** (use a category from dfir_backend/ttx/scenario_taxonomy.md)
- **Planned duration (minutes):** (e.g., 60 / 90 / 120)
- **Audiences (roles):** (e.g., Executive, IT, Security, Legal/PR)

---

## 2) Scenario narrative and context (draft)

### Summary (2–4 sentences)
Write a short summary suitable for a client-facing AAR.

- 

### Threat context (2–6 sentences)
Describe how the adversary operates in this scenario (high level only).

- 

### Business context (2–6 sentences)
Describe what the organization relies on and what makes this scenario high impact (clients, uptime, revenue, brand).

- 

---

## 3) Objectives, assumptions, and success criteria (draft)

### Objectives (3–5 bullets)
Objectives should be observable (decisions made, comms executed, escalation clarity tested).

- 
- 
- 

### Assumptions (3–8 bullets)
Assumptions allow the discussion to progress without technical rabbit holes.

- 
- 
- 

### Constraints / redlines (optional)
Examples: “discussion only,” “no ransom payment discussion,” “no law enforcement engagement.”

- 

### Out of scope (optional)
Examples: deep forensics, precise log queries, malware reverse engineering.

- 

### Success criteria (3–6 bullets)
Define what “good” looks like for decision quality, authority, and coordination.

- 
- 
- 

### Pre-read (optional)
What participants should know before joining.

- 

---

## 4) Facilitator notes (draft)

Use this section for:
- pacing guidance
- common rabbit holes to avoid
- branching triggers (contain vs observe, notify vs wait)
- “if asked” details you can provide

Facilitator notes:
- 

---

## 5) Inject ladder (draft)

Design injects to:
- force decisions,
- surface information gaps,
- validate escalation/comms/legal decision points,
- and increase impact progressively.

Recommended cadence for 90 minutes:
- 6–8 injects, delivered every ~10–15 minutes.

For each inject, use dfir_backend/ttx/inject_template.md during drafting.

Inject list (draft):
- Inject i01 @ T+__ min — audience: ______ — decision focus: ______
- Inject i02 @ T+__ min — audience: ______ — decision focus: ______
- Inject i03 @ T+__ min — audience: ______ — decision focus: ______
- Inject i04 @ T+__ min — audience: ______ — decision focus: ______
- Inject i05 @ T+__ min — audience: ______ — decision focus: ______
- Inject i06 @ T+__ min — audience: ______ — decision focus: ______

---

## 6) YAML skeleton (copy/paste and fill)

Copy this into a new file under dfir_backend/ttx/scenarios/ and fill in values.
Keep content **non-client-specific**.

version: 1

scenario:
  id: "ttx-REPLACE-ME"
  title: "REPLACE ME"
  category: "REPLACE ME"
  duration_minutes: 90
  audiences:
    - "Executive"
    - "IT"
    - "Security"
    - "Legal/PR"
  summary: >
    REPLACE ME
  threat_context: >
    REPLACE ME
  business_context: >
    REPLACE ME
  objectives:
    - "REPLACE ME"
  assumptions:
    - "REPLACE ME"
  constraints:
    - "This is a discussion exercise only; no systems are touched."
  success_criteria:
    - "REPLACE ME"
  pre_read:
    - "REPLACE ME"
  out_of_scope:
    - "REPLACE ME"
  facilitator_notes: >
    REPLACE ME

injects:
  - id: i01
    t_plus_min: 0
    delivery_method: "Verbal"
    audience:
      - "Security"
      - "IT"
    participant_prompt: >
      REPLACE ME
    expected_discussion:
      - "REPLACE ME"
    expected_decisions:
      - "REPLACE ME"
    evaluation_criteria:
      - "REPLACE ME"
    branching_guidance: "REPLACE ME"
    facilitator_notes: "REPLACE ME"
    evidence_refs:
      - "SIM-REPLACE-ME-001"

---

## 7) Review checklist (before marking scenario “Ready”)

- [ ] Scenario is non-client-specific (no real names/domains/incidents)
- [ ] Objectives are decision-focused and observable
- [ ] Injects force decisions and escalate impact progressively
- [ ] Each inject has clear audience targeting and time-boxed decisions
- [ ] Facilitator notes include pacing and “if asked” details
- [ ] Scenario YAML conforms to dfir_backend/ttx/schemas/ttx_scenario.schema.json
