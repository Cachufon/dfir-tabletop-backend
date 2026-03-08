# SaaS Collector Stub

## Purpose
Ingest SaaS application activity including mail, files, collaboration, and app access to inform user and data-centric investigations. Mapping should align to the [normalized data contract](../../normalization/normalized_data_contract.md).

## Required inputs
- Audit logs or activity streams
- User identity
- Action performed
- Target object or resource

## Optional inputs
- Mailbox rule changes and forwarding configurations
- File downloads, sync events, or exfiltration indicators
- External sharing and access invitations
- OAuth consent grants and application authorizations
- Administrative actions

## Normalized output
- SaaS Event Schema defined in the normalized data contract

## Failure modes and limitations
- Limited audit depth can obscure sensitive actions (e.g., file reads vs. edits)
- Missing target context or identifiers reduces investigation fidelity
- Variations across vendors require careful field mapping to stay vendor-agnostic
- Deferred or throttled log delivery may delay detections and timeline reconstruction
