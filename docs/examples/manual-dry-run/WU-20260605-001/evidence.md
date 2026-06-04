# Evidence & Result Record

Status: Day-0 Smoke Artifact + Live Build-Lab Read-Only Run

## Identity

- Work Unit id: `WU-20260605-001`
- Work Card: manual smoke artifact
- Assignment Packet: `docs/examples/manual-dry-run/WU-20260605-001/assignment.md`
- Team Lead OpenClaw Agent: `build-lab`
- Submitted at: `2026-06-05`

## Result Summary

The repository now documents Team Lead Protocol Capsules as a packet-first
execution contract. Canonical protocol references exist for `goal`, `verify`,
and `conv`, and the Assignment Packet / Team Playbook templates describe how the
Team Lead should execute a delegated Work Unit without a separate execution runtime.

## Evidence

- Protocol references:
  - `docs/protocols/README.md`
  - `docs/protocols/goal.md`
  - `docs/protocols/verify.md`
  - `docs/protocols/conv.md`
- Updated templates:
  - `docs/templates/assignment-packet.md`
  - `docs/templates/team-playbook.md`
  - `docs/templates/README.md`
- Updated architecture/index:
  - `docs/architecture.md`
  - `README.md`
  - `docs/examples/manual-dry-run/README.md`
- Smoke artifacts:
  - `docs/examples/manual-dry-run/WU-20260605-001/assignment.md`
  - `docs/examples/manual-dry-run/WU-20260605-001/claim.md`
  - `docs/examples/manual-dry-run/WU-20260605-001/evidence.md`
  - `docs/examples/manual-dry-run/WU-20260605-001/decision.md`

## Verification Performed

- `git diff --check`
- Required-content validation script.
- Private-name scan over public docs.
- Live `build-lab` read-only smoke run through OpenClaw Gateway:
  - First run: `blocked` because the relative Assignment Packet path was not
    present in the Team Lead workspace.
  - Revised run: `pass` and recommended `accept` after Operations Lead supplied
    the absolute Assignment Packet path.
- Protocol Capsule mode retest after removing the template `mode: goal`
  default:
  - Direct non-Work-Unit request returned `mode=direct` and answered normally.
  - Verify-only packet returned `mode=verify`, `goal_work_started=no`, and
    rejected the false claim `2 + 2 = 5`.
  - Goal packet returned `mode=goal`, `goal_work_started=yes`, and accepted the
    requested one-sentence output.
  - Conv packet returned `mode=conv`, `goal_work_started=no`, recovered state,
    and named the next action.
- `git status --short`

## Done Criteria Mapping

- Criterion: Canonical protocol files exist under `docs/protocols/`.
  - Status: `pass`
  - Evidence: `docs/protocols/README.md`, `goal.md`, `verify.md`, `conv.md`
- Criterion: Assignment Packet template includes a Protocol Capsule section.
  - Status: `pass`
  - Evidence: `docs/templates/assignment-packet.md`
- Criterion: Team Playbook includes packet-first, `goal`, `verify`, and `conv`
  execution guidance.
  - Status: `pass`
  - Evidence: `docs/templates/team-playbook.md`
- Criterion: Architecture and index docs reference Team Lead Protocols and
  Protocol Capsules.
  - Status: `pass`
  - Evidence: `docs/architecture.md`, `README.md`, `docs/templates/README.md`
- Criterion: A manual smoke example exists for `WU-20260605-001`.
  - Status: `pass`
  - Evidence: this directory.
- Criterion: A live read-only `build-lab` smoke run records packet-first
  behavior.
  - Status: `pass`
  - Evidence: first `build-lab` run blocked on missing packet; second run read
    the repo source-of-truth packet at
    `docs/examples/manual-dry-run/WU-20260605-001/assignment.md`, executed
    `goal` with `verify` and `conv` support, mapped criteria to evidence, and
    recommended `accept`.
- Criterion: Protocol Capsule mode selection does not force all requests into
  `goal`.
  - Status: `pass`
  - Evidence: direct, verify-only, goal, and conv smoke turns returned the
    requested modes; verify-only and conv both reported `goal_work_started=no`.
- Criterion: Static validation checks pass.
  - Status: `pass`
  - Evidence: validation commands listed above.

## Remaining Risks

- The live `build-lab` run was read-only documentation verification, not a
  product implementation Work Unit.
- The next stronger test should use this same Packet-First Rule on a real
  build-lab implementation Work Unit.

## Open Questions

- None for this documentation smoke artifact.

## Team Lead Recommendation

Recommended decision:

- `accept`

Rationale:

The documentation and templates now encode the Protocol Capsule convention and
static checks confirm the required files and phrases exist. The live read-only
`build-lab` smoke also demonstrated the intended behavior: block when the packet
is unavailable, execute the explicit packet when provided, answer direct
non-Work-Unit requests normally, and select `goal`, `verify`, or `conv` from the
active Protocol Capsule instead of defaulting every request to `goal`.
