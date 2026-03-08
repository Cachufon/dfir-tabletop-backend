# Triage Runbook

## Steps
1. Review `detections_rollup.md` and per-scope `hits_summary.md`.
2. Open each `hits.json` and tag obvious false positives.
3. Cluster hits into storylines (by actor, asset, time proximity, technique).
4. Write `storyline_candidates.md` (using the template).
5. Promote validated storylines to findings:
   - Create `analysis/findings/finding_ID-###.md` using `dfir_backend/reporting/finding_template.md`.
   - Create or update `analysis/findings/findings_index.md`.
6. Mark dismissed items and record rationale in `triage_notes.md`.
7. Ensure each finding references `hit_ids` and evidence refs.

## Guidance
- Separate severity from confidence to avoid conflating impact with evidence strength.
- Use MITRE ATT&CK mapping when applicable to aid cross-case consistency.
- Record limitations and data gaps explicitly so stakeholders understand residual risk.
