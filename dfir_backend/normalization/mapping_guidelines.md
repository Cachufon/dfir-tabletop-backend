# Mapping Guidelines

- Convert all timestamps to UTC and retain the original timestamp field in the raw payload when available.
- If required fields are missing, set them to `null` in the normalized output and record a validation warning.
- User identifiers: prefer stable IDs; if only an email exists, map it to `user_email` and leave `user_id` as `null`.
- IP fields: store the original string representation; do not attempt enrichment unless explicitly part of the workflow.
- `raw_event_ref`: store a relative path to the raw file and record offset or line details when available.
- Preserve source or vendor identifiers in the `source` field to maintain traceability.
