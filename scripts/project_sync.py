#!/usr/bin/env python3
"""Plan GitHub Project dashboard sync from Company Ops source artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from ops_claim_ledger import DEFAULT_LEDGER
from work_unit_status import DEFAULT_ARTIFACT_ROOT, build_summary


WORK_UNIT_RE = re.compile(r"^WU-[A-Za-z0-9][A-Za-z0-9-]*$")
DEFAULT_FIELDS = (
    "Work Unit id",
    "Repository",
    "Work Card",
    "Team Lead",
    "Status",
    "Phase",
    "Priority",
    "Blocker",
    "Evidence present",
    "Decision",
    "Last proof or last source update",
    "Assignment Packet reference",
    "Ops Claim Ledger reference",
    "Evidence & Result Record reference",
    "Operations Lead Decision reference",
)


def required_work_unit(value: str) -> str:
    cleaned = value.strip()
    if not WORK_UNIT_RE.match(cleaned):
        raise argparse.ArgumentTypeError("expected Work Unit id starting with WU-")
    return cleaned


def normalize(value: str) -> str:
    return value.strip().lower().replace("_", " ").replace("-", " ")


def has_real_ref(value: str) -> bool:
    return bool(value and value != "pending")


def load_field_map(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"project_id": "", "fields": {}, "source": "unconfigured"}
    expanded = path.expanduser()
    try:
        data = json.loads(expanded.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"field map is not valid JSON: {expanded}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"field map root must be a JSON object: {expanded}")
    fields = data.get("fields", {})
    if fields is None:
        fields = {}
    if not isinstance(fields, dict):
        raise ValueError(f"field map fields must be a JSON object: {expanded}")
    return {
        "project_id": str(data.get("project_id") or ""),
        "fields": {str(key): str(value) for key, value in fields.items()},
        "source": str(expanded),
    }


def list_work_units(root: Path) -> list[str]:
    expanded = root.expanduser()
    if not expanded.exists():
        return []
    return sorted(path.name for path in expanded.iterdir() if path.is_dir() and WORK_UNIT_RE.match(path.name))


def team_from_summary(summary: dict[str, Any]) -> str:
    assignment_fields = summary["artifacts"]["assignment.md"]["fields"]
    claim = summary["claim"]
    return (
        assignment_fields.get("assigned team lead openclaw agent")
        or claim.get("owner_session_ref", "").removeprefix("agent=")
        or "unknown"
    )


def decision_value(summary: dict[str, Any]) -> str:
    decision_fields = summary["artifacts"]["decision.md"]["fields"]
    raw_decision = decision_fields.get("decision", "")
    if raw_decision:
        return raw_decision.strip("`").strip()
    status = summary["decision"]["status"]
    return status or "pending"


def derive_status(summary: dict[str, Any]) -> tuple[str, str]:
    missing = set(summary["missing_artifacts"])
    claim_state = normalize(summary["claim"]["expected_state"])
    evidence_status = normalize(summary["evidence"]["status"])
    decision_status = normalize(summary["decision"]["status"])
    decision = normalize(decision_value(summary))

    if "assignment.md" in missing:
        return "Blocked", "missing Assignment Packet"
    if "claim.md" in missing:
        return "Blocked", "missing Ops Claim Ledger artifact"
    if claim_state == "blocked" or "blocked" in decision_status or decision == "blocked":
        return "Blocked", "source artifact records blocked state"
    if decision in {"accept", "accepted"} or decision_status == "accepted":
        return "Accepted", "Operations Lead decision accepted"
    if decision in {"revise", "revision"} or "revise" in decision_status:
        return "Revise", "Operations Lead decision requests revision"
    if "result ready" in evidence_status or claim_state == "result ready":
        return "Result Ready", "Evidence is ready for Operations Lead review"
    if claim_state in {"working", "waiting"}:
        return "In Progress", f"claim expected_state is {claim_state}"
    return "Assigned", "Assignment Packet exists"


def derive_blocker(summary: dict[str, Any], status: str, reason: str) -> str:
    if status == "Blocked":
        return reason
    if summary["audit_problems"]:
        return "; ".join(summary["audit_problems"])
    return ""


def desired_fields(summary: dict[str, Any], repository: str) -> dict[str, str]:
    status, reason = derive_status(summary)
    evidence = summary["evidence"]
    decision = summary["decision"]
    claim = summary["claim"]
    fields = {
        "Work Unit id": summary["work_unit_id"],
        "Repository": repository,
        "Work Card": summary["work_card"],
        "Team Lead": team_from_summary(summary),
        "Status": status,
        "Phase": "",
        "Priority": "",
        "Blocker": derive_blocker(summary, status, reason),
        "Evidence present": "yes" if evidence["exists"] and has_real_ref(evidence["ref"]) else "no",
        "Decision": decision_value(summary),
        "Last proof or last source update": summary["next_review"],
        "Assignment Packet reference": summary["assignment_packet"],
        "Ops Claim Ledger reference": claim["claim_ref"],
        "Evidence & Result Record reference": evidence["ref"],
        "Operations Lead Decision reference": decision["ref"],
    }
    return fields


def build_actions(fields: dict[str, str], field_map: dict[str, Any]) -> list[dict[str, str]]:
    mapped_fields = field_map["fields"]
    actions = [
        {
            "type": "ensure_project_item",
            "field": "",
            "field_id": "",
            "current": "unknown",
            "desired": fields.get("Work Card", ""),
            "reason": "dry-run Project item membership from source Work Card",
        }
    ]
    for name in DEFAULT_FIELDS:
        actions.append(
            {
                "type": "set_project_field",
                "field": name,
                "field_id": mapped_fields.get(name, ""),
                "current": "unknown",
                "desired": fields.get(name, ""),
                "reason": "dry-run desired state from source artifacts",
            }
        )
    return actions


def plan_work_unit(args: argparse.Namespace, work_unit_id: str, field_map: dict[str, Any]) -> dict[str, Any]:
    status_args = argparse.Namespace(
        artifact_root=args.artifact_root,
        work_unit_id=work_unit_id,
        ledger=args.ledger,
        require_ledger=args.require_ledger,
    )
    summary, return_code = build_summary(status_args)
    fields = desired_fields(summary, args.repository)
    missing_field_ids = [field for field in DEFAULT_FIELDS if field not in field_map["fields"]]
    return {
        "work_unit_id": work_unit_id,
        "work_card": summary["work_card"],
        "source_truth": {
            "artifact_dir": summary["artifact_dir"],
            "assignment_packet": summary["assignment_packet"],
            "claim_ref": summary["claim"]["claim_ref"],
            "evidence_ref": summary["evidence"]["ref"],
            "decision_ref": summary["decision"]["ref"],
        },
        "desired_fields": fields,
        "planned_actions": build_actions(fields, field_map),
        "audit_problems": summary["audit_problems"],
        "missing_artifacts": summary["missing_artifacts"],
        "mutation_ready": bool(field_map["project_id"]) and not missing_field_ids,
        "missing_field_ids": missing_field_ids,
        "source_status_return_code": return_code,
    }


def print_text(plan: dict[str, Any]) -> None:
    print("Project sync dry-run")
    print(f"Mode: {plan['mode']}")
    print(f"Project mutation: {str(plan['project_mutation']).lower()}")
    print(f"Project id: {plan['project']['project_id'] or 'unconfigured'}")
    for item in plan["work_units"]:
        print()
        print(f"Work Unit: {item['work_unit_id']}")
        print(f"Work Card: {item['work_card'] or 'missing'}")
        print(f"Desired Status: {item['desired_fields']['Status']}")
        print(f"Team Lead: {item['desired_fields']['Team Lead']}")
        print(f"Evidence present: {item['desired_fields']['Evidence present']}")
        print(f"Decision: {item['desired_fields']['Decision']}")
        print(f"Mutation ready: {str(item['mutation_ready']).lower()}")
        if item["audit_problems"]:
            print("Audit problems:")
            for problem in item["audit_problems"]:
                print(f"- {problem}")
        else:
            print("Audit problems: none")
        print(f"Planned actions: {len(item['planned_actions'])}")


def cmd_dry_run(args: argparse.Namespace) -> int:
    try:
        field_map = load_field_map(args.field_map)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    work_units = [args.work_unit_id] if args.work_unit_id else list_work_units(args.artifact_root)
    if not work_units:
        print("error: no Work Unit artifacts found", file=sys.stderr)
        return 1

    try:
        planned = [plan_work_unit(args, work_unit_id, field_map) for work_unit_id in work_units]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    plan = {
        "mode": "dry-run",
        "apply": False,
        "project_mutation": False,
        "llm_calls": 0,
        "project": {
            "project_id": field_map["project_id"],
            "field_map_source": field_map["source"],
            "configured_field_count": len(field_map["fields"]),
        },
        "work_units": planned,
        "summary": {
            "work_unit_count": len(planned),
            "mutation_ready_count": sum(1 for item in planned if item["mutation_ready"]),
            "audit_problem_count": sum(len(item["audit_problems"]) for item in planned),
        },
    }
    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print_text(plan)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan GitHub Project sync from source artifacts.")
    subparsers = parser.add_subparsers(dest="resource")

    project_sync = subparsers.add_parser("project-sync", help="Plan or apply Project dashboard sync")
    project_subparsers = project_sync.add_subparsers(dest="action")

    dry_run = project_subparsers.add_parser("dry-run", help="Show Project changes without mutation")
    dry_run.add_argument("--work-unit-id", type=required_work_unit, help="Optional single Work Unit id")
    dry_run.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help=f"Root containing <work-unit-id>/ artifacts, default: {DEFAULT_ARTIFACT_ROOT}",
    )
    dry_run.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help=f"Optional JSON ledger to read, default: {DEFAULT_LEDGER}",
    )
    dry_run.add_argument("--no-ledger", action="store_const", const=None, dest="ledger")
    dry_run.add_argument("--require-ledger", action="store_true")
    dry_run.add_argument("--repository", default="moonhwilee/openclaw-company-ops")
    dry_run.add_argument("--field-map", type=Path, help="Optional local JSON field-id map; never stores tokens")
    dry_run.add_argument("--format", choices=("text", "json"), default="text")
    dry_run.set_defaults(func=cmd_dry_run)

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
