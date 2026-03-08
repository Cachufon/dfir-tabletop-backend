# Cloud Collector Stub

## Purpose
Ingest cloud control-plane and access telemetry to monitor configuration changes, resource operations, and administrative activity. Mapping should align to the [normalized data contract](../../normalization/normalized_data_contract.md).

## Required inputs
- Audit trail or control-plane event stream
- Principal identity (user, role, service)
- Action performed

## Optional inputs
- IAM or access policy snapshots
- Kubernetes audit logs
- Network flow logs

## Normalized output
- Cloud Event Schema defined in the normalized data contract

## Failure modes and limitations
- Gaps in audit logging or disabled services create blind spots for key operations
- Lack of principal context (assumed roles, federated identities) limits attribution
- Network and Kubernetes visibility varies by platform and may require additional collectors
- Delayed or regionalized log delivery can complicate timeline alignment
