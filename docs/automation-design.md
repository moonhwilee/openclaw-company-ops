# Company Ops Automation Design

Status: future design, not implemented

This document records a future Company Ops automation path for GitHub issue
intake and Project revise/blocked recovery. It is a design contract for later
implementation, not a runtime commitment.

The design intentionally preserves the current Company Ops source model:
source artifacts remain authoritative, while GitHub Issues, GitHub Projects,
labels, comments, Discord, and chat are trigger or mirror surfaces.

## Purpose

Automate two owner-approved workflows without turning Company Ops into a hidden
daemon or automatic decision engine:

- GitHub issue intake into staged Work Unit candidates.
- GitHub Project `Revise` and `Blocked` recovery planning from source artifacts.

The v1 target is:

```text
GitHub issue or Project trigger
-> local one-shot scan
-> staged candidate
-> fresh intake Operations Lead review
-> Work Unit draft/handoff spec
-> owner-visible report
-> foreground owner-approved promotion
```

The v2 target may allow low-risk execution, but only in isolated
branch/worktree/PR or patch-bundle form. V2 must not apply changes directly to
`main` or mutate final source artifacts without foreground approval.

## Non-Goals

- No hidden orchestrator, long-running daemon, webhook server, or automatic
  Team Lead dispatcher in v1.
- No cron job that creates Work Units, dispatches Team Leads, closes issues,
  archives Project items, writes `decision.md`, or edits Work Unit evidence.
- No dashboard-to-source reverse import.
- No label-only recovery.
- No LLM classifier as a source of truth.
- No database-backed queue for v1.
- No automatic `main` mutation in v2.
- No direct use of dropped staged output as trusted input.

## Source And Surface Model

Authoritative Company Ops source artifacts include:

- Assignment Packet.
- Work Card source reference.
- claim state.
- `progress.jsonl`.
- `visibility-proof.jsonl`.
- Evidence & Result Record.
- Operations Lead Decision.
- closeout stage artifacts.
- `dispatch.json`.
- `closeout-delegate-wake.json`.

Trigger and mirror surfaces include:

- GitHub issue labels and issue comments.
- GitHub Project fields such as `Revise` or `Blocked`.
- GitHub Work Card queue labels.
- Discord cards and readback proof.
- Telegram owner-visible reports.

A trigger may start a scan. It must not create authority by itself.

## Design Completeness Gate

Every future automation feature must define these items before code is written:

- Artifact: exact files, schema, state directory, and authority level.
- CLI: commands, flags, dry-run behavior, JSON output, and exit codes.
- State transition: allowed states, terminal states, retry behavior, and locks.
- Owner UX: how the owner sees, approves, drops, or applies the candidate.
- Cleanup: drop, expire, archive, idempotency, and tracked-file cleanliness.
- Tests: fake-`gh`, schema validation, idempotency, cleanup, and no-mutation checks.
- Forbidden mutations: explicit operations the feature may never perform.
- Rollback: how to stop, disable, or remove output without changing source truth.

If one of these is missing, the feature is not implementation-ready.

## Implementation Plan

### Phase 0: Design Contract

Deliverable:

- This document plus later JSON schema fixtures.

Allowed writes:

- Documentation and test fixtures only.

Forbidden:

- Runtime scheduler installation.
- GitHub mutation.
- Work Unit source artifact mutation.

Completion criteria:

- The implementation plan defines deliverables, commands, writes allowed,
  forbidden actions, tests, and rollback for every phase.

### Phase 1: Project Sync Cron-Once Wrapper

Deliverable:

- A bounded foreground command such as:

```text
company-ops project-sync cron-once --sync-issue-labels --max-runtime 60 --format json
```

Implementation direction:

- Reuse existing `project-sync reconcile`.
- Keep reconcile existing-item-only.
- Use existing lock and audit log.
- Emit stable JSON status for cron/launchd.
- Do not create missing Project items.

Allowed writes:

- Existing Project item field updates.
- Managed issue queue label convergence.
- Project sync audit log.

Forbidden:

- Work Unit creation.
- Team Lead dispatch.
- Issue close/reopen/archive.
- Work Unit source artifact mutation.
- Dashboard state interpreted as source truth.

Tests:

- Lock contention.
- Auth failure.
- GitHub rate limit.
- Readback mismatch.
- Changed-only writes.
- Missing Project item skip.
- Managed label convergence.

Rollback:

- Disable the scheduled caller.
- Leave audit log as diagnostic history.

### Phase 2: Candidate Lifecycle Core

Deliverable:

- A foreground issue candidate command family such as:

```text
company-ops github issue-inbox scan --dry-run
company-ops github issue-inbox stage
company-ops github issue-inbox list
company-ops github issue-inbox show <candidate-id>
company-ops github issue-inbox drop <candidate-id> --reason <reason>
company-ops github issue-inbox expire
```

Staging root:

```text
~/.openclaw/state/openclaw-company-ops/intake/
```

Candidate states:

```text
new -> staged -> reported -> approved -> promoting -> promoted
staged/reported -> dropped
staged/reported -> expired
new -> invalid
new -> blocked
```

Required candidate files:

- `candidate.json`: canonical machine-readable candidate.
- `summary.md`: owner/Operations Lead review summary.
- `source-snapshot.json`: GitHub issue title/body/labels/comments snapshot and hashes.
- `policy-report.json`: risk, autonomy, blockers, and manual-required findings.
- `promotion-preview.md`: planned Work Unit draft/handoff preview.

Allowed writes:

- Non-authoritative candidate files under the staging root.
- Intake audit jsonl under local state.

Forbidden:

- Writes under `docs/work-units/`.
- `work-unit create`.
- `work-unit handoff`.
- `work-unit start`.
- `work-unit dispatch`.
- GitHub issue mutation in v1.

Tests:

- Schema validation.
- Duplicate idempotency.
- Malformed issue body.
- Path traversal rejection.
- Symlink rejection.
- Absolute path rejection.
- `.git` path rejection.
- Script/path injection rejection.
- No tracked repo files changed after scan/stage/drop/expire.

Rollback:

- Drop or expire staged candidates.
- Remove the local staging root after confirming no promoted candidates depend
  on it.

### Phase 3: Candidate Policy And Review UX

Deliverable:

- A policy gate that classifies each candidate as one of:

```text
dry-run
stage-only
promotable
manual-required
blocked
invalid
```

Required policy fields:

- `risk`: `low`, `medium`, `high`, or `manual-required`.
- `autonomy`: candidate handling mode.
- `source_type`: `github-issue` or `project-recovery`.
- `allowed_paths`.
- `forbidden_paths`.
- `forbidden_mutations`.
- `required_checks`.
- `owner_approval_required`.
- `idempotency_key`.
- `source_hash`.
- `intake_version`.

Owner review surfaces:

- Telegram summary report.
- `issue-inbox list`.
- `issue-inbox show <candidate-id>`.
- Candidate file inspection.

Forbidden:

- Treating the policy report as Work Unit evidence.
- Treating LLM risk classification as final authority.

Tests:

- Manual-required label handling.
- Agent-hold label handling.
- Missing repo allowlist.
- Missing required issue fields.
- Ambiguous scope.
- High-risk path classification.

### Phase 4: Promotion Dry-Run Preview

Deliverable:

```text
company-ops github issue-inbox promote <candidate-id> --dry-run
```

Implementation direction:

- Convert the candidate into a `work-unit draft-handoff --dry-run` spec.
- Generate a Work Unit draft/handoff preview only.
- Do not create a Work Unit or publish visibility.

Allowed writes:

- Candidate-local promotion preview updates.

Forbidden:

- Work Card creation.
- Assignment Packet creation under the active Work Unit root.
- Discord publish.
- Project mutation.
- Team Lead dispatch.

Tests:

- Valid candidate converts to draft-handoff preview.
- Dropped/expired/invalid candidate cannot promote.
- Source hash mismatch blocks promote.
- Missing required fields blocks promote.

### Phase 5: Foreground Owner-Approved Promotion

Deliverable:

```text
company-ops github issue-inbox promote <candidate-id> --publish
```

Required preconditions:

- Candidate is `approved`.
- Source hash still matches.
- Owner approval source is recorded.
- Dry-run preview has passed.
- Work Unit capacity is available if dispatch is requested.

Allowed writes:

- Work Unit source artifacts through official foreground Work Unit commands.
- Optional owner-approved GitHub comment/label that links the new Work Unit.

Default:

- Create/handoff only.
- `start` and `dispatch` require explicit separate approval or a later accepted
  policy gate.

Forbidden:

- Cron-initiated promotion.
- Promotion from dropped, expired, invalid, or source-mismatched candidates.
- Silent dispatch.
- Direct Project final-status mutation.

Tests:

- Approval required.
- Source hash revalidation.
- Capacity gate.
- Duplicate promotion idempotency.
- Failed publish leaves recoverable candidate state.

Rollback:

- If not promoted, drop the candidate.
- If promoted, normal Work Unit source artifacts remain authoritative and are
  not deleted by dropping the candidate.

### Phase 6: Project Revise/Blocked Recovery Candidates

Deliverable:

```text
company-ops recovery-candidate scan --dry-run
company-ops recovery-candidate stage
```

Implementation direction:

- Reuse the candidate lifecycle core.
- Use `source_type: project-recovery`.
- Treat Project `Revise` and `Blocked` as triggers only.
- Reread source artifacts before staging.

Required source reads:

- `decision.md`.
- closeout stage artifacts.
- blocker source.
- evidence.
- claim/status summary.
- proof/progress logs where relevant.

Allowed outputs:

- Recovery candidate.
- Mirror drift report.
- Owner-visible summary.

Forbidden:

- Restarting a Work Unit from dashboard status alone.
- Rewriting `decision.md`.
- Creating follow-up WU without owner approval in v1.
- Auto-resolving owner-input, credential, legal, cost, or external blockers.

Tests:

- Dashboard trigger with missing source blocks.
- Mirror drift detected without new WU candidate.
- Real revise follow-up staged.
- Owner-needed blocker reported as manual-required.
- Blocker source missing blocks.

### Phase 7: Local Schedule Binding

Deliverable:

- Optional launchd/cron setup guide.
- No scheduled job installed by default.

Example schedule intent:

```text
*/5 * * * * company-ops github issue-inbox stage --limit 20 --max-runtime 60 --format json
*/5 * * * * company-ops project-sync cron-once --sync-issue-labels --max-runtime 60 --format json
```

Scheduling rules:

- Start with one-shot commands only.
- Install schedule only after Phase 1 through Phase 6 tests pass.
- Default interval: 5 minutes.
- Minimum interval: 3 minutes unless explicitly approved.
- Each command has its own lock.
- Stale lock is reported, not automatically deleted.
- Auth/rate-limit/schema failures write audit and owner-visible failure report.

Forbidden:

- Installing launchd/cron during package setup without explicit approval.
- Scheduler that performs promotion or dispatch.
- Scheduler that rewrites source artifacts.

Tests:

- Cron environment path handling.
- Missing `gh` auth.
- Lock already held.
- Timeout.
- No mutation beyond allowed local staging or mirror writes.

### Phase 8: V2 Low-Risk Isolated Execution

Deliverable:

- Low-risk candidate automation that may execute work only in isolation.

Allowed execution forms:

- Branch.
- Worktree.
- Draft PR.
- Patch bundle.

Forbidden:

- Direct `main` mutation.
- Direct close/merge.
- Direct source artifact final decision.
- Applying dropped output.

Apply/drop UX:

- `apply`: foreground owner-approved command.
- `drop`: close draft PR or delete local worktree/branch after cleanliness
  checks.

Required verification:

- Tests declared by candidate policy.
- `git status` cleanliness check.
- Patch/PR summary.
- Drop leaves tracked source files unchanged.

## Label Vocabulary

Inbound trigger labels:

- `company-ops-intake`.
- `agent-ready`.
- `agent-dry-run`.

Hold or manual labels:

- `agent-hold`.
- `manual-required`.
- `owner-input-required`.

Managed mirror labels must stay separate from trigger labels. Queue labels such
as `working`, `done`, `blocked`, or `revise` are derived mirror labels and must
not be used alone as intake authority.

## Idempotency

Issue intake idempotency key:

```text
repo
issue_number
trigger_labels
issue_updated_at
issue_body_sha256
issue_comment_cursor_or_hash
intake_version
```

Project recovery idempotency key:

```text
work_unit_id
project_item_id
trigger_status
decision_sha256
evidence_sha256
closeout_stage_hash
recovery_version
```

Dropped candidates suppress recreation for the same idempotency key. If the
source changes, a new candidate may be staged with a new key.

## Drop And Expire Protocol

`drop` is a required first-class command, not a manual file deletion.

Drop must:

- Mark the candidate `dropped`.
- Record reason, actor, timestamp, source hash, and previous state.
- Move it out of the active pending set, preferably to `archive/dropped/`.
- Prevent same-key restaging.
- Verify tracked repo files are unchanged.

Expire must:

- Mark stale pending candidates `expired`.
- Keep enough metadata to explain why the candidate is no longer active.
- Never delete promoted Work Unit artifacts.

Physical deletion may be a later maintenance command, but it must not be the
normal drop path because operators need to understand why an issue did not
reappear.

## Cron/Poller Spec

The scheduler is an operating binding around one-shot commands, not an
independent service.

Required fields:

- command.
- interval.
- max runtime.
- lock file.
- audit log.
- JSON output path or log path.
- failure reporting rule.
- allowed writes.
- forbidden writes.
- idempotency key.
- auth requirements.

Default policy:

- stage-only for issue intake.
- mirror-only for Project sync.
- no promotion.
- no dispatch.
- no close/archive/reopen.
- no source artifact mutation.

## Acceptance Criteria

- Dry-run performs no mutation.
- Stage writes only non-authoritative local candidate files.
- Drop and expire remove candidates from active pending views.
- Same source does not create duplicate active candidates.
- Changed source can create a new candidate.
- Cron one-shot respects lock and timeout.
- Cron one-shot never promotes or dispatches.
- Project recovery blocks when source artifacts are missing.
- Dashboard/label state alone never creates a Work Unit.
- Promotion revalidates source hash and owner approval.
- V2 drop leaves the repo clean.
- Fake-`gh` tests cover auth failure, rate limit, malformed JSON, readback
  mismatch, label convergence, and no-create-missing behavior.

## Future Implementation Memory

When this design is implemented later, start with Phase 0 and Phase 1. Do not
skip directly to issue polling or scheduler installation. The safest first code
slice is the bounded `project-sync cron-once` wrapper because it reuses existing
source-derived Project sync logic and does not introduce a new source surface.
