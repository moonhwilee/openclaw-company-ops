# Company Ops Capacity Policy

Status: active operating policy

This document is the source of truth for Company Ops capacity sizing. Phase
documents may reference it, but the policy is not phase-specific.

## Scope

Company Ops capacity has two layers:

- OpenClaw host recommendations, which are read-only preflight checks unless
  an operator explicitly applies OpenClaw config changes.
- Company Ops runtime rules, which limit Company Ops' own dispatch behavior.

Company Ops must not silently mutate OpenClaw global config, restart Gateway,
enforce session cleanup, install hook/tool limits for subagents, or create a
hidden scheduler to bypass these limits.

## Agent Count

The sizing input is the Company Ops active OpenClaw agent count:

```text
company_ops_agent_count = operations_lead_count + team_lead_count
```

The current package baseline is:

- Operations Lead: 1
- Team Leads: 4
- Company Ops active OpenClaw agent count: 5

Installed but idle agent definitions do not count unless they are intended to
operate as active Company Ops agents.

## OpenClaw Host Recommendations

Recommended host values:

```text
agents.defaults.maxConcurrent = max(8, company_ops_agent_count * 2)
agents.defaults.subagents.maxConcurrent = max(16, company_ops_agent_count * 4)
```

For the current Company Ops baseline:

```text
agents.defaults.maxConcurrent = max(8, 5 * 2) = 10
agents.defaults.subagents.maxConcurrent = max(16, 5 * 4) = 20
```

These are host-wide OpenClaw settings. Setup, doctor, or preflight may read the
current values and warn when they are lower than recommended. They must not
change them automatically.

If a config change is desired, the operator must apply it explicitly. Any
Gateway restart follows the workspace Gateway restart preflight and explicit
approval policy.

## Company Ops Active Work Unit Cap

Company Ops dispatch uses this derived cap:

```text
company_ops_active_wu_cap = max(1, effective_maxConcurrent - 2)
```

The two reserved slots are for the Operations Lead main session, owner
requests, result-ready/closeout handling, hooks, and exceptional operating
work.

For the current recommended OpenClaw value:

```text
company_ops_active_wu_cap = 10 - 2 = 8
```

Dispatch admission is fail-closed when the cap is full. A capacity-full dispatch
must not write `dispatch.json`, append a `dispatched` progress row, mutate a
Project mirror, publish closeout, or spawn a hidden recovery path.

The active Work Unit count is derived from source artifacts under the configured
artifact root. OpenClaw sessions, Telegram/Discord messages, GitHub Project
fields, and GitHub comments are advisory mirrors, not capacity truth.

Closeout delegate wake has a separate small foreground cap because delegated
audit also consumes fresh OpenClaw execution slots and must leave room for main
Operations Lead exceptions. The initial cap is 2 active delegate wakes. When
the cap is full, `work-unit review-wake --publish` must return
`review-wake capacity-full`, write no wake record, and leave the Work Unit
recoverable through `work-unit inbox --result-ready`. Do not add a daemon,
hidden queue, retry worker, or fake closeout to work around this cap.

## Subagent Budget

The Assignment Packet and package prompt carry the subagent budget. It is a
Team Lead instruction contract, not a hook/tool policy or runtime hard
enforcement layer.

Allowed budgets:

- `none`: Team Lead handles the Work Unit directly.
- `2`: simple delegated work.
- `3`: normal goal/verify work.
- `5`: complex, high-risk, or broad verification work.

More than `5` requires explicit Operations Lead or owner approval.

Team Leads should report actual subagent usage in the Evidence & Result Record
when they use subagents. Subagent output is input for Team Lead judgment; it is
not completion truth.

## Session Maintenance

Company Ops does not implement session deletion. Session cleanup belongs to
OpenClaw host maintenance.

Company Ops preflight may report session maintenance status and recommend an
OpenClaw dry-run cleanup, but it must not run `openclaw sessions cleanup
--enforce`, set `session.maintenance.mode = enforce`, or delete session records
during package setup.
