# Ops Claim Ledger Entry

Status: Draft

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-260607-003-001`
- Work Unit id: `WU-260607-003`
- Title: Verify Company Ops operating path
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/22
- Claim type: `execution`
- Owner session ref: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Expected Responsibility

- Expected state: `waiting`
- Expected until: `2026-06-07T03:30:00+09:00`
- Last claim: Operations Lead revised the Work Unit after final proof validation
  failed on Discord assignment ordering. Work Card remains open and Project item
  remains visible for owner review/follow-up.
- Last seen compaction count: `unknown`

Allowed expected states:

- `assigned`
- `working`
- `waiting`
- `blocked`
- `result_ready`
- `done`

`done` is not completion truth. It is an expected responsibility state after
the Operations Lead has made a decision.

## Artifact References

- Assignment Packet: `docs/examples/manual-dry-run/WU-260607-003/assignment.md`
- Evidence ref: `docs/examples/manual-dry-run/WU-260607-003/evidence.md`
- Operations Lead decision ref: `docs/examples/manual-dry-run/WU-260607-003/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- Execution route: `cli-direct`.
- Discord visibility route: foreground `discord publish-card` to `#ops-feed`
  and `#team-build-lab`.
- GitHub Project sync route: one-shot `project-sync apply` through
  `discord publish-card --project-sync-field-map`.
- Verify-only guardrail: Team Lead must not mutate files, GitHub, Project, or
  Discord.
- Observation: parallel `discord publish-card` calls can race the Project sync
  lock. In this run, the ops-feed card read back successfully while its Project
  sync failed on the lock; the team-detail publish immediately after succeeded
  and left the Project item in `Assigned`.
