# verify Protocol

Status: Manual Day-0

`verify` is the Team Lead protocol for checking whether outputs and evidence
satisfy the Assignment Packet.

It may run as a standalone verification Work Unit or inside the `goal` loop.
Standalone `verify` is read-only with respect to the candidate output being
checked, but it may write its own verification artifact. Allowed verify writes
must be scoped to its own Work Unit artifact subtree,
`docs/work-units/<work-unit-id>/`, and must not directly edit core Work Unit
control artifacts such as assignment, claim, decision, progress, proof,
dispatch, card, or closeout files. Verify must not mutate candidate outputs,
git, GitHub Project, Discord, or external systems.
Official Work Unit lifecycle commands are a narrow exception: a `verify` Team
Lead may publish source-backed `CHECKPOINT` or `RESULT_READY` proof through the
foreground Company Ops commands after writing evidence. Those commands may
update lifecycle visibility such as Discord proof or Project `Result Ready`,
but they must not change the candidate output or make final closeout decisions.

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
7. When evidence is ready, use the official result-ready path rather than
   writing final decision, GitHub Project final status, or Discord closeout
   messages directly.

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
- Verification-only auxiliary artifacts under the same Work Unit artifact
  subtree.

Unacceptable evidence includes:

- "I did it" claims.
- Dashboard-only status.
- Discord messages.
- Labels.
- PR summaries that do not link to the real artifact.

## Result

Verification must produce a criterion-by-criterion mapping that the Operations
Lead can review without inferring missing context.
