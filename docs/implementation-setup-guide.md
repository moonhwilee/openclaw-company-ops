# Implementation Setup Guide

Status: Manual Implementation Draft

This guide is the follow-along implementation path for OpenClaw Company Ops.
It is for users who want to build the complete operating structure before a
supported CLI or package exists.

The manual steps are intentionally detailed. As automation is implemented,
replace each manual block with supported commands instead of keeping two
parallel setup paths.

## What This Guide Builds

This guide builds the current practical structure:

```text
Owner -> Operations Lead -> Team Lead OpenClaw Agent -> Subagents
```

It sets up:

- OpenClaw agent roles for Operations Lead and Team Leads.
- GitHub Issues as Work Cards.
- Assignment Packet, claim, evidence, and decision artifact storage.
- A manual file-backed Ops Claim Ledger.
- Manual Pulse Monitor checks that can later become alert-only automation.
- Discord visibility conventions.
- Team Lead Execution boundaries.
- An end-to-end smoke test.

This guide does not create a finished product runtime. It creates the structure
that the future runtime must automate.

## Automation Replacement Map

Use this map when turning manual setup into CLI commands later.

| Manual block today | Future automation target |
| --- | --- |
| Create directories and template files | `openclaw-company-ops init` |
| Create labels and issue templates | `openclaw-company-ops github bootstrap` |
| Create Work Card plus artifacts | `openclaw-company-ops work-unit create` |
| Update claim files | `openclaw-company-ops claim update` |
| Run stale/session checks manually | `openclaw-company-ops pulse check` |
| Post Discord visibility messages | `openclaw-company-ops discord emit` |
| Run smoke test manually | `openclaw-company-ops smoke` |

When a command exists, remove or collapse the corresponding manual section.
Do not keep a hidden legacy path.

## Required Principles

These rules apply during manual setup and after automation exists:

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- No Discord command router in v1.
- No required database for the v1 ledger.
- No GitHub Issue, PR summary, dashboard note, or Discord message may replace
  the Assignment Packet.
- No dashboard field, label, or Discord event may replace Evidence & Result
  Records.
- No completion may be inferred without an Operations Lead decision.

If a required artifact is missing, the correct state is `blocked`.

## Prerequisites

Install and verify these tools before creating the operating structure.

```bash
openclaw --version
openclaw status
gh --version
gh auth status
git --version
```

You need:

- A working OpenClaw install for the Operations Lead.
- One or more OpenClaw agent identities for Team Leads.
- A GitHub account with permission to create or administer the target repo.
- GitHub Issues enabled on the target repo.
- A local workspace for private runtime state.
- Optional: a Discord server or channel for visibility events.

If an OpenClaw command differs in your environment, run the matching help
command first:

```bash
openclaw --help
openclaw agents --help
openclaw sessions --help
openclaw message --help
openclaw cron --help
```

## Directory Model

Use one public repo for the reusable operating model and one private runtime
state root for local claims, evidence, and checks.

Recommended public repo:

```text
openclaw-company-ops/
  .github/ISSUE_TEMPLATE/
  docs/
  docs/templates/
  docs/examples/manual-dry-run/
```

Recommended private runtime root:

```text
~/.openclaw/state/openclaw-company-ops/
  work-units/
  claims/
  evidence/
  decisions/
  pulse/
  discord/
```

Create the private runtime root:

```bash
mkdir -p ~/.openclaw/state/openclaw-company-ops/{work-units,claims,evidence,decisions,pulse,discord}
```

Public-safe examples may live in the repo. User-specific execution state,
private inputs, secrets, raw transcripts, and private evidence should live
under the private runtime root and should not be committed.

## OpenClaw Agent Setup

Status: Manual implementation

The Operations Lead coordinates work and records decisions. Each Team Lead
OpenClaw Agent owns one active Work Unit and directly manages its own
subagents.

### Verify OpenClaw

```bash
openclaw status
openclaw status --json
```

If OpenClaw is not configured yet, start with the normal setup flow:

```bash
openclaw setup
```

or, where appropriate:

```bash
openclaw onboard
```

### Create Agent Identities

Create or verify an Operations Lead identity and one Team Lead identity.
Exact flags may vary by OpenClaw version, so check help before running:

```bash
openclaw agents --help
openclaw agents add --help
openclaw agents set-identity --help
```

Manual target:

```bash
openclaw agents add operations-lead
openclaw agents set-identity --agent operations-lead --name "Operations Lead"
openclaw agents add team-lead-1
openclaw agents set-identity --agent team-lead-1 --name "Team Lead 1"
openclaw agents list
```

If your OpenClaw install uses generated agent ids instead of custom names,
record the generated id in the Assignment Packet and claim.

### Choose Standing Or Project-Specific Team Leads

For constrained development servers, prefer one long-lived Operations Lead plus
small standing Team Lead role agents.

Recommended shape:

- Operations Lead: long-lived, memory-preserving, decision-owning.
- `build`: shared lightweight build/development role agent.
- `ops`: shared lightweight operations/integration role agent.

Do not delete standing `build` or `ops` agents on normal project closure. Keep
their heartbeat and direct message bindings disabled unless explicitly needed,
keep their workspace minimal, and remove project clones, raw archives, large
evidence bundles, and temporary cache after substantial work.

Create a project-specific agent only when the Work Unit needs stronger
isolation than a standing role agent provides. When that project ends, remove
the project-specific agent with:

```bash
openclaw agents delete <id>
```

This keeps standing role agents reusable while allowing temporary project
agents to be cleaned up with their workspace, state, and session transcripts.

### Bind Message Routing If Needed

Use bindings only for routing. A binding is not a source of truth.

```bash
openclaw agents bind --help
openclaw agents bindings
```

Record the Team Lead agent id in:

- Work Card.
- Assignment Packet.
- Ops Claim Ledger entry.
- Evidence & Result Record.

### Record Session References

The claim must include an `owner_session_ref` for the agent expected to own the
next action.

Inspect sessions:

```bash
openclaw sessions --all-agents --json
openclaw sessions --agent <agent-id> --json
```

Use the most stable available reference from your OpenClaw output. Good
references include:

- Agent id.
- Session id.
- Current conversation/thread id.
- Last active timestamp.
- A local session artifact path.

If no stable session id is exposed, record:

```text
agent=<agent-id>; observed_at=<ISO-8601 timestamp>; source=openclaw sessions
```

### Record Compaction State

If your OpenClaw session output exposes compaction count, record it in
`last_seen_compaction_count`.

If not available, write:

```text
last_seen_compaction_count: unknown
```

After any interruption or compaction, the owning agent must refresh the claim
instead of assuming the previous claim is still fresh.

## GitHub Setup

Status: Manual implementation

GitHub provides Work Cards, PRs, review links, and optional dashboard views.
It is not the Assignment Packet, claim ledger, evidence store, or decision
store.

### Create Or Prepare The Repo

For a new public repo:

```bash
gh repo create <owner>/openclaw-company-ops --public --clone
cd openclaw-company-ops
gh repo edit <owner>/openclaw-company-ops --enable-issues=true --enable-wiki=false --delete-branch-on-merge=true
```

For an existing repo:

```bash
gh repo view --json nameWithOwner,visibility,hasIssuesEnabled,hasWikiEnabled,deleteBranchOnMerge
gh auth status
```

### Install Work Card Labels

Run these in the target repo:

```bash
gh label create work-unit --color 5319E7 --description "OpenClaw Company Ops Work Unit" --force
gh label create assignment-ready --color 1D76DB --description "Assignment Packet exists and is ready for execution" --force
gh label create working --color 0E8A16 --description "Team Lead is actively working the Work Unit" --force
gh label create blocked --color D93F0B --description "Work Unit is blocked by missing input, permission, artifact, or decision" --force
gh label create result-ready --color 006B75 --description "Evidence and result are ready for Operations Lead review" --force
gh label create decision-needed --color FBCA04 --description "Operations Lead decision is required" --force
gh label create done --color C5DEF5 --description "Evidence and Operations Lead decision are linked; Work Card can close" --force
```

### Install The Issue Template

Place the Work Card form at:

```text
.github/ISSUE_TEMPLATE/work-card.yml
```

Minimal Work Card fields:

- Work Unit id.
- Goal.
- Assigned Team Lead OpenClaw Agent.
- Assignment Packet reference.
- Current state.
- Done criteria.
- Evidence & Result Record reference when available.
- Operations Lead decision reference when available.

The Work Card must link to the Assignment Packet. It must not become the
Assignment Packet.

### Defer Branch Protection

Do not enable strict branch protection before the manual loop is stable.

Turn on branch protection later when:

- The repo has repeatable PR checks.
- The merge path is clear.
- The Operations Lead decision rule is already practiced.

Branch protection can require checks, but it must not become completion truth.

### Defer Company Dashboard

Do not create a GitHub Project just because setup exists.

Create a dashboard only when there are enough active Work Cards or repos to
make cross-work visibility useful. Dashboard timing is defined in
`docs/company-dashboard-timing.md`.

## Artifact Storage Setup

Status: Manual implementation

Every Work Unit needs four artifact classes:

- Assignment Packet.
- Ops Claim Ledger entry.
- Evidence & Result Record.
- Operations Lead Decision.

For public-safe examples, use:

```text
docs/examples/manual-dry-run/<work-unit-id>/
  assignment.md
  claim.md
  evidence.md
  decision.md
```

For real private work, use:

```text
~/.openclaw/state/openclaw-company-ops/work-units/<work-unit-id>/
  assignment.md
  claim.md
  evidence.md
  decision.md
```

Create a new Work Unit artifact directory:

```bash
WU_ID=WU-YYYYMMDD-001
mkdir -p ~/.openclaw/state/openclaw-company-ops/work-units/$WU_ID
cp docs/templates/assignment-packet.md ~/.openclaw/state/openclaw-company-ops/work-units/$WU_ID/assignment.md
cp docs/templates/ops-claim-ledger-entry.md ~/.openclaw/state/openclaw-company-ops/work-units/$WU_ID/claim.md
cp docs/templates/evidence-result-record.md ~/.openclaw/state/openclaw-company-ops/work-units/$WU_ID/evidence.md
cp docs/templates/operations-lead-decision.md ~/.openclaw/state/openclaw-company-ops/work-units/$WU_ID/decision.md
```

Future automation should replace this with:

```bash
openclaw-company-ops work-unit create ...
```

## Work Unit Creation Flow

Status: Manual implementation

1. Owner gives a goal.
2. Operations Lead decides whether it becomes one Work Unit.
3. Operations Lead creates the Assignment Packet.
4. Operations Lead creates the GitHub Work Card.
5. Operations Lead records an initial claim.
6. Team Lead executes.
7. Team Lead submits evidence.
8. Operations Lead records a decision.
9. Work Card closes only after evidence and decision are linked.

Create the Work Card:

```bash
gh issue create \
  --title "[Work Unit] <short goal>" \
  --label work-unit \
  --label assignment-ready \
  --body-file /tmp/work-card.md
```

Move labels manually as the state changes:

```bash
gh issue edit <issue-number> --remove-label assignment-ready --add-label working
gh issue edit <issue-number> --remove-label working --add-label result-ready --add-label decision-needed
gh issue edit <issue-number> --remove-label result-ready --remove-label decision-needed --add-label done
gh issue close <issue-number>
```

Labels are visibility only. The Work Card closes because evidence and decision
exist, not because a label says `done`. Avoid routine close comments; required
links belong in the Work Card body, PR, evidence record, or decision record.

## Ops Claim Ledger Setup

Status: Manual implementation

The Ops Claim Ledger records expected responsibility. It is not a database of
truth, progress history, event log, dashboard backend, or recovery system.

Required fields:

```text
claim_ref:
work_unit_id:
work_card:
claim_type: orchestration | execution
owner_session_ref:
expected_state:
expected_until:
last_claim:
last_seen_compaction_count:
assignment_packet:
evidence_ref:
operations_lead_decision_ref:
```

Allowed `expected_state` values:

- `assigned`
- `working`
- `waiting`
- `blocked`
- `result_ready`
- `done`

Manual claim file example:

```text
Claim ref: CLAIM-WU-YYYYMMDD-001-001
Work Unit id: WU-YYYYMMDD-001
Claim type: execution
Owner session ref: agent=team-lead-1; observed_at=2026-06-04T09:00:00+09:00
Expected state: working
Expected until: 2026-06-04T10:00:00+09:00
Last claim: Team Lead is implementing the assigned scope.
Last seen compaction count: unknown
Assignment Packet: ./assignment.md
Evidence ref: pending
Operations Lead decision ref: pending
```

Refresh the claim when:

- Work starts.
- Work blocks.
- Expected update time changes.
- Evidence is submitted.
- Compaction or interruption occurs.
- Operations Lead makes a decision.

Use a simple single-writer rule until automation exists:

- The current owner of the next action edits the claim.
- The Operations Lead may edit the claim during review, reassignment judgment,
  or decision.
- Do not allow two agents to update the same claim simultaneously.

Future automation should replace manual edits with:

```bash
openclaw-company-ops claim update ...
```

## Pulse Monitor Setup

Status: Manual implementation now, alert-only automation later

The Pulse Monitor compares the expected responsibility claim with available
OpenClaw/session signals.

Manual Day-0 check:

```bash
openclaw sessions --agent <agent-id> --json
openclaw status --json
```

Compare:

- Does the owner session still appear active?
- Is the claim older than `expected_until`?
- Did compaction appear to occur without a refreshed claim?
- Does the GitHub label disagree with the claim?
- Did the Team Lead report completion without evidence?

Allowed alert statuses:

- `SESSION_MISMATCH`
- `CLAIM_STALE`
- `COMPACTION_RECOVERY_SUSPECTED`

The monitor must only alert. It must not:

- Restart agents.
- Reassign work.
- Recover sessions.
- Cancel work.
- Mark completion.
- Modify GitHub state.
- Modify execution state.
- Infer a fallback source of truth.

Future automation should replace the manual comparison with:

```bash
openclaw-company-ops pulse check --claim <claim-ref>
```

or a scheduled alert-only job:

```bash
openclaw cron add company-ops-pulse -- <command>
```

## Discord Visibility Setup

Status: Manual implementation now, visibility bridge later

Discord is optional. If used, it is only an event visibility surface.

Recommended channels:

- `#ops-feed`: assignments, starts, blockers, results, and decisions.
- `#ops-alerts`: stale claims, suspected session mismatch, and suspected
  compaction recovery.

Verify available OpenClaw messaging commands:

```bash
openclaw message --help
openclaw channels status
```

Manual event format:

```text
[RESULT_READY] WU-YYYYMMDD-001
Work Card: <GitHub Issue URL>
Assignment: <Assignment Packet ref>
Claim: <Claim ref>
Evidence: <Evidence & Result Record ref>
Next action: Operations Lead decision
```

Recommended event types:

- `ASSIGNED`
- `STARTED`
- `BLOCKED`
- `CLAIM_STALE`
- `SESSION_MISMATCH`
- `COMPACTION_RECOVERY_SUSPECTED`
- `RESULT_READY`
- `DECISION`

Every Discord event must link back to the real artifact. Discord must not
accept commands that mutate Work Units in v1.

Future automation should replace manual event posting with:

```bash
openclaw-company-ops discord emit --event RESULT_READY --work-unit <id>
```

## Team Lead Execution Setup

Status: Manual implementation

Each Team Lead OpenClaw Agent owns execution for one Work Unit and directly
manages its own subagents.

The Team Lead should:

1. Read the Assignment Packet.
2. Confirm scope, constraints, and done criteria.
3. Create a short execution plan.
4. Use the Team Playbook if helpful.
5. Directly spawn or coordinate its own subagents.
6. Keep claim state fresh.
7. Produce the Evidence & Result Record.

The Team Playbook is a support protocol for the owning Team Lead. It must not
create or become a hidden orchestrator agent.

Execution artifacts should carry:

- Work Unit id.
- Work Card ref.
- Assignment Packet ref.
- Claim ref.
- Evidence ref.
- Team Lead session ref.
- Subagent task refs where relevant.

Template:

```text
docs/templates/team-playbook.md
```

## End-To-End Smoke Test

Status: Manual implementation

Run this smoke test after setup.

1. Create a demo Work Unit id:

   ```bash
   WU_ID=WU-YYYYMMDD-001
   ```

2. Create artifact files from templates.

3. Fill the Assignment Packet with a small documentation or no-op task.

4. Create a GitHub Work Card and link the Assignment Packet.

5. Create a claim with `expected_state: working`.

6. Have the Team Lead produce an Evidence & Result Record.

7. Record an Operations Lead decision.

8. Link evidence and decision from the Work Card.

9. Close the Work Card only after the links exist.

10. Run sanity checks:

    ```bash
    git diff --check
    ruby -e 'require "yaml"; Dir[".github/ISSUE_TEMPLATE/*.yml"].each { |p| YAML.load_file(p); puts "ok #{p}" }'
    rg -n "fallback source of truth|hidden orchestrator|automatic recovery|Discord command router" README.md docs .github
    ```

Pass criteria:

- Work Card links to Assignment Packet, claim, evidence, and decision.
- Evidence maps to done criteria.
- Decision is explicit.
- Missing artifacts are treated as blocked.
- Discord and dashboard references, if any, are visibility only.
- No hidden orchestrator or automatic recovery path is introduced.

## Troubleshooting

If a Team Lead cannot find the Assignment Packet, mark the Work Unit blocked.

If the Work Card and claim disagree, trust neither blindly. The Operations
Lead reviews the artifacts and records the next expected responsibility.

If a claim is stale, alert and review manually. Do not restart or reassign
automatically.

If Discord says work is done but evidence is missing, the Work Unit is not
complete.

If a PR is merged but there is no Operations Lead decision, the Work Card
still lacks the required closure artifact.

If GitHub Project or dashboard status disagrees with the artifacts, treat the
dashboard as stale visibility and update it after reviewing the source
artifacts.

## Future CLI Migration

When CLI automation exists, update this guide in place.

Recommended replacement order:

1. Replace directory/bootstrap commands with `init`.
2. Replace GitHub label/template setup with `github bootstrap`.
3. Replace artifact scaffolding with `work-unit create`.
4. Replace manual claim edits with `claim update`.
5. Replace manual pulse comparison with `pulse check`.
6. Replace manual Discord posting with `discord emit`.
7. Replace the manual smoke test with `smoke`.

Do not leave manual commands as an alternate legacy operating path after the
supported command is available. Keep only emergency diagnostics and explicit
manual repair notes.
