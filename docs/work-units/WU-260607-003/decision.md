# Operations Lead Decision

Status: Revise

The Operations Lead decision records whether the submitted result satisfies the
Assignment Packet and evidence requirements.

## Identity

- Decision ref: `DECISION-WU-260607-003`
- Work Unit id: `WU-260607-003`
- Title: Verify Company Ops operating path
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/22
- Assignment Packet: `docs/work-units/WU-260607-003/assignment.md`
- Evidence & Result Record: `docs/work-units/WU-260607-003/evidence.md`
- Operations Lead: `main`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Decision

Choose one:

- `accept`
- `revise`
- `hold`
- `reject`

## Rationale

Revise.

The Work Unit verifies that the Company Ops real operating path mostly works as
expected:

- The owner made a short natural-language request.
- Operations Lead restored context, confirmed the execution scope, and created
  Work Card `#22`.
- Source artifacts were generated and filled before Team Lead execution.
- Discord `ASSIGNED`, `ASSIGNED_DETAIL`, `STARTED`, and `RESULT_READY` cards
  were published and read back.
- GitHub Project mirrored source-backed state transitions from `Assigned` to
  `In Progress` to `Result Ready`.
- The real `build-lab` Team Lead was invoked through OpenClaw CLI in
  verify-only mode.
- The Team Lead did not start implementation and did not mutate repo, GitHub,
  Project, or Discord surfaces.
- The Team Lead returned a criterion-by-criterion report and correctly flagged
  that Operations Lead post-result steps were still pending at report time.

However, the final Discord proof validator failed because the first two
visibility cards were published in parallel. The team-detail `ASSIGNED_DETAIL`
message read back 12ms before the owner-facing ops-feed `ASSIGNED` message.
That violates the Company Ops visibility contract: the owner-visible request
must precede the team handoff.

The Team Lead's `revise` recommendation was therefore appropriate, not merely
conservative. The path is structurally sound, but the live publisher behavior
needs a small operational correction: multi-card transitions must be serialized
when Project sync and proof validation are enabled.

## Required Follow-up

- Keep Work Card `#22` open and Project item visible for owner review.
- Do not archive immediately.
- Serialize multi-card `discord publish-card` calls when
  `--project-sync-field-map` is enabled.
- Add or use a wrapper for assignment transitions so ops-feed `ASSIGNED` is
  published and validated before team-detail `ASSIGNED_DETAIL`.

## Closure Instruction

If accepted:

- Link this decision to the Work Card.
- Link the Evidence & Result Record to the Work Card.
- Close the Work Card only after both links exist and the owner has confirmed
  review or cleanup.

If not accepted:

- Keep the Work Card open.
- Update the Ops Claim Ledger entry with the next expected responsibility.

## No Fallback Rule

This decision must not be inferred from GitHub labels, dashboard status,
Discord messages, or Team Lead claims.
