# Tabletop Exercises (TTX) — Service Overview

Tabletop Exercises (TTX) are **facilitated, discussion-based incident simulations** designed to test and improve incident response readiness across technical and executive stakeholders.

The focus is on:
- decision-making under time pressure,
- escalation and authority clarity,
- communications governance (internal/external),
- legal/regulatory awareness,
- and actionable improvement planning.

This is not a live-fire exercise and does not validate technical control effectiveness.

---

## Typical customers
- Security and IT leaders maturing incident response capabilities
- SaaS and technology companies with high client trust sensitivity
- Regulated organizations that need demonstrable preparedness
- Leadership teams seeking clarity on decision rights during major incidents

---

## What’s in scope
- Scenario selection and tailoring to business context and likely threats
- Facilitated tabletop session(s) for defined audiences (Exec, IT, Security, Legal/PR, etc.)
- Structured capture of decisions, gaps, and action items
- After-Action Report (AAR) and prioritized improvement plan (0/30/90 days)
- Optional executive readout and follow-on recommendations

---

## Out of scope
- Hands-on-keyboard incident response or forensic investigations during the exercise
- Live technical testing (purple teaming, red teaming, control validation)
- Building a full crisis communications program end-to-end
- Providing legal advice or acting as external counsel

---

## Engagement options (recommended packaging)
### Option A — TTX Core (single exercise)
- 60–120 minute facilitated session (typical: 90 minutes)
- Single scenario and inject ladder
- AAR + improvement plan

### Option B — TTX+ (expanded audience or complexity)
- Two sessions (e.g., Exec-only + Technical; or two scenarios)
- Greater emphasis on communications and decision rights alignment
- Consolidated improvement plan

### Option C — TTX Program (quarterly cadence)
- Quarterly exercises with tracked improvement items
- Progressive scenario complexity and measurable readiness uplift
- Optional integration with compromise assessment recommendations

---

## Inputs (minimum viable)
- Target audience(s), duration, and format (virtual/in-person)
- Business context:
  - top critical services
  - crown jewels (data/systems/revenue pathways)
  - operational constraints (uptime/client commitments)
- Decision rights and escalation expectations (who approves what)
- Constraints/redlines (recording policy, topics to avoid)

Optional (high value):
- Existing incident response plan and escalation guides
- Third-party dependencies (MSSP, key vendors)
- Leadership concerns and key business risks

Note:
- Client contact lists, org charts, and IR plans are handled as client-sensitive inputs and must be stored in approved secure project storage (not committed to git).

---

## Outputs (standard)
- Scenario (client-tailored version stored in secure project storage)
- Facilitator guide (run-sheet)
- Scribe logs:
  - inject execution log
  - decision log
  - action items list
  - communications log (optional)
- After-Action Report (AAR) and prioritized improvement plan (0/30/90 days)
- Optional 1-page executive readout

---

## Delivery backbone (internal source of truth)
Reusable delivery assets (templates, taxonomy, generalized scenarios) live in:
- dfir_backend/ttx/

Workflow and runbooks:
- dfir_backend/workflows/ttx_workflow.md
- dfir_backend/playbooks/tabletop_exercise_playbook.md
- dfir_backend/runbooks/ttx_engagement_runbook.md

---

## Common follow-on work (optional)
- Targeted tabletop for a specific function (Exec-only, Legal/PR, IT/Security)
- Compromise assessment recommendation based on observed visibility gaps
- Incident response plan updates based on improvement plan outcomes
