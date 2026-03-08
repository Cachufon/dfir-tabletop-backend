# INTERNAL - Tabletop Exercise Workflow

## Purpose
Deliver repeatable, discussion-based tabletop exercises (TTX) that validate incident response readiness, decision-making, escalation authority, and communications across technical and executive stakeholders.

This workflow is designed to be:
- usable by a human facilitator immediately, and
- compatible with future automation (scenario generation, inject orchestration, and AAR drafting).

## Scope boundaries
Tabletop Exercises are **discussion-based simulations**:
- No systems are touched.
- No forensic analysis is performed during the exercise.
- Outputs focus on process, governance, decision rights, and communications — not technical control validation.

## Canonical assets (source of truth)
TTX reusable content lives under:
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

## Data handling rule (critical)
This repo must contain **non-client-specific** reusable content only.
Do NOT commit:
- client IR plans, org charts, contact lists,
- client-tailored scenarios,
- any client incident details, logs, exports, tickets, or screenshots.

Client-specific materials must be stored in approved secure project storage and referenced by case/engagement ID.

## Roles
- Facilitator: leads session, controls pacing, delivers injects, forces decisions, manages branching.
- Scribe: captures inject log, decision log, communications log (optional), and action items.
- Participants: represent their functions and describe actions/decisions they would take.
- Observers (optional): silent unless invited; provide feedback during debrief only.

## Inputs (minimum viable)
- Target audience(s) and exercise duration (60/90/120 minutes)
- Business context (crown jewels, critical services, and top operational risks)
- Relevant constraints/redlines (recording policy, topics to avoid)
- Any existing IR plan or escalation guidance (stored outside git)

## Outputs (standard)
- Scenario YAML (client-tailored versions stored outside git)
- Facilitator guide (session run-sheet)
- Inject execution log + decision log (+ communications log optional)
- After-Action Report (AAR) + prioritized improvement plan (0/30/90 day timeframes)

---

## Workflow phases

### Phase 1: Intake & scoping
1) Confirm:
   - duration, format (virtual/in-person), and audience composition
   - objectives (3–5) and success criteria
   - constraints/redlines (e.g., no law enforcement discussion; no ransom payment discussion)
   - recording policy and handling of notes

2) Collect minimal context:
   - top 3 critical business services and “crown jewels”
   - relevant third parties (MSSP, key vendors) and comms stakeholders
   - decision rights: who can authorize containment, comms, and notifications

3) Select scenario category:
   - choose from dfir_backend/ttx/scenario_taxonomy.md

### Phase 2: Scenario development
1) Draft scenario using:
   - dfir_backend/ttx/scenario_template.md

2) Draft inject ladder:
   - 6–8 injects for a 90-minute session (typical)
   - each inject must force a decision, surface a gap, or validate a process

3) Author scenario in YAML:
   - store in dfir_backend/ttx/scenarios/ if generalized (non-client-specific)
   - store client-tailored YAML outside git

4) Prepare facilitation artifacts:
   - facilitator guide populated with scenario metadata
   - inject/decision logs ready for the scribe

### Phase 3: Pre-exercise coordination
1) Confirm roster (roles only) and schedule.
2) Send a short pre-read (1 page max), including:
   - objectives, constraints, and “state assumptions” rule
   - who to bring (exec, IT, security, legal/PR, etc.)
3) Confirm logistics:
   - meeting link, room setup, timing, and how injects will be delivered

### Phase 4: Conduct (facilitation)
1) Opening (5 minutes):
   - rules of engagement (no-fault learning, time-boxed decisions, confidentiality)
2) Context setup (5 minutes):
   - scenario framing and assumptions
3) Inject cycles (majority of session):
   - deliver inject participant_prompt verbatim
   - ask decision-forcing questions
   - time-box discussion and capture decisions + owners
4) Hotwash (10–15 minutes):
   - what worked, what slowed down, what was unclear, top improvements

### Phase 5: Scoring & synthesis
1) Facilitator assigns scores using:
   - dfir_backend/ttx/scoring_model.md
2) Ensure each dimension has:
   - 2–4 concrete examples
3) Mark priority gaps:
   - any score of 2 or below becomes an improvement plan priority

### Phase 6: After-Action Report (AAR) & improvement plan
1) Draft AAR using:
   - dfir_backend/ttx/after_action_report_template.md
2) Build improvement plan:
   - owned, time-boxed, realistic recommendations (0/30/90)
3) Internal QA:
   - remove unnecessary names/PII
   - validate that recommendations map to observed gaps
4) Deliver readout:
   - leadership summary + prioritized improvement plan
   - optional deeper technical/process workshop follow-on

---

## Quality gates (internal)
Before marking an exercise “complete”:
- [ ] Scenario aligns to objectives and audience (no rabbit holes)
- [ ] Decision log contains owners + timeframes for major actions
- [ ] Priority gaps are explicit and mapped to improvement plan items
- [ ] Client-sensitive info is not committed to git
- [ ] AAR executive summary is readable standalone (1 page)

End of workflow.
