# INTERNAL - TTX Inject Template

This template is used to design **one inject** for a tabletop exercise (TTX). Injects are ultimately stored in a scenario YAML file that conforms to:
- dfir_backend/ttx/schemas/ttx_scenario.schema.json

Use this template for drafting, review, and facilitation planning. Then translate the final content into YAML fields.

---

## 1) Inject design goals

A good inject should do at least one of the following:
- Force a decision (contain vs observe, notify vs wait, escalate vs handle locally)
- Reveal an information gap (what data/tool/process is missing?)
- Validate a process step (severity classification, escalation, comms approvals)
- Increase realism without adding technical rabbit holes

Keep injects:
- **Decision-focused**
- **Role-targeted** (who must respond?)
- **Time-boxed** (what must happen in the next 15–30 minutes?)
- **Short** (participant prompt typically <= 120 words)

---

## 2) Inject specification (draft)

### Inject metadata
- **Inject ID:** (e.g., i01, i02, i03)
- **Planned T+ (minutes):** (integer)
- **Delivery method:** (Verbal / Chat / Email / Slide)
- **Audience (roles):** (list roles, not names)

### Participant prompt (verbatim)
Write exactly what participants will see/hear.

> (paste participant-facing prompt here)

### Expected discussion prompts
List questions you expect the room to discuss (not the “right answer”).

- 
- 
- 

### Expected decisions
List the concrete decisions that should be made (who owns them, and by when).

- 
- 
- 

### Evaluation criteria
What does “good” look like for this inject? (Use rubric language where possible.)

- 
- 
- 

### Facilitator notes (NOT shown to participants)
Use this for:
- “If asked” details you can provide
- Steering guidance if the discussion stalls
- Reminders to capture specific decisions/owners

Facilitator notes:
- 

### Branching guidance (optional)
Describe how the scenario should adapt based on participant choices.

Examples:
- If participants contain immediately, emphasize business disruption and comms complexity.
- If participants delay containment, emphasize expanding scope and external impact.

Branching guidance:
- 

### Evidence references (optional; synthetic only)
List references to simulated artifacts (safe and non-client-specific).

- (e.g., SIM-IDP-ALERT-001)
- 

---

## 3) YAML mapping

When transferring this inject into a scenario YAML file, map fields as follows:

- Inject ID -> injects[].id
- Planned T+ (minutes) -> injects[].t_plus_min
- Delivery method -> injects[].delivery_method
- Audience (roles) -> injects[].audience[]
- Participant prompt -> injects[].participant_prompt
- Expected discussion prompts -> injects[].expected_discussion[]
- Expected decisions -> injects[].expected_decisions[]
- Evaluation criteria -> injects[].evaluation_criteria[]
- Facilitator notes -> injects[].facilitator_notes
- Branching guidance -> injects[].branching_guidance
- Evidence references -> injects[].evidence_refs[]

---

## 4) Common failure modes (avoid)

- Inject is purely technical and does not require a decision
- Prompt is too long, too vague, or contains multiple unrelated events
- No explicit owner for decisions (everyone assumes someone else will act)
- The facilitator supplies too much detail instead of asking what info to request
- The inject cadence is too slow (discussion drifts) or too fast (no decisions captured)
