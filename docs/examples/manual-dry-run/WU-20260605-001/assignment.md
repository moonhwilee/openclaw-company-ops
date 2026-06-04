# Assignment Packet

Status: Day-0 Smoke Artifact + Live Build-Lab Read-Only Run

## Identity

- Work Unit id: `WU-20260605-001`
- Work Card: manual smoke artifact
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-05`
- Updated at: `2026-06-05`

## Goal

Validate that Team Lead Protocol Capsule documentation and templates make the
Team Lead run delegated Work Units packet-first through `goal`, `verify`, and
`conv`, without introducing a separate execution runtime.

## Background

The Company Ops structure relies on Team Lead OpenClaw Agents reproducing the
old legacy convergence loop through compact LLM instructions. The
Operations Lead must provide an Assignment Packet with a Protocol Capsule, and
the Team Lead must execute that packet rather than inventing criteria from
request prose.

## Scope

- Add canonical protocol references for `goal`, `verify`, and `conv`.
- Add Protocol Capsule guidance to the Assignment Packet template.
- Add packet-first execution guidance to the Team Playbook.
- Update architecture and index documents.
- Produce a manual smoke artifact showing the expected Work Unit shape.
- Run a live read-only `build-lab` smoke turn against this Assignment Packet.
- Run static validation checks on the documentation.

## Non-goals

- Do not implement a CLI.
- Do not implement a protocol runtime, daemon, classifier, database, or hidden
  protocol runtime replacement.
- Do not mutate live OpenClaw agent configuration.
- Do not claim a real build-lab runtime execution unless a separate delegated
  session is run and recorded.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Keep the mechanism LLM-first and prompt/template based.

## Inputs

- `docs/architecture.md`
- `docs/templates/assignment-packet.md`
- `docs/templates/team-playbook.md`
- `docs/templates/README.md`
- `docs/examples/manual-dry-run/README.md`
- `README.md`

## Done Criteria

The Work Unit can be considered ready for review when:

- Canonical protocol files exist under `docs/protocols/`.
- The Assignment Packet template includes a Protocol Capsule section.
- The Team Playbook includes packet-first, `goal`, `verify`, and
  `conv` execution guidance.
- Architecture and index docs reference Team Lead Protocols and Protocol
  Capsules.
- A manual smoke example exists for `WU-20260605-001`.
- A live read-only `build-lab` smoke run records packet-first behavior:
  blocked when the packet is unavailable, then pass after the packet is provided
  by absolute source-of-truth path.
- Static validation checks pass.

## Verification Criteria

Evidence or checks required for review:

- `git diff --check`
- A content validation check confirming required files and phrases exist.
- A private-name scan confirming public docs do not introduce private user
  names.
- A live `build-lab` smoke result confirming the Team Lead follows the
  Packet-First Rule and returns an evidence-mapped decision.
- `git status --short` showing the exact changed files.

## Protocol Capsule

```yaml
protocol_capsule:
  mode: goal
  support: [verify, conv]
  loop: plan -> act -> verify -> improve -> reverify
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

- Evidence & Result Record: `docs/examples/manual-dry-run/WU-20260605-001/evidence.md`
- PR or artifact: local documentation patch
- Decision-ready summary: `docs/examples/manual-dry-run/WU-20260605-001/decision.md`

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.

## Blocked Rule

If protocol files, template changes, or validation evidence are missing, report
`blocked`. Do not substitute a status message for the Evidence & Result Record.
