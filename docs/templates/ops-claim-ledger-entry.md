# Ops Claim Ledger Entry

Status: Manual Day-0

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref:
- Work Unit id:
- Work Card:
- Claim type: `orchestration` or `execution`
- Owner session ref:
- Created at:
- Updated at:

## Expected Responsibility

- Expected state:
- Expected until:
- Last claim:
- Last seen compaction count:

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
- Evidence ref:
- Operations Lead decision ref:

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

-
