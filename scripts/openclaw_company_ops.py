#!/usr/bin/env python3
"""Repo-local entrypoint for OpenClaw Company Ops tools."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROUTES = {
    "work-unit": ("work_unit_artifacts.py", True),
    "claim": ("ops_claim_ledger.py", True),
    "pulse": ("pulse_monitor.py", True),
    "daemon": ("pulse_daemon.py", True),
    "discord": ("discord_ops.py", False),
    "dashboard": ("dashboard_snapshot.py", True),
    "project-sync": ("project_sync.py", True),
    "status": ("work_unit_status.py", True),
    "smoke": ("company_ops_smoke.py", False),
}


def print_help() -> None:
    commands = ", ".join(sorted(ROUTES))
    print("usage: openclaw_company_ops.py <command> [args...]")
    print()
    print(f"commands: {commands}")
    print()
    print("examples:")
    print("  python3 scripts/openclaw_company_ops.py work-unit create --help")
    print("  python3 scripts/openclaw_company_ops.py claim status --help")
    print("  python3 scripts/openclaw_company_ops.py status work-unit --help")
    print("  python3 scripts/openclaw_company_ops.py project-sync dry-run --work-unit-id WU-260606-001")
    print("  python3 scripts/openclaw_company_ops.py project-sync field-map --owner @me --project-number 1 --output ~/.openclaw/state/openclaw-company-ops/project-field-map.json")
    print("  python3 scripts/openclaw_company_ops.py project-sync apply --work-unit-id WU-260606-001 --field-map ~/.openclaw/state/openclaw-company-ops/project-field-map.json")
    print("  python3 scripts/openclaw_company_ops.py pulse check --help")
    print("  python3 scripts/openclaw_company_ops.py smoke multi-team")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print_help()
        return 0

    command = argv.pop(0)
    route = ROUTES.get(command)
    if route is None:
        print(f"error: unknown command: {command}", file=sys.stderr)
        print_help()
        return 2

    target, keep_root_command = route
    script = SCRIPT_DIR / target
    if not script.exists():
        print(f"error: routed script not found: {script}", file=sys.stderr)
        return 1

    routed_args = [command, *argv] if keep_root_command else argv
    result = subprocess.run([sys.executable, str(script), *routed_args], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
