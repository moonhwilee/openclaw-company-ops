# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260607-003`
- Title: Verify Company Ops operating path
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/22
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Goal

Verify whether the Company Ops real operating path works as intended for a
short owner request that is expanded by the Operations Lead into a source-backed
verify-only Work Unit.

## Background

The owner approved this live verify-mode test after confirming the desired UX:
the owner should be able to make a short request, then the Operations Lead
should restore context, confirm the execution scope, create the Work Unit and
Assignment Packet, route it to the Team Lead, publish Discord visibility, sync
the GitHub Project dashboard, review the result, and leave accepted work visible
for owner review.

This Work Unit must verify the operating path. It is not a request to implement
new automation.

## Scope

What the team lead should do:

- Inspect the relevant Company Ops docs, scripts, and current artifacts.
- Verify the requested path against the criteria below.
- Map evidence criterion by criterion.
- Explicitly judge whether the path is working as intended, partially working,
  or not working.
- Report any gaps as `revise` recommendations, not as new implementation work.

## Non-goals

What the team lead should not do:

- Do not edit files.
- Do not create, update, close, or archive GitHub issues or Project items.
- Do not send Discord messages.
- Do not run `project-sync`, `discord publish-card`, or other mutation commands.
- Do not start a goal-mode implementation loop.
- Do not restart OpenClaw, Gateway, or any external service.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Verify-only means read, inspect, and judge. The Operations Lead owns all
  visibility, dashboard, and source artifact mutations for this test.

## Inputs

Links, files, references, or starting state:

- Owner request: `Company Ops 실전 경로를 Verify 모드로 검증하고 싶어.`
- Operations Lead confirmation was sent before execution and approved by owner.
- Work Card: `https://github.com/moonhwilee/openclaw-company-ops/issues/22`
- `README.md`
- `docs/operations-manual.md`
- `docs/discord-event-visibility.md`
- `docs/company-dashboard-timing.md`
- `docs/post-setup-plan.md`
- `docs/protocols/README.md`
- `docs/protocols/verify.md`
- `docs/templates/assignment-packet.md`
- `scripts/openclaw_company_ops.py`
- `scripts/discord_ops.py`
- `scripts/project_sync.py`
- `docs/examples/manual-dry-run/WU-260607-003/assignment.md`
- Prior comparable smoke: `docs/examples/manual-dry-run/WU-260607-002/`

## Done Criteria

The Work Unit can be considered ready for review when:

- The Team Lead result states whether the short-request-to-verify workflow is
  operating as intended.
- The result distinguishes Team Lead responsibilities from Operations Lead
  responsibilities.
- The result confirms whether `verify` mode prevented new implementation work.
- The result includes a criterion-by-criterion evidence map.
- Any gap is clearly marked as a risk or revise item.

## Verification Criteria

Evidence or checks required for review:

- Owner request was short, and Operations Lead expanded it into a detailed Work
  Unit only after confirmation.
- The Assignment Packet carries `protocol_capsule.mode: verify`.
- The Team Lead did not mutate repo, GitHub, Project, or Discord surfaces.
- Discord remains visibility-only and is not treated as command router or source
  of truth.
- GitHub Project remains a source-backed mirror, not the completion authority.
- `Result Ready -> Accepted -> owner review -> archive/close` is preserved.
- The final recommendation is supported by concrete file paths, commands, or
  existing artifacts.

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

```yaml
protocol_capsule:
  mode: verify
  support: []
  goal_work_started: no
  loop: none_for_verify
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

- Evidence & Result Record: Team Lead response captured by Operations Lead in
  `docs/examples/manual-dry-run/WU-260607-003/evidence.md`
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
