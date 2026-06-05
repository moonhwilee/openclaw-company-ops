# Codex Hook Harness

Status: Planned, not implemented

This document is the source of truth for future Codex hook decisions in
OpenClaw Company Ops. It records what hooks should enforce, what they must not
do, when they should be introduced, and what evidence is required before
expanding them.

Hooks are optional guardrails around the existing operating model. They are not
the operating model.

## Current Decision

Do not implement the full hook harness before Phase 1, Phase 2, or the Phase 3
friction patch.

Introduce a small repo-local hook MVP after Phase 3 and before Phase 4, unless
Phase 1 or Phase 2 reveals a specific safety issue that justifies an earlier
small spike.

The intended implementation point is:

```text
Phase 3.5: Hook Harness MVP
```

This timing is deliberate:

- Phase 1 should prove Discord visibility without adding a new moving part.
- Phase 2 should run one real dogfood Work Unit manually so real failure modes
  are observed instead of imagined.
- Phase 3 should patch the concrete friction from dogfood.
- Phase 4 should not begin real Team Lead delegation until completion and
  red-line guardrails exist.

## Design Principle

Use hooks to prevent missing evidence, unsafe commands, and lost handoff
context.

Do not use hooks to decide work, mutate operating state, or create hidden
orchestration.

Good hook behavior:

- Block a dangerous command before it runs.
- Warn that a Work Unit completion report is missing evidence, decision, or
  checks.
- Remind the agent to preserve Work Unit handoff before compaction.
- Point back to the required source artifact.

Forbidden hook behavior:

- Close a Work Card.
- Mark an Ops Claim Ledger entry `done`.
- Create, assign, reassign, recover, restart, cancel, or complete a Work Unit.
- Treat Discord text as a command router.
- Mutate GitHub Projects, GitHub Issues, Discord, or the claim ledger as a
  hidden side effect.
- Replace Operations Lead judgment.

If a required source artifact is missing, the hook should block or warn and
tell the agent what to produce. It should not produce the official artifact on
the agent's behalf unless the user explicitly requested that artifact-writing
work in the current turn.

## Scope By Role

Role-specific checks must be conservative. A repo-local hook can run for
Operations Lead sessions, Team Lead sessions, subagents, and simple inspection
sessions in the same repository.

Do not assume the current role from the repository alone. Until a role signal is
explicit and reliable, apply only the common red-line guard and no-op or warn
for role-specific gates. A missing or ambiguous role signal should never cause a
Team Lead session to inherit the full Operations Lead completion gate.

### All Agents

All agents may share a narrow `PreToolUse` red-line guard.

Allowed common checks:

- Block `sudo npm`.
- Block `sudo openclaw`.
- Block `git reset --hard`.
- Block destructive `git checkout --` or equivalent user-change reverts unless
  explicitly requested.
- Block obviously destructive `rm -rf` patterns where `trash` or a safer path is
  required.
- Warn on commands that appear to print or transmit secrets.

This common layer must stay narrow. Do not block broad classes of `openclaw`,
`gh`, or Discord commands because Phase 1 and later phases need legitimate
configuration, binding, and verification commands.

### Operations Lead

The Operations Lead hook is the strongest layer because the Operations Lead is
the role that reviews evidence and records decisions.

Recommended Operations Lead checks:

- Before final completion reporting, require a Work Card, Assignment Packet,
  claim, Evidence & Result Record, and Operations Lead Decision when the task is
  a Work Unit.
- Require evidence to map back to done criteria and verification criteria.
- Require repo checks named by the Assignment Packet or a recorded blocker that
  explains why they could not run.
- Require Discord/dashboard outputs to link back to source artifacts.
- Before compaction, require a concise handoff with Work Unit id, current
  claim, evidence/decision state, blocker, and next action.

This layer may continue the agent's work by returning feedback to Codex. It
must not mutate the Work Unit state itself.

### Team Lead Agents

Team Lead hooks should be added only after Phase 4 shows they are needed.

Recommended Team Lead checks if enabled:

- Confirm an Assignment Packet exists before treating a request as delegated
  execution.
- Warn when the agent is outside the assigned Work Unit scope.
- Require a result summary and evidence links before claiming result-ready.
- Block or warn on attempts to write the Operations Lead decision, close the
  Work Card, or mark the claim `done`.

Team Lead hooks should be lighter than Operations Lead hooks. A Team Lead owns
execution and evidence, not final acceptance.

### Subagents

Do not add heavy subagent hooks in v1.

Subagent output is reviewed by the Team Lead and then by the Operations Lead.
For short or disposable subagent tasks, prompt instructions and parent-agent
review are cheaper and less brittle than hook enforcement.

## Phase Tracking

Track hook relevance through the remaining phases:

- Phase 1: No full hook harness. Observe whether Discord setup creates real
  safety needs. A tiny safety-only hook spike is allowed only if a concrete
  red-line risk appears.
- Phase 2: No full hook harness. Record any missing evidence, stale claim,
  compaction, or completion-report problems observed during real dogfood.
- Phase 3: Patch concrete friction first. Decide whether the observed issues
  justify the Phase 3.5 MVP.
- Phase 3.5: Implement the repo-local hook MVP if Phase 2/3 evidence supports
  it or if Phase 4 delegation would otherwise create unacceptable completion
  risk.
- Phase 4: Run first Team Lead delegation with the Operations Lead hook active.
  Observe whether Team Lead-specific hooks are needed.
- Phase 5: Evaluate hook expansion alongside Discord publisher, GitHub Project
  sync, scheduled Pulse Monitor, and packaging. Expansion requires explicit
  yes/no rationale.
- Phase 6: If hooks are kept, document install, disable, smoke-test, and
  troubleshooting instructions as part of packaging.
- Phase 7: Cross-project adoption should be opt-in per project. Do not install
  Company Ops hooks into product repos until the project-specific source
  artifacts and checks are clear.

## MVP Implementation Shape

The Phase 3.5 MVP should be repo-local.

Recommended files:

```text
.codex/hooks.json
.codex/hooks/company_ops_gate.py
```

The hook script should:

- Read the Codex hook event payload from stdin.
- No-op outside the Company Ops repo unless explicitly configured otherwise.
- No-op when there is no active Work Unit signal.
- No-op role-specific gates when role identity is missing or ambiguous.
- Prefer cheap structural checks before expensive smoke checks.
- Return actionable feedback that tells the agent what to do next.
- Start in warn/continue mode for non-red-line checks.
- Hard-block only clear red-line behavior.

The MVP should not create a new workflow runtime or database. It should also
document an explicit disable or bypass path for troubleshooting; the exact
mechanism should match the current Codex hook interface at implementation time.

### PreToolUse

Purpose: stop unsafe actions before they run.

Hard-block examples:

- `sudo npm`
- `sudo openclaw`
- `git reset --hard`
- destructive user-change reverts
- unsafe deletion commands where `trash` or explicit confirmation is required

Warn-only examples:

- broad GitHub or Discord mutation commands
- commands that may expose tokens
- commands that appear to close, merge, assign, reassign, or mark work done

Do not block normal inspection, smoke tests, artifact reads, channel listing,
or approved Phase 1 Discord configuration commands.

### Stop

Purpose: stop premature completion reporting.

The Stop hook should look for active Work Unit context before enforcing.
Possible signals:

- changed files under `docs/examples/manual-dry-run/WU-*`;
- an Assignment Packet path in the current task;
- a Work Unit id in current artifact paths;
- a known Work Card link in current evidence.

If active Work Unit context exists, check:

- `assignment.md` exists.
- `claim.md` exists or a JSON claim ledger entry is referenced.
- `evidence.md` exists and contains real evidence or an explicit blocker.
- `decision.md` exists when the Operations Lead is reporting acceptance.
- required checks were run or the blocker explains why they could not run.
- Discord/dashboard messages are visibility-only and link to artifacts.

The hook should not demand `accept`. `revise`, `hold`, `reject`, and `blocked`
are valid outcomes when evidence or context is insufficient.

### PreCompact / PostCompact

Purpose: reduce Work Unit context loss.

The hook should require or remind for a short handoff:

- Work Unit id.
- Work Card.
- current owner or next-action owner.
- claim state.
- evidence state.
- decision state.
- blocker if any.
- exact next action.

Do not auto-write long memory entries by default. The first implementation
should prompt for handoff or validate that it exists.

## Implementation Work Unit Acceptance Gate

When Phase 3.5 is opened as a Work Unit, it is accepted only if:

- hook files are repo-local and easy to disable;
- simple non-Work-Unit requests no-op;
- ambiguous-role sessions receive only the common safety layer;
- dangerous-command fixtures are blocked;
- normal repo inspection and smoke commands are not blocked;
- a seeded missing-evidence completion case is caught;
- a seeded valid blocked/hold case is allowed;
- `python3 scripts/company_ops_smoke.py multi-team` passes;
- `python3 scripts/openclaw_company_ops.py smoke multi-team` passes;
- `git diff --check` passes;
- the implementation does not mutate GitHub, Discord, claims, or Work Cards
  except when explicitly requested as the active task.

## Deferred Candidates

These are not part of the Phase 3.5 MVP:

- Team Lead-specific scope hooks.
- Subagent-specific hooks.
- Discord publisher hooks.
- GitHub Project sync hooks.
- Pulse Monitor auto-recovery hooks.
- automatic evidence generation.
- automatic Work Card closure.
- automatic claim `done` mutation.

Each deferred candidate needs observed evidence, explicit rationale, and a
separate activation decision before implementation.

## Recheck At Implementation Time

Before implementing hooks, re-read:

- this document;
- `docs/post-setup-plan.md`;
- `docs/operations-manual.md`;
- `docs/architecture.md`;
- the current official Codex hook documentation.

Hook event payloads and behavior may change. Treat this document as the Company
Ops policy source of truth, but verify the live Codex hook interface before
coding.
