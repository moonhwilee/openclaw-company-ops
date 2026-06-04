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
- The owner can see company-wide state through a dashboard and event feed.
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
- Dashboard and Discord event visibility.
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

### Standing Role Agents And Project-Specific Agents

Team Lead OpenClaw Agents may be standing role agents or project-specific
agents.

Standing role agents, such as `build` and `ops`, are shared lightweight
capacity. They are not removed when one project ends. They should keep minimal
workspace state, avoid default direct chat bindings or heartbeat unless
explicitly needed, and must not accumulate project clones, raw archives, large
evidence bundles, or long-term memory.

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
  mode: <goal|verify|conv>
  support: []
  loop: <only_if_mode_requires_a_loop>
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

### 5. Team Playbook

Team Playbook is the operating checklist used by the team lead.

For v1, this is prompt/checklist first. It does not require a separate execution runtime.

The playbook tells the team lead how to:

- Restate the assignment.
- Confirm the Assignment Packet and Protocol Capsule.
- Run `goal`: plan, act, verify, improve, and reverify until done criteria pass.
- Run `verify`: map outputs and evidence to done and verification criteria.
- Run `conv`: recover context after long work, compaction, or subagent result
  integration.
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
11. Company Dashboard and Discord Ops reflect the state.
12. Pulse Monitor emits alerts only if claim expectations and session signals
    diverge.

## Discord Ops

Discord Ops is the human-visible event feed.

Allowed event types:

- `ASSIGNED`
- `STARTED`
- `BLOCKED`
- `RESULT_READY`
- `DECISION`
- `DONE`
- `ALERT`

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

Build in this order:

1. Documentation and templates.
2. Manual operating dry run with one Work Unit.
3. GitHub Issue and Project setup.
4. Discord event dry run.
5. File-backed Ops Claim Ledger.
6. Manual Pulse Monitor check.
7. Optional Pulse Monitor daemon.
8. Optional Discord Ops formatter/publisher.
9. Reproducible package for other users.

Do not implement optional automation until the manual operating loop is proven.

## Open Decisions

These decisions are not blockers for the architecture:

- When to implement the Pulse Monitor daemon.
- When to automate Discord Ops publishing.
- When to create the public GitHub repository.
- Whether the first public package is a CLI, OpenClaw skill, setup script, or a
  combination.
