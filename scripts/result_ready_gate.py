#!/usr/bin/env python3
"""Shared repair-first Result Ready gate for Company Ops source artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROOF_LOG_NAME = "visibility-proof.jsonl"
FIELD_RE = re.compile(r"^- ([^:]+):\s*(.*)$")
STATUS_RE = re.compile(r"^Status:\s*(.+)$", re.MULTILINE)
RESULT_READY_PROOF_REQUIRED_ROUTES = {"discord-bound"}
STARTED_PROGRESS_KINDS = {"start", "started"}


def clean_markdown_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == "`":
        return cleaned[1:-1].strip()
    return cleaned


def normalized_state(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def normalize_route(value: str) -> str:
    return clean_markdown_value(value).strip().lower().rstrip(".")


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


def local_source_ref_exists(source_ref: str, artifact_dir: Path) -> bool:
    cleaned = source_ref.strip()
    if not cleaned or "://" in cleaned or cleaned.startswith("#"):
        return True
    path = Path(cleaned).expanduser()
    if path.is_absolute():
        return path.exists()
    repo_root = SCRIPT_DIR.parent
    return (repo_root / path).exists() or (artifact_dir / path).exists()


def result_ready_requested(claim_state: str, evidence_status: str, progress_rows: list[dict[str, Any]]) -> bool:
    if normalized_state(claim_state) == "result_ready":
        return True
    if normalized_state(evidence_status) == "result_ready":
        return True
    return any(normalized_state(str(row.get("transition_kind") or "")) == "result_ready" for row in progress_rows)


def has_started_source(progress_rows: list[dict[str, Any]], proof_path: Path, work_unit_id: str) -> bool:
    return any(
        normalized_state(str(row.get("transition_kind") or "")) in STARTED_PROGRESS_KINDS
        for row in progress_rows
    ) or has_started_proof(proof_path, work_unit_id)


def read_progress_rows(path: Path, work_unit_id: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(
                structured_failure(
                    "repairable",
                    str(path),
                    f"progress.jsonl:{index}",
                    f"invalid progress JSON: {exc}",
                    "Fix or remove the malformed progress row, then rerun the gate.",
                )
            )
            continue
        if not isinstance(row, dict):
            failures.append(
                structured_failure(
                    "repairable",
                    str(path),
                    f"progress.jsonl:{index}",
                    "progress row is not an object",
                    "Replace the row with a JSON object.",
                )
            )
            continue
        row_work_unit = str(row.get("work_unit_id") or "")
        if row_work_unit and row_work_unit != work_unit_id:
            continue
        rows.append(row)
    return rows, failures


def has_result_ready_proof(proof_path: Path, work_unit_id: str) -> bool:
    return has_visibility_proof(proof_path, work_unit_id, "RESULT_READY")


def has_started_proof(proof_path: Path, work_unit_id: str) -> bool:
    return has_visibility_proof(proof_path, work_unit_id, "STARTED")


def has_visibility_proof(proof_path: Path, work_unit_id: str, kind: str) -> bool:
    if not proof_path.exists():
        return False
    for line in proof_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        if str(row.get("work_unit_id") or "") != work_unit_id:
            continue
        if row.get("dry_run") is True:
            continue
        if row.get("surface") != "team-detail" or row.get("kind") != kind:
            continue
        if row.get("readback_ok") is False:
            continue
        return True
    return False


def structured_failure(
    failure_class: str,
    path: str,
    field: str,
    message: str,
    repair_hint: str,
) -> dict[str, str]:
    return {
        "class": failure_class,
        "path": path,
        "field": field,
        "message": message,
        "repair_hint": repair_hint,
    }


def result_ready_gate(
    artifact_root: Path,
    work_unit_id: str,
    *,
    claim_state_override: str = "",
    evidence_status_override: str = "",
    projected_progress_rows: list[dict[str, Any]] | None = None,
    require_live_visibility: bool | None = None,
    require_started_visibility: bool | None = None,
) -> dict[str, Any]:
    artifact_root = artifact_root.expanduser()
    artifact_dir = artifact_root / work_unit_id
    assignment = parse_markdown_source(artifact_dir / "assignment.md")
    claim = parse_markdown_source(artifact_dir / "claim.md")
    evidence = parse_markdown_source(artifact_dir / "evidence.md")
    progress_path = artifact_dir / "progress.jsonl"
    proof_path = artifact_dir / DEFAULT_PROOF_LOG_NAME
    progress_rows, failures = read_progress_rows(progress_path, work_unit_id)
    if projected_progress_rows:
        progress_rows.extend(projected_progress_rows)

    claim_state = claim_state_override or claim["fields"].get("expected state", "")
    evidence_status = evidence_status_override or str(evidence.get("status") or "")
    requested = result_ready_requested(claim_state, evidence_status, progress_rows)

    if not requested:
        return {
            "status": "not-requested",
            "requested": False,
            "ready": False,
            "failures": failures,
            "blockers": [failure["message"] for failure in failures],
            "artifact_dir": str(artifact_dir),
            "source": "local-source-artifacts",
        }

    if not assignment.get("exists"):
        failures.append(
            structured_failure(
                "blocked",
                str(artifact_dir / "assignment.md"),
                "assignment.md",
                "Assignment Packet is missing",
                "Restore or create the Assignment Packet before declaring result_ready.",
            )
        )
    if not has_started_source(progress_rows, proof_path, work_unit_id):
        failures.append(
            structured_failure(
                "blocked",
                str(progress_path),
                "progress.STARTED",
                "result_ready requires prior STARTED source event",
                "Run the canonical start transition before declaring result_ready.",
            )
        )
    if normalized_state(claim_state) == "result_ready":
        if not evidence.get("exists"):
            failures.append(
                structured_failure(
                    "repairable",
                    str(artifact_dir / "evidence.md"),
                    "evidence.status",
                    "claim result_ready but evidence.md is missing",
                    "Create an Evidence & Result Record with source-backed proof, then rerun the gate.",
                )
            )
        elif normalized_state(evidence_status) in {"", "draft", "pending"}:
            failures.append(
                structured_failure(
                    "repairable",
                    str(evidence["path"]),
                    "evidence.status",
                    f"claim result_ready but evidence status is {evidence_status or 'missing'}",
                    "Update evidence only after real verification/source proof exists.",
                )
            )

    for index, row in enumerate(progress_rows, start=1):
        source_ref = str(row.get("source_ref") or "")
        if source_ref and not local_source_ref_exists(source_ref, artifact_dir):
            failures.append(
                structured_failure(
                    "repairable",
                    str(progress_path),
                    f"progress.source_ref:{index}",
                    f"missing source_ref: {source_ref}",
                    "Point source_ref at an existing local source artifact or remove the invalid row.",
                )
            )

    route = ""
    for field in ("execution route", "execution route for this work unit"):
        route = normalize_route(str(assignment["fields"].get(field) or ""))
        if route:
            break
    route_requires_live_visibility = route in RESULT_READY_PROOF_REQUIRED_ROUTES
    if require_live_visibility is None:
        require_live_visibility = route_requires_live_visibility
    if require_started_visibility is None:
        require_started_visibility = route_requires_live_visibility or bool(require_live_visibility)
    if require_live_visibility and not has_result_ready_proof(proof_path, work_unit_id):
        failures.append(
            structured_failure(
                "rerun-required",
                str(proof_path),
                "visibility-proof.RESULT_READY",
                "live visibility requires RESULT_READY proof but no valid proof row exists",
                "Publish/read back RESULT_READY or rerun the visible result-ready transition.",
            )
        )
    if require_started_visibility and not has_started_proof(proof_path, work_unit_id):
        failures.append(
            structured_failure(
                "rerun-required",
                str(proof_path),
                "visibility-proof.STARTED",
                "live visibility requires STARTED proof but no valid proof row exists",
                "Publish/read back STARTED or rerun the visible start transition.",
            )
        )

    ready = requested and not failures
    return {
        "status": "ready" if ready else "repair-needed",
        "requested": requested,
        "ready": ready,
        "failures": failures,
        "blockers": [failure["message"] for failure in failures],
        "artifact_dir": str(artifact_dir),
        "source": "local-source-artifacts",
    }
