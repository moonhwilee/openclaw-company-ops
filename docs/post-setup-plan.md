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
- A seeded valid blocked case is allowed.
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
  - seeded blocked evidence is allowed.
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

Status: accepted as bounded GitHub Project foreground sync.

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
- whether explicit foreground reconcile can repair stale-dashboard drift with
  locking, logs, and failure reports.

Accepted v1 shape:

- lifecycle one-shot sync is the primary update path for `ASSIGNED`,
  `STARTED`, `CHECKPOINT`, `RESULT_READY`, review, blocker, and closeout state
  changes;
- one-shot sync adds roughly 1-3 seconds only to state-changing lifecycle
  events;
- explicit foreground reconcile is a safety net, not the normal dashboard update
  path;
- public v1 does not install scheduled dashboard reconcile, cron, launchd,
  daemon, GitHub Actions schedule, or hidden Project mutation runner;
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

Status: accepted narrow hardening. P0 foreground publishing, proof validation,
sequence ordering, and card-shape guards exist. Public v1 keeps the foreground
publisher shape and adds only local pre-send guards.

Purpose: prevent duplicate or misrouted visibility cards before packaging
without adding workflow cost, hidden automation, or a second source of truth.

Phase 5.4 does not authorize a daemon, scheduler, Discord bridge, command
router, or hidden orchestration runtime. The accepted P0 shape is the
foreground `publish-card` command that sends one explicit, already-formatted
card at a time.

Accepted hardening:

- `publish-card` refuses a card that already has successful proof in the same
  proof log unless `--force` is explicit.
- `publish-card` can require an expected target and/or surface before sending.
- `publish-sequence` can require expected ops-feed and team-detail targets, so
  assignment/detail cards fail before send when routed to the wrong surface.
- `visibility-proof.jsonl` is the canonical Work Unit proof log name. This
  preserves the existing `work-unit` and `project-sync` source-artifact
  contract instead of introducing a second proof convention.

Deferred/no-go:

- Automatic retry loops are not added. Send/readback boundary failures remain
  explicit proof failures because blind retry can duplicate Discord messages.
- No background queue, hidden bridge, command reader, or recovery runner is
  introduced.

Publisher no-go boundaries:

- It may send explicitly targeted formatted messages only.
- It sends one card per invocation; it does not batch-generate a whole Work Unit
  timeline after completion.
- It must not read Discord messages as commands.
- It must not mutate source artifacts, Work Cards, claims, evidence, decisions,
  dashboard state, recovery status, or completion status.

### Distribution Surface Decision

Company Ops must not depend on installer-written user memory. A clean OpenClaw
install should not require modifying `MEMORY.md`, `AGENTS.md`, or any private
workspace bootstrap file to learn the routing rules. Those files can be useful
for one owner's development workspace, but they are not a distributable control
plane.

Installed target:

- The package installs into the user's OpenClaw runtime/workspace where the
  Operations Lead agent runs. In the default company model, that means the main
  agent acting as Operations Lead consumes the bundled skill and calls the
  packaged foreground CLI. It is not installed into the human user, and it must
  not treat private memory files as the control plane.
- In a multi-agent company model, the same packaged Company Ops skill,
  protocol docs, templates, and CLI should also be discoverable by Team Lead
  agents. This is shared capability, not shared authority: Team Leads need the
  references and source-backed commands to execute packet-first work reliably,
  but Operations Lead commands and decisions remain role-scoped.
- If Team Leads run in separate OpenClaw runtimes or workspaces, Phase 6
  packaging must either install/expose the same package to those runtimes or
  return a setup-needed checklist. Do not assume the Operations Lead can enforce
  the workflow by copying all rules through chat.
- The owner still uses natural-language requests. The packaged skill tells the
  Operations Lead when Company Ops applies and how to think about `ops-direct`,
  `team-qna`, and `detached-wu`; the packaged CLI provides the ticketing,
  inbox, lock, dashboard, and visibility tools needed for source-backed
  execution.

For distribution, use two explicit surfaces:

- OpenClaw skill: carries the short trigger/routing instructions that should be
  loaded when a user asks for Company Ops behavior. The skill should summarize
  `ops-direct`, `team-qna`, and `detached-wu`, point to the packaged docs, and
  tell the agent to call foreground commands for route/inbox/closeout decisions.
  It is good for context injection and safe defaults, but it should not own
  filesystem mutation, dashboard sync, Discord publish, or closeout state.
- OpenClaw plugin or package: carries the executable repo-local tools, CLI
  entrypoint, templates, smoke tests, and optional connector bindings. It is the
  right home for `route`, `work-unit inbox`, `work-unit closeout`,
  `project-sync`, and Discord publisher commands. It can be installed and
  versioned without editing user memory.

Cold packaging judgment:

- A skill alone is not enough. It can teach the agent the operating pattern, but
  it cannot reliably enforce source-backed state, locks, deterministic inbox
  ordering, or no-mutation dry-runs.
- A plugin/package alone is also not enough for natural-language use. It exposes
  commands, but the agent still needs a small instruction surface telling it
  when to use those commands and where authority boundaries are.
- The appropriate v1 distribution shape is therefore a Company Ops plugin or
  package that includes a small Company Ops skill plus foreground CLI tools. The
  installer may print an optional onboarding note, but it must not edit private
  memory automatically.

Deployment acceptance for this decision:

- A clean OpenClaw install can discover the Company Ops skill/plugin without
  writing user memory.
- Natural-language Company Ops requests load the skill instructions or otherwise
  direct the agent to the same packaged routing policy.
- Configured Team Lead agents can discover the shared Team Lead protocols,
  templates, and allowed source-backed commands without relying on Operations
  Lead chat memory.
- The foreground CLI remains the authority for deterministic route, inbox, and
  closeout checks.
- Operations Lead-only commands can fail closed without the required role
  context; Team Lead writes can be constrained to the assigned Work Unit.
- Uninstall removes package/plugin files without needing to clean private
  `MEMORY.md` edits.

Impact on existing docs and repository layout:

- Current repo-local scripts and docs are still valid as the development
  surface. Do not restructure the repository into an installable plugin package
  outside Phase 6 packaging work.
- There is not yet a published distribution target to install into. Phase 5.7
  recorded the package boundary and role-authority model; Phase 6 builds the
  actual plugin/package layout, shared skill/docs placement, CLI entrypoint,
  and any role-scoped command guards.
- Existing manual/setup docs should describe the accepted direction, not present
  skill, CLI, plugin, or setup script as equally open public-v1 choices.
- Phase 5.7 produced the concrete packaging layout decision: plugin/package
  direction, bundled small skill, packaged foreground CLI entrypoint, included
  templates/docs, smoke/setup docs, optional uninstall behavior, and explicit
  proof boundary that install/uninstall must not edit user memory.
- Phase 6 is the right time to move or copy files into the package layout. Until
  then, keep implementation in the existing repo-local `scripts/`, `docs/`,
  `.codex/`, and template paths until Phase 6 begins the package layout work.

### Phase 5.5: Result Ready Inbox / Closeout Lock Gate

Status: accepted and implemented as a foreground, dry-run-first safety gate.

Purpose: make more than one active Work Unit recoverable without relying on
chat arrival order, main-session memory, or manual transcript scanning.

Scope:

- Added a foreground/manual result-ready inbox command,
  `work-unit inbox --result-ready`, that lists Work Units ready for Operations
  Lead review from source artifacts, claim state, and proof/progress logs.
- Added an official foreground result-ready publication command,
  `work-unit result-ready --dry-run/--publish`, that wraps the existing shared
  Result Ready gate and Discord `RESULT_READY` publish/readback path.
- The result-ready command deliberately splits pre-publish and post-publish
  checks: source/evidence must pass before send, live `RESULT_READY` proof is
  required only after the publish/readback step.
- The command supports text and JSON output. JSON output includes at
  least `work_unit_id`, `title`, `team`, `claim_state`, `result_ready_at`,
  `result_ready_source`, `evidence_path`, `decision_path`, `decision_exists`,
  `proof_path`, `project_dry_run_supported`, `stale_reason`, and `sort_key`.
- Sort ready Work Units by the Operations Manual Result Ready Inbox Rule:
  earliest valid `RESULT_READY` proof timestamp, then claim `updated_at`, then
  Work Unit id.
- Source scanning should be local-first: Work Unit artifact directories, claim
  state, evidence/result records, decisions, and proof/progress logs. It must
  not read Discord history, GitHub Project fields, GitHub comments, or chat
  transcripts to discover result readiness.
- The implemented inbox scans only the configured artifact root:
  `<artifact-root>/<WU>/assignment.md`, `claim.md`, `evidence.md`,
  `decision.md`, `progress.jsonl`, and `visibility-proof.jsonl`. GitHub Project
  status, Discord/Telegram history, GitHub comments, and OpenClaw session
  history may be reported as mirror context only after a Work Unit is already
  discovered from source artifacts.
- Include `--artifact-root`, `--work-unit-id`, `--team`, `--limit`, and
  `--format text|json` options. The default should scan the configured artifact
  root and show actionable ready items only.
- Added a WU-scoped closeout path,
  `work-unit closeout --work-unit-id <id> --dry-run/--publish`, that takes a
  closeout lock, rereads assignment/evidence/claim/proof/progress source state,
  and supports explicit Operations Lead decisions: `accept`, `revise`, or
  `blocked`.
- `--dry-run` plans the final review/owner closeout cards without mutating
  `decision.md`, Discord, Project, or owner completion state. `--publish`
  records `decision.md`, publishes exactly one team final review followed by
  exactly one owner closeout, then optionally syncs the Project mirror.
- The closeout lock should be a local source-adjacent lock file or atomic lock
  directory keyed by Work Unit id. Lock acquisition must happen before any
  decision write, Project mutation, Discord publish, or owner-facing report.
- The lock is a short-lived command guard, not a durable workflow state. The
  first implementation should fail clearly when a lock already exists, include
  the lock path in the error, and avoid adding force-unlock behavior until a
  separate stale-lock policy is accepted.
- `accept` and `revise` require a source-backed `result_ready` submission.
  `blocked` does not require `result_ready`; it requires blocker source,
  reason, needed action, and next owner.
- If a decision already exists, closeout preparation must exit as stale or
  already-decided and must not overwrite, reopen, or append a competing
  decision.
- If proof or source artifacts contain multiple competing final reviews for the
  same Work Unit, or duplicate result-ready evidence with different source
  timestamps, the inbox/closeout output must mark the item `needs-ops-decision`
  or `conflict` instead of choosing a winner.
- Preserve the canonical routing labels: `ops-direct`, `team-qna`, and
  `detached-wu`.
- Defer route-helper implementation from the first Phase 5.5 patch. A later
  foreground route helper, for example `route --intent <text>`, can be accepted
  only if it remains deterministic, conservative, and able to return
  `needs-ops-decision` rather than guessing or calling an LLM.

Decision output: foreground inbox, official result-ready publish, and explicit
closeout decision commands are accepted for multi-WU operation. Route helper and
stale-lock recovery remain separate decisions.

No-go boundaries:

- This phase must not create a daemon, scheduler, or hidden background runner.
- It must not reorder OpenClaw inbound delivery. It only defines foreground
  source-backed recovery and review order.
- It must not automatically accept, reject, reopen, overwrite, reassign,
  complete, or report owner completion.
- It must not add LLM calls or network reads to list local ready Work Units.
- It must not turn Discord, GitHub Project, GitHub comments, Telegram messages,
  or OpenClaw session history into a source of truth.
- It must not silently modify user memory, install a cron, or run as a
  background service.

Acceptance gate:

- Fixture with two ready Work Units is listed in deterministic order.
- Duplicate ready evidence for a Work Unit with an existing decision is reported
  as stale or blocked for manual review, not overwritten.
- A concurrent closeout attempt for the same Work Unit fails before mutation
  when the closeout lock already exists.
- Dry-run mode performs no external mutation and no owner-facing completion.
- JSON output is stable enough for an agent to consume without reading raw
  artifact files into the main context.
- Missing or malformed proof rows are surfaced as warnings without inventing a
  fallback result-ready state.
- Conflicting final reviews or duplicate ready evidence are reported as
  `needs-ops-decision` or `conflict`, not auto-resolved.
- Route helper remains deferred from the first Phase 5.5 implementation; if it
  is later accepted, it returns one of `ops-direct`, `team-qna`, `detached-wu`,
  or `needs-ops-decision` and explains the decision with a short deterministic
  reason.

### Phase 5.5a: Handoff Amendment / Replan Dry-Run Gate

Purpose: make post-handoff plan changes source-backed without slowing normal
Work Units or making the Assignment Packet too rigid.

This phase is implemented after Phase 5.5's result-ready inbox and closeout
lock path. It is not a replacement for the original handoff; it is a small
foreground helper for the cases where execution discovers new facts.

Implemented:

- Added a foreground `work-unit amend --spec amendment.json --dry-run` helper.
- The implementation plans a source-backed amendment when execution
  discovers a new issue that changes scope, done criteria, verification
  criteria, risk, cost, authority, or target artifact paths. It does not record
  or apply the amendment.
- The dry-run spec must be explicit local input, not inferred from chat or
  mirrors. Required fields: `work_unit_id`, `reason`, `changed_fields`,
  `proposed_updates`, `source_refs`, and `requested_by`.
- Missing or ambiguous judgment fields must remain `needs-ops-decision`; the
  helper must not invent scope, authority, cost, or route decisions.
- `--dry-run` is mandatory and must show the
  planned amendment, affected fields, unchanged handoff facts, source refs, and
  optional visibility/Project mirror plan without writing files or mutating
  external systems.
- A later non-dry-run path requires a separate acceptance decision. It may then
  append an amendment/revision note, update `Updated at`, optionally publish one
  factual CHECKPOINT or REVISE visibility note, and run Project sync as a
  mirror.

Stable facts that must not be rewritten:

- Work Unit id.
- Work Card.
- Original owner request and business intent.
- Assigned Team Lead and Operations Lead.
- Protocol mode, safety constraints, and no-go boundaries.
- Original handoff timestamp and proof trail.

No-go boundaries:

- Do not overwrite the original Assignment Packet as if the earlier handoff
  never existed.
- Do not automatically accept, reject, close, reopen, reassign, complete, or
  report owner completion.
- Do not use Discord, GitHub Project, comments, Telegram, or OpenClaw session
  history as the source of the amendment.
- Do not add LLM calls, network reads, daemon behavior, schedulers, retries, or
  hidden runners.
- Do not require this helper for small findings that stay inside the existing
  scope. Those should remain normal progress/checkpoint evidence.

Acceptance gate:

- Dry-run has no file writes, Discord sends, GitHub mutations, owner-facing
  reports, or LLM calls.
- The helper preserves a pointer to the original Assignment Packet and proof
  trail.
- The planned amendment names the changed fields, reason for change, source
  refs, unchanged stable facts, and any `needs-ops-decision` fields.
- Existing scope-contained findings are documented as progress/checkpoint
  examples, not forced into amendment.
- A smoke fixture proves the original handoff is not overwritten, no amendment
  artifact is written, and the output reports the planned artifact/action for a
  later explicit acceptance path.

Cost/risk judgment:

- Normal Work Units pay no runtime cost because the helper runs only when a
  meaningful plan change is requested.
- The first implementation should be local-file-first and deterministic, so
  dry-run should be near-instant and add no network, LLM, daemon, or scheduler
  cost.
- The main over-tightening risk is using amendments for every small discovery.
  Keep the threshold limited to scope, criteria, risk, cost, authority, or
  target-artifact changes.

### Phase 5.5b: Handoff Draft / Spec Generator Gate

Purpose: reduce repeated Work Card / Assignment Packet / handoff spec assembly
after Operations Lead judgment is already complete.

This is an implemented bounded phase after Phase 5.5 and Phase 5.5a. It is not
a routing engine, automatic assignment engine, or substitute for
LLM/Operations Lead judgment. Its value is consistency and reduced repetitive
formatting, not faster Discord/GitHub validation.

The helper must not replace Operations Lead judgment.

Implementation scope:

- Implemented only the foreground dry-run command
  `work-unit draft-handoff --spec draft-input.json --dry-run`.
- The draft input must be a structured local spec, not a free-form owner chat
  request. Required first-version fields: `requested_by`, `source_refs`, and
  at least one request summary field such as `title` or `owner_request`.
- Optional Operations Lead-supplied fields include `work_unit_id`, `mode`,
  `team`, `scope`, `done_criteria`, `verification_criteria`, `no_go`,
  `target_paths`, `work_card`, and `targets`.
- The helper may produce a Work Card draft, Assignment Packet draft, handoff
  spec draft, missing-field list, and no-go/ordering checklist.
- The helper must make all generated output review-only until Operations Lead
  explicitly converts it into a real handoff.
- The first implementation must be dry-run only: no Work Card creation, no
  source artifact write, no Discord publish, no GitHub Project mutation, no
  owner-facing completion report.
- The helper must accept only Operations Lead-supplied judgment facts. Missing
  `mode`, `team`, `scope`, `done_criteria`, `verification_criteria`,
  `target_paths`, or `targets` are surfaced in `missing_fields` and represented
  as `needs-ops-decision`; the helper must not invent or infer them.
- The draft handoff spec must stay aligned with the existing
  `work-unit handoff` contract. Avoid a second independent handoff template path
  when the existing spec validation or artifact renderer can be reused.

Current insight:

- `work-unit handoff` already makes the publish/readback planning step short
  and ordered. Controlled dry-run probes showed validation itself is not the
  bottleneck.
- The remaining opportunity is before handoff validation: turning already-made
  Operations Lead decisions into consistent Work Card, Assignment Packet, and
  spec scaffolding.
- A draft helper must preserve the existing quality bar by leaving scope,
  Team Lead, risk, no-go, done criteria, and verification criteria under
  Operations Lead control.
- The implementation goal is not to eliminate thinking time. It is to reduce
  repeated packet/spec assembly without adding LLM/token/network cost or normal
  Work Unit runtime overhead.

No-go boundaries:

- No automatic Team Lead selection.
- No automatic route decision from owner text.
- No free-form request parsing that turns owner text into mode, team, scope,
  criteria, or targets.
- No automatic Work Card creation, Discord publish, GitHub Project mutation, or
  source artifact write from the draft command.
- No additional LLM calls, token use, network reads, daemon, scheduler,
  background queue, retry loop, or hidden orchestrator.
- No confidence scores or authoritative-looking claims that could make a draft
  appear reviewed.
- No guessing for ambiguous fields. Mark them as `needs-ops-decision`.
- No source of truth outside Work Card, Assignment Packet, source artifacts,
  and explicit Operations Lead decisions.

Acceptance gate:

- Dry-run creates no persistent Work Unit artifacts and performs no external
  mutation.
- Draft output includes Work Card, Assignment Packet, handoff spec, missing
  fields, and no-go/order checklist sections.
- Ambiguous or missing judgment fields are surfaced as `needs-ops-decision`.
- The raw draft spec is not required to pass handoff validation while judgment
  fields are missing. A completed draft spec, after Operations Lead fills the
  required values, can be passed to `work-unit handoff --dry-run`.
- Smoke coverage proves the helper does not publish, create Work Cards, mutate
  Project state, call an LLM, parse free-form request text into routing
  decisions, or choose a Team Lead by itself.
- The helper is documented as an Operations Lead drafting tool, not as a source
  of truth or an autonomous work router.

Preliminary dry-run probe:

- The owner-approved probe used six controlled Company Ops requests:
  verify/light, verify/medium, verify/long, goal/light, goal/medium, and
  goal/long.
- On 2026-06-07, Operations Lead ran six controlled dry-run-only requests in two
  waves of three parallel handoff validations: verify/light, verify/medium,
  verify/long, goal/light, goal/medium, and goal/long.
- The first attempt intentionally surfaced a real guardrail: test Work Unit ids
  that did not match `WU-YYMMDD-NNN` were rejected before any artifact write or
  external mutation.
- The corrected run used valid local-study Work Unit ids and passed all six
  dry-runs with no persistent handoff artifact writes, no Discord sends, no
  GitHub Project mutation, no Work Card creation, no Team Lead agent spawn, and
  no LLM calls.
- Observed local dry-run validation time was about 160-177ms per Work Unit when
  three requests were validated concurrently; wave spans were about 161ms and
  178ms.
- This proves that the existing deterministic handoff validation surface is not
  the bottleneck and can tolerate small parallel dry-run bursts.
- It does not prove that live Operations Lead thinking time has been optimized,
  because the probe measured scripted packet assembly and CLI validation, not
  real LLM judgment, ambiguity handling, or live Discord/GitHub readback.

Updated interpretation: if later Work Units still show multi-minute pre-handoff
delay, the likely opportunity is not faster validation. It is reducing repeated
manual packet/spec assembly while keeping Operations Lead judgment in control.

### Phase 5.6: Scheduled Pulse / Daemon Gate

Decision: defer scheduled Pulse activation with trigger. Manual/foreground
Pulse checks are accepted; scheduled Pulse is not a required public-v1 surface
today.

Purpose: decide whether alert-only stalled-work detection should ever interrupt
the owner automatically.

Current user-facing judgment:

- The current surfaces are not duplicate alerts. They have separate roles:
  - GitHub Project Dashboard: status board for pull-based inspection.
  - Discord visibility/proof: event trail and readback proof.
  - `work-unit inbox --result-ready`: foreground review queue for submitted
    results.
  - Pulse Monitor: stalled-work detector for claims that go quiet before a
    result exists.
- The current system is close to "required visibility only"; alert noise is not
  currently high.
- The risk is future interrupt noise if scheduled Pulse alerts run alongside
  result-ready review signals without suppression.

Optimization principle:

- Do not merge role-distinct surfaces into one tool just to reduce apparent
  overlap.
- Keep dashboards, proof trails, review inboxes, and stalled-work detection
  separate.
- Consolidate only the interrupting alert policy: what is allowed to wake the
  owner, when it is suppressed, and which channel may receive it.

Evaluate:

- whether manual pulse checks reveal repeated stale-claim risk;
- whether scheduled Pulse would add actionable signal beyond existing
  Dashboard, Discord proof, and result-ready inbox surfaces;
- whether a foreground/manual runner is enough for public v1.
- whether Phase 5.5's foreground result-ready inbox is enough before any
  scheduled monitoring.

Accepted now:

- Manual `pulse check`.
- Foreground bounded runner for smoke/debug only.

Deferred unless trigger:

- Any cron/scheduled Pulse install.
- Any long-running daemon/launchd install.
- Any automatic `#ops-alerts` Pulse publish.

Trigger to revisit scheduled Pulse:

- two or more meaningful real Work Units show stale-claim, session-mismatch, or
  compaction-suspect conditions that were not caught soon enough by manual
  review and the result-ready inbox; or
- the owner explicitly accepts unattended monitoring for long-running Work
  Units.

If scheduled Pulse is later accepted:

- Prefer one-shot scheduled `pulse check` over a long-running daemon.
- Keep `pulse_daemon.py daemon run` as a foreground smoke/debug runner unless a
  separate gate accepts installation.
- Suppress Pulse alerts for Work Units that are already result-ready, accepted,
  revise-requested, blocked, or otherwise decided by source artifacts.
- Do not publish automatic `#ops-alerts` messages without a separate delivery
  gate and proof/readback check.

Decision output: manual/foreground accepted, scheduled activation deferred with
trigger, daemon install no-go for now.

No-go boundaries:

- Pulse Monitor remains alert-only.
- No daemon restarts, reassigns, recovers, cancels, or completes work.
- Phase 5.5 result-ready inbox remains foreground/manual and source-backed.
  Scheduled Pulse must not compete with it, run closeout, or make decisions.

### Phase 5.7: Packaging Readiness Decision

Purpose: lock the surface that is allowed to enter Phase 6.

Accepted Phase 6 surface:

- small Company Ops skill with routing triggers, authority boundaries, and
  foreground-command instructions;
- Work Unit artifact generator;
- Ops Claim Ledger CLI;
- implemented alert-only `pulse check` for manual/foreground stalled-work
  inspection;
- accepted foreground result-ready inbox/result-ready publish/closeout decision
  helper, including the closeout-lock helper;
- accepted foreground handoff amendment/replan helper;
- accepted dry-run handoff draft/spec generator helper;
- dashboard snapshot;
- Discord card composer, guard, JSON output, and sequence validator;
- smoke tests and setup docs;
- optional hook guard as a guardrail only, because Phase 5.2 accepted it
  narrowly.

Phase 6 included surfaces are limited to:

- small Company Ops skill plus foreground CLI entrypoint, installed as shared
  Company Ops capability for Operations Lead and Team Lead agents in the same
  runtime;
- packaged protocol docs and templates that Team Leads can reference while
  executing assigned Work Units;
- source-backed Work Unit, claim, inbox, closeout dry-run, amendment dry-run,
  draft-handoff dry-run, and `pulse check` commands;
- GitHub Project dashboard dry-run/apply tooling only as a configured
  foreground mirror that requires an explicit local field map and `gh` auth
  with `project` scope before mutation;
- Discord card/publish/proof tooling only as configured foreground
  visibility/proof commands with explicit targets, readback proof, and no
  bridge or queue;
- smoke tests, templates, package docs, and optional hook install/disable/smoke
  instructions.

Packaged Pulse operation:

- Public v1 should expose `openclaw-company-ops pulse check` as a normal
  foreground CLI command.
- The default ledger path should remain the user's local Company Ops claim
  ledger under their OpenClaw state directory.
- Session/compaction checks may use an explicit local session snapshot, but the
  command must still work without one for claim freshness checks.
- The small Company Ops skill may tell the Operations Lead when to run
  `pulse check`, for example after a long Work Unit goes quiet, before owner
  status reporting on unattended work, or after compaction recovery.
- Installation must not enable Pulse cron, launchd, daemon, or automatic
  `#ops-alerts` publishing. Those remain deferred surfaces.

Shared access and role authority:

- The distribution should expose Company Ops skill/protocol/docs/CLI to both
  Operations Lead and Team Lead agents so Team Leads can re-check packet-first
  rules, verification expectations, claim/evidence formats, and no-go
  boundaries during execution.
- The Operations Lead owns `pulse check`, result-ready inbox review, closeout
  decisions, configured Project/Discord mutation, and owner-facing completion.
- Team Leads may use shared tools only for the Work Unit they were assigned:
  claim refresh, progress/evidence/result writing, local verification, and
  blocker reporting.
- Phase 6 should implement role-scoped CLI guards as command/protocol-level
  fail-closed checks. This is not OS-level isolation; it is the public-v1
  safety boundary that prevents shared package access from becoming shared
  authority.
- Role context should be resolved deterministically from explicit command
  input first, then environment, then local config. Missing or conflicting
  role context must fail closed before mutation instead of guessing.
- Operations Lead-only commands must require an Operations Lead role context:
  `pulse check`, result-ready inbox review, closeout decisions, Project
  apply/reconcile, Discord publish, and owner-facing completion.
- Team Lead-scoped write commands must require a Team Lead role context plus
  the active assigned Work Unit id, and must reject writes outside that Work
  Unit. Read-only help, docs, status inspection, and smoke commands may remain
  role-neutral when they do not mutate operating state.
- These guards should be part of the packaged CLI/setup contract, not just
  prose in the skill. The skill tells agents when to call commands; the CLI
  should still reject unauthorized or out-of-scope mutations when it can.
- This is command/protocol-level authority, not a claim that the operating
  system has per-agent security isolation. Any harder isolation depends on the
  OpenClaw runtime's agent identity, workspace, and tool-exposure features.

Phase 6 deferred surfaces remain:

- scheduled Pulse/cron activation;
- scheduled dashboard reconcile, cron, launchd, daemon, GitHub Actions schedule,
  or hidden Project mutation runner;
- `pulse_daemon.py daemon run` as anything more than a bounded foreground
  smoke/debug diagnostic;
- route helper `route --intent`;
- amendment apply/record commands;
- closeout expansion beyond the accepted foreground `work-unit closeout
  --dry-run/--publish` lock gate, including automatic closeout;
- automatic `#ops-alerts` publishing;
- broader Discord retry, queue, or bridge behavior.

Phase 6 no-go surfaces remain:

- installer edits to private user `MEMORY.md`, `AGENTS.md`, or bootstrap files;
- Discord, GitHub Project, Telegram, or session history as source of truth;
- automatic restart, reassignment, recovery, cancellation, or completion;
- hidden orchestrator, command router, protocol runtime, or classifier.

Permission and failure boundary:

- Project live mutation is allowed only after `project-sync field-map` has
  produced an apply-ready local field map and `gh auth` includes the `project`
  scope. Missing field map, missing field ids, invalid Work Card URLs, missing
  auth, or missing scope must fail before mutation.
- Discord live mutation is allowed only through explicit foreground
  `discord publish-card`/`publish-sequence` commands with an explicit target
  and proof log. Target/surface mismatches must fail before send; send/readback
  failure records incomplete proof and does not mutate source artifacts.
- Optional hooks must protect source-artifact structure only. They must not be
  required runtime state, publish messages, run Project sync, or make Work Unit
  decisions.

Setup/preflight decision:

- Phase 6 includes setup documentation and should include a foreground
  read-only `doctor` / `preflight` helper. The helper exists to make initial
  setup and later configuration drift obvious; it is not an auto-repair
  workflow.
- The helper should check package/CLI availability, source artifact and
  template paths, local config readability, role-context config, Project
  field-map readiness, GitHub Project scope, Discord target configuration,
  proof-log path writability, claim ledger readability, foreground
  `pulse check` viability, stale Project mirror hygiene, and Work Card body
  rendering problems such as literal escaped newlines.
- The helper should report `OK`, `WARN`, or `BLOCKED` with exact next steps,
  and should support both human-readable output and machine-readable JSON.
- The helper must not grant OAuth scopes, create Projects, create Discord
  channels, choose targets, bind agents, publish cards, archive Project items,
  start scheduled jobs, or mutate source artifacts.
- Missing Project/Discord setup is not a reason to silently degrade into a
  fallback source of truth. It should disable only that external mirror/proof
  action while keeping source-backed Work Unit commands usable.

Phase 6 implementation decisions to keep narrow:

- Distribution shape: build one package/plugin surface with a bundled small
  Company Ops skill plus foreground CLI. Do not split into a standalone skill
  without the deterministic CLI, and do not leave repo-local scripts as a
  parallel legacy path after packaging.
- Command naming: expose a user-facing `doctor` command and allow `preflight`
  as an alias or internal action. The command should be read-only unless a
  separate explicit mutation command is added later.
- Config location: keep local package config under the user's Company Ops
  state root, for example `~/.openclaw/state/openclaw-company-ops/`. Config may
  name field-map paths, Discord targets, proof-log paths, and role context, but
  it is not Work Unit source truth.
- Guided team setup: keep dry-run planning in v1. This is an onboarding
  blueprint/checklist for users who start with one OpenClaw agent and need to
  see the recommended Operations Lead, Team Lead, GitHub Project, Discord
  target, role config, and missing-setup steps before anything is created. Any
  agent creation, binding, credential, Discord, Project, cron, or
  external-resource change requires a separate explicit foreground
  confirmation.
- Dashboard hygiene: `doctor` may report stale mirror items and literal body
  rendering problems. Automatic archive remains out of scope; any archive path
  must be an explicit foreground cleanup command. Public v1 uses explicit
  foreground `project-sync reconcile` for stale mirror recovery; scheduled
  dashboard reconcile remains deferred.

Decision output: accepted. Phase 5.7 locks the Phase 6 included surfaces,
deferred surfaces, and no-go surfaces listed above.

### Phase 5.8: Live Workflow Stabilization Gate

Purpose: resolve the live workflow lifecycle issues found in
`WU-260608-001` through `WU-260608-004`, plus the distribution-critical
verify/fix boundary and dashboard convergence issues exposed by the 5.8.6 live
gate, before Phase 6 packaging begins.

Implementation reference: `docs/phase-5.8-stabilization-gate.md`.

Scope:

- Record the live workflow issue register and phase order.
- Separate lifecycle state from responsibility state before changing status
  behavior.
- Add a canonical `STARTED` transition and result-ready guard.
- Make closeout finalization update lifecycle/status consistently.
- Preserve or rehydrate Work Card links in Operations Lead decisions.
- Define and implement the minimum detached dispatch behavior required for
  Operations Lead handoff without blocking on Team Lead execution.
- Add result-ready closeout delegate wake, guarded commit-request closeout, and
  explicit partial-publish resume behavior.
- Add a no-bypass regression gate for live workflow tests.
- Add a 5.8.7 public-install gate for structured Assignment Packet mutation
  authority, verify-only read-only boundaries, explicit Project sync
  required/disabled state, final GitHub Project desired-vs-live readback,
  narrow command/protocol guards, minimal setup preflight, and a small live
  verify fast-path policy.

Acceptance gate:

- Phase 5.8 P0 items are resolved in repo-local code.
- A small live workflow regression batch passes without manual lifecycle proof
  insertion.
- Status output and decision artifacts agree after closeout.
- Final decisions retain Work Card references when source artifacts contain
  them.
- The tested detached path does not require the Operations Lead to hold the
  Team Lead foreground execution.
- Result-ready delegate wake and guarded closeout commit request are exercised,
  including fail-closed and partial-resume edge cases introduced by 5.8.4c.
- Verify-only work cannot mutate Company Ops-owned product/source code or final
  external state; defects found during verify become revise/blocked/findings
  unless a separate owner-approved goal/hardening slice grants structured
  mutation authority.
- Final Company Ops completion with required Project visibility requires live
  dashboard readback, not only local stage flags, omitted field-map arguments,
  or Discord proof.
- Public-install preflight can detect missing Project/Discord/auth/adapter/role
  readiness without creating or mutating resources.
- Any remaining P1/P2 items have explicit owner-approved defer rationale.

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

Precondition: Phase 5.7 package boundary and Phase 5.8 live workflow
stabilization gate are both satisfied.

Scope:

- Turn the repo-local entrypoint into the selected plugin/package distribution
  shape with a bundled small Company Ops skill and foreground CLI tools.
- Expose the bundled skill, protocol docs, templates, and allowed CLI commands
  to configured Team Lead agents as shared capability, while keeping
  Operations Lead-only commands role-scoped.
- Keep command names aligned with the supported scripts.
- Replace manual setup-guide blocks only where supported commands exist.
- Include smoke tests and clear install/usage instructions.
- Include a foreground read-only `doctor` / `preflight` helper with text and
  JSON output.
- Include command/protocol-level role guards for Operations Lead-only commands
  and Team Lead Work Unit-scoped writes.
- Include explicit install and uninstall behavior. Installation must not write
  private `MEMORY.md`, `AGENTS.md`, or other user bootstrap files.
- Offer an optional guided team setup path for users who start with a single
  OpenClaw agent. The guided setup may propose a default company topology
  such as Operations Lead plus build, product, market, and revenue Team Leads,
  generate a dry-run plan, and then apply only the user-approved local
  configuration/artifacts.
- Guided team setup must not auto-create or bind agents, credentials, Discord
  channels, GitHub Projects, scheduled jobs, or external resources without an
  explicit foreground confirmation. When the runtime cannot create Team Lead
  agents programmatically, it should leave a clear manual setup checklist and
  keep the single-agent mode usable.
- Single-agent mode remains valid after install: `ops-direct` works
  immediately, while `team-qna` and `detached-wu` either route to configured
  Team Leads or return a setup-needed result with next steps.
- If hooks are retained, document install, disable, smoke-test, and
  troubleshooting instructions. Hooks remain optional guardrails around source
  artifacts, not required state storage.

Acceptance gate:

- A fresh user can initialize or run the validated flow without reading private
  local memory.
- A fresh single-agent user can run guided setup, inspect the proposed team
  topology, confirm or decline it, and receive clear next steps without knowing
  OpenClaw agent harness internals.
- The guided setup dry run explains what would be configured and what is
  missing, but it does not create agents, channels, Projects, credentials,
  cron jobs, or external resources.
- `doctor` / `preflight` reports missing Project, Discord, role-context,
  proof-log, dashboard-hygiene, and Work Card rendering setup without mutating
  source artifacts or external surfaces.
- Role-guard smoke proves Operations Lead-only mutation commands fail closed
  without Operations Lead context, and Team Lead write commands fail outside
  the assigned Work Unit id.
- Guided setup has a dry-run mode and leaves source-backed configuration or
  setup artifacts, not private memory edits.
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
