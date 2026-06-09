# Ops Claim Ledger Entry

Status: Done

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-260606-003-001`
- Work Unit id: `WU-260606-003`
- Title: Add execution route to Work Unit status summary
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/19
- Claim type: `execution`
- Owner session ref: `agent:build-lab:discord:channel:1512413731752116335`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Expected Responsibility

- Expected state: `done`
- Expected until: `2026-06-06T04:00:00+09:00`
- Last claim: Operations Lead accepted the execution-route status summary
  patch after verifying evidence and checks.
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

- Assignment Packet: `docs/work-units/WU-260606-003/assignment.md`
- Evidence ref: `docs/work-units/WU-260606-003/evidence.md`
- Operations Lead decision ref: `docs/work-units/WU-260606-003/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- Execution route: `discord-bound`
- Target team channel: `#team-build-lab`
- Route validation: owner-authored inbound message and build-lab response were
  read back in the target team channel before this Work Unit started.
- Expected Discord team-channel record: assignment handoff and Team Lead result
  response should be visible in `#team-build-lab`.
