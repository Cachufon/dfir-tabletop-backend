# Finding Taxonomy (v1)

This document defines how Gruve DFIR findings are structured, classified, and reported during Compromise Assessments. It is an internal backend standard used to ensure consistency, defensibility, and clarity across analysts, reports, and future automation.

---

## What Is a Finding

A finding is a defensible conclusion drawn from one or more detections, supported by evidence, and evaluated along two independent dimensions:
- Severity (impact if true)
- Confidence (likelihood the activity is malicious or unauthorized)

Detections alone do not constitute findings. Analyst judgment is required to aggregate, contextualize, and assess detections before issuing a finding.

---

## Finding Structure

Each finding must include:

- Finding ID
- Title
- Module (Identity, SaaS, Endpoint)
- Category
- Description
- Evidence Summary
- Severity
- Confidence
- Blast Radius
- ATT&CK Techniques (when applicable)
- Status
- Recommendations
- Notes / Caveats

MITRE ATT&CK is used as a behavioral taxonomy for detections and findings, not as a prescriptive workflow.

---

## Severity Scale (Impact-Based)

Severity reflects potential impact, not certainty.

### Critical
- Confirmed or near-confirmed compromise
- Direct access to sensitive data, systems, or admin privileges

### High
- Strong indicators of compromise
- Significant security impact if unaddressed

### Medium
- Suspicious activity with plausible benign explanations
- Elevated risk or control weakness

### Low
- Minor anomalies or hygiene issues
- Low immediate impact

### Informational
- Contextual observations
- No immediate security risk

---

## Confidence Scale (Likelihood-Based)

Confidence reflects evidentiary strength.

### High Confidence
- Multiple corroborating data points
- Minimal alternative explanations

### Medium Confidence
- Partial evidence
- Some benign explanations possible

### Low Confidence
- Weak or ambiguous signals
- Heavily assumption-dependent

High severity findings may have low confidence when potential impact is significant but evidence is incomplete.

---

## Blast Radius Classification

Each finding must describe scope of impact across one or more dimensions:

- Identities (users, admins, service accounts)
- SaaS assets (mailboxes, files, repos)
- Endpoints (hosts, VMs)
- Data types (email, source code, PII, IP)
- Time (first seen, last seen)

Blast radius may be characterized as minimal, moderate, or wide.

---

## Finding Status

Findings should be labeled as one of:

- Active
- Remediated
- Unknown

Status reflects point-in-time assessment and may change during post-incident sweeps or follow-up engagements.

---

## Mapping Detections to Findings

- Multiple detections may roll up into a single finding.
- A single detection may contribute to multiple findings in rare cases.
- Findings must reference which detections and data sources contributed.

---

## Module-Specific Finding Categories

### Identity
- Account Takeover
- MFA Abuse
- Privilege Escalation
- OAuth Abuse
- Policy Weakening
- Identity Hygiene Risk

### SaaS
- Mailbox Compromise
- Data Exfiltration
- External Sharing Abuse
- OAuth / Application Abuse
- SaaS Admin Misuse
- SaaS Hygiene Risk

### Endpoint
- Persistence
- Malware Execution
- Privilege Escalation
- Lateral Movement
- EDR Tampering
- Host-Based Exfiltration
- Endpoint Hygiene Risk

---

## Recommendations

Each finding must include actionable recommendations, typically grouped into:
- Immediate (0–7 days)
- Short-term (30 days)
- Longer-term (90 days)

Recommendations should be specific, realistic, and tied to reducing the risk described in the finding.

---

This taxonomy is used across all Compromise Assessment models (Broad Sweep, Post-Incident Sweep, Targeted Threat Hunt) and scope areas.
