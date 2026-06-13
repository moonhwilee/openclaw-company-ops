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
3. Act on the plan. Use subagents only under direct Team Lead control and
   within the Assignment Packet's `subagent_budget` contract.
4. Run `verify` against the outputs and evidence.
5. If verification fails or is unknown, identify the concrete gap and improve
   the work.
6. Repeat `verify` after each improvement.
7. Before submission, write `goal-convergence-receipt.json` for goal-mode Work
   Units. It must include this Work Unit id, the Assignment Packet done plus
   verification criterion count, and one unique `criterion_id` entry for every
   criterion with a verdict, evidence ref, and any repair/reverify refs. The
   `criterion_id` set must exactly match the generated Assignment Packet ids
   (`done-1`, `verification-1`, etc.) with no missing or extra ids. It must use
   integer `unresolved_debt_count: 0`.
   If any criterion is `fail` or `unknown`, keep the Evidence & Result Record in
   `Status: Draft`, write/refresh repair-needed details, and continue the same
   Team Lead loop. Before retrying result-ready after a repair or reverify
   cycle, increment the goal/convergence round and publish a source-backed
   `CHECKPOINT` with `--mode goal` or `--mode convergence`, `--round`, and
   `--phase-index` when a `checkpoint_contract` is available. This keeps the
   same Work Unit and Work Card append-only; do not create a new Work Unit or
   reset progress just to represent a repair round.
8. Submit an Evidence & Result Record only when done criteria pass with
   evidence, then pass the shared Result Ready Gate before any `result_ready`
   claim, progress row, Discord `RESULT_READY`, or Project `Result Ready` mirror.
   If the gate fails, treat it as repair-needed unless the failure is a true
   missing input, authority, access, safety, budget, or source-truth blocker.
   A repair-needed gate failure re-enters the same Team Lead loop and should be
   followed by the next round checkpoint before another result-ready attempt
   when checkpoint publishing is available.
   The official result-ready command performs the guarded `Status: Result Ready`
   source transition after the convergence receipt and source checks pass.

If the goal discovers follow-up issues, route each one with severity and one of
`direct_patch`, `docs_or_preflight`, `owner_decision`, or `observe`. This keeps
the Operations Lead review cheap without expanding Team Lead authority.

Cross-Work-Unit or parallelism criteria are Operations Lead-owned unless the
Assignment Packet names the exact peer Work Unit ids and source refs the Team
Lead may inspect. A Team Lead must not read or mutate unrelated Work Unit
artifacts just to prove overlap.

## Live Visibility During Long Work

`goal` is not a separate runtime, so live progress is not automatic. For long
Work Units, the operating loop must surface progress at the time work is
happening:

- Publish assignment and start visibility before meaningful execution continues.
- Use `work-unit checkpoint` at each major slice boundary or at least every
  10-15 minutes while work remains active. The foreground command publishes the
  team `CHECKPOINT`, records matching `progress.jsonl` metadata after readback,
  and can run one changed-only Project mirror sync from the same payload. In
  detached execution, Team Leads should use the dispatch packet
  `checkpoint_contract` when present so Discord `CHECKPOINT` proof and Project
  `Progress` stay in sync from one source-backed checkpoint trigger.
- Keep checkpoint text factual: current slice, status, elapsed time or last
  checkpoint, next expected checkpoint, and source artifact or evidence pointer
  when one exists.
- If the work is a `goal` or `convergence` loop, include `--mode goal` or
  `--mode convergence`, `--round <round-number>`, and `--phase-index`. The dashboard renders
  these as `R<round> · P<phase-index>/<phase-total> · <slice>` when a total is
  known, or `R<round> · P<phase-index> · <slice>` when the total is not known.
  The renderer does not clamp or ellipsize source progress text; keep the slice
  concise as a writing rule rather than relying on display truncation.
  For one-pass `verify`, keep round metadata out of the dashboard unless the
  owner explicitly asks for it with `--show-round`.
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
