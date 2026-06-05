# OpenClaw Company Ops Architecture

Internal architecture version: v1

## Purpose

OpenClaw Company Ops is a lightweight operating structure for running many
OpenClaw-agent-led tasks without turning the system into a heavy workflow
platform.

It exists to make this possible:

- The Operations Lead can define and assign many Work Units.
- Each team lead OpenClaw agent can execute one Work Unit at a time.
- Each team lead can directly manage its own subagents.
- The owner can see company-wide state through a dashboard and `#ops-feed`
  request/result timeline.
- The owner can ask Team Leads direct questions in team channels without turning
  those channels into an operating-state command router.
- Stalled work can be detected without automatic recovery or hidden
  orchestration.

## Accountability Chain

```text
Owner -> Operations Lead -> Team Lead OpenClaw Agent -> Subagents
```

Work Unit is not an actor. A Work Unit is the task unit owned by one team lead
session.

## Roles

### Owner

The owner supervises the Operations Lead.

The owner checks:

- Operations Lead operating judgment.
- Company direction and priorities.
- Final result quality.
- Dashboard visibility and Discord request/result visibility.
- Direct Team Lead answers when a question is better asked in the team channel.
- Operations Lead decision records.

### Operations Lead

The Operations Lead is the role responsible for defining, assigning, reviewing,
and deciding work across team leads.

The Operations Lead owns:

- Work Unit definition.
- Assignment Packet creation.
- Team lead assignment.
- Result and evidence review.
- Final decision.
- Recovery or reassignment judgment when a team lead is stale, blocked, or
  failed.

The Operations Lead does not directly operate a team lead's execution loop or subagents.

### Team Lead OpenClaw Agent

A team lead is an OpenClaw main session that owns exactly one active Work Unit.

The team lead owns:

- Work Unit execution.
- Team Playbook use.
- Direct subagent orchestration.
- Evidence collection.
- Result submission to the Operations Lead.
- Ops Claim Ledger updates for its execution responsibility.

Team Leads may answer direct owner questions in their team channel. Those
answers can clarify status, evidence location, or possible approaches. They do
not become delegated Work Unit execution unless the normal Work Card,
Assignment Packet, claim, evidence, and decision trail exists.

### Standing Role Agents And Project-Specific Agents

Team Lead OpenClaw Agents may be standing role agents or project-specific
agents.

Standing role agents, such as `build-pq`, `build-lab`, `market`, and
`revenue`, are shared lightweight capacity. They are not removed when one
project ends. They should keep minimal workspace state, avoid default direct
chat bindings or heartbeat unless explicitly needed, and must not accumulate
project clones, raw archives, large evidence bundles, or long-term memory.

Project-specific agents are created only when a Work Unit or project needs
stronger isolation than a standing role agent provides. When that project ends,
remove the project-specific agent with the normal OpenClaw deletion flow, such
as `openclaw agents delete <id>`, so its workspace, agent state, and session
transcripts move to Trash.

The Operations Lead is the long-lived memory-preserving role. Standing role
agents are reusable. Project-specific agents are disposable by default.

### Subagents

Subagents are workers under a team lead.

Subagents report to the team lead, not directly to the Operations Lead.

## Operating Elements

OpenClaw Company Ops has eight v1 elements.

### 1. Company Dashboard

Company Dashboard is the company-wide visibility surface.

Default implementation: GitHub Projects.

It shows:

- Work Unit.
- Work Card.
- Team lead.
- State.
- Priority.
- Blocker summary.
- PR/result link.
- Evidence link.
- Operations Lead decision link.

It is not a source of truth.

### 2. Work Card

Work Card is the official shared task card.

Default implementation: GitHub Issue.

It contains only:

- Work Unit id.
- Title.
- Goal.
- Team lead.
- Scope.
- Done criteria.
- Assignment Packet reference.
- Current result/evidence links when available.

It is not the detailed handoff.

### 3. Assignment Packet

Assignment Packet is the detailed handoff from the Operations Lead to the team
lead.

It contains:

- Goal.
- Background.
- Scope.
- Non-goals.
- Constraints.
- Inputs.
- Done criteria.
- Verification criteria.
- Protocol Capsule.
- Expected outputs.
- Reporting format.

GitHub issue text, PR summaries, Discord messages, and dashboard notes cannot
replace the Assignment Packet.

The Protocol Capsule is a compact execution instruction embedded in the
Assignment Packet. It tells the Team Lead which protocol loop to run, but it
does not replace the packet itself.

Canonical protocol files live under `docs/protocols/`. They are references for
the Operations Lead when composing capsules. The Team Lead should execute the
capsule in the active Assignment Packet instead of searching protocol files and
interpreting the Work Unit from scratch.

The capsule mode is explicit. There is no default mode that turns every Work
Unit into `goal`; the Operations Lead selects the mode that matches the
delegated Work Unit.

```yaml
protocol_capsule:
  mode: <goal|verify>
  support: []
  loop: <plan -> repeat(act_or_improve -> verify) until stop_only_on, only for goal>
  stop_only_on:
    - done_criteria_passed_with_evidence
    - explicit_blocker
    - safety_or_budget_limit
    - operations_lead_or_user_pause
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_selected_mode
```

### 4. Team Lead Session

Team Lead Session is the OpenClaw main session responsible for one Work Unit.

The team lead session must directly control its subagents.

There must be no hidden orchestrator agent between the team lead and its
subagents.

There may be a direct team Discord channel for each standing role agent. That
channel is a human/agent communication path, not a state mutation path. A direct
question can produce an answer or a draft recommendation, but it must not create
or close official work without source artifacts.

### 5. Team Playbook

Team Playbook is the operating checklist used by the team lead.

For v1, this is prompt/checklist first. It does not require a separate execution runtime.

The playbook tells the team lead how to:

- Restate the assignment.
- Confirm the Assignment Packet and Protocol Capsule.
- Run `goal`: plan once, then repeat act-or-improve and verify until done
  criteria pass.
- Run `verify`: map outputs and evidence to done and verification criteria.
- Recover context after long work, compaction, or subagent result integration,
  then continue the selected mode.
- Delegate partial work to subagents while keeping Work Unit ownership.
- Review subagent output as input, not as completion truth.
- Produce evidence.
- Report result-ready or blockers.

A future runtime may later support this flow, but v1 must not depend on that.

### 6. Evidence & Result Record

Evidence & Result Record is the completion proof bundle.

It may include:

- PR.
- Test output.
- Review notes.
- Report.
- Sources.
- Screenshots.
- Generated artifacts.
- Decision record.

It is not a new database. It is a small bundle of links and artifacts that lets
the Operations Lead decide whether the Work Unit is done.

No evidence means no completion.

### 7. Ops Claim Ledger

Ops Claim Ledger is the lightweight expected-responsibility ledger.

It records what responsibility is currently expected, who owns it, and when that
expectation expires.

It is not:

- Runtime truth.
- Progress history.
- Event log.
- Dashboard database.
- Evidence storage.
- Recovery system.

Minimum fields:

- `claim_ref`
- `claim_type`
- `owner_session_ref`
- `expected_state`
- `expected_until`
- `last_claim`
- `evidence_ref`
- `last_seen_compaction_count`

Claim types:

- `orchestration`: Operations Lead responsibility, such as assignment, review,
  decision, or recovery judgment.
- `execution`: team lead responsibility for Work Unit execution.

Expected states:

- `assigned`
- `working`
- `waiting`
- `blocked`
- `result_ready`
- `done`

`last_claim` is a short status claim that includes timestamp meaning. It is used
to judge staleness.

`done` is not completion truth. It is an expected responsibility state after the
Operations Lead has made the decision.

### 8. Pulse Monitor

Pulse Monitor compares Ops Claim Ledger expectations with available OpenClaw
session signals.

It is alert-only.

Allowed alerts:

- `SESSION_MISMATCH`
- `COMPACTION_RECOVERY_SUSPECTED`
- `CLAIM_STALE`

Alert priority:

1. `SESSION_MISMATCH`: owner session is missing or dead.
2. `COMPACTION_RECOVERY_SUSPECTED`: compaction count increased and the claim was
   not refreshed before `expected_until`.
3. `CLAIM_STALE`: owner session exists, but the claim or evidence was not
   refreshed before `expected_until`.

Pulse Monitor must not:

- Restart agents.
- Recover agents.
- Reassign work.
- Cancel work.
- Modify GitHub.
- Modify execution state.
- Mark completion.
- Infer a fallback source of truth.
- Make Operations Lead decisions.

## Operating Flow

1. Owner states a goal or priority.
2. Operations Lead defines a Work Unit.
3. Operations Lead writes an Assignment Packet with a Protocol Capsule.
4. Operations Lead creates a Work Card.
5. Operations Lead assigns one team lead OpenClaw agent.
6. Operations Lead or the team lead creates the relevant Ops Claim Ledger claim.
7. Team lead executes packet-first through Team Playbook.
8. Team lead directly manages subagents.
9. Team lead submits Evidence & Result Record.
10. Operations Lead reviews evidence and records a final decision.
11. Company Dashboard and Discord visibility reflect the state.
12. Pulse Monitor emits alerts only if claim expectations and session signals
    diverge.

## Discord Ops

Discord Ops is the human-visible request/result briefing timeline and team
detail trail.

Allowed `#ops-feed` owner-facing summary kinds:

- `ASSIGNED`
- `COMPLETED`
- `BLOCKED`

Allowed `#team-*` detail trail kinds:

- `ASSIGNED_DETAIL`
- `STARTED`
- `RESULT_READY`
- `ACCEPTED`
- `REVISE`
- `BLOCKED_DETAIL`

`RESULT_READY` is the Team Lead submission signal. A normal team detail trail
is not closed until Operations Lead review is posted as `ACCEPTED`, `REVISE`,
or `BLOCKED_DETAIL`.

Normal visibility uses one Operations Lead composition step per transition:
compose a user-friendly `#ops-feed` card and a separate detailed `#team-*`
message from the same facts. This should not add another Team Lead execution or
LLM summarization call. `#ops-feed` content should use owner-facing labels such
as `문제`, `요청`, `기준`, `결과`, `확인`, and `다음` rather than internal fields
such as `Surface`, raw `Source`, mechanical `Owner`, or default
`Public summary`.

Internal schema can remain stable English; owner-facing cards and internal
long-form values use Korean by default. Public/package examples may use
English.

Discord Ops must not become:

- A command router.
- A truth store.
- An Assignment Packet substitute.
- An Ops Claim Ledger substitute.
- A place for raw logs, secrets, or private context dumps.

## GitHub Layer

GitHub is used for work tracking, review, and evidence.

GitHub may provide:

- Issues as Work Cards.
- Projects as Company Dashboard.
- PRs as result records.
- Actions as deterministic check evidence.
- Comments as decision records.

GitHub must not replace:

- Assignment Packet.
- Ops Claim Ledger.
- Team Playbook.
- Operations Lead judgment.

## No Legacy And No Fallback

No legacy means older experimental structures are reference
material only. They are not compatibility targets.

No fallback means one layer cannot silently replace another.

Forbidden substitutions:

- GitHub Issue text cannot replace Assignment Packet.
- Discord messages cannot replace Assignment Packet.
- Protocol files cannot replace Assignment Packet or Protocol Capsule.
- Team Lead execution plans cannot replace Assignment Packet.
- GitHub labels or Project status cannot replace Ops Claim Ledger.
- PR summaries cannot replace evidence.
- Pulse Monitor cannot replace Operations Lead judgment.
- The Team Playbook cannot create a hidden orchestrator agent.
- Operations Lead cannot directly operate a team lead's subagents.

If a required layer is missing, the state is `blocked` or `control_gap`.

## Explicitly Out Of Scope For This Version

- Required Probot automation.
- Discord command router.
- Full Discord Ops Bridge.
- SQLite or database-backed ledger.
- Automatic restart, recovery, cancellation, or reassignment.
- Automatic completion.
- Hidden orchestrator agent.
- Operations Lead directly manipulating team lead execution internals.
- A protocol runtime, classifier, or daemon that replaces the Assignment Packet
  and Team Lead prompt loop.
- Marketplace or multi-user platform features.

## Implementation Direction

The base setup foundation now includes documentation, templates, repo-local
Work Unit artifact generation, JSON-backed Ops Claim Ledger support, alert-only
Pulse Monitor checks, a bounded multi-team smoke, Discord alert formatting,
dashboard snapshots, a non-installing pulse daemon runner, and a repo-local
entrypoint.

The active remaining order is documented in `docs/post-setup-plan.md`. Phases
1-4 have been exercised; the current work is Phase 5 activation sub-gates:

1. Visibility contract close.
2. Completion / Hook Guard MVP decision.
3. Dashboard gate.
4. Discord publisher gate.
5. Scheduled Pulse / daemon gate.
6. Packaging readiness decision.

After Phase 5:

- Phase 6: Packaging / public v1.
- Phase 7: Cross-project adoption.

Do not activate optional automation unless the relevant Phase 5 sub-gate has an
explicit yes/no/defer decision with rationale and preserves the source-artifact
model.

## Open Decisions

These decisions are not blockers for the architecture:

- When to install or schedule the Pulse Monitor daemon runner.
- When to promote the foreground Discord `publish-card` path beyond P0 proof
  into a broader operating surface.
- When to create or sync a GitHub Project dashboard.
- Whether the first public package is a CLI, OpenClaw skill, setup script, or a
  combination.
