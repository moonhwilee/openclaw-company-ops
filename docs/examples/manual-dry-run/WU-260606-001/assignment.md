# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-260606-001`
- Title: Add Work Unit status summary helper
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/17
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Goal

Add a small repo-local Work Unit status summary helper that lets a person audit
one Work Unit from source artifacts without trusting a chat summary.

## Background

Phase 2 of the post-setup plan requires one real product-shaped dogfood Work
Unit. The current repo already has:

- Work Unit artifact generation in `scripts/work_unit_artifacts.py`.
- JSON-backed claim management in `scripts/ops_claim_ledger.py`.
- Ledger-based dashboard snapshots in `scripts/dashboard_snapshot.py`.
- Visibility-only Discord alert formatting in `scripts/discord_ops.py`.

What is missing is a focused command that answers, for one Work Unit, whether
the audit trail is ready: Work Card, assignment, claim, evidence, decision,
current expected state, missing artifacts, and next review.

## Scope

What the team lead should do:

- Add a read-only status summary helper script for one Work Unit.
- Expose it through the repo-local entrypoint.
- Read source artifacts and optional claim ledger data.
- Report current audit state, missing artifacts, and next action.
- Support at least text output and JSON output.
- Keep behavior deterministic and local; no GitHub, Discord, claim, evidence,
  decision, dashboard, recovery, reassignment, or completion mutation.

## Non-goals

What the team lead should not do:

- Do not send Discord messages.
- Do not mutate GitHub issues, labels, projects, or pull requests.
- Do not update claim ledger state from this helper.
- Do not infer completion from labels, dashboard rows, or chat messages.
- Do not implement the optional hook harness.
- Do not add a database or external service.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- This Work Unit is Phase 2 dogfood, not a Phase 3 friction patch.
- The helper must make missing evidence or missing decisions visible instead of
  papering them over.

## Inputs

Links, files, references, or starting state:

- Plan: `docs/post-setup-plan.md`
- Operations manual: `docs/operations-manual.md`
- Architecture: `docs/architecture.md`
- Entrypoint: `scripts/openclaw_company_ops.py`
- Claim CLI: `scripts/ops_claim_ledger.py`
- Dashboard snapshot CLI: `scripts/dashboard_snapshot.py`
- Existing accepted example: `docs/examples/manual-dry-run/WU-20260605-003/`
- This Work Unit artifacts: `docs/examples/manual-dry-run/WU-260606-001/`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/17

## Done Criteria

The Work Unit can be considered ready for review when:

- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001 ...`
  or an equally clear command renders a readable summary for this Work Unit.
- The command reports Work Card, Assignment Packet, claim, evidence, decision,
  current state, missing artifacts, and next review or next action.
- JSON output is available for future dashboard or Discord formatter inputs.
- Missing evidence or pending decision states are shown explicitly.
- The helper is read-only and does not mutate any operating surface.
- The entrypoint help includes the new command.

## Verification Criteria

Evidence or checks required for review:

- `python3 -m py_compile scripts/*.py`
- A positive status summary smoke for `WU-260606-001`.
- A positive status summary smoke for accepted Phase 1 artifact
  `WU-20260605-003`.
- A JSON output smoke that parses as JSON.
- A missing Work Unit or missing artifact smoke that fails or reports an audit
  problem clearly.
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
  loop: plan -> repeat(act_or_improve -> verify) until stop_only_on
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
- PR or artifact: new or updated repo-local helper script and entrypoint route
- Decision-ready summary: concise mapping from done criteria to verification
  evidence

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
