# Validation Rules

## Identity minimum required
- `event_id`, `event_type`, `event_timestamp`, `source`, `scope_area`
- `user_email` **OR** `user_id`
- `auth_result` (if auth-related event)
- `source_ip` (when present)

## SaaS minimum required
- `event_id`, `event_type`, `event_timestamp`, `source`, `scope_area`
- `user_email` **OR** `user_id`
- `service`
- `action`
- `object_type` (when applicable)

## Cloud minimum required
- `event_id`, `event_type`, `event_timestamp`, `source`, `scope_area`
- `cloud_provider`
- `action`
- `principal_id` (when applicable)

## Endpoint minimum required
- `event_id`, `event_type`, `event_timestamp`, `source`, `scope_area`
- `hostname` **OR** `host_id`
- `action`
- `process_name` (when applicable)

## AI artifact minimum required (Model 5)
- `scope_area` = `ai`
- `artifact_type`
- `artifact_id`
- `ai_system` (if known)
- `source`

Missing required fields reduce confidence and should be recorded as limitations in reporting so analysts know where assumptions or gaps exist.
