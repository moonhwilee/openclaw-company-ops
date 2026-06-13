# Evidence & Result Record

Status: Draft

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id:
- Work Card:
- Assignment Packet:
- Team Lead OpenClaw Agent:
- Submitted at:

## Result Summary

Summarize what was completed.

## Evidence

Link only real artifacts or checks that exist.

- PR:
- Test output:
- Reports:
- Sources:
- Screenshots:
- Generated artifacts:
- Review notes:

## Findings And Follow-up Routing

For each meaningful finding, include severity and routing so the Operations
Lead can decide without another broad summarization pass.

- Finding:
  - Severity: `P0|P1|P2|P3`
  - Routing: `direct_patch|docs_or_preflight|owner_decision|observe`
  - Evidence:
  - Recommended next action:

## Verification Performed

-

## Goal Convergence Receipt

For goal-mode Work Units, link the machine-checkable receipt that closes every
verification debt before result-ready:

- Receipt: `goal-convergence-receipt.json`
- Work Unit id:
- Assignment criteria count:
- Unresolved debt count:
- Criterion ids: use the exact generated Assignment Packet ids (`done-1`,
  `verification-1`, etc.) with no missing or extra ids.

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion:
  - Status:
  - Evidence:

## Remaining Risks

-

## Open Questions

-

## Team Lead Recommendation

Recommended decision:

- `<accept|revise|blocked>`

Use exactly one recommendation. Do not leave multiple choice options in the
final Evidence & Result Record.

Rationale:

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
