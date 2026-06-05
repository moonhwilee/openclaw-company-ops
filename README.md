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
repo-local support scripts. The owner-visible dogfood, friction patch, first
real Team Lead delegation, Phase 5.1 visibility contract close, and the narrow
Phase 5.2 hook guard MVP have been exercised. The remaining internal work is to
complete the later Phase 5 activation sub-gates, then package only the stable
surface.

Phase 5.1 has accepted the visibility contract: `discord card`, foreground
`discord publish-card`, and `discord proof-validate` are the stable live
visibility path. Phase 5.2 has accepted only a narrow repo-local hook guard:
`.codex/hooks.json` plus `.codex/hooks/company_ops_gate.py`. The guard blocks
clear red-line commands and checks Work Unit completion/handoff structure; it
does not publish progress or mutate operating state. Remaining Phase 5 work is
limited to the later activation decisions before packaging.

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

- Follow the post-setup realization plan from the current Phase 5 activation
  sub-gates: decide the hook/dashboard/publisher-hardening and
  scheduled-monitor gates, lock the Phase 6 packaging surface, and only then
  adopt it across product repos.
- Treat GitHub Project or equivalent dashboard visibility as part of final
  completion unless the owner explicitly records a no-go decision with
  rationale.
- Turn the repo-local entrypoint into a small reproducible package only after
  the Phase 5 activation sub-gates pass or record explicit no-go/defer
  rationale.
