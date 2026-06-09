# Ops Claim Ledger Entry

Status: Active

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-260607-004-001`
- Work Unit id: `WU-260607-004`
- Title: Verify Company Ops live operating path after Progress updates
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/23
- Claim type: `execution`
- Owner session ref: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Expected Responsibility

- Expected state: `waiting`
- Expected until: `2026-06-06T21:00:00Z`
- Last claim: Operations Lead decision is `Revise`; waiting for owner or the
  next Work Unit to add a formal revise closeout path.
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

- Assignment Packet: `docs/work-units/WU-260607-004/assignment.md`
- Evidence ref: `docs/work-units/WU-260607-004/evidence.md`
- Operations Lead decision ref: `docs/work-units/WU-260607-004/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- This claim tracks expected responsibility only. GitHub Project `Progress`,
  Discord visibility, and Work Card labels remain mirrors/proofs, not source of
  truth.
