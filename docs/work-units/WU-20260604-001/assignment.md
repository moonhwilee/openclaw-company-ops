# Assignment Packet: WU-20260604-001

Status: Manual Day-0

## Identity

- Work Unit id: `WU-20260604-001`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/4
- Operations Lead: Operations Lead
- Assigned Team Lead OpenClaw Agent: current OpenClaw main session
- Created at: 2026-06-04 KST
- Updated at: 2026-06-04 KST

## Goal

Run one small manual Work Unit using the current Day-0 templates, then write an
operations manual based on what the dry run proves.

## Background

OpenClaw Company Ops currently has architecture docs, a setup guide, GitHub
labels, a Work Card issue form, and Manual Day-0 templates. The next validation
step is to prove that the templates can carry one complete operating loop
without introducing a legacy path or fallback source of truth.

## Scope

The Team Lead should:

- Use Work Card #4 as the shared task card.
- Create a manual Assignment Packet, Ops Claim Ledger entry, Evidence & Result
  Record, and Operations Lead Decision for `WU-20260604-001`.
- Write `docs/operations-manual.md` from the observed manual flow.
- Update README and setup guide links so users can find the operations manual
  and dry run example.
- Keep all public docs generalized around the Operations Lead role.

## Non-goals

The Team Lead should not:

- Implement Pulse Monitor.
- Implement Discord Ops Bridge.
- Create or configure a GitHub Project.
- Add branch protection, rulesets, or required checks.
- Treat GitHub labels, dashboard state, Discord messages, or PR summaries as
  replacement truth for assignment, evidence, or decision artifacts.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- The Work Card must link to the Assignment Packet instead of replacing it.
- Completion requires evidence and an Operations Lead decision.

## Inputs

- `docs/templates/work-card.md`
- `docs/templates/assignment-packet.md`
- `docs/templates/ops-claim-ledger-entry.md`
- `docs/templates/evidence-result-record.md`
- `docs/templates/operations-lead-decision.md`
- `docs/setup-guide.md`
- `README.md`
- Work Card #4: https://github.com/moonhwilee/openclaw-company-ops/issues/4

## Done Criteria

The Work Unit can be considered ready for review when:

- The dry run artifacts exist under
  `docs/work-units/WU-20260604-001/`.
- `docs/operations-manual.md` explains daily manual operation.
- README links to the operations manual and dry run example.
- The setup guide points to the completed dry run and updated manual path.
- The manual flow preserves No legacy / No fallback rules.

## Verification Criteria

Evidence or checks required for review:

- `git diff --check` passes.
- GitHub Issue form YAML still parses.
- Public docs contain no private Operations Lead nickname.
- Docs do not claim that planned components are implemented.
- Docs do not turn Work Cards, labels, dashboards, Discord, or PR summaries into
  fallback truth sources.

## Expected Outputs

- Evidence & Result Record:
  `docs/work-units/WU-20260604-001/evidence.md`
- PR or artifact: documentation PR for this Work Unit
- Decision-ready summary: concise summary in the Evidence & Result Record

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
