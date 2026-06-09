# Operations Lead Decision

Status: Accepted

The Operations Lead decision records whether the submitted result satisfies the
Assignment Packet and evidence requirements.

## Identity

- Decision ref: `DECISION-WU-260606-002`
- Work Unit id: `WU-260606-002`
- Title: Patch Work Unit execution visibility routing
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/18
- Assignment Packet: `docs/work-units/WU-260606-002/assignment.md`
- Evidence & Result Record: `docs/work-units/WU-260606-002/evidence.md`
- Operations Lead: `main`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Decision

- `accept`

## Rationale

The evidence satisfies the Assignment Packet.

The patch removes the Phase 2 ambiguity by:

- adding a repo-local Work Unit lifecycle event formatter for `ASSIGNED`,
  `STARTED`, `BLOCKED`, `RESULT_READY`, and `DECISION`;
- routing the formatter through
  `python3 scripts/openclaw_company_ops.py discord event ...`;
- documenting `cli-direct` versus `discord-bound` execution visibility;
- stating that CLI-direct execution does not create team-channel records and
  must be made visible through source-artifact-backed `#ops-feed` events;
- preserving Discord as visibility-only and mutation-free.

Verification passed for formatter help, text output, JSON output, unsupported
event rejection, Python compilation, existing multi-team smokes, Work Unit
status summary, and diff checks.

## Required Follow-up

- Phase 3.5 hook or publisher automation is not required immediately for this
  patch. Keep the formatter print-only until the activation decision gate or
  until repeated manual lifecycle posting becomes the next observed friction.
- Carry forward one friction observation: direct Team Lead CLI still may not
  return final terminal text even after file/commit output is produced. This is
  not a blocker for this Work Unit because source artifacts and checks were
  audited directly, but it remains relevant before larger delegation.

## Closure Instruction

If accepted:

- Link this decision to the Work Card.
- Link the Evidence & Result Record to the Work Card.
- Close the Work Card only after both links exist.

If not accepted:

- Keep the Work Card open.
- Update the Ops Claim Ledger entry with the next expected responsibility.

## No Fallback Rule

This decision must not be inferred from GitHub labels, dashboard status,
Discord messages, or Team Lead claims.
