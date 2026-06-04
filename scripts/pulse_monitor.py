#!/usr/bin/env python3
"""Run alert-only checks against the OpenClaw Company Ops claim ledger."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from ops_claim_ledger import DEFAULT_LEDGER, get_claims, load_ledger


ALERT_SESSION_MISMATCH = "SESSION_MISMATCH"
ALERT_COMPACTION_RECOVERY_SUSPECTED = "COMPACTION_RECOVERY_SUSPECTED"
ALERT_CLAIM_STALE = "CLAIM_STALE"


def parse_time(value: str, *, field: str) -> dt.datetime:
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601 datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
    return parsed.astimezone(dt.timezone.utc)


def parse_now(value: str | None) -> dt.datetime:
    if value is None:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return parse_time(value, field="--now")


def load_session_snapshot(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"active_owner_session_refs": [], "compaction_counts": {}}
    expanded = path.expanduser()
    try:
        data = json.loads(expanded.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"session snapshot not found: {expanded}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"session snapshot is not valid JSON: {expanded}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"session snapshot root must be a JSON object: {expanded}")
    active = data.get("active_owner_session_refs", [])
    compactions = data.get("compaction_counts", {})
    if not isinstance(active, list) or not all(isinstance(item, str) for item in active):
        raise ValueError("session snapshot active_owner_session_refs must be a string list")
    if not isinstance(compactions, dict):
        raise ValueError("session snapshot compaction_counts must be a JSON object")
    return {
        "active_owner_session_refs": active,
        "compaction_counts": compactions,
    }


def is_stale(claim: dict[str, Any], now: dt.datetime) -> bool:
    expected_until = claim.get("expected_until")
    if not isinstance(expected_until, str) or not expected_until.strip():
        raise ValueError(f"{claim.get('claim_ref', '<unknown>')} expected_until is required")
    return parse_time(expected_until, field="expected_until") < now


def to_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def build_alert(
    claim: dict[str, Any],
    alert_type: str,
    reason: str,
    *,
    now: dt.datetime,
) -> dict[str, Any]:
    return {
        "alert": alert_type,
        "claim_ref": claim.get("claim_ref", ""),
        "work_unit_id": claim.get("work_unit_id", ""),
        "owner_session_ref": claim.get("owner_session_ref", ""),
        "expected_state": claim.get("expected_state", ""),
        "expected_until": claim.get("expected_until", ""),
        "checked_at": now.isoformat().replace("+00:00", "Z"),
        "reason": reason,
    }


def evaluate_claims(
    claims: list[dict[str, Any]],
    *,
    active_owner_session_refs: set[str],
    compaction_counts: dict[str, Any],
    now: dt.datetime,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    has_active_snapshot = bool(active_owner_session_refs)

    for claim in claims:
        stale = is_stale(claim, now)
        owner_ref = claim.get("owner_session_ref")
        owner = owner_ref if isinstance(owner_ref, str) else ""

        if has_active_snapshot and owner not in active_owner_session_refs:
            alerts.append(
                build_alert(
                    claim,
                    ALERT_SESSION_MISMATCH,
                    "owner session ref is not present in the supplied active session snapshot",
                    now=now,
                )
            )

        current_compaction = to_int(compaction_counts.get(owner))
        last_seen_compaction = to_int(claim.get("last_seen_compaction_count"))
        if (
            stale
            and current_compaction is not None
            and last_seen_compaction is not None
            and current_compaction > last_seen_compaction
        ):
            alerts.append(
                build_alert(
                    claim,
                    ALERT_COMPACTION_RECOVERY_SUSPECTED,
                    "compaction count increased and the claim was not refreshed before expected_until",
                    now=now,
                )
            )

        if stale:
            alerts.append(
                build_alert(
                    claim,
                    ALERT_CLAIM_STALE,
                    "claim was not refreshed before expected_until",
                    now=now,
                )
            )

    return alerts


def cmd_check(args: argparse.Namespace) -> int:
    try:
        now = parse_now(args.now)
        ledger = load_ledger(args.ledger)
        snapshot = load_session_snapshot(args.session_snapshot)
        claims_by_ref = get_claims(ledger)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    claims = [
        claim
        for claim in sorted(claims_by_ref.values(), key=lambda item: item.get("claim_ref", ""))
        if args.claim_ref is None or claim.get("claim_ref") == args.claim_ref
    ]
    if args.claim_ref and not claims:
        print(f"error: claim not found: {args.claim_ref}", file=sys.stderr)
        return 1

    try:
        alerts = evaluate_claims(
            claims,
            active_owner_session_refs=set(snapshot["active_owner_session_refs"]),
            compaction_counts=snapshot["compaction_counts"],
            now=now,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"alerts": alerts}, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    if not alerts:
        print("OK no alerts")
        return 0
    for alert in alerts:
        print(
            f"{alert['alert']} "
            f"{alert['claim_ref']} "
            f"{alert['work_unit_id']} "
            f"owner={alert['owner_session_ref']} "
            f"until={alert['expected_until']} "
            f"reason={alert['reason']}"
        )
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help=f"JSON ledger path, default: {DEFAULT_LEDGER}",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run alert-only Company Ops pulse checks.")
    subparsers = parser.add_subparsers(dest="resource")

    pulse = subparsers.add_parser("pulse", help="Run Pulse Monitor checks")
    pulse_subparsers = pulse.add_subparsers(dest="action")

    check = pulse_subparsers.add_parser("check", help="Check claim freshness and session signals")
    add_common(check)
    check.add_argument("--claim-ref", help="Limit checks to one claim ref")
    check.add_argument("--session-snapshot", type=Path, help="Optional JSON session signal snapshot")
    check.add_argument("--now", help="Override current time for deterministic checks")
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.set_defaults(func=cmd_check)

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
