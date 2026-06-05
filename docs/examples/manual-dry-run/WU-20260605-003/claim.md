# Ops Claim Ledger Entry

Status: Draft

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

- Expected state: `assigned`
- Expected until: `2026-06-05`
- Last claim: Phase 1 pre-dogfood visibility Work Unit prepared; waiting for
  Discord channel/setup and routing execution.
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

- Assignment Packet: `docs/examples/manual-dry-run/WU-20260605-003/assignment.md`
- Evidence ref: `docs/examples/manual-dry-run/WU-20260605-003/evidence.md`
- Operations Lead decision ref: `docs/examples/manual-dry-run/WU-20260605-003/decision.md`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

- Discord is not configured in local OpenClaw at assignment creation time.
- Current OpenClaw agent routing bindings are zero at assignment creation time.
- If Discord credentials or channel ids are missing, report `blocked` instead
  of substituting Telegram summaries for Discord visibility.
