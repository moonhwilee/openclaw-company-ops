# WU-260612-503 Live Test Source

Status: Source

## Purpose

Verify the merged P3-lite closeout source index behavior after commit
`cbb96a751f041b86618994c797e3efa67c66841b`.

## Required Checks

- Confirm `work-unit closeout --dry-run` exposes a source index preview without
  writing `closeout-source-index.json`.
- Confirm `work-unit closeout --publish` writes `closeout-source-index.json`.
- Confirm the index is derived, non-authoritative, pointer-only, and uses
  `source_resolution_mode: direct_source_scan`.
- Confirm the index adds no external calls, LLM calls, daemon, DB, vector
  search, or GitHub/Discord/Project cache.
- Confirm associated docs describe timing artifacts and source indexes as
  diagnostic or derived metadata, not proof authority.

## Non-goals

- Do not change runtime code.
- Do not add a new source of truth.
- Do not use GitHub comments, Project fields, Discord messages, or timing files
  as closeout decision authority.
