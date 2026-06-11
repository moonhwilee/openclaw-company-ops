"""Deterministic Work Unit progress display helpers."""

from __future__ import annotations

from typing import Any

ROUND_VISIBLE_MODES = {"goal", "convergence"}

AT_RISK_STATES = {"at-risk", "at_risk", "risk", "blocked", "blocker", "blocked_progress"}
RETRY_STATES = {"retry", "re-run", "rerun", "re_run", "retrying"}


def truthy(value: Any) -> bool:
    return value is True or str(value or "").strip().lower() in {"1", "true", "yes"}


def should_show_round(mode: str, explicit_show_round: Any) -> bool:
    if mode.strip().lower() not in ROUND_VISIBLE_MODES:
        return False
    if str(explicit_show_round or "").strip().lower() in {"0", "false", "no"}:
        return False
    return True


def normalized_state(value: Any) -> str:
    return str(value or "").strip().lower()


def progress_icon(row: dict[str, Any]) -> str:
    risk_state = normalized_state(row.get("risk_state")).replace(" ", "_")
    retry_state = normalized_state(row.get("retry_state")).replace(" ", "_")
    if risk_state in AT_RISK_STATES:
        return "⚠️"
    if retry_state in RETRY_STATES:
        return "🔄"
    return "🧭"


def progress_parts(row: dict[str, Any]) -> tuple[str, str, str]:
    phase = str(row.get("phase") or "").strip()
    current_slice = str(row.get("current_slice") or "").strip()
    round_value = str(row.get("round") or "").strip()
    mode = str(row.get("mode") or "").strip().lower()
    index = str(row.get("phase_index") or "").strip()
    total = str(row.get("phase_total") or "").strip()

    prefix = f"P{index}/{total}" if index and total else f"P{index}" if index else ""
    round_part = f"R{round_value}" if round_value and should_show_round(mode, row.get("show_round")) else ""
    label = current_slice or phase
    return round_part, prefix, label


def render_progress_display(row: dict[str, Any]) -> dict[str, Any]:
    round_part, prefix, label = progress_parts(row)
    summary = " · ".join(part for part in (round_part, prefix, label) if part)
    return {
        "rendered_progress_summary": summary,
        "icon": progress_icon(row),
    }


def render_progress_summary(row: dict[str, Any]) -> str:
    return str(render_progress_display(row)["rendered_progress_summary"])
