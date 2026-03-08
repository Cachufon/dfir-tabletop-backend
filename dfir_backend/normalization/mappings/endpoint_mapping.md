# Endpoint Mapping

## Purpose
Describe how endpoint telemetry maps to the normalized schema for host-level detections and triage.

## Common Raw Sources (examples)
- EDR process events with fields like `deviceId`, `hostname`, `process.name`, `action`
- Syslog exports containing `host`, `pid`, `cmdline`, `result`

## Field Mapping
| Common Raw Field Pattern | Normalized Field | Notes |
| --- | --- | --- |
| `deviceId`, `agent.id`, `hostId` | `host_id` | Prefer stable agent identifier when present. |
| `hostname`, `host` | `hostname` | Preserve original casing. |
| `process.name`, `exe`, `image` | `process_name` | Record executable name without path when possible. |
| `process.commandLine`, `cmdline` | `process_command_line` | Keep raw string; do not parse arguments. |
| `action`, `event.type`, `operation` | `action` | Normalize verbs for detection alignment. |
| `timestamp`, `eventTime` | `event_timestamp` | Convert to UTC; reference raw source. |
| `source.ip`, `remote_address` | `source_ip` | Keep as provided; no enrichment. |
| log file reference | `raw_event_ref` | Relative path with line or offset when available. |

## Ambiguities and Handling
- If both `host_id` and `hostname` exist, populate both to support joins.
- When `process_name` is missing but `cmdline` is present, derive only if clear; otherwise set `process_name` to `null` and warn.
- File paths may use different separators; store as seen and avoid normalization that may obscure provenance.

## Example Normalized Record
```json
{
  "event_id": "endpoint-321",
  "event_type": "process.start",
  "event_timestamp": "2024-04-15T07:45:00Z",
  "scope_area": "endpoint",
  "source": "generic_edr",
  "host_id": "agent-1001",
  "hostname": "workstation-01",
  "process_name": "powershell.exe",
  "process_command_line": "powershell.exe -enc ...",
  "action": "start",
  "source_ip": "203.0.113.50",
  "raw_event_ref": "../raw/endpoint/process.log:233"
}
```
