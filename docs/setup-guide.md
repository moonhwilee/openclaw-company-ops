# Setup Guide

This guide explains how to set up OpenClaw Company Ops in its current stage.

OpenClaw Company Ops is not yet a finished installable product. The current
repo contains a public operating model, manual Day-0 setup steps, and planned
component boundaries. As components are implemented, this same guide should be
updated in place from concept and manual setup notes into installation,
connection, and usage instructions.

For a detailed follow-along guide that a user can use to manually implement
the full structure before CLI automation exists, see
`docs/implementation-setup-guide.md`.

For the active post-setup realization sequence after this base setup, see
`docs/post-setup-plan.md`.

## Document Status

Use these labels when reading this guide:

- `Status: Concept`: the component is an architectural concept. It is not
  installable or runnable yet.
- `Status: Planned`: the component is intended for implementation, but no
  supported setup path exists yet.
- `Status: Manual Day-0`: the step can be run manually today without dedicated
  automation.
- `Status: Implemented`: the component has real installation, connection, and
  usage instructions.

The current setup is mostly `Manual Day-0` plus `Concept` and `Planned`
components.

## Current Scope

This guide is for people who want to reproduce the operating structure before
the full toolchain exists.

It covers:

- GitHub setup for Work Cards, evidence links, and later dashboard use.
- Discord visibility setup for operational observability. It is optional for a
  generic manual reproduction, but required before accepting the first real
  post-setup dogfood Work Unit.
- Manual Assignment Packet, Work Card, and Evidence & Result Record flow.
- Planned components that must not be treated as implemented yet.

It does not cover:

- Installing a finished OpenClaw Company Ops package.
- Installing a scheduled Pulse Monitor background job.
- Connecting a full Discord command bridge.
- Installing a Company Dashboard app.
- Running an automated Ops Claim Ledger backend.

## Prerequisites

Status: Manual Day-0

You need:

- OpenClaw access for the Operations Lead and any Team Lead OpenClaw Agents.
- A GitHub repository for the operating system workspace.
- GitHub Issues enabled.
- A place to store Assignment Packets and Evidence & Result Records.
- Optional for generic manual setup, required for post-setup dogfood: a Discord
  server or channel for operational visibility.

For the current repo, GitHub is already configured with:

- Public visibility.
- Issues enabled.
- Manual Day-0 Work Card labels.
- GitHub Issue template for Work Cards.
- Wiki disabled.
- MIT license.
- Topics and description for discoverability.

Branch protection, rulesets, GitHub Projects, and website/homepage are deferred
until the manual workflow has enough real Work Cards to justify them.

## GitHub Setup

Status: Manual Day-0

GitHub is the default shared work surface.

Use GitHub Issues as Work Cards. A Work Card should be small and link to the
real handoff packet instead of trying to contain every detail.

For an existing owner environment like this repo, the immediate GitHub setup is
small:

- Keep one repository for the OpenClaw Company Ops manual, templates, and future
  package.
- Keep Issues enabled.
- Use the current Work Card labels and issue template.
- Keep the repo public if the goal is public distribution.
- Keep branch protection and rulesets deferred until the manual dry run is
  stable.
- Leave website/homepage empty until there is a docs site, GitHub Pages site,
  or released manual.
- Phase 5.3 accepts a GitHub Project dashboard with bounded auto-sync for
  owner-facing at-a-glance visibility. Keep it as a mirror of Issues and source
  artifacts, not as operating truth.

Recommended issue labels:

- `work-unit`
- `assignment-ready`
- `working`
- `blocked`
- `result-ready`
- `decision-needed`
- `done`

Recommended Work Card fields:

- Work Unit id.
- Goal.
- Assigned Team Lead OpenClaw Agent.
- Assignment Packet reference.
- Current state.
- Done criteria.
- Evidence & Result Record reference when available.
- Operations Lead decision reference when available.

Do not use a GitHub Issue as a fallback Assignment Packet. If the Assignment
Packet does not exist or cannot be read, the Work Unit is blocked.

## Repository Strategy

Status: Manual Day-0

Use one GitHub repository per real project or product, not one repository per
Work Unit.

Recommended model:

- `openclaw-company-ops`: the operating model, public docs, templates, and
  future reusable package.
- One separate repository for each active product or codebase that needs its
  own source code, issues, PRs, tests, and releases.
- Work Units live as Issues inside the repository where the work belongs.
- Cross-project visibility comes from GitHub Projects or saved issue views, not
  from a fake umbrella repository.

Do not create a dedicated "dashboard repository" just to hold the Company
Dashboard. A GitHub Project can exist at the user or organization level and can
reference issues and pull requests from multiple repositories.

For this repo, the current recommendation is:

- Do not create more GitHub repositories yet.
- Start with this repo's Issues only when writing templates or running a manual
  dry run.
- Use the accepted Company Dashboard GitHub Project as a visibility mirror once
  the bounded sync command and fields are configured.

When the dashboard is created, make it a visibility layer with fields such as:

- Work Unit id.
- Repository.
- Team Lead.
- State.
- Priority.
- Blocker.
- Assignment Packet reference.
- Evidence & Result Record reference.
- Operations Lead decision reference.

The dashboard must point back to source artifacts. It must not become the source
artifact itself.

Dashboard creation timing is documented in `docs/company-dashboard-timing.md`.

## Discord Setup

Status: Repo-local visibility formatter supported, pre-dogfood visibility required

Discord remains a visibility-only surface. For post-setup dogfood, however, a
minimal Discord visibility path should be configured before the first real Work
Unit so the owner can follow the `#ops-feed` request/result timeline and drill
into team detail trails instead of relying only on Operations Lead summaries.

Recommended channels:

- `#ops-lead`: owner-to-Operations-Lead planning, scope alignment, phase
  decisions, and handoff preparation.
- `#ops-feed`: owner-facing assignment, completion, and blocker briefing cards.
- `#ops-alerts`: stale claim, suspected session mismatch, and suspected
  compaction recovery alerts.
- `#team-build-pq`: direct questions for the PrimeQuant platform team lead.
- `#team-build-lab`: direct questions for the new product/tooling team lead.
- `#team-market`: direct questions for the market/content team lead.
- `#team-revenue`: direct questions for the revenue/customer team lead.

Direct team channels are allowed. The owner can ask a Team Lead for status,
clarification, evidence location, or early thinking in the relevant channel.
That is not a Discord command router as long as chat text does not automatically
create, close, approve, reassign, recover, or mutate Work Units.

Routing rules:

- Bind `#ops-lead` to the Operations Lead only.
- Bind one default Team Lead per team channel.
- Let the Operations Lead answer owner-authored messages in `#ops-lead` by
  default.
- Let the matching Team Lead answer owner-authored messages in that team
  channel by default.
- Require an explicit mention or address before an agent answers non-owner
  chatter.
- Keep `#ops-feed` focused on owner-facing request/result summaries.
- Do not expose internal fields such as `Surface`, raw `Source`, mechanical
  `Owner`, or default `Public summary` in normal `#ops-feed` posts.
- Keep `#ops-alerts` alert-focused.
- Do not bind default conversational responders to `#ops-feed` or
  `#ops-alerts`.
- Do not assume OpenClaw will answer unless an agent is explicitly bound to the
  channel.
- If multiple agents answer the same team channel by default, fix routing before
  dogfood.
- If a team channel becomes noisy, switch it to mention-required mode before
  dogfood.
- Promote any official new work request into a Work Card, Assignment Packet,
  claim, evidence, and decision trail.

Slash or application commands may be introduced later for read-only lookup,
such as `/status`, `/evidence`, or `/claim`. Do not add v1 commands that mutate
state, such as `/done`, `/assign`, `/reassign`, or `/recover`.

Recommended event types:

- `#ops-feed`: `ASSIGNED`, `COMPLETED`, `BLOCKED`.
- `#team-*`: `ASSIGNED_DETAIL`, `STARTED`, `CHECKPOINT`, `RESULT_READY`,
  `ACCEPTED`, `REVISE`, `BLOCKED_DETAIL`.
- `CHECKPOINT` is for long-running live progress between `STARTED` and
  `RESULT_READY`.
- `#ops-alerts`: `CLAIM_STALE`, `SESSION_MISMATCH`,
  `COMPACTION_RECOVERY_SUSPECTED`.

For internal operation, keep event kinds and internal schema in stable English
but write owner-facing `#ops-feed` cards and long human-readable values in
Korean by default. A team channel result that stops at `RESULT_READY` is not
closed; the Operations Lead must post `ACCEPTED`, `REVISE`, or
`BLOCKED_DETAIL` before reporting completion.

Normal visibility should not add another Team Lead execution or LLM
summarization call. The Operations Lead should use one composition step per
transition to write a purpose-built `#ops-feed` card and a separate
purpose-built `#team-*` detail message from the same facts.

Before formatter guard runs, ask Team Lead and Operations Lead Discord-facing
handoff text to stay within 1,600 characters. Discord content has a 2,000
character hard limit; Company Ops formatter output targets 1,800 characters as
the fallback margin.

Discord messages are not a source of truth. They must point back to the Work
Card, Assignment Packet, Ops Claim Ledger entry, Evidence & Result Record, or
Operations Lead decision.

Detailed Discord event conventions are documented in
`docs/discord-event-visibility.md`.

The first post-setup phase is a pre-dogfood visibility setup. It verifies that
at least one harmless event can be seen in the chosen channel and traced back to
the source artifact. It also verifies that a harmless direct Team Lead question
can be answered in the correct team channel without mutating official operating
state. This is not a Discord command router and not a state owner.

## Manual Day-0 Operating Flow

Status: Manual Day-0

Use this flow before any dedicated automation exists.

1. Owner states a goal, priority, or problem.
2. Operations Lead converts it into one Work Unit.
3. Operations Lead writes an Assignment Packet.
4. Operations Lead creates a GitHub Issue as the Work Card.
5. Operations Lead assigns one Team Lead OpenClaw Agent.
6. Operations Lead records the initial responsibility expectation.
7. Team Lead executes the Work Unit and directly manages its own subagents.
8. Team Lead produces an Evidence & Result Record.
9. Operations Lead reviews the evidence and records a decision.
10. Work Card is closed only after the decision and evidence are linked.

Completion requires evidence. A status claim, Discord message, or GitHub
comment is not enough by itself.

The daily operating procedure is documented in `docs/operations-manual.md`.

## Manual Artifact Convention

Status: Manual Day-0

Until tools exist, use the templates in `docs/templates/` with a simple file or
note convention for each Work Unit.

Suggested structure:

```text
docs/examples/manual-dry-run/<work-unit-id>/
  assignment.md
  claim.md
  evidence.md
  decision.md
```

Suggested meanings:

- `assignment.md`: the Assignment Packet.
- `claim.md`: the current expected responsibility claim.
- `evidence.md`: links, outputs, checks, sources, or artifacts.
- `decision.md`: Operations Lead review decision and rationale.

This structure is a manual convention, not a runtime requirement. It can later
be replaced by a package-managed layout.

## Assignment Packet

Status: Manual Day-0

The Assignment Packet is the detailed handoff from the Operations Lead to the
Team Lead OpenClaw Agent.

Template: `docs/templates/assignment-packet.md`

Minimum fields:

- Work Unit id.
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

The Assignment Packet must be explicit enough that the Team Lead can execute
without relying on unstated context from the Operations Lead.

## Evidence & Result Record

Status: Manual Day-0

The Evidence & Result Record is the proof bundle used for review.

Template: `docs/templates/evidence-result-record.md`

It may include:

- PR links.
- Test output.
- Reports.
- Source links.
- Screenshots.
- Generated artifacts.
- Review notes.
- Remaining risks.

The Operations Lead decides whether the Work Unit is complete based on the
evidence and the Assignment Packet criteria.

## Planned Components

The components below are part of the architecture, but they are not implemented
as installable software in this repo yet.

### Ops Claim Ledger

Status: Repo-local script supported

Ops Claim Ledger will track expected responsibility claims.

It is not a database of truth, progress history, event log, dashboard backend,
or recovery system.

Current practice: use `scripts/ops_claim_ledger.py` to maintain a small
JSON-backed responsibility ledger. Manual `claim.md` files may still be used as
public-safe examples or evidence artifacts, but the JSON ledger is the supported
repo-local source for active claim state.

Future setup path: package the same behavior as `openclaw-company-ops claim
create`, `openclaw-company-ops claim update`, and `openclaw-company-ops claim
status`.

### Pulse Monitor

Status: Repo-local script supported

Pulse Monitor will compare Ops Claim Ledger expectations with available
OpenClaw session and compaction signals.

It is alert-only.

It must not:

- Restart agents.
- Recover agents.
- Reassign work.
- Cancel work.
- Modify GitHub.
- Modify execution state.
- Mark completion.
- Infer a fallback source of truth.

Current practice: use `scripts/pulse_monitor.py` to run an alert-only check
against the JSON claim ledger. Optional session snapshots can supply active
owner session refs and compaction counts.

Future setup path: package the same behavior as `openclaw-company-ops pulse
check`, then optionally schedule it as an alert-only job.

### Discord Ops Bridge

Status: Visibility formatter supported, publisher gated

Discord Ops Bridge will publish normalized operating events to Discord.

It is a visibility bridge, not a command router and not a state owner.

Current practice: the Operations Lead or Team Lead posts concise updates that
link back to the relevant source artifact. Pulse Monitor alert JSON can be
formatted with `scripts/discord_ops.py` before manual posting.

Post-setup path: first verify manual or formatter-assisted posting in
pre-dogfood visibility setup. The first approved send path should be a
foreground publisher that sends one explicit card, immediately reads it back,
and records proof. Do not connect a daemon, scheduler, or automatic bridge until
a later activation decision justifies that extra surface. Any publisher must
emit the same event shape without deciding, recovering, reassigning, closing, or
mutating Work Units.

### Company Dashboard

Status: GitHub Project dashboard accepted with bounded auto-sync

Company Dashboard will show company-wide Work Unit state.

The accepted default is a GitHub Project plus deterministic source-backed sync.
It is a visibility layer, not a source of truth.

Current practice: review the GitHub Issues list and linked artifacts, or render
a local visibility snapshot with `scripts/dashboard_snapshot.py`.

Setup path: configure the GitHub Project fields and bounded `project-sync`
workflow described in `docs/company-dashboard-timing.md`. Final Company Ops
completion requires GitHub Project or equivalent dashboard visibility unless the
owner explicitly records a no-go decision with rationale.

### Templates

Status: Manual Day-0

The current repo includes Manual Day-0 templates:

- `docs/templates/work-card.md`
- `docs/templates/assignment-packet.md`
- `docs/templates/ops-claim-ledger-entry.md`
- `docs/templates/evidence-result-record.md`
- `docs/templates/operations-lead-decision.md`
- `docs/templates/team-playbook.md`

The GitHub Issue form for Work Cards lives in:

- `.github/ISSUE_TEMPLATE/work-card.yml`

These templates make the manual loop reproducible. They are not an implemented
runtime, database, dashboard, command router, or recovery system.

The first worked manual example lives in:

- `docs/examples/manual-dry-run/WU-20260604-001/`
- `docs/examples/manual-dry-run/WU-20260604-002/`
- `docs/examples/manual-dry-run/WU-20260604-003/`
- `docs/examples/manual-dry-run/WU-20260604-004/`

## Future Installation Path

Status: Concept

As components become real, this guide should be updated in place.

Repo-local entrypoint:

```bash
python3 scripts/openclaw_company_ops.py --help
```

The intended transition:

- `Concept` sections become architecture references or are removed.
- `Planned` sections become installation and configuration instructions.
- `Manual Day-0` steps become fallback-free operating checks or are replaced by
  supported commands.
- `Implemented` sections become the user-facing setup path.

Do not keep duplicate implementation and user guides unless the project grows
large enough to justify that split.

## No Legacy / No Fallback Rules

Status: Manual Day-0

These rules apply now and after implementation:

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- No Discord command router in v1.
- No required database for the v1 ledger.
- No GitHub Issue, PR summary, dashboard note, or Discord message may replace
  the Assignment Packet.
- No dashboard or Discord event may replace Evidence & Result Records.
- If a required artifact is missing, mark the Work Unit blocked instead of
  substituting another artifact.

## Current Completion Criteria

Status: Manual Day-0

The current setup is ready for a manual dry run when:

- A Work Card can link to a real Assignment Packet.
- A Team Lead OpenClaw Agent can receive exactly one Work Unit.
- The Team Lead can produce an Evidence & Result Record.
- The Operations Lead can make and record a decision.
- Any missing claim, evidence, or assignment artifact is treated as blocked,
  not replaced by a fallback.

The first manual dry run is documented at:

- `docs/examples/manual-dry-run/WU-20260604-001/`

The second manual dry run is documented at:

- `docs/examples/manual-dry-run/WU-20260604-002/`

The third manual dry run is documented at:

- `docs/examples/manual-dry-run/WU-20260604-003/`

The fourth manual dry run is documented at:

- `docs/examples/manual-dry-run/WU-20260604-004/`

The first small Work Unit artifact generator exists as
`scripts/work_unit_artifacts.py`, and the first repo-local Ops Claim Ledger CLI
exists as `scripts/ops_claim_ledger.py`. The first repo-local Pulse Monitor
check exists as `scripts/pulse_monitor.py`. The first bounded multi-team smoke
exists as `scripts/company_ops_smoke.py`. The first Discord alert formatter
exists as `scripts/discord_ops.py`. The first dashboard snapshot CLI exists as
`scripts/dashboard_snapshot.py`. The first non-installing Pulse Monitor daemon
runner exists as `scripts/pulse_daemon.py`.

The next recommended step is still not packaging. Phase 5.1 has accepted the
visibility contract; continue the remaining activation gates in
`docs/post-setup-plan.md`: decide the hook/dashboard/publisher-hardening and
scheduled-monitor gates, lock the Phase 6 surface, then proceed to
packaging/public v1 and cross-project adoption.
