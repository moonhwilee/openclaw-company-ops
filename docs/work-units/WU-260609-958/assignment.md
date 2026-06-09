# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260609-958`
- Title: Phase 5.8.6 delegated closeout live gate
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/37
- Operations Lead: `gbee`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Mode: `verify`
- Created at: `2026-06-09T11:59:46Z`
- Updated at: `2026-06-09T11:59:46Z`

## Owner Request

Run a small live external gate for Phase 5.8.6 delegated closeout after no-legacy rename.

## Goal

Verify that RESULT_READY wakes a fresh main closeout delegate and that guarded closeout publishes accept/revise/blocked without returning routine final write work to the foreground main OL.

## Assumptions And Open Questions

- Initial handoff may start from these facts, but scope, criteria, cost, risk,
  or authority changes require an Operations Lead amendment.

## Change Log

- Initial handoff: `2026-06-09T11:59:46Z`
- Amendments:

## Scope

- Read README.md, docs/operations-manual.md, docs/phase-5.8-stabilization-gate.md, scripts/work_unit_artifacts.py, and scripts/openclaw_closeout_delegate_sessions_send.py.
- Confirm active code and docs use canonical closeout delegate/delegate-wake naming without reviewer fallback on the active path.
- Confirm the delegated closeout authority path is fresh main OL delegate plus guarded closeout only.
- Do not edit repository files.

## Non-goals

- Do not expand beyond this initial handoff scope.
- Do not treat Discord, GitHub Project, comments, or labels as source truth.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.

## Inputs

- See Work Card and source artifacts.

## Done Criteria

- Evidence states whether active code/docs use canonical closeout delegate naming.
- Evidence confirms the delegated closeout authority path is fresh main OL delegate plus guarded closeout.
- Evidence confirms no files were edited by the Team Lead.
- Team Lead submits RESULT_READY only through the source-backed result-ready command.

## Verification Criteria

- Cites current HEAD 5f3a20f and clean status, or reports any mismatch.
- Mentions the latest controlled smoke evidence or identifies blockers.
- Lists any red-line/manual_required condition; otherwise says none.

## Protocol Capsule

```yaml
protocol_capsule:
  mode: verify
  support: []
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  subagent_budget: 3
  subagent_budget_reason: normal
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

- Evidence & Result Record: `docs/work-units/WU-260609-958/evidence.md`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

Result summary, evidence links, checks performed, remaining risks, blockers.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
