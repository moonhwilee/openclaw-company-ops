# Work Unit Artifacts

Status: canonical repo-local artifact root

This directory is the canonical repo-local Work Unit artifact root for Company
Ops. It contains historical dry-run, smoke, dogfood, and live-gate evidence
under one `<artifact-root>/<work-unit-id>/` layout.

These artifacts are source truth and audit evidence for individual Work Units.
External surfaces such as Discord, GitHub Project dashboards, and GitHub Work
Cards are visibility mirrors unless a command explicitly readbacks and records
their convergence.

This directory is not a runtime, dashboard backend, database, command router,
recovery system, hidden retry queue, or Project source of truth.

## Examples

- `WU-20260604-001`: validates the current Day-0 templates and produces the
  first operations manual.
- `WU-20260604-002`: validates the manual loop on a Discord event visibility
  guide.
- `WU-20260604-003`: validates the manual loop on a Company Dashboard timing
  guide.
- `WU-20260604-004`: validates the manual loop on a full implementation setup
  guide.
- `WU-20260605-001`: validates the Team Lead Protocol Capsule convention and
  packet-first `goal` / `verify` loop before CLI work starts.
- `WU-20260605-002`: real product Work Unit for the first minimal Work Unit
  artifact generator CLI.
- `WU-20260605-003`: real product Work Unit for the Team Lead Protocol Capsule
  convention and related repo-local smoke coverage.
- `WU-260606-001` through `WU-260606-003`: repo-local examples for source-backed
  state publishing, Discord visibility, and GitHub Project dashboard sync
  improvements.
- `WU-260607-001` through `WU-260607-005`: later dogfood examples for
  result-ready, revise/accept closeout, Project mirror proof, and Discord
  foreground publisher/proof paths.
- `scripts/company_ops_smoke.py multi-team`: bounded repo-local smoke that
  validates two Team Lead claims, Pulse Monitor no-alert behavior, and one
  result-ready claim update without mutating external systems.

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
exclude concrete `WU-*` evidence files. Source clones may retain historical audit
artifacts; those records are not active protocol contracts.

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
