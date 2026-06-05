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

LIFECYCLE_EVENTS = {
    "ASSIGNED",
    "STARTED",
    "BLOCKED",
    "RESULT_READY",
    "DECISION",
}


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
    return "\n".join(lines)


def lifecycle_event_from_args(args: argparse.Namespace) -> dict[str, str]:
    if args.event not in LIFECYCLE_EVENTS:
        raise ValueError(f"unsupported lifecycle event: {args.event}")
    return {
        "event": args.event,
        "work_unit_id": args.work_unit_id,
        "work_card": args.work_card,
        "owner": args.owner,
        "source": args.source_artifact,
        "summary": args.summary,
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


def cmd_event(args: argparse.Namespace) -> int:
    try:
        event = lifecycle_event_from_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"event": event}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(format_text_event(event))
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

    event = subparsers.add_parser("event", help="Format a Work Unit lifecycle event for #ops-feed")
    event.add_argument(
        "--event",
        required=True,
        help="Lifecycle event name: ASSIGNED, STARTED, BLOCKED, RESULT_READY, or DECISION",
    )
    event.add_argument("--work-unit-id", required=True, help="Work Unit id")
    event.add_argument("--work-card", required=True, help="Work Card URL")
    event.add_argument("--owner", required=True, help="Current owner or next-action owner")
    event.add_argument("--source-artifact", required=True, help="Source artifact path or URL")
    event.add_argument("--summary", required=True, help="Short human-readable summary")
    event.add_argument("--next", default="none", help="Expected next action")
    event.add_argument("--format", choices=("text", "json"), default="text")
    event.set_defaults(func=cmd_event)

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
