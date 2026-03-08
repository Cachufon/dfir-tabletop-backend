# Prompt: Draft TTX After-Action Report (AAR) & Improvement Plan from Scribe Notes

## Purpose

Use this prompt to draft a **Tabletop Exercise After-Action Report (AAR) & Improvement Plan** in Markdown based on:
- the scenario YAML (client-tailored, stored in secure project storage), and
- scribe logs captured during facilitation (inject log, decision log, action items, optional comms log).

The draft should align to:
- dfir_backend/ttx/after_action_report_template.md
- dfir_backend/ttx/scoring_model.md

**Important:** This output is client-sensitive and must be stored in secure project storage (outside git). Do not commit generated AARs to git.

---

## Inputs

Provide the model with:

1) Scenario YAML (full text)
2) Scribe logs (paste as text):
   - Inject execution log
   - Decision log
   - Action items list
   - Communications log (optional)
3) Engagement metadata (if available):
   - case/engagement ID, date, timezone, duration, format (virtual/in-person)
   - participant roles present (roles only)
4) Scoring preference:
   - Include numeric scores in the AAR (Yes/No)
5) Constraints/redlines (if any)
6) Any customer preferences about tone:
   - executive-friendly / technical / balanced

Optional (high value):
- Facilitator notes (hotwash notes, key quotes, key “stuck points”)
- Any pre-defined success criteria or objectives from the intake

---

## Data handling / safety constraints (must follow)

- Do not include real employee names, personal emails, phone numbers, or unnecessary PII.
- Prefer roles over names (e.g., “IT Lead”, “Legal”, “CISO”, “Executive Sponsor”).
- Do not fabricate facts about the customer environment or incident.
- If details are missing, label them as **Unknown** or **Not observed**.
- Keep this framed as a **discussion-based exercise**:
  - Do not claim technical control effectiveness.
  - Do not claim breach confirmation.
  - Clearly separate “observed” vs “assumed”.
- Legal support context:
  - Focus on civil/regulatory posture only.
  - Do not assume law enforcement engagement unless explicitly in-scope.

---

## Instructions to the Model (v1)

You are a DFIR lead and tabletop facilitator. Using the scenario YAML and scribe logs:

### Step 1 — Build a clean executive summary (client-facing)
Create:
- 1–3 sentence overall readiness statement
- Top strengths (3–5 bullets)
- Top gaps/risks (3–5 bullets)
- Most important improvements for 30–90 days (3–5 bullets)

### Step 2 — Extract and summarize key decisions
From the decision log, identify:
- major containment/continuity decisions (or lack thereof)
- escalation/authority decisions (who owned what)
- communications/notification posture decisions
- decisions that were delayed or unclear

Summarize them in plain language.

### Step 3 — Score (if requested) using the scoring model
Dimensions:
- Detection & Awareness
- Decision-Making
- Communication
- Escalation & Authority
- Legal & Regulatory Awareness
- Documentation & Tracking

If numeric scores are requested:
- Assign a 1–5 score per dimension
- Provide 2–4 concrete examples per dimension drawn from notes/logs
- Mark priority gaps where score <= 2

If numeric scores are NOT requested:
- Provide qualitative statements per dimension (e.g., “Adequate with gaps in X”)
- Do not include numeric values

Do not invent evidence. Use “Not observed” where appropriate.

### Step 4 — Produce observations and recommendations
For each scoring dimension:
- Strengths (bullets)
- Gaps (bullets)
- Impact (1–3 sentences)
- Recommendation (1–3 sentences)

Recommendations must be:
- actionable
- realistic
- tied directly to observed gaps

### Step 5 — Build an improvement plan (0/30/90)
Create a prioritized improvement plan table with:
- Priority rank
- Timeframe (0/30/90)
- Recommendation
- Owner (role)
- Expected outcome
- Effort (S/M/L)
- Dependencies/notes

Apply the priority gap rule:
- Any dimension that is “Very weak/Weak” (score <= 2) must appear in the improvement plan.

### Step 6 — Create an inject-by-inject timeline summary
Summarize each inject with:
- what happened (1–2 sentences)
- decisions made (summary)
- open questions/follow-ups

If the inject log is incomplete, document what is missing (do not fabricate).

---

## Output format requirements (strict)

Return ONLY Markdown (no code fences).

Use the following section order and headings:

1) Document control
2) Executive summary (client-facing)
3) Exercise scope and approach
4) Scenario summary (client-facing)
5) Key decisions observed (high level)
6) Scoring summary (internal by default)
7) Observations (strengths and gaps)
8) Exercise timeline (inject-by-inject summary)
9) Improvement plan (0 / 30 / 90 days)
10) Optional: Recommended follow-on exercises / validation
11) Appendices (optional)

Include the statement in the executive summary or scope section:
- “This AAR documents observed discussion and stated actions. It is not an audit and does not prove technical control effectiveness.”

Do not add any additional sections.
