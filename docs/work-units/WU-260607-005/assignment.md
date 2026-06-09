# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260607-005`
- Title: Verify Phase 5.3 dashboard sync implementation
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/24
- Operations Lead: `geumbi`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Mode: `verify`
- Created at: `2026-06-06T20:27:30Z`
- Updated at: `2026-06-06T20:27:30Z`

## Owner Request

phase5.3 구현에 대해서 verify 진행해줘.

## Goal

Verify whether the Phase 5.3 Dashboard Gate implementation satisfies the accepted Company Ops procedure and implementation principles.

## Scope

- Inspect Phase 5.3 source docs and current implementation state from the active repo
- Verify project-sync dry-run, field-map/apply/reconcile behavior, lifecycle one-shot sync boundaries, and dashboard mirror principles
- Check deterministic evidence only; do not rely on prior conversation memory as proof
- Report accept/revise/hold/reject recommendation with criterion-by-criterion evidence

## Non-goals

- Do not expand beyond this initial handoff scope.
- Do not treat Discord, GitHub Project, comments, or labels as source truth.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.

## Inputs

- docs/post-setup-plan.md#phase-53-dashboard-gate
- docs/company-dashboard-timing.md#current-state-for-this-repo
- scripts/project_sync.py
- scripts/discord_ops.py
- scripts/company_ops_smoke.py

## Done Criteria

- Phase 5.3 implementation criteria are mapped to concrete source files, commands, and test evidence
- No legacy path, fallback source of truth, reverse import, hidden orchestrator, or unintended source mutation is found
- Relevant deterministic checks pass or each failure is identified with a concrete missing artifact or blocker
- Team Lead verify result recommends accept, revise, hold, or reject with evidence

## Verification Criteria

- Read docs/post-setup-plan.md Phase 5.3 and docs/company-dashboard-timing.md current-state sections
- Inspect scripts/project_sync.py and lifecycle sync integration points without assuming from memory
- Run python3 -m py_compile scripts/*.py .codex/hooks/*.py
- Run python3 scripts/company_ops_smoke.py multi-team
- Run python3 scripts/openclaw_company_ops.py smoke multi-team
- Run project-sync dry-run for an existing Work Unit with the configured field-map and confirm llm_calls=0 and project_mutation=false
- Run a non-mutating project-sync/apply or idempotency-safe readback check only if it does not create misleading operational state
- Check git status and identify any unrelated local side effects

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

- Evidence & Result Record: `docs/work-units/WU-260607-005/evidence.md`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

Criterion-by-criterion verify mapping, commands run, pass/fail/unknown items, principle audit, recommendation.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
