# INTERNAL - TTX Scoring Model

This scoring model is used by the facilitator and scribe to evaluate tabletop exercise (TTX) performance in a **discussion-based** setting.
It is intended to:
- create consistent observations across exercises,
- support an After-Action Report (AAR) and improvement plan,
- identify priority gaps for remediation.

**Important:** Scores reflect observed discussion, stated actions, and decision-making during the exercise.
This is not an audit and does not prove technical control effectiveness.

---

## 1) Scoring scale (1–5)

Use the same scale for each dimension:

1. **Very weak** — No defined approach; confusion on ownership; actions are ad-hoc or absent.
2. **Weak** — Some awareness, but major gaps; slow/unclear decisions; inconsistent coordination.
3. **Adequate** — Baseline approach exists and is mostly followed; some gaps or delays.
4. **Strong** — Coordinated, risk-based decisions; minor improvement opportunities only.
5. **Excellent** — Proactive, repeatable, and well-documented; clear authority; strong cross-functional alignment.

---

## 2) Scoring dimensions and behavioral anchors

Score each dimension 1–5 and record 2–4 concrete examples supporting the score.

### A) Detection & Awareness
How quickly participants recognize signals, validate legitimacy, and establish an initial incident hypothesis.

- **1:** Participants miss obvious indicators; no coherent incident hypothesis; unclear what to check first.
- **2:** Slow to recognize seriousness; limited data requests; confusion about what evidence matters.
- **3:** Recognize likely issue; request key logs/data; form a reasonable hypothesis with some uncertainty.
- **4:** Rapid triage framing; clear initial hypothesis + alternatives; targeted evidence requests with purpose.
- **5:** Strong situational awareness; anticipates second-order effects; aligns detection posture with scenario evolution.

Evidence to cite:
- What initial data was requested and why (identity logs, email audit, EDR, cloud control plane, etc.)
- How quickly an initial working hypothesis was established

---

### B) Decision-Making
Quality and speed of decisions, including tradeoffs (risk vs business impact) and time-boxing.

- **1:** No decisions made; participants defer repeatedly; no owner or timeline.
- **2:** Decisions made late or only after prompting; tradeoffs not articulated; inconsistent severity classification.
- **3:** Decisions generally made with some prompting; tradeoffs acknowledged; owners identified most of the time.
- **4:** Timely decisions; clear owners; tradeoffs explicit; decisions revisited as new info appears.
- **5:** High-quality risk-based decisions under time pressure; pre-defined thresholds/triggers used effectively.

Evidence to cite:
- Decision log entries: decisions, owners, rationale, time to decide
- Use (or lack) of severity classification and escalation triggers

---

### C) Communication
Internal and external communications clarity, timeliness, and governance (approvals, single source of truth).

- **1:** No comms plan; conflicting messages; no approval process; stakeholders not identified.
- **2:** Some communications occur but inconsistent; unclear who approves; messaging not aligned to uncertainty.
- **3:** Basic comms approach exists; approvals mostly clear; internal updates are timely; external comms cautious.
- **4:** Clear comms owner; consistent messaging; good use of “known/unknown/next update” framing.
- **5:** Mature comms governance; stakeholder mapping is strong; messaging balances transparency and risk well.

Evidence to cite:
- Communications log entries
- Who is authorized to speak externally and when

---

### D) Escalation & Authority
Clarity of incident command, escalation paths, and decision rights across teams (Security, IT, Exec, Legal/PR).

- **1:** No incident command owner; authority unclear; teams work in silos; escalations missed.
- **2:** Partial escalation; unclear thresholds; frequent “who owns this?” moments.
- **3:** Incident lead identified; escalation occurs; some ambiguity remains for major decisions.
- **4:** Clear incident command + roles; well-understood thresholds; cross-functional coordination is effective.
- **5:** Highly effective command structure; strong delegation; clear decision rights across all major actions.

Evidence to cite:
- Who acted as incident commander (role) and when
- Escalation triggers used and stakeholders engaged

---

### E) Legal & Regulatory Awareness
Appropriate consideration of privilege, notification triggers, and regulatory/contractual obligations.

- **1:** Legal/privacy not considered; privilege not discussed; no awareness of notification triggers.
- **2:** Legal mentioned late; triggers unclear; participants conflate “suspected” vs “confirmed” breach requirements.
- **3:** Legal engaged appropriately; basic awareness of triggers; uncertainty is acknowledged and tracked.
- **4:** Legal/PR coordination is timely; privilege considerations stated; notification decision points are clear.
- **5:** Strong governance; clear approval workflow; good framing for client/regulator notifications under uncertainty.

Evidence to cite:
- When Legal/Privacy was engaged
- How notification decisions were framed and approved

---

### F) Documentation & Tracking
Quality of note-taking, decision logging, ownership assignment, and action tracking.

- **1:** Little/no documentation; no action tracking; decisions not captured.
- **2:** Notes exist but incomplete; owners/dates missing; action items not prioritized.
- **3:** Decision/action logs mostly complete; owners assigned; some follow-ups lack timeframes.
- **4:** Strong logs; clear owners and due windows; improvement items are prioritized and realistic.
- **5:** Excellent documentation discipline; clear audit trail; immediate conversion into an improvement plan.

Evidence to cite:
- Completeness of inject log and decision log
- Action item list quality (owner + timeframe + status)

---

## 3) Scoring method

1) During the exercise, the scribe maintains:
- Inject execution log
- Decision log
- Communications log (optional)
- Action items list

2) After the hotwash, the facilitator assigns:
- A 1–5 score per dimension
- 2–4 concrete examples per dimension (quotes/paraphrases are fine)

3) Overall readiness score:
- Average of all dimension scores (round to one decimal place)

4) Priority gap rule:
- Any dimension scored **2 or below** is a priority remediation item in the AAR improvement plan.

---

## 4) Scoring worksheet (copy/paste)

| Dimension | Score (1–5) | Evidence / examples (2–4 bullets) | Priority gap? (Y/N) |
|---|---:|---|---|
| Detection & Awareness |  |  |  |
| Decision-Making |  |  |  |
| Communication |  |  |  |
| Escalation & Authority |  |  |  |
| Legal & Regulatory Awareness |  |  |  |
| Documentation & Tracking |  |  |  |

Overall readiness score (avg): _______

---

## 5) Client-facing guidance (optional)

If numeric scores are not desired in client deliverables:
- Convert each dimension into a qualitative statement (e.g., “Adequate with gaps in X”).
- Keep numeric scores in internal notes only.
