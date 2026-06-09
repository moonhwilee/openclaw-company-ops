# Ops Claim Ledger Entry

Status: Draft

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-260609-958-001`
- Work Unit id: `WU-260609-958`
- Title: Phase 5.8.6 delegated closeout live gate
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/37
- Claim type: `execution`
- Owner session ref: `build-lab`
- Created at: `2026-06-09T11:59:46Z`
- Updated at: `2026-06-09T12:01:03Z`

## Expected Responsibility

- Expected state: `working`
- Expected until:
- Last claim: `build-lab` started work. Source: `docs/examples/manual-dry-run/WU-260609-958/assignment.md`.
- Last seen compaction count: `unknown`

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

- Assignment Packet: `docs/examples/manual-dry-run/WU-260609-958/assignment.md`
- Evidence ref: `docs/examples/manual-dry-run/WU-260609-958/evidence.md`
- Operations Lead decision ref: `docs/examples/manual-dry-run/WU-260609-958/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

-
