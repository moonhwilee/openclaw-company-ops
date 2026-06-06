# Visibility Card Implementation Plan

Status: Active surface complete; Phase 5.1 accepted

This plan describes the first repo-local implementation pass for user-friendly
Company Ops Discord visibility.

## Objective

Replace generic owner-facing `#ops-feed` field dumps with concise briefing
cards while keeping `#team-*` as the detailed execution and review trail.

The implementation must not add another Team Lead execution or LLM
summarization call to the normal path. It should format and validate messages
that the Operations Lead composes from the same facts in one transition.

## Target Message Families

`#ops-feed` cards:

- Request card: `📌 [요청]`, with `문제`, `요청`, `기준`, optional `주의`,
  optional human-readable `근거`, and `다음`.
- Completion card: `✅ [완료]`, with `결과`, `기준 대비`, `금비 판정`, `확인`,
  optional human-readable `근거`, and `다음`.
- Blocker card: `⛔ [막힘]`, with `문제`, `원인`, `필요`, optional
  human-readable `근거`, and `다음`.

`#team-*` trail messages:

- `📋 [ASSIGNED_DETAIL]`: goal, scope, criteria, cautions, and report format.
- `📦 [RESULT_READY]`: result, evidence, verification, risks, and next action.
- `✅ [ACCEPTED]`, `🔁 [REVISE]`, or `⛔ [BLOCKED_DETAIL]`: decision, reason, evidence or blocker,
  and next action.

## Header Icon Policy

Visibility card headers must make both status and target easy to scan.

Header shape:

```text
<status-icon> [<status-label>] <work-unit-id> · <team-icon> <team>
```

Default team icons:

- `🧱 build-pq`: PrimeQuant platform engineering.
- `🧪 build-lab`: experiments, product/tooling, and smoke/prototype work.
- `📣 market`: market research, positioning, and content.
- `💼 revenue`: customer, proposal, payment, and delivery.
- `👥 <team>`: defensive fallback for an unmapped team. This is not a
  canonical role icon; if it appears in normal operations, add an explicit team
  mapping or fix the team name.

Default status icons:

- `📌 [요청]`: owner-visible assignment/request.
- `✅ [완료]`: owner-visible completion after an accepted team review.
- `⛔ [막힘]`: owner-visible blocker.
- `📋 [ASSIGNED_DETAIL]`: detailed team assignment.
- `▶️ [STARTED]`: team execution has started.
- `📦 [RESULT_READY]`: team result is ready for Operations Lead review.
- `✅ [ACCEPTED]`: Operations Lead accepted the team result.
- `🔁 [REVISE]`: Operations Lead requests revision.
- `⛔ [BLOCKED_DETAIL]`: detailed team blocker.

Alternatives considered: request can use `📝` or `➡️`; completion can use `🟢`
or `🏁`; blocker can use `🛑` or `⚠️`; result-ready can use `📤` or `🔎`;
revision can use `🛠️` or `✏️`. The defaults above are intentionally compact
and high-contrast for quick Discord scanning.

## Composer Boundary

The active visibility surface is intentionally narrow.

Use `discord card` to compose purpose-specific cards, `discord publish-card` to
send one prepared card and record readback proof, and `discord proof-validate`
to validate the live trail. Do not keep a generic compatibility formatter as a
parallel operating path. Machine-readable state belongs in source artifacts and
proof JSONL, not in an alternate Discord formatting command.

## Validation Rules

The validator should reject or flag:

- `#ops-feed` output containing `Surface`, raw `Source`, mechanical `Owner`, or
  default `Public summary`.
- `#ops-feed` completion before a matching team final review event.
- Mismatched Work Unit id, team, decision, or next action between paired
  messages.
- A sequence that starts with `#team-*` before the owner-visible `#ops-feed`
  request card.
- Any Discord-bound text that would exceed the single-message guard budget.
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

## Implemented Local Command

The first local composer is available without sending to Discord:

```bash
python3 scripts/openclaw_company_ops.py discord card ...
```

Supported local card families:

- `--surface ops-feed --kind ASSIGNED|COMPLETED|NEEDS_REVISION|BLOCKED`
- `--surface team-detail --kind ASSIGNED_DETAIL|STARTED|CHECKPOINT|RESULT_READY|ACCEPTED|REVISE|BLOCKED_DETAIL`
- `discord card-pair --ops-card-json <path> --team-card-json <path>` validates
  one ops-feed card against one team-detail card.
- `discord card-sequence --card-json <path> ...` validates the actual posting
  order for one Work Unit and prevents a team handoff from preceding the
  `#ops-feed` request card.
- `discord guard --message-file <path>` compacts arbitrary Discord-bound text
  to the same single-message budget. Use it before manually posting Team Lead
  output that did not come from `discord card`.
- Team Lead and Operations Lead prompt/template output should stay within a
  1,600-character Discord generation budget before formatter guard runs. This is
  the first defense; the formatter guard is only a deterministic size check, not
  an alternate visibility path.

The active visibility surface is intentionally narrow: compose with
`discord card`, publish one prepared card with `discord publish-card`, and
validate final live proof with `discord proof-validate`. Do not keep any
parallel Discord formatting command in normal operations.

Implemented validation:

- `#ops-feed` cards reject exposed internal labels such as `Surface`, raw
  `Source`, mechanical `Owner`, and default `Public summary`.
- `#ops-feed COMPLETED` requires `--team-final-review-kind ACCEPTED`.
- `#ops-feed BLOCKED` requires `--team-final-review-kind BLOCKED_DETAIL`.
- Required fields are enforced by card kind.
- Paired-card validation checks Work Unit id, team, compatible event kinds, and
  non-conflicting decisions.
- Generated card text, alert text, and arbitrary manually guarded text are
  compacted to stay within a single Discord message.
  The header and next action are preserved, and long body content is marked as
  partially omitted. This is deterministic compaction, not semantic LLM
  summarization. Detailed evidence belongs in the source artifact, not inside a
  long Discord post.
- Discord-bound LLM-generated handoff text has a 1,600-character prompt budget
  so most messages fit before deterministic compaction is needed.
- Formatter guard uses UTF-16 content units so Korean Hangul syllables count as
  one unit while supplementary emoji are counted conservatively.
- Sequence validation requires `#ops-feed [요청]` before `#team-*`
  `ASSIGNED_DETAIL`, and requires `RESULT_READY` plus the final Operations Lead
  review before owner-facing completion/blocker cards.
- Live visibility validation requires timestamped Discord readback proof. A
  correct sequence that is posted as a burst after completion is replay
  evidence, not a successful live visibility run.

## Implementation Notes

- Keep event kinds internally stable in English.
- Keep visible owner-facing card labels localizable.
- Default internal operation is Korean for long human-readable text.
- Public/package examples may use English.
- `CHECKPOINT` is the long-running team-detail progress card between
  `STARTED` and `RESULT_READY`.
- The first publisher surface is the foreground `publish-card` command. It
  sends one explicit card at a time, reads it back, records JSONL proof, and
  remains publisher-only. It must not route commands or mutate state.
