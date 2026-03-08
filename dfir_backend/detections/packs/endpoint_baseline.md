# Endpoint Baseline Pack

Use this pack for endpoint detections across operating systems and EDR sources.

- Reference both `dfir_backend/rules/sigma/` and `dfir_backend/rules/yara/` for endpoint coverage.
- Typical categories: persistence, suspicious processes, lateral movement, and EDR tampering.
- Combine baseline rules with host-specific content under `dfir_backend/custom/<case_id>/` when applicable.
