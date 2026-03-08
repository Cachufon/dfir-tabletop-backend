# Cloud Mapping

## Purpose
Provide guidance for mapping cloud control plane and service activity events into the normalized schema.

## Common Raw Sources (examples)
- API gateway logs with fields like `principalId`, `eventName`, `sourceIPAddress`
- Cloud audit trails containing `identity.user`, `service`, `requestParameters`

## Field Mapping
| Common Raw Field Pattern | Normalized Field | Notes |
| --- | --- | --- |
| `principalId`, `identity.user` | `principal_id` | Use the unique principal or role identifier. |
| `userAgent`, `caller` | `source` | Preserve string to indicate originating service or role. |
| `eventName`, `operation`, `action` | `action` | Normalize verbs but keep original in raw reference. |
| `service`, `eventSource` | `cloud_provider` | Identify provider or service family. |
| `timestamp`, `eventTime` | `event_timestamp` | Convert to UTC and keep raw reference. |
| `sourceIPAddress`, `client.ip` | `source_ip` | Store without enrichment. |
| resource identifiers | `resource_id` | Use when the resource is clearly specified. |
| log location or object path | `raw_event_ref` | Relative path with offset or byte range when available. |

## Ambiguities and Handling
- When both user and assumed role are present, map `principal_id` to the effective identity and note the assumed role in a secondary field if available.
- If the provider cannot be determined, set `cloud_provider` to `unknown` and flag in validation.
- Complex nested resources should be flattened cautiously; retain raw path in `raw_event_ref`.

## Example Normalized Record
```json
{
  "event_id": "cloud-789",
  "event_type": "api.call",
  "event_timestamp": "2024-03-05T18:30:00Z",
  "scope_area": "cloud",
  "source": "control_plane",
  "cloud_provider": "generic_cloud",
  "action": "CreateInstance",
  "principal_id": "role/service-account",
  "source_ip": "192.0.2.44",
  "raw_event_ref": "../raw/cloud/audit.log:128"
}
```
