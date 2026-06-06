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
PROJECT_SYNC = SCRIPT_DIR / "project_sync.py"
HOOK_GUARD = SCRIPT_DIR.parent / ".codex" / "hooks" / "company_ops_gate.py"


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


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
    if "📌 [요청] WU-260605-901 · 🧪 build-lab" not in request_result.stdout:
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
    if "📋 [ASSIGNED_DETAIL] WU-260605-901 · 🧪 build-lab" not in assigned_detail.stdout:
        raise RuntimeError("team assignment card did not include expected header")
    if "Goal:" not in assigned_detail.stdout or "Report:" not in assigned_detail.stdout:
        raise RuntimeError("team assignment card missing expected detail fields")

    build_pq_started = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "STARTED",
            "--work-unit-id",
            "WU-260605-903",
            "--team",
            "build-pq",
            "--status",
            "PrimeQuant platform smoke started.",
            "--next",
            "Team Lead returns RESULT_READY.",
        ]
    )
    require_success(build_pq_started, "discord build-pq started card")
    if "▶️ [STARTED] WU-260605-903 · 🧱 build-pq" not in build_pq_started.stdout:
        raise RuntimeError("build-pq card did not include canonical team icon")

    checkpoint = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "CHECKPOINT",
            "--work-unit-id",
            "WU-260605-903",
            "--team",
            "build-pq",
            "--current-slice",
            "Phase 1 data inspection",
            "--status",
            "Inspecting source artifacts before implementation.",
            "--elapsed",
            "12m",
            "--next-checkpoint",
            "within 10m or at next slice boundary",
            "--source",
            "local-smoke://checkpoint",
            "--next",
            "Continue current slice.",
        ]
    )
    require_success(checkpoint, "discord team checkpoint card")
    if "⏱️ [CHECKPOINT] WU-260605-903 · 🧱 build-pq" not in checkpoint.stdout:
        raise RuntimeError("checkpoint card did not include expected header")
    for expected in ("Slice:", "Status:", "Next checkpoint:", "Next:"):
        if expected not in checkpoint.stdout:
            raise RuntimeError(f"checkpoint card missing {expected}")

    market_blocked = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "BLOCKED",
            "--work-unit-id",
            "WU-260605-904",
            "--team",
            "market",
            "--problem",
            "Market positioning input is missing.",
            "--cause",
            "No source brief was provided.",
            "--needed",
            "Owner or Operations Lead must provide the brief.",
            "--team-final-review-kind",
            "BLOCKED_DETAIL",
            "--next",
            "Wait for source brief.",
        ]
    )
    require_success(market_blocked, "discord market blocker card")
    if "⛔ [막힘] WU-260605-904 · 📣 market" not in market_blocked.stdout:
        raise RuntimeError("market card did not include canonical team icon")

    revenue_revise = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "REVISE",
            "--work-unit-id",
            "WU-260605-905",
            "--team",
            "revenue",
            "--decision",
            "REVISE",
            "--reason",
            "Pricing assumption needs one more check.",
            "--next",
            "Revenue Lead revises the result.",
        ]
    )
    require_success(revenue_revise, "discord revenue revise card")
    if "🔁 [REVISE] WU-260605-905 · 💼 revenue" not in revenue_revise.stdout:
        raise RuntimeError("revenue card did not include canonical team icon")

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
    if "📦 [RESULT_READY] WU-260605-901 · 🧪 build-lab" not in result_ready.stdout:
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
    if "✅ [ACCEPTED] WU-260605-901 · 🧪 build-lab" not in accepted_text:
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
    if "✅ [완료] WU-260605-901 · 🧪 build-lab" not in text:
        raise RuntimeError("ops-feed completion card did not include expected header")
    for expected in ("결과:", "기준 대비:", "금비 판정:", "확인:", "다음:"):
        if expected not in text:
            raise RuntimeError(f"ops-feed completion card missing {expected}")
    require_absent(text, forbidden_ops_labels, "ops-feed completion card")

    with tempfile.TemporaryDirectory(prefix="openclaw-company-ops-card-pair.") as pair_dir_raw:
        pair_dir = Path(pair_dir_raw)
        request_card_json = pair_dir / "request-card.json"
        assigned_card_json = pair_dir / "assigned-card.json"
        started_card_json = pair_dir / "started-card.json"
        checkpoint_card_json = pair_dir / "checkpoint-card.json"
        result_card_json = pair_dir / "result-card.json"
        ops_card_json = pair_dir / "ops-card.json"
        team_card_json = pair_dir / "team-card.json"
        request_json = run_command(
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
                "build-lab에 card composer smoke를 맡깁니다.",
                "--criteria",
                "ops-feed에는 내부 필드 없이 문제, 요청, 기준, 다음 액션이 보여야 합니다.",
                "--caution",
                "외부 Discord 전송 없이 로컬 formatter만 검증합니다.",
                "--next",
                "Team Lead가 실행 후 결과 요약을 보고합니다.",
                "--format",
                "json",
            ]
        )
        require_success(request_json, "discord ops-feed request card JSON")
        assigned_json = run_command(
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
                "--report",
                "RESULT_READY with evidence and verification.",
                "--next",
                "Team Lead returns RESULT_READY.",
                "--format",
                "json",
            ]
        )
        require_success(assigned_json, "discord team assigned detail card JSON")
        started_json = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card",
                "--surface",
                "team-detail",
                "--kind",
                "STARTED",
                "--work-unit-id",
                "WU-260605-901",
                "--team",
                "build-lab",
                "--status",
                "Team Lead has started the bounded smoke slice.",
                "--next",
                "Publish checkpoint before RESULT_READY if work runs long.",
                "--format",
                "json",
            ]
        )
        require_success(started_json, "discord team started card JSON")
        checkpoint_json = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card",
                "--surface",
                "team-detail",
                "--kind",
                "CHECKPOINT",
                "--work-unit-id",
                "WU-260605-901",
                "--team",
                "build-lab",
                "--current-slice",
                "formatter smoke execution",
                "--status",
                "Card sequence fixture is still in progress.",
                "--next-checkpoint",
                "before RESULT_READY",
                "--next",
                "Return RESULT_READY.",
                "--format",
                "json",
            ]
        )
        require_success(checkpoint_json, "discord team checkpoint card JSON")
        result_json = run_command(
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
                "--next",
                "Operations Lead review.",
                "--format",
                "json",
            ]
        )
        require_success(result_json, "discord team result ready card JSON")
        request_card_json.write_text(request_json.stdout, encoding="utf-8")
        assigned_card_json.write_text(assigned_json.stdout, encoding="utf-8")
        started_card_json.write_text(started_json.stdout, encoding="utf-8")
        checkpoint_card_json.write_text(checkpoint_json.stdout, encoding="utf-8")
        result_card_json.write_text(result_json.stdout, encoding="utf-8")
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

        sequence_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card-sequence",
                "--card-json",
                str(request_card_json),
                "--card-json",
                str(assigned_card_json),
                "--card-json",
                str(started_card_json),
                "--card-json",
                str(checkpoint_card_json),
                "--card-json",
                str(result_card_json),
                "--card-json",
                str(team_card_json),
                "--card-json",
                str(ops_card_json),
            ]
        )
        require_success(sequence_result, "discord card sequence validation")
        if "OK visibility card sequence: WU-260605-901 · build-lab · 7 cards" not in sequence_result.stdout:
            raise RuntimeError("card sequence validation did not include expected result")

        missing_request_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card-sequence",
                "--card-json",
                str(assigned_card_json),
                "--card-json",
                str(result_card_json),
                "--card-json",
                str(team_card_json),
                "--card-json",
                str(ops_card_json),
            ]
        )
        if missing_request_result.returncode == 0:
            raise RuntimeError("card sequence passed without an ops-feed request card")

        missing_started_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card-sequence",
                "--card-json",
                str(request_card_json),
                "--card-json",
                str(assigned_card_json),
                "--card-json",
                str(result_card_json),
                "--card-json",
                str(team_card_json),
                "--card-json",
                str(ops_card_json),
            ]
        )
        if missing_started_result.returncode == 0:
            raise RuntimeError("card sequence passed RESULT_READY without STARTED")

        late_checkpoint_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card-sequence",
                "--card-json",
                str(request_card_json),
                "--card-json",
                str(assigned_card_json),
                "--card-json",
                str(started_card_json),
                "--card-json",
                str(result_card_json),
                "--card-json",
                str(checkpoint_card_json),
                "--card-json",
                str(team_card_json),
                "--card-json",
                str(ops_card_json),
            ]
        )
        if late_checkpoint_result.returncode == 0:
            raise RuntimeError("card sequence accepted CHECKPOINT after RESULT_READY")

        proof_log = pair_dir / "live-proof.jsonl"
        base_proof = {
            "proof_version": 1,
            "work_unit_id": "WU-260605-901",
            "team": "build-lab",
            "target": "channel:local-smoke",
            "channel": "discord",
            "thread_id": "",
            "readback_ok": True,
            "dry_run": False,
            "error": "",
            "send_result": {},
            "readback_result": {},
        }
        proof_events = [
            ("ops-feed", "ASSIGNED", "card-001", "2026-06-05T21:00:00Z"),
            ("team-detail", "ASSIGNED_DETAIL", "card-002", "2026-06-05T21:00:05Z"),
            ("team-detail", "STARTED", "card-003", "2026-06-05T21:00:10Z"),
            ("team-detail", "CHECKPOINT", "card-004", "2026-06-05T21:10:10Z"),
            ("team-detail", "RESULT_READY", "card-005", "2026-06-05T21:20:15Z"),
            ("team-detail", "ACCEPTED", "card-006", "2026-06-05T21:20:45Z"),
            ("ops-feed", "COMPLETED", "card-007", "2026-06-05T21:21:00Z"),
        ]
        write_jsonl(
            proof_log,
            [
                {
                    **base_proof,
                    "proof_id": f"WU-260605-901:{surface}:{kind}:{card_id}",
                    "card_id": card_id,
                    "surface": surface,
                    "kind": kind,
                    "transition_at": timestamp,
                    "sent_at": timestamp,
                    "readback_at": timestamp,
                    "discord_timestamp": timestamp,
                    "discord_message_id": f"msg-{card_id}",
                }
                for surface, kind, card_id, timestamp in proof_events
            ],
        )
        proof_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "proof-validate",
                "--proof-log",
                str(proof_log),
                "--work-unit-id",
                "WU-260605-901",
                "--require-checkpoint",
                "--min-live-span-seconds",
                "60",
            ]
        )
        require_success(proof_result, "discord live proof validation")
        if "OK live visibility proof: WU-260605-901" not in proof_result.stdout:
            raise RuntimeError("live proof validation did not include expected result")

        replay_proof_log = pair_dir / "replay-proof.jsonl"
        write_jsonl(
            replay_proof_log,
            [
                {
                    **base_proof,
                    "proof_id": f"WU-260605-901:{surface}:{kind}:replay-{index}",
                    "card_id": f"replay-{index}",
                    "surface": surface,
                    "kind": kind,
                    "transition_at": f"2026-06-05T21:30:0{index}Z",
                    "sent_at": f"2026-06-05T21:30:0{index}Z",
                    "readback_at": f"2026-06-05T21:30:0{index}Z",
                    "discord_timestamp": f"2026-06-05T21:30:0{index}Z",
                    "discord_message_id": f"msg-replay-{index}",
                }
                for index, (surface, kind, _card_id, _timestamp) in enumerate(proof_events, start=1)
            ],
        )
        replay_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "proof-validate",
                "--proof-log",
                str(replay_proof_log),
                "--work-unit-id",
                "WU-260605-901",
                "--require-checkpoint",
                "--min-live-span-seconds",
                "60",
            ]
        )
        if replay_result.returncode == 0:
            raise RuntimeError("live proof validation accepted a burst/replay proof")

    long_result = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "RESULT_READY",
            "--work-unit-id",
            "WU-260605-906",
            "--team",
            "build-lab",
            "--result",
            "A" * 1300,
            "--evidence",
            "B" * 900,
            "--verification",
            "C" * 900,
            "--risks",
            "D" * 400,
            "--next",
            "Operations Lead review.",
        ]
    )
    require_success(long_result, "discord long card compaction")
    if len(long_result.stdout) > 1850:
        raise RuntimeError("long Discord card exceeded target one-message length")
    if "일부 생략됨" not in long_result.stdout:
        raise RuntimeError("long Discord card did not include compaction notice")
    if "📦 [RESULT_READY] WU-260605-906 · 🧪 build-lab" not in long_result.stdout:
        raise RuntimeError("long Discord card lost its header during compaction")

    with tempfile.TemporaryDirectory(prefix="openclaw-company-ops-discord-guard.") as guard_dir_raw:
        guard_path = Path(guard_dir_raw) / "message.txt"
        guard_path.write_text(
            "📦 [RESULT_READY] WU-260605-907 · 🧪 build-lab\n"
            + ("long team lead detail " * 220)
            + "\nNext: Operations Lead review.",
            encoding="utf-8",
        )
        guard_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "guard",
                "--message-file",
                str(guard_path),
                "--format",
                "json",
            ]
        )
        require_success(guard_result, "discord arbitrary message guard")
        guard_json = json.loads(guard_result.stdout)
        if not guard_json.get("compacted"):
            raise RuntimeError("discord arbitrary message guard did not compact long text")
        if guard_json.get("generation_target_chars") != 1600:
            raise RuntimeError("discord generation target is not 1600")
        if guard_json.get("output_content_units", 9999) > 1800:
            raise RuntimeError("discord arbitrary message guard exceeded output budget")


def run_hook_guard(
    payload: dict[str, Any],
    mode: str,
    *extra_args: str,
) -> tuple[int, dict[str, Any]]:
    result = subprocess.run(
        [sys.executable, str(HOOK_GUARD), "--mode", mode, *extra_args],
        input=json.dumps(payload),
        check=False,
        text=True,
        capture_output=True,
    )
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"hook guard returned invalid JSON: {result.stdout!r}") from exc
    return result.returncode, parsed


def require_hook_status(payload: dict[str, Any], mode: str, expected: str, *extra_args: str) -> dict[str, Any]:
    returncode, parsed = run_hook_guard(payload, mode, *extra_args)
    if parsed.get("status") != expected:
        raise RuntimeError(f"hook {mode} expected {expected}, got {parsed}")
    if expected == "block" and returncode == 0:
        raise RuntimeError(f"hook {mode} block returned success exit code")
    if expected != "block" and returncode != 0:
        raise RuntimeError(f"hook {mode} non-block returned failing exit code: {parsed}")
    return parsed


def run_hook_guard_smoke() -> None:
    require_hook_status(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"cmd": "sudo npm install -g openclaw"},
        },
        "pretool",
        "block",
    )
    require_hook_status(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"cmd": "git reset --hard HEAD~1"},
        },
        "pretool",
        "block",
    )
    require_hook_status(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"cmd": "rm -fr /"},
        },
        "pretool",
        "block",
    )
    require_hook_status(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"cmd": "rg -n hook docs/codex-hook-harness.md"},
        },
        "pretool",
        "pass",
    )
    require_hook_status(
        {
            "hook_event_name": "Stop",
            "transcript_tail": "Short repo inspection finished with no Work Unit.",
        },
        "stop",
        "pass",
    )

    with tempfile.TemporaryDirectory(prefix="openclaw-company-ops-hook-smoke.") as work_root_raw:
        work_root = Path(work_root_raw)
        missing_dir = work_root / "WU-260606-901"
        missing_dir.mkdir()
        (missing_dir / "assignment.md").write_text("# Assignment\n\nReal assignment text for smoke.\n", encoding="utf-8")
        (missing_dir / "claim.md").write_text("# Claim\n\nReal claim text for smoke.\n", encoding="utf-8")
        missing_payload = {
            "hook_event_name": "Stop",
            "final_response": "Task WU-260606-901 complete and accepted.",
        }
        parsed_missing = require_hook_status(
            missing_payload,
            "stop",
            "block",
            "--work-unit-root",
            str(work_root),
        )
        if not any(finding.get("code") == "missing-work-unit-artifact" for finding in parsed_missing["findings"]):
            raise RuntimeError("hook guard did not identify missing Work Unit artifact")

        suffix_dir = work_root / "WU-260606-LIVE-P0"
        suffix_dir.mkdir()
        (suffix_dir / "assignment.md").write_text("# Assignment\n\nReal suffix assignment text for smoke.\n", encoding="utf-8")
        (suffix_dir / "claim.md").write_text("# Claim\n\nReal suffix claim text for smoke.\n", encoding="utf-8")
        suffix_payload = {
            "hook_event_name": "Stop",
            "final_response": "Task WU-260606-LIVE-P0 complete and accepted.",
        }
        parsed_suffix = require_hook_status(
            suffix_payload,
            "stop",
            "block",
            "--work-unit-root",
            str(work_root),
        )
        if not any(finding.get("code") == "missing-work-unit-artifact" for finding in parsed_suffix["findings"]):
            raise RuntimeError("hook guard did not identify suffix Work Unit missing artifact")

        valid_dir = work_root / "WU-260606-902"
        valid_dir.mkdir()
        (valid_dir / "assignment.md").write_text(
            "# Assignment\n\n"
            "This assignment packet has enough detail for smoke validation and names a bounded "
            "repo-local hook guard fixture with no external mutation.\n",
            encoding="utf-8",
        )
        (valid_dir / "claim.md").write_text(
            "# Claim\n\n"
            "The Team Lead owns this bounded smoke slice and has not marked it done; the claim "
            "exists only to prove the hook allows blocked or hold outcomes.\n",
            encoding="utf-8",
        )
        (valid_dir / "evidence.md").write_text(
            "# Evidence\n\nStatus: blocked.\n\n## Verification Performed\n\nBlocked before external checks because source input is missing.\n",
            encoding="utf-8",
        )
        valid_payload = {
            "hook_event_name": "Stop",
            "final_response": "WU-260606-902 is blocked; evidence records the blocker.",
        }
        require_hook_status(valid_payload, "stop", "pass", "--work-unit-root", str(work_root))

    require_hook_status(
        {
            "hook_event_name": "PreCompact",
            "handoff": "WU-260606-902 claim working, evidence blocked, decision hold, next wait for source.",
        },
        "precompact",
        "pass",
    )
    require_hook_status(
        {
            "hook_event_name": "PreCompact",
            "handoff": "WU-260606-902 still active.",
        },
        "precompact",
        "warn",
    )


def run_project_sync_smoke(ledger: Path, artifact_root: Path, work_unit_id: str) -> None:
    field_map = artifact_root.parent / "project-field-map.json"
    write_json(
        field_map,
        {
            "project_id": "PVT_local_smoke",
            "fields": {
                "Work Unit id": "field_work_unit",
                "Repository": "field_repository",
                "Work Card": "field_work_card",
                "Team Lead": "field_team_lead",
                "Status": "field_status",
                "Phase": "field_phase",
                "Priority": "field_priority",
                "Blocker": "field_blocker",
                "Evidence present": "field_evidence_present",
                "Decision": "field_decision",
                "Last proof or last source update": "field_last_update",
                "Assignment Packet reference": "field_assignment",
                "Ops Claim Ledger reference": "field_claim",
                "Evidence & Result Record reference": "field_evidence",
                "Operations Lead Decision reference": "field_ops_decision",
            },
        },
    )
    result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--ledger",
            str(ledger),
            "--artifact-root",
            str(artifact_root),
            "--work-unit-id",
            work_unit_id,
            "--field-map",
            str(field_map),
            "--format",
            "json",
        ]
    )
    require_success(result, "project sync dry-run")
    parsed = json.loads(result.stdout)
    if parsed.get("project_mutation") is not False or parsed.get("llm_calls") != 0:
        raise RuntimeError("project sync dry-run reported mutation or LLM usage")
    work_units = parsed.get("work_units") or []
    if len(work_units) != 1:
        raise RuntimeError(f"project sync dry-run expected one Work Unit, got {len(work_units)}")
    planned = work_units[0]
    fields = planned.get("desired_fields") or {}
    if fields.get("Status") != "Result Ready":
        raise RuntimeError(f"project sync dry-run expected Result Ready status, got {fields.get('Status')}")
    if fields.get("Evidence present") != "yes":
        raise RuntimeError("project sync dry-run did not mark evidence present")
    if not planned.get("mutation_ready"):
        raise RuntimeError("project sync dry-run did not validate complete field map")
    if len(planned.get("planned_actions") or []) != 16:
        raise RuntimeError("project sync dry-run did not plan the expected item and field updates")
    if planned["planned_actions"][0].get("type") != "ensure_project_item":
        raise RuntimeError("project sync dry-run did not plan Project item membership first")

    suffix_root = artifact_root.parent / "suffix-artifacts"
    suffix_dir = suffix_root / "WU-260606-LIVE-P0"
    suffix_dir.mkdir(parents=True)
    (suffix_dir / "assignment.md").write_text(
        "# Assignment Packet\n\nStatus: Assigned\n\n"
        "## Identity\n\n"
        "- Work Unit id: `WU-260606-LIVE-P0`\n"
        "- Work Card: local-smoke://WU-260606-LIVE-P0\n"
        "- Assigned Team Lead OpenClaw Agent: `build-lab`\n",
        encoding="utf-8",
    )
    (suffix_dir / "claim.md").write_text(
        "# Ops Claim Ledger Entry\n\nStatus: Working\n\n"
        "- Claim ref: `CLAIM-WU-260606-LIVE-P0-001`\n"
        "- Work Unit id: `WU-260606-LIVE-P0`\n"
        "- Work Card: local-smoke://WU-260606-LIVE-P0\n"
        "- Expected state: `working`\n",
        encoding="utf-8",
    )
    suffix_result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--no-ledger",
            "--artifact-root",
            str(suffix_root),
            "--work-unit-id",
            "WU-260606-LIVE-P0",
            "--format",
            "json",
        ]
    )
    require_success(suffix_result, "project sync suffix dry-run")
    suffix_plan = json.loads(suffix_result.stdout)["work_units"][0]
    if suffix_plan["desired_fields"]["Status"] != "In Progress":
        raise RuntimeError("project sync suffix dry-run did not derive In Progress")
    if suffix_plan["desired_fields"]["Team Lead"] != "build-lab":
        raise RuntimeError("project sync suffix dry-run did not preserve Team Lead")


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
        run_hook_guard_smoke()
        run_discord_card_smoke()
        update_result_ready(ledger, build_claim, build_artifacts)
        run_project_sync_smoke(ledger, work_dir / "artifacts", "WU-260605-901")
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
        "repo-local hook guard fixtures, "
        "purpose-specific Discord card/checkpoint composition, "
        "live proof validation with burst replay rejection, "
        "Project sync dry-run planning without mutation, "
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
