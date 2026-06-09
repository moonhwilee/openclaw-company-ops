# Evidence & Result Record

Status: Result Ready

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `WU-260607-001`
- Title: Dashboard sync sample request
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/20
- Assignment Packet: `docs/work-units/WU-260607-001/assignment.md`
- Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Result Summary

One fresh sample Company Ops request was pushed through the real dashboard sync
path:

- Work Card issue was created as GitHub issue #20.
- Source artifacts were created under this Work Unit directory.
- `project-sync dry-run` reported mutation-ready with no missing fields.
- `project-sync apply` added the issue to `Company Ops Dashboard`.
- Project readback confirmed the sample item and Company Ops fields.
- The first dashboard state showed `Ops Status=Assigned` while source evidence
  and decision were still draft/pending, proving the dashboard reflects source
  artifact state rather than inventing completion.

## Evidence

Link only real artifacts or checks that exist.

- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/20
- Project: https://github.com/users/moonhwilee/projects/1
- Assignment Packet:
  `docs/work-units/WU-260607-001/assignment.md`
- Claim:
  `docs/work-units/WU-260607-001/claim.md`
- Field map:
  `~/.openclaw/state/openclaw-company-ops/project-field-map.json`
- Project item readback:
  `WU-260607-001`, `Ops Status=Assigned`, `status=Todo`,
  `Source Repository=moonhwilee/openclaw-company-ops`,
  `Blocker=evidence status is Draft; decision status is Pending`.
- Final Project item readback after accepted decision:
  `Ops Status=Accepted`, `Decision=Accepted`, `Blocker=null`,
  `Evidence present=yes`.
- Convergence fix:
  `scripts/project_sync.py` now respects field aliases such as
  `Status -> Ops Status` when comparing current Project values, and uses
  `gh project item-edit --clear` when the desired value is empty.

## Verification Performed

- PASS: GitHub issue created:
  `https://github.com/moonhwilee/openclaw-company-ops/issues/20`
- PASS: `python3 scripts/openclaw_company_ops.py work-unit create --work-unit-id WU-260607-001 ...`
- PASS: `python3 scripts/openclaw_company_ops.py project-sync dry-run --work-unit-id WU-260607-001 --field-map ~/.openclaw/state/openclaw-company-ops/project-field-map.json --format json`
  returned `mutation_ready=true` and `missing_field_ids=[]`.
- PASS: `python3 scripts/openclaw_company_ops.py project-sync apply --work-unit-id WU-260607-001 --field-map ~/.openclaw/state/openclaw-company-ops/project-field-map.json --format json`
  returned `changed=1`, `failed=0`.
- PASS: `gh project item-list 1 --owner moonhwilee --limit 50 --format json`
  read back the sample item and populated Company Ops fields.
- PASS: Final `project-sync apply` after accepted decision returned
  `changed=1`, `failed=0` and updated `Blocker`, `Decision`, and
  `Last proof or last source update`.
- PASS: Re-running `project-sync apply` returned `unchanged=1`, `failed=0`,
  proving idempotency for this sample.
- PASS: `python3 -m py_compile scripts/*.py .codex/hooks/*.py`.
- PASS: `python3 scripts/company_ops_smoke.py multi-team`.
- PASS: `python3 scripts/openclaw_company_ops.py smoke multi-team`.
- PASS: `git diff --check`.

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion: A fresh Work Card exists.
  - Status: Met.
  - Evidence: GitHub issue #20.
- Criterion: Required source artifacts exist under this Work Unit directory.
  - Status: Met.
  - Evidence: `assignment.md`, `claim.md`, `evidence.md`, `decision.md`.
- Criterion: `project-sync dry-run` reports mutation-ready with no missing
  fields.
  - Status: Met.
  - Evidence: dry-run check above.
- Criterion: `project-sync apply` mutates or confirms the Project item.
  - Status: Met.
  - Evidence: apply check above, Project item id
    `PVTI_lAHOAXpIUs4BZ5tWzgu6lvw`.
- Criterion: Project readback shows the sample item and Company Ops fields.
  - Status: Met.
  - Evidence: initial and final readback checks above.
- Criterion: The `Status` versus `Ops Status` distinction is explained to the
  owner.
  - Status: Met for evidence; owner-facing explanation is in the completion
    report for this Work Unit.

## Remaining Risks

- The GitHub Project template's built-in `Status` field remains visible and
  separate from Company Ops `Ops Status`.
- This sample verifies direct one-shot apply, not yet the 5-minute reconcile
  scheduler.

## Open Questions

- Whether to keep sample issue #20 open as a visible test record or close it
  after owner review.

## Team Lead Recommendation

Recommended decision:

- `accept`

Rationale:

The sample met the bounded dashboard sync criteria and exposed the expected
Status/Ops Status distinction clearly.

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
