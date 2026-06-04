# goal Protocol

Status: Manual Day-0

`goal` is the Team Lead execution protocol for completing a delegated Work Unit.

It is not a separate runtime. It is a compact operating loop that the Team Lead
follows when the Assignment Packet includes a goal-mode Protocol Capsule.

## Inputs

- Assignment Packet.
- Protocol Capsule.
- Work Card.
- Ops Claim Ledger entry, when available.
- Existing evidence or artifacts, when available.

## Loop

1. Restate the Work Unit goal, scope, non-goals, done criteria, and verification
   criteria from the Assignment Packet.
2. Create an Execution Plan. The Team Lead may plan work but must not rewrite
   the Assignment Packet.
3. Act on the plan. Use subagents only under direct Team Lead control.
4. Run `verify` against the outputs and evidence.
5. If verification fails or is unknown, identify the concrete gap and improve
   the work.
6. Reverify after each improvement.
7. Submit an Evidence & Result Record only when done criteria pass with
   evidence, or report a true blocker.

## Stop Conditions

The Team Lead may stop only on:

- Done criteria passed with evidence.
- Explicit blocker requiring input, access, or a decision.
- Safety or budget limit.
- Operations Lead or user pause.

## Non-Completion

The following are not completion:

- A status claim.
- A subagent claim.
- A PR summary without evidence mapping.
- A dashboard, Discord, or GitHub label status.
- A first attempt that has not been verified against the Assignment Packet.

## Ownership

The Team Lead owns the Work Unit until the Operations Lead accepts the submitted
evidence. Subagents may perform partial work, but they must not receive Work
Unit ownership.
