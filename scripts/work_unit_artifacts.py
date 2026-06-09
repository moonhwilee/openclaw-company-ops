#!/usr/bin/env python3
"""Create the four required OpenClaw Company Ops Work Unit artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from progress_display import ROUND_VISIBLE_MODES, render_progress_display, should_show_round
from result_ready_gate import result_ready_gate


ARTIFACTS = ("assignment.md", "claim.md", "evidence.md", "decision.md")
WORK_UNIT_RE = re.compile(r"^WU-\d{6}-\d{3}$")
FIELD_RE = re.compile(r"^- ([^:]+):\s*(.*)$")
STATUS_RE = re.compile(r"^Status:\s*(.+)$", re.MULTILINE)
HANDOFF_MODE_CHOICES = {"goal", "verify"}
MUTATION_SURFACE_CHOICES = {"source", "project", "discord", "git", "external"}
PROJECT_SYNC_MODE_CHOICES = ("disabled", "required")
WORK_CARD_SUMMARY_MODE_CHOICES = ("disabled", "required")
GITHUB_WORK_CARD_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/(?:issues|pull)/(?P<number>\d+)(?:[?#].*)?$"
)
WORK_CARD_SUMMARY_MARKER_TEMPLATE = "<!-- company-ops-work-card-summary:{work_unit_id}:v1 -->"
WORK_CARD_SUMMARY_MIN_CHARS = 20
WORK_CARD_SUMMARY_MAX_CHARS = 700
WORK_CARD_SUMMARY_PLACEHOLDERS = {
    "summarize what was completed.",
    "summarize what was completed",
    "result summary",
    "n/a",
    "none",
    "todo",
    "tbd",
    "-",
}
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROOF_LOG_NAME = "visibility-proof.jsonl"
DEFAULT_ARTIFACT_ROOT = Path("docs/work-units")
DEFAULT_PROJECT_FIELD_MAP = Path("~/.openclaw/state/openclaw-company-ops/project-field-map.json")
DEFAULT_PROJECT_LEDGER = Path("~/.openclaw/state/openclaw-company-ops/claims/ledger.json")
DEFAULT_PROJECT_AUDIT_LOG = Path("~/.openclaw/state/openclaw-company-ops/project-sync-audit.jsonl")
DISPATCH_RUNTIME_CHOICES = ("record-ref", "openclaw-agent")
DISPATCH_ADAPTER_CHOICES = ("auto", "fake", "command")
DISPATCH_ADAPTER_COMMAND_ENV = "COMPANY_OPS_DISPATCH_ADAPTER_COMMAND"
CLOSEOUT_DELEGATE_RUNTIME_CHOICES = ("none", "openclaw-agent")
CLOSEOUT_DELEGATE_ADAPTER_CHOICES = ("auto", "fake", "command")
CLOSEOUT_DELEGATE_ADAPTER_COMMAND_ENV = "COMPANY_OPS_CLOSEOUT_DELEGATE_ADAPTER_COMMAND"
CLOSEOUT_DELEGATE_WAKE_FILENAME = "closeout-delegate-wake.json"
CLOSEOUT_DELEGATE_AUTHORITY_BOUNDARY = "closeout_delegate_guarded_closeout_only"
CLOSEOUT_DELEGATE_ALLOWED_AGENTS = ("main",)
CLOSEOUT_PUBLISH_AUTHORITY_ROLES = ("operations-lead", "operations-lead-delegate")
CLOSEOUT_DELEGATE_ACTIVE_CAP_DEFAULT = 2
CLOSEOUT_COMMIT_REQUEST_REQUIRED_HASHES = (
    "assignment.md",
    "claim.md",
    "evidence.md",
    "progress.jsonl",
    DEFAULT_PROOF_LOG_NAME,
    "result_ready_proof_rows",
)
CLOSEOUT_AUTONOMY_CLASSES = ("auto_eligible", "deep_review_auto_eligible", "manual_required")
CLOSEOUT_RED_LINE_CATEGORIES = (
    "security_credential_auth",
    "ops_deploy_db_migration",
    "cost_bearing",
    "destructive_action",
    "external_public_customer",
    "owner_intent_ambiguity",
    "evidence_missing_or_stale",
    "proof_or_hash_mismatch",
    "critical_disagreement",
    "unresolved_dependency",
)
DEFAULT_COMPANY_OPS_AGENT_COUNT = 5
DEFAULT_CAPACITY_RESERVED_SLOTS = 2
OPENCLAW_MAX_CONCURRENT_FLOOR = 8
OPENCLAW_SUBAGENTS_MAX_CONCURRENT_FLOOR = 16
OPENCLAW_MAX_CONCURRENT_PER_AGENT = 2
OPENCLAW_SUBAGENTS_MAX_CONCURRENT_PER_AGENT = 4
ACTIVE_WU_TERMINAL_STATES = {
    "accepted",
    "blocked",
    "blocked_detail",
    "completed",
    "done",
    "needs_revision",
    "result_ready",
    "revise",
    "revision_requested",
}
ACTIVE_WU_SOURCE_STATES = {"start", "started", "dispatch", "dispatched", "working"}
FINAL_REVIEW_KINDS = {"ACCEPTED", "REVISE", "BLOCKED_DETAIL"}
CLOSEOUT_BY_FINAL_REVIEW = {
    "ACCEPTED": "COMPLETED",
    "REVISE": "NEEDS_REVISION",
    "BLOCKED_DETAIL": "BLOCKED",
}
FINAL_REVIEW_BY_RECOMMENDATION = {
    "accept": "ACCEPTED",
    "accepted": "ACCEPTED",
    "revise": "REVISE",
    "revision": "REVISE",
    "blocked": "BLOCKED_DETAIL",
    "block": "BLOCKED_DETAIL",
}
FINAL_REVIEW_BY_DECISION = {
    "accept": "ACCEPTED",
    "revise": "REVISE",
    "blocked": "BLOCKED_DETAIL",
}
OWNER_CLOSEOUT_BY_DECISION = {
    "accept": "COMPLETED",
    "revise": "NEEDS_REVISION",
    "blocked": "BLOCKED",
}
DECISION_STATUS_BY_DECISION = {
    "accept": "Accepted",
    "revise": "Revise",
    "blocked": "Blocked",
}
AMENDMENT_SPEC_FIELDS = {
    "work_unit_id",
    "reason",
    "changed_fields",
    "proposed_updates",
    "source_refs",
    "requested_by",
}
DRAFT_HANDOFF_SPEC_FIELDS = {
    "work_unit_id",
    "title",
    "owner_request",
    "requested_by",
    "source_refs",
    "operations_lead",
    "team",
    "mode",
    "goal",
    "scope",
    "done_criteria",
    "verification_criteria",
    "targets",
    "target_paths",
    "work_card",
    "work_card_ref",
    "work_card_repo",
    "no_go",
    "next",
    "report",
    "created_at",
    "subagent_budget",
    "subagent_budget_reason",
    "mutation_authority",
    "mutation_allowed",
    "allowed_paths",
    "allowed_surfaces",
    "external_mutation_allowed",
    "commit_push_allowed",
}
STABLE_HANDOFF_FIELDS = {
    "work unit id",
    "work card",
    "operations lead",
    "assigned team lead openclaw agent",
    "mode",
    "created at",
}
SUBAGENT_BUDGET_CHOICES = {"none", "2", "3", "5"}


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


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def progress_row_from_args(
    args: argparse.Namespace,
    *,
    transition_at: str,
    proof_ref: str | None = None,
) -> dict[str, Any]:
    mode = args.mode.strip().lower()
    return {
        "work_unit_id": args.work_unit_id,
        "transition_kind": args.transition_kind,
        "mode": mode,
        "phase": args.phase,
        "phase_index": args.phase_index,
        "phase_total": args.phase_total,
        "round": args.round,
        "show_round": should_show_round(mode, bool(args.show_round)),
        "current_slice": args.current_slice,
        "risk_state": getattr(args, "risk_state", ""),
        "retry_state": getattr(args, "retry_state", ""),
        "next_checkpoint": args.next_checkpoint,
        "source_ref": args.source_ref,
        "proof_ref": proof_ref if proof_ref is not None else args.proof_ref,
        "transition_at": transition_at,
        "recorded_by": args.recorded_by,
    }


def validate_progress_metadata(row: dict[str, Any]) -> str:
    mode = normalized_state(row.get("mode"))
    if mode not in ROUND_VISIBLE_MODES:
        return ""
    if not str(row.get("round") or "").strip():
        return f"{mode} progress requires --round"
    if not str(row.get("phase_index") or "").strip():
        return f"{mode} progress requires --phase-index"
    return ""


def append_progress_row(output_dir: Path, row: dict[str, Any]) -> Path:
    progress_path = output_dir / "progress.jsonl"
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return progress_path


def run_json_command(command: list[str]) -> tuple[int, dict[str, Any], str]:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    parsed: dict[str, Any] = {}
    if result.stdout.strip():
        try:
            loaded = json.loads(result.stdout)
            if isinstance(loaded, dict):
                parsed = loaded
        except json.JSONDecodeError:
            parsed = {}
    return result.returncode, parsed, result.stderr.strip() or result.stdout.strip()


def run_json_stdin_command(command: list[str], payload: dict[str, Any], timeout_seconds: int) -> tuple[int, dict[str, Any], str]:
    try:
        result = subprocess.run(
            command,
            input=json.dumps(payload, sort_keys=True, ensure_ascii=False),
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, {}, f"runtime adapter timed out after {timeout_seconds}s: {' '.join(command)}"
    parsed: dict[str, Any] = {}
    if result.stdout.strip():
        try:
            loaded = json.loads(result.stdout)
            if isinstance(loaded, dict):
                parsed = loaded
        except json.JSONDecodeError:
            parsed = {}
    return result.returncode, parsed, result.stderr.strip() or result.stdout.strip()


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"input is not valid JSON: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"input root must be a JSON object: {path}")
    return loaded


def nested_config_value(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if re.fullmatch(r"-?\d+", cleaned):
            return int(cleaned)
    return None


def recommended_main_concurrency(agent_count: int) -> int:
    return max(OPENCLAW_MAX_CONCURRENT_FLOOR, agent_count * OPENCLAW_MAX_CONCURRENT_PER_AGENT)


def recommended_subagent_concurrency(agent_count: int) -> int:
    return max(
        OPENCLAW_SUBAGENTS_MAX_CONCURRENT_FLOOR,
        agent_count * OPENCLAW_SUBAGENTS_MAX_CONCURRENT_PER_AGENT,
    )


def active_wu_cap(max_concurrent: int, reserved_slots: int = DEFAULT_CAPACITY_RESERVED_SLOTS) -> int:
    return max(1, max_concurrent - reserved_slots)


def read_openclaw_config_value(path: str) -> tuple[int | None, str]:
    result = subprocess.run(
        ["openclaw", "config", "get", "--json", path],
        check=False,
        text=True,
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip() or f"openclaw config get failed: {path}"
    value = int_or_none(result.stdout.strip())
    if value is None:
        return None, f"openclaw config get returned non-integer for {path}: {result.stdout.strip()!r}"
    return value, ""


def openclaw_capacity_values(args: argparse.Namespace) -> tuple[int | None, int | None, list[str], str]:
    warnings: list[str] = []
    source = "openclaw-config"
    max_concurrent = int_or_none(getattr(args, "openclaw_max_concurrent", None))
    subagents_max = int_or_none(getattr(args, "openclaw_subagents_max_concurrent", None))
    config_json = getattr(args, "config_json", None)
    if config_json:
        source = str(config_json)
        try:
            config = read_json_file(config_json)
        except (OSError, ValueError) as exc:
            warnings.append(f"could not read config JSON: {exc}")
            config = {}
        if max_concurrent is None:
            max_concurrent = int_or_none(nested_config_value(config, "agents.defaults.maxConcurrent"))
        if subagents_max is None:
            subagents_max = int_or_none(nested_config_value(config, "agents.defaults.subagents.maxConcurrent"))
    if max_concurrent is None and not config_json:
        value, warning = read_openclaw_config_value("agents.defaults.maxConcurrent")
        max_concurrent = value
        if warning:
            warnings.append(warning)
    if subagents_max is None and not config_json:
        value, warning = read_openclaw_config_value("agents.defaults.subagents.maxConcurrent")
        subagents_max = value
        if warning:
            warnings.append(warning)
    return max_concurrent, subagents_max, warnings, source


def require_spec_text(spec: dict[str, Any], key: str) -> str:
    value = spec.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"handoff spec requires non-empty string: {key}")
    return value.strip()


def optional_spec_text(spec: dict[str, Any], key: str, default: str = "") -> str:
    value = spec.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"handoff spec field must be a string: {key}")
    return value.strip()


def spec_bool_value(value: Any, *, default: bool, key: str) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"true", "yes", "1", "on"}:
            return True
        if cleaned in {"false", "no", "0", "off", ""}:
            return False
    raise ValueError(f"handoff spec field must be boolean: {key}")


def normalize_handoff_mode(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("handoff spec requires non-empty string: mode")
    mode = value.strip().lower()
    if mode not in HANDOFF_MODE_CHOICES:
        raise ValueError("handoff spec mode must be one of: goal, verify")
    return mode


def normalize_subagent_budget(value: Any, default: str = "3") -> str:
    raw = default if value is None or value == "" else str(value).strip().lower()
    if raw in {"0", "no", "none", "unused"}:
        raw = "none"
    if raw not in SUBAGENT_BUDGET_CHOICES:
        raise ValueError("subagent_budget must be one of: none, 2, 3, 5")
    return raw


def normalize_subagent_budget_reason(value: Any, budget: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return {
        "none": "team_lead_direct",
        "2": "simple_delegated",
        "3": "normal",
        "5": "complex_high_risk",
    }[budget]


def spec_text_list(spec: dict[str, Any], key: str) -> list[str]:
    value = spec.get(key)
    if isinstance(value, str):
        items = [line.strip(" -") for line in value.splitlines()]
    elif isinstance(value, list):
        items = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"handoff spec list contains non-string item: {key}")
            items.append(item.strip())
    else:
        raise ValueError(f"handoff spec requires non-empty string or list: {key}")
    cleaned = [item for item in items if item]
    if not cleaned:
        raise ValueError(f"handoff spec requires at least one value: {key}")
    return cleaned


def optional_spec_text_list(spec: dict[str, Any], key: str) -> list[str]:
    if key not in spec or spec.get(key) is None:
        return []
    return spec_text_list(spec, key)


def spec_string_list_value(value: Any, *, key: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [line.strip(" -,") for line in value.splitlines()]
    elif isinstance(value, list):
        items = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"handoff spec list contains non-string item: {key}")
            items.append(item.strip())
    else:
        raise ValueError(f"handoff spec field must be string or list: {key}")
    return [item for item in items if item]


def is_verify_output_path(path: str, work_unit_id: str) -> bool:
    normalized = path.strip().strip("`").replace("\\", "/")
    work_unit_segment = f"/{work_unit_id}/"
    return (
        normalized.endswith(f"/{work_unit_id}/evidence.md")
        or normalized.endswith(f"/{work_unit_id}/verification.md")
        or f"{work_unit_segment}verification-artifacts/" in normalized
        or normalized.endswith(f"/{work_unit_id}/verification-artifacts")
        or f"{work_unit_segment}evidence-artifacts/" in normalized
        or normalized.endswith(f"/{work_unit_id}/evidence-artifacts")
    )


def normalize_mutation_authority(spec: dict[str, Any], mode: str) -> dict[str, Any]:
    raw = spec.get("mutation_authority")
    if raw is None:
        raw_authority: dict[str, Any] = {}
    elif isinstance(raw, dict):
        raw_authority = raw
    else:
        raise ValueError("handoff spec field must be an object: mutation_authority")

    mutation_allowed = spec_bool_value(
        spec.get("mutation_allowed", raw_authority.get("mutation_allowed")),
        default=False,
        key="mutation_allowed",
    )
    external_mutation_allowed = spec_bool_value(
        spec.get("external_mutation_allowed", raw_authority.get("external_mutation_allowed")),
        default=False,
        key="external_mutation_allowed",
    )
    commit_push_allowed = spec_bool_value(
        spec.get("commit_push_allowed", raw_authority.get("commit_push_allowed")),
        default=False,
        key="commit_push_allowed",
    )
    allowed_paths = spec_string_list_value(
        spec.get("allowed_paths", raw_authority.get("allowed_paths")),
        key="allowed_paths",
    )
    allowed_surfaces = [
        item.lower()
        for item in spec_string_list_value(
            spec.get("allowed_surfaces", raw_authority.get("allowed_surfaces")),
            key="allowed_surfaces",
        )
    ]
    unknown_surfaces = sorted(set(allowed_surfaces) - MUTATION_SURFACE_CHOICES)
    if unknown_surfaces:
        raise ValueError(f"handoff spec has unknown allowed_surfaces: {', '.join(unknown_surfaces)}")

    grants_mutation = (
        mutation_allowed
        or external_mutation_allowed
        or commit_push_allowed
        or bool(allowed_paths)
        or bool(allowed_surfaces)
    )
    if (external_mutation_allowed or commit_push_allowed or allowed_paths or allowed_surfaces) and not mutation_allowed:
        raise ValueError("allowed mutation scope requires mutation_allowed=true")
    if commit_push_allowed and "git" not in allowed_surfaces:
        raise ValueError("commit_push_allowed requires allowed_surfaces to include git")
    if external_mutation_allowed and not ({"project", "discord", "external"} & set(allowed_surfaces)):
        raise ValueError("external_mutation_allowed requires an external allowed surface")
    if mode == "verify" and grants_mutation:
        work_unit = optional_spec_text(spec, "work_unit_id")
        verify_output_only = (
            mutation_allowed
            and not external_mutation_allowed
            and not commit_push_allowed
            and set(allowed_surfaces) <= {"source"}
            and bool(allowed_paths)
            and all(is_verify_output_path(path, work_unit) for path in allowed_paths)
        )
        if not verify_output_only:
            raise ValueError(
                "verify mode can only write its own evidence.md, verification.md, "
                "verification-artifacts, or evidence-artifacts; "
                "it cannot mutate candidate outputs, git, Project, Discord, or external surfaces"
            )

    return {
        "mutation_allowed": mutation_allowed,
        "allowed_paths": allowed_paths,
        "allowed_surfaces": allowed_surfaces,
        "external_mutation_allowed": external_mutation_allowed,
        "commit_push_allowed": commit_push_allowed,
    }


def bool_yaml(value: bool) -> str:
    return "true" if value else "false"


def inline_yaml_list(items: list[str]) -> str:
    return json.dumps(items, ensure_ascii=False)


def human_list_or_none(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


def amendment_value_needs_decision(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "needs-ops-decision"}
    if isinstance(value, list):
        return not value or any(amendment_value_needs_decision(item) for item in value)
    if isinstance(value, dict):
        return not value or any(amendment_value_needs_decision(item) for item in value.values())
    return False


def markdown_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def clean_markdown_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == "`":
        return cleaned[1:-1].strip()
    return cleaned


def parse_markdown_source(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "status": "", "fields": {}, "text": ""}
    text = path.read_text(encoding="utf-8")
    status_match = STATUS_RE.search(text)
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if match:
            fields[match.group(1).strip().lower()] = clean_markdown_value(match.group(2))
    return {
        "exists": True,
        "path": str(path),
        "status": clean_markdown_value(status_match.group(1)) if status_match else "",
        "fields": fields,
        "text": text,
    }


def markdown_protocol_capsule_value(source: dict[str, Any], key: str) -> str:
    text = str(source.get("text") or "")
    for match in re.finditer(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE):
        value = clean_markdown_value(match.group(1))
        if value.startswith("<") and value.endswith(">"):
            continue
        return value
    return ""


def markdown_section(text: str, heading: str) -> str:
    heading_key = heading.strip().lower()
    lines = text.splitlines()
    capture = False
    captured: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            current = stripped.lstrip("#").strip().lower()
            if capture:
                break
            capture = current == heading_key
            continue
        if capture:
            captured.append(line.rstrip())
    return "\n".join(captured).strip()


def compact_summary_text(value: str, *, limit: int = WORK_CARD_SUMMARY_MAX_CHARS) -> str:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    cleaned = " ".join(lines).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    home = str(Path.home())
    if home and home in cleaned:
        cleaned = cleaned.replace(home, "~")
    token_patterns = (
        r"ghp_[A-Za-z0-9_]+",
        r"github_pat_[A-Za-z0-9_]+",
        r"sk-[A-Za-z0-9_-]+",
    )
    for pattern in token_patterns:
        cleaned = re.sub(pattern, "[redacted]", cleaned)
    if len(cleaned) > limit:
        return cleaned[: max(0, limit - 1)].rstrip() + "…"
    return cleaned


def low_information_summary(value: str) -> bool:
    cleaned = compact_summary_text(value, limit=10_000).strip()
    lowered = cleaned.lower()
    if len(cleaned) < WORK_CARD_SUMMARY_MIN_CHARS:
        return True
    if lowered in WORK_CARD_SUMMARY_PLACEHOLDERS:
        return True
    if lowered.startswith("summarize ") or lowered.startswith("todo"):
        return True
    return False


def github_work_card_parts(work_card: str) -> dict[str, str]:
    match = GITHUB_WORK_CARD_RE.match(work_card.strip())
    if not match:
        return {}
    return match.groupdict()


def safe_source_artifact_ref(value: str | Path, *, work_unit_id: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if re.match(r"^[a-z][a-z0-9+.-]*://", raw, flags=re.IGNORECASE):
        return raw
    path = Path(raw).expanduser()
    repo_root = Path.cwd().resolve()
    candidates = [path]
    if not path.is_absolute():
        candidates.append(repo_root / path)
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=False)
            return resolved.relative_to(repo_root).as_posix()
        except ValueError:
            continue
    if path.name in ARTIFACTS or path.name in {DEFAULT_PROOF_LOG_NAME, "progress.jsonl"}:
        return (DEFAULT_ARTIFACT_ROOT / work_unit_id / path.name).as_posix()
    parts = path.parts
    if "docs" in parts:
        docs_index = parts.index("docs")
        return Path(*parts[docs_index:]).as_posix()
    for index, part in enumerate(parts):
        if WORK_UNIT_RE.match(part):
            return (DEFAULT_ARTIFACT_ROOT / Path(*parts[index:])).as_posix()
    return path.name or raw


def source_field_value(
    sources: list[tuple[str, dict[str, Any]]],
    field: str,
) -> tuple[str, str]:
    normalized_field = field.strip().lower()
    for source_name, source in sources:
        value = clean_markdown_value(str(source.get("fields", {}).get(normalized_field, "") or ""))
        if value:
            return value, source_name
    return "", ""


def parse_timestamp(value: str) -> dt.datetime:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("missing timestamp")
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def read_jsonl_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], [f"proof log missing: {path}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            loaded = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"{path}:{index}: invalid JSON: {exc}")
            continue
        if not isinstance(loaded, dict):
            warnings.append(f"{path}:{index}: proof row is not an object")
            continue
        rows.append(loaded)
    return rows, warnings


def proof_rows_for_work_unit(path: Path, work_unit: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows, warnings = read_jsonl_rows(path)
    filtered = [row for row in rows if str(row.get("work_unit_id") or "") == work_unit]
    for row in filtered:
        if row.get("dry_run"):
            warnings.append("dry-run proof row ignored for result-ready inbox")
        for field in ("transition_at", "discord_timestamp", "readback_at"):
            value = str(row.get(field) or "")
            if value:
                try:
                    parse_timestamp(value)
                except ValueError:
                    warnings.append(f"malformed proof timestamp {field}={value!r}")
    return [row for row in filtered if not row.get("dry_run")], warnings


def local_source_ref_exists(source_ref: str, artifact_dir: Path) -> bool:
    cleaned = source_ref.strip()
    if not cleaned or "://" in cleaned or cleaned.startswith("#"):
        return True
    path = Path(cleaned).expanduser()
    if path.is_absolute():
        return path.exists()
    repo_root = SCRIPT_DIR.parent
    return (repo_root / path).exists() or (artifact_dir / path).exists()


def assignment_requires_live_visibility(assignment: dict[str, Any]) -> bool:
    for field in ("execution route", "execution route for this work unit"):
        route = clean_markdown_value(str(assignment.get("fields", {}).get(field) or "")).strip().lower().rstrip(".")
        if route:
            return route == "discord-bound"
    return False


def canonical_json_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def result_ready_proof_rows(proof_path: Path, work_unit: str) -> list[dict[str, Any]]:
    rows, _warnings = proof_rows_for_work_unit(proof_path, work_unit)
    return [
        row
        for row in rows
        if row.get("surface") == "team-detail"
        and row.get("kind") == "RESULT_READY"
        and row.get("readback_ok") is not False
    ]


def closeout_delegate_session_key(work_unit_id: str) -> str:
    return f"company-ops-closeout-delegate-{work_unit_id.lower()}"


def artifact_hashes_for_closeout_delegate(artifact_dir: Path, work_unit_id: str) -> dict[str, Any]:
    proof_path = artifact_dir / DEFAULT_PROOF_LOG_NAME
    proof_rows = result_ready_proof_rows(proof_path, work_unit_id)
    return {
        "assignment.md": file_sha256(artifact_dir / "assignment.md"),
        "claim.md": file_sha256(artifact_dir / "claim.md"),
        "evidence.md": file_sha256(artifact_dir / "evidence.md"),
        "progress.jsonl": file_sha256(artifact_dir / "progress.jsonl"),
        DEFAULT_PROOF_LOG_NAME: file_sha256(proof_path),
        "result_ready_proof_rows": [canonical_json_hash(row) for row in proof_rows],
    }


def guarded_closeout_contract(
    work_unit_id: str,
    *,
    artifact_root: Path,
    team_target: str,
    ops_target: str,
    project_sync_field_map: str,
    project_sync_ledger: str,
    project_sync_audit_log: str,
) -> dict[str, str]:
    project_field_map = project_sync_field_map or str(DEFAULT_PROJECT_FIELD_MAP)
    project_ledger = project_sync_ledger or str(DEFAULT_PROJECT_LEDGER)
    project_audit_log = project_sync_audit_log or str(DEFAULT_PROJECT_AUDIT_LOG)
    return {
        "command": (
            "python3 scripts/openclaw_company_ops.py work-unit closeout "
            f"--work-unit-id {work_unit_id} --artifact-root {artifact_root} "
            "--commit-request <json> --authority-role operations-lead-delegate "
            f"--team-target {team_target} --ops-target {ops_target} "
            "--channel discord --account default "
            "--project-sync-mode required "
            f"--project-sync-field-map {project_field_map} "
            f"--project-sync-ledger {project_ledger} "
            f"--project-sync-audit-log {project_audit_log} "
            "--publish"
        ),
        "rule": "Fresh OL delegate may judge and publish only through guarded closeout.",
    }


def closeout_red_line_template() -> dict[str, str]:
    return {"status": "clear", **{category: "clear" for category in CLOSEOUT_RED_LINE_CATEGORIES}}


def closeout_commit_request_template(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "work_unit_id": packet.get("work_unit_id"),
        "decision": "accept|revise|blocked",
        "reason": "<delegated OL audit rationale>",
        "source_ref": packet.get("refs", {}).get("source_ref"),
        "result_ready_proof_id": packet.get("result_ready", {}).get("proof_id"),
        "artifact_hashes": packet.get("artifact_hashes"),
        "delegate_session_ref": packet.get("delegate", {}).get("session_key")
        if isinstance(packet.get("delegate"), dict)
        else "",
        "delegate_job_ref": f"{packet.get('work_unit_id')}:closeout-delegate",
        "delegate_message_ref": "<delegate-message-or-run-ref>",
        "autonomy_class": "auto_eligible|deep_review_auto_eligible|manual_required",
        "review_depth": "<source/proof/hash/criteria review depth>",
        "red_line_check": closeout_red_line_template(),
    }


def progress_has_transition(progress_path: Path, work_unit: str, transition_kinds: set[str]) -> bool:
    if not progress_path.exists():
        return False
    for line in progress_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        row_work_unit = str(row.get("work_unit_id") or "")
        if row_work_unit and row_work_unit != work_unit:
            continue
        if normalized_state(str(row.get("transition_kind") or "")) in transition_kinds:
            return True
    return False


def proof_has_event(proof_path: Path, work_unit: str, kind: str) -> bool:
    rows, _warnings = proof_rows_for_work_unit(proof_path, work_unit)
    return any(
        row.get("surface") == "team-detail"
        and row.get("kind") == kind
        and row.get("readback_ok") is not False
        for row in rows
    )


def latest_visibility_target(artifact_dir: Path, work_unit: str, surface: str, fallback: str) -> str:
    proof_log = artifact_dir / DEFAULT_PROOF_LOG_NAME
    proof_rows, _warnings = proof_rows_for_work_unit(proof_log, work_unit)
    for row in reversed(proof_rows):
        if row.get("surface") == surface and row.get("target") and row.get("readback_ok") is not False:
            return str(row["target"])
    return fallback


def build_closeout_delegate_payload(
    args: argparse.Namespace,
    item: dict[str, Any],
    artifact_dir: Path,
    *,
    transition_at: str,
) -> dict[str, Any]:
    session_key = args.closeout_delegate_session_key or closeout_delegate_session_key(args.work_unit_id)
    args.closeout_delegate_session_key = session_key
    source_ref = args.source_ref or item["evidence_path"]
    team_target = latest_visibility_target(artifact_dir, args.work_unit_id, "team-detail", "<team-detail-target>")
    ops_target = latest_visibility_target(artifact_dir, args.work_unit_id, "ops-feed", "<ops-feed-target>")
    payload = {
        "protocol": "company_ops_closeout_delegate_wake_v1",
        "work_unit_id": args.work_unit_id,
        "title": item["title"],
        "team": args.team or item["team"],
        "artifact_root": str(args.artifact_root.expanduser()),
        "artifact_dir": str(artifact_dir),
        "work_card": item["work_card"],
        "refs": {
            "assignment": str(artifact_dir / "assignment.md"),
            "claim": str(artifact_dir / "claim.md"),
            "evidence": str(artifact_dir / "evidence.md"),
            "decision": str(artifact_dir / "decision.md"),
            "progress": str(artifact_dir / "progress.jsonl"),
            "visibility_proof": str(artifact_dir / DEFAULT_PROOF_LOG_NAME),
            "source_ref": source_ref,
        },
        "result_ready": {
            "proof_id": item["result_ready_source"].split("#", 1)[1] if "#" in item["result_ready_source"] else "",
            "proof_ref": item["result_ready_source"],
            "published_at": item["result_ready_at"],
            "source_ref": source_ref,
        },
        "artifact_hashes": artifact_hashes_for_closeout_delegate(artifact_dir, args.work_unit_id),
        "delegate": {
            "agent": args.closeout_delegate_agent,
            "session_key": session_key,
            "runtime": args.closeout_delegate_runtime,
            "authority_role": "operations-lead-delegate",
            "allowed_agents": list(CLOSEOUT_DELEGATE_ALLOWED_AGENTS),
        },
        "targets": {
            "team_detail": team_target,
            "ops_feed": ops_target,
        },
        "guarded_closeout_contract": guarded_closeout_contract(
            args.work_unit_id,
            artifact_root=args.artifact_root,
            team_target=team_target,
            ops_target=ops_target,
            project_sync_field_map=getattr(args, "project_sync_field_map", ""),
            project_sync_ledger=getattr(args, "project_sync_ledger", ""),
            project_sync_audit_log=getattr(args, "project_sync_audit_log", ""),
        ),
        "authority_boundary": CLOSEOUT_DELEGATE_AUTHORITY_BOUNDARY,
        "autonomy_classes": ["auto_eligible", "deep_review_auto_eligible", "manual_required"],
        "red_line_categories": list(CLOSEOUT_RED_LINE_CATEGORIES),
        "commit_request_template": {},
        "no_go_actions": [
            "Do not write decision.md directly.",
            "Do not mutate Project final status directly.",
            "Do not archive, reassign, or reverse-import external mirror state.",
            "Use guarded closeout for any final decision, final Discord review, owner completion, or Project final mirror update.",
        ],
        "created_at": transition_at,
    }
    payload["commit_request_template"] = closeout_commit_request_template(payload)
    return payload


def closeout_delegate_payload_hash(payload: dict[str, Any]) -> str:
    return canonical_json_hash(payload)


def closeout_delegate_adapter_command(args: argparse.Namespace) -> str:
    return args.closeout_delegate_adapter_command.strip() or os.environ.get(
        CLOSEOUT_DELEGATE_ADAPTER_COMMAND_ENV,
        "",
    ).strip()


def fake_closeout_delegate_acceptance(args: argparse.Namespace, payload: dict[str, Any], accepted_at: str) -> dict[str, Any]:
    payload_hash = closeout_delegate_payload_hash(payload)
    return {
        "status": "accepted",
        "adapter": "fake-closeout-delegate",
        "adapter_version": 1,
        "agent": args.closeout_delegate_agent,
        "session_key": args.closeout_delegate_session_key,
        "session_ref": f"session:{args.closeout_delegate_session_key}",
        "job_ref": f"job:{args.work_unit_id}:closeout-delegate",
        "message_ref": f"message:{args.work_unit_id}:closeout-delegate-accepted",
        "accepted_at": accepted_at,
        "readback": {
            "work_unit_id": args.work_unit_id,
            "closeout_delegate_payload_hash": payload_hash,
            "guarded_closeout_contract": payload["guarded_closeout_contract"]["command"],
            "authority_boundary": CLOSEOUT_DELEGATE_AUTHORITY_BOUNDARY,
        },
    }


def validate_closeout_delegate_acceptance(args: argparse.Namespace, payload: dict[str, Any], proof: dict[str, Any]) -> str:
    if not proof:
        return "closeout delegate adapter did not return JSON acceptance proof"
    candidate = proof.get("result") if isinstance(proof.get("result"), dict) else proof
    if not isinstance(candidate, dict):
        return "closeout delegate acceptance proof must be a JSON object"
    if str(candidate.get("status", "")).strip().lower() != "accepted":
        return "closeout delegate adapter did not return status=accepted"
    readback = candidate.get("readback") if isinstance(candidate.get("readback"), dict) else {}
    if (readback.get("work_unit_id") or candidate.get("work_unit_id")) != args.work_unit_id:
        return "closeout delegate accepted proof has mismatched work_unit_id"
    expected_hash = closeout_delegate_payload_hash(payload)
    if (readback.get("closeout_delegate_payload_hash") or candidate.get("closeout_delegate_payload_hash")) != expected_hash:
        return "closeout delegate accepted proof has mismatched payload hash"
    expected_contract = payload["guarded_closeout_contract"]["command"]
    if (readback.get("guarded_closeout_contract") or candidate.get("guarded_closeout_contract")) != expected_contract:
        return "closeout delegate accepted proof did not confirm guarded closeout contract"
    if (readback.get("authority_boundary") or candidate.get("authority_boundary")) != CLOSEOUT_DELEGATE_AUTHORITY_BOUNDARY:
        return "closeout delegate accepted proof did not confirm authority boundary"
    if not candidate.get("job_ref"):
        return "closeout delegate accepted proof did not return an execution enqueue reference"
    if not (candidate.get("session_ref") or candidate.get("message_ref")):
        return "closeout delegate accepted proof did not return a recoverable acceptance reference"
    return ""


def apply_closeout_delegate_acceptance(args: argparse.Namespace, proof: dict[str, Any]) -> dict[str, Any]:
    candidate = proof.get("result") if isinstance(proof.get("result"), dict) else proof
    assert isinstance(candidate, dict)
    for field in ("session_ref", "job_ref", "message_ref"):
        target_attr = f"closeout_delegate_{field}"
        if not getattr(args, target_attr, "") and isinstance(candidate.get(field), str):
            setattr(args, target_attr, candidate[field].strip())
    return compact_acceptance(candidate)


def run_closeout_delegate_adapter(
    args: argparse.Namespace,
    *,
    payload: dict[str, Any],
    artifact_dir: Path,
    transition_at: str,
) -> tuple[dict[str, Any] | None, str]:
    adapter = args.closeout_delegate_adapter
    command_text = closeout_delegate_adapter_command(args)
    if adapter == "auto":
        adapter = "command" if command_text else ""
    if not adapter:
        return None, (
            "automatic closeout delegate adapter is not configured; configure "
            f"{CLOSEOUT_DELEGATE_ADAPTER_COMMAND_ENV} or pass --closeout-delegate-adapter-command"
        )
    if adapter == "fake":
        proof = fake_closeout_delegate_acceptance(args, payload, transition_at)
        reason = validate_closeout_delegate_acceptance(args, payload, proof)
        return (proof, "" if not reason else reason)
    if adapter == "command":
        if not command_text:
            return None, f"--closeout-delegate-adapter command requires --closeout-delegate-adapter-command or {CLOSEOUT_DELEGATE_ADAPTER_COMMAND_ENV}"
        command = shlex.split(command_text)
        if not command:
            return None, "closeout delegate adapter command is empty"
        request = {
            "adapter_protocol": "company_ops_closeout_delegate_adapter_v1",
            "work_unit_id": args.work_unit_id,
            "agent": args.closeout_delegate_agent,
            "runtime": args.closeout_delegate_runtime,
            "session_key": args.closeout_delegate_session_key,
            "artifact_dir": str(artifact_dir),
            "transition_at": transition_at,
            "packet": payload,
            "required_acceptance": {
                "work_unit_id": args.work_unit_id,
                "closeout_delegate_payload_hash": closeout_delegate_payload_hash(payload),
                "guarded_closeout_contract": payload["guarded_closeout_contract"]["command"],
                "authority_boundary": CLOSEOUT_DELEGATE_AUTHORITY_BOUNDARY,
            },
        }
        returncode, proof, output = run_json_stdin_command(
            command,
            request,
            args.closeout_delegate_adapter_timeout_seconds,
        )
        if returncode != 0:
            return None, f"closeout delegate adapter command failed ({returncode}): {output}"
        reason = validate_closeout_delegate_acceptance(args, payload, proof)
        return (proof, "" if not reason else reason)
    return None, f"unsupported closeout delegate adapter: {adapter}"


def closeout_delegate_ref(args: argparse.Namespace) -> str:
    return args.closeout_delegate_job_ref or args.closeout_delegate_session_ref or args.closeout_delegate_message_ref


def closeout_delegate_setup_needed_payload(args: argparse.Namespace, reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "dry_run": bool(args.dry_run),
        "status": "delegate-wake setup-needed",
        "work_unit_id": args.work_unit_id,
        "runtime": args.closeout_delegate_runtime,
        "adapter": args.closeout_delegate_adapter,
        "reason": reason,
        "delegate_payload": payload,
        "delegate_payload_hash": closeout_delegate_payload_hash(payload),
        "would_write_delegate_wake": False,
        "would_mutate_decision": False,
        "would_mutate_project_final": False,
        "next_action": "Recover through work-unit inbox --result-ready, then rerun the foreground delegate-wake path.",
    }


def closeout_delegate_capacity(artifact_root: Path, current_work_unit_id: str = "") -> dict[str, Any]:
    active: list[str] = []
    for work_unit in iter_work_unit_ids(artifact_root):
        artifact_dir = artifact_root / work_unit
        if work_unit != current_work_unit_id and (artifact_dir / "decision.md").exists():
            try:
                item = build_work_unit_readiness(artifact_root, work_unit)
            except Exception:
                item = {}
            if item.get("decision_final"):
                continue
        wake_path = artifact_dir / CLOSEOUT_DELEGATE_WAKE_FILENAME
        if not wake_path.exists():
            continue
        try:
            wake = json.loads(wake_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(wake, dict) and str(wake.get("status") or "") == "delegate-wake-enqueued":
            active.append(work_unit)
    return {
        "active_count": len(active),
        "active_work_units": active,
        "current_active": current_work_unit_id in active,
        "other_active_count": len([work_unit for work_unit in active if work_unit != current_work_unit_id]),
    }


def closeout_delegate_capacity_failure(args: argparse.Namespace, artifact_root: Path) -> dict[str, Any] | None:
    cap = getattr(args, "closeout_delegate_active_cap", CLOSEOUT_DELEGATE_ACTIVE_CAP_DEFAULT)
    if cap < 1:
        return {
            "enabled": True,
            "status": "delegate-wake setup-needed",
            "reason": "--closeout-delegate-active-cap must be >= 1",
        }
    capacity = closeout_delegate_capacity(artifact_root, args.work_unit_id)
    if capacity["other_active_count"] >= cap and not capacity["current_active"]:
        return {
            "enabled": True,
            "status": "delegate-wake capacity-full",
            "work_unit_id": args.work_unit_id,
            "capacity": {
                **capacity,
                "closeout_delegate_active_cap": cap,
            },
            "reason": (
                "closeout delegate active cap reached "
                f"({capacity['other_active_count']} active other delegate wakes, cap {cap})"
            ),
            "would_write_delegate_wake": False,
            "would_mutate_decision": False,
            "would_mutate_project_final": False,
            "next_action": "Leave the WU in result-ready inbox and retry foreground delegate-wake after a delegate closes or escalates.",
        }
    return None


def closeout_delegate_wake_record(
    args: argparse.Namespace,
    payload: dict[str, Any],
    accepted_proof: dict[str, Any],
    transition_at: str,
) -> dict[str, Any]:
    return {
        "version": 1,
        "status": "delegate-wake-enqueued",
        "work_unit_id": args.work_unit_id,
        "delegate_payload_hash": closeout_delegate_payload_hash(payload),
        "delegate_agent": args.closeout_delegate_agent,
        "delegate_runtime": args.closeout_delegate_runtime,
        "delegate_session_key": args.closeout_delegate_session_key,
        "delegate_authority_role": "operations-lead-delegate",
        "session_ref": args.closeout_delegate_session_ref,
        "job_ref": args.closeout_delegate_job_ref,
        "message_ref": args.closeout_delegate_message_ref,
        "accepted_proof": accepted_proof,
        "payload": payload,
        "enqueued_at": transition_at,
        "recorded_by": getattr(args, "recorded_by", "team-lead-result-ready"),
    }


def latest_progress_timestamp(path: Path, work_unit: str, artifact_dir: Path) -> tuple[str, list[str], list[str]]:
    if not path.exists():
        return "", [], []
    latest = ""
    warnings: list[str] = []
    missing_source_refs: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"{path}:{index}: invalid progress JSON: {exc}")
            continue
        if not isinstance(row, dict):
            warnings.append(f"{path}:{index}: progress row is not an object")
            continue
        row_work_unit = str(row.get("work_unit_id") or "")
        if row_work_unit and row_work_unit != work_unit:
            continue
        timestamp = str(row.get("transition_at") or row.get("updated_at") or "")
        if timestamp:
            latest = timestamp
        source_ref = str(row.get("source_ref") or "")
        if source_ref and not local_source_ref_exists(source_ref, artifact_dir):
            missing_source_refs.append(f"{path}:{index}: missing source_ref: {source_ref}")
    return latest, warnings, missing_source_refs


def first_result_ready_time(proof_rows: list[dict[str, Any]]) -> tuple[str, str]:
    candidates: list[tuple[dt.datetime, str, str]] = []
    for row in proof_rows:
        if row.get("surface") != "team-detail" or row.get("kind") != "RESULT_READY":
            continue
        raw_time = str(row.get("discord_timestamp") or row.get("transition_at") or row.get("readback_at") or "")
        try:
            candidates.append((parse_timestamp(raw_time), raw_time, str(row.get("proof_id") or row.get("card_id") or "")))
        except ValueError:
            continue
    if not candidates:
        return "", ""
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1], candidates[0][2]


def final_review_kinds(proof_rows: list[dict[str, Any]]) -> list[str]:
    return [
        str(row.get("kind"))
        for row in proof_rows
        if row.get("surface") == "team-detail" and str(row.get("kind")) in FINAL_REVIEW_KINDS
        and row.get("readback_ok") is not False
    ]


def owner_closeout_kinds(proof_rows: list[dict[str, Any]]) -> list[str]:
    return [
        str(row.get("kind"))
        for row in proof_rows
        if row.get("surface") == "ops-feed" and str(row.get("kind")) in set(CLOSEOUT_BY_FINAL_REVIEW.values())
        and row.get("readback_ok") is not False
    ]


def normalized_state(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def is_result_ready(claim_state: str, evidence_status: str) -> bool:
    return normalized_state(claim_state) == "result_ready" or normalized_state(evidence_status) == "result_ready"


def result_ready_blockers(
    claim_state: str,
    evidence: dict[str, Any],
    missing_progress_source_refs: list[str],
) -> list[str]:
    blockers: list[str] = []
    claim_is_ready = normalized_state(claim_state) == "result_ready"
    evidence_status = normalized_state(str(evidence.get("status") or ""))
    if claim_is_ready:
        if not evidence.get("exists"):
            blockers.append("claim result_ready but evidence.md is missing")
        elif evidence_status in {"", "draft", "pending"}:
            blockers.append(f"claim result_ready but evidence status is {evidence.get('status') or 'missing'}")
    if missing_progress_source_refs:
        blockers.extend(missing_progress_source_refs)
    return blockers


def source_ref_failures_for_row(output_dir: Path, row: dict[str, Any]) -> list[dict[str, str]]:
    source_ref = str(row.get("source_ref") or "")
    if not source_ref or local_source_ref_exists(source_ref, output_dir):
        return []
    return [
        {
            "class": "repairable",
            "path": str(output_dir / "progress.jsonl"),
            "field": "progress.source_ref",
            "message": f"missing source_ref: {source_ref}",
            "repair_hint": "Point source_ref at an existing local source artifact before appending progress.",
        }
    ]


def print_gate_failure(prefix: str, gate: dict[str, Any]) -> None:
    failures = gate.get("failures") or []
    print(f"error: {prefix}: {gate.get('status') or 'repair-needed'}", file=sys.stderr)
    for failure in failures:
        print(
            "  - "
            f"{failure.get('class')}: {failure.get('field')}: {failure.get('message')} "
            f"({failure.get('repair_hint')})",
            file=sys.stderr,
        )


def replace_markdown_field(text: str, field: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(rf"^- {re.escape(field)}:\s*.*$", re.MULTILINE)
    replacement = f"- {field}: {value}"
    updated, count = pattern.subn(replacement, text, count=1)
    return updated, count > 0


def render_started_claim_text(claim_path: Path, *, team: str, transition_at: str, source_ref: str) -> str:
    if not claim_path.exists():
        raise FileNotFoundError(f"claim.md is missing: {claim_path}")
    text = claim_path.read_text(encoding="utf-8")
    updates = {
        "Expected state": "`working`",
        "Updated at": f"`{transition_at}`",
        "Last claim": f"`{team}` started work. Source: `{source_ref}`.",
    }
    updated = text
    missing: list[str] = []
    for field, value in updates.items():
        updated, ok = replace_markdown_field(updated, field, value)
        if not ok:
            missing.append(field)
    if missing:
        raise ValueError(f"claim.md missing required field(s): {', '.join(missing)}")
    return updated


def decision_is_final(decision_status: str, decision_text: str = "") -> bool:
    status = normalized_state(decision_status)
    decision = normalized_state(decision_text)
    if status in {"", "pending", "draft"} and decision in {"", "choose_one"}:
        return False
    return status not in {"", "pending", "draft"} or decision not in {"", "choose_one"}


def extract_recommendation(evidence_text: str) -> str:
    lines = evidence_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower().startswith("recommended decision"):
            tokens: list[str] = []
            for candidate in lines[index + 1 : index + 8]:
                raw = candidate.strip()
                if raw.startswith("##"):
                    break
                cleaned = clean_markdown_value(raw.lstrip("-").strip())
                if not cleaned or cleaned.lower() in {"choose one:", "rationale:"}:
                    continue
                token = cleaned.split()[0].strip("`:.").lower()
                if token in {"accept", "accepted", "revise", "revision", "blocked", "block"}:
                    tokens.append(token)
            distinct = list(dict.fromkeys(tokens))
            return distinct[0] if len(distinct) == 1 else ""
    return ""


def build_work_unit_readiness(artifact_root: Path, work_unit: str) -> dict[str, Any]:
    artifact_dir = artifact_root / work_unit
    assignment = parse_markdown_source(artifact_dir / "assignment.md")
    claim = parse_markdown_source(artifact_dir / "claim.md")
    evidence = parse_markdown_source(artifact_dir / "evidence.md")
    decision = parse_markdown_source(artifact_dir / "decision.md")
    proof_path = artifact_dir / DEFAULT_PROOF_LOG_NAME
    progress_path = artifact_dir / "progress.jsonl"
    proof_rows, warnings = proof_rows_for_work_unit(proof_path, work_unit)
    progress_at, progress_warnings, missing_progress_source_refs = latest_progress_timestamp(
        progress_path,
        work_unit,
        artifact_dir,
    )
    warnings.extend(progress_warnings)

    claim_state = claim["fields"].get("expected state", "")
    evidence_status = evidence["status"]
    decision_text = decision["fields"].get("decision", "")
    decision_final = decision_is_final(decision["status"], decision_text)
    result_ready_at, result_ready_proof = first_result_ready_time(proof_rows)
    final_reviews = final_review_kinds(proof_rows)
    closeouts = owner_closeout_kinds(proof_rows)
    distinct_final_reviews = sorted(set(final_reviews))
    stale_reason = ""
    conflict_reason = ""
    if decision_final:
        stale_reason = "decision already recorded"
    if len(distinct_final_reviews) > 1:
        conflict_reason = "competing final review kinds: " + ", ".join(distinct_final_reviews)
    if len(set(row.get("discord_timestamp") or row.get("transition_at") or "" for row in proof_rows if row.get("kind") == "RESULT_READY")) > 1:
        warnings.append("multiple RESULT_READY proof timestamps found")
    if len(set(closeouts)) > 1:
        conflict_reason = "competing owner closeout kinds: " + ", ".join(sorted(set(closeouts)))

    title = assignment["fields"].get("title") or claim["fields"].get("title") or ""
    team = (
        assignment["fields"].get("assigned team lead openclaw agent")
        or evidence["fields"].get("team lead openclaw agent")
        or claim["fields"].get("owner session ref", "").removeprefix("agent=")
    )
    work_card, work_card_source = source_field_value(
        [
            ("assignment.md", assignment),
            ("claim.md", claim),
            ("evidence.md", evidence),
            ("decision.md", decision),
        ],
        "work card",
    )
    recommendation = extract_recommendation(evidence["text"])
    suggested_final = FINAL_REVIEW_BY_RECOMMENDATION.get(recommendation, "")
    suggested_closeout = CLOSEOUT_BY_FINAL_REVIEW.get(suggested_final, "")

    gate = result_ready_gate(artifact_root, work_unit)
    readiness_requested = bool(gate["requested"])
    readiness_blockers = list(gate["blockers"])
    ready = bool(gate["ready"])
    sort_time = result_ready_at or claim["fields"].get("updated at", "") or progress_at or ""
    sort_key = f"{sort_time or '9999-99-99T99:99:99Z'}|{work_unit}"
    actionable = ready and not stale_reason and not conflict_reason
    return {
        "work_unit_id": work_unit,
        "title": title,
        "work_card": work_card,
        "work_card_source": work_card_source,
        "team": team,
        "artifact_dir": str(artifact_dir),
        "claim_state": claim_state,
        "evidence_status": evidence_status,
        "result_ready_requested": readiness_requested,
        "result_ready": ready,
        "result_ready_blockers": readiness_blockers,
        "result_ready_gate": gate,
        "result_ready_gate_failures": gate["failures"],
        "result_ready_at": result_ready_at,
        "result_ready_source": f"{proof_path}#{result_ready_proof}" if result_ready_proof else str(evidence["path"] if evidence["exists"] else claim["path"]),
        "evidence_path": str(artifact_dir / "evidence.md"),
        "decision_path": str(artifact_dir / "decision.md"),
        "decision_exists": bool(decision["exists"]),
        "decision_status": decision["status"],
        "decision_final": decision_final,
        "proof_path": str(proof_path),
        "progress_path": str(progress_path),
        "project_dry_run_supported": True,
        "stale_reason": stale_reason,
        "conflict_reason": conflict_reason,
        "warnings": warnings,
        "sort_key": sort_key,
        "actionable": actionable,
        "final_reviews": final_reviews,
        "owner_closeouts": closeouts,
        "team_recommendation": recommendation,
        "suggested_final_review_kind": suggested_final,
        "suggested_owner_closeout_kind": suggested_closeout,
    }


def iter_work_unit_ids(artifact_root: Path, requested: str = "") -> list[str]:
    if requested:
        return [requested]
    if not artifact_root.exists():
        return []
    return sorted(path.name for path in artifact_root.iterdir() if path.is_dir() and WORK_UNIT_RE.match(path.name))


def progress_states(progress_path: Path, work_unit: str) -> set[str]:
    states: set[str] = set()
    if not progress_path.exists():
        return states
    for line in progress_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        row_work_unit = str(row.get("work_unit_id") or "")
        if row_work_unit and row_work_unit != work_unit:
            continue
        state = normalized_state(str(row.get("transition_kind") or ""))
        if state:
            states.add(state)
    return states


def active_wu_item(artifact_root: Path, work_unit: str) -> dict[str, Any]:
    artifact_dir = artifact_root / work_unit
    claim = parse_markdown_source(artifact_dir / "claim.md")
    evidence = parse_markdown_source(artifact_dir / "evidence.md")
    decision = parse_markdown_source(artifact_dir / "decision.md")
    assignment = parse_markdown_source(artifact_dir / "assignment.md")
    states = progress_states(artifact_dir / "progress.jsonl", work_unit)
    claim_state = normalized_state(str(claim.get("fields", {}).get("expected state") or ""))
    evidence_status = normalized_state(str(evidence.get("status") or ""))
    decision_text = str(decision.get("fields", {}).get("decision") or "")
    terminal = (
        decision_is_final(str(decision.get("status") or ""), decision_text)
        or claim_state in ACTIVE_WU_TERMINAL_STATES
        or evidence_status in ACTIVE_WU_TERMINAL_STATES
        or bool(states & ACTIVE_WU_TERMINAL_STATES)
    )
    source_active = (
        bool(states & ACTIVE_WU_SOURCE_STATES)
        or claim_state in {"working", "waiting"}
        or (artifact_dir / "dispatch.json").exists()
    )
    active = source_active and not terminal
    return {
        "work_unit_id": work_unit,
        "active": active,
        "source_active": source_active,
        "terminal": terminal,
        "claim_state": claim_state,
        "evidence_status": evidence_status,
        "progress_states": sorted(states),
        "team": assignment.get("fields", {}).get("assigned team lead openclaw agent", ""),
        "artifact_dir": str(artifact_dir),
    }


def active_wu_capacity(artifact_root: Path, current_work_unit_id: str = "") -> dict[str, Any]:
    items = [active_wu_item(artifact_root, work_unit) for work_unit in iter_work_unit_ids(artifact_root)]
    active_items = [item for item in items if item["active"]]
    current_active = any(item["work_unit_id"] == current_work_unit_id and item["active"] for item in items)
    other_active_items = [item for item in active_items if item["work_unit_id"] != current_work_unit_id]
    return {
        "artifact_root": str(artifact_root),
        "active_count": len(active_items),
        "other_active_count": len(other_active_items),
        "current_active": current_active,
        "active_work_units": active_items,
    }


def path_parent_writable(path: Path) -> bool:
    parent = path.expanduser().parent
    return parent.exists() and os.access(parent, os.W_OK)


def public_install_preflight_checks(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[str]]:
    checks: list[dict[str, str]] = []
    blockers: list[str] = []

    project_sync_mode = str(getattr(args, "project_sync_mode", "disabled") or "disabled")
    project_sync_field_map = str(getattr(args, "project_sync_field_map", "") or "").strip()
    if project_sync_mode == "required":
        if not project_sync_field_map:
            blockers.append("Project sync is required but --project-sync-field-map is missing")
            checks.append({"name": "project_field_map", "status": "BLOCKED", "reason": "missing"})
        elif not Path(project_sync_field_map).expanduser().exists():
            blockers.append(f"Project field map does not exist: {project_sync_field_map}")
            checks.append({"name": "project_field_map", "status": "BLOCKED", "reason": "missing_file"})
        else:
            checks.append({"name": "project_field_map", "status": "OK", "reason": project_sync_field_map})
    else:
        checks.append({"name": "project_sync_mode", "status": "OK", "reason": project_sync_mode})

    proof_log_value = str(getattr(args, "proof_log", "") or "").strip()
    if proof_log_value:
        proof_log = Path(proof_log_value)
        if path_parent_writable(proof_log):
            checks.append({"name": "proof_log_writable", "status": "OK", "reason": proof_log_value})
        else:
            blockers.append(f"Proof log parent is not writable: {proof_log_value}")
            checks.append({"name": "proof_log_writable", "status": "BLOCKED", "reason": "parent_not_writable"})

    if bool(getattr(args, "require_discord_targets", False)):
        missing_targets = []
        if not str(getattr(args, "team_target", "") or "").strip():
            missing_targets.append("team-target")
        if not str(getattr(args, "ops_target", "") or "").strip():
            missing_targets.append("ops-target")
        if missing_targets:
            blockers.append(f"Discord target(s) missing: {', '.join(missing_targets)}")
            checks.append({"name": "discord_targets", "status": "BLOCKED", "reason": ",".join(missing_targets)})
        else:
            checks.append({"name": "discord_targets", "status": "OK", "reason": "team+ops"})

    if bool(getattr(args, "require_adapter_command", False)):
        adapter_command = str(getattr(args, "adapter_command", "") or "").strip()
        if not adapter_command:
            blockers.append("Adapter command is required but missing")
            checks.append({"name": "adapter_command", "status": "BLOCKED", "reason": "missing"})
        else:
            checks.append({"name": "adapter_command", "status": "OK", "reason": adapter_command})

    if hasattr(args, "role_context"):
        role_context = str(getattr(args, "role_context", "") or "").strip()
        if role_context:
            checks.append({"name": "role_context", "status": "OK", "reason": role_context})
        else:
            blockers.append("Role context is missing")
            checks.append({"name": "role_context", "status": "BLOCKED", "reason": "missing"})

    return checks, blockers


def capacity_check(args: argparse.Namespace) -> int:
    agent_count = args.company_ops_agent_count
    if agent_count < 1:
        print("error: --company-ops-agent-count must be >= 1", file=sys.stderr)
        return 1
    if args.reserved_slots < 0:
        print("error: --reserved-slots must be >= 0", file=sys.stderr)
        return 1
    recommended_main = recommended_main_concurrency(agent_count)
    recommended_subagents = recommended_subagent_concurrency(agent_count)
    max_concurrent, subagents_max, warnings, config_source = openclaw_capacity_values(args)
    effective_max = max_concurrent if max_concurrent is not None else recommended_main
    cap = active_wu_cap(effective_max, args.reserved_slots)
    capacity = active_wu_capacity(args.artifact_root.expanduser(), args.work_unit_id)
    host_warnings: list[str] = []
    if max_concurrent is None:
        host_warnings.append(
            f"agents.defaults.maxConcurrent unreadable; using recommended value {recommended_main} for derived Company Ops cap"
        )
    elif max_concurrent < recommended_main:
        host_warnings.append(
            f"agents.defaults.maxConcurrent is {max_concurrent}; recommended minimum is {recommended_main}"
        )
    if subagents_max is None:
        host_warnings.append(f"agents.defaults.subagents.maxConcurrent unreadable; recommended minimum is {recommended_subagents}")
    elif subagents_max < recommended_subagents:
        host_warnings.append(
            f"agents.defaults.subagents.maxConcurrent is {subagents_max}; recommended minimum is {recommended_subagents}"
        )
    capacity_warnings: list[str] = []
    if capacity["active_count"] > cap:
        capacity_warnings.append(f"Company Ops active WU count is {capacity['active_count']}; cap is {cap}")
    elif capacity["active_count"] == cap and not capacity["current_active"]:
        capacity_warnings.append(f"Company Ops active WU cap is full at {cap}")
    setup_checks, setup_blockers = public_install_preflight_checks(args)
    status = "OK" if not host_warnings and not capacity_warnings else "WARN"
    if setup_blockers:
        status = "BLOCKED"
    payload = {
        "status": status,
        "source": "local-source-artifacts-and-openclaw-config",
        "config_source": config_source,
        "company_ops_agent_count": agent_count,
        "recommended": {
            "agents.defaults.maxConcurrent": recommended_main,
            "agents.defaults.subagents.maxConcurrent": recommended_subagents,
            "reserved_slots": args.reserved_slots,
        },
        "current": {
            "agents.defaults.maxConcurrent": max_concurrent,
            "agents.defaults.subagents.maxConcurrent": subagents_max,
        },
        "derived": {
            "effective_maxConcurrent": effective_max,
            "company_ops_active_wu_cap": cap,
        },
        "active": capacity,
        "warnings": [*warnings, *host_warnings, *capacity_warnings],
        "setup_checks": setup_checks,
        "setup_blockers": setup_blockers,
        "apply_policy": {
            "openclaw_config_auto_mutation": False,
            "gateway_restart_auto": False,
            "session_cleanup_auto_enforce": False,
            "subagent_budget_runtime_enforcement": False,
        },
        "next_action": (
            "Resolve BLOCKED setup checks before live Company Ops mutation."
            if status == "BLOCKED"
            else (
            "Review warnings and explicitly update OpenClaw host config if appropriate."
            if status == "WARN"
            else "Capacity policy is within the recommended boundary."
            )
        ),
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"{status} Company Ops capacity preflight")
        print(f"- Company Ops agents: {agent_count}")
        print(f"- Recommended OpenClaw maxConcurrent/subagents: {recommended_main}/{recommended_subagents}")
        print(f"- Current OpenClaw maxConcurrent/subagents: {max_concurrent or 'unreadable'}/{subagents_max or 'unreadable'}")
        print(f"- Derived Company Ops active WU cap: {cap}")
        print(f"- Active WUs: {capacity['active_count']}")
        for warning in payload["warnings"]:
            print(f"- WARN: {warning}")
        for blocker in setup_blockers:
            print(f"- BLOCKED: {blocker}")
        print(f"- Next: {payload['next_action']}")
    return 0


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


def validate_handoff_spec(spec: dict[str, Any]) -> dict[str, Any]:
    targets = spec.get("targets")
    if not isinstance(targets, dict):
        raise ValueError("handoff spec requires object: targets")
    ops_target = targets.get("ops_feed")
    team_target = targets.get("team_detail")
    if not isinstance(ops_target, str) or not ops_target.strip():
        raise ValueError("handoff spec requires non-empty targets.ops_feed")
    if not isinstance(team_target, str) or not team_target.strip():
        raise ValueError("handoff spec requires non-empty targets.team_detail")

    mode = normalize_handoff_mode(spec.get("mode"))
    subagent_budget = normalize_subagent_budget(spec.get("subagent_budget"), default="3")
    mutation_authority = normalize_mutation_authority(spec, mode)
    normalized = {
        "work_unit_id": work_unit_id(require_spec_text(spec, "work_unit_id")),
        "title": require_spec_text(spec, "title"),
        "team": require_spec_text(spec, "team"),
        "mode": mode,
        "goal": require_spec_text(spec, "goal"),
        "scope": spec_text_list(spec, "scope"),
        "done_criteria": spec_text_list(spec, "done_criteria"),
        "verification_criteria": spec_text_list(spec, "verification_criteria"),
        "targets": {
            "ops_feed": ops_target.strip(),
            "team_detail": team_target.strip(),
        },
        "owner_request": optional_spec_text(spec, "owner_request"),
        "next": optional_spec_text(spec, "next", "Team Lead starts from the Assignment Packet."),
        "report": optional_spec_text(
            spec,
            "report",
            "Result summary, evidence links, checks performed, remaining risks, blockers.",
        ),
        "operations_lead": optional_spec_text(spec, "operations_lead", "operations-lead"),
        "work_card": optional_spec_text(spec, "work_card") or optional_spec_text(spec, "work_card_ref"),
        "work_card_repo": optional_spec_text(spec, "work_card_repo"),
        "created_at": optional_spec_text(spec, "created_at"),
        "source_refs": spec_text_list(spec, "source_refs") if "source_refs" in spec else [],
        "subagent_budget": subagent_budget,
        "subagent_budget_reason": normalize_subagent_budget_reason(spec.get("subagent_budget_reason"), subagent_budget),
        "mutation_authority": mutation_authority,
    }
    if not normalized["work_card"] and not normalized["work_card_repo"]:
        raise ValueError("handoff spec requires work_card/work_card_ref or work_card_repo")
    return normalized


def work_card_body(spec: dict[str, Any], output_dir: Path) -> str:
    assignment_path = output_dir / "assignment.md"
    evidence_path = output_dir / "evidence.md"
    decision_path = output_dir / "decision.md"
    source_refs = markdown_bullets(spec["source_refs"]) if spec["source_refs"] else "-"
    return f"""# Work Card

## Identity

- Work Unit id: `{spec["work_unit_id"]}`
- Assigned Team Lead OpenClaw Agent: `{spec["team"]}`
- Mode: `{spec["mode"]}`
- Assignment Packet: `{assignment_path}`
- Evidence & Result Record: `{evidence_path}`
- Operations Lead Decision: `{decision_path}`

## Goal

{spec["goal"]}

## Scope

{markdown_bullets(spec["scope"])}

## Done Criteria

{markdown_bullets(spec["done_criteria"])}

## Verification Criteria

{markdown_bullets(spec["verification_criteria"])}

## Mutation Authority

- Mutation allowed: `{bool_yaml(spec["mutation_authority"]["mutation_allowed"])}`
- Allowed paths: `{human_list_or_none(spec["mutation_authority"]["allowed_paths"])}`
- Allowed surfaces: `{human_list_or_none(spec["mutation_authority"]["allowed_surfaces"])}`
- External mutation allowed: `{bool_yaml(spec["mutation_authority"]["external_mutation_allowed"])}`
- Commit/push allowed: `{bool_yaml(spec["mutation_authority"]["commit_push_allowed"])}`

## Source Refs

{source_refs}

## Rule

This Work Card is a visibility card. The Assignment Packet and source artifacts
remain the source of truth.
"""


def create_github_work_card(spec: dict[str, Any], output_dir: Path) -> str:
    body = work_card_body(spec, output_dir)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        body_path = Path(handle.name)
        handle.write(body)
    try:
        command = [
            "gh",
            "issue",
            "create",
            "--repo",
            spec["work_card_repo"],
            "--title",
            f"{spec['work_unit_id']} · {spec['title']}",
            "--body-file",
            str(body_path),
            "--label",
            "work-unit",
            "--label",
            "assignment-ready",
        ]
        result = subprocess.run(command, check=False, text=True, capture_output=True)
    finally:
        try:
            body_path.unlink()
        except FileNotFoundError:
            pass
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue create failed")
    created_url = result.stdout.strip().splitlines()[-1].strip()
    if not created_url:
        raise RuntimeError("gh issue create did not return a Work Card URL")
    return created_url


def render_handoff_assignment(context: dict[str, Any]) -> str:
    return f"""# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Operations Lead: `{context["operations_lead"]}`
- Assigned Team Lead OpenClaw Agent: `{context["team_lead"]}`
- Mode: `{context["mode"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Owner Request

{context["owner_request"] or context["goal"]}

## Goal

{context["goal"]}

## Assumptions And Open Questions

- Initial handoff may start from these facts, but scope, criteria, cost, risk,
  or authority changes require an Operations Lead amendment.

## Change Log

- Initial handoff: `{context["created_at"]}`
- Amendments:

## Scope

{markdown_bullets(context["scope"])}

## Non-goals

- Do not expand beyond this initial handoff scope.
- Do not treat Discord, GitHub Project, comments, or labels as source truth.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.

## Inputs

{markdown_bullets(context["source_refs"]) if context["source_refs"] else "- See Work Card and source artifacts."}

## Done Criteria

{markdown_bullets(context["done_criteria"])}

## Verification Criteria

{markdown_bullets(context["verification_criteria"])}

## Mutation Authority

- Mutation allowed: `{bool_yaml(context["mutation_authority"]["mutation_allowed"])}`
- Allowed paths: `{human_list_or_none(context["mutation_authority"]["allowed_paths"])}`
- Allowed surfaces: `{human_list_or_none(context["mutation_authority"]["allowed_surfaces"])}`
- External mutation allowed: `{bool_yaml(context["mutation_authority"]["external_mutation_allowed"])}`
- Commit/push allowed: `{bool_yaml(context["mutation_authority"]["commit_push_allowed"])}`

Mode boundary:

- `verify` is read-only with respect to the candidate output being checked.
- `verify` may write its own Work Unit `evidence.md`, `verification.md`,
  `verification-artifacts/`, or `evidence-artifacts/` when those paths are
  explicitly allowed.
- `verify` must not mutate candidate outputs, git, GitHub Project, Discord, or
  external systems.

## Protocol Capsule

```yaml
protocol_capsule:
  mode: {context["mode"]}
  mutation_authority:
    mutation_allowed: {bool_yaml(context["mutation_authority"]["mutation_allowed"])}
    allowed_paths: {inline_yaml_list(context["mutation_authority"]["allowed_paths"])}
    allowed_surfaces: {inline_yaml_list(context["mutation_authority"]["allowed_surfaces"])}
    external_mutation_allowed: {bool_yaml(context["mutation_authority"]["external_mutation_allowed"])}
    commit_push_allowed: {bool_yaml(context["mutation_authority"]["commit_push_allowed"])}
  support: []
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  subagent_budget: {context["subagent_budget"]}
  subagent_budget_reason: {context["subagent_budget_reason"]}
  subagent_budget_enforcement: prompt_and_packet_contract_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: revise_means_operations_lead_replan_then_reenter_selected_mode
```

Subagent budget policy:

- `none`: Team Lead handles the Work Unit directly.
- `2`: simple delegated work.
- `3`: normal goal/verify work.
- `5`: complex, high-risk, or broad verification work.
- More than `5` requires explicit Operations Lead or owner approval.

This budget is an Assignment Packet and package-prompt contract. It is not a
runtime hook, tool policy, or hard enforcement layer.

Before invoking `work-unit result-ready`, update the Evidence & Result Record to
`Status: Result Ready`. A draft evidence file must remain in repair-needed
state and should not publish a `RESULT_READY` proof.

## Expected Outputs

- Evidence & Result Record: `{context["evidence_path"]}`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

{context["report"]}

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
"""


def render_handoff_artifacts(spec: dict[str, Any], output_dir: Path, created_at: str) -> dict[str, str]:
    context = {
        "work_unit_id": spec["work_unit_id"],
        "title": spec["title"],
        "work_card": spec["work_card"],
        "operations_lead": spec["operations_lead"],
        "team_lead": spec["team"],
        "mode": spec["mode"],
        "goal": spec["goal"],
        "owner_request": spec["owner_request"],
        "scope": spec["scope"],
        "done_criteria": spec["done_criteria"],
        "verification_criteria": spec["verification_criteria"],
        "mutation_authority": spec["mutation_authority"],
        "source_refs": spec["source_refs"],
        "report": spec["report"],
        "subagent_budget": spec["subagent_budget"],
        "subagent_budget_reason": spec["subagent_budget_reason"],
        "created_at": created_at,
        "assignment_path": f"{output_dir / 'assignment.md'}",
        "claim_path": f"{output_dir / 'claim.md'}",
        "evidence_path": f"{output_dir / 'evidence.md'}",
        "decision_path": f"{output_dir / 'decision.md'}",
    }
    base_context = {
        key: str(context[key])
        for key in (
            "work_unit_id",
            "title",
            "work_card",
            "operations_lead",
            "team_lead",
            "created_at",
            "assignment_path",
            "claim_path",
            "evidence_path",
            "decision_path",
        )
    }
    return {
        "assignment.md": render_handoff_assignment(context),
        "claim.md": render_claim(base_context),
        "evidence.md": render_evidence(base_context),
        "decision.md": render_decision(base_context),
    }


def handoff_card_payloads(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    criteria = "; ".join(spec["done_criteria"])
    caution = "Scope is limited to the Assignment Packet and source artifacts."
    source = spec["work_card"]
    ops_code, ops_payload, ops_error = run_json_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "ASSIGNED",
            "--work-unit-id",
            spec["work_unit_id"],
            "--team",
            spec["team"],
            "--problem",
            spec["title"],
            "--request",
            spec["owner_request"] or spec["goal"],
            "--criteria",
            criteria,
            "--next",
            spec["next"],
            "--source",
            source,
            "--format",
            "json",
        ]
    )
    if ops_code != 0:
        raise RuntimeError(f"ops ASSIGNED card failed: {ops_error}")
    team_code, team_payload, team_error = run_json_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "ASSIGNED_DETAIL",
            "--work-unit-id",
            spec["work_unit_id"],
            "--team",
            spec["team"],
            "--goal",
            spec["goal"],
            "--scope",
            first_line("; ".join(spec["scope"])),
            "--criteria",
            criteria,
            "--caution",
            caution,
            "--report",
            spec["report"],
            "--next",
            spec["next"],
            "--source",
            source,
            "--format",
            "json",
        ]
    )
    if team_code != 0:
        raise RuntimeError(f"team ASSIGNED_DETAIL card failed: {team_error}")
    return ops_payload["card"], team_payload["card"], ops_payload["text"], team_payload["text"]


def write_handoff_files(
    output_dir: Path,
    rendered: dict[str, str],
    ops_card: dict[str, Any],
    team_card: dict[str, Any],
    *,
    force: bool,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        **{filename: output_dir / filename for filename in ARTIFACTS},
        "ops_card": output_dir / "ops-assigned-card.json",
        "team_card": output_dir / "team-assigned-card.json",
    }
    if not force:
        existing = [str(path) for path in paths.values() if path.exists()]
        if existing:
            raise FileExistsError("handoff output already exists: " + ", ".join(existing))
    for filename, content in rendered.items():
        paths[filename].write_text(content, encoding="utf-8")
    paths["ops_card"].write_text(json.dumps({"card": ops_card}, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["team_card"].write_text(json.dumps({"card": team_card}, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def publish_handoff_sequence(args: argparse.Namespace, spec: dict[str, Any], paths: dict[str, str], proof_log: Path) -> tuple[int, dict[str, Any], str]:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "discord_ops.py"),
        "publish-sequence",
        "--card-target",
        f"{paths['ops_card']}={spec['targets']['ops_feed']}",
        "--card-target",
        f"{paths['team_card']}={spec['targets']['team_detail']}",
        "--proof-log",
        str(proof_log),
        "--ops-feed-target",
        spec["targets"]["ops_feed"],
        "--team-detail-target",
        spec["targets"]["team_detail"],
        "--transition-at",
        args.transition_at,
        "--readback-limit",
        str(args.readback_limit),
        "--format",
        "json",
    ]
    if args.channel:
        command.extend(["--channel", args.channel])
    if args.account:
        command.extend(["--account", args.account])
    if args.thread_id:
        command.extend(["--thread-id", args.thread_id])
    return run_json_command(command)


def handoff_work_unit(args: argparse.Namespace) -> int:
    try:
        spec = validate_handoff_spec(read_json_file(args.spec))
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not args.dry_run and not args.publish:
        print("error: handoff requires --dry-run or --publish", file=sys.stderr)
        return 1

    output_dir = args.output_root.expanduser() / spec["work_unit_id"]
    created_at = spec["created_at"] or args.created_at or utc_now_iso()
    proof_log = args.proof_log.expanduser() if args.proof_log else output_dir / DEFAULT_PROOF_LOG_NAME
    args.work_unit_id = spec["work_unit_id"]
    args.output_root = args.output_root.expanduser()
    args.transition_at = args.transition_at or utc_now_iso()

    if not spec["work_card"]:
        spec["work_card"] = f"planned Work Card in {spec['work_card_repo']}"

    try:
        rendered = render_handoff_artifacts(spec, output_dir, created_at)
        ops_card, team_card, ops_text, team_text = handoff_card_payloads(spec)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.publish and not args.force:
        planned_paths = [output_dir / filename for filename in (*ARTIFACTS, "ops-assigned-card.json", "team-assigned-card.json")]
        existing = [str(path) for path in planned_paths if path.exists()]
        if existing:
            print(f"error: handoff output already exists: {', '.join(existing)}", file=sys.stderr)
            return 1

    if args.publish and spec["work_card"].startswith("planned Work Card in "):
        try:
            spec["work_card"] = create_github_work_card(spec, output_dir)
            rendered = render_handoff_artifacts(spec, output_dir, created_at)
            ops_card, team_card, ops_text, team_text = handoff_card_payloads(spec)
        except RuntimeError as exc:
            print(f"error: Work Card creation failed: {exc}", file=sys.stderr)
            return 1

    plan = {
        "work_unit_id": spec["work_unit_id"],
        "dry_run": bool(args.dry_run),
        "output_dir": str(output_dir),
        "work_card": spec["work_card"],
        "artifacts": [str(output_dir / filename) for filename in ARTIFACTS],
        "cards": [
            {"surface": "ops-feed", "kind": "ASSIGNED", "target": spec["targets"]["ops_feed"], "path": str(output_dir / "ops-assigned-card.json")},
            {"surface": "team-detail", "kind": "ASSIGNED_DETAIL", "target": spec["targets"]["team_detail"], "path": str(output_dir / "team-assigned-card.json")},
        ],
        "proof_log": str(proof_log),
        "project_sync": {
            "enabled": bool(args.project_sync_field_map),
            "mode": "warning-only mirror",
        },
    }
    if args.dry_run:
        payload = {
            "plan": plan,
            "ops_card": ops_card,
            "team_card": team_card,
            "ops_text": ops_text,
            "team_text": team_text,
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(f"DRY-RUN handoff {spec['work_unit_id']}")
            print(f"- Work Card: {spec['work_card']}")
            print(f"- Artifacts: {output_dir}")
            print("- Publish order: ops-feed ASSIGNED -> team-detail ASSIGNED_DETAIL")
        return 0

    try:
        paths = write_handoff_files(output_dir, rendered, ops_card, team_card, force=args.force)
    except (OSError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    publish_code, publish_payload, publish_error = publish_handoff_sequence(args, spec, paths, proof_log)
    project_sync = {"enabled": False}
    if publish_code == 0:
        project_sync = run_project_sync(args)
        if project_sync.get("enabled") and not project_sync.get("ok"):
            print(f"warning: Project handoff sync failed: {project_sync.get('error')}", file=sys.stderr)
    else:
        print(publish_error or "error: handoff publish failed", file=sys.stderr)

    payload = {
        "plan": plan,
        "paths": paths,
        "publish": publish_payload.get("sequence", []),
        "project_sync": project_sync,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    elif publish_code == 0:
        print(f"OK handoff published: {spec['work_unit_id']} · {spec['team']} · source artifacts + ASSIGNED readbacks")
    return publish_code


def validate_draft_handoff_spec(spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    unknown = sorted(set(spec) - DRAFT_HANDOFF_SPEC_FIELDS)
    if unknown:
        warnings.append("ignored unknown draft handoff spec fields: " + ", ".join(unknown))

    requested_by = require_spec_text(spec, "requested_by")
    source_refs = spec_text_list(spec, "source_refs")
    if any(item.strip().lower() == "needs-ops-decision" for item in source_refs):
        raise ValueError("draft handoff spec requires concrete source_refs")

    title = optional_spec_text(spec, "title")
    owner_request = optional_spec_text(spec, "owner_request")
    if not title and not owner_request:
        raise ValueError("draft handoff spec requires title or owner_request")

    raw_targets = spec.get("targets", {})
    if raw_targets is None:
        raw_targets = {}
    if not isinstance(raw_targets, dict):
        raise ValueError("draft handoff spec field must be an object: targets")
    targets = {
        "ops_feed": optional_spec_text(raw_targets, "ops_feed"),
        "team_detail": optional_spec_text(raw_targets, "team_detail"),
    }

    subagent_budget = normalize_subagent_budget(spec.get("subagent_budget"), default="3")
    normalized = {
        "work_unit_id": optional_spec_text(spec, "work_unit_id"),
        "title": title,
        "owner_request": owner_request,
        "requested_by": requested_by,
        "source_refs": source_refs,
        "operations_lead": optional_spec_text(spec, "operations_lead", "operations-lead"),
        "team": optional_spec_text(spec, "team"),
        "mode": optional_spec_text(spec, "mode"),
        "goal": optional_spec_text(spec, "goal"),
        "scope": optional_spec_text_list(spec, "scope"),
        "done_criteria": optional_spec_text_list(spec, "done_criteria"),
        "verification_criteria": optional_spec_text_list(spec, "verification_criteria"),
        "targets": targets,
        "target_paths": optional_spec_text_list(spec, "target_paths"),
        "work_card": optional_spec_text(spec, "work_card") or optional_spec_text(spec, "work_card_ref"),
        "work_card_repo": optional_spec_text(spec, "work_card_repo"),
        "no_go": optional_spec_text_list(spec, "no_go"),
        "next": optional_spec_text(spec, "next", "Team Lead starts from the Assignment Packet."),
        "report": optional_spec_text(
            spec,
            "report",
            "Result summary, evidence links, checks performed, remaining risks, blockers.",
        ),
        "created_at": optional_spec_text(spec, "created_at"),
        "subagent_budget": subagent_budget,
        "subagent_budget_reason": normalize_subagent_budget_reason(spec.get("subagent_budget_reason"), subagent_budget),
    }
    return normalized, warnings


def draft_missing_fields(spec: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in (
        "work_unit_id",
        "title",
        "team",
        "mode",
        "goal",
        "scope",
        "done_criteria",
        "verification_criteria",
    ):
        if amendment_value_needs_decision(spec.get(key)):
            missing.append(key)
    if amendment_value_needs_decision(spec.get("targets", {}).get("ops_feed")):
        missing.append("targets.ops_feed")
    if amendment_value_needs_decision(spec.get("targets", {}).get("team_detail")):
        missing.append("targets.team_detail")
    if not spec.get("work_card") and not spec.get("work_card_repo"):
        missing.append("work_card_or_work_card_repo")
    return missing


def draft_handoff_spec_candidate(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "work_unit_id": spec["work_unit_id"] or "needs-ops-decision",
        "title": spec["title"] or "needs-ops-decision",
        "work_card": spec["work_card"] or "",
        "work_card_repo": spec["work_card_repo"] or "",
        "operations_lead": spec["operations_lead"],
        "team": spec["team"] or "needs-ops-decision",
        "mode": spec["mode"] or "needs-ops-decision",
        "owner_request": spec["owner_request"],
        "goal": spec["goal"] or "needs-ops-decision",
        "scope": spec["scope"] or ["needs-ops-decision"],
        "done_criteria": spec["done_criteria"] or ["needs-ops-decision"],
        "verification_criteria": spec["verification_criteria"] or ["needs-ops-decision"],
        "targets": {
            "ops_feed": spec["targets"]["ops_feed"] or "needs-ops-decision",
            "team_detail": spec["targets"]["team_detail"] or "needs-ops-decision",
        },
        "source_refs": spec["source_refs"],
        "next": spec["next"],
        "report": spec["report"],
        "created_at": spec["created_at"],
    }


def render_draft_work_card(spec: dict[str, Any]) -> str:
    source_refs = markdown_bullets(spec["source_refs"])
    scope = markdown_bullets(spec["scope"] or ["needs-ops-decision"])
    done = markdown_bullets(spec["done_criteria"] or ["needs-ops-decision"])
    verification = markdown_bullets(spec["verification_criteria"] or ["needs-ops-decision"])
    return f"""# Work Card Draft

## Identity

- Work Unit id: `{spec["work_unit_id"] or "needs-ops-decision"}`
- Assigned Team Lead OpenClaw Agent: `{spec["team"] or "needs-ops-decision"}`
- Mode: `{spec["mode"] or "needs-ops-decision"}`

## Title

{spec["title"] or "needs-ops-decision"}

## Owner Request

{spec["owner_request"] or "needs-ops-decision"}

## Goal

{spec["goal"] or "needs-ops-decision"}

## Scope

{scope}

## Done Criteria

{done}

## Verification Criteria

{verification}

## Source Refs

{source_refs}

## Rule

This is a review-only draft. It is not a Work Card until the Operations Lead
creates or links the real Work Card.
"""


def render_draft_assignment(spec: dict[str, Any]) -> str:
    no_go = markdown_bullets(spec["no_go"] or ["Do not expand beyond Operations Lead-approved scope."])
    target_paths = markdown_bullets(spec["target_paths"] or ["needs-ops-decision"])
    return f"""# Assignment Packet Draft

Status: Draft

This is a review-only handoff draft prepared from structured Operations
Lead-supplied facts. It is not a source artifact.

## Identity

- Work Unit id: `{spec["work_unit_id"] or "needs-ops-decision"}`
- Title: {spec["title"] or "needs-ops-decision"}
- Operations Lead: `{spec["operations_lead"]}`
- Assigned Team Lead OpenClaw Agent: `{spec["team"] or "needs-ops-decision"}`
- Mode: `{spec["mode"] or "needs-ops-decision"}`

## Owner Request

{spec["owner_request"] or "needs-ops-decision"}

## Goal

{spec["goal"] or "needs-ops-decision"}

## Scope

{markdown_bullets(spec["scope"] or ["needs-ops-decision"])}

## Non-goals

{no_go}

## Target Paths

{target_paths}

## Done Criteria

{markdown_bullets(spec["done_criteria"] or ["needs-ops-decision"])}

## Verification Criteria

{markdown_bullets(spec["verification_criteria"] or ["needs-ops-decision"])}

## Inputs

{markdown_bullets(spec["source_refs"])}
"""


def draft_handoff_work_unit(args: argparse.Namespace) -> int:
    try:
        spec, warnings = validate_draft_handoff_spec(read_json_file(args.spec))
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not args.dry_run:
        print("error: draft-handoff currently supports --dry-run only", file=sys.stderr)
        return 1

    missing_fields = draft_missing_fields(spec)
    status = "needs-ops-decision" if missing_fields else "ready"
    handoff_spec = draft_handoff_spec_candidate(spec)
    completed_handoff_spec_valid = False
    validation_error = ""
    rendered_preview: dict[str, str] = {}
    if not missing_fields:
        try:
            completed = validate_handoff_spec(handoff_spec)
            if not completed["work_card"]:
                completed["work_card"] = f"planned Work Card in {completed['work_card_repo']}"
            output_root = args.output_root.expanduser()
            output_dir = output_root / completed["work_unit_id"]
            created_at = completed["created_at"] or args.created_at or utc_now_iso()
            rendered_preview = render_handoff_artifacts(completed, output_dir, created_at)
            completed_handoff_spec_valid = True
        except (ValueError, argparse.ArgumentTypeError) as exc:
            status = "needs-ops-decision"
            validation_error = str(exc)

    payload = {
        "dry_run": True,
        "status": status,
        "requested_by": spec["requested_by"],
        "missing_fields": missing_fields,
        "warnings": warnings,
        "source_refs": spec["source_refs"],
        "work_card_draft": render_draft_work_card(spec),
        "assignment_packet_draft": rendered_preview.get("assignment.md") or render_draft_assignment(spec),
        "handoff_spec_draft": handoff_spec,
        "no_go_order_checklist": [
            "Operations Lead reviews every needs-ops-decision field.",
            "Completed draft spec passes work-unit handoff --dry-run before publish.",
            "ops-feed ASSIGNED remains before team-detail ASSIGNED_DETAIL.",
            "Discord and GitHub Project remain mirrors, not source truth.",
        ],
        "completed_handoff_spec_valid": completed_handoff_spec_valid,
        "validation_error": validation_error,
        "would_create_work_card": False,
        "would_write_source_artifacts": False,
        "would_publish_discord": False,
        "would_mutate_project": False,
        "would_send_owner_report": False,
        "checks": {
            "local_spec_only": True,
            "structured_input": True,
            "free_form_request_routing": False,
            "team_lead_auto_selected": False,
            "external_sources_read": False,
            "llm_calls": 0,
            "uses_handoff_validator_when_complete": completed_handoff_spec_valid,
        },
        "next_action": (
            "Operations Lead fills missing fields before validating with work-unit handoff --dry-run."
            if status == "needs-ops-decision"
            else "Operations Lead may validate this completed spec with work-unit handoff --dry-run."
        ),
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"DRY-RUN draft-handoff: {status}")
        print(f"- Requested by: {spec['requested_by']}")
        print(f"- Source refs: {', '.join(spec['source_refs'])}")
        if missing_fields:
            print("- Missing fields:")
            for field in missing_fields:
                print(f"  - {field}")
        if validation_error:
            print(f"- Validation error: {validation_error}")
        print(f"- Completed handoff spec valid: {completed_handoff_spec_valid}")
        print(f"- Next: {payload['next_action']}")
    return 0


def validate_amendment_spec(spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    unknown = sorted(set(spec) - AMENDMENT_SPEC_FIELDS)
    if unknown:
        warnings.append("ignored unknown amendment spec fields: " + ", ".join(unknown))

    proposed_updates = spec.get("proposed_updates")
    if not isinstance(proposed_updates, dict):
        raise ValueError("amendment spec requires object: proposed_updates")
    normalized_updates: dict[str, Any] = {}
    for key, value in proposed_updates.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("amendment spec proposed_updates keys must be non-empty strings")
        normalized_updates[key.strip()] = value

    normalized = {
        "work_unit_id": work_unit_id(require_spec_text(spec, "work_unit_id")),
        "reason": require_spec_text(spec, "reason"),
        "changed_fields": spec_text_list(spec, "changed_fields"),
        "proposed_updates": normalized_updates,
        "source_refs": spec_text_list(spec, "source_refs"),
        "requested_by": require_spec_text(spec, "requested_by"),
    }
    return normalized, warnings


def amendment_needs_ops_decision(spec: dict[str, Any]) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []
    changed_fields = [field.strip() for field in spec["changed_fields"] if field.strip()]
    update_keys = set(spec["proposed_updates"])
    for field in changed_fields:
        if field not in update_keys:
            reasons.append(f"missing proposed update for changed field: {field}")
            continue
        value = spec["proposed_updates"].get(field)
        if amendment_value_needs_decision(value):
            reasons.append(f"proposed update needs Operations Lead decision: {field}")

    extra_updates = sorted(update_keys - set(changed_fields))
    if extra_updates:
        warnings.append("proposed_updates contains fields not listed in changed_fields: " + ", ".join(extra_updates))

    return reasons, warnings


def handoff_stable_facts(assignment: dict[str, Any], work_unit: str) -> dict[str, str]:
    fields = assignment.get("fields", {})
    facts = {key: fields[key] for key in sorted(STABLE_HANDOFF_FIELDS) if fields.get(key)}
    facts.setdefault("work unit id", work_unit)
    return facts


def amend_work_unit(args: argparse.Namespace) -> int:
    try:
        spec, warnings = validate_amendment_spec(read_json_file(args.spec))
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not args.dry_run:
        print("error: amend currently supports --dry-run only", file=sys.stderr)
        return 1

    artifact_root = args.artifact_root.expanduser()
    artifact_dir = artifact_root / spec["work_unit_id"]
    assignment_path = artifact_dir / "assignment.md"
    if not artifact_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {artifact_dir}", file=sys.stderr)
        return 1
    assignment = parse_markdown_source(assignment_path)
    if not assignment["exists"]:
        print(f"error: Assignment Packet not found: {assignment_path}", file=sys.stderr)
        return 1

    decision_reasons, decision_warnings = amendment_needs_ops_decision(spec)
    warnings.extend(decision_warnings)
    status = "needs-ops-decision" if decision_reasons else "ready"
    planned_artifact = artifact_dir / "amendment.md"
    payload = {
        "dry_run": True,
        "status": status,
        "work_unit_id": spec["work_unit_id"],
        "artifact_dir": str(artifact_dir),
        "assignment_path": str(assignment_path),
        "planned_artifact": str(planned_artifact),
        "requested_by": spec["requested_by"],
        "reason": spec["reason"],
        "changed_fields": spec["changed_fields"],
        "proposed_updates": spec["proposed_updates"],
        "source_refs": spec["source_refs"],
        "stable_facts": handoff_stable_facts(assignment, spec["work_unit_id"]),
        "needs_ops_decision": decision_reasons,
        "warnings": warnings,
        "would_update_assignment_packet": False,
        "would_write_amendment_artifact": False,
        "would_publish_discord": False,
        "would_mutate_project": False,
        "would_send_owner_report": False,
        "checks": {
            "local_spec_only": True,
            "assignment_packet_reread": True,
            "original_handoff_preserved": True,
            "external_sources_read": False,
            "llm_calls": 0,
        },
        "next_action": (
            "Operations Lead resolves missing/ambiguous amendment fields before any write."
            if decision_reasons
            else "Operations Lead may review this dry-run before any separately accepted write path."
        ),
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"DRY-RUN amend {spec['work_unit_id']}: {status}")
        print(f"- Assignment Packet: {assignment_path}")
        print(f"- Planned artifact: {planned_artifact} (not written)")
        print(f"- Changed fields: {', '.join(spec['changed_fields'])}")
        if decision_reasons:
            print("- Needs Operations Lead decision:")
            for reason in decision_reasons:
                print(f"  - {reason}")
        print(f"- Next: {payload['next_action']}")
    return 0


def append_progress(args: argparse.Namespace) -> int:
    output_dir = args.output_root.expanduser() / args.work_unit_id
    if not output_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {output_dir}", file=sys.stderr)
        return 1
    if not any((args.phase, args.current_slice, args.round, args.next_checkpoint)):
        print(
            "error: progress requires at least one of --phase, --current-slice, --round, or --next-checkpoint",
            file=sys.stderr,
        )
        return 1
    row = progress_row_from_args(args, transition_at=args.transition_at or utc_now_iso())
    metadata_error = validate_progress_metadata(row)
    if metadata_error:
        print(f"error: {metadata_error}", file=sys.stderr)
        return 1
    source_failures = source_ref_failures_for_row(output_dir, row)
    if source_failures:
        print_gate_failure(
            "progress source_ref preflight failed",
            {"status": "repair-needed", "failures": source_failures},
        )
        return 1
    if normalized_state(str(row.get("transition_kind") or "")) == "result_ready":
        gate = result_ready_gate(args.output_root, args.work_unit_id, projected_progress_rows=[row])
        if not gate["ready"]:
            print_gate_failure("result_ready progress gate failed", gate)
            return 1
    progress_path = append_progress_row(output_dir, row)
    print(f"recorded progress {args.work_unit_id}: {progress_path}")
    return 0


def checkpoint_card_args(args: argparse.Namespace) -> list[str]:
    progress_row = progress_row_from_args(
        args,
        transition_at=args.transition_at or utc_now_iso(),
        proof_ref=args.proof_ref,
    )
    rendered = render_progress_display(progress_row)
    command = [
        sys.executable,
        str(SCRIPT_DIR / "discord_ops.py"),
        "card",
        "--surface",
        "team-detail",
        "--kind",
        "CHECKPOINT",
        "--work-unit-id",
        args.work_unit_id,
        "--team",
        args.team,
        "--current-slice",
        args.current_slice,
        "--mode",
        progress_row["mode"],
        "--phase",
        progress_row["phase"],
        "--phase-index",
        progress_row["phase_index"],
        "--phase-total",
        progress_row["phase_total"],
        "--round",
        progress_row["round"],
        "--show-round",
        str(progress_row["show_round"]).lower(),
        "--risk-state",
        progress_row["risk_state"],
        "--retry-state",
        progress_row["retry_state"],
        "--rendered-progress-summary",
        rendered["rendered_progress_summary"],
        "--clamp-version",
        rendered["clamp_version"],
        "--status",
        args.status,
        "--next",
        args.next,
        "--format",
        "json",
    ]
    optional_args = (
        ("--elapsed", args.elapsed),
        ("--next-checkpoint", args.next_checkpoint),
        ("--evidence", args.evidence),
        ("--source", args.source_ref),
    )
    for flag, value in optional_args:
        if value:
            command.extend([flag, value])
    return command


def publish_card(
    args: argparse.Namespace,
    card: dict[str, Any],
    proof_log: Path,
    *,
    target: str | None = None,
    expect_surface: str = "team-detail",
) -> tuple[int, dict[str, Any], str]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        temp_path = Path(handle.name)
        json.dump({"card": card}, handle, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    try:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "publish-card",
            "--card-json",
            str(temp_path),
            "--target",
            target or args.target,
            "--expect-surface",
            expect_surface,
            "--proof-log",
            str(proof_log),
            "--channel",
            args.channel,
            "--transition-at",
            args.transition_at,
            "--readback-limit",
            str(args.readback_limit),
            "--format",
            "json",
        ]
        if args.account:
            command.extend(["--account", args.account])
        if args.thread_id:
            command.extend(["--thread-id", args.thread_id])
        if getattr(args, "force", False):
            command.append("--force")
        return run_json_command(command)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def run_project_sync(args: argparse.Namespace) -> dict[str, Any]:
    sync_mode = getattr(args, "project_sync_mode", "auto")
    if sync_mode not in {"auto", *PROJECT_SYNC_MODE_CHOICES}:
        return {
            "enabled": False,
            "required": False,
            "ok": False,
            "sync_state": "failed",
            "error": f"unknown Project sync mode: {sync_mode}",
        }
    required_sync = sync_mode == "required"
    if sync_mode == "disabled":
        return {"enabled": False, "required": False, "ok": False, "sync_state": "not_configured"}
    if not getattr(args, "project_sync_field_map", ""):
        state = "not_attempted" if required_sync else "not_configured"
        return {
            "enabled": False,
            "required": required_sync,
            "ok": False,
            "sync_state": state,
            "error": "Project sync is required but --project-sync-field-map is missing" if required_sync else "",
        }
    artifact_root = getattr(args, "artifact_root", None) or args.output_root
    command = [
        sys.executable,
        str(SCRIPT_DIR / "project_sync.py"),
        "project-sync",
        "apply",
        "--work-unit-id",
        args.work_unit_id,
        "--artifact-root",
        str(artifact_root.expanduser()),
        "--field-map",
        args.project_sync_field_map,
        "--audit-log",
        args.project_sync_audit_log,
        "--format",
        "json",
    ]
    if getattr(args, "project_sync_no_create_missing_project_item", False):
        command.append("--no-create-missing-project-item")
    if required_sync:
        command.append("--sync-issue-labels")
    if args.project_sync_ledger:
        command.extend(["--ledger", args.project_sync_ledger])
    else:
        command.append("--no-ledger")
    code, parsed, output = run_json_command(command)
    sync_state = parsed.get("sync_state")
    if not isinstance(sync_state, str) or not sync_state.strip():
        sync_state = "attempted_ok" if code == 0 else "failed"
    return {
        "enabled": True,
        "required": required_sync,
        "ok": code == 0 and sync_state == "attempted_ok",
        "mode": "apply",
        "returncode": code,
        "sync_state": sync_state,
        "summary": parsed.get("summary", {}),
        "readback": parsed.get("readback", {}),
        "error": output if code != 0 else "",
    }


def started_card(args: argparse.Namespace, assignment: dict[str, Any]) -> tuple[dict[str, Any], str]:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "discord_ops.py"),
        "card",
        "--surface",
        "team-detail",
        "--kind",
        "STARTED",
        "--work-unit-id",
        args.work_unit_id,
        "--team",
        args.team or assignment["fields"].get("assigned team lead openclaw agent", ""),
        "--status",
        args.status,
        "--next",
        args.next,
        "--format",
        "json",
    ]
    return card_from_command(command, "start")


def started_progress_row(args: argparse.Namespace, *, transition_at: str, proof_ref: str = "") -> dict[str, Any]:
    return {
        "work_unit_id": args.work_unit_id,
        "transition_kind": "started",
        "mode": args.mode.strip().lower(),
        "phase": args.phase,
        "phase_index": args.phase_index,
        "phase_total": args.phase_total,
        "round": args.round,
        "show_round": should_show_round(args.mode.strip().lower(), bool(args.round)),
        "current_slice": args.current_slice,
        "next_checkpoint": args.next_checkpoint,
        "source_ref": args.source_ref,
        "proof_ref": proof_ref,
        "transition_at": transition_at,
        "recorded_by": args.recorded_by,
    }


def normalized_session_key(work_unit_id: str, team: str) -> str:
    cleaned_team = re.sub(r"[^a-z0-9]+", "-", team.strip().lower()).strip("-") or "team"
    return f"company-ops-{cleaned_team}-{work_unit_id.lower()}"


def session_key_strategy(session_key: str, default_session_key: str) -> str:
    if session_key == default_session_key:
        return "work-unit-specific"
    return "operator-specified"


def dispatch_ref(args: argparse.Namespace) -> str:
    return args.job_ref or args.session_ref or args.message_ref


def dispatch_adapter_command(args: argparse.Namespace) -> str:
    return args.adapter_command.strip() or os.environ.get(DISPATCH_ADAPTER_COMMAND_ENV, "").strip()


def dispatch_adapter_request(
    args: argparse.Namespace,
    *,
    packet: dict[str, Any],
    artifact_dir: Path,
    transition_at: str,
) -> dict[str, Any]:
    return {
        "adapter_protocol": "company_ops_dispatch_adapter_v1",
        "work_unit_id": args.work_unit_id,
        "team": args.team,
        "agent": args.agent,
        "runtime": args.runtime,
        "session_key": args.session_key,
        "default_session_key": args.default_session_key,
        "session_key_strategy": args.session_key_strategy,
        "session_key_provided": args.session_key_provided,
        "artifact_dir": str(artifact_dir),
        "transition_at": transition_at,
        "packet": packet,
        "required_acceptance": {
            "work_unit_id": args.work_unit_id,
            "assignment_packet": packet["assignment_packet"],
            "result_ready_contract": packet["result_ready_contract"]["command"],
            "authority_boundary": "team_lead_result_ready_only",
        },
    }


def fake_dispatch_acceptance(args: argparse.Namespace, packet: dict[str, Any], accepted_at: str) -> dict[str, Any]:
    return {
        "status": "accepted",
        "adapter": "fake",
        "adapter_version": 1,
        "agent": args.agent,
        "session_key": args.session_key,
        "session_ref": f"session:{args.session_key}",
        "job_ref": f"job:{args.work_unit_id}:dispatch-execute",
        "message_ref": f"message:{args.work_unit_id}:dispatch-accepted",
        "accepted_at": accepted_at,
        "readback": {
            "work_unit_id": args.work_unit_id,
            "assignment_packet": packet["assignment_packet"],
            "result_ready_contract": packet["result_ready_contract"]["command"],
            "authority_boundary": "team_lead_result_ready_only",
        },
    }


def compact_acceptance(proof: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in proof.items()
        if key
        in {
            "status",
            "adapter",
            "adapter_version",
            "agent",
            "session_key",
            "session_ref",
            "job_ref",
            "message_ref",
            "accepted_at",
            "readback",
            "gateway",
        }
    }


def validate_dispatch_acceptance(args: argparse.Namespace, packet: dict[str, Any], proof: dict[str, Any]) -> str:
    if not proof:
        return "runtime adapter did not return JSON acceptance proof"
    candidate = proof.get("result") if isinstance(proof.get("result"), dict) else proof
    if not isinstance(candidate, dict):
        return "runtime adapter acceptance proof must be a JSON object"
    if str(candidate.get("status", "")).strip().lower() != "accepted":
        return "runtime adapter did not return status=accepted"
    readback = candidate.get("readback") if isinstance(candidate.get("readback"), dict) else {}
    if (readback.get("work_unit_id") or candidate.get("work_unit_id")) != args.work_unit_id:
        return "runtime adapter accepted proof has mismatched work_unit_id"
    if (readback.get("assignment_packet") or candidate.get("assignment_packet")) != packet["assignment_packet"]:
        return "runtime adapter accepted proof has mismatched assignment_packet"
    expected_contract = packet["result_ready_contract"]["command"]
    if (readback.get("result_ready_contract") or candidate.get("result_ready_contract")) != expected_contract:
        return "runtime adapter accepted proof did not confirm result_ready_contract"
    if not (readback.get("authority_boundary") or candidate.get("authority_boundary")):
        return "runtime adapter accepted proof did not confirm authority boundary"
    if not candidate.get("job_ref"):
        return "runtime adapter accepted proof did not return an execution enqueue reference"
    if not (candidate.get("session_ref") or candidate.get("message_ref")):
        return "runtime adapter accepted proof did not return a recoverable acceptance reference"
    return ""


def apply_dispatch_acceptance(args: argparse.Namespace, proof: dict[str, Any]) -> dict[str, Any]:
    candidate = proof.get("result") if isinstance(proof.get("result"), dict) else proof
    assert isinstance(candidate, dict)
    for field in ("session_ref", "job_ref", "message_ref"):
        if not getattr(args, field, "") and isinstance(candidate.get(field), str):
            setattr(args, field, candidate[field].strip())
    return compact_acceptance(candidate)


def run_dispatch_adapter(
    args: argparse.Namespace,
    *,
    packet: dict[str, Any],
    artifact_dir: Path,
    transition_at: str,
) -> tuple[dict[str, Any] | None, str]:
    if args.runtime == "record-ref":
        return None, ""
    adapter = args.adapter
    command_text = dispatch_adapter_command(args)
    if adapter == "auto":
        adapter = "command" if command_text else ""
    if not adapter:
        return None, (
            "automatic runtime dispatch adapter is not configured; configure "
            f"{DISPATCH_ADAPTER_COMMAND_ENV} or pass --adapter-command for OpenClaw sessions.send"
        )
    if adapter == "fake":
        proof = fake_dispatch_acceptance(args, packet, transition_at)
        reason = validate_dispatch_acceptance(args, packet, proof)
        return (proof, "" if not reason else reason)
    if adapter == "command":
        if not command_text:
            return None, f"--adapter command requires --adapter-command or {DISPATCH_ADAPTER_COMMAND_ENV}"
        command = shlex.split(command_text)
        if not command:
            return None, "runtime adapter command is empty"
        request = dispatch_adapter_request(args, packet=packet, artifact_dir=artifact_dir, transition_at=transition_at)
        returncode, proof, output = run_json_stdin_command(command, request, args.adapter_timeout_seconds)
        if returncode != 0:
            return None, f"runtime adapter command failed ({returncode}): {output}"
        reason = validate_dispatch_acceptance(args, packet, proof)
        return (proof, "" if not reason else reason)
    return None, f"unsupported runtime adapter: {args.adapter}"


def dispatch_progress_row(
    args: argparse.Namespace,
    *,
    transition_at: str,
    assignment: dict[str, Any],
) -> dict[str, Any]:
    mode = args.mode or clean_markdown_value(str(assignment["fields"].get("mode") or ""))
    return {
        "work_unit_id": args.work_unit_id,
        "transition_kind": "dispatched",
        "mode": mode.strip().lower(),
        "phase": args.phase,
        "phase_index": args.phase_index,
        "phase_total": args.phase_total,
        "round": args.round,
        "show_round": should_show_round(mode, bool(args.round)),
        "current_slice": args.current_slice,
        "next_checkpoint": args.next_checkpoint,
        "source_ref": args.source_ref,
        "proof_ref": dispatch_ref(args),
        "runtime": args.runtime,
        "agent": args.agent,
        "session_key": args.session_key,
        "session_ref": args.session_ref,
        "job_ref": args.job_ref,
        "message_ref": args.message_ref,
        "transition_at": transition_at,
        "recorded_by": args.recorded_by,
    }


def latest_team_detail_target(artifact_dir: Path, work_unit: str) -> str:
    proof_log = artifact_dir / DEFAULT_PROOF_LOG_NAME
    proof_rows, _warnings = proof_rows_for_work_unit(proof_log, work_unit)
    for row in reversed(proof_rows):
        if (
            row.get("surface") == "team-detail"
            and row.get("target")
            and row.get("readback_ok") is not False
        ):
            return str(row["target"])
    return "<team-detail-target>"


def dispatch_packet(args: argparse.Namespace, assignment: dict[str, Any], artifact_dir: Path) -> dict[str, Any]:
    evidence_path = artifact_dir / "evidence.md"
    fields = assignment.get("fields", {})
    subagent_budget = normalize_subagent_budget(
        fields.get("subagent_budget")
        or fields.get("subagent budget")
        or markdown_protocol_capsule_value(assignment, "subagent_budget"),
        default="3",
    )
    subagent_budget_reason = normalize_subagent_budget_reason(
        fields.get("subagent_budget_reason")
        or fields.get("subagent budget reason")
        or markdown_protocol_capsule_value(assignment, "subagent_budget_reason"),
        subagent_budget,
    )
    team_detail_target = latest_team_detail_target(artifact_dir, args.work_unit_id)
    result_ready_command = (
        "python3 scripts/openclaw_company_ops.py work-unit result-ready "
        f"--work-unit-id {args.work_unit_id} --artifact-root {args.artifact_root} "
        f"--team {args.team} --result <result-summary> --evidence {evidence_path} "
        f"--verification <verification-summary> --source-ref {evidence_path} "
        f"--target {team_detail_target} --channel discord --account default "
        f"--project-sync-field-map {DEFAULT_PROJECT_FIELD_MAP} "
        f"--project-sync-ledger {DEFAULT_PROJECT_LEDGER} "
        f"--project-sync-audit-log {DEFAULT_PROJECT_AUDIT_LOG} "
        "--closeout-delegate-runtime openclaw-agent "
        f"--closeout-delegate-agent {args.closeout_delegate_agent} "
        "--closeout-delegate-adapter command "
        "--closeout-delegate-adapter-command 'python3 scripts/openclaw_closeout_delegate_sessions_send.py' "
        "--publish --format json"
    )
    return {
        "protocol": "company_ops_detached_dispatch_v1",
        "work_unit_id": args.work_unit_id,
        "title": clean_markdown_value(str(assignment["fields"].get("title") or "")),
        "team": args.team,
        "agent": args.agent,
        "runtime": args.runtime,
        "session_key": args.session_key,
        "default_session_key": args.default_session_key,
        "session_key_strategy": args.session_key_strategy,
        "session_key_provided": args.session_key_provided,
        "work_card": clean_markdown_value(str(assignment["fields"].get("work card") or "")),
        "repo_root": str(SCRIPT_DIR.parent),
        "assignment_packet": str(artifact_dir / "assignment.md"),
        "evidence_ref": str(evidence_path),
        "subagent_budget": {
            "budget": subagent_budget,
            "reason": subagent_budget_reason,
            "enforcement": "prompt_and_packet_contract_only",
        },
        "result_ready_contract": {
            "command": result_ready_command,
            "rule": "Team Lead submits source-backed evidence and enqueues a fresh OL closeout delegate; the delegate may publish only through guarded closeout.",
            "required_closeout_delegate_wake": True,
            "closeout_delegate_agent": args.closeout_delegate_agent,
            "team_detail_target": team_detail_target,
            "channel": "discord",
            "account": "default",
            "project_sync": {
                "field_map": str(DEFAULT_PROJECT_FIELD_MAP),
                "ledger": str(DEFAULT_PROJECT_LEDGER),
                "audit_log": str(DEFAULT_PROJECT_AUDIT_LOG),
            },
        },
        "instructions": [
            "Read assignment.md before executing.",
            "Use repo_root when resolving relative source paths.",
            "Do not mutate outside the assigned Work Unit scope.",
            "Follow the Assignment Packet subagent_budget as a prompt/packet contract; do not exceed 5 without explicit approval.",
            "Set Evidence & Result Record status to Result Ready before calling the result-ready command.",
            "Return result evidence through the result-ready path with a fresh closeout delegate wake.",
            "Replace <result-summary> and <verification-summary> with concrete text before running the result-ready command.",
            "Do not publish closeout, Project mutation, or owner completion from the Team Lead dispatch.",
        ],
    }


def dispatch_record(
    args: argparse.Namespace,
    assignment: dict[str, Any],
    artifact_dir: Path,
    dispatched_at: str,
    accepted_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "version": 1,
        "status": "dispatched",
        "work_unit_id": args.work_unit_id,
        "team": args.team,
        "agent": args.agent,
        "runtime": args.runtime,
        "session_key": args.session_key,
        "default_session_key": args.default_session_key,
        "session_key_strategy": args.session_key_strategy,
        "session_key_provided": args.session_key_provided,
        "session_ref": args.session_ref,
        "job_ref": args.job_ref,
        "message_ref": args.message_ref,
        "source_ref": args.source_ref,
        "assignment_packet": str(artifact_dir / "assignment.md"),
        "dispatch_ref": dispatch_ref(args),
        "accepted_proof": accepted_proof,
        "dispatched_at": dispatched_at,
        "recorded_by": args.recorded_by,
        "packet": dispatch_packet(args, assignment, artifact_dir),
    }


def setup_needed_payload(args: argparse.Namespace, reason: str, assignment: dict[str, Any] | None = None, artifact_dir: Path | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "dry_run": bool(args.dry_run),
        "status": "setup-needed",
        "work_unit_id": args.work_unit_id,
        "runtime": args.runtime,
        "adapter": getattr(args, "adapter", ""),
        "reason": reason,
        "would_write_dispatch": False,
        "would_append_progress": False,
        "would_spawn_runtime": False,
    }
    if assignment is not None and artifact_dir is not None:
        payload["dispatch_packet"] = dispatch_packet(args, assignment, artifact_dir)
    return payload


def print_dispatch_failure(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"error: {payload['status']}: {payload['reason']}", file=sys.stderr)


def dispatch_capacity_failure(args: argparse.Namespace, artifact_root: Path) -> dict[str, Any] | None:
    max_concurrent = args.capacity_max_concurrent
    capacity_config_source = "cli-override"
    capacity_warnings: list[str] = []
    if max_concurrent is None:
        value, warning = read_openclaw_config_value("agents.defaults.maxConcurrent")
        if value is None:
            max_concurrent = recommended_main_concurrency(DEFAULT_COMPANY_OPS_AGENT_COUNT)
            capacity_config_source = "recommended-fallback"
            capacity_warnings.append(
                warning
                or "agents.defaults.maxConcurrent unreadable; using recommended value for dispatch capacity"
            )
        else:
            max_concurrent = value
            capacity_config_source = "openclaw-config"
    if max_concurrent < 1:
        return setup_needed_payload(args, "capacity config invalid: --capacity-max-concurrent must be >= 1")
    if args.capacity_reserved_slots < 0:
        return setup_needed_payload(args, "capacity config invalid: --capacity-reserved-slots must be >= 0")
    cap = active_wu_cap(max_concurrent, args.capacity_reserved_slots)
    capacity = active_wu_capacity(artifact_root, args.work_unit_id)
    would_exceed = capacity["active_count"] > cap or (capacity["other_active_count"] >= cap and not capacity["current_active"])
    if not would_exceed:
        args.capacity_active_wu_cap = cap
        args.capacity_active_count = capacity["active_count"]
        args.capacity_effective_max_concurrent = max_concurrent
        args.capacity_config_source = capacity_config_source
        args.capacity_warnings = capacity_warnings
        return None
    payload = setup_needed_payload(
        args,
        (
            "capacity-full: Company Ops active WU cap reached "
            f"({capacity['other_active_count']} active other Work Units, cap {cap})"
        ),
    )
    payload.update(
        {
            "status": "capacity-full",
            "capacity": {
                **capacity,
                "effective_maxConcurrent": max_concurrent,
                "reserved_slots": args.capacity_reserved_slots,
                "company_ops_active_wu_cap": cap,
                "config_source": capacity_config_source,
                "warnings": capacity_warnings,
            },
            "next_action": "Close or revise existing active Work Units, or explicitly raise OpenClaw capacity after preflight.",
        }
    )
    return payload


def dispatch_work_unit(args: argparse.Namespace) -> int:
    artifact_root = args.artifact_root.expanduser()
    artifact_dir = artifact_root / args.work_unit_id
    if not artifact_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {artifact_dir}", file=sys.stderr)
        return 1
    assignment = parse_markdown_source(artifact_dir / "assignment.md")
    if not assignment.get("exists"):
        print(f"error: assignment.md is missing: {artifact_dir / 'assignment.md'}", file=sys.stderr)
        return 1
    if not args.team:
        args.team = assignment["fields"].get("assigned team lead openclaw agent", "")
    if not args.team:
        print("error: dispatch requires --team when assignment.md does not name a Team Lead", file=sys.stderr)
        return 1
    if not args.agent:
        args.agent = args.team
    if not args.mode:
        args.mode = clean_markdown_value(str(assignment["fields"].get("mode") or ""))
    default_session_key = normalized_session_key(args.work_unit_id, args.team)
    session_key_provided = bool(args.session_key)
    if not args.session_key:
        args.session_key = default_session_key
    args.default_session_key = default_session_key
    args.session_key_strategy = session_key_strategy(args.session_key, default_session_key)
    args.session_key_provided = session_key_provided
    if (
        args.runtime == "openclaw-agent"
        and args.session_key_strategy != "work-unit-specific"
        and not args.allow_custom_session_key
    ):
        print(
            "error: openclaw-agent dispatch uses the fresh Work Unit-specific session key by default; "
            "pass --allow-custom-session-key only for an intentional existing/custom session",
            file=sys.stderr,
        )
        return 1
    if not args.source_ref:
        print("error: dispatch requires --source-ref", file=sys.stderr)
        return 1
    if args.adapter_timeout_seconds < 1:
        print("error: dispatch requires --adapter-timeout-seconds >= 1", file=sys.stderr)
        return 1
    if not local_source_ref_exists(args.source_ref, artifact_dir):
        print(f"error: dispatch source_ref does not exist: {args.source_ref}", file=sys.stderr)
        return 1
    proof_log = args.proof_log.expanduser() if args.proof_log else artifact_dir / DEFAULT_PROOF_LOG_NAME
    if not progress_has_transition(artifact_dir / "progress.jsonl", args.work_unit_id, {"start", "started"}):
        print("error: dispatch requires prior STARTED source event", file=sys.stderr)
        return 1
    if assignment_requires_live_visibility(assignment) and not proof_has_event(proof_log, args.work_unit_id, "STARTED"):
        print("error: dispatch requires prior STARTED visibility proof for discord-bound Work Units", file=sys.stderr)
        return 1
    capacity_failure = dispatch_capacity_failure(args, artifact_root)
    if capacity_failure:
        print_dispatch_failure(args, capacity_failure)
        return 1
    dispatch_path = artifact_dir / "dispatch.json"
    if not args.force:
        if dispatch_path.exists():
            print("error: dispatch.json already exists; use --force to rerun intentionally", file=sys.stderr)
            return 1
        if progress_has_transition(artifact_dir / "progress.jsonl", args.work_unit_id, {"dispatch", "dispatched"}):
            print("error: DISPATCHED source event already exists; use --force to rerun intentionally", file=sys.stderr)
            return 1
    transition_at = args.transition_at or utc_now_iso()
    args.transition_at = transition_at
    packet = dispatch_packet(args, assignment, artifact_dir)
    accepted_proof: dict[str, Any] | None = None

    if args.publish:
        if args.runtime == "record-ref":
            if not dispatch_ref(args):
                payload = setup_needed_payload(
                    args,
                    "dispatch publish requires --session-ref, --job-ref, or --message-ref",
                    assignment,
                    artifact_dir,
                )
                print_dispatch_failure(args, payload)
                return 1
        else:
            raw_proof, adapter_reason = run_dispatch_adapter(
                args,
                packet=packet,
                artifact_dir=artifact_dir,
                transition_at=transition_at,
            )
            if adapter_reason:
                payload = setup_needed_payload(args, adapter_reason, assignment, artifact_dir)
                print_dispatch_failure(args, payload)
                return 1
            assert raw_proof is not None
            accepted_proof = apply_dispatch_acceptance(args, raw_proof)
            if not dispatch_ref(args):
                payload = setup_needed_payload(
                    args,
                    "runtime adapter accepted proof did not produce a dispatch reference",
                    assignment,
                    artifact_dir,
                )
                print_dispatch_failure(args, payload)
                return 1

    row = dispatch_progress_row(args, transition_at=transition_at, assignment=assignment)
    metadata_error = validate_progress_metadata(row)
    if metadata_error:
        print(f"error: {metadata_error}", file=sys.stderr)
        return 1
    record = dispatch_record(args, assignment, artifact_dir, transition_at, accepted_proof)

    payload = {
        "dry_run": bool(args.dry_run),
        "status": "ready-to-dispatch" if args.dry_run else "dispatched",
        "work_unit_id": args.work_unit_id,
        "runtime": args.runtime,
        "adapter": args.adapter,
        "team": args.team,
        "agent": args.agent,
        "session_key": args.session_key,
        "default_session_key": args.default_session_key,
        "session_key_strategy": args.session_key_strategy,
        "session_key_provided": args.session_key_provided,
        "session_ref": args.session_ref,
        "job_ref": args.job_ref,
        "message_ref": args.message_ref,
        "accepted_proof": accepted_proof,
        "capacity": {
            "effective_maxConcurrent": args.capacity_effective_max_concurrent,
            "reserved_slots": args.capacity_reserved_slots,
            "company_ops_active_wu_cap": args.capacity_active_wu_cap,
            "active_wu_count": args.capacity_active_count,
            "config_source": args.capacity_config_source,
            "warnings": args.capacity_warnings,
        },
        "dispatch_packet": packet,
        "dispatch_record": record,
        "progress_row": row,
        "dispatch_path": str(dispatch_path),
        "would_write_dispatch": bool(args.publish),
        "would_append_progress": bool(args.publish),
        "would_call_runtime_adapter": bool(args.publish and args.runtime != "record-ref"),
        "would_spawn_runtime": False,
        "next_action": (
            "Run publish with a configured runtime adapter, or use record-ref for a manually started session."
            if args.dry_run
            else "Team Lead owns execution until result-ready."
        ),
    }
    if args.dry_run:
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(f"DRY-RUN dispatch {args.work_unit_id}")
            print(f"- Team: {args.team}")
            print(f"- Session key: {args.session_key}")
            print("- No source artifacts, runtime sessions, Project mirrors, or owner reports mutated.")
        return 0

    dispatch_path.write_text(json.dumps(payload["dispatch_record"], indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    progress_path = append_progress_row(artifact_dir, row)
    payload["progress_path"] = str(progress_path)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"OK dispatch recorded: {args.work_unit_id} · {args.team} · {dispatch_ref(args)}")
    return 0


def start_work_unit(args: argparse.Namespace) -> int:
    artifact_root = args.artifact_root.expanduser()
    artifact_dir = artifact_root / args.work_unit_id
    if not artifact_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {artifact_dir}", file=sys.stderr)
        return 1
    assignment = parse_markdown_source(artifact_dir / "assignment.md")
    if not assignment.get("exists"):
        print(f"error: assignment.md is missing: {artifact_dir / 'assignment.md'}", file=sys.stderr)
        return 1
    claim_path = artifact_dir / "claim.md"
    if not args.team:
        args.team = assignment["fields"].get("assigned team lead openclaw agent", "")
    if not args.team:
        print("error: start requires --team when assignment.md does not name a Team Lead", file=sys.stderr)
        return 1
    if not args.mode:
        args.mode = clean_markdown_value(str(assignment["fields"].get("mode") or ""))
    if not args.source_ref:
        print("error: start requires --source-ref", file=sys.stderr)
        return 1
    if not local_source_ref_exists(args.source_ref, artifact_dir):
        print(f"error: start source_ref does not exist: {args.source_ref}", file=sys.stderr)
        return 1
    transition_at = args.transition_at or utc_now_iso()
    args.transition_at = transition_at
    proof_log = args.proof_log.expanduser() if args.proof_log else artifact_dir / DEFAULT_PROOF_LOG_NAME
    live_required = assignment_requires_live_visibility(assignment)
    if args.publish and live_required and not args.target:
        print("error: discord-bound start requires --target", file=sys.stderr)
        return 1
    if not args.force:
        if progress_has_transition(artifact_dir / "progress.jsonl", args.work_unit_id, {"start", "started"}):
            print("error: STARTED source event already exists; use --force to rerun intentionally", file=sys.stderr)
            return 1
        if proof_has_event(proof_log, args.work_unit_id, "STARTED"):
            print("error: STARTED proof already exists; use --force to rerun intentionally", file=sys.stderr)
            return 1
    try:
        updated_claim = render_started_claim_text(
            claim_path,
            team=args.team,
            transition_at=transition_at,
            source_ref=args.source_ref,
        )
        card, text = started_card(args, assignment)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: start preflight failed: {exc}", file=sys.stderr)
        return 1

    projected_row = started_progress_row(args, transition_at=transition_at)
    metadata_error = validate_progress_metadata(projected_row)
    if metadata_error:
        print(f"error: {metadata_error}", file=sys.stderr)
        return 1
    if args.dry_run:
        payload = {
            "dry_run": True,
            "status": "ready-to-start",
            "work_unit_id": args.work_unit_id,
            "card": card,
            "text": text,
            "progress_row": projected_row,
            "claim_path": str(claim_path),
            "would_update_claim": True,
            "would_append_progress": True,
            "would_publish_started": bool(args.target),
            "would_mutate_project": False,
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(text)
            print("\nDRY-RUN start: no claim, progress, Discord proof, or Project mirror mutated.")
        return 0

    publish_payload: dict[str, Any] = {"enabled": bool(args.target)}
    proof_ref = ""
    if args.target:
        publish_code, publish_payload, publish_error = publish_card(args, card, proof_log)
        if publish_code != 0:
            print(publish_error or "error: STARTED publish failed", file=sys.stderr)
            return 1
        proof = publish_payload.get("publish") or {}
        proof_ref = str(proof_log)
        if proof.get("proof_id"):
            proof_ref = f"{proof_ref}#{proof['proof_id']}"

    claim_path.write_text(updated_claim, encoding="utf-8")
    progress_path = append_progress_row(
        artifact_dir,
        started_progress_row(args, transition_at=transition_at, proof_ref=proof_ref),
    )
    project_sync = run_project_sync(args)
    if project_sync.get("enabled") and not project_sync.get("ok"):
        print(f"warning: Project start sync failed: {project_sync.get('error')}", file=sys.stderr)

    payload = {
        "dry_run": False,
        "status": "started",
        "work_unit_id": args.work_unit_id,
        "publish": publish_payload.get("publish", publish_payload),
        "claim_path": str(claim_path),
        "progress_path": str(progress_path),
        "project_sync": project_sync,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"started {args.work_unit_id}: {progress_path}")
    return 0


def checkpoint_work_unit(args: argparse.Namespace) -> int:
    output_dir = args.output_root.expanduser() / args.work_unit_id
    if not output_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {output_dir}", file=sys.stderr)
        return 1
    if not args.dry_run and not args.publish:
        print("error: checkpoint requires --dry-run or --publish", file=sys.stderr)
        return 1
    if args.publish and not args.target:
        print("error: --publish requires --target", file=sys.stderr)
        return 1

    transition_at = args.transition_at or utc_now_iso()
    args.transition_at = transition_at
    proof_log = args.proof_log.expanduser() if args.proof_log else output_dir / DEFAULT_PROOF_LOG_NAME
    projected_row = progress_row_from_args(args, transition_at=transition_at, proof_ref="")
    metadata_error = validate_progress_metadata(projected_row)
    if metadata_error:
        print(f"error: {metadata_error}", file=sys.stderr)
        return 1
    source_failures = source_ref_failures_for_row(output_dir, projected_row)
    if source_failures:
        print_gate_failure(
            "checkpoint source_ref preflight failed",
            {"status": "repair-needed", "failures": source_failures},
        )
        return 1
    if normalized_state(str(projected_row.get("transition_kind") or "")) == "result_ready":
        gate = result_ready_gate(args.output_root, args.work_unit_id, projected_progress_rows=[projected_row])
        if not gate["ready"]:
            print_gate_failure("result_ready checkpoint gate failed", gate)
            return 1

    card_code, card_payload, card_error = run_json_command(checkpoint_card_args(args))
    if card_code != 0:
        print(f"error: checkpoint card validation failed: {card_error}", file=sys.stderr)
        return 1
    card = card_payload.get("card") or {}
    text = card_payload.get("text") or ""
    if not isinstance(card, dict) or not text:
        print("error: checkpoint card command returned invalid JSON", file=sys.stderr)
        return 1

    if args.dry_run:
        payload = {
            "dry_run": True,
            "card": card,
            "text": text,
            "progress_row": projected_row,
            "project_sync": {
                "enabled": bool(args.project_sync_field_map),
                "mode": "skipped",
                "reason": "dry-run does not append progress or mutate Project mirror",
            },
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(text)
            print(f"\nDRY-RUN checkpoint progress: {projected_row['work_unit_id']} show_round={str(projected_row['show_round']).lower()}")
        return 0

    publish_code, publish_payload, publish_error = publish_card(args, card, proof_log)
    if publish_code != 0:
        print(publish_error or "error: checkpoint publish failed", file=sys.stderr)
        return 1

    proof = publish_payload.get("publish") or {}
    proof_ref = str(proof_log)
    if proof.get("proof_id"):
        proof_ref = f"{proof_ref}#{proof['proof_id']}"
    progress_row = progress_row_from_args(args, transition_at=transition_at, proof_ref=proof_ref)
    progress_path = append_progress_row(output_dir, progress_row)
    project_sync = run_project_sync(args)
    if project_sync.get("enabled") and not project_sync.get("ok"):
        print(f"warning: Project checkpoint sync failed: {project_sync.get('error')}", file=sys.stderr)

    payload = {
        "dry_run": False,
        "publish": publish_payload.get("publish", {}),
        "progress_path": str(progress_path),
        "progress_row": progress_row,
        "project_sync": project_sync,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"recorded checkpoint {args.work_unit_id}: {progress_path}")
    return 0


def card_from_command(command: list[str], label: str) -> tuple[dict[str, Any], str]:
    code, payload, error = run_json_command(command)
    if code != 0:
        raise RuntimeError(f"{label} card validation failed: {error}")
    card = payload.get("card") or {}
    text = payload.get("text") or ""
    if not isinstance(card, dict) or not text:
        raise RuntimeError(f"{label} card command returned invalid JSON")
    return card, text


def result_ready_card(args: argparse.Namespace, item: dict[str, Any]) -> tuple[dict[str, Any], str]:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "discord_ops.py"),
        "card",
        "--surface",
        "team-detail",
        "--kind",
        "RESULT_READY",
        "--work-unit-id",
        args.work_unit_id,
        "--team",
        args.team or item["team"],
        "--result",
        args.result,
        "--evidence",
        args.evidence,
        "--verification",
        args.verification,
        "--next",
        args.next,
        "--format",
        "json",
    ]
    if args.risks:
        command.extend(["--risks", args.risks])
    if args.source_ref:
        command.extend(["--source", args.source_ref])
    return card_from_command(command, "result-ready")


def perform_closeout_delegate_wake(
    args: argparse.Namespace,
    *,
    artifact_root: Path,
    artifact_dir: Path,
    transition_at: str,
) -> tuple[int, dict[str, Any]]:
    if args.closeout_delegate_runtime == "none":
        return 0, {
            "enabled": False,
            "status": "skipped",
            "reason": "closeout delegate wake was not requested",
        }
    if args.closeout_delegate_runtime != "openclaw-agent":
        return 1, {
            "enabled": True,
            "status": "delegate-wake setup-needed",
            "reason": f"unsupported closeout delegate runtime: {args.closeout_delegate_runtime}",
        }
    if args.closeout_delegate_adapter_timeout_seconds < 1:
        return 1, {
            "enabled": True,
            "status": "delegate-wake setup-needed",
            "reason": "closeout delegate wake requires --closeout-delegate-adapter-timeout-seconds >= 1",
        }
    if not args.closeout_delegate_agent:
        args.closeout_delegate_agent = "main"
    if args.closeout_delegate_agent not in CLOSEOUT_DELEGATE_ALLOWED_AGENTS:
        return 1, {
            "enabled": True,
            "status": "delegate-wake setup-needed",
            "reason": (
                "closeout delegate agent must be one of "
                + ", ".join(CLOSEOUT_DELEGATE_ALLOWED_AGENTS)
            ),
            "would_write_delegate_wake": False,
        }
    item = build_work_unit_readiness(artifact_root, args.work_unit_id)
    assigned_team = str(args.team or item.get("team") or "").strip()
    if assigned_team and args.closeout_delegate_agent == assigned_team:
        return 1, {
            "enabled": True,
            "status": "delegate-wake setup-needed",
            "reason": "closeout delegate agent must be independent from the assigned Team Lead",
            "would_write_delegate_wake": False,
        }
    capacity_failure = closeout_delegate_capacity_failure(args, artifact_root)
    if capacity_failure:
        return 1, capacity_failure
    if not item["result_ready"]:
        return 1, {
            "enabled": True,
            "status": "repair-needed",
            "reason": "closeout delegate wake requires a source-backed result_ready Work Unit",
            "item": item,
        }
    if item["stale_reason"] or item["conflict_reason"] or item["result_ready_blockers"]:
        return 1, {
            "enabled": True,
            "status": "repair-needed",
            "reason": item["stale_reason"] or item["conflict_reason"] or "result_ready gate blockers remain",
            "item": item,
            "would_write_delegate_wake": False,
        }
    if not args.closeout_delegate_session_key:
        args.closeout_delegate_session_key = closeout_delegate_session_key(args.work_unit_id)
    payload = build_closeout_delegate_payload(args, item, artifact_dir, transition_at=transition_at)
    unresolved_targets = [
        name
        for name, target in payload.get("targets", {}).items()
        if isinstance(target, str) and target.startswith("<") and target.endswith(">")
    ]
    if unresolved_targets:
        return 1, {
            "enabled": True,
            "status": "delegate-wake setup-needed",
            "reason": "closeout delegate requires live visibility targets before guarded closeout",
            "missing_targets": unresolved_targets,
            "delegate_payload": payload,
            "would_write_delegate_wake": False,
        }
    wake_path = artifact_dir / CLOSEOUT_DELEGATE_WAKE_FILENAME
    base_payload = {
        "enabled": True,
        "dry_run": bool(args.dry_run),
        "status": "ready-to-delegate-wake" if args.dry_run else "delegate-wake-enqueued",
        "work_unit_id": args.work_unit_id,
        "delegate_agent": args.closeout_delegate_agent,
        "delegate_runtime": args.closeout_delegate_runtime,
        "delegate_session_key": args.closeout_delegate_session_key,
        "closeout_delegate_active_cap": args.closeout_delegate_active_cap,
        "adapter": args.closeout_delegate_adapter,
        "delegate_payload": payload,
        "delegate_payload_hash": closeout_delegate_payload_hash(payload),
        "wake_path": str(wake_path),
        "would_write_delegate_wake": bool(args.publish),
        "would_mutate_decision": False,
        "would_mutate_project_final": False,
    }
    if args.dry_run:
        return 0, base_payload
    if wake_path.exists() and not args.force:
        return 1, {
            **base_payload,
            "status": "delegate-wake setup-needed",
            "reason": f"{CLOSEOUT_DELEGATE_WAKE_FILENAME} already exists; use --force to rerun intentionally",
            "would_write_delegate_wake": False,
        }
    raw_proof, adapter_reason = run_closeout_delegate_adapter(
        args,
        payload=payload,
        artifact_dir=artifact_dir,
        transition_at=transition_at,
    )
    if adapter_reason:
        return 1, closeout_delegate_setup_needed_payload(args, adapter_reason, payload)
    assert raw_proof is not None
    accepted_proof = apply_closeout_delegate_acceptance(args, raw_proof)
    if not closeout_delegate_ref(args):
        return 1, closeout_delegate_setup_needed_payload(
            args,
            "closeout delegate accepted proof did not produce a delegate enqueue reference",
            payload,
        )
    record = closeout_delegate_wake_record(args, payload, accepted_proof, transition_at)
    wake_path.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0, {
        **base_payload,
        "status": "delegate-wake-enqueued",
        "accepted_proof": accepted_proof,
        "record": record,
        "session_ref": args.closeout_delegate_session_ref,
        "job_ref": args.closeout_delegate_job_ref,
        "message_ref": args.closeout_delegate_message_ref,
        "delegate_ref": closeout_delegate_ref(args),
        "would_write_delegate_wake": True,
    }


def closeout_delegate_wake_work_unit(args: argparse.Namespace) -> int:
    artifact_root = args.artifact_root.expanduser()
    artifact_dir = artifact_root / args.work_unit_id
    if not artifact_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {artifact_dir}", file=sys.stderr)
        return 1
    transition_at = args.transition_at or utc_now_iso()
    args.transition_at = transition_at
    code, payload = perform_closeout_delegate_wake(
        args,
        artifact_root=artifact_root,
        artifact_dir=artifact_dir,
        transition_at=transition_at,
    )
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    elif code == 0:
        print(f"{payload['status']} {args.work_unit_id}: {payload.get('delegate_ref') or payload.get('wake_path')}")
    else:
        print(f"error: {payload.get('status')}: {payload.get('reason')}", file=sys.stderr)
    return code


def result_ready_work_unit(args: argparse.Namespace) -> int:
    artifact_root = args.artifact_root.expanduser()
    artifact_dir = artifact_root / args.work_unit_id
    if not artifact_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {artifact_dir}", file=sys.stderr)
        return 1
    if args.publish and not args.target:
        print("error: --publish requires --target", file=sys.stderr)
        return 1

    pre_gate = result_ready_gate(artifact_root, args.work_unit_id, require_live_visibility=False)
    if not pre_gate["ready"]:
        print_gate_failure("result-ready pre-publish gate failed", pre_gate)
        return 1
    if args.source_ref and not local_source_ref_exists(args.source_ref, artifact_dir):
        print(f"error: result-ready source_ref does not exist: {args.source_ref}", file=sys.stderr)
        return 1
    item = build_work_unit_readiness(artifact_root, args.work_unit_id)
    if not (args.team or item["team"]):
        print("error: result-ready requires --team when source artifacts do not name a Team Lead", file=sys.stderr)
        return 1

    try:
        card, text = result_ready_card(args, item)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    proof_log = args.proof_log.expanduser() if args.proof_log else artifact_dir / DEFAULT_PROOF_LOG_NAME
    existing_proofs, proof_warnings = proof_rows_for_work_unit(proof_log, args.work_unit_id)
    existing_result_ready = [
        row
        for row in existing_proofs
        if row.get("surface") == "team-detail"
        and row.get("kind") == "RESULT_READY"
        and row.get("readback_ok") is not False
    ]
    if args.publish and existing_result_ready and not args.force:
        payload = {
            "dry_run": False,
            "status": "already-result-ready",
            "work_unit_id": args.work_unit_id,
            "pre_publish_gate": pre_gate,
            "existing_result_ready_count": len(existing_result_ready),
            "latest_result_ready": existing_result_ready[-1],
            "would_publish_result_ready": False,
            "would_mutate_project": False,
            "delegate_wake": {
                "mode": "skipped",
                "reason": "existing RESULT_READY proof makes this retry idempotent",
            },
            "next_action": (
                "Use work-unit inbox --result-ready or work-unit delegate-wake "
                "to recover closeout delegate setup if closeout has not started."
            ),
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(f"already result-ready {args.work_unit_id}: {existing_result_ready[-1].get('proof_id', '')}")
            print(f"next: {payload['next_action']}")
        return 0
    if args.dry_run:
        payload = {
            "dry_run": True,
            "status": "ready-to-publish",
            "work_unit_id": args.work_unit_id,
            "pre_publish_gate": pre_gate,
            "card": card,
            "text": text,
            "would_publish_result_ready": True,
            "would_append_proof": False,
            "would_mutate_project": False,
            "existing_result_ready_count": len(existing_result_ready),
            "proof_warnings": proof_warnings,
            "post_publish_gate": {
                "mode": "skipped",
                "reason": "dry-run does not publish/read back RESULT_READY proof",
            },
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(text)
            print("\nDRY-RUN result-ready: source gate passed; no Discord proof or Project mirror mutated.")
        return 0

    publish_code, publish_payload, publish_error = publish_card(args, card, proof_log)
    if publish_code != 0:
        print(publish_error or "error: result-ready publish failed", file=sys.stderr)
        return 1

    post_gate = result_ready_gate(artifact_root, args.work_unit_id, require_live_visibility=True)
    if not post_gate["ready"]:
        print_gate_failure("result-ready post-publish proof gate failed", post_gate)
        return 1
    project_sync = run_project_sync(args)
    if project_sync.get("enabled") and not project_sync.get("ok"):
        print(f"warning: Project result-ready sync failed: {project_sync.get('error')}", file=sys.stderr)
    delegate_wake_code, delegate_wake = perform_closeout_delegate_wake(
        args,
        artifact_root=artifact_root,
        artifact_dir=artifact_dir,
        transition_at=args.transition_at or utc_now_iso(),
    )
    delegate_wake_status = commit_request_text(delegate_wake.get("status")) if isinstance(delegate_wake, dict) else ""

    payload = {
        "dry_run": False,
        "status": "published" if delegate_wake_code == 0 else delegate_wake_status or "delegate-wake setup-needed",
        "work_unit_id": args.work_unit_id,
        "pre_publish_gate": pre_gate,
        "publish": publish_payload.get("publish", {}),
        "post_publish_gate": post_gate,
        "project_sync": project_sync,
        "delegate_wake": delegate_wake,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"published result-ready {args.work_unit_id}: {payload['publish'].get('proof_id', '')}")
        if delegate_wake_code != 0:
            print(f"warning: closeout delegate wake failed: {delegate_wake.get('reason')}", file=sys.stderr)
    return delegate_wake_code


class CloseoutLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.acquired = False

    def __enter__(self) -> "CloseoutLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.mkdir()
        except FileExistsError as exc:
            raise RuntimeError(f"closeout lock already exists: {self.path}") from exc
        self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if not self.acquired:
            return
        try:
            self.path.rmdir()
        except FileNotFoundError:
            pass


def inbox_result_ready(args: argparse.Namespace) -> int:
    artifact_root = args.artifact_root.expanduser()
    work_units = iter_work_unit_ids(artifact_root, args.work_unit_id)
    items = [build_work_unit_readiness(artifact_root, work_unit) for work_unit in work_units]
    if args.team:
        items = [item for item in items if item["team"] == args.team]
    if args.result_ready:
        items = [item for item in items if item["result_ready"]]
    if not args.include_stale and not args.work_unit_id:
        items = [item for item in items if item["actionable"]]
    items.sort(key=lambda item: item["sort_key"])
    if args.limit:
        items = items[: args.limit]

    payload = {
        "artifact_root": str(artifact_root),
        "items": items,
        "count": len(items),
        "source": "local-source-artifacts",
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if not items:
        print("No result-ready Work Units found.")
        return 0
    for item in items:
        flags = []
        if item["stale_reason"]:
            flags.append(f"stale={item['stale_reason']}")
        if item["conflict_reason"]:
            flags.append(f"conflict={item['conflict_reason']}")
        if item["result_ready_blockers"]:
            flags.append(f"repair-needed={len(item['result_ready_blockers'])}")
        if item["warnings"]:
            flags.append(f"warnings={len(item['warnings'])}")
        suffix = f" ({'; '.join(flags)})" if flags else ""
        print(
            f"{item['work_unit_id']} · {item['team'] or 'unknown-team'} · "
            f"{item['result_ready_at'] or 'no-proof-time'} · {item['evidence_path']}{suffix}"
        )
    return 0


def closeout_decision_source_refs(args: argparse.Namespace) -> list[str]:
    refs = [args.source_ref] if args.source_ref else []
    if args.blocker_source:
        refs.append(args.blocker_source)
    return refs


def parse_commit_request_value(value: str) -> dict[str, Any]:
    raw = value.strip()
    if not raw:
        return {}
    if raw.startswith("@"):
        raw = Path(raw[1:]).expanduser().read_text(encoding="utf-8")
    else:
        candidate_path = Path(raw).expanduser()
        if raw.endswith(".json") and candidate_path.exists():
            raw = candidate_path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--commit-request is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--commit-request must be a JSON object")
    return parsed


def commit_request_text(value: Any) -> str:
    return str(value or "").strip()


def commit_request_hashes(value: dict[str, Any]) -> dict[str, Any]:
    hashes = value.get("artifact_hashes")
    if isinstance(hashes, dict):
        return hashes
    source_snapshot = value.get("source_snapshot")
    if isinstance(source_snapshot, dict) and isinstance(source_snapshot.get("artifact_hashes"), dict):
        return source_snapshot["artifact_hashes"]
    return {}


def commit_request_result_ready_proof_id(value: dict[str, Any]) -> str:
    for key in ("result_ready_proof_id", "proof_id"):
        candidate = commit_request_text(value.get(key))
        if candidate:
            return candidate
    result_ready = value.get("result_ready")
    if isinstance(result_ready, dict):
        return commit_request_text(result_ready.get("proof_id"))
    return ""


def commit_request_ref(value: dict[str, Any], *keys: str) -> str:
    for key in keys:
        candidate = commit_request_text(value.get(key))
        if candidate:
            return candidate
    delegate = value.get("delegate")
    if isinstance(delegate, dict):
        for key in keys:
            candidate = commit_request_text(delegate.get(key))
            if candidate:
                return candidate
    return ""


def red_line_check_is_clear(value: Any) -> bool:
    if isinstance(value, dict):
        status = commit_request_text(value.get("status") or value.get("result") or value.get("decision")).lower()
        if status not in {"clear", "passed", "pass", "no_red_line", "none"}:
            return False
        for category in CLOSEOUT_RED_LINE_CATEGORIES:
            if commit_request_text(value.get(category)).lower() not in {"clear", "passed", "pass", "no_red_line", "none"}:
                return False
        return True
    return commit_request_text(value).lower() in {"clear", "passed", "pass", "no_red_line", "none"}


def red_line_check_failures(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["commit-request red_line_check must be a structured object with all red-line categories clear"]
    failures: list[str] = []
    status = commit_request_text(value.get("status") or value.get("result") or value.get("decision")).lower()
    if status not in {"clear", "passed", "pass", "no_red_line", "none"}:
        failures.append("commit-request red_line_check.status must be clear")
    for category in CLOSEOUT_RED_LINE_CATEGORIES:
        category_value = commit_request_text(value.get(category)).lower()
        if category_value not in {"clear", "passed", "pass", "no_red_line", "none"}:
            failures.append(f"commit-request red_line_check.{category} must be clear")
    return failures


def validate_closeout_authority(args: argparse.Namespace, item: dict[str, Any], request: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    role = commit_request_text(getattr(args, "authority_role", ""))
    if role not in CLOSEOUT_PUBLISH_AUTHORITY_ROLES:
        failures.append(
            "closeout publish requires --authority-role operations-lead "
            "or --authority-role operations-lead-delegate"
        )
    if role == "operations-lead-delegate":
        agent = commit_request_text(getattr(args, "delegate_agent", "")) or commit_request_ref(request, "delegate_agent", "agent")
        if agent not in CLOSEOUT_DELEGATE_ALLOWED_AGENTS:
            failures.append("delegated closeout requires --delegate-agent main")
        assigned_team = commit_request_text(item.get("team"))
        if assigned_team and agent == assigned_team:
            failures.append("delegated closeout agent must be independent from the assigned Team Lead")
        boundary = commit_request_text(request.get("authority_boundary"))
        if boundary and boundary != CLOSEOUT_DELEGATE_AUTHORITY_BOUNDARY:
            failures.append(
                "commit-request authority_boundary must be closeout_delegate_guarded_closeout_only"
            )
    return failures


def apply_closeout_commit_request(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    if not getattr(args, "commit_request", ""):
        args.commit_request_payload = {}
        return {}, []
    failures: list[str] = []
    try:
        request = parse_commit_request_value(args.commit_request)
    except ValueError as exc:
        args.commit_request_payload = {}
        return {}, [str(exc)]
    request_wu = commit_request_text(request.get("work_unit_id"))
    if request_wu != args.work_unit_id:
        failures.append("commit-request work_unit_id mismatch")

    def set_or_reject(attr: str, key: str) -> None:
        value = commit_request_text(request.get(key))
        current = commit_request_text(getattr(args, attr, ""))
        if not value:
            return
        if current and current != value:
            failures.append(f"commit-request {key} conflicts with --{attr.replace('_', '-')}")
        else:
            setattr(args, attr, value)

    set_or_reject("decision", "decision")
    set_or_reject("reason", "reason")
    set_or_reject("source_ref", "source_ref")
    set_or_reject("outcome", "outcome")
    set_or_reject("criteria_result", "criteria_result")
    set_or_reject("verification", "verification")
    set_or_reject("needed", "needed")
    set_or_reject("blocker_source", "blocker_source")
    set_or_reject("next_owner", "next_owner")
    set_or_reject("next", "next")
    set_or_reject("recorded_by", "recorded_by")
    authority_role = commit_request_text(request.get("authority_role"))
    if authority_role:
        current = commit_request_text(getattr(args, "authority_role", ""))
        if current and current not in {"operations-lead", authority_role}:
            failures.append("commit-request authority_role conflicts with --authority-role")
        else:
            setattr(args, "authority_role", authority_role)
    delegate_agent = commit_request_text(request.get("delegate_agent"))
    if delegate_agent and not commit_request_text(getattr(args, "delegate_agent", "")):
        setattr(args, "delegate_agent", delegate_agent)
    args.commit_request_payload = request
    return request, failures


def validate_closeout_commit_request(
    args: argparse.Namespace,
    request: dict[str, Any],
    item: dict[str, Any],
    artifact_dir: Path,
    *,
    partial_resume: bool = False,
) -> list[str]:
    if not request:
        return []
    failures: list[str] = []
    decision = commit_request_text(request.get("decision"))
    if decision not in FINAL_REVIEW_BY_DECISION:
        failures.append("commit-request decision must be accept, revise, or blocked")
    if not commit_request_text(request.get("reason")):
        failures.append("commit-request reason is required")
    if not commit_request_text(request.get("source_ref")):
        failures.append("commit-request source_ref is required")

    proof_id = commit_request_result_ready_proof_id(request)
    if not proof_id:
        failures.append("commit-request result_ready_proof_id is required")
    else:
        proof_ids = [
            commit_request_text(row.get("proof_id") or row.get("message_id") or row.get("id"))
            for row in result_ready_proof_rows(artifact_dir / DEFAULT_PROOF_LOG_NAME, args.work_unit_id)
        ]
        result_ready_source = commit_request_text(item.get("result_ready_source"))
        if proof_id not in proof_ids and not result_ready_source.endswith(f"#{proof_id}"):
            failures.append("commit-request result_ready_proof_id does not match current RESULT_READY proof")

    expected_hashes = artifact_hashes_for_closeout_delegate(artifact_dir, args.work_unit_id)
    supplied_hashes = commit_request_hashes(request)
    for key in CLOSEOUT_COMMIT_REQUEST_REQUIRED_HASHES:
        if key not in supplied_hashes:
            failures.append(f"commit-request artifact_hashes missing {key}")
            continue
        if partial_resume and key == DEFAULT_PROOF_LOG_NAME:
            continue
        if supplied_hashes.get(key) != expected_hashes.get(key):
            failures.append(f"commit-request artifact hash mismatch: {key}")

    autonomy_class = commit_request_text(request.get("autonomy_class"))
    if autonomy_class not in CLOSEOUT_AUTONOMY_CLASSES:
        failures.append("commit-request autonomy_class is invalid or missing")
    elif autonomy_class == "manual_required":
        failures.append("commit-request autonomy_class manual_required cannot auto-commit")
    if not commit_request_text(request.get("review_depth")):
        failures.append("commit-request review_depth is required")
    failures.extend(red_line_check_failures(request.get("red_line_check")))
    if not (
        commit_request_ref(request, "delegate_session_ref", "session_ref")
        or commit_request_ref(request, "delegate_job_ref", "job_ref", "run_ref")
        or commit_request_ref(request, "delegate_message_ref", "message_ref")
    ):
        failures.append("commit-request requires a delegate session, job, run, or message ref")
    return failures


def decision_ready_summary(item: dict[str, Any], decision: str, reason: str) -> tuple[dict[str, str], list[str]]:
    evidence_path = Path(str(item.get("evidence_path") or ""))
    failures: list[str] = []
    evidence_text = ""
    if evidence_path.exists():
        evidence_text = evidence_path.read_text(encoding="utf-8")
    elif decision in {"accept", "revise"}:
        failures.append(f"Evidence & Result Record not found: {evidence_path}")

    result_summary = markdown_section(evidence_text, "Result Summary") if evidence_text else ""
    verification = markdown_section(evidence_text, "Verification Performed") if evidence_text else ""
    risks = markdown_section(evidence_text, "Remaining Risks") if evidence_text else ""
    done_mapping = markdown_section(evidence_text, "Done Criteria Mapping") if evidence_text else ""

    if decision in {"accept", "revise"} and low_information_summary(result_summary):
        failures.append("Evidence Result Summary is missing, placeholder, or too low-information for Work Card summary")
    if decision in {"accept", "revise"} and low_information_summary(verification):
        failures.append("Evidence Verification Performed is missing, placeholder, or too low-information for Work Card summary")
    if decision == "blocked" and low_information_summary(reason):
        failures.append("blocked closeout requires a concrete reason for Work Card summary")

    return {
        "result_summary": compact_summary_text(result_summary or reason),
        "verification": compact_summary_text(verification or "Operations Lead reviewed source artifacts."),
        "remaining_risks": compact_summary_text(risks or "None recorded."),
        "done_criteria_mapping": compact_summary_text(done_mapping, limit=500),
    }, failures


def work_card_summary_state(args: argparse.Namespace, item: dict[str, Any]) -> dict[str, Any]:
    mode = getattr(args, "work_card_summary_mode", "required")
    work_card = str(item.get("work_card") or "")
    parts = github_work_card_parts(work_card)
    state = {
        "mode": mode,
        "required": mode == "required",
        "sync_state": "not_configured" if mode == "disabled" else "not_attempted",
        "work_card": work_card,
        "github_issue": parts,
        "ok": False,
        "error": "",
    }
    if mode == "disabled":
        return state
    if not work_card:
        state.update({"sync_state": "work_card_missing", "error": "Work Card summary required but source Work Card is missing"})
    elif not parts:
        state.update({"sync_state": "non_github_work_card", "error": "Work Card summary required but Work Card is not a GitHub issue or pull request URL"})
    return state


def validate_work_card_summary(args: argparse.Namespace, item: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    state = work_card_summary_state(args, item)
    if state["required"] and state["error"]:
        failures.append(state["error"])
    if state["required"] and getattr(args, "decision", ""):
        _, summary_failures = decision_ready_summary(item, args.decision, args.reason)
        failures.extend(summary_failures)
    return failures


def render_work_card_summary_comment(
    args: argparse.Namespace,
    item: dict[str, Any],
    *,
    decided_at: str,
    decision_path: Path,
) -> dict[str, Any]:
    summary, failures = decision_ready_summary(item, args.decision, args.reason)
    if failures:
        return {"ok": False, "error": "; ".join(failures), "body": ""}
    status = DECISION_STATUS_BY_DECISION[args.decision]
    marker = WORK_CARD_SUMMARY_MARKER_TEMPLATE.format(work_unit_id=args.work_unit_id)
    evidence_ref = safe_source_artifact_ref(args.source_ref or item["evidence_path"], work_unit_id=args.work_unit_id)
    decision_ref = safe_source_artifact_ref(decision_path, work_unit_id=args.work_unit_id)
    next_action = args.next or args.next_owner or ("Owner may inspect the accepted Work Unit." if args.decision == "accept" else "See source decision for next action.")
    body = f"""{marker}
## Company Ops Result Summary

Work Unit: `{args.work_unit_id}`
Decision: `{status}`
Source of truth: source artifacts, not this GitHub comment.

### Result
{summary["result_summary"]}

### Verification
{summary["verification"]}

### Remaining Risks
{summary["remaining_risks"]}

### Next Action
{compact_summary_text(next_action, limit=300)}

### Source Artifacts
- Evidence: `{evidence_ref}`
- Decision: `{decision_ref}`
- Work Card: {item.get("work_card") or "missing"}

Published by guarded Company Ops closeout at `{decided_at}`.
"""
    return {
        "ok": True,
        "marker": marker,
        "body": body.strip() + "\n",
        "summary": summary,
    }


def run_gh_api(endpoint: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, Any, str]:
    command = ["gh", "api", endpoint]
    if method != "GET":
        command.extend(["-X", method])
    tmp_path: Path | None = None
    try:
        if payload is not None:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
                json.dump(payload, handle, ensure_ascii=False)
                tmp_path = Path(handle.name)
            command.extend(["--input", str(tmp_path)])
        result = subprocess.run(command, check=False, text=True, capture_output=True)
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass
    if result.returncode != 0:
        return result.returncode, None, result.stderr.strip() or result.stdout.strip()
    if not result.stdout.strip():
        return 0, None, ""
    try:
        return 0, json.loads(result.stdout), ""
    except json.JSONDecodeError as exc:
        return 1, None, f"gh api returned invalid JSON: {exc}"


def fetch_github_issue_comments(parts: dict[str, str], *, per_page: int = 100) -> tuple[int, list[dict[str, Any]], str]:
    comments: list[dict[str, Any]] = []
    for page in range(1, 101):
        endpoint = (
            f"repos/{parts['owner']}/{parts['repo']}/issues/{parts['number']}/comments"
            f"?per_page={per_page}&page={page}"
        )
        code, page_comments, error = run_gh_api(endpoint)
        if code != 0:
            return code, comments, error
        if not isinstance(page_comments, list):
            return 1, comments, "gh api returned non-list issue comments"
        comments.extend(comment for comment in page_comments if isinstance(comment, dict))
        if len(page_comments) < per_page:
            return 0, comments, ""
    return 1, comments, "issue comments pagination exceeded 100 pages"


def publish_work_card_summary_comment(
    args: argparse.Namespace,
    item: dict[str, Any],
    *,
    decided_at: str,
    decision_path: Path,
) -> dict[str, Any]:
    state = work_card_summary_state(args, item)
    if not state["required"]:
        return state
    if state["error"]:
        state["ok"] = False
        return state
    rendered = render_work_card_summary_comment(args, item, decided_at=decided_at, decision_path=decision_path)
    if not rendered.get("ok"):
        state.update({"ok": False, "sync_state": "source_summary_invalid", "error": rendered.get("error", "")})
        return state
    body = rendered["body"]
    parts = state["github_issue"]
    issue_comments_endpoint = f"repos/{parts['owner']}/{parts['repo']}/issues/{parts['number']}/comments"
    code, comments, error = fetch_github_issue_comments(parts)
    if code != 0:
        state.update({"ok": False, "sync_state": "readback_failed", "error": error})
        return state
    existing = None
    for comment in comments:
        if rendered["marker"] in str(comment.get("body") or ""):
            existing = comment
            break
    if existing:
        comment_id = existing.get("id")
        code, response, error = run_gh_api(
            f"repos/{parts['owner']}/{parts['repo']}/issues/comments/{comment_id}",
            method="PATCH",
            payload={"body": body},
        )
    else:
        code, response, error = run_gh_api(issue_comments_endpoint, method="POST", payload={"body": body})
    if code != 0:
        state.update({"ok": False, "sync_state": "comment_write_failed", "error": error})
        return state
    if not isinstance(response, dict) or rendered["marker"] not in str(response.get("body") or ""):
        state.update({"ok": False, "sync_state": "readback_mismatch", "error": "created/updated comment readback did not contain managed marker"})
        return state
    state.update(
        {
            "ok": True,
            "sync_state": "attempted_ok",
            "comment_id": response.get("id"),
            "comment_url": response.get("html_url") or response.get("url") or "",
            "marker": rendered["marker"],
            "rendered_summary": rendered["summary"],
        }
    )
    return state


def validate_closeout_decision(
    args: argparse.Namespace,
    item: dict[str, Any],
    artifact_dir: Path,
    *,
    partial_resume: bool = False,
) -> list[str]:
    failures: list[str] = []
    decision = args.decision
    expected_final_review = FINAL_REVIEW_BY_DECISION.get(decision, "")
    expected_owner_closeout = OWNER_CLOSEOUT_BY_DECISION.get(decision, "")
    if item["decision_final"] and not partial_resume:
        failures.append("decision.md already records a final Operations Lead decision")
    if item["conflict_reason"]:
        failures.append(item["conflict_reason"])
    if item["final_reviews"] and not (
        partial_resume and proof_contains_only_expected(item["final_reviews"], expected_final_review)
    ):
        failures.append("team final review proof already exists")
    if item["owner_closeouts"] and not (
        partial_resume and proof_contains_only_expected(item["owner_closeouts"], expected_owner_closeout)
    ):
        failures.append("owner closeout proof already exists")
    if not args.reason:
        failures.append("--reason is required for explicit closeout decisions")
    if not item.get("work_card"):
        failures.append("closeout decision requires a source Work Card in assignment.md, claim.md, evidence.md, or decision.md")
    failures.extend(validate_work_card_summary(args, item))
    for source_ref in closeout_decision_source_refs(args):
        if not local_source_ref_exists(source_ref, artifact_dir):
            failures.append(f"missing source_ref: {source_ref}")

    if decision in {"accept", "revise"}:
        if not item["result_ready"]:
            failures.append(f"{decision} closeout requires a source-backed result_ready submission")
        if item["result_ready_blockers"]:
            failures.extend(item["result_ready_blockers"])
    elif decision == "blocked":
        if not args.blocker_source:
            failures.append("blocked closeout requires --blocker-source")
        if not args.needed:
            failures.append("blocked closeout requires --needed")
        if not args.next_owner:
            failures.append("blocked closeout requires --next-owner")
    return failures


def closeout_cards(args: argparse.Namespace, item: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], str]:
    team = args.team or item["team"]
    final_kind = FINAL_REVIEW_BY_DECISION[args.decision]
    owner_kind = OWNER_CLOSEOUT_BY_DECISION[args.decision]
    source_ref = args.source_ref or item["evidence_path"]
    next_action = args.next or {
        "accept": "Owner may inspect the accepted Work Unit.",
        "revise": "Team Lead revises the result from Operations Lead feedback.",
        "blocked": f"{args.next_owner} resolves the blocker before closeout can continue.",
    }[args.decision]

    if final_kind == "BLOCKED_DETAIL":
        team_command = [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            final_kind,
            "--work-unit-id",
            args.work_unit_id,
            "--team",
            team,
            "--problem",
            item["title"] or f"{args.work_unit_id} is blocked",
            "--cause",
            args.reason,
            "--needed",
            args.needed,
            "--evidence",
            args.blocker_source or source_ref,
            "--next",
            next_action,
            "--format",
            "json",
        ]
    else:
        team_command = [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            final_kind,
            "--work-unit-id",
            args.work_unit_id,
            "--team",
            team,
            "--decision",
            final_kind,
            "--reason",
            args.reason,
            "--evidence",
            source_ref,
            "--next",
            next_action,
            "--format",
            "json",
        ]
    team_card, team_text = card_from_command(team_command, "closeout team-final")

    if owner_kind == "BLOCKED":
        owner_command = [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            owner_kind,
            "--work-unit-id",
            args.work_unit_id,
            "--team",
            team,
            "--problem",
            item["title"] or f"{args.work_unit_id} is blocked",
            "--cause",
            args.reason,
            "--needed",
            args.needed,
            "--evidence",
            args.blocker_source or source_ref,
            "--team-final-review-kind",
            final_kind,
            "--next",
            next_action,
            "--format",
            "json",
        ]
    else:
        owner_command = [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            owner_kind,
            "--work-unit-id",
            args.work_unit_id,
            "--team",
            team,
            "--outcome",
            args.outcome or args.reason,
            "--criteria-result",
            args.criteria_result or args.reason,
            "--decision",
            final_kind,
            "--verification",
            args.verification or f"Operations Lead reviewed {source_ref}.",
            "--evidence",
            source_ref,
            "--team-final-review-kind",
            final_kind,
            "--next",
            next_action,
            "--format",
            "json",
        ]
    owner_card, owner_text = card_from_command(owner_command, "closeout owner")
    return team_card, team_text, owner_card, owner_text


def render_closeout_decision(args: argparse.Namespace, item: dict[str, Any], decided_at: str) -> str:
    status = DECISION_STATUS_BY_DECISION[args.decision]
    source_refs = closeout_decision_source_refs(args) or [item["evidence_path"]]
    follow_up = args.needed if args.decision == "blocked" else (args.next or "None.")
    commit_request = getattr(args, "commit_request_payload", {}) if isinstance(getattr(args, "commit_request_payload", {}), dict) else {}
    commit_request_section = ""
    if commit_request:
        delegate_refs = [
            value
            for value in (
                commit_request_ref(commit_request, "delegate_session_ref", "session_ref"),
                commit_request_ref(commit_request, "delegate_job_ref", "job_ref", "run_ref"),
                commit_request_ref(commit_request, "delegate_message_ref", "message_ref"),
            )
            if value
        ]
        commit_request_section = f"""
## Guarded Commit Request

- Result-ready proof id: `{commit_request_result_ready_proof_id(commit_request)}`
- Autonomy class: `{commit_request_text(commit_request.get("autonomy_class"))}`
- Review depth: `{commit_request_text(commit_request.get("review_depth"))}`
- Delegate refs: {", ".join(f"`{ref}`" for ref in delegate_refs) if delegate_refs else "`missing`"}
- Artifact snapshot hash: `{canonical_json_hash(commit_request_hashes(commit_request)) if commit_request_hashes(commit_request) else ""}`
"""
    return f"""# Operations Lead Decision

Status: {status}

The Operations Lead decision records whether the submitted result satisfies the
Assignment Packet and evidence requirements.

## Identity

- Decision ref: `DECISION-{args.work_unit_id}`
- Work Unit id: `{args.work_unit_id}`
- Title: {item["title"]}
- Work Card: {item["work_card"]}
- Assignment Packet: `{Path(item["artifact_dir"]) / "assignment.md"}`
- Evidence & Result Record: `{item["evidence_path"]}`
- Operations Lead: `{args.recorded_by}`
- Decided at: `{decided_at}`
- Updated at: `{decided_at}`

## Decision

- `{args.decision}`

## Rationale

{args.reason}

## Source Refs

{markdown_bullets(source_refs)}
{commit_request_section}

## Required Follow-up

- {follow_up}

## Closure Instruction

- Team final review kind: `{FINAL_REVIEW_BY_DECISION[args.decision]}`
- Owner closeout kind: `{OWNER_CLOSEOUT_BY_DECISION[args.decision]}`

## No Fallback Rule

This decision must not be inferred from GitHub labels, dashboard status,
Discord messages, or Team Lead claims.
"""


def write_closeout_card_files(
    artifact_dir: Path,
    args: argparse.Namespace,
    team_card: dict[str, Any],
    owner_card: dict[str, Any],
    *,
    allow_existing: bool = False,
) -> dict[str, Path]:
    suffix = args.decision.replace("_", "-")
    paths = {
        "team_card": artifact_dir / f"team-{suffix}-card.json",
        "owner_card": artifact_dir / f"ops-{OWNER_CLOSEOUT_BY_DECISION[args.decision].lower().replace('_', '-')}-card.json",
    }
    if not args.force and not allow_existing:
        existing = [str(path) for path in paths.values() if path.exists()]
        if existing:
            raise FileExistsError("closeout card output already exists: " + ", ".join(existing))
    if args.force or not paths["team_card"].exists():
        paths["team_card"].write_text(
            json.dumps({"card": team_card}, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    if args.force or not paths["owner_card"].exists():
        paths["owner_card"].write_text(
            json.dumps({"card": owner_card}, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return paths


def read_closeout_stage(stage_path: Path) -> dict[str, Any]:
    if not stage_path.exists():
        return {}
    try:
        parsed = json.loads(stage_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FileExistsError(f"closeout stage is unreadable: {stage_path}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise FileExistsError(f"closeout stage is not a JSON object: {stage_path}")
    return parsed


def closeout_stage_allows_resume(stage: dict[str, Any], args: argparse.Namespace, item: dict[str, Any]) -> bool:
    if not stage:
        return False
    if stage.get("work_unit_id") != args.work_unit_id or stage.get("decision") != args.decision:
        return False
    status = str(stage.get("status") or "")
    if item["decision_final"] and status not in {"project-sync-needed", "work-card-summary-needed"}:
        return False
    return status in {"started", "team-published", "visibility-published", "project-sync-needed", "work-card-summary-needed"}


def proof_contains_only_expected(values: list[str], expected: str) -> bool:
    return bool(values) and set(values) <= {expected}


def write_closeout_stage(
    stage_path: Path,
    *,
    args: argparse.Namespace,
    status: str,
    decided_at: str,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = {
        "version": 1,
        "status": status,
        "work_unit_id": args.work_unit_id,
        "decision": args.decision,
        "decided_at": decided_at,
        "recorded_by": args.recorded_by,
        "commit_request_present": bool(getattr(args, "commit_request_payload", {})),
    }
    if extra:
        payload.update(extra)
    stage_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def closeout_dry_run(args: argparse.Namespace) -> int:
    artifact_root = args.artifact_root.expanduser()
    artifact_dir = artifact_root / args.work_unit_id
    closeout_exit_code = 0
    if not artifact_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {artifact_dir}", file=sys.stderr)
        return 1
    if not args.dry_run and not args.publish:
        print("error: closeout requires --dry-run or --publish", file=sys.stderr)
        return 1
    commit_request, commit_request_failures = apply_closeout_commit_request(args)
    if commit_request_failures:
        payload = {
            "dry_run": bool(args.dry_run),
            "status": "repair-needed",
            "work_unit_id": args.work_unit_id,
            "commit_request": commit_request,
            "decision_failures": commit_request_failures,
            "would_write_decision": False,
            "would_publish_team_final_review": False,
            "would_publish_owner_closeout": False,
            "would_mutate_project": False,
            "next_action": "Repair commit-request before closeout.",
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(f"error: repair-needed: {commit_request_failures[0]}", file=sys.stderr)
        return 1
    if args.publish and not args.decision:
        print("error: --publish requires --decision", file=sys.stderr)
        return 1
    if args.publish and (not args.team_target or not args.ops_target):
        print("error: --publish requires --team-target and --ops-target", file=sys.stderr)
        return 1

    lock_path = args.lock_path.expanduser() if args.lock_path else artifact_dir / ".closeout.lock"
    try:
        with CloseoutLock(lock_path):
            item = build_work_unit_readiness(artifact_root, args.work_unit_id)
            stage_path = artifact_dir / f"closeout-{args.decision.replace('_', '-')}-stage.json" if args.decision else None
            stage_payload = read_closeout_stage(stage_path) if stage_path else {}
            partial_resume = closeout_stage_allows_resume(stage_payload, args, item)
            status = "ready"
            next_action = "Operations Lead reviews source artifacts before any decision write."
            if item["decision_final"]:
                status = "already-decided"
                next_action = "Do not overwrite, reopen, or append a competing decision."
            elif item["conflict_reason"]:
                status = "conflict"
                next_action = "Resolve competing source/proof rows before closeout."
            elif item["result_ready_requested"] and item["result_ready_blockers"]:
                status = "repair-needed"
                next_action = "Repair result_ready gate failures before Operations Lead closeout."
            elif not item["result_ready"]:
                status = "not-result-ready"
                next_action = "Wait for claim/evidence result_ready before closeout."
            elif not item["suggested_final_review_kind"]:
                status = "needs-ops-decision"
                next_action = "Evidence recommendation is missing or ambiguous; Operations Lead must decide."
            decision_failures: list[str] = []
            team_card: dict[str, Any] = {}
            owner_card: dict[str, Any] = {}
            team_text = ""
            owner_text = ""
            decision_preview = ""
            decision_decided_at = ""
            work_card_summary_preview: dict[str, Any] = {}
            if args.decision:
                if stage_payload and not partial_resume and not args.force:
                    decision_failures.append(f"closeout stage already exists: {stage_path}")
                decision_failures.extend(
                    validate_closeout_decision(args, item, artifact_dir, partial_resume=partial_resume)
                )
                decision_failures.extend(validate_closeout_authority(args, item, commit_request))
                decision_failures.extend(
                    validate_closeout_commit_request(
                        args,
                        commit_request,
                        item,
                        artifact_dir,
                        partial_resume=partial_resume,
                    )
                )
                if decision_failures:
                    status = "repair-needed"
                    next_action = "Repair closeout decision failures before publishing final review."
                else:
                    try:
                        team_card, team_text, owner_card, owner_text = closeout_cards(args, item)
                    except RuntimeError as exc:
                        print(f"error: {exc}", file=sys.stderr)
                        return 1
                    decision_decided_at = args.transition_at or utc_now_iso()
                    decision_preview = render_closeout_decision(args, item, decision_decided_at)
                    summary_state = work_card_summary_state(args, item)
                    if summary_state["required"] and not summary_state["error"]:
                        rendered_summary = render_work_card_summary_comment(
                            args,
                            item,
                            decided_at=decision_decided_at,
                            decision_path=artifact_dir / "decision.md",
                        )
                        work_card_summary_preview = {
                            **summary_state,
                            "sync_state": "dry_run_rendered",
                            "ok": True,
                            "planned_body": rendered_summary.get("body", ""),
                            "render_error": rendered_summary.get("error", ""),
                        }
                    else:
                        work_card_summary_preview = summary_state
                    status = "decision-ready"
                    next_action = "Publish records decision.md, team final review, and owner closeout."

            payload = {
                "dry_run": bool(args.dry_run),
                "status": status,
                "work_unit_id": args.work_unit_id,
                "lock_path": str(lock_path),
                "lock_released": True,
                "item": item,
                "decision": args.decision,
                "decision_failures": decision_failures,
                "team_card": team_card,
                "owner_card": owner_card,
                "team_text": team_text,
                "owner_text": owner_text,
                "decision_preview": decision_preview,
                "work_card_summary": work_card_summary_preview,
                "commit_request": commit_request,
                "closeout_stage": stage_payload,
                "partial_resume": partial_resume,
                "resolved_work_card": item.get("work_card", ""),
                "work_card_source": item.get("work_card_source", ""),
                "would_write_decision": bool(args.decision and not decision_failures),
                "would_publish_team_final_review": bool(args.decision and not decision_failures),
                "would_publish_owner_closeout": bool(args.decision and not decision_failures),
                "would_mutate_project": bool(args.project_sync_field_map and args.publish and not decision_failures),
                "next_action": next_action,
                "checks": {
                    "source_artifacts_reread": True,
                    "decision_exists_rechecked": True,
                    "proof_progress_reread": True,
                    "project_dry_run_state": "supported-but-not-mutated",
                },
            }
            if args.dry_run or not args.decision or decision_failures:
                publish_payload = payload
            else:
                decided_at = decision_decided_at
                args.transition_at = decided_at
                proof_log = args.proof_log.expanduser() if args.proof_log else artifact_dir / DEFAULT_PROOF_LOG_NAME
                decision_path = artifact_dir / "decision.md"
                assert stage_path is not None
                if not partial_resume:
                    write_closeout_stage(
                        stage_path,
                        args=args,
                        status="started",
                        decided_at=decided_at,
                        extra={"decision_path": str(decision_path)},
                    )
                card_paths = write_closeout_card_files(
                    artifact_dir,
                    args,
                    team_card,
                    owner_card,
                    allow_existing=partial_resume,
                )
                expected_final_review = FINAL_REVIEW_BY_DECISION[args.decision]
                expected_owner_closeout = OWNER_CLOSEOUT_BY_DECISION[args.decision]
                if proof_contains_only_expected(item["final_reviews"], expected_final_review):
                    team_publish = {"publish": {"skipped": True, "reason": "matching team final review proof already exists"}}
                else:
                    team_code, team_publish, team_error = publish_card(
                        args,
                        team_card,
                        proof_log,
                        target=args.team_target,
                        expect_surface="team-detail",
                    )
                    if team_code != 0:
                        print(team_error or "error: team final review publish failed", file=sys.stderr)
                        return 1
                write_closeout_stage(
                    stage_path,
                    args=args,
                    status="team-published",
                    decided_at=decided_at,
                    extra={
                        "decision_path": str(decision_path),
                        "card_paths": {key: str(value) for key, value in card_paths.items()},
                        "team_publish": team_publish.get("publish", {}),
                    },
                )
                if proof_contains_only_expected(item["owner_closeouts"], expected_owner_closeout):
                    owner_publish = {"publish": {"skipped": True, "reason": "matching owner closeout proof already exists"}}
                else:
                    owner_code, owner_publish, owner_error = publish_card(
                        args,
                        owner_card,
                        proof_log,
                        target=args.ops_target,
                        expect_surface="ops-feed",
                    )
                    if owner_code != 0:
                        print(owner_error or "error: owner closeout publish failed", file=sys.stderr)
                        return 1
                write_closeout_stage(
                    stage_path,
                    args=args,
                    status="visibility-published",
                    decided_at=decided_at,
                    extra={
                        "decision_path": str(decision_path),
                        "card_paths": {key: str(value) for key, value in card_paths.items()},
                        "team_publish": team_publish.get("publish", {}),
                        "owner_publish": owner_publish.get("publish", {}),
                    },
                )
                decision_path.write_text(decision_preview, encoding="utf-8")
                project_sync = run_project_sync(args)
                if project_sync.get("required") and not project_sync.get("ok"):
                    print(f"error: Project closeout sync failed: {project_sync.get('error')}", file=sys.stderr)
                    stage_status = "project-sync-needed"
                    closeout_exit_code = 1
                elif project_sync.get("enabled") and not project_sync.get("ok"):
                    print(f"error: Project closeout sync failed: {project_sync.get('error')}", file=sys.stderr)
                    stage_status = "project-sync-needed"
                    closeout_exit_code = 1
                else:
                    stage_status = "published"
                work_card_summary = work_card_summary_state(args, item)
                if stage_status == "published":
                    work_card_summary = publish_work_card_summary_comment(
                        args,
                        item,
                        decided_at=decided_at,
                        decision_path=decision_path,
                    )
                    if work_card_summary.get("required") and not work_card_summary.get("ok"):
                        print(
                            f"error: Work Card summary failed: {work_card_summary.get('error')}",
                            file=sys.stderr,
                        )
                        stage_status = "work-card-summary-needed"
                        closeout_exit_code = 1
                write_closeout_stage(
                    stage_path,
                    args=args,
                    status=stage_status,
                    decided_at=decided_at,
                    extra={
                        "decision_path": str(decision_path),
                        "card_paths": {key: str(value) for key, value in card_paths.items()},
                        "team_publish": team_publish.get("publish", {}),
                        "owner_publish": owner_publish.get("publish", {}),
                        "project_sync_state": project_sync.get("sync_state", "not_configured"),
                        "project_sync_required": bool(project_sync.get("required")),
                        "work_card_summary": work_card_summary,
                    },
                )
                publish_payload = {
                    **payload,
                    "dry_run": False,
                    "status": stage_status,
                    "decision_path": str(decision_path),
                    "stage_path": str(stage_path),
                    "card_paths": {key: str(value) for key, value in card_paths.items()},
                    "team_publish": team_publish.get("publish", {}),
                    "owner_publish": owner_publish.get("publish", {}),
                    "project_sync": project_sync,
                    "work_card_summary": work_card_summary,
                }
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(publish_payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        prefix = "DRY-RUN" if publish_payload["dry_run"] else "PUBLISHED"
        print(f"{prefix} closeout {args.work_unit_id}: {publish_payload['status']}")
        print(f"- Evidence: {publish_payload['item']['evidence_path']}")
        print(f"- Decision: {publish_payload['item']['decision_path']} status={publish_payload['item']['decision_status'] or 'missing'}")
        print(f"- Suggested review: {publish_payload['item']['suggested_final_review_kind'] or 'needs-ops-decision'}")
        print(f"- Suggested owner closeout: {publish_payload['item']['suggested_owner_closeout_kind'] or 'none'}")
        print(f"- Next: {publish_payload['next_action']}")
    if closeout_exit_code:
        return closeout_exit_code
    return 0 if publish_payload["status"] in {"ready", "needs-ops-decision", "decision-ready", "published"} else 1


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

## Assumptions And Open Questions

List assumptions that are safe to start with and questions that may require an
Operations Lead amendment if they change scope, criteria, cost, risk, or
authority.

-

## Change Log

Record source-backed changes after the initial handoff. Do not erase the
original handoff when execution discovers a better plan or a new issue.

- Initial handoff:
- Amendments:

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
  subagent_budget: <none|2|3|5>
  subagent_budget_reason: <team_lead_direct|simple_delegated|normal|complex_high_risk>
  subagent_budget_enforcement: prompt_and_packet_contract_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: revise_means_operations_lead_replan_then_reenter_selected_mode
```

Subagent budget policy:

- `none`: Team Lead handles the Work Unit directly.
- `2`: simple delegated work.
- `3`: normal goal/verify work.
- `5`: complex, high-risk, or broad verification work.
- More than `5` requires explicit Operations Lead or owner approval.

This budget is an Assignment Packet and package-prompt contract. It is not a
runtime hook, tool policy, or hard enforcement layer.

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

Discord generation budget:

- Keep Discord-facing result text within 1,600 characters.
- Put detailed logs, diffs, and long findings in the Evidence & Result Record or
  another source artifact.
- If the result needs more room, report the artifact path plus a short decision
  summary instead of pasting full detail into Discord.

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

Do not use this field as completion truth. User-facing status derives lifecycle
from source artifacts in this order: final Operations Lead decision, result
evidence/proof, claim responsibility, then assignment. Accepted work remains
`accepted` until owner inspection and Work Card cleanup make it archival
`done`.

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
- `blocked`

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
- `blocked`

## Rationale

Explain the decision using the Assignment Packet and Evidence & Result Record.

## Required Follow-up

-

## Closure Instruction

If accepted:

- Link this decision to the Work Card.
- Link the Evidence & Result Record to the Work Card.
- Keep the Work Card visible for owner inspection until both links exist and
  the owner has had a reasonable chance to inspect it.

If revise:

- Keep the Work Card open.
- Replan the revision before creating a new Team Lead revision assignment.

If blocked:

- Keep the Work Card open.
- Record the blocker source, needed action, and next owner.

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
    capacity = work_unit_subparsers.add_parser(
        "capacity-check",
        help="Read-only Company Ops capacity preflight",
    )
    capacity.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing Work Unit source artifacts",
    )
    capacity.add_argument("--work-unit-id", default="", type=str, help="Optional current Work Unit id")
    capacity.add_argument("--company-ops-agent-count", type=int, default=DEFAULT_COMPANY_OPS_AGENT_COUNT)
    capacity.add_argument("--reserved-slots", type=int, default=DEFAULT_CAPACITY_RESERVED_SLOTS)
    capacity.add_argument("--config-json", type=Path, help="Optional OpenClaw config JSON for offline preflight")
    capacity.add_argument("--openclaw-max-concurrent", type=int, help="Override current agents.defaults.maxConcurrent")
    capacity.add_argument(
        "--openclaw-subagents-max-concurrent",
        type=int,
        help="Override current agents.defaults.subagents.maxConcurrent",
    )
    capacity.add_argument("--format", choices=("text", "json"), default="text")
    capacity.set_defaults(func=capacity_check)

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

    handoff = work_unit_subparsers.add_parser(
        "handoff",
        help="Create and optionally publish the initial ASSIGNED handoff bundle",
    )
    handoff.add_argument("--spec", required=True, type=Path, help="Structured handoff JSON fact packet")
    handoff.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory that will receive <work-unit-id>/",
    )
    handoff.add_argument("--created-at", default="", help="Creation timestamp/date, default: now")
    handoff.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    handoff.add_argument("--channel", default="discord", help="OpenClaw message channel")
    handoff.add_argument("--account", default="", help="OpenClaw channel account id")
    handoff.add_argument("--thread-id", default="", help="Optional Discord thread id")
    handoff.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    handoff.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    handoff.add_argument(
        "--project-sync-field-map",
        default="",
        help="Optional Project field-map JSON; runs mirror sync after successful handoff publish",
    )
    handoff.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync; empty disables ledger",
    )
    handoff.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful Project mirror sync",
    )
    handoff.add_argument(
        "--force",
        action="store_true",
        help="Replace generated handoff artifacts in an existing output directory",
    )
    handoff.add_argument("--format", choices=("text", "json"), default="text")
    handoff_mode = handoff.add_mutually_exclusive_group(required=True)
    handoff_mode.add_argument("--dry-run", action="store_true", help="Validate and preview without writes or sends")
    handoff_mode.add_argument("--publish", action="store_true", help="Write artifacts, publish/read back Discord, then sync Project mirror")
    handoff.set_defaults(func=handoff_work_unit)

    draft_handoff = work_unit_subparsers.add_parser(
        "draft-handoff",
        help="Preview Work Card, Assignment Packet, and handoff spec drafts without mutation",
    )
    draft_handoff.add_argument("--spec", required=True, type=Path, help="Structured draft-handoff JSON fact packet")
    draft_handoff.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Preview root for planned <work-unit-id>/ paths; no files are written",
    )
    draft_handoff.add_argument("--created-at", default="", help="Preview timestamp/date, default: now when complete")
    draft_handoff.add_argument("--dry-run", action="store_true", help="Required; no Work Card, artifact, Discord, or Project mutation")
    draft_handoff.add_argument("--format", choices=("text", "json"), default="text")
    draft_handoff.set_defaults(func=draft_handoff_work_unit)

    amend = work_unit_subparsers.add_parser(
        "amend",
        help="Preview a source-backed handoff amendment without mutation",
    )
    amend.add_argument("--spec", required=True, type=Path, help="Structured amendment JSON fact packet")
    amend.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id>/ source artifacts",
    )
    amend.add_argument("--dry-run", action="store_true", help="Required; no assignment, artifact, Discord, or Project mutation")
    amend.add_argument("--format", choices=("text", "json"), default="text")
    amend.set_defaults(func=amend_work_unit)

    progress = work_unit_subparsers.add_parser(
        "progress",
        help="Append source-backed progress metadata for dashboard sync",
    )
    progress.add_argument("--work-unit-id", required=True, type=work_unit_id)
    progress.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory containing <work-unit-id>/",
    )
    progress.add_argument("--transition-kind", default="checkpoint", type=required)
    progress.add_argument(
        "--mode",
        default="",
        help="Progress mode; goal and convergence automatically display round when present",
    )
    progress.add_argument("--phase", default="", help="Current phase label")
    progress.add_argument("--phase-index", default="", help="Current phase number or label")
    progress.add_argument("--phase-total", default="", help="Known total phase count, if any")
    progress.add_argument("--round", default="", help="Current convergence round, if applicable")
    progress.add_argument(
        "--show-round",
        action="store_true",
        help="Display round in dashboard Progress; use for convergence/goal rounds or explicit owner request",
    )
    progress.add_argument("--current-slice", default="", help="Current execution slice")
    progress.add_argument("--risk-state", default="", help="Progress risk state for display, e.g. at-risk or blocked")
    progress.add_argument("--retry-state", default="", help="Progress retry state for display, e.g. retry or re-run")
    progress.add_argument("--next-checkpoint", default="", help="Next expected checkpoint time/window")
    progress.add_argument("--source-ref", default="", help="Source artifact reference for this progress update")
    progress.add_argument("--proof-ref", default="", help="Optional proof log or Discord proof reference")
    progress.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    progress.add_argument("--recorded-by", default="operations-lead", help="Recorder identity")
    progress.set_defaults(func=append_progress)

    start = work_unit_subparsers.add_parser(
        "start",
        help="Move a Work Unit from assigned to working with a source-backed STARTED transition",
    )
    start.add_argument("--work-unit-id", required=True, type=work_unit_id)
    start.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id>/ source artifacts",
    )
    start.add_argument("--team", default="", help="Team Lead; defaults from assignment.md")
    start.add_argument("--status", default="Team Lead started work.", help="Status line for the STARTED card")
    start.add_argument("--current-slice", default="started", help="Initial execution slice for progress metadata")
    start.add_argument("--next-checkpoint", default="", help="Next expected checkpoint time/window")
    start.add_argument("--mode", default="", help="Progress mode for dashboard sync")
    start.add_argument("--phase", default="", help="Current phase label for dashboard Progress")
    start.add_argument("--phase-index", default="", help="Current phase number or label for dashboard Progress")
    start.add_argument("--phase-total", default="", help="Known total phase count, if any")
    start.add_argument("--round", default="", help="Current goal/convergence round")
    start.add_argument("--source-ref", required=True, help="Source artifact reference for the start decision")
    start.add_argument("--next", default="Publish checkpoint before RESULT_READY if work runs long.", help="Discord next action")
    start.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    start.add_argument("--recorded-by", default="operations-lead", help="Recorder identity")
    start.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    start.add_argument("--target", default="", help="Discord team-detail target for live visibility")
    start.add_argument("--channel", default="discord", help="OpenClaw message channel")
    start.add_argument("--account", default="", help="OpenClaw channel account id")
    start.add_argument("--thread-id", default="", help="Optional Discord thread id")
    start.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    start.add_argument(
        "--project-sync-field-map",
        default="",
        help="Optional Project field-map JSON; runs mirror sync after successful start",
    )
    start.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync; empty disables ledger",
    )
    start.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful Project mirror sync",
    )
    start.add_argument("--force", action="store_true", help="Allow duplicate STARTED proof/source when intentionally rerunning")
    start.add_argument("--format", choices=("text", "json"), default="text")
    start_mode = start.add_mutually_exclusive_group(required=True)
    start_mode.add_argument("--dry-run", action="store_true", help="Validate and preview without writes or sends")
    start_mode.add_argument("--publish", action="store_true", help="Record STARTED source state and optionally publish/read back")
    start.set_defaults(func=start_work_unit)

    dispatch = work_unit_subparsers.add_parser(
        "dispatch",
        help="Record a detached Team Lead execution reference after STARTED",
    )
    dispatch.add_argument("--work-unit-id", required=True, type=work_unit_id)
    dispatch.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id>/ source artifacts",
    )
    dispatch.add_argument("--team", default="", help="Team Lead; defaults from assignment.md")
    dispatch.add_argument("--agent", default="", help="OpenClaw agent id; defaults to --team")
    dispatch.add_argument(
        "--runtime",
        choices=DISPATCH_RUNTIME_CHOICES,
        default="record-ref",
        help="Runtime adapter. record-ref only records an externally started session/job reference.",
    )
    dispatch.add_argument("--session-key", default="", help="Stable planned Team Lead session key")
    dispatch.add_argument("--session-ref", default="", help="Recoverable Team Lead session reference to record")
    dispatch.add_argument("--job-ref", default="", help="Recoverable Team Lead job/task reference to record")
    dispatch.add_argument("--message-ref", default="", help="Recoverable Team Lead dispatch message reference to record")
    dispatch.add_argument(
        "--adapter",
        choices=DISPATCH_ADAPTER_CHOICES,
        default="auto",
        help="Runtime adapter implementation for openclaw-agent. auto uses a configured command; fake is smoke-only.",
    )
    dispatch.add_argument(
        "--adapter-command",
        default="",
        help=f"Command that reads adapter JSON on stdin and returns accepted proof JSON. Defaults from {DISPATCH_ADAPTER_COMMAND_ENV}.",
    )
    dispatch.add_argument(
        "--adapter-timeout-seconds",
        type=int,
        default=30,
        help="Timeout for the runtime adapter command",
    )
    dispatch.add_argument("--source-ref", required=True, help="Source artifact reference for the dispatch decision")
    dispatch.add_argument("--current-slice", default="detached-dispatch", help="Dispatch slice for progress metadata")
    dispatch.add_argument("--next-checkpoint", default="Team Lead reports result-ready or blocker.", help="Next expected checkpoint")
    dispatch.add_argument("--mode", default="", help="Progress mode; defaults from assignment.md")
    dispatch.add_argument("--phase", default="", help="Current phase label for dashboard Progress")
    dispatch.add_argument("--phase-index", default="", help="Current phase number or label for dashboard Progress")
    dispatch.add_argument("--phase-total", default="", help="Known total phase count, if any")
    dispatch.add_argument("--round", default="", help="Current goal/convergence round")
    dispatch.add_argument(
        "--capacity-max-concurrent",
        type=int,
        help=(
            "Override effective OpenClaw maxConcurrent used for Company Ops active WU cap; "
            "defaults to current OpenClaw config, then recommended fallback if unreadable"
        ),
    )
    dispatch.add_argument(
        "--capacity-reserved-slots",
        type=int,
        default=DEFAULT_CAPACITY_RESERVED_SLOTS,
        help="Slots reserved outside Company Ops active WU dispatch",
    )
    dispatch.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    dispatch.add_argument("--recorded-by", default="operations-lead", help="Recorder identity")
    dispatch.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    dispatch.add_argument("--force", action="store_true", help="Allow duplicate dispatch records when intentionally rerunning")
    dispatch.add_argument(
        "--allow-custom-session-key",
        action="store_true",
        help="Allow openclaw-agent dispatch to use a non-derived session key intentionally",
    )
    dispatch.add_argument(
        "--closeout-delegate-agent",
        default="main",
        help="Closeout delegate agent id to name in the result-ready contract",
    )
    dispatch.add_argument("--format", choices=("text", "json"), default="text")
    dispatch_mode = dispatch.add_mutually_exclusive_group(required=True)
    dispatch_mode.add_argument("--dry-run", action="store_true", help="Validate and preview without source or runtime mutation")
    dispatch_mode.add_argument("--publish", action="store_true", help="Write dispatch.json and a dispatched progress row")
    dispatch.set_defaults(func=dispatch_work_unit)

    preflight = subparsers.add_parser("preflight", help="Read-only Company Ops setup/capacity preflight")
    preflight.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing Work Unit source artifacts",
    )
    preflight.add_argument("--work-unit-id", default="", type=str, help="Optional current Work Unit id")
    preflight.add_argument("--company-ops-agent-count", type=int, default=DEFAULT_COMPANY_OPS_AGENT_COUNT)
    preflight.add_argument("--reserved-slots", type=int, default=DEFAULT_CAPACITY_RESERVED_SLOTS)
    preflight.add_argument("--config-json", type=Path, help="Optional OpenClaw config JSON for offline preflight")
    preflight.add_argument("--openclaw-max-concurrent", type=int, help="Override current agents.defaults.maxConcurrent")
    preflight.add_argument(
        "--openclaw-subagents-max-concurrent",
        type=int,
        help="Override current agents.defaults.subagents.maxConcurrent",
    )
    preflight.add_argument("--project-sync-mode", choices=PROJECT_SYNC_MODE_CHOICES, default="disabled")
    preflight.add_argument("--project-sync-field-map", default="", help="Project field-map JSON to verify when required")
    preflight.add_argument("--proof-log", default="", help="Optional proof log path whose parent must be writable")
    preflight.add_argument("--team-target", default="", help="Optional Discord team-detail target")
    preflight.add_argument("--ops-target", default="", help="Optional Discord ops-feed target")
    preflight.add_argument("--require-discord-targets", action="store_true")
    preflight.add_argument("--adapter-command", default="", help="Optional adapter command for install readiness checks")
    preflight.add_argument("--require-adapter-command", action="store_true")
    preflight.add_argument("--role-context", default="operations-lead")
    preflight.add_argument("--format", choices=("text", "json"), default="text")
    preflight.set_defaults(func=capacity_check)

    checkpoint = work_unit_subparsers.add_parser(
        "checkpoint",
        help="Publish a team CHECKPOINT and record matching source-backed progress",
    )
    checkpoint.add_argument("--work-unit-id", required=True, type=work_unit_id)
    checkpoint.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory containing <work-unit-id>/",
    )
    checkpoint.add_argument("--team", required=True, type=required)
    checkpoint.add_argument("--status", required=True, type=required)
    checkpoint.add_argument("--current-slice", required=True, type=required)
    checkpoint.add_argument("--risk-state", default="", help="Progress risk state for display, e.g. at-risk or blocked")
    checkpoint.add_argument("--retry-state", default="", help="Progress retry state for display, e.g. retry or re-run")
    checkpoint.add_argument("--next", required=True, type=required, help="Discord next action")
    checkpoint.add_argument("--elapsed", default="", help="Elapsed time or progress age")
    checkpoint.add_argument("--next-checkpoint", default="", help="Next expected checkpoint time/window")
    checkpoint.add_argument("--evidence", default="", help="Optional checkpoint evidence")
    checkpoint.add_argument("--source-ref", default="", help="Source artifact reference for this checkpoint")
    checkpoint.add_argument("--transition-kind", default="checkpoint", type=required)
    checkpoint.add_argument(
        "--mode",
        default="",
        help="Progress mode; goal and convergence automatically display round when present",
    )
    checkpoint.add_argument("--phase", default="", help="Current phase label for dashboard Progress")
    checkpoint.add_argument("--phase-index", default="", help="Current phase number or label")
    checkpoint.add_argument("--phase-total", default="", help="Known total phase count, if any")
    checkpoint.add_argument("--round", default="", help="Current convergence round, if applicable")
    checkpoint.add_argument(
        "--show-round",
        action="store_true",
        help="Show round in dashboard Progress for goal/convergence modes",
    )
    checkpoint.add_argument("--proof-ref", default="", help=argparse.SUPPRESS)
    checkpoint.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    checkpoint.add_argument("--recorded-by", default="operations-lead", help="Recorder identity")
    checkpoint.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    checkpoint.add_argument("--target", default="", help="Discord target for --publish")
    checkpoint.add_argument("--channel", default="discord", help="OpenClaw message channel")
    checkpoint.add_argument("--account", default="", help="OpenClaw channel account id")
    checkpoint.add_argument("--thread-id", default="", help="Optional Discord thread id")
    checkpoint.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    checkpoint.add_argument(
        "--project-sync-field-map",
        default="",
        help="Optional Project field-map JSON; runs mirror sync after successful publish",
    )
    checkpoint.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync; empty disables ledger",
    )
    checkpoint.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful Project mirror sync",
    )
    checkpoint.add_argument("--format", choices=("text", "json"), default="text")
    mode_group = checkpoint.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true", help="Validate and preview without writes or sends")
    mode_group.add_argument("--publish", action="store_true", help="Publish/read back Discord, append progress, then sync Project mirror")
    checkpoint.set_defaults(func=checkpoint_work_unit)

    result_ready = work_unit_subparsers.add_parser(
        "result-ready",
        help="Official foreground RESULT_READY transition with pre/post shared gate checks",
    )
    result_ready.add_argument("--work-unit-id", required=True, type=work_unit_id)
    result_ready.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id>/ source artifacts",
    )
    result_ready.add_argument("--team", default="", help="Team Lead; defaults from source artifacts")
    result_ready.add_argument("--result", required=True, type=required, help="Result summary for the RESULT_READY card")
    result_ready.add_argument("--evidence", required=True, type=required, help="Evidence reference for the RESULT_READY card")
    result_ready.add_argument("--verification", required=True, type=required, help="Verification summary for the RESULT_READY card")
    result_ready.add_argument("--risks", default="", help="Known risks or remaining caveats")
    result_ready.add_argument("--source-ref", default="", help="Optional source reference for the card")
    result_ready.add_argument("--next", default="Operations Lead review.", help="Next action after RESULT_READY")
    result_ready.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    result_ready.add_argument("--target", default="", help="Discord team-detail target for --publish")
    result_ready.add_argument("--channel", default="discord", help="OpenClaw message channel")
    result_ready.add_argument("--account", default="", help="OpenClaw channel account id")
    result_ready.add_argument("--thread-id", default="", help="Optional Discord thread id")
    result_ready.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    result_ready.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    result_ready.add_argument(
        "--project-sync-field-map",
        default="",
        help="Optional Project field-map JSON; runs mirror sync after successful publish",
    )
    result_ready.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync; empty disables ledger",
    )
    result_ready.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful Project mirror sync",
    )
    result_ready.add_argument(
        "--closeout-delegate-runtime",
        choices=CLOSEOUT_DELEGATE_RUNTIME_CHOICES,
        default="none",
        help="Optional fresh closeout delegate wake after successful RESULT_READY publish",
    )
    result_ready.add_argument("--closeout-delegate-agent", default="main")
    result_ready.add_argument("--closeout-delegate-session-key", default="")
    result_ready.add_argument("--closeout-delegate-session-ref", default="", help=argparse.SUPPRESS)
    result_ready.add_argument("--closeout-delegate-job-ref", default="", help=argparse.SUPPRESS)
    result_ready.add_argument("--closeout-delegate-message-ref", default="", help=argparse.SUPPRESS)
    result_ready.add_argument(
        "--closeout-delegate-adapter",
        choices=CLOSEOUT_DELEGATE_ADAPTER_CHOICES,
        default="auto",
        help="Delegate wake adapter. auto uses a configured command; fake is smoke-only.",
    )
    result_ready.add_argument(
        "--closeout-delegate-adapter-command",
        default="",
        help=f"Command that reads delegate wake JSON on stdin and returns accepted proof JSON. Defaults from {CLOSEOUT_DELEGATE_ADAPTER_COMMAND_ENV}.",
    )
    result_ready.add_argument("--closeout-delegate-adapter-timeout-seconds", type=int, default=30)
    result_ready.add_argument("--closeout-delegate-active-cap", type=int, default=CLOSEOUT_DELEGATE_ACTIVE_CAP_DEFAULT)
    result_ready.add_argument("--force", action="store_true", help="Allow duplicate publish proof when intentionally rerunning")
    result_ready.add_argument("--format", choices=("text", "json"), default="text")
    result_ready_mode = result_ready.add_mutually_exclusive_group(required=True)
    result_ready_mode.add_argument("--dry-run", action="store_true", help="Validate and preview without sends or proof writes")
    result_ready_mode.add_argument("--publish", action="store_true", help="Publish/read back RESULT_READY, then run post-proof gate")
    result_ready.set_defaults(func=result_ready_work_unit)

    delegate_wake = work_unit_subparsers.add_parser(
        "delegate-wake",
        help="Foreground wake of a fresh closeout delegate for a source-backed RESULT_READY Work Unit",
    )
    delegate_wake.add_argument("--work-unit-id", required=True, type=work_unit_id)
    delegate_wake.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id> source artifacts",
    )
    delegate_wake.add_argument("--team", default="", help="Team Lead; defaults from source artifacts")
    delegate_wake.add_argument("--source-ref", default="", help="Source reference for delegate payload; defaults to evidence.md")
    delegate_wake.add_argument("--closeout-delegate-runtime", choices=CLOSEOUT_DELEGATE_RUNTIME_CHOICES, default="openclaw-agent")
    delegate_wake.add_argument("--closeout-delegate-agent", default="main")
    delegate_wake.add_argument("--closeout-delegate-session-key", default="")
    delegate_wake.add_argument("--closeout-delegate-session-ref", default="", help=argparse.SUPPRESS)
    delegate_wake.add_argument("--closeout-delegate-job-ref", default="", help=argparse.SUPPRESS)
    delegate_wake.add_argument("--closeout-delegate-message-ref", default="", help=argparse.SUPPRESS)
    delegate_wake.add_argument(
        "--closeout-delegate-adapter",
        choices=CLOSEOUT_DELEGATE_ADAPTER_CHOICES,
        default="auto",
        help="Delegate wake adapter. auto uses a configured command; fake is smoke-only.",
    )
    delegate_wake.add_argument(
        "--closeout-delegate-adapter-command",
        default="",
        help=f"Command that reads delegate wake JSON on stdin and returns accepted proof JSON. Defaults from {CLOSEOUT_DELEGATE_ADAPTER_COMMAND_ENV}.",
    )
    delegate_wake.add_argument("--closeout-delegate-adapter-timeout-seconds", type=int, default=30)
    delegate_wake.add_argument("--closeout-delegate-active-cap", type=int, default=CLOSEOUT_DELEGATE_ACTIVE_CAP_DEFAULT)
    delegate_wake.add_argument(
        "--project-sync-field-map",
        default=str(DEFAULT_PROJECT_FIELD_MAP),
        help="Project field-map JSON embedded into the guarded closeout contract",
    )
    delegate_wake.add_argument(
        "--project-sync-ledger",
        default=str(DEFAULT_PROJECT_LEDGER),
        help="Ledger embedded into the guarded closeout contract; empty disables ledger",
    )
    delegate_wake.add_argument(
        "--project-sync-audit-log",
        default=str(DEFAULT_PROJECT_AUDIT_LOG),
        help="Project audit log embedded into the guarded closeout contract",
    )
    delegate_wake.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    delegate_wake.add_argument("--recorded-by", default="operations-lead")
    delegate_wake.add_argument("--force", action="store_true", help="Replace an existing closeout-delegate-wake record intentionally")
    delegate_wake.add_argument("--format", choices=("text", "json"), default="text")
    delegate_wake_mode = delegate_wake.add_mutually_exclusive_group(required=True)
    delegate_wake_mode.add_argument("--dry-run", action="store_true", help="Validate and preview without delegate wake record or runtime call")
    delegate_wake_mode.add_argument("--publish", action="store_true", help="Enqueue delegate through the configured adapter and record proof")
    delegate_wake.set_defaults(func=closeout_delegate_wake_work_unit)

    inbox = work_unit_subparsers.add_parser(
        "inbox",
        help="List source-backed Work Units ready for Operations Lead review",
    )
    inbox.add_argument(
        "--result-ready",
        action="store_true",
        help="Show Work Units whose claim or evidence state is result_ready",
    )
    inbox.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id>/ source artifacts",
    )
    inbox.add_argument("--work-unit-id", default="", type=lambda value: work_unit_id(value) if value else "")
    inbox.add_argument("--team", default="", help="Filter by Team Lead")
    inbox.add_argument("--limit", type=int, default=0, help="Maximum number of rows to return")
    inbox.add_argument(
        "--include-stale",
        action="store_true",
        help="Include already-decided or conflicted ready items in the listing",
    )
    inbox.add_argument("--format", choices=("text", "json"), default="text")
    inbox.set_defaults(func=inbox_result_ready)

    closeout = work_unit_subparsers.add_parser(
        "closeout",
        help="Prepare or publish an Operations Lead closeout from source artifacts",
    )
    closeout.add_argument("--work-unit-id", required=True, type=work_unit_id)
    closeout.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id>/ source artifacts",
    )
    closeout.add_argument(
        "--lock-path",
        type=Path,
        help="Optional WU-scoped atomic lock directory, default: <WU>/.closeout.lock",
    )
    closeout.add_argument("--decision", choices=("accept", "revise", "blocked"), default="")
    closeout.add_argument(
        "--commit-request",
        default="",
        help="Structured delegate commit-request JSON or @path; binds closeout to source hashes and RESULT_READY proof",
    )
    closeout.add_argument("--team", default="", help="Team Lead; defaults from source artifacts")
    closeout.add_argument("--reason", default="", help="Operations Lead rationale for an explicit decision")
    closeout.add_argument("--source-ref", default="", help="Decision/evidence source reference")
    closeout.add_argument("--outcome", default="", help="Owner-facing closeout outcome, default: reason")
    closeout.add_argument("--criteria-result", default="", help="Owner-facing criteria result, default: reason")
    closeout.add_argument("--verification", default="", help="Owner-facing verification summary")
    closeout.add_argument("--needed", default="", help="Required for blocked decisions")
    closeout.add_argument("--blocker-source", default="", help="Required for blocked decisions")
    closeout.add_argument("--next-owner", default="", help="Required for blocked decisions")
    closeout.add_argument("--next", default="", help="Next action for final review and owner closeout cards")
    closeout.add_argument("--recorded-by", default="operations-lead")
    closeout.add_argument("--authority-role", choices=CLOSEOUT_PUBLISH_AUTHORITY_ROLES, default="")
    closeout.add_argument("--delegate-agent", default="", help="Required for operations-lead-delegate closeout authority")
    closeout.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    closeout.add_argument("--team-target", default="", help="Discord team-detail target for --publish")
    closeout.add_argument("--ops-target", default="", help="Discord ops-feed target for --publish")
    closeout.add_argument("--channel", default="discord", help="OpenClaw message channel")
    closeout.add_argument("--account", default="", help="OpenClaw channel account id")
    closeout.add_argument("--thread-id", default="", help="Optional Discord thread id")
    closeout.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    closeout.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    closeout.add_argument(
        "--project-sync-field-map",
        default="",
        help="Project field-map JSON; required when --project-sync-mode=required",
    )
    closeout.add_argument(
        "--project-sync-mode",
        choices=PROJECT_SYNC_MODE_CHOICES,
        default="disabled",
        help="Final closeout Project mirror policy. required fails closed unless live readback matches.",
    )
    closeout.add_argument(
        "--work-card-summary-mode",
        choices=WORK_CARD_SUMMARY_MODE_CHOICES,
        default="required",
        help=(
            "Final GitHub Work Card summary comment policy. required is the live default; "
            "disabled is for local smoke, non-GitHub cards, or owner-approved no-go."
        ),
    )
    closeout.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync; empty disables ledger",
    )
    closeout.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful Project mirror sync",
    )
    closeout.add_argument("--force", action="store_true", help="Replace closeout card files or duplicate publish proof")
    closeout_mode = closeout.add_mutually_exclusive_group(required=True)
    closeout_mode.add_argument("--dry-run", action="store_true", help="Validate and preview without decision, Discord, or Project mutation")
    closeout_mode.add_argument("--publish", action="store_true", help="Write decision, publish final review/owner closeout, then sync Project mirror")
    closeout.add_argument("--format", choices=("text", "json"), default="text")
    closeout.set_defaults(func=closeout_dry_run, project_sync_no_create_missing_project_item=True)
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
