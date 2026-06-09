# OpenClaw Company Ops

OpenClaw Company Ops is a company-style operating structure for coordinating
multiple OpenClaw agents.

The core chain is:

```text
Owner -> Operations Lead -> Team Lead OpenClaw Agent -> Subagents
```

The Operations Lead defines work, assigns team leads, reviews evidence, and
makes final decisions. Each team lead owns one Work Unit and directly manages
its own subagents.

## First-Time User Note

Company Ops Public v1 is meant to help an Operations Lead turn owner requests
into source-backed Work Units, prepare Team Lead assignments, and review
evidence before a closeout decision. It provides a clear operating model,
templates, protocol docs, and foreground source-backed tooling for
deterministic handoff, visibility, dashboard, inbox, and closeout workflows.

It does not automatically run the company for you. Public v1 has no hidden
orchestrator, automatic completion, recovery, restart, reassignment,
cancellation, background watcher, or fallback source of truth. Discord,
GitHub Issues, GitHub Projects, and chat summaries are visibility or work
surfaces; they do not replace the Work Unit source artifacts.

Those source artifacts matter because they are the recoverable state: the
Assignment Packet, Work Card, claim state, progress/proof logs, Evidence &
Result Record, and Operations Lead Decision let a person or agent resume,
audit, verify, or reject the work without trusting memory or a transient chat
thread.

Sizeable `goal` and `verify` work is detached Work Unit work. The Operations
Lead should not hold the main session blocked on Team Lead execution; source
artifacts, claim state, proof/progress logs, and the dashboard mirror carry the
recoverable state until the Team Lead result is ready for Operations Lead
review.

## Current Status

This project is the new source for OpenClaw Company Ops. Earlier experimental
projects are reference material only and are not compatibility targets.

Current internal architecture version: v1.

Most operating elements now have either documented manual practices or
repo-local support scripts. The owner-visible dogfood, friction patch, first
real Team Lead delegation, Phase 5.1 visibility contract, narrow Phase 5.2 hook
guard MVP, Phase 5.3 GitHub Project dashboard sync, Phase 5.4 foreground
Discord publisher hardening, Phase 5.5 result-ready inbox/result-ready
publish/closeout decision gate, Phase 5.5a amendment dry-run gate, Phase 5.5b
draft-handoff dry-run gate, and Phase 5.6 Pulse activation decision are
complete.

Phase 5.7 Packaging Readiness Decision is complete: the Phase 6 included
surfaces, deferred surfaces, and no-go surfaces are locked. Phase 5.8
Stabilization Gate includes the distribution-critical 5.8.7 follow-up and the
5.8.8 GitHub Work Card final-result visibility blocker.
Phases 5.8.1 through 5.8.7 are implemented in the repo-local and controlled
smoke model: canonical start/result-ready guards, final closeout lifecycle
convergence, fresh-session detached dispatch, capacity policy, result-ready
closeout delegate wake, guarded `--commit-request` closeout, resumable closeout
visibility publish, duplicate RESULT_READY suppression, closeout delegate
replay-safe idempotency, delegated closeout authority, verify/fix authority
boundaries, final Project readback convergence, and minimal public-install
preflight are all present. Phase 6 Packaging / Public v1 can begin after owner
acceptance of the Phase 5.8.7 boundary/convergence implementation and the
Phase 5.8.8 GitHub Work Card final-result visibility boundary.

Company Ops capacity sizing is a general operating policy, not a phase-local
patch. See [`docs/capacity-policy.md`](docs/capacity-policy.md) for OpenClaw
host recommendations, Company Ops active Work Unit caps, and subagent budget
contracts.

Phase 5.1 accepted the visibility contract: `discord card`, foreground
`discord publish-card`, and `discord proof-validate` are the stable live
visibility path. Phase 5.2 accepted only a narrow, optional repo-local hook
guard: `.codex/hooks.json` plus `.codex/hooks/company_ops_gate.py`. The guard
blocks clear red-line commands and checks Work Unit completion/handoff
structure; it does not publish progress, store state, or replace source
artifacts. Phase 5.6 accepted manual/foreground `pulse check` and deferred
scheduled Pulse activation with trigger; daemon installation remains no-go for
now.

Owner-visible dogfood uses `#ops-feed` as the owner-facing request/result
briefing timeline and `#team-*` as the detailed Team Lead execution trail.
`#ops-feed` should show concise cards about the problem, request, criteria,
result, verification, and next action; it should not expose internal formatter
fields. Direct Team Lead answers are allowed, but they do not mutate official
Work Unit state unless the normal source artifacts exist.

Repo-local tooling is available through:

```bash
python3 scripts/openclaw_company_ops.py --help
```

The target distributable shape is not a memory edit, standalone skill, or
standalone CLI. Public v1 should be a Company Ops plugin or package that
includes a small Company Ops skill for natural-language routing plus foreground
CLI tools for deterministic route, inbox, closeout, dashboard, and visibility
operations. Phase 5.7 has locked the included surfaces; the current repository
layout stays repo-local until Phase 6 creates the installable layout.

The package is installed into the OpenClaw runtime/workspace used by the
Operations Lead agent. It does not install instructions into the human owner or
write private memory. Phase 6 may include optional guided team setup for users
who start with a single OpenClaw agent, but that setup must be dry-run first
and must require explicit confirmation before creating or binding Team Lead
agents or external resources.

The packaged Company Ops skill, protocol docs, templates, and CLI should be a
shared install capability for the Operations Lead and Team Lead agents in the
same Company Ops runtime. If Team Leads run in separate OpenClaw runtimes or
workspaces, Phase 6 packaging must either install/expose the same package there
or produce an explicit setup-needed checklist; it must not rely on the
Operations Lead's chat memory as the only transfer mechanism. Shared access
does not mean shared authority. The Operations Lead owns routing,
`pulse check`, result-ready inbox review, closeout decisions, configured
Project/Discord mutation, and owner-facing completion. Team Leads may use the
shared protocol references and source-backed CLI only inside their assigned
Work Unit to refresh claims, follow the Assignment Packet, run verification,
and submit evidence/results. Phase 5.7 recorded this boundary; Phase 6 is when
the installable package layout and any role-scoped command guards are actually
built. Until then, this repository's docs, templates, and scripts are the
repo-local model, not a published package.

Packaged users should operate Pulse the same way as this repo: as an explicit
foreground check, not as an installed watcher. The packaged CLI should expose
`pulse check`, read the user's local claim ledger by default, and optionally
accept a local session snapshot for session/compaction checks. Installation
must not create cron, launchd, daemon, or `#ops-alerts` delivery.

External mutation setup is also foreground-only. Project mutation requires an
apply-ready local field map plus GitHub auth with Project scope, and Discord
publishing requires explicit targets and proof logs. Public v1 should guide
users through setup/preflight checks and fail closed when configuration or
permission is missing; it must not auto-create Projects, bind Discord channels,
guess targets, or grant permissions on the user's behalf.

## Documents

- [Architecture](docs/architecture.md)
- [Team Lead Protocols](docs/protocols/README.md)
- [Setup Guide](docs/setup-guide.md)
- [Implementation Setup Guide](docs/implementation-setup-guide.md)
- [Manual Day-0 Templates](docs/templates/README.md)
- [Operations Manual](docs/operations-manual.md)
- [Phase 5.8 Stabilization Gate](docs/phase-5.8-stabilization-gate.md)
- [Discord Event Visibility](docs/discord-event-visibility.md)
- [Visibility Card Implementation Plan](docs/visibility-card-implementation-plan.md)
- [Company Dashboard Timing](docs/company-dashboard-timing.md)
- [Post-Setup Realization Plan](docs/post-setup-plan.md)
- [Work Unit Artifacts](docs/work-units/README.md)

## Project Rules

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, or completion.
- No required database for the v1 ledger.
- No Discord command router in v1.
- No protocol runtime, classifier, or hidden runtime in v1.

## Planned Work

- Accept Phase 5.8.7 and implement/accept Phase 5.8.8 GitHub Work Card final
  result visibility, then run the Phase 5.8.9 Discord Progress display cleanup
  as a P1 readability slice without changing internal checkpoint proof
  semantics. Phase 6 Packaging / Public v1 begins from the stabilized
  verify-only boundary, goal/fix mutation authority, final GitHub Project live
  readback, final Work Card summary visibility, and distribution preflight
  readiness contract.
- Treat GitHub Project or equivalent dashboard visibility as part of final
  completion unless the owner explicitly records a no-go decision with
  rationale.
- Turn the repo-local entrypoint into the accepted plugin/package plus small
  skill distribution.
- Keep scheduled Pulse, scheduled dashboard reconcile, daemon install, route
  helpers, amendment apply/record, automatic closeout, automatic ops-alerts
  publishing, hidden orchestrators, and fallback truth sources out of public v1
  unless a later explicit gate changes that decision. Foreground `work-unit
  closeout --dry-run/--publish` remains an accepted Operations Lead surface.
