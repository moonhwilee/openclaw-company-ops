# Assignment Packet: WU-20260604-002

Status: Manual Day-0

## Identity

- Work Unit id: `WU-20260604-002`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/6
- Operations Lead: Operations Lead
- Assigned Team Lead OpenClaw Agent: current OpenClaw main session
- Created at: 2026-06-04 KST
- Updated at: 2026-06-04 KST

## Goal

Write a Discord event visibility guide for OpenClaw Company Ops and validate it
as the second manual Work Unit.

## Background

The setup guide already names Discord as an optional event visibility surface.
The operations manual also states that Discord messages are not source
artifacts. The next useful documentation slice is a dedicated guide that tells
users exactly what Discord may publish, what it must link to, and what it must
never decide.

## Scope

The Team Lead should:

- Use Work Card #6 as the shared task card.
- Create assignment, claim, evidence, and decision artifacts for
  `WU-20260604-002`.
- Write `docs/discord-event-visibility.md`.
- Update README, setup guide, operations manual, and dry run index links if
  needed.
- Keep Discord scoped to visibility and alert publication only.

## Non-goals

The Team Lead should not:

- Implement Discord Ops Bridge.
- Create a Discord bot.
- Create a Discord command router.
- Add state mutation through Discord.
- Implement Pulse Monitor.
- Create a GitHub Project.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Discord must not be described as an authority, database, command router, or
  source of truth.
- Completion requires evidence and an Operations Lead decision.

## Inputs

- `README.md`
- `docs/setup-guide.md`
- `docs/operations-manual.md`
- `docs/examples/manual-dry-run/README.md`
- Work Card #6: https://github.com/moonhwilee/openclaw-company-ops/issues/6

## Done Criteria

The Work Unit can be considered ready for review when:

- `docs/discord-event-visibility.md` exists.
- The guide defines channels, event types, required fields, message shape,
  forbidden actions, blocked events, alert events, and decision events.
- README, setup guide, operations manual, and dry run index link to the guide or
  second dry run where appropriate.
- The guide preserves No legacy / No fallback rules.

## Verification Criteria

Evidence or checks required for review:

- `git diff --check` passes.
- GitHub Issue form YAML still parses.
- Public docs contain no private Operations Lead nickname.
- Discord is not described as source of truth, command router, or mutation
  surface.
- Planned Discord Ops Bridge remains clearly unimplemented.

## Expected Outputs

- Evidence & Result Record:
  `docs/examples/manual-dry-run/WU-20260604-002/evidence.md`
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
