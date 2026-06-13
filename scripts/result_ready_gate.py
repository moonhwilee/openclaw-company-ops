#!/usr/bin/env python3
"""Shared repair-first Result Ready gate for Company Ops source artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROOF_LOG_NAME = "visibility-proof.jsonl"
GOAL_CONVERGENCE_RECEIPT_NAME = "goal-convergence-receipt.json"
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


def read_json_source(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.exists():
        return None, "missing"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"
    if not isinstance(value, dict):
        return None, "JSON root is not an object"
    return value, ""


def assignment_is_goal_mode(assignment: dict[str, Any]) -> bool:
    text = str(assignment.get("text") or "")
    return bool(re.search(r"(?im)^\s*mode:\s*`?goal`?\s*$", text))


def strict_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def section_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    collecting = False
    collected: list[str] = []
    heading_re = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE)
    for line in lines:
        if heading_re.match(line.strip()):
            collecting = True
            continue
        if collecting and re.match(r"^##\s+", line):
            break
        if collecting:
            collected.append(line)
    return collected


def extract_assignment_criteria(text: str) -> list[dict[str, str]]:
    criteria: list[dict[str, str]] = []
    for prefix, heading in (("done", "Done Criteria"), ("verification", "Verification Criteria")):
        index = 0
        for line in section_lines(text, heading):
            match = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
            if not match:
                continue
            value = clean_markdown_value(match.group(1)).strip()
            if not value or value in {"-", "<criteria>"}:
                continue
            index += 1
            criteria.append({"id": f"{prefix}-{index}", "text": value})
    return criteria


def path_is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def local_receipt_ref_exists(source_ref: str, artifact_dir: Path) -> bool:
    cleaned = source_ref.strip()
    if not cleaned or "://" in cleaned or cleaned.startswith("#"):
        return False
    without_fragment = cleaned.split("#", 1)[0].strip()
    if not without_fragment:
        return False
    repo_root = SCRIPT_DIR.parent
    candidates: list[Path]
    path = Path(without_fragment).expanduser()
    if path.is_absolute():
        candidates = [path]
    else:
        candidates = [repo_root / path, artifact_dir / path]
    for candidate in candidates:
        if not candidate.exists():
            continue
        if path_is_under(candidate, repo_root) or path_is_under(candidate, artifact_dir):
            return True
    return False


def validate_goal_convergence_receipt(
    receipt_path: Path,
    artifact_dir: Path,
    work_unit_id: str,
    assignment_criteria: list[dict[str, str]],
) -> list[dict[str, str]]:
    assignment_criteria_count = len(assignment_criteria)
    receipt, error = read_json_source(receipt_path)
    if error:
        return [
            structured_failure(
                "repairable",
                str(receipt_path),
                "goal_convergence_receipt",
                f"goal convergence receipt is {error}",
                "Write goal-convergence-receipt.json before declaring result-ready.",
            )
        ]

    failures: list[dict[str, str]] = []
    receipt_work_unit_id = str(receipt.get("work_unit_id") or "").strip()
    if receipt_work_unit_id != work_unit_id:
        failures.append(
            structured_failure(
                "repairable",
                str(receipt_path),
                "work_unit_id",
                f"goal convergence receipt work_unit_id is {receipt_work_unit_id or 'missing'}",
                "Write a convergence receipt for this exact Work Unit before result-ready.",
            )
        )
    status = normalized_state(str(receipt.get("status") or ""))
    if status not in {"ready_for_result_ready", "finalized"}:
        failures.append(
            structured_failure(
                "repairable",
                str(receipt_path),
                "status",
                f"goal convergence receipt status is {receipt.get('status') or 'missing'}",
                "Set status to ready_for_result_ready only after verification debt is closed.",
            )
        )
    unresolved_debt_count = strict_int(receipt.get("unresolved_debt_count"))
    if unresolved_debt_count != 0:
        failures.append(
            structured_failure(
                "repairable",
                str(receipt_path),
                "unresolved_debt_count",
                f"unresolved debt count is {receipt.get('unresolved_debt_count')!r}",
                "Repair fail/unknown criteria and rerun verification until unresolved_debt_count is 0.",
            )
        )
    receipt_assignment_criteria_count = strict_int(receipt.get("assignment_criteria_count"))
    if assignment_criteria_count <= 0:
        failures.append(
            structured_failure(
                "repairable",
                str(artifact_dir / "assignment.md"),
                "assignment.criteria",
                "goal Assignment Packet has no concrete done/verification criteria",
                "Record concrete Done Criteria and Verification Criteria before result-ready.",
            )
        )
    elif receipt_assignment_criteria_count != assignment_criteria_count:
        failures.append(
            structured_failure(
                "repairable",
                str(receipt_path),
                "assignment_criteria_count",
                (
                    "goal convergence receipt assignment_criteria_count is "
                    f"{receipt.get('assignment_criteria_count')!r}; expected {assignment_criteria_count}"
                ),
                "Map every Assignment Packet done/verification criterion into the receipt.",
            )
        )

    criteria = receipt.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        failures.append(
            structured_failure(
                "repairable",
                str(receipt_path),
                "criteria",
                "goal convergence receipt has no criteria list",
                "Record each done/verification criterion with verdict and evidence refs.",
            )
        )
        return failures
    if assignment_criteria_count > 0 and len(criteria) != assignment_criteria_count:
        failures.append(
            structured_failure(
                "repairable",
                str(receipt_path),
                "criteria",
                f"goal convergence receipt maps {len(criteria)} criteria; expected {assignment_criteria_count}",
                "Include exactly one receipt entry for every Assignment Packet done/verification criterion.",
            )
        )

    seen_criterion_ids: set[str] = set()
    for index, criterion in enumerate(criteria, start=1):
        if not isinstance(criterion, dict):
            failures.append(
                structured_failure(
                    "repairable",
                    str(receipt_path),
                    f"criteria[{index}]",
                    "criterion entry is not an object",
                    "Replace each criterion entry with an object.",
                )
            )
            continue
        criterion_id = str(criterion.get("criterion_id") or "").strip()
        if not criterion_id:
            failures.append(
                structured_failure(
                    "repairable",
                    str(receipt_path),
                    f"criteria[{index}].criterion_id",
                    "criterion is missing criterion_id",
                    "Give each mapped criterion a stable criterion_id.",
                )
            )
        elif criterion_id in seen_criterion_ids:
            failures.append(
                structured_failure(
                    "repairable",
                    str(receipt_path),
                    f"criteria[{index}].criterion_id",
                    f"duplicate criterion_id: {criterion_id}",
                    "Use each criterion_id only once in the convergence receipt.",
                )
            )
        else:
            seen_criterion_ids.add(criterion_id)
        verdict = normalized_state(str(criterion.get("final_verdict") or criterion.get("verdict") or ""))
        if verdict != "pass":
            failures.append(
                structured_failure(
                    "repairable",
                    str(receipt_path),
                    f"criteria[{index}].final_verdict",
                    f"criterion final verdict is {criterion.get('final_verdict') or criterion.get('verdict') or 'missing'}",
                    "Do not declare result-ready until every criterion final_verdict is pass.",
                )
            )
        evidence_ref = str(criterion.get("evidence_ref") or "").strip()
        if not evidence_ref:
            failures.append(
                structured_failure(
                    "repairable",
                    str(receipt_path),
                    f"criteria[{index}].evidence_ref",
                    "criterion is missing evidence_ref",
                    "Point evidence_ref at the source artifact proving this criterion.",
                )
            )
        elif not local_source_ref_exists(evidence_ref, artifact_dir):
            failures.append(
                structured_failure(
                    "repairable",
                    str(receipt_path),
                    f"criteria[{index}].evidence_ref",
                    f"missing evidence_ref: {evidence_ref}",
                    "Point evidence_ref at an existing local source artifact.",
                )
            )
        elif not local_receipt_ref_exists(evidence_ref, artifact_dir):
            failures.append(
                structured_failure(
                    "repairable",
                    str(receipt_path),
                    f"criteria[{index}].evidence_ref",
                    f"evidence_ref is outside allowed receipt sources: {evidence_ref}",
                    "Point evidence_ref inside the repository or this Work Unit artifact directory.",
                )
            )
        initial_verdict = normalized_state(str(criterion.get("verdict") or ""))
        if initial_verdict in {"fail", "unknown"}:
            for field in ("repair_action_ref", "reverify_ref"):
                value = str(criterion.get(field) or "").strip()
                if not value:
                    failures.append(
                        structured_failure(
                            "repairable",
                            str(receipt_path),
                            f"criteria[{index}].{field}",
                            f"criterion started as {initial_verdict} but is missing {field}",
                            "Record the repair and later reverify source refs before result-ready.",
                        )
                    )
                elif not local_source_ref_exists(value, artifact_dir):
                    failures.append(
                        structured_failure(
                            "repairable",
                            str(receipt_path),
                            f"criteria[{index}].{field}",
                            f"missing {field}: {value}",
                            "Point repair/reverify refs at existing local source artifacts.",
                        )
                    )
                elif not local_receipt_ref_exists(value, artifact_dir):
                    failures.append(
                        structured_failure(
                            "repairable",
                            str(receipt_path),
                            f"criteria[{index}].{field}",
                            f"{field} is outside allowed receipt sources: {value}",
                            "Point repair/reverify refs inside the repository or this Work Unit artifact directory.",
                        )
                    )
    expected_criterion_ids = {str(item.get("id") or "").strip() for item in assignment_criteria}
    expected_criterion_ids.discard("")
    if expected_criterion_ids and seen_criterion_ids != expected_criterion_ids:
        missing_ids = sorted(expected_criterion_ids - seen_criterion_ids)
        extra_ids = sorted(seen_criterion_ids - expected_criterion_ids)
        details: list[str] = []
        if missing_ids:
            details.append(f"missing {', '.join(missing_ids)}")
        if extra_ids:
            details.append(f"unexpected {', '.join(extra_ids)}")
        failures.append(
            structured_failure(
                "repairable",
                str(receipt_path),
                "criteria.criterion_id",
                "goal convergence receipt criterion_id set does not match Assignment Packet criteria"
                + (f": {'; '.join(details)}" if details else ""),
                "Use exactly the Assignment Packet criterion ids generated from Done Criteria and Verification Criteria.",
            )
        )
    return failures


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
    allow_draft_evidence_with_convergence_receipt: bool = False,
    allow_draft_evidence_with_existing_result_ready: bool = False,
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
    raw_evidence_status = str(evidence.get("status") or "")
    evidence_status = evidence_status_override or raw_evidence_status
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

    goal_mode = False
    receipt_failures: list[dict[str, str]] = []
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
    else:
        goal_mode = assignment_is_goal_mode(assignment)
        if goal_mode:
            assignment_criteria = extract_assignment_criteria(str(assignment.get("text") or ""))
            receipt_failures = validate_goal_convergence_receipt(
                artifact_dir / GOAL_CONVERGENCE_RECEIPT_NAME,
                artifact_dir,
                work_unit_id,
                assignment_criteria,
            )
            failures.extend(receipt_failures)
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
    draft_allowed = bool(
        allow_draft_evidence_with_convergence_receipt
        and goal_mode
        and not receipt_failures
    ) or allow_draft_evidence_with_existing_result_ready
    if not evidence.get("exists"):
        failures.append(
            structured_failure(
                "repairable",
                str(artifact_dir / "evidence.md"),
                "evidence.status",
                "result_ready requested but evidence.md is missing",
                "Create an Evidence & Result Record with source-backed proof, then rerun the gate.",
            )
        )
    else:
        raw_status = normalized_state(raw_evidence_status)
        raw_status_can_be_projected = raw_status == "result_ready" or (draft_allowed and raw_status == "draft")
        effective_evidence_status = evidence_status_override or raw_evidence_status
        evidence_status = normalized_state(effective_evidence_status)
        evidence_status_ok = (
            raw_status_can_be_projected
            and (evidence_status == "result_ready" or (draft_allowed and evidence_status == "draft"))
        )
        if not evidence_status_ok:
            expected_status = (
                "Status: Draft before official publish, then Status: Result Ready after publish"
                if draft_allowed
                else "Status: Result Ready from the official result-ready publish path"
            )
            failures.append(
                structured_failure(
                    "repairable",
                    str(evidence["path"]),
                    "evidence.status",
                    f"result_ready requested but evidence status is {effective_evidence_status or 'missing'}",
                    expected_status,
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
