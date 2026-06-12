# Work Unit Artifacts

Status: canonical repo-local artifact root

This directory is the canonical repo-local Work Unit artifact root for Company
Ops. Current active Work Unit evidence lives under one
`<artifact-root>/<work-unit-id>/` layout when active Work Units exist. The root
may be empty between active Work Units.

These artifacts are source truth and audit evidence for individual Work Units.
External surfaces such as Discord, GitHub Project dashboards, and GitHub Work
Cards are visibility mirrors unless a command explicitly readbacks and records
their convergence.

This directory is not a runtime, dashboard backend, database, command router,
recovery system, hidden retry queue, or Project source of truth.

## Current Scope

Only Work Units that remain active work should be kept in the active source
tree. Completed, removed, failed-test, Day-0, dry-run, and dogfood artifacts
should be pruned from this tree after owner-approved cleanup; they remain
recoverable from Git history when needed.

`scripts/company_ops_smoke.py multi-team` is the bounded repo-local smoke that
validates the current multi-team lifecycle without mutating external systems.

## Layout

Work Unit directories use this structure when the corresponding lifecycle step
exists:

- `assignment.md`
- `claim.md`
- `evidence.md`
- `decision.md`
- `progress.jsonl`
- `visibility-proof.jsonl`
- `handoff-preflight.json`
- `handoff-timing.json`
- `dispatch.json`
- `closeout-delegate-wake.json`
- `closeout-commit-request.json`
- `closeout-source-index.json`
- `closeout-timing.json`
- `closeout-<decision>-stage.json`
- Discord card JSON files

Handoff spec drafts may live next to Work Unit directories as
`<work-unit-id>-handoff-spec.json`.

Project sync audit is intentionally separate from repo-local Work Unit artifacts:
`~/.openclaw/state/openclaw-company-ops/project-sync-audit.jsonl`.

`handoff-timing.json` and `closeout-timing.json` are diagnostic metadata only.
They record local command step durations from `time.perf_counter()` so
operators can distinguish local rendering, source-context, publish,
Project-sync, summary-comment, and issue-close cost. They do not call external
services, add waits, or change source-truth decisions.

The final Work Card summary comment may include a derived Team Lead evidence
criteria counter such as `6/6 met before closeout`. It is an operator-facing
display of the pre-closeout `Done Criteria Mapping`, not a closeout decision.
Both bullet-prefixed `- Status:` and indented `Status:` lines are valid mapping
formats.

`closeout-source-index.json` is a derived closeout pointer index only. It may
record source artifact paths, hashes, line pointers, proof row hashes, and row
counts from the direct source scan, but it is not a source of truth and must not
contain accept/revise/block decisions, natural-language judgment summaries, or
external mirror cache data. If it is missing, stale, or mismatched, consumers
must ignore it and inspect the source artifacts directly.

## Distribution Boundary

Release/package exports include this guide and the empty artifact root, but
exclude concrete `WU-*` evidence files. Source clones should keep only current
active Work Unit artifacts; removed historical records are not active protocol
contracts. The broader package boundary is recorded in
[`../package-boundary.md`](../package-boundary.md).

## Rules

- A Work Card is the shared task card, not the Assignment Packet.
- A Protocol Capsule guides Team Lead execution, but cannot replace the
  Assignment Packet.
- A claim entry records expected responsibility, not completion truth.
- Evidence must link to real artifacts or checks.
- Operations Lead decisions must not be inferred from labels, dashboard fields,
  Discord messages, or Team Lead claims.
- If an artifact is missing, the Work Unit is blocked. Do not substitute another
  surface as a fallback source of truth.
