# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260608-004`
- Title: Document result-ready inbox closeout checklist
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/29
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `revenue`
- Mode: `goal`
- Created at: `2026-06-07T19:43:56Z`
- Updated at: `2026-06-07T19:43:56Z`

## Owner Request

Document a simple 5-8 item Operations Lead checklist for processing result-ready inbox items, emphasizing no automatic completion, no Project/Discord reverse-import, and no decision overwrite. Keep scope to a small documentation change.

## Goal

Add a concise operating checklist for Operations Lead result-ready inbox processing in the most appropriate docs location without changing code or workflow behavior.

## Assumptions And Open Questions

- Initial handoff may start from these facts, but scope, criteria, cost, risk,
  or authority changes require an Operations Lead amendment.

## Change Log

- Initial handoff: `2026-06-07T19:43:56Z`
- Amendments:

## Scope

- Inspect docs/operations-manual.md result-ready inbox and closeout sections.
- Add or update a small documentation section with 5-8 checklist items.
- Checklist must include no automatic completion, no Project/Discord reverse-import, and no decision overwrite.
- Keep change documentation-only and small; no code, template, script, workflow behavior, GitHub Project, or Discord changes except Company Ops operating artifacts.

## Non-goals

- Do not expand beyond this initial handoff scope.
- Do not treat Discord, GitHub Project, comments, or labels as source truth.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.

## Inputs

- docs/operations-manual.md
- docs/templates/operations-lead-decision.md
- docs/templates/assignment-packet.md
- docs/templates/evidence-result-record.md

## Done Criteria

- A 5-8 item checklist exists in an appropriate documentation file.
- The checklist is usable by Operations Lead while processing result-ready inbox items.
- The checklist explicitly covers automatic completion, Project/Discord reverse-import, and decision overwrite prevention.
- The change is documentation-only and small.
- The Team Lead returns a 1-round goal result with changed files, verification, risks, and recommendation.

## Verification Criteria

- The checklist aligns with existing Result Ready Inbox Rule and Decision Rules.
- The checklist does not introduce new automation, source of truth, or authority model.
- git diff --check passes.
- Operations Lead can accept/revise based on the diff and source refs.

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

- Evidence & Result Record: `docs/examples/manual-dry-run/WU-260608-004/evidence.md`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

Return changed file path, summary, verification commands, remaining risks, and recommended decision.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
