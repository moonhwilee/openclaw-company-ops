# Visibility Card Implementation Plan

Status: Implementation prep

This plan prepares the next implementation pass for user-friendly Company Ops
Discord visibility.

## Objective

Replace generic owner-facing `#ops-feed` field dumps with concise briefing
cards while keeping `#team-*` as the detailed execution and review trail.

The implementation must not add another Team Lead execution or LLM
summarization call to the normal path. It should format and validate messages
that the Operations Lead composes from the same facts in one transition.

## Target Message Families

`#ops-feed` cards:

- Request card: `[요청]`, with `문제`, `요청`, `기준`, optional `주의`,
  optional human-readable `근거`, and `다음`.
- Completion card: `[완료]`, with `결과`, `기준 대비`, `금비 판정`, `확인`,
  optional human-readable `근거`, and `다음`.
- Blocker card: `[막힘]`, with `문제`, `원인`, `필요`, optional
  human-readable `근거`, and `다음`.

`#team-*` trail messages:

- `[ASSIGNED_DETAIL]`: goal, scope, criteria, cautions, and report format.
- `[RESULT_READY]`: result, evidence, verification, risks, and next action.
- `[ACCEPTED|REVISE|BLOCKED_DETAIL]`: decision, reason, evidence or blocker,
  and next action.

## Composer Boundary

Add a higher-level composer on top of the existing generic visibility formatter
instead of deleting the generic formatter immediately.

The existing command can remain useful for machine-readable JSON, alerts, and
backward-compatible manual formatting. The new card composer should be the
preferred interface for normal owner-facing and team-detail delegation
visibility.

## Validation Rules

The validator should reject or flag:

- `#ops-feed` output containing `Surface`, raw `Source`, mechanical `Owner`, or
  default `Public summary`.
- `#ops-feed` completion before a matching team final review event.
- Mismatched Work Unit id, team, decision, or next action between paired
  messages.
- Completion cards that do not state criteria result and verification.
- Request cards that do not state the problem, request, criteria, and next
  action.
- Source references shown as raw `Source:` fields in `#ops-feed` instead of
  readable `근거` lines.
- Messages that imply Discord is source of truth or can mutate state.

## Fresh E2E Proof

After implementation, run a fresh virtual Work Unit and verify readback order:

1. `#ops-feed`: `[요청]`.
2. `#team-*`: `[ASSIGNED_DETAIL]`.
3. `#team-*`: `[RESULT_READY]`.
4. `#team-*`: `[ACCEPTED]`, `[REVISE]`, or `[BLOCKED_DETAIL]`.
5. `#ops-feed`: `[완료]` or `[막힘]`.

The proof must use a new Work Unit id. Retroactive repair messages are not
evidence that the flow works.

## Implementation Notes

- Keep event kinds internally stable in English.
- Keep visible owner-facing card labels localizable.
- Default internal operation is Korean for long human-readable text.
- Public/package examples may use English.
- A future Discord publisher may send the composed cards, but it must remain
  publisher-only and must not route commands or mutate state.
