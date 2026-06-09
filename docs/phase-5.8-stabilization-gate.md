# Phase 5.8 Stabilization Gate

Status: distribution-critical Phases 5.8.7 through 5.8.9 implemented in
repo-local and controlled smoke. Phase 5.8.8 adds final GitHub Work Card
summary visibility before Phase 6 packaging. Phase 5.8.9 adds Discord
Progress display cleanup; it improves long-work readability without changing
source/proof semantics.
Phases 5.8.1 through 5.8.6 are implemented and live-verified, but the
`WU-260609-958` live gate exposed a final packaging blocker: verify/fix
authority boundaries and live dashboard convergence must be enforced as
protocol invariants, not operator judgment. The current code includes canonical
start/result-ready guards, closeout lifecycle convergence, source-backed
detached dispatch, fail-closed OpenClaw runtime adapter delivery, fresh
Work Unit-specific Team Lead sessions, conservative capacity policy,
result-ready closeout delegate wake, guarded closeout `--commit-request`, and
resumable closeout publish staging. Phase 5.8.5 live testing also added
duplicate RESULT_READY suppression and closeout delegate replay-safe
idempotency. Phase 5.8.6 added delegated closeout authority and expanded
negative smoke coverage. Phase 5.8.7 closes the verify-only boundary, Project
readback, and public-install preflight gaps as repo-local command/protocol
guards. Phase 5.8.8 closes the remaining GitHub Work Card inspection gap: a
maintainer must be able to read the final result summary from the Work Card
itself without following every source artifact link. Phase 5.8.9 makes
long-running checkpoint visibility read as Progress to operators while keeping
the internal proof event contract stable. Live OpenClaw delivery still requires configured adapter
commands for dispatch and closeout delegate wake; if a required adapter is
missing or cannot return current proof, the command returns `setup-needed` or
`repair-needed` and writes no false source success.

Phase 5.8 captures the live workflow issues found during the
`WU-260608-001` through `WU-260608-004` test batch, the follow-up 5.8.5 live
gate, and the 5.8.6 delegated closeout live gate. Phase 6 Packaging /
Public v1 must wait for owner acceptance of the Phase 5.8.7
boundary/convergence implementation and the Phase 5.8.8 GitHub Work Card final
result visibility boundary, unless a no-go/defer decision is explicitly
recorded.

This gate is not a feature expansion. It stabilizes the Work Unit runtime
contract that Phase 6 packaging depends on.

Capacity sizing for detached Work Unit dispatch is governed by
[`docs/capacity-policy.md`](capacity-policy.md). This phase may require that
policy, but the policy itself is a general Company Ops operating rule rather
than a Phase 5.8-only decision.

## Why This Gate Exists

The initial live test batch showed that the repository had strong source artifact,
visibility, result-ready, and closeout tooling, but lacked a complete runtime
path for detached Team Lead execution and post-result-ready closeout wake. The
5.8.1-5.8.4 implementation covered those repo-local gaps, and 5.8.5 proved the
full path with a no-bypass live regression gate before packaging.

Observed mismatch:

- The operating model says sizeable `goal` and `verify` work becomes a
  detached Work Unit.
- The current repo-local workflow can create Work Cards, Assignment Packets,
  claims, visibility cards, result-ready records, and closeout decisions.
- The workflow must prove that the Operations Lead can assign the Work Unit,
  record the handoff/start/dispatch, return idle while a fresh Team Lead
  session owns execution, then rely on result-ready delegate wake and guarded
  closeout for final convergence.

Before this gate, Phase 6 packaging would have risked shipping a protocol that
only passed local smoke and expert-assisted repair paths.

The 5.8.6 delegated closeout live gate exposed one more public-v1 risk: a
small verify Work Unit can accidentally become a combined verify/fix/hardening
run, and local closeout stage flags can report success while a configured
GitHub Project dashboard remains at `Result Ready`. For distribution, those
must become command-level and smoke-tested invariants instead of relying on an
expert Operations Lead to notice and repair them.

## Evidence From Live Tests

### `WU-260608-001`

- Team Lead: `build-lab`
- Mode: `verify`
- Work Card: `#26`
- Closeout: `REVISE`
- Finding: `STARTED` was missing from the team-detail visibility trail before
  `RESULT_READY`, causing Discord proof validation to fail.
- Finding: `decision.md` recorded Revise, but status still derived current
  state from the claim as `result_ready`.

### `WU-260608-002`

- Team Lead: `revenue`
- Mode: `verify`
- Work Card: `#27`
- Closeout: `ACCEPTED`
- Finding: `STARTED` proof existed only because it was manually inserted
  during the test run, not because the canonical protocol path generated it.
- Finding: closeout left status showing claim-state `result_ready` despite an
  Accepted decision.
- Finding: closeout-generated `decision.md` had an empty Work Card field.
- Finding: the closeout lock correctly blocked a concurrent dry-run/publish
  race and allowed a later single retry.

### `WU-260608-003`

- Team Lead: `market`
- Mode: `goal`, 1 round
- Work Card: `#28`
- Closeout: `ACCEPTED`
- Finding: the same status and decision Work Card issues repeated.

### `WU-260608-004`

- Team Lead: `revenue`
- Mode: `goal`, 1 round
- Work Card: `#29`
- Closeout: `ACCEPTED`
- Finding: the same status and decision Work Card issues repeated.

## Issue Register

### P0: Detached Work Unit Dispatch Is Missing

Status: resolved and live-verified in Phase 5.8.5.

Original problem:

The Operations Lead could prepare a Work Unit and call a Team Lead, but the
repo did not yet provide a standard detached dispatch path. In the live tests,
the Operations Lead effectively held the Team Lead execution foreground session
and processed each request sequentially.

Impact:

- Owner-observable behavior does not match the Company Ops model.
- Multiple Work Units cannot be assigned and left to Team Leads cleanly.
- Phase 6 packaging would expose a protocol that still depends on manual
  operator discipline instead of a deterministic dispatch surface.

Implemented direction:

The repo now implements a minimal detached dispatch surface that:

- creates or validates the source-backed Work Unit handoff;
- records a canonical execution start;
- records the Team Lead session/job/message reference and dispatch proof;
- returns control to the Operations Lead without waiting for Team Lead result;
- leaves result submission to result-ready inbox / closeout processing.

### P0: `STARTED` Is Required But Not Standardized

Status: resolved and live-verified in Phase 5.8.5.

Original problem:

Docs and proof validation required a team-detail `STARTED` event, but the
canonical handoff/result-ready path did not generate or enforce it.

Impact:

- Proof validation can fail on normal Work Units.
- Operators can hide the defect by manually inserting `STARTED`, which makes
  live tests unreliable.
- Packaged users would have to know an internal lifecycle event that should be
  handled by tooling.

Implemented direction:

Introduce a canonical start transition as:

- `work-unit start --work-unit-id <id> --team <team> --source-ref <ref> --publish`.

The transition must update source state, publish/read back `STARTED` when live
visibility is enabled, and make result-ready publication fail closed when the
Work Unit has not started.

### P0: Closeout Does Not Finalize Lifecycle State

Status: resolved and live-verified in Phase 5.8.5.

Original problem:

Closeout wrote `decision.md` and published review/completion visibility, but
status continued to derive current state from `claim.md` as `result_ready`.

Impact:

- Operators see a Work Unit as still result-ready even after Accepted or Revise.
- Source artifacts disagree about lifecycle state.
- Dashboard/status output can mislead Operations Lead review.

Implemented direction:

Clarify and implement final lifecycle semantics:

- accepted closeout moves lifecycle to `accepted`;
- `done` is reserved for archival completion after owner inspection and Work
  Card cleanup;
- revise closeout moves lifecycle to `revision_requested`;
- blocked closeout moves lifecycle to `blocked`;
- status output must prioritize a final decision over stale claim state.

Also separate two concepts in status output:

- lifecycle state: where the Work Unit is in the protocol;
- responsibility state: who currently owns the next action.

### P1: Closeout Decision Loses Work Card Reference

Status: resolved in code; keep in Phase 5.8.5 regression coverage.

Original problem:

Closeout-generated `decision.md` can render an empty Work Card field even when
the Assignment Packet, claim, and evidence records contain the Work Card URL.

Impact:

- The final decision artifact loses a key audit link.
- Project/dashboard reconciliation and owner inspection become harder.
- A Work Card could be accepted without a complete decision backlink.

Implemented direction:

Make closeout rehydrate Work Card from canonical source artifacts in this
order:

1. assignment packet;
2. claim;
3. evidence/result record;
4. existing decision draft.

If no Work Card can be found, closeout should warn or fail closed before
publishing an accepted decision.

### P1: Status Model Mixes Lifecycle And Responsibility

Status: resolved in code; keep in Phase 5.8.5 regression coverage.

Original problem:

Current status output treats claim expected state as the Work Unit current
state. That conflates a Team Lead's last responsibility claim with the final
Operations Lead decision.

Impact:

- Accepted or Revise decisions can look unfinished.
- Pulse, dashboard, and owner inspection can read the wrong operating signal.

Implemented direction:

Expose lifecycle and responsibility separately. At minimum, final decision
state must override claim state in user-facing status.

### P2: Live Test Mode Allowed Manual Bypass

Status: resolved by Phase 5.8.5 live no-bypass gate.

Problem:

After `WU-260608-001` exposed missing `STARTED`, later Work Units inserted
`STARTED` manually. That produced successful proof trails but contaminated the
test of the canonical protocol path.

Impact:

- The test no longer measured whether Company Ops naturally generated the
  required lifecycle evidence.
- Repeated defects were hidden instead of reproduced.

Fix direction:

Add a no-bypass rule for live workflow tests:

- do not manually add missing lifecycle events;
- do not patch proof trails to satisfy validators;
- if the canonical path fails, record the failure and stop or continue only as
  an explicitly labeled manual-override run.

### P0: Verify Mode Can Drift Into Fix/Hardening Work

Status: open; Phase 5.8.7 blocker before Phase 6 packaging.

Problem:

The `WU-260609-958` live gate was described as a small verify run, but the
overall Operations Lead flow also patched repo code, expanded smoke coverage,
committed, pushed, and reported completion in the same run. The Team Lead Work
Unit stayed verify-scoped, but the owner-visible workflow mixed verification,
repair, hardening, and release synchronization.

Impact:

- Packaged users cannot tell whether a verify-only request is read-only.
- A defect found during verification can be silently repaired and shipped
  without a separate goal/hardening boundary.
- Latency expectations become misleading because post-accept hardening work is
  counted as verify completion time.

Fix direction:

- Make standalone `verify` read-only except for its own evidence/result
  artifacts and allowed proof/progress rows.
- If verify finds a defect, produce `revise`, `blocked`, or explicit finding
  evidence. Do not edit product/source code, commit, push, mutate final Project
  state, or run hardening work under the same verify completion claim.
- Allow fixes only in `goal`, explicit hardening, or owner-approved follow-up
  scope, and only when the Assignment Packet grants the needed mutation
  authority.
- Completion reports must distinguish `verify completed`, `defect found`,
  `fix started`, `fix accepted`, and `hardening synchronized`.

### P0: Dashboard Final Convergence Can Be Misreported

Status: open; Phase 5.8.7 blocker before Phase 6 packaging.

Problem:

The 5.8.6 live gate produced Discord `ACCEPTED` / `COMPLETED` proof, but the
GitHub Project dashboard item for Work Card #37 remained at `Result Ready`.
The closeout stage could report `project_sync_ok=true` when Project sync was
not actually attempted in the final closeout command.

Impact:

- Owner-facing dashboard visibility can disagree with source/Discord final
  state.
- Public installers may trust a false convergence flag and ship a workflow
  that looks complete in chat while dashboards remain stale.
- A configured Project mirror is treated as optional at the exact point where
  final Company Ops completion requires dashboard visibility unless explicitly
  disabled by owner decision.

Fix direction:

- Split Project sync state into `attempted`, `ok`, `not_configured`,
  `not_attempted`, and `failed` instead of treating disabled sync as OK.
- When Project sync is configured and final completion requires dashboard
  visibility, closeout must fail or leave an explicit `project-sync-needed`
  stage until live Project readback confirms the desired final fields.
- The final completion gate must compare source-derived desired Project fields
  with live GitHub Project readback. Discord/source acceptance alone is not a
  full public-v1 completion proof when Project visibility is configured.

### P1: Small Live Verify Path Pays Heavy Repeated Setup Cost

Status: open; Phase 5.8.7 should optimize after P0 boundaries are enforced.

Problem:

The 5.8.6 live gate repeated startup reads, CLI help scans, artifact rereads,
full smoke runs, commit/push synchronization, and final reporting inside one
owner-visible verify flow.

Impact:

- Small verify runs take minutes before assignment and minutes after accept.
- Useful safety checks are mixed with low-signal repetition.
- Operators cannot easily explain whether time went to verification,
  external readback, defect repair, or release synchronization.

Fix direction:

- Add a small live verify fast path with a bounded preflight and no commit/push
  synchronization.
- Keep broad smoke, commit, push, and release sync in explicit hardening or
  goal slices after the verify outcome is reported.
- Use source hashes and structured proof refs to reduce repeated full artifact
  rereads by every participant.

## Phase Breakdown

### Phase 5.8.0: Issue Register And Stabilization Gate

Scope:

- Record the live workflow issues.
- Classify P0/P1/P2 severity.
- Define the phase order and acceptance gates.

Acceptance:

- This document exists and is linked from the project docs.
- Phase 6 is explicitly blocked until P0 stabilization is complete.
- The first implementation phase has a narrow, testable scope.

### Phase 5.8.1: Lifecycle And Status Contract

Depends on:

- Phase 5.8.0.

Scope:

- Define canonical lifecycle states and responsibility states.
- Decide closeout target states for accept, revise, and blocked.
- Update docs/templates/status expectations before implementation.
- Align decision vocabulary to `accept`, `revise`, and `blocked`.
- Define status derivation precedence: final Operations Lead decision, result
  evidence/proof, claim responsibility, then assignment.
- Define integrity requirements that later phases must enforce, including
  `STARTED` before `RESULT_READY` and Work Card preservation in final
  decisions.

Canonical lifecycle states:

- `assigned`: assignment exists and execution has not started.
- `working`: Team Lead is expected to be executing or waiting inside the
  delegated work loop.
- `result_ready`: source-backed evidence is ready for Operations Lead review.
- `accepted`: Operations Lead accepted the result; owner inspection or Work
  Card cleanup may still be pending.
- `revision_requested`: Operations Lead requested revision; Operations Lead
  must replan before a new Team Lead revision assignment.
- `blocked`: required artifact, evidence, permission, context, owner input, or
  external action is missing.
- `done`: archival state after owner inspection and Work Card cleanup.

Canonical responsibility states:

- `team_lead_assigned`
- `team_lead_working`
- `operations_lead_review`
- `operations_lead_replan`
- `team_lead_revision_assigned`
- `owner_inspection`
- `owner_input_needed`
- `external_wait`
- `archived`

Acceptance:

- Docs name lifecycle and responsibility separately.
- `accepted` and `done` are explicitly separate states.
- Revise closeout defaults to `revision_requested` +
  `operations_lead_replan`, not automatic Team Lead reassignment.
- Status output contract says final decisions override stale claim state.
- Claim artifacts are documented as expected responsibility, not lifecycle
  truth or completion truth.
- Project Status follows lifecycle; responsibility appears in progress,
  blocker, or next-action fields.
- No implementation work begins with ambiguous state semantics.

### Phase 5.8.2: Start Transition And Result-Ready Guard

Depends on:

- Phase 5.8.1.

Scope:

- Implement the canonical `work-unit start` transition.
- Update claim/source state when a Team Lead starts work.
- Publish/read back `STARTED` when live visibility is enabled.
- Make result-ready fail closed when required start evidence is missing.

Acceptance:

- A Work Unit can move from assigned to working through one standard command.
- Missing `STARTED` is caught before result-ready publication.
- Proof validation passes without manual lifecycle event insertion.
- Dry-run start/result-ready paths do not mutate source artifacts, visibility,
  Project mirrors, or owner reports.

### Phase 5.8.3: Closeout Finalization And Decision Rehydration

Depends on:

- Phase 5.8.1.
- Phase 5.8.2.

Scope:

- Make closeout update lifecycle/status consistently.
- Make closeout rehydrate Work Card references.
- Keep closeout lock behavior unchanged.

Acceptance:

- Accepted, Revise, and Blocked closeouts no longer display as result-ready.
- `decision.md` includes the Work Card when source artifacts contain it.
- Existing closeout lock race protection still works.

### Phase 5.8.4: Detached Dispatch MVP

Depends on:

- Phase 5.8.2.
- Phase 5.8.3.

Current status:

- Implemented: `work-unit dispatch --dry-run|--publish` as the source-backed
  dispatch contract.
- Implemented: STARTED preconditions, `dispatch.json`, a `dispatched`
  `progress.jsonl` row, recoverable `session-ref` / `job-ref` recording, and
  fail-closed `setup-needed` behavior when a runtime adapter is unavailable.
- Implemented: an `openclaw-agent` runtime adapter contract that requires
  adapter-produced accepted/readback proof before source artifacts are written.
  The smoke path uses `--adapter fake`; the live path uses `--adapter command`
  or `COMPANY_OPS_DISPATCH_ADAPTER_COMMAND`.
- Live adapter note: `scripts/openclaw_dispatch_sessions_send.py` is the
  standard command adapter for OpenClaw deployments. It uses a short
  `openclaw agent --json` turn to collect accepted/readback proof from the
  target Team Lead session, then uses Gateway `sessions.send` with
  `timeoutMs=0` to enqueue the actual execution message. If that live command is
  absent, uses embedded fallback, or fails to return real Gateway proof,
  dispatch fails closed as `setup-needed`.

Scope:

- Define the minimal detach contract for Team Lead execution.
- Add a dispatcher/run surface with a fail-closed setup-needed state when a
  detached runtime adapter is unavailable.
- Record session/job/message reference and accepted proof in source artifacts
  when dispatch succeeds.
- Return Operations Lead control after assignment/start, without waiting for
  Team Lead result.

Acceptance:

- The Operations Lead can assign a Work Unit, start it, and record a detached
  execution reference without changing lifecycle state.
- The runtime adapter does not count "message sent" as success. It must receive
  accepted/readback proof from the Team Lead runtime before writing
  `dispatch.json` or appending `dispatched`.
- Live OpenClaw dispatch must prove both acceptance and execution enqueue. The
  accepted/readback envelope is the acceptance proof; the second `sessions.send`
  enqueue/run reference is the detached execution proof. The adapter must not
  wait for result-ready or closeout.
- The Team Lead execution reference is recoverable from source artifacts.
- Result submission still goes through result-ready inbox and closeout.
- The implementation does not introduce a hidden orchestrator, daemon,
  automatic recovery, automatic reassignment, or automatic completion.

### Phase 5.8.4d: Busy Team Lead Dispatch Reliability Gate

Depends on:

- Phase 5.8.4b runtime adapter and dispatch proof hardening.

Current status:

- Live busy-session experiment completed on 2026-06-09 KST.
- Implemented as a dispatch policy/regression gate: prefer fresh
  Work Unit-specific Team Lead sessions, bound adapter waits, and fail closed
  without source mutation when acceptance cannot return current proof.
- Implemented: `openclaw-agent` dispatch uses the derived fresh
  Work Unit-specific session key by default and rejects custom/shared session
  keys unless the operator passes `--allow-custom-session-key`.
- This phase is needed because detached dispatch proof hardening prevents false
  success, but it does not by itself make shared busy Team Lead sessions an
  acceptable dispatch target.

Problem:

- A Team Lead session may already have an active run when Operations Lead tries
  to dispatch the next Work Unit.
- Live evidence showed that a same-session acceptance turn can remain queued
  behind active work, outlive the Operations Lead adapter timeout, and later run
  as a follow-up acceptance response.
- `sessions.describe` / `sessions.list` can be used as diagnostics, but they are
  snapshots rather than a lease or lock. They must not be treated as dispatch
  proof.
- A late acceptance response must not be able to rewrite source truth or turn a
  failed dispatch into success without fresh validation.

Goal:

- Fix the busy Team Lead dispatch policy with live evidence and regression
  coverage before packaging the workflow.
- Keep the Operations Lead nonblocking while preserving receipt-first,
  fail-closed source truth.
- Choose the smallest safe policy for busy Team Lead handling.

Required boundary:

- Do not add a background worker, polling daemon, retry loop, hidden queue, or
  hidden orchestrator.
- Do not record `dispatched` unless accepted/readback proof and execution enqueue
  proof are both real and current.
- Treat idle/busy preflight as advisory only unless OpenClaw later provides a
  documented lock/lease contract.
- Use fresh Work Unit-specific Team Lead sessions as the default dispatch
  target. Do not route new dispatches through a known shared busy Team Lead
  session unless the operator explicitly allows a custom session key.
- Bound acceptance/adapter waits. If the current proof does not arrive within
  that bound, fail closed as `setup-needed` and write no `dispatch.json` or
  `dispatched` progress row.

Live findings:

- Idle baseline dispatch to a Team Lead session succeeded and wrote
  `dispatch.json` only after acceptance and execution enqueue proof.
- Dispatch to a busy same-session Team Lead failed closed through the bounded
  adapter path. It wrote no `dispatch.json` and appended no `dispatched` row.
- After the active run completed, OpenClaw processed the earlier same-session
  acceptance prompt as a later run. That late acceptance remained session
  history only and did not mutate Company Ops source truth.
- Dispatch to a fresh Work Unit-specific Team Lead session succeeded while
  another same-agent session was still busy.
- `sessions.describe` and `sessions.list` showed useful status snapshots, but no
  queue-depth, lock, or lease contract strong enough to gate dispatch success.

Acceptance:

- A busy Team Lead scenario cannot leave `dispatch.json` or `progress.jsonl`
  claiming success without real current proof.
- A late or fallback acceptance cannot become dispatch success after the adapter
  path has failed closed.
- The Operations Lead is bounded by the adapter timeout rather than held
  indefinitely by a busy Team Lead receipt wait.
- Fresh Work Unit-specific Team Lead sessions are the default recommended live
  dispatch path.
- A custom/shared session key requires explicit operator override and is recorded
  as `operator-specified`.
- The chosen policy is covered by smoke/regression tests and the live
  busy-session experiment record.
- The implementation still has no hidden orchestrator, daemon, automatic retry,
  automatic reassignment, or automatic completion path.

### Phase 5.8.4.c: Result-Ready Wake / B-Prime Closeout Review

Depends on:

- Phase 5.8.2.
- Phase 5.8.3.
- Phase 5.8.4b runtime adapter, once implemented.
- Phase 5.8.4d busy Team Lead dispatch reliability gate.

Current status:

- `5.8.4c-1` wake foundation is implemented: foreground
  `result-ready --publish` can request a fresh Work Unit-scoped closeout
  delegate wake after successful RESULT_READY publish/readback, and
  `work-unit delegate-wake` provides a source-backed foreground recovery path.
- `5.8.4c-2` guarded closeout commit request is implemented: existing
  `work-unit closeout` accepts structured delegate `--commit-request` JSON,
  revalidates current RESULT_READY proof/source hashes/manual-required policy,
  records a narrow closeout stage file during publish, and can foreground-resume
  the same guarded closeout after partial visibility publish failure without
  writing final `decision.md` early.
- The B-prime design baseline remains: the fresh closeout delegate may judge
  the Work Unit, but final decisions are applied only through the guarded
  closeout path.
- This phase is needed because detached dispatch solves Operations Lead
  foreground blocking, but it does not by itself wake the Operations Lead when a
  Team Lead later publishes `result-ready`.

Problem:

- Phase 5.8.4b should let the Operations Lead dispatch work and return idle.
- A detached Team Lead can still publish checkpoints and `result-ready` through
  source-backed Team Lead surfaces.
- However, final `accept`, `revise`, `blocked`, owner completion, and Project
  final status are Operations Lead decisions. Without a wake/notification layer,
  owner-visible status can remain at `Result Ready` until the Operations Lead
  explicitly checks the inbox.

Goal:

- Preserve the nonblocking Operations Lead model while restoring real-time-ish
  completion visibility for owners.
- Make `result-ready --publish` create source-backed review visibility and
  enqueue a fresh closeout delegate session without waiting for final closeout.
- Let the fresh `main` closeout delegate perform source-backed review, including deep review for
  broad code changes or multi-WU dependencies, while preserving fail-closed
  red-line/manual review boundaries.
- Apply final `accept`, `revise`, or `blocked` decisions only through a single
  guarded closeout commit path.

Required boundary:

- Team Lead authority may produce `CHECKPOINT` and `RESULT_READY` visibility.
- Operations Lead authority, including explicit `operations-lead-delegate`
  authority, remains the only path to `ACCEPTED`, `REVISE`, `BLOCKED_DETAIL`,
  owner-facing `COMPLETED`, `NEEDS_REVISION`, or `BLOCKED`, and Project
  final-state mutation.
- Goal/convergence internal rounds stay Team Lead-owned before `result-ready`.
  Operations Lead `revise` means post-result-ready replan/amendment, not the
  normal mechanism for Team Lead internal improvement loops.
- Team Lead waits only for `RESULT_READY` proof/readback and closeout delegate
  enqueue proof. It must not wait for delegate judgment or closeout completion.
- The fresh `main` closeout delegate may judge `accept`, `revise`, or
  `blocked`, run guarded closeout dry-run, and publish only through
  `work-unit closeout --authority-role operations-lead-delegate` when every
  red-line category is clear. It must not write `decision.md` directly, mutate
  Project final status directly, publish final Discord cards directly, archive,
  cleanup, or reassign.
- The guarded closeout path must reread source artifacts under a WU-scoped
  closeout lock, reject existing final decisions, and fail closed on stale,
  duplicate, conflicting, or hash-mismatched input.

B-prime implementation baseline:

- Trigger source: foreground `work-unit result-ready --publish` after
  successful pre-gate, live RESULT_READY publish/readback, and post-gate.
- Wake target: a fresh Work Unit-scoped closeout delegate session, not the busy
  Operations Lead foreground session.
- Delegate session key: deterministic and Work Unit-scoped, for example
  `company-ops-closeout-delegate-<work-unit-id>`.
- Delegate agent: v1 allows the configured `main` agent only. Unknown agents
  and the assigned Team Lead agent are setup-needed, not fallback routes.
- Delivery guarantee: one-shot delegate enqueue proof with recoverable session,
  message, or run refs. No background daemon, durable queue, retry worker, DB,
  hidden workflow runner, or multi-agent consensus.
- Capacity guard: closeout delegate wake has a small foreground active cap
  (default 2). Capacity-full leaves the WU recoverable in the result-ready
  inbox; it does not queue, retry, or fake closeout.
- Failure behavior: if RESULT_READY publish succeeds but delegate wake/enqueue
  fails, do not roll back RESULT_READY and do not fake closeout. Report
  `delegate-wake setup-needed` and leave the WU recoverable through
  `work-unit inbox --result-ready`.
- Suppression: already-decided, stale, duplicate, hash-mismatched, or
  conflicting Work Units must not produce a normal delegate wake. Surface them
  only as explicit repair-needed or exception states.
- Visibility mirror: Discord/GitHub Project may show `Result Ready` or
  `Review Needed` from source artifacts, but must not become source truth.

Self-contained wake payload:

- Include `work_unit_id`, title, team, artifact root, Work Card ref,
  `assignment.md`, `claim.md`, `evidence.md`, `progress.jsonl`,
  `visibility-proof.jsonl`, result-ready proof id/timestamp/source ref,
  delegate session key, guarded closeout command contract, and no-go actions.
- Include artifact hashes for `assignment.md`, `claim.md`, `evidence.md`,
  `progress.jsonl`, and the relevant `visibility-proof.jsonl` proof rows so the
  guarded closeout commit can bind delegate judgment to the source snapshot the
  delegate actually inspected.
- No-go actions must explicitly forbid direct `decision.md`, Project final
  state, Discord final review, owner completion, reassignment, archive, or
  reverse-import mutation outside guarded closeout.

Delegate autonomy classes:

- `auto_eligible`: normal verify, docs, and small code Work Units. The fresh
  delegate may accept, revise, or block through guarded closeout when evidence
  is sufficient.
- `deep_review_auto_eligible`: broad code changes, many changed files, or
  multi-WU dependencies. Size alone is not a manual-review trigger. The fresh
  delegate should increase review depth, inspect diffs/tests/dependency refs,
  and may use subagents before guarded closeout.
- `manual_required`: operating-server actions, deployment, DB migration,
  credential/auth/security boundaries, cost-bearing actions, destructive
  changes, external public release/customer impact, unclear owner intent,
  unresolved dependency, critical delegate/subagent disagreement, missing evidence, stale
  source, or hash/proof mismatch.

Guarded closeout commit request:

- Extend existing `work-unit closeout --publish`; do not build a separate
  commit system.
- Add a structured `--commit-request <json>` input so the fresh delegate does
  not synthesize arbitrary closeout CLI arguments.
- Minimum commit request fields: `work_unit_id`, `decision`, `reason`,
  `source_ref`, `result_ready_proof_id`, `artifact_hashes`, delegate
  session/run refs, `authority_role`, `delegate_agent`, `autonomy_class`,
  `review_depth`, structured `red_line_check`, and
  blocked-only fields such as `blocker_source`, `needed`, and `next_owner`.
- Before writing final state, closeout must revalidate WU id, result-ready
  proof, source refs, artifact hashes, final-decision absence, final proof
  absence, stale/duplicate/conflict status, and manual-required red lines.
- Closeout uses a small staging guard around `decision.md`, card file writes,
  Discord publishes, and Project sync so a publish failure leaves an explicit
  stage artifact instead of silently looking like a clean converged path.
- Final `decision.md` is written only after team-detail and owner-facing
  visibility publish succeed. If a same-decision closeout stage is left
  mid-publish, a foreground rerun may skip matching already-published proofs and
  continue the guarded closeout instead of requiring manual source edits.

Implementation slices:

- `5.8.4c-1` (implemented): result-ready wake foundation: self-contained wake
  payload, closeout-delegate-specific session-send adapter, enqueue proof,
  foreground `delegate-wake` recovery path, stale/duplicate suppression, and
  source-inbox recovery after wake failure. This slice deliberately does not
  add a daemon, queue, DB, retry worker, reverse-import path, or final
  auto-closeout.
- `5.8.4c-2` (implemented): B-prime guarded closeout: `--commit-request`,
  artifact hash and result-ready proof revalidation, delegate autonomy classes,
  manual-required/red-line fail-closed checks, closeout staging/resume guard,
  and final visibility/status convergence regression coverage.
- `5.8.6` (implemented in this slice): delegated closeout authority: fresh
  `main` OL delegate, role-checked guarded publish, structured red-line
  categories, closeout delegate capacity cap, Project sync recoverable
  `project-sync-needed` stage, and expanded negative commit-request smoke.

Acceptance, once implemented:

- A detached Team Lead `result-ready --publish` creates source-backed result
  visibility and fresh closeout delegate enqueue proof without requiring the Operations
  Lead to keep a foreground session open.
- The Team Lead returns after enqueue proof only. It does not wait for delegate
  judgment or guarded closeout completion.
- A wake failure leaves the WU visible in `work-unit inbox --result-ready`
  rather than dropping or rolling back source truth.
- The fresh `main` closeout delegate can restore the WU from source artifacts and may accept
  broad code or multi-WU-dependent work after deep review when no red-line
  risk or evidence gap exists.
- Red-line risk, evidence insufficiency, unresolved dependency, critical
  disagreement, stale source, or hash/proof mismatch produces
  `manual_required`, `revise`, or `blocked`, not automatic accept.
- Only guarded closeout writes final `decision.md`, team-detail final review,
  owner-facing closeout, and Project final status; direct writes by the
  delegate remain forbidden.
- Project sync failure after successful source/Discord closeout leaves an
  explicit `project-sync-needed` stage and nonzero command result rather than a
  false fully-converged publish.
- Duplicate/stale wake attempts cannot overwrite or compete with an existing
  final decision.
- Owner-facing status distinguishes `Result Ready / Review Needed` from final
  `Accepted / Needs Revision / Blocked / Done`.

Regression coverage to add:

- Wake payload self-containment and no-go boundary.
- Delegate enqueue proof success/failure, including no wake record without
  current acceptance/readback and enqueue/run refs.
- Source inbox recovery when RESULT_READY succeeds but delegate wake fails.
- Delegate wake capacity-full recovery without hidden queue/retry.
- `--commit-request` WU mismatch, stale decision, duplicate final proof,
  missing source ref, missing proof id, proof mismatch, missing hashes, missing
  delegate refs, missing review depth, artifact hash mismatch, and structured
  red-line fail-closed cases.
- Accepted, Revise, and Blocked convergence across `decision.md`, status
  lifecycle, Project dry-run status, and Discord proof rows.

### Phase 5.8.5: No-Bypass Regression Gate

Status: passed in live gate. `WU-260609-907` completed the clean acceptance
path without manual lifecycle/proof repair: handoff, STARTED, detached dispatch,
Team Lead RESULT_READY, fresh closeout-audit wake, guarded commit-request,
Operations Lead dry-run, Operations Lead publish, Discord readback, and Project
sync all converged. The same live run also produced negative coverage:

- `WU-260609-901`/`902` exposed missing closeout-audit agent setup and closeout
  role overreach, leading to explicit configured audit agents and audit-only
  commit-request authority. Phase 5.8.6 supersedes that conservative boundary
  with role-checked fresh `main` closeout delegation.
- `WU-260609-903`/`904` exposed duplicate RESULT_READY risk, leading to
  fail-closed duplicate suppression before publish.
- `WU-260609-905`/`906` exposed timestamp/hash ambiguity and proved
  `manual_required` fail-closed behavior.
- `WU-260609-907` exposed closeout-audit replay idempotency, leading to
  payload/prompt-versioned closeout delegate execution keys before the final
  accepted closeout.

Depends on:

- Phase 5.8.2.
- Phase 5.8.3.
- Phase 5.8.4.
- Phase 5.8.4d.
- Phase 5.8.4.c.

Scope:

- Rerun a small live workflow batch with manual bypass prohibited. Include at
  least one verify Work Unit and one 1-round goal Work Unit.
- Start each Work Unit only through `work-unit start --publish`; do not insert
  `STARTED` proof rows, proof-log entries, claim state, or status fields by
  hand.
- Dispatch through the fresh Work Unit-specific Team Lead path. The
  Operations Lead must return after accepted/readback plus execution enqueue
  proof, not after Team Lead result completion. Shared/custom session dispatch
  must be either rejected or explicitly marked `operator-specified`.
- Publish Team Lead `RESULT_READY` through the canonical command and request
  closeout delegate wake with the configured command adapter. If wake fails,
  record the `delegate-wake setup-needed` outcome and recover only through
  foreground `work-unit delegate-wake`; do not fake closeout.
- Close final decisions through guarded `work-unit closeout --commit-request`
  only. Cover Accepted, Revise, and Blocked or record an explicit rationale for
  any decision not exercised live.
- Verify source artifacts, Discord proof, status output, decision records, and
  Project dry-run output after each closeout.
- Include at least one partial closeout publish/resume simulation in local
  smoke or controlled fixture: team final review published, owner closeout
  initially failed, rerun skips matching team proof, publishes owner closeout,
  writes final `decision.md`, and marks the closeout stage `published`.
- Include negative cases for guarded closeout: WU mismatch, stale/existing
  decision, duplicate final proof, missing source ref, RESULT_READY proof id
  mismatch, artifact hash mismatch, `manual_required`, unclear red-line check,
  and missing delegate refs must fail closed.
- Include dispatch/wake negative cases: missing adapter command, adapter
  timeout/failure, missing accepted/readback proof, missing execution enqueue
  reference, busy/shared session timeout, and late acceptance after timeout
  must not mutate source success.
- Verify no hidden daemon, queue, DB, retry worker, Project/Discord
  reverse-import, automatic reassignment, or automatic closeout path appears in
  the tested flow.

Acceptance:

- No manual `STARTED` insertion is needed.
- Status and decision artifacts agree after closeout.
- Work Card references remain present in final decisions.
- Operations Lead does not hold Team Lead foreground execution for the tested
  detached path.
- Result-ready delegate wake either records current enqueue proof or leaves a
  visible recoverable setup-needed state without rollback or fake success.
- Guarded commit-request closeout revalidates current source proof/hash/red-line
  state and is the only writer of final `decision.md`, team-detail final
  review, owner-facing closeout, and final Project status.
- Partial publish failure is explicit and foreground-resumable with the same
  guarded request.
- Phase 6 may begin only after this gate passes or an explicit no-go/defer
  decision is recorded with rationale.

### Phase 5.8.7: Verify Boundary / Dashboard Convergence / Public Install Gate

Status: implemented in repo-local command/protocol guards and controlled smoke;
awaiting owner acceptance before Phase 6 packaging.

Depends on:

- Phase 5.8.5.
- Phase 5.8.6.

Purpose:

Turn the 5.8.6 live-gate lessons into public-v1 invariants so another user can
install the distribution without inheriting expert-only repair habits.

Scope:

Slice A, authority boundary:

- Add structured Assignment Packet authority fields such as
  `mutation_allowed`, `allowed_paths`, `allowed_surfaces`,
  `external_mutation_allowed`, and `commit_push_allowed`.
- Default standalone `verify` to read-only for product/source code and final
  external state. Verify may create/update only its assigned evidence/result,
  progress, and proof artifacts, plus non-final visibility where the protocol
  already allows it.
- Allow `goal` and explicit hardening/fix scopes to mutate source code only
  when the Assignment Packet grants mutation authority, target paths/surfaces,
  and verification criteria.
- Record defects found during verify as `revise`, `blocked`, or explicit
  findings instead of silently patching under the verify label.
- Gate Company Ops-owned source/external mutation commands against mode and
  authority context. This is command/protocol-level fail-closed behavior, not
  an OS filesystem sandbox for arbitrary shell edits.
- Require owner-visible reports to label follow-up repair/hardening separately
  from verify completion.

Slice B, closeout/dashboard convergence:

- Add an explicit Project sync requirement state, for example
  `--project-sync-mode required|disabled` or an equivalent config-backed
  `require_project_sync`, so final closeout cannot infer that Project
  visibility is disabled merely because a field-map argument was omitted.
- Make closeout delegate wake and guarded closeout preflight require every live
  target and Project sync argument needed for final convergence when Project
  visibility is required.
- Replace ambiguous `project_sync_ok=true` with structured states such as
  `not_configured`, `not_attempted`, `attempted_ok`, `failed`, and
  `readback_mismatch`.
- Implement final desired-vs-live GitHub Project readback in
  `project_sync.py`; closeout consumes that result instead of inferring
  convergence from local stage flags or subprocess success alone.
- Treat Project item absence during final closeout as `project_item_missing` or
  `project-sync-needed`. Creation of missing Project items belongs to setup,
  handoff, or explicit foreground reconcile, not final completion.

Slice C, minimal public-install preflight:

- Add only the read-only checks needed by Slices A and B: Project field-map
  readiness, GitHub `project` scope, Project readback support, Discord target
  config, proof-log writability, adapter command presence, role context/config,
  and package/CLI availability.
- Report `OK`, `WARN`, or `BLOCKED` with JSON and human-readable output.
- Do not include broad stale-dashboard hygiene or repair automation in this
  phase; that remains Phase 6 packaging or later foreground reconcile work.

Slice D, small verify fast-path acceptance:

- Treat small verify fast-path as a policy and smoke fixture, not a new
  workflow. The path is: bounded preflight, verify evidence, report
  `accept`/`revise`/`blocked`/finding, then stop.
- Avoid repeated CLI help scans, broad smoke, commit, push, release sync, or
  repair unless a separate hardening/fix slice is explicitly opened.

No-go boundaries:

- Do not turn the Project dashboard into source truth. It remains a mirror, but
  a required mirror must be read back before final public-v1 completion is
  claimed.
- Do not auto-create Projects, grant scopes, bind Discord targets, start
  daemons, install cron, archive items, or repair external resources from the
  setup/preflight helper.
- Do not let a verify-only Work Unit start product/source edits, commits,
  pushes, final closeout, or Project final mutation under a verify completion
  label.
- Do not hide a verify defect by immediately patching it unless the current
  Work Unit is explicitly converted through an owner-approved goal/hardening
  boundary.
- Do not claim universal protection against arbitrary shell edits. The v1
  boundary is the package's command/protocol authority guard plus evidence and
  dirty-state checks where the workflow owns them.
- Do not silently create missing Project items during final closeout. Missing
  final dashboard membership is a setup/reconcile problem, not a reason to
  claim completion.
- Do not add a background reconciler, retry queue, or hidden dashboard repair
  runner.

Acceptance:

- Assignment Packet rendering and validation include structured mutation
  authority fields; standalone verify defaults to mutation denied.
- A verify-only fixture that attempts Company Ops-owned product/source edits,
  commits, pushes, final Project mutation, or code hardening fails closed
  before mutation.
- A goal/hardening fixture with explicit mutation authority can patch and
  verify; the same fixture without mutation authority fails closed.
- Closeout with Project visibility required but missing field-map, live targets,
  Project args, or readback support fails before publishing a false
  fully-converged completion.
- Closeout with Project sync disabled reports `not_configured` or
  owner-approved dashboard no-go, not `ok`; closeout with no attempted sync
  reports `not_attempted`.
- A live-readback or controlled mock fixture proves final Project fields match
  source-derived desired `Accepted`, `Needs Revision`, or `Blocked` state before
  final completion is claimed.
- A final closeout fixture with a missing Project item reports
  `project_item_missing` or `project-sync-needed` instead of auto-creating the
  item and claiming convergence.
- Distribution preflight reports missing Project field map, missing GitHub
  `project` scope, missing Discord targets, unwritable proof logs, missing
  adapters, and missing role context as `WARN` or `BLOCKED` with next steps,
  without creating or mutating resources.
- Small verify fast-path smoke completes without full smoke, commit, push, or
  release sync, and reports any discovered defect as a separate next action.
- Owner-visible reporting tests or examples show an immediate accepted/interim
  report when follow-up hardening continues after acceptance.

### Phase 5.8.8: GitHub Work Card Final Result Visibility

Status: implemented in repo-local and controlled smoke; awaiting owner
acceptance before Phase 6 packaging.

Depends on:

- Phase 5.8.7.

Purpose:

Make every accepted, revise, or blocked Work Unit inspectable from its GitHub
Work Card by adding exactly one source-backed final result summary comment.
The comment is a maintainer visibility mirror for owner inspection. It must
never become source truth or a status derivation input.

Scope:

Slice A, source-backed decision-ready summary:

- Require the Team Lead's submitted source artifacts to contain a concise,
  human-readable decision-ready summary before `RESULT_READY` can be accepted
  for closeout. The primary source is the Evidence & Result Record `Result
  Summary`, backed by verification, remaining risks, and done-criteria mapping.
- Reject missing, placeholder, template-like, or low-information summaries in
  the result-ready or closeout readiness gate.
- Do not generate the final GitHub comment from Discord text, Telegram text,
  free-chat session summaries, GitHub Project fields, labels, or comments.

Slice B, deterministic Work Card summary comment:

- Add an explicit Work Card summary visibility mode such as
  `--work-card-summary-mode required|disabled`.
- Default live GitHub Work Card closeout should use `required` once this phase
  is implemented and enabled. `disabled` is only for local smoke, non-GitHub
  Work Cards, private/no-GitHub deployments, or an owner-approved no-go where
  GitHub Work Card comments are intentionally unavailable.
- Render a bounded deterministic comment from current source artifacts:
  Assignment Packet identity, Evidence & Result Record summary, Operations Lead
  Decision, verification summary, remaining risks, next action, and source
  artifact links.
- Use one canonical hidden marker, for example
  `<!-- company-ops-work-card-summary:<WU>:v1 -->`, to create or update exactly
  one managed summary comment. Never edit "the latest comment" by position and
  never create repeated summary spam on closeout retry.
- The comment must state that source artifacts remain the source of truth.

Slice C, guarded closeout integration:

- The guarded closeout path owns final GitHub summary comment mutation. A
  closeout delegate may request or call the guarded closeout path, but it must
  not write the Work Card comment outside that path.
- On dry-run, render and report the planned comment without mutating GitHub.
- On publish with summary mode `required`, create or update the managed comment,
  read it back, and record the comment id/url or failure state in the closeout
  stage/proof.
- If the source decision publishes but the required comment or readback fails,
  do not roll back the source decision. Leave the closeout stage in an explicit
  visibility state such as `work-card-summary-needed`, return nonzero, and do
  not report fully converged completion.

Slice D, public-safety and non-truth guarantees:

- Redact or omit raw logs, secrets, tokens, private absolute paths, Discord
  internals, long diffs, and overly long evidence text from GitHub comments.
- Keep comments bounded and maintainer-readable. The default implementation
  must not make an extra LLM call; if LLM-polished summaries are ever added,
  they require an explicit opt-in phase and must still be source-backed.
- Inbox, status, closeout readiness, and dashboard derivation must never read
  GitHub comments as source truth.
- Do not add a daemon, background reconciler, hidden retry queue, automatic
  archive, label automation, or GitHub issue body rewrite in this phase.

Acceptance:

- `RESULT_READY` or closeout readiness rejects missing, placeholder, or
  low-information decision-ready summaries.
- Dry-run renders a deterministic final Work Card summary comment without
  GitHub mutation.
- Publish with a GitHub Work Card and summary mode `required` creates or updates
  exactly one marker-managed comment, reads it back, and records the comment
  reference in source closeout proof.
- Retrying the same closeout updates or no-ops the managed comment without
  duplicate summary comments.
- Required mode with a non-GitHub Work Card, missing Work Card URL, GitHub auth
  failure, or readback mismatch fails as `work-card-summary-needed` or an
  equivalent explicit state instead of silently reporting completion.
- Disabled mode reports `not_configured` or an owner-approved no-go, not `ok`.
- Smoke fixtures cover accept, revise, and blocked comment rendering.
- Smoke fixtures prove comments are never consumed by status, inbox, Project
  sync, result-ready, or closeout decision derivation.
- Active-path scans show no legacy or fallback comment formats.

### Phase 5.8.9: Discord Progress Update Display

Status: implemented in repo-local and controlled smoke; P1
visibility/readability cleanup.

Depends on:

- Phase 5.8.8.

Purpose:

Make long-running Work Unit progress easier to inspect in Discord by rendering
operator-facing progress cards as `PROGRESS` updates, while preserving the
existing internal checkpoint event contract. This phase is a display-layer
cleanup, not a new state machine, dashboard truth source, or CLI rename.

Scope:

Slice A, two-line progress card layout:

- Render checkpoint visibility cards with a short, stable header:
  `🧭 [PROGRESS] WU-<id> · 🧪 <team>`.
- Put the actual progress detail in the first body line by reusing the same
  deterministic display string that feeds the dashboard `Progress` field:
  `Progress: <rendered_progress_summary>`.
- Build `<rendered_progress_summary>` from source progress fields in the
  existing order: optional goal/convergence round, optional phase index/total,
  then `current_slice` or `phase`. Examples:
  - `Progress: positioning note`;
  - `Progress: 1/3 · positioning note`;
  - `Progress: R1 · 1/3 · positioning note`.
- Do not move round or phase count into the header for this phase. Keep the
  header stable and put the dashboard-style Progress text in the body.
- Treat `phase`, `current_slice`, round, and phase count as display inputs, not
  parser inputs. Round and phase count are optional; do not fabricate them when
  a Work Unit only has a current slice. Round display is suppressed outside
  round-based `goal` or `convergence` work even if a stale/provided
  `show_round` flag is present.

Slice B, icon and clamping rules:

- Use one leading icon:
  - `🧭` for normal progress;
  - `⚠️` for at-risk or blocked progress;
  - `🔄` for retry or re-run progress.
- If more than one condition applies, choose the leading icon by priority:
  `⚠️` > `🔄` > `🧭`.
- Keep retry/re-run progress visually distinct from closeout revision events
  such as `🔁 [REVISE]`.
- Clamp the slice/phase label inside the rendered progress summary to roughly
  24-32 display characters, keep the full progress detail around 40 characters
  when possible, and keep the header under roughly 55-60 UTF-16 code units so
  mobile Discord does not push Work Unit id and team out of view.

Slice C, structured proof and readback:

- Card titles are display-only. Do not parse title text to recover lifecycle
  state or progress semantics.
- Preserve structured fields in the card/proof row: `work_unit_id`, `team`,
  `mode`, `round`, `show_round`, `phase`, `phase_index`, `phase_total`,
  `current_slice`, `risk_state`, `retry_state`, `rendered_title`,
  `rendered_progress_summary`, and `clamp_version`.
- Readback may match the rendered title/header, but status and Project
  derivation must continue to use source artifacts and structured fields.

Slice D, internal contract boundary:

- Keep internal `card.kind = CHECKPOINT`, proof lifecycle event `CHECKPOINT`,
  CLI command `work-unit checkpoint`, and progress row
  `transition_kind = checkpoint` in this phase.
- Do not hard-rename `work-unit checkpoint` to `work-unit progress`; an existing
  `work-unit progress` command already has a different metadata-append meaning.
- Do not rename `transition_kind=checkpoint` to `progress`, do not rewrite
  historical artifacts, and do not add compatibility aliases or fallback
  readers.
- Documentation and help text may describe this as: the internal checkpoint
  event publishes a user-facing Progress update.

Acceptance:

- `discord_ops.py card --kind CHECKPOINT` or equivalent renderer smoke shows a
  user-facing `PROGRESS` header using the two-line layout.
- `work-unit checkpoint --dry-run --format json` still emits internal
  `card.kind == CHECKPOINT` and `progress_row.transition_kind == checkpoint`.
- Lifecycle/proof sequence validation still accepts
  `STARTED -> CHECKPOINT -> RESULT_READY`.
- Project `Progress` derivation continues to use source `progress.jsonl`; proof
  rows preserve the rendered fields as readback receipts, not as a new source of
  truth.
- Smoke expectations are updated for the rendered Progress header.
- Active-path scans prove this phase introduced no aliases, fallback readers,
  hard-renamed checkpoint commands, or historical artifact rewrites.

## Phase 6 Blocker Rule

Reopened by the Phase 5.8.6 live gate, implemented through Phase 5.8.7, and
extended by the Phase 5.8.8 Work Card final-result visibility boundary. Phase 6
packaging must not begin until the owner accepts the 5.8.7
boundary/convergence implementation and the 5.8.8 GitHub Work Card visibility
boundary, or explicitly records a no-go/defer decision with rationale for each
P0 boundary.

Historical rule:

- Phase 5.8 P0 items are resolved;
- Phase 5.8.5 passes without manual bypass; and
- any remaining P1/P2 items are either fixed or explicitly deferred with
  owner-approved rationale.

This prevents Public v1 from packaging a workflow that only works when an
expert operator manually repairs lifecycle and proof gaps.
