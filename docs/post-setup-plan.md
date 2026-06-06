# Post-Setup Realization Plan

Status: Active post-setup plan

This plan refines the remaining OpenClaw Company Ops work after the base setup
scripts and docs exist. It does not change the architecture or goal. It changes
the order and acceptance gates so the owner can observe orchestration before
the first real dogfood Work Unit.

The target behavior remains:

- Work Cards, Assignment Packets, Ops Claim Ledger entries, Evidence & Result
  Records, and Operations Lead Decisions are the source artifacts.
- Discord and dashboards are visibility layers only.
- The owner may ask Team Lead agents direct questions in the appropriate team
  channel. Those answers are advisory, status, or clarification messages unless
  they are backed by source artifacts.
- Pulse Monitor is alert-only.
- Team Lead OpenClaw Agents own execution for one Work Unit at a time.
- The Operations Lead reviews evidence and records decisions.
- There is no hidden orchestrator, fallback truth source, command router, or
  automatic recovery/reassignment/completion.

Codex hooks are tracked as an optional guardrail layer, not as an operating
state owner. The hook policy and future implementation reference is
`docs/codex-hook-harness.md`. Use that document at implementation time rather
than relying on conversation memory.

## Phase 1: Pre-Dogfood Visibility Setup

Purpose: make orchestration observable before asking whether it works.

Set up the smallest Discord visibility path that lets the owner watch Work Unit
state changes and alerts without relying only on Operations Lead summaries.

Scope:

- Select or create the main Operations Lead channel:
  - `#ops-lead` for owner-to-Operations-Lead planning, scope alignment, phase
    decisions, and handoff preparation before Team Lead delegation.
- Select or create the visibility channels:
  - `#ops-feed` for owner-facing assignment, completion, and blocker
    summaries.
  - `#ops-alerts` for stale claim, session mismatch, and suspected compaction
    recovery alerts.
- Select or create the direct team channels:
  - `#team-build-pq` for PrimeQuant platform engineering questions.
  - `#team-build-lab` for new product and tooling questions.
  - `#team-market` for market, positioning, and content questions.
  - `#team-revenue` for customer, proposal, payment, and delivery questions.
- Bind direct team channels deliberately:
  - `#ops-lead` should route to the Operations Lead only;
  - only the matching Team Lead should answer by default;
  - the matching Team Lead may answer owner-authored messages in that team
    channel;
  - non-owner chatter should require an explicit mention or address before an
    agent answers;
  - `#ops-feed` should remain event-focused, not a general discussion channel;
  - if no agent is bound to a channel, no response should be assumed;
  - if multiple agents are bound to one channel, the routing is invalid until
    the noisy overlap is removed.
- Use the Phase 1 response trigger policy:
  - start with one Team Lead binding per team channel;
  - switch any noisy or overlapping channel to mention-required mode;
  - reserve future slash or application commands for read-only lookup such as
    `/status`, `/evidence`, or `/claim`, not state mutation.
- Decide the first send mechanism:
  - manual posting from formatter output, or
  - a one-off approved send using an existing messaging surface.
- Emit and verify at least one harmless test event that links to a real source
  artifact.
- Ask at least one harmless direct question in a team channel and verify that
  the matching Team Lead can answer without mutating official operating state.
- Confirm that no Discord message can mutate GitHub, mutate the claim ledger,
  close work, approve completion, reassign work, or recover agents.
- Observe whether Phase 1 reveals a concrete need for an early safety-only
  hook spike. Do not install the full hook harness in Phase 1.

Acceptance gate:

- Owner can ask the Operations Lead in `#ops-lead`, or fall back to the
  existing private Telegram direct chat for sensitive setup and recovery.
- Owner can open the Discord channel and see an event with Work Unit id, source
  artifact link, owner/next-action owner, and next action.
- Owner can directly ask a Team Lead a status or clarification question in the
  correct team channel and receive an answer from that Team Lead.
- Team channel response behavior is proven: the matching Team Lead answers the
  owner, non-owner chatter does not create default agent responses, and noisy
  channels can be moved to mention-required mode.
- The same event is traceable back to the Work Card, Assignment Packet, claim,
  evidence, or decision artifact.
- Direct Team Lead answers can link or explain source artifacts, but they do
  not create, close, reassign, approve, or mutate Work Units by themselves.
- Discord remains visibility-only plus direct human/agent Q&A. It is not an
  operating-state authority.
- Any early hook work, if performed, is limited to narrow red-line safety
  checks and is recorded as a spike, not as the Company Ops hook harness.

## Progress Reporting

Company Ops setup reports should include the current phase in the visible
header, for example:

```text
Task: Company Ops Setup (Phase 1/7)
Slice: Discord visibility setup | Next: connect Discord and verify routing
```

Use the seven primary phases in this document for progress reporting. Phase
3.5 is a historical optional insertion point, not a new primary phase. Current
hook activation decisions are handled under Phase 5.2.

## Phase 2: Real Dogfood Work Unit

Purpose: run one real product-shaped Work Unit through the system.

This must not be another documentation-only smoke. It should produce a small
useful product artifact, script, integration, or operational improvement.

Scope:

- Create a Work Card.
- Create the Assignment Packet with the correct Protocol Capsule.
- Create or update the Ops Claim Ledger entry.
- Assign exactly one Team Lead OpenClaw Agent.
- Have the Team Lead execute packet-first.
- Produce an Evidence & Result Record.
- Record an Operations Lead Decision.
- Emit Discord visibility messages for the major transitions.
- Record any missing evidence, stale claim, compaction, unsafe-command, or
  premature-completion friction that a future hook could prevent.

Acceptance gate:

- A person can audit the Work Unit without trusting a chat summary.
- Discord events point to the source artifacts.
- Evidence maps back to done criteria and verification criteria.
- Only an Operations Lead `accept` decision can close the Work Card.
- Hook observations are captured for later evaluation, but the full hook
  harness remains off during this first real dogfood run.

## Phase 3: Dogfood Friction Patch

Purpose: patch the first real operational pain before scaling.

Scope:

- Fix confusing CLI arguments, missing output, brittle artifact paths, stale
  docs, awkward Discord message format, or claim/evidence gaps found in Phase 2.
- Keep fixes narrow and repo-local unless a broader package boundary is clearly
  justified.
- Preserve all no-fallback and visibility-only rules.
- Decide whether the concrete Phase 2 friction justifies the Phase 3.5 hook
  MVP described in `docs/codex-hook-harness.md`.

Acceptance gate:

- The specific friction observed in Phase 2 is removed or documented as an
  explicit limitation.
- Existing setup smokes still pass.
- The owner can still audit the Work Unit trail through artifacts plus
  visibility messages.
- Any hook decision has a yes/no rationale. If hooks are still not justified,
  record why and proceed without them.

## Phase 3.5: Hook Harness MVP

Status: optional pre-Phase-4 insertion point, not executed before Phase 4.
Current hook activation is reconsidered under Phase 5.2 based on observed
completion, sequence, and handoff risks.

Purpose: record the optional minimum Codex hook guardrails that could have been
added before scaling to real Team Lead delegation.

This phase was optional until Phase 2/3 evidence justified it. It would have
been completed before Phase 4 if the next delegation otherwise relied too much
on manual completion discipline.

Implementation reference: `docs/codex-hook-harness.md`.

Scope:

- Implement a repo-local hook MVP, not a user-global workflow platform.
- Prefer `.codex/hooks.json` plus `.codex/hooks/company_ops_gate.py`.
- Add a narrow `PreToolUse` red-line guard for clearly dangerous commands.
- Add an Operations Lead `Stop` completion gate for Work Unit evidence,
  decision, and check omissions.
- Add `PreCompact` / `PostCompact` handoff validation or reminders.
- Start non-red-line checks in warn/continue mode.
- Keep Team Lead-specific hooks deferred unless Phase 4 risk is already clear.
- Do not mutate GitHub, Discord, claim state, Work Cards, or decisions from the
  hook.

Acceptance gate:

- Simple non-Work-Unit requests no-op.
- Dangerous-command fixtures are blocked.
- Normal repo inspection, artifact reads, and smoke commands are not blocked.
- A seeded missing-evidence completion case is caught.
- A seeded valid blocked or hold case is allowed.
- Existing setup smokes still pass.
- The hook can be disabled or bypassed deliberately for troubleshooting.
- No hook behavior creates hidden orchestration, automatic recovery,
  reassignment, completion, or fallback truth.

Current state:

- Phase 4 completed without opening this MVP.
- The relevant hook decision is now Phase 5.2, not a return to a pre-Phase-4
  branch.
- If Phase 5.2 accepts a hook MVP, reuse this section's boundaries and
  `docs/codex-hook-harness.md` as the implementation policy.

## Phase 4: First Real Team Delegation

Purpose: prove the team-lead model, not just the Operations Lead loop.

Default route:

- Phase 4 proved that strict `discord-bound` routing can work, but it is not
  the normal operating path. The default path is now `CLI-first + #ops-feed
  owner summary + #team-* detail trail`.
- Operations Lead assigns through CLI or a local agent session for speed.
- Operations Lead posts one owner-facing `[ASSIGNED]` summary in `#ops-feed`.
- Operations Lead posts one `[ASSIGNED_DETAIL]` entry in the relevant
  `#team-*` channel.
- Multi-card assignment visibility is a serial lifecycle transition: publish
  and read back the owner-facing assignment before publishing the team-detail
  handoff.
- Team Lead reports back through the CLI path and includes a concise result
  summary, verification summary, changed/source artifacts, blocker if any, and
  next action.
- Operations Lead posts detailed trail entries such as `[STARTED]` and
  `[RESULT_READY]` in the relevant `#team-*` channel when claim or result
  information is available.
- Operations Lead posts `[ACCEPTED]`, `[REVISE]`, or `[BLOCKED_DETAIL]` in the
  relevant `#team-*` channel after review.
- Operations Lead posts one owner-facing `[COMPLETED]` or `[BLOCKED]` summary
  in `#ops-feed` after the team detail trail has been closed.
- A team detail trail that stops at `[RESULT_READY]` is visibility-incomplete;
  `[RESULT_READY]` is the Team Lead's submission, not the Operations Lead's
  review decision.
- Discord visibility messages must not create, mutate, approve, close,
  reassign, recover, or complete Work Units.
- `discord-bound` route validation is reserved for diagnostics, owner-authored
  Q&A smoke tests, or deliberate experiments where the Discord channel itself
  must be the execution session.

Scope:

- Choose the correct standing role agent for one real assignment:
  `build-pq`, `build-lab`, `market`, or `revenue`.
- Give that agent an Assignment Packet, not a vague instruction.
- Require claim refreshes and evidence output from the Team Lead.
- Let the Team Lead use subagents directly if useful.
- Keep Operations Lead review and decision separate from Team Lead execution.
- Emit Discord visibility events for owner observability.
- Run delegation with the Operations Lead hook gate active if Phase 3.5 was
  accepted. Observe whether Team Lead-specific scope hooks are actually needed.

Acceptance gate:

- The Team Lead can execute without hidden Operations Lead intervention.
- The route is recorded truthfully, usually `cli-direct`.
- `#ops-feed` contains one owner-facing assignment summary and one owner-facing
  completion or blocker summary.
- The relevant team channel contains a detailed execution trail covering
  assignment detail, result/evidence detail, and Operations Lead review.
- The relevant team channel closes each submitted result with exactly one
  Operations Lead review event: `[ACCEPTED]`, `[REVISE]`, or
  `[BLOCKED_DETAIL]`.
- The visibility messages are composed from the Team Lead result and Operations
  Lead review in one Operations Lead composition step per transition, not from
  a separate Team Lead execution or LLM summarization call.
- The `#ops-feed` messages are owner-facing briefing cards, not generic field
  dumps. They must avoid internal fields such as `Surface`, raw `Source`,
  mechanical `Owner`, and default `Public summary`.
- CLI-triggered delivery status may be captured if used, but it is delivery
  evidence only.
- Subagent output is treated as input, not completion truth.
- Evidence and decision are sufficient for an independent audit.
- Discord visibility shows what happened without becoming the operating record.
- Team Lead-specific hooks are either explicitly deferred or proposed with
  evidence from this delegation.

Observed Phase 4 result:

- `WU-260606-003` proved the stricter route gate: owner-authored inbound in
  `#team-build-lab`, Team Lead response in the same channel, Operations Lead
  assignment/result handoff visible there, lifecycle visibility in `#ops-feed`,
  and `execution_route: discord-bound` in the source artifact.
- The result also proved that strict `discord-bound` ceremony is too expensive
  as the default. In the Phase 4 slice, the build-lab execution itself took
  about four minutes, while route validation plus manual
  visibility/evidence/decision handling took the overall slice to roughly
  eleven minutes.
- The revised default keeps the useful visibility outcome and removes the
  strict-route ceremony. Compared with the CLI-first baseline, only
  deterministic visibility card composition and manual posting are incremental.
  Expected added cost is roughly thirty to ninety seconds while posting remains
  manual.
- Rerun owner-authored route validation only when diagnosing a new channel,
  thread, binding, agent, or suspected stale session. It is not part of normal
  delegation.

## Phase 5: Activation Decision Gates

Purpose: decide which optional automation is ready to activate before packaging.

Phase 4 changed the priority from "enable more automation" to "simplify the
default visible delegation path." Phase 5 is therefore split into narrow
decision gates. Each gate either accepts a small surface, rejects it, or records
why it remains deferred. Defer is valid only when it includes rationale and a
future review trigger.

### Phase 5.1: Visibility Contract Close

Status: Accepted on 2026-06-06.

Purpose: close the formatter, reporting, and transition-time visibility
contract as the stable owner-visible loop.

Phase 5.1 was not accepted by card shape alone. A Discord trail that is generated
or sent only after all work is complete is a replay, not live visibility. It may
prove formatting, but it does not prove that the owner could observe a long
Work Unit while it was running.

Accepted evidence:

- `discord card` can generate owner-facing `#ops-feed` briefing cards and
  `#team-*` detail trail cards locally without sending or mutating state.
- Headers include canonical state icons and team icons.
- `#ops-feed` uses owner-friendly labels such as `[요청]`, `[완료]`, and
  `[막힘]` instead of internal field dumps.
- Team detail trails close each `RESULT_READY` with exactly one Operations Lead
  review: `ACCEPTED`, `REVISE`, or `BLOCKED_DETAIL`.
- `discord card-sequence` detects missing `#ops-feed [요청]`, missing
  `RESULT_READY`, and missing final review before owner completion.
- Discord-facing generation budget is 1,600 characters, final formatter target
  is 1,800 content units, and the guard counts UTF-16 content units so Korean
  complete syllables count as one unit while supplementary characters are not
  undercounted.
- Deterministic compaction is labeled as partial omission, not semantic LLM
  summarization.
- Normal visibility does not add another Team Lead execution call or LLM
  summarization call.
- Long `goal` work has a transition-time visibility rule: assignment and start
  are posted before meaningful execution continues, and `CHECKPOINT` updates
  are posted at each major slice boundary or at least every 10-15 minutes while
  work remains active.
- E2E proof includes Discord readback timestamps showing that assignment,
  start, checkpoint, result, review, and owner closeout messages were sent near
  their operating transitions, not burst-published after completion.
- Post-hoc burst/replay messages are invalid evidence for live visibility even
  when the card content and final sequence are correct.
- Visibility send/readback failure is reported as `visibility incomplete`; it
  must not be counted as a successful visibility run.

Decision output: explicit accept/revise/no-go record for the visibility
contract. If live timing proof is missing, the decision is `REVISE`, not
`ACCEPT`.

Decision record:

- Decision: `ACCEPT`.
- Evidence:
  - `discord card`, `discord publish-card`, and `discord proof-validate` are
    the active visibility path.
  - Active legacy `discord visibility` generic formatting was removed from the
    CLI surface.
  - `WU-260606-LIVE-P0` proved live timed Discord send/readback with
    assignment, start, checkpoint, result, review, and owner closeout.
  - `WU-260606-CONVERGE-P0` repeated the timed live proof after convergence and
    no-legacy cleanup.
  - Smoke coverage rejects missing `STARTED`, `CHECKPOINT` after
    `RESULT_READY`, replay/burst proof, dry-run proof, send/readback failure,
    and duplicate card ids.
- Rationale: the owner can observe the stable CLI-first delegation loop through
  source artifacts plus live Discord readback proof without adding a second
  Team Lead execution call, LLM summarization call, hidden command router, or
  fallback truth source.
- Remaining caveat: CHECKPOINTs remain explicit operator/agent publications.
  No automatic checkpoint-needed guard, yieldable long-work runner, or daemon is
  accepted as part of Phase 5.1.

### Phase 5.2: Completion / Hook Guard MVP Decision

Status: Accepted on 2026-06-06 as a narrow repo-local MVP.

Purpose: decide whether to implement a small repo-local hook guard now.

Phase 3.5 was the optional pre-Phase-4 hook insertion point. Because Phase 4
completed without that MVP, current hook activation is reconsidered here based
on observed completion, sequence, and handoff risks.

Evaluate:

- `ops-feed [요청]` or equivalent owner-request visibility omitted before team
  detail posting.
- live transition proof, checkpoint proof, or Discord readback timestamps
  omitted before final completion reporting.
- Completion reported without evidence, decision, sequence proof, or required
  checks.
- Dangerous commands or user-change reverts attempted during Work Unit work.
- Compaction or handoff risk that can lose Work Unit id, claim, evidence,
  decision, blocker, or next action.

Allowed MVP shape:

- repo-local `.codex/hooks.json` plus `.codex/hooks/company_ops_gate.py`, or
  the current Codex-equivalent local hook shape at implementation time;
- Stop / PreToolUse / PreCompact guardrails;
- warn/continue for non-red-line checks first;
- hard block only clear red lines.

Hook timing boundary:

- Stop hooks are late safeguards. They can prevent a final completion report
  when live visibility proof is missing, but they cannot create the missed
  mid-run visibility after the owner has already waited through a silent run.
- PreCompact hooks preserve handoff context such as Work Unit id, claim,
  evidence state, last Discord checkpoint, and next expected checkpoint.
- Hooks do not publish progress. Live progress belongs to the explicit
  foreground publisher or operating loop at the moment the transition happens.

Checkpoint automation boundary:

- Do not implement `checkpoint-needed` as a user-facing Phase 5.2 feature.
  It adds little owner value after `proof-validate` and cannot solve silent
  blocking work by itself.
- Do not add a yieldable long-work runner or foreground monitor in Phase 5.2.
  That would increase harness complexity and introduce new error surfaces
  before there is concrete evidence that the cost is justified.
- If repeated silent-agent incidents appear later, evaluate a separate
  `stale-agent audit` surface that joins OpenClaw session state, claim ledger,
  and live proof timestamps. That audit may alert Operations Lead attention,
  but it must not publish semantic CHECKPOINTs or mutate work state.

No-go boundaries:

- No hook mutates GitHub, Discord, claim state, Work Cards, evidence,
  decisions, dashboard state, recovery status, or completion status.
- No hook replaces Operations Lead judgment.
- No Team Lead-specific scope hook is added unless concrete Phase 4/5 evidence
  shows the common guard is insufficient.

Decision output: implement MVP now, defer with trigger, or no-go with rationale.

Decision record:

- Decision: `ACCEPT_NARROW_MVP`.
- Implemented files:
  - `.codex/hooks.json`
  - `.codex/hooks/company_ops_gate.py`
- Implemented scope:
  - `PreToolUse` common red-line guard for `sudo npm`, `sudo openclaw`,
    `git reset --hard`, destructive user-change reverts, and obviously unsafe
    broad `rm -rf` targets.
  - `Stop` Work Unit artifact gate that no-ops without Work Unit context and
    blocks seeded missing-evidence completion cases.
  - `PreCompact` handoff guard that no-ops without Work Unit context and warns
    when handoff text would lose claim, evidence, decision, or next-action
    state.
- Evidence:
  - repo-local hook smoke fixtures were added to
    `python3 scripts/company_ops_smoke.py multi-team`;
  - dangerous-command fixtures are blocked;
  - normal repo inspection and existing smoke commands are allowed;
  - simple non-Work-Unit completion no-ops;
  - seeded missing-evidence completion is caught for numeric and suffix Work
    Unit ids;
  - seeded blocked/hold evidence is allowed.
- Boundary:
  - no `checkpoint-needed` user-facing feature;
  - no yieldable long-work runner;
  - no foreground monitor;
  - no automatic Discord publish;
  - no GitHub, Discord, claim, Work Card, evidence, decision, dashboard, or
    completion mutation.
- Rationale: this gives a cheap late safety layer for clear red lines and
  premature completion without adding a hidden orchestrator or making hooks an
  operating state owner.

### Phase 5.3: Dashboard Gate

Status: accepted as bounded GitHub Project auto-sync.

Purpose: give the owner an at-a-glance Company Dashboard while preserving
source artifacts as operating truth.

Decision:

- accept a GitHub Project as the v1 dashboard surface;
- keep Discord as event stream and Q&A visibility, not portfolio dashboard;
- keep `dashboard_snapshot.py` as local inspection support, not owner-facing
  dashboard replacement;
- implement Project sync as a deterministic mirror from source artifacts;
- use no LLM calls in the sync path.

Evaluate:

- whether GitHub auth can read Issues and write Project items/fields;
- whether Project id and field ids can be discovered or configured without
  storing secrets in the repo;
- whether status mapping from Work Cards and source artifacts is deterministic;
- whether `project-sync dry-run` can show planned changes without mutation;
- whether `project-sync apply` is idempotent and changed-only;
- whether lifecycle one-shot sync can run after source-backed state changes
  without making Work Unit completion depend on Project sync;
- whether scheduled reconcile can run every few minutes as stale-dashboard
  recovery with locking, logs, and failure alerts.

Accepted v1 shape:

- lifecycle one-shot sync is the primary update path for `ASSIGNED`,
  `STARTED`, `CHECKPOINT`, `RESULT_READY`, review, blocker, and closeout state
  changes;
- one-shot sync adds roughly 1-3 seconds only to state-changing lifecycle
  events;
- scheduled reconcile is a safety net, not the normal dashboard update path;
- default scheduled reconcile interval: 5 minutes as the stale-dashboard
  recovery window;
- allowed faster reconcile interval when owner wants tighter stale-recovery:
  2-3 minutes;
- the Project is a visibility mirror only.

No-go boundaries:

- no Project field may replace assignment, claim, evidence, or decision
  artifacts;
- no Project sync may close Issues, create evidence, create decisions, reassign
  Team Leads, recover agents, or publish semantic Discord progress;
- no long-lived daemon is required for v1;
- no hidden orchestrator, fallback truth, command router, or automatic
  completion may be introduced.

Implementation details are tracked in `docs/company-dashboard-timing.md`.

Current implementation state:

- `project-sync dry-run` computes desired Project fields from source artifacts
  and optional ledger state without mutation.
- `project-sync field-map` reads an existing GitHub Project and writes local
  field-id config without storing secrets. GitHub's built-in `Status` field is
  the canonical dashboard status field; source repository text maps to the
  editable `Source Repository` field because GitHub's built-in `Repository`
  field is read-only through Project item mutation APIs.
- `project-sync apply` requires an explicit local field map and `gh` auth with
  `project` scope, then adds missing Project item membership and updates changed
  fields only.
- `project-sync reconcile` runs the same changed-only apply path for existing
  dashboard items with locking for stale-dashboard recovery, skipping
  historical/local-only Work Units and absent Project items so archived history
  does not reappear.
- `discord publish-card` can run nonblocking one-shot sync after successful
  publish when a field map is supplied.
- The sync path does not close/open GitHub Issues, create source artifacts,
  mutate claims/evidence/decisions, or publish semantic Discord status.
- Primary dashboard view should emphasize `Title`, `Status`, `Priority`, `Team
  Lead`, evidence, decision, blocker, proof/update, Work Card, Work Unit id, and
  Source Repository. GitHub collaboration and source-reference fields should be
  hidden unless needed for an active Work Unit.
- Accepted Work Units are the owner's final-review queue. Keep accepted items
  visible until the owner has had a reasonable chance to inspect them or
  explicitly says they can be cleared. Then archive the Project item from the
  active dashboard and close the Work Card when the task is fully closed.
  Immediate archive is reserved for completed samples, internal smoke tests, or
  owner-approved cleanup. Archiving a Project item is safe because source
  artifacts remain the source of truth.

### Phase 5.4: Discord Publisher Hardening Gate

Purpose: decide whether the accepted foreground Discord publisher needs
additional hardening before packaging.

Phase 5.4 does not authorize a daemon, scheduler, Discord bridge, command
router, or hidden orchestration runtime. The accepted P0 shape is the
foreground `publish-card` command that sends one explicit, already-formatted
card at a time.

Evaluate:

- whether retry/idempotency behavior needs more hardening before public v1;
- whether proof logs need a stable artifact location convention;
- whether target route validation should be stricter;
- whether the current one-card foreground publisher is enough for v1.

Decision output: accept current P0 publisher as v1-ready, implement narrow
hardening, defer hardening with trigger, or no-go with rationale.

Publisher no-go boundaries:

- It may send explicitly targeted formatted messages only.
- It sends one card per invocation; it does not batch-generate a whole Work Unit
  timeline after completion.
- It must not read Discord messages as commands.
- It must not mutate source artifacts, Work Cards, claims, evidence, decisions,
  dashboard state, recovery status, or completion status.

### Phase 5.5: Result Ready Inbox / Closeout Lock Gate

Purpose: make more than one active Work Unit recoverable without relying on
chat arrival order, main-session memory, or manual transcript scanning.

Scope:

- Add a foreground/manual result-ready inbox command, for example
  `work-unit inbox --result-ready`, that lists Work Units ready for Operations
  Lead review from source artifacts, claim state, and proof/progress logs.
- Sort ready Work Units by the Operations Manual Result Ready Inbox Rule:
  earliest valid `RESULT_READY` proof timestamp, then claim `updated_at`, then
  Work Unit id.
- Add a WU-scoped closeout preparation path, for example
  `work-unit closeout --work-unit-id <id> --dry-run`, that takes a closeout lock,
  rereads assignment/evidence/claim/proof/progress/project dry-run state, and
  re-checks whether a decision artifact already exists before any write.
- Preserve the canonical routing labels: `ops-direct`, `team-qna`, and
  `detached-wu`.

Decision output: accept the foreground inbox and closeout-lock path as required
for multi-WU operation, implement a narrower version with rationale, or no-go
with the remaining race risk stated plainly.

No-go boundaries:

- This phase must not create a daemon, scheduler, or hidden background runner.
- It must not reorder OpenClaw inbound delivery. It only defines foreground
  source-backed recovery and review order.
- It must not automatically accept, reject, reopen, overwrite, reassign,
  complete, or report owner completion.
- It must not add LLM calls or network reads to list local ready Work Units.

Acceptance gate:

- Fixture with two ready Work Units is listed in deterministic order.
- Duplicate ready evidence for a Work Unit with an existing decision is reported
  as stale or blocked for manual review, not overwritten.
- A concurrent closeout attempt for the same Work Unit fails before mutation
  when the closeout lock already exists.
- Dry-run mode performs no external mutation and no owner-facing completion.

### Phase 5.6: Scheduled Pulse / Daemon Gate

Purpose: decide whether to install or schedule alert-only monitoring.

Evaluate:

- whether manual pulse checks reveal repeated stale-claim risk;
- whether alert noise and false positives are acceptable;
- whether a foreground/manual runner is enough for public v1.
- whether Phase 5.5's foreground result-ready inbox is enough before any
  scheduled monitoring.

Decision output: accept scheduled install, keep manual/foreground only, defer
with trigger, or no-go with rationale.

No-go boundaries:

- Pulse Monitor remains alert-only.
- No daemon restarts, reassigns, recovers, cancels, or completes work.
- Phase 5.5 result-ready inbox remains foreground/manual and source-backed.
  Scheduled pulse may alert that review is needed, but it must not run closeout
  or decisions.

### Phase 5.7: Packaging Readiness Decision

Purpose: lock the surface that is allowed to enter Phase 6.

Candidate Phase 6 surface:

- Work Unit artifact generator;
- Ops Claim Ledger CLI;
- alert-only pulse check and any accepted manual runner;
- accepted foreground result-ready inbox and closeout-lock helper;
- dashboard snapshot;
- Discord card composer, guard, JSON output, and sequence validator;
- smoke tests and setup docs;
- optional hook guard only if Phase 5.2 accepts it.

Decision output: a Phase 6 scope record that lists included surfaces, deferred
surfaces, and no-go surfaces.

Phase 5 acceptance gate:

- Each activation has an explicit yes/no decision with rationale.
- Final Company Ops completion requires GitHub Project or equivalent dashboard
  visibility unless the owner explicitly records a no-go decision with
  rationale.
- No activation introduces command routing, hidden truth, automatic recovery,
  automatic reassignment, or automatic completion.
- No hook activation mutates operating state or replaces source artifacts.
- Any external send or scheduled job has explicit owner approval before it is
  enabled.

## Phase 6: Packaging / Public v1

Purpose: make the validated operating surface reproducible.

Scope:

- Turn the repo-local entrypoint into the selected distribution shape.
- Keep command names aligned with the supported scripts.
- Replace manual setup-guide blocks only where supported commands exist.
- Include smoke tests and clear install/usage instructions.
- If hooks are retained, document install, disable, smoke-test, and
  troubleshooting instructions. Hooks remain optional guardrails around source
  artifacts, not required state storage.

Acceptance gate:

- A fresh user can initialize or run the validated flow without reading private
  local memory.
- Public docs do not mention private nicknames or internal-only state.
- Package behavior matches the artifacts-and-visibility model.
- Packaged hook behavior, if included, is reproducible and does not interfere
  with simple non-Work-Unit requests.

## Phase 7: Cross-Project Adoption

Purpose: apply the structure to real project work after it is proven.

Likely first candidate: `pq_platform`, because it already has real code,
incidents, runtime operations, and PR-based evidence.

Scope:

- Create project-local Work Cards in the repo where work belongs.
- Keep Company Ops as the operating model, not an umbrella source repo for
  product code.
- Reuse Discord visibility and dashboard rules only after their earlier gates
  pass.
- Apply hooks to product repos only as an explicit opt-in after project-local
  source artifacts, checks, and no-go boundaries are documented.

Acceptance gate:

- Cross-project Work Units remain auditable through source artifacts.
- Project repos keep their own code, tests, PRs, and release/apply policies.
- Company Ops gives visibility and coordination without replacing project
  ownership.
- Hook usage in project repos remains guardrail-only and can be audited against
  `docs/codex-hook-harness.md`.

## Cold Review

Current assessment after reordering:

- Missing visibility was the real gap. It is now placed before dogfood instead
  of being deferred to a later activation gate.
- The plan still preserves the original principles: Discord is a feed, not a
  truth source; dashboards are views, not state; Pulse Monitor alerts only.
- The revised order improves auditability because the owner can inspect
  orchestration events during dogfood instead of only receiving a final summary.
- The plan does not require Discord to decide work, accept commands, or replace
  source artifacts.
- The remaining risk is setup availability: channel ids, permissions, and send
  credentials must be verified before Phase 1 can be called complete.
- Hooks can reduce completion and safety drift later, but they should not be
  used to compensate for an unproven operating loop.

If all phases pass, the desired behavior is achievable: a Work Unit can be
assigned to a Team Lead, observed in Discord, discussed directly with the
appropriate Team Lead, tracked through a claim ledger, verified through
evidence, decided by the Operations Lead, and surfaced in a GitHub Project or
equivalent dashboard without creating hidden automation or fallback truth.
Hook guardrails, if accepted, make those existing source-artifact requirements
harder to skip; they do not replace any of them.
