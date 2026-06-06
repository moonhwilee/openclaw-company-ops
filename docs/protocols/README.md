# Team Lead Protocols

Status: Manual Day-0

These protocol files are canonical references for Team Lead execution. They are
not a runtime, command router, database, or hidden runtime.

The Operations Lead uses these files to compose a short Protocol Capsule inside
each Assignment Packet. The Team Lead executes the capsule packet-first instead
of searching protocol files and interpreting the Work Unit from scratch.

These protocols apply only to delegated Work Units. Simple direct questions,
quick lookups, and conversational requests should not be promoted into Work Unit
protocol unless the Operations Lead explicitly assigns them that way.

## Detached Work Unit Requirement

`goal` and standalone `verify` are delegated Work Unit protocols for sizeable
work. When either mode needs a Team Lead, subagents, code changes, external
mutation, live visibility, or multi-step verification, the Operations Lead must
handoff a detached Work Unit instead of waiting in the main session.

The main session may continue serving the owner after source-backed handoff.
Team Lead results return through the Work Unit artifacts, claim state, and
proof/progress trail. The Operations Lead later rereads those sources and makes
the decision. The Team Lead must not assume that returning a result directly to
the current chat completes the Work Unit.

## Protocol Set

- [goal](goal.md): complete the Work Unit through an initial plan followed by
  repeated act-or-improve and verify cycles until a valid stop condition is met.
- [verify](verify.md): compare outputs and evidence against done and
  verification criteria.

Context recovery is a support procedure, not a separate mode. After long
execution, compaction, resumed sessions, or subagent result integration, recover
the packet, evidence, gaps, and next action, then continue `goal` or `verify`.
See [context recovery](context-recovery.md).

## Packet-First Rule

If a delegated Work Unit includes an Assignment Packet, the packet is the source
of truth.

If a delegated Work Unit lacks an Assignment Packet, done criteria, or
verification criteria, the Team Lead must report `blocked` instead of starting a
goal loop from request prose.

Simple direct questions do not require Work Unit protocol.

Packet-first does not mean goal-always. The active Protocol Capsule selects
`goal` or `verify`; the Team Lead must not start goal work when the packet asks
only for verification or a simple direct answer.

## Protocol Capsule

The Protocol Capsule is the compact execution instruction embedded in an
Assignment Packet. It should be short enough to fit in the active context and
strict enough to prevent the Team Lead from inventing completion criteria.

Goal-mode example:

```yaml
protocol_capsule:
  mode: goal
  support: [verify]
  loop: plan -> repeat(act_or_improve -> verify) until stop_only_on
  stop_only_on:
    - done_criteria_passed_with_evidence
    - explicit_blocker
    - safety_or_budget_limit
    - operations_lead_or_user_pause
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_goal_loop
```

The capsule cannot replace the Assignment Packet. It only tells the Team Lead
how to execute the packet.

`goal` mode must not stop after a single failed verification. The Team Lead
plans once, then repeats implementation or improvement and verification until
one `stop_only_on` condition is true.
