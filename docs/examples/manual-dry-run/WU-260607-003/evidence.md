# Evidence & Result Record

Status: Result Ready

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `WU-260607-003`
- Title: Verify Company Ops operating path
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/22
- Assignment Packet: `docs/examples/manual-dry-run/WU-260607-003/assignment.md`
- Team Lead OpenClaw Agent: `build-lab`
- Created at: `2026-06-07`
- Updated at: `2026-06-07`

## Result Summary

The verify-mode operating path worked through most real Company Ops surfaces:
short owner request, Operations Lead confirmation, GitHub Work Card, source
Assignment Packet, Discord assignment/start visibility, GitHub Project mirror,
real `build-lab` verify-only execution, and Team Lead result capture.

The Team Lead returned a `revise` recommendation. Operations Lead initially
interpreted it as conservative, but final proof validation confirmed it was the
right decision: the first two Discord cards were published in parallel, causing
the team-detail handoff to read back 12ms before the owner-facing ops-feed
request.

## Evidence

Link only real artifacts or checks that exist.

- PR:
- Test output:
- Reports:
  - Team Lead verify result:
    `docs/examples/manual-dry-run/WU-260607-003/team-lead-result.md`
- Sources:
  - Team Lead CLI response from `openclaw agent --agent build-lab --session-key agent:build-lab:WU-260607-003 --json`.
  - Discord live proof log:
    `/tmp/company-ops-verify.WU-260607-003.cdloae/proof.jsonl`.
  - GitHub Work Card:
    `https://github.com/moonhwilee/openclaw-company-ops/issues/22`.
  - GitHub Project:
    `https://github.com/users/moonhwilee/projects/1`.
- Screenshots:
- Generated artifacts:
- Review notes:
  - Operations Lead observed a Project sync lock race when publishing two
    Discord cards in parallel. The first card still posted and read back; the
    following publish synced Project state successfully.
  - Final Discord proof validation failed because ops-feed `ASSIGNED` did not
    read back before team-detail `ASSIGNED_DETAIL`.

## Verification Performed

- Operations Lead created GitHub Work Card `#22`.
- Operations Lead generated and filled Work Unit source artifacts.
- Operations Lead published and read back owner-facing `ASSIGNED` and
  team-detail `ASSIGNED_DETAIL` cards.
- Operations Lead updated the claim to `working`, published and read back
  `STARTED`, and confirmed Project Status moved to `In Progress`.
- Operations Lead invoked the real `build-lab` Team Lead via OpenClaw CLI with
  verify-only constraints.
- `build-lab` returned a criterion-by-criterion verify report and did not start
  goal-mode implementation.
- Operations Lead captured the Team Lead result in a source artifact and judged
  the `revise` recommendation appropriate after final proof validation.

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion: The Team Lead result states whether the short-request-to-verify
  workflow is operating as intended.
  - Status: met
  - Evidence:
    `docs/examples/manual-dry-run/WU-260607-003/team-lead-result.md`
- Criterion: The result distinguishes Team Lead responsibilities from
  Operations Lead responsibilities.
  - Status: met
  - Evidence: Team Lead marked post-result visibility and decision as Operations
    Lead responsibilities.
- Criterion: The result confirms whether `verify` mode prevented new
  implementation work.
  - Status: met
  - Evidence: Team Lead reported read-only inspection and no repo/GitHub/Project
    or Discord mutation.
- Criterion: The result includes a criterion-by-criterion evidence map.
  - Status: met
  - Evidence:
    `docs/examples/manual-dry-run/WU-260607-003/team-lead-result.md`
- Criterion: Any gap is clearly marked as a risk or revise item.
  - Status: met
  - Evidence: The Team Lead identified missing post-result Operations Lead steps
    and the Project sync lock race.

## Remaining Risks

- Live `discord publish-card` calls should be serialized when Project sync is
  enabled; parallel calls can race the lock.
- Assignment transitions must not publish owner-facing and team-detail cards in
  parallel; proof validation requires ops-feed assignment readback first.
- Owner confirmation evidence is visible in Telegram but not linked as a durable
  source artifact in the Work Card.

## Open Questions

- Should Company Ops add a small publisher wrapper that serializes
  `publish-card` calls for multi-card transitions?

## Team Lead Recommendation

Recommended decision:

- `revise`

Rationale:

The Team Lead recommendation was appropriate. Final proof validation showed the
same class of issue the Team Lead warned about: the lifecycle should not be
accepted until the post-result and visibility proof are valid.

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
