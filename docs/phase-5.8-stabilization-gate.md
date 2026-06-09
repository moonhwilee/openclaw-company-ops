# Phase 5.8 Stabilization Gate

Status: complete stabilization gate before Phase 6. Phases 5.8.1 through 5.8.5
are implemented and live-verified. The current code includes canonical
start/result-ready guards, closeout lifecycle convergence, source-backed
detached dispatch, fail-closed OpenClaw runtime adapter delivery, fresh
Work Unit-specific Team Lead sessions, conservative capacity policy,
result-ready closeout reviewer wake, guarded closeout `--commit-request`, and
resumable closeout publish staging. Phase 5.8.5 live testing also added
duplicate RESULT_READY suppression and closeout reviewer replay-safe
idempotency. Live OpenClaw delivery still requires configured adapter commands
for dispatch and closeout reviewer wake; if a required adapter is missing or
cannot return current proof, the command returns `setup-needed` or
`repair-needed` and writes no false source success.

Phase 5.8 captures the live workflow issues found during the
`WU-260608-001` through `WU-260608-004` test batch and the follow-up 5.8.5
live gate. Phase 6 Packaging / Public v1 may begin after this completed gate.

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
  session owns execution, then rely on result-ready reviewer wake and guarded
  closeout for final convergence.

Before this gate, Phase 6 packaging would have risked shipping a protocol that
only passed local smoke and expert-assisted repair paths.

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
  reviewer wake after successful RESULT_READY publish/readback, and
  `work-unit review-wake` provides a source-backed foreground recovery path.
- `5.8.4c-2` guarded closeout commit request is implemented: existing
  `work-unit closeout` accepts structured reviewer `--commit-request` JSON,
  revalidates current RESULT_READY proof/source hashes/manual-required policy,
  records a narrow closeout stage file during publish, and can foreground-resume
  the same guarded closeout after partial visibility publish failure without
  writing final `decision.md` early.
- The B-prime design baseline remains: the fresh closeout reviewer may judge
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
  enqueue a fresh closeout reviewer session without waiting for final closeout.
- Let the fresh reviewer perform source-backed review, including deep review for
  broad code changes or multi-WU dependencies, while preserving fail-closed
  red-line/manual review boundaries.
- Apply final `accept`, `revise`, or `blocked` decisions only through a single
  guarded closeout commit path.

Required boundary:

- Team Lead authority may produce `CHECKPOINT` and `RESULT_READY` visibility.
- Operations Lead authority remains the only path to `ACCEPTED`, `REVISE`,
  `BLOCKED_DETAIL`, owner-facing `COMPLETED`, `NEEDS_REVISION`, or `BLOCKED`,
  and Project final-state mutation.
- Goal/convergence internal rounds stay Team Lead-owned before `result-ready`.
  Operations Lead `revise` means post-result-ready replan/amendment, not the
  normal mechanism for Team Lead internal improvement loops.
- Team Lead waits only for `RESULT_READY` proof/readback and closeout reviewer
  enqueue proof. It must not wait for reviewer judgment or closeout completion.
- The fresh reviewer may judge `accept`, `revise`, or `blocked`, but it must
  not run guarded closeout itself and must not write `decision.md`, Project
  final status, Discord final review, or owner-facing completion directly. It
  may only prepare the structured `closeout-commit-request.json` for Operations
  Lead foreground closeout.
- The guarded closeout path must reread source artifacts under a WU-scoped
  closeout lock, reject existing final decisions, and fail closed on stale,
  duplicate, conflicting, or hash-mismatched input.

B-prime implementation baseline:

- Trigger source: foreground `work-unit result-ready --publish` after
  successful pre-gate, live RESULT_READY publish/readback, and post-gate.
- Wake target: a fresh Work Unit-scoped closeout reviewer session, not the busy
  Operations Lead foreground session.
- Reviewer session key: deterministic and Work Unit-scoped, for example
  `company-ops-closeout-reviewer-<work-unit-id>`.
- Reviewer agent: must be a configured independent OpenClaw agent id. If a
  dedicated `closeout-reviewer` agent is not configured, the operator must pass
  an explicit configured reviewer agent; unknown agent ids are setup-needed.
- Delivery guarantee: one-shot reviewer enqueue proof with recoverable session,
  message, or run refs. No background daemon, durable queue, retry worker, DB,
  hidden workflow runner, or multi-reviewer consensus.
- Failure behavior: if RESULT_READY publish succeeds but reviewer wake/enqueue
  fails, do not roll back RESULT_READY and do not fake closeout. Report
  `review-wake setup-needed` and leave the WU recoverable through
  `work-unit inbox --result-ready`.
- Suppression: already-decided, stale, duplicate, hash-mismatched, or
  conflicting Work Units must not produce a normal reviewer wake. Surface them
  only as explicit repair-needed or exception states.
- Visibility mirror: Discord/GitHub Project may show `Result Ready` or
  `Review Needed` from source artifacts, but must not become source truth.

Self-contained wake payload:

- Include `work_unit_id`, title, team, artifact root, Work Card ref,
  `assignment.md`, `claim.md`, `evidence.md`, `progress.jsonl`,
  `visibility-proof.jsonl`, result-ready proof id/timestamp/source ref,
  reviewer session key, guarded closeout command contract, and no-go actions.
- Include artifact hashes for `assignment.md`, `claim.md`, `evidence.md`,
  `progress.jsonl`, and the relevant `visibility-proof.jsonl` proof rows so the
  guarded closeout commit can bind reviewer judgment to the source snapshot the
  reviewer actually inspected.
- No-go actions must explicitly forbid direct `decision.md`, Project final
  state, Discord final review, owner completion, reassignment, archive, or
  reverse-import mutation outside guarded closeout.

Reviewer autonomy classes:

- `auto_eligible`: normal verify, docs, and small code Work Units. The fresh
  reviewer may accept, revise, or block through guarded closeout when evidence
  is sufficient.
- `deep_review_auto_eligible`: broad code changes, many changed files, or
  multi-WU dependencies. Size alone is not a manual-review trigger. The fresh
  reviewer should increase review depth, inspect diffs/tests/dependency refs,
  and may use subagents before guarded closeout.
- `manual_required`: operating-server actions, deployment, DB migration,
  credential/auth/security boundaries, cost-bearing actions, destructive
  changes, external public release, unclear owner intent, unresolved
  dependency, critical reviewer/subagent disagreement, missing evidence, stale
  source, or hash/proof mismatch.

Guarded closeout commit request:

- Extend existing `work-unit closeout --publish`; do not build a separate
  commit system.
- Add a structured `--commit-request <json>` input so the fresh reviewer does
  not synthesize arbitrary closeout CLI arguments.
- Minimum commit request fields: `work_unit_id`, `decision`, `reason`,
  `source_ref`, `result_ready_proof_id`, `artifact_hashes`, reviewer
  session/run refs, `autonomy_class`, `review_depth`, `red_line_check`, and
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
  payload, closeout-review-specific session-send adapter, enqueue proof,
  foreground `review-wake` recovery path, stale/duplicate suppression, and
  source-inbox recovery after wake failure. This slice deliberately does not
  add a daemon, queue, DB, retry worker, reverse-import path, or final
  auto-closeout.
- `5.8.4c-2` (implemented): B-prime guarded closeout: `--commit-request`,
  artifact hash and result-ready proof revalidation, reviewer autonomy classes,
  manual-required/red-line fail-closed checks, closeout staging/resume guard,
  and final visibility/status convergence regression coverage.

Acceptance, once implemented:

- A detached Team Lead `result-ready --publish` creates source-backed review
  visibility and fresh reviewer enqueue proof without requiring the Operations
  Lead to keep a foreground session open.
- The Team Lead returns after enqueue proof only. It does not wait for reviewer
  judgment or guarded closeout completion.
- A wake failure leaves the WU visible in `work-unit inbox --result-ready`
  rather than dropping or rolling back source truth.
- The fresh reviewer can restore the WU from source artifacts and may accept
  broad code or multi-WU-dependent work after deep review when no red-line
  risk or evidence gap exists.
- Red-line risk, evidence insufficiency, unresolved dependency, critical
  disagreement, stale source, or hash/proof mismatch produces
  `manual_required`, `revise`, or `blocked`, not automatic accept.
- Only guarded closeout writes final `decision.md`, team-detail final review,
  owner-facing closeout, and Project final status.
- Duplicate/stale wake attempts cannot overwrite or compete with an existing
  final decision.
- Owner-facing status distinguishes `Result Ready / Review Needed` from final
  `Accepted / Needs Revision / Blocked / Done`.

Regression coverage to add:

- Wake payload self-containment and no-go boundary.
- Reviewer enqueue proof success/failure, including no wake record without
  current acceptance/readback and enqueue/run refs.
- Source inbox recovery when RESULT_READY succeeds but reviewer wake fails.
- `--commit-request` WU mismatch, stale decision, duplicate final proof,
  missing source ref, artifact hash mismatch, and manual-required red-line
  fail-closed cases.
- Accepted, Revise, and Blocked convergence across `decision.md`, status
  lifecycle, Project dry-run status, and Discord proof rows.

### Phase 5.8.5: No-Bypass Regression Gate

Status: passed in live gate. `WU-260609-907` completed the clean acceptance
path without manual lifecycle/proof repair: handoff, STARTED, detached dispatch,
Team Lead RESULT_READY, fresh reviewer wake, reviewer-generated guarded
commit-request, Operations Lead dry-run, Operations Lead publish, Discord
readback, and Project sync all converged. The same live run also produced
negative coverage:

- `WU-260609-901`/`902` exposed missing reviewer-agent setup and reviewer
  overreach, leading to explicit configured reviewer agents and reviewer-only
  commit-request authority.
- `WU-260609-903`/`904` exposed duplicate RESULT_READY risk, leading to
  fail-closed duplicate suppression before publish.
- `WU-260609-905`/`906` exposed timestamp/hash ambiguity and proved
  `manual_required` fail-closed behavior.
- `WU-260609-907` exposed reviewer replay idempotency, leading to
  payload/prompt-versioned closeout review execution keys before the final
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
  closeout reviewer wake with the configured command adapter. If wake fails,
  record the `review-wake setup-needed` outcome and recover only through
  foreground `work-unit review-wake`; do not fake closeout.
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
  and missing reviewer refs must fail closed.
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
- Result-ready reviewer wake either records current enqueue proof or leaves a
  visible recoverable setup-needed state without rollback or fake success.
- Guarded commit-request closeout revalidates current source proof/hash/red-line
  state and is the only writer of final `decision.md`, team-detail final
  review, owner-facing closeout, and final Project status.
- Partial publish failure is explicit and foreground-resumable with the same
  guarded request.
- Phase 6 may begin only after this gate passes or an explicit no-go/defer
  decision is recorded with rationale.

## Phase 6 Blocker Rule

Satisfied as of the Phase 5.8.5 live gate. If future changes reopen any P0
workflow issue, reapply this blocker before Phase 6 packaging continues.

Historical rule:

- Phase 5.8 P0 items are resolved;
- Phase 5.8.5 passes without manual bypass; and
- any remaining P1/P2 items are either fixed or explicitly deferred with
  owner-approved rationale.

This prevents Public v1 from packaging a workflow that only works when an
expert operator manually repairs lifecycle and proof gaps.
