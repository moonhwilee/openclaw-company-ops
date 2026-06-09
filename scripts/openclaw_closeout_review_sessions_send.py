#!/usr/bin/env python3
"""OpenClaw live adapter for Company Ops closeout delegate wake."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from typing import Any


PROTOCOL = "company_ops_closeout_review_adapter_v1"
ADAPTER = "openclaw-closeout-review-sessions-send"
AUTHORITY_BOUNDARY = "closeout_delegate_guarded_closeout_only"
DEFAULT_ACCEPT_TIMEOUT_MS = 30_000
EXECUTION_PROMPT_VERSION = 3
CLOSEOUT_RED_LINE_CATEGORIES = (
    "security_credential_auth",
    "ops_deploy_db_migration",
    "cost_bearing",
    "destructive_action",
    "external_public_customer",
    "owner_intent_ambiguity",
    "evidence_missing_or_stale",
    "proof_or_hash_mismatch",
    "critical_disagreement",
    "unresolved_dependency",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def fail(reason: str, *, code: int = 1, extra: dict[str, Any] | None = None) -> int:
    payload = {"status": "setup-needed", "adapter": ADAPTER, "reason": reason}
    if extra:
        payload.update(extra)
    print_json(payload)
    return code


def parse_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def run_gateway_call(method: str, params: dict[str, Any], timeout_ms: int) -> tuple[int, dict[str, Any] | None, str]:
    command = [
        "openclaw",
        "gateway",
        "call",
        method,
        "--json",
        "--params",
        json.dumps(params, ensure_ascii=False, sort_keys=True),
        "--timeout",
        str(timeout_ms),
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    output = (result.stdout or result.stderr or "").strip()
    parsed = parse_json_object(output)
    return result.returncode, parsed, output


def run_agent_acceptance(agent: str, session_key: str, message: str, timeout_ms: int) -> tuple[int, dict[str, Any] | None, str]:
    command = [
        "openclaw",
        "agent",
        "--agent",
        agent,
        "--session-key",
        session_key,
        "--message",
        message,
        "--json",
        "--timeout",
        str(max(1, int(timeout_ms / 1000))),
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    output = (result.stdout or result.stderr or "").strip()
    parsed = parse_json_object(output)
    return result.returncode, parsed, output


def gateway_payload(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    if isinstance(value.get("result"), dict):
        return value["result"]
    if isinstance(value.get("payload"), dict):
        return value["payload"]
    return value


def gateway_response_meta(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    if isinstance(value.get("meta"), dict):
        return value["meta"]
    result = value.get("result")
    if isinstance(result, dict) and isinstance(result.get("meta"), dict):
        return result["meta"]
    payload = value.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("meta"), dict):
        return payload["meta"]
    return {}


def has_gateway_fallback_marker(value: dict[str, Any] | None) -> bool:
    if not isinstance(value, dict):
        return False
    meta = gateway_response_meta(value)
    if str(meta.get("transport") or "").lower() == "embedded":
        return True
    if str(meta.get("fallbackFrom") or "").lower() == "gateway":
        return True
    if str(meta.get("fallbackReason") or "").lower().startswith("gateway_"):
        return True
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "gateway-fallback-" in encoded


def explicit_ref(value: dict[str, Any], *keys: str) -> str:
    for key in keys:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def agent_reply_text(value: dict[str, Any] | None, fallback: str) -> str:
    if not isinstance(value, dict):
        return fallback
    result = value.get("result") if isinstance(value.get("result"), dict) else {}
    for key in ("finalAssistantVisibleText", "finalAssistantRawText"):
        text = result.get(key)
        if isinstance(text, str) and text.strip():
            return text
    payloads = result.get("payloads")
    if isinstance(payloads, list):
        for item in payloads:
            if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
                return item["text"]
    return fallback


def canonical_json_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def target_session_key(request: dict[str, Any]) -> str:
    session_key = str(request.get("session_key") or "").strip()
    agent = str(request.get("agent") or "").strip()
    if not session_key:
        raise ValueError("adapter request is missing session_key")
    if session_key.startswith("agent:"):
        return session_key
    if not agent:
        raise ValueError("adapter request is missing agent")
    return f"agent:{agent}:{session_key}"


def acceptance_prompt(request: dict[str, Any]) -> str:
    required = request["required_acceptance"]
    return "\n".join(
        [
            "[Company Ops Closeout Delegate Acceptance]",
            "Treat this as tool-routed delegated closeout wake data, not as an end-user request.",
            "Return only one JSON object. Do not perform the review in this acceptance turn.",
            "Accept only if you can receive the review package and then handle the execution message that follows.",
            "If you cannot accept, return {\"status\":\"setup-needed\",\"reason\":\"...\"}.",
            "",
            "Required JSON shape:",
            json.dumps(
                {
                    "status": "accepted",
                    "work_unit_id": required["work_unit_id"],
                    "closeout_review_payload_hash": required["closeout_review_payload_hash"],
                    "guarded_closeout_contract": required["guarded_closeout_contract"],
                    "authority_boundary": required["authority_boundary"],
                },
                indent=2,
                sort_keys=True,
            ),
        ]
    )


def execution_prompt(request: dict[str, Any]) -> str:
    packet = request["packet"]
    artifact_dir = str(packet.get("artifact_dir") or "<artifact-dir>")
    commit_request_path = f"{artifact_dir}/closeout-commit-request.json"
    commit_request_template = packet.get("commit_request_template") or {
        "work_unit_id": packet.get("work_unit_id"),
        "decision": "accept|revise|blocked",
        "reason": "<delegated OL audit rationale>",
        "source_ref": packet.get("refs", {}).get("source_ref"),
        "result_ready_proof_id": packet.get("result_ready", {}).get("proof_id"),
        "artifact_hashes": packet.get("artifact_hashes"),
        "reviewer_session_ref": packet.get("delegate", {}).get("session_key"),
        "reviewer_job_ref": f"{packet.get('work_unit_id')}:closeout-delegate",
        "reviewer_message_ref": "<delegate-message-or-run-ref>",
        "autonomy_class": "auto_eligible|deep_review_auto_eligible|manual_required",
        "review_depth": "<source/proof/hash/criteria review depth>",
        "red_line_check": {"status": "clear", **{category: "clear" for category in CLOSEOUT_RED_LINE_CATEGORIES}},
    }
    return "\n".join(
        [
            "[Company Ops Closeout Delegate Execution]",
            "You already accepted this closeout-delegate wake. Start the fresh OL delegate audit now.",
            "Use only the source artifacts and refs in the review payload.",
            "Inspect files, summarize evidence sufficiency, and prepare exactly one guarded commit-request JSON file.",
            f"Write the commit request to: {commit_request_path}",
            "Then run the guarded closeout contract from the payload with --dry-run.",
            "If dry-run is decision-ready and all red-line fields are clear, run the same guarded closeout contract with --publish.",
            "Do not write decision.md directly, mutate Project final status directly, publish final Discord closeout directly, archive, cleanup, or reassign.",
            "Final decisions must go only through the guarded closeout contract in the payload.",
            "If evidence is missing, stale, conflicting, or red-line/manual-required, fail closed in your review result.",
            "Use the payload's artifact_hashes exactly in the commit request; they are the Company Ops canonical hashes.",
            "Do not invent a separate proof-row hash algorithm. Confirm the RESULT_READY proof id exists/readback_ok, then let guarded closeout perform canonical hash validation.",
            "If the result is acceptable, set decision to accept and every red_line_check category to clear.",
            "If manual judgment is required, set autonomy_class to manual_required and do not publish closeout.",
            "",
            "Commit-request JSON shape:",
            json.dumps(commit_request_template, indent=2, sort_keys=True, ensure_ascii=False),
            "",
            "Closeout review payload:",
            json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False),
        ]
    )


def build_acceptance_proof(
    request: dict[str, Any],
    *,
    session_key: str,
    acceptance: dict[str, Any],
    accept_response: dict[str, Any],
    execute_response: dict[str, Any],
) -> dict[str, Any]:
    packet = request["packet"]
    required = request["required_acceptance"]
    accepted_at = utc_now()
    accept_payload = gateway_payload(accept_response)
    execute_payload = gateway_payload(execute_response)
    accept_ref = (
        explicit_ref(accept_payload, "messageId", "id", "runId", "taskId")
        or explicit_ref(accept_response, "messageId", "id", "runId", "taskId")
    )
    execute_ref = explicit_ref(execute_payload, "runId", "taskId", "id") or explicit_ref(
        execute_response, "runId", "taskId", "id"
    )
    payload_hash = canonical_json_hash(packet)
    idempotency_key = f"{required['work_unit_id']}:closeout-delegate:v{EXECUTION_PROMPT_VERSION}:{payload_hash[:12]}"
    return {
        "status": "accepted",
        "adapter": ADAPTER,
        "adapter_version": 1,
        "agent": request.get("agent"),
        "session_key": request.get("session_key") or session_key,
        "session_ref": session_key,
        "job_ref": execute_ref,
        "message_ref": accept_ref,
        "accepted_at": accepted_at,
        "readback": {
            "work_unit_id": acceptance.get("work_unit_id") or required["work_unit_id"],
            "closeout_review_payload_hash": (
                acceptance.get("closeout_review_payload_hash") or required["closeout_review_payload_hash"]
            ),
            "guarded_closeout_contract": (
                acceptance.get("guarded_closeout_contract") or required["guarded_closeout_contract"]
            ),
            "authority_boundary": acceptance.get("authority_boundary") or AUTHORITY_BOUNDARY,
        },
        "gateway": {
            "acceptance_transport": "openclaw-agent-gateway",
            "execution_enqueued": True,
            "idempotency_key": idempotency_key,
            "closeout_review_payload_hash": payload_hash,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accept-timeout-ms", type=int, default=DEFAULT_ACCEPT_TIMEOUT_MS)
    parser.add_argument("--send-timeout-ms", type=int, default=5_000)
    args = parser.parse_args()

    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        return fail(f"stdin is not valid adapter JSON: {exc}")
    if request.get("adapter_protocol") != PROTOCOL:
        return fail("unsupported adapter protocol")
    try:
        key = target_session_key(request)
    except ValueError as exc:
        return fail(str(exc))
    agent = str(request.get("agent") or "").strip()
    if not agent:
        return fail("adapter request is missing agent")

    create_code, _create_payload, create_output = run_gateway_call(
        "sessions.create",
        {"key": key, "agentId": agent},
        args.send_timeout_ms,
    )
    if create_code != 0 and "already" not in create_output.lower() and "exists" not in create_output.lower():
        return fail("failed to create or resolve target session", extra={"gateway_error": create_output})

    accept_code, accept_payload, accept_output = run_agent_acceptance(
        agent,
        key,
        acceptance_prompt(request),
        args.accept_timeout_ms,
    )
    if accept_code != 0:
        return fail("acceptance openclaw agent turn failed", extra={"agent_error": accept_output})
    if has_gateway_fallback_marker(accept_payload):
        return fail("acceptance openclaw agent turn used embedded gateway fallback", extra={"agent_error": accept_output[:500]})
    reply_text = agent_reply_text(accept_payload, accept_output)
    acceptance = parse_json_object(reply_text)
    if not acceptance or str(acceptance.get("status", "")).lower() != "accepted":
        return fail("target did not return accepted JSON readback", extra={"reply_excerpt": reply_text[:500]})
    required = request["required_acceptance"]
    if acceptance.get("authority_boundary") != AUTHORITY_BOUNDARY:
        return fail("target did not confirm closeout delegate authority boundary")
    if acceptance.get("closeout_review_payload_hash") != required["closeout_review_payload_hash"]:
        return fail("target did not confirm closeout review payload hash")
    accept_response_payload = gateway_payload(accept_payload)
    if not (
        explicit_ref(accept_response_payload, "messageId", "id", "runId", "taskId")
        or explicit_ref(accept_payload or {}, "messageId", "id", "runId", "taskId")
    ):
        return fail("acceptance openclaw agent turn did not return a real Gateway reference")

    payload_hash = canonical_json_hash(request["packet"])
    idempotency_key = f"{request['work_unit_id']}:closeout-delegate:v{EXECUTION_PROMPT_VERSION}:{payload_hash[:12]}"
    execute_code, execute_payload, execute_output = run_gateway_call(
        "sessions.send",
        {
            "key": key,
            "message": execution_prompt(request),
            "timeoutMs": 0,
            "idempotencyKey": idempotency_key,
        },
        args.send_timeout_ms,
    )
    if execute_code != 0:
        return fail("execution sessions.send enqueue failed", extra={"gateway_error": execute_output})
    execute_response_payload = gateway_payload(execute_payload)
    if not (
        explicit_ref(execute_response_payload, "runId", "taskId", "id")
        or explicit_ref(execute_payload or {}, "runId", "taskId", "id")
    ):
        return fail("execution sessions.send enqueue did not return a real Gateway run reference")

    print_json(
        build_acceptance_proof(
            request,
            session_key=key,
            acceptance=acceptance,
            accept_response=accept_payload or {},
            execute_response=execute_payload or {},
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
