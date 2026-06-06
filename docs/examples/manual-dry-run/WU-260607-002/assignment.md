# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260607-002`
- Title: Full Company Ops integration smoke
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/21
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Goal

Run a bounded end-to-end Company Ops integration smoke that exercises the
actual Team Lead request path plus live Discord visibility and GitHub Project
dashboard sync.

## Background

The owner has already configured the GitHub Project table view. The remaining
question is whether the whole Company Ops structure works together when the
Operations Lead sends a real Team Lead request, rather than only testing the
GitHub Project sync in isolation.

## Scope

What the team lead should do:

- Inspect the current Company Ops docs and scripts relevant to Team Lead
  delegation, Discord visibility, and Project dashboard sync.
- Judge whether the implemented structure is ready for a live integrated smoke.
- Report the result in a concise Team Lead format: result summary, evidence,
  checks performed, remaining risks, blocker if any, and next action.

## Non-goals

What the team lead should not do:

- Do not edit files.
- Do not create, close, or update GitHub issues or Project items.
- Do not send Discord messages.
- Do not mutate claim, evidence, decision, dashboard, or Work Unit state.
- Do not restart OpenClaw, Gateway, or any external service.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Treat this as a verification Work Unit, not a product implementation task.
- Keep the result under the Discord generation budget.

## Inputs

Links, files, references, or starting state:

- `README.md`
- `docs/operations-manual.md`
- `docs/discord-event-visibility.md`
- `docs/company-dashboard-timing.md`
- `docs/post-setup-plan.md`
- `scripts/discord_ops.py`
- `scripts/project_sync.py`
- `scripts/openclaw_company_ops.py`

## Done Criteria

The Work Unit can be considered ready for review when:

- The Team Lead result explicitly answers whether the whole structure can be
  tested end to end.
- The Team Lead result distinguishes implemented proof from remaining caveats.
- The result includes the files or commands inspected.

## Verification Criteria

Evidence or checks required for review:

- Team Lead CLI response or session readback.
- Operations Lead local smoke checks.
- Discord live publish/readback proof.
- GitHub Project sync readback.

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

```yaml
protocol_capsule:
  mode: verify
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
- PR or artifact: none expected from Team Lead
- Decision-ready summary: required

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
