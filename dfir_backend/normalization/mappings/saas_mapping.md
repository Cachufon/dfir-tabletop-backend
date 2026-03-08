# SaaS Mapping

## Purpose
Outline how SaaS activity logs are transformed into the normalized schema for consistent cross-service analytics.

## Common Raw Sources (examples)
- API audit logs with fields like `actor.email`, `serviceName`, `methodName`
- Admin activity exports containing `user`, `action`, `object`, `ipAddress`

## Field Mapping
| Common Raw Field Pattern | Normalized Field | Notes |
| --- | --- | --- |
| `actor.id`, `user` | `user_id` | Use stable IDs when provided; otherwise leave `user_id` null. |
| `actor.email`, `userEmail` | `user_email` | Map email directly; avoid inference. |
| `serviceName`, `app`, `product` | `service` | Identify SaaS platform name. |
| `methodName`, `action`, `activity` | `action` | Align to normalized verbs when possible. |
| `resource.type`, `object.type` | `object_type` | Set when the target object is known. |
| `timestamp`, `eventTime` | `event_timestamp` | Convert to UTC; reference raw location. |
| file location or log reference | `raw_event_ref` | Store relative path and offset if available. |
| `client.ip`, `ipAddress` | `source_ip` | Preserve raw string format. |

## Ambiguities and Handling
- If only an email is present, set `user_email` and keep `user_id` as `null`.
- When `object_type` is unclear, set to `null` and note in validation warnings.
- Multi-tenant identifiers should be preserved in `source` to maintain context.

## Example Normalized Record
```json
{
  "event_id": "saas-456",
  "event_type": "file.download",
  "event_timestamp": "2024-02-10T09:15:00Z",
  "scope_area": "saas",
  "source": "generic_saas",
  "user_email": "owner@example.com",
  "service": "document_store",
  "action": "download",
  "object_type": "file",
  "source_ip": "198.51.100.25",
  "raw_event_ref": "../raw/saas/audit.json:5"
}
```
