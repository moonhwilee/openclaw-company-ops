# Assignment Packet

Status: Product Work Unit Assignment

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260607-001`
- Title: Dashboard sync sample request
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/20
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Goal

Run one real sample Company Ops dashboard request through the Work Card,
source artifact, and GitHub Project sync path.

## Background

Project sync was enabled for the user-level `Company Ops Dashboard`, but the
first smoke used an existing historical Work Unit. This sample proves a fresh
request can be represented as a new Work Card, source artifacts, and Project
dashboard item.

## Scope

What the team lead should do:

- Confirm this Work Unit has a real GitHub Work Card.
- Confirm the Work Unit source artifacts exist in this repository.
- Run `project-sync dry-run` with the configured Project field map.
- Run `project-sync apply` against `Company Ops Dashboard`.
- Read back the Project item and verify Company Ops fields are populated.
- Explain the default GitHub `Status` field versus the dedicated `Ops Status`
  field.

## Non-goals

What the team lead should not do:

- Do not implement a production feature.
- Do not treat the GitHub Project as source of truth.
- Do not reverse-write from Project fields into assignment, claim, evidence,
  or decision artifacts.
- Do not add hidden recovery, reassignment, or completion automation.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Keep the sample clearly marked as a dashboard sync sample.

## Inputs

Links, files, references, or starting state:

- Repository: `/Users/moon/src/openclaw-company-ops`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/20
- Project: https://github.com/users/moonhwilee/projects/1
- Field map:
  `~/.openclaw/state/openclaw-company-ops/project-field-map.json`

## Done Criteria

The Work Unit can be considered ready for review when:

- A fresh Work Card exists.
- The required source artifacts exist under
  `docs/examples/manual-dry-run/WU-260607-001/`.
- `project-sync dry-run` reports mutation-ready with no missing fields.
- `project-sync apply` mutates or confirms the Project item.
- Project readback shows `WU-260607-001`, `Ops Status`, source repository,
  Work Card, evidence, and decision fields.
- The `Status` versus `Ops Status` distinction is explained to the owner.

## Verification Criteria

Evidence or checks required for review:

- `git status --short --branch`
- `project-sync dry-run --work-unit-id WU-260607-001`
- `project-sync apply --work-unit-id WU-260607-001`
- `gh project item-list 1 --owner moonhwilee`
- `git diff --check`

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

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

For `goal` mode, do not stop after one failed verification. Plan once, then
repeat implementation or improvement and verification until a `stop_only_on`
condition is true.

Planning is required for `goal`, but it should be proportional. Small Work
Units can use a concise 1-3 bullet plan; risky or multi-step Work Units need a
fuller plan.

## Expected Outputs

- Evidence & Result Record:
- PR or artifact: source artifacts in `docs/examples/manual-dry-run/WU-260607-001/`
- Decision-ready summary:

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.

Discord generation budget:

- Keep Discord-facing result text within 1,600 characters.
- Put detailed logs, diffs, and long findings in the Evidence & Result Record or
  another source artifact.
- If the result needs more room, report the artifact path plus a short decision
  summary instead of pasting full detail into Discord.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
