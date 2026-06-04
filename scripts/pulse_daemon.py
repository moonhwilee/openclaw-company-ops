#!/usr/bin/env python3
"""Run Pulse Monitor checks repeatedly without installing a scheduler."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ops_claim_ledger import DEFAULT_LEDGER


SCRIPT_DIR = Path(__file__).resolve().parent
PULSE = SCRIPT_DIR / "pulse_monitor.py"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_pulse(args: argparse.Namespace) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(PULSE),
        "pulse",
        "check",
        "--ledger",
        str(args.ledger),
        "--format",
        "json",
    ]
    if args.session_snapshot:
        command.extend(["--session-snapshot", str(args.session_snapshot)])
    if args.now:
        command.extend(["--now", args.now])
    return subprocess.run(command, check=False, text=True, capture_output=True)


def append_jsonl(path: Path | None, record: dict[str, Any]) -> None:
    line = json.dumps(record, sort_keys=True, ensure_ascii=False)
    if path is None:
        print(line)
        return
    expanded = path.expanduser()
    expanded.parent.mkdir(parents=True, exist_ok=True)
    with expanded.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def cmd_run(args: argparse.Namespace) -> int:
    if args.interval_seconds < 1:
        print("error: --interval-seconds must be >= 1", file=sys.stderr)
        return 2
    if args.max_runs is not None and args.max_runs < 1:
        print("error: --max-runs must be >= 1", file=sys.stderr)
        return 2

    run_count = 0
    while True:
        run_count += 1
        checked_at = utc_now()
        result = run_pulse(args)
        record: dict[str, Any] = {
            "checked_at": checked_at,
            "run": run_count,
            "returncode": result.returncode,
        }
        if result.returncode == 0:
            try:
                record.update(json.loads(result.stdout))
            except json.JSONDecodeError:
                record["error"] = "pulse output was not valid JSON"
                record["stdout"] = result.stdout
                append_jsonl(args.output_jsonl, record)
                return 1
        else:
            record["error"] = result.stderr.strip() or result.stdout.strip() or "pulse check failed"
            append_jsonl(args.output_jsonl, record)
            return 1

        append_jsonl(args.output_jsonl, record)
        if args.max_runs is not None and run_count >= args.max_runs:
            return 0
        time.sleep(args.interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repeated alert-only Pulse Monitor checks.")
    subparsers = parser.add_subparsers(dest="resource")

    daemon = subparsers.add_parser("daemon", help="Run repeated pulse checks")
    daemon_subparsers = daemon.add_subparsers(dest="action")

    run = daemon_subparsers.add_parser("run", help="Run pulse checks until stopped or max-runs is reached")
    run.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help=f"JSON ledger path, default: {DEFAULT_LEDGER}",
    )
    run.add_argument("--session-snapshot", type=Path, help="Optional JSON session signal snapshot")
    run.add_argument("--output-jsonl", type=Path, help="Optional JSONL output log path")
    run.add_argument("--interval-seconds", type=int, default=300)
    run.add_argument("--max-runs", type=int, help="Bounded run count for smoke tests or foreground checks")
    run.add_argument("--now", help="Override pulse check time for deterministic tests")
    run.set_defaults(func=cmd_run)

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
