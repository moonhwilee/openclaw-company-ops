# Evidence & Result Record

Status: Accepted

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `WU-260606-001`
- Title: Add Work Unit status summary helper
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/17
- Assignment Packet: `docs/examples/manual-dry-run/WU-260606-001/assignment.md`
- Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-06`
- Updated at: `2026-06-06`

## Result Summary

Implemented a read-only Work Unit status summary helper and exposed it through
the repo-local entrypoint as:

```bash
python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001
```

The helper reads local Work Unit artifacts, reports Work Card, Assignment
Packet, claim, evidence, decision, current expected state, missing artifacts,
audit problems, next review, and next action. It supports `--format json` for
future formatter inputs. It does not mutate GitHub, Discord, claim ledger,
evidence, decision, dashboard, recovery, reassignment, or completion state.

## Evidence

Link only real artifacts or checks that exist.

- Source:
  - `scripts/work_unit_status.py`
  - `scripts/openclaw_company_ops.py`
- Assignment Packet:
  `docs/examples/manual-dry-run/WU-260606-001/assignment.md`
- Evidence record:
  `docs/examples/manual-dry-run/WU-260606-001/evidence.md`
- Work Card:
  https://github.com/moonhwilee/openclaw-company-ops/issues/17
- Positive status summary smoke:
  `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001 --no-ledger`
- Accepted artifact status smoke:
  `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-20260605-003 --no-ledger`
- JSON parse smoke:
  `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001 --no-ledger --format json | python3 -m json.tool >/dev/null`
- Missing Work Unit smoke:
  `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-999 --no-ledger`

## Verification Performed

- `python3 -m py_compile scripts/*.py`
  - Result: passed.
- `python3 scripts/openclaw_company_ops.py --help`
  - Result: passed; help includes `status` and the
    `status work-unit --help` example.
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001 --no-ledger`
  - Result: passed; reports state `working`, Work Card issue 17, assignment,
    claim, evidence status `Draft` before this record update, decision status
    `Pending`, no missing artifacts, and explicit audit problems for draft
    evidence and pending decision.
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-20260605-003 --no-ledger`
  - Result: passed; reports state `done`, accepted evidence, accepted decision,
    no missing artifacts, and no audit problems.
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001 --no-ledger --format json | python3 -m json.tool >/dev/null`
  - Result: passed.
- `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-999 --no-ledger`
  - Result: passed as a negative smoke; command exited `1` and reported missing
    assignment, claim, evidence, and decision artifacts clearly.
- `python3 scripts/company_ops_smoke.py multi-team`
  - Result: passed.
- `python3 scripts/openclaw_company_ops.py smoke multi-team`
  - Result: passed.
- `git diff --check`
  - Result: passed.

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion: Status command renders a readable summary for this Work Unit.
  - Status: met.
  - Evidence:
    `python3 scripts/openclaw_company_ops.py status work-unit --work-unit-id WU-260606-001 --no-ledger`
- Criterion: Command reports Work Card, Assignment Packet, claim, evidence,
  decision, current state, missing artifacts, and next review or next action.
  - Status: met.
  - Evidence: status smoke output reports all required fields.
- Criterion: JSON output is available for future dashboard or Discord formatter
  inputs.
  - Status: met.
  - Evidence: JSON parse smoke passed with `python3 -m json.tool`.
- Criterion: Missing evidence or pending decision states are shown explicitly.
  - Status: met.
  - Evidence: WU-260606-001 status smoke reported audit problems for draft
    evidence and pending decision before this result record update; decision
    remains pending.
- Criterion: Helper is read-only and does not mutate operating surfaces.
  - Status: met.
  - Evidence: implementation only reads files and optional JSON ledger data;
    it does not call any write, GitHub, Discord, dashboard, recovery,
    reassignment, completion, or claim-update path.
- Criterion: Entrypoint help includes the new command.
  - Status: met.
  - Evidence: `python3 scripts/openclaw_company_ops.py --help`.

## Remaining Risks

- The helper parses the existing markdown artifact format with simple field and
  status extraction. If future artifact templates become less regular, the
  parser may need a small update.
- The default JSON ledger path is optional. If it is missing, the helper still
  reports the local claim artifact; use `--require-ledger` when a ledger-backed
  audit must be enforced.
- Markdown parsing is intentionally simple and may need a Phase 3 friction patch
  if future templates become less regular.

## Open Questions

- None blocking review.

## Team Lead Recommendation

Recommended decision:

- `accept`

Rationale:

The requested read-only helper is implemented, exposed through the repo-local
entrypoint, and passes all Assignment Packet verification criteria. Missing or
pending audit states remain visible instead of being inferred away.

Operations Lead decision:

- `docs/examples/manual-dry-run/WU-260606-001/decision.md`

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
