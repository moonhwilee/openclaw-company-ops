# Assignment Packet

Status: Product Work Unit Assignment

## Identity

- Work Unit id: `WU-20260605-002`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/14
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-05`
- Updated at: `2026-06-05`

## Goal

Implement the first minimal Work Unit artifact generator so users can create
the four required Work Unit artifacts without manually copying template files.

## Background

The implementation setup guide currently tells users to create a Work Unit
artifact directory by hand and copy `assignment.md`, `claim.md`, `evidence.md`,
and `decision.md` from templates. The automation replacement map already names
this future command as `openclaw-company-ops work-unit create`.

This Work Unit should start the product path with the smallest maintainable
repo-local CLI/script that replaces that manual artifact scaffolding block.

## Scope

- Add a minimal repo-local command or script for Work Unit artifact scaffolding.
- Keep the implementation small and easy to inspect.
- Generate `assignment.md`, `claim.md`, `evidence.md`, and `decision.md`.
- Populate at least Work Unit id, title, Work Card, Operations Lead, assigned
  Team Lead, and creation date where the target artifact supports those fields.
- Refuse to overwrite an existing output directory unless an explicit force
  option is provided.
- Validate required inputs before writing files.
- Update the implementation setup guide so the manual copy block points to the
  new command/script.
- Record evidence and a decision-ready summary in this Work Unit directory.

## Non-goals

- Do not implement a daemon, runtime service, database, dashboard backend, or
  hidden orchestrator.
- Do not implement Discord events, GitHub label mutation, claim mutation,
  automatic completion, automatic recovery, or stale-claim monitoring.
- Do not introduce a broad package framework unless the repo already requires
  it for this narrow CLI.
- Do not treat the GitHub Work Card as a replacement for this Assignment Packet.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Keep the implementation compatible with the current docs-first repo shape.
- Prefer Python standard library only unless a dependency is already present
  and clearly justified.

## Inputs

- Repository: `/Users/moon/src/openclaw-company-ops`
- Working branch: `codex/work-unit-artifact-generator`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/14
- Current manual setup guide: `docs/implementation-setup-guide.md`
- Templates:
  - `docs/templates/assignment-packet.md`
  - `docs/templates/ops-claim-ledger-entry.md`
  - `docs/templates/evidence-result-record.md`
  - `docs/templates/operations-lead-decision.md`
- Prior accepted smoke:
  - `docs/work-units/WU-20260605-001/decision.md`

## Done Criteria

The Work Unit can be considered ready for Operations Lead review when:

- A minimal CLI/script exists and is committed in the repo.
- The CLI/script creates a Work Unit artifact directory containing exactly the
  required four artifact files by default.
- Required inputs are validated before file creation.
- Existing artifact directories are not overwritten by default.
- Generated artifacts include the requested Work Unit id and title.
- The implementation setup guide documents the supported command/script and no
  longer presents the manual copy block as the only path.
- Evidence maps each done criterion to a check or artifact.
- The repo has no unintended dirty files outside this Work Unit scope.

## Verification Criteria

Evidence or checks required for review:

- Smoke command showing artifact generation into a temporary or test output
  directory.
- Smoke command showing overwrite protection.
- Static validation such as `git diff --check`.
- A file listing of the generated artifact directory.
- `git status --short` showing only intentional changed files.

## Protocol Capsule

```yaml
protocol_capsule:
  mode: goal
  support: [verify]
  loop: plan -> repeat(act_or_improve -> verify) until stop_only_on
  stop_only_on:
    - done_criteria_passed_with_evidence
    - explicit_blocker
    - safety_or_budget_limit
    - operations_lead_or_user_pause
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_goal_loop
```

## Expected Outputs

- Evidence & Result Record:
  `docs/work-units/WU-20260605-002/evidence.md`
- Operations Lead Decision:
  `docs/work-units/WU-20260605-002/decision.md`
- PR or artifact: implementation branch / PR for the minimal artifact
  generator.
- Decision-ready summary: concise Team Lead result report with checks,
  changed files, and residual risks.

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.

## Blocked Rule

If required inputs, done criteria, verification criteria, or this Protocol
Capsule are missing, report `blocked` before starting a goal loop. Do not
substitute the Work Card, a PR summary, or a Telegram status message for this
Assignment Packet.
