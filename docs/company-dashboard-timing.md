# Company Dashboard Timing

Status: GitHub Project dashboard accepted with bounded auto-sync

This guide defines when and how to use the Company Dashboard for OpenClaw
Company Ops.

The default dashboard is a GitHub Project. The owner watches Discord for the
event stream, but Discord is not enough for portfolio-level visibility. The
GitHub Project gives the owner an at-a-glance board/table for current Work Unit
state.

The dashboard is a visibility mirror only. It must point back to Work Cards,
Assignment Packets, Ops Claim Ledger entries, Evidence & Result Records, and
Operations Lead Decisions.

It is not a source of truth, not an Assignment Packet, not evidence, not a
decision record, not a command router, and not a recovery system.

## Current Recommendation

Enable a Company Dashboard with bounded auto-sync.

The accepted v1 shape is:

- a user-level or organization-level GitHub Project;
- a small, stable field set;
- a deterministic sync command with `--dry-run` and `--apply`;
- lifecycle one-shot sync as the primary update path for state changes;
- scheduled reconcile every few minutes as a safety net;
- no LLM calls in the sync path.

The repo-local visibility snapshot remains useful for local inspection:

```bash
python3 scripts/dashboard_snapshot.py dashboard snapshot --ledger "$LEDGER"
```

The snapshot reads source artifacts and renders dashboard-ready rows. It does
not create or mutate a GitHub Project.

## Operating Surface

Operating surface means the moving parts that must be configured, monitored,
debugged, secured, and recovered.

For dashboard sync, the operating surface includes:

- schedule configuration;
- GitHub auth and Project permissions;
- Project id and field ids;
- logs and audit records;
- duplicate-run locking;
- failure alerts;
- install, disable, and troubleshooting instructions.

Keep this surface small for v1.

## Scheduler Choice

Use a small scheduled command for v1. It should run, reconcile, write an audit
record, and exit.

Preferred options:

- OpenClaw cron or local scheduled runner: lowest operating surface for v1.
- `launchd` daemon: more durable for always-on services, but larger operating
  surface because it adds plist configuration, process lifecycle, restart
  policy, crash behavior, logs, and install/uninstall handling.
- GitHub Actions schedule: remote and convenient, but adds Actions quota,
  workflow/secrets management, and GitHub-hosted failure modes. Do not use it
  for v1 unless local scheduling is unavailable.

The sync is not an LLM-observed task. The scheduler runs a deterministic script
under the Company Ops host/user account. Team Leads create or update source
artifacts; they do not run the sync. The Operations Lead owns the sync policy
and reviews failures.

If the host is asleep, offline, or the local scheduler is disabled, sync pauses
until the host resumes. This is acceptable for v1 as long as the failure is
visible.

## Sync Interval

One-shot sync should run immediately after each accepted lifecycle state change,
so its freshness is normally the lifecycle command runtime plus GitHub API/UI
delay.

Dashboard freshness is approximately:

```text
one-shot runtime + small GitHub API/UI propagation delay
```

The scheduled reconcile interval is the stale-dashboard recovery window, not the
normal update path.

Recommended v1 reconcile interval:

- default: 5 minutes;
- allowed when owner wants faster stale-recovery: 2-3 minutes;
- do not go below 1 minute without evidence that the extra churn is useful.

At current expected Work Unit volume, a 5-minute interval has negligible system
load. It is normally JSON/Markdown reads plus a small number of GitHub API
calls. The main risks are GitHub API rate limit, auth failure, stale field ids,
and duplicate runs, not CPU or memory.

Required protections:

- lock file: skip if the previous sync is still running;
- idempotency: do not update fields that already match;
- changed-only API writes;
- max-run-time or timeout;
- audit log for each changed Project item;
- failure alert that does not invent or mutate status.

## Hybrid Sync Model

Use lifecycle one-shot sync as the primary dashboard update path.

Run one-shot sync after each source-backed lifecycle state change, such as:

- Work Card or Assignment Packet creation;
- `ASSIGNED`;
- `STARTED`;
- `CHECKPOINT`;
- `RESULT_READY`;
- Operations Lead review states such as `ACCEPTED`, `REVISE`, or
  `BLOCKED_DETAIL`;
- final closeout events.

The lifecycle operation must not depend on Project sync success. If Project
sync fails, the source artifact and Discord visibility result remain what they
are; the sync failure is logged and alerted separately.

Use scheduled reconcile as a safety net. It should detect and repair stale
Project state when one-shot sync was skipped, failed, or never ran because a
source artifact changed outside the normal lifecycle command path.

This gives:

- normal lifecycle overhead: roughly `+1-3s` per synced state transition;
- dashboard freshness: usually near-immediate after lifecycle events;
- recovery window for missed updates: typically within the scheduled reconcile
  interval.

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

Start with a small field set:

- Work Unit id.
- Repository.
- Work Card.
- Team Lead.
- Status.
- Phase.
- Priority.
- Blocker.
- Evidence present.
- Decision.
- Last proof or last source update.
- Assignment Packet reference.
- Ops Claim Ledger reference.
- Evidence & Result Record reference.
- Operations Lead Decision reference.

Avoid adding fields just because GitHub Projects allows them. Add fields only
when they support actual review or coordination.

## Views To Use

Start with four views:

- Active Work: open Work Cards grouped by status.
- Blocked Work: Work Cards where status is `blocked` or blocker is present.
- Decision Queue: Work Cards with result-ready evidence waiting for Operations
  Lead review.
- Packaging Readiness: Phase 6 and packaging-bound items only.

Optional later views:

- By repository.
- By Team Lead.
- By expected next review.
- Closed decisions.

Do not use views to hide missing artifacts. If an artifact is missing, the Work
Unit is blocked or stale until the source artifact is fixed.

## Auto-Sync Rules

The sync reads:

- GitHub Issues, labels, assignees, and milestones;
- Assignment Packets;
- Ops Claim Ledger entries;
- Evidence & Result Records;
- Operations Lead Decisions;
- proof logs or Discord visibility proof references when available.

The sync writes only:

- Project item membership;
- Project custom fields;
- sync audit logs;
- optional sync-failure alerts.

The sync must never:

- close or reopen Issues;
- create evidence;
- create Operations Lead decisions;
- mutate assignment or claim state;
- reassign Team Leads;
- recover agents;
- publish semantic Discord progress;
- treat Project fields as source truth;
- back-propagate Project edits into source artifacts.

If the dashboard disagrees with a source artifact, fix the dashboard. Do not
rewrite the source artifact to match the dashboard unless the source artifact is
actually wrong and the Operations Lead records the correction.

## Implementation Stages

Implement the dashboard sync in narrow stages:

1. `project-sync --dry-run`
   - Read source state.
   - Resolve Project and field ids.
   - Print planned item and field changes.
   - Mutate nothing.
2. `project-sync --apply`
   - Apply only changed Project item/field updates.
   - Record an audit log.
   - Preserve idempotency.
3. Lifecycle one-shot sync
   - Run after source-backed state transitions.
   - Scope to one Work Unit when possible.
   - Never make lifecycle success depend on Project sync success.
4. Scheduled reconcile
   - Run every 5 minutes by default as stale-dashboard recovery.
   - Use a lock file to prevent overlap.
   - Alert on failure without mutating source state.

## Creation Checklist

Before enabling the first Company Dashboard, confirm:

- Project fields and views are named.
- GitHub auth can read Issues and write Project items/fields.
- Project id and field ids are discoverable without storing secrets in the repo.
- `--dry-run` shows a clear diff.
- `--apply` is idempotent.
- Lifecycle one-shot sync can target one Work Unit.
- Scheduled reconcile has locking and logs.
- Failure alerts are visible but do not invent status.
- No rule requires dashboard data as completion truth.

If any item fails, keep GitHub Issues and source artifacts as the operating
truth and treat the Project as stale visibility until sync is fixed.

## Current State For This Repo

For `moonhwilee/openclaw-company-ops`, Phase 5.3 accepts a GitHub Project
dashboard with bounded auto-sync.

The next implementation work should prepare the Project field model and a
deterministic `project-sync` command. Do not install a long-lived daemon or use
LLM interpretation in the sync path.
