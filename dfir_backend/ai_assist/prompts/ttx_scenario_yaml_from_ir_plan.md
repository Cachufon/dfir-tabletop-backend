# Prompt: Generate TTX Scenario YAML from Customer IR Plan + Intake Notes

## Purpose

Use this prompt to generate a **client-tailored tabletop exercise scenario** in YAML format that conforms to:
- `dfir_backend/ttx/schemas/ttx_scenario.schema.json`

This output is intended to be saved as:
- `<secure_storage>/ttx/<case_id>/20_delivery/scenario.yaml`

**Important:** Do not commit client-tailored scenarios to git.

---

## Inputs

Provide the model with:

1) Customer IR Plan (full text or key excerpts)
2) TTX Intake Notes (business context + crown jewels + critical services)
3) Audience / participant roles (roles only)
4) Duration (60/90/120 minutes)
5) Constraints / redlines (recording policy, topics to avoid, etc.)
6) Environment summary (high-level):
   - Identity/email platform (e.g., Okta/Entra/Google Workspace)
   - Cloud/IaaS (if applicable)
   - Endpoint/EDR (if applicable)
   - Key third parties (MSSP, critical vendors)
7) Industry + region (high level)

Optional (high value):
- Known prior incidents / concerns
- Severity classification scheme (if defined)
- Notification/communications approval workflow (if defined)

---

## Data handling / safety constraints (must follow)

- Do not include real employee names, personal emails, private phone numbers, or unnecessary PII.
- Prefer roles over names in scenario content.
- Do not fabricate facts about the customer environment.
- If a required detail is unknown, state an assumption explicitly in `scenario.assumptions`.
- Keep this a discussion-based tabletop:
  - no “run this command” steps,
  - no deep forensic analysis,
  - focus on decisions, authority, comms, and legal/regulatory decision points.
- For legal support context: focus on civil/regulatory posture; do not assume criminal investigation or law-enforcement engagement unless explicitly requested as an in-scope discussion topic.

---

## Instructions to the Model (v1)

You are an expert incident response facilitator and DFIR lead. Using the provided customer IR plan and intake notes:

### Step 1 — Extract and normalize key governance facts
Identify and summarize:
- Incident commander role (or closest equivalent)
- Escalation paths and thresholds (if present)
- Decision rights for:
  - containment actions that cause outage/disruption
  - external communications (press/customer statements)
  - notification decisions (client/partner/regulatory)
- Who must be engaged early (Legal/PR/HR/Finance) based on IR plan language
- Any explicit constraints/redlines in the IR plan

If missing, do not invent; add assumptions.

### Step 2 — Select scenario category
Choose **one** `scenario.category` from the canonical categories in:
- `dfir_backend/ttx/scenario_taxonomy.md`

Set `scenario.category` to match the taxonomy heading exactly (e.g., `SaaS / Identity`, `Ransomware / Extortion`, etc.).

### Step 3 — Generate a decision-focused inject ladder
Generate 6–8 injects for a 90-minute exercise (scale down/up for 60/120 minutes).
Each inject must:
- target specific audiences (roles),
- force at least one concrete decision,
- include evaluation criteria aligned to readiness and governance,
- avoid technical rabbit holes.

Cadence:
- i01 at T+0, then every ~10–15 minutes.

### Step 4 — Output valid YAML conforming to schema
Output YAML with:
- `version: 1`
- `scenario: { ... }` with required fields:
  - id, title, category, duration_minutes, audiences, objectives, assumptions
- `injects: [ ... ]` with required fields:
  - id, t_plus_min, delivery_method, audience, participant_prompt
And recommended fields:
- expected_discussion, expected_decisions, evaluation_criteria, facilitator_notes, branching_guidance, evidence_refs

Formatting rules:
- Use inject IDs `i01`, `i02`, `i03`, ...
- `t_plus_min` must be integers
- Keep `participant_prompt` concise (typically <= 120 words)
- Use `delivery_method` values like: `Verbal`, `Chat/Email`, `Slide`
- Use `evidence_refs` only for **synthetic** references like `SIM-IDP-ALERT-001` (do not reference real client ticket numbers)

### Step 5 — Branching guidance
Include branching guidance to adapt the scenario if participants choose:
- aggressive containment (emphasize business disruption + comms)
- delayed containment (emphasize expanding scope + external impact risk)

---

## Output requirements (strict)

Return ONLY the YAML.
- Do not include code fences.
- Do not include markdown.
- Do not include commentary before or after the YAML.
