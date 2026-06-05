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

## Current Status

This project is the new source for OpenClaw Company Ops. Earlier experimental
projects are reference material only and are not compatibility targets.

Current internal architecture version: v1.

Most operating elements now have either documented manual practices or
repo-local support scripts. The remaining work is to prove the operating loop
with owner-visible dogfood, decide which visibility/automation gates to
activate, and package only the stable surface.

Owner-visible dogfood uses `#ops-feed` as the owner-facing request/result
timeline and `#team-*` as the detailed Team Lead execution trail. Direct Team
Lead answers are allowed, but they do not mutate official Work Unit state unless
the normal source artifacts exist.

Repo-local tooling is available through:

```bash
python3 scripts/openclaw_company_ops.py --help
```

## Documents

- [Architecture](docs/architecture.md)
- [Team Lead Protocols](docs/protocols/README.md)
- [Setup Guide](docs/setup-guide.md)
- [Implementation Setup Guide](docs/implementation-setup-guide.md)
- [Manual Day-0 Templates](docs/templates/README.md)
- [Operations Manual](docs/operations-manual.md)
- [Discord Event Visibility](docs/discord-event-visibility.md)
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

- Follow the post-setup realization plan: first make orchestration observable
  through `#ops-feed` owner summaries, `#team-*` detail trails, and direct Team
  Lead Q&A, then run a real dogfood Work Unit, patch friction, delegate to a
  real Team Lead, decide activation gates, package the stable surface, and only
  then adopt it across product repos.
- Treat GitHub Project or equivalent dashboard visibility as part of final
  completion unless the owner explicitly records a no-go decision with
  rationale.
- Turn the repo-local entrypoint into a small reproducible package only after
  dogfood, delegation, and activation gates pass.
