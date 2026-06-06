#!/usr/bin/env python3
"""Summarize one Work Unit audit trail from local source artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from ops_claim_ledger import DEFAULT_LEDGER, get_claims, load_ledger


DEFAULT_ARTIFACT_ROOT = Path("docs/examples/manual-dry-run")
REQUIRED_ARTIFACTS = ("assignment.md", "claim.md", "evidence.md", "decision.md")
PROGRESS_ARTIFACT = "progress.jsonl"
FIELD_RE = re.compile(r"^- ([^:]+):\s*(.*)$")
STATUS_RE = re.compile(r"^Status:\s*(.+)$", re.MULTILINE)
WORK_UNIT_RE = re.compile(r"^WU-(?:\d{6}|\d{8})-\d{3}$")
EXECUTION_ROUTE_FIELDS = {
    "execution route",
    "execution route for this work unit",
}
VALID_EXECUTION_ROUTES = {"cli-direct", "cli-delivered", "discord-bound"}


def clean_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "`":
        return value[1:-1]
    return value


def status_work_unit_id(value: str) -> str:
    cleaned = clean_value(value)
    if not WORK_UNIT_RE.match(cleaned):
        raise argparse.ArgumentTypeError("expected format WU-YYMMDD-NNN or WU-YYYYMMDD-NNN")
    return cleaned


def parse_markdown_artifact(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    status_match = STATUS_RE.search(text)
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if match:
            fields[match.group(1).strip().lower()] = clean_value(match.group(2))
    return {
        "path": str(path),
        "exists": True,
        "status": clean_value(status_match.group(1)) if status_match else "",
        "fields": fields,
    }


def missing_artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": False, "status": "", "fields": {}}


def has_real_ref(value: str) -> bool:
    return bool(value and value != "pending")


def find_ledger_claim(ledger_path: Path, work_unit: str) -> tuple[dict[str, Any] | None, str]:
    expanded = ledger_path.expanduser()
    if not expanded.exists():
        return None, f"ledger not found: {expanded}"
    ledger = load_ledger(expanded)
    matches = [
        claim
        for claim in get_claims(ledger).values()
        if str(claim.get("work_unit_id") or "") == work_unit
    ]
    if not matches:
        return None, f"no ledger claim for {work_unit}"
    matches.sort(key=lambda claim: str(claim.get("claim_ref") or ""))
    return matches[0], ""


def choose_first(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def read_progress(path: Path, work_unit_id: str) -> dict[str, Any]:
    empty = {
        "exists": False,
        "ref": "",
        "phase": "",
        "phase_index": "",
        "phase_total": "",
        "round": "",
        "show_round": False,
        "current_slice": "",
        "next_checkpoint": "",
        "updated_at": "",
        "source_ref": "",
        "valid_rows": 0,
        "invalid_rows": 0,
    }
    if not path.exists():
        return empty

    latest: dict[str, Any] = {}
    valid_rows = 0
    invalid_rows = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            invalid_rows += 1
            continue
        if not isinstance(row, dict):
            invalid_rows += 1
            continue
        row_work_unit = str(row.get("work_unit_id") or "")
        if row_work_unit and row_work_unit != work_unit_id:
            invalid_rows += 1
            continue
        if not any(row.get(key) for key in ("phase", "current_slice", "round", "next_checkpoint")):
            invalid_rows += 1
            continue
        latest = row
        valid_rows += 1

    return {
        "exists": True,
        "ref": str(path),
        "phase": str(latest.get("phase") or ""),
        "phase_index": str(latest.get("phase_index") or ""),
        "phase_total": str(latest.get("phase_total") or ""),
        "round": str(latest.get("round") or ""),
        "show_round": latest.get("show_round") is True
        or str(latest.get("show_round") or "").strip().lower() in {"1", "true", "yes"},
        "current_slice": str(latest.get("current_slice") or ""),
        "next_checkpoint": str(latest.get("next_checkpoint") or ""),
        "updated_at": str(latest.get("transition_at") or latest.get("updated_at") or ""),
        "source_ref": str(latest.get("source_ref") or latest.get("proof_ref") or ""),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
    }


def clean_route_value(value: str) -> str:
    cleaned = clean_value(value).strip().rstrip(".")
    if len(cleaned) >= 2 and cleaned[0] == "`" and cleaned[-1] == "`":
        cleaned = cleaned[1:-1]
    return cleaned.strip().lower()


def derive_execution_route(artifacts: dict[str, dict[str, Any]]) -> dict[str, str]:
    for filename in REQUIRED_ARTIFACTS:
        artifact = artifacts[filename]
        if not artifact["exists"]:
            continue
        for field_name, raw_value in artifact["fields"].items():
            if field_name not in EXECUTION_ROUTE_FIELDS:
                continue
            value = clean_route_value(raw_value)
            if value in VALID_EXECUTION_ROUTES:
                return {
                    "value": value,
                    "source": filename,
                    "field": field_name,
                }
            return {
                "value": "unknown",
                "source": filename,
                "field": field_name,
                "note": f"unsupported execution route value: {raw_value}",
            }
    return {
        "value": "unknown",
        "source": "missing",
        "field": "",
        "note": "no execution route field found",
    }


def derive_next_action(
    missing: list[str],
    claim_state: str,
    evidence_status: str,
    decision_status: str,
) -> str:
    if "assignment.md" in missing:
        return "Create or restore the Assignment Packet."
    if "claim.md" in missing:
        return "Create or restore the local claim artifact."
    if "evidence.md" in missing:
        return "Team Lead must produce Evidence & Result Record."
    if "decision.md" in missing:
        return "Operations Lead decision artifact is missing."
    if claim_state == "blocked":
        return "Operations Lead blocker review."
    if evidence_status.lower() in {"", "draft"}:
        return "Team Lead must update evidence before review."
    if decision_status.lower() in {"", "pending"}:
        return "Operations Lead decision is pending."
    if claim_state == "done" and decision_status.lower() == "accepted":
        return "Audit trail accepted; no next action recorded."
    return "Review current artifact state."


def derive_next_review(claim_fields: dict[str, str], next_action: str) -> str:
    expected_until = claim_fields.get("expected until", "")
    if next_action == "Operations Lead decision is pending.":
        return "Operations Lead decision"
    return expected_until or next_action


def build_summary(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    artifact_dir = args.artifact_root.expanduser() / args.work_unit_id
    artifacts: dict[str, dict[str, Any]] = {}
    missing: list[str] = []

    for filename in REQUIRED_ARTIFACTS:
        path = artifact_dir / filename
        if path.exists():
            artifacts[filename] = parse_markdown_artifact(path)
        else:
            artifacts[filename] = missing_artifact(path)
            missing.append(filename)

    assignment_fields = artifacts["assignment.md"]["fields"]
    claim_fields = artifacts["claim.md"]["fields"]
    evidence_fields = artifacts["evidence.md"]["fields"]
    decision_fields = artifacts["decision.md"]["fields"]
    progress = read_progress(artifact_dir / PROGRESS_ARTIFACT, args.work_unit_id)

    ledger_claim = None
    ledger_note = ""
    ledger_error = ""
    if args.ledger:
        try:
            ledger_claim, ledger_note = find_ledger_claim(args.ledger, args.work_unit_id)
        except ValueError as exc:
            ledger_error = str(exc)

    claim_state = choose_first(
        str(ledger_claim.get("expected_state") or "") if ledger_claim else "",
        claim_fields.get("expected state", ""),
    )
    evidence_status = artifacts["evidence.md"]["status"]
    decision_status = artifacts["decision.md"]["status"]
    next_action = derive_next_action(missing, claim_state, evidence_status, decision_status)
    next_review = derive_next_review(claim_fields, next_action)
    execution_route = derive_execution_route(artifacts)

    audit_problems = []
    for filename in missing:
        audit_problems.append(f"missing artifact: {filename}")
    if artifacts["evidence.md"]["exists"] and evidence_status.lower() in {"", "draft"}:
        audit_problems.append(f"evidence status is {evidence_status or 'missing'}")
    if artifacts["decision.md"]["exists"] and decision_status.lower() in {"", "pending"}:
        audit_problems.append(f"decision status is {decision_status or 'missing'}")
    if ledger_error:
        audit_problems.append(f"ledger problem: {ledger_error}")
    elif args.require_ledger and ledger_claim is None:
        audit_problems.append(f"ledger problem: {ledger_note}")
    if progress["exists"] and progress["invalid_rows"]:
        audit_problems.append(f"progress artifact has invalid rows: {progress['invalid_rows']}")

    work_card = choose_first(
        assignment_fields.get("work card", ""),
        claim_fields.get("work card", ""),
        evidence_fields.get("work card", ""),
        decision_fields.get("work card", ""),
    )
    assignment_packet = choose_first(
        claim_fields.get("assignment packet", ""),
        evidence_fields.get("assignment packet", ""),
        decision_fields.get("assignment packet", ""),
        str(artifact_dir / "assignment.md") if artifacts["assignment.md"]["exists"] else "",
    )
    evidence_ref = choose_first(
        claim_fields.get("evidence ref", ""),
        decision_fields.get("evidence & result record", ""),
        str(artifact_dir / "evidence.md") if artifacts["evidence.md"]["exists"] else "",
    )
    decision_ref = choose_first(
        claim_fields.get("operations lead decision ref", ""),
        str(artifact_dir / "decision.md") if artifacts["decision.md"]["exists"] else "",
    )

    summary = {
        "work_unit_id": args.work_unit_id,
        "artifact_dir": str(artifact_dir),
        "work_card": work_card,
        "assignment_packet": assignment_packet,
        "claim": {
            "claim_ref": choose_first(
                str(ledger_claim.get("claim_ref") or "") if ledger_claim else "",
                claim_fields.get("claim ref", ""),
            ),
            "expected_state": claim_state,
            "expected_until": choose_first(
                str(ledger_claim.get("expected_until") or "") if ledger_claim else "",
                claim_fields.get("expected until", ""),
            ),
            "owner_session_ref": choose_first(
                str(ledger_claim.get("owner_session_ref") or "") if ledger_claim else "",
                claim_fields.get("owner session ref", ""),
            ),
            "source": "ledger" if ledger_claim else "artifact" if artifacts["claim.md"]["exists"] else "missing",
            "ledger_note": ledger_note,
        },
        "evidence": {
            "ref": evidence_ref,
            "status": evidence_status,
            "exists": artifacts["evidence.md"]["exists"],
        },
        "decision": {
            "ref": decision_ref,
            "status": decision_status,
            "exists": artifacts["decision.md"]["exists"],
        },
        "progress": progress,
        "execution_route": execution_route,
        "current_state": claim_state or "unknown",
        "missing_artifacts": missing,
        "audit_problems": audit_problems,
        "next_review": next_review,
        "next_action": next_action,
        "artifacts": artifacts,
        "ledger": {
            "path": str(args.ledger.expanduser()) if args.ledger else "",
            "claim": ledger_claim,
            "note": ledger_note,
            "error": ledger_error,
        },
    }
    return summary, 1 if not artifact_dir.exists() else 0


def print_text(summary: dict[str, Any]) -> None:
    print(f"Work Unit: {summary['work_unit_id']}")
    print(f"Current state: {summary['current_state']}")
    print(f"Work Card: {summary['work_card'] or 'missing'}")
    print(f"Assignment Packet: {summary['assignment_packet'] or 'missing'}")
    claim = summary["claim"]
    print(
        "Claim: "
        f"{claim['claim_ref'] or 'missing'} "
        f"state={claim['expected_state'] or 'unknown'} "
        f"owner={claim['owner_session_ref'] or 'unknown'} "
        f"until={claim['expected_until'] or 'unknown'} "
        f"source={claim['source']}"
    )
    print(
        "Evidence: "
        f"{summary['evidence']['ref'] or 'missing'} "
        f"status={summary['evidence']['status'] or 'missing'}"
    )
    print(
        "Decision: "
        f"{summary['decision']['ref'] or 'missing'} "
        f"status={summary['decision']['status'] or 'missing'}"
    )
    progress = summary["progress"]
    print(
        "Progress: "
        f"{progress['ref'] or 'missing'} "
        f"phase={progress['phase'] or progress['current_slice'] or 'unknown'} "
        f"round={progress['round'] or 'unknown'}"
    )
    route = summary["execution_route"]
    print(
        "Execution route: "
        f"{route['value']} "
        f"source={route['source']}"
        f"{' field=' + route['field'] if route['field'] else ''}"
    )
    print(f"Next review: {summary['next_review'] or 'unknown'}")
    print(f"Next action: {summary['next_action']}")
    if summary["missing_artifacts"]:
        print("Missing artifacts:")
        for item in summary["missing_artifacts"]:
            print(f"- {item}")
    else:
        print("Missing artifacts: none")
    if summary["audit_problems"]:
        print("Audit problems:")
        for item in summary["audit_problems"]:
            print(f"- {item}")
    else:
        print("Audit problems: none")


def cmd_work_unit(args: argparse.Namespace) -> int:
    try:
        summary, return_code = build_summary(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print_text(summary)
    return return_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize Work Unit audit state from local artifacts.")
    subparsers = parser.add_subparsers(dest="resource")

    status = subparsers.add_parser("status", help="Read-only status summaries")
    status_subparsers = status.add_subparsers(dest="target")

    work_unit = status_subparsers.add_parser("work-unit", help="Summarize one Work Unit")
    work_unit.add_argument("--work-unit-id", required=True, type=status_work_unit_id)
    work_unit.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help=f"Root containing <work-unit-id>/ artifacts, default: {DEFAULT_ARTIFACT_ROOT}",
    )
    work_unit.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help=f"Optional JSON ledger to read, default: {DEFAULT_LEDGER}",
    )
    work_unit.add_argument(
        "--no-ledger",
        action="store_const",
        const=None,
        dest="ledger",
        help="Do not read the optional JSON claim ledger.",
    )
    work_unit.add_argument(
        "--require-ledger",
        action="store_true",
        help="Report an audit problem if the JSON ledger or Work Unit claim is missing.",
    )
    work_unit.add_argument("--format", choices=("text", "json"), default="text")
    work_unit.set_defaults(func=cmd_work_unit)

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
