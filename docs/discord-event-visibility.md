# Discord Event Visibility

Status: Repo-local alert formatter supported

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

## Execution Routes

Use explicit execution route names when recording or reviewing Work Unit
visibility:

- `cli-direct`: the Team Lead is invoked directly through a CLI or local agent
  session. This route does not target Discord and does not create a
  team-channel execution record. It is suitable for internal repo-local work
  only when the Operations Lead accepts that the team conversation itself will
  not be visible in Discord.
- `discord-bound`: the Team Lead is invoked from a bound Discord team channel
  or thread. This route should leave a team-channel or thread record because
  Discord was the execution conversation surface.

Both routes still use the same source artifacts: Work Card, Assignment Packet,
Ops Claim Ledger entry, Evidence & Result Record, and Operations Lead Decision.
Discord remains visibility-only for both routes.

For `cli-direct` execution, do not pretend that `#team-build-lab` or another
team channel has an execution record. The required owner-visible trail is
source-artifact-backed lifecycle events in `#ops-feed`.

Known limitation: a successful `cli-direct` agent run may still fail to return a
clean final text response to the caller's terminal even when the agent session
itself ended successfully and the final assistant message exists in the session
store. Treat this as a runner/output-plumbing risk. Before relying on a
`cli-direct` result, verify at least one of:

- structured CLI output such as `--json`, when available and known to return;
- a session-store readback showing the final assistant message and successful
  session end;
- source artifacts, evidence, and checks produced by the Team Lead.

Do not use plain `cli-direct` as the owner-visible path for real Team Lead
delegation. If the owner should be able to watch Operations Lead to Team Lead
communication, use `discord-bound`.

For `discord-bound` execution, team-channel records are expected for the
Discord conversation itself. They are still not source of truth and must point
back to the source artifacts.

Before Phase 4 or any other real delegation that is meant to be owner-visible,
run a route validation: send a small assignment or status handoff through the
selected team channel or Work Unit thread, confirm the matching Team Lead
responds there, and read the message back. If this validation fails, do not
claim that Discord-visible delegation has been proven.

## Recommended Channels

Use seven channels for Phase 1 operation.

Use one Operations Lead channel for owner-to-Operations-Lead discussion:

- `#ops-lead`: Company Ops planning, scope alignment, phase decisions, and
  handoff preparation. This channel should route to the Operations Lead only.

Use two channels for event and alert visibility:

- `#ops-feed`: assignment, started, blocked, result-ready, and decision events.
- `#ops-alerts`: claim stale, session mismatch, and suspected compaction
  recovery alerts.

Use team channels when the owner needs to ask a Team Lead directly:

- `#team-build-pq`: PrimeQuant platform engineering.
- `#team-build-lab`: new product and tooling.
- `#team-market`: market, positioning, and content.
- `#team-revenue`: customer, proposal, payment, and delivery.

Bind these channels deliberately. The matching Team Lead should answer by
default. If no agent is bound to a channel, a response should not be assumed. If
multiple agents answer the same team channel by default, fix routing before
dogfood because the channel is no longer auditable.

Telegram direct chat remains the fallback and private control plane for
sensitive setup, credentials locations, Discord outage, and recovery. It should
not broadcast normal Discord requests back into Discord by default.

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

## Event Types

Use these event names consistently:

- `ASSIGNED`: Operations Lead assigned a Work Unit.
- `STARTED`: Team Lead started execution.
- `BLOCKED`: required input, artifact, permission, or decision is missing.
- `CLAIM_STALE`: claim is older than its expected window.
- `SESSION_MISMATCH`: observed session state conflicts with the claim.
- `COMPACTION_RECOVERY_SUSPECTED`: compaction may have interrupted Work Unit
  recovery.
- `RESULT_READY`: Team Lead submitted evidence.
- `DECISION`: Operations Lead recorded accept, revise, hold, or reject.

Manual Day-0 events may be posted by the Operations Lead or Team Lead. Pulse
Monitor alert JSON can be formatted with `scripts/discord_ops.py`. Future bridge
events may be automated, but they must remain visibility events.

Repo-local lifecycle events can be formatted without sending:

```bash
python3 scripts/openclaw_company_ops.py discord event \
  --event ASSIGNED \
  --work-unit-id WU-260606-002 \
  --work-card https://github.com/moonhwilee/openclaw-company-ops/issues/18 \
  --owner build-lab \
  --source-artifact docs/examples/manual-dry-run/WU-260606-002/assignment.md \
  --summary "Work Unit assigned for routing and visibility patch."
```

Use `--format json` when another publisher needs structured output. The
formatter prints only; it does not send to Discord, mutate GitHub, update
claims, or change execution state.

## Required Event Fields

Every Discord event should include:

- Event type.
- Work Unit id.
- Work Card link.
- Current owner or next-action owner.
- Source artifact link.
- Short human-readable summary.

Use one source artifact link per event when possible:

- `ASSIGNED`: Assignment Packet.
- `STARTED`: Ops Claim Ledger entry.
- `BLOCKED`: Work Card or claim entry with blocker.
- `CLAIM_STALE`: Ops Claim Ledger entry.
- `SESSION_MISMATCH`: Ops Claim Ledger entry and alert note.
- `COMPACTION_RECOVERY_SUSPECTED`: Ops Claim Ledger entry and alert note.
- `RESULT_READY`: Evidence & Result Record.
- `DECISION`: Operations Lead Decision.

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

Recommended manual format:

```text
[EVENT_TYPE] WU-YYMMDD-NNN
Summary: one short sentence.
Owner: Operations Lead or Team Lead OpenClaw Agent.
Source: link to the relevant artifact.
Next: expected next action or "none".
```

Example:

```text
[RESULT_READY] WU-260606-001
Summary: Demo thread handoff evidence is ready for review.
Owner: Operations Lead
Source: docs/examples/manual-dry-run/WU-260606-001/evidence.md
Next: Operations Lead decision.
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

## Decision Events

Use `DECISION` only after an Operations Lead Decision artifact exists.

The Discord event may summarize the decision, but the decision artifact remains
the authority.

Accepted decisions can lead to Work Card closure only after both the Evidence &
Result Record and Operations Lead Decision are linked from the Work Card.

## Manual Day-0 Checklist

Before posting a Discord event, check:

- The Work Unit id is present.
- The Work Card link is present.
- The source artifact link exists.
- The event does not imply completion without evidence and decision.
- The event does not tell Discord to mutate state.
- The event is short enough to scan.

If the event lacks a source artifact, do not post it as an operating event. Add
or fix the source artifact first.

## Pre-Dogfood Visibility Gate

Before running the first real dogfood Work Unit:

- Choose the actual channels for `#ops-feed` and `#ops-alerts`.
- Verify that the owner can see the channels.
- Post or emit one harmless test event with a real source artifact link.
- Confirm that the event is traceable back to the Work Card, Assignment Packet,
  claim, evidence, or decision artifact.
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
