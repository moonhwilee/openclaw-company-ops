# Codex Hook Harness

Status: Narrow Phase 5.2 MVP implemented; full hook harness remains deferred

This document is the source of truth for Company Ops hook decisions. It records
what hooks enforce, what they must not do, when they may expand, and what
evidence is required before expansion.

Hooks are optional guardrails around the existing operating model. They are not
the operating model.

## Current Decision

The full hook harness remains unimplemented. Phase 5.2 accepted only a narrow
repo-local MVP:

```text
.codex/hooks.json
.codex/hooks/company_ops_gate.py
```

The MVP has three deterministic guard surfaces:

- `PreToolUse`: hard-blocks only clear red lines such as `sudo npm`,
  `sudo openclaw`, `git reset --hard`, destructive user-change reverts, and
  obviously unsafe broad `rm -rf` targets.
- `Stop`: no-ops without Work Unit context; with Work Unit context, checks for
  source artifacts before completion reporting.
- `PreCompact`: no-ops without Work Unit context; with Work Unit context,
  warns when handoff text lacks claim, evidence, decision, or next-action
  state.

It returns JSON feedback, writes no files, calls no network APIs, sends no
Discord messages, mutates no claims, and does not replace Operations Lead
judgment.

The earlier rule was to avoid a full harness before Phase 1, Phase 2, or the
Phase 3 friction patch so those phases could reveal real operating risks first.

Phase 3.5 was the optional insertion point after Phase 3 and before Phase 4.
Phase 4 completed without opening that MVP, so the hook decision point moved to
Phase 5.2 in `docs/post-setup-plan.md`.

The historical insertion point remains:

```text
Phase 3.5: Hook Harness MVP
```

That timing was deliberate:

- Phase 1 should prove Discord visibility without adding a new moving part.
- Phase 2 should run one real dogfood Work Unit manually so real failure modes
  are observed instead of imagined.
- Phase 3 should patch the concrete friction from dogfood.
- Phase 4 should have used the MVP if real Team Lead delegation otherwise
  depended too much on manual completion and red-line discipline.

Because Phase 4 proceeded without the hook MVP, do not reopen Phase 3.5 as a
parallel active phase. Phase 5.2 accepted a small repo-local guard, not the
full harness described by the historical Phase 3.5 candidate.

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
- Phase 3.5: Historical optional insertion point. It was not opened before
  Phase 4; keep its scope and boundaries as implementation reference.
- Phase 4: Run first Team Lead delegation. If Phase 3.5 was accepted, run with
  the Operations Lead hook active; otherwise record observed completion,
  sequence, and handoff risks for Phase 5.2.
- Phase 5.2: Accepted the small repo-local Completion / Hook Guard MVP.
  Further expansion requires explicit yes/no rationale and must preserve the
  no-mutation boundaries in this document.
- Phase 5.3-5.6: Keep hook expansion separate from dashboard, foreground
  publisher, scheduled monitor, and packaging decisions. Hooks may later check
  whether live visibility proof exists before final completion, but hooks must
  not publish Discord progress themselves.
- Phase 6: If hooks are kept, document install, disable, smoke-test, and
  troubleshooting instructions as part of packaging.
- Phase 7: Cross-project adoption should be opt-in per project. Do not install
  Company Ops hooks into product repos until the project-specific source
  artifacts and checks are clear.

## MVP Implementation Shape

Any Phase 3.5 or Phase 5.2 hook MVP should be repo-local.

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

The hook should not demand `accept`. `revise` and `blocked` are valid outcomes
when evidence or context is insufficient.

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

When Phase 3.5 or Phase 5.2 opens a hook MVP Work Unit, it is accepted only if:

- hook files are repo-local and easy to disable;
- simple non-Work-Unit requests no-op;
- ambiguous-role sessions receive only the common safety layer;
- dangerous-command fixtures are blocked;
- normal repo inspection and smoke commands are not blocked;
- a seeded missing-evidence completion case is caught;
- a seeded valid blocked case is allowed;
- `python3 scripts/company_ops_smoke.py multi-team` passes;
- `python3 scripts/openclaw_company_ops.py smoke multi-team` passes;
- `git diff --check` passes;
- the implementation does not mutate GitHub, Discord, claims, or Work Cards
  except when explicitly requested as the active task.

## Deferred Candidates

These are not part of the Phase 3.5 MVP:

- Team Lead-specific scope hooks.
- Subagent-specific hooks.
- Discord publisher hooks. Publishing belongs to an explicit foreground
  publisher at the operating transition time; a Stop hook is already too late to
  create missed mid-run visibility.
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
