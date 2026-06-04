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

Most operating elements are currently documented as concepts, planned
components, or manual Day-0 practices. The setup guide labels each element by
status so the public docs can later be updated in place into installation and
connection instructions as components are implemented.

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

- Turn the repo-local entrypoint into a small reproducible package for other
  users when the operating surface stabilizes.
