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
| Format Discord alert messages | `openclaw-company-ops discord alerts` |
| Publish Discord visibility messages | `openclaw-company-ops discord card` + foreground `discord publish-card` after activation |
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
- Optional: a Discord server or channel for visibility messages.

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
- `build-pq`: PrimeQuant product development role agent.
- `build-lab`: new product and automation development role agent.
- `market`: market research, positioning, and content role agent.
- `revenue`: revenue operations and customer workflow role agent.

Do not delete standing role agents on normal project closure. Keep their
heartbeat and direct message bindings disabled unless explicitly needed, keep
their workspace minimal, and remove project clones, raw archives, large
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
- Lifecycle state.
- Responsibility state.
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

### Company Dashboard

Phase 5.3 accepted a GitHub Project dashboard because the owner needs an
at-a-glance view beyond the Discord event stream. Phase 5.7/6 narrows the
packaged public-v1 behavior to bounded foreground sync: lifecycle one-shot sync
plus explicit Operations Lead reconcile, with no scheduled dashboard reconcile
installed by default.

Create or configure the dashboard only as a visibility mirror. It must read
Issues and source artifacts, then update Project items/fields. It must not
replace assignment, claim, evidence, decision, recovery, or completion truth.
Dashboard timing and sync boundaries are defined in
`docs/company-dashboard-timing.md`.

## Artifact Storage Setup

Status: Repo-local script supported

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

Create a new Work Unit artifact directory with the repo-local script:

```bash
WU_ID=WU-YYMMDD-001
python3 scripts/work_unit_artifacts.py work-unit create \
  --work-unit-id "$WU_ID" \
  --title "<short Work Unit title>" \
  --work-card "<GitHub issue URL or manual smoke artifact>" \
  --operations-lead "main" \
  --team-lead "<team-lead-agent-id>" \
  --output-root ~/.openclaw/state/openclaw-company-ops/work-units
```

The script validates required inputs, creates exactly these four files by
default, and refuses an existing output directory unless `--force` is provided:

```text
assignment.md
claim.md
evidence.md
decision.md
```

Future packaging can expose the same behavior as
`openclaw-company-ops work-unit create`.

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

Status: Repo-local script supported

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

Create or update the JSON-backed ledger with the repo-local script:

```bash
LEDGER=~/.openclaw/state/openclaw-company-ops/claims/ledger.json
python3 scripts/ops_claim_ledger.py claim create \
  --ledger "$LEDGER" \
  --work-unit-id WU-YYMMDD-001 \
  --work-card "<GitHub Issue URL>" \
  --claim-type execution \
  --owner-session-ref "agent=team-lead-1" \
  --expected-state working \
  --expected-until "2026-06-04T10:00:00+09:00" \
  --last-claim "Team Lead is implementing the assigned scope." \
  --assignment-packet ./assignment.md
```

Refresh an existing claim:

```bash
python3 scripts/ops_claim_ledger.py claim update \
  --ledger "$LEDGER" \
  --claim-ref CLAIM-WU-YYMMDD-001-001 \
  --expected-state result_ready \
  --last-claim "Evidence has been submitted for Operations Lead review." \
  --evidence-ref ./evidence.md
```

Inspect claim state:

```bash
python3 scripts/ops_claim_ledger.py claim status --ledger "$LEDGER"
python3 scripts/ops_claim_ledger.py claim status \
  --ledger "$LEDGER" \
  --claim-ref CLAIM-WU-YYMMDD-001-001 \
  --format json
```

Manual claim file example:

```text
Claim ref: CLAIM-WU-YYMMDD-001-001
Work Unit id: WU-YYMMDD-001
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

Future packaging can expose the same behavior as:

```bash
openclaw-company-ops claim update ...
```

## Pulse Monitor Setup

Status: Repo-local script supported, alert-only; scheduled activation deferred

The Pulse Monitor compares the expected responsibility claim with available
OpenClaw/session signals.

Current Phase 5.6 decision: keep Pulse as a manual/foreground stalled-work
detector for now. The existing Dashboard, Discord proof timeline, and
`work-unit inbox --result-ready` are not duplicate alerts; they serve different
visibility and review roles. Do not schedule Pulse just because the command
exists.

Run the repo-local alert-only check against the JSON ledger:

```bash
python3 scripts/pulse_monitor.py pulse check --ledger "$LEDGER"
```

Optionally provide observed session signals as a JSON snapshot:

```json
{
  "active_owner_session_refs": ["agent=team-lead-1"],
  "compaction_counts": {
    "agent=team-lead-1": 2
  }
}
```

```bash
python3 scripts/pulse_monitor.py pulse check \
  --ledger "$LEDGER" \
  --session-snapshot ./session-snapshot.json
```

The check compares:

- Does the owner session still appear active?
- Is the claim older than `expected_until`?
- Did compaction appear to occur without a refreshed claim?

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

Future packaging can expose the same behavior as:

```bash
openclaw-company-ops pulse check --claim-ref <claim-ref>
```

Future trigger-only path, not current setup:

```bash
openclaw cron add company-ops-pulse -- <command>
```

Only revisit scheduled Pulse after real stale-claim/session-mismatch evidence
shows that manual checks and the result-ready inbox miss meaningful unattended
work. If accepted later, prefer a one-shot scheduled `pulse check` over a
long-running daemon and suppress Work Units that are already result-ready or
decided by source artifacts.

Run the non-installing daemon runner in the foreground for bounded smoke/debug:

```bash
python3 scripts/pulse_daemon.py daemon run \
  --ledger "$LEDGER" \
  --session-snapshot ./session-snapshot.json \
  --output-jsonl ~/.openclaw/state/openclaw-company-ops/pulse/events.jsonl
```

Use `--max-runs 1` for a bounded smoke. This runner does not install cron,
launchd, or any background job by itself. Automatic `#ops-alerts` delivery is
also deferred until a separate delivery gate accepts channel, suppression, and
readback behavior.

## Discord Visibility Setup

Status: Repo-local visibility formatter supported, pre-dogfood visibility required

Discord is only a visibility surface. For post-setup dogfood, configure a
minimal Discord visibility path before the first real Work Unit so the owner can
follow the `#ops-feed` request/result timeline and team detail trails directly.

Recommended channels:

- `#ops-lead`: direct owner-to-Operations-Lead planning, phase decisions, and
  handoff preparation.
- `#ops-feed`: owner-facing assignment, completion, and blocker briefing cards.
- `#ops-alerts`: stale claims, suspected session mismatch, and suspected
  compaction recovery.
- `#team-build-pq`: direct questions for the PrimeQuant platform team lead.
- `#team-build-lab`: direct questions for the new product/tooling team lead.
- `#team-market`: direct questions for the market/content team lead.
- `#team-revenue`: direct questions for the revenue/customer team lead.

The owner may ask Team Leads direct questions in these team channels. This is
allowed for status checks, evidence locations, clarification, and early
thinking. It is not a Discord command router unless chat text automatically
mutates Work Cards, claims, assignments, decisions, GitHub state, or execution
state.

Bind routing deliberately:

- one default Operations Lead binding for `#ops-lead`;
- one default Team Lead per team channel;
- no general discussion in `#ops-feed`;
- no assumption that OpenClaw answers unless an agent is bound to the channel;
- no multiple-agent pileup in one team channel.

Verify available OpenClaw messaging commands:

```bash
openclaw message --help
openclaw channels status
```

Format Pulse Monitor alerts before manual posting:

```bash
python3 scripts/pulse_monitor.py pulse check \
  --ledger "$LEDGER" \
  --session-snapshot ./session-snapshot.json \
  --format json > pulse-alerts.json

python3 scripts/discord_ops.py alerts \
  --pulse-json pulse-alerts.json \
  --source-ref "$LEDGER"
```

The repo-local formatter prints Discord-ready text only. It does not send
messages or mutate state.

Manual team-detail event format:

```text
📦 [RESULT_READY] WU-YYMMDD-001 · <team-icon> <team>
Work Card: <GitHub Issue URL>
Assignment: <Assignment Packet ref>
Claim: <Claim ref>
Evidence: <Evidence & Result Record ref>
Next action: Operations Lead가 ACCEPTED 또는 REVISE를 남깁니다.
```

Recommended visibility kinds:

- `#ops-feed`: `ASSIGNED`, `COMPLETED`, `NEEDS_REVISION`, `BLOCKED`.
- `#team-*`: `ASSIGNED_DETAIL`, `STARTED`, `CHECKPOINT`, `RESULT_READY`,
  `ACCEPTED`, `REVISE`, `BLOCKED_DETAIL`.
- `CHECKPOINT` is for long-running live progress between `STARTED` and
  `RESULT_READY`.
- `#ops-alerts`: `CLAIM_STALE`, `SESSION_MISMATCH`,
  `COMPACTION_RECOVERY_SUSPECTED`.

Use stable English for event kinds and internal schema, but use Korean by
default for owner-facing `#ops-feed` cards and internal long-form values.
Public/package examples may use English. For team detail trails, `RESULT_READY`
is not enough to close the trail; Operations Lead review must follow as
`ACCEPTED`, `REVISE`, or `BLOCKED_DETAIL`.

Owner-facing `#ops-feed` cards should use reader-friendly labels instead of
generic formatter fields:

```text
📌 [요청] WU-YYMMDD-001 · <team-icon> <team>
문제: 무엇이 불확실하거나 막혀 있는가.
요청: 누구에게 무엇을 맡겼는가.
기준: 어떤 조건이면 성공 또는 실패로 볼 것인가.
주의: 범위 제한이나 금지사항.
다음: 결과를 받은 뒤 금비가 판단할 일.
```

```text
✅ [완료] WU-YYMMDD-001 · <team-icon> <team>
결과: 팀장이 확인, 생성, 수정, 또는 판단한 핵심 결과.
기준 대비: 요청 기준을 충족했는가.
금비 판정: ACCEPTED, REVISE, or BLOCKED.
확인: 테스트, readback, repo state, evidence 등 핵심 검증.
다음: 다음 액션 또는 추가 조치 없음.
```

Normal visibility should not add another Team Lead execution or LLM
summarization call. Use one Operations Lead composition step per transition to
write the `#ops-feed` card and the `#team-*` detail message from the same facts,
then validate that they do not contradict each other.

Before deterministic formatter guard runs, keep Team Lead and Operations Lead
Discord-facing handoff text within 1,600 characters. Discord content has a
2,000-character hard limit; Company Ops formatter output targets 1,800
characters to leave margin for headers, links, Korean text, and emoji.

Every Discord visibility message must link back to the real artifact or source
reference. Discord must not accept commands that mutate Work Units in v1.

Every official Work Unit still needs the normal artifact trail. A direct team
question becomes official work only after a Work Card, Assignment Packet, claim,
Evidence & Result Record, and Operations Lead Decision are created or updated.

Repo-local card composition is available now. It prints visibility text only and
does not post to Discord:

```bash
python3 scripts/openclaw_company_ops.py discord card --surface team-detail --kind RESULT_READY --work-unit-id <id> ...
```

The foreground `publish-card` publisher sends one card at a time, immediately
reads it back, and records local proof in `visibility-proof.jsonl`. It refuses
duplicate successful card proof unless `--force` is explicit and can check the
expected target/surface before sending. It does not batch-replay a Work Unit
timeline after completion.

Do not add a Discord command router. The implementation is a publisher-only path
that posts source-artifact-backed visibility messages and cannot mutate GitHub,
claims, decisions, assignments, or execution state.

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

Status: Repo-local multi-team smoke supported

Run the bounded repo-local smoke first:

```bash
python3 scripts/company_ops_smoke.py multi-team
```

This creates temporary artifacts and a temporary claim ledger for two Team Lead
owners. It checks artifact generation, two independent claims, an alert-only
Pulse Monitor no-alert pass, and one `result_ready` claim update.

It does not create GitHub issues, post Discord messages, restart agents,
recover sessions, reassign work, or mark real Work Units complete.

Manual implementation smoke can still be used when exercising GitHub Work Cards
and real Team Lead handoffs.

Run this smoke test after setup.

1. Create a demo Work Unit id:

   ```bash
   WU_ID=WU-YYMMDD-001
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

For a local visibility snapshot of current claim state:

```bash
python3 scripts/dashboard_snapshot.py dashboard snapshot --ledger "$LEDGER"
```

Use this as a review aid only. It must not replace Work Cards, Assignment
Packets, claims, evidence, or Operations Lead decisions.

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

## Post-Setup Realization

Status: Active plan

After the base setup and repo-local scripts exist, continue tracking
implementation status in `docs/post-setup-plan.md`. Phases 1-4 and Phase 5.1
have been exercised. Phase 5.2 accepted the narrow repo-local hook guard MVP,
and Phase 5.3 accepted the bounded GitHub Project dashboard sync. Phase 5.5
implemented the foreground result-ready inbox, official result-ready publish
command, and closeout decision lock gate, Phase 5.5a implemented the foreground
handoff amendment dry-run gate, and Phase
5.5b implemented the foreground handoff draft/spec generator dry-run gate.
Phase 5.6 recorded the Pulse activation decision: manual/foreground accepted;
scheduled activation deferred with trigger; daemon install no-go for now. Phase
5.7 recorded the final Phase 6 package boundary: manual/foreground
`pulse check` is implemented and included; scheduled Pulse and daemon
installation remain deferred/no-go; Project and Discord live mutation tools
remain configured foreground-only; hooks remain optional guardrails, not
required runtime state. Phase 5.8.1 through 5.8.4 are implemented in the
repo-local model, including canonical start/result-ready guards, detached
fresh-session dispatch, closeout delegate wake, guarded commit-request
closeout, and foreground-resumable closeout publish staging. Phase 5.8.5
remains the live no-bypass regression gate before Phase 6 packaging begins.

For packaged users, `pulse check` remains a foreground operating command. The
package should expose it through the installed CLI, read the user's local
Company Ops claim ledger by default, and optionally accept a local
session-snapshot file for session mismatch or compaction-suspect checks. The
small Company Ops skill can instruct an Operations Lead to run it at decision
points, but install must not turn it into cron, launchd, daemon, or automatic
alert delivery.

Final completion requires GitHub Project or equivalent dashboard visibility
unless the owner explicitly records a no-go decision with rationale.

## Future CLI And Package Migration

When CLI automation or packaged distribution exists, update this guide in
place.

Current repo-local entrypoint:

```bash
python3 scripts/openclaw_company_ops.py --help
```

This entrypoint routes to the implemented repo-local scripts. It is not yet a
published package. The accepted public-v1 direction is a Company Ops plugin or
package that bundles a small Company Ops skill for natural-language routing and
foreground CLI tools for deterministic source-backed operations. Do not make
user `MEMORY.md` or `AGENTS.md` edits part of the install path.

Until Phase 6, there is no installable distribution target. The current target
is the repo-local model: scripts, docs, protocol references, and templates.
Phase 5.7 has recorded what must be packaged; Phase 6 builds the actual
plugin/package layout.

The packaged runtime should make Company Ops skill/protocol/docs/CLI visible to
both the Operations Lead and Team Lead agents. This is required so Team Leads
can re-check the packet-first protocol, claim/evidence/result formats, and
verification/no-go rules during long work. If Team Leads run in separate
OpenClaw runtimes or workspaces, Phase 6 setup must expose the package there or
return explicit setup-needed steps. Authority remains role-scoped: Operations
Lead owns route, `pulse check`, inbox/closeout, configured Project/Discord
mutation, and owner-facing completion; Team Leads may use shared tools only
within their assigned Work Unit for claim refresh, progress/evidence/result
writing, local verification, and blocker reporting.

Practical role assignment is possible at command/protocol level. Phase 6 should
add CLI guards that require an Operations Lead role context for `pulse check`,
inbox/closeout, Project apply, and Discord publish, while requiring Team Lead
commands to include an assigned Work Unit id and refusing writes outside that
scope. Treat this as fail-closed operating authority, not guaranteed OS-level
per-agent isolation unless the OpenClaw runtime supplies identity/workspace/tool
isolation.

Recommended replacement order:

1. Replace directory/bootstrap commands with `init`.
2. Replace GitHub label/template setup with `github bootstrap`.
3. Replace artifact scaffolding with `work-unit create`.
4. Replace manual claim edits with `claim update`.
5. Replace manual pulse comparison with `pulse check`.
6. Replace manual Discord posting with `discord card` plus foreground
   `discord publish-card`; keep publisher proof explicit in
   `visibility-proof.jsonl` and do not add a hidden bridge.
7. Use the implemented `work-unit inbox --result-ready`,
   `work-unit result-ready --dry-run/--publish`, optional
   `work-unit delegate-wake --dry-run/--publish`, and guarded
   `work-unit closeout --dry-run/--publish --commit-request <json|@path>`
   commands before scaling multi-Work Unit result recovery. The implementation
   scans only local Work Unit source artifacts and treats Project/chat surfaces
   as mirrors, not inbox sources.
8. Add the accepted `work-unit draft-handoff --spec draft-input.json --dry-run`
   helper only as a review-only Operations Lead drafting surface. It must expose
   missing judgment fields as `needs-ops-decision` and validate completed output
   through the existing `work-unit handoff --dry-run` path rather than becoming
   an alternate handoff source of truth.
9. Keep scheduled Pulse activation deferred unless the Phase 5.6 trigger is
   later met. If accepted, use one-shot scheduled `pulse check`, not a
   long-running daemon by default, and suppress result-ready/decided Work Units.
10. Defer a conservative `route --intent <text>` helper until after the
   result-ready inbox and closeout-lock path are stable. Add it only if it
   remains deterministic and can return `needs-ops-decision` when ambiguous.
11. Package the accepted surfaces as a plugin/package with a bundled small skill
   now that Phase 5.7 has locked the included and deferred surfaces.
12. Replace the manual smoke test with `smoke`.

Do not leave manual commands as an alternate legacy operating path after the
supported command is available. Keep only emergency diagnostics and explicit
manual repair notes.

Permission and guardrail requirements for Phase 6:

- `project-sync apply` must stay fail-closed: it requires an apply-ready local
  field map, GitHub issue or pull request Work Card URLs, and `gh auth` with
  the `project` scope before any Project mutation.
- `discord publish-card` and `publish-sequence` must stay explicit foreground
  commands. They require a target and proof log, can enforce expected
  target/surface before send, record incomplete proof on send/readback failure,
  and must not treat Discord as source truth.
- Optional hooks may block clear red-line commands or malformed source
  artifacts, but Company Ops must remain usable without hooks installed. Hooks
  must not store operating state, publish messages, run Project sync, or decide
  Work Unit status.

Public-v1 setup/preflight guidance:

- The install guide should include a foreground setup check for Project and
  Discord readiness. Phase 6 should include a `doctor`/`preflight` helper if it
  only reports readiness and next steps.
- Project readiness means: existing Project selected, field map generated from
  that Project, required field ids/options present, GitHub auth includes
  `project` scope, and source Work Cards are GitHub Issue/PR URLs.
- Discord readiness means: explicit ops-feed/team-detail targets are known,
  `publish-card` can be run with expected target/surface checks, proof-log
  paths are writable, and readback is available.
- The setup check must not create or bind external resources automatically.
  Missing readiness should fail only the external mirror/proof action, not the
  source-backed Work Unit flow.
- The helper should also check package/CLI availability, role-context config,
  source artifact/template paths, claim ledger readability, foreground
  `pulse check` viability, stale Project mirror hygiene, and literal escaped
  newline issues in generated Work Card bodies. Report `OK`, `WARN`, or
  `BLOCKED` with exact next steps. Keep text output for humans and JSON output
  for smoke tests.
- Do not let `doctor` or `preflight` become an auto-fix wizard. It must not
  grant OAuth scopes, create Projects, create Discord channels, choose targets,
  publish cards, archive Project items, start scheduled jobs, bind Team Lead
  agents, or mutate source artifacts.
