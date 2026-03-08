# Endpoint Scope Area Data Sources

This document describes the minimum and optional data sources required to run the Endpoint scope area effectively.

## Minimum Data Sources

At least ONE of the following must be available for endpoints in scope:

- EDR alert/detection feeds (e.g., CrowdStrike, Defender for Endpoint, SentinelOne), OR
- Host triage bundles for selected endpoints (e.g., Velociraptor/OSQuery/macOS triage scripts)

These allow Gruve to:
- Identify hosts with suspicious or confirmed detections
- Review a sample of endpoints for persistence and anomalous behavior

## Optional Data Sources (Recommended Where Available)

- EDR timeline / raw telemetry exports (process, network, file events)
- Additional host triage collections (persistence, user activity, installed software)
- Sysmon and relevant Windows event logs
- macOS-specific artifacts, such as LaunchAgents/Daemons, TCC databases, and unified logs

Optional sources strengthen:
- Detection of subtle or stealthy persistence
- Reconstruction of endpoint-level timelines and potential lateral movement
- Understanding how endpoint-level activity relates to identity and SaaS findings
