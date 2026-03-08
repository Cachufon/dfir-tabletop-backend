# Endpoint Collector Stub

## Purpose
Ingest endpoint alerts or triage artifacts to support host-based investigation and response. Mapping should align to the [normalized data contract](../../normalization/normalized_data_contract.md).

## Required inputs
- Endpoint alerts or triage bundle

## Optional inputs
- Process telemetry (command lines, hashes, parent/child relationships)
- Network connections or flow summaries
- Persistence mechanisms (services, autoruns, scheduled tasks)
- Removable media/USB activity

## Normalized output
- Endpoint Event Schema defined in the normalized data contract

## Failure modes and limitations
- Missing triage elements (memory, persistence, network) reduce investigation completeness
- Alerts without supporting telemetry may be insufficient for root-cause analysis
- Sensor tampering or containment actions can interrupt data collection
- Large bundles may need staged processing or filtering to meet ingestion limits
