# Ops Claim Ledger Entry

Status: Done

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-260606-001-001`
- Work Unit id: `WU-260606-001`
- Title: Add Work Unit status summary helper
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/17
- Claim type: `execution`
- Owner session ref: `build-lab`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Expected Responsibility

- Expected state: `done`
- Expected until: `2026-06-06T03:00:00+09:00`
- Last claim: Operations Lead accepted evidence; Work Card ready for closure after source links are present.
- Last seen compaction count: `0`

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

- Assignment Packet: `docs/examples/manual-dry-run/WU-260606-001/assignment.md`
- Evidence ref: `docs/examples/manual-dry-run/WU-260606-001/evidence.md`
- Operations Lead decision ref: `docs/examples/manual-dry-run/WU-260606-001/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- Phase 2 dogfood claim. The helper must remain read-only.
