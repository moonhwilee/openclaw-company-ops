# Evidence & Result Record

Status: Result Ready

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `WU-260606-002`
- Title: Patch Work Unit execution visibility routing
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/18
- Assignment Packet: `docs/examples/manual-dry-run/WU-260606-002/assignment.md`
- Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Result Summary

Implemented a repo-local lifecycle event formatter for Work Unit Discord
visibility and routed it through the unified entrypoint as:

```bash
python3 scripts/openclaw_company_ops.py discord event ...
```

The formatter supports `ASSIGNED`, `STARTED`, `BLOCKED`, `RESULT_READY`, and
`DECISION`, requires Work Unit id, Work Card, owner, source artifact, and
summary, and prints either text or JSON without sending Discord messages or
mutating operating state.

Documentation now distinguishes `cli-direct` and `discord-bound` execution:
`cli-direct` does not create a team-channel execution record and must be made
visible with source-artifact-backed `#ops-feed` lifecycle events.

## Evidence

Link only real artifacts or checks that exist.

- PR: none; repo-local Work Unit patch.
- Test output:
  - `python3 scripts/openclaw_company_ops.py discord event --help`: passed.
  - Text `ASSIGNED` formatting smoke: passed.
  - JSON `RESULT_READY` formatting smoke piped to `python3 -m json.tool`:
    passed.
  - Unsupported event validation smoke with `BAD_EVENT`: failed as expected
    with `error: unsupported lifecycle event: BAD_EVENT`.
  - `python3 -m py_compile scripts/*.py`: passed.
  - `python3 scripts/company_ops_smoke.py multi-team`: passed.
  - `python3 scripts/openclaw_company_ops.py smoke multi-team`: passed.
  - `git diff --check`: passed.
- Reports:
  - No Discord messages sent.
  - No GitHub issues closed or mutated.
- Sources:
  - `scripts/discord_ops.py`
  - `docs/discord-event-visibility.md`
  - `docs/operations-manual.md`
  - `docs/examples/manual-dry-run/WU-260606-002/evidence.md`
- Screenshots: none.
- Generated artifacts: none.
- Review notes: Phase 3.5 publisher/hook automation is justified only if
  lifecycle events need automatic posting later. This patch intentionally keeps
  the formatter print-only and mutation-free.

## Verification Performed

- `python3 scripts/openclaw_company_ops.py discord event --help`
- `python3 scripts/openclaw_company_ops.py discord event --event ASSIGNED --work-unit-id WU-260606-002 --work-card https://github.com/moonhwilee/openclaw-company-ops/issues/18 --owner build-lab --source-artifact docs/examples/manual-dry-run/WU-260606-002/assignment.md --summary 'Work Unit assigned for routing and visibility patch.'`
- `python3 scripts/openclaw_company_ops.py discord event --event RESULT_READY --work-unit-id WU-260606-002 --work-card https://github.com/moonhwilee/openclaw-company-ops/issues/18 --owner main --source-artifact docs/examples/manual-dry-run/WU-260606-002/evidence.md --summary 'Evidence is ready for Operations Lead review.' --next 'Operations Lead decision.' --format json | python3 -m json.tool`
- `python3 scripts/openclaw_company_ops.py discord event --event BAD_EVENT --work-unit-id WU-260606-002 --work-card https://github.com/moonhwilee/openclaw-company-ops/issues/18 --owner build-lab --source-artifact docs/examples/manual-dry-run/WU-260606-002/assignment.md --summary 'Invalid event smoke.'`
- `python3 -m py_compile scripts/*.py`
- `python3 scripts/company_ops_smoke.py multi-team`
- `python3 scripts/openclaw_company_ops.py smoke multi-team`
- `git diff --check`

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion: `scripts/discord_ops.py` can format lifecycle events:
  `ASSIGNED`, `STARTED`, `BLOCKED`, `RESULT_READY`, and `DECISION`.
  - Status: met.
  - Evidence: `scripts/discord_ops.py`; help, text, JSON, and unsupported-event
    smokes listed above.
- Criterion: Formatter requires Work Unit id, Work Card, owner, source
  artifact, and summary.
  - Status: met.
  - Evidence: `scripts/discord_ops.py`; `discord event --help` shows all five
    fields as required options.
- Criterion: Formatter can output both text and JSON.
  - Status: met.
  - Evidence: text `ASSIGNED` smoke and JSON `RESULT_READY` smoke with parse
    validation.
- Criterion: Docs explicitly distinguish `cli-direct` and `discord-bound`
  execution routes.
  - Status: met.
  - Evidence: `docs/discord-event-visibility.md`;
    `docs/operations-manual.md`.
- Criterion: Docs state that CLI-direct execution does not create team-channel
  records and must be made visible through source-artifact-backed `#ops-feed`
  events.
  - Status: met.
  - Evidence: `docs/discord-event-visibility.md`;
    `docs/operations-manual.md`.
- Criterion: Existing setup smokes still pass.
  - Status: met.
  - Evidence: `python3 scripts/company_ops_smoke.py multi-team` and
    `python3 scripts/openclaw_company_ops.py smoke multi-team` both passed.

## Remaining Risks

- No automatic Discord publisher or hook exists yet. That remains an explicit
  future decision and should stay publisher-only if implemented.

## Open Questions

- None.

## Team Lead Recommendation

Recommended decision:

- `accept`

Rationale:

All done criteria and verification criteria passed. The patch removes the
routing ambiguity by documenting route expectations and adding a formatter that
produces source-artifact-backed lifecycle visibility events without making
Discord authoritative.

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
