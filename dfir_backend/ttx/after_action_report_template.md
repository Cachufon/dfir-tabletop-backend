# INTERNAL - Tabletop Exercise After-Action Report (AAR) & Improvement Plan Template

This template is used to document outcomes from a **discussion-based** tabletop exercise (TTX).
It pairs with:
- Scenario YAML (conforming to dfir_backend/ttx/schemas/ttx_scenario.schema.json)
- Facilitator guide (dfir_backend/ttx/facilitator_guide_template.md)
- Scoring model (dfir_backend/ttx/scoring_model.md)

**Note:** This AAR documents observed discussion and stated actions. It is not an audit and does not prove technical control effectiveness.

---

## 1) Document control

- **Engagement / Case ID:**
- **Client / Organization:**
- **Exercise date:**
- **Timezone:**
- **Prepared by (role):**
- **Facilitator (role):**
- **Scribe (role):**
- **Distribution:** (Internal only / Client / Limited)
- **Version:**
- **Scenario YAML path:**
- **Scenario ID:**
- **Scenario title:**
- **Scenario category:**
- **Exercise duration (minutes):**
- **Format:** (Virtual / In-person)

---

## 2) Executive summary (client-facing)

Provide a 1-page summary suitable for leadership.

### Overall readiness statement (1–3 sentences)
- 

### Top strengths (3–5 bullets)
- 
- 
- 

### Top gaps / risks (3–5 bullets)
- 
- 
- 

### Most important improvements (next 30–90 days) (3–5 bullets)
- 
- 
- 

---

## 3) Exercise scope and approach

### Objectives (copy from scenario YAML)
- 
- 
- 

### Assumptions (copy from scenario YAML)
- 
- 
- 

### Constraints / redlines (copy from scenario YAML)
- 
- 
- 

### Out of scope (copy from scenario YAML)
- 
- 
- 

### Participants (roles only)
List roles only (avoid names in deliverables unless required by the engagement).

- Executive:
- IT:
- Security:
- Legal:
- PR / Comms:
- HR:
- Product / Engineering:
- Finance:
- Third-party / Vendor reps (if applicable):
- Observers (optional):

---

## 4) Scenario summary (client-facing)

### Summary
- 

### Threat context
- 

### Business context
- 

### Scenario progression (1 paragraph)
- 

---

## 5) Key decisions observed (high level)

Capture the highest-impact decisions, including decisions to *not* act.

- 
- 
- 

---

## 6) Scoring summary (internal by default)

Use dfir_backend/ttx/scoring_model.md. If numeric scores are not desired in client deliverables, convert to qualitative statements and keep numbers internal.

### Scores and evidence

| Dimension | Score (1–5) | Evidence / examples (2–4 bullets) | Priority gap? (Y/N) |
|---|---:|---|---|
| Detection & Awareness |  |  |  |
| Decision-Making |  |  |  |
| Communication |  |  |  |
| Escalation & Authority |  |  |  |
| Legal & Regulatory Awareness |  |  |  |
| Documentation & Tracking |  |  |  |

**Overall readiness score (avg):** _______

**Priority gap rule:** Any dimension scored **2 or below** must be addressed in the improvement plan.

---

## 7) Observations (strengths and gaps)

For each dimension, document:
- What worked well (strengths)
- What needs improvement (gaps)
- Impact if unaddressed
- Recommendation (1–3 sentences)

### A) Detection & Awareness
**Strengths**
- 

**Gaps**
- 

**Impact**
- 

**Recommendation**
- 

---

### B) Decision-Making
**Strengths**
- 

**Gaps**
- 

**Impact**
- 

**Recommendation**
- 

---

### C) Communication
**Strengths**
- 

**Gaps**
- 

**Impact**
- 

**Recommendation**
- 

---

### D) Escalation & Authority
**Strengths**
- 

**Gaps**
- 

**Impact**
- 

**Recommendation**
- 

---

### E) Legal & Regulatory Awareness
**Strengths**
- 

**Gaps**
- 

**Impact**
- 

**Recommendation**
- 

---

### F) Documentation & Tracking
**Strengths**
- 

**Gaps**
- 

**Impact**
- 

**Recommendation**
- 

---

## 8) Exercise timeline (inject-by-inject summary)

Summarize each inject and the decisions it produced. Use the scribe logs as the source of truth.

| Inject ID | Planned T+ (min) | Actual T+ (min) | Audience (roles) | What happened (1–2 sentences) | Decisions made (summary) | Open questions / follow-ups |
|---|---:|---:|---|---|---|---|
|  |  |  |  |  |  |  |

---

## 9) Improvement plan (0 / 30 / 90 days)

Create actionable, owned improvements. Keep them realistic and tied to gaps observed.

### Improvement plan table

| Priority | Timeframe (0/30/90) | Recommendation | Owner (role) | Expected outcome | Effort (S/M/L) | Dependencies / notes |
|---:|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |

### Notes on prioritization
- Prioritize items that reduce decision latency, clarify authority, and improve detection/visibility gaps.
- Treat “missing data/tools” as a scoped requirement (what exact data is needed, from where, by whom).

---

## 10) Optional: Recommended follow-on exercises / validation

Use this section to propose a programmatic path (quarterly TTX, targeted TTX for execs, etc.).

- 
- 
- 

---

## 11) Appendices (internal, attach as appropriate)

### Appendix A: Attendance (roles only)
- 

### Appendix B: Inject execution log (paste from facilitator guide)
(paste table)

### Appendix C: Decision log (paste from facilitator guide)
(paste table)

### Appendix D: Communications log (optional)
(paste table)

### Appendix E: Scenario YAML reference
- YAML path:
- Scenario ID:

---

_End of template._
