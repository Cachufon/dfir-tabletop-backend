# CA Case Workflow State Machine

## Purpose

Define a single CA state machine that supports three ingestion strategies and converges to shared delivery gates.

## Ingestion Strategies

- export
- hunt-in-place
- remote collection

## State Machine

### Entry

- `case_created`

### Strategy-Specific Ingestion States

- `ingestion_export`
- `ingestion_hunt_in_place`
- `ingestion_remote_collection`

### Converged Gates (Required for All Strategies)

After ingestion, every strategy must converge to the same gate sequence:

1. `telemetry_validated`
2. `normalized`
3. `detections`
4. `triage`
5. `findings`
6. `reporting`

### Exit

- `case_closed`

## Transition Rules

- `case_created -> ingestion_export`
- `case_created -> ingestion_hunt_in_place`
- `case_created -> ingestion_remote_collection`
- `ingestion_export -> telemetry_validated`
- `ingestion_hunt_in_place -> telemetry_validated`
- `ingestion_remote_collection -> telemetry_validated`
- `telemetry_validated -> normalized`
- `normalized -> detections`
- `detections -> triage`
- `triage -> findings`
- `findings -> reporting`
- `reporting -> case_closed`

## Data Handling Warning

**DO NOT COMMIT CLIENT DATA**
