# Compromise Assessment Playbook

## Purpose
This playbook guides analysts through executing a Compromise Assessment (CA) to determine whether there is evidence of attacker activity in a customer environment. It covers identity, SaaS, and endpoint telemetry, with optional add-on support for Customized Threat Hunting & Recovery Validation.

## Service Mapping
- Service: Compromise Assessments
- Supports add-on:
  - Customized Threat Hunting & Recovery Validation

---

## Prerequisites

### Data Sources (as scoped)
- Identity:
  - Okta System Logs
  - Azure AD / Entra sign-in and audit logs
  - Google Workspace login/admin logs
- SaaS:
  - O365 Unified Audit Log
  - Exchange / Message Trace
  - SharePoint / OneDrive audit logs
  - Slack audit logs
  - GitHub audit logs (if applicable)
- Endpoint:
  - EDR telemetry (CrowdStrike, Defender, SentinelOne, etc.)
  - Host triage collections (Velociraptor/OSQuery/macOS triage) as needed

### Tools Required
- Collection scripts (dfir_backend/collectors)
- Triage scripts (dfir_backend/triage)
- Normalization helpers (dfir_backend/normalization)
- Forensic tools as needed (Axiom, BlackLight, etc.)

### Permissions
- Read-only access to relevant log sources or exported data
- Customer approval of scope, timeframe, and data-sharing method

---

## Workflow Steps

### 1. Define Objective and Scope
- Confirm with the customer:
  - Primary question: "Are we compromised?" or "What is our residual risk?"
  - Time window (e.g., last 30 / 60 / 90 days)
  - In-scope systems:
    - Identity providers (Okta, Entra, Google)
    - SaaS platforms (O365, Google Workspace, Slack, GitHub)
    - Endpoints/EDR
- Document:
  - Scope
  - Out-of-scope areas
  - Assumptions and constraints

**Output:** Scoped CA engagement description (link in case management system).

---

### 2. Identify Data Sources and Access Paths
- Select relevant data sources from `dfir_backend/data_sources`.
- For each source:
  - Confirm collection method (API, export, script).
  - Confirm format (JSON, CSV, etc).
- Build a data request checklist for the customer.

**Output:** Data Source Checklist.

---

### 3. Collect Logs and Artifacts
- Execute or guide:
  - Identity log exports (Okta, Entra, Google).
  - SaaS log exports (O365 UAL, SharePoint/OneDrive, Slack, GitHub).
  - EDR telemetry export or host triage collection.
- Verify:
  - Time coverage matches scope.
  - No obvious gaps in critical time windows.

**Output:** Raw log and artifact bundles in Evidence Vault (QNAP/S3).

---

### 4. Ingest and Normalize Data
- Use scripts in `dfir_backend/normalization` to:
  - Flatten JSON where needed.
  - Convert CSV → a stable format (e.g., Parquet/SQLite).
  - Apply basic identity/saas/endpoint schemas.
- Record any normalization issues or gaps.

**Output:** Normalized datasets ready for analysis.

---

### 5. Apply Detection Rules (Identity / SaaS / Endpoint)
Using `dfir_backend/rules`:

#### Identity
- Run relevant Sigma rules for identity:
  - okta_impossible_travel.yml
  - mfa-related rules
  - admin privilege change rules (when added)
- Focus patterns:
  - Impossible travel
  - MFA fatigue / push bombing
  - Suspicious OAuth grants
  - New devices and locations
  - Admin role changes and risky actions

#### SaaS
- Run relevant Sigma rules for SaaS:
  - o365_inbox_forwarding.yml
  - mass download / exfil rules
  - external sharing anomalies
- Focus patterns:
  - Inbox rules and mail forwarding
  - Suspicious OAuth app usage
  - Large file access or downloads
  - Sharing to external/personal accounts

#### Endpoint
- Use EDR detections and/or Sigma/YARA where applicable:
  - Persistence rules
  - EDR tampering
  - Suspicious processes
  - C2-like network behavior

**Output:** Initial detection hits (alerts, matches, suspicious events).

---

### 6. Triage Findings
For each hit:

- Validate:
  - Is this a real anomaly or expected behavior?
  - Is there business context that explains it?
- Correlate:
  - Cross-check identity events with SaaS and endpoint events.
  - Look for repeated patterns across users, locations, devices.
- De-duplicate:
  - Group events into candidate “incidents” or “storylines.”

**Output:** Triage notes and a list of candidate findings.

---

### 7. Investigate and Build Narrative
For high-interest candidates:

- Reconstruct the sequence:
  - Initial access or suspicious event (e.g., login).
  - Follow-on actions (OAuth grants, inbox rules, downloads).
  - Possible lateral movement or escalation.
- Evaluate:
  - Impact (data touched, systems accessed).
  - Likelihood (confidence based on evidence quality).
- For the threat-hunting add-on:
  - Pull in relevant IOC bundles from `dfir_backend/rules/iocs`.
  - Run targeted searches against normalized datasets.

**Output:** Draft narratives for each confirmed or likely finding.

---

### 8. Assess Blast Radius and Residual Risk
For each confirmed or probable compromise:

- Identify:
  - Affected accounts, devices, applications.
  - Data access and potential exfiltration paths.
- Evaluate containment (if incident already handled):
  - Were credentials rotated?
  - Were tokens invalidated?
  - Were OAuth apps removed?
  - Were endpoints re-imaged or cleaned?

**Output:** Blast radius assessment and residual risk summary.

---

### 9. Draft Report and Recommendations
Using templates in `dfir_backend/report_templates`:

- Populate:
  - Executive Summary
  - Scope and Methodology
  - Data Sources
  - Detailed Findings (one per finding using finding_template)
  - Blast Radius section
  - Recommendations:
    - Short-term (0–7 days)
    - Medium-term (7–30 days)
    - Longer-term (30–90 days)

**Output:** Draft technical report + executive summary.

---

### 10. Internal Review and Customer Readout
- Internal QA:
  - Check evidence alignment with findings.
  - Validate severity and confidence ratings.
  - Ensure recommendations are realistic for customer’s size/maturity.
- Customer readout:
  - Walk through high-level story first.
  - Answer: “Were we compromised?” and “How bad could it have been?”
  - Provide clear action plan.

**Output:** Final report delivered and readout completed.

---

## Indicators to Hunt For (High-Level)
- Identity:
  - Unknown/new locations and devices.
  - Excessive failed MFA followed by success.
  - Unusual OAuth app grants.
- SaaS:
  - Inbox forwarding to external domains.
  - Mass download or sync from critical document stores.
  - Sudden sharing to personal accounts.
- Endpoint:
  - Persistence and EDR tampering.
  - Unexpected remote access tools.
  - Repeated connection to suspicious IPs/domains.

---

## Common Pitfalls
- Incomplete log retention windows.
- Timezone mismatches across sources.
- Missing or inconsistent user identifiers.
- Over-reliance on EDR alerts instead of raw telemetry.
- Treating every anomaly as compromise instead of risk signal.

---

## Output Artifacts
- Final PDF/Docx report.
- Executive summary deck (optional).
- IOC and detection lists used.
- (Optional) Timeline or graph visualizations for key incidents.
