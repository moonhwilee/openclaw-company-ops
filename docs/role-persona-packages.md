# Role Persona Packages

Status: Design

Role persona packages are curated Team Lead and subagent role definitions for
Company Ops. They are not a new worker runtime, hidden orchestrator, mailbox, or
state machine.

The goal is to make clean installs repeatable without changing the Company Ops
execution model:

Owner -> Operations Lead -> Team Lead -> optional subagents -> evidence ->
Operations Lead decision.

## Design Principles

- Goal completion comes first.
- Avoid overengineering and runtime expansion.
- Keep Work Unit ownership with the assigned Team Lead.
- Keep Operations Lead authority over routing, budgets, guardrails, source
  truth, closeout, Project mutation, and owner-facing completion.
- Treat subagent output as input for Team Lead judgment, not completion truth.
- Keep the default package small and inspectable.
- Make all installed role instructions visible, repeatable, and removable.
- Do not copy private Operations Lead memory, owner chat history, credentials,
  local personal context, or machine-specific paths into public package
  templates.

## Package Types

### Core Package

The core package should be installed by default when Company Ops is installed.
It should stay small enough that Team Leads can choose roles without spending
work budget on role selection.

Recommended core roles:

- `planner`: decomposes the Work Unit into a proportional plan.
- `verifier`: checks outputs and evidence against done and verification
  criteria.
- `critic-reviewer`: challenges assumptions, scope creep, and missing tests.
- `researcher`: gathers source-backed facts and cites source refs.
- `risk-security-reviewer`: checks authority, external mutation, credential,
  safety, and destructive-action risks.

### Domain Packages

Domain packages are optional overlays for recurring operating domains. They
should be installed only when the owner or Operations Lead accepts the setup
plan.

Examples:

- `company-ops-dev`: implementer, architect-reviewer, test-verifier,
  refactor-critic.
- `company-ops-revenue`: customer-workflow-verifier, pricing-critic,
  funnel-researcher.
- `company-ops-market`: market-researcher, source-verifier,
  competitor-critic.
- `company-ops-ops`: process-verifier, runbook-critic,
  incident-risk-reviewer.

Domain packages must not replace the core protocol. They only provide reusable
role definitions that the Team Lead may invoke within the Assignment Packet's
budget and authority.

## Invocation Model

The Assignment Packet remains the source of truth. Role packages do not decide
the Work Unit's staffing plan by themselves.

The Operations Lead sets:

- Work Unit route and mode.
- Done and verification criteria.
- Mutation authority.
- Source context refs.
- Subagent control policy and budget.
- Any hard constraints or required perspectives.

The Team Lead decides:

- Whether subagents are useful.
- Which installed roles to invoke.
- Which domain overlays fit the Work Unit.
- How to reconcile conflicting subagent outputs.
- What evidence is ready for Operations Lead review.

`subagents` describes who controls subagents if they are used.
`subagent_budget: none` means the Work Unit uses no subagents and is handled
directly by the Team Lead.

There is no one-subagent path. If the Team Lead uses subagents, it should use at
least two complementary perspectives within the approved budget.

## Source Context Delivery

Team Leads must be able to inspect the real source context. The Operations Lead
must not replace required source documents with a compressed chat summary.

For `goal` and `verify` Work Units, source context should be delivered as source
refs:

- Repo-relative paths.
- Work Unit artifact paths.
- Attached files materialized into the Work Unit artifact subtree.
- Stable URLs when the Team Lead has network access and the URL is allowed by
  the Assignment Packet.
- A source context manifest when the reference set is large.

The Assignment Packet may summarize why each document matters, but the summary
is only a navigation aid. It is not source truth and must not replace the source
document.

When documents are large, create or reference a source context manifest such as:

```yaml
source_context:
  required:
    - path: docs/specs/implementation-plan.md
      reason: primary implementation plan
      expected_use: read before planning
    - path: docs/references/customer-notes.md
      reason: customer workflow evidence
      expected_use: verify claims against raw notes
  optional:
    - path: docs/archive/previous-review.md
      reason: prior context only
  forbidden:
    - private memory
    - credentials
    - owner chat history unless explicitly approved
```

For very large corpora, the Team Lead should receive a manifest plus exact
paths, file groups, or search instructions. The Team Lead can then inspect,
search, and cite the underlying documents directly. If the runtime cannot expose
the referenced documents to the Team Lead, the Work Unit is `blocked` with
`setup-needed`; the Operations Lead should not hand over a lossy summary as a
substitute.

## Clean Install Requirement

A clean Company Ops install must make the following available to Operations Lead
and Team Lead agents:

- Company Ops skill or routing instructions.
- Protocol docs.
- Assignment Packet templates.
- The context-recovery core prompt and Company Ops source-record overlay from
  `docs/protocols/context-recovery.md`, installed into Team Lead and
  closeout-delegate setup prompts.
- CLI tools needed for source-backed claim, progress, evidence, result-ready,
  and local verification work.
- Installed role persona package definitions accepted during setup.
- Source context refs or manifests for each Work Unit.

If Team Leads run in a separate runtime or workspace, setup must expose the same
Company Ops package and the referenced source documents there, or return
`setup-needed`.

## Non-Goals

- Do not implement a gajae-code-style team runtime.
- Do not add mailbox, worker claim, or inter-worker state machinery.
- Do not let packages mutate Project, Discord closeout, owner-facing reports,
  credentials, production systems, or external surfaces.
- Do not install large persona collections by default.
- Do not turn role packages into automatic routing or staffing decisions.

## Acceptance Criteria

Role persona packages are acceptable when:

- The core package stays small and inspectable.
- Domain packages are optional and owner-approved.
- Team Lead ownership remains intact.
- Operations Lead authority boundaries remain intact.
- Assignment Packets continue to carry source truth, criteria, authority, and
  budget.
- Required documents are passed as source refs or manifests, not lossy summaries.
- Evidence records actual subagent usage and reconciles outputs.

If these criteria are not met, the package should be revised before Phase 6
packaging.
