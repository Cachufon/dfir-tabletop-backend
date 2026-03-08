# Normalized Data Contract (v1)

This document defines the normalized data contract used by Gruve Compromise Assessment workflows (Models 1–4) and the AI Safety & Prompt Security Assessment (Model 5).

The normalized data contract specifies the minimum expected structure of data after ingestion and before detection, analysis, or reporting. It is vendor-agnostic and intentionally minimal.

---

## General Principles

- Raw telemetry and artifacts are preserved separately.
- Normalized records enable cross-source correlation and consistent detection logic.
- Collection mechanisms may vary; normalized structure should not.
- AI Safety artifacts (Model 5) use a separate, non-event-based schema.

---

## Common Fields (All Telemetry Records)

All normalized telemetry records must include:

- event_id
- event_type
- event_timestamp (UTC)
- source
- scope_area
- raw_event_ref
- ingest_time (UTC)
- confidence_hint (optional)

---

## Identity Event Schema

Used for identity-related telemetry in Models 1–4.

Fields:
- scope_area: identity
- user_id
- user_email
- auth_method
- auth_result
- mfa_method
- source_ip
- geo_country
- geo_city
- device_id
- app_id
- is_admin_action

---

## SaaS Event Schema

Used for SaaS-related telemetry in Models 1–4.

Fields:
- scope_area: saas
- user_id
- user_email
- service
- object_type
- object_id
- action
- target
- source_ip
- is_external

---

## Cloud Event Schema

Used for cloud provider telemetry in Models 1–4.

Fields:
- scope_area: cloud
- cloud_provider
- account_id
- principal_id
- principal_type
- action
- resource
- source_ip
- geo_country

---

## Endpoint Event Schema

Used for endpoint telemetry in Models 1–4.

Fields:
- scope_area: endpoint
- host_id
- hostname
- os
- user_id
- process_name
- process_path
- command_line
- parent_process
- action
- destination_ip

---

## AI Artifact Schema (Model 5 Only)

Used exclusively for AI Safety and Prompt Security Assessment (Model 5).

This schema is artifact-based, not event-based.

Fields:
- scope_area: ai
- artifact_type
- artifact_id
- ai_system
- source
- review_context

---

## Notes

- Not all fields are required for all sources; missing fields should be null.
- Additional source-specific fields may exist in raw data but should not be relied upon for detection logic.
- Detection rules and workflows should assume this normalized structure.

This contract is expected to evolve, but changes should remain backward-compatible where possible.
