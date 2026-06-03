# OpenClaw Company Ops Architecture

Internal architecture version: v1

## Purpose

OpenClaw Company Ops is a lightweight operating structure for running many
OpenClaw-agent-led tasks without turning the system into a heavy workflow
platform.

It exists to make this possible:

- Goldbee can define and assign many Work Units.
- Each team lead OpenClaw agent can execute one Work Unit at a time.
- Each team lead can directly manage its own subagents.
- The owner can see company-wide state through a dashboard and event feed.
- Stalled work can be detected without automatic recovery or hidden
  orchestration.

## Accountability Chain

```text
Owner -> Goldbee -> Team Lead OpenClaw Agent -> Subagents
```

Work Unit is not an actor. A Work Unit is the task unit owned by one team lead
session.

## Roles

### Owner

The owner supervises Goldbee.

The owner checks:

- Goldbee's operating judgment.
- Company direction and priorities.
- Final result quality.
- Dashboard and Discord event visibility.
- Goldbee decision records.

### Goldbee

Goldbee is the research director and operations lead.

Goldbee owns:

- Work Unit definition.
- Assignment Packet creation.
- Team lead assignment.
- Result and evidence review.
- Final decision.
- Recovery or reassignment judgment when a team lead is stale, blocked, or
  failed.

Goldbee does not directly operate a team lead's Pilot or subagents.

### Team Lead OpenClaw Agent

A team lead is an OpenClaw main session that owns exactly one active Work Unit.

The team lead owns:

- Work Unit execution.
- Team Playbook / Pilot Prompt use.
- Direct subagent orchestration.
- Evidence collection.
- Result submission to Goldbee.
- Ops Claim Ledger updates for its execution responsibility.

### Subagents

Subagents are workers under a team lead.

Subagents report to the team lead, not directly to Goldbee.

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
- Goldbee decision link.

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

Assignment Packet is the detailed handoff from Goldbee to the team lead.

It contains:

- Goal.
- Background.
- Scope.
- Non-goals.
- Constraints.
- Inputs.
- Done criteria.
- Verification criteria.
- Expected outputs.
- Reporting format.

GitHub issue text, PR summaries, Discord messages, and dashboard notes cannot
replace the Assignment Packet.

### 4. Team Lead Session

Team Lead Session is the OpenClaw main session responsible for one Work Unit.

The team lead session must directly control its subagents.

There must be no hidden orchestrator agent between the team lead and its
subagents.

### 5. Team Playbook / Pilot Prompt

Team Playbook / Pilot Prompt is the operating checklist used by the team lead.

For v1, this is prompt/checklist first. It does not require a heavy Pilot
runtime.

The playbook tells the team lead how to:

- Restate the assignment.
- Split the work.
- Delegate to subagents.
- Review subagent output.
- Verify results.
- Produce evidence.
- Report completion or blockers.

Pilot may later become a stronger runtime, but v1 must not depend on that.

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
Goldbee decide whether the Work Unit is done.

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

- `orchestration`: Goldbee responsibility, such as assignment, review,
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

`done` is not completion truth. It is an expected responsibility state after
Goldbee has made the decision.

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
- Modify Pilot state.
- Mark completion.
- Infer a fallback source of truth.
- Make Goldbee decisions.

## Operating Flow

1. Owner states a goal or priority.
2. Goldbee defines a Work Unit.
3. Goldbee writes an Assignment Packet.
4. Goldbee creates a Work Card.
5. Goldbee assigns one team lead OpenClaw agent.
6. Goldbee or the team lead creates the relevant Ops Claim Ledger claim.
7. Team lead executes through Team Playbook / Pilot Prompt.
8. Team lead directly manages subagents.
9. Team lead submits Evidence & Result Record.
10. Goldbee reviews evidence and records a final decision.
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
- Team Playbook / Pilot Prompt.
- Goldbee judgment.

## No Legacy And No Fallback

No legacy means older Workbench or Project Cell structures are reference
material only. They are not compatibility targets.

No fallback means one layer cannot silently replace another.

Forbidden substitutions:

- GitHub Issue text cannot replace Assignment Packet.
- Discord messages cannot replace Assignment Packet.
- GitHub labels or Project status cannot replace Ops Claim Ledger.
- PR summaries cannot replace evidence.
- Pulse Monitor cannot replace Goldbee judgment.
- Pilot cannot create a hidden orchestrator agent.
- Goldbee cannot directly operate a team lead's subagents.

If a required layer is missing, the state is `blocked` or `control_gap`.

## Explicitly Out Of Scope For This Version

- Required Probot automation.
- Discord command router.
- Full Discord Ops Bridge.
- SQLite or database-backed ledger.
- Automatic restart, recovery, cancellation, or reassignment.
- Automatic completion.
- Hidden orchestrator agent.
- Goldbee directly manipulating team lead Pilot internals.
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
