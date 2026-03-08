# macOS Investigations Playbook

## Purpose
Provide a consistent approach to investigating macOS security incidents, from scoping impacted hosts to validating remediation and documenting findings.

## Service Mapping
- macOS Investigations.

## Prerequisites
- Data sources required: EDR telemetry, unified logs, endpoint inventory, network proxy or firewall logs, and authentication events.
- Tools required: macOS unified log collection utilities, EDR collection modules, file system triage tools (e.g., mac_apt, Kape), and timestomping validation utilities.
- Permissions required: ability to request host-based collections, access to management consoles (MDM/EDR), and approval to pull network telemetry.
- Any approvals or scoping steps: confirm engagement scope with customer, validate affected business units, and obtain change control approval for live response actions.

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
- Suspicious LaunchAgents/LaunchDaemons, login items, or persistent profiles.
- Unsigned or recently compiled binaries in user-writable paths (~/Library, /Users/Shared).
- Abnormal network connections (dynamic DNS, uncommon ports, encrypted tunnels).
- Abuse of native utilities (osascript, curl, powershell, python3) for execution or data staging.
- TCC or privacy control modifications allowing unexpected access to mic/camera or documents.
- Repeated failed sudo prompts or anomalous authentication events.

## Common Pitfalls
- Missing unified log context due to time-window gaps or incorrect timezone handling.
- Collecting artifacts without ensuring Full Disk Access, leading to incomplete data.
- Overlooking quarantine, Gatekeeper, and notarization metadata when validating file provenance.
- Ignoring user-specific persistence locations that differ from system-wide paths.

## Output Artifacts
- Incident summary report with timeline, blast radius, and remediation actions.
- Evidence bundle of collected artifacts, logs, and screenshots.
- IOC list for monitoring, blocking, and retrospective searches.
- Recommendations and hardening checklist tailored to affected macOS versions.
