# Phase 1 Normalization Overview

This document outlines a first-pass normalization approach for commonly ingested log sources. The goal is to emit consistent records with a small set of required fields so downstream analytics and detections can operate across disparate products.

## Common fields
- `timestamp` — Original event time preserved with timezone when provided.
- `actor` — Primary user or principal (username, UID, service account, or API client) responsible for the event.
- `ip` — Source IP address for the actor or requesting host.
- `action` — Normalized verb describing the operation (e.g., `login`, `create`, `update`, `delete`, `execute`).
- `resource` — Target entity impacted by the action (file path, object ID, endpoint, or SaaS resource).
- `status` — Success/failure indicator captured as `success` or `failure`, derived from native status codes.

## Identity telemetry (IdP and auth infrastructure)
- Parse authentication and authorization events from IdPs (SSO, MFA, VPN concentrators).
- Map original event codes to normalized `action` values such as `login`, `logout`, `password_change`, `mfa_challenge`, and `token_issue`.
- Populate `actor` from the asserted username or account identifier; include device identifiers in a `device_id` extended field when present.
- Capture IP information from connection metadata, preferring client/source fields over load balancer addresses.
- Normalize outcome to `status` and include native result codes in `raw_status` for troubleshooting.

## SaaS application logs
- Focus on user-facing activities (document access, sharing, permission changes, admin actions).
- Derive `action` from audit verbs or CRUD operations; consider `share`, `download`, `upload`, `permission_change`, and `config_change` as common values.
- Use `resource` to store the affected asset (document ID, folder path, project, dashboard, etc.).
- Capture `actor` from user email or account ID and `ip` from session metadata or request context.
- Include additional normalized context fields such as `device`, `location`, and `actor_role` when available.

## Endpoint logs (EDR/AV/OS telemetry)
- Normalize process and file activity to actions like `process_start`, `process_end`, `file_create`, `file_modify`, `file_delete`, and `network_connection`.
- Populate `resource` with the object under operation (process path, file path, registry key, or remote address/port for network events).
- Set `actor` to the executing user SID/UID or service account associated with the process.
- Preserve host identifiers (`hostname`, `asset_id`, `sensor_id`) in extended fields to correlate across data sources.
- Map engine verdicts or detection outcomes to `status`, keeping raw disposition or severity in supplemental fields.

## General considerations
- Maintain a minimal schema for Phase 1 to unblock ingestion; additional fields can be added in later phases.
- Keep original raw records available for enrichment and troubleshooting alongside normalized outputs.
- Document field mappings per source to ensure repeatability and make detection queries portable across environments.
