# verify Protocol

Status: Manual Day-0

`verify` is the Team Lead protocol for checking whether outputs and evidence
satisfy the Assignment Packet.

It may run as a standalone verification Work Unit or inside the `goal` loop.
Standalone `verify` is read-only with respect to the candidate output being
checked, but it may write its own verification artifact. Allowed verify writes
must be scoped to the Work Unit's `evidence.md`, `verification.md`,
`verification-artifacts/`, or `evidence-artifacts/`; verify must not mutate
candidate outputs, git, GitHub Project, Discord, or external systems.

## Inputs

- Assignment Packet done criteria.
- Assignment Packet verification criteria.
- Candidate outputs.
- Evidence & Result Record draft or submitted evidence.

## Procedure

1. Extract each done criterion and verification criterion.
2. Match each criterion to concrete evidence.
3. Mark each criterion as `pass`, `fail`, or `unknown`.
4. For each `fail` or `unknown`, state the specific missing artifact, check, or
   decision.
5. If running inside `goal`, return failures to the improvement loop.
6. If running as verification-only, recommend `accept`, `revise`, or
   `blocked`.

If the Assignment Packet authorizes subagents for verification, use only the
packet's `subagent_budget`. The budget is a prompt/packet contract, not a
runtime hook or hard enforcement layer.

## Evidence Standard

Verification recognizes evidence, not effort.

Acceptable evidence includes:

- Existing file paths.
- PRs or commits.
- Test or validation output.
- Reports or generated artifacts.
- Review notes tied to the Assignment Packet.

Unacceptable evidence includes:

- "I did it" claims.
- Dashboard-only status.
- Discord messages.
- Labels.
- PR summaries that do not link to the real artifact.

## Result

Verification must produce a criterion-by-criterion mapping that the Operations
Lead can review without inferring missing context.
