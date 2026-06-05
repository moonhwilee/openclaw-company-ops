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

## Daily Operating Surfaces

Use these surfaces together. None of them may replace another required
artifact.

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

## Standard Manual Loop

1. Owner states a goal or problem.
2. Operations Lead decides whether it should become a Work Unit.
3. Operations Lead writes an Assignment Packet.
4. Operations Lead creates a GitHub Issue as the Work Card.
5. Operations Lead links the Assignment Packet from the Work Card.
6. Operations Lead records an initial Ops Claim Ledger Entry.
7. Operations Lead emits an `ASSIGNED` visibility event when Discord visibility
   is active.
8. Operations Lead assigns one Team Lead OpenClaw Agent.
9. Team Lead executes the Work Unit and manages its own subagents.
10. Team Lead updates the claim when state changes.
11. Team Lead emits visibility events for started, blocked, and result-ready
    states when Discord visibility is active.
12. Team Lead submits an Evidence & Result Record.
13. Operations Lead reviews evidence against the Assignment Packet.
14. Operations Lead records a decision.
15. Operations Lead emits a decision visibility event when Discord visibility
    is active.
16. Work Card is closed only after evidence and decision links exist.

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
