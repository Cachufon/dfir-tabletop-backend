# Prompt: Draft TTX Executive Readout from Scenario + Runtime Notes

## Purpose

Use this prompt to produce a concise **1-page executive readout** in Markdown for leadership review, based on:
- scenario YAML (planned context), and
- scribe runtime JSON (captured discussion notes).

This is a discussion-based tabletop output, not a technical validation report.

---

## Inputs

Provide the model with:
1) Scenario YAML (full text)
2) Scribe runtime JSON export (full text)
3) Optional engagement metadata (if available): case ID, client/org, timezone, duration
4) Optional supporting notes: intake notes, IR plan excerpts

---

## Required constraints (must follow)

- Return **Markdown only**.
- **Do not** use code fences.
- Keep output to approximately **one page**.
- Use **roles, not names**.
- **Do not invent facts**.
- If information is missing, write exactly: **(not captured)**.

---

## Output format (strict section order)

Use exactly these sections in this order:

1) **Document control**
2) **Executive summary** (3–6 bullets)
3) **What went well** (3–5 bullets)
4) **Key risks/gaps** (3–5 bullets; each bullet must include why it matters)
5) **Decisions that mattered** (bullets)
6) **Recommended improvements** (table)

### Required table format for "Recommended improvements"

Use a Markdown table with columns:
- **Timeframe (0/30/90)**
- **Recommendation**
- **Owner role**
- **Effort (S/M/L)**

Only use 0, 30, or 90 in the timeframe column.

---

## Drafting instructions

- Prioritize clarity for executive readers.
- Tie every statement to provided scenario/runtime content.
- Preserve uncertainty when evidence is incomplete.
- Keep language concise and action-oriented.
