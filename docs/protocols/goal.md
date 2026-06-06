# goal Protocol

Status: Manual Day-0

`goal` is the Team Lead execution protocol for completing a delegated Work Unit.

It is not a separate runtime. It is a compact operating loop that the Team Lead
follows when the Assignment Packet includes a goal-mode Protocol Capsule.

## Inputs

- Assignment Packet.
- Protocol Capsule.
- Work Card.
- Ops Claim Ledger entry, when available.
- Existing evidence or artifacts, when available.

## Loop

This is a convergence loop, not a one-pass checklist. The Team Lead plans once,
then repeats implementation or improvement and verification until one stop
condition is met.

1. Restate the Work Unit goal, scope, non-goals, done criteria, and verification
   criteria from the Assignment Packet.
2. Create an Execution Plan. The Team Lead may plan work but must not rewrite
   the Assignment Packet. The plan should be proportional to the Work Unit: a
   small task may need only a few bullets, while risky or multi-step work needs
   a fuller plan.
3. Act on the plan. Use subagents only under direct Team Lead control.
4. Run `verify` against the outputs and evidence.
5. If verification fails or is unknown, identify the concrete gap and improve
   the work.
6. Repeat `verify` after each improvement.
7. Submit an Evidence & Result Record only when done criteria pass with
   evidence, or report a true blocker.

## Live Visibility During Long Work

`goal` is not a separate runtime, so live progress is not automatic. For long
Work Units, the operating loop must surface progress at the time work is
happening:

- Publish assignment and start visibility before meaningful execution continues.
- Use `work-unit checkpoint` at each major slice boundary or at least every
  10-15 minutes while work remains active. The foreground command publishes the
  team `CHECKPOINT`, records matching `progress.jsonl` metadata after readback,
  and can run one Project mirror sync from the same payload.
- Keep checkpoint text factual: current slice, status, elapsed time or last
  checkpoint, next expected checkpoint, and source artifact or evidence pointer
  when one exists.
- If the work is a `goal` or `convergence` loop, include `--mode goal` or
  `--mode convergence`; round display is automatic when `--round` is present.
  For one-pass `verify`, keep round metadata out of the dashboard unless the
  owner explicitly asks for it with `--show-round`. If the work has a known
  phase count, include `phase_index` and `phase_total`; otherwise record only
  the current phase or slice without inventing totals.
- Do not use an LLM call just to make a checkpoint sound polished.
- Do not claim live visibility from messages generated after the result is
  already ready.

If a Work Unit uses a single long blocking command, that command must either be
supervised/yielded so checkpoints can be published, or the Work Unit is not
live-visible while the command runs.

## Stop Conditions

The Team Lead may stop only on:

- Done criteria passed with evidence.
- Explicit blocker requiring input, access, or a decision.
- Safety or budget limit.
- Operations Lead or user pause.

## Non-Completion

The following are not completion:

- A status claim.
- A subagent claim.
- A PR summary without evidence mapping.
- A dashboard, Discord, or GitHub label status.
- A first attempt that has not been verified against the Assignment Packet.

## Ownership

The Team Lead owns the Work Unit until the Operations Lead accepts the submitted
evidence. Subagents may perform partial work, but they must not receive Work
Unit ownership.
