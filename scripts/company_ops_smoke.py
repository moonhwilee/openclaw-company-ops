#!/usr/bin/env python3
"""Run bounded OpenClaw Company Ops smoke tests without external mutation."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACTS = SCRIPT_DIR / "work_unit_artifacts.py"
DISPATCH_SESSIONS_SEND = SCRIPT_DIR / "openclaw_dispatch_sessions_send.py"
CLOSEOUT_REVIEW_SESSIONS_SEND = SCRIPT_DIR / "openclaw_closeout_review_sessions_send.py"
CLAIMS = SCRIPT_DIR / "ops_claim_ledger.py"
PULSE = SCRIPT_DIR / "pulse_monitor.py"
DISCORD = SCRIPT_DIR / "discord_ops.py"
PROJECT_SYNC = SCRIPT_DIR / "project_sync.py"
HOOK_GUARD = SCRIPT_DIR.parent / ".codex" / "hooks" / "company_ops_gate.py"
REPO_ROOT = SCRIPT_DIR.parent


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True, env=env)


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


def canonical_json_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_dashboard_timestamp(value: str) -> str:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    local = parsed.astimezone()
    local_zone = local.tzname() or local.strftime("%z")
    return f"{local:%Y-%m-%d %H:%M} {local_zone}"


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


def mark_artifact_started(artifact_dir: Path, *, work_unit_id: str | None = None) -> None:
    work_unit = work_unit_id or artifact_dir.name
    progress_path = artifact_dir / "progress.jsonl"
    rows = []
    if progress_path.exists():
        rows = [line for line in progress_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.append(
        json.dumps(
            {
                "work_unit_id": work_unit,
                "transition_kind": "started",
                "mode": "smoke",
                "phase": "started",
                "phase_index": "",
                "phase_total": "",
                "round": "",
                "show_round": False,
                "current_slice": "started",
                "next_checkpoint": "Return RESULT_READY.",
                "source_ref": str(artifact_dir / "assignment.md"),
                "proof_ref": "",
                "transition_at": "2026-06-07T01:00:00Z",
                "recorded_by": "operations-lead",
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    progress_path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def remove_work_card_fields(artifact_dir: Path) -> None:
    for filename in ("assignment.md", "claim.md", "evidence.md", "decision.md"):
        path = artifact_dir / filename
        text = path.read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if not line.startswith("- Work Card:")]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def assert_status_lifecycle(artifact_root: Path, work_unit_id: str, expected_lifecycle: str) -> None:
    result = run_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "work_unit_status.py"),
            "status",
            "work-unit",
            "--work-unit-id",
            work_unit_id,
            "--artifact-root",
            str(artifact_root),
            "--no-ledger",
            "--format",
            "json",
        ]
    )
    require_success(result, f"status lifecycle {work_unit_id}")
    lifecycle = json.loads(result.stdout)["lifecycle"]["state"]
    if lifecycle != expected_lifecycle:
        raise RuntimeError(f"{work_unit_id} lifecycle expected {expected_lifecycle}, got {lifecycle}")


def assert_project_status(
    artifact_root: Path,
    field_map: Path,
    work_unit_id: str,
    expected_status: str,
) -> None:
    result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--no-ledger",
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
    require_success(result, f"project status {work_unit_id}")
    status = json.loads(result.stdout)["work_units"][0]["desired_fields"]["Status"]
    if status != expected_status:
        raise RuntimeError(f"{work_unit_id} Project Status expected {expected_status}, got {status}")


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


def mark_artifact_result_ready(artifact_dir: Path, *, recommendation: str | None = "accept") -> None:
    claim = artifact_dir / "claim.md"
    claim_text = claim.read_text(encoding="utf-8")
    claim_text = claim_text.replace("- Expected state: `assigned`", "- Expected state: `result_ready`")
    claim_text = claim_text.replace("- Expected state: `working`", "- Expected state: `result_ready`")
    claim_text = claim_text.replace("- Updated at: `2026-06-05`", "- Updated at: `2026-06-05T12:00:00Z`")
    claim.write_text(claim_text, encoding="utf-8")

    evidence = artifact_dir / "evidence.md"
    evidence_text = evidence.read_text(encoding="utf-8")
    evidence_text = evidence_text.replace("Status: Draft", "Status: Result Ready")
    if recommendation is not None:
        evidence_text = evidence_text.replace(
            "Recommended decision:\n\n- `accept`\n- `revise`\n- `blocked`",
            f"Recommended decision:\n\n- {recommendation}",
        )
    evidence.write_text(evidence_text, encoding="utf-8")


def proof_rows(work_unit_id: str, events: list[tuple[str, str, str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "work_unit_id": work_unit_id,
            "proof_id": f"{work_unit_id}:{surface}:{kind}:{card_id}",
            "card_id": card_id,
            "surface": surface,
            "kind": kind,
            "target": "local-smoke",
            "transition_at": timestamp,
            "sent_at": timestamp,
            "readback_at": timestamp,
            "discord_timestamp": timestamp,
            "discord_message_id": f"msg-{card_id}",
            "readback_ok": True,
            "dry_run": False,
            "error": "",
            "send_result": {},
            "readback_result": {},
        }
        for surface, kind, card_id, timestamp in events
    ]


def closeout_commit_request(
    artifact_dir: Path,
    work_unit_id: str,
    *,
    proof_id: str,
    proof_timestamp: str = "2026-06-07T01:35:00Z",
    decision: str = "accept",
    autonomy_class: str = "auto_eligible",
) -> dict[str, Any]:
    proof_row = proof_rows(
        work_unit_id,
        [("team-detail", "RESULT_READY", proof_id, proof_timestamp)],
    )[0]
    return {
        "work_unit_id": work_unit_id,
        "decision": decision,
        "reason": "Fresh closeout reviewer accepts the source-backed result.",
        "source_ref": str(artifact_dir / "evidence.md"),
        "result_ready_proof_id": f"{work_unit_id}:team-detail:RESULT_READY:{proof_id}",
        "artifact_hashes": {
            "assignment.md": file_sha256(artifact_dir / "assignment.md"),
            "claim.md": file_sha256(artifact_dir / "claim.md"),
            "evidence.md": file_sha256(artifact_dir / "evidence.md"),
            "progress.jsonl": file_sha256(artifact_dir / "progress.jsonl"),
            "visibility-proof.jsonl": file_sha256(artifact_dir / "visibility-proof.jsonl"),
            "result_ready_proof_rows": [canonical_json_hash(proof_row)],
        },
        "reviewer_session_ref": f"session:{work_unit_id}:closeout-review",
        "reviewer_job_ref": f"job:{work_unit_id}:closeout-review",
        "autonomy_class": autonomy_class,
        "review_depth": "source-artifacts-and-smoke-diff",
        "red_line_check": "clear",
    }


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

    revenue_revise_json = run_command(
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
            "--format",
            "json",
        ]
    )
    require_success(revenue_revise_json, "discord revenue revise card JSON")

    blocked_needs_revision = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "NEEDS_REVISION",
            "--work-unit-id",
            "WU-260605-905",
            "--team",
            "revenue",
            "--outcome",
            "검토 결과 수정이 필요합니다.",
            "--criteria-result",
            "핵심 증거는 있으나 가격 가정 보강이 필요합니다.",
            "--decision",
            "REVISE",
            "--verification",
            "Team detail REVISE review inspected.",
            "--team-final-review-kind",
            "ACCEPTED",
            "--next",
            "Revenue Lead revises the result.",
        ]
    )
    if blocked_needs_revision.returncode == 0:
        raise RuntimeError("ops-feed revise closeout passed with non-REVISE final review gate")

    needs_revision = run_command(
        [
            sys.executable,
            str(DISCORD),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "NEEDS_REVISION",
            "--work-unit-id",
            "WU-260605-905",
            "--team",
            "revenue",
            "--outcome",
            "검토 결과 수정이 필요합니다.",
            "--criteria-result",
            "핵심 증거는 있으나 가격 가정 보강이 필요합니다.",
            "--decision",
            "REVISE",
            "--verification",
            "Team detail REVISE review inspected.",
            "--evidence",
            "team REVISE card smoke",
            "--team-final-review-kind",
            "REVISE",
            "--next",
            "Revenue Lead revises the result.",
            "--format",
            "json",
        ]
    )
    require_success(needs_revision, "discord ops-feed needs-revision card")
    needs_revision_text = json.loads(needs_revision.stdout).get("text", "")
    if "🔁 [수정필요] WU-260605-905 · 💼 revenue" not in needs_revision_text:
        raise RuntimeError("ops-feed needs-revision card did not include expected header")

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
        revise_ops_card_json = pair_dir / "revise-ops-card.json"
        revise_team_card_json = pair_dir / "revise-team-card.json"
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
        revise_ops_card_json.write_text(needs_revision.stdout, encoding="utf-8")
        revise_team_card_json.write_text(revenue_revise_json.stdout, encoding="utf-8")
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

        revise_pair_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "card-pair",
                "--ops-card-json",
                str(revise_ops_card_json),
                "--team-card-json",
                str(revise_team_card_json),
            ]
        )
        require_success(revise_pair_result, "discord revise card pair validation")
        if "OK paired visibility cards: WU-260605-905 · revenue NEEDS_REVISION + REVISE" not in revise_pair_result.stdout:
            raise RuntimeError("revise card pair validation did not include expected result")

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

        publish_sequence_proof = pair_dir / "publish-sequence-proof.jsonl"
        publish_sequence_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "publish-sequence",
                "--card-target",
                f"{request_card_json}=channel:ops-feed-smoke",
                "--card-target",
                f"{assigned_card_json}=channel:team-build-lab-smoke",
                "--proof-log",
                str(publish_sequence_proof),
                "--dry-run",
                "--format",
                "json",
            ]
        )
        require_success(publish_sequence_result, "discord publish sequence dry-run")
        published_sequence = json.loads(publish_sequence_result.stdout).get("sequence") or []
        if len(published_sequence) != 2:
            raise RuntimeError("publish-sequence dry-run did not publish two cards")
        if [row.get("publish", {}).get("kind") for row in published_sequence] != [
            "ASSIGNED",
            "ASSIGNED_DETAIL",
        ]:
            raise RuntimeError("publish-sequence did not preserve card order")

        duplicate_guard_proof = pair_dir / "duplicate-guard-proof.jsonl"
        duplicate_publish_args = [
            sys.executable,
            str(DISCORD),
            "publish-card",
            "--card-json",
            str(request_card_json),
            "--target",
            "channel:ops-feed-smoke",
            "--expect-target",
            "channel:ops-feed-smoke",
            "--expect-surface",
            "ops-feed",
            "--proof-log",
            str(duplicate_guard_proof),
            "--dry-run",
        ]
        require_success(run_command(duplicate_publish_args), "discord publish duplicate guard seed")
        duplicate_publish_result = run_command(duplicate_publish_args)
        if duplicate_publish_result.returncode == 0:
            raise RuntimeError("publish-card accepted duplicate successful card proof without --force")
        forced_duplicate_result = run_command([*duplicate_publish_args, "--force"])
        require_success(forced_duplicate_result, "discord publish duplicate guard force")

        bad_target_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "publish-card",
                "--card-json",
                str(request_card_json),
                "--target",
                "channel:team-build-lab-smoke",
                "--expect-target",
                "channel:ops-feed-smoke",
                "--proof-log",
                str(pair_dir / "bad-target-proof.jsonl"),
                "--dry-run",
            ]
        )
        if bad_target_result.returncode == 0:
            raise RuntimeError("publish-card accepted a mismatched expected target")

        bad_sequence_target_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "publish-sequence",
                "--card-target",
                f"{request_card_json}=channel:team-build-lab-smoke",
                "--card-target",
                f"{assigned_card_json}=channel:team-build-lab-smoke",
                "--ops-feed-target",
                "channel:ops-feed-smoke",
                "--team-detail-target",
                "channel:team-build-lab-smoke",
                "--proof-log",
                str(pair_dir / "bad-sequence-target-proof.jsonl"),
                "--dry-run",
            ]
        )
        if bad_sequence_target_result.returncode == 0:
            raise RuntimeError("publish-sequence accepted an ops-feed card on the team-detail target")

        bad_publish_sequence_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "publish-sequence",
                "--card-target",
                f"{assigned_card_json}=channel:team-build-lab-smoke",
                "--card-target",
                f"{request_card_json}=channel:ops-feed-smoke",
                "--proof-log",
                str(pair_dir / "bad-publish-sequence-proof.jsonl"),
                "--dry-run",
            ]
        )
        if bad_publish_sequence_result.returncode == 0:
            raise RuntimeError("publish-sequence accepted team handoff before ops-feed request")

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

        revise_proof_log = pair_dir / "revise-proof.jsonl"
        revise_proof_events = [
            ("ops-feed", "ASSIGNED", "revise-card-001", "2026-06-05T22:00:00Z"),
            ("team-detail", "ASSIGNED_DETAIL", "revise-card-002", "2026-06-05T22:00:05Z"),
            ("team-detail", "STARTED", "revise-card-003", "2026-06-05T22:00:10Z"),
            ("team-detail", "CHECKPOINT", "revise-card-004", "2026-06-05T22:10:10Z"),
            ("team-detail", "RESULT_READY", "revise-card-005", "2026-06-05T22:20:15Z"),
            ("team-detail", "REVISE", "revise-card-006", "2026-06-05T22:20:45Z"),
            ("ops-feed", "NEEDS_REVISION", "revise-card-007", "2026-06-05T22:21:00Z"),
        ]
        write_jsonl(
            revise_proof_log,
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
                for surface, kind, card_id, timestamp in revise_proof_events
            ],
        )
        revise_proof_result = run_command(
            [
                sys.executable,
                str(DISCORD),
                "proof-validate",
                "--proof-log",
                str(revise_proof_log),
                "--work-unit-id",
                "WU-260605-901",
                "--require-checkpoint",
                "--min-live-span-seconds",
                "60",
            ]
        )
        require_success(revise_proof_result, "discord revise proof validation")

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
            "The Team Lead owns this bounded smoke slice and the claim "
            "exists only to prove the hook allows blocked outcomes.\n",
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
            "handoff": "WU-260606-902 claim working, evidence blocked, decision blocked, next wait for source.",
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


def run_async_work_unit_policy_smoke() -> None:
    checks = {
        "docs/operations-manual.md": (
            "Main Session Nonblocking Rule",
            "Work Unit Handoff Change Rule",
            "The initial handoff is a source-backed starting contract",
            "Do not silently rewrite the original handoff",
            "`ops-direct`",
            "`team-qna`",
            "`detached-wu`",
            "Direct Team Lead Q&A",
            "Result Ready Inbox Rule",
            "This rule does not reorder OpenClaw inbound messages.",
            "Process pending Team Lead results one at a time in a deterministic order",
            "closeout lock",
            "Only the Operations Lead may record `ACCEPTED`, `REVISE`, or",
        ),
        "docs/protocols/README.md": (
            "Detached Work Unit Requirement",
            "Small domain-specific questions may be routed to the matching Team Lead",
            "handoff a detached Work Unit",
        ),
        "docs/post-setup-plan.md": (
            "Company Ops must not depend on installer-written user memory.",
            "installs into the user's OpenClaw runtime/workspace",
            "Operations Lead consumes the bundled skill",
            "Company Ops plugin",
            "foreground CLI tools",
            "Impact on existing docs and repository layout",
            "small Company Ops skill with routing triggers",
            "optional guided team setup path",
            "users who start with a single",
            "must not auto-create or bind agents",
            "setup-needed result",
            "Phase 5.5: Result Ready Inbox / Closeout Lock Gate",
            "work-unit inbox --result-ready",
            "closeout-lock helper",
            "must not automatically accept",
            "It must not add LLM calls or network reads to list local ready Work Units.",
            "needs-ops-decision",
            "Phase 5.5a: Handoff Amendment / Replan Dry-Run Gate",
            "work-unit amend --spec amendment.json --dry-run",
            "Do not overwrite the original Assignment Packet",
            "Normal Work Units pay no runtime cost",
            "Phase 5.5b: Handoff Draft / Spec Generator Gate",
            "implemented bounded phase",
            "work-unit draft-handoff --spec draft-input.json --dry-run",
            "needs-ops-decision",
            "six controlled Company Ops requests",
            "must not replace Operations Lead judgment",
        ),
        "docs/setup-guide.md": (
            "Distribution Surface",
            "Company Ops plugin or package",
            "installed into the OpenClaw runtime/workspace",
            "Optional guided onboarding for single-agent users",
            "explicit confirmation before creating or binding Team Lead agents",
            "must not silently edit user `MEMORY.md`",
        ),
        "docs/templates/assignment-packet.md": (
            "Request route: <detached-wu>",
            "Execution route: <cli-direct|cli-delivered|discord-bound>",
            "Main session behavior: detached after handoff",
            "Assumptions And Open Questions",
            "Change Log",
            "Returning this report does not complete the Work Unit.",
        ),
        "README.md": (
            "Sizeable `goal` and `verify` work is detached Work Unit work.",
            "installed into the OpenClaw runtime/workspace used by the",
            "optional guided team setup",
        ),
    }
    for relative_path, required_phrases in checks.items():
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for phrase in required_phrases:
            if phrase not in text:
                raise RuntimeError(f"{relative_path} missing async Work Unit policy phrase: {phrase}")


def run_project_sync_smoke(args: argparse.Namespace, ledger: Path, artifact_root: Path, work_unit_id: str) -> None:
    field_map = artifact_root.parent / "project-field-map.json"
    write_json(
        field_map,
        {
            "owner": "@me",
            "project_number": 1,
            "project_id": "PVT_local_smoke",
            "fields": {
                "Work Unit id": "field_work_unit",
                "Repository": "field_repository",
                "Work Card": "field_work_card",
                "Team Lead": "field_team_lead",
                "Status": "field_status",
                "Progress": "field_progress",
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
    progress_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "progress",
            "--work-unit-id",
            work_unit_id,
            "--output-root",
            str(artifact_root),
            "--phase-index",
            "2",
            "--phase-total",
            "7",
            "--phase",
            "dashboard progress smoke",
            "--round",
            "1",
            "--current-slice",
            "project-sync derivation",
            "--next-checkpoint",
            "local-smoke://next-checkpoint",
            "--source-ref",
            f"{artifact_root / work_unit_id / 'evidence.md'}",
            "--transition-at",
            "2026-06-06T12:00:00Z",
        ]
    )
    require_success(progress_result, "project progress artifact append")
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
    if fields.get("Progress") != "2/7 · dashboard progress smoke":
        raise RuntimeError(
            f"project sync dry-run did not derive Progress from progress artifact: {fields.get('Progress')}"
        )
    expected_last_update = expected_dashboard_timestamp("2026-06-06T12:00:00Z")
    if fields.get("Last proof or last source update") != expected_last_update:
        raise RuntimeError("project sync dry-run did not use progress timestamp as last source update")
    if not planned.get("mutation_ready"):
        raise RuntimeError("project sync dry-run did not validate complete field map")
    if len(planned.get("planned_actions") or []) != 16:
        raise RuntimeError("project sync dry-run did not plan the expected item and field updates")
    if planned["planned_actions"][0].get("type") != "ensure_project_item":
        raise RuntimeError("project sync dry-run did not plan Project item membership first")

    proof_only_root = artifact_root.parent / "proof-only-artifacts"
    shutil.copytree(artifact_root / work_unit_id, proof_only_root / work_unit_id)
    proof_only_progress = proof_only_root / work_unit_id / "progress.jsonl"
    proof_only_progress.unlink(missing_ok=True)
    proof_only_assignment = proof_only_root / work_unit_id / "assignment.md"
    proof_only_assignment.write_text(
        proof_only_assignment.read_text(encoding="utf-8").replace(
            f"- Assigned Team Lead OpenClaw Agent: `build-lab`\n",
            "- Assigned Team Lead OpenClaw Agent: `build-lab`\n- Mode: `verify`\n",
        ),
        encoding="utf-8",
    )
    proof_timestamp = "2026-06-06T13:04:00Z"
    write_jsonl(
        proof_only_root / work_unit_id / "visibility-proof.jsonl",
        [
            {
                "work_unit_id": work_unit_id,
                "surface": "team-detail",
                "kind": "STARTED",
                "dry_run": False,
                "readback_ok": True,
                "discord_timestamp": "2026-06-06T13:00:00Z",
            },
            {
                "work_unit_id": work_unit_id,
                "surface": "team-detail",
                "kind": "RESULT_READY",
                "dry_run": False,
                "readback_ok": True,
                "discord_timestamp": "2026-06-06T13:02:00Z",
            },
            {
                "work_unit_id": work_unit_id,
                "surface": "ops-feed",
                "kind": "COMPLETED",
                "dry_run": False,
                "readback_ok": True,
                "discord_timestamp": proof_timestamp,
            },
        ],
    )
    proof_only_result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--ledger",
            str(ledger),
            "--artifact-root",
            str(proof_only_root),
            "--work-unit-id",
            work_unit_id,
            "--field-map",
            str(field_map),
            "--format",
            "json",
        ]
    )
    require_success(proof_only_result, "project sync proof-derived lifecycle display dry-run")
    proof_only_fields = json.loads(proof_only_result.stdout)["work_units"][0]["desired_fields"]
    if proof_only_fields.get("Progress") != "verify · accepted":
        raise RuntimeError(
            "project sync dry-run did not derive proof-backed lifecycle display: "
            f"{proof_only_fields.get('Progress')}"
        )
    if proof_only_fields.get("Last proof or last source update") != expected_dashboard_timestamp(proof_timestamp):
        raise RuntimeError("project sync dry-run did not use latest proof timestamp")

    invalid_proof_root = artifact_root.parent / "invalid-proof-artifacts"
    shutil.copytree(proof_only_root / work_unit_id, invalid_proof_root / work_unit_id)
    write_jsonl(
        invalid_proof_root / work_unit_id / "visibility-proof.jsonl",
        [
            {
                "work_unit_id": work_unit_id,
                "surface": "team-detail",
                "kind": "STARTED",
                "dry_run": True,
                "readback_ok": True,
                "discord_timestamp": "2026-06-06T13:10:00Z",
            },
            {
                "work_unit_id": "WU-OTHER",
                "surface": "ops-feed",
                "kind": "COMPLETED",
                "dry_run": False,
                "readback_ok": True,
                "discord_timestamp": "2026-06-06T13:11:00Z",
            },
            {
                "work_unit_id": work_unit_id,
                "surface": "ops-feed",
                "kind": "COMPLETED",
                "dry_run": False,
                "readback_ok": False,
                "discord_timestamp": "2026-06-06T13:12:00Z",
            },
        ],
    )
    with (invalid_proof_root / work_unit_id / "visibility-proof.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{not valid json}\n")
    invalid_proof_result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--ledger",
            str(ledger),
            "--artifact-root",
            str(invalid_proof_root),
            "--work-unit-id",
            work_unit_id,
            "--field-map",
            str(field_map),
            "--format",
            "json",
        ]
    )
    require_success(invalid_proof_result, "project sync invalid proof display dry-run")
    invalid_proof_fields = json.loads(invalid_proof_result.stdout)["work_units"][0]["desired_fields"]
    if invalid_proof_fields.get("Progress") != "result preflight repair needed":
        raise RuntimeError("project sync dry-run did not surface invalid proof repair state")
    if invalid_proof_fields.get("Last proof or last source update") not in {"", "pending"}:
        raise RuntimeError("project sync dry-run used narrative or invalid proof timestamp as last update")

    round_only_root = artifact_root.parent / "round-only-artifacts"
    shutil.copytree(artifact_root / work_unit_id, round_only_root / work_unit_id)
    round_only_progress = round_only_root / work_unit_id / "progress.jsonl"
    round_only_progress.write_text(
        json.dumps(
            {
                "work_unit_id": work_unit_id,
                "transition_kind": "started",
                "source_ref": str(round_only_root / work_unit_id / "assignment.md"),
                "transition_at": "2026-06-06T12:00:00Z",
                "recorded_by": "operations-lead",
            },
            ensure_ascii=True,
        )
        + "\n"
        +
        json.dumps(
            {
                "work_unit_id": work_unit_id,
                "transition_kind": "checkpoint",
                "round": "2",
                "transition_at": "2026-06-06T12:30:00Z",
                "recorded_by": "operations-lead",
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    round_only_result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--ledger",
            str(ledger),
            "--artifact-root",
            str(round_only_root),
            "--work-unit-id",
            work_unit_id,
            "--field-map",
            str(field_map),
            "--format",
            "json",
        ]
    )
    require_success(round_only_result, "project sync round-only progress dry-run")
    round_only_fields = json.loads(round_only_result.stdout)["work_units"][0]["desired_fields"]
    if round_only_fields.get("Progress") != "":
        raise RuntimeError(
            f"project sync dry-run displayed implicit round-only progress: {round_only_fields.get('Progress')}"
        )

    show_round_root = artifact_root.parent / "show-round-artifacts"
    shutil.copytree(artifact_root / work_unit_id, show_round_root / work_unit_id)
    show_round_progress = show_round_root / work_unit_id / "progress.jsonl"
    show_round_progress.write_text(
        json.dumps(
            {
                "work_unit_id": work_unit_id,
                "transition_kind": "started",
                "source_ref": str(show_round_root / work_unit_id / "assignment.md"),
                "transition_at": "2026-06-06T12:00:00Z",
                "recorded_by": "operations-lead",
            },
            ensure_ascii=True,
        )
        + "\n"
        +
        json.dumps(
            {
                "work_unit_id": work_unit_id,
                "transition_kind": "checkpoint",
                "phase_index": "3",
                "phase_total": "3",
                "phase": "verify operating path",
                "round": "1",
                "show_round": True,
                "transition_at": "2026-06-06T12:45:00Z",
                "recorded_by": "operations-lead",
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    show_round_result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--ledger",
            str(ledger),
            "--artifact-root",
            str(show_round_root),
            "--work-unit-id",
            work_unit_id,
            "--field-map",
            str(field_map),
            "--format",
            "json",
        ]
    )
    require_success(show_round_result, "project sync explicit round progress dry-run")
    show_round_fields = json.loads(show_round_result.stdout)["work_units"][0]["desired_fields"]
    if show_round_fields.get("Progress") != "R1 · 3/3 · verify operating path":
        raise RuntimeError(
            f"project sync dry-run did not format explicit round first: {show_round_fields.get('Progress')}"
        )

    goal_round_root = artifact_root.parent / "goal-round-artifacts"
    shutil.copytree(artifact_root / work_unit_id, goal_round_root / work_unit_id)
    goal_round_progress = goal_round_root / work_unit_id / "progress.jsonl"
    goal_round_progress.write_text(
        json.dumps(
            {
                "work_unit_id": work_unit_id,
                "transition_kind": "started",
                "source_ref": str(goal_round_root / work_unit_id / "assignment.md"),
                "transition_at": "2026-06-06T12:00:00Z",
                "recorded_by": "operations-lead",
            },
            ensure_ascii=True,
        )
        + "\n"
        +
        json.dumps(
            {
                "work_unit_id": work_unit_id,
                "transition_kind": "checkpoint",
                "mode": "goal",
                "phase_index": "1",
                "phase_total": "4",
                "phase": "converge implementation",
                "round": "2",
                "transition_at": "2026-06-06T12:50:00Z",
                "recorded_by": "operations-lead",
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    goal_round_result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--ledger",
            str(ledger),
            "--artifact-root",
            str(goal_round_root),
            "--work-unit-id",
            work_unit_id,
            "--field-map",
            str(field_map),
            "--format",
            "json",
        ]
    )
    require_success(goal_round_result, "project sync automatic goal round progress dry-run")
    goal_round_fields = json.loads(goal_round_result.stdout)["work_units"][0]["desired_fields"]
    if goal_round_fields.get("Progress") != "R2 · 1/4 · converge implementation":
        raise RuntimeError(
            f"project sync dry-run did not auto-display goal round: {goal_round_fields.get('Progress')}"
        )

    checkpoint_root = artifact_root.parent / "checkpoint-artifacts"
    shutil.copytree(artifact_root / work_unit_id, checkpoint_root / work_unit_id)
    checkpoint_progress = checkpoint_root / work_unit_id / "progress.jsonl"
    before_checkpoint = checkpoint_progress.read_text(encoding="utf-8") if checkpoint_progress.exists() else ""
    checkpoint_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "checkpoint",
            "--work-unit-id",
            work_unit_id,
            "--output-root",
            str(checkpoint_root),
            "--team",
            "build-lab",
            "--status",
            "Goal loop checkpoint is ready.",
            "--current-slice",
            "checkpoint command smoke",
            "--next",
            "Continue the next goal slice.",
            "--mode",
            "goal",
            "--round",
            "2",
            "--phase-index",
            "1",
            "--phase-total",
            "4",
            "--phase",
            "converge implementation",
            "--source-ref",
            "local-smoke://checkpoint",
            "--transition-at",
            "2026-06-06T12:55:00Z",
            "--format",
            "json",
            "--dry-run",
        ]
    )
    require_success(checkpoint_result, "work-unit checkpoint dry-run")
    checkpoint_payload = json.loads(checkpoint_result.stdout)
    checkpoint_row = checkpoint_payload.get("progress_row") or {}
    if checkpoint_row.get("show_round") is not True:
        raise RuntimeError("checkpoint dry-run did not auto-enable goal round display")
    if checkpoint_payload.get("card", {}).get("kind") != "CHECKPOINT":
        raise RuntimeError("checkpoint dry-run did not create a CHECKPOINT card")
    after_checkpoint = checkpoint_progress.read_text(encoding="utf-8") if checkpoint_progress.exists() else ""
    if after_checkpoint != before_checkpoint:
        raise RuntimeError("checkpoint dry-run mutated progress.jsonl")

    handoff_root = artifact_root.parent / "handoff-artifacts"
    handoff_spec = artifact_root.parent / "handoff-spec.json"
    handoff_spec_data = {
        "work_unit_id": "WU-260606-906",
        "title": "Smoke initial handoff bundle",
        "work_card": "local-smoke://WU-260606-906",
        "operations_lead": "gbee",
        "team": "build-lab",
        "mode": "verify",
        "owner_request": "Verify the thin handoff bundle.",
        "goal": "Create a deterministic initial handoff bundle without external mutation.",
        "scope": ["Render source artifacts", "Prepare ASSIGNED Discord cards"],
        "done_criteria": ["Artifacts and initial visibility cards are planned from one spec"],
        "verification_criteria": ["Dry-run has no persistent artifact writes", "ops-feed ASSIGNED precedes team-detail ASSIGNED_DETAIL"],
        "targets": {
            "ops_feed": "channel:ops-feed-smoke",
            "team_detail": "channel:team-build-lab-smoke",
        },
        "next": "Team Lead starts from the generated Assignment Packet.",
    }
    write_json(handoff_spec, handoff_spec_data)
    handoff_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "handoff",
            "--spec",
            str(handoff_spec),
            "--output-root",
            str(handoff_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(handoff_result, "work-unit handoff dry-run")
    handoff_payload = json.loads(handoff_result.stdout)
    if handoff_payload.get("ops_card", {}).get("kind") != "ASSIGNED":
        raise RuntimeError("handoff dry-run did not create ops-feed ASSIGNED card")
    if handoff_payload.get("team_card", {}).get("kind") != "ASSIGNED_DETAIL":
        raise RuntimeError("handoff dry-run did not create team-detail ASSIGNED_DETAIL card")
    planned_cards = handoff_payload.get("plan", {}).get("cards") or []
    if [card.get("kind") for card in planned_cards] != ["ASSIGNED", "ASSIGNED_DETAIL"]:
        raise RuntimeError("handoff dry-run did not preserve initial publish order")
    if (handoff_root / "WU-260606-906").exists():
        raise RuntimeError("handoff dry-run wrote persistent artifacts")

    bad_handoff_spec = artifact_root.parent / "bad-handoff-spec.json"
    bad_handoff_data = dict(handoff_spec_data)
    bad_handoff_data.pop("verification_criteria")
    write_json(bad_handoff_spec, bad_handoff_data)
    bad_handoff_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "handoff",
            "--spec",
            str(bad_handoff_spec),
            "--output-root",
            str(handoff_root),
            "--dry-run",
        ]
    )
    if bad_handoff_result.returncode == 0:
        raise RuntimeError("handoff dry-run accepted missing verification criteria")

    draft_handoff_root = artifact_root.parent / "draft-handoff-artifacts"
    draft_handoff_spec = artifact_root.parent / "draft-handoff-spec.json"
    draft_handoff_data = {
        **handoff_spec_data,
        "work_unit_id": "WU-260607-206",
        "title": "Smoke draft handoff bundle",
        "requested_by": "operations-lead",
        "source_refs": ["local-smoke://phase-5.5b/draft-handoff"],
        "no_go": ["Do not publish from the draft command."],
        "target_paths": ["docs/examples/manual-dry-run/WU-260607-206/assignment.md"],
    }
    write_json(draft_handoff_spec, draft_handoff_data)
    draft_handoff_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "draft-handoff",
            "--spec",
            str(draft_handoff_spec),
            "--output-root",
            str(draft_handoff_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(draft_handoff_result, "work-unit draft-handoff dry-run")
    draft_payload = json.loads(draft_handoff_result.stdout)
    if draft_payload.get("status") != "ready":
        raise RuntimeError(f"draft-handoff expected ready, got {draft_payload.get('status')}")
    if draft_payload.get("completed_handoff_spec_valid") is not True:
        raise RuntimeError("draft-handoff did not validate completed handoff spec")
    if draft_payload.get("checks", {}).get("llm_calls") != 0:
        raise RuntimeError("draft-handoff reported LLM calls")
    if draft_payload.get("checks", {}).get("free_form_request_routing") is not False:
        raise RuntimeError("draft-handoff reported free-form routing")
    for mutation_key in (
        "would_create_work_card",
        "would_write_source_artifacts",
        "would_publish_discord",
        "would_mutate_project",
        "would_send_owner_report",
    ):
        if draft_payload.get(mutation_key) is not False:
            raise RuntimeError(f"draft-handoff reported mutation: {mutation_key}")
    if (draft_handoff_root / "WU-260607-206").exists():
        raise RuntimeError("draft-handoff dry-run wrote persistent artifacts")
    if "Work Card Draft" not in draft_payload.get("work_card_draft", ""):
        raise RuntimeError("draft-handoff did not produce a Work Card draft")
    if "Assignment Packet" not in draft_payload.get("assignment_packet_draft", ""):
        raise RuntimeError("draft-handoff did not produce an Assignment Packet draft")

    completed_draft_spec = artifact_root.parent / "completed-draft-handoff-spec.json"
    write_json(completed_draft_spec, draft_payload["handoff_spec_draft"])
    completed_handoff_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "handoff",
            "--spec",
            str(completed_draft_spec),
            "--output-root",
            str(draft_handoff_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(completed_handoff_result, "completed draft spec handoff dry-run")

    missing_draft_spec = artifact_root.parent / "missing-draft-handoff-spec.json"
    missing_draft_data = dict(draft_handoff_data)
    missing_draft_data.pop("team")
    missing_draft_data["done_criteria"] = "needs-ops-decision"
    write_json(missing_draft_spec, missing_draft_data)
    missing_draft_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "draft-handoff",
            "--spec",
            str(missing_draft_spec),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(missing_draft_result, "work-unit draft-handoff missing fields")
    missing_draft_payload = json.loads(missing_draft_result.stdout)
    if missing_draft_payload.get("status") != "needs-ops-decision":
        raise RuntimeError("draft-handoff did not surface missing fields as needs-ops-decision")
    if "team" not in missing_draft_payload.get("missing_fields", []):
        raise RuntimeError("draft-handoff did not list missing Team Lead")
    if "done_criteria" not in missing_draft_payload.get("missing_fields", []):
        raise RuntimeError("draft-handoff did not list ambiguous done criteria")
    if missing_draft_payload.get("completed_handoff_spec_valid") is not False:
        raise RuntimeError("draft-handoff treated incomplete spec as handoff-valid")

    source_less_draft_spec = artifact_root.parent / "source-less-draft-handoff-spec.json"
    source_less_draft_data = dict(draft_handoff_data)
    source_less_draft_data.pop("source_refs")
    write_json(source_less_draft_spec, source_less_draft_data)
    source_less_draft = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "draft-handoff",
            "--spec",
            str(source_less_draft_spec),
            "--dry-run",
        ]
    )
    if source_less_draft.returncode == 0:
        raise RuntimeError("draft-handoff accepted source-less input")

    draft_without_dry_run = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "draft-handoff",
            "--spec",
            str(draft_handoff_spec),
        ]
    )
    if draft_without_dry_run.returncode == 0:
        raise RuntimeError("draft-handoff accepted a non-dry-run path")
    if "supports --dry-run only" not in draft_without_dry_run.stderr:
        raise RuntimeError(f"draft-handoff non-dry-run guard failed for wrong reason: {draft_without_dry_run.stderr}")

    amend_root = artifact_root.parent / "amend-artifacts"
    amend_dir = create_artifacts(args, amend_root, "WU-260607-106", "build-lab")
    assignment_before = (amend_dir / "assignment.md").read_text(encoding="utf-8")
    amend_spec = artifact_root.parent / "amend-spec.json"
    amend_spec_data = {
        "work_unit_id": "WU-260607-106",
        "reason": "New verification target changes the done criteria.",
        "changed_fields": ["done_criteria", "verification_criteria"],
        "proposed_updates": {
            "done_criteria": ["Add source-backed amendment dry-run evidence."],
            "verification_criteria": ["Prove original Assignment Packet is unchanged."],
        },
        "source_refs": ["local-smoke://phase-5.5a/amendment"],
        "requested_by": "operations-lead",
    }
    write_json(amend_spec, amend_spec_data)
    amend_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "amend",
            "--spec",
            str(amend_spec),
            "--artifact-root",
            str(amend_root / "artifacts"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(amend_result, "work-unit amend dry-run")
    amend_payload = json.loads(amend_result.stdout)
    if amend_payload.get("status") != "ready":
        raise RuntimeError(f"amend dry-run expected ready, got {amend_payload.get('status')}")
    if amend_payload.get("would_update_assignment_packet") is not False:
        raise RuntimeError("amend dry-run reported assignment mutation")
    if amend_payload.get("would_write_amendment_artifact") is not False:
        raise RuntimeError("amend dry-run reported amendment artifact write")
    if (amend_dir / "amendment.md").exists():
        raise RuntimeError("amend dry-run wrote amendment artifact")
    if (amend_dir / "assignment.md").read_text(encoding="utf-8") != assignment_before:
        raise RuntimeError("amend dry-run changed the original Assignment Packet")

    amend_without_dry_run = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "amend",
            "--spec",
            str(amend_spec),
            "--artifact-root",
            str(amend_root / "artifacts"),
        ]
    )
    if amend_without_dry_run.returncode == 0:
        raise RuntimeError("amend accepted a non-dry-run path")
    if "supports --dry-run only" not in amend_without_dry_run.stderr:
        raise RuntimeError(f"amend non-dry-run guard failed for wrong reason: {amend_without_dry_run.stderr}")

    ambiguous_amend_spec = artifact_root.parent / "ambiguous-amend-spec.json"
    ambiguous_amend_data = dict(amend_spec_data)
    ambiguous_amend_data["proposed_updates"] = {
        "done_criteria": "needs-ops-decision",
    }
    write_json(ambiguous_amend_spec, ambiguous_amend_data)
    ambiguous_amend = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "amend",
            "--spec",
            str(ambiguous_amend_spec),
            "--artifact-root",
            str(amend_root / "artifacts"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(ambiguous_amend, "work-unit amend dry-run ambiguous")
    ambiguous_payload = json.loads(ambiguous_amend.stdout)
    if ambiguous_payload.get("status") != "needs-ops-decision":
        raise RuntimeError("amend dry-run did not surface ambiguous updates as needs-ops-decision")
    if not ambiguous_payload.get("needs_ops_decision"):
        raise RuntimeError("amend dry-run did not explain why Operations Lead decision is needed")

    source_less_amend_spec = artifact_root.parent / "source-less-amend-spec.json"
    source_less_data = dict(amend_spec_data)
    source_less_data.pop("source_refs")
    write_json(source_less_amend_spec, source_less_data)
    source_less_amend = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "amend",
            "--spec",
            str(source_less_amend_spec),
            "--artifact-root",
            str(amend_root / "artifacts"),
            "--dry-run",
        ]
    )
    if source_less_amend.returncode == 0:
        raise RuntimeError("amend dry-run accepted an amendment without source refs")

    apply_guard = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "apply",
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
    if apply_guard.returncode == 0:
        raise RuntimeError("project sync apply unexpectedly accepted a non-GitHub smoke Work Card")
    if "apply requires GitHub issue or pull request Work Card URLs" not in apply_guard.stderr:
        raise RuntimeError(f"project sync apply guard failed for wrong reason: {apply_guard.stderr}")

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


def run_result_ready_inbox_smoke(args: argparse.Namespace, work_dir: Path) -> None:
    inbox_work_dir = work_dir / "phase55"
    ready_late = create_artifacts(args, inbox_work_dir, "WU-260607-101", "build-lab")
    ready_early = create_artifacts(args, inbox_work_dir, "WU-260607-102", "market")
    stale_dir = create_artifacts(args, inbox_work_dir, "WU-260607-103", "finance")
    conflict_dir = create_artifacts(args, inbox_work_dir, "WU-260607-104", "ops")
    invalid_dir = create_artifacts(args, inbox_work_dir, "WU-260607-106", "build-lab")
    invalid_progress_dir = create_artifacts(args, inbox_work_dir, "WU-260607-107", "build-lab")
    start_dir = create_artifacts(args, inbox_work_dir, "WU-260607-110", "ops")
    missing_started_dir = create_artifacts(args, inbox_work_dir, "WU-260607-111", "market")
    live_start_dir = create_artifacts(args, inbox_work_dir, "WU-260607-112", "ops")
    adapter_dir = create_artifacts(args, inbox_work_dir, "WU-260607-113", "ops")
    command_adapter_dir = create_artifacts(args, inbox_work_dir, "WU-260607-114", "ops")
    custom_session_dir = create_artifacts(args, inbox_work_dir, "WU-260607-116", "ops")
    artifact_root = inbox_work_dir / "artifacts"

    for artifact_dir in (ready_late, ready_early, stale_dir, conflict_dir, invalid_dir, invalid_progress_dir):
        mark_artifact_started(artifact_dir)
    mark_artifact_result_ready(ready_late, recommendation="accept")
    mark_artifact_result_ready(ready_early, recommendation="revise")
    mark_artifact_result_ready(stale_dir, recommendation="accept")
    stale_decision = stale_dir / "decision.md"
    stale_decision.write_text(
        stale_decision.read_text(encoding="utf-8").replace("Status: Pending", "Status: Accepted"),
        encoding="utf-8",
    )
    mark_artifact_result_ready(conflict_dir, recommendation="accept")
    invalid_claim = invalid_dir / "claim.md"
    invalid_claim.write_text(
        invalid_claim.read_text(encoding="utf-8").replace(
            "- Expected state: `assigned`",
            "- Expected state: `result_ready`",
        ),
        encoding="utf-8",
    )
    mark_artifact_result_ready(missing_started_dir, recommendation="accept")
    mark_artifact_started(adapter_dir)
    mark_artifact_started(command_adapter_dir)
    mark_artifact_started(custom_session_dir)

    start_progress_before = (start_dir / "progress.jsonl").read_text(encoding="utf-8") if (start_dir / "progress.jsonl").exists() else ""
    start_dry_run = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "start",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(start_dry_run, "work-unit start dry-run")
    if (start_dir / "progress.jsonl").exists() and (start_dir / "progress.jsonl").read_text(encoding="utf-8") != start_progress_before:
        raise RuntimeError("start dry-run mutated progress.jsonl")
    start_payload = json.loads(start_dry_run.stdout)
    if start_payload.get("status") != "ready-to-start" or start_payload.get("would_append_progress") is not True:
        raise RuntimeError("start dry-run did not report the planned started source event")
    start_publish = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "start",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    require_success(start_publish, "work-unit start publish local source")
    if '"transition_kind": "started"' not in (start_dir / "progress.jsonl").read_text(encoding="utf-8"):
        raise RuntimeError("start publish did not append a started progress row")
    if "- Expected state: `working`" not in (start_dir / "claim.md").read_text(encoding="utf-8"):
        raise RuntimeError("start publish did not update claim expected state to working")
    duplicate_start = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "start",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    if duplicate_start.returncode == 0:
        raise RuntimeError("start publish accepted duplicate STARTED without --force")
    dispatch_progress_before = (start_dir / "progress.jsonl").read_text(encoding="utf-8")
    dispatch_dry_run = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(dispatch_dry_run, "work-unit dispatch dry-run")
    dispatch_payload = json.loads(dispatch_dry_run.stdout)
    if dispatch_payload.get("status") != "ready-to-dispatch":
        raise RuntimeError("dispatch dry-run did not report ready-to-dispatch")
    if dispatch_payload.get("dispatch_packet", {}).get("session_key") != "company-ops-ops-wu-260607-110":
        raise RuntimeError("dispatch dry-run did not derive a stable session key")
    if dispatch_payload.get("session_key_strategy") != "work-unit-specific":
        raise RuntimeError("dispatch dry-run did not use the fresh Work Unit-specific session strategy")
    if dispatch_payload.get("session_key_provided") is not False:
        raise RuntimeError("dispatch dry-run did not report an auto-derived session key")
    if dispatch_payload.get("would_write_dispatch") is not False or dispatch_payload.get("would_spawn_runtime") is not False:
        raise RuntimeError("dispatch dry-run reported mutation")
    if (start_dir / "dispatch.json").exists():
        raise RuntimeError("dispatch dry-run wrote dispatch.json")
    if (start_dir / "progress.jsonl").read_text(encoding="utf-8") != dispatch_progress_before:
        raise RuntimeError("dispatch dry-run mutated progress.jsonl")
    capacity_root = work_dir / "capacity-artifacts"
    capacity_dirs: list[Path] = []
    for index in range(1, 10):
        wu_id = f"WU-260607-20{index}"
        capacity_dir = capacity_root / wu_id
        require_success(
            run_command(
                [
                    sys.executable,
                    str(ARTIFACTS),
                    "work-unit",
                    "create",
                    "--work-unit-id",
                    wu_id,
                    "--title",
                    f"Capacity smoke {index}",
                    "--work-card",
                    f"local-smoke://{wu_id}",
                    "--operations-lead",
                    "gbee",
                    "--team-lead",
                    "ops",
                    "--output-root",
                    str(capacity_root),
                    "--created-at",
                    args.created_at,
                ]
            ),
            f"capacity artifact create {wu_id}",
        )
        mark_artifact_started(capacity_dir, work_unit_id=wu_id)
        capacity_dirs.append(capacity_dir)
    low_config = work_dir / "low-openclaw-config.json"
    write_json(
        low_config,
        {
            "agents": {
                "defaults": {
                    "maxConcurrent": 4,
                    "subagents": {"maxConcurrent": 8},
                }
            }
        },
    )
    capacity_preflight = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "capacity-check",
            "--artifact-root",
            str(capacity_root),
            "--config-json",
            str(low_config),
            "--format",
            "json",
        ]
    )
    require_success(capacity_preflight, "work-unit capacity-check")
    capacity_preflight_payload = json.loads(capacity_preflight.stdout)
    if capacity_preflight_payload.get("status") != "WARN":
        raise RuntimeError("capacity-check did not warn for low OpenClaw host config")
    if capacity_preflight_payload.get("recommended", {}).get("agents.defaults.maxConcurrent") != 10:
        raise RuntimeError("capacity-check did not derive current package recommendation 10")
    if capacity_preflight_payload.get("recommended", {}).get("agents.defaults.subagents.maxConcurrent") != 20:
        raise RuntimeError("capacity-check did not derive current package recommendation 20")
    if capacity_preflight_payload.get("derived", {}).get("company_ops_active_wu_cap") != 2:
        raise RuntimeError("capacity-check did not derive cap from the supplied low config")
    top_level_preflight = run_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "openclaw_company_ops.py"),
            "preflight",
            "--artifact-root",
            str(capacity_root),
            "--config-json",
            str(low_config),
            "--format",
            "json",
        ]
    )
    require_success(top_level_preflight, "top-level preflight")
    capacity_full_progress_before = (capacity_dirs[-1] / "progress.jsonl").read_text(encoding="utf-8")
    capacity_full_dispatch = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-209",
            "--artifact-root",
            str(capacity_root),
            "--capacity-max-concurrent",
            "10",
            "--source-ref",
            str(capacity_dirs[-1] / "assignment.md"),
            "--publish",
            "--session-ref",
            "session:capacity-over-cap",
            "--format",
            "json",
        ]
    )
    if capacity_full_dispatch.returncode == 0:
        raise RuntimeError("dispatch accepted a Work Unit over the active WU cap")
    capacity_full_payload = json.loads(capacity_full_dispatch.stdout)
    if capacity_full_payload.get("status") != "capacity-full":
        raise RuntimeError("capacity-full dispatch did not report capacity-full")
    if (capacity_dirs[-1] / "dispatch.json").exists():
        raise RuntimeError("capacity-full dispatch wrote dispatch.json")
    if (capacity_dirs[-1] / "progress.jsonl").read_text(encoding="utf-8") != capacity_full_progress_before:
        raise RuntimeError("capacity-full dispatch mutated progress.jsonl")
    dispatch_missing_started = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-111",
            "--artifact-root",
            str(artifact_root),
            "--source-ref",
            str(missing_started_dir / "assignment.md"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if dispatch_missing_started.returncode == 0:
        raise RuntimeError("dispatch accepted missing STARTED source")
    if "prior STARTED source" not in dispatch_missing_started.stderr:
        raise RuntimeError("dispatch missing STARTED failure did not explain the source precondition")
    dispatch_setup_needed = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--runtime",
            "openclaw-agent",
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    if dispatch_setup_needed.returncode == 0:
        raise RuntimeError("automatic dispatch passed without a runtime reference")
    dispatch_setup_payload = json.loads(dispatch_setup_needed.stdout)
    if dispatch_setup_payload.get("status") != "setup-needed":
        raise RuntimeError("automatic dispatch did not fail as setup-needed")
    if (start_dir / "dispatch.json").exists():
        raise RuntimeError("setup-needed dispatch wrote dispatch.json")
    if (start_dir / "progress.jsonl").read_text(encoding="utf-8") != dispatch_progress_before:
        raise RuntimeError("setup-needed dispatch mutated progress.jsonl")
    dispatch_runtime_manual_ref = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--runtime",
            "openclaw-agent",
            "--session-ref",
            "session:manual-ref-is-not-proof",
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    if dispatch_runtime_manual_ref.returncode == 0:
        raise RuntimeError("openclaw-agent dispatch accepted a manual ref without adapter proof")
    if (start_dir / "dispatch.json").exists():
        raise RuntimeError("manual-ref runtime dispatch wrote dispatch.json without adapter proof")
    if (start_dir / "progress.jsonl").read_text(encoding="utf-8") != dispatch_progress_before:
        raise RuntimeError("manual-ref runtime dispatch mutated progress.jsonl without adapter proof")
    custom_session_progress_before = (custom_session_dir / "progress.jsonl").read_text(encoding="utf-8")
    dispatch_custom_session_rejected = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-116",
            "--artifact-root",
            str(artifact_root),
            "--runtime",
            "openclaw-agent",
            "--adapter",
            "fake",
            "--session-key",
            "company-ops-shared-ops-session",
            "--source-ref",
            str(custom_session_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    if dispatch_custom_session_rejected.returncode == 0:
        raise RuntimeError("openclaw-agent dispatch accepted a custom/shared session key by default")
    if "fresh Work Unit-specific session key" not in dispatch_custom_session_rejected.stderr:
        raise RuntimeError("custom/shared session rejection did not explain the fresh session requirement")
    if (custom_session_dir / "dispatch.json").exists():
        raise RuntimeError("custom/shared session rejection wrote dispatch.json")
    if (custom_session_dir / "progress.jsonl").read_text(encoding="utf-8") != custom_session_progress_before:
        raise RuntimeError("custom/shared session rejection mutated progress.jsonl")
    dispatch_custom_session_allowed = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-116",
            "--artifact-root",
            str(artifact_root),
            "--runtime",
            "openclaw-agent",
            "--adapter",
            "fake",
            "--session-key",
            "company-ops-shared-ops-session",
            "--allow-custom-session-key",
            "--source-ref",
            str(custom_session_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    require_success(dispatch_custom_session_allowed, "work-unit dispatch custom session explicit override")
    custom_session_record = json.loads((custom_session_dir / "dispatch.json").read_text(encoding="utf-8"))
    if custom_session_record.get("session_key_strategy") != "operator-specified":
        raise RuntimeError("explicit custom session dispatch did not record operator-specified strategy")
    dispatch_fake_adapter = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-113",
            "--artifact-root",
            str(artifact_root),
            "--runtime",
            "openclaw-agent",
            "--adapter",
            "fake",
            "--source-ref",
            str(adapter_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    require_success(dispatch_fake_adapter, "work-unit dispatch fake adapter publish")
    dispatch_fake_payload = json.loads(dispatch_fake_adapter.stdout)
    if dispatch_fake_payload.get("accepted_proof", {}).get("adapter") != "fake":
        raise RuntimeError("fake adapter dispatch did not persist accepted proof")
    fake_dispatch_record = json.loads((adapter_dir / "dispatch.json").read_text(encoding="utf-8"))
    if fake_dispatch_record.get("dispatch_ref") != "job:WU-260607-113:dispatch-execute":
        raise RuntimeError("fake adapter dispatch did not derive a recoverable dispatch ref")
    if fake_dispatch_record.get("accepted_proof", {}).get("readback", {}).get("work_unit_id") != "WU-260607-113":
        raise RuntimeError("fake adapter dispatch did not persist the Team Lead readback")
    adapter_script = work_dir / "accept_dispatch_adapter.py"
    adapter_script.write_text(
        "\n".join(
            [
                "import json, sys",
                "request = json.load(sys.stdin)",
                "packet = request['packet']",
                "print(json.dumps({",
                "    'status': 'accepted',",
                "    'adapter': 'smoke-command',",
                "    'session_ref': 'session:' + request['session_key'],",
                "    'job_ref': 'job:' + request['work_unit_id'] + ':execute',",
                "    'message_ref': 'message:' + request['work_unit_id'] + ':accepted',",
                "    'accepted_at': request['transition_at'],",
                "    'readback': {",
                "        'work_unit_id': request['work_unit_id'],",
                "        'assignment_packet': packet['assignment_packet'],",
                "        'result_ready_contract': packet['result_ready_contract']['command'],",
                "        'authority_boundary': 'team_lead_result_ready_only',",
                "    },",
                "}, sort_keys=True))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    hanging_adapter_script = work_dir / "hanging_dispatch_adapter.py"
    hanging_adapter_script.write_text(
        "\n".join(
            [
                "import time",
                "time.sleep(2)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    command_adapter_progress_before = (command_adapter_dir / "progress.jsonl").read_text(
        encoding="utf-8"
    )
    dispatch_busy_timeout = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-114",
            "--artifact-root",
            str(artifact_root),
            "--runtime",
            "openclaw-agent",
            "--adapter",
            "command",
            "--adapter-command",
            f"{sys.executable} {hanging_adapter_script}",
            "--adapter-timeout-seconds",
            "1",
            "--source-ref",
            str(command_adapter_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    if dispatch_busy_timeout.returncode == 0:
        raise RuntimeError("busy Team Lead adapter timeout was accepted as dispatch success")
    dispatch_busy_timeout_payload = json.loads(dispatch_busy_timeout.stdout)
    if dispatch_busy_timeout_payload.get("status") != "setup-needed":
        raise RuntimeError("busy Team Lead adapter timeout did not fail as setup-needed")
    if "runtime adapter timed out" not in str(dispatch_busy_timeout_payload.get("reason") or ""):
        raise RuntimeError("busy Team Lead adapter timeout did not explain the timeout")
    if (command_adapter_dir / "dispatch.json").exists():
        raise RuntimeError("busy Team Lead adapter timeout wrote dispatch.json")
    if (command_adapter_dir / "progress.jsonl").read_text(encoding="utf-8") != command_adapter_progress_before:
        raise RuntimeError("busy Team Lead adapter timeout mutated progress.jsonl")
    dispatch_command_adapter = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-114",
            "--artifact-root",
            str(artifact_root),
            "--runtime",
            "openclaw-agent",
            "--adapter",
            "command",
            "--adapter-command",
            f"{sys.executable} {adapter_script}",
            "--source-ref",
            str(command_adapter_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    require_success(dispatch_command_adapter, "work-unit dispatch command adapter publish")
    command_dispatch_record = json.loads((command_adapter_dir / "dispatch.json").read_text(encoding="utf-8"))
    if command_dispatch_record.get("accepted_proof", {}).get("adapter") != "smoke-command":
        raise RuntimeError("command adapter dispatch did not persist adapter accepted proof")
    fake_openclaw = work_dir / "openclaw"
    fake_openclaw.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, os, sys",
                "mode = os.environ.get('COMPANY_OPS_FAKE_OPENCLAW_MODE', 'ok')",
                "if len(sys.argv) > 1 and sys.argv[1] == 'agent':",
                "    readback = {",
                "        'status': 'accepted',",
                "        'work_unit_id': 'WU-260607-115',",
                "        'assignment_packet': 'assignment.md',",
                "        'result_ready_contract': 'work-unit result-ready --publish',",
                "        'authority_boundary': 'team_lead_result_ready_only',",
                "    }",
                "    if mode == 'fallback_acceptance':",
                "        print(json.dumps({'runId': 'gateway-fallback-run', 'meta': {'transport': 'embedded', 'fallbackFrom': 'gateway', 'fallbackReason': 'gateway_timeout', 'sessionKey': 'gateway-fallback-WU-260607-115'}, 'result': {'payloads': [{'text': json.dumps(readback)}], 'finalAssistantVisibleText': json.dumps(readback)}}))",
                "        sys.exit(0)",
                "    if mode == 'missing_accept_ref':",
                "        print(json.dumps({'status': 'ok', 'result': {'payloads': [{'text': json.dumps(readback)}], 'finalAssistantVisibleText': json.dumps(readback)}}))",
                "        sys.exit(0)",
                "    print(json.dumps({'runId': 'run-accept', 'status': 'ok', 'result': {'payloads': [{'text': json.dumps(readback)}], 'finalAssistantVisibleText': json.dumps(readback)}}))",
                "    sys.exit(0)",
                "method = sys.argv[sys.argv.index('call') + 1]",
                "params = json.loads(sys.argv[sys.argv.index('--params') + 1])",
                "if method == 'sessions.create':",
                "    print(json.dumps({'result': {'key': params['key']}}))",
                "elif method == 'sessions.send':",
                "    if mode == 'missing_send_ref':",
                "        print(json.dumps({'result': {'status': 'queued'}}))",
                "        sys.exit(0)",
                "    print(json.dumps({'result': {'runId': 'run-execute', 'messageId': 'msg-execute'}}))",
                "else:",
                "    print(json.dumps({'error': 'unexpected method'}))",
                "    sys.exit(1)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    fake_openclaw.chmod(0o755)
    wrapper_request = {
        "adapter_protocol": "company_ops_dispatch_adapter_v1",
        "work_unit_id": "WU-260607-115",
        "team": "ops",
        "agent": "ops",
        "runtime": "openclaw-agent",
        "session_key": "company-ops-ops-wu-260607-115",
        "artifact_dir": str(work_dir),
        "transition_at": args.created_at,
        "packet": {
            "assignment_packet": "assignment.md",
            "result_ready_contract": {"command": "work-unit result-ready --publish"},
        },
        "required_acceptance": {
            "work_unit_id": "WU-260607-115",
            "assignment_packet": "assignment.md",
            "result_ready_contract": "work-unit result-ready --publish",
            "authority_boundary": "team_lead_result_ready_only",
        },
    }

    def run_wrapper(mode: str = "ok") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(DISPATCH_SESSIONS_SEND), "--accept-timeout-ms", "1000"],
            check=False,
            text=True,
            input=json.dumps(wrapper_request),
            capture_output=True,
            env={
                **os.environ,
                "PATH": f"{work_dir}:{os.environ.get('PATH', '')}",
                "COMPANY_OPS_FAKE_OPENCLAW_MODE": mode,
            },
        )

    wrapper_result = run_wrapper()
    require_success(wrapper_result, "openclaw dispatch sessions.send wrapper")
    wrapper_payload = json.loads(wrapper_result.stdout)
    if wrapper_payload.get("adapter") != "openclaw-agent-sessions-send":
        raise RuntimeError("sessions.send wrapper did not report the standard adapter")
    if wrapper_payload.get("job_ref") != "run-execute":
        raise RuntimeError("sessions.send wrapper did not preserve execution run reference")
    wrapper_gateway = wrapper_payload.get("gateway", {})
    if wrapper_gateway.get("acceptance_transport") != "openclaw-agent-gateway":
        raise RuntimeError("sessions.send wrapper did not require Gateway-backed acceptance")
    if wrapper_gateway.get("idempotency_key") != "WU-260607-115:dispatch-execute":
        raise RuntimeError("sessions.send wrapper did not persist the dispatch idempotency key")
    packet_hash = str(wrapper_gateway.get("dispatch_packet_hash") or "")
    if len(packet_hash) != 64:
        raise RuntimeError("sessions.send wrapper did not persist a dispatch packet hash")
    if wrapper_payload.get("readback", {}).get("authority_boundary") != "team_lead_result_ready_only":
        raise RuntimeError("sessions.send wrapper did not preserve authority boundary readback")

    fallback_result = run_wrapper("fallback_acceptance")
    if fallback_result.returncode == 0:
        raise RuntimeError("sessions.send wrapper accepted embedded fallback proof")
    fallback_payload = json.loads(fallback_result.stdout)
    if "embedded gateway fallback" not in str(fallback_payload.get("reason") or ""):
        raise RuntimeError("sessions.send wrapper did not explain embedded fallback rejection")

    missing_accept_ref_result = run_wrapper("missing_accept_ref")
    if missing_accept_ref_result.returncode == 0:
        raise RuntimeError("sessions.send wrapper accepted proof without a Gateway acceptance ref")
    missing_accept_ref_payload = json.loads(missing_accept_ref_result.stdout)
    if "real Gateway reference" not in str(missing_accept_ref_payload.get("reason") or ""):
        raise RuntimeError("sessions.send wrapper did not reject missing Gateway acceptance ref")

    missing_send_ref_result = run_wrapper("missing_send_ref")
    if missing_send_ref_result.returncode == 0:
        raise RuntimeError("sessions.send wrapper accepted execution enqueue without a Gateway run ref")
    missing_send_ref_payload = json.loads(missing_send_ref_result.stdout)
    if "real Gateway run reference" not in str(missing_send_ref_payload.get("reason") or ""):
        raise RuntimeError("sessions.send wrapper did not reject missing Gateway execution ref")

    fake_openclaw.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json, os, sys",
                "mode = os.environ.get('COMPANY_OPS_FAKE_OPENCLAW_MODE', 'ok')",
                "if len(sys.argv) > 1 and sys.argv[1] == 'agent':",
                "    readback = {",
                "        'status': 'accepted',",
                "        'work_unit_id': 'WU-260607-121',",
                "        'closeout_review_payload_hash': 'smoke-closeout-review-hash',",
                "        'guarded_closeout_contract': 'work-unit closeout --commit-request <json> --publish',",
                "        'authority_boundary': 'closeout_reviewer_guarded_commit_only',",
                "    }",
                "    if mode == 'fallback_acceptance':",
                "        print(json.dumps({'runId': 'gateway-fallback-run', 'meta': {'transport': 'embedded', 'fallbackFrom': 'gateway', 'fallbackReason': 'gateway_timeout', 'sessionKey': 'gateway-fallback-WU-260607-121'}, 'result': {'payloads': [{'text': json.dumps(readback)}], 'finalAssistantVisibleText': json.dumps(readback)}}))",
                "        sys.exit(0)",
                "    if mode == 'missing_accept_ref':",
                "        print(json.dumps({'status': 'ok', 'result': {'payloads': [{'text': json.dumps(readback)}], 'finalAssistantVisibleText': json.dumps(readback)}}))",
                "        sys.exit(0)",
                "    print(json.dumps({'runId': 'run-closeout-accept', 'status': 'ok', 'result': {'payloads': [{'text': json.dumps(readback)}], 'finalAssistantVisibleText': json.dumps(readback)}}))",
                "    sys.exit(0)",
                "method = sys.argv[sys.argv.index('call') + 1]",
                "params = json.loads(sys.argv[sys.argv.index('--params') + 1])",
                "if method == 'sessions.create':",
                "    print(json.dumps({'result': {'key': params['key']}}))",
                "elif method == 'sessions.send':",
                "    if mode == 'missing_send_ref':",
                "        print(json.dumps({'result': {'status': 'queued'}}))",
                "        sys.exit(0)",
                "    print(json.dumps({'result': {'runId': 'run-closeout-execute', 'messageId': 'msg-closeout-execute'}}))",
                "else:",
                "    print(json.dumps({'error': 'unexpected method'}))",
                "    sys.exit(1)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    closeout_wrapper_request = {
        "adapter_protocol": "company_ops_closeout_review_adapter_v1",
        "work_unit_id": "WU-260607-121",
        "team": "ops",
        "agent": "closeout-reviewer",
        "runtime": "openclaw-agent",
        "session_key": "company-ops-closeout-reviewer-wu-260607-121",
        "artifact_dir": str(work_dir),
        "transition_at": args.created_at,
        "packet": {
            "protocol": "company_ops_closeout_review_wake_v1",
            "work_unit_id": "WU-260607-121",
            "guarded_closeout_contract": {"command": "work-unit closeout --commit-request <json> --publish"},
            "authority_boundary": "closeout_reviewer_guarded_commit_only",
        },
        "required_acceptance": {
            "work_unit_id": "WU-260607-121",
            "closeout_review_payload_hash": "smoke-closeout-review-hash",
            "guarded_closeout_contract": "work-unit closeout --commit-request <json> --publish",
            "authority_boundary": "closeout_reviewer_guarded_commit_only",
        },
    }

    def run_closeout_wrapper(mode: str = "ok") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLOSEOUT_REVIEW_SESSIONS_SEND), "--accept-timeout-ms", "1000"],
            check=False,
            text=True,
            input=json.dumps(closeout_wrapper_request),
            capture_output=True,
            env={
                **os.environ,
                "PATH": f"{work_dir}:{os.environ.get('PATH', '')}",
                "COMPANY_OPS_FAKE_OPENCLAW_MODE": mode,
            },
        )

    closeout_wrapper_result = run_closeout_wrapper()
    require_success(closeout_wrapper_result, "openclaw closeout review sessions.send wrapper")
    closeout_wrapper_payload = json.loads(closeout_wrapper_result.stdout)
    if closeout_wrapper_payload.get("adapter") != "openclaw-closeout-review-sessions-send":
        raise RuntimeError("closeout review wrapper did not report the standard adapter")
    if closeout_wrapper_payload.get("job_ref") != "run-closeout-execute":
        raise RuntimeError("closeout review wrapper did not preserve execution run reference")
    closeout_gateway = closeout_wrapper_payload.get("gateway", {})
    idempotency_key = closeout_gateway.get("idempotency_key", "")
    if not idempotency_key.startswith("WU-260607-121:closeout-review:"):
        raise RuntimeError("closeout review wrapper did not persist the review idempotency key")
    if closeout_wrapper_payload.get("readback", {}).get("authority_boundary") != "closeout_reviewer_guarded_commit_only":
        raise RuntimeError("closeout review wrapper did not preserve authority boundary readback")

    closeout_fallback_result = run_closeout_wrapper("fallback_acceptance")
    if closeout_fallback_result.returncode == 0:
        raise RuntimeError("closeout review wrapper accepted embedded fallback proof")
    closeout_fallback_payload = json.loads(closeout_fallback_result.stdout)
    if "embedded gateway fallback" not in str(closeout_fallback_payload.get("reason") or ""):
        raise RuntimeError("closeout review wrapper did not explain embedded fallback rejection")

    closeout_missing_accept_ref = run_closeout_wrapper("missing_accept_ref")
    if closeout_missing_accept_ref.returncode == 0:
        raise RuntimeError("closeout review wrapper accepted proof without a Gateway acceptance ref")
    closeout_missing_accept_payload = json.loads(closeout_missing_accept_ref.stdout)
    if "real Gateway reference" not in str(closeout_missing_accept_payload.get("reason") or ""):
        raise RuntimeError("closeout review wrapper did not reject missing Gateway acceptance ref")

    closeout_missing_send_ref = run_closeout_wrapper("missing_send_ref")
    if closeout_missing_send_ref.returncode == 0:
        raise RuntimeError("closeout review wrapper accepted execution enqueue without a Gateway run ref")
    closeout_missing_send_payload = json.loads(closeout_missing_send_ref.stdout)
    if "real Gateway run reference" not in str(closeout_missing_send_payload.get("reason") or ""):
        raise RuntimeError("closeout review wrapper did not reject missing Gateway execution ref")
    dispatch_publish = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--session-ref",
            "session:ops:WU-260607-110",
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    require_success(dispatch_publish, "work-unit dispatch publish")
    dispatch_publish_payload = json.loads(dispatch_publish.stdout)
    if dispatch_publish_payload.get("status") != "dispatched":
        raise RuntimeError("dispatch publish did not record dispatched status")
    if "session:ops:WU-260607-110" not in (start_dir / "dispatch.json").read_text(encoding="utf-8"):
        raise RuntimeError("dispatch publish did not persist the session ref")
    if '"transition_kind": "dispatched"' not in (start_dir / "progress.jsonl").read_text(encoding="utf-8"):
        raise RuntimeError("dispatch publish did not append a dispatched progress row")
    if "- Owner session ref: `ops`" not in (start_dir / "claim.md").read_text(encoding="utf-8"):
        raise RuntimeError("dispatch publish overwrote the Team Lead claim identity")
    duplicate_dispatch = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "dispatch",
            "--work-unit-id",
            "WU-260607-110",
            "--artifact-root",
            str(artifact_root),
            "--session-ref",
            "session:ops:WU-260607-110",
            "--source-ref",
            str(start_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    if duplicate_dispatch.returncode == 0:
        raise RuntimeError("dispatch publish accepted duplicate dispatch without --force")
    live_assignment = live_start_dir / "assignment.md"
    live_assignment.write_text(
        live_assignment.read_text(encoding="utf-8").replace(
            "- Assigned Team Lead OpenClaw Agent: `ops`",
            "- Assigned Team Lead OpenClaw Agent: `ops`\n- Execution route: `discord-bound`",
        ),
        encoding="utf-8",
    )
    live_start_without_target = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "start",
            "--work-unit-id",
            "WU-260607-112",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(live_start_dir / "assignment.md"),
            "--publish",
            "--format",
            "json",
        ]
    )
    if live_start_without_target.returncode == 0:
        raise RuntimeError("discord-bound start publish accepted missing --target")
    mark_artifact_started(live_start_dir)
    mark_artifact_result_ready(live_start_dir, recommendation="accept")
    live_result_ready_without_started_proof = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "result-ready",
            "--work-unit-id",
            "WU-260607-112",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--result",
            "This must not publish because live STARTED proof is missing.",
            "--evidence",
            str(live_start_dir / "evidence.md"),
            "--verification",
            "Negative smoke for live STARTED proof precondition.",
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if live_result_ready_without_started_proof.returncode == 0:
        raise RuntimeError("discord-bound result-ready dry-run accepted missing STARTED proof")
    if "visibility-proof.STARTED" not in live_result_ready_without_started_proof.stderr:
        raise RuntimeError("missing live STARTED proof failure did not point at visibility-proof.STARTED")

    write_jsonl(
        ready_late / "visibility-proof.jsonl",
        proof_rows(
            "WU-260607-101",
            [("team-detail", "RESULT_READY", "late-001", "2026-06-07T01:20:00Z")],
        ),
    )
    write_jsonl(
        ready_early / "visibility-proof.jsonl",
        proof_rows(
            "WU-260607-102",
            [("team-detail", "RESULT_READY", "early-001", "2026-06-07T01:10:00Z")],
        ),
    )
    write_jsonl(
        stale_dir / "visibility-proof.jsonl",
        proof_rows(
            "WU-260607-103",
            [("team-detail", "RESULT_READY", "stale-001", "2026-06-07T01:05:00Z")],
        ),
    )
    write_jsonl(
        conflict_dir / "visibility-proof.jsonl",
        proof_rows(
            "WU-260607-104",
            [
                ("team-detail", "RESULT_READY", "conflict-001", "2026-06-07T01:01:00Z"),
                ("team-detail", "ACCEPTED", "conflict-002", "2026-06-07T01:02:00Z"),
                ("team-detail", "REVISE", "conflict-003", "2026-06-07T01:03:00Z"),
            ],
        ),
    )
    write_jsonl(
        invalid_dir / "progress.jsonl",
        [
            {
                "work_unit_id": "WU-260607-106",
                "transition_kind": "result_ready",
                "source_ref": "docs/examples/manual-dry-run/WU-260607-106/missing-result.md",
                "transition_at": "2026-06-07T01:25:00Z",
            }
        ],
    )
    inbox_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "inbox",
            "--result-ready",
            "--artifact-root",
            str(artifact_root),
            "--format",
            "json",
        ]
    )
    require_success(inbox_result, "result-ready inbox json")
    inbox_payload = json.loads(inbox_result.stdout)
    inbox_ids = [item["work_unit_id"] for item in inbox_payload["items"]]
    if inbox_ids != ["WU-260607-102", "WU-260607-101"]:
        raise RuntimeError(f"result-ready inbox did not sort actionable items deterministically: {inbox_ids}")

    review_wake_dir = create_artifacts(args, inbox_work_dir, "WU-260607-117", "ops")
    review_command_dir = create_artifacts(args, inbox_work_dir, "WU-260607-118", "ops")
    review_setup_dir = create_artifacts(args, inbox_work_dir, "WU-260607-119", "ops")
    for artifact_dir in (review_wake_dir, review_command_dir, review_setup_dir):
        mark_artifact_started(artifact_dir)
        mark_artifact_result_ready(artifact_dir, recommendation="accept")
    for work_unit_id, artifact_dir, proof_id in (
        ("WU-260607-117", review_wake_dir, "review-wake-001"),
        ("WU-260607-118", review_command_dir, "review-wake-002"),
        ("WU-260607-119", review_setup_dir, "review-wake-003"),
    ):
        write_jsonl(
            artifact_dir / "visibility-proof.jsonl",
            proof_rows(
                work_unit_id,
                [("team-detail", "RESULT_READY", proof_id, "2026-06-07T01:35:00Z")],
            ),
        )
    review_wake_progress_before = (review_wake_dir / "progress.jsonl").read_text(encoding="utf-8")
    review_wake_dry_run = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "review-wake",
            "--work-unit-id",
            "WU-260607-117",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(review_wake_dir / "evidence.md"),
            "--closeout-reviewer-runtime",
            "openclaw-agent",
            "--closeout-reviewer-adapter",
            "fake",
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(review_wake_dry_run, "closeout review wake dry-run")
    review_wake_dry_payload = json.loads(review_wake_dry_run.stdout)
    if review_wake_dry_payload.get("status") != "ready-to-review-wake":
        raise RuntimeError("closeout review wake dry-run did not report ready-to-review-wake")
    review_payload = review_wake_dry_payload.get("review_payload", {})
    if review_payload.get("authority_boundary") != "closeout_reviewer_guarded_commit_only":
        raise RuntimeError("closeout review payload did not carry the guarded authority boundary")
    if review_payload.get("reviewer", {}).get("session_key") != "company-ops-closeout-reviewer-wu-260607-117":
        raise RuntimeError("closeout review payload did not derive a stable reviewer session key")
    if "evidence.md" not in review_payload.get("artifact_hashes", {}):
        raise RuntimeError("closeout review payload did not bind evidence to an artifact hash")
    if (review_wake_dir / "closeout-review-wake.json").exists():
        raise RuntimeError("closeout review wake dry-run wrote a wake record")
    if (review_wake_dir / "progress.jsonl").read_text(encoding="utf-8") != review_wake_progress_before:
        raise RuntimeError("closeout review wake dry-run mutated progress.jsonl")

    review_wake_publish = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "review-wake",
            "--work-unit-id",
            "WU-260607-117",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(review_wake_dir / "evidence.md"),
            "--closeout-reviewer-runtime",
            "openclaw-agent",
            "--closeout-reviewer-adapter",
            "fake",
            "--publish",
            "--format",
            "json",
        ]
    )
    require_success(review_wake_publish, "closeout review wake fake adapter publish")
    review_wake_publish_payload = json.loads(review_wake_publish.stdout)
    if review_wake_publish_payload.get("status") != "review-wake-enqueued":
        raise RuntimeError("closeout review wake publish did not report review-wake-enqueued")
    review_wake_record = json.loads((review_wake_dir / "closeout-review-wake.json").read_text(encoding="utf-8"))
    if review_wake_record.get("accepted_proof", {}).get("readback", {}).get("authority_boundary") != "closeout_reviewer_guarded_commit_only":
        raise RuntimeError("closeout review wake record did not persist guarded readback")
    if (review_wake_dir / "decision.md").read_text(encoding="utf-8").count("Status: Pending") != 1:
        raise RuntimeError("closeout review wake mutated decision.md")
    duplicate_review_wake = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "review-wake",
            "--work-unit-id",
            "WU-260607-117",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(review_wake_dir / "evidence.md"),
            "--closeout-reviewer-runtime",
            "openclaw-agent",
            "--closeout-reviewer-adapter",
            "fake",
            "--publish",
            "--format",
            "json",
        ]
    )
    if duplicate_review_wake.returncode == 0:
        raise RuntimeError("closeout review wake accepted duplicate wake without --force")

    review_accept_adapter = work_dir / "accept_closeout_review_adapter.py"
    review_accept_adapter.write_text(
        "\n".join(
            [
                "import json, sys",
                "request = json.load(sys.stdin)",
                "required = request['required_acceptance']",
                "print(json.dumps({",
                "    'status': 'accepted',",
                "    'adapter': 'smoke-closeout-review-command',",
                "    'session_ref': 'session:' + request['session_key'],",
                "    'job_ref': 'job:' + request['work_unit_id'] + ':closeout-review',",
                "    'message_ref': 'message:' + request['work_unit_id'] + ':closeout-review-accepted',",
                "    'accepted_at': request['transition_at'],",
                "    'readback': {",
                "        'work_unit_id': required['work_unit_id'],",
                "        'closeout_review_payload_hash': required['closeout_review_payload_hash'],",
                "        'guarded_closeout_contract': required['guarded_closeout_contract'],",
                "        'authority_boundary': required['authority_boundary'],",
                "    },",
                "}, sort_keys=True))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    review_command_wake = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "review-wake",
            "--work-unit-id",
            "WU-260607-118",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(review_command_dir / "evidence.md"),
            "--closeout-reviewer-runtime",
            "openclaw-agent",
            "--closeout-reviewer-adapter",
            "command",
            "--closeout-reviewer-adapter-command",
            f"{sys.executable} {review_accept_adapter}",
            "--publish",
            "--format",
            "json",
        ]
    )
    require_success(review_command_wake, "closeout review wake command adapter publish")
    review_command_record = json.loads((review_command_dir / "closeout-review-wake.json").read_text(encoding="utf-8"))
    if review_command_record.get("accepted_proof", {}).get("adapter") != "smoke-closeout-review-command":
        raise RuntimeError("closeout review command adapter proof was not persisted")

    review_hanging_adapter = work_dir / "hanging_closeout_review_adapter.py"
    review_hanging_adapter.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
    setup_progress_before = (review_setup_dir / "progress.jsonl").read_text(encoding="utf-8")
    review_setup_needed = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "review-wake",
            "--work-unit-id",
            "WU-260607-119",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "ops",
            "--source-ref",
            str(review_setup_dir / "evidence.md"),
            "--closeout-reviewer-runtime",
            "openclaw-agent",
            "--closeout-reviewer-adapter",
            "command",
            "--closeout-reviewer-adapter-command",
            f"{sys.executable} {review_hanging_adapter}",
            "--closeout-reviewer-adapter-timeout-seconds",
            "1",
            "--publish",
            "--format",
            "json",
        ]
    )
    if review_setup_needed.returncode == 0:
        raise RuntimeError("closeout review wake accepted a timed-out adapter")
    review_setup_payload = json.loads(review_setup_needed.stdout)
    if review_setup_payload.get("status") != "review-wake setup-needed":
        raise RuntimeError("timed-out closeout review adapter did not fail as setup-needed")
    if (review_setup_dir / "closeout-review-wake.json").exists():
        raise RuntimeError("setup-needed closeout review wake wrote a wake record")
    if (review_setup_dir / "progress.jsonl").read_text(encoding="utf-8") != setup_progress_before:
        raise RuntimeError("setup-needed closeout review wake mutated progress.jsonl")
    missed_wake_inbox = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "inbox",
            "--result-ready",
            "--artifact-root",
            str(artifact_root),
            "--work-unit-id",
            "WU-260607-119",
            "--format",
            "json",
        ]
    )
    require_success(missed_wake_inbox, "source inbox recovery after missed closeout review wake")
    if json.loads(missed_wake_inbox.stdout)["items"][0].get("work_unit_id") != "WU-260607-119":
        raise RuntimeError("missed closeout review wake was not recoverable from result-ready inbox")

    invalid_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-106",
            "--artifact-root",
            str(artifact_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if invalid_result.returncode == 0:
        raise RuntimeError("invalid result-ready closeout should fail closed")
    invalid_payload = json.loads(invalid_result.stdout)
    if invalid_payload.get("status") != "repair-needed":
        raise RuntimeError(f"invalid result-ready expected gate failure, got {invalid_payload.get('status')}")
    blockers = invalid_payload["item"].get("result_ready_blockers", [])
    if not any("evidence status is Draft" in blocker for blocker in blockers):
        raise RuntimeError("invalid result-ready gate did not reject draft evidence")
    if not any("missing source_ref" in blocker for blocker in blockers):
        raise RuntimeError("invalid result-ready gate did not reject missing progress source_ref")

    invalid_result_ready_publish = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "result-ready",
            "--work-unit-id",
            "WU-260607-106",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "build-lab",
            "--result",
            "This must not publish because evidence is still draft.",
            "--evidence",
            str(invalid_dir / "evidence.md"),
            "--verification",
            "Negative smoke for pre-publish gate.",
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if invalid_result_ready_publish.returncode == 0:
        raise RuntimeError("result-ready dry-run accepted draft evidence")

    missing_started_result_ready = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "result-ready",
            "--work-unit-id",
            "WU-260607-111",
            "--artifact-root",
            str(artifact_root),
            "--team",
            "market",
            "--result",
            "This must not publish because STARTED source is missing.",
            "--evidence",
            str(missing_started_dir / "evidence.md"),
            "--verification",
            "Negative smoke for STARTED precondition.",
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if missing_started_result_ready.returncode == 0:
        raise RuntimeError("result-ready dry-run accepted missing STARTED source")
    if "progress.STARTED" not in missing_started_result_ready.stderr:
        raise RuntimeError("missing STARTED failure did not point at progress.STARTED")

    invalid_project_field_map = inbox_work_dir / "project-field-map.json"
    write_json(
        invalid_project_field_map,
        {
            "owner": "@me",
            "project_number": 1,
            "project_id": "PVT_local_smoke",
            "fields": {
                "Work Unit id": "field_work_unit",
                "Repository": "field_repository",
                "Work Card": "field_work_card",
                "Team Lead": "field_team_lead",
                "Status": "field_status",
                "Progress": "field_progress",
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
    invalid_project_result = run_command(
        [
            sys.executable,
            str(PROJECT_SYNC),
            "project-sync",
            "dry-run",
            "--no-ledger",
            "--artifact-root",
            str(artifact_root),
            "--work-unit-id",
            "WU-260607-106",
            "--field-map",
            str(invalid_project_field_map),
            "--format",
            "json",
        ]
    )
    require_success(invalid_project_result, "invalid result-ready project dry-run")
    invalid_project_fields = json.loads(invalid_project_result.stdout)["work_units"][0]["desired_fields"]
    if invalid_project_fields.get("Status") != "In Progress":
        raise RuntimeError("Project sync mirrored invalid result_ready as Result Ready")
    if invalid_project_fields.get("Progress") != "result preflight repair needed":
        raise RuntimeError("Project sync did not show repair-needed progress for invalid result_ready")
    if invalid_project_fields.get("Blocker"):
        raise RuntimeError("Project sync treated repair-needed result_ready as a Blocked Work Unit")
    assert_status_lifecycle(artifact_root, "WU-260607-110", "working")
    assert_project_status(artifact_root, invalid_project_field_map, "WU-260607-110", "In Progress")

    invalid_progress_path = invalid_progress_dir / "progress.jsonl"
    before_invalid_progress = invalid_progress_path.read_text(encoding="utf-8") if invalid_progress_path.exists() else ""
    invalid_progress_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "progress",
            "--work-unit-id",
            "WU-260607-107",
            "--output-root",
            str(artifact_root),
            "--phase",
            "invalid source smoke",
            "--source-ref",
            "docs/examples/manual-dry-run/WU-260607-107/missing-source.md",
            "--transition-at",
            "2026-06-07T01:26:00Z",
        ]
    )
    if invalid_progress_result.returncode == 0:
        raise RuntimeError("progress append accepted a missing source_ref")
    after_invalid_progress = invalid_progress_path.read_text(encoding="utf-8") if invalid_progress_path.exists() else ""
    if before_invalid_progress != after_invalid_progress:
        raise RuntimeError("failed progress gate mutated progress.jsonl")

    invalid_claim_ledger = inbox_work_dir / "invalid-claim-ledger.json"
    invalid_claim_ref = create_claim(args, invalid_claim_ledger, "WU-260607-107", "build-lab", invalid_progress_dir)
    invalid_claim_result = run_command(
        [
            sys.executable,
            str(CLAIMS),
            "claim",
            "update",
            "--ledger",
            str(invalid_claim_ledger),
            "--claim-ref",
            invalid_claim_ref,
            "--expected-state",
            "result_ready",
            "--last-claim",
            "Trying to mark result_ready before evidence is ready.",
            "--evidence-ref",
            str(invalid_progress_dir / "evidence.md"),
        ]
    )
    if invalid_claim_result.returncode == 0:
        raise RuntimeError("claim update accepted result_ready with draft evidence")
    invalid_claim_status = run_command(
        [
            sys.executable,
            str(CLAIMS),
            "claim",
            "status",
            "--ledger",
            str(invalid_claim_ledger),
            "--claim-ref",
            invalid_claim_ref,
            "--format",
            "json",
        ]
    )
    require_success(invalid_claim_status, "invalid claim status readback")
    if json.loads(invalid_claim_status.stdout).get("expected_state") != "working":
        raise RuntimeError("failed claim gate mutated the ledger expected_state")

    ambiguous_dir = create_artifacts(args, inbox_work_dir, "WU-260607-105", "design")
    mark_artifact_started(ambiguous_dir)
    mark_artifact_result_ready(ambiguous_dir, recommendation=None)
    write_jsonl(
        ambiguous_dir / "visibility-proof.jsonl",
        proof_rows(
            "WU-260607-105",
            [("team-detail", "RESULT_READY", "ambiguous-001", "2026-06-07T01:30:00Z")],
        ),
    )

    stale_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "inbox",
            "--result-ready",
            "--artifact-root",
            str(artifact_root),
            "--work-unit-id",
            "WU-260607-103",
            "--format",
            "json",
        ]
    )
    require_success(stale_result, "result-ready stale item json")
    stale_item = json.loads(stale_result.stdout)["items"][0]
    if stale_item.get("stale_reason") != "decision already recorded":
        raise RuntimeError("result-ready inbox did not report already-decided stale item")

    conflict_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "inbox",
            "--result-ready",
            "--artifact-root",
            str(artifact_root),
            "--work-unit-id",
            "WU-260607-104",
            "--format",
            "json",
        ]
    )
    require_success(conflict_result, "result-ready conflict item json")
    conflict_item = json.loads(conflict_result.stdout)["items"][0]
    if "competing final review" not in conflict_item.get("conflict_reason", ""):
        raise RuntimeError("result-ready inbox did not report final-review conflict")

    closeout_result = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(closeout_result, "closeout dry-run ready")
    closeout_payload = json.loads(closeout_result.stdout)
    if closeout_payload.get("status") != "ready":
        raise RuntimeError(f"closeout dry-run expected ready, got {closeout_payload.get('status')}")
    if closeout_payload["item"].get("suggested_final_review_kind") != "ACCEPTED":
        raise RuntimeError("closeout dry-run did not derive accepted review candidate")
    if closeout_payload.get("would_publish_owner_closeout") is not False:
        raise RuntimeError("closeout dry-run reported owner closeout mutation")
    if (ready_late / ".closeout.lock").exists():
        raise RuntimeError("closeout dry-run left the WU lock behind")

    result_ready_proof_before = (ready_late / "visibility-proof.jsonl").read_text(encoding="utf-8")
    result_ready_dry_run = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "result-ready",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--result",
            "Result-ready official transition smoke.",
            "--evidence",
            str(ready_late / "evidence.md"),
            "--verification",
            "Pre-publish gate passes after STARTED source evidence exists.",
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(result_ready_dry_run, "work-unit result-ready dry-run")
    result_ready_payload = json.loads(result_ready_dry_run.stdout)
    if result_ready_payload.get("status") != "ready-to-publish":
        raise RuntimeError("result-ready dry-run did not report ready-to-publish")
    if result_ready_payload.get("card", {}).get("kind") != "RESULT_READY":
        raise RuntimeError("result-ready dry-run did not compose a RESULT_READY card")
    if result_ready_payload.get("would_append_proof") is not False:
        raise RuntimeError("result-ready dry-run reported proof mutation")
    if (ready_late / "visibility-proof.jsonl").read_text(encoding="utf-8") != result_ready_proof_before:
        raise RuntimeError("result-ready dry-run mutated visibility proof")
    duplicate_result_ready = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "result-ready",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--result",
            "Duplicate RESULT_READY should fail before publish.",
            "--evidence",
            str(ready_late / "evidence.md"),
            "--verification",
            "Existing RESULT_READY proof already exists.",
            "--target",
            "local-smoke",
            "--publish",
            "--format",
            "json",
        ]
    )
    if duplicate_result_ready.returncode == 0:
        raise RuntimeError("result-ready publish accepted duplicate RESULT_READY without --force")
    if "RESULT_READY proof already exists" not in duplicate_result_ready.stderr:
        raise RuntimeError("duplicate RESULT_READY failure did not explain the existing proof guard")
    if (ready_late / "visibility-proof.jsonl").read_text(encoding="utf-8") != result_ready_proof_before:
        raise RuntimeError("duplicate RESULT_READY guard mutated visibility proof")

    decision_before = (ready_late / "decision.md").read_text(encoding="utf-8")
    closeout_accept = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--decision",
            "accept",
            "--reason",
            "Operations Lead accepts the source-backed result.",
            "--source-ref",
            str(ready_late / "evidence.md"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(closeout_accept, "closeout accept decision dry-run")
    accept_payload = json.loads(closeout_accept.stdout)
    if accept_payload.get("status") != "decision-ready":
        raise RuntimeError(f"closeout accept dry-run expected decision-ready, got {accept_payload.get('status')}")
    if accept_payload.get("team_card", {}).get("kind") != "ACCEPTED":
        raise RuntimeError("closeout accept dry-run did not compose ACCEPTED team card")
    if accept_payload.get("owner_card", {}).get("kind") != "COMPLETED":
        raise RuntimeError("closeout accept dry-run did not compose COMPLETED owner card")
    if accept_payload.get("resolved_work_card") != "local-smoke://WU-260607-101":
        raise RuntimeError("closeout accept dry-run did not resolve Work Card")
    if accept_payload.get("work_card_source") != "assignment.md":
        raise RuntimeError("closeout accept dry-run used the wrong Work Card source")
    if "- Work Card: local-smoke://WU-260607-101" not in accept_payload.get("decision_preview", ""):
        raise RuntimeError("closeout accept decision preview did not preserve Work Card")
    if (ready_late / "decision.md").read_text(encoding="utf-8") != decision_before:
        raise RuntimeError("closeout accept dry-run mutated decision.md")
    if (ready_late / "team-accept-card.json").exists() or (ready_late / "ops-completed-card.json").exists():
        raise RuntimeError("closeout accept dry-run wrote card artifacts")

    commit_request = closeout_commit_request(
        ready_late,
        "WU-260607-101",
        proof_id="late-001",
        proof_timestamp="2026-06-07T01:20:00Z",
    )
    closeout_commit_request_dry_run = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--commit-request",
            json.dumps(commit_request, sort_keys=True),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(closeout_commit_request_dry_run, "closeout commit-request dry-run")
    commit_payload = json.loads(closeout_commit_request_dry_run.stdout)
    if commit_payload.get("status") != "decision-ready":
        raise RuntimeError("closeout commit-request did not produce decision-ready")
    if "## Guarded Commit Request" not in commit_payload.get("decision_preview", ""):
        raise RuntimeError("closeout commit-request decision preview did not record guarded request context")
    if (ready_late / "decision.md").read_text(encoding="utf-8") != decision_before:
        raise RuntimeError("closeout commit-request dry-run mutated decision.md")

    mismatched_request = json.loads(json.dumps(commit_request))
    mismatched_request["artifact_hashes"]["evidence.md"] = "0" * 64
    closeout_hash_mismatch = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--commit-request",
            json.dumps(mismatched_request, sort_keys=True),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if closeout_hash_mismatch.returncode == 0:
        raise RuntimeError("closeout commit-request accepted an artifact hash mismatch")
    hash_mismatch_payload = json.loads(closeout_hash_mismatch.stdout)
    if "artifact hash mismatch: evidence.md" not in " ".join(hash_mismatch_payload.get("decision_failures", [])):
        raise RuntimeError("closeout commit-request hash mismatch failure did not explain evidence.md")
    if (ready_late / "decision.md").read_text(encoding="utf-8") != decision_before:
        raise RuntimeError("hash-mismatched commit-request mutated decision.md")

    partial_root = work_dir / "partial-closeout-artifacts"
    partial_wu = partial_root / "WU-260607-101"
    shutil.copytree(ready_late, partial_wu)
    partial_request = closeout_commit_request(
        partial_wu,
        "WU-260607-101",
        proof_id="late-001",
        proof_timestamp="2026-06-07T01:20:00Z",
    )
    partial_decision_before = (partial_wu / "decision.md").read_text(encoding="utf-8")
    sys.path.insert(0, str(SCRIPT_DIR))
    import work_unit_artifacts as work_unit_module  # type: ignore

    partial_parser = work_unit_module.build_parser()
    publish_calls: list[str] = []
    original_publish_card = work_unit_module.publish_card
    original_project_sync = work_unit_module.run_project_sync

    def fake_publish_card(args: argparse.Namespace, card: dict[str, Any], proof_log: Path, *, target: str | None = None, expect_surface: str = "team-detail") -> tuple[int, dict[str, Any], str]:
        publish_calls.append(expect_surface)
        failed_owner = expect_surface == "ops-feed" and publish_calls.count("ops-feed") == 1
        row = {
            "work_unit_id": args.work_unit_id,
            "surface": expect_surface,
            "kind": card["kind"],
            "target": target or "",
            "transition_at": args.transition_at,
            "sent_at": args.transition_at,
            "readback_at": args.transition_at,
            "discord_timestamp": args.transition_at,
            "discord_message_id": f"partial-{expect_surface}-{len(publish_calls)}",
            "proof_id": f"{args.work_unit_id}:{expect_surface}:{card['kind']}:partial-{len(publish_calls)}",
            "readback_ok": not failed_owner,
            "dry_run": False,
            "error": "owner closeout publish failed for partial smoke" if failed_owner else "",
            "send_result": {},
            "readback_result": {},
        }
        proof_log.parent.mkdir(parents=True, exist_ok=True)
        with proof_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        if failed_owner:
            return 1, {"publish": row}, "owner closeout publish failed for partial smoke"
        return 0, {"publish": row}, ""

    try:
        work_unit_module.publish_card = fake_publish_card
        work_unit_module.run_project_sync = lambda args: {"enabled": False}
        partial_args = partial_parser.parse_args(
            [
                "work-unit",
                "closeout",
                "--work-unit-id",
                "WU-260607-101",
                "--artifact-root",
                str(partial_root),
                "--commit-request",
                json.dumps(partial_request, sort_keys=True),
                "--publish",
                "--team-target",
                "channel:team",
                "--ops-target",
                "channel:ops",
                "--transition-at",
                "2026-06-07T02:00:00Z",
                "--format",
                "json",
            ]
        )
        first_stdout = io.StringIO()
        first_stderr = io.StringIO()
        with contextlib.redirect_stdout(first_stdout), contextlib.redirect_stderr(first_stderr):
            first_partial = partial_args.func(partial_args)
        if first_partial == 0:
            raise RuntimeError("partial closeout smoke unexpectedly succeeded on owner publish failure")
        if (partial_wu / "decision.md").read_text(encoding="utf-8") != partial_decision_before:
            raise RuntimeError("partial closeout wrote final decision before owner visibility succeeded")
        stage_payload = json.loads((partial_wu / "closeout-accept-stage.json").read_text(encoding="utf-8"))
        if stage_payload.get("status") != "team-published":
            raise RuntimeError("partial closeout stage did not record team-published recovery point")

        second_args = partial_parser.parse_args(
            [
                "work-unit",
                "closeout",
                "--work-unit-id",
                "WU-260607-101",
                "--artifact-root",
                str(partial_root),
                "--commit-request",
                json.dumps(partial_request, sort_keys=True),
                "--publish",
                "--team-target",
                "channel:team",
                "--ops-target",
                "channel:ops",
                "--transition-at",
                "2026-06-07T02:01:00Z",
                "--format",
                "json",
            ]
        )
        second_stdout = io.StringIO()
        second_stderr = io.StringIO()
        with contextlib.redirect_stdout(second_stdout), contextlib.redirect_stderr(second_stderr):
            require_code = second_args.func(second_args)
        if require_code != 0:
            raise RuntimeError(
                "partial closeout resume did not complete: "
                + (second_stderr.getvalue().strip() or second_stdout.getvalue().strip() or "no output")
            )
        if publish_calls != ["team-detail", "ops-feed", "ops-feed"]:
            raise RuntimeError(f"partial closeout resume did not skip duplicate team publish: {publish_calls}")
        if "Status: Accepted" not in (partial_wu / "decision.md").read_text(encoding="utf-8"):
            raise RuntimeError("partial closeout resume did not write final decision after visibility succeeded")
        stage_payload = json.loads((partial_wu / "closeout-accept-stage.json").read_text(encoding="utf-8"))
        if stage_payload.get("status") != "published":
            raise RuntimeError("partial closeout resume did not publish final stage")
    finally:
        work_unit_module.publish_card = original_publish_card
        work_unit_module.run_project_sync = original_project_sync

    manual_required_request = json.loads(json.dumps(commit_request))
    manual_required_request["autonomy_class"] = "manual_required"
    closeout_manual_required = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--commit-request",
            json.dumps(manual_required_request, sort_keys=True),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if closeout_manual_required.returncode == 0:
        raise RuntimeError("closeout commit-request accepted manual_required auto-commit")
    manual_required_payload = json.loads(closeout_manual_required.stdout)
    if "manual_required cannot auto-commit" not in " ".join(manual_required_payload.get("decision_failures", [])):
        raise RuntimeError("manual_required commit-request failure did not fail closed explicitly")

    wrong_wu_request = json.loads(json.dumps(commit_request))
    wrong_wu_request["work_unit_id"] = "WU-260607-999"
    closeout_wrong_wu = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--commit-request",
            json.dumps(wrong_wu_request, sort_keys=True),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if closeout_wrong_wu.returncode == 0:
        raise RuntimeError("closeout commit-request accepted mismatched Work Unit id")
    wrong_wu_payload = json.loads(closeout_wrong_wu.stdout)
    if "work_unit_id mismatch" not in " ".join(wrong_wu_payload.get("decision_failures", [])):
        raise RuntimeError("commit-request WU mismatch failure did not explain the mismatch")

    (ready_late / "decision.md").write_text(accept_payload["decision_preview"], encoding="utf-8")
    closeout_already_decided_commit = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-101",
            "--artifact-root",
            str(artifact_root),
            "--commit-request",
            json.dumps(commit_request, sort_keys=True),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if closeout_already_decided_commit.returncode == 0:
        raise RuntimeError("closeout commit-request accepted an already-decided Work Unit")
    already_decided_payload = json.loads(closeout_already_decided_commit.stdout)
    if "already records a final" not in " ".join(already_decided_payload.get("decision_failures", [])):
        raise RuntimeError("already-decided commit-request failure did not cite final decision guard")
    assert_status_lifecycle(artifact_root, "WU-260607-101", "accepted")
    assert_project_status(artifact_root, invalid_project_field_map, "WU-260607-101", "Accepted")

    closeout_revise = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-102",
            "--artifact-root",
            str(artifact_root),
            "--decision",
            "revise",
            "--reason",
            "Operations Lead needs one more source-backed correction.",
            "--source-ref",
            str(ready_early / "evidence.md"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(closeout_revise, "closeout revise decision dry-run")
    revise_payload = json.loads(closeout_revise.stdout)
    if revise_payload.get("team_card", {}).get("kind") != "REVISE":
        raise RuntimeError("closeout revise dry-run did not compose REVISE team card")
    if revise_payload.get("owner_card", {}).get("kind") != "NEEDS_REVISION":
        raise RuntimeError("closeout revise dry-run did not compose NEEDS_REVISION owner card")
    if "- Work Card: local-smoke://WU-260607-102" not in revise_payload.get("decision_preview", ""):
        raise RuntimeError("closeout revise decision preview did not preserve Work Card")
    (ready_early / "decision.md").write_text(revise_payload["decision_preview"], encoding="utf-8")
    assert_status_lifecycle(artifact_root, "WU-260607-102", "revision_requested")
    assert_project_status(artifact_root, invalid_project_field_map, "WU-260607-102", "Revise")

    blocked_dir = create_artifacts(args, inbox_work_dir, "WU-260607-108", "build-lab")
    blocked_closeout = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-108",
            "--artifact-root",
            str(artifact_root),
            "--decision",
            "blocked",
            "--reason",
            "Required owner input is missing.",
            "--blocker-source",
            "owner-request://missing-input",
            "--needed",
            "Owner provides the missing source input.",
            "--next-owner",
            "operations-lead",
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(blocked_closeout, "closeout blocked decision dry-run")
    blocked_payload = json.loads(blocked_closeout.stdout)
    if blocked_payload.get("status") != "decision-ready":
        raise RuntimeError("blocked closeout should not require result_ready")
    if blocked_payload.get("team_card", {}).get("kind") != "BLOCKED_DETAIL":
        raise RuntimeError("blocked closeout did not compose BLOCKED_DETAIL team card")
    if blocked_payload.get("owner_card", {}).get("kind") != "BLOCKED":
        raise RuntimeError("blocked closeout did not compose BLOCKED owner card")
    if "- Work Card: local-smoke://WU-260607-108" not in blocked_payload.get("decision_preview", ""):
        raise RuntimeError("blocked closeout decision preview did not preserve Work Card")
    if (blocked_dir / "decision.md").read_text(encoding="utf-8").startswith("Status: Blocked"):
        raise RuntimeError("blocked closeout dry-run mutated decision.md")
    (blocked_dir / "decision.md").write_text(blocked_payload["decision_preview"], encoding="utf-8")
    assert_status_lifecycle(artifact_root, "WU-260607-108", "blocked")
    assert_project_status(artifact_root, invalid_project_field_map, "WU-260607-108", "Blocked")

    missing_work_card_dir = create_artifacts(args, inbox_work_dir, "WU-260607-109", "build-lab")
    mark_artifact_started(missing_work_card_dir)
    mark_artifact_result_ready(missing_work_card_dir, recommendation="accept")
    remove_work_card_fields(missing_work_card_dir)
    missing_work_card_closeout = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-109",
            "--artifact-root",
            str(artifact_root),
            "--decision",
            "accept",
            "--reason",
            "Operations Lead accepts the source-backed result.",
            "--source-ref",
            str(missing_work_card_dir / "evidence.md"),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if missing_work_card_closeout.returncode == 0:
        raise RuntimeError("closeout accepted missing Work Card source")
    missing_work_card_payload = json.loads(missing_work_card_closeout.stdout)
    if missing_work_card_payload.get("status") != "repair-needed":
        raise RuntimeError("missing Work Card closeout did not return repair-needed")
    if missing_work_card_payload.get("decision_preview"):
        raise RuntimeError("missing Work Card closeout produced a decision preview")
    if "source Work Card" not in " ".join(missing_work_card_payload.get("decision_failures", [])):
        raise RuntimeError("missing Work Card closeout did not explain the source Work Card failure")

    lock_path = ready_late / ".closeout.lock"
    lock_path.mkdir()
    try:
        locked_result = run_command(
            [
                sys.executable,
                str(ARTIFACTS),
                "work-unit",
                "closeout",
                "--work-unit-id",
                "WU-260607-101",
                "--artifact-root",
                str(artifact_root),
                "--dry-run",
                "--format",
                "json",
            ]
        )
        if locked_result.returncode == 0:
            raise RuntimeError("closeout dry-run ignored an existing WU lock")
        if "closeout lock already exists" not in locked_result.stderr:
            raise RuntimeError(f"closeout lock failed for wrong reason: {locked_result.stderr}")
    finally:
        lock_path.rmdir()

    stale_closeout = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-103",
            "--artifact-root",
            str(artifact_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    if stale_closeout.returncode == 0:
        raise RuntimeError("closeout dry-run accepted already-decided Work Unit")
    if json.loads(stale_closeout.stdout).get("status") != "already-decided":
        raise RuntimeError("closeout dry-run did not mark stale Work Unit already-decided")

    ambiguous_closeout = run_command(
        [
            sys.executable,
            str(ARTIFACTS),
            "work-unit",
            "closeout",
            "--work-unit-id",
            "WU-260607-105",
            "--artifact-root",
            str(artifact_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    require_success(ambiguous_closeout, "closeout dry-run ambiguous recommendation")
    ambiguous_payload = json.loads(ambiguous_closeout.stdout)
    if ambiguous_payload.get("status") != "needs-ops-decision":
        raise RuntimeError("closeout dry-run did not require Operations Lead decision for ambiguous template")
    if ambiguous_payload["item"].get("suggested_final_review_kind"):
        raise RuntimeError("closeout dry-run guessed a final review from the default recommendation template")


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
        run_async_work_unit_policy_smoke()
        run_discord_card_smoke()
        mark_artifact_started(build_artifacts)
        mark_artifact_result_ready(build_artifacts)
        update_result_ready(ledger, build_claim, build_artifacts)
        run_project_sync_smoke(args, ledger, work_dir / "artifacts", "WU-260605-901")
        run_result_ready_inbox_smoke(args, work_dir)
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
        "async Work Unit policy docs, "
        "purpose-specific Discord card/checkpoint composition, "
        "thin handoff dry-run/no-mutation validation, "
        "handoff draft dry-run/no-mutation validation, "
        "handoff amendment dry-run/no-mutation validation, "
        "live proof validation with burst replay rejection, "
        "Project sync dry-run planning without mutation, "
        "dispatch source contract/setup-needed guard, fresh session key guard, fake and command adapter accepted-proof guards, "
        "closeout review wrapper and wake accepted-proof guards, source inbox recovery after missed review wake, "
        "guarded closeout commit-request proof/hash/manual-required guards, partial closeout publish resume, "
        "result-ready publish dry-run and closeout decision safety, "
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
