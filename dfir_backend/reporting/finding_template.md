# Finding Template (v1)

This document defines the standard internal template for DFIR findings used in Gruve Compromise Assessments. A finding represents a defensible conclusion drawn from one or more detections and is evaluated independently for severity (impact) and confidence (likelihood).

---

# Finding {{FINDING_ID}} — {{TITLE}}

## Overview
Brief, plain-language summary of the finding. This should be understandable to a non-technical reader and answer: “What happened?”

## Module
Identity | SaaS | Endpoint

## Category
(Select one from the module-specific finding categories)

## Severity
Critical | High | Medium | Low | Informational

## Confidence
High | Medium | Low

## Status
Active | Remediated | Unknown

## MITRE ATT&CK Mapping (Optional)
- Technique ID(s) and name(s), if applicable

---

## Description
Detailed explanation of the activity observed. This section should explain:
- What behavior was detected
- Why it is suspicious or malicious
- How it relates to known attack patterns or TTPs

Avoid speculation; focus on observable behavior and reasonable inference.

---

## Evidence Summary
Summarize the evidence supporting this finding, including:
- Data sources used
- Key timestamps
- Relevant users, systems, or assets
- Detection rules or queries that contributed

---

## Blast Radius

### Identities
List affected users or service accounts.

### SaaS Assets
List affected mailboxes, files, repositories, or other SaaS resources.

### Endpoints
List affected hosts or devices, if applicable.

### Data Types
Identify data types potentially impacted (e.g., email, files, source code, PII).

### Time Range
- First observed:
- Last observed:

---

## Analysis & Interpretation
Analyst interpretation tying evidence together. This section should explain:
- Why the activity is believed to be malicious or unauthorized
- Alternative explanations considered
- Rationale for severity and confidence ratings
- Assumptions or data gaps

---

## Recommendations

### Immediate (0–7 Days)
Concrete actions to reduce immediate risk.

### Short-Term (30 Days)
Actions to reduce likelihood of recurrence.

### Longer-Term (90 Days)
Strategic or structural improvements.

---

## Notes / Caveats
Document limitations, telemetry gaps, assumptions, or recommended follow-up investigations.

---

This template is used across all Compromise Assessment models and scope areas and serves as the atomic unit for reporting, quality assurance, and future automation.
