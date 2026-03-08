# Detection Execution Contract

This document defines the canonical structure for detection execution outputs produced from normalized datasets under `dfir_backend/custom/<case_id>/normalized/`.

## Hit Record Schema

Each detection hit is represented as a JSON object with the following fields:

- `hit_id` (string)
- `rule_id` (string)
- `rule_name` (string)
- `rule_type` (`sigma` | `yara` | `ioc` | `maps`)
- `scope_area` (`identity` | `saas` | `cloud` | `endpoint` | `ai`)
- `severity_hint` (`info` | `low` | `medium` | `high` | `critical`)  # pre-triage
- `event_time` (UTC timestamp, optional if artifact-based)
- `actor` (user_id/user_email or principal_id)
- `asset` (hostname, mailbox, file, repo, cloud resource, or ai_system)
- `source` (where it came from: okta/o365/aws/etc)
- `evidence_refs` (list of raw_event_ref or artifact pointers)
- `summary` (1-2 sentences)
- `notes` (optional)

`hits.json` is an array of hit objects adhering to this schema.

## Hits Summary

`hits_summary.md` is a human-readable table summarizing detections for quick triage. At minimum it should include:

- `rule_id`
- `rule_name`
- `count`
- key actors/assets involved

This summary complements the detailed records in `hits.json`.
