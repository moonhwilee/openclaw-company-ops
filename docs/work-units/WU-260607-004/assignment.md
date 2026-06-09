# Assignment Packet

Status: Ready

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260607-004`
- Title: Verify Company Ops live operating path after Progress updates
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/23
- Operations Lead: `geumbi`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Goal

Verify whether the current Company Ops live operating path works as intended
after the Progress dashboard updates.

## Background

The owner asked to run the real Company Ops verify-mode path and monitor the
whole process for workflow problems. This is a live operating-path verification,
not a replay of prior smoke output. The Team Lead should verify the current
source-backed workflow from the active repo, source artifacts, Project sync
state, and deterministic checks.

## Scope

What the team lead should do:

- Inspect the current Company Ops repo state and relevant protocol docs.
- Verify this Work Unit's Assignment Packet, Work Card, claim state, Progress
  row, GitHub Project sync plan/apply state, and Discord visibility proof.
- Run the relevant deterministic checks needed to decide whether the live path
  behaved correctly.
- Map evidence to each done and verification criterion.
- Recommend `accept`, `revise`, `hold`, or `reject` for this verify-only Work
  Unit.

## Non-goals

What the team lead should not do:

- Do not modify source files.
- Do not create fallback truth in GitHub Project, Discord, or comments.
- Do not close or mutate the Work Card.
- Do not use prior smoke artifacts as the answer key.
- Do not implement fixes unless explicitly reassigned by Operations Lead.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- No extra LLM call for dashboard progress inference.
- Verify evidence, not effort or status claims.

## Inputs

Links, files, references, or starting state:

- Owner request: "Company Ops 실전 경로를 Verify 모드로 검증하고 싶어..."
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/23
- Assignment Packet: `docs/work-units/WU-260607-004/assignment.md`
- Claim: `docs/work-units/WU-260607-004/claim.md`
- Evidence draft: `docs/work-units/WU-260607-004/evidence.md`
- Decision draft: `docs/work-units/WU-260607-004/decision.md`
- Protocols: `docs/operations-manual.md`, `docs/protocols/verify.md`,
  `docs/protocols/goal.md`, `docs/company-dashboard-timing.md`
- Project field-map:
  `/Users/moon/.openclaw/state/openclaw-company-ops/project-field-map.json`

## Done Criteria

The Work Unit can be considered ready for review when:

- Work Unit artifacts exist and contain this verify-only scope.
- Owner-facing and team-detail assignment visibility are published in the
  required serial order and read back.
- `progress.jsonl` records source-backed progress for this Work Unit and
  Project sync derives `Progress` without LLM calls.
- GitHub Project sync dry-run/apply has no audit problems and does not use
  fallback state.
- Team Lead verify result maps each criterion to concrete evidence.
- Operations Lead can make a decision from source artifacts and verify result.

## Verification Criteria

Evidence or checks required for review:

- `python3 -m py_compile scripts/*.py .codex/hooks/*.py`
- `python3 scripts/company_ops_smoke.py multi-team`
- `python3 scripts/openclaw_company_ops.py smoke multi-team`
- `python3 scripts/openclaw_company_ops.py project-sync dry-run --work-unit-id
  WU-260607-004 --field-map
  /Users/moon/.openclaw/state/openclaw-company-ops/project-field-map.json
  --format json`
- `python3 scripts/openclaw_company_ops.py project-sync apply --work-unit-id
  WU-260607-004 --field-map
  /Users/moon/.openclaw/state/openclaw-company-ops/project-field-map.json
  --format json`
- Discord proof validation for `WU-260607-004`.
- GitHub Project readback for `WU-260607-004` fields: `Status`, `Progress`,
  `Evidence present`, `Decision`, and source references.

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

```yaml
protocol_capsule:
  mode: verify
  support: []
  loop: map_criteria_to_evidence_once
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
  `docs/work-units/WU-260607-004/evidence.md`
- PR or artifact: no PR expected; source artifact updates may be committed by
  Operations Lead after review.
- Decision-ready summary: concise verify recommendation with evidence mapping.

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
