# Assignment Packet: WU-20260604-003

Status: Manual Day-0

## Identity

- Work Unit id: `WU-20260604-003`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/8
- Operations Lead: Operations Lead
- Assigned Team Lead OpenClaw Agent: current OpenClaw main session
- Created at: 2026-06-04 KST
- Updated at: 2026-06-04 KST

## Goal

Write a Company Dashboard timing guide that explains when to create a GitHub
Project, what it should track, and what it must not replace.

## Background

The setup guide and operations manual already say that GitHub Projects /
Company Dashboard should be deferred until enough Work Cards exist. The next
useful slice is a dedicated timing guide that prevents premature dashboard
setup while preserving the future path for cross-repository visibility.

## Scope

The Team Lead should:

- Use Work Card #8 as the shared task card.
- Create assignment, claim, evidence, and decision artifacts for
  `WU-20260604-003`.
- Write `docs/company-dashboard-timing.md`.
- Update README, setup guide, operations manual, and dry run index links if
  needed.
- Keep GitHub Project / Company Dashboard scoped to visibility only.

## Non-goals

The Team Lead should not:

- Create a GitHub Project.
- Create a dashboard repository.
- Implement dashboard software.
- Add branch protection or rulesets.
- Treat dashboard fields as source artifacts.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Dashboard must not be described as assignment, claim, evidence, decision, or
  completion truth.
- Completion requires evidence and an Operations Lead decision.

## Inputs

- `README.md`
- `docs/setup-guide.md`
- `docs/operations-manual.md`
- `docs/examples/manual-dry-run/README.md`
- Work Card #8: https://github.com/moonhwilee/openclaw-company-ops/issues/8
- GitHub Projects documentation:
  - https://docs.github.com/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project
  - https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project
  - https://docs.github.com/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically

## Done Criteria

The Work Unit can be considered ready for review when:

- `docs/company-dashboard-timing.md` exists.
- The guide defines do-not-create and create criteria.
- The guide explains user/org-level GitHub Project visibility.
- The guide defines dashboard fields and views.
- The guide forbids dashboard-as-truth behavior.
- README, setup guide, operations manual, and dry run index link to the guide or
  third dry run where appropriate.

## Verification Criteria

Evidence or checks required for review:

- `git diff --check` passes.
- GitHub Issue form YAML still parses.
- Public docs contain no private Operations Lead nickname.
- Dashboard is not described as source of truth, assignment packet, evidence,
  decision, or mutation authority.
- Planned dashboard remains clearly uncreated and unimplemented.

## Expected Outputs

- Evidence & Result Record:
  `docs/examples/manual-dry-run/WU-20260604-003/evidence.md`
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
