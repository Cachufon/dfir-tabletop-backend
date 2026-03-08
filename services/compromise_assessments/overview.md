# Compromise Assessments

## Service Overview

A Gruve Compromise Assessment is a structured, time-bounded investigation to determine whether there is evidence of attacker activity in a customer’s environment, and to measure the residual risk of undetected compromise. We run five models (Broad Sweep, Post-Incident Sweep, Targeted Threat Hunt, Continuous Compromise Monitoring, and AI Safety / Prompt Security Assessment) across one or more scope areas: Identity, SaaS, Cloud, Endpoint, and AI. The goal is not just “yes/no compromise,” but a clear picture of blast radius, gaps, and concrete next steps.

## Typical Customers

- Mid-market or growth-stage SaaS companies
- Professional services and law firms
- Organizations that:
  - Suspect suspicious activity but don’t have a full-blown incident response
  - Have recently improved security and want a “health check” on compromise risk
  - Have just gone through an incident and want an independent second look
  - Need a periodic “are we quietly owned?” assessment for leadership and the board

## Scope (What’s Included)

Core compromise assessment activities include:

### Identity & Access

- Analysis of Okta / Entra / Google identity logs
- Review of authentication and MFA behavior
- Review of admin actions and privilege changes
- Review of OAuth and app grants for risky access patterns

### SaaS Applications

- Analysis of O365 / Google Workspace / Slack / GitHub audit logs (as applicable)
- Detection of suspicious inbox rules and inbox manipulation
- Review of file access, downloads, and external sharing patterns
- Review of OAuth app behavior in SaaS platforms

### Cloud

- Analysis of AWS / GCP / Azure audit telemetry and IAM configuration changes
- Identification of access anomalies, risky service enablement, and cross-account access
- Review of cloud misconfigurations and CSPM/Kubernetes/VPC flow signals where available

### Endpoints / EDR (Targeted)

- High-level review of EDR detection timelines
- Identification of high-risk persistence or tampering patterns
- Targeted host triage where necessary (small set of representative endpoints)

### AI (Model 5 or when AI telemetry is in scope)

- AI Safety and Prompt Security Assessment as one of the five models
- Review of prompts, transcripts, and agent/tool schemas for misuse and guardrail gaps
- Capability risk scoring and governance-aligned recommendations when AI systems are in scope

## Add-on: Customized Threat Hunting & Recovery Validation

As an add-on to the core Compromise Assessment, Gruve offers targeted threat hunting and recovery validation. This includes:

- Customized hunts for specific threat actors, campaigns, or IOCs based on threat reports or customer concerns
- Validation of post-incident cleanup and containment steps
- Checks for residual access, undetected lateral movement, or lingering persistence

This add-on leverages the same data sources as the core assessment but applies more focused, scenario-driven analysis.

## Out of Scope (v1)

The Compromise Assessment is not intended to provide:

- Full incident response with 24/7 on-call containment and hands-on remediation
- Deep disk and memory forensics across the entire endpoint fleet
- Full red team or assumed-breach simulation exercises
- Ongoing managed detection and response (MDR) services
- A comprehensive security program maturity assessment (policies, training, vendor review, etc.)

These may be offered as adjacent or future services.

## Inputs (What the Customer Must Provide)

- Confirmed scope and time window for review (for example, the last 30, 60, or 90 days)
- Exported logs or access for:
  - Identity provider(s) in scope
  - Core SaaS platforms in scope
  - EDR / endpoint sources if endpoint analysis is included
- Named contacts for:
  - Security / IT
  - Identity / SaaS administrators
  - Business or application owners when additional context is needed
- Any known indicators of compromise (IOCs), threat reports, or prior incident details when using the threat hunting and recovery validation add-on

## Outputs (What the Customer Receives)

### Executive Summary

- A clear, plain-language answer to “Did we see evidence of compromise?”
- An overall risk rating (for example, Low / Medium / High)
- The top three to five prioritized recommendations

### Technical Findings

- Identity findings (e.g., account takeover indicators, risky logins, MFA abuse, OAuth misuse)
- SaaS findings (e.g., suspicious inbox rules, data exfiltration patterns, abnormal sharing)
- Endpoint / EDR findings (e.g., persistence mechanisms, gaps in coverage, suspicious processes)
- Each finding includes severity, confidence, and clear remediation guidance

### Blast Radius & Residual Risk Assessment

- Identification of the most at-risk identities, devices, and applications
- Pointers to where logs, telemetry, or controls are insufficient
- Areas where additional investigation may be warranted

### Appendices (Optional Depth)

- IOC lists and detection categories used
- Supporting event samples, timelines, or screenshots
- Any additional technical detail required for follow-on work or internal teams
