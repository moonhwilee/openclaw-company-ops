#!/usr/bin/env python3
"""Plan GitHub Project dashboard sync from Company Ops source artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
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
FIELD_FALLBACKS = {
    # GitHub's built-in Repository field is read-only through the Project item
    # mutation API, so sync our source repository string into the editable
    # project-specific field when it exists.
    "Repository": ("Source Repository",),
}
DEFAULT_AUDIT_LOG = Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"
DEFAULT_LOCK_FILE = Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync.lock"
PROJECT_SCOPE_HINT = "run: gh auth refresh -s project"
GITHUB_ISSUE_OR_PR_RE = re.compile(r"^https://github\.com/[^/\s]+/[^/\s]+/(?:issues|pull)/\d+(?:[?#].*)?$")


class ProjectSyncError(RuntimeError):
    """Expected project sync failure with a user-actionable message."""


class ProjectSyncLock:
    def __init__(self, path: Path | None):
        self.path = path.expanduser() if path else None
        self.fd: int | None = None

    def __enter__(self) -> "ProjectSyncLock":
        if self.path is None:
            return self
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ProjectSyncError(f"project sync already running: lock exists at {self.path}") from exc
        os.write(self.fd, f"{os.getpid()}\n".encode("utf-8"))
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        if self.path is not None:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


def required_work_unit(value: str) -> str:
    cleaned = value.strip()
    if not WORK_UNIT_RE.match(cleaned):
        raise argparse.ArgumentTypeError("expected Work Unit id starting with WU-")
    return cleaned


def normalize(value: str) -> str:
    return value.strip().lower().replace("_", " ").replace("-", " ")


def has_real_ref(value: str) -> bool:
    return bool(value and value != "pending")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_field_entry(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return {"id": value, "type": "text", "options": {}}
    if not isinstance(value, dict):
        raise ValueError("field map field entries must be strings or JSON objects")
    field_id = str(value.get("id") or value.get("field_id") or "")
    field_type = str(value.get("type") or value.get("data_type") or "text").strip().lower()
    if field_type in {"textarea", "string"}:
        field_type = "text"
    if field_type not in {"text", "single_select", "number", "date"}:
        raise ValueError(f"unsupported Project field type for {field_id or '<missing id>'}: {field_type}")
    options = value.get("options") or {}
    if not isinstance(options, dict):
        raise ValueError(f"field options must be a JSON object for {field_id or '<missing id>'}")
    return {
        "id": field_id,
        "type": field_type,
        "options": {str(key): str(option_id) for key, option_id in options.items()},
    }


def load_field_map(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "owner": "",
            "project_number": "",
            "project_id": "",
            "fields": {},
            "source": "unconfigured",
        }
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
    normalized_fields = {str(key): normalize_field_entry(value) for key, value in fields.items()}
    aliases = data.get("field_aliases") or {}
    if not isinstance(aliases, dict):
        raise ValueError(f"field map field_aliases must be a JSON object: {expanded}")
    return {
        "owner": str(data.get("owner") or data.get("project_owner") or ""),
        "project_number": str(data.get("project_number") or data.get("number") or ""),
        "project_id": str(data.get("project_id") or ""),
        "fields": normalized_fields,
        "field_aliases": {str(key): str(value) for key, value in aliases.items()},
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
                "field_id": mapped_fields.get(name, {}).get("id", ""),
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


def require_apply_field_map(field_map: dict[str, Any]) -> None:
    missing = []
    if not field_map["owner"]:
        missing.append("owner")
    if not field_map["project_number"]:
        missing.append("project_number")
    if not field_map["project_id"]:
        missing.append("project_id")
    missing.extend(field for field in DEFAULT_FIELDS if not field_map["fields"].get(field, {}).get("id"))
    if missing:
        raise ProjectSyncError("field map is not apply-ready; missing: " + ", ".join(missing))
    for name, entry in field_map["fields"].items():
        if name not in DEFAULT_FIELDS:
            continue
        if entry["type"] == "single_select":
            if not entry["options"]:
                raise ProjectSyncError(f"single_select field needs option ids in field map: {name}")


def require_applyable_work_cards(planned: list[dict[str, Any]]) -> None:
    bad_cards = [
        f"{item['work_unit_id']}={item['work_card'] or '<missing>'}"
        for item in planned
        if not GITHUB_ISSUE_OR_PR_RE.match(item["work_card"] or "")
    ]
    if bad_cards:
        raise ProjectSyncError(
            "apply requires GitHub issue or pull request Work Card URLs; invalid: " + ", ".join(bad_cards)
        )


def split_applyable_work_cards(planned: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    applyable: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for item in planned:
        work_card = item["work_card"] or ""
        if GITHUB_ISSUE_OR_PR_RE.match(work_card):
            applyable.append(item)
        else:
            skipped.append(
                {
                    "work_unit_id": item["work_unit_id"],
                    "work_card": work_card,
                    "reason": "non-GitHub Work Card is not Project-sync applyable",
                }
            )
    return applyable, skipped


def require_project_scope(gh_binary: str) -> None:
    result = subprocess.run([gh_binary, "auth", "status"], text=True, capture_output=True, check=False)
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        raise ProjectSyncError("GitHub auth is not ready for project sync")
    if "Token scopes:" not in output or "'project'" not in output:
        raise ProjectSyncError(f"GitHub auth lacks required 'project' scope; {PROJECT_SCOPE_HINT}")


def run_json_command(command: list[str], timeout: int) -> dict[str, Any]:
    result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=timeout)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ProjectSyncError(f"command failed: {' '.join(command[:4])}: {detail}")
    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise ProjectSyncError(f"command returned invalid JSON: {' '.join(command[:4])}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ProjectSyncError(f"command returned non-object JSON: {' '.join(command[:4])}")
    return parsed


def append_audit(path: Path, row: dict[str, Any]) -> None:
    expanded = path.expanduser()
    expanded.parent.mkdir(parents=True, exist_ok=True)
    with expanded.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def item_url(item: dict[str, Any]) -> str:
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    return str(content.get("url") or item.get("url") or "")


def item_id(item: dict[str, Any]) -> str:
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    return str(item.get("id") or item.get("item_id") or content.get("id") or "")


def list_project_items(args: argparse.Namespace, field_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parsed = run_json_command(
        [
            args.gh_binary,
            "project",
            "item-list",
            field_map["project_number"],
            "--owner",
            field_map["owner"],
            "--limit",
            str(args.item_limit),
            "--format",
            "json",
        ],
        args.timeout,
    )
    items = parsed.get("items") or []
    if not isinstance(items, list):
        raise ProjectSyncError("gh project item-list returned unexpected JSON shape")
    return {item_url(item): item for item in items if isinstance(item, dict) and item_url(item)}


def fetch_current_field_values(args: argparse.Namespace, item_node_id: str) -> dict[str, str]:
    query = """
query($itemId: ID!) {
  node(id: $itemId) {
    ... on ProjectV2Item {
      fieldValues(first: 100) {
        nodes {
          ... on ProjectV2ItemFieldTextValue {
            text
            field { ... on ProjectV2FieldCommon { name } }
          }
          ... on ProjectV2ItemFieldSingleSelectValue {
            name
            field { ... on ProjectV2FieldCommon { name } }
          }
          ... on ProjectV2ItemFieldNumberValue {
            number
            field { ... on ProjectV2FieldCommon { name } }
          }
          ... on ProjectV2ItemFieldDateValue {
            date
            field { ... on ProjectV2FieldCommon { name } }
          }
        }
      }
    }
  }
}
"""
    parsed = run_json_command(
        [args.gh_binary, "api", "graphql", "-f", f"query={query}", "-F", f"itemId={item_node_id}"],
        args.timeout,
    )
    nodes = (((parsed.get("data") or {}).get("node") or {}).get("fieldValues") or {}).get("nodes") or []
    current: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        field = node.get("field") if isinstance(node.get("field"), dict) else {}
        name = str(field.get("name") or "")
        if not name:
            continue
        if "text" in node:
            current[name] = str(node.get("text") or "")
        elif "name" in node:
            current[name] = str(node.get("name") or "")
        elif "number" in node:
            current[name] = str(node.get("number") or "")
        elif "date" in node:
            current[name] = str(node.get("date") or "")
    return current


def current_value_for_field(current_values: dict[str, str], field_map: dict[str, Any], field_name: str) -> str:
    alias = field_map.get("field_aliases", {}).get(field_name, "")
    if alias:
        return current_values.get(alias, current_values.get(field_name, ""))
    return current_values.get(field_name, "")


def add_project_item(args: argparse.Namespace, field_map: dict[str, Any], work_card: str) -> str:
    parsed = run_json_command(
        [
            args.gh_binary,
            "project",
            "item-add",
            field_map["project_number"],
            "--owner",
            field_map["owner"],
            "--url",
            work_card,
            "--format",
            "json",
        ],
        args.timeout,
    )
    item = parsed.get("item") if isinstance(parsed.get("item"), dict) else parsed
    node_id = item_id(item)
    if not node_id:
        raise ProjectSyncError("gh project item-add did not return an item id")
    return node_id


def edit_project_field(
    args: argparse.Namespace,
    field_map: dict[str, Any],
    item_node_id: str,
    field_name: str,
    field_entry: dict[str, Any],
    desired: str,
) -> None:
    command = [
        args.gh_binary,
        "project",
        "item-edit",
        "--id",
        item_node_id,
        "--project-id",
        field_map["project_id"],
        "--field-id",
        field_entry["id"],
        "--format",
        "json",
    ]
    if field_entry["type"] == "text":
        if desired:
            command.extend(["--text", desired])
        else:
            command.append("--clear")
    elif field_entry["type"] == "single_select":
        if not desired:
            command.append("--clear")
            run_json_command(command, args.timeout)
            return
        option_id = field_entry["options"].get(desired)
        if not option_id:
            raise ProjectSyncError(f"missing single_select option id for {field_name}={desired}")
        command.extend(["--single-select-option-id", option_id])
    elif field_entry["type"] == "number":
        if desired:
            command.extend(["--number", desired])
        else:
            command.append("--clear")
    elif field_entry["type"] == "date":
        if desired:
            command.extend(["--date", desired])
        else:
            command.append("--clear")
    else:
        raise ProjectSyncError(f"unsupported field type for {field_name}: {field_entry['type']}")
    run_json_command(command, args.timeout)


def field_entry_from_project_field(field: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(field.get("name") or "")
    raw_type = str(field.get("dataType") or field.get("type") or "TEXT").lower()
    field_type = "single_select" if "single" in raw_type else "text"
    options: dict[str, str] = {}
    for option in field.get("options") or []:
        if isinstance(option, dict) and option.get("name") and option.get("id"):
            options[str(option["name"])] = str(option["id"])
    return name, {"id": str(field.get("id") or ""), "type": field_type, "options": options}


def cmd_field_map(args: argparse.Namespace) -> int:
    try:
        require_project_scope(args.gh_binary)
        project = run_json_command(
            [
                args.gh_binary,
                "project",
                "view",
                str(args.project_number),
                "--owner",
                args.owner,
                "--format",
                "json",
            ],
            args.timeout,
        )
        fields_json = run_json_command(
            [
                args.gh_binary,
                "project",
                "field-list",
                str(args.project_number),
                "--owner",
                args.owner,
                "--limit",
                str(args.field_limit),
                "--format",
                "json",
            ],
            args.timeout,
        )
    except (subprocess.TimeoutExpired, ProjectSyncError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    project_id = str(project.get("id") or (project.get("project") or {}).get("id") or "")
    available = {}
    for field in fields_json.get("fields") or []:
        if not isinstance(field, dict):
            continue
        name, entry = field_entry_from_project_field(field)
        if name:
            available[name] = entry
    selected = {}
    aliases = {}
    for name in DEFAULT_FIELDS:
        for fallback in FIELD_FALLBACKS.get(name, ()):
            if fallback in available:
                selected[name] = available[fallback]
                aliases[name] = fallback
                break
        if name in selected:
            continue
        if name in available:
            selected[name] = available[name]
            continue
    output = {
        "owner": args.owner,
        "project_number": args.project_number,
        "project_id": project_id,
        "fields": selected,
        "missing_fields": [name for name in DEFAULT_FIELDS if name not in selected],
    }
    if aliases:
        output["field_aliases"] = aliases
    if args.output:
        destination = args.output.expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def apply_work_units(args: argparse.Namespace, plan: dict[str, Any], field_map: dict[str, Any]) -> dict[str, Any]:
    item_index = list_project_items(args, field_map)
    result: dict[str, Any] = {
        "mode": "apply",
        "project_mutation": True,
        "llm_calls": 0,
        "work_units": [],
        "summary": {"changed": 0, "unchanged": 0, "failed": 0, "skipped": 0},
        "skipped_work_units": [],
    }
    for item_plan in plan["work_units"]:
        work_card = item_plan["work_card"]
        existing = item_index.get(work_card)
        item_node_id = item_id(existing) if existing else ""
        item_changed = False
        actions: list[dict[str, str]] = []
        if item_node_id:
            current_values = fetch_current_field_values(args, item_node_id)
            actions.append({"type": "ensure_project_item", "result": "unchanged", "work_card": work_card})
        elif getattr(args, "skip_missing_project_items", False):
            result["summary"]["skipped"] += 1
            result["skipped_work_units"].append(
                {
                    "work_unit_id": item_plan["work_unit_id"],
                    "work_card": work_card,
                    "reason": "Project item is absent; reconcile updates existing dashboard items only",
                }
            )
            continue
        else:
            current_values = {}
            item_node_id = add_project_item(args, field_map, work_card)
            item_index[work_card] = {"id": item_node_id, "url": work_card}
            item_changed = True
            actions.append({"type": "ensure_project_item", "result": "changed", "work_card": work_card})

        for field_name in DEFAULT_FIELDS:
            desired = item_plan["desired_fields"].get(field_name, "")
            current = current_value_for_field(current_values, field_map, field_name)
            if current == desired:
                actions.append({"type": "set_project_field", "field": field_name, "result": "unchanged"})
                continue
            edit_project_field(args, field_map, item_node_id, field_name, field_map["fields"][field_name], desired)
            item_changed = True
            actions.append(
                {
                    "type": "set_project_field",
                    "field": field_name,
                    "result": "changed",
                    "current": current,
                    "desired": desired,
                }
            )

        status = "changed" if item_changed else "unchanged"
        result["summary"][status] += 1
        unit_result = {
            "work_unit_id": item_plan["work_unit_id"],
            "work_card": work_card,
            "project_item_id": item_node_id,
            "result": status,
            "actions": actions,
        }
        result["work_units"].append(unit_result)
        append_audit(
            args.audit_log,
            {
                "ts": utc_now_iso(),
                "mode": "apply",
                "work_unit_id": item_plan["work_unit_id"],
                "work_card": work_card,
                "project_item_id": item_node_id,
                "result": status,
                "changed_action_count": sum(1 for action in actions if action.get("result") == "changed"),
            },
        )
    return result


def build_plan(args: argparse.Namespace, field_map: dict[str, Any], mode: str, project_mutation: bool) -> dict[str, Any]:
    work_units = [args.work_unit_id] if args.work_unit_id else list_work_units(args.artifact_root)
    if not work_units:
        raise ProjectSyncError("no Work Unit artifacts found")

    planned = [plan_work_unit(args, work_unit_id, field_map) for work_unit_id in work_units]

    return {
        "mode": mode,
        "apply": project_mutation,
        "project_mutation": project_mutation,
        "llm_calls": 0,
        "project": {
            "owner": field_map["owner"],
            "project_number": field_map["project_number"],
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


def cmd_dry_run(args: argparse.Namespace) -> int:
    try:
        field_map = load_field_map(args.field_map)
        plan = build_plan(args, field_map, "dry-run", False)
    except (ValueError, ProjectSyncError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print_text(plan)
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    skipped: list[dict[str, str]] = []
    try:
        field_map = load_field_map(args.field_map)
        plan = build_plan(args, field_map, "apply", True)
        require_apply_field_map(field_map)
        if getattr(args, "skip_invalid_work_cards", False):
            plan["work_units"], skipped = split_applyable_work_cards(plan["work_units"])
            if not plan["work_units"]:
                raise ProjectSyncError("no applyable GitHub issue or pull request Work Cards found")
        else:
            require_applyable_work_cards(plan["work_units"])
        require_project_scope(args.gh_binary)
        with ProjectSyncLock(args.lock_file):
            result = apply_work_units(args, plan, field_map)
    except (subprocess.TimeoutExpired, ValueError, ProjectSyncError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if skipped:
        result["summary"]["skipped"] += len(skipped)
        result["skipped_work_units"].extend(skipped)
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(
            "Project sync apply complete: "
            f"changed={result['summary']['changed']} "
            f"unchanged={result['summary']['unchanged']} "
            f"audit_log={args.audit_log.expanduser()}"
        )
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    args.work_unit_id = None
    args.skip_invalid_work_cards = True
    args.skip_missing_project_items = True
    return cmd_apply(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan GitHub Project sync from source artifacts.")
    subparsers = parser.add_subparsers(dest="resource")

    project_sync = subparsers.add_parser("project-sync", help="Plan or apply Project dashboard sync")
    project_subparsers = project_sync.add_subparsers(dest="action")

    def add_source_args(command: argparse.ArgumentParser) -> None:
        command.add_argument("--work-unit-id", type=required_work_unit, help="Optional single Work Unit id")
        command.add_argument(
            "--artifact-root",
            type=Path,
            default=DEFAULT_ARTIFACT_ROOT,
            help=f"Root containing <work-unit-id>/ artifacts, default: {DEFAULT_ARTIFACT_ROOT}",
        )
        command.add_argument(
            "--ledger",
            type=Path,
            default=DEFAULT_LEDGER,
            help=f"Optional JSON ledger to read, default: {DEFAULT_LEDGER}",
        )
        command.add_argument("--no-ledger", action="store_const", const=None, dest="ledger")
        command.add_argument("--require-ledger", action="store_true")
        command.add_argument("--repository", default="moonhwilee/openclaw-company-ops")
        command.add_argument("--field-map", type=Path, help="Optional local JSON field-id map; never stores tokens")
        command.add_argument("--format", choices=("text", "json"), default="text")

    def add_apply_args(command: argparse.ArgumentParser) -> None:
        add_source_args(command)
        command.add_argument("--audit-log", type=Path, default=DEFAULT_AUDIT_LOG)
        command.add_argument("--lock-file", type=Path, default=DEFAULT_LOCK_FILE)
        command.add_argument("--no-lock", action="store_const", const=None, dest="lock_file")
        command.add_argument("--gh-binary", default="gh")
        command.add_argument("--timeout", type=int, default=30)
        command.add_argument("--item-limit", type=int, default=200)

    dry_run = project_subparsers.add_parser("dry-run", help="Show Project changes without mutation")
    add_source_args(dry_run)
    dry_run.set_defaults(func=cmd_dry_run)

    field_map = project_subparsers.add_parser("field-map", help="Generate a local field map from an existing Project")
    field_map.add_argument("--owner", required=True, help="Project owner login, or @me")
    field_map.add_argument("--project-number", required=True, type=int)
    field_map.add_argument("--output", type=Path, help="Optional local JSON output path")
    field_map.add_argument("--gh-binary", default="gh")
    field_map.add_argument("--timeout", type=int, default=30)
    field_map.add_argument("--field-limit", type=int, default=100)
    field_map.set_defaults(func=cmd_field_map)

    apply = project_subparsers.add_parser("apply", help="Apply changed Project item/field updates")
    add_apply_args(apply)
    apply.set_defaults(func=cmd_apply)

    reconcile = project_subparsers.add_parser("reconcile", help="Apply full safety-net reconcile over all Work Units")
    add_apply_args(reconcile)
    reconcile.set_defaults(func=cmd_reconcile)

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
