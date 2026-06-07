# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260608-001`
- Title: Verify Phase 6 doctor and preflight documentation boundaries
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/26
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Mode: `verify`
- Created at: `2026-06-07T19:15:59Z`
- Updated at: `2026-06-07T19:15:59Z`

## Owner Request

Verify that the Phase 6 doctor/preflight documentation consistently describes the helper as read-only, foreground, and no-mutation. Do not modify code.

## Goal

Verify whether README.md, docs/operations-manual.md, and docs/setup-guide.md consistently state the Phase 6 doctor/preflight boundary as read-only, foreground, and non-mutating.

## Assumptions And Open Questions

- Initial handoff may start from these facts, but scope, criteria, cost, risk,
  or authority changes require an Operations Lead amendment.

## Change Log

- Initial handoff: `2026-06-07T19:15:59Z`
- Amendments:

## Scope

- Inspect README.md for Phase 6 doctor/preflight scope and no-go claims.
- Inspect docs/operations-manual.md for read-only, foreground, no-mutation boundary language.
- Inspect docs/setup-guide.md for setup/preflight expectations and no auto-create/no grant/no mutation language.
- Compare the three documents for contradictions, missing boundary language, or overclaims.

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
- docs/protocols/verify.md
- docs/templates/assignment-packet.md

## Done Criteria

- The Team Lead maps the requested doctor/preflight boundary to concrete text in all three target documents.
- The Team Lead identifies any inconsistency, missing statement, or overclaim, or states that none were found.
- No source code or documentation is modified by the Team Lead during this verify Work Unit.
- The Team Lead returns a decision-ready verify summary with evidence references.

## Verification Criteria

- Evidence cites README.md, docs/operations-manual.md, and docs/setup-guide.md.
- Evidence explicitly checks read-only, foreground, and no-mutation boundaries.
- Evidence distinguishes implemented behavior from planned Phase 6 behavior.
- Operations Lead can independently reread the cited source lines before closeout.

## Protocol Capsule

```yaml
protocol_capsule:
  mode: verify
  support: []
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_selected_mode
```

## Expected Outputs

- Evidence & Result Record: `docs/examples/manual-dry-run/WU-260608-001/evidence.md`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

Return result summary, cited source refs, checks performed, inconsistencies or none found, remaining risks, and recommended next action.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
