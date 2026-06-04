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

## Output

The output should be a concise continuity note:

- Current goal.
- Remaining criteria.
- Evidence so far.
- Gaps or blockers.
- Next action.
