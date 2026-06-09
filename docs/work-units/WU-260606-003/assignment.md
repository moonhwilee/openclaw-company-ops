# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260606-003`
- Title: Add execution route to Work Unit status summary
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/19
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Goal

Add read-only execution route visibility to the Work Unit status summary so an
Operations Lead can audit whether a Work Unit used `cli-direct`,
`cli-delivered`, or `discord-bound` from source artifacts.

## Background

Phase 2 and Phase 3 exposed that Team Lead execution can succeed while Discord
team-channel visibility differs by route. The docs now distinguish three
routes:

- `cli-direct`: no Discord team-channel execution record is expected.
- `cli-delivered`: a CLI-triggered run delivered a message to Discord, but this
  is not proof of Discord-bound conversation by itself.
- `discord-bound`: the team channel or thread is the actual execution
  conversation surface.

The current status helper summarizes Work Unit artifacts, but it does not
surface execution route. That makes route regressions too easy to miss during
Operations Lead review.

Phase 4 route validation has already passed for `#team-build-lab`: an
owner-authored Discord inbound message routed to `build-lab`, and build-lab
answered in the same team channel. This Work Unit should therefore run through
that `discord-bound` team-channel path.

## Scope

What the team lead should do:

- Update `scripts/work_unit_status.py` so `status work-unit` derives and
  displays an `execution_route` value from source artifacts.
- Include `execution_route` in JSON status output.
- Keep parsing simple and artifact-backed. Prefer fields or notes such as
  `Execution route`, `Execution Route`, or `Execution route for this Work
  Unit` in `assignment.md`, `claim.md`, `evidence.md`, or `decision.md`.
- Add or update this Work Unit's artifacts so they record that the route is
  `discord-bound`.
- Preserve existing status behavior for older Work Units that do not record a
  route; they should report an unknown/missing route without failing.
- Record evidence that existing Work Units `WU-260606-001` and `WU-260606-002`
  still summarize.

## Non-goals

What the team lead should not do:

- Do not send Discord messages from `scripts/work_unit_status.py`.
- Do not implement a Discord publisher, command router, hook harness, or daemon.
- Do not mutate GitHub, claims, evidence, decisions, or dashboard state from
  status reads.
- Do not make Discord a source of truth.
- Do not change OpenClaw agent/channel routing.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Discord remains visibility-only and source artifacts remain the operating
  record.
- The new route parsing must be conservative. It may read simple markdown
  fields/notes; it should not infer route from arbitrary prose when a field is
  absent.
- Existing text output should remain readable and stable.
- Existing JSON consumers should remain compatible; adding a top-level
  `execution_route` object is acceptable.

## Inputs

Links, files, references, or starting state:

- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/19
- Assignment Packet:
  `docs/work-units/WU-260606-003/assignment.md`
- Status helper: `scripts/work_unit_status.py`
- Unified entrypoint: `scripts/openclaw_company_ops.py`
- Route docs: `docs/discord-event-visibility.md`
- Existing Work Units for compatibility checks:
  - `docs/work-units/WU-260606-001/`
  - `docs/work-units/WU-260606-002/`

## Done Criteria

The Work Unit can be considered ready for review when:

- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id
  WU-260606-003` displays an execution route.
- JSON status output includes execution route information.
- Missing route metadata does not break summaries for older Work Units.
- `WU-260606-002` shows `cli-direct` from its existing artifact note.
- This Work Unit's artifacts record `discord-bound` execution route.
- Existing setup smokes still pass.

## Verification Criteria

Evidence or checks required for review:

- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id
  WU-260606-003`
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id
  WU-260606-003 --format json | python3 -m json.tool`
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id
  WU-260606-002`
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id
  WU-260606-001`
- `python3 -m py_compile scripts/*.py`
- `python3 scripts/company_ops_smoke.py multi-team`
- `python3 scripts/openclaw_company_ops.py smoke multi-team`
- `git diff --check`

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

```yaml
protocol_capsule:
  mode: goal
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
  `docs/work-units/WU-260606-003/evidence.md`
- PR or artifact: repo-local code and artifact patch, commit if accepted.
- Decision-ready summary: include route parsing behavior, checks performed, and
  any residual route ambiguity.

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
