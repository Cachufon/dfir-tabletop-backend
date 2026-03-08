# AI Artifact Mapping

## Purpose
Define how AI-related artifacts (Model 5) are mapped into the normalized schema to support AI investigation workflows.

## Common Raw Sources (examples)
- Model output logs containing `artifactId`, `artifactType`, `model`
- AI audit traces with `user`, `prompt`, `output_path`, `timestamp`

## Field Mapping
| Common Raw Field Pattern | Normalized Field | Notes |
| --- | --- | --- |
| `artifactId`, `id` | `artifact_id` | Unique identifier for the AI artifact. |
| `artifactType`, `type` | `artifact_type` | Normalize to categories like `prompt`, `output`, `model_file`. |
| `model`, `ai_system`, `engine` | `ai_system` | Capture model or system identifier when known. |
| `timestamp`, `eventTime` | `event_timestamp` | Convert to UTC; keep raw reference. |
| `user`, `actor.email` | `user_id`/`user_email` | Map stable ID when available; otherwise map email. |
| `location`, `path`, `uri` | `raw_event_ref` | Use relative paths for artifact provenance. |
| `source` or system label | `source` | Preserve origin system label. |

## Ambiguities and Handling
- When the artifact is generated automatically, `user_id` may be null; note this during validation.
- If `ai_system` is not provided, set to `null` but preserve any related hints in `raw_event_ref`.
- Prompts and outputs may be large; store references rather than full content in the normalized record when feasible.

## Example Normalized Record
```json
{
  "event_id": "ai-999",
  "event_type": "ai.artifact",
  "event_timestamp": "2024-05-20T14:00:00Z",
  "scope_area": "ai",
  "source": "model_pipeline",
  "artifact_id": "prompt-001",
  "artifact_type": "prompt",
  "ai_system": "model5",
  "user_email": "creator@example.com",
  "raw_event_ref": "../raw/ai/prompts.json:12"
}
```
