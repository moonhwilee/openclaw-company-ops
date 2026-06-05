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


def require_absent(text: str, forbidden: tuple[str, ...], label: str) -> None:
    leaked = [item for item in forbidden if item in text]
    if leaked:
        raise RuntimeError(f"{label} leaked internal labels: {', '.join(leaked)}")


def run_discord_card_smoke() -> None:
    forbidden_ops_labels = ("Surface:", "Owner:", "Source:", "Public summary:")
    request_result = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "ASSIGNED",
            "--work-unit-id",
            "WU-260605-901",
            "--team",
            "build-lab",
            "--problem",
            "요청-완료 visibility 흐름이 사용자 관점에서 읽히는지 확인이 필요합니다.",
            "--request",
            "build-lab에 bounded smoke 기준의 card composer 출력을 점검하도록 맡깁니다.",
            "--criteria",
            "ops-feed에는 내부 필드 없이 문제, 요청, 기준, 다음 액션이 보여야 합니다.",
            "--caution",
            "외부 Discord 전송 없이 로컬 formatter만 검증합니다.",
            "--evidence",
            "scripts/discord_ops.py card composer",
            "--next",
            "Team Lead 상세 trail을 생성합니다.",
        ]
    )
    require_success(request_result, "discord ops-feed request card")
    if "[요청] WU-260605-901 · build-lab" not in request_result.stdout:
        raise RuntimeError("ops-feed request card did not include expected header")
    for expected in ("문제:", "요청:", "기준:", "다음:"):
        if expected not in request_result.stdout:
            raise RuntimeError(f"ops-feed request card missing {expected}")
    require_absent(request_result.stdout, forbidden_ops_labels, "ops-feed request card")

    assigned_detail = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "ASSIGNED_DETAIL",
            "--work-unit-id",
            "WU-260605-901",
            "--team",
            "build-lab",
            "--goal",
            "Validate card composer output for a bounded smoke slice.",
            "--scope",
            "Local formatter only; no Discord mutation.",
            "--criteria",
            "Return concise result, evidence, verification, and risks.",
            "--caution",
            "Do not edit repo state during this smoke.",
            "--report",
            "RESULT_READY with evidence and verification.",
            "--next",
            "Team Lead returns RESULT_READY.",
        ]
    )
    require_success(assigned_detail, "discord team assigned detail card")
    if "[ASSIGNED_DETAIL] WU-260605-901 · build-lab" not in assigned_detail.stdout:
        raise RuntimeError("team assignment card did not include expected header")
    if "Goal:" not in assigned_detail.stdout or "Report:" not in assigned_detail.stdout:
        raise RuntimeError("team assignment card missing expected detail fields")

    result_ready = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "RESULT_READY",
            "--work-unit-id",
            "WU-260605-901",
            "--team",
            "build-lab",
            "--result",
            "Card composer produced separate ops-feed and team-detail messages.",
            "--evidence",
            "local smoke command output",
            "--verification",
            "request card did not expose internal labels.",
            "--risks",
            "Fresh Discord posting remains outside this smoke.",
            "--next",
            "Operations Lead review.",
        ]
    )
    require_success(result_ready, "discord team result ready card")
    if "[RESULT_READY] WU-260605-901 · build-lab" not in result_ready.stdout:
        raise RuntimeError("team result card did not include expected header")
    if "Evidence:" not in result_ready.stdout or "Verification:" not in result_ready.stdout:
        raise RuntimeError("team result card missing expected fields")

    accepted = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "ACCEPTED",
            "--work-unit-id",
            "WU-260605-901",
            "--team",
            "build-lab",
            "--decision",
            "ACCEPTED",
            "--reason",
            "The bounded output meets the card composer smoke criteria.",
            "--evidence",
            "RESULT_READY local smoke output",
            "--next",
            "ops-feed completion card.",
            "--format",
            "json",
        ]
    )
    require_success(accepted, "discord team accepted card")
    accepted_parsed = json.loads(accepted.stdout)
    accepted_text = accepted_parsed.get("text", "")
    if "[ACCEPTED] WU-260605-901 · build-lab" not in accepted_text:
        raise RuntimeError("team accepted card did not include expected header")

    blocked_completion = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "COMPLETED",
            "--work-unit-id",
            "WU-260605-901",
            "--team",
            "build-lab",
            "--outcome",
            "build-lab card smoke 결과가 Operations Lead 검토를 통과했습니다.",
            "--criteria-result",
            "내부 필드 제거와 team final review gate를 모두 충족했습니다.",
            "--decision",
            "ACCEPTED",
            "--verification",
            "request, result, accepted card output inspected.",
            "--next",
            "추가 조치 없음.",
        ]
    )
    if blocked_completion.returncode == 0:
        raise RuntimeError("ops-feed completion card passed without team final review gate")

    completion = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "COMPLETED",
            "--work-unit-id",
            "WU-260605-901",
            "--team",
            "build-lab",
            "--outcome",
            "build-lab card smoke 결과가 Operations Lead 검토를 통과했습니다.",
            "--criteria-result",
            "내부 필드 제거와 team final review gate를 모두 충족했습니다.",
            "--decision",
            "ACCEPTED",
            "--verification",
            "request, result, accepted card output inspected.",
            "--evidence",
            "team RESULT_READY and ACCEPTED card smoke",
            "--team-final-review-kind",
            "ACCEPTED",
            "--next",
            "추가 조치 없음.",
            "--format",
            "json",
        ]
    )
    require_success(completion, "discord ops-feed completion card")
    parsed = json.loads(completion.stdout)
    text = parsed.get("text", "")
    if parsed.get("card", {}).get("kind") != "COMPLETED":
        raise RuntimeError("completion card JSON did not include COMPLETED kind")
    if "[완료] WU-260605-901 · build-lab" not in text:
        raise RuntimeError("ops-feed completion card did not include expected header")
    for expected in ("결과:", "기준 대비:", "금비 판정:", "확인:", "다음:"):
        if expected not in text:
            raise RuntimeError(f"ops-feed completion card missing {expected}")
    require_absent(text, forbidden_ops_labels, "ops-feed completion card")

    with tempfile.TemporaryDirectory(prefix="openclaw-company-ops-card-pair.") as pair_dir_raw:
        pair_dir = Path(pair_dir_raw)
        ops_card_json = pair_dir / "ops-card.json"
        team_card_json = pair_dir / "team-card.json"
        ops_card_json.write_text(completion.stdout, encoding="utf-8")
        team_card_json.write_text(accepted.stdout, encoding="utf-8")
        pair_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card-pair",
                "--ops-card-json",
                str(ops_card_json),
                "--team-card-json",
                str(team_card_json),
            ]
        )
        require_success(pair_result, "discord card pair validation")
        if "OK paired visibility cards: WU-260605-901 · build-lab COMPLETED + ACCEPTED" not in pair_result.stdout:
            raise RuntimeError("card pair validation did not include expected result")


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
        run_discord_card_smoke()
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
        "discord visibility formatting, purpose-specific visibility card composition, "
        "and one result_ready update"
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
