# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260609-906`
- Title: Phase 5.8.5 one-round goal no-bypass gate
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/35
- Operations Lead: `gbee`
- Assigned Team Lead OpenClaw Agent: `revenue`
- Mode: `goal`
- Created at: `2026-06-09T03:16:00Z`
- Updated at: `2026-06-09T03:16:00Z`

## Owner Request

Create a small one-round operator-facing checklist for executing duplicate-guarded Phase 5.8.5 without bypasses.

## Goal

Produce a short checklist in the Work Unit evidence artifact that an Operations Lead can use while running the 5.8.5 live gate.

## Assumptions And Open Questions

- Initial handoff may start from these facts, but scope, criteria, cost, risk,
  or authority changes require an Operations Lead amendment.

## Change Log

- Initial handoff: `2026-06-09T03:16:00Z`
- Amendments:

## Scope

- Use the current docs as source input
- Produce the checklist only inside this Work Unit evidence/result artifact
- Do not modify repo docs or source code

## Non-goals

- Do not expand beyond this initial handoff scope.
- Do not treat Discord, GitHub Project, comments, or labels as source truth.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.

## Inputs

- docs/phase-5.8-stabilization-gate.md
- docs/operations-manual.md

## Done Criteria

- Evidence includes a concise one-round checklist for Phase 5.8.5 live execution
- Checklist covers start, fresh dispatch, result-ready reviewer wake, guarded closeout commit-request, partial resume, and negative fail-closed checks
- Team Lead submits result-ready through the source-backed command

## Verification Criteria

- git status was checked before result-ready
- Checklist maps to docs/phase-5.8-stabilization-gate.md
- No manual STARTED/proof/source-truth insertion was used

## Protocol Capsule

```yaml
protocol_capsule:
  mode: goal
  support: []
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  subagent_budget: none
  subagent_budget_reason: One-round goal scoped to a Work Unit evidence artifact.
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

## Expected Outputs

- Evidence & Result Record: `docs/examples/manual-dry-run/WU-260609-906/evidence.md`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

Return a concise checklist, verification summary, changed artifact list, blocker if any, and next action.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
