# AI Model 5 MAPS Pack

Model 5 leverages MAPS detections to monitor AI systems and related artifacts.

- MAPS consumes AI artifacts from `normalized/ai_artifacts.json` within the case directory.
- Findings and hits are produced for analysis under `analysis/detections/ai/` using the hit contract defined for MAPS (`rule_type=maps`).
- Use this pack to guide MAPS-based triage and to connect MAPS outputs back to the Model 5 scope.
