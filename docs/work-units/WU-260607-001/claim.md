# Ops Claim Ledger Entry

Status: Done After Operations Lead Review

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-260607-001-001`
- Work Unit id: `WU-260607-001`
- Title: Dashboard sync sample request
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/20
- Claim type: `execution`
- Owner session ref: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Expected Responsibility

- Expected state: `done`
- Expected until: `2026-06-08`
- Last claim: `build-lab` sample request was executed by the Operations Lead
  session, Project sync was applied, and Project readback was verified.
- Last seen compaction count: `1`

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

- Assignment Packet: `docs/work-units/WU-260607-001/assignment.md`
- Evidence ref: `docs/work-units/WU-260607-001/evidence.md`
- Operations Lead decision ref: `docs/work-units/WU-260607-001/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- This is an intentionally bounded dashboard sync sample, not a production
  feature implementation Work Unit.
