#!/usr/bin/env python3
"""Owner-facing `/ops` router for Company Ops.

This is a thin intent-to-CLI adapter. It does not execute a hidden
orchestrator, choose teams autonomously, or mutate source artifacts unless the
called foreground Company Ops command is explicitly asked to publish.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ARTIFACT_ROOT = Path("docs/work-units")
DEFAULT_WORK_CARD_REPO = "moonhwilee/openclaw-company-ops"
DEFAULT_OPERATIONS_LEAD = "operations-lead"


def run_company_ops(args: list[str]) -> int:
    command = [sys.executable, str(SCRIPT_DIR / "openclaw_company_ops.py"), *args]
    return subprocess.run(command, check=False).returncode


def local_now() -> datetime:
    return datetime.now().astimezone()


def next_work_unit_id(artifact_root: Path) -> str:
    now = local_now()
    prefix = f"WU-{now:%y%m%d}-"
    used: set[int] = set()
    root = artifact_root.expanduser()
    if root.exists():
        for path in root.iterdir():
            name = path.name
            if name.startswith(prefix) and len(name) >= len(prefix) + 3:
                suffix = name[len(prefix) : len(prefix) + 3]
                if suffix.isdigit():
                    used.add(int(suffix))
    for index in range(1, 1000):
        if index not in used:
            return f"{prefix}{index:03d}"
    raise RuntimeError(f"no available Work Unit id for {prefix}")


def request_text(parts: list[str]) -> str:
    text = " ".join(part.strip() for part in parts if part.strip()).strip()
    if not text:
        raise ValueError("request text is required")
    return text


def compact_title(text: str, mode: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= 78:
        return collapsed
    return f"{mode}: {collapsed[:70].rstrip()}..."


def source_refs(args: argparse.Namespace, work_unit_id: str) -> list[str]:
    refs = [item.strip() for item in args.source_ref if item.strip()]
    if refs:
        return refs
    return [f"owner-request://ops/{work_unit_id}"]


def common_spec(args: argparse.Namespace, mode: str) -> dict[str, object]:
    work_unit_id = args.work_unit_id or next_work_unit_id(args.artifact_root)
    request = request_text(args.request)
    targets = {
        "ops_feed": args.ops_target or "",
        "team_detail": args.team_target or "",
    }
    spec: dict[str, object] = {
        "work_unit_id": work_unit_id,
        "title": args.title or compact_title(request, mode),
        "owner_request": request,
        "requested_by": "ops-router",
        "operations_lead": args.operations_lead,
        "team": args.team or "",
        "mode": mode,
        "goal": args.goal or request,
        "scope": args.scope or [request],
        "done_criteria": args.done_criteria,
        "verification_criteria": args.verification_criteria,
        "targets": targets,
        "work_card_repo": args.work_card_repo,
        "source_refs": source_refs(args, work_unit_id),
        "next": args.next,
        "report": args.report,
        "subagent_budget": args.subagent_budget,
        "subagent_budget_reason": args.subagent_budget_reason,
    }
    if args.target_path:
        spec["target_paths"] = args.target_path
    spec["no_go"] = args.no_go or [
        "Do not expand beyond Operations Lead-approved scope.",
        "Do not treat dashboard, Discord, labels, or comments as source truth.",
    ]
    return spec


def draft_handoff_from_spec(spec: dict[str, object], args: argparse.Namespace) -> int:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        path = Path(handle.name)
        json.dump(spec, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    try:
        return run_company_ops(
            [
                "work-unit",
                "draft-handoff",
                "--spec",
                str(path),
                "--output-root",
                str(args.artifact_root),
                "--dry-run",
                "--format",
                args.format,
            ]
        )
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def handle_goal(args: argparse.Namespace) -> int:
    if args.done_criteria is None:
        args.done_criteria = [
            "Requested outcome is completed within the approved scope.",
            "Evidence maps the result to the owner request and done criteria.",
            "Remaining risks, blockers, and follow-up routes are explicit.",
        ]
    if args.verification_criteria is None:
        args.verification_criteria = [
            "Evidence and changed artifacts are directly inspectable.",
            "Checks or review steps are recorded with concrete outputs.",
            "No source of truth is replaced by dashboard, Discord, labels, or comments.",
        ]
    return draft_handoff_from_spec(common_spec(args, "goal"), args)


def handle_verify(args: argparse.Namespace) -> int:
    if args.done_criteria is None:
        args.done_criteria = [
            "Verification report maps each criterion to concrete evidence.",
            "Candidate verdict is clearly separated from verification Work Unit completion.",
            "Failures, unknowns, and required follow-ups are explicit.",
        ]
    if args.verification_criteria is None:
        args.verification_criteria = [
            "Candidate output is not mutated by the verify Work Unit.",
            "Each pass, fail, or unknown verdict cites source evidence.",
            "Recommendations are accept, revise, or blocked with rationale.",
        ]
    args.no_go = args.no_go or [
        "Do not mutate candidate output.",
        "Do not make final closeout decisions from a verification-only Work Unit.",
    ]
    return draft_handoff_from_spec(common_spec(args, "verify"), args)


def handle_status(args: argparse.Namespace) -> int:
    command = ["status", "work-unit", "--work-unit-id", args.work_unit_id]
    if args.artifact_root:
        command.extend(["--artifact-root", str(args.artifact_root)])
    if args.no_ledger:
        command.append("--no-ledger")
    if args.require_ledger:
        command.append("--require-ledger")
    command.extend(["--format", args.format])
    return run_company_ops(command)


def handle_inbox(args: argparse.Namespace) -> int:
    command = ["work-unit", "inbox", "--result-ready"]
    if args.artifact_root:
        command.extend(["--artifact-root", str(args.artifact_root)])
    if args.team:
        command.extend(["--team", args.team])
    if args.limit:
        command.extend(["--limit", str(args.limit)])
    if args.include_stale:
        command.append("--include-stale")
    command.extend(["--format", args.format])
    return run_company_ops(command)


def handle_decide(args: argparse.Namespace) -> int:
    if args.dry_run and args.publish:
        raise ValueError("choose either --dry-run or --publish, not both")
    command = ["work-unit", "closeout", "--work-unit-id", args.work_unit_id]
    if args.artifact_root:
        command.extend(["--artifact-root", str(args.artifact_root)])
    if args.decision:
        command.extend(["--decision", args.decision])
    if args.reason:
        command.extend(["--reason", args.reason])
    if args.source_ref:
        for ref in args.source_ref:
            command.extend(["--source-ref", ref])
    if args.needed:
        command.extend(["--needed", args.needed])
    if args.blocker_source:
        command.extend(["--blocker-source", args.blocker_source])
    if args.next_owner:
        command.extend(["--next-owner", args.next_owner])
    if args.next:
        command.extend(["--next", args.next])
    command.append("--publish" if args.publish else "--dry-run")
    command.extend(["--format", args.format])
    return run_company_ops(command)


def handle_preflight(args: argparse.Namespace) -> int:
    command = ["preflight"]
    if args.artifact_root:
        command.extend(["--artifact-root", str(args.artifact_root)])
    if args.work_unit_id:
        command.extend(["--work-unit-id", args.work_unit_id])
    if args.role_context:
        command.extend(["--role-context", args.role_context])
    if args.project_sync_field_map:
        command.extend(["--project-sync-mode", "required", "--project-sync-field-map", args.project_sync_field_map])
    if args.require_discord_targets:
        command.append("--require-discord-targets")
    if args.ops_target:
        command.extend(["--ops-target", args.ops_target])
    if args.team_target:
        command.extend(["--team-target", args.team_target])
    command.extend(["--format", args.format])
    return run_company_ops(command)


def add_draft_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("request", nargs="*", help="Owner request text")
    parser.add_argument("--work-unit-id", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--team", default="")
    parser.add_argument("--goal", default="")
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--done-criteria", action="append", default=None)
    parser.add_argument("--verification-criteria", action="append", default=None)
    parser.add_argument("--source-ref", action="append", default=[])
    parser.add_argument("--target-path", action="append", default=[])
    parser.add_argument("--ops-target", default="")
    parser.add_argument("--team-target", default="")
    parser.add_argument("--work-card-repo", default=DEFAULT_WORK_CARD_REPO)
    parser.add_argument("--operations-lead", default=DEFAULT_OPERATIONS_LEAD)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--no-go", action="append", default=[])
    parser.add_argument("--next", default="Operations Lead reviews the draft and fills any needs-ops-decision fields.")
    parser.add_argument(
        "--report",
        default="Result summary, evidence links, checks performed, remaining risks, blockers.",
    )
    parser.add_argument("--subagent-budget", choices=("none", "2", "3", "5"), default="3")
    parser.add_argument("--subagent-budget-reason", default="")
    parser.add_argument("--format", choices=("text", "json"), default="text")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops",
        description="Owner-facing Company Ops router. Use through /ops or openclaw_company_ops.py ops.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    goal = sub.add_parser("goal", help="Draft a goal-mode Work Unit handoff")
    add_draft_args(goal)
    goal.set_defaults(func=handle_goal)

    verify = sub.add_parser("verify", help="Draft a verify-mode Work Unit handoff")
    add_draft_args(verify)
    verify.set_defaults(func=handle_verify)

    status = sub.add_parser("status", help="Show source-backed Work Unit status")
    status.add_argument("work_unit_id")
    status.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    status.add_argument("--no-ledger", action="store_true")
    status.add_argument("--require-ledger", action="store_true")
    status.add_argument("--format", choices=("text", "json"), default="text")
    status.set_defaults(func=handle_status)

    inbox = sub.add_parser("inbox", help="List result-ready Work Units for Operations Lead review")
    inbox.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    inbox.add_argument("--team", default="")
    inbox.add_argument("--limit", type=int, default=20)
    inbox.add_argument("--include-stale", action="store_true")
    inbox.add_argument("--format", choices=("text", "json"), default="text")
    inbox.set_defaults(func=handle_inbox)

    decide = sub.add_parser("decide", help="Preview or publish a guarded Work Unit closeout decision")
    decide.add_argument("work_unit_id")
    decide.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    decide.add_argument("--decision", choices=("accept", "revise", "blocked"), required=True)
    decide.add_argument("--reason", default="")
    decide.add_argument("--source-ref", action="append", default=[])
    decide.add_argument("--needed", default="")
    decide.add_argument("--blocker-source", default="")
    decide.add_argument("--next-owner", default="")
    decide.add_argument("--next", default="")
    decide.add_argument("--dry-run", action="store_true", help="Preview without writes or sends (default)")
    decide.add_argument("--publish", action="store_true")
    decide.add_argument("--format", choices=("text", "json"), default="text")
    decide.set_defaults(func=handle_decide)

    preflight = sub.add_parser("preflight", help="Run a foreground setup/readiness preflight")
    preflight.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    preflight.add_argument("--work-unit-id", default="")
    preflight.add_argument("--role-context", default="operations-lead")
    preflight.add_argument("--project-sync-field-map", default="")
    preflight.add_argument("--require-discord-targets", action="store_true")
    preflight.add_argument("--ops-target", default="")
    preflight.add_argument("--team-target", default="")
    preflight.add_argument("--format", choices=("text", "json"), default="text")
    preflight.set_defaults(func=handle_preflight)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
