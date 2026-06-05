#!/usr/bin/env python3
"""Format OpenClaw Company Ops visibility events without sending them."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


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


def format_text_visibility(event: dict[str, str]) -> str:
    lines = [
        f"[{event['kind']}] {event['work_unit_id']}",
        f"Surface: {event['surface']}",
        f"Summary: {event['summary']}",
        f"Owner: {event['owner']}",
        f"Source: {event['source']}",
    ]
    why = event.get("why")
    if why:
        lines.append(f"Why: {why}")
    verification = event.get("verification")
    if verification:
        lines.append(f"Verification: {verification}")
    public_summary = event.get("public_summary")
    if public_summary:
        lines.append(f"Public summary: {public_summary}")
    lines.append(f"Next: {event['next']}")
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


def visibility_from_args(args: argparse.Namespace) -> dict[str, str]:
    if args.surface not in VISIBILITY_SURFACES:
        raise ValueError(f"unsupported visibility surface: {args.surface}")
    allowed = OPS_FEED_EVENTS if args.surface == "ops-feed" else TEAM_DETAIL_EVENTS
    if args.kind not in allowed:
        raise ValueError(f"unsupported {args.surface} visibility kind: {args.kind}")
    return {
        "kind": args.kind,
        "surface": args.surface,
        "work_unit_id": args.work_unit_id,
        "owner": args.owner,
        "source": args.source,
        "summary": args.summary,
        "why": args.why,
        "verification": args.verification,
        "public_summary": args.public_summary,
        "next": args.next,
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


def cmd_visibility(args: argparse.Namespace) -> int:
    try:
        event = visibility_from_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"visibility": event}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(format_text_visibility(event))
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
        description="Format Company Ops Discord visibility events without sending them."
    )
    subparsers = parser.add_subparsers(dest="resource")

    alerts = subparsers.add_parser("alerts", help="Format Pulse Monitor alerts for #ops-alerts")
    alerts.add_argument("--pulse-json", default="-", help="Pulse Monitor JSON path, or '-' for stdin")
    alerts.add_argument("--source-ref", required=True, help="Ledger or claim source ref to include")
    alerts.add_argument("--format", choices=("text", "json"), default="text")
    alerts.set_defaults(func=cmd_alerts)

    visibility = subparsers.add_parser(
        "visibility", help="Format owner-summary or team-detail visibility text"
    )
    visibility.add_argument(
        "--surface",
        required=True,
        choices=tuple(sorted(VISIBILITY_SURFACES)),
        help="Visibility surface: ops-feed or team-detail",
    )
    visibility.add_argument(
        "--kind",
        required=True,
        help=(
            "Visibility kind. ops-feed: ASSIGNED, COMPLETED, BLOCKED. "
            "team-detail: ASSIGNED_DETAIL, STARTED, RESULT_READY, ACCEPTED, REVISE, BLOCKED_DETAIL."
        ),
    )
    visibility.add_argument("--work-unit-id", required=True, help="Work Unit id or task id")
    visibility.add_argument("--owner", required=True, help="Assigned Team Lead or result owner")
    visibility.add_argument("--source", default="cli-direct", help="CLI assignment, repo path, or URL")
    visibility.add_argument("--summary", required=True, help="Short human-readable summary")
    visibility.add_argument("--why", default="", help="Short reason for assignment or decision")
    visibility.add_argument("--verification", default="", help="Short verification summary for result events")
    visibility.add_argument(
        "--public-summary",
        default="",
        help="Optional English one-liner for public/package reuse",
    )
    visibility.add_argument("--next", default="none", help="Expected next action")
    visibility.add_argument("--format", choices=("text", "json"), default="text")
    visibility.set_defaults(func=cmd_visibility)

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
            "team-detail: ASSIGNED_DETAIL, STARTED, RESULT_READY, ACCEPTED, REVISE, BLOCKED_DETAIL."
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
