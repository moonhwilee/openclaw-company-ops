# Operations Manual

Status: Manual Day-0

This manual explains how to run OpenClaw Company Ops day to day before the
planned automation exists.

It is an operating manual, not an installation guide. For setup status and
planned components, see `docs/setup-guide.md`. For a follow-along manual
implementation path, see `docs/implementation-setup-guide.md`.

## Operating Chain

```text
Owner -> Operations Lead -> Team Lead OpenClaw Agent -> Subagents
```

- Owner states goals, priorities, constraints, and final business direction.
- Operations Lead turns those goals into Work Units, assigns Team Leads,
  reviews evidence, and records decisions.
- Team Lead OpenClaw Agent owns exactly one Work Unit at a time and directly
  manages its own subagents.
- Subagents support the Team Lead. They do not report directly to the
  Operations Lead.

A Work Unit is not an actor. It is the task unit owned by a Team Lead session.

## Main Session Nonblocking Rule

The Operations Lead main session must not sit idle waiting for sizeable Team
Lead work.

Any owner request that uses a `goal` protocol, a standalone `verify` protocol
with Team Lead or subagent work, or any other multi-step delegated execution
must be converted into a detached Work Unit before the Team Lead starts. The
handoff must leave enough source-backed state for the Operations Lead to resume
without relying on chat memory:

- Work Card or explicit Work Card plan.
- Assignment Packet with done and verification criteria.
- Ops Claim Ledger entry or claim artifact with expected state.
- Owner-facing and team-detail assignment visibility when the Work Unit is
  live-visible.
- Dashboard mirror sync when configured.

After that handoff, the main session may handle other owner requests. A
detached Work Unit remains owned by the assigned Team Lead until the Operations
Lead later reviews the submitted evidence and records a decision.

Route owner requests through one of three paths:

- `ops-direct`: Direct Operations Lead response. Use for small generic questions, tiny local
  checks, or reversible actions where specialist continuity does not help.
- `team-qna`: Direct Team Lead Q&A. Use for small domain-specific questions where the
  matching Team Lead's standing persona and channel context improve judgment or
  preserve Operations Lead context. This is advisory/status/clarification only.
- `detached-wu`: Detached Work Unit. Use for official delegated execution, `goal`, standalone
  `verify`, subagent delegation, code changes, external mutation, live
  visibility, multi-step verification, or anything that needs durable state.

The routine exception to detached Work Unit handling is therefore not "small
means direct." It is "small and advisory may be direct or Team Lead Q&A; official
delegated work becomes a detached Work Unit."

These route labels are the canonical deployable routing surface. Tooling,
templates, smoke tests, and future Discord/team-channel bindings should use the
same labels instead of inventing synonyms. Routing is an Operations Lead
decision; do not add an automatic classifier unless it is explicitly accepted in
a later implementation phase.

Do not use a hidden background orchestrator to satisfy this rule. The detached
state is the Work Unit source artifacts, proof/progress logs, claim state, and
dashboard mirror.

## Work Unit Handoff Change Rule

The initial handoff is a source-backed starting contract, not a promise that
every execution detail is frozen forever.

Treat these parts as stable identity and audit facts:

- Work Unit id.
- Work Card.
- Original owner request and business intent.
- Assigned Team Lead and Operations Lead.
- Protocol mode, safety constraints, and no-go boundaries.
- Original handoff timestamp and proof trail.

Treat these parts as changeable only through an explicit source-backed
amendment or revision note:

- Execution plan.
- Narrow scope details.
- Inputs and assumptions.
- Done criteria or verification criteria.
- Target artifact paths, if the original target becomes wrong.

When the Team Lead discovers a new issue during execution:

1. If the issue is inside the existing scope, record it in progress/checkpoint
   evidence and continue the selected protocol.
2. If the issue changes scope, done criteria, verification criteria, risk, cost,
   or required authority, pause the affected slice and request an Operations
   Lead amendment decision.
3. The Operations Lead may amend the Assignment Packet, record a revision note,
   split out a new Work Unit, mark the current Work Unit `REVISE`/blocked, or
   ask the owner for direction.
4. Do not silently rewrite the original handoff as if the earlier decision never
   existed. Keep the original packet and proof trail auditable, update
   `Updated at`, and point to the amendment or revised packet.
5. Dashboard and Discord updates are mirrors of the source-backed amendment;
   they do not create the amendment by themselves.

Phase 5.5a's first helper is only a planning surface:
`work-unit amend --spec amendment.json --dry-run`. It must not edit the
original Assignment Packet, write an amendment artifact, publish Discord,
mutate Project, or decide the change. Source-backed recording of an amendment
requires a later explicit acceptance path.

Rule of thumb: a plan can change, but the change needs a visible source-backed
reason. The Team Lead can replan within the Assignment Packet; the Operations
Lead owns scope and closeout changes.

## Result Ready Inbox Rule

Team Lead results are inputs for Operations Lead review, not automatic
completion.

If a Team Lead result arrives while the main session is handling another owner
request, OpenClaw message routing determines when that notification is delivered
to the Operations Lead. This rule does not reorder OpenClaw inbound messages.
It defines how the Operations Lead recovers and processes ready results after
delivery: finish or pause the active owner request first, then process ready
results from the source-backed inbox. The inbox is the set of Work Units whose
claim or evidence state is `result_ready` and whose team-detail trail has a
valid `RESULT_READY` proof when live visibility is required.

The inbox is discovered from local source artifacts only: Work Unit directories
under the configured artifact root, `claim.md`, `evidence.md`, `decision.md`,
`progress.jsonl`, and `visibility-proof.jsonl`. GitHub Project fields, Discord
or Telegram history, GitHub comments, and OpenClaw session history are mirrors
or delivery surfaces. They must not create a ready item by themselves.

Process pending Team Lead results one at a time in a deterministic order:

1. Earliest valid `RESULT_READY` proof timestamp.
2. Then claim `updated_at` timestamp when proof time is unavailable.
3. Then Work Unit id as a final tie-breaker.

Before closing any result, the Operations Lead must reread the Assignment
Packet, evidence, claim, proof/progress logs, and current dashboard dry-run.
Never decide from the remembered chat transcript alone.

Race control:

- Only the Operations Lead may record `ACCEPTED`, `REVISE`, or
  `BLOCKED_DETAIL` and owner-facing `COMPLETED`, `NEEDS_REVISION`, or
  `BLOCKED`.
- Team Lead result arrival must not mutate GitHub Project, close Work Cards,
  publish owner completion, or overwrite decisions by itself.
- Run one closeout at a time. Project sync already uses a lock; source decision
  artifacts are single-writer Operations Lead outputs. The foreground
  `work-unit closeout --dry-run` command uses a Work Unit-specific closeout lock
  and re-checks whether a final decision already exists before planning any
  later write.
- The closeout lock is a short-lived command guard, not a durable workflow
  owner. If the lock already exists, the command should fail before mutation and
  report the lock path; force-unlock behavior requires a separate stale-lock
  policy.
- If a duplicate or stale Team Lead result arrives after a decision exists,
  compare it to the existing source artifacts and report it as stale or a
  revision request. Do not reopen or overwrite accepted work automatically.
- If the source trail contains competing final reviews for the same Work Unit,
  or duplicate result-ready evidence with conflicting timestamps or sources,
  report `needs-ops-decision` and require Operations Lead review instead of
  choosing a winner automatically.
- If two results race for different Work Units, process both through the same
  deterministic inbox order. If two results race for the same Work Unit, the
  first valid Operations Lead decision wins until the owner explicitly asks for
  a revision or reopen.

## Operating Surfaces

Use the smallest surface that preserves truth and visibility.

For every Team Lead delegation, the required visibility surfaces are:

- CLI Team Lead assignment and result.
- `#ops-feed` owner-facing assignment and result summaries.
- Relevant `#team-*` detailed execution trail.
- Operations Lead final report with lightweight verification and judgment.

All Team Lead delegations are audit-visible. The Discord flow does not split
into normal and formal message modes. Only the depth of source artifacts varies
with task risk.

For work that changes source, affects operations, carries external/cost risk,
or needs later audit, also use these source artifacts together. None of them
may replace another required artifact:

- Work Card: shared GitHub Issue for the Work Unit.
- Assignment Packet: detailed handoff from Operations Lead to Team Lead.
- Ops Claim Ledger Entry: expected responsibility record.
- Evidence & Result Record: proof bundle for review.
- Operations Lead Decision: final accept, revise, hold, or reject decision.

Visibility surfaces such as GitHub labels, GitHub Projects, saved issue views,
or Discord messages must point back to these artifacts. They are not source
artifacts.

For Discord-specific event conventions, see
`docs/discord-event-visibility.md`.

For the active post-setup sequence, see `docs/post-setup-plan.md`. In that
sequence, Discord visibility is checked before the first real dogfood Work Unit
is accepted, so the owner can observe orchestration transitions directly.

## Default Delegation Path

Use `CLI-first + #ops-feed owner summary + #team-* detail trail` as the default
delegation path.

The default flow is:

1. Operations Lead posts one owner-facing `[ASSIGNED]` summary in `#ops-feed`.
2. Operations Lead posts one `[ASSIGNED_DETAIL]` entry in the relevant
   `#team-*` channel.
3. Operations Lead assigns the Team Lead through CLI or a local agent session.
4. Operations Lead posts `[STARTED]` when the Team Lead starts or claims the
   work.
5. For long `goal` work, Operations Lead runs `work-unit checkpoint` at major
   slice boundaries or at least every 10-15 minutes while work remains active.
   This publishes/readbacks the team `CHECKPOINT`, then records matching
   source-backed `progress.jsonl` metadata and can run one Project mirror sync.
6. For standalone progress metadata without Discord visibility, Operations Lead
   may still use `work-unit progress`, but it must not replace the normal
   checkpoint briefing path during live long work.
7. Operations Lead posts `[RESULT_READY]` when the Team Lead result is actually
   available.
8. Operations Lead performs lightweight verification before final reporting.
9. Operations Lead posts the detailed `[ACCEPTED]`, `[REVISE]`, or
   `[BLOCKED_DETAIL]` review note in the relevant `#team-*` channel.
10. Operations Lead posts one owner-facing `[COMPLETED]`, `[NEEDS_REVISION]`,
   or `[BLOCKED]` summary in `#ops-feed`.

`[RESULT_READY]` is a Team Lead result-submission signal, not an Operations
Lead decision. A Team Lead delegation is visibility-incomplete if the relevant
team channel stops at `[RESULT_READY]`. Before reporting completion, the
Operations Lead must close the team detail trail with `[ACCEPTED]`, `[REVISE]`,
or `[BLOCKED_DETAIL]`, and then close the owner-facing timeline in `#ops-feed`
with `[COMPLETED]`, `[NEEDS_REVISION]`, or `[BLOCKED]`.

The Discord messages are visibility only. They show the owner what was assigned,
what changed, what result came back, and where to inspect detail, but they do
not create, mutate, approve, close, reassign, recover, or complete Work Units.

After the Operations Lead accepts a result, the matching GitHub Project item
stays visible as `Accepted` for owner final review. Archive the Project item and
close the Work Card only after the owner has had a reasonable chance to inspect
it, explicitly says it can be cleared, or the item is a completed sample/internal
smoke test. Project archive clears active dashboard clutter; it does not delete
the source artifact trail.

The expected Team Lead result should include a short result summary,
verification summary, changed artifact list, blocker if any, and next action.
This avoids a second Team Lead execution or LLM summarization call for normal
visibility.

The Operations Lead should use one composition step per operating transition,
but should write separate messages for separate readers:

- Assignment transition: one owner-facing `#ops-feed` request card and one
  detailed `#team-*` assignment message.
- Review/completion transition: one detailed `#team-*` review message and one
  owner-facing `#ops-feed` completion or blocker card.

These messages share a fact packet, but they are not the same event text
rendered twice. `#ops-feed` is the owner's briefing timeline. `#team-*` is the
Team Lead execution and review trail.

When the assignment handoff requires both owner-facing and team-detail
visibility cards, publish them as a validated serial sequence. The owner-facing
`#ops-feed` assignment must be sent and read back before the team detail
handoff. Do not parallelize multi-card assignment handoffs.

Live dogfood and verify runs must execute from the current Company Ops
contract: the owner request, this manual, the active protocol capsule, source
artifacts, and deterministic scripts. Prior smoke artifacts are regression
references only. They must not be treated as an answer key for a live operating
test.

Use stable English for event kinds and internal schema, and Korean by default
for owner-facing `#ops-feed` card content and internal long-form
human-readable values. Public/package documentation, CLI help text, and
reusable release examples may use English. Do not show `Public summary`,
`Surface`, raw `Source`, or mechanical `Owner` fields in normal internal
`#ops-feed` posts.

Owner-facing `#ops-feed` cards use reader-friendly labels:

- Request: `문제`, `요청`, `기준`, optional `주의`, optional `근거`, `다음`.
- Completion: `결과`, `기준 대비`, `금비 판정`, `확인`, optional `근거`,
  `다음`.
- Blocker: `문제`, `원인`, `필요`, optional `근거`, `다음`.

When a source reference is useful for the owner, show it as a human-readable
`근거` line. Do not expose a raw `Source:` field in `#ops-feed`.

Team detail messages may use operational labels such as `Goal`, `Scope`,
`Criteria`, `Cautions`, `Result`, `Evidence`, `Verification`, `Decision`,
`Reason`, and `Next`.

Keep a lightweight final judgment. The Operations Lead still checks that the
result matches the request, required smoke or tests passed, and repo state is
not misleading. For small delegated tasks this judgment lives in the final
report, such as `Verification: pass` and `Decision: accept`; it does not require
a separate decision artifact.

If a Discord visibility send fails, say that the visibility send failed. Do not
create a fallback truth source, do not pretend Discord visibility was achieved,
and do not route commands through another surface to compensate. The source of
truth remains the repo artifacts, checks, and final Operations Lead report.

Live visibility requires timing, not just content. A final burst of correct
Discord cards after all work is complete is not a successful visible run. It is
only formatter or replay proof. For long `goal` work, checkpoint messages must
be sent and read back while the work is still active.

Discord-bound execution is no longer the default path. Use it only for route
diagnostics, owner-authored Q&A smoke tests, or a deliberate experiment where
the team channel itself must be the execution conversation surface.

For all paths, Discord is visibility-only and publisher-only. It must not create,
mutate, approve, close, reassign, recover, or complete Work Units.

## Manual Cost Budget

Use this budget against the default `cli-direct` baseline.

Additional default visibility cost:

- `#ops-feed` assignment summary and matching team detail: about ten to thirty
  seconds when manually posted.
- `#ops-feed` completion or blocker summary and matching team detail: about
  twenty to sixty seconds when manually posted.
- Expected additional cost over the CLI-first flow: roughly thirty to ninety
  seconds while posting is manual.
- Long `goal` checkpoint cost: roughly one short send/readback cycle per major
  slice or every 10-15 minutes. This should not add an LLM call.
- Long Work Unit `Progress` dashboard cost: one small `progress.jsonl` append
  and changed-only `project-sync` update from source artifacts. This should not
  add a Team Lead, summary LLM call, daemon, or fallback state store.
- Short Work Unit dashboard display may use proof-derived lifecycle projection
  from local `visibility-proof.jsonl` when no `progress.jsonl` row exists. This
  is a mirror display only, should be a compact lifecycle label, and should not
  infer phase/round detail.

Do not add a second Team Lead or LLM summarization call for visibility. Use one
Operations Lead composition step per transition to write both the owner-facing
`#ops-feed` card and the detailed `#team-*` message from the same facts. A
deterministic validator should check Work Unit id, team, decision, next action,
team-final-review-before-ops-completion, and absence of internal fields in
`#ops-feed`.

The approved P0 publisher shape is the foreground `publish-card` command. It
sends one explicit formatted card, immediately reads it back, and appends local
proof to the Work Unit `visibility-proof.jsonl`. It refuses duplicate
successful proof unless `--force` is explicit and can validate expected
target/surface before sending. It must not decide channels by reading message
content, batch-replay a Work Unit timeline after completion, mutate state,
approve results, retry in the background, or become a command router.

One-time route diagnostics may still add one short Team Lead LLM response when
testing a new Discord channel, thread, binding, agent, or suspected stale
session. That diagnostic is not part of normal delegation cost.

## Direct Owner Questions To Team Leads

The owner may ask Team Lead OpenClaw Agents direct questions in the relevant
team Discord channel.

This is allowed for:

- Status checks.
- Evidence or artifact location questions.
- Clarifying technical, market, or revenue judgment.
- Exploring whether something should become a Work Unit.

Direct Team Lead answers do not bypass the Operations Lead decision path. A
direct Discord message may explain state or link evidence, but it must not
automatically create, close, approve, reassign, recover, or mutate a Work Unit.

If a direct question becomes official delegated work, convert it into the
normal operating trail: Work Card, Assignment Packet, Ops Claim Ledger entry,
Evidence & Result Record, and Operations Lead Decision.

## Standard Manual Loop

1. Owner states a goal or problem.
2. Operations Lead decides whether it should become an official Work Unit or a
   smaller delegated task.
3. Operations Lead sends the Team Lead a CLI-first assignment.
4. Operations Lead posts `[ASSIGNED]` in `#ops-feed`.
5. Operations Lead posts `[ASSIGNED_DETAIL]` in the relevant team channel.
6. Team Lead executes the work and reports back with a concise result summary,
   verification summary, changed artifact list, and next action when possible.
7. Operations Lead posts team detail trail entries as claim, progress, result,
   and review information become available.
8. Operations Lead verifies the result at the level required by the task.
9. Operations Lead posts `[ACCEPTED]`, `[REVISE]`, or `[BLOCKED_DETAIL]` in the
   relevant team channel.
10. Operations Lead posts `[COMPLETED]` or `[BLOCKED]` in `#ops-feed`.
11. Operations Lead reports the final result with lightweight verification and
   accept/revise/hold judgment.

For normal official Work Units, prefer the foreground handoff command over
manually assembling the initial assignment trail:

```bash
python3 scripts/openclaw_company_ops.py work-unit handoff --spec handoff.json --dry-run
python3 scripts/openclaw_company_ops.py work-unit handoff --spec handoff.json --publish
```

The handoff command is only an initial assignment assembler. It creates or
verifies the Work Card, renders the Assignment Packet and source artifacts,
prepares `#ops-feed [ASSIGNED]` plus `#team-* [ASSIGNED_DETAIL]`, publishes
ops-feed first, then publishes team-detail only after ops readback succeeds.
It must not infer scope from prose, execute the Team Lead's work, publish
checkpoints/results/decisions, retry in the background, or treat Discord/GitHub
Project as source truth.

For higher-risk delegated work, also create the Work Card, Assignment Packet,
Ops Claim Ledger entry, Evidence & Result Record, and Operations Lead Decision.
These artifacts are required before closing a Work Card, but Discord detail
trail is always required for Team Lead delegation even when a separate Work
Card is not created.

If any required artifact is missing, mark the Work Unit blocked instead of
substituting a GitHub comment, Discord message, PR summary, or dashboard field.

## Work Card Rules

The Work Card is the shared task card. It should be short and link to deeper
artifacts.

It should include:

- Work Unit id.
- Goal.
- Assigned Team Lead OpenClaw Agent.
- Assignment Packet reference.
- Done criteria.
- Evidence & Result Record reference when available.
- Operations Lead decision reference when available.

It should not include every execution detail. If the Assignment Packet is
missing or unreadable, the Work Unit is blocked.

GitHub comments are not the routine progress log. Do not use comments for
`ASSIGNED`, `STARTED`, heartbeat, stale-claim, result-ready, or closure updates.
Use the Work Card body, labels, Assignment Packet, Ops Claim Ledger entry,
Evidence & Result Record, and Operations Lead Decision instead. Reserve comments
for human review notes or external collaborator context that cannot live in
those artifacts.

## Label Meanings

GitHub labels are visibility signals only.

- `work-unit`: this issue is a Work Unit.
- `assignment-ready`: Assignment Packet exists and the Work Unit can be picked
  up.
- `working`: Team Lead is actively working the Work Unit.
- `blocked`: required input, artifact, permission, or decision is missing.
- `result-ready`: Team Lead submitted an Evidence & Result Record.
- `decision-needed`: Operations Lead needs to review and decide.
- `done`: Work Card can be closed or has been closed after evidence and
  decision were linked.

Labels do not prove completion. They must not replace the claim, evidence, or
decision artifacts.

## Assignment Packet Rules

The Assignment Packet is required before execution starts.

It must include:

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

The Team Lead should be able to execute the Work Unit from this packet without
relying on unstated context.

## Claim Rules

The Ops Claim Ledger Entry records expected responsibility.

It should answer:

- Who owns the next action?
- What state is expected?
- Until when is that expectation fresh?
- What artifact links support that expectation?

The claim is not progress truth, completion truth, a dashboard database, or a
recovery mechanism. If the claim goes stale, the Operations Lead reviews the
state and records a decision or next action manually.

## Evidence Rules

No evidence means no completion.

Evidence may include:

- PR links.
- Test output.
- Reports.
- Source links.
- Screenshots.
- Generated artifacts.
- Review notes.
- Remaining risks.

The Evidence & Result Record must map result evidence back to the Assignment
Packet done criteria. Status claims alone are not evidence.

## Decision Rules

The Operations Lead decision must be explicit.

Allowed decisions:

- `accept`: evidence satisfies the Assignment Packet.
- `revise`: result is useful but needs changes.
- `hold`: decision is blocked by missing evidence, dependency, or context.
- `reject`: result does not satisfy the Assignment Packet.

Only `accept` can lead to Work Card closure. A merged PR, green check, label, or
Discord update is not enough unless the Evidence & Result Record and Operations
Lead decision are linked.

## Blocked Work

Use `blocked` when:

- Assignment Packet is missing or unreadable.
- Required input is missing.
- Permission or environment access is missing.
- Evidence cannot be produced.
- The Team Lead cannot verify the result.
- The Operations Lead decision is waiting on unresolved context.

Blocked work should include the blocker, owner of the next action, and the next
review time.

## Stale Work

Manual Day-0 stale checks are performed by the Operations Lead.

Review a Work Unit when:

- The claim is older than the expected window.
- The Team Lead has not refreshed the claim after compaction or interruption.
- The Work Card label and claim disagree.
- Evidence is missing after the Team Lead reports completion.
- A blocker has no owner or next review time.

Future Pulse Monitor automation may alert on stale claims, session mismatches,
or suspected compaction recovery issues. It must remain alert-only.

## No Legacy / No Fallback

These rules apply to every Work Unit:

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

If the real artifact is missing, the correct state is `blocked`.

## Dashboard Timing

Do not create a Company Dashboard just because the structure exists.

Create a GitHub Project or other dashboard only when there are enough active
Work Cards or repositories to make cross-work visibility useful. The dashboard
must remain a visibility layer that points back to Work Cards, Assignment
Packets, claims, evidence, and decisions.

Detailed timing criteria are documented in
`docs/company-dashboard-timing.md`.

## Reference Dry Run

The first manual dry run is:

- Work Unit: `WU-20260604-001`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/4
- Artifacts: `docs/examples/manual-dry-run/WU-20260604-001/`

Use it as a worked example of the manual loop, not as a runtime implementation.

The second manual dry run is:

- Work Unit: `WU-20260604-002`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/6
- Artifacts: `docs/examples/manual-dry-run/WU-20260604-002/`
- Output: `docs/discord-event-visibility.md`

The third manual dry run is:

- Work Unit: `WU-20260604-003`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/8
- Artifacts: `docs/examples/manual-dry-run/WU-20260604-003/`
- Output: `docs/company-dashboard-timing.md`

The fourth manual dry run is:

- Work Unit: `WU-20260604-004`
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/10
- Artifacts: `docs/examples/manual-dry-run/WU-20260604-004/`
- Output: `docs/implementation-setup-guide.md`

The active post-setup plan is:

- `docs/post-setup-plan.md`
