#!/usr/bin/env python3
"""Compose, publish, and validate OpenClaw Company Ops Discord visibility."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ALERT_EVENTS = {
    "CLAIM_STALE",
    "SESSION_MISMATCH",
    "COMPACTION_RECOVERY_SUSPECTED",
}

VISIBILITY_SURFACES = {
    "ops-feed",
    "team-detail",
}

OPS_FEED_EVENTS = {
    "ASSIGNED",
    "COMPLETED",
    "BLOCKED",
}

TEAM_DETAIL_EVENTS = {
    "ASSIGNED_DETAIL",
    "STARTED",
    "CHECKPOINT",
    "RESULT_READY",
    "ACCEPTED",
    "REVISE",
    "BLOCKED_DETAIL",
}

OPS_FEED_CARD_LABELS = {
    "ASSIGNED": "요청",
    "COMPLETED": "완료",
    "BLOCKED": "막힘",
}

OPS_FEED_CARD_STATUS_ICONS = {
    "ASSIGNED": "📌",
    "COMPLETED": "✅",
    "BLOCKED": "⛔",
}

TEAM_DETAIL_STATUS_ICONS = {
    "ASSIGNED_DETAIL": "📋",
    "STARTED": "▶️",
    "CHECKPOINT": "⏱️",
    "RESULT_READY": "📦",
    "ACCEPTED": "✅",
    "REVISE": "🔁",
    "BLOCKED_DETAIL": "⛔",
}

TEAM_ICONS = {
    "build-pq": "🧱",
    "build-lab": "🧪",
    "market": "📣",
    "revenue": "💼",
}

DEFAULT_TEAM_ICON = "👥"

OPS_FEED_FORBIDDEN_LABELS = (
    "Surface:",
    "Owner:",
    "Source:",
    "Public summary:",
)

TEAM_FINAL_REVIEW_EVENTS = {
    "ACCEPTED",
    "REVISE",
    "BLOCKED_DETAIL",
}

DISCORD_MESSAGE_LIMIT = 2000
DISCORD_GENERATION_TARGET_CHARS = 1600
DISCORD_MESSAGE_TARGET_CHARS = 1800
DISCORD_COMPACTION_SUFFIX = "… (일부 생략됨; 상세 내용은 source artifact 또는 team result 원문을 확인하세요.)"
PROOF_TIMESTAMP_FIELDS = ("transition_at", "sent_at", "readback_at", "discord_timestamp")


def read_json(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
        source = "stdin"
    else:
        source_path = Path(path).expanduser()
        raw = source_path.read_text(encoding="utf-8")
        source = str(source_path)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"input is not valid JSON: {source}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"input root must be a JSON object: {source}")
    return data


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).expanduser().read_text(encoding="utf-8")


def read_card_json(path: str) -> dict[str, str]:
    data = read_json(path)
    card = data.get("card", data)
    if not isinstance(card, dict):
        raise ValueError(f"card JSON must contain an object: {path}")
    normalized = {str(key): "" if value is None else str(value) for key, value in card.items()}
    validate_card(normalized)
    return normalized


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str, field: str) -> datetime:
    if not value:
        raise ValueError(f"proof row missing timestamp: {field}")
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid {field} timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} timestamp must include timezone: {value}")
    return parsed.astimezone(UTC)


def read_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_path = Path(path).expanduser()
    for line_number, raw in enumerate(source_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source_path}:{line_number}: invalid JSONL row: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{source_path}:{line_number}: proof row must be a JSON object")
        rows.append(row)
    return rows


def append_jsonl(path: str, row: dict[str, Any]) -> None:
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def run_project_one_shot_sync(card: dict[str, str], args: argparse.Namespace) -> dict[str, Any]:
    if not args.project_sync_field_map:
        return {"enabled": False}
    command = [
        sys.executable,
        str(SCRIPT_DIR / "project_sync.py"),
        "project-sync",
        "dry-run" if args.dry_run else "apply",
        "--work-unit-id",
        card["work_unit_id"],
        "--artifact-root",
        args.project_sync_artifact_root,
        "--field-map",
        args.project_sync_field_map,
        "--format",
        "json",
    ]
    if not args.dry_run:
        command.extend(["--audit-log", args.project_sync_audit_log])
    if args.project_sync_ledger:
        command.extend(["--ledger", args.project_sync_ledger])
    else:
        command.append("--no-ledger")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    parsed: dict[str, Any] = {}
    if result.stdout:
        try:
            loaded = json.loads(result.stdout)
            if isinstance(loaded, dict):
                parsed = loaded
        except json.JSONDecodeError:
            parsed = {}
    return {
        "enabled": True,
        "ok": result.returncode == 0,
        "mode": "dry-run" if args.dry_run else "apply",
        "returncode": result.returncode,
        "summary": parsed.get("summary", {}),
        "error": result.stderr.strip(),
    }


def stable_card_id(card: dict[str, str], text: str) -> str:
    payload = json.dumps(card, sort_keys=True, ensure_ascii=False) + "\n" + text
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def find_values(data: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, (str, int)):
                found.append(str(value))
            found.extend(find_values(value, keys))
    elif isinstance(data, list):
        for item in data:
            found.extend(find_values(item, keys))
    return found


def find_message_objects(data: Any) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if isinstance(data, dict):
        text = data.get("message") or data.get("content") or data.get("text") or data.get("body")
        message_id = data.get("messageId") or data.get("message_id") or data.get("id")
        if isinstance(text, str) and message_id is not None:
            messages.append(data)
        for value in data.values():
            messages.extend(find_message_objects(value))
    elif isinstance(data, list):
        for item in data:
            messages.extend(find_message_objects(item))
    return messages


def message_text(message: dict[str, Any]) -> str:
    for key in ("message", "content", "text", "body"):
        value = message.get(key)
        if isinstance(value, str):
            return value
    return ""


def message_id(message: dict[str, Any]) -> str:
    for key in ("messageId", "message_id", "id"):
        value = message.get(key)
        if value is not None:
            return str(value)
    return ""


def message_timestamp(message: dict[str, Any]) -> str:
    for key in ("createdAt", "created_at", "timestamp", "date", "sentAt", "sent_at"):
        value = message.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def first_sent_message_id(data: dict[str, Any]) -> str:
    values = find_values(data, {"messageId", "message_id", "id"})
    return values[0] if values else ""


def result_summary(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "message_id_candidates": find_values(data, {"messageId", "message_id", "id"})[:5],
        "handled_by": data.get("handledBy", ""),
        "action": data.get("action", ""),
        "dry_run": data.get("dryRun", False),
    }


def run_openclaw_message(command: list[str]) -> tuple[int, dict[str, Any], str, str]:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    data: dict[str, Any] = {}
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            data = parsed
    return result.returncode, data, result.stdout, result.stderr


def readback_match(
    args: argparse.Namespace,
    text: str,
    sent_message_id: str,
) -> tuple[bool, str, str, dict[str, Any], str]:
    command = [
        "openclaw",
        "message",
        "read",
        "--channel",
        args.channel,
        "--target",
        args.target,
        "--limit",
        str(args.readback_limit),
        "--json",
    ]
    if args.account:
        command.extend(["--account", args.account])
    if args.thread_id:
        command.extend(["--thread-id", args.thread_id])
    if sent_message_id:
        command.extend(["--message-id", sent_message_id])

    code, data, stdout, stderr = run_openclaw_message(command)
    if code != 0:
        return False, "", "", data, stderr.strip() or stdout.strip()

    expected_header = text.splitlines()[0] if text else ""
    for candidate in find_message_objects(data):
        candidate_id = message_id(candidate)
        candidate_text = message_text(candidate)
        if sent_message_id and candidate_id == sent_message_id:
            return True, candidate_id, message_timestamp(candidate), data, ""
        if candidate_text == text or (expected_header and expected_header in candidate_text):
            return True, candidate_id, message_timestamp(candidate), data, ""
    return False, "", "", data, "sent message was not found in readback"


def normalize_alerts(data: dict[str, Any]) -> list[dict[str, Any]]:
    alerts = data.get("alerts", [])
    if not isinstance(alerts, list):
        raise ValueError("alerts must be a list")
    normalized: list[dict[str, Any]] = []
    for alert in alerts:
        if not isinstance(alert, dict):
            raise ValueError("each alert must be a JSON object")
        event = alert.get("alert")
        if event not in ALERT_EVENTS:
            raise ValueError(f"unsupported alert event: {event}")
        normalized.append(alert)
    return normalized


def source_for(alert: dict[str, Any], source_ref: str) -> str:
    claim_ref = alert.get("claim_ref")
    if not claim_ref:
        return source_ref
    return f"{source_ref}#{claim_ref}"


def event_from_alert(alert: dict[str, Any], source_ref: str) -> dict[str, str]:
    event = str(alert["alert"])
    work_unit_id = str(alert.get("work_unit_id") or "UNKNOWN_WORK_UNIT")
    owner = str(alert.get("owner_session_ref") or "unknown")
    reason = str(alert.get("reason") or "Pulse Monitor alert requires review.")
    next_action = "Operations Lead review."
    return {
        "event": event,
        "work_unit_id": work_unit_id,
        "summary": reason,
        "owner": owner,
        "source": source_for(alert, source_ref),
        "next": next_action,
    }


def format_text_event(event: dict[str, str]) -> str:
    lines = [
        f"[{event['event']}] {event['work_unit_id']}",
        f"Summary: {event['summary']}",
    ]
    work_card = event.get("work_card")
    if work_card:
        lines.append(f"Work Card: {work_card}")
    lines.extend(
        [
            f"Owner: {event['owner']}",
            f"Source: {event['source']}",
            f"Next: {event['next']}",
        ]
    )
    return compact_discord_text("\n".join(lines))


def require_fields(card: dict[str, str], fields: tuple[str, ...], context: str) -> None:
    missing = [field for field in fields if not card.get(field)]
    if missing:
        raise ValueError(f"{context} requires: {', '.join(missing)}")


def append_line(lines: list[str], label: str, value: str | None) -> None:
    if value:
        lines.append(f"{label}: {value}")


def team_display(team: str) -> str:
    return f"{TEAM_ICONS.get(team, DEFAULT_TEAM_ICON)} {team}"


def discord_content_units(text: str) -> int:
    """Return a conservative Discord content length using UTF-16 code units."""
    return len(text.encode("utf-16-le")) // 2


def truncate_to_discord_units(text: str, limit: int) -> str:
    if discord_content_units(text) <= limit:
        return text
    units = 0
    result: list[str] = []
    for char in text:
        char_units = discord_content_units(char)
        if units + char_units > limit:
            break
        result.append(char)
        units += char_units
    return "".join(result)


def compact_discord_text(text: str, limit: int = DISCORD_MESSAGE_TARGET_CHARS) -> str:
    """Keep Discord visibility text inside one message while preserving the header."""
    if limit > DISCORD_MESSAGE_LIMIT:
        raise ValueError(f"Discord guard limit must be <= {DISCORD_MESSAGE_LIMIT}")
    if discord_content_units(text) <= limit:
        return text

    lines = text.splitlines()
    if not lines:
        return text

    header = lines[0]
    tail = ""
    body_lines = lines[1:]
    if body_lines and (
        body_lines[-1].startswith("Next:")
        or body_lines[-1].startswith("다음:")
    ):
        tail = body_lines[-1]
        body_lines = body_lines[:-1]

    fixed_parts = [header, DISCORD_COMPACTION_SUFFIX]
    if tail:
        fixed_parts.append(tail)
    fixed_len = sum(discord_content_units(part) for part in fixed_parts) + max(
        0,
        len(fixed_parts) - 1,
    )
    body_budget = limit - fixed_len
    if body_budget < 80:
        raise ValueError("Discord guard limit leaves no room for message body")

    body = "\n".join(body_lines)
    compacted_body = truncate_to_discord_units(body, body_budget).rstrip()
    compacted_lines = [header]
    if compacted_body:
        compacted_lines.append(compacted_body)
    compacted_lines.append(DISCORD_COMPACTION_SUFFIX)
    if tail:
        compacted_lines.append(tail)
    compacted = "\n".join(compacted_lines)
    overflow = discord_content_units(compacted) - limit
    if overflow > 0 and compacted_body:
        compacted_body = truncate_to_discord_units(
            compacted_body,
            max(0, discord_content_units(compacted_body) - overflow),
        ).rstrip()
        compacted_lines = [header]
        if compacted_body:
            compacted_lines.append(compacted_body)
        compacted_lines.append(DISCORD_COMPACTION_SUFFIX)
        if tail:
            compacted_lines.append(tail)
        compacted = "\n".join(compacted_lines)
    if discord_content_units(compacted) > limit:
        raise ValueError("Discord message guard failed to compact text under limit")
    return compacted


def validate_ops_feed_text(text: str) -> None:
    for label in OPS_FEED_FORBIDDEN_LABELS:
        if label in text:
            raise ValueError(f"ops-feed card must not expose internal label: {label}")


def validate_final_review_gate(card: dict[str, str]) -> None:
    if card["surface"] != "ops-feed" or card["kind"] not in {"COMPLETED", "BLOCKED"}:
        return
    final_review = card.get("team_final_review_kind", "")
    if final_review not in TEAM_FINAL_REVIEW_EVENTS:
        raise ValueError(
            "ops-feed completion/blocker cards require --team-final-review-kind "
            "ACCEPTED, REVISE, or BLOCKED_DETAIL"
        )
    if card["kind"] == "COMPLETED" and final_review != "ACCEPTED":
        raise ValueError("ops-feed COMPLETED cards require team final review ACCEPTED")
    if card["kind"] == "BLOCKED" and final_review != "BLOCKED_DETAIL":
        raise ValueError("ops-feed BLOCKED cards require team final review BLOCKED_DETAIL")


def card_from_args(args: argparse.Namespace) -> dict[str, str]:
    if args.surface not in VISIBILITY_SURFACES:
        raise ValueError(f"unsupported card surface: {args.surface}")
    allowed = OPS_FEED_EVENTS if args.surface == "ops-feed" else TEAM_DETAIL_EVENTS
    if args.kind not in allowed:
        raise ValueError(f"unsupported {args.surface} card kind: {args.kind}")

    card = {
        "surface": args.surface,
        "kind": args.kind,
        "work_unit_id": args.work_unit_id,
        "team": args.team,
        "problem": args.problem,
        "request": args.request,
        "criteria": args.criteria,
        "caution": args.caution,
        "evidence": args.evidence,
        "next": args.next,
        "outcome": args.outcome,
        "criteria_result": args.criteria_result,
        "decision": args.decision,
        "verification": args.verification,
        "cause": args.cause,
        "needed": args.needed,
        "goal": args.goal,
        "scope": args.scope,
        "report": args.report,
        "result": args.result,
        "risks": args.risks,
        "reason": args.reason,
        "status": args.status,
        "current_slice": args.current_slice,
        "elapsed": args.elapsed,
        "next_checkpoint": args.next_checkpoint,
        "source": args.source,
        "team_final_review_kind": args.team_final_review_kind,
    }
    validate_card(card)
    return card


def validate_card(card: dict[str, str]) -> None:
    require_fields(card, ("surface", "kind", "work_unit_id", "team", "next"), "visibility card")
    if card["surface"] not in VISIBILITY_SURFACES:
        raise ValueError(f"unsupported card surface: {card['surface']}")
    allowed = OPS_FEED_EVENTS if card["surface"] == "ops-feed" else TEAM_DETAIL_EVENTS
    if card["kind"] not in allowed:
        raise ValueError(f"unsupported {card['surface']} card kind: {card['kind']}")

    if card["surface"] == "ops-feed":
        if card["kind"] == "ASSIGNED":
            require_fields(card, ("problem", "request", "criteria"), "ops-feed request card")
        elif card["kind"] == "COMPLETED":
            require_fields(
                card,
                ("outcome", "criteria_result", "decision", "verification"),
                "ops-feed completion card",
            )
        elif card["kind"] == "BLOCKED":
            require_fields(card, ("problem", "cause", "needed"), "ops-feed blocker card")
        validate_final_review_gate(card)
        return

    if card["kind"] == "ASSIGNED_DETAIL":
        require_fields(card, ("goal", "scope", "criteria", "report"), "team assignment detail")
    elif card["kind"] == "STARTED":
        require_fields(card, ("status",), "team started card")
    elif card["kind"] == "CHECKPOINT":
        require_fields(card, ("status", "current_slice"), "team checkpoint card")
    elif card["kind"] == "RESULT_READY":
        require_fields(card, ("result", "evidence", "verification"), "team result ready card")
    elif card["kind"] in {"ACCEPTED", "REVISE"}:
        require_fields(card, ("decision", "reason"), f"team {card['kind']} review card")
    elif card["kind"] == "BLOCKED_DETAIL":
        require_fields(card, ("problem", "cause", "needed"), "team blocked detail card")


def format_ops_feed_card(card: dict[str, str]) -> str:
    label = OPS_FEED_CARD_LABELS[card["kind"]]
    status_icon = OPS_FEED_CARD_STATUS_ICONS[card["kind"]]
    lines = [f"{status_icon} [{label}] {card['work_unit_id']} · {team_display(card['team'])}"]

    if card["kind"] == "ASSIGNED":
        lines.extend(
            [
                f"문제: {card['problem']}",
                f"요청: {card['request']}",
                f"기준: {card['criteria']}",
            ]
        )
        append_line(lines, "주의", card.get("caution"))
        append_line(lines, "근거", card.get("evidence"))
    elif card["kind"] == "COMPLETED":
        lines.extend(
            [
                f"결과: {card['outcome']}",
                f"기준 대비: {card['criteria_result']}",
                f"금비 판정: {card['decision']}",
                f"확인: {card['verification']}",
            ]
        )
        append_line(lines, "근거", card.get("evidence"))
    elif card["kind"] == "BLOCKED":
        lines.extend(
            [
                f"문제: {card['problem']}",
                f"원인: {card['cause']}",
                f"필요: {card['needed']}",
            ]
        )
        append_line(lines, "근거", card.get("evidence"))

    lines.append(f"다음: {card['next']}")
    text = "\n".join(lines)
    validate_ops_feed_text(text)
    return compact_discord_text(text)


def format_team_detail_card(card: dict[str, str]) -> str:
    status_icon = TEAM_DETAIL_STATUS_ICONS[card["kind"]]
    lines = [f"{status_icon} [{card['kind']}] {card['work_unit_id']} · {team_display(card['team'])}"]

    if card["kind"] == "ASSIGNED_DETAIL":
        lines.extend(
            [
                f"Goal: {card['goal']}",
                f"Scope: {card['scope']}",
                f"Criteria: {card['criteria']}",
            ]
        )
        append_line(lines, "Cautions", card.get("caution"))
        lines.append(f"Report: {card['report']}")
    elif card["kind"] == "STARTED":
        lines.append(f"Status: {card['status']}")
    elif card["kind"] == "CHECKPOINT":
        lines.extend(
            [
                f"Slice: {card['current_slice']}",
                f"Status: {card['status']}",
            ]
        )
        append_line(lines, "Elapsed", card.get("elapsed"))
        append_line(lines, "Next checkpoint", card.get("next_checkpoint"))
        append_line(lines, "Evidence", card.get("evidence"))
        append_line(lines, "Source", card.get("source"))
    elif card["kind"] == "RESULT_READY":
        lines.extend(
            [
                f"Result: {card['result']}",
                f"Evidence: {card['evidence']}",
                f"Verification: {card['verification']}",
            ]
        )
        append_line(lines, "Risks", card.get("risks"))
    elif card["kind"] in {"ACCEPTED", "REVISE"}:
        lines.extend(
            [
                f"Decision: {card['decision']}",
                f"Reason: {card['reason']}",
            ]
        )
        append_line(lines, "Evidence", card.get("evidence"))
    elif card["kind"] == "BLOCKED_DETAIL":
        lines.extend(
            [
                f"Problem: {card['problem']}",
                f"Cause: {card['cause']}",
                f"Needed: {card['needed']}",
            ]
        )
        append_line(lines, "Evidence", card.get("evidence"))

    lines.append(f"Next: {card['next']}")
    return compact_discord_text("\n".join(lines))


def format_text_card(card: dict[str, str]) -> str:
    if card["surface"] == "ops-feed":
        return format_ops_feed_card(card)
    return format_team_detail_card(card)


def validate_card_sequence(cards: list[dict[str, str]]) -> dict[str, str]:
    if not cards:
        raise ValueError("card sequence requires at least one card")

    work_unit_ids = {card.get("work_unit_id") for card in cards}
    teams = {card.get("team") for card in cards}
    if len(work_unit_ids) != 1:
        raise ValueError("card sequence must use one Work Unit id")
    if len(teams) != 1:
        raise ValueError("card sequence must use one team")

    events = [(card["surface"], card["kind"]) for card in cards]
    try:
        ops_assigned_index = events.index(("ops-feed", "ASSIGNED"))
    except ValueError as exc:
        raise ValueError("card sequence must start with ops-feed ASSIGNED before team handoff") from exc

    if ops_assigned_index != 0:
        raise ValueError("ops-feed ASSIGNED must be the first visibility card in the sequence")

    if ("team-detail", "ASSIGNED_DETAIL") not in events:
        raise ValueError("card sequence requires team-detail ASSIGNED_DETAIL")
    if events.index(("team-detail", "ASSIGNED_DETAIL")) < ops_assigned_index:
        raise ValueError("team-detail ASSIGNED_DETAIL must not precede ops-feed ASSIGNED")

    if ("team-detail", "RESULT_READY") in events:
        result_ready_index = events.index(("team-detail", "RESULT_READY"))
        if ("team-detail", "STARTED") not in events:
            raise ValueError("team-detail RESULT_READY requires prior team-detail STARTED")
        if events.index(("team-detail", "STARTED")) > result_ready_index:
            raise ValueError("team-detail STARTED must precede team-detail RESULT_READY")

    checkpoint_indexes = [
        index for index, event in enumerate(events) if event == ("team-detail", "CHECKPOINT")
    ]
    for checkpoint_index in checkpoint_indexes:
        if ("team-detail", "STARTED") not in events:
            raise ValueError("team-detail CHECKPOINT requires prior team-detail STARTED")
        if events.index(("team-detail", "STARTED")) > checkpoint_index:
            raise ValueError("team-detail STARTED must precede team-detail CHECKPOINT")
        if ("team-detail", "RESULT_READY") in events and events.index(("team-detail", "RESULT_READY")) < checkpoint_index:
            raise ValueError("team-detail CHECKPOINT must not follow team-detail RESULT_READY")

    if ("ops-feed", "COMPLETED") in events:
        completed_index = events.index(("ops-feed", "COMPLETED"))
        if ("team-detail", "RESULT_READY") not in events:
            raise ValueError("ops-feed COMPLETED requires prior team-detail RESULT_READY")
        if events.index(("team-detail", "RESULT_READY")) > completed_index:
            raise ValueError("team-detail RESULT_READY must precede ops-feed COMPLETED")
        if ("team-detail", "ACCEPTED") not in events:
            raise ValueError("ops-feed COMPLETED requires prior team-detail ACCEPTED")
        if events.index(("team-detail", "ACCEPTED")) > completed_index:
            raise ValueError("team-detail ACCEPTED must precede ops-feed COMPLETED")

    if ("ops-feed", "BLOCKED") in events:
        blocked_index = events.index(("ops-feed", "BLOCKED"))
        if ("team-detail", "RESULT_READY") not in events:
            raise ValueError("ops-feed BLOCKED requires prior team-detail RESULT_READY")
        if events.index(("team-detail", "RESULT_READY")) > blocked_index:
            raise ValueError("team-detail RESULT_READY must precede ops-feed BLOCKED")
        if ("team-detail", "BLOCKED_DETAIL") not in events:
            raise ValueError("ops-feed BLOCKED requires prior team-detail BLOCKED_DETAIL")
        if events.index(("team-detail", "BLOCKED_DETAIL")) > blocked_index:
            raise ValueError("team-detail BLOCKED_DETAIL must precede ops-feed BLOCKED")

    return {
        "work_unit_id": next(iter(work_unit_ids)) or "",
        "team": next(iter(teams)) or "",
        "cards": str(len(cards)),
        "status": "ok",
    }


def validate_card_pair(ops_card: dict[str, str], team_card: dict[str, str]) -> dict[str, str]:
    if ops_card.get("surface") != "ops-feed":
        raise ValueError("ops card must have surface ops-feed")
    if team_card.get("surface") != "team-detail":
        raise ValueError("team card must have surface team-detail")
    if ops_card.get("work_unit_id") != team_card.get("work_unit_id"):
        raise ValueError("paired cards must use the same Work Unit id")
    if ops_card.get("team") != team_card.get("team"):
        raise ValueError("paired cards must use the same team")

    ops_kind = ops_card["kind"]
    team_kind = team_card["kind"]
    if ops_kind == "ASSIGNED" and team_kind != "ASSIGNED_DETAIL":
        raise ValueError("ops-feed ASSIGNED pairs with team-detail ASSIGNED_DETAIL")
    if ops_kind == "COMPLETED" and team_kind != "ACCEPTED":
        raise ValueError("ops-feed COMPLETED pairs with team-detail ACCEPTED")
    if ops_kind == "BLOCKED" and team_kind != "BLOCKED_DETAIL":
        raise ValueError("ops-feed BLOCKED pairs with team-detail BLOCKED_DETAIL")

    ops_decision = ops_card.get("decision")
    team_decision = team_card.get("decision")
    if ops_decision and team_decision and ops_decision != team_decision:
        raise ValueError("paired cards must not disagree on decision")

    return {
        "work_unit_id": ops_card["work_unit_id"],
        "team": ops_card["team"],
        "ops_kind": ops_kind,
        "team_kind": team_kind,
        "status": "ok",
    }


def cmd_alerts(args: argparse.Namespace) -> int:
    try:
        data = read_json(args.pulse_json)
        events = [event_from_alert(alert, args.source_ref) for alert in normalize_alerts(data)]
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"events": events}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    if not events:
        print("No Discord alert events.")
        return 0
    print("\n\n".join(format_text_event(event) for event in events))
    return 0


def cmd_card(args: argparse.Namespace) -> int:
    try:
        card = card_from_args(args)
        text = format_text_card(card)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"card": card, "text": text}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(text)
    return 0


def cmd_card_pair(args: argparse.Namespace) -> int:
    try:
        result = validate_card_pair(
            read_card_json(args.ops_card_json),
            read_card_json(args.team_card_json),
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"pair": result}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(
        "OK paired visibility cards: "
        f"{result['work_unit_id']} · {result['team']} "
        f"{result['ops_kind']} + {result['team_kind']}"
    )
    return 0


def cmd_card_sequence(args: argparse.Namespace) -> int:
    try:
        result = validate_card_sequence([read_card_json(path) for path in args.card_json])
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"sequence": result}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(
        "OK visibility card sequence: "
        f"{result['work_unit_id']} · {result['team']} · {result['cards']} cards"
    )
    return 0


def proof_row_from_card(
    card: dict[str, str],
    text: str,
    args: argparse.Namespace,
    send_result: dict[str, Any],
    readback_result: dict[str, Any],
    sent_message_id: str,
    readback_message_id: str,
    discord_timestamp: str,
    transition_at: str,
    sent_at: str,
    readback_at: str,
    readback_ok: bool,
    error: str = "",
) -> dict[str, Any]:
    card_id = stable_card_id(card, text)
    return {
        "proof_version": 1,
        "proof_id": f"{card['work_unit_id']}:{card['surface']}:{card['kind']}:{card_id}",
        "card_id": card_id,
        "work_unit_id": card["work_unit_id"],
        "team": card["team"],
        "surface": card["surface"],
        "kind": card["kind"],
        "target": args.target,
        "channel": args.channel,
        "thread_id": args.thread_id or "",
        "transition_at": transition_at,
        "sent_at": sent_at,
        "readback_at": readback_at,
        "discord_message_id": readback_message_id or sent_message_id,
        "discord_timestamp": discord_timestamp or readback_at,
        "readback_ok": readback_ok,
        "dry_run": bool(args.dry_run),
        "error": error,
        "send_result": result_summary(send_result),
        "readback_result": {
            **result_summary(readback_result),
            "matched": readback_ok,
            "matched_message_id": readback_message_id,
        },
    }


def cmd_publish_card(args: argparse.Namespace) -> int:
    try:
        card = read_card_json(args.card_json)
        text = format_text_card(card)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    transition_at = args.transition_at or utc_now_iso()
    sent_at = utc_now_iso()

    if args.dry_run:
        project_sync = run_project_one_shot_sync(card, args)
        readback_at = utc_now_iso()
        row = proof_row_from_card(
            card,
            text,
            args,
            {"dryRun": True},
            {"dryRun": True},
            "dry-run",
            "dry-run",
            readback_at,
            transition_at,
            sent_at,
            readback_at,
            True,
        )
        append_jsonl(args.proof_log, row)
        if args.format == "json":
            print(
                json.dumps(
                    {"publish": row, "text": text, "project_sync": project_sync},
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
        else:
            print(f"DRY-RUN publish-card proof recorded: {row['proof_id']}")
            if project_sync.get("enabled"):
                print(f"DRY-RUN project one-shot sync ok: {str(project_sync.get('ok')).lower()}")
        return 0

    command = [
        "openclaw",
        "message",
        "send",
        "--channel",
        args.channel,
        "--target",
        args.target,
        "--message",
        text,
        "--json",
    ]
    if args.account:
        command.extend(["--account", args.account])
    if args.thread_id:
        command.extend(["--thread-id", args.thread_id])

    code, send_result, stdout, stderr = run_openclaw_message(command)
    sent_at = utc_now_iso()
    if code != 0:
        row = proof_row_from_card(
            card,
            text,
            args,
            send_result,
            {},
            "",
            "",
            "",
            transition_at,
            sent_at,
            "",
            False,
            stderr.strip() or stdout.strip() or "send failed",
        )
        append_jsonl(args.proof_log, row)
        print(f"error: Discord publish send failed; proof recorded as incomplete: {row['error']}", file=sys.stderr)
        return 1

    sent_message_id = first_sent_message_id(send_result)
    readback_ok, readback_message_id, discord_timestamp, readback_result, readback_error = readback_match(
        args, text, sent_message_id
    )
    readback_at = utc_now_iso()
    row = proof_row_from_card(
        card,
        text,
        args,
        send_result,
        readback_result,
        sent_message_id,
        readback_message_id,
        discord_timestamp,
        transition_at,
        sent_at,
        readback_at,
        readback_ok,
        readback_error,
    )
    append_jsonl(args.proof_log, row)

    if not readback_ok:
        print(f"error: Discord publish readback failed; proof recorded as incomplete: {readback_error}", file=sys.stderr)
        return 1

    project_sync = run_project_one_shot_sync(card, args)
    if project_sync.get("enabled") and not project_sync.get("ok"):
        print(f"warning: Project one-shot sync failed: {project_sync.get('error')}", file=sys.stderr)

    if args.format == "json":
        print(json.dumps({"publish": row, "project_sync": project_sync}, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(
            "OK published visibility card: "
            f"{card['work_unit_id']} · {card['team']} · {card['surface']} {card['kind']} · "
            f"{row['discord_message_id']}"
        )
    return 0


def validate_proof_rows(
    rows: list[dict[str, Any]],
    work_unit_id: str,
    require_checkpoint: bool,
    min_live_span_seconds: int,
) -> dict[str, Any]:
    filtered = [row for row in rows if str(row.get("work_unit_id")) == work_unit_id]
    if not filtered:
        raise ValueError(f"proof log contains no rows for Work Unit id: {work_unit_id}")

    failed = [row for row in filtered if not row.get("readback_ok")]
    if failed:
        kinds = ", ".join(f"{row.get('surface')} {row.get('kind')}" for row in failed)
        raise ValueError(f"proof log contains incomplete send/readback rows: {kinds}")
    if any(row.get("dry_run") for row in filtered):
        raise ValueError("dry-run rows cannot satisfy live visibility proof")

    seen_card_ids: set[str] = set()
    for row in filtered:
        card_id = str(row.get("card_id") or "")
        if not card_id:
            raise ValueError("proof row missing card_id")
        if card_id in seen_card_ids:
            raise ValueError(f"duplicate proof card_id cannot count as fresh progress: {card_id}")
        seen_card_ids.add(card_id)
        for field in PROOF_TIMESTAMP_FIELDS:
            parse_timestamp(str(row.get(field) or ""), field)

    events = [(str(row.get("surface")), str(row.get("kind"))) for row in filtered]
    required = [
        ("ops-feed", "ASSIGNED"),
        ("team-detail", "ASSIGNED_DETAIL"),
        ("team-detail", "STARTED"),
        ("team-detail", "RESULT_READY"),
    ]
    for event in required:
        if event not in events:
            raise ValueError(f"proof log missing required live event: {event[0]} {event[1]}")

    def event_time(surface: str, kind: str) -> datetime:
        return min(
            parse_timestamp(str(row["discord_timestamp"]), "discord_timestamp")
            for row in filtered
            if row.get("surface") == surface and row.get("kind") == kind
        )

    if event_time("ops-feed", "ASSIGNED") > event_time("team-detail", "ASSIGNED_DETAIL"):
        raise ValueError("ops-feed ASSIGNED must be read back before team-detail ASSIGNED_DETAIL")
    if event_time("team-detail", "ASSIGNED_DETAIL") > event_time("team-detail", "STARTED"):
        raise ValueError("team-detail ASSIGNED_DETAIL must be read back before STARTED")
    if event_time("team-detail", "STARTED") > event_time("team-detail", "RESULT_READY"):
        raise ValueError("team-detail STARTED must be read back before RESULT_READY")

    result_ready_time = event_time("team-detail", "RESULT_READY")
    checkpoint_rows = [
        row for row in filtered if row.get("surface") == "team-detail" and row.get("kind") == "CHECKPOINT"
    ]
    if require_checkpoint and not checkpoint_rows:
        raise ValueError("live proof requires at least one team-detail CHECKPOINT")
    for checkpoint in checkpoint_rows:
        checkpoint_time = parse_timestamp(str(checkpoint["discord_timestamp"]), "discord_timestamp")
        if checkpoint_time >= result_ready_time:
            raise ValueError("team-detail CHECKPOINT must have a Discord timestamp before RESULT_READY")

    first_time = min(parse_timestamp(str(row["discord_timestamp"]), "discord_timestamp") for row in filtered)
    last_time = max(parse_timestamp(str(row["discord_timestamp"]), "discord_timestamp") for row in filtered)
    live_span_seconds = int((last_time - first_time).total_seconds())
    if min_live_span_seconds and live_span_seconds < min_live_span_seconds:
        raise ValueError(
            "live proof span is too short; possible burst/replay: "
            f"{live_span_seconds}s < {min_live_span_seconds}s"
        )

    final_reviews = [event for event in events if event in {("team-detail", "ACCEPTED"), ("team-detail", "REVISE"), ("team-detail", "BLOCKED_DETAIL")}]
    if len(final_reviews) != 1:
        raise ValueError("proof log must contain exactly one team-detail final review")
    final_surface, final_kind = final_reviews[0]
    if event_time(final_surface, final_kind) < result_ready_time:
        raise ValueError("team-detail final review must follow RESULT_READY")

    closeouts = [event for event in events if event in {("ops-feed", "COMPLETED"), ("ops-feed", "BLOCKED")}]
    if len(closeouts) != 1:
        raise ValueError("proof log must contain exactly one owner closeout")
    closeout_surface, closeout_kind = closeouts[0]
    if event_time(closeout_surface, closeout_kind) < event_time(final_surface, final_kind):
        raise ValueError("owner closeout must follow team-detail final review")

    return {
        "work_unit_id": work_unit_id,
        "rows": len(filtered),
        "checkpoints": len(checkpoint_rows),
        "live_span_seconds": str(live_span_seconds),
        "status": "ok",
    }


def cmd_proof_validate(args: argparse.Namespace) -> int:
    try:
        result = validate_proof_rows(
            read_jsonl(args.proof_log),
            args.work_unit_id,
            args.require_checkpoint,
            args.min_live_span_seconds,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"proof": result}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(
        "OK live visibility proof: "
        f"{result['work_unit_id']} · {result['rows']} rows · "
        f"{result['checkpoints']} checkpoints · {result['live_span_seconds']}s"
    )
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    try:
        original = read_text(args.message_file)
        text = compact_discord_text(original, args.limit)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(
            json.dumps(
                {
                    "text": text,
                    "generation_target_chars": DISCORD_GENERATION_TARGET_CHARS,
                    "original_chars": len(original),
                    "original_content_units": discord_content_units(original),
                    "output_chars": len(text),
                    "output_content_units": discord_content_units(text),
                    "compacted": text != original,
                    "limit": args.limit,
                },
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
        )
        return 0

    print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compose, publish, and validate Company Ops Discord visibility events."
    )
    subparsers = parser.add_subparsers(dest="resource")

    alerts = subparsers.add_parser("alerts", help="Format Pulse Monitor alerts for #ops-alerts")
    alerts.add_argument("--pulse-json", default="-", help="Pulse Monitor JSON path, or '-' for stdin")
    alerts.add_argument("--source-ref", required=True, help="Ledger or claim source ref to include")
    alerts.add_argument("--format", choices=("text", "json"), default="text")
    alerts.set_defaults(func=cmd_alerts)

    card = subparsers.add_parser(
        "card",
        help="Compose purpose-specific ops-feed briefing cards or team-detail trail messages",
    )
    card.add_argument(
        "--surface",
        required=True,
        choices=tuple(sorted(VISIBILITY_SURFACES)),
        help="Card surface: ops-feed or team-detail",
    )
    card.add_argument(
        "--kind",
        required=True,
        help=(
            "Card kind. ops-feed: ASSIGNED, COMPLETED, BLOCKED. "
            "team-detail: ASSIGNED_DETAIL, STARTED, CHECKPOINT, RESULT_READY, ACCEPTED, REVISE, BLOCKED_DETAIL."
        ),
    )
    card.add_argument("--work-unit-id", required=True, help="Work Unit id or task id")
    card.add_argument("--team", required=True, help="Responsible team or Team Lead")
    card.add_argument("--problem", default="", help="Problem statement for request/blocker cards")
    card.add_argument("--request", default="", help="User-facing request summary for ops-feed")
    card.add_argument("--criteria", default="", help="Success criteria or acceptance criteria")
    card.add_argument("--caution", default="", help="Scope limit or caution")
    card.add_argument("--evidence", default="", help="Human-readable evidence or basis")
    card.add_argument("--next", required=True, help="Expected next action")
    card.add_argument("--outcome", default="", help="Completion outcome for ops-feed")
    card.add_argument("--criteria-result", default="", help="Criteria-vs-result summary")
    card.add_argument("--decision", default="", help="Operations Lead decision")
    card.add_argument("--verification", default="", help="Verification summary")
    card.add_argument("--cause", default="", help="Blocker cause")
    card.add_argument("--needed", default="", help="Needed action or decision")
    card.add_argument("--goal", default="", help="Team assignment goal")
    card.add_argument("--scope", default="", help="Team assignment scope")
    card.add_argument("--report", default="", help="Expected Team Lead report format")
    card.add_argument("--result", default="", help="Team Lead result summary")
    card.add_argument("--risks", default="", help="Remaining risks")
    card.add_argument("--reason", default="", help="Operations Lead review reason")
    card.add_argument("--status", default="", help="Team execution status")
    card.add_argument("--current-slice", default="", help="Current long-running slice for CHECKPOINT")
    card.add_argument("--elapsed", default="", help="Elapsed time or progress age for CHECKPOINT")
    card.add_argument("--next-checkpoint", default="", help="Next expected checkpoint time/window")
    card.add_argument("--source", default="", help="Source artifact or local proof reference")
    card.add_argument(
        "--team-final-review-kind",
        default="",
        choices=("", *tuple(sorted(TEAM_FINAL_REVIEW_EVENTS))),
        help="Required gate for ops-feed completion/blocker cards",
    )
    card.add_argument("--format", choices=("text", "json"), default="text")
    card.set_defaults(func=cmd_card)

    card_pair = subparsers.add_parser(
        "card-pair",
        help="Validate one ops-feed card JSON against one team-detail card JSON",
    )
    card_pair.add_argument("--ops-card-json", required=True, help="ops-feed card JSON path")
    card_pair.add_argument("--team-card-json", required=True, help="team-detail card JSON path")
    card_pair.add_argument("--format", choices=("text", "json"), default="text")
    card_pair.set_defaults(func=cmd_card_pair)

    card_sequence = subparsers.add_parser(
        "card-sequence",
        help="Validate ordered ops-feed and team-detail cards for one Work Unit",
    )
    card_sequence.add_argument(
        "--card-json",
        required=True,
        action="append",
        help="Card JSON path in the actual planned Discord posting order",
    )
    card_sequence.add_argument("--format", choices=("text", "json"), default="text")
    card_sequence.set_defaults(func=cmd_card_sequence)

    publish_card = subparsers.add_parser(
        "publish-card",
        help="Send one composed Discord card, read it back, and append JSONL proof",
    )
    publish_card.add_argument("--card-json", required=True, help="Card JSON path")
    publish_card.add_argument("--target", required=True, help="Discord target, for example channel:<id>")
    publish_card.add_argument("--proof-log", required=True, help="JSONL proof log path to append")
    publish_card.add_argument("--channel", default="discord", help="OpenClaw message channel")
    publish_card.add_argument("--account", default="", help="OpenClaw channel account id")
    publish_card.add_argument("--thread-id", default="", help="Optional Discord thread id")
    publish_card.add_argument("--transition-at", default="", help="UTC ISO timestamp for the operating transition")
    publish_card.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    publish_card.add_argument("--dry-run", action="store_true", help="Record dry-run proof without sending")
    publish_card.add_argument(
        "--project-sync-field-map",
        default="",
        help="Optional Project field-map JSON; enables nonblocking one-shot sync after successful publish",
    )
    publish_card.add_argument(
        "--project-sync-artifact-root",
        default="docs/examples/manual-dry-run",
        help="Artifact root passed to project-sync one-shot",
    )
    publish_card.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync one-shot; empty disables ledger",
    )
    publish_card.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful non-dry-run one-shot sync",
    )
    publish_card.add_argument("--format", choices=("text", "json"), default="text")
    publish_card.set_defaults(func=cmd_publish_card)

    proof_validate = subparsers.add_parser(
        "proof-validate",
        help="Validate timestamped publish-card JSONL proof for one Work Unit",
    )
    proof_validate.add_argument("--proof-log", required=True, help="JSONL proof log path")
    proof_validate.add_argument("--work-unit-id", required=True, help="Work Unit id to validate")
    proof_validate.add_argument(
        "--require-checkpoint",
        action="store_true",
        help="Require at least one CHECKPOINT before RESULT_READY",
    )
    proof_validate.add_argument(
        "--min-live-span-seconds",
        type=int,
        default=0,
        help="Fail if Discord timestamps span less than this many seconds",
    )
    proof_validate.add_argument("--format", choices=("text", "json"), default="text")
    proof_validate.set_defaults(func=cmd_proof_validate)

    guard = subparsers.add_parser(
        "guard",
        help="Compact arbitrary Discord-bound text to a single-message budget",
    )
    guard.add_argument("--message-file", default="-", help="Message text path, or '-' for stdin")
    guard.add_argument(
        "--limit",
        type=int,
        default=DISCORD_MESSAGE_TARGET_CHARS,
        help=f"Maximum output chars, <= {DISCORD_MESSAGE_LIMIT}",
    )
    guard.add_argument("--format", choices=("text", "json"), default="text")
    guard.set_defaults(func=cmd_guard)

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
