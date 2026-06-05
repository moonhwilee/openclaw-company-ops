# Evidence & Result Record

Status: Result Ready

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `WU-260606-003`
- Title: Add execution route to Work Unit status summary
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/19
- Assignment Packet: `docs/examples/manual-dry-run/WU-260606-003/assignment.md`
- Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Result Summary

Implemented read-only execution route visibility in
`scripts/work_unit_status.py`.

The status helper now derives a top-level `execution_route` object from
explicit markdown fields in Work Unit source artifacts. It accepts only the
documented route values `cli-direct`, `cli-delivered`, and `discord-bound`, and
only from conservative field names such as `Execution route` or
`Execution route for this Work Unit`.

Text status output now displays the route value and source artifact. JSON status
output includes the same route metadata. Older Work Units without explicit route
metadata continue to summarize with `unknown` route instead of failing.

This Work Unit ran through the validated Discord-bound `#team-build-lab`
execution route, with source artifacts remaining the source of truth.

## Evidence

Link only real artifacts or checks that exist.

- PR: none; repo-local Work Unit patch.
- Test output:
  - `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-003`: passed; displayed `Execution route: discord-bound source=claim.md field=execution route`.
  - `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-003 --format json | python3 -m json.tool`: passed; JSON included `execution_route.value` as `discord-bound`.
  - `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-002`: passed; displayed `Execution route: cli-direct source=claim.md field=execution route for this work unit`.
  - `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001`: passed; displayed `Execution route: unknown source=missing` and summarized without audit problems.
  - `python3 -m py_compile scripts/*.py`: passed.
  - `python3 scripts/company_ops_smoke.py multi-team`: passed.
  - `python3 scripts/openclaw_company_ops.py smoke multi-team`: passed.
  - `git diff --check`: passed.
- Reports:
  - Execution route: `discord-bound`.
  - Source of truth remains repo-local Work Unit artifacts and GitHub artifacts.
  - Discord remains visibility-only; the status helper sends no Discord
    messages and performs no external mutations.
- Sources:
  - `scripts/work_unit_status.py`
  - `docs/examples/manual-dry-run/WU-260606-003/assignment.md`
  - `docs/examples/manual-dry-run/WU-260606-003/claim.md`
  - `docs/examples/manual-dry-run/WU-260606-003/evidence.md`
- Screenshots: none.
- Generated artifacts: none.
- Review notes: No Discord publishers, daemons, hooks, routing changes, GitHub
  issue mutations, or decision-state changes were implemented.

## Verification Performed

- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-003`
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-003 --format json | python3 -m json.tool`
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-002`
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001`
- `python3 -m py_compile scripts/*.py`
- `python3 scripts/company_ops_smoke.py multi-team`
- `python3 scripts/openclaw_company_ops.py smoke multi-team`
- `git diff --check`

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion: `status work-unit` displays an execution route for
  `WU-260606-003`.
  - Status: met.
  - Evidence: text status smoke displayed `Execution route: discord-bound
    source=claim.md field=execution route`.
- Criterion: JSON status output includes execution route information.
  - Status: met.
  - Evidence: JSON status smoke parsed with `python3 -m json.tool` and included
    `execution_route.value` as `discord-bound`.
- Criterion: Missing route metadata does not break summaries for older Work
  Units.
  - Status: met.
  - Evidence: `WU-260606-001` summarized successfully with `Execution route:
    unknown source=missing`.
- Criterion: `WU-260606-002` shows `cli-direct` from its existing artifact note.
  - Status: met.
  - Evidence: `WU-260606-002` status displayed `Execution route: cli-direct
    source=claim.md field=execution route for this work unit`.
- Criterion: This Work Unit's artifacts record `discord-bound` execution route.
  - Status: met.
  - Evidence: `docs/examples/manual-dry-run/WU-260606-003/claim.md` records
    `Execution route: discord-bound`; this evidence record also records
    `Execution route: discord-bound`.
- Criterion: Existing setup smokes still pass.
  - Status: met.
  - Evidence: `python3 scripts/company_ops_smoke.py multi-team` and
    `python3 scripts/openclaw_company_ops.py smoke multi-team` both passed.

## Remaining Risks

- Route parsing remains intentionally narrow. Artifacts that mention routes only
  in arbitrary prose will still report `unknown` until they add an explicit
  route field.
- The status helper reports unsupported explicit route values as `unknown`
  metadata; it does not fail status reads.

## Open Questions

- None.

## Team Lead Recommendation

Recommended decision:

- `accept`

Rationale:

All done criteria and verification criteria passed. The patch adds
source-artifact-backed route visibility to the existing read-only status helper
without making Discord authoritative or adding any publisher, daemon, hook, or
routing behavior.

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
