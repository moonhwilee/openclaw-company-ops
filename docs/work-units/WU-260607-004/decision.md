# Operations Lead Decision

Status: Revise

The Operations Lead decision records whether the submitted result satisfies the
Assignment Packet and evidence requirements.

## Identity

- Decision ref: `DECISION-WU-260607-004`
- Work Unit id: `WU-260607-004`
- Title: Verify Company Ops live operating path after Progress updates
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/23
- Assignment Packet: `docs/work-units/WU-260607-004/assignment.md`
- Evidence & Result Record: `docs/work-units/WU-260607-004/evidence.md`
- Operations Lead: `geumbi`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Decision

`revise`

## Rationale

Revise.

The current Company Ops live verify path works through the core surfaces:

- Work Card and source artifacts were created.
- Claim ledger and `progress.jsonl` were source-backed.
- Assignment visibility used the new serial publish path and read back in the
  correct order.
- Project sync ran without LLM calls and mirrored `Status=In Progress` and
  `Progress=2/3 · verify operating path · round 1`.
- Team Lead `build-lab` ran verify-only and returned evidence mapping.

However, the path should not be accepted yet. The Team Lead correctly flagged
that the Work Unit was not decision-ready at the time of verification. After
Operations Lead review, a deeper workflow gap remains: current proof validation
requires exactly one owner closeout, but the card model has no valid
owner-facing closeout for `REVISE`. `ops-feed COMPLETED` requires
`ACCEPTED`; `ops-feed BLOCKED` requires `BLOCKED_DETAIL`. Treating a revise
decision as completed or blocked would be a semantic workaround, so it is not
acceptable under no-legacy/no-fallback principles.

## Required Follow-up

- Keep Work Card `#23` open.
- Do not archive the Project item.
- Add a formal owner-facing revise/needs-revision closeout path, or adjust
  proof validation so `REVISE` can close the team-detail trail without forcing
  an invalid owner closeout.
- Rerun this verify path after the revise closeout behavior is implemented.

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
