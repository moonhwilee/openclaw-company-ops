# Assignment Packet

Status: Manual Day-0

## Identity

- Work Unit id: `WU-20260604-004`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/10
- Operations Lead: Operations Lead
- Assigned Team Lead OpenClaw Agent: current documentation implementation session
- Created at: 2026-06-04
- Updated at: 2026-06-04

## Goal

Create an Implementation Setup Guide that a user can follow to manually build
the complete OpenClaw Company Ops structure before CLI automation exists.

## Background

The existing setup guide explains the Manual Day-0 operating model, but it is
not yet sufficient for a new user to install or implement the full structure.
The missing pieces include OpenClaw agent setup, GitHub setup, artifact storage,
Ops Claim Ledger setup, Pulse Monitor setup, Discord visibility setup, Team
Lead / Pilot execution setup, smoke testing, and forbidden fallback rules.

## Scope

The Team Lead should:

- Add `docs/implementation-setup-guide.md`.
- Include detailed current manual implementation steps.
- Make each manual block easy to replace later with CLI automation.
- Cover OpenClaw agent setup.
- Cover GitHub repo, labels, and issue template setup.
- Cover Work Unit artifact storage.
- Cover file-backed Ops Claim Ledger setup.
- Cover alert-only Pulse Monitor setup.
- Cover Discord visibility setup.
- Cover Team Lead / Pilot execution setup.
- Cover an end-to-end smoke test and troubleshooting.
- Link the new guide from the existing docs entry points.

## Non-goals

- Do not implement the CLI in this Work Unit.
- Do not add a database ledger.
- Do not create a GitHub Project dashboard.
- Do not create a Discord command router.
- Do not add automatic recovery, restart, reassignment, or completion.
- Do not introduce a hidden orchestrator agent.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Public docs must use `Operations Lead`.
- Discord and dashboard surfaces must remain visibility only.
- Manual implementation steps should be removable when CLI automation exists.

## Inputs

- `README.md`
- `docs/setup-guide.md`
- `docs/operations-manual.md`
- `docs/company-dashboard-timing.md`
- `docs/discord-event-visibility.md`
- `docs/templates/`
- Work Card #10

## Done Criteria

The Work Unit is ready for review when:

- `docs/implementation-setup-guide.md` exists.
- The guide can be followed as a manual implementation path.
- The guide clearly distinguishes current manual steps from future CLI
  replacement points.
- OpenClaw agent setup and GitHub setup are covered.
- Runtime state, claim ledger, pulse, Discord, Team Lead/Pilot, smoke test, and
  troubleshooting sections are covered.
- Existing docs link to the new guide.
- Evidence and decision artifacts exist for this Work Unit.

## Verification Criteria

Required checks:

- Markdown whitespace check.
- GitHub Issue template YAML parse.
- Public nickname scan.
- No legacy / no fallback invariant scan.
- Manual review that Discord/dashboard remain visibility only.

## Expected Outputs

- Evidence & Result Record: `evidence.md`
- PR or artifact: documentation PR for the implementation setup guide
- Decision-ready summary: included in PR and Work Card comment

## Reporting Format

Report:

- Result summary.
- Files changed.
- Checks performed.
- Remaining risks.
- PR and Work Card links.

## Blocked Rule

If required setup facts cannot be verified, state the limitation in the guide
instead of inventing a supported command. Do not substitute a GitHub comment,
Discord message, or dashboard note for required artifacts.
