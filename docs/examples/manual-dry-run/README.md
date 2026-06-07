# Manual Dry Run Examples

Status: Manual Day-0

This directory contains historical and current repo-local Work Unit examples
that exercised the OpenClaw Company Ops templates as the operating loop moved
from manual Day-0 practice to supported foreground CLI commands.

The examples are evidence of the operating loop. They are not an implemented
runtime, dashboard backend, database, command router, or recovery system.

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
