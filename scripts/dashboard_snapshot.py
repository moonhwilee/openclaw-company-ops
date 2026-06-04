#!/usr/bin/env python3
"""Build visibility-only dashboard snapshots from Company Ops source artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ops_claim_ledger import DEFAULT_LEDGER, get_claims, load_ledger


def row_from_claim(claim: dict[str, Any]) -> dict[str, str]:
    evidence = str(claim.get("evidence_ref") or "")
    decision = str(claim.get("operations_lead_decision_ref") or "")
    return {
        "work_unit_id": str(claim.get("work_unit_id") or ""),
        "work_card": str(claim.get("work_card") or ""),
        "claim_ref": str(claim.get("claim_ref") or ""),
        "team_lead": str(claim.get("owner_session_ref") or ""),
        "state": str(claim.get("expected_state") or ""),
        "expected_until": str(claim.get("expected_until") or ""),
        "assignment_packet": str(claim.get("assignment_packet") or ""),
        "evidence_ref": evidence,
        "operations_lead_decision_ref": decision,
        "next_review": next_review_for(claim, evidence, decision),
    }


def next_review_for(claim: dict[str, Any], evidence: str, decision: str) -> str:
    state = str(claim.get("expected_state") or "")
    if state == "result_ready" and not has_real_ref(decision):
        return "Operations Lead decision"
    if state == "blocked":
        return "Operations Lead blocker review"
    if not has_real_ref(evidence) and state == "done":
        return "Evidence missing; review before closure"
    return str(claim.get("expected_until") or "")


def has_real_ref(value: str) -> bool:
    return bool(value and value != "pending")


def print_markdown(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No dashboard rows.")
        return
    headers = ("Work Unit", "State", "Team Lead", "Expected Until", "Next Review", "Claim")
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        print(
            "| "
            + " | ".join(
                [
                    row["work_unit_id"],
                    row["state"],
                    row["team_lead"],
                    row["expected_until"],
                    row["next_review"],
                    row["claim_ref"],
                ]
            )
            + " |"
        )


def cmd_snapshot(args: argparse.Namespace) -> int:
    try:
        ledger = load_ledger(args.ledger)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows = [
        row_from_claim(claim)
        for claim in sorted(get_claims(ledger).values(), key=lambda item: item.get("work_unit_id", ""))
    ]
    if args.state:
        rows = [row for row in rows if row["state"] == args.state]

    if args.format == "json":
        print(json.dumps({"rows": rows}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print_markdown(rows)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build visibility-only dashboard snapshots.")
    subparsers = parser.add_subparsers(dest="resource")

    dashboard = subparsers.add_parser("dashboard", help="Build dashboard visibility outputs")
    dashboard_subparsers = dashboard.add_subparsers(dest="action")

    snapshot = dashboard_subparsers.add_parser("snapshot", help="Render ledger claims as dashboard rows")
    snapshot.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help=f"JSON ledger path, default: {DEFAULT_LEDGER}",
    )
    snapshot.add_argument("--state", help="Optional expected_state filter")
    snapshot.add_argument("--format", choices=("markdown", "json"), default="markdown")
    snapshot.set_defaults(func=cmd_snapshot)

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
