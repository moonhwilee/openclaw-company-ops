# Ops Claim Ledger Entry: WU-20260604-002

Status: Manual Day-0

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-20260604-002-001`
- Work Unit id: `WU-20260604-002`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/6
- Claim type: `execution`
- Owner session ref: current OpenClaw main session
- Created at: 2026-06-04 KST
- Updated at: 2026-06-04 KST

## Expected Responsibility

- Expected state: `working`
- Expected until: before the next visible completion report for this Work Unit
- Last claim: Team Lead is writing the Discord event visibility guide and
  manual dry-run artifacts from Work Card #6.
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
  `docs/work-units/WU-20260604-002/assignment.md`
- Evidence ref:
  `docs/work-units/WU-20260604-002/evidence.md`
- Operations Lead decision ref:
  `docs/work-units/WU-20260604-002/decision.md`

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
