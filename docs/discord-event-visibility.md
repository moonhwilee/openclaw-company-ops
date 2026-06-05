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

## Recommended Channels

Use two channels for Manual Day-0 operation:

- `#ops-feed`: assignment, started, blocked, result-ready, and decision events.
- `#ops-alerts`: claim stale, session mismatch, and suspected compaction
  recovery alerts.

Do not create extra channels until the event volume proves they are needed.

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

## Message Shape

Recommended manual format:

```text
[EVENT_TYPE] WU-YYYYMMDD-NNN
Summary: one short sentence.
Owner: Operations Lead or Team Lead OpenClaw Agent.
Source: link to the relevant artifact.
Next: expected next action or "none".
```

Example:

```text
[RESULT_READY] WU-20260604-002
Summary: Discord event visibility guide is ready for review.
Owner: Operations Lead
Source: docs/examples/manual-dry-run/WU-20260604-002/evidence.md
Next: Operations Lead decision.
```

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
