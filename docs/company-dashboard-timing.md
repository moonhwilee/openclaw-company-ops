# Company Dashboard Timing

Status: Manual Day-0

This guide explains when to create a Company Dashboard for OpenClaw Company Ops.

The default dashboard candidate is a GitHub Project. Do not create it too early.
At the current stage, the dashboard is a visibility layer only. It must point
back to Work Cards, Assignment Packets, Ops Claim Ledger entries, Evidence &
Result Records, and Operations Lead Decisions.

It is not a source of truth, not an Assignment Packet, not evidence, not a
decision record, not a command router, and not a recovery system.

## Current Recommendation

Do not enable a Company Dashboard yet.

Use GitHub Issues and linked manual artifacts until the work naturally grows
beyond a single repo issue list.

Create the first dashboard only when at least one of these is true:

- There are 5 or more active Work Cards at the same time.
- There are 2 or more active repositories with Work Cards.
- The Operations Lead needs to compare blockers, owners, or decision status
  across multiple Work Units.
- The Owner asks for portfolio-level visibility.
- Manual issue-list review is causing missed stale claims or missed decisions.

If none of these are true, the dashboard adds overhead before it adds value.

## Repository Strategy

Use one repository per real project or product. Do not create one repository per
Work Unit.

Do not create a dedicated dashboard repository just to hold dashboard state.

Recommended structure:

- Product/project repo: source code, issues, pull requests, tests, releases.
- Work Card: GitHub Issue in the repo where the work belongs.
- Company Dashboard: user-level or organization-level GitHub Project that can
  reference issues and pull requests across repositories.

GitHub's Projects documentation describes projects as user or organization work
planning surfaces, and project items can include issues and pull requests. Use
that cross-repository ability for visibility instead of creating an umbrella
repo.

References:

- https://docs.github.com/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project
- https://docs.github.com/enterprise-cloud@latest/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically

## Fields To Use

When the dashboard is created, start with a small field set:

- Work Unit id.
- Repository.
- Work Card.
- Team Lead.
- State.
- Priority.
- Blocker.
- Expected next review.
- Assignment Packet reference.
- Ops Claim Ledger reference.
- Evidence & Result Record reference.
- Operations Lead Decision reference.

Avoid adding fields just because GitHub Projects allows them. Add fields only
when they support actual review or coordination.

## Views To Use

Start with three views:

- Active Work: open Work Cards grouped by state.
- Blocked Work: Work Cards where state is `blocked` or blocker is present.
- Decision Queue: Work Cards with result-ready evidence waiting for Operations
  Lead review.

Optional later views:

- By repository.
- By Team Lead.
- By expected next review.
- Closed decisions.

Do not use views to hide missing artifacts. If an artifact is missing, the Work
Unit is blocked.

## Manual Add Rules

Manual Day-0 dashboard management should stay explicit.

Add a Work Card to the dashboard only after:

- The Work Card exists.
- The Assignment Packet exists.
- The initial claim exists.
- The dashboard item links back to those artifacts.

Remove or archive dashboard items only after:

- Evidence is linked.
- Operations Lead Decision is linked.
- Work Card is closed or the Work Unit is explicitly abandoned by decision.

Dashboard cleanup must not replace Work Card closure.

## Automation Timing

Do not automate dashboard intake until manual use proves the field set and views
are correct.

Automation may be considered when:

- There are repeated manual dashboard-add steps.
- Multiple repos produce Work Cards.
- Missing dashboard items create real visibility problems.
- The dashboard field set has stabilized.

Even then, automation should only add or update visibility items from source
artifacts. It must not decide assignment, evidence, completion, reassignment, or
recovery.

## Forbidden Uses

The dashboard must not:

- Replace a Work Card.
- Replace an Assignment Packet.
- Replace an Ops Claim Ledger entry.
- Replace Evidence & Result Records.
- Replace Operations Lead Decisions.
- Infer completion from a field value.
- Reassign Team Leads.
- Restart or recover agents.
- Mutate execution state.
- Act as a command router.
- Become a hidden database of work truth.

If the dashboard disagrees with a source artifact, fix the dashboard. Do not
rewrite the source artifact to match the dashboard unless the source artifact is
actually wrong and the Operations Lead records the correction.

## Creation Checklist

Before creating the first Company Dashboard, confirm:

- At least 5 active Work Cards, or multiple active repos, or a real visibility
  failure.
- Work Card labels are stable enough to support dashboard views.
- Assignment, claim, evidence, and decision artifacts are being used
  consistently.
- The Operations Lead can name the dashboard fields and views needed.
- The dashboard will be user-level or organization-level, not a fake umbrella
  repo.
- No rule requires dashboard data as completion truth.

If any item fails, keep using GitHub Issues and linked artifacts.

## Current State For This Repo

For `moonhwilee/openclaw-company-ops`, do not create a GitHub Project yet.

The current active Work Card count is low, and the recent Work Units have been
sequential documentation dry runs. The issue list and linked artifacts are still
sufficient.

The next dashboard decision should be revisited when:

- Multiple Work Cards are open at once.
- Multiple product repositories need shared visibility.
- The Operations Lead starts missing blockers, stale claims, or decision queues
  because the issue list is no longer enough.
