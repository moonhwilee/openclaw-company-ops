# Discord Event Visibility

Status: Repo-local visibility formatter supported

This guide describes how to use Discord as an operational visibility surface for
OpenClaw Company Ops before an implemented Discord Ops Bridge exists.

Discord is not a source of truth, not a command router, not a state database,
and not a completion authority.

For post-setup dogfood, Discord visibility is required before the first real
Work Unit is accepted as a valid dogfood run. The requirement is observability,
not authority: the owner should be able to see events and follow links back to
source artifacts.

## Purpose

Discord should make Work Unit activity easy to notice.

It should answer:

- What Work Unit changed?
- Which source artifact should be opened?
- Is attention needed from the Operations Lead or Team Lead?
- Is this an informational event, a blocker, an alert, a result, or a decision?

It should not answer by itself:

- Whether work is complete.
- Whether evidence is sufficient.
- Whether a claim is true.
- Whether a Work Card should close.
- Whether a Team Lead should be restarted, replaced, or reassigned.

Those judgments stay in the Assignment Packet, Ops Claim Ledger entry, Evidence
& Result Record, and Operations Lead Decision.

## Default Visibility Flow

The default delegation path is `CLI-first + #ops-feed owner summary +
#team-* detail trail`.

Use the CLI or local agent session for actual Team Lead execution. Every Team
Lead delegation also produces the same Discord audit-visible trail:

- `#ops-feed`: owner-facing briefing cards for assignment and
  result/blocker summaries.
- `#team-*`: detailed assignment, progress, result, and Operations Lead review
  trail for the relevant Team Lead.

The team detail trail must close every Team Lead result with Operations Lead
review. `RESULT_READY` means the Team Lead submitted a result; it is not the
Operations Lead decision. After `RESULT_READY`, the relevant team channel must
receive exactly one final review event: `ACCEPTED`, `REVISE`, or
`BLOCKED_DETAIL`. The owner-facing `#ops-feed` completion or blocker summary
does not replace that team-channel review event.

There is no normal/formal Discord message-mode split. The Discord flow is the
same for every Team Lead delegation. Only the depth of source artifacts changes
with task risk.

The Discord messages are not commands, source artifacts, state changes,
approvals, recoveries, or completion truth.

## Composition Model

Visibility messages should be composed from the same known facts, but they
should not be rendered as the same generic event object.

The Operations Lead should perform one composition step per operating
transition:

- Assignment transition: compose the internal fact packet, one `#ops-feed`
  request card, and one `#team-*` assignment detail.
- Review/completion transition: compose the updated internal fact packet, one
  `#team-*` review message, and one `#ops-feed` completion or blocker card.

This is a writing and validation structure, not a requirement for extra LLM
calls. Normal visibility must not add a second Team Lead execution call or a
separate LLM summarization call. A second LLM review is reserved for high-risk
work, public-facing releases, or explicit owner request.

## Transition-Time Visibility Contract

Discord visibility is only valid when messages are sent and read back near the
operating transition they describe. A correct card sequence that is generated or
posted after all work is complete is replay evidence, not live visibility.

Required timing:

- Before Team Lead execution starts: `#ops-feed [요청]` and the relevant
  `#team-* [ASSIGNED_DETAIL]` are sent and read back.
- At execution start or claim: `#team-* [STARTED]` is sent and read back before
  meaningful work continues.
- During long `goal` work: `#team-* [CHECKPOINT]` is sent and read back at each
  major slice boundary or at least every 10-15 minutes, whichever comes first.
- At result submission: `#team-* [RESULT_READY]` is sent when the Team Lead
  result is actually ready for Operations Lead review, not after review is
  complete.
- At review: exactly one `#team-* [ACCEPTED|REVISE|BLOCKED_DETAIL]` is sent
  after Operations Lead judgment.
- At owner closeout: `#ops-feed [완료|수정필요|막힘]` is sent only after the
  team detail trail is closed.

Proof requirements:

- The E2E proof includes Discord readback timestamps and message ids, not just
  local card text.
- Checkpoint timestamps must precede `RESULT_READY`; a checkpoint created after
  result submission is not live progress.
- Burst-published timelines are invalid for live visibility even when the
  messages are ordered correctly.
- Send or readback failure means visibility is incomplete. The source artifact
  may remain true, but the visibility gate has not passed.

This contract does not make Discord authoritative. Completion still depends on
the Assignment Packet, claim, evidence, verification, and Operations Lead
decision.

## Message Length Budget

Discord normal message `content` is limited to 2,000 characters. Company Ops uses
three layers so normal visibility stays readable without adding another LLM
call:

1. Generation budget: ask Team Lead and Operations Lead outputs that will be
   pasted or transformed into Discord to stay within 1,600 characters.
2. Formatter target: keep generated Discord cards under 1,800 characters so
   headers, Korean text, links, and emoji have margin below Discord's hard
   limit.
3. Fallback compaction: if a message still exceeds the formatter target, preserve
   the header and next action, omit middle body content, and mark it as partially
   omitted.

The first layer is a prompt and template constraint, not semantic summarization.
Long logs, raw diffs, and exhaustive findings belong in the Evidence & Result
Record or another source artifact. The Discord message should carry the decision
summary and artifact path.

The formatter counts output using UTF-16 content units as a conservative proxy
for Discord validation. Korean Hangul syllables count as one unit in this model,
while many emoji and supplementary characters count as two. The generation
budget stays below the formatter target so emoji headers, links, newlines, and
labels still have margin.

The internal fact packet keeps stable facts aligned:

- Work Unit id.
- Team and responsible agent.
- Problem being addressed.
- Requested work.
- Done and verification criteria.
- Scope limits and cautions.
- Team Lead result.
- Operations Lead review decision.
- Verification performed.
- Next action.
- Human-readable evidence or source reference.

`#ops-feed` and `#team-*` messages use those facts for different readers. The
`#ops-feed` message is a concise owner briefing. The `#team-*` message is a
detailed execution and review trail. They may share facts, but they should not
share the same wording.

Recommended `#ops-feed` request card:

```text
📌 [요청] WU-YYMMDD-001 · 🧪 build-lab
문제: route cost guidance가 현재 운영 기준과 맞는지 확인이 필요합니다.
요청: build-lab에 문서와 formatter smoke 기준을 점검하도록 맡겼습니다.
기준: 변경이 필요하면 최소 패치 범위와 검증 방법을 함께 제시해야 합니다.
주의: Work Unit 상태, GitHub issue, claim/evidence/decision artifact는 변경하지 않습니다.
다음: Team Lead 결과를 받은 뒤 금비가 수락 또는 수정요청 여부를 판정합니다.
```

Recommended `#team-*` assignment detail:

```text
📋 [ASSIGNED_DETAIL] WU-YYMMDD-001 · 🧪 build-lab
Goal: route cost guidance가 현재 Company Ops visibility 원칙과 맞는지 검토합니다.
Scope: 문서와 formatter smoke 기준만 확인합니다.
Criteria: 불일치가 있으면 위치, 영향, 최소 수정 방향을 보고합니다.
Cautions: 상태 mutation, GitHub issue 변경, claim/evidence/decision artifact 변경은 금지합니다.
Report: 결과 요약, 기준별 판단, 확인한 파일, blocker, 다음 액션을 보고합니다.
```

Recommended `#team-*` result-ready detail:

```text
📦 [RESULT_READY] WU-YYMMDD-001 · 🧪 build-lab
Result: Team Lead 결과가 제출되었고 Operations Lead 검토 대기 상태입니다.
Evidence: docs/examples/manual-dry-run/WU-YYMMDD-001/evidence.md
Verification: Team Lead가 보고한 smoke와 diff-check가 통과했습니다.
Risks: 추가 artifact 변경은 보고되지 않았습니다.
Next: Operations Lead가 결과를 검토하고 ACCEPTED 또는 REVISE를 남깁니다.
```

Recommended `#team-*` Operations Lead review detail:

```text
✅ [ACCEPTED] WU-YYMMDD-001 · 🧪 build-lab
Decision: 금비 검토 결과, Team Lead 결과는 요청 범위와 검증 기준을 충족했습니다.
Reason: evidence, smoke, repo state를 확인했고 추가 수정 요구는 없습니다.
Evidence: docs/examples/manual-dry-run/WU-YYMMDD-001/decision.md
Next: ops-feed에 주인님용 completion card를 남깁니다.
```

Recommended `#ops-feed` completion card:

```text
✅ [완료] WU-YYMMDD-001 · 🧪 build-lab
결과: build-lab 결과를 금비가 검토했고 요청 범위 안에서 기준 충족을 확인했습니다.
기준 대비: 문서 원칙과 formatter smoke 기준을 충족했습니다.
금비 판정: ACCEPTED.
확인: evidence, smoke, repo state를 확인했습니다.
다음: 추가 조치 없음.
```

If a visibility message cannot be sent, report that the visibility send failed.
Do not invent a fallback truth source and do not claim Discord visibility was
achieved.

## Execution Routes

Use explicit route names when recording or reviewing execution behavior:

- `cli-direct`: the Team Lead is invoked directly through CLI or a local agent
  session. This is the default execution surface.
- `cli-delivered`: a CLI-triggered run uses delivery options to post a result
  into Discord. This proves delivery only.
- `discord-bound`: the Team Lead is invoked from a bound Discord team channel
  or thread. This is a diagnostic or deliberate experiment, not the normal
  delegation path.

All routes keep source of truth outside Discord. Formal Work Units still use
the Work Card, Assignment Packet, Ops Claim Ledger entry, Evidence & Result
Record, and Operations Lead Decision when those artifacts are required.

Known limitation: a successful `cli-direct` agent run may still fail to return a
clean final text response to the caller's terminal even when the agent session
itself ended successfully and the final assistant message exists in the session
store. Treat this as a runner/output-plumbing risk. Before relying on a
`cli-direct` result, verify at least one of:

- structured CLI output such as `--json`, when available and known to return;
- for CLI-triggered visible sends, `--json --deliver` delivery status showing a
  successful send to the expected channel or thread;
- a session-store readback showing the final assistant message and successful
  session end;
- source artifacts, evidence, and checks produced by the Team Lead.

Use `discord-bound` route validation only when proving or diagnosing a channel
session. For normal delegation, owner-visible communication is provided by the
`#ops-feed` owner timeline and `#team-*` detail trail, not by forcing the
execution session into Discord.

Do not count a CLI command that only uses `--deliver --reply-channel discord
--reply-to ...` as this route validation by itself. Official OpenClaw CLI
semantics treat reply-channel and reply-to as delivery overrides, separate from
session routing. They can prove delivery into Discord, but not that the Team
Lead conversation is running from the bound Discord channel or thread.

## Cost And Activation Guidance

Compare against the baseline of CLI-first execution.

- `#ops-feed` assignment summary plus matching team detail adds about ten to
  thirty seconds when posted manually.
- `#ops-feed` completion or blocker summary plus matching team detail adds
  about twenty to sixty seconds when posted manually.
- Expected added default overhead is roughly thirty to ninety seconds while
  posting is manual.
- No extra Team Lead execution call or LLM summarization call should be added
  for normal visibility. Ask the Team Lead to include a concise result summary,
  verification summary, changed/source artifacts, blocker if any, and next
  action in the normal result, then compose the owner-facing card and team
  detail message in one Operations Lead composition step.
- `discord-bound` diagnostics can still add one short Team Lead LLM response,
  but diagnostics are not the default run path.

Activation priority after Phase 4 follows the Phase 5 sub-gates in
`docs/post-setup-plan.md`:

1. Phase 5.1 accepted the visibility contract: card composer, header icons,
   sequence guard, UTF-16 length guard, 1,600-character generation budget,
   foreground `publish-card`, live `proof-validate`, and no extra Team Lead or
   LLM summarization call for normal visibility.
2. Phase 5.2 accepted a narrow repo-local Completion / Hook Guard MVP:
   `.codex/hooks.json` plus `.codex/hooks/company_ops_gate.py`. It is a late
   safety layer for red-line commands, Work Unit completion artifacts, and
   compaction handoff; it does not publish progress or mutate operating state.
   Checkpoint-needed automation and yieldable long-work runners are not part of
   this gate unless later evidence reopens them.
3. Phase 5.3 accepts a GitHub Project dashboard with bounded auto-sync:
   Work Cards, source artifacts, issue labels, and `dashboard_snapshot.py`
   remain source-backed inputs, while the Project is a few-minutes-fresh
   visibility mirror for at-a-glance owner review.
4. Phase 5.4 accepts narrow foreground publisher hardening: duplicate-card proof
   guard, expected target/surface checks, and the canonical
   `visibility-proof.jsonl` proof-log convention. It must remain an explicit
   one-card publisher, not a daemon, command router, retry loop, or timeline
   replay tool.
5. Phase 5.5 implemented the foreground result-ready inbox and closeout dry-run
   lock gate for multi-Work Unit review safety. It scans only local Work Unit
   source artifacts and keeps route-helper behavior deferred.
6. Phase 5.5a implemented only a foreground amendment/replan dry-run gate for
   source-backed post-handoff plan changes, not automatic closeout, rerouting,
   amendment writes, or external mutation.
7. Phase 5.5b accepts a bounded Handoff Draft / Spec Generator gate. Its first
   command shape is `work-unit draft-handoff --spec draft-input.json --dry-run`.
   It drafts Work Card / Assignment / spec scaffolding only from structured
   Operations Lead-supplied facts, and must not parse free-form owner text into
   routes, assign Team Leads, publish, mutate GitHub, or replace Operations
   Lead judgment.
8. Phase 5.6 keeps scheduled daemon or Pulse Monitor activation deferred unless
   real stale-claim risk outweighs alert noise and false positives.
9. Phase 5.7 locks the surfaces allowed to enter packaging/public v1.

## Recommended Channels

Use seven channels for Phase 1 operation.

Use one Operations Lead channel for owner-to-Operations-Lead discussion:

- `#ops-lead`: Company Ops planning, scope alignment, phase decisions, and
  handoff preparation. This channel should route to the Operations Lead only.

Use two channels for owner timeline and alert visibility:

- `#ops-feed`: owner-facing `ASSIGNED`, `COMPLETED`, `NEEDS_REVISION`, and
  `BLOCKED` summaries.
- `#ops-alerts`: claim stale, session mismatch, and suspected compaction
  recovery alerts only.

Use team channels when the owner needs to ask a Team Lead directly:

- `#team-build-pq`: PrimeQuant platform engineering.
- `#team-build-lab`: new product and tooling.
- `#team-market`: market, positioning, and content.
- `#team-revenue`: customer, proposal, payment, and delivery.

Bind these channels deliberately. The matching Team Lead should answer by
default. If no agent is bound to a channel, a response should not be assumed. If
multiple agents answer the same team channel by default, fix routing before
dogfood because the channel is no longer auditable.

Telegram direct chat remains the private control plane for sensitive setup,
credentials locations, Discord outage, and recovery discussion. It is not a
replacement source of truth and should not broadcast normal Discord requests
back into Discord by default.

Do not create extra channels beyond these seven until the event or
direct-question volume proves they are needed.

## Response Trigger Policy

Use explicit routing instead of broad "answer every message" behavior.

Phase 1 default:

- `#ops-lead` has exactly one default Operations Lead binding.
- Each team channel has exactly one default Team Lead binding.
- The Operations Lead may answer owner-authored messages in `#ops-lead` by
  default.
- The matching Team Lead may answer owner-authored messages in that team
  channel by default.
- Non-owner chatter should not trigger agent responses unless the agent is
  mentioned or explicitly addressed.
- `#ops-feed` and `#ops-alerts` should not have default conversational agent
  responders.
- If noise, overlap, or multi-agent replies appear, switch that channel to
  mention-required mode before dogfood.
- Do not grant broad message-content scanning just to make every Discord
  channel act as an input stream.

Future slash or application commands may be added for read-only lookup, such
as `/status`, `/evidence`, or `/claim`. State-changing commands such as
`/done`, `/assign`, `/reassign`, or `/recover` remain out of bounds for v1.

## Direct Team Lead Questions

The owner may ask a Team Lead direct questions in the relevant team channel.
This is allowed and expected.

Allowed examples:

- Asking for current status.
- Asking where evidence lives.
- Asking for clarification on a technical, market, or revenue point.
- Asking a Team Lead to draft a possible approach before a Work Unit exists.

These messages are not a Discord command router because they do not mutate
operating state by themselves.

If a direct question becomes official work, promote it through the normal
artifacts:

1. Create or update the Work Card.
2. Create or update the Assignment Packet.
3. Create or update the Ops Claim Ledger entry.
4. Require Evidence & Result and an Operations Lead Decision before closure.

Forbidden direct-message behavior:

- A chat message automatically creates, closes, approves, or reassigns a Work
  Unit.
- A Team Lead treats a direct question as delegated execution when no Assignment
  Packet exists.
- A Team Lead marks work complete from chat text without Evidence & Result and
  an Operations Lead Decision.
- Multiple Team Leads answer one team channel by default without an explicit
  routing reason.

Direct answers can be useful context, but source artifacts remain the operating
record.

## Visibility Kinds

Use these event names consistently.

`#ops-feed` owner-facing summary kinds:

- `ASSIGNED`: Operations Lead assigned a Team Lead.
- `COMPLETED`: Operations Lead accepted the result for owner-facing purposes.
- `NEEDS_REVISION`: Operations Lead reviewed the result and requires revision.
- `BLOCKED`: required input, artifact, permission, or decision is missing.

`#team-*` detail-trail kinds:

- `ASSIGNED_DETAIL`: detailed Team Lead assignment and done criteria.
- `STARTED`: Team Lead started or claimed execution.
- `CHECKPOINT`: long-running progress card between `STARTED` and
  `RESULT_READY`, used at slice boundaries or the 10-15 minute checkpoint
  interval.
- `RESULT_READY`: Team Lead submitted result, evidence, or verification
  candidates.
- `ACCEPTED`: Operations Lead accepted the result after review.
- `REVISE`: Operations Lead requires revision.
- `BLOCKED_DETAIL`: blocker details, missing evidence, or required owner input.

`#ops-alerts` alert kinds:

- `CLAIM_STALE`: claim is older than its expected window.
- `SESSION_MISMATCH`: observed session state conflicts with the claim.
- `COMPACTION_RECOVERY_SUSPECTED`: compaction may have interrupted Work Unit
  recovery.

Header icons make status and target scannable in busy Discord channels. Use
`<status-icon> [<status-label>] <work-unit-id> · <team-icon> <team>` for
purpose-specific card output.

Default team icons:

- `🧱 build-pq`
- `🧪 build-lab`
- `📣 market`
- `💼 revenue`
- `👥 <team>` defensive fallback for an unmapped team; normal operations should
  use one of the canonical mapped team icons.

Default status icons:

- `📌 [요청]` / `✅ [완료]` / `⛔ [막힘]`
- `📋 [ASSIGNED_DETAIL]` / `▶️ [STARTED]` / `⏱️ [CHECKPOINT]` /
  `📦 [RESULT_READY]`
- `✅ [ACCEPTED]` / `🔁 [REVISE]` / `⛔ [BLOCKED_DETAIL]`

Discord is the limiting surface. Visibility card output must fit into one
Discord message by default. If the body is too long, compact it before sending:
preserve the header and next action, mark the body as partially omitted, and
keep the full detail in the Work Unit evidence, Team Lead result, or source
artifact. This is deterministic compaction, not semantic LLM summarization.
Do not rely on Discord's automatic message splitting for normal operations.
For manual posts that do not come from `discord card`, run the same guard first:

```bash
python3 scripts/openclaw_company_ops.py discord guard --message-file team-result.txt
```

Manual Day-0 visibility may be posted by the Operations Lead. Pulse Monitor
alert JSON can be formatted with `scripts/discord_ops.py`. Future bridge events
may be automated, but they must remain visibility events.

Preferred repo-local visibility cards can be composed without sending:

```bash
python3 scripts/openclaw_company_ops.py discord card \
  --surface ops-feed \
  --kind ASSIGNED \
  --work-unit-id WU-260606-002 \
  --team build-lab \
  --problem "요청-완료 visibility 흐름이 실제로 보이는지 확인이 필요합니다." \
  --request "build-lab에 card composer smoke를 맡깁니다." \
  --criteria "ops-feed에는 내부 필드 없이 문제, 요청, 기준, 다음 액션이 보여야 합니다." \
  --evidence "docs/examples/manual-dry-run/WU-260606-002/assignment.md" \
  --next "Team Lead가 실행 후 결과 요약을 보고합니다."
```

For live Work Unit proof or manual posting, validate the sequence before calling
the flow complete:

```bash
python3 scripts/openclaw_company_ops.py discord card-sequence \
  --card-json ops-request.json \
  --card-json team-assigned.json \
  --card-json team-result.json \
  --card-json team-review.json \
  --card-json ops-completion.json
```

The sequence must start with the owner-visible `#ops-feed` request. A
team-detail handoff without the matching `#ops-feed` request is an incomplete
visibility flow, even if the Team Lead actually did the work.

Use `--format json` when another publisher needs structured output. The card
composer prints only; it does not send to Discord, mutate GitHub, update claims,
or change execution state.

The active visibility surface is `discord card` plus, when live Discord proof is
required, foreground `discord publish-card`. Do not use a generic compatibility
formatter as an alternate path.

Repo-local team-detail text uses the same command with `--surface team-detail`:

```bash
python3 scripts/openclaw_company_ops.py discord card \
  --surface team-detail \
  --kind RESULT_READY \
  --work-unit-id WU-YYMMDD-001 \
  --team build-lab \
  --result "Evidence가 제출되었고 Operations Lead 검토 대기 상태입니다." \
  --evidence "docs/examples/manual-dry-run/WU-YYMMDD-001/evidence.md" \
  --verification "smoke checks가 통과했습니다." \
  --next "Operations Lead가 ACCEPTED 또는 REVISE를 남깁니다."
```

Visibility card composition prints only; it does not send to Discord, mutate GitHub,
update claims, or change execution state.

To publish one prepared card and record timestamped readback proof:

```bash
python3 scripts/openclaw_company_ops.py discord publish-card \
  --card-json team-checkpoint.json \
  --target channel:<discord-channel-id> \
  --expect-surface team-detail \
  --proof-log artifacts/WU-YYMMDD-001/visibility-proof.jsonl
```

Validate live proof before accepting a long-running visibility flow:

```bash
python3 scripts/openclaw_company_ops.py discord proof-validate \
  --proof-log artifacts/WU-YYMMDD-001/visibility-proof.jsonl \
  --work-unit-id WU-YYMMDD-001 \
  --require-checkpoint \
  --min-live-span-seconds 60
```

## Required Message Content

Every Discord visibility message should include:

- Event kind.
- Work Unit id.
- Short human-readable summary.
- Next action.

`#ops-feed` cards should not show internal routing fields such as `Surface`,
raw `Source`, mechanical `Owner`, or default `Public summary`. The channel
already identifies the surface. Use reader-friendly labels instead:

- Request card: `문제`, `요청`, `기준`, optional `주의`, optional `근거`,
  `다음`.
- Completion card: `결과`, `기준 대비`, `금비 판정`, `확인`, optional `근거`,
  `다음`.
- Blocker card: `문제`, `원인`, `필요`, optional `근거`, `다음`.

`#team-*` detail messages may use more operational labels such as `Goal`,
`Scope`, `Criteria`, `Cautions`, `Result`, `Evidence`, `Verification`, `Risks`,
`Decision`, `Reason`, and `Next`.

Use stable English for event kinds. Use Korean by default for owner-facing
`#ops-feed` card content and internal long-form human-readable values. Public
package documentation, CLI help text, and reusable release examples may use
English. Add an English public one-liner only when a message is explicitly
intended for public/package reuse; do not show `Public summary` by default in
internal `#ops-feed`.

Include a Work Card or deeper source artifact link when one exists. Small
delegated tasks may use a CLI assignment reference or source path until a Work
Card is justified by task risk.

For `#ops-feed`, expose that source as a human-readable `근거` line only when it
helps the owner inspect detail. Do not show it as a raw `Source:` field.

Use one source artifact link per event when possible:

- `ASSIGNED`: Assignment Packet or CLI assignment reference.
- `ASSIGNED_DETAIL`: Assignment Packet or CLI assignment reference.
- `STARTED`: Ops Claim Ledger entry or claim note.
- `NEEDS_REVISION`: owner-facing revision-required summary source.
- `BLOCKED`: owner-facing blocked summary source.
- `BLOCKED_DETAIL`: Work Card, claim entry, or blocker note.
- `CLAIM_STALE`: Ops Claim Ledger entry.
- `SESSION_MISMATCH`: Ops Claim Ledger entry and alert note.
- `COMPACTION_RECOVERY_SUSPECTED`: Ops Claim Ledger entry and alert note.
- `RESULT_READY`: Evidence & Result Record.
- `COMPLETED`: accepted result source or Operations Lead Decision.
- `ACCEPTED`: Operations Lead Decision or final review note.
- `REVISE`: Operations Lead review note.

## Work Unit Id Format

Use this Work Unit id format for newly created Work Units:

```text
WU-YYMMDD-NNN
```

Example:

```text
WU-260606-001
```

The date segment uses the last two digits of the year, then month and day. The
final segment is a three-digit sequence for that day. Existing completed
examples may keep the older `WU-YYYYMMDD-NNN` form as historical records, but
new Work Units should use `WU-YYMMDD-NNN`.

## Message Shape

Recommended `#ops-feed` request card:

```text
📌 [요청] WU-YYMMDD-NNN · <team-icon> <team>
문제: 주인님이 한눈에 이해해야 할 문제나 불확실성.
요청: 금비가 누구에게 무엇을 맡겼는지.
기준: 성공, 실패, 또는 검토 기준.
주의: 범위 제한이나 금지사항.
근거: Work Card, Assignment Packet, 또는 source artifact를 사람이 이해할 수 있게 표시.
다음: 결과를 받은 뒤 금비가 판단할 일.
```

Recommended `#ops-feed` completion card:

```text
✅ [완료] WU-YYMMDD-NNN · <team-icon> <team>
결과: 팀장이 확인, 생성, 수정, 또는 판단한 핵심 결과.
기준 대비: 요청 기준을 충족했는지.
금비 판정: ACCEPTED, REVISE, or BLOCKED.
확인: readback, tests, repo state, evidence 등 핵심 검증.
근거: Team Lead 결과, evidence, decision, 또는 readback 위치를 사람이 이해할 수 있게 표시.
다음: 다음 액션 또는 추가 조치 없음.
```

Recommended `#team-*` detail message:

```text
📦 [RESULT_READY] WU-260606-001 · 🧪 build-lab
Result: Demo thread handoff evidence가 제출되었고 금비 검토 대기 상태입니다.
Evidence: docs/examples/manual-dry-run/WU-260606-001/evidence.md
Verification: Team Lead가 보고한 smoke가 통과했습니다.
Next: Operations Lead가 ACCEPTED 또는 REVISE를 남깁니다.
```

## Threaded Handoff

For owner-visible Operations Lead to Team Lead communication, prefer one
Discord thread per active Work Unit inside the relevant team channel.

This does not add an OpenClaw thread-management layer. OpenClaw uses Discord
threads only as a visibility and conversation grouping feature. The operating
record remains the GitHub Work Card, Assignment Packet, Ops Claim Ledger entry,
Evidence & Result Record, and Operations Lead Decision.

The Discord thread is a conversation container only. It is not source of truth,
a blocker record, an execution database, a workflow state machine, a recovery
mechanism, or a command router. Normal operation only requires creating a
Discord thread, replying in it, and reading it back for owner visibility.

Do not add routine thread deletion, lock, archive, rename, or management
operations to the Company Ops operating loop. If the Discord bot has thread
management permission, treat it as an admin recovery safety net for mistakes
such as demo cleanup, duplicate threads, or a bad thread name. It should not
become another operating control plane.

Set the Discord parent channel's default thread auto-archive duration to `3
days` for team handoff channels. This is a Discord visibility default, not a
source-of-truth field. It gives weekend work enough time to remain visible
without keeping old Work Unit conversations active indefinitely.

When creating threads from OpenClaw, prefer inheriting the Discord channel
default. Do not routinely pass `--auto-archive-min`; use that option only for
explicit one-off overrides such as short-lived demos. The durable operating
record remains the GitHub-based ledger, not the Discord archive setting.

Use these canonical role headers for the single-bot Discord setup:

- `🎯 [OPS-LEAD] [ASSIGNED] WU-260606-001`
- `🧱 [BUILD-PQ] [ACK] WU-260606-001`
- `🧪 [BUILD-LAB] [STARTED] WU-260606-001`
- `📣 [MARKET] [BLOCKED] WU-260606-001`
- `💼 [REVENUE] [RESULT_READY] WU-260606-001`
- `🚦 [OPS-FEED] [DECISION] WU-260606-001`
- `🚨 [OPS-ALERTS] [CLAIM_STALE] WU-260606-001`

## Forbidden Actions

Discord must not:

- Replace the Assignment Packet.
- Replace the Ops Claim Ledger entry.
- Replace Evidence & Result Records.
- Replace Operations Lead decisions.
- Close Work Cards.
- Approve completion.
- Reassign Team Leads.
- Restart or recover agents.
- Mutate GitHub state.
- Mutate execution state.
- Act as a command router in v1.

If a Discord message says something that is not backed by a source artifact,
treat it as an unverified note.

## Blocked Events

Use `BLOCKED` when work cannot continue because a required artifact, input,
permission, or decision is missing.

The message should include:

- What is blocked.
- Who owns the next action.
- Which artifact proves the blocker.
- When the Operations Lead should review it again.

Do not use a Discord thread as the blocker record. Link back to the Work Card
or claim entry.

## Alert Events

Manual Day-0 alerts are human-triggered. Future Pulse Monitor alerts may be
automated.

Allowed alert events:

- `CLAIM_STALE`
- `SESSION_MISMATCH`
- `COMPACTION_RECOVERY_SUSPECTED`

Alert events are prompts for review, not recovery actions. They must not
restart, reassign, cancel, or close work.

Format Pulse Monitor alert JSON before posting it manually:

```bash
python3 scripts/pulse_monitor.py pulse check \
  --ledger "$LEDGER" \
  --session-snapshot ./session-snapshot.json \
  --format json > pulse-alerts.json

python3 scripts/discord_ops.py alerts \
  --pulse-json pulse-alerts.json \
  --source-ref "$LEDGER"
```

The formatter prints messages only. It does not send to Discord or mutate any
operating state.

## Decision Visibility

Use `ACCEPTED` or `REVISE` in the team detail trail only after Operations Lead
review. Use `COMPLETED` in `#ops-feed` only when the owner-facing result summary
is accepted. Use `NEEDS_REVISION` in `#ops-feed` after a team-detail `REVISE`.

The Discord visibility message may summarize the decision, but the decision
artifact or final Operations Lead review remains the authority.

Do not call a delegated task complete while its team detail trail stops at
`RESULT_READY`. A normal successful delegation is incomplete for visibility
until the same team channel also contains `ACCEPTED`. If the result requires
changes, post `REVISE` in the team detail trail and `NEEDS_REVISION` in
`#ops-feed`; if a blocker prevents review or continuation, post
`BLOCKED_DETAIL`.

Accepted decisions can lead to Work Card closure only after both the Evidence &
Result Record and Operations Lead Decision are linked from the Work Card.

## Manual Day-0 Checklist

Before posting a Discord visibility message, check:

- The Work Unit id is present.
- The surface is explicit: `ops-feed`, `team-detail`, or `ops-alerts`.
- The source artifact or source reference exists.
- The message does not imply completion without evidence and Operations Lead
  review.
- The message does not tell Discord to mutate state.
- The message is short enough to scan.

If the message lacks a source artifact or source reference, do not post it as an
operating visibility message. Add or fix the source artifact first.

## Pre-Dogfood Visibility Gate

Before running the first real dogfood Work Unit:

- Choose the actual channels for `#ops-feed` and `#ops-alerts`.
- Verify that the owner can see the channels.
- Post or emit one harmless visibility message with a real source artifact link.
- Confirm that the message is traceable back to the Work Card, Assignment
  Packet, claim, evidence, or decision artifact.
- Confirm that no Discord action can mutate operating state.

If these checks fail, the dogfood Work Unit can still be prepared, but it should
not be accepted as a full orchestration dogfood run because owner-visible
orchestration was not proven.

## Future Bridge Boundary

When Discord Ops Bridge is implemented, it should publish normalized events from
source artifacts and trusted operating transitions.

It should not:

- Interpret free-form Discord commands.
- Decide whether work is complete.
- Infer state from chat text.
- Reassign work.
- Recover sessions.
- Modify GitHub or execution state without a separate approved mechanism.

The bridge is a publisher. It is not an operating authority.
