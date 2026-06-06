# Progress Log

Status: Optional Source Artifact

`progress.jsonl` records source-backed progress metadata for owner-facing
dashboard visibility. It is not evidence, not a decision, not completion truth,
and not a Team Lead execution log.

Use it only to keep long-running Work Units visibly alive in the Company
Dashboard without adding an LLM summarization call.

Each row is a JSON object:

```json
{
  "work_unit_id": "WU-260607-999",
  "transition_kind": "checkpoint",
  "phase_index": "2",
  "phase_total": "7",
  "phase": "implementation",
  "round": "1",
  "current_slice": "project-sync derivation",
  "next_checkpoint": "2026-06-07T04:00:00+09:00",
  "source_ref": "docs/examples/manual-dry-run/WU-260607-999/progress.jsonl",
  "proof_ref": "",
  "transition_at": "2026-06-06T18:00:00Z",
  "recorded_by": "operations-lead"
}
```

## Rules

- Append rows; do not treat the file as a dashboard database.
- Keep `Status` lifecycle coarse. Do not encode `Round 2` or `Phase 3` as a
  status.
- Do not infer progress from GitHub Project fields, GitHub comments, or
  free-form Discord text.
- `project-sync` may derive dashboard `Phase` from the latest valid row.
- Missing progress rows are normal for short Work Units.
