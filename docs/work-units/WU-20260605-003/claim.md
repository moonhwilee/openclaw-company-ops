# Ops Claim Ledger Entry

Status: Done

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-WU-20260605-003-001`
- Work Unit id: `WU-20260605-003`
- Title: Pre-Dogfood Discord Visibility Setup
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/16
- Claim type: `execution`
- Owner session ref: `main`
- Created at: `2026-06-05`
- Updated at: `2026-06-05`

## Expected Responsibility

- Expected state: `done`
- Expected until: `2026-06-05`
- Last claim: Phase 1 pre-dogfood Discord visibility accepted. Discord
  connector, channel map, route bindings, harmless `#ops-feed` event, and
  owner-authored `#team-build-pq` Q&A smoke are recorded in evidence and
  accepted by Operations Lead decision.
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

- Assignment Packet: `docs/work-units/WU-20260605-003/assignment.md`
- Evidence ref: `docs/work-units/WU-20260605-003/evidence.md`
- Operations Lead decision ref: `docs/work-units/WU-20260605-003/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- Discord was not configured at assignment creation time; Phase 1 configured
  and verified it.
- Initial Team Lead Q&A failed because `build-pq` lacked Company Ops
  source-of-truth context, then failed once more because the Discord channel
  session reused stale context. The stale session was archived and the fresh
  session passed.
- Discord remains visibility and direct Q&A only, not source-of-truth mutation.
