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
- Request route: <detached-wu>
- Execution route: <cli-direct|cli-delivered|discord-bound>
- Main session behavior: detached after handoff for sizeable `goal` or `verify`
  work.
- Created at:
- Updated at:

## Goal

State the single outcome expected from this Work Unit.

## Background

Include only the context needed to execute the Work Unit.

## Assumptions And Open Questions

List assumptions that are safe to start with and questions that may require an
Operations Lead amendment if they change scope, criteria, cost, risk, or
authority.

-

## Change Log

Record source-backed changes after the initial handoff. Do not erase the
original handoff when execution discovers a better plan or a new issue.

- Initial handoff:
- Amendments:

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

Shared Company Ops references available to the Team Lead:

-

## Done Criteria

The Work Unit can be considered ready for review when:

-

## Verification Criteria

Evidence or checks required for review:

-

## Mutation Authority

This block is structured authority, not prose. Company Ops-owned commands and
handoff validators use it to fail closed when mode and mutation scope conflict.

- Mutation allowed: `<true|false>`
- Allowed paths: `<none|repo-relative paths>`
- Allowed surfaces: `<none|source|project|discord|git|external>`
- External mutation allowed: `<true|false>`
- Commit/push allowed: `<true|false>`

Mode boundary:

- `verify` is read-only with respect to the candidate output being checked.
- `verify` may write verification records and auxiliary proof artifacts inside
  its own Work Unit artifact subtree, `docs/work-units/<work-unit-id>/`, when
  those paths are explicitly allowed. Direct writes to core Work Unit control
  artifacts such as assignment, claim, decision, progress, proof, dispatch,
  card, or closeout files are not allowed.
- `verify` may use official Company Ops lifecycle commands for source-backed
  `CHECKPOINT` or `RESULT_READY` proof after evidence is written; those commands
  may update lifecycle visibility, but they are not permission to change the
  candidate output or make closeout decisions.
- `verify` must not mutate candidate outputs, git, GitHub Project final status,
  Discord closeout messages, or external systems outside the official Work Unit
  lifecycle commands.

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
  mutation_authority:
    mutation_allowed: <true|false>
    allowed_paths: []
    allowed_surfaces: []
    external_mutation_allowed: <true|false>
    commit_push_allowed: <true|false>
  support: []
  loop: <plan -> repeat(act_or_improve -> verify) until stop_only_on, only for goal>
  stop_only_on:
    - done_criteria_passed_with_evidence
    - explicit_blocker
    - safety_or_budget_limit
    - operations_lead_or_user_pause
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  subagent_budget: <none|2|3|5>
  subagent_budget_reason: <team_lead_direct|simple_delegated|normal|complex_high_risk>
  subagent_budget_enforcement: prompt_and_packet_contract_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: revise_means_operations_lead_replan_then_reenter_selected_mode
```

Subagent budget policy:

- `none`: Team Lead handles the Work Unit directly.
- `2`: simple delegated work.
- `3`: normal goal/verify work.
- `5`: complex, high-risk, or broad verification work.
- More than `5` requires explicit Operations Lead or owner approval.

This budget is an Assignment Packet and package-prompt contract. It is not a
runtime hook, tool policy, or hard enforcement layer.

Before invoking `work-unit result-ready`, update the Evidence & Result Record to
`Status: Result Ready`. A draft evidence file must remain in repair-needed
state and should not publish a `RESULT_READY` proof.

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

If the Work Unit discovers issues, route them in the Evidence & Result Record
with severity and one of `direct_patch`, `docs_or_preflight`, `owner_decision`,
or `observe`. Use `owner_decision` when the finding changes authority,
automation scope, cost, destructive behavior, or user-facing policy.

Cross-Work-Unit or parallelism criteria are Operations Lead-owned unless the
Assignment Packet names the exact peer Work Unit ids and source refs the Team
Lead may inspect. The Team Lead must not read or mutate unrelated Work Unit
artifacts just to prove overlap.

Returning this report does not complete the Work Unit. It moves the Work Unit
to result-ready review. The Operations Lead must reread the source artifacts,
verify the evidence, and record `accept`, `revise`, or `blocked`.

Discord generation budget:

- Keep the Discord-facing result text within 1,600 characters.
- Put detailed logs, diffs, and long findings in the Evidence & Result Record or
  another source artifact.
- If the result needs more room, report the artifact path plus a short decision
  summary instead of pasting the full detail into Discord.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.

If this packet lacks done criteria, verification criteria, or a Protocol
Capsule for delegated multi-step work, report `blocked` before starting a goal
loop.
