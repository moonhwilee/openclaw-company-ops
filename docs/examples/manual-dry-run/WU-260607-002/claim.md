# Ops Claim Ledger Entry

Status: Done

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-260607-002-001`
- Work Unit id: `WU-260607-002`
- Title: Full Company Ops integration smoke
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/21
- Claim type: `execution`
- Owner session ref: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Expected Responsibility

- Expected state: `done`
- Expected until: `2026-06-07T02:30:00+09:00`
- Last claim: Operations Lead accepted the Team Lead result and completed the
  integration smoke review.
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

- Assignment Packet: `docs/examples/manual-dry-run/WU-260607-002/assignment.md`
- Evidence ref: `docs/examples/manual-dry-run/WU-260607-002/evidence.md`
- Operations Lead decision ref: `docs/examples/manual-dry-run/WU-260607-002/decision.md`

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
