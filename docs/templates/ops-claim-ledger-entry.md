# Ops Claim Ledger Entry

Status: Manual Day-0

The Ops Claim Ledger records expected responsibility. It is not lifecycle
truth, progress history, evidence storage, a dashboard database, or a recovery
system.

This is an internal responsibility artifact, not a user-facing UI. Owners and
packaged users should normally inspect the GitHub Project dashboard, Work Card,
Discord visibility cards, evidence, and Operations Lead decision instead.

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

Do not use this field as completion truth. User-facing status derives lifecycle
from source artifacts in this order: final Operations Lead decision, result
evidence/proof, claim responsibility, then assignment. Accepted work remains
`accepted` until owner inspection and Work Card cleanup make it archival
`done`.

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
