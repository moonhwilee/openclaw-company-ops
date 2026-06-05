# Evidence & Result Record

Status: Accepted

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `WU-20260605-003`
- Title: Pre-Dogfood Discord Visibility Setup
- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/16
- Assignment Packet: `docs/examples/manual-dry-run/WU-20260605-003/assignment.md`
- Team Lead OpenClaw Agent: `main`
- Created at: `2026-06-05`
- Updated at: `2026-06-05`

## Result Summary

Phase 1 Discord visibility is ready for the first real dogfood Work Unit.
OpenClaw Discord was configured, connected, mapped to the intended Company Ops
channels, and bound only to the approved conversational channels. A harmless
`#ops-feed` event was sent and read back. A direct owner-authored Q&A smoke in
`#team-build-pq` initially exposed stale Team Lead context, was corrected, and
then passed in a fresh `build-pq` Discord channel session.

## Evidence

Link only real artifacts or checks that exist.

- Work Card: https://github.com/moonhwilee/openclaw-company-ops/issues/16
- Source artifact:
  `docs/examples/manual-dry-run/WU-20260605-003/assignment.md`
- Channel map:
  - `#ops-lead`: `1512413555939344494`
  - `#ops-feed`: `1512413593142956153`
  - `#ops-alerts`: `1512413655260594307`
  - `#team-build-pq`: `1512413703302021140`
  - `#team-build-lab`: `1512413731752116335`
  - `#team-market`: `1512413754640564365`
  - `#team-revenue`: `1512413775393984602`
- Routing bindings:
  - `#ops-lead` -> `main`
  - `#team-build-pq` -> `build-pq`
  - `#team-build-lab` -> `build-lab`
  - `#team-market` -> `market`
  - `#team-revenue` -> `revenue`
  - `#ops-feed` and `#ops-alerts` have no conversational binding.
- Harmless ops event:
  - Channel: `#ops-feed`
  - Message id: `1512455288173629571`
  - Event included Work Unit id, source artifact, owner/next-action owner, and
    next action.
- Direct Team Lead Q&A smoke:
  - Initial owner message id: `1512457081205161984`
  - Initial bot response id: `1512457236172243066`
  - Initial result: failed content quality; `build-pq` did not find the Work
    Unit source artifact.
  - Retry owner message id: `1512458615083106414`
  - Retry bot response id: `1512458662868815956`
  - Retry result: failed due to stale Discord channel session context.
  - Final owner message id: `1512459532935237844`
  - Final bot interim response id: `1512459565914919053`
  - Final bot answer id: `1512459659963928607`
  - Final result: passed; response identified source artifact
    `docs/examples/manual-dry-run/WU-20260605-003/assignment.md`.
- Stale session handling:
  - Archived stale `build-pq` Discord channel session:
    `agent:build-pq:discord:channel:1512413703302021140`
  - Old session id: `858bbef4-e57b-49d8-b488-3dea3e3f9717`
  - Archive path:
    `/Users/moon/.openclaw/agents/build-pq/sessions/archive-phase1-stale-discord-session-20260605T1411Z`
  - Fresh passing session id: `688e774f-256e-44af-9170-fd946468390d`
- Team Lead context fix:
  - Team agent workspace instructions now point Company Ops Q&A to
    `/Users/moon/src/openclaw-company-ops` as the source of truth.

## Verification Performed

- `openclaw channels status --deep --json`
- `openclaw message read --channel discord --account default --target channel:1512413703302021140 --limit 20 --json`
- `python3 scripts/company_ops_smoke.py multi-team`
- `python3 scripts/openclaw_company_ops.py smoke multi-team`
- `openclaw config validate`
- `git diff --check`

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion: Discord setup status is recorded.
  - Status: met.
  - Evidence: Discord account `default` is configured, running, connected, and
    token status is available in `openclaw channels status --deep --json`.
- Criterion: Actual channel names or channel ids are recorded.
  - Status: met.
  - Evidence: channel map above.
- Criterion: Response trigger policy is recorded for each team channel.
  - Status: met.
  - Evidence: conversational default bindings are present for `#ops-lead` and
    the four team channels only; `#ops-feed` and `#ops-alerts` are visibility
    only.
- Criterion: Harmless event message is produced or sent.
  - Status: met.
  - Evidence: `#ops-feed` message id `1512455288173629571`.
- Criterion: One direct Team Lead Q&A path is tested.
  - Status: met after correction.
  - Evidence: final `#team-build-pq` answer id `1512459659963928607`.
- Criterion: No Discord action mutated source artifacts or operating state.
  - Status: met.
  - Evidence: Discord was used for visibility and Q&A only; repo evidence,
    claim, and decision are updated by Operations Lead artifact recording, not
    by a Discord command path.

## Remaining Risks

- Only `#team-build-pq` received a live owner-authored Q&A smoke in Phase 1.
  The other team channels have bindings and updated instructions, but their
  first live Q&A should be watched during later phases.
- The first `build-pq` responses revealed stale channel-session context. The
  stale session was archived and the new session passed, but future Team Lead
  instruction changes should either inject context explicitly or reset the
  affected channel session before acceptance testing.
- The passing `build-pq` answer included a short interim "checking" message
  before the final answer. This is acceptable for Phase 1 visibility, but later
  team-channel Q&A quality can be tightened.

## Open Questions

- None blocking Phase 1.

## Team Lead Recommendation

Recommended decision:

- `accept`

Rationale:

All required visibility, channel mapping, routing, event, and direct Q&A checks
passed after the stale session was corrected. Discord remains an observation and
direct Q&A surface only.

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
