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

## Shared Capability And Role Authority

Company Ops skill, protocol docs, templates, and CLI are shared capabilities in
the packaged runtime. The Operations Lead and Team Lead agents should be able
to read the same packaged Company Ops references and call the same installed
entrypoint when their role permits it. If those agents run in separate
OpenClaw runtimes or workspaces, packaging/setup must expose the same package
to each runtime or return a clear setup-needed checklist. This prevents Team
Leads from depending only on chat memory or a perfectly copied assignment
prompt during long work, compaction, or verification.

Shared capability does not grant shared authority:

- Operations Lead authority: route owner requests, create and amend Assignment
  Packets, run `pulse check` for operating review, process result-ready inbox,
  record closeout decisions, run configured Project/Discord mutation, and send
  owner-facing completion.
- Team Lead authority: execute only the assigned Work Unit, follow the
  Assignment Packet and Protocol Capsule packet-first, refresh its own claim,
  run local verification, write progress/evidence/result artifacts, and report
  blockers.

The Assignment Packet and Protocol Capsule remain the enforcement surface for a
Team Lead. If a Team Lead can access the shared CLI, it must still stay within
the assigned Work Unit scope and must not perform Operations Lead decisions,
automatic recovery, reassignment, completion, Project mutation, or owner-facing
visibility. Phase 6 packaging should add role-scoped command guards to make
these authority boundaries fail closed, but the operating rule already applies
here.

Practical Phase 6 guards can be command-level rather than OS-level security:
Operations Lead-only commands should require an Operations Lead role context
and fail closed without it, while Team Lead commands should require an active
assigned Work Unit id and refuse writes outside that Work Unit. Do not describe
this as hard per-agent isolation unless the OpenClaw runtime explicitly
supports separate agent identity, workspace, and tool-exposure enforcement.

Role context should be resolved in a predictable order: explicit command input,
then environment, then local config. Missing or conflicting role context is a
blocked state, not a reason to infer authority from chat history, Project
status, Discord channel, or the current shell. Operations Lead-only mutation
commands include result-ready inbox review, closeout decisions, Project
apply/reconcile, Discord publish, Pulse operating review, and owner-facing
completion. Team Lead mutation commands are limited to the assigned Work Unit:
claim refresh, progress/evidence/result writes, local verification references,
and blocker reports. Read-only status, docs, help, and smoke checks may stay
role-neutral when they do not change operating state.

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

Detached Work Unit dispatch is bounded by the general
[capacity policy](capacity-policy.md). Company Ops reserves two OpenClaw
concurrency slots outside its active Work Unit cap so the Operations Lead main
session, owner requests, result-ready/closeout handling, hooks, and exceptional
operating work can still run. Capacity is checked from source artifacts and
OpenClaw host config; dispatch must fail closed when the active Work Unit cap is
full.

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

Phase 5.5a's implemented helper is only a planning surface:
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
valid `RESULT_READY` proof when live visibility is required. If `claim.md` says
`result_ready`, the referenced Evidence & Result Record must exist and must not
still be `Draft` or `Pending`. Progress rows used around a ready transition must
not point at missing local `source_ref` files.

The inbox is discovered from local source artifacts only: Work Unit directories
under the configured artifact root, `claim.md`, `evidence.md`, `decision.md`,
`progress.jsonl`, and `visibility-proof.jsonl`. GitHub Project fields, Discord
or Telegram history, GitHub comments, and OpenClaw session history are mirrors
or delivery surfaces. They must not create a ready item by themselves.

Official `STARTED` publication should use `work-unit start --dry-run` before
`work-unit start --publish`. The command validates the local source reference,
previews the STARTED card and claim/progress changes, then records a
source-backed `started` progress row and moves the claim to `working` only on
publish. When the Assignment Packet uses a live Discord-bound execution route,
the command must also publish/read back the team-detail `STARTED` proof.

Official detached execution reference recording should use
`work-unit dispatch --dry-run` before `work-unit dispatch --publish`. Dispatch
does not create a new lifecycle state and does not replace `start`; it requires
prior source-backed STARTED evidence, prepares the Team Lead dispatch packet,
and records a recoverable session/job/message reference in `dispatch.json` plus
a `dispatched` progress row only on publish.

Dispatch also applies the Company Ops active Work Unit cap from
[`docs/capacity-policy.md`](capacity-policy.md). A capacity-full dispatch writes
no source artifacts and starts no runtime path.

Detached dispatch is fire-and-forget by default. After `dispatch --publish`
returns accepted runtime proof and records `dispatch.json`, the Operations Lead
must send a handoff/status report and stop foreground waiting. The main session
must not wait for `RESULT_READY`, closeout delegate judgment, `ACCEPTED`, or
`COMPLETED` unless the owner explicitly requested live protocol observation or
manual recovery. Later review resumes from source artifacts, proof/progress
logs, the result-ready inbox, or `delegate-wake`.

For `--runtime record-ref`, dispatch records a manually obtained
`--session-ref`, `--job-ref`, or `--message-ref`. For
`--runtime openclaw-agent`, manual refs are not enough: the runtime adapter must
return accepted/readback proof before source artifacts are written. The smoke
adapter is `--adapter fake`; live OpenClaw delivery should use
`--adapter command` or `COMPANY_OPS_DISPATCH_ADAPTER_COMMAND` with
`scripts/openclaw_dispatch_sessions_send.py`. The standard adapter runs a short
`openclaw agent --json` turn against the target Team Lead session to receive
the accepted envelope, then enqueues the execution message through Gateway
`sessions.send` with `timeoutMs=0`. Embedded `openclaw agent` fallback output
and synthetic session/job/message references are not dispatch proof; the
adapter must return real Gateway acceptance and execution references. If no
detached runtime adapter is configured, automatic dispatch requests must fail
closed as `setup-needed` instead of spawning a hidden orchestrator, daemon,
auto-retry loop, or automatic completion path.

Live OpenClaw dispatch uses the derived fresh Work Unit-specific Team Lead
session key by default. Reusing a known busy shared Team Lead session is not a
reliable dispatch path: the acceptance prompt can be processed later after the
adapter has already failed closed. `--runtime openclaw-agent` therefore rejects
non-derived session keys unless the operator passes `--allow-custom-session-key`
for an intentional existing/custom session. A busy/timeout path must write no
`dispatch.json` and append no `dispatched` progress row. `sessions.describe` and
`sessions.list` are useful diagnostics, but they are not a lock, lease,
queue-depth proof, or dispatch success condition.

Official `RESULT_READY` publication should use
`work-unit result-ready --dry-run` before `work-unit result-ready --publish`.
The command runs the shared Result Ready gate before publishing. The gate
requires a prior `started` source event, and live Discord-bound routes require a
valid team-detail `STARTED` proof. After publishing, the gate also requires the
live `RESULT_READY` readback proof. This prevents the circular failure where
RESULT_READY proof is required before the command has had a chance to create it,
while still blocking result-ready submissions for Work Units that never started.

For detached Work Units, `result-ready --publish` may also enqueue a fresh
Work Unit-scoped closeout delegate session after successful RESULT_READY
publish/readback:

```bash
python3 scripts/openclaw_company_ops.py work-unit result-ready \
  --work-unit-id <id> \
  --result "..." \
  --evidence <source-ref> \
  --verification "..." \
  --publish \
  --closeout-delegate-runtime openclaw-agent \
  --closeout-delegate-agent main \
  --closeout-delegate-adapter command \
  --closeout-delegate-adapter-command "python3 scripts/openclaw_closeout_delegate_sessions_send.py"
```

The default closeout delegate runtime is `none`, so existing result-ready
publication remains unchanged unless the operator requests the wake path. The
v1 delegate agent is the allowlisted `main` agent in a fresh Work Unit-scoped
session, with an injected closeout-delegate prompt. Unknown agents and the
assigned Team Lead agent are setup-needed, not fallback routes. The delegate
adapter must return current accepted/enqueued proof, including a recoverable
session/job/message reference and confirmation that the delegate is bound to
guarded closeout only. The delegate execution turn prepares
`closeout-commit-request.json`, runs guarded closeout dry-run, and may publish
only through the guarded closeout command when all red-line categories are
clear. It must not write `decision.md` directly, mutate Project final status
directly, publish final Discord cards directly, archive, cleanup, or reassign.
`--closeout-delegate-adapter fake` is a smoke/local contract fixture, not a
production path. Production wake should use the configured command adapter,
usually through `COMPANY_OPS_CLOSEOUT_DELEGATE_ADAPTER_COMMAND`.
Delegate execution enqueue keys include the payload hash and prompt version, so
an intentional foreground `delegate-wake --force` can replay after a corrected
payload or delegate prompt without reusing a stale execution result.

If RESULT_READY publish succeeds but delegate wake fails, do not roll back
RESULT_READY and do not fake closeout. Treat the result as still visible in
`work-unit inbox --result-ready`, then recover with the foreground
`work-unit delegate-wake --dry-run/--publish` path after adapter setup is fixed.
The Team Lead waits only for RESULT_READY readback and delegate enqueue proof;
it must not wait for delegate judgment or final closeout completion.
If a readback-ok RESULT_READY proof already exists, `result-ready --publish`
fails closed unless the operator passes `--force` for an intentional duplicate
publication. Do not use `--force` to paper over a confused Team Lead rerun.

After terminal closeout proof exists, recovery work must be read-only by
default. Do not rewrite `evidence.md`, `decision.md`, proof logs, or closeout
artifacts after `ACCEPTED`/`COMPLETED` unless the owner explicitly approves an
artifact repair. If a post-closeout inconsistency is found, record a separate
follow-up Work Unit or recovery note instead of changing the closed evidence
chain.

Process pending Team Lead results one at a time in a deterministic order:

1. Earliest valid `RESULT_READY` proof timestamp.
2. Then claim `updated_at` timestamp when proof time is unavailable.
3. Then Work Unit id as a final tie-breaker.

Before closing any result, the Operations Lead must reread the Assignment
Packet, evidence, claim, proof/progress logs, and current dashboard dry-run.
Never decide from the remembered chat transcript alone.

Operations Lead result-ready closeout checklist:

1. Open the next ready Work Unit from the deterministic inbox order and verify
   its Assignment Packet is readable.
2. Confirm the claim, Evidence & Result Record, progress rows, and required
   visibility proof all point to existing source artifacts.
3. Compare the evidence against the packet's done and verification criteria;
   do not let a Team Lead status claim, green check, label, Project field,
   Discord message, or chat summary stand in for evidence.
4. Check whether a final `decision.md` already exists. If it does, do not
   overwrite it; report the new result as stale, duplicate, or requiring an
   explicit owner-requested revision/reopen.
5. Choose the Operations Lead decision explicitly: `accept`, `revise`, or
   `blocked` according to the closeout command contract. No automatic completion
   follows from result arrival.
6. Keep GitHub Project and Discord data as mirrors only. Do not reverse-import
   Project fields, Discord history, GitHub comments, or labels into assignment,
   claim, evidence, decision, or completion state.
7. Run closeout as a foreground Operations Lead action, dry-run first, then
   publish only when the planned decision, owner-facing status, and optional
   mirror updates match the source artifacts.

When closeout is initiated by a fresh closeout delegate, use the structured
guarded path:

```bash
python3 scripts/openclaw_company_ops.py work-unit closeout \
  --work-unit-id <id> \
  --commit-request @commit-request.json \
  --authority-role operations-lead-delegate \
  --delegate-agent main \
  --dry-run
```

The commit request binds the delegate judgment to the source snapshot it
inspected. It must include the Work Unit id, decision, reason, source ref,
current RESULT_READY proof id, source artifact hashes, delegate session/job/run
or message refs, autonomy class, review depth, and a structured red-line check
whose categories are all clear.
`manual_required`, stale source, missing proof, hash mismatch, duplicate final
proof, existing final decision, missing Work Card, or unclear red-line status
must fail closed as `repair-needed`; the delegate judgment alone is not enough
to write final state without the guarded command.

Race control:

- Only the Operations Lead may record `ACCEPTED`, `REVISE`, or
  `BLOCKED_DETAIL` and owner-facing `COMPLETED`, `NEEDS_REVISION`, or
  `BLOCKED`.
- Team Lead result arrival must not mutate GitHub Project, close Work Cards,
  publish owner completion, or overwrite decisions by itself.
- Run one closeout at a time. Project sync already uses a lock; source decision
  artifacts are single-writer Operations Lead outputs. The foreground
  `work-unit closeout --dry-run` / `work-unit closeout --publish` command uses
  a Work Unit-specific closeout lock and re-checks whether a final decision
  already exists before planning or writing any later decision.
- Explicit `accept` and `revise` closeouts require a source-backed
  `result_ready` submission. `blocked` closeout does not require
  `result_ready`; it requires blocker reason/source, needed action, and next
  owner instead.
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
- Guarded closeout publish records a narrow stage file named
  `closeout-<decision>-stage.json`. The stage progresses through `started`,
  `team-published`, `visibility-published`, and `published`. Final
  `decision.md` is written only after team-detail final review and owner-facing
  ops-feed closeout publish both succeed. If publish fails mid-way, rerun the
  same Work Unit/decision/commit request in foreground; the command may skip
  matching already-published proof rows and continue instead of duplicating
  visibility or requiring manual source edits.

Goal/convergence revision boundary:

- A `goal` or `convergence` Work Unit is allowed to iterate inside the Team
  Lead execution loop before `result-ready`: plan, act or improve, verify, then
  repeat until done criteria pass with evidence or a true blocker appears.
- Use `work-unit checkpoint` and `progress.jsonl` rows for Team Lead-owned
  round visibility during that internal loop. In a detached path, those
  checkpoints are Team Lead execution visibility, not Operations Lead closeout.
- Operations Lead `revise` is different. It happens only after a source-backed
  `result-ready` submission is reviewed and found insufficient against the
  Assignment Packet. It produces lifecycle `revision_requested` and default
  responsibility `operations_lead_replan`; Team Lead responsibility resumes
  only after a revised packet or explicit revision assignment exists.
- Do not use Operations Lead `revise` as the normal mechanism for every failed
  Team Lead verification round. Failed internal verification should stay inside
  the selected `goal` loop until it converges, blocks, or hits a safety/budget
  limit.

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
- Operations Lead Decision: final accept, revise, or blocked decision.

Visibility surfaces such as GitHub labels, GitHub Projects, saved issue views,
or Discord messages must point back to these artifacts. They are not source
artifacts.

### Handoff Draft Rule

The Phase 5.5b handoff draft helper is a foreground planning surface for the
Operations Lead, not a router or source of truth. Its first implementation is
limited to:

```bash
python3 scripts/openclaw_company_ops.py work-unit draft-handoff --spec draft-input.json --dry-run
```

The input is a structured local spec containing Operations Lead-provided facts.
Do not use raw owner chat text as enough input to choose `mode`, Team Lead,
scope, criteria, targets, or no-go boundaries. Missing judgment fields must be
listed as `needs-ops-decision`, not filled by the helper.

The helper may draft Work Card text, Assignment Packet text, a handoff spec,
missing fields, and no-go/order checks. It must not create Work Cards, write
source artifacts, publish Discord cards, mutate GitHub Project, send owner
completion, call an LLM, or choose a Team Lead. Before any real handoff, the
Operations Lead must review/fill the draft and validate the completed spec
through `work-unit handoff --dry-run`.

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
4. Operations Lead runs `work-unit start --dry-run`, then
   `work-unit start --publish` when the Team Lead starts or claims the work.
5. Operations Lead runs `work-unit dispatch --dry-run`, then
   `work-unit dispatch --publish --runtime openclaw-agent` with a configured
   adapter command. The adapter receives a short Team Lead accepted/readback
   envelope through `openclaw agent --json`, enqueues the execution message via
   Gateway `sessions.send`, and only then records
   `dispatch.json` plus the `dispatched` progress row. If the live adapter is
   not configured, use `--runtime record-ref` only for an explicitly manual,
   audit-safe reference.
6. For long `goal` work, publish `work-unit checkpoint` at major slice
   boundaries or at least every 10-15 minutes while work remains active. In the
   current foreground/manual flow, Operations Lead may perform this while
   holding the execution session. In the detached flow, this becomes Team
   Lead-owned execution visibility. The command publishes/readbacks the team
   `CHECKPOINT`, then records matching source-backed `progress.jsonl` metadata
   and can run one Project mirror sync.
7. For standalone progress metadata without Discord visibility, Operations Lead
   may still use `work-unit progress`, but it must not replace the normal
   checkpoint briefing path during live long work.
8. Publish `[RESULT_READY]` when the Team Lead result is actually available.
   In the current foreground/manual flow, Operations Lead may post it after
   confirming the Team Lead result. In the detached flow, this is Team
   Lead-owned result submission through `work-unit result-ready`. For detached
   work, request a fresh closeout delegate wake when configured; if wake fails,
   leave the WU in the result-ready inbox and recover through `work-unit
   delegate-wake`.
9. A closeout delegate or Operations Lead performs source-backed verification
   and prepares a guarded `--commit-request`.
10. The fresh `main` closeout delegate may publish final closeout through
   `work-unit closeout --authority-role operations-lead-delegate` when all
   red-line categories are clear. Security, deployment, DB migration,
   credential/auth, cost-bearing, destructive, external/public/customer,
   owner-intent ambiguity, evidence/proof/hash mismatch, critical disagreement,
   or unresolved-dependency cases must escalate to main Operations Lead with no
   final write.
11. `work-unit closeout` writes `decision.md`, posts the detailed `[ACCEPTED]`,
   `[REVISE]`, or `[BLOCKED_DETAIL]` review note in the relevant `#team-*`
   channel, posts one owner-facing `[COMPLETED]`, `[NEEDS_REVISION]`, or
   `[BLOCKED]` summary in `#ops-feed`, and optionally syncs the Project mirror
   after source/proof revalidation. It never archives or cleans up Work Cards.

`[RESULT_READY]` is a Team Lead result-submission signal, not an Operations
Lead decision. A Team Lead delegation is visibility-incomplete if the relevant
team channel stops at `[RESULT_READY]`. Before reporting completion, the
Operations Lead or delegated closeout path must close the team detail trail
with `[ACCEPTED]`, `[REVISE]`, or `[BLOCKED_DETAIL]`, and then close the
owner-facing timeline in `#ops-feed` with `[COMPLETED]`, `[NEEDS_REVISION]`, or
`[BLOCKED]`.

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
- Parallel lifecycle publishes may contend on the single Project sync lock.
  Foreground lifecycle commands may perform a short bounded retry for that
  mirror update. If the lock still does not clear, source proof remains valid
  and the Project mirror is recovered later through foreground `project-sync`
  apply/reconcile; do not invent fallback dashboard truth.
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
   accept/revise/blocked judgment.

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
`ASSIGNED`, `STARTED`, heartbeat, stale-claim, result-ready, or routine
timeline updates. Use the Work Card body, labels, Assignment Packet, Ops Claim
Ledger entry, Evidence & Result Record, and Operations Lead Decision instead.

The one planned exception is the Phase 5.8.8 final Work Card result summary
comment: after guarded closeout records `accept`, `revise`, or `blocked`, the
closeout path may create or update exactly one marker-managed GitHub comment
that mirrors the source-backed Evidence & Result Record and Operations Lead
Decision for maintainer inspection. That comment is never source truth and must
not be read by status, inbox, Project sync, result-ready, or closeout decision
derivation.

Reserve any other comments for human review notes or external collaborator
context that cannot live in source artifacts.

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

When final closeout runs with `--project-sync-mode required`, GitHub issue
hygiene is included in the same foreground Project sync gate. For recovery or
maintenance, use the explicit foreground path `project-sync apply
--sync-issue-labels` or `project-sync reconcile --sync-issue-labels`. It
derives desired labels from source status and only changes managed queue labels.
It does not close Accepted issues; Accepted remains an owner-inspection
lifecycle until a separate cleanup/archive action is approved.

Project sync is a derived mirror update, not source truth. The foreground sync
path uses changed-only Project field updates, bounded retry/backoff for
transient `gh`/GitHub failures, final desired-vs-live readback, and diagnostic
details for auth/scope/rate-limit failures. If a Project field update fails,
the sync records the failed field and leaves an explicit `project-sync-needed`
state instead of treating the dashboard as converged.

During guarded closeout, Project sync failure must not block publication of the
final marker-managed Work Card summary comment when the source-backed decision
and GitHub Work Card are otherwise valid. In that case, the source artifacts and
summary comment remain inspectable, while the dashboard mirror is repaired later
through foreground `project-sync apply` or `project-sync reconcile`. Do not
reverse-import GitHub Project values into Work Unit source artifacts.

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

## Lifecycle And Responsibility Rules

User-facing status must separate lifecycle from responsibility.

Lifecycle answers where the Work Unit is in the protocol:

- `assigned`
- `working`
- `result_ready`
- `accepted`
- `revision_requested`
- `blocked`
- `done`

Responsibility answers who owns the next action:

- `team_lead_assigned`
- `team_lead_working`
- `operations_lead_review`
- `operations_lead_replan`
- `team_lead_revision_assigned`
- `owner_inspection`
- `owner_input_needed`
- `external_wait`
- `archived`

Status derivation order is:

1. final Operations Lead decision;
2. result evidence or visibility proof;
3. claim expected responsibility;
4. assignment existence.

An accepted decision produces lifecycle `accepted`, not archival `done`.
Archival `done` is reserved for the point after owner inspection and Work Card
cleanup. A revise decision produces lifecycle `revision_requested` and default
responsibility `operations_lead_replan`; Team Lead responsibility resumes only
after a new revision assignment exists.

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

A `result_ready` claim without an existing non-draft Evidence & Result Record is
a repair-needed ready transition, not a weak ready item and not Work Unit
failure. The shared Result Ready Gate must keep the Work Unit `In Progress`,
avoid writing or mirroring `Result Ready`, and return structured repair hints
until the missing source artifact, evidence, or proof is fixed. In the Project
dashboard, keep the coarse `Status` as `In Progress`; put
`result preflight repair needed` in `Progress` and the concrete repair reason in
`Blocker`.

## Decision Rules

The Operations Lead decision must be explicit.

Allowed decisions:

- `accept`: evidence satisfies the Assignment Packet.
- `revise`: result is useful but needs changes.
- `blocked`: decision is blocked by missing evidence, dependency, context, or
  required owner/external action.

For standalone `verify` Work Units, `accept` approves the completed
verification procedure and report, not necessarily the candidate output under
test. A complete verification report can be accepted while its criterion mapping
records that the candidate failed or is unknown. The decision rationale must
explicitly say whether the candidate passed, failed, or remains unknown, and
must not let `Accepted` imply candidate pass. Candidate non-compliance belongs
in the Evidence & Result Record and follow-up routing; incomplete verification
evidence should be `revise` or `blocked`, not accepted.

Only `accept` can move the lifecycle to `accepted`; it is not archival `done`
until owner inspection and Work Card cleanup are complete. A merged PR, green
check, label, or Discord update is not enough unless the Evidence & Result
Record and Operations Lead decision are linked.

## Blocked Work

Use `blocked` when:

- Assignment Packet is missing or unreadable.
- Required input is missing.
- Permission or environment access is missing.
- Evidence or source truth cannot be produced.
- Verification cannot be rerun or repaired because required input, authority,
  access, safety, or budget is missing.
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

Manual/foreground Pulse checks may alert on stale claims, session mismatches, or
suspected compaction recovery issues. Current Phase 5.6 policy keeps scheduled
Pulse activation deferred with trigger because the Dashboard, Discord proof
timeline, and result-ready inbox already cover distinct visibility/review roles.
If scheduled Pulse is later accepted, it must suppress Work Units that are
already result-ready or decided by source artifacts. Pulse must remain
alert-only.

The hook guard, when installed, is optional protection around source artifacts.
It may block clear red-line commands or malformed completion/handoff structure,
but it must not be required for normal operation, store Work Unit state, publish
messages, run Project sync, or decide Work Unit status.

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

## Reference Work Units

Current active Work Units live under `docs/work-units/` and mirror into the
configured GitHub Project from source artifacts. Earlier Day-0 reference dry
runs were removed from the active tree after the current artifact structure
stabilized; use Git history for those historical examples when needed.

The active post-setup plan is:

- `docs/post-setup-plan.md`
