# Templates

Status: Manual Day-0

These templates make the current manual operating loop reproducible before a
dedicated OpenClaw Company Ops package exists.

They are not an automated runtime, database, dashboard, or command router.

## Available Templates

- [Work Card](work-card.md): manual version of the GitHub Issue Work Card.
- [Assignment Packet](assignment-packet.md): detailed handoff from Operations
  Lead to Team Lead OpenClaw Agent.
- [Ops Claim Ledger Entry](ops-claim-ledger-entry.md): current responsibility
  expectation record.
- [Evidence & Result Record](evidence-result-record.md): result proof bundle for
  review.
- [Operations Lead Decision](operations-lead-decision.md): review decision and
  rationale.
- [Progress Log](progress-log.md): optional source-backed long-work progress
  metadata for dashboard `Phase`.
- [Team Playbook](team-playbook.md): prompt/checklist
  for team lead execution.
- [Team Lead Protocols](../protocols/README.md): canonical references for
  `goal` and `verify` Protocol Capsules.

The GitHub Issue form for Work Cards lives in
`.github/ISSUE_TEMPLATE/work-card.yml`.

## Rules

- A Work Card cannot replace the Assignment Packet.
- Protocol files cannot replace the Assignment Packet or active Protocol
  Capsule.
- A GitHub label, dashboard field, or Discord message cannot replace the Ops
  Claim Ledger entry.
- A status claim cannot replace the Evidence & Result Record.
- A PR summary cannot replace Operations Lead review.
- If a required artifact is missing, mark the Work Unit blocked.
