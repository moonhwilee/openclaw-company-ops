# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260606-002`
- Title: Patch Work Unit execution visibility routing
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/18
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Goal

Remove the Phase 2 dogfood friction where Team Lead execution routing and
Discord visibility expectations were ambiguous.

## Background

Phase 2 completed as a source-artifact Work Unit, but the `build-lab` Team Lead
was invoked through a direct CLI session. Because that route did not target
Discord, `#team-build-lab` had no Work Unit record. Only a final `DECISION`
event was posted to `#ops-feed`, so the owner could not observe the full
`ASSIGNED -> STARTED -> RESULT_READY -> DECISION` path.

The correct patch is not to make Discord authoritative. The correct patch is to
make execution route selection explicit and give Operations Lead/Team Lead users
a repo-local formatter for source-artifact-backed lifecycle visibility events.

## Scope

What the team lead should do:

- Add a repo-local Work Unit lifecycle event formatter to `scripts/discord_ops.py`.
- Route the formatter through `scripts/openclaw_company_ops.py discord event ...`.
- Document the difference between `cli-direct` and `discord-bound` execution.
- Document when team-channel records are expected and when `#ops-feed` lifecycle
  events are the required visibility trail.
- Preserve Discord as visibility-only and publisher-only; do not add a command
  router, state mutation, or automatic sender.

## Non-goals

What the team lead should not do:

- Do not send Discord messages automatically from the formatter.
- Do not add a Discord command router.
- Do not mutate GitHub, claims, evidence, decisions, or execution state from
  Discord messages.
- Do not implement hooks in this Work Unit; only record whether Phase 3.5 is
  justified.
- Do not re-run or rewrite Phase 2.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- `#ops-feed` remains visibility-only.
- `#team-build-lab` records are required only for Discord-bound execution or
  explicit team-channel Q&A. CLI-direct execution must not pretend it created a
  team-channel record.

## Inputs

Links, files, references, or starting state:

- Phase 2 Work Unit: `WU-260606-001`
- Phase 2 evidence: `docs/examples/manual-dry-run/WU-260606-001/evidence.md`
- Phase 2 decision: `docs/examples/manual-dry-run/WU-260606-001/decision.md`
- Discord visibility guide: `docs/discord-event-visibility.md`
- Operations manual: `docs/operations-manual.md`
- Event formatter: `scripts/discord_ops.py`
- Unified entrypoint: `scripts/openclaw_company_ops.py`

## Done Criteria

The Work Unit can be considered ready for review when:

- `scripts/discord_ops.py` can format lifecycle events: `ASSIGNED`, `STARTED`,
  `BLOCKED`, `RESULT_READY`, and `DECISION`.
- The formatter requires Work Unit id, Work Card, owner, source artifact, and
  summary.
- The formatter can output both text and JSON.
- Docs explicitly distinguish `cli-direct` and `discord-bound` execution routes.
- Docs state that CLI-direct execution does not create team-channel records and
  must be made visible through source-artifact-backed `#ops-feed` events.
- Existing setup smokes still pass.

## Verification Criteria

Evidence or checks required for review:

- `python3 scripts/openclaw_company_ops.py discord event --help`
- Text event formatting smoke for `ASSIGNED`
- JSON event formatting smoke for `RESULT_READY` with parse validation
- Unsupported event validation smoke
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
  `docs/examples/manual-dry-run/WU-260606-002/evidence.md`
- PR or artifact:
  repo commit containing docs and formatter changes
- Decision-ready summary:
  a concise explanation of the removed routing/visibility ambiguity

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
