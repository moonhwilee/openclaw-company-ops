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
- `dispatch.json`
- `closeout-delegate-wake.json`
- `closeout-commit-request.json`
- `closeout-<decision>-stage.json`
- Discord card JSON files

Handoff spec drafts may live next to Work Unit directories as
`<work-unit-id>-handoff-spec.json`.

Project sync audit is intentionally separate from repo-local Work Unit artifacts:
`~/.openclaw/state/openclaw-company-ops/project-sync-audit.jsonl`.

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
