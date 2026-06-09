# Evidence & Result Record

Status: Ready For Review

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `WU-260609-904`
- Title: Phase 5.8.5 one-round goal no-bypass gate
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/33
- Assignment Packet: `docs/examples/manual-dry-run/WU-260609-904/assignment.md`
- Team Lead OpenClaw Agent: `revenue`
- Created at: `2026-06-09T02:53:19Z`
- Updated at: `2026-06-09T03:00:49Z`

## Result Summary

Created a concise one-round Operations Lead checklist for executing the
patched Phase 5.8.5 live gate without bypasses. The checklist is limited to
this Work Unit evidence artifact and maps to the current Phase 5.8
stabilization gate and Operations Manual.

## Evidence

Link only real artifacts or checks that exist.

- PR:
- Test output:
- Reports:
- Sources:
  - `docs/phase-5.8-stabilization-gate.md`
  - `docs/operations-manual.md`
  - `docs/examples/manual-dry-run/WU-260609-904/assignment.md`
  - `docs/examples/manual-dry-run/WU-260609-904/progress.jsonl`
  - `docs/examples/manual-dry-run/WU-260609-904/dispatch.json`
  - `docs/examples/manual-dry-run/WU-260609-904/visibility-proof.jsonl`
- Screenshots:
- Generated artifacts:
  - `docs/examples/manual-dry-run/WU-260609-904/evidence.md`
- Review notes:
  - `git status --short` was checked before result-ready preparation.
  - No source docs or repo code were modified for this Work Unit.
  - Corrected result-ready publish uses concrete contract paths:
    artifact root `docs/examples/manual-dry-run`, Project field map
    `/Users/moon/.openclaw/state/openclaw-company-ops/project-field-map.json`,
    claims ledger
    `/Users/moon/.openclaw/state/openclaw-company-ops/claims/ledger.json`,
    Project sync audit log
    `/Users/moon/.openclaw/state/openclaw-company-ops/project-sync-audit.jsonl`,
    and closeout reviewer agent `market`.

## Phase 5.8.5 One-Round No-Bypass Checklist

Use this as the operator-facing checklist for a patched Phase 5.8.5 live gate
round. Treat source artifacts as truth; Discord, GitHub Project fields,
comments, labels, and chat/session history are visibility or delivery surfaces
only.

1. Start from source.
   - Reread the Assignment Packet and current source inputs before execution:
     `docs/examples/manual-dry-run/WU-260609-904/assignment.md`,
     `docs/phase-5.8-stabilization-gate.md`, and
     `docs/operations-manual.md`.
   - Confirm the Work Unit id, Work Card, Team Lead, done criteria,
     verification criteria, no-go boundaries, and result-ready contract.

2. Prove canonical `STARTED`.
   - Run `work-unit start --dry-run`, then `work-unit start --publish`.
   - Require a source-backed `started` progress row and live team-detail
     `STARTED` readback proof before any result-ready attempt.
   - Do not manually add missing `STARTED` rows, proof-log entries, claim
     state, or status fields. If canonical start fails, record the failure as
     failed/blocked and stop the normal gate.
   - Current WU evidence: `progress.jsonl` has a `started` row and
     `visibility-proof.jsonl` has readback proof
     `WU-260609-904:team-detail:STARTED:37f5a29333d1f348`.

3. Dispatch through a fresh Work Unit-specific Team Lead session.
   - Run `work-unit dispatch --dry-run`, then publish with
     `--runtime openclaw-agent` and the configured command adapter.
   - Use the derived fresh Work Unit-specific session key by default. A
     custom/shared session key requires explicit operator override.
   - Require adapter-produced current acceptance/readback proof and execution
     enqueue proof before writing `dispatch.json` or a `dispatched` progress
     row.
   - If the adapter is missing, times out, uses fallback/synthetic proof, or
     cannot return current proof, it must fail closed as `setup-needed` with no
     dispatch source mutation.
   - Current WU evidence: `dispatch.json` records accepted/enqueued proof for
     `company-ops-revenue-wu-260609-904`, and `progress.jsonl` has a matching
     `dispatched` row.

4. Submit Team Lead result-ready with fresh reviewer wake.
   - After the one Team Lead round produces evidence, run
     `work-unit result-ready --dry-run`, then `work-unit result-ready
     --publish`.
   - Include the Evidence & Result Record as `--evidence` and `--source-ref`.
   - Request a fresh Work Unit-scoped closeout reviewer wake with
     `--closeout-reviewer-runtime openclaw-agent`,
     `--closeout-reviewer-agent <configured-independent-reviewer>`,
     `--closeout-reviewer-adapter command`, and the configured
     `scripts/openclaw_closeout_review_sessions_send.py` adapter.
   - Wait only for `RESULT_READY` readback and reviewer enqueue proof. Do not
     wait for reviewer judgment or final closeout completion in the Team Lead
     execution turn.
   - If `RESULT_READY` publishes but reviewer wake fails, do not roll back
     `RESULT_READY` and do not fake closeout. Leave the Work Unit in
     `work-unit inbox --result-ready` and recover with foreground
     `work-unit review-wake --dry-run/--publish` after setup is repaired.

5. Guard final closeout with reviewer commit request.
   - A fresh reviewer may inspect source artifacts and prepare
     `closeout-commit-request.json`; it must not run `work-unit closeout`,
     write `decision.md`, mutate Project final status, publish final Discord
     cards, archive, reassign, or send owner completion.
   - Operations Lead reruns source checks, then executes
     `work-unit closeout --commit-request @commit-request.json --dry-run`
     before publish.
   - The guarded closeout must revalidate Work Unit id, decision, source ref,
     current `RESULT_READY` proof id, artifact hashes, reviewer refs, autonomy
     class, review depth, red-line status, Work Card, and absence of an
     existing final decision.
   - `manual_required`, stale source, WU mismatch, missing proof, hash
     mismatch, duplicate final proof, existing final decision, missing source
     ref, missing Work Card, unclear red-line status, or missing reviewer refs
     must fail closed as `repair-needed`.

6. Exercise partial closeout resume.
   - Include a controlled smoke/fixture where guarded closeout publish leaves a
     matching same-decision stage after team-detail final review succeeds and
     owner-facing closeout initially fails.
   - Rerun the same Work Unit/decision/commit request in foreground.
   - Confirm it skips matching already-published team proof, publishes the
     remaining owner closeout, writes final `decision.md` only after both
     visibility publishes succeed, and marks the stage `published`.

7. Run negative fail-closed checks.
   - Verify the gate fails closed for missing canonical `STARTED`, missing live
     `STARTED` proof, fallback/synthetic dispatch proof, busy/timeout dispatch
     without current proof, reviewer wake setup-needed, WU mismatch, stale or
     existing decision, duplicate final proof, missing source ref, invalid or
     missing `RESULT_READY` proof id, hash mismatch, missing Work Card,
     `manual_required`, red-line unclear, and missing reviewer refs.
   - Confirm no hidden orchestrator, background daemon, retry loop,
     auto-recovery, auto-reassignment, reverse-import mutation, automatic
     closeout, Project-as-truth, Discord-as-truth, or owner completion appears.

8. Inspect status and mirrors after closeout.
   - Confirm final lifecycle/status agrees with the final decision:
     `accepted`, `revision_requested`, or `blocked`, while `done` remains
     reserved for later archival after owner inspection and Work Card cleanup.
   - Confirm `decision.md` preserves the Work Card reference.
   - Confirm Project and Discord are mirrors backed by source artifacts, not
     source-truth mutation inputs.

## Verification Performed

- Read the Assignment Packet before execution.
- Read `docs/phase-5.8-stabilization-gate.md`.
- Read `docs/operations-manual.md`.
- Checked `docs/examples/manual-dry-run/WU-260609-904/progress.jsonl`,
  `dispatch.json`, and `visibility-proof.jsonl` for current canonical
  start/dispatch evidence.
- Checked `git status --short` before preparing result-ready.
- Kept changes limited to
  `docs/examples/manual-dry-run/WU-260609-904/evidence.md`.

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion: Evidence includes a concise one-round checklist for Phase 5.8.5
  live execution.
  - Status: Met.
  - Evidence: `Phase 5.8.5 One-Round No-Bypass Checklist` section above.
- Criterion: Checklist covers start, fresh dispatch, result-ready reviewer
  wake, guarded closeout commit-request, partial resume, and negative
  fail-closed checks.
  - Status: Met.
  - Evidence: Checklist items 2 through 7.
- Criterion: Team Lead submits result-ready through the source-backed command.
  - Status: Submitted through the source-backed result-ready command.
  - Evidence: `visibility-proof.jsonl` RESULT_READY proof and
    `closeout-review-wake.json` reviewer wake record.

## Remaining Risks

- This artifact is an operator checklist, not proof that the full Phase 5.8.5
  live gate has passed.
- Reviewer wake and guarded closeout still depend on configured live adapter
  commands returning current proof during the actual gate.

## Open Questions

- None for this Work Unit scope.

## Team Lead Recommendation

Recommended decision:

- `accept`

Rationale:

The requested checklist has been produced inside the assigned Work Unit
evidence artifact, is mapped to the current source docs, and stays within the
Team Lead authority boundary. Operations Lead should proceed with
source-backed result-ready review and guarded closeout; no owner-facing
completion or Project final decision is requested from this Team Lead turn.

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
