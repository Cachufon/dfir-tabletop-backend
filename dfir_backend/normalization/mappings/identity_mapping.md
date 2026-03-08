# Identity Mapping

## Purpose
Describe how identity-related authentication and access events map into the normalized schema for consistent detection logic.

## Common Raw Sources (examples)
- Authentication logs exporting `user`, `actor.email`, `ipAddress`, `result`
- Directory service audit events containing `principalId`, `timestamp`, `status`

## Field Mapping
| Common Raw Field Pattern | Normalized Field | Notes |
| --- | --- | --- |
| `user`, `actor.id`, `principalId` | `user_id` | Prefer stable unique identifiers; fall back to email when only available. |
| `userEmail`, `actor.email`, `email` | `user_email` | Preserve case as provided; do not derive domain. |
| `ipAddress`, `client.ip` | `source_ip` | Store as string without enrichment. |
| `timestamp`, `eventTime` | `event_timestamp` | Convert to UTC; retain raw timestamp reference. |
| `eventType`, `action`, `operation` | `event_type` | Normalize to verb-style where possible. |
| `status`, `result`, `auth.result` | `auth_result` | Map to canonical success/failure/unknown values. |
| file location or log reference | `raw_event_ref` | Relative path with offset or line when possible. |

## Ambiguities and Handling
- When both `user` and `actor.email` exist, map `user_id` to the most stable identifier and set `user_email` separately.
- If `auth_result` is missing, set to `null` and log a validation warning.
- Mixed timestamp formats should be recorded in `raw_event_ref` to aid troubleshooting.

## Example Normalized Record
```json
{
  "event_id": "abc-123",
  "event_type": "user.login",
  "event_timestamp": "2024-01-01T12:00:00Z",
  "scope_area": "identity",
  "source": "example_idp",
  "user_id": "00u1abcd",
  "user_email": "analyst@example.com",
  "source_ip": "203.0.113.10",
  "auth_result": "success",
  "raw_event_ref": "../raw/identity/auth.log:42"
}
```
