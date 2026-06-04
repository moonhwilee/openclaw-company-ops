# Ops Claim Ledger Entry: WU-20260604-001

Status: Manual Day-0

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-20260604-001-001`
- Work Unit id: `WU-20260604-001`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/4
- Claim type: `execution`
- Owner session ref: current OpenClaw main session
- Created at: 2026-06-04 KST
- Updated at: 2026-06-04 KST

## Expected Responsibility

- Expected state: `working`
- Expected until: before the next visible completion report for this Work Unit
- Last claim: Team Lead is writing the manual dry run artifacts and operations
  manual from Work Card #4.
- Last seen compaction count: not recorded in this manual example

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

- Assignment Packet:
  `docs/examples/manual-dry-run/WU-20260604-001/assignment.md`
- Evidence ref:
  `docs/examples/manual-dry-run/WU-20260604-001/evidence.md`
- Operations Lead decision ref:
  `docs/examples/manual-dry-run/WU-20260604-001/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- Work Card label `working` is a visibility signal only.
- This claim does not close the Work Unit.
- Completion still requires an Evidence & Result Record and Operations Lead
  decision.
