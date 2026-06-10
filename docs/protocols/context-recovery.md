# Context Recovery Procedure

Status: Manual Day-0

Context recovery is the Team Lead support procedure for preserving continuity.

It is used after long execution, compaction, resumed sessions, or subagent
result integration. It prevents the Team Lead from losing the Work Unit goal and
done criteria.

## Inputs

- Assignment Packet.
- Protocol Capsule.
- Current evidence.
- Subagent results, if any.
- Operations Lead decisions or revision notes, if any.

## Procedure

1. Recover the Work Unit id, goal, scope, non-goals, and constraints.
2. Recover done criteria and verification criteria.
3. Summarize evidence already collected.
4. Summarize unresolved gaps, blockers, or rejected items.
5. Identify the next single action.
6. Resume `goal` or `verify` using the recovered context.

## Rules

- Do not treat a context summary as evidence.
- Do not invent new done criteria.
- Do not drop unresolved verification gaps.
- Do not replace the Assignment Packet with chat history.
- Do not continue a delegated goal loop if the Assignment Packet is missing.
- After compaction, continue normally unless the task touches Work Unit
  recovery, closeout, result-ready, terminal proof, or source/proof conflict.
- For those sensitive cases, read source artifacts and proof before acting:
  assignment, dispatch, evidence, decision, progress, visibility proof, and
  closeout stage when present.
- If a final decision plus `ACCEPTED`/`COMPLETED` proof exists, treat the Work
  Unit as terminal. Do not rewrite evidence, decision, proof, or closeout
  artifacts; report from source artifacts only.
- If `RESULT_READY` exists without a final decision, recover closeout review.
  If dispatch exists without `RESULT_READY`, treat the Work Unit as in-flight
  unless an explicit stale/timeout rule applies.
- If source artifacts and proof conflict, use a separate repair or follow-up
  path instead of mutating the closed Work Unit.

## Output

The output should be a concise continuity note:

- Current goal.
- Remaining criteria.
- Evidence so far.
- Gaps or blockers.
- Next action.
