# INTERNAL - Tabletop Exercise Facilitator Guide Template

This document is the facilitator run-sheet used to conduct a tabletop exercise (TTX).
It is designed to pair with a YAML scenario file that conforms to:
- dfir_backend/ttx/schemas/ttx_scenario.schema.json

---

## 1) Exercise metadata

- **Engagement / Case ID:**
- **Client / Organization:**
- **Date:**
- **Timezone:**
- **Planned duration (minutes):**
- **Scenario YAML path:**
- **Scenario ID:**
- **Scenario title:**
- **Scenario category:**
- **Facilitator:**
- **Co-facilitator (optional):**
- **Scribe / Note-taker:**
- **Observers (optional):**
- **Recording policy (Yes/No) + storage location (if Yes):**
- **Redlines / constraints (copy from scenario YAML):**

---

## 2) Participant roster (roles only)

List roles only (do not include names in client-facing outputs unless required).

- Executive:
- IT:
- Security:
- Legal:
- PR / Comms:
- HR:
- Product / Engineering:
- Finance:
- Third-party / Vendor reps (if applicable):

---

## 3) Objectives, assumptions, and success criteria (copy from scenario YAML)

### Objectives
- 
- 
- 

### Assumptions
- 
- 
- 

### Success criteria
- 
- 
- 

---

## 4) Rules of engagement (read aloud)

1. **No-fault learning environment:** This exercise is to improve readiness, not to grade individuals.
2. **Discussion-based:** No systems are touched; we focus on decisions, communications, and process.
3. **State assumptions:** If information is missing, participants should clearly state what they assume.
4. **Time-boxed decisions:** The facilitator may force a decision to keep the exercise moving.
5. **One conversation at a time:** Avoid side threads; use the “parking lot” for later discussion.
6. **Confidentiality:** Treat discussion as sensitive unless explicitly stated otherwise.

---

## 5) Roles during the session

- **Facilitator:** Drives pacing, reads injects, asks decision-forcing questions, controls branches.
- **Scribe:** Captures decisions, owners, rationale, gaps, and action items in the logs below.
- **Participants:** Describe what they would do, who owns it, and what information they need.
- **Observers (optional):** Silent unless asked; capture separate notes for debrief.

---

## 6) Materials checklist (before starting)

- [ ] Scenario YAML available and reviewed (scenario + injects + facilitator notes)
- [ ] Inject log + decision log tables ready for scribe
- [ ] Scoring dimensions available (dfir_backend/ttx/scoring_model.md)
- [ ] After-action report template available (dfir_backend/ttx/after_action_report_template.md)
- [ ] Attendance captured (roles only)
- [ ] Timing plan set (inject cadence)

---

## 7) Session flow (recommended 60–120 minutes)

Adjust timing to your duration.

### 0–5 min: Opening
- [ ] Welcome + purpose
- [ ] Confirm objectives and audience
- [ ] Confirm rules of engagement

### 5–10 min: Context setup
- [ ] Quick org/context recap (1–2 minutes)
- [ ] Confirm any key assumptions
- [ ] Assign incident command owner *for the exercise* (even if hypothetical)

### 10–(end-15) min: Inject cycles
For each inject:
1) Read participant-facing prompt verbatim
2) Ask decision-forcing questions
3) Capture decisions, owners, and follow-ups
4) Time-box and move on

Decision-forcing questions (use repeatedly):
- “What decision do you need to make right now?”
- “Who owns that decision?”
- “What is the immediate priority in the next 30 minutes?”
- “What information do you need, and who will request it?”
- “What is the business impact of containment vs continued operation?”
- “What are you communicating internally and externally, and who approves it?”

### (end-15)–(end-5) min: Hotwash (debrief)
- “What worked well?”
- “What slowed you down?”
- “Where were decision rights unclear?”
- “What information/tools were missing?”
- “What are the top 3 improvements you would make in 30 days?”

### (end-5)–end: Closeout
- [ ] Summarize key decisions and high-impact gaps
- [ ] Confirm post-exercise deliverables and timeline (AAR + improvement plan)
- [ ] Thank participants

---

## 8) Pacing and branching guidance (facilitator notes)

Use scenario YAML fields:
- scenario.facilitator_notes
- inject.facilitator_notes
- inject.branching_guidance

Pacing tips:
- If participants dive into deep technical detail, interrupt politely and ask for:
  - the decision they are trying to make, and
  - the specific data request needed to make it.
- If participants are stuck, offer a binary choice:
  - “Contain now” vs “observe briefly”
  - “Notify now” vs “prepare notification pending confirmation”
- If the room is too quiet, direct questions to specific roles.

Branching rules (general):
- If participants choose aggressive containment, injects should emphasize business disruption and comms complexity.
- If participants delay containment, injects should emphasize expanding scope, lateral movement, and external impact.

---

## 9) Inject execution log (scribe)

| Inject ID | Planned T+ (min) | Actual T+ (min) | Audience | Delivery method | 1–2 sentence summary of discussion | Notes / deviations |
|---|---:|---:|---|---|---|---|
|  |  |  |  |  |  |  |

---

## 10) Decision log (scribe)

Capture decisions as they occur. A “decision” includes choosing to *not* act.

| Time | Decision | Decision owner (role) | Rationale / tradeoffs | Info needed / requested | Follow-up action (owner + due) |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

---

## 11) Communications log (optional, scribe)

| Time | Audience (internal/external) | Message purpose | Who approves | Channel | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

---

## 12) Action items (scribe)

| Action item | Owner (role) | Target timeframe (0/30/90) | Status | Notes |
|---|---|---|---|---|
|  |  |  |  |  |

---

## 13) Scoring notes (facilitator)

Use dfir_backend/ttx/scoring_model.md scoring dimensions:
- Detection & Awareness
- Decision-Making
- Communication
- Escalation & Authority
- Legal & Regulatory Awareness
- Documentation & Tracking

Notes:
- Record concrete examples for each score.
- Flag any dimension scored 2 or below as a priority gap.
