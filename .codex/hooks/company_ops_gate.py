#!/usr/bin/env python3
"""Repo-local Company Ops hook guard.

The guard is intentionally small: it inspects hook payloads, returns
actionable feedback, and never mutates operating state.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
DEFAULT_WORK_UNIT_ROOT = REPO_ROOT / "docs" / "work-units"
WORK_UNIT_RE = re.compile(r"\bWU-[A-Z0-9]+(?:-[A-Z0-9]+)+\b")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def load_payload() -> Any:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def iter_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            strings.extend(iter_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(iter_strings(item))
    return strings


def payload_text(payload: Any) -> str:
    return "\n".join(iter_strings(payload))


def get_mode(args: argparse.Namespace, payload: Any) -> str:
    if args.mode:
        return args.mode
    if isinstance(payload, dict):
        event = payload.get("hook_event_name") or payload.get("event")
        if isinstance(event, str):
            normalized = event.lower()
            if normalized == "pretooluse":
                return "pretool"
            if normalized == "precompact":
                return "precompact"
            if normalized == "stop":
                return "stop"
    return "pretool"


def get_tool_command(payload: Any) -> str:
    if not isinstance(payload, dict):
        return payload_text(payload)

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cmd", "command", "source"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
        args = tool_input.get("args")
        if isinstance(args, dict):
            for key in ("cmd", "command", "source"):
                value = args.get(key)
                if isinstance(value, str):
                    return value
    for key in ("cmd", "command", "source"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return payload_text(payload)


def normalize_command(command: str) -> str:
    command = command.replace("\\\n", " ")
    return re.sub(r"\s+", " ", command.strip())


def split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def command_contains(command: str, pattern: str) -> bool:
    return re.search(pattern, command, flags=re.IGNORECASE) is not None


def pretool_findings(payload: Any) -> list[Finding]:
    command = normalize_command(get_tool_command(payload))
    if not command:
        return []

    findings: list[Finding] = []
    lower = command.lower()
    tokens = split_command(command)
    joined_tokens = " ".join(tokens).lower()

    red_lines = [
        (
            "sudo-npm",
            r"(^|[;&|]\s*)sudo\s+npm\b",
            "sudo npm is forbidden in this workspace.",
        ),
        (
            "sudo-openclaw",
            r"(^|[;&|]\s*)sudo\s+openclaw\b",
            "sudo openclaw is forbidden in this workspace.",
        ),
        (
            "git-reset-hard",
            r"\bgit\s+reset\s+--hard\b",
            "git reset --hard is a destructive revert and needs explicit owner request.",
        ),
        (
            "git-checkout-revert",
            r"\bgit\s+checkout\s+--\s+",
            "git checkout -- can discard user changes and is blocked by default.",
        ),
        (
            "git-restore-revert",
            r"\bgit\s+restore\s+(?:\.|:/|--worktree\b|--source\b)",
            "git restore can discard user changes and is blocked by default.",
        ),
        (
            "unsafe-rm-rf",
            r"\brm\s+-(?:[^\s;|&]*r[^\s;|&]*f|[^\s;|&]*f[^\s;|&]*r)[^\n;|&]*(?:\s+/(?:\s|$)|\s+/\*(?:\s|$)|\s+\.{1,2}(?:\s|$)|\s+\*(?:\s|$)|\s+~(?:\s|$)|\s+\$HOME(?:\s|$)|\s+\$\{HOME\}(?:\s|$))",
            "unsafe rm -rf target is blocked; use trash or a narrower explicit path.",
        ),
    ]
    for code, pattern, message in red_lines:
        if command_contains(command, pattern):
            findings.append(Finding("block", code, message))

    warning_patterns = [
        (
            "possible-secret-output",
            r"\b(?:cat|printenv|env|echo)\b.*\b(?:TOKEN|SECRET|PASSWORD|PASSWD|API[_-]?KEY)\b",
            "command may print secrets; inspect locally without exposing values.",
        ),
        (
            "external-work-mutation",
            r"\bgh\s+(?:pr\s+merge|issue\s+close|issue\s+edit|project\s+item-edit)\b",
            "external work-state mutation should stay explicit and source-backed.",
        ),
    ]
    for code, pattern, message in warning_patterns:
        if command_contains(command, pattern):
            findings.append(Finding("warn", code, message))

    normal_inspection = (
        lower.startswith(("rg ", "sed ", "cat ", "ls ", "git status", "git diff", "python3 scripts/"))
        or "python3 scripts/company_ops_smoke.py multi-team" in joined_tokens
        or "python3 scripts/openclaw_company_ops.py smoke multi-team" in joined_tokens
    )
    if normal_inspection and not findings:
        findings.append(Finding("pass", "normal-inspection", "normal inspection or smoke command allowed."))

    return findings


def find_work_unit_ids(payload: Any) -> list[str]:
    found = WORK_UNIT_RE.findall(payload_text(payload))
    return sorted(set(found))


def has_real_content(path: Path, required_terms: tuple[str, ...] = ()) -> bool:
    if not path.exists() or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if len(text.strip()) < 80:
        return False
    lowered = text.lower()
    return all(term.lower() in lowered for term in required_terms)


def stop_findings(payload: Any, work_unit_root: Path) -> list[Finding]:
    work_unit_ids = find_work_unit_ids(payload)
    if not work_unit_ids:
        return [Finding("pass", "no-work-unit", "no active Work Unit signal; completion gate no-op.")]

    text = payload_text(payload).lower()
    accepting = any(word in text for word in ("accept", "accepted", "완료", "완료됐", "닫고", "closeout"))
    findings: list[Finding] = []

    for work_unit_id in work_unit_ids:
        root = work_unit_root / work_unit_id
        if not root.exists():
            findings.append(
                Finding(
                    "warn",
                    "work-unit-artifact-dir-missing",
                    f"{work_unit_id} has no repo-local artifact directory; role-specific gate no-op.",
                )
            )
            continue
        required = {
            "assignment.md": (),
            "claim.md": (),
            "evidence.md": ("verification",),
        }
        if accepting:
            required["decision.md"] = ("decision",)
        for filename, terms in required.items():
            path = root / filename
            if not has_real_content(path, terms):
                findings.append(
                    Finding(
                        "block",
                        "missing-work-unit-artifact",
                        f"{work_unit_id} completion is missing usable {filename}.",
                    )
                )

    if not findings:
        findings.append(Finding("pass", "work-unit-artifacts-present", "required Work Unit artifacts are present."))
    return findings


def precompact_findings(payload: Any) -> list[Finding]:
    work_unit_ids = find_work_unit_ids(payload)
    if not work_unit_ids:
        return [Finding("pass", "no-work-unit", "no active Work Unit signal; handoff gate no-op.")]

    text = payload_text(payload).lower()
    required_terms = ("claim", "evidence", "decision", "next")
    missing = [term for term in required_terms if term not in text]
    if missing:
        return [
            Finding(
                "warn",
                "handoff-incomplete",
                "handoff should preserve Work Unit id, claim, evidence, decision, blocker if any, and next action.",
            )
        ]
    return [Finding("pass", "handoff-present", "handoff preserves Work Unit state and next action.")]


def choose_status(findings: list[Finding]) -> str:
    if any(finding.severity == "block" for finding in findings):
        return "block"
    if any(finding.severity == "warn" for finding in findings):
        return "warn"
    return "pass"


def emit(mode: str, findings: list[Finding]) -> int:
    status = choose_status(findings)
    payload = {
        "status": status,
        "mode": mode,
        "findings": [finding.__dict__ for finding in findings],
        "mutation": "none",
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 2 if status == "block" else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Company Ops repo-local hook guard.")
    parser.add_argument("--mode", choices=("pretool", "stop", "precompact"))
    parser.add_argument(
        "--work-unit-root",
        type=Path,
        default=DEFAULT_WORK_UNIT_ROOT,
        help="Work Unit artifact root; default: docs/work-units",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = load_payload()
    mode = get_mode(args, payload)
    if mode == "pretool":
        findings = pretool_findings(payload)
    elif mode == "stop":
        findings = stop_findings(payload, args.work_unit_root)
    elif mode == "precompact":
        findings = precompact_findings(payload)
    else:
        findings = [Finding("warn", "unknown-mode", f"unknown hook mode: {mode}")]
    if not findings:
        findings = [Finding("pass", "no-op", "no relevant Company Ops hook signal.")]
    return emit(mode, findings)


if __name__ == "__main__":
    raise SystemExit(main())
