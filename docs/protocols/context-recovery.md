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
- After compaction, continue normally unless the next action could rewrite,
  close, publish, or repair durable state.
- For those sensitive actions, read authoritative source records before acting.
- If source records show terminal state, report from those records and do not
  rewrite closed evidence or final state.
- If source records are incomplete, continue from the earliest safe pending
  step.
- If source records conflict, stop mutation and use a separate repair or
  follow-up path.

## Package Prompt

Install the following core prompt in Team Lead and closeout-delegate role
instructions. It is intentionally protocol-generic so it remains stable if
Company Ops state names change:

> After compaction/resume, continue normally unless the next action could
> rewrite, close, publish, or repair durable state. For those sensitive actions,
> do not rely on chat summary alone: first read the authoritative source records
> for the current task. If the source records show the task is already terminal,
> do not rewrite closed evidence or final state; report from the source records.
> If records are incomplete, continue from the earliest safe pending step. If
> records conflict, stop mutation and use a separate repair/follow-up path.

Add this Company Ops overlay next to the core prompt:

> Company Ops source records include the Assignment Packet, dispatch record,
> evidence/result record, Operations Lead decision, progress/proof logs, and
> closeout stage files when present.

Do not use the detailed reference below as the standing package prompt. It is
for documentation, audits, and future implementation checks.

## Company Ops Reference

When applying the generic prompt to current Company Ops artifacts:

- Final decision plus accepted/completed visibility proof is terminal. Do not
  rewrite evidence, decision, proof, or closeout artifacts.
- Result-ready proof without a final decision belongs to Operations Lead
  closeout review.
- Dispatch without result-ready proof is in flight unless an explicit stale or
  timeout rule applies.
- Source/proof conflicts require a separate repair or follow-up path instead of
  mutating a closed Work Unit.

## Output

The output should be a concise continuity note:

- Current goal.
- Remaining criteria.
- Evidence so far.
- Gaps or blockers.
- Next action.
