#!/usr/bin/env python3
"""Run bounded OpenClaw Company Ops smoke tests without external mutation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS = SCRIPT_DIR / "work_unit_artifacts.py"
CLAIMS = SCRIPT_DIR / "ops_claim_ledger.py"
PULSE = SCRIPT_DIR / "pulse_monitor.py"
DISCORD = SCRIPT_DIR / "discord_ops.py"


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True)


def require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode == 0:
        return
    message = result.stderr.strip() or result.stdout.strip() or "no output"
    raise RuntimeError(f"{label} failed: {message}")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def create_artifacts(args: argparse.Namespace, work_dir: Path, work_unit_id: str, team_lead: str) -> Path:
    output_root = work_dir / "artifacts"
    command = [
        sys.executable,
        str(ARTIFACTS),
        "work-unit",
        "create",
        "--work-unit-id",
        work_unit_id,
        "--title",
        f"Multi-team smoke slice for {team_lead}",
        "--work-card",
        f"local-smoke://{work_unit_id}",
        "--operations-lead",
        "gbee",
        "--team-lead",
        team_lead,
        "--output-root",
        str(output_root),
        "--created-at",
        args.created_at,
    ]
    if args.force:
        command.append("--force")
    require_success(run_command(command), f"artifact create {work_unit_id}")
    return output_root / work_unit_id


def create_claim(args: argparse.Namespace, ledger: Path, work_unit_id: str, team_lead: str, artifact_dir: Path) -> str:
    claim_ref = f"CLAIM-{work_unit_id}-001"
    require_success(
        run_command(
            [
                sys.executable,
                str(CLAIMS),
                "claim",
                "create",
                "--ledger",
                str(ledger),
                "--work-unit-id",
                work_unit_id,
                "--work-card",
                f"local-smoke://{work_unit_id}",
                "--claim-type",
                "execution",
                "--owner-session-ref",
                f"agent={team_lead}",
                "--expected-state",
                "working",
                "--expected-until",
                args.expected_until,
                "--last-claim",
                f"{team_lead} owns this bounded smoke slice.",
                "--last-seen-compaction-count",
                "0",
                "--assignment-packet",
                str(artifact_dir / "assignment.md"),
            ]
        ),
        f"claim create {work_unit_id}",
    )
    return claim_ref


def run_pulse_ok(args: argparse.Namespace, ledger: Path, snapshot: Path) -> None:
    result = run_command(
        [
            sys.executable,
            str(PULSE),
            "pulse",
            "check",
            "--ledger",
            str(ledger),
            "--session-snapshot",
            str(snapshot),
            "--now",
            args.now,
        ]
    )
    require_success(result, "pulse check")
    if result.stdout.strip() != "OK no alerts":
        raise RuntimeError(f"pulse check expected no alerts, got: {result.stdout.strip()}")


def update_result_ready(ledger: Path, claim_ref: str, artifact_dir: Path) -> None:
    require_success(
        run_command(
            [
                sys.executable,
                str(CLAIMS),
                "claim",
                "update",
                "--ledger",
                str(ledger),
                "--claim-ref",
                claim_ref,
                "--expected-state",
                "result_ready",
                "--last-claim",
                "Evidence has been produced for Operations Lead review.",
                "--evidence-ref",
                str(artifact_dir / "evidence.md"),
            ]
        ),
        f"claim update {claim_ref}",
    )


def load_claims(ledger: Path) -> list[dict[str, Any]]:
    result = run_command(
        [
            sys.executable,
            str(CLAIMS),
            "claim",
            "status",
            "--ledger",
            str(ledger),
            "--format",
            "json",
        ]
    )
    require_success(result, "claim status")
    parsed = json.loads(result.stdout)
    if not isinstance(parsed, list):
        raise RuntimeError("claim status did not return a claim list")
    return parsed


def run_discord_visibility_smoke() -> None:
    text_result = run_command(
        [
            sys.executable,
            str(DISCORD),
            "visibility",
            "--surface",
            "ops-feed",
            "--kind",
            "ASSIGNED",
            "--work-unit-id",
            "WU-260605-901",
            "--owner",
            "build-lab",
            "--source",
            "cli-direct",
            "--summary",
            "build-lab가 이 제한된 smoke slice를 맡았습니다.",
            "--why",
            "visibility formatter smoke입니다.",
            "--next",
            "Team Lead가 간단한 결과 요약을 반환합니다.",
        ]
    )
    require_success(text_result, "discord ops-feed visibility")
    if "[ASSIGNED] WU-260605-901" not in text_result.stdout:
        raise RuntimeError("discord ops-feed visibility did not include expected header")

    json_result = run_command(
        [
            sys.executable,
            str(DISCORD),
            "visibility",
            "--surface",
            "team-detail",
            "--kind",
            "RESULT_READY",
            "--work-unit-id",
            "WU-260605-901",
            "--owner",
            "build-lab",
            "--source",
            "local-smoke://WU-260605-901",
            "--summary",
            "Smoke 결과 상세가 Operations Lead 검토 대기 상태입니다.",
            "--verification",
            "visibility formatter JSON 파싱이 통과했습니다.",
            "--next",
            "Operations Lead가 최종 판정을 남깁니다.",
            "--format",
            "json",
        ]
    )
    require_success(json_result, "discord team-detail visibility json")
    parsed = json.loads(json_result.stdout)
    if parsed.get("visibility", {}).get("kind") != "RESULT_READY":
        raise RuntimeError("discord visibility JSON did not include RESULT_READY kind")

    accepted_result = run_command(
        [
            sys.executable,
            str(DISCORD),
            "visibility",
            "--surface",
            "team-detail",
            "--kind",
            "ACCEPTED",
            "--work-unit-id",
            "WU-260605-901",
            "--owner",
            "Operations Lead",
            "--source",
            "local-smoke://WU-260605-901/final-review",
            "--summary",
            "Operations Lead 검토 결과, smoke 결과를 수락합니다.",
            "--verification",
            "RESULT_READY 이후 ACCEPTED까지 team detail trail이 닫혔습니다.",
            "--public-summary",
            "Operations Lead accepted the bounded visibility smoke result.",
            "--next",
            "ops-feed completion summary.",
        ]
    )
    require_success(accepted_result, "discord team-detail accepted visibility")
    if "[ACCEPTED] WU-260605-901" not in accepted_result.stdout:
        raise RuntimeError("discord accepted visibility did not include expected header")


def cmd_multi_team(args: argparse.Namespace) -> int:
    work_dir = args.work_dir or Path(tempfile.mkdtemp(prefix="openclaw-company-ops-multi-team-smoke."))
    work_dir = work_dir.expanduser()
    ledger = work_dir / "claims" / "ledger.json"
    snapshot = work_dir / "session-snapshot.json"

    try:
        build_artifacts = create_artifacts(args, work_dir, "WU-260605-901", "build-lab")
        market_artifacts = create_artifacts(args, work_dir, "WU-260605-902", "market")
        build_claim = create_claim(args, ledger, "WU-260605-901", "build-lab", build_artifacts)
        create_claim(args, ledger, "WU-260605-902", "market", market_artifacts)
        write_json(
            snapshot,
            {
                "active_owner_session_refs": ["agent=build-lab", "agent=market"],
                "compaction_counts": {"agent=build-lab": 0, "agent=market": 0},
            },
        )
        run_pulse_ok(args, ledger, snapshot)
        run_discord_visibility_smoke()
        update_result_ready(ledger, build_claim, build_artifacts)
        claims = load_claims(ledger)
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if len(claims) != 2:
        print(f"error: expected 2 claims, got {len(claims)}", file=sys.stderr)
        return 1
    states = {claim.get("owner_session_ref"): claim.get("expected_state") for claim in claims}
    if states.get("agent=build-lab") != "result_ready" or states.get("agent=market") != "working":
        print(f"error: unexpected final claim states: {states}", file=sys.stderr)
        return 1

    print(f"PASS multi-team smoke work_dir={work_dir}")
    print(
        "checked artifact generation, two independent claims, pulse no-alert check, "
        "discord visibility formatting through accepted review, and one result_ready update"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Company Ops bounded smoke tests.")
    subparsers = parser.add_subparsers(dest="smoke")

    multi_team = subparsers.add_parser("multi-team", help="Run a two-team bounded operation smoke")
    multi_team.add_argument("--work-dir", type=Path, help="Smoke work directory; default: new temp dir")
    multi_team.add_argument("--force", action="store_true", help="Allow artifact regeneration in work-dir")
    multi_team.add_argument("--created-at", default="2026-06-05")
    multi_team.add_argument("--expected-until", default="2026-06-05T12:00:00+09:00")
    multi_team.add_argument("--now", default="2026-06-05T05:00:00+09:00")
    multi_team.set_defaults(func=cmd_multi_team)

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
