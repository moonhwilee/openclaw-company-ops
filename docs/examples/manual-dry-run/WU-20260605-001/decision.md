# Operations Lead Decision

Status: Day-0 Smoke Artifact + Live Build-Lab Read-Only Run

Supersession note: this decision records an earlier smoke pass that treated
context recovery as a third Protocol Capsule mode. Current active docs use only
`goal` and `verify`; context recovery is now a support procedure.

## Identity

- Decision ref: `DECISION-WU-20260605-001`
- Work Unit id: `WU-20260605-001`
- Work Card: manual smoke artifact
- Assignment Packet: `docs/examples/manual-dry-run/WU-20260605-001/assignment.md`
- Evidence & Result Record: `docs/examples/manual-dry-run/WU-20260605-001/evidence.md`
- Decided at: `2026-06-05`

## Decision

- `accept`

## Rationale

The documentation smoke Work Unit satisfied the Assignment Packet at that time.
It added canonical `goal`, `verify`, and a superseded third context-recovery
mode reference, embedded the Protocol Capsule convention in the Assignment
Packet template, updated the Team Playbook with packet-first execution rules,
recorded a manual smoke artifact, and passed a live read-only `build-lab` smoke
run.

The live smoke produced the expected two-step behavior:

- Initial relative-path packet handoff failed and `build-lab` reported
  `blocked` instead of inventing a goal loop.
- Revised absolute-path packet handoff passed; `build-lab` restated the packet,
  executed `goal` with verify and context-recovery support, mapped criteria to
  evidence, and recommended `accept`.

After the Assignment Packet template was changed away from a default
`mode: goal`, follow-up smoke turns confirmed the intended path:

- A direct non-Work-Unit question returned `mode=direct`.
- A verify-only packet returned `mode=verify` and `goal_work_started=no`.
- A goal packet returned `mode=goal` and `goal_work_started=yes`.
- A superseded context-recovery-mode packet returned the recovery mode and
  `goal_work_started=no`.

## Required Follow-up

- Use the same packet-first contract on the next real product implementation
  Work Unit before beginning any broader CLI/runtime work.

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
