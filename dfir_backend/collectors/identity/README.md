# Identity Collector Stub

## Purpose
Ingest identity authentication, MFA, administrative, and application-access telemetry to support user-centric investigations and detections. Mapping should align to the [normalized data contract](../../normalization/normalized_data_contract.md).

## Required inputs
- Authentication events (login/logoff, token issuance)
- User identity (account, tenant, identifiers)
- Source IP or originating host
- Result status (success, failure, challenge)

## Optional inputs
- Multi-factor authentication logs (prompts, methods, outcomes)
- Administrative activity logs (privileged actions, role changes)
- OAuth or SAML federation events

## Normalized output
- Identity Event Schema defined in the normalized data contract

## Failure modes and limitations
- Missing user identifiers or source context reduces correlation and enrichments
- Incomplete MFA signals may limit detection of bypass attempts
- Vendor-specific fields must be mapped to the schema without introducing proprietary dependencies
- Time skew or partial log delivery can cause sequence gaps and false negatives
