# Setup Guide

This guide explains how to set up OpenClaw Company Ops in its current stage.

OpenClaw Company Ops is not yet a finished installable product. The current
repo contains a public operating model, manual Day-0 setup steps, repo-local
foreground tooling, and the accepted Phase 6 package boundary. As components
move from repo-local scripts into an installable package, this same guide should
be updated in place from manual setup notes into installation, connection, and
usage instructions.

For the current development-workspace/package-export boundary, see
`docs/package-boundary.md`.

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
  automation. Some Day-0 sections are historical baseline procedures; where a
  repo-local foreground command now exists, prefer the supported command and
  keep the manual notes as setup context or emergency repair guidance.
- `Status: Repo-local script supported`: the component has a supported
  foreground command in this repository, but is not packaged for distribution
  yet.
- `Status: Implemented`: the component has real installation, connection, and
  usage instructions for the distribution surface.

The current setup is mostly `Manual Day-0` plus `Repo-local script supported`
components. The finished installable package/plugin is still a Phase 6 target.

## Current Scope

This guide is for people who want to reproduce the operating structure before
the full toolchain exists.

It covers:

- GitHub setup for Work Cards, evidence links, and later dashboard use.
- Discord visibility setup for operational observability. It is optional for a
  generic manual reproduction, but required before accepting the first real
  post-setup dogfood Work Unit.
- Manual Assignment Packet, Work Card, and Evidence & Result Record flow.
- Repo-local components that must not be mistaken for a finished distribution
  package yet.

It does not cover:

- Installing a finished OpenClaw Company Ops package.
- Installing a Company Ops plugin/package with its bundled small skill.
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

Branch protection, rulesets, and website/homepage are deferred until the manual
workflow has enough real Work Cards to justify them. GitHub Projects are no
longer blanket-deferred: Phase 5.3 accepts a bounded dashboard mirror when the
field map, source-backed sync, and fail-closed preflight rules in
`docs/company-dashboard-timing.md` are satisfied.

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
- Phase 5.3 accepted a GitHub Project dashboard for owner-facing at-a-glance
  visibility. Phase 5.7/6 keeps it as a bounded foreground mirror of Issues and
  source artifacts, not as operating truth or a scheduled background job.
- For active long Work Units, the dashboard `Progress` field is derived from
  the latest valid `progress.jsonl` row. Prefer `work-unit checkpoint` during
  live work so Discord `CHECKPOINT`, source-backed progress, and optional
  Project mirror sync use the same payload. After terminal closeout, Project
  sync overrides checkpoint progress with `Final: Accepted`,
  `Final: Revise requested`, or `Final: Blocked` so completed Work Units do not
  look stuck mid-phase. Short non-terminal Work Units without a progress row may
  show a compact proof-derived lifecycle display from local
  `visibility-proof.jsonl`. Do not manually backfill Progress from Project
  edits or Discord text.
- `work-unit closeout --publish --project-sync-mode required` also converges
  GitHub Issue queue labels as part of the required Project sync readback. The
  same hygiene can be run explicitly with `project-sync apply
  --sync-issue-labels` or `project-sync reconcile --sync-issue-labels`. It
  removes stale queue labels and adds the one desired queue label set, but it
  does not close, reopen, archive, or otherwise treat the Issue as source
  truth.
- `Last proof or last source update` is a dashboard text mirror. Keep source
  artifact timestamps in UTC, but let `project-sync` display the value in the
  runner machine's local timezone. This field should contain timestamps only,
  not next-action prose.

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
- Lifecycle state.
- Responsibility state.
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

Create these channels in the owner's Discord server, then record each channel
as an explicit target string in the form `channel:<discord-channel-id>`.
Company Ops does not publish by channel name. Reusing the same visible channel
name after deleting or cloning a channel is not enough because Discord assigns a
new channel id.

Minimum target inventory before live dogfood:

- `ops_feed_target`: `channel:<id-for-ops-feed>`.
- `ops_alerts_target`: `channel:<id-for-ops-alerts>` if alerts are enabled.
- `team_build_pq_target`: `channel:<id-for-team-build-pq>`.
- `team_build_lab_target`: `channel:<id-for-team-build-lab>`.
- `team_market_target`: `channel:<id-for-team-market>`.
- `team_revenue_target`: `channel:<id-for-team-revenue>`.

`#ops-lead` is primarily a planning and Q&A channel. It only needs a recorded
target if an operating command will publish cards there; otherwise it is a
conversation binding, not a required `discord publish-card` target.

If channels are recreated to clear noisy test history, refresh every affected
`channel:<id>` target before the next live publish. Historical proof rows may
keep their old message and channel ids as audit history; new publishes must use
the new channel ids.

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

- `#ops-feed`: `ASSIGNED`, `COMPLETED`, `NEEDS_REVISION`, `BLOCKED`.
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
docs/work-units/<work-unit-id>/
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

## Repo-Local Components And Phase 6 Package Boundary

The components below are already part of the architecture. Some have supported
repo-local foreground scripts today; none of them should be mistaken for a
finished installable distribution until Phase 6 packages the shared
skill/docs/templates/CLI surface and role-scoped guards.

### Ops Claim Ledger

Status: Repo-local script supported

Ops Claim Ledger tracks expected responsibility claims.

It is not a database of truth, progress history, event log, dashboard backend,
or recovery system.

Current practice: use `scripts/ops_claim_ledger.py` to maintain a small
JSON-backed responsibility ledger. Manual `claim.md` files may still be used as
public-safe examples or evidence artifacts, but the JSON ledger is the supported
repo-local source for active claim state.

Phase 6 setup path: package the same behavior as `openclaw-company-ops claim
create`, `openclaw-company-ops claim update`, and `openclaw-company-ops claim
status`.

### Pulse Monitor

Status: Repo-local script supported

Pulse Monitor compares Ops Claim Ledger expectations with available OpenClaw
session and compaction signals.

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

Phase 6 setup path: package the same behavior as `openclaw-company-ops pulse
check` as a manual/foreground Operations Lead capability. Scheduled Pulse stays
deferred until a later explicit activation gate; the installer must not create
cron, launchd, daemon, or automatic alert delivery.

### Discord Ops Bridge

Status: Visibility formatter supported, publisher gated

Discord Ops Bridge publishes normalized operating events to Discord only after
explicit foreground configuration and proof capture.

It is a visibility bridge, not a command router and not a state owner.

Current practice: the supported path is a foreground publisher/proof command
that sends one explicit card, immediately reads it back, and records proof.
Manual or formatter-assisted posting remains useful as historical setup context
or emergency repair, but it is no longer the preferred current path when the
publisher is configured. Foreground publisher/proof commands may be used only
with explicit target and proof-log configuration.

Do not connect a daemon, scheduler, retry queue, or automatic bridge until a
later activation decision justifies that extra surface. Any publisher must emit
the same event shape without deciding, recovering, reassigning, closing, or
mutating Work Units.

### Company Dashboard

Status: GitHub Project dashboard accepted with bounded foreground sync

Company Dashboard shows company-wide Work Unit state.

The accepted default is a GitHub Project plus deterministic source-backed
foreground sync. It is a visibility layer, not a source of truth.

Current practice: review the GitHub Issues list and linked artifacts, or render
a local visibility snapshot with `scripts/dashboard_snapshot.py`.

Setup path: configure the GitHub Project fields and bounded `project-sync`
workflow described in `docs/company-dashboard-timing.md`. Public v1 must not
install scheduled dashboard reconcile, cron, launchd, daemon, GitHub Actions
schedule, or hidden Project mutation runner. Final Company Ops completion
requires GitHub Project or equivalent dashboard visibility unless the owner
explicitly records a no-go decision with rationale.

### Shared Distribution Surface

Status: Planned

The accepted public-v1 direction is a Company Ops plugin or package that
includes:

- a small Company Ops skill for trigger/routing instructions, including
  `ops-direct`, `team-qna`, and `detached-wu`;
- foreground CLI tools for source-backed route, Work Unit inbox, closeout,
  project sync, Discord visibility, pulse checks, and smoke validation;
- templates and docs that match the packaged commands.

The package installer must not silently edit user `MEMORY.md`, `AGENTS.md`, or
other private workspace bootstrap files. A development workspace may use a
memory pointer temporarily, but public install behavior must come from the
skill/plugin/package and explicit foreground commands.

Packaged Pulse behavior stays manual/foreground for every installer. The
installed CLI should expose `pulse check`, read the local Company Ops claim
ledger by default, and accept an optional local session snapshot. The installer
must not create cron, launchd, daemon, or automatic `#ops-alerts` delivery.
Operators run Pulse at review points such as long unattended Work Units,
stale-looking claims, or compaction/session recovery.

Installed target: the package is installed into the OpenClaw runtime/workspace
where the Operations Lead agent runs. The human owner keeps using natural
language. The Operations Lead uses the bundled skill as the routing manual and
uses the packaged foreground CLI as the ticketing, inbox, lock, dashboard, and
visibility toolset.

Project and Discord setup remains explicit foreground setup. Public v1 should
guide users through a setup/preflight check for Project field-map readiness,
GitHub `project` scope, Discord targets, proof-log paths, and readback
availability. A setup/preflight helper may report missing configuration and
next steps, but it must not grant scopes, create Projects, create Discord
channels, bind targets, publish cards, or mutate source artifacts.

The Phase 6 setup helper should be read-only by default. It should behave like
`doctor` / `preflight`: inspect package/CLI availability, local Company Ops
config, Project field-map readiness, GitHub Project scope, Discord target
configuration, proof-log path writability, claim ledger readability,
foreground `pulse check` viability, stale Project mirror hygiene, and Work
Card body rendering issues such as literal escaped newlines. The helper should
report `OK`, `WARN`, or `BLOCKED` plus exact next steps, with both
human-readable and JSON output. It must not auto-fix by granting scopes,
creating Projects or channels, guessing targets, archiving Project items,
publishing cards, starting scheduled jobs, or editing source artifacts.

Optional guided onboarding for single-agent users is a Phase 6 packaging
option, not an implemented setup step today. It should start from one OpenClaw
agent, propose a default team topology, show a dry-run plan, and require
explicit confirmation before creating or binding Team Lead agents, credentials,
Discord channels, GitHub Projects, cron jobs, or external resources. Treat the
dry-run plan as an initial setup blueprint: it tells the user which roles,
targets, config files, field maps, and manual steps are recommended or missing,
but it does not create those resources by itself. If a runtime cannot create
Team Lead agents programmatically, guided onboarding should output a manual
checklist and keep single-agent `ops-direct` mode usable while `team-qna` and
`detached-wu` report setup-needed next steps.

Guided onboarding may create Team Lead agents only after explicit foreground
approval. When it does, it should install role instructions into each Team Lead
workspace rather than relying on hidden conversation memory. The installed
instructions should be generated from Company Ops templates and should stay
small: role scope, Work Unit authority, evidence requirements, subagent budget
rules, the context-recovery package prompt from
[`docs/protocols/context-recovery.md`](protocols/context-recovery.md#package-prompt),
and the rule that Team Leads should actively consider subagents for non-trivial
`goal` and `verify` Work Units. Work Unit-specific details still belong in the
Assignment Packet; permanent operating rules belong in the Team Lead workspace
instructions.

Do not copy the Operations Lead's private memory, chat history, credentials,
tokens, or broad personal bootstrap files into Team Lead agents. Public agent
templates may be used only after curation; do not bulk-import third-party
persona packs into a user's install. A guided setup should report the exact
files it would write, the agents it would create, and the commands it would
run before asking for confirmation.

Local development Team Lead `AGENTS.md` files may be used as reference
material for package design, but public install templates must be curated and
sanitized before distribution. Do not copy local paths, private owner context,
local-only operating notes, or workspace-specific memory into the public
template.

Do not reorganize the repository into an installable layout during setup. Phase
5.7 locks the included surfaces, and Phase 6 performs the packaging layout and
install/uninstall work.

The shared distribution surface must be visible to both Operations Lead and
Team Lead agents. If Team Leads run in separate OpenClaw runtimes or
workspaces, Phase 6 must install or expose the same package, skill, docs,
templates, and CLI there too, or return a setup-needed checklist before
detached work starts. Context recovery is part of that installed prompt surface:
`docs/protocols/context-recovery.md` is the source reference, but the Team Lead
and closeout-delegate setup prompts are the actual enforcement location.
Copying all rules through chat text is not a stable distribution model.

Shared access does not mean shared authority. Operations Lead-only commands
such as Pulse review, result-ready inbox, closeout decision, Project mutation,
and owner-facing Discord completion must fail closed unless the command has an
Operations Lead role context. Team Lead commands must stay scoped to the
assigned Work Unit id and must fail closed on writes outside that Work Unit.
This is command/protocol-level guarding for public v1, not an OS-level security
boundary.

Role context should be explicit and deterministic. Phase 6 should prefer
command input first, environment second, and local config third. If role
context is missing, conflicting, or not tied to an assigned Work Unit for Team
Lead writes, mutation must fail before any source artifact, Project, or
Discord change. Read-only help, docs, status inspection, and smoke checks may
remain role-neutral when they do not mutate operating state.

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

Current active Work Unit examples live in `docs/work-units/` and are mirrored
from source artifacts into the configured GitHub Project. Older Day-0 worked
examples were removed from the active tree after the artifact layout stabilized;
use Git history when those historical records are needed.

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
- `Repo-local script supported` sections become package command instructions.
- `Manual Day-0` steps become explicit operating checks or are replaced by
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

Current active Work Unit artifacts are documented under `docs/work-units/`.
Historical Day-0 dry-run artifacts were removed from the active tree and remain
recoverable from Git history.

The first small Work Unit artifact generator exists as
`scripts/work_unit_artifacts.py`, and the first repo-local Ops Claim Ledger CLI
exists as `scripts/ops_claim_ledger.py`. The first repo-local Pulse Monitor
check exists as `scripts/pulse_monitor.py`. The first bounded multi-team smoke
exists as `scripts/company_ops_smoke.py`. The first Discord alert formatter
exists as `scripts/discord_ops.py`. The first dashboard snapshot CLI exists as
`scripts/dashboard_snapshot.py`. The first non-installing Pulse Monitor daemon
runner exists as `scripts/pulse_daemon.py`.

Phases 5.1 through 5.7 have either accepted, implemented, deferred, or rejected
their activation and package-boundary decisions. Phase 6 packaging/public v1
must wait for owner acceptance of the Phase 5.8.7 boundary/convergence
implementation and the Phase 5.8.8 GitHub Work Card final-result visibility
boundary, then continue from the included, deferred, and no-go surfaces locked
in `docs/post-setup-plan.md`. Phase 5.8.9 is implemented as a P1 Discord
Progress display cleanup, not a checkpoint proof-contract rename.
