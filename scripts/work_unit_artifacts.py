#!/usr/bin/env python3
"""Create the four required OpenClaw Company Ops Work Unit artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


ARTIFACTS = ("assignment.md", "claim.md", "evidence.md", "decision.md")
WORK_UNIT_RE = re.compile(r"^WU-\d{6}-\d{3}$")


def required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise argparse.ArgumentTypeError("value must not be empty")
    return cleaned


def work_unit_id(value: str) -> str:
    cleaned = required(value)
    if not WORK_UNIT_RE.match(cleaned):
        raise argparse.ArgumentTypeError("expected format WU-YYMMDD-NNN")
    return cleaned


def create_work_unit(args: argparse.Namespace) -> int:
    output_dir = args.output_root.expanduser() / args.work_unit_id
    created_at = args.created_at or dt.date.today().isoformat()

    if output_dir.exists() and not args.force:
        print(
            f"error: output directory already exists: {output_dir}\n"
            "Use --force to replace generated artifact files.",
            file=sys.stderr,
        )
        return 1

    if output_dir.exists() and not output_dir.is_dir():
        print(f"error: output path exists and is not a directory: {output_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    context = {
        "work_unit_id": args.work_unit_id,
        "title": args.title,
        "work_card": args.work_card,
        "operations_lead": args.operations_lead,
        "team_lead": args.team_lead,
        "created_at": created_at,
        "assignment_path": f"{output_dir / 'assignment.md'}",
        "claim_path": f"{output_dir / 'claim.md'}",
        "evidence_path": f"{output_dir / 'evidence.md'}",
        "decision_path": f"{output_dir / 'decision.md'}",
    }

    rendered = {
        "assignment.md": render_assignment(context),
        "claim.md": render_claim(context),
        "evidence.md": render_evidence(context),
        "decision.md": render_decision(context),
    }

    for filename, content in rendered.items():
        path = output_dir / filename
        if path.exists() and not args.force:
            print(f"error: artifact already exists: {path}", file=sys.stderr)
            return 1
        path.write_text(content, encoding="utf-8")

    print(f"created {output_dir}")
    for filename in ARTIFACTS:
        print(f"- {filename}")
    return 0


def render_assignment(context: dict[str, str]) -> str:
    return f"""# Assignment Packet

Status: Draft

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Operations Lead: `{context["operations_lead"]}`
- Assigned Team Lead OpenClaw Agent: `{context["team_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Goal

State the single outcome expected from this Work Unit.

## Background

Include only the context needed to execute the Work Unit.

## Scope

What the team lead should do:

-

## Non-goals

What the team lead should not do:

-

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Other constraints:

## Inputs

Links, files, references, or starting state:

-

## Done Criteria

The Work Unit can be considered ready for review when:

-

## Verification Criteria

Evidence or checks required for review:

-

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

```yaml
protocol_capsule:
  mode: <goal|verify>
  support: []
  loop: <plan -> repeat(act_or_improve -> verify) until stop_only_on, only for goal>
  stop_only_on:
    - done_criteria_passed_with_evidence
    - explicit_blocker
    - safety_or_budget_limit
    - operations_lead_or_user_pause
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_selected_mode
```

For `goal` mode, do not stop after one failed verification. Plan once, then
repeat implementation or improvement and verification until a `stop_only_on`
condition is true.

Planning is required for `goal`, but it should be proportional. Small Work
Units can use a concise 1-3 bullet plan; risky or multi-step Work Units need a
fuller plan.

## Expected Outputs

- Evidence & Result Record:
- PR or artifact:
- Decision-ready summary:

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
"""


def render_claim(context: dict[str, str]) -> str:
    return f"""# Ops Claim Ledger Entry

Status: Draft

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-{context["work_unit_id"]}-001`
- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Claim type: `execution`
- Owner session ref: `{context["team_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Expected Responsibility

- Expected state: `assigned`
- Expected until:
- Last claim: Assignment Packet prepared; waiting for `{context["team_lead"]}` execution.
- Last seen compaction count: `unknown`

Allowed expected states:

- `assigned`
- `working`
- `waiting`
- `blocked`
- `result_ready`
- `done`

`done` is not completion truth. It is an expected responsibility state after
the Operations Lead has made a decision.

## Artifact References

- Assignment Packet: `{context["assignment_path"]}`
- Evidence ref: `{context["evidence_path"]}`
- Operations Lead decision ref: `{context["decision_path"]}`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

-
"""


def render_evidence(context: dict[str, str]) -> str:
    return f"""# Evidence & Result Record

Status: Draft

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Assignment Packet: `{context["assignment_path"]}`
- Team Lead OpenClaw Agent: `{context["team_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Result Summary

Summarize what was completed.

## Evidence

Link only real artifacts or checks that exist.

- PR:
- Test output:
- Reports:
- Sources:
- Screenshots:
- Generated artifacts:
- Review notes:

## Verification Performed

-

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion:
  - Status:
  - Evidence:

## Remaining Risks

-

## Open Questions

-

## Team Lead Recommendation

Recommended decision:

- `accept`
- `revise`
- `hold`
- `reject`

Rationale:

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
"""


def render_decision(context: dict[str, str]) -> str:
    return f"""# Operations Lead Decision

Status: Pending

The Operations Lead decision records whether the submitted result satisfies the
Assignment Packet and evidence requirements.

## Identity

- Decision ref: `DECISION-{context["work_unit_id"]}`
- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Assignment Packet: `{context["assignment_path"]}`
- Evidence & Result Record: `{context["evidence_path"]}`
- Operations Lead: `{context["operations_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Decision

Choose one:

- `accept`
- `revise`
- `hold`
- `reject`

## Rationale

Explain the decision using the Assignment Packet and Evidence & Result Record.

## Required Follow-up

-

## Closure Instruction

If accepted:

- Link this decision to the Work Card.
- Link the Evidence & Result Record to the Work Card.
- Close the Work Card only after both links exist.

If not accepted:

- Keep the Work Card open.
- Update the Ops Claim Ledger entry with the next expected responsibility.

## No Fallback Rule

This decision must not be inferred from GitHub labels, dashboard status,
Discord messages, or Team Lead claims.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create OpenClaw Company Ops Work Unit artifact files.",
    )
    subparsers = parser.add_subparsers(dest="resource")

    work_unit = subparsers.add_parser("work-unit", help="Manage Work Unit artifacts")
    work_unit_subparsers = work_unit.add_subparsers(dest="action")
    create = work_unit_subparsers.add_parser(
        "create",
        help="Create assignment.md, claim.md, evidence.md, and decision.md",
    )
    create.add_argument("--work-unit-id", required=True, type=work_unit_id)
    create.add_argument("--title", required=True, type=required)
    create.add_argument("--work-card", required=True, type=required)
    create.add_argument("--operations-lead", required=True, type=required)
    create.add_argument("--team-lead", required=True, type=required)
    create.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory that will receive <work-unit-id>/",
    )
    create.add_argument(
        "--created-at",
        type=required,
        help="Creation date to record, default: today's local date",
    )
    create.add_argument(
        "--force",
        action="store_true",
        help="Replace generated artifact files in an existing output directory",
    )
    create.set_defaults(func=create_work_unit)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help(sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
