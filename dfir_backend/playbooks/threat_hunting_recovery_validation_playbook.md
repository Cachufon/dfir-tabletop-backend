# Threat Hunting Recovery Validation Playbook

## Purpose
Guide threat hunting activities focused on validating recovery efforts, ensuring eradication steps are effective, and confirming no residual adversary activity remains.

## Service Mapping
- Compromise Assessments Add-on.

## Prerequisites
- Data sources required: post-incident telemetry (EDR, SIEM), recovery change logs, endpoint configuration baselines, authentication activity, and network egress monitoring.
- Tools required: hunting query library, detection engineering platform, EDR remote response, and timeline construction utilities.
- Permissions required: access to production telemetry, authority to initiate ad-hoc collections, and approval to run validation scripts on recovered systems.
- Any approvals or scoping steps: align on recovery objectives, confirm list of remediated assets, and define success criteria for validation checks.

## Workflow Steps
1. Define objective.
2. Identify data sources and assets.
3. Request or collect logs and artifacts.
4. Ingest and normalize data.
5. Apply relevant detection rules.
6. Triage and investigate findings.
7. Build narrative and blast radius.
8. Draft report and recommendations.
9. Internal QA review.
10. Deliver readout to customer.

## Indicators to Hunt For
- Reappearance of previously identified IOCs or persistence mechanisms.
- Anomalous service creations, scheduled tasks, or launch items after remediation.
- Residual lateral movement or credential theft activity (Kerberoasting, token abuse, Pass-the-Hash).
- Unauthorized outbound connections or beaconing from assets marked as recovered.
- Configuration drift from hardened baselines, including disabled logging or tampered EDR agents.

## Common Pitfalls
- Assuming recovery success without validating on all affected asset classes.
- Not updating detection content with new IOCs, causing missed recurrences.
- Incomplete scoping of remediated hosts, leaving related assets unvalidated.
- Skipping coordination with change management, leading to false positives from planned work.

## Output Artifacts
- Recovery validation report summarizing hunt scope, checks performed, and residual risk.
- Updated IOC and detection sets incorporating lessons learned from the incident.
- Evidence package of validation queries, results, and any follow-up actions.
- Recommendations for hardening and monitoring to prevent recurrence.
