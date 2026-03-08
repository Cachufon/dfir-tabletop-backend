# Cloud Scope Area Workflow (Stub)

This document outlines the high-level workflow for running the Cloud scope area within a Compromise Assessment. It can be used:

- As a cloud-only compromise assessment, or
- Combined with Identity, SaaS, Endpoint, and/or AI scope areas.

## High-Level Steps (v1 Stub)

1. Confirm in-scope cloud providers (AWS, GCP, Azure) and the review window.
2. Collect cloud data:
   - Cloud audit trails (CloudTrail, Azure Activity Logs, GCP Admin/audit logs) as the minimum set.
   - Optional IAM configuration snapshots, CSPM exports, Kubernetes audit logs, and VPC flow/proxy logs when available.
3. Normalize and prepare cloud events for analysis.
4. Apply cloud-focused detection logic (e.g., anomalous IAM changes, suspicious access patterns, risky service enablement, cross-account access anomalies).
5. Triage and investigate notable cloud activity with emphasis on access anomalies and misconfiguration-driven exposure.
6. Summarize cloud-related findings, including suspicious principals, projects/subscriptions, and risky service usage.
7. When combined with other scope areas, correlate cloud findings with suspect identities, SaaS resources, endpoints, or AI workloads.

This file will be expanded with more detailed steps, queries, and mappings to specific detection rules.
