#!/usr/bin/env python3
"""Manage a small JSON-backed OpenClaw Company Ops claim ledger."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

from result_ready_gate import result_ready_gate


DEFAULT_LEDGER = Path("~/.openclaw/state/openclaw-company-ops/claims/ledger.json")
DEFAULT_ARTIFACT_ROOT = Path("docs/examples/manual-dry-run")
LEDGER_VERSION = 1
WORK_UNIT_RE = re.compile(r"^WU-\d{6}-\d{3}$")
CLAIM_RE = re.compile(r"^CLAIM-.+")
CLAIM_TYPES = ("orchestration", "execution")
EXPECTED_STATES = ("assigned", "working", "waiting", "blocked", "result_ready", "done")
UPDATE_FIELDS = (
    "work_card",
    "owner_session_ref",
    "expected_state",
    "expected_until",
    "last_claim",
    "last_seen_compaction_count",
    "assignment_packet",
    "evidence_ref",
    "operations_lead_decision_ref",
)


def infer_artifact_root(work_unit: str, *refs: str) -> Path | None:
    for ref in refs:
        cleaned = str(ref or "").strip()
        if not cleaned or cleaned == "pending" or "://" in cleaned or cleaned.startswith("#"):
            continue
        path = Path(cleaned).expanduser()
        parent = path.parent
        if parent.name == work_unit:
            return parent.parent
    return None


def validate_result_ready_claim(
    args: argparse.Namespace,
    work_unit: str,
    claim_state: str,
    *refs: str,
) -> tuple[bool, dict[str, Any]]:
    if claim_state != "result_ready":
        return True, {}
    artifact_root = infer_artifact_root(work_unit, *refs) or args.artifact_root
    gate = result_ready_gate(artifact_root, work_unit, claim_state_override=claim_state)
    return bool(gate["ready"]), gate


def print_gate_failure(gate: dict[str, Any]) -> None:
    print(f"error: result_ready claim gate failed: {gate.get('status') or 'repair-needed'}", file=sys.stderr)
    for failure in gate.get("failures") or []:
        print(
            "  - "
            f"{failure.get('class')}: {failure.get('field')}: {failure.get('message')} "
            f"({failure.get('repair_hint')})",
            file=sys.stderr,
        )


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


def claim_ref(value: str) -> str:
    cleaned = required(value)
    if not CLAIM_RE.match(cleaned):
        raise argparse.ArgumentTypeError("expected format CLAIM-...")
    return cleaned


def now_iso() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def load_ledger(path: Path, *, allow_missing: bool = False) -> dict[str, Any]:
    expanded = path.expanduser()
    if not expanded.exists():
        if not allow_missing:
            raise ValueError(f"ledger not found: {expanded}")
        return {"version": LEDGER_VERSION, "claims": {}}
    try:
        data = json.loads(expanded.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"ledger is not valid JSON: {expanded}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"ledger root must be a JSON object: {expanded}")
    claims = data.get("claims")
    if claims is None:
        data["claims"] = {}
    elif not isinstance(claims, dict):
        raise ValueError(f"ledger claims must be a JSON object: {expanded}")
    data.setdefault("version", LEDGER_VERSION)
    return data


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    expanded = path.expanduser()
    expanded.parent.mkdir(parents=True, exist_ok=True)
    temp_path = expanded.with_suffix(expanded.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(expanded)


def get_claims(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return ledger["claims"]


def cmd_create(args: argparse.Namespace) -> int:
    try:
        ledger = load_ledger(args.ledger, allow_missing=True)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    claims = get_claims(ledger)
    ref = args.claim_ref or f"CLAIM-{args.work_unit_id}-001"
    if ref in claims:
        print(f"error: claim already exists: {ref}", file=sys.stderr)
        return 1

    timestamp = args.created_at or now_iso()
    ok, gate = validate_result_ready_claim(
        args,
        args.work_unit_id,
        args.expected_state,
        args.assignment_packet,
        args.evidence_ref,
        args.operations_lead_decision_ref,
    )
    if not ok:
        print_gate_failure(gate)
        return 1
    claims[ref] = {
        "claim_ref": ref,
        "work_unit_id": args.work_unit_id,
        "work_card": args.work_card,
        "claim_type": args.claim_type,
        "owner_session_ref": args.owner_session_ref,
        "expected_state": args.expected_state,
        "expected_until": args.expected_until,
        "last_claim": args.last_claim,
        "last_seen_compaction_count": args.last_seen_compaction_count,
        "assignment_packet": args.assignment_packet,
        "evidence_ref": args.evidence_ref,
        "operations_lead_decision_ref": args.operations_lead_decision_ref,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    save_ledger(args.ledger, ledger)
    print(f"created {ref}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    try:
        ledger = load_ledger(args.ledger)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    claims = get_claims(ledger)
    claim = claims.get(args.claim_ref)
    if claim is None:
        print(f"error: claim not found: {args.claim_ref}", file=sys.stderr)
        return 1

    changes = {field: getattr(args, field) for field in UPDATE_FIELDS if getattr(args, field) is not None}
    if not changes:
        print("error: provide at least one field to update", file=sys.stderr)
        return 2

    projected = dict(claim)
    projected.update(changes)
    ok, gate = validate_result_ready_claim(
        args,
        str(projected.get("work_unit_id") or ""),
        str(projected.get("expected_state") or ""),
        str(projected.get("assignment_packet") or ""),
        str(projected.get("evidence_ref") or ""),
        str(projected.get("operations_lead_decision_ref") or ""),
    )
    if not ok:
        print_gate_failure(gate)
        return 1

    claim.update(changes)
    claim["updated_at"] = args.updated_at or now_iso()
    save_ledger(args.ledger, ledger)
    print(f"updated {args.claim_ref}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    try:
        ledger = load_ledger(args.ledger)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    claims = get_claims(ledger)
    if args.claim_ref:
        claim = claims.get(args.claim_ref)
        if claim is None:
            print(f"error: claim not found: {args.claim_ref}", file=sys.stderr)
            return 1
        output = claim
    else:
        output = [
            claim
            for claim in sorted(claims.values(), key=lambda item: item.get("claim_ref", ""))
            if args.expected_state is None or claim.get("expected_state") == args.expected_state
        ]

    if args.format == "json":
        print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    if isinstance(output, dict):
        print_claim(output)
        return 0

    if not output:
        print("no claims")
        return 0
    for claim in output:
        print(
            f"{claim.get('claim_ref')} "
            f"{claim.get('work_unit_id')} "
            f"{claim.get('expected_state')} "
            f"owner={claim.get('owner_session_ref')} "
            f"until={claim.get('expected_until')}"
        )
    return 0


def print_claim(claim: dict[str, Any]) -> None:
    fields = (
        "claim_ref",
        "work_unit_id",
        "work_card",
        "claim_type",
        "owner_session_ref",
        "expected_state",
        "expected_until",
        "last_claim",
        "last_seen_compaction_count",
        "assignment_packet",
        "evidence_ref",
        "operations_lead_decision_ref",
        "created_at",
        "updated_at",
    )
    for field in fields:
        print(f"{field}: {claim.get(field, '')}")


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help=f"JSON ledger path, default: {DEFAULT_LEDGER}",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help=f"Root containing <work-unit-id>/ source artifacts, default: {DEFAULT_ARTIFACT_ROOT}",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage OpenClaw Company Ops claim ledger JSON.")
    subparsers = parser.add_subparsers(dest="resource")

    claim = subparsers.add_parser("claim", help="Manage responsibility claims")
    claim_subparsers = claim.add_subparsers(dest="action")

    create = claim_subparsers.add_parser("create", help="Create a responsibility claim")
    add_common(create)
    create.add_argument("--claim-ref", type=claim_ref, help="Default: CLAIM-<work-unit-id>-001")
    create.add_argument("--work-unit-id", required=True, type=work_unit_id)
    create.add_argument("--work-card", required=True, type=required)
    create.add_argument("--claim-type", required=True, choices=CLAIM_TYPES)
    create.add_argument("--owner-session-ref", required=True, type=required)
    create.add_argument("--expected-state", required=True, choices=EXPECTED_STATES)
    create.add_argument("--expected-until", required=True, type=required)
    create.add_argument("--last-claim", required=True, type=required)
    create.add_argument("--last-seen-compaction-count", default="unknown", type=required)
    create.add_argument("--assignment-packet", required=True, type=required)
    create.add_argument("--evidence-ref", default="pending", type=required)
    create.add_argument("--operations-lead-decision-ref", default="pending", type=required)
    create.add_argument("--created-at", type=required)
    create.set_defaults(func=cmd_create)

    update = claim_subparsers.add_parser("update", help="Update an existing responsibility claim")
    add_common(update)
    update.add_argument("--claim-ref", required=True, type=claim_ref)
    update.add_argument("--work-card", type=required)
    update.add_argument("--owner-session-ref", type=required)
    update.add_argument("--expected-state", choices=EXPECTED_STATES)
    update.add_argument("--expected-until", type=required)
    update.add_argument("--last-claim", type=required)
    update.add_argument("--last-seen-compaction-count", type=required)
    update.add_argument("--assignment-packet", type=required)
    update.add_argument("--evidence-ref", type=required)
    update.add_argument("--operations-lead-decision-ref", type=required)
    update.add_argument("--updated-at", type=required)
    update.set_defaults(func=cmd_update)

    status = claim_subparsers.add_parser("status", help="Show claim status")
    add_common(status)
    status.add_argument("--claim-ref", type=claim_ref)
    status.add_argument("--expected-state", choices=EXPECTED_STATES)
    status.add_argument("--format", choices=("text", "json"), default="text")
    status.set_defaults(func=cmd_status)

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
