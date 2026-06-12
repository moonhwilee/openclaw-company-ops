# Runtime Failure And Alerting

Status: implemented-v1

This document defines the narrow Company Ops v1 alerting surface for stalled or
abnormal Work Unit execution. It is an observability tool, not an automation or
recovery engine.

## Purpose

`work-unit alert-scan` lets the Operations Lead detect Work Units that appear to
have stalled or entered an abnormal state, then report those findings to
`#ops-alerts`.

The v1 goal is simple:

- read Work Unit source artifacts;
- classify local alert events;
- optionally report the alert summary to Discord;
- record alert audit/suppression state outside the repository;
- never retry, recover, reassign, close, or mutate Work Unit source artifacts.

## Command

```bash
python3 scripts/openclaw_company_ops.py work-unit alert-scan --format json
```

To preview the Discord message without sending:

```bash
python3 scripts/openclaw_company_ops.py work-unit alert-scan \
  --discord \
  --dry-run \
  --target channel:<ops-alerts-channel-id> \
  --format json
```

To send a report:

```bash
python3 scripts/openclaw_company_ops.py work-unit alert-scan \
  --discord \
  --target channel:<ops-alerts-channel-id>
```

State is stored under:

```text
~/.openclaw/state/openclaw-company-ops/alerts/
```

## Deploying With Company Ops

To ship `alert-scan` with Company Ops, include these repo artifacts in the same
commit or package build as the rest of the Company Ops CLI:

- `scripts/work_unit_alert_scan.py`;
- the `work-unit alert-scan` parser registration in `scripts/work_unit_artifacts.py`;
- the wrapper help entry in `scripts/openclaw_company_ops.py`;
- smoke coverage in `scripts/company_ops_smoke.py`;
- this document and the README document index.

That makes the command available anywhere this Company Ops repository or package
is installed. It does not, by itself, install a daemon, cron job, LaunchAgent, or
automatic Discord delivery.

## Activation Model

There are two separate steps:

1. Deploy the command.
2. Register a caller.

After deployment, the command is available immediately for explicit foreground
use:

```bash
python3 scripts/openclaw_company_ops.py work-unit alert-scan --format json
```

For live Discord reporting, the caller must pass the actual `#ops-alerts`
target each time or through a separately approved wrapper:

```bash
python3 scripts/openclaw_company_ops.py work-unit alert-scan \
  --discord \
  --target channel:<ops-alerts-channel-id>
```

For periodic operation, register a bounded one-shot caller such as OpenClaw cron
or launchd. The registered job should run the same foreground command, use an
explicit target, and rely on suppression state to prevent repeated noise.

Registering a periodic caller changes the operating state from "available
manual command" to "actively monitoring." Until that caller exists, Company Ops
does not continuously scan.

## Local Operating State

Current local dogfood behavior is intentionally foreground-first:

- the command exists in the repo-local CLI;
- a live Discord send can be run with an explicit target;
- live sends write audit/suppression state under
  `~/.openclaw/state/openclaw-company-ops/alerts/`;
- no cron, LaunchAgent, daemon, retry, takeover, or source mutation is installed
  by this feature.

The first live send used target `channel:1512413655260594307` and read back the
message from Discord. That target is the locally configured alert channel used
for the Company Ops `#ops-alerts` surface.

## v1 Alert Types

`stale_progress`

: A Work Unit is active, but no source-backed progress or RESULT_READY proof has
  appeared within the configured threshold.

`result_missing`

: Source state indicates result-ready, but live RESULT_READY proof was not found.

`failure_recorded`

: Local dispatch/runtime state records a non-accepted status.

`drop_or_retry_recorded`

: Source progress rows record retry, drop, or takeover-related state. v1 only
  reports this; cleanup or takeover requires owner approval.

## Stale Thresholds

Defaults:

- small/docs: 30 minutes;
- normal code: 60 minutes;
- long/test-heavy: 120 minutes.

The scanner may infer a broad class from source artifact text, but operators can
override classification with `--small-work-unit-id` or `--long-work-unit-id`.

## Boundaries

The scanner is allowed to:

- read `docs/work-units/<WU>/` source artifacts;
- read local progress, dispatch, and proof files;
- write alert audit/suppression state under `~/.openclaw/state/...`;
- send a Discord message only when `--discord --target ...` is explicit.

The scanner must not:

- create, modify, or delete Work Unit source artifacts;
- retry or take over Team Lead work;
- close, reopen, or comment on GitHub issues or PRs;
- mutate Project fields;
- delete branches or worktrees;
- treat GitHub, Project, or Discord as source truth.

## Discord Policy

Default target is operator-provided `#ops-alerts`.

Repeated alerts are suppressed by event key:

- warning: 60 minutes;
- critical: 15 minutes;
- info: no suppression by default.

Suppression/audit state is only recorded when using `--record` or live
`--discord`; dry-runs do not update state.

## Follow-Up

Any retry, takeover, drop cleanup, PR close, or branch/worktree cleanup remains a
separate owner-approved operation. Alerting is evidence for review, not
permission to act.
