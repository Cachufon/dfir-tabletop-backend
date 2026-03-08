# Gruve Compromise Assessment Workflow (v1)

This document defines the internal, backend operational workflow for executing a Gruve Compromise Assessment (CA). It is not customer-facing. It aligns with the Models × Scope Areas structure and references Identity, SaaS, Cloud, Endpoint, and AI scope area workflows, as well as custom case content under dfir_backend/custom/.

---

# Framework Alignment

The Gruve Compromise Assessment workflow aligns with the NIST 800-61 Incident Response lifecycle while remaining operationally focused and vendor-agnostic.

---

# PHASE 1 — SCOPING & MODEL/SCOPE AREA SELECTION

## 1.1 Determine Assessment Model
Models define the approach and depth:
- **Broad Sweep** — fast, low-touch, rule-driven.
- **Post-Incident Sweep** — IOC-driven validation using IR reports and incident intel.
- **Targeted Threat Hunt** — scenario/actor/TTP-focused proactive hunt.

## 1.2 Select Scope Areas
Scope areas define the surfaces included:
- Identity
- SaaS
- Cloud
- Endpoint
- AI
Any model can be combined with any scope area, depending on customer data availability and goals.

## 1.3 Define Scope Window
Typically 30, 60, or 90 days, or incident-bound.

## 1.4 Confirm Required Inputs
For each scope area, confirm minimum vs. optional data sources, as defined in the scope area data_sources.md files.

## 1.5 Setup Case Workspace
Create:

dfir_backend/custom/<case_id>/
  intel/
  iocs/
  sigma/
  yara/
  ai_prompts/
  detection_plan.yaml
  notes.md

This becomes the detection and analysis workspace.

---

# PHASE 2 — DATA COLLECTION & INGESTION

## 2.1 Collect Scope Area–Specific Data

### Identity
- Primary IDP logs (Okta, Entra/AAD, or Google Workspace)
- MFA logs
- Admin/audit logs (if available)
- OAuth/SAML logs

### SaaS
- O365 UAL or Google Workspace audit logs
- Exchange/Gmail mailbox logs
- SharePoint/Drive/Slack/GitHub logs
- SaaS OAuth application logs

### Cloud
- Cloud audit logs (CloudTrail, Azure Activity Logs, GCP Admin/audit logs)
- IAM configuration snapshots (optional)
- CSPM exports, Kubernetes audit logs, or VPC flow/proxy logs where applicable

### Endpoint
- EDR alerts/detections
- EDR telemetry/timelines (if available)
- Host triage bundles where applicable

### AI
- Prompt logs or transcripts
- System/developer prompt artifacts
- Agent manifests/tool schemas
- Model gateway/policy logs or evaluation artifacts (optional)

## 2.2 Verify Coverage
Assess telemetry coverage, retention gaps, missing logs, incomplete timelines, and missing high-value users or devices. Document gaps as findings.

## 2.3 Normalize Data
Use dfir_backend/normalization tools to:
- Flatten JSON
- Convert CSV → Parquet
- Standardize timestamps
- Normalize field names by scope area classification
Store normalized outputs under:

dfir_backend/custom/<case_id>/normalized/

---

# PHASE 3 — DETECTION & TRIAGE

## 3.1 Load Global Rule Packs
From dfir_backend/rules/:
- Sigma rules
- YARA rules
- IOC bundles
- NOVA/prompt rules

Rule selection depends on the selected model and scope area(s).

## 3.2 Load Custom Case Rules
From:

dfir_backend/custom/<case_id>/

Include:
- IOC bundles
- Case-specific Sigma/YARA rules
- AI-generated prompt rules (if applicable)

## 3.3 Execute Scope Area Workflows

### Identity Scope Area
Detect:
- Suspicious sign-ins
- MFA abuse
- Admin/role escalation
- OAuth anomalies
- Policy misconfigurations

### SaaS Scope Area
Detect:
- Mailbox manipulation
- File access anomalies
- External sharing
- OAuth application abuse
- Slack/GitHub misuse
- SaaS admin changes

### Cloud Scope Area
Detect:
- Anomalous IAM changes
- Suspicious access to cloud services or projects
- Risky configuration changes
- Cross-account or cross-tenant access anomalies
- Potential data exfiltration via cloud services

### Endpoint Scope Area
Detect:
- Persistence mechanisms
- Suspicious process execution
- Privilege escalation
- Lateral movement
- EDR tampering/evasion
- Host-based exfiltration
- Anomalous outbound network behavior

### AI Scope Area
Detect:
- Prompt injection patterns or unsafe capability exposure
- Risky or ungoverned tool/agent behaviors
- Misuse patterns in transcripts or prompts
- Gaps in policy enforcement or guardrails

## 3.4 Triage Findings
For each scope area:
- Remove false positives
- Cluster related events
- Identify repeated actors and systems
- Score severity + confidence

Store triage output under:

dfir_backend/custom/<case_id>/analysis/

---

# PHASE 4 — INVESTIGATION & BLAST RADIUS ANALYSIS

## 4.1 Build Event Storylines
Reconstruct event sequences for each suspicious user, device, or SaaS resource.

## 4.2 Cross-Scope Correlation
Examples:
- Identity → SaaS: flag suspect users for mailbox/file reviews
- SaaS → Endpoint: exfil patterns → check endpoints for CLI exfil tools
- Cloud → Identity/SaaS: risky IAM or service enablement → validate related user and app activity
- Endpoint → Identity: persistence on device → confirm user identity activity
- AI → Identity/SaaS: prompt misuse tied to specific users or workspaces

## 4.3 Determine Blast Radius
Identify:
- Impacted accounts
- Impacted data
- Involved devices
- Potential lateral movement
- Persistence footholds

## 4.4 Residual Risk Assessment
Document:
- Gaps in detection or telemetry
- Identity/SaaS/cloud/endpoint/AI misconfigurations
- Additional risk factors

---

# PHASE 5 — REPORTING & DELIVERY

## 5.1 Draft Report
Use templates in dfir_backend/report_templates/ to build:
- Executive Summary
- Scope (model + scope areas)
- Data Sources
- Findings per scope area
- Blast Radius
- Residual Risk
- Recommendations (0–7 days, 30 days, 90 days)
- Appendices (IOC matches, rule hits, logs)

## 5.2 Internal QA
A second reviewer validates:
- Evidence-linking
- Correct severity + confidence
- Consistency with CA workflow

## 5.3 Customer Readout
Deliver:
- Full CA report
- Executive summary deck
- Optional: timelines, CSVs, IOC extractions

End of workflow.

---

Ensure the markdown formatting is preserved.
