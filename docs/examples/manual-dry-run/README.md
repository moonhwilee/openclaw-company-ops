# Manual Dry Run Examples

Status: Manual Day-0

This directory contains manual Work Unit examples that exercise the current
OpenClaw Company Ops templates before dedicated automation exists.

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

## Rules

- A Work Card is the shared task card, not the Assignment Packet.
- A claim entry records expected responsibility, not completion truth.
- Evidence must link to real artifacts or checks.
- Operations Lead decisions must not be inferred from labels, dashboard fields,
  Discord messages, or Team Lead claims.
- If an artifact is missing, the Work Unit is blocked. Do not substitute another
  surface as a fallback source of truth.
