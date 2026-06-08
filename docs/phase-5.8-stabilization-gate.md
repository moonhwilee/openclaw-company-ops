# Phase 5.8 Stabilization Gate

Status: planned stabilization gate before Phase 6

Phase 5.8 captures the live workflow issues found during the
`WU-260608-001` through `WU-260608-004` test batch. Phase 6 Packaging /
Public v1 must not begin until the P0 items in this document are resolved and
the regression gate passes.

This gate is not a feature expansion. It stabilizes the Work Unit runtime
contract that Phase 6 packaging depends on.

## Why This Gate Exists

The live test batch showed that the current repository has strong source
artifact, visibility, result-ready, and closeout tooling, but it still lacks a
complete runtime path for detached Team Lead execution.

Observed mismatch:

- The operating model says sizeable `goal` and `verify` work becomes a
  detached Work Unit.
- The current repo-local workflow can create Work Cards, Assignment Packets,
  claims, visibility cards, result-ready records, and closeout decisions.
- The current workflow does not yet provide a standard detached dispatch path
  where the Operations Lead assigns the Work Unit, records the handoff, starts
  the Team Lead execution, and then returns idle while a Team Lead session owns
  execution.

Until that missing layer is resolved, Phase 6 packaging would ship a protocol
that still requires expert manual correction during real operation.

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

Problem:

The Operations Lead can prepare a Work Unit and call a Team Lead, but the repo
does not yet provide a standard detached dispatch path. In the live tests, the
Operations Lead effectively held the Team Lead execution foreground session and
processed each request sequentially.

Impact:

- Owner-observable behavior does not match the Company Ops model.
- Multiple Work Units cannot be assigned and left to Team Leads cleanly.
- Phase 6 packaging would expose a protocol that still depends on manual
  operator discipline instead of a deterministic dispatch surface.

Fix direction:

Define and implement a minimal detached dispatch or run surface that:

- creates or validates the source-backed Work Unit handoff;
- records a canonical execution start;
- records the Team Lead session or job reference;
- returns control to the Operations Lead without waiting for Team Lead result;
- leaves result submission to result-ready inbox / closeout processing.

### P0: `STARTED` Is Required But Not Standardized

Problem:

Docs and proof validation require a team-detail `STARTED` event, but the
canonical handoff/result-ready path does not generate or enforce it.

Impact:

- Proof validation can fail on normal Work Units.
- Operators can hide the defect by manually inserting `STARTED`, which makes
  live tests unreliable.
- Packaged users would have to know an internal lifecycle event that should be
  handled by tooling.

Fix direction:

Introduce a canonical start transition, either as:

- `work-unit start --work-unit-id <id> --team <team> --publish`, or
- part of a higher-level `work-unit dispatch/run --detach` command.

The transition must update source state, publish/read back `STARTED` when live
visibility is enabled, and make result-ready publication fail closed when the
Work Unit has not started.

### P0: Closeout Does Not Finalize Lifecycle State

Problem:

Closeout writes `decision.md` and publishes review/completion visibility, but
status continues to derive current state from `claim.md` as `result_ready`.

Impact:

- Operators see a Work Unit as still result-ready even after Accepted or Revise.
- Source artifacts disagree about lifecycle state.
- Dashboard/status output can mislead Operations Lead review.

Fix direction:

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

Problem:

Closeout-generated `decision.md` can render an empty Work Card field even when
the Assignment Packet, claim, and evidence records contain the Work Card URL.

Impact:

- The final decision artifact loses a key audit link.
- Project/dashboard reconciliation and owner inspection become harder.
- A Work Card could be accepted without a complete decision backlink.

Fix direction:

Make closeout rehydrate Work Card from canonical source artifacts in this
order:

1. assignment packet;
2. claim;
3. evidence/result record;
4. existing decision draft.

If no Work Card can be found, closeout should warn or fail closed before
publishing an accepted decision.

### P1: Status Model Mixes Lifecycle And Responsibility

Problem:

Current status output treats claim expected state as the Work Unit current
state. That conflates a Team Lead's last responsibility claim with the final
Operations Lead decision.

Impact:

- Accepted or Revise decisions can look unfinished.
- Pulse, dashboard, and owner inspection can read the wrong operating signal.

Fix direction:

Expose lifecycle and responsibility separately. At minimum, final decision
state must override claim state in user-facing status.

### P2: Live Test Mode Allowed Manual Bypass

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

- Implement the canonical `STARTED` transition.
- Update claim/source state when a Team Lead starts work.
- Publish/read back `STARTED` when live visibility is enabled.
- Make result-ready fail closed when required start evidence is missing.

Acceptance:

- A Work Unit can move from assigned to working through one standard command.
- Missing `STARTED` is caught before result-ready publication.
- Proof validation passes without manual lifecycle event insertion.

### Phase 5.8.3: Closeout Finalization And Decision Rehydration

Depends on:

- Phase 5.8.1.

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

Scope:

- Define the minimal detach contract for Team Lead execution.
- Add a dispatcher/run surface or document a fail-closed setup-needed state if
  a detached runtime is unavailable.
- Record session/job reference in source artifacts when dispatch succeeds.
- Return Operations Lead control after assignment/start, without waiting for
  Team Lead result.

Acceptance:

- The Operations Lead can assign a Work Unit and return idle.
- The Team Lead execution reference is recoverable from source artifacts.
- Result submission still goes through result-ready inbox and closeout.
- The implementation does not introduce a hidden orchestrator, daemon,
  automatic recovery, automatic reassignment, or automatic completion.

### Phase 5.8.5: No-Bypass Regression Gate

Depends on:

- Phase 5.8.2.
- Phase 5.8.3.
- Phase 5.8.4, if detached dispatch is implemented in this stabilization pass.

Scope:

- Rerun a small live workflow batch with manual bypass prohibited.
- Include at least one verify Work Unit and one 1-round goal Work Unit.
- Verify source artifacts, Discord proof, status output, decision records, and
  Project dry-run output.

Acceptance:

- No manual `STARTED` insertion is needed.
- Status and decision artifacts agree after closeout.
- Work Card references remain present in final decisions.
- Operations Lead does not hold Team Lead foreground execution for the tested
  detached path.
- Phase 6 may begin only after this gate passes or an explicit no-go/defer
  decision is recorded with rationale.

## Phase 6 Blocker Rule

Do not begin Phase 6 Packaging / Public v1 implementation until:

- Phase 5.8 P0 items are resolved;
- Phase 5.8.5 passes without manual bypass; and
- any remaining P1/P2 items are either fixed or explicitly deferred with
  owner-approved rationale.

This prevents Public v1 from packaging a workflow that only works when an
expert operator manually repairs lifecycle and proof gaps.
