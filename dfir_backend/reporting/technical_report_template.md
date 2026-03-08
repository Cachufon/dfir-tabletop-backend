# Compromise Assessment Technical Report Template (v1)

This document defines the standard internal technical report structure for Gruve Compromise Assessments. It is intended for security, DFIR, legal, and technical stakeholders and is not a marketing document.

---

## 1. Executive Overview (Technical)

Provide a brief technical summary describing:
- Why the assessment was performed
- Which assessment model was used (Broad Sweep, Post-Incident Sweep, or Targeted Threat Hunt)
- Which scope areas were in scope (Identity, SaaS, Endpoint)
- High-level outcome of the assessment

---

## 2. Engagement Scope

### 2.1 Assessment Model
Specify the model used.

### 2.2 Scope Areas in Scope
List all scope areas included in the assessment.

### 2.3 Time Window
Document the start and end dates of the assessment window.

### 2.4 Out of Scope
Explicitly list systems, platforms, or data sources that were not assessed.

---

## 3. Methodology

Describe that the assessment followed Gruve’s Compromise Assessment workflow, aligned with the NIST 800-61 Incident Response lifecycle, and included the following phases:
- Scoping and preparation
- Data collection and normalization
- Detection and triage
- Investigation and blast radius analysis
- Reporting and recommendations

---

## 4. Data Sources Reviewed

### 4.1 Identity
List identity providers and log types reviewed.

### 4.2 SaaS
List SaaS platforms and audit logs reviewed.

### 4.3 Endpoint
List EDR or host telemetry reviewed, if applicable.

### 4.4 Data Gaps and Limitations
Document missing telemetry, retention gaps, or unavailable data sources that may affect findings or confidence.

---

## 5. Summary of Findings

### 5.1 Findings by Severity
Summarize findings grouped by severity (Critical, High, Medium, Low, Informational).

### 5.2 Findings by Scope Area
Summarize findings grouped by scope area (Identity, SaaS, Endpoint).

---

## 6. Detailed Findings

Each finding should be documented using the standard Finding Template and included in full in this section, unless moved to an appendix.

Repeat this subsection for each finding:
- Finding ID
- Title
- Full finding content

---

## 7. Cross-Scope-Area Analysis and Correlation

Describe relationships between findings across scope areas, including any observed attack paths or confirmation that activity appears isolated.

---

## 8. Blast Radius Assessment

Summarize:
- Impacted identities
- Impacted SaaS assets
- Impacted endpoints
- Data types potentially accessed
- Observed time range of activity

---

## 9. Residual Risk and Assessment Confidence

### 9.1 Residual Risk
Describe remaining risk after remediation or containment actions.

### 9.2 Overall Confidence
Explain the overall confidence in the assessment conclusions and how data gaps influence confidence.

---

## 10. Recommendations

Summarize recommendations derived from findings.

### Immediate (0–7 Days)

### Short-Term (30 Days)

### Longer-Term (90 Days)

---

## 11. MITRE ATT&CK Technique Summary (Optional)

List MITRE ATT&CK techniques observed or suspected during the assessment. This section is informational and intended to provide behavioral context.

---

## 12. Limitations and Assumptions

Explicitly document assumptions, scope constraints, and limitations of the assessment.

---

## 13. Appendix

### A. Finding Index
List all findings with ID, title, severity, confidence, and status.

### B. Data Source Details
Optional expanded detail on log sources reviewed.

### C. IOC Summary (If Applicable)
Summarize IOC bundles used in post-incident sweeps or threat hunts.

