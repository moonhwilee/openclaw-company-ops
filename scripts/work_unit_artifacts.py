#!/usr/bin/env python3
"""Create the four required OpenClaw Company Ops Work Unit artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ARTIFACTS = ("assignment.md", "claim.md", "evidence.md", "decision.md")
WORK_UNIT_RE = re.compile(r"^WU-\d{6}-\d{3}$")
ROUND_VISIBLE_MODES = {"goal", "convergence"}
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROOF_LOG_NAME = "visibility-proof.jsonl"


def required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise argparse.ArgumentTypeError("value must not be empty")
    return cleaned


def work_unit_id(value: str) -> str:
    cleaned = required(value)
    if not WORK_UNIT_RE.match(cleaned):
        raise argparse.ArgumentTypeError("expected format WU-YYMMDD-NNN")
    return cleaned


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def should_show_round(mode: str, explicit_show_round: bool) -> bool:
    return explicit_show_round or mode.strip().lower() in ROUND_VISIBLE_MODES


def progress_row_from_args(
    args: argparse.Namespace,
    *,
    transition_at: str,
    proof_ref: str | None = None,
) -> dict[str, Any]:
    mode = args.mode.strip().lower()
    return {
        "work_unit_id": args.work_unit_id,
        "transition_kind": args.transition_kind,
        "mode": mode,
        "phase": args.phase,
        "phase_index": args.phase_index,
        "phase_total": args.phase_total,
        "round": args.round,
        "show_round": should_show_round(mode, bool(args.show_round)),
        "current_slice": args.current_slice,
        "next_checkpoint": args.next_checkpoint,
        "source_ref": args.source_ref,
        "proof_ref": proof_ref if proof_ref is not None else args.proof_ref,
        "transition_at": transition_at,
        "recorded_by": args.recorded_by,
    }


def append_progress_row(output_dir: Path, row: dict[str, Any]) -> Path:
    progress_path = output_dir / "progress.jsonl"
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return progress_path


def run_json_command(command: list[str]) -> tuple[int, dict[str, Any], str]:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    parsed: dict[str, Any] = {}
    if result.stdout.strip():
        try:
            loaded = json.loads(result.stdout)
            if isinstance(loaded, dict):
                parsed = loaded
        except json.JSONDecodeError:
            parsed = {}
    return result.returncode, parsed, result.stderr.strip() or result.stdout.strip()


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"input is not valid JSON: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"input root must be a JSON object: {path}")
    return loaded


def require_spec_text(spec: dict[str, Any], key: str) -> str:
    value = spec.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"handoff spec requires non-empty string: {key}")
    return value.strip()


def optional_spec_text(spec: dict[str, Any], key: str, default: str = "") -> str:
    value = spec.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"handoff spec field must be a string: {key}")
    return value.strip()


def spec_text_list(spec: dict[str, Any], key: str) -> list[str]:
    value = spec.get(key)
    if isinstance(value, str):
        items = [line.strip(" -") for line in value.splitlines()]
    elif isinstance(value, list):
        items = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"handoff spec list contains non-string item: {key}")
            items.append(item.strip())
    else:
        raise ValueError(f"handoff spec requires non-empty string or list: {key}")
    cleaned = [item for item in items if item]
    if not cleaned:
        raise ValueError(f"handoff spec requires at least one value: {key}")
    return cleaned


def markdown_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def create_work_unit(args: argparse.Namespace) -> int:
    output_dir = args.output_root.expanduser() / args.work_unit_id
    created_at = args.created_at or dt.date.today().isoformat()

    if output_dir.exists() and not args.force:
        print(
            f"error: output directory already exists: {output_dir}\n"
            "Use --force to replace generated artifact files.",
            file=sys.stderr,
        )
        return 1

    if output_dir.exists() and not output_dir.is_dir():
        print(f"error: output path exists and is not a directory: {output_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    context = {
        "work_unit_id": args.work_unit_id,
        "title": args.title,
        "work_card": args.work_card,
        "operations_lead": args.operations_lead,
        "team_lead": args.team_lead,
        "created_at": created_at,
        "assignment_path": f"{output_dir / 'assignment.md'}",
        "claim_path": f"{output_dir / 'claim.md'}",
        "evidence_path": f"{output_dir / 'evidence.md'}",
        "decision_path": f"{output_dir / 'decision.md'}",
    }

    rendered = {
        "assignment.md": render_assignment(context),
        "claim.md": render_claim(context),
        "evidence.md": render_evidence(context),
        "decision.md": render_decision(context),
    }

    for filename, content in rendered.items():
        path = output_dir / filename
        if path.exists() and not args.force:
            print(f"error: artifact already exists: {path}", file=sys.stderr)
            return 1
        path.write_text(content, encoding="utf-8")

    print(f"created {output_dir}")
    for filename in ARTIFACTS:
        print(f"- {filename}")
    return 0


def validate_handoff_spec(spec: dict[str, Any]) -> dict[str, Any]:
    targets = spec.get("targets")
    if not isinstance(targets, dict):
        raise ValueError("handoff spec requires object: targets")
    ops_target = targets.get("ops_feed")
    team_target = targets.get("team_detail")
    if not isinstance(ops_target, str) or not ops_target.strip():
        raise ValueError("handoff spec requires non-empty targets.ops_feed")
    if not isinstance(team_target, str) or not team_target.strip():
        raise ValueError("handoff spec requires non-empty targets.team_detail")

    normalized = {
        "work_unit_id": work_unit_id(require_spec_text(spec, "work_unit_id")),
        "title": require_spec_text(spec, "title"),
        "team": require_spec_text(spec, "team"),
        "mode": require_spec_text(spec, "mode"),
        "goal": require_spec_text(spec, "goal"),
        "scope": spec_text_list(spec, "scope"),
        "done_criteria": spec_text_list(spec, "done_criteria"),
        "verification_criteria": spec_text_list(spec, "verification_criteria"),
        "targets": {
            "ops_feed": ops_target.strip(),
            "team_detail": team_target.strip(),
        },
        "owner_request": optional_spec_text(spec, "owner_request"),
        "next": optional_spec_text(spec, "next", "Team Lead starts from the Assignment Packet."),
        "report": optional_spec_text(
            spec,
            "report",
            "Result summary, evidence links, checks performed, remaining risks, blockers.",
        ),
        "operations_lead": optional_spec_text(spec, "operations_lead", "operations-lead"),
        "work_card": optional_spec_text(spec, "work_card") or optional_spec_text(spec, "work_card_ref"),
        "work_card_repo": optional_spec_text(spec, "work_card_repo"),
        "created_at": optional_spec_text(spec, "created_at"),
        "source_refs": spec_text_list(spec, "source_refs") if "source_refs" in spec else [],
    }
    if not normalized["work_card"] and not normalized["work_card_repo"]:
        raise ValueError("handoff spec requires work_card/work_card_ref or work_card_repo")
    return normalized


def work_card_body(spec: dict[str, Any], output_dir: Path) -> str:
    assignment_path = output_dir / "assignment.md"
    evidence_path = output_dir / "evidence.md"
    decision_path = output_dir / "decision.md"
    source_refs = markdown_bullets(spec["source_refs"]) if spec["source_refs"] else "-"
    return f"""# Work Card

## Identity

- Work Unit id: `{spec["work_unit_id"]}`
- Assigned Team Lead OpenClaw Agent: `{spec["team"]}`
- Mode: `{spec["mode"]}`
- Assignment Packet: `{assignment_path}`
- Evidence & Result Record: `{evidence_path}`
- Operations Lead Decision: `{decision_path}`

## Goal

{spec["goal"]}

## Scope

{markdown_bullets(spec["scope"])}

## Done Criteria

{markdown_bullets(spec["done_criteria"])}

## Verification Criteria

{markdown_bullets(spec["verification_criteria"])}

## Source Refs

{source_refs}

## Rule

This Work Card is a visibility card. The Assignment Packet and source artifacts
remain the source of truth.
"""


def create_github_work_card(spec: dict[str, Any], output_dir: Path) -> str:
    body = work_card_body(spec, output_dir)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        body_path = Path(handle.name)
        handle.write(body)
    try:
        command = [
            "gh",
            "issue",
            "create",
            "--repo",
            spec["work_card_repo"],
            "--title",
            f"{spec['work_unit_id']} · {spec['title']}",
            "--body-file",
            str(body_path),
            "--label",
            "work-unit",
            "--label",
            "assignment-ready",
        ]
        result = subprocess.run(command, check=False, text=True, capture_output=True)
    finally:
        try:
            body_path.unlink()
        except FileNotFoundError:
            pass
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue create failed")
    created_url = result.stdout.strip().splitlines()[-1].strip()
    if not created_url:
        raise RuntimeError("gh issue create did not return a Work Card URL")
    return created_url


def render_handoff_assignment(context: dict[str, Any]) -> str:
    return f"""# Assignment Packet

Status: Assigned

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Operations Lead: `{context["operations_lead"]}`
- Assigned Team Lead OpenClaw Agent: `{context["team_lead"]}`
- Mode: `{context["mode"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Owner Request

{context["owner_request"] or context["goal"]}

## Goal

{context["goal"]}

## Scope

{markdown_bullets(context["scope"])}

## Non-goals

- Do not expand beyond this initial handoff scope.
- Do not treat Discord, GitHub Project, comments, or labels as source truth.

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.

## Inputs

{markdown_bullets(context["source_refs"]) if context["source_refs"] else "- See Work Card and source artifacts."}

## Done Criteria

{markdown_bullets(context["done_criteria"])}

## Verification Criteria

{markdown_bullets(context["verification_criteria"])}

## Protocol Capsule

```yaml
protocol_capsule:
  mode: {context["mode"]}
  support: []
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_selected_mode
```

## Expected Outputs

- Evidence & Result Record: `{context["evidence_path"]}`
- PR or artifact:
- Decision-ready summary:

## Reporting Format

{context["report"]}

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
"""


def render_handoff_artifacts(spec: dict[str, Any], output_dir: Path, created_at: str) -> dict[str, str]:
    context = {
        "work_unit_id": spec["work_unit_id"],
        "title": spec["title"],
        "work_card": spec["work_card"],
        "operations_lead": spec["operations_lead"],
        "team_lead": spec["team"],
        "mode": spec["mode"],
        "goal": spec["goal"],
        "owner_request": spec["owner_request"],
        "scope": spec["scope"],
        "done_criteria": spec["done_criteria"],
        "verification_criteria": spec["verification_criteria"],
        "source_refs": spec["source_refs"],
        "report": spec["report"],
        "created_at": created_at,
        "assignment_path": f"{output_dir / 'assignment.md'}",
        "claim_path": f"{output_dir / 'claim.md'}",
        "evidence_path": f"{output_dir / 'evidence.md'}",
        "decision_path": f"{output_dir / 'decision.md'}",
    }
    base_context = {
        key: str(context[key])
        for key in (
            "work_unit_id",
            "title",
            "work_card",
            "operations_lead",
            "team_lead",
            "created_at",
            "assignment_path",
            "claim_path",
            "evidence_path",
            "decision_path",
        )
    }
    return {
        "assignment.md": render_handoff_assignment(context),
        "claim.md": render_claim(base_context),
        "evidence.md": render_evidence(base_context),
        "decision.md": render_decision(base_context),
    }


def handoff_card_payloads(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    criteria = "; ".join(spec["done_criteria"])
    caution = "Scope is limited to the Assignment Packet and source artifacts."
    source = spec["work_card"]
    ops_code, ops_payload, ops_error = run_json_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "ops-feed",
            "--kind",
            "ASSIGNED",
            "--work-unit-id",
            spec["work_unit_id"],
            "--team",
            spec["team"],
            "--problem",
            spec["title"],
            "--request",
            spec["owner_request"] or spec["goal"],
            "--criteria",
            criteria,
            "--next",
            spec["next"],
            "--source",
            source,
            "--format",
            "json",
        ]
    )
    if ops_code != 0:
        raise RuntimeError(f"ops ASSIGNED card failed: {ops_error}")
    team_code, team_payload, team_error = run_json_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "card",
            "--surface",
            "team-detail",
            "--kind",
            "ASSIGNED_DETAIL",
            "--work-unit-id",
            spec["work_unit_id"],
            "--team",
            spec["team"],
            "--goal",
            spec["goal"],
            "--scope",
            first_line("; ".join(spec["scope"])),
            "--criteria",
            criteria,
            "--caution",
            caution,
            "--report",
            spec["report"],
            "--next",
            spec["next"],
            "--source",
            source,
            "--format",
            "json",
        ]
    )
    if team_code != 0:
        raise RuntimeError(f"team ASSIGNED_DETAIL card failed: {team_error}")
    return ops_payload["card"], team_payload["card"], ops_payload["text"], team_payload["text"]


def write_handoff_files(
    output_dir: Path,
    rendered: dict[str, str],
    ops_card: dict[str, Any],
    team_card: dict[str, Any],
    *,
    force: bool,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        **{filename: output_dir / filename for filename in ARTIFACTS},
        "ops_card": output_dir / "ops-assigned-card.json",
        "team_card": output_dir / "team-assigned-card.json",
    }
    if not force:
        existing = [str(path) for path in paths.values() if path.exists()]
        if existing:
            raise FileExistsError("handoff output already exists: " + ", ".join(existing))
    for filename, content in rendered.items():
        paths[filename].write_text(content, encoding="utf-8")
    paths["ops_card"].write_text(json.dumps({"card": ops_card}, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["team_card"].write_text(json.dumps({"card": team_card}, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def publish_handoff_sequence(args: argparse.Namespace, spec: dict[str, Any], paths: dict[str, str], proof_log: Path) -> tuple[int, dict[str, Any], str]:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "discord_ops.py"),
        "publish-sequence",
        "--card-target",
        f"{paths['ops_card']}={spec['targets']['ops_feed']}",
        "--card-target",
        f"{paths['team_card']}={spec['targets']['team_detail']}",
        "--proof-log",
        str(proof_log),
        "--transition-at",
        args.transition_at,
        "--readback-limit",
        str(args.readback_limit),
        "--format",
        "json",
    ]
    if args.channel:
        command.extend(["--channel", args.channel])
    if args.account:
        command.extend(["--account", args.account])
    if args.thread_id:
        command.extend(["--thread-id", args.thread_id])
    return run_json_command(command)


def handoff_work_unit(args: argparse.Namespace) -> int:
    try:
        spec = validate_handoff_spec(read_json_file(args.spec))
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not args.dry_run and not args.publish:
        print("error: handoff requires --dry-run or --publish", file=sys.stderr)
        return 1

    output_dir = args.output_root.expanduser() / spec["work_unit_id"]
    created_at = spec["created_at"] or args.created_at or utc_now_iso()
    proof_log = args.proof_log.expanduser() if args.proof_log else output_dir / DEFAULT_PROOF_LOG_NAME
    args.work_unit_id = spec["work_unit_id"]
    args.output_root = args.output_root.expanduser()
    args.transition_at = args.transition_at or utc_now_iso()

    if not spec["work_card"]:
        spec["work_card"] = f"planned Work Card in {spec['work_card_repo']}"

    try:
        rendered = render_handoff_artifacts(spec, output_dir, created_at)
        ops_card, team_card, ops_text, team_text = handoff_card_payloads(spec)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.publish and not args.force:
        planned_paths = [output_dir / filename for filename in (*ARTIFACTS, "ops-assigned-card.json", "team-assigned-card.json")]
        existing = [str(path) for path in planned_paths if path.exists()]
        if existing:
            print(f"error: handoff output already exists: {', '.join(existing)}", file=sys.stderr)
            return 1

    if args.publish and spec["work_card"].startswith("planned Work Card in "):
        try:
            spec["work_card"] = create_github_work_card(spec, output_dir)
            rendered = render_handoff_artifacts(spec, output_dir, created_at)
            ops_card, team_card, ops_text, team_text = handoff_card_payloads(spec)
        except RuntimeError as exc:
            print(f"error: Work Card creation failed: {exc}", file=sys.stderr)
            return 1

    plan = {
        "work_unit_id": spec["work_unit_id"],
        "dry_run": bool(args.dry_run),
        "output_dir": str(output_dir),
        "work_card": spec["work_card"],
        "artifacts": [str(output_dir / filename) for filename in ARTIFACTS],
        "cards": [
            {"surface": "ops-feed", "kind": "ASSIGNED", "target": spec["targets"]["ops_feed"], "path": str(output_dir / "ops-assigned-card.json")},
            {"surface": "team-detail", "kind": "ASSIGNED_DETAIL", "target": spec["targets"]["team_detail"], "path": str(output_dir / "team-assigned-card.json")},
        ],
        "proof_log": str(proof_log),
        "project_sync": {
            "enabled": bool(args.project_sync_field_map),
            "mode": "warning-only mirror",
        },
    }
    if args.dry_run:
        payload = {
            "plan": plan,
            "ops_card": ops_card,
            "team_card": team_card,
            "ops_text": ops_text,
            "team_text": team_text,
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(f"DRY-RUN handoff {spec['work_unit_id']}")
            print(f"- Work Card: {spec['work_card']}")
            print(f"- Artifacts: {output_dir}")
            print("- Publish order: ops-feed ASSIGNED -> team-detail ASSIGNED_DETAIL")
        return 0

    try:
        paths = write_handoff_files(output_dir, rendered, ops_card, team_card, force=args.force)
    except (OSError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    publish_code, publish_payload, publish_error = publish_handoff_sequence(args, spec, paths, proof_log)
    project_sync = {"enabled": False}
    if publish_code == 0:
        project_sync = run_project_sync(args)
        if project_sync.get("enabled") and not project_sync.get("ok"):
            print(f"warning: Project handoff sync failed: {project_sync.get('error')}", file=sys.stderr)
    else:
        print(publish_error or "error: handoff publish failed", file=sys.stderr)

    payload = {
        "plan": plan,
        "paths": paths,
        "publish": publish_payload.get("sequence", []),
        "project_sync": project_sync,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    elif publish_code == 0:
        print(f"OK handoff published: {spec['work_unit_id']} · {spec['team']} · source artifacts + ASSIGNED readbacks")
    return publish_code


def append_progress(args: argparse.Namespace) -> int:
    output_dir = args.output_root.expanduser() / args.work_unit_id
    if not output_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {output_dir}", file=sys.stderr)
        return 1
    if not any((args.phase, args.current_slice, args.round, args.next_checkpoint)):
        print(
            "error: progress requires at least one of --phase, --current-slice, --round, or --next-checkpoint",
            file=sys.stderr,
        )
        return 1
    row = progress_row_from_args(args, transition_at=args.transition_at or utc_now_iso())
    progress_path = append_progress_row(output_dir, row)
    print(f"recorded progress {args.work_unit_id}: {progress_path}")
    return 0


def checkpoint_card_args(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "discord_ops.py"),
        "card",
        "--surface",
        "team-detail",
        "--kind",
        "CHECKPOINT",
        "--work-unit-id",
        args.work_unit_id,
        "--team",
        args.team,
        "--current-slice",
        args.current_slice,
        "--status",
        args.status,
        "--next",
        args.next,
        "--format",
        "json",
    ]
    optional_args = (
        ("--elapsed", args.elapsed),
        ("--next-checkpoint", args.next_checkpoint),
        ("--evidence", args.evidence),
        ("--source", args.source_ref),
    )
    for flag, value in optional_args:
        if value:
            command.extend([flag, value])
    return command


def publish_card(
    args: argparse.Namespace,
    card: dict[str, Any],
    proof_log: Path,
) -> tuple[int, dict[str, Any], str]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        temp_path = Path(handle.name)
        json.dump({"card": card}, handle, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    try:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "discord_ops.py"),
            "publish-card",
            "--card-json",
            str(temp_path),
            "--target",
            args.target,
            "--proof-log",
            str(proof_log),
            "--channel",
            args.channel,
            "--transition-at",
            args.transition_at,
            "--readback-limit",
            str(args.readback_limit),
            "--format",
            "json",
        ]
        if args.account:
            command.extend(["--account", args.account])
        if args.thread_id:
            command.extend(["--thread-id", args.thread_id])
        return run_json_command(command)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def run_project_sync(args: argparse.Namespace) -> dict[str, Any]:
    if not args.project_sync_field_map:
        return {"enabled": False}
    command = [
        sys.executable,
        str(SCRIPT_DIR / "project_sync.py"),
        "project-sync",
        "apply",
        "--work-unit-id",
        args.work_unit_id,
        "--artifact-root",
        str(args.output_root.expanduser()),
        "--field-map",
        args.project_sync_field_map,
        "--audit-log",
        args.project_sync_audit_log,
        "--format",
        "json",
    ]
    if args.project_sync_ledger:
        command.extend(["--ledger", args.project_sync_ledger])
    else:
        command.append("--no-ledger")
    code, parsed, output = run_json_command(command)
    return {
        "enabled": True,
        "ok": code == 0,
        "mode": "apply",
        "returncode": code,
        "summary": parsed.get("summary", {}),
        "error": output if code != 0 else "",
    }


def checkpoint_work_unit(args: argparse.Namespace) -> int:
    output_dir = args.output_root.expanduser() / args.work_unit_id
    if not output_dir.is_dir():
        print(f"error: Work Unit artifact directory not found: {output_dir}", file=sys.stderr)
        return 1
    if not args.dry_run and not args.publish:
        print("error: checkpoint requires --dry-run or --publish", file=sys.stderr)
        return 1
    if args.publish and not args.target:
        print("error: --publish requires --target", file=sys.stderr)
        return 1

    transition_at = args.transition_at or utc_now_iso()
    args.transition_at = transition_at
    proof_log = args.proof_log.expanduser() if args.proof_log else output_dir / DEFAULT_PROOF_LOG_NAME

    card_code, card_payload, card_error = run_json_command(checkpoint_card_args(args))
    if card_code != 0:
        print(f"error: checkpoint card validation failed: {card_error}", file=sys.stderr)
        return 1
    card = card_payload.get("card") or {}
    text = card_payload.get("text") or ""
    if not isinstance(card, dict) or not text:
        print("error: checkpoint card command returned invalid JSON", file=sys.stderr)
        return 1

    preview_row = progress_row_from_args(args, transition_at=transition_at, proof_ref="")
    if args.dry_run:
        payload = {
            "dry_run": True,
            "card": card,
            "text": text,
            "progress_row": preview_row,
            "project_sync": {
                "enabled": bool(args.project_sync_field_map),
                "mode": "skipped",
                "reason": "dry-run does not append progress or mutate Project mirror",
            },
        }
        if args.format == "json":
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(text)
            print(f"\nDRY-RUN checkpoint progress: {preview_row['work_unit_id']} show_round={str(preview_row['show_round']).lower()}")
        return 0

    publish_code, publish_payload, publish_error = publish_card(args, card, proof_log)
    if publish_code != 0:
        print(publish_error or "error: checkpoint publish failed", file=sys.stderr)
        return 1

    proof = publish_payload.get("publish") or {}
    proof_ref = str(proof_log)
    if proof.get("proof_id"):
        proof_ref = f"{proof_ref}#{proof['proof_id']}"
    progress_row = progress_row_from_args(args, transition_at=transition_at, proof_ref=proof_ref)
    progress_path = append_progress_row(output_dir, progress_row)
    project_sync = run_project_sync(args)
    if project_sync.get("enabled") and not project_sync.get("ok"):
        print(f"warning: Project checkpoint sync failed: {project_sync.get('error')}", file=sys.stderr)

    payload = {
        "dry_run": False,
        "publish": publish_payload.get("publish", {}),
        "progress_path": str(progress_path),
        "progress_row": progress_row,
        "project_sync": project_sync,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"recorded checkpoint {args.work_unit_id}: {progress_path}")
    return 0


def render_assignment(context: dict[str, str]) -> str:
    return f"""# Assignment Packet

Status: Draft

The Assignment Packet is the detailed handoff from the Operations Lead to one
Team Lead OpenClaw Agent for a delegated Work Unit.

## Identity

- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Operations Lead: `{context["operations_lead"]}`
- Assigned Team Lead OpenClaw Agent: `{context["team_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Goal

State the single outcome expected from this Work Unit.

## Background

Include only the context needed to execute the Work Unit.

## Scope

What the team lead should do:

-

## Non-goals

What the team lead should not do:

-

## Constraints

- No legacy operating path.
- No fallback source of truth.
- No hidden orchestrator agent.
- No automatic recovery, restart, reassignment, cancellation, or completion.
- Other constraints:

## Inputs

Links, files, references, or starting state:

-

## Done Criteria

The Work Unit can be considered ready for review when:

-

## Verification Criteria

Evidence or checks required for review:

-

## Protocol Capsule

Use this compact execution protocol for this Work Unit. Do not replace this
packet by searching protocol docs or inferring completion criteria from request
prose.

```yaml
protocol_capsule:
  mode: <goal|verify>
  support: []
  loop: <plan -> repeat(act_or_improve -> verify) until stop_only_on, only for goal>
  stop_only_on:
    - done_criteria_passed_with_evidence
    - explicit_blocker
    - safety_or_budget_limit
    - operations_lead_or_user_pause
  ownership: team_lead_owns_execution
  subagents: direct_team_lead_control_only
  result: map_evidence_to_done_and_verification_criteria
  revision_rule: reject_means_reenter_selected_mode
```

For `goal` mode, do not stop after one failed verification. Plan once, then
repeat implementation or improvement and verification until a `stop_only_on`
condition is true.

Planning is required for `goal`, but it should be proportional. Small Work
Units can use a concise 1-3 bullet plan; risky or multi-step Work Units need a
fuller plan.

## Expected Outputs

- Evidence & Result Record:
- PR or artifact:
- Decision-ready summary:

## Reporting Format

The Team Lead should report:

- Result summary.
- Evidence links.
- Checks performed.
- Remaining risks.
- Blockers or missing artifacts.

Discord generation budget:

- Keep Discord-facing result text within 1,600 characters.
- Put detailed logs, diffs, and long findings in the Evidence & Result Record or
  another source artifact.
- If the result needs more room, report the artifact path plus a short decision
  summary instead of pasting full detail into Discord.

## Blocked Rule

If a required input or artifact is missing, report `blocked`. Do not substitute
this packet with a GitHub comment, Discord message, dashboard note, or PR
summary.
"""


def render_claim(context: dict[str, str]) -> str:
    return f"""# Ops Claim Ledger Entry

Status: Draft

The Ops Claim Ledger records expected responsibility. It is not runtime truth,
progress history, evidence storage, a dashboard database, or a recovery system.

## Claim Identity

- Claim ref: `CLAIM-{context["work_unit_id"]}-001`
- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Claim type: `execution`
- Owner session ref: `{context["team_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Expected Responsibility

- Expected state: `assigned`
- Expected until:
- Last claim: Assignment Packet prepared; waiting for `{context["team_lead"]}` execution.
- Last seen compaction count: `unknown`

Allowed expected states:

- `assigned`
- `working`
- `waiting`
- `blocked`
- `result_ready`
- `done`

`done` is not completion truth. It is an expected responsibility state after
the Operations Lead has made a decision.

## Artifact References

- Assignment Packet: `{context["assignment_path"]}`
- Evidence ref: `{context["evidence_path"]}`
- Operations Lead decision ref: `{context["decision_path"]}`

## Staleness Check

If this claim is not refreshed before `expected_until`, the Operations Lead
should review the Work Unit state.

The Pulse Monitor, when implemented, may alert on stale or mismatched claims. It
must not restart, reassign, recover, mutate GitHub, or mark completion.

## Notes

-
"""


def render_evidence(context: dict[str, str]) -> str:
    return f"""# Evidence & Result Record

Status: Draft

The Evidence & Result Record is the proof bundle the Operations Lead uses to
review a Work Unit.

No evidence means no completion.

## Identity

- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Assignment Packet: `{context["assignment_path"]}`
- Team Lead OpenClaw Agent: `{context["team_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Result Summary

Summarize what was completed.

## Evidence

Link only real artifacts or checks that exist.

- PR:
- Test output:
- Reports:
- Sources:
- Screenshots:
- Generated artifacts:
- Review notes:

## Verification Performed

-

## Done Criteria Mapping

For each done criterion, state whether it is met and link evidence.

- Criterion:
  - Status:
  - Evidence:

## Remaining Risks

-

## Open Questions

-

## Team Lead Recommendation

Recommended decision:

- `accept`
- `revise`
- `hold`
- `reject`

Rationale:

## Fallback Rule

Do not treat status claims, Discord messages, dashboard fields, or PR summaries
as evidence unless they link to the real artifact being reviewed.
"""


def render_decision(context: dict[str, str]) -> str:
    return f"""# Operations Lead Decision

Status: Pending

The Operations Lead decision records whether the submitted result satisfies the
Assignment Packet and evidence requirements.

## Identity

- Decision ref: `DECISION-{context["work_unit_id"]}`
- Work Unit id: `{context["work_unit_id"]}`
- Title: {context["title"]}
- Work Card: {context["work_card"]}
- Assignment Packet: `{context["assignment_path"]}`
- Evidence & Result Record: `{context["evidence_path"]}`
- Operations Lead: `{context["operations_lead"]}`
- Created at: `{context["created_at"]}`
- Updated at: `{context["created_at"]}`

## Decision

Choose one:

- `accept`
- `revise`
- `hold`
- `reject`

## Rationale

Explain the decision using the Assignment Packet and Evidence & Result Record.

## Required Follow-up

-

## Closure Instruction

If accepted:

- Link this decision to the Work Card.
- Link the Evidence & Result Record to the Work Card.
- Close the Work Card only after both links exist.

If not accepted:

- Keep the Work Card open.
- Update the Ops Claim Ledger entry with the next expected responsibility.

## No Fallback Rule

This decision must not be inferred from GitHub labels, dashboard status,
Discord messages, or Team Lead claims.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create OpenClaw Company Ops Work Unit artifact files.",
    )
    subparsers = parser.add_subparsers(dest="resource")

    work_unit = subparsers.add_parser("work-unit", help="Manage Work Unit artifacts")
    work_unit_subparsers = work_unit.add_subparsers(dest="action")
    create = work_unit_subparsers.add_parser(
        "create",
        help="Create assignment.md, claim.md, evidence.md, and decision.md",
    )
    create.add_argument("--work-unit-id", required=True, type=work_unit_id)
    create.add_argument("--title", required=True, type=required)
    create.add_argument("--work-card", required=True, type=required)
    create.add_argument("--operations-lead", required=True, type=required)
    create.add_argument("--team-lead", required=True, type=required)
    create.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory that will receive <work-unit-id>/",
    )
    create.add_argument(
        "--created-at",
        type=required,
        help="Creation date to record, default: today's local date",
    )
    create.add_argument(
        "--force",
        action="store_true",
        help="Replace generated artifact files in an existing output directory",
    )
    create.set_defaults(func=create_work_unit)

    handoff = work_unit_subparsers.add_parser(
        "handoff",
        help="Create and optionally publish the initial ASSIGNED handoff bundle",
    )
    handoff.add_argument("--spec", required=True, type=Path, help="Structured handoff JSON fact packet")
    handoff.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory that will receive <work-unit-id>/",
    )
    handoff.add_argument("--created-at", default="", help="Creation timestamp/date, default: now")
    handoff.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    handoff.add_argument("--channel", default="discord", help="OpenClaw message channel")
    handoff.add_argument("--account", default="", help="OpenClaw channel account id")
    handoff.add_argument("--thread-id", default="", help="Optional Discord thread id")
    handoff.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    handoff.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    handoff.add_argument(
        "--project-sync-field-map",
        default="",
        help="Optional Project field-map JSON; runs mirror sync after successful handoff publish",
    )
    handoff.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync; empty disables ledger",
    )
    handoff.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful Project mirror sync",
    )
    handoff.add_argument(
        "--force",
        action="store_true",
        help="Replace generated handoff artifacts in an existing output directory",
    )
    handoff.add_argument("--format", choices=("text", "json"), default="text")
    handoff_mode = handoff.add_mutually_exclusive_group(required=True)
    handoff_mode.add_argument("--dry-run", action="store_true", help="Validate and preview without writes or sends")
    handoff_mode.add_argument("--publish", action="store_true", help="Write artifacts, publish/read back Discord, then sync Project mirror")
    handoff.set_defaults(func=handoff_work_unit)

    progress = work_unit_subparsers.add_parser(
        "progress",
        help="Append source-backed progress metadata for dashboard sync",
    )
    progress.add_argument("--work-unit-id", required=True, type=work_unit_id)
    progress.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory containing <work-unit-id>/",
    )
    progress.add_argument("--transition-kind", default="checkpoint", type=required)
    progress.add_argument(
        "--mode",
        default="",
        help="Progress mode; goal and convergence automatically display round when present",
    )
    progress.add_argument("--phase", default="", help="Current phase label")
    progress.add_argument("--phase-index", default="", help="Current phase number or label")
    progress.add_argument("--phase-total", default="", help="Known total phase count, if any")
    progress.add_argument("--round", default="", help="Current convergence round, if applicable")
    progress.add_argument(
        "--show-round",
        action="store_true",
        help="Display round in dashboard Progress; use for convergence/goal rounds or explicit owner request",
    )
    progress.add_argument("--current-slice", default="", help="Current execution slice")
    progress.add_argument("--next-checkpoint", default="", help="Next expected checkpoint time/window")
    progress.add_argument("--source-ref", default="", help="Source artifact reference for this progress update")
    progress.add_argument("--proof-ref", default="", help="Optional proof log or Discord proof reference")
    progress.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    progress.add_argument("--recorded-by", default="operations-lead", help="Recorder identity")
    progress.set_defaults(func=append_progress)

    checkpoint = work_unit_subparsers.add_parser(
        "checkpoint",
        help="Publish a team CHECKPOINT and record matching source-backed progress",
    )
    checkpoint.add_argument("--work-unit-id", required=True, type=work_unit_id)
    checkpoint.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory containing <work-unit-id>/",
    )
    checkpoint.add_argument("--team", required=True, type=required)
    checkpoint.add_argument("--status", required=True, type=required)
    checkpoint.add_argument("--current-slice", required=True, type=required)
    checkpoint.add_argument("--next", required=True, type=required, help="Discord next action")
    checkpoint.add_argument("--elapsed", default="", help="Elapsed time or progress age")
    checkpoint.add_argument("--next-checkpoint", default="", help="Next expected checkpoint time/window")
    checkpoint.add_argument("--evidence", default="", help="Optional checkpoint evidence")
    checkpoint.add_argument("--source-ref", default="", help="Source artifact reference for this checkpoint")
    checkpoint.add_argument("--transition-kind", default="checkpoint", type=required)
    checkpoint.add_argument(
        "--mode",
        default="",
        help="Progress mode; goal and convergence automatically display round when present",
    )
    checkpoint.add_argument("--phase", default="", help="Current phase label for dashboard Progress")
    checkpoint.add_argument("--phase-index", default="", help="Current phase number or label")
    checkpoint.add_argument("--phase-total", default="", help="Known total phase count, if any")
    checkpoint.add_argument("--round", default="", help="Current convergence round, if applicable")
    checkpoint.add_argument(
        "--show-round",
        action="store_true",
        help="Force round display in dashboard Progress",
    )
    checkpoint.add_argument("--proof-ref", default="", help=argparse.SUPPRESS)
    checkpoint.add_argument("--transition-at", default="", help="UTC ISO timestamp, default: now")
    checkpoint.add_argument("--recorded-by", default="operations-lead", help="Recorder identity")
    checkpoint.add_argument(
        "--proof-log",
        type=Path,
        help=f"JSONL proof log path, default: <work-unit-id>/{DEFAULT_PROOF_LOG_NAME}",
    )
    checkpoint.add_argument("--target", default="", help="Discord target for --publish")
    checkpoint.add_argument("--channel", default="discord", help="OpenClaw message channel")
    checkpoint.add_argument("--account", default="", help="OpenClaw channel account id")
    checkpoint.add_argument("--thread-id", default="", help="Optional Discord thread id")
    checkpoint.add_argument("--readback-limit", type=int, default=10, help="Recent message count for readback")
    checkpoint.add_argument(
        "--project-sync-field-map",
        default="",
        help="Optional Project field-map JSON; runs mirror sync after successful publish",
    )
    checkpoint.add_argument(
        "--project-sync-ledger",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "claims" / "ledger.json"),
        help="Ledger passed to project-sync; empty disables ledger",
    )
    checkpoint.add_argument(
        "--project-sync-audit-log",
        default=str(Path.home() / ".openclaw" / "state" / "openclaw-company-ops" / "project-sync-audit.jsonl"),
        help="Audit log for successful Project mirror sync",
    )
    checkpoint.add_argument("--format", choices=("text", "json"), default="text")
    mode_group = checkpoint.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true", help="Validate and preview without writes or sends")
    mode_group.add_argument("--publish", action="store_true", help="Publish/read back Discord, append progress, then sync Project mirror")
    checkpoint.set_defaults(func=checkpoint_work_unit)
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
