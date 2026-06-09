# Company Dashboard Timing

Status: GitHub Project dashboard accepted with bounded foreground sync

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

Enable a Company Dashboard with bounded source-backed foreground sync.

The accepted v1 shape is:

- a user-level or organization-level GitHub Project;
- a small, stable field set;
- a deterministic sync command with `dry-run` and `apply` actions;
- lifecycle one-shot sync as the primary update path for state changes;
- explicit foreground reconcile as the stale-mirror safety net;
- no public-v1 scheduled dashboard reconcile, cron, launchd, daemon, or hidden
  runner;
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

- GitHub auth and Project permissions;
- Project id and field ids;
- logs and audit records;
- duplicate-run locking;
- failure reports;
- explicit enable, disable, and troubleshooting instructions.

Keep this surface small for v1.

## Reconcile Choice

Public v1 must not install a scheduled dashboard reconcile. Reconcile is a
foreground Operations Lead command: run it explicitly when `doctor` reports stale
mirror drift, after manual source repair, or during operator review.

Allowed public-v1 path:

- `project-sync reconcile` as an explicit foreground command with local
  field-map configuration, `gh` auth, locking, and audit output.

Deferred paths:

- OpenClaw cron or a local scheduled runner;
- `launchd` daemon;
- GitHub Actions schedule;
- any hidden runner that mutates Project items without an explicit foreground
  operation.

The sync is not an LLM-observed task. The foreground command runs a deterministic
script under the Company Ops host/user account. Team Leads create or update
source artifacts; they do not run the sync. The Operations Lead owns the sync
policy and reviews failures.

## Sync Interval

One-shot sync should run immediately after each accepted lifecycle state change,
so its freshness is normally the lifecycle command runtime plus GitHub API/UI
delay.

Dashboard freshness is approximately:

```text
one-shot runtime + small GitHub API/UI propagation delay
```

There is no public-v1 scheduled reconcile interval. The stale-dashboard recovery
window is the next explicit foreground reconcile, or the next `doctor` /
`preflight` check that reports stale mirror drift.

If a later gate accepts scheduled dashboard reconcile, it must define:

- the schedule owner and disable path;
- the exact interval and failure reporting behavior;
- duplicate-run locking;
- suppression rules for archived, closed, or local-only Work Units;
- evidence that the extra operating surface is worth it.

Required protections:

- lock file: skip if the previous sync is still running;
- idempotency: do not update fields that already match;
- changed-only API writes;
- max-run-time or timeout;
- audit log for each changed Project item;
- failure report that does not invent or mutate status.

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

When the assignment handoff creates both owner-facing and team-detail
visibility cards, use a validated serial publish. The owner-facing assignment
readback must complete before team-detail handoff readback. Project one-shot
sync may run after each successful card, but Project sync failure must not cause
the publisher to invent or reorder source state.

The lifecycle operation must not depend on Project sync success. If Project
sync fails, the source artifact and Discord visibility result remain what they
are; the sync failure is logged and alerted separately.

Use explicit foreground reconcile as a safety net. It should detect and repair
stale Project state when one-shot sync was skipped, failed, or never ran because
a source artifact changed outside the normal lifecycle command path.

This gives:

- normal lifecycle overhead: roughly `+1-3s` per synced state transition;
- dashboard freshness: usually near-immediate after lifecycle events;
- recovery for missed updates: when Operations Lead runs foreground reconcile or
  `doctor` reports stale mirror drift and the operator follows the next step.

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
- Repository. Use the editable `Source Repository` field in GitHub Projects
  field maps because GitHub's built-in `Repository` field is read-only through
  Project item mutation APIs.
- Work Card.
- Team Lead.
- Status. Use GitHub's built-in `Status` field as the dashboard status field,
  with Company Ops options: `Assigned`, `In Progress`, `Result Ready`,
  `Accepted`, `Revise`, and `Blocked`.
- Progress.
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

`Last proof or last source update` is a GitHub Project text field. Source
artifacts keep UTC timestamps for audit stability, while `project-sync` formats
the dashboard mirror using the machine's local timezone. This field is
timestamp-first only; do not place next-action prose or audit narrative in it.

Long-running Work Units should keep `Status` coarse and put progress detail in
separate dashboard fields. Do not create statuses such as `Round 2` or `Phase
3`; those are progress metadata, not lifecycle states. The recommended shape is:

- `Status`: lifecycle state such as `In Progress`, `Result Ready`, or `Revise`.
- `Progress`: current phase, round, or slice label from a source-backed
  progress artifact or checkpoint while work is active; terminal closeouts show
  a final summary such as `Final: Accepted`.
- optional later fields such as `Round`, `Current slice`, or `Next checkpoint`
  only if they are populated from source artifacts or proof logs.

For v1, source-backed progress is recorded as optional Work Unit
`progress.jsonl` rows. While work is active, `project-sync` derives the
dashboard `Progress` field from the latest valid row. A compact value such as
`2/7 · implementation` is enough for one-pass work. When a Work Unit is `goal`
or `convergence` mode, display the round first in compact form, for example
`R1 · 2/7 · implementation`. After final closeout, `project-sync` overrides the
checkpoint-derived value with `Final: Accepted`, `Final: Revise requested`, or
`Final: Blocked` so terminal Work Units do not look partially complete. This
keeps active work distinct from completed work without requiring a new LLM
summary or expensive progress calculation.

Short Work Units may not need a checkpoint or explicit `progress.jsonl` row.
When no valid progress row exists, `project-sync` may display a proof-derived
lifecycle value from the local `visibility-proof.jsonl`, such as
`verify · started`, `verify · result ready`, or `verify · accepted`. This is a
dashboard projection only: it must use validated local proof rows, must not
infer phase/round/slice details, and must not read Discord/GitHub Project text
back into source truth.

The dashboard may display phase or round progress only when the value is derived
from source-backed lifecycle updates. Manual Project edits remain visibility
notes only and must not become operating truth.

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

For the primary owner-facing table view, prefer this visible field order:

1. Title.
2. Status.
3. Progress.
4. Priority.
5. Team Lead.
6. Evidence present.
7. Decision.
8. Blocker.
9. Last proof or last source update.
10. Work Card.
11. Work Unit id.
12. Source Repository.

Keep GitHub collaboration fields such as Assignees, Linked pull requests,
Sub-issues progress, Reviewers, Milestone, Iteration, Estimate, Start date, and
Target date available but hidden in the primary owner view unless they are
actively used for a specific Work Unit. Keep source artifact reference fields
hidden in the primary view; they are audit drill-down fields.

Accepted Work Units are the owner's final-review queue. After the Operations
Lead has sent the visible completion report and the Work Card has an accepted
decision/evidence trail, keep the Project item visible as `Accepted` until the
owner has had a reasonable chance to inspect it or explicitly says it can be
cleared. Then archive the Project item from the active dashboard and close the
Work Card when the task is fully closed. Immediate archive is reserved for
completed samples, internal smoke tests, or owner-approved cleanup. Project
archive is safe because source artifacts remain the source of truth.

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

1. `project-sync dry-run` - implemented as local planner
   - Read source state.
   - Read optional local Project and field-id map.
   - Print planned item and field changes.
   - Mutate nothing.
2. `project-sync field-map` - implemented as the local configuration helper
   - Read an existing GitHub Project and its fields through `gh`.
   - Write a local field-id map outside repo state.
   - Map source repository text to `Source Repository` when GitHub's built-in
     `Repository` field is present.
   - Store no tokens.
3. `project-sync apply` - implemented as the Project mutation path
   - Require an explicit local field map with owner, Project number, Project id,
     and field ids.
   - Require `gh` auth with the `project` scope before mutation.
   - Add the Work Card issue or pull request to the Project when missing.
   - Apply only changed Project item/field updates.
   - Record an audit log.
   - Preserve idempotency.
4. Lifecycle one-shot sync - implemented for `discord publish-card`
   - Runs after a successful source-backed visibility publish when a field map is
     provided.
   - Scopes to the card's Work Unit.
   - Never makes Discord publish success depend on Project sync success.
5. Serial assignment publish - implemented for `discord publish-sequence`
   - Validates card order before any send/readback occurs.
   - Publishes one card at a time and stops on the first failed send/readback.
   - Blocks team-detail handoff before owner-facing assignment visibility.
   - Uses the same source-backed single-card publish path; it does not add a
     legacy route, fallback store, or hidden runner.
6. Foreground reconcile - implemented as the existing-item safety-net path
   - `project-sync reconcile` scans Work Unit artifacts and applies changed
     Project updates only for items already present in the dashboard.
   - Skip historical or local-only Work Units whose Work Card is not a GitHub
     issue or pull request.
   - Do not add missing Project items; lifecycle one-shot sync owns active item
     creation so archived history does not reappear.
   - Uses a lock file to prevent overlap.
   - Run explicitly by Operations Lead as stale-dashboard recovery; public v1
     must not install a scheduled reconcile by default.
   - Reports/logs failure without mutating source state.

## Creation Checklist

Before enabling the first Company Dashboard, confirm:

- Project fields and views are named.
- GitHub auth can read Issues and write Project items/fields.
- Project id and field ids are discoverable without storing secrets in the repo.
- `project-sync dry-run` shows a clear diff.
- `project-sync apply` is idempotent.
- Lifecycle one-shot sync can target one Work Unit.
- Scheduled reconcile has locking and logs.
- Failure alerts are visible but do not invent status.
- No rule requires dashboard data as completion truth.

If any item fails, keep GitHub Issues and source artifacts as the operating
truth and treat the Project as stale visibility until sync is fixed.

## Current State For This Repo

For `moonhwilee/openclaw-company-ops`, Phase 5.3 accepted a GitHub Project
dashboard mirror, and Phase 5.7/6 narrowed the packaged public-v1 behavior to
bounded foreground sync.

Current implementation state:

- `python3 scripts/openclaw_company_ops.py project-sync dry-run` exists.
- `python3 scripts/openclaw_company_ops.py project-sync field-map` exists.
- `python3 scripts/openclaw_company_ops.py project-sync apply` exists.
- `python3 scripts/openclaw_company_ops.py project-sync reconcile` exists.
- Dry-run reads Work Unit source artifacts and optional claim ledger state,
  derives desired Project fields deterministically, and mutates nothing.
- Field-map generation reads an existing GitHub Project and writes local config
  only.
- Apply requires an explicit local field map and `gh` auth with `project` scope.
- Example local field map shape is documented in
  `docs/company-dashboard-project-field-map.example.json`; copy it outside the
  repo state path before inserting real ids.
- Apply adds missing Project item membership and updates changed fields only.
- Apply writes an audit log and uses a lock by default.
- `discord publish-card` can run a nonblocking one-shot Project sync after a
  successful visibility publish when a field map is supplied.
- `work-unit progress` can append optional source-backed progress rows.
- `work-unit checkpoint` is the preferred live checkpoint path because it
  validates one payload, publishes/readbacks the team `CHECKPOINT`, appends the
  matching progress row, and can run one changed-only Project mirror sync.
- `project-sync` derives the dashboard `Progress` field from the latest valid
  progress row for active work, from a proof-derived lifecycle display when no
  progress row exists, and from the final decision when the Work Unit is
  terminal.
- The sync path performs no GitHub Issue close/open, Discord semantic publish,
  source artifact, claim, evidence, or decision mutation.

Operational enablement still requires a real GitHub Project, text-compatible
fields, a local field-id map, and `gh auth refresh -s project` on the runner.
Public v1 setup should make this a foreground setup/preflight check: confirm
that the field map is apply-ready, the `gh` token has Project scope, Work Cards
are GitHub Issue or PR URLs, and audit/log paths are writable. The check may
print next steps, but it must not create Projects, grant scopes, add fields, or
mutate Project items on the user's behalf. Do not install a long-lived daemon
or use LLM interpretation in the sync path.
