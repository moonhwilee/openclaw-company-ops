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
  "mode": "goal",
  "phase_index": "2",
  "phase_total": "7",
  "phase": "implementation",
  "round": "1",
  "show_round": false,
  "current_slice": "project-sync derivation",
  "next_checkpoint": "2026-06-07T04:00:00+09:00",
  "source_ref": "docs/work-units/WU-260607-999/progress.jsonl",
  "proof_ref": "",
  "transition_at": "2026-06-06T18:00:00Z",
  "recorded_by": "operations-lead"
}
```

## Rules

- Append rows; do not treat the file as a dashboard database.
- Keep `Status` lifecycle coarse. Do not encode `Round 2` or `Phase 3` as a
  status.
- `mode=goal` and `mode=convergence` automatically display `round` as a compact
  leading label such as `R1`. Keep `show_round` false or absent for one-pass
  work such as ordinary verify unless the owner explicitly asks to see round
  labels in the dashboard.
- Prefer `work-unit checkpoint` for live long-work checkpoints. It uses one
  payload for the team `CHECKPOINT`, the `progress.jsonl` row, and changed-only
  Project mirror sync after Discord readback when the dispatch
  `checkpoint_contract` or explicit Project sync args are present.
- Progress display preserves the full source slice text. Keep checkpoint labels
  concise as source writing discipline; do not depend on renderer truncation.
- Do not infer progress from GitHub Project fields, GitHub comments, or
  free-form Discord text.
- `project-sync` may derive dashboard `Progress` from the latest valid row.
- Missing progress rows are normal for short Work Units.
