# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260608-003`
- Title: Add first-time user positioning note for Public v1
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/28
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `market`
- Mode: `goal`
- Created at: `2026-06-07T19:33:22Z`
- Updated at: `2026-06-07T19:33:22Z`

## Owner Request

Add a short positioning note for first-time users explaining what Company Ops Public v1 does, what it does not do automatically, and why source artifacts matter. Keep scope to a small documentation change.

## Goal

Draft and apply a concise first-time user positioning note in the most appropriate repo documentation location, likely README.md, without expanding implementation scope.

## Assumptions And Open Questions

- Initial handoff may start from these facts, but scope, criteria, cost, risk,
  or authority changes require an Operations Lead amendment.

## Change Log

- Initial handoff: `2026-06-07T19:33:22Z`
- Amendments:

## Scope

- Inspect README.md and nearby docs to find the least disruptive location for a first-time user positioning note.
- Add or update a small documentation section explaining what Company Ops helps coordinate.
- State what Company Ops does not automatically do, including no hidden orchestration, automatic completion, recovery, or external mutation.
- Explain why source artifacts matter as the recoverable state and source of truth.
- Keep changes narrow to documentation; no code, script, template, or workflow behavior changes.

## Non-goals

- Do not expand beyond this initial handoff scope.
- Do not treat Discord, GitHub Project, comments, or labels as source truth.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.

## Inputs

- README.md
- docs/operations-manual.md
- docs/setup-guide.md
- docs/post-setup-plan.md

## Done Criteria

- A short positioning note exists in an appropriate documentation file.
- The note is understandable to a first-time Public v1 user.
- The note covers what the tool does, what it does not automate, and why source artifacts matter.
- The change stays small and documentation-only.
- The Team Lead returns a 1-round goal result with changed files, verification, risks, and recommendation.

## Verification Criteria

- The note does not claim Phase 6 implementation already exists.
- The note does not soften no-go rules around automatic recovery, completion, hidden orchestration, or source-of-truth boundaries.
- The note fits the surrounding README/docs style.
- git diff --check passes after the documentation change.

## Protocol Capsule

```yaml
protocol_capsule:
  mode: goal
  support: []
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_selected_mode
```

## Expected Outputs

- Evidence & Result Record: `docs/work-units/WU-260608-003/evidence.md`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

Return changed file path, summary, verification commands, remaining risks, and recommended decision.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
