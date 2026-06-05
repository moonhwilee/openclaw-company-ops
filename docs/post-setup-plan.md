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

## Phase 1: Pre-Dogfood Visibility Setup

Purpose: make orchestration observable before asking whether it works.

Set up the smallest Discord visibility path that lets the owner watch Work Unit
state changes and alerts without relying only on Operations Lead summaries.

Scope:

- Select or create the visibility channels:
  - `#ops-feed` for assignment, started, blocked, result-ready, and decision
    events.
  - `#ops-alerts` for stale claim, session mismatch, and suspected compaction
    recovery alerts.
- Select or create the direct team channels:
  - `#team-build-pq` for PrimeQuant platform engineering questions.
  - `#team-build-lab` for new product and tooling questions.
  - `#team-market` for market, positioning, and content questions.
  - `#team-revenue` for customer, proposal, payment, and delivery questions.
- Bind direct team channels deliberately:
  - only the matching Team Lead should answer by default;
  - `#ops-feed` should remain event-focused, not a general discussion channel;
  - if no agent is bound to a channel, no response should be assumed;
  - if multiple agents are bound to one channel, the routing is invalid until
    the noisy overlap is removed.
- Decide the first send mechanism:
  - manual posting from formatter output, or
  - a one-off approved send using an existing messaging surface.
- Emit and verify at least one harmless test event that links to a real source
  artifact.
- Ask at least one harmless direct question in a team channel and verify that
  the matching Team Lead can answer without mutating official operating state.
- Confirm that no Discord message can mutate GitHub, mutate the claim ledger,
  close work, approve completion, reassign work, or recover agents.

Acceptance gate:

- Owner can open the Discord channel and see an event with Work Unit id, source
  artifact link, owner/next-action owner, and next action.
- Owner can directly ask a Team Lead a status or clarification question in the
  correct team channel and receive an answer from that Team Lead.
- The same event is traceable back to the Work Card, Assignment Packet, claim,
  evidence, or decision artifact.
- Direct Team Lead answers can link or explain source artifacts, but they do
  not create, close, reassign, approve, or mutate Work Units by themselves.
- Discord remains visibility-only plus direct human/agent Q&A. It is not an
  operating-state authority.

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
- Emit Discord visibility events for the major transitions.

Acceptance gate:

- A person can audit the Work Unit without trusting a chat summary.
- Discord events point to the source artifacts.
- Evidence maps back to done criteria and verification criteria.
- Only an Operations Lead `accept` decision can close the Work Card.

## Phase 3: Dogfood Friction Patch

Purpose: patch the first real operational pain before scaling.

Scope:

- Fix confusing CLI arguments, missing output, brittle artifact paths, stale
  docs, awkward Discord message format, or claim/evidence gaps found in Phase 2.
- Keep fixes narrow and repo-local unless a broader package boundary is clearly
  justified.
- Preserve all no-fallback and visibility-only rules.

Acceptance gate:

- The specific friction observed in Phase 2 is removed or documented as an
  explicit limitation.
- Existing setup smokes still pass.
- The owner can still audit the Work Unit trail through artifacts plus
  visibility events.

## Phase 4: First Real Team Delegation

Purpose: prove the team-lead model, not just the Operations Lead loop.

Scope:

- Choose the correct standing role agent for one real assignment:
  `build-pq`, `build-lab`, `market`, or `revenue`.
- Give that agent an Assignment Packet, not a vague instruction.
- Require claim refreshes and evidence output from the Team Lead.
- Let the Team Lead use subagents directly if useful.
- Keep Operations Lead review and decision separate from Team Lead execution.
- Emit Discord visibility events for owner observability.

Acceptance gate:

- The Team Lead can execute without hidden Operations Lead intervention.
- Subagent output is treated as input, not completion truth.
- Evidence and decision are sufficient for an independent audit.
- Discord visibility shows what happened without becoming the operating record.

## Phase 5: Activation Decision Gates

Purpose: decide which optional automation is ready to activate.

Evaluate each gate independently:

- Discord publisher: enable only if Phase 1-4 event volume proves manual or
  one-off posting is too slow or too hidden.
- GitHub Project sync: enable only if there are enough Work Cards or repos to
  make a dashboard useful.
- Scheduled Pulse Monitor: enable only if manual pulse checks reveal real stale
  claim risk.
- Packaging/public v1: enable only if the repo-local commands are stable enough
  for another user or agent to reproduce.

Acceptance gate:

- Each activation has an explicit yes/no decision with rationale.
- Final Company Ops completion requires GitHub Project or equivalent dashboard
  visibility unless the owner explicitly records a no-go decision with
  rationale.
- No activation introduces command routing, hidden truth, automatic recovery,
  automatic reassignment, or automatic completion.
- Any external send or scheduled job has explicit owner approval before it is
  enabled.

## Phase 6: Packaging / Public v1

Purpose: make the validated operating surface reproducible.

Scope:

- Turn the repo-local entrypoint into the selected distribution shape.
- Keep command names aligned with the supported scripts.
- Replace manual setup-guide blocks only where supported commands exist.
- Include smoke tests and clear install/usage instructions.

Acceptance gate:

- A fresh user can initialize or run the validated flow without reading private
  local memory.
- Public docs do not mention private nicknames or internal-only state.
- Package behavior matches the artifacts-and-visibility model.

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

Acceptance gate:

- Cross-project Work Units remain auditable through source artifacts.
- Project repos keep their own code, tests, PRs, and release/apply policies.
- Company Ops gives visibility and coordination without replacing project
  ownership.

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

If all phases pass, the desired behavior is achievable: a Work Unit can be
assigned to a Team Lead, observed in Discord, discussed directly with the
appropriate Team Lead, tracked through a claim ledger, verified through
evidence, decided by the Operations Lead, and surfaced in a GitHub Project or
equivalent dashboard without creating hidden automation or fallback truth.
