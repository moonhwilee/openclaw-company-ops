# Assignment Packet

Status: Draft

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `WU-20260605-003`
- Title: Pre-Dogfood Discord Visibility Setup
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/16
- Operations Lead: `main`
- Assigned Team Lead OpenClaw Agent: `main`
- Created at: `2026-06-05`
- Updated at: `2026-06-05`

## Goal

Make the Company Ops Discord visibility path ready for the first real dogfood
Work Unit by mapping channels, confirming routing boundaries, and proving a
harmless owner-visible event plus one direct Team Lead Q&A path.

## Background

The owner challenged whether Company Ops orchestration can be trusted if the
Operations Lead only reports summaries in Telegram. The plan now requires
pre-dogfood visibility before a real dogfood Work Unit can be accepted.

The current documented v1 design is:

- Discord is visibility plus direct Q&A, not source of truth.
- `#ops-lead` is the owner-to-Operations-Lead channel for planning, phase
  decisions, and handoff preparation.
- `#ops-feed` and `#ops-alerts` are event/alert channels.
- `#team-build-pq`, `#team-build-lab`, `#team-market`, and `#team-revenue`
  are direct owner-to-Team-Lead Q&A channels.
- `#ops-lead` has one default Operations Lead responder.
- Team channels start with exactly one default Team Lead responder.
- No Discord command router, hidden orchestrator, automatic recovery,
  automatic reassignment, or automatic completion is allowed.

Current local OpenClaw state before execution:

- Team agents exist: `main`, `build-pq`, `build-lab`, `market`, `revenue`.
- OpenClaw config validates.
- Discord is not installed/configured yet.
- Agent routing bindings are currently zero.

## Scope

What the team lead should do:

- Confirm the actual Discord setup mechanism available in the current
  OpenClaw install.
- Select or create the minimum channel map:
  - ops lead channel;
  - ops feed channel;
  - ops alerts channel;
  - one team channel for each standing Team Lead.
- Configure or document the selected send path for the first harmless event.
- Configure or document the selected Team Lead routing path for direct Q&A.
- Prove a harmless event can be visible to the owner and trace back to a source
  artifact.
- Prove one harmless owner-authored team-channel question reaches only the
  matching Team Lead.
- Confirm that no Discord message mutates Work Card, claim, evidence,
  decision, GitHub, or agent execution state.

## Non-goals

What the team lead should not do:

- Do not create a Discord command router.
- Do not add state-changing slash commands.
- Do not enable automatic recovery, reassignment, restart, or completion.
- Do not enable a scheduled daemon.
- Do not create or sync a GitHub Project dashboard in this Work Unit.
- Do not run a real dogfood Work Unit before visibility is proven.
- Do not restart Gateway without explicit owner approval and required
  preflight.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Discord is an observation and direct Q&A surface only.
- Broad "answer every message" behavior is not allowed.
- If channel noise or multiple default responders appear, switch to
  mention-required mode before dogfood.

## Inputs

Links, files, references, or starting state:

- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/16
- Post-setup plan: `docs/post-setup-plan.md`
- Discord visibility guide: `docs/discord-event-visibility.md`
- Setup guide Discord section: `docs/setup-guide.md`
- OpenClaw channel status command: `openclaw channels status --probe`
- OpenClaw agent binding commands: `openclaw agents bind --help`,
  `openclaw agents bindings`
- Existing team agents: `main`, `build-pq`, `build-lab`, `market`, `revenue`

## Done Criteria

The Work Unit can be considered ready for review when:

- Discord setup status is recorded: installed/configured/enabled/probed or
  blocked with the missing credential/setup step named.
- Actual channel names or channel ids are recorded for:
  - ops lead;
  - ops feed;
  - ops alerts;
  - build-pq;
  - build-lab;
  - market;
  - revenue.
- The selected response trigger policy is recorded for each team channel:
  channel default binding or mention-required.
- A harmless event message is produced or sent and includes:
  - Work Unit id;
  - source artifact link;
  - owner or next-action owner;
  - next action.
- One direct Team Lead Q&A path is tested or marked blocked with the exact
  missing setup step.
- Evidence shows that no Discord action mutated source artifacts or operating
  state.

## Verification Criteria

Evidence or checks required for review:

- `openclaw channels list --all`
- `openclaw channels status --probe`
- `openclaw agents list --bindings`
- `openclaw agents bindings`
- Discord event output or screenshot/link, if a live Discord send is possible.
- Team-channel direct Q&A transcript/link, if live Discord routing is possible.
- Repo checks:
  - `python3 scripts/company_ops_smoke.py multi-team`
  - `python3 scripts/openclaw_company_ops.py smoke multi-team`
  - `git diff --check`

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

```yaml
protocol_capsule:
  mode: goal
  support:
    - discord_visibility
    - routing_check
    - no_mutation_boundary
  loop: <plan -> repeat(act_or_improve -> verify) until stop_only_on, only for goal>
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

For `goal` mode, do not stop after one failed verification. Plan once, then
repeat implementation or improvement and verification until a `stop_only_on`
condition is true.

Planning is required for `goal`, but it should be proportional. Small Work
Units can use a concise 1-3 bullet plan; risky or multi-step Work Units need a
fuller plan.

## Expected Outputs

- Evidence & Result Record:
  `docs/work-units/WU-20260605-003/evidence.md`
- Updated claim:
  `docs/work-units/WU-20260605-003/claim.md`
- Decision-ready summary with either:
  - Phase 1 accepted as visibility-ready; or
  - Phase 1 blocked with exact missing Discord credential/channel/binding step.

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
