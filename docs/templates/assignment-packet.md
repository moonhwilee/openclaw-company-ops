# Assignment Packet

Status: Manual Day-0

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

It is required before delegated Work Unit execution starts. Simple direct
questions or quick lookups do not need an Assignment Packet unless the
Operations Lead explicitly promotes them into a Work Unit. A GitHub Issue, PR
summary, dashboard note, or Discord message cannot replace this packet.

## Identity

- Work Unit id:
- Work Card:
- Operations Lead:
- Assigned Team Lead OpenClaw Agent:
- Created at:
- Updated at:

## Goal

State the single outcome expected from this Work Unit.

## Background

Include only the context needed to execute the Work Unit.

## Scope

What the team lead should do:

-

## Non-goals

What the team lead should not do:

-

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Other constraints:

## Inputs

Links, files, references, or starting state:

-

## Done Criteria

The Work Unit can be considered ready for review when:

-

## Verification Criteria

Evidence or checks required for review:

-

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

Select the mode that matches the delegated Work Unit:

- `goal`: produce or change a durable outcome through an initial plan followed
  by repeated act-or-improve and verify cycles until a valid stop condition is
  met.
- `verify`: review existing output or evidence without starting new goal work.

Context recovery is not a separate mode. If the Team Lead resumes after long
work, compaction, or subagent result integration, recover the packet, evidence,
gaps, and next action, then continue the selected mode.

```yaml
protocol_capsule:
  mode: <goal|verify>
  support: []
  loop: <plan -> repeat(act_or_improve -> verify) until stop_only_on, only for goal>
  stop_only_on:
    - done_criteria_passed_with_evidence
    - explicit_blocker
    - safety_or_budget_limit
    - operations_lead_or_user_pause
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_selected_mode
```

For `goal` mode, do not stop after one failed verification. Plan once, then
repeat implementation or improvement and verification until a `stop_only_on`
condition is true.

Planning is required for `goal`, but it should be proportional. Small Work
Units can use a concise 1-3 bullet plan; risky or multi-step Work Units need a
fuller plan.

## Expected Outputs

- Evidence & Result Record:
- PR or artifact:
- Decision-ready summary:

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.
- Recommended next action.

The Team Lead report is input for Operations Lead review. It should be concise
enough to support one Operations Lead composition step for both the owner-facing
`#ops-feed` result card and the detailed `#team-*` review trail. Do not ask for
or create a separate LLM summarization call just for visibility.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.

If this packet lacks done criteria, verification criteria, or a Protocol
Capsule for delegated multi-step work, report `blocked` before starting a goal
loop.
