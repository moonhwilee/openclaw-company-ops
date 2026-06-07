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

Sizeable `goal` and `verify` work is detached Work Unit work. The Operations
Lead should not leave the main session idle while a Team Lead executes; source
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
Discord publisher hardening, Phase 5.5 result-ready inbox and closeout dry-run
lock, Phase 5.5a amendment dry-run gate, Phase 5.5b draft-handoff dry-run gate,
and Phase 5.6 Pulse activation decision are complete.

Current Phase 5 work is limited to Phase 5.7 Packaging Readiness Decision:
lock the Phase 6 included surfaces, deferred surfaces, and no-go surfaces
before building an installable package.

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
operations. The current repository layout stays repo-local until the Phase 5.7
packaging-readiness gate locks the included surfaces and Phase 6 creates the
installable layout.

The package is installed into the OpenClaw runtime/workspace used by the
Operations Lead agent. It does not install instructions into the human owner or
write private memory. Phase 6 may include optional guided team setup for users
who start with a single OpenClaw agent, but that setup must be dry-run first
and must require explicit confirmation before creating or binding Team Lead
agents or external resources.

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
- [Discord Event Visibility](docs/discord-event-visibility.md)
- [Visibility Card Implementation Plan](docs/visibility-card-implementation-plan.md)
- [Company Dashboard Timing](docs/company-dashboard-timing.md)
- [Post-Setup Realization Plan](docs/post-setup-plan.md)
- [Manual Dry Run Examples](docs/examples/manual-dry-run/README.md)

## Project Rules

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, or completion.
- No required database for the v1 ledger.
- No Discord command router in v1.
- No protocol runtime, classifier, or hidden runtime in v1.

## Planned Work

- Complete Phase 5.7 by recording the exact Phase 6 packaging scope:
  included surfaces, deferred surfaces, and no-go surfaces.
- Treat GitHub Project or equivalent dashboard visibility as part of final
  completion unless the owner explicitly records a no-go decision with
  rationale.
- Turn the repo-local entrypoint into the accepted plugin/package plus small
  skill distribution only after Phase 5.7 locks the package boundaries.
- Keep scheduled Pulse, daemon install, route helpers, non-dry-run closeout or
  amendment apply, automatic ops-alerts publishing, hidden orchestrators, and
  fallback truth sources out of public v1 unless a later explicit gate changes
  that decision.
