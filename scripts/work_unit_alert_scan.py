#!/usr/bin/env python3
"""Read-only Work Unit alert scan for stalled or abnormal Company Ops work."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from work_unit_status import (
    DEFAULT_ARTIFACT_ROOT,
    WORK_UNIT_RE,
    build_summary,
    normalize_state,
    status_work_unit_id,
)


DEFAULT_ALERT_STATE_DIR = Path("~/.openclaw/state/openclaw-company-ops/alerts")
DEFAULT_WARNING_SUPPRESS_MINUTES = 60
DEFAULT_CRITICAL_SUPPRESS_MINUTES = 15
DEFAULT_SMALL_STALE_MINUTES = 30
DEFAULT_NORMAL_STALE_MINUTES = 60
DEFAULT_LONG_STALE_MINUTES = 120
TERMINAL_LIFECYCLE_STATES = {"accepted", "blocked", "done", "revision_requested"}
ACTIVE_LIFECYCLE_STATES = {"working", "assigned"}
CRITICAL_EVENT_TYPES = {"takeover_needed", "source_inconsistent", "untracked_discard"}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_time(value: str, *, field: str) -> dt.datetime:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field} is empty")
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def parse_optional_time(value: str) -> dt.datetime | None:
    try:
        return parse_time(value, field="timestamp")
    except (TypeError, ValueError):
        return None


def parse_now(value: str | None) -> dt.datetime:
    if not value:
        return utc_now()
    return parse_time(value, field="--now")


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return rows
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def work_unit_dirs(root: Path, requested: str) -> list[Path]:
    expanded = root.expanduser()
    if requested:
        return [expanded / requested]
    if not expanded.exists():
        return []
    return sorted(
        path
        for path in expanded.iterdir()
        if path.is_dir() and WORK_UNIT_RE.match(path.name)
    )


def latest_progress_time(rows: list[dict[str, Any]]) -> dt.datetime | None:
    latest: dt.datetime | None = None
    for row in rows:
        candidate = parse_optional_time(str(row.get("transition_at") or row.get("updated_at") or ""))
        if candidate and (latest is None or candidate > latest):
            latest = candidate
    return latest


def dispatch_time(dispatch: dict[str, Any]) -> dt.datetime | None:
    accepted = dispatch.get("accepted_proof") if isinstance(dispatch.get("accepted_proof"), dict) else {}
    values = [
        str(dispatch.get("dispatched_at") or ""),
        str(accepted.get("accepted_at") or ""),
    ]
    for value in values:
        parsed = parse_optional_time(value)
        if parsed:
            return parsed
    return None


def result_ready_proof_exists(rows: list[dict[str, Any]], work_unit_id: str) -> bool:
    for row in rows:
        if str(row.get("work_unit_id") or "") != work_unit_id:
            continue
        if str(row.get("kind") or "").upper() == "RESULT_READY":
            return True
        proof_id = str(row.get("proof_id") or "")
        if ":RESULT_READY:" in proof_id:
            return True
    return False


def classify_threshold(summary: dict[str, Any], args: argparse.Namespace) -> tuple[str, int]:
    work_unit_id = summary["work_unit_id"]
    if work_unit_id in set(args.small_work_unit_id or []):
        return "small", args.small_stale_minutes
    if work_unit_id in set(args.long_work_unit_id or []):
        return "long", args.long_stale_minutes

    text = " ".join(
        [
            str(summary.get("work_card") or ""),
            str(summary.get("assignment_packet") or ""),
            str(summary.get("claim", {}).get("expected_state") or ""),
            str(summary.get("progress", {}).get("phase") or ""),
            str(summary.get("progress", {}).get("current_slice") or ""),
        ]
    ).lower()
    assignment = summary.get("artifacts", {}).get("assignment.md", {}).get("fields", {})
    title = str(assignment.get("title") or "").lower()
    mode = str(assignment.get("mode") or "").lower()
    combined = f"{title} {mode} {text}"
    if any(token in combined for token in ("long-running", "live test", "protocol", "smoke", "test-heavy")):
        return "long", args.long_stale_minutes
    if any(token in combined for token in ("docs", "doc", "readme", "typo", "copy")):
        return "small", args.small_stale_minutes
    return "normal", args.normal_stale_minutes


def event_id(parts: list[str]) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def make_event(
    *,
    event_type: str,
    severity: str,
    summary: dict[str, Any],
    checked_at: str,
    reason: str,
    recommended_action: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    work_unit_id = summary["work_unit_id"]
    suppress_key = f"{work_unit_id}:{event_type}:{severity}"
    return {
        "event_id": event_id([checked_at, suppress_key, reason]),
        "event_type": event_type,
        "severity": severity,
        "work_unit_id": work_unit_id,
        "title": summary.get("artifacts", {}).get("assignment.md", {}).get("fields", {}).get("title", ""),
        "team": summary.get("claim", {}).get("owner_session_ref", ""),
        "session_ref": evidence.get("session_ref", ""),
        "work_card": summary.get("work_card", ""),
        "current_state": summary.get("current_state", ""),
        "checked_at": checked_at,
        "reason": reason,
        "recommended_action": recommended_action,
        "source": "work_unit_artifacts",
        "source_ref": summary.get("artifact_dir", ""),
        "evidence": evidence,
        "suppress_key": suppress_key,
        "auto_action": "report_only",
    }


def detect_events(summary: dict[str, Any], *, now: dt.datetime, args: argparse.Namespace) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    checked_at = now.isoformat().replace("+00:00", "Z")
    work_unit_id = summary["work_unit_id"]
    artifact_dir = Path(summary["artifact_dir"])
    progress_rows = read_jsonl(artifact_dir / "progress.jsonl")
    proof_rows = read_jsonl(artifact_dir / "visibility-proof.jsonl")
    dispatch = read_json(artifact_dir / "dispatch.json")
    latest_progress = latest_progress_time(progress_rows)
    latest_dispatch = dispatch_time(dispatch)
    latest_activity = latest_progress or latest_dispatch
    lifecycle = normalize_state(str(summary.get("current_state") or ""))

    accepted_proof = dispatch.get("accepted_proof") if isinstance(dispatch.get("accepted_proof"), dict) else {}
    accepted_status = normalize_state(str(accepted_proof.get("status") or dispatch.get("status") or ""))
    session_ref = str(dispatch.get("session_ref") or accepted_proof.get("session_ref") or "")

    if lifecycle in ACTIVE_LIFECYCLE_STATES and latest_activity:
        threshold_class, threshold_minutes = classify_threshold(summary, args)
        age_minutes = int((now - latest_activity).total_seconds() // 60)
        has_result_ready = result_ready_proof_exists(proof_rows, work_unit_id)
        if age_minutes >= threshold_minutes and not has_result_ready:
            events.append(
                make_event(
                    event_type="stale_progress",
                    severity="warning",
                    summary=summary,
                    checked_at=checked_at,
                    reason=(
                        f"No source-backed progress or RESULT_READY for {age_minutes} minutes "
                        f"(threshold={threshold_minutes}m, class={threshold_class})."
                    ),
                    recommended_action="Inspect source artifacts; owner approval is required before retry or takeover.",
                    evidence={
                        "last_activity_at": latest_activity.isoformat().replace("+00:00", "Z"),
                        "age_minutes": age_minutes,
                        "threshold_minutes": threshold_minutes,
                        "threshold_class": threshold_class,
                        "progress_ref": str(artifact_dir / "progress.jsonl"),
                        "dispatch_ref": str(artifact_dir / "dispatch.json"),
                        "session_ref": session_ref,
                    },
                )
            )

    evidence_status = normalize_state(str(summary.get("evidence", {}).get("status") or ""))
    claim_state = normalize_state(str(summary.get("claim", {}).get("expected_state") or ""))
    if (evidence_status == "result_ready" or claim_state == "result_ready") and not result_ready_proof_exists(
        proof_rows, work_unit_id
    ):
        events.append(
            make_event(
                event_type="result_missing",
                severity="warning",
                summary=summary,
                checked_at=checked_at,
                reason="Source state indicates result-ready, but live RESULT_READY proof was not found.",
                recommended_action="Inspect evidence and proof log before closeout or takeover.",
                evidence={
                    "evidence_status": evidence_status,
                    "claim_state": claim_state,
                    "proof_ref": str(artifact_dir / "visibility-proof.jsonl"),
                    "session_ref": session_ref,
                },
            )
        )

    if dispatch and accepted_status and accepted_status != "accepted":
        events.append(
            make_event(
                event_type="failure_recorded",
                severity="warning",
                summary=summary,
                checked_at=checked_at,
                reason=f"Dispatch/runtime status is {accepted_status}; Team Lead execution may not be active.",
                recommended_action="Inspect dispatch runtime proof; owner approval is required before redispatch.",
                evidence={
                    "dispatch_status": accepted_status,
                    "dispatch_ref": str(artifact_dir / "dispatch.json"),
                    "session_ref": session_ref,
                },
            )
        )

    for row in progress_rows:
        transition = normalize_state(str(row.get("transition_kind") or ""))
        retry_state = normalize_state(str(row.get("retry_state") or ""))
        if transition in {"retry", "drop", "dropped", "takeover"} or retry_state:
            events.append(
                make_event(
                    event_type="drop_or_retry_recorded",
                    severity="info",
                    summary=summary,
                    checked_at=checked_at,
                    reason="Progress log records drop, retry, or takeover-related state.",
                    recommended_action="Confirm this was owner-approved and audit-backed.",
                    evidence={
                        "transition_kind": transition,
                        "retry_state": retry_state,
                        "progress_ref": str(artifact_dir / "progress.jsonl"),
                        "transition_at": str(row.get("transition_at") or ""),
                        "session_ref": session_ref,
                    },
                )
            )
            break

    if lifecycle in TERMINAL_LIFECYCLE_STATES:
        return [event for event in events if event["event_type"] != "stale_progress"]
    return events


def load_suppress_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"version": 1, "alerts": {}}
    if not isinstance(data, dict) or not isinstance(data.get("alerts"), dict):
        return {"version": 1, "alerts": {}}
    return data


def store_suppress_state(path: Path, state: dict[str, Any]) -> None:
    expanded = path.expanduser()
    expanded.parent.mkdir(parents=True, exist_ok=True)
    expanded.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def suppress_window_minutes(event: dict[str, Any], args: argparse.Namespace) -> int:
    if event["severity"] == "critical":
        return args.critical_suppress_minutes
    if event["severity"] == "warning":
        return args.warning_suppress_minutes
    return args.info_suppress_minutes


def apply_suppression(
    events: list[dict[str, Any]],
    *,
    now: dt.datetime,
    state_path: Path,
    args: argparse.Namespace,
    update: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    state = load_suppress_state(state_path)
    alerts = state.setdefault("alerts", {})
    visible: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for event in events:
        key = event["suppress_key"]
        previous = alerts.get(key) if isinstance(alerts.get(key), dict) else {}
        previous_at = parse_optional_time(str(previous.get("last_reported_at") or ""))
        window = suppress_window_minutes(event, args)
        is_suppressed = bool(
            previous_at
            and window > 0
            and (now - previous_at).total_seconds() < window * 60
        )
        if is_suppressed:
            event = {**event, "suppressed": True, "suppressed_until_minutes": window}
            suppressed.append(event)
            continue
        visible.append({**event, "suppressed": False})
        if update:
            alerts[key] = {
                "last_reported_at": now.isoformat().replace("+00:00", "Z"),
                "event_type": event["event_type"],
                "severity": event["severity"],
                "work_unit_id": event["work_unit_id"],
            }
    if update:
        store_suppress_state(state_path, state)
    return visible, suppressed


def scan(args: argparse.Namespace) -> dict[str, Any]:
    now = parse_now(args.now)
    all_events: list[dict[str, Any]] = []
    scanned: list[str] = []
    errors: list[dict[str, str]] = []
    for artifact_dir in work_unit_dirs(args.artifact_root, args.work_unit_id):
        work_unit = artifact_dir.name
        scanned.append(work_unit)
        try:
            summary_args = argparse.Namespace(
                artifact_root=args.artifact_root,
                work_unit_id=work_unit,
                ledger=None,
                require_ledger=False,
                format="json",
            )
            summary, _ = build_summary(summary_args)
            all_events.extend(detect_events(summary, now=now, args=args))
        except (OSError, ValueError) as exc:
            errors.append({"work_unit_id": work_unit, "error": str(exc)})

    state_dir = args.state_dir.expanduser()
    visible, suppressed = apply_suppression(
        all_events,
        now=now,
        state_path=args.suppress_state or state_dir / "suppress-state.json",
        args=args,
        update=args.record or (args.discord and not args.dry_run),
    )
    return {
        "version": 1,
        "status": "alerts" if visible else "ok",
        "checked_at": now.isoformat().replace("+00:00", "Z"),
        "artifact_root": str(args.artifact_root.expanduser()),
        "scanned_work_units": scanned,
        "events": visible,
        "suppressed_events": suppressed,
        "errors": errors,
        "policy": {
            "auto_action": "report_only",
            "source_mutation": "forbidden",
            "retry_takeover": "owner_approval_required",
        },
    }


def append_audit(path: Path, payload: dict[str, Any]) -> None:
    expanded = path.expanduser()
    expanded.parent.mkdir(parents=True, exist_ok=True)
    with expanded.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")


def format_event(event: dict[str, Any]) -> str:
    title = event.get("title") or "untitled"
    lines = [
        f"[{event['severity'].upper()}] {event['event_type']} {event['work_unit_id']}",
        f"Title: {title}",
        f"State: {event.get('current_state') or 'unknown'}",
        f"Team: {event.get('team') or 'unknown'}",
        f"Reason: {event['reason']}",
        f"Next: {event['recommended_action']}",
        f"Source: {event['source_ref']}",
    ]
    work_card = event.get("work_card")
    if work_card:
        lines.append(f"Work Card: {work_card}")
    return "\n".join(lines)


def format_discord_message(payload: dict[str, Any]) -> str:
    events = payload["events"]
    if not events:
        return (
            "[OK] Company Ops alert-scan\n"
            f"Checked: {payload['checked_at']}\n"
            f"Scanned: {len(payload['scanned_work_units'])} Work Units\n"
            "Alerts: none"
        )
    lines = [
        "[ALERT] Company Ops alert-scan",
        f"Checked: {payload['checked_at']}",
        f"Events: {len(events)}",
        "",
    ]
    lines.extend("\n\n".join(format_event(event) for event in events).splitlines())
    text = "\n".join(lines)
    return text[:1900]


def send_discord(args: argparse.Namespace, text: str) -> tuple[int, dict[str, Any], str]:
    if not args.target:
        return 1, {}, "error: --target is required with --discord"
    if args.dry_run:
        return 0, {"dry_run": True, "target": args.target, "message": text}, ""
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
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    data: dict[str, Any] = {}
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                data = parsed
        except json.JSONDecodeError:
            data = {"stdout": result.stdout.strip()}
    error = result.stderr.strip() if result.returncode else ""
    return result.returncode, data, error


def print_text(payload: dict[str, Any]) -> None:
    if not payload["events"]:
        print(f"OK no alerts; scanned {len(payload['scanned_work_units'])} Work Units")
        return
    for event in payload["events"]:
        print(format_event(event))
        print()


def cmd_alert_scan(args: argparse.Namespace) -> int:
    try:
        payload = scan(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    discord_result: dict[str, Any] | None = None
    if args.discord:
        message = format_discord_message(payload)
        code, data, error = send_discord(args, message)
        discord_result = {
            "status": "sent" if code == 0 and not args.dry_run else "dry-run" if args.dry_run else "failed",
            "target": args.target,
            "error": error,
            "response": data,
            "message": message if args.dry_run else "",
        }
        payload["discord"] = discord_result
        if not args.dry_run:
            audit_path = args.audit_log or args.state_dir.expanduser() / "alerts.jsonl"
            append_audit(audit_path, {"scan": payload, "discord": discord_result})
        if code != 0:
            if args.format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
            else:
                print_text(payload)
                print(error, file=sys.stderr)
            return 1
    elif args.record:
        audit_path = args.audit_log or args.state_dir.expanduser() / "alerts.jsonl"
        append_audit(audit_path, {"scan": payload})

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print_text(payload)
    return 0


def add_alert_scan_parser(work_unit_subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    alert_scan = work_unit_subparsers.add_parser(
        "alert-scan",
        help="Read-only scan for stalled or abnormal Work Units",
    )
    alert_scan.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory containing <work-unit-id>/ source artifacts",
    )
    alert_scan.add_argument("--work-unit-id", default="", type=lambda value: status_work_unit_id(value) if value else "")
    alert_scan.add_argument("--now", default="", help="Override current UTC time for deterministic checks")
    alert_scan.add_argument("--small-stale-minutes", type=int, default=DEFAULT_SMALL_STALE_MINUTES)
    alert_scan.add_argument("--normal-stale-minutes", type=int, default=DEFAULT_NORMAL_STALE_MINUTES)
    alert_scan.add_argument("--long-stale-minutes", type=int, default=DEFAULT_LONG_STALE_MINUTES)
    alert_scan.add_argument("--small-work-unit-id", action="append", default=[])
    alert_scan.add_argument("--long-work-unit-id", action="append", default=[])
    alert_scan.add_argument("--state-dir", type=Path, default=DEFAULT_ALERT_STATE_DIR)
    alert_scan.add_argument("--suppress-state", type=Path)
    alert_scan.add_argument("--warning-suppress-minutes", type=int, default=DEFAULT_WARNING_SUPPRESS_MINUTES)
    alert_scan.add_argument("--critical-suppress-minutes", type=int, default=DEFAULT_CRITICAL_SUPPRESS_MINUTES)
    alert_scan.add_argument("--info-suppress-minutes", type=int, default=0)
    alert_scan.add_argument("--record", action="store_true", help="Record audit/suppress state without sending Discord")
    alert_scan.add_argument("--audit-log", type=Path, help="JSONL audit log path, default: <state-dir>/alerts.jsonl")
    alert_scan.add_argument("--discord", action="store_true", help="Send alert summary to Discord target")
    alert_scan.add_argument("--target", default="", help="Discord target, for example channel:<id>")
    alert_scan.add_argument("--channel", default="discord", help="OpenClaw message channel")
    alert_scan.add_argument("--account", default="", help="OpenClaw account id")
    alert_scan.add_argument("--thread-id", default="", help="Optional Discord thread id")
    alert_scan.add_argument("--dry-run", action="store_true", help="Preview Discord send without sending or recording state")
    alert_scan.add_argument("--format", choices=("text", "json"), default="text")
    alert_scan.set_defaults(func=cmd_alert_scan)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Company Ops Work Unit alert scan.")
    subparsers = parser.add_subparsers(dest="resource")
    work_unit = subparsers.add_parser("work-unit", help="Manage Work Unit alert checks")
    work_unit_subparsers = work_unit.add_subparsers(dest="action")
    add_alert_scan_parser(work_unit_subparsers)
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
