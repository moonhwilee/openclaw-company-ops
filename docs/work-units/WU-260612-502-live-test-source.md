# WU-260612-502 Live Test Source

Purpose: verify the live Company Ops protocol after commit `8c0b0a2`
(`Harden Company Ops visibility readbacks`).

This live test must use source artifacts as the source of truth. Discord,
GitHub Work Cards, and GitHub Project fields are mirrors that need readback
proof.

## Focus Areas

- Discord proof rows preserve expected/live text hashes, lengths, bounded
  snippets, and match basis.
- Goal/convergence progress uses `CHECKPOINT` rendered as `[PROGRESS]`.
- Retry/re-run loop progress uses `🔄 [PROGRESS]`.
- Closeout revision states use `⚠️ [REVISE]` and owner-facing
  `⚠️ [수정필요]`.
- Project sync stores per-Work Unit readback snapshots and compact managed
  issue-label snapshots.
- Accepted closeout stores Work Card summary comment and issue close readback
  snapshots.

## Test Boundary

The Operations Lead must stop after accepted Team Lead dispatch in the default
fire-and-forget path. After dispatch, any observation must be read-only unless
the owner explicitly approves recovery or takeover.
