# Triage Object Model (Analyst Reference)

Use this lightweight model to capture how detection hits roll up into storylines and ultimately findings. It guides consistent note-taking; it is **not** a code schema.

- **Storyline ID**
- **Related hit_ids**
- **Primary actor(s) (user/principal)**
- **Primary asset(s) (mailbox/host/resource/ai_system)**
- **Suspected technique/theme**
- **Time window (first/last)**
- **Working hypothesis**
- **Evidence summary links (raw_event_ref pointers)**
- **Triage status (candidate / validated / dismissed)**
- **Notes**

Multiple hits can map to a single storyline. Multiple storylines can map to one finding (rare), so keep references explicit.
