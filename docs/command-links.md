# Command Links

Status: repo-local owner-facing command surface

Company Ops uses a namespaced owner command surface so it does not conflict
with native OpenClaw or Codex slash commands such as `/goal`, `/plan`,
`/review`, or `/status`.

The repo-local entrypoint is:

```bash
python3 scripts/openclaw_company_ops.py ops <command> ...
```

In an OpenClaw or Telegram package, the owner-facing slash command should map
to the same entrypoint:

```text
/ops <command> ...
```

Telegram command menus may expose short aliases when subcommands are not
discoverable enough:

- `/ops_goal` -> `/ops goal`
- `/ops_verify` -> `/ops verify`
- `/ops_status` -> `/ops status`

The canonical command remains `/ops`; aliases are convenience links only.

## Owner Commands

### `/ops goal <request>`

Draft a goal-mode Work Unit handoff from an owner request.

Repo-local form:

```bash
python3 scripts/openclaw_company_ops.py ops goal "Improve the onboarding report"
```

The command writes nothing by itself. It calls the guarded
`work-unit draft-handoff --dry-run` path and returns a Work Card draft,
Assignment Packet draft, missing Operations Lead decisions, and a completed
handoff spec candidate when enough structured fields are supplied.

Useful options:

- `--team <agent>` assigns the Team Lead.
- `--ops-target <target>` and `--team-target <target>` fill visibility targets.
- `--source-ref <ref>` may be repeated for concrete source truth.
- `--done-criteria <text>` and `--verification-criteria <text>` may be repeated.
- `--format json` returns machine-readable output.

### `/ops verify <target-or-request>`

Draft a verify-mode Work Unit handoff.

Repo-local form:

```bash
python3 scripts/openclaw_company_ops.py ops verify "Verify docs/report.md" --source-ref docs/report.md
```

The generated verify draft is read-only with respect to the candidate output.
It may write verification artifacts only after Operations Lead review and
normal Work Unit handoff.

### `/ops status <work-unit-id>`

Show source-backed status for one Work Unit.

```bash
python3 scripts/openclaw_company_ops.py ops status WU-260606-001
```

This is read-only and routes to `status work-unit`.

### `/ops inbox`

Show source-backed Work Units ready for Operations Lead review.

```bash
python3 scripts/openclaw_company_ops.py ops inbox
```

This is read-only and routes to `work-unit inbox --result-ready`.

### `/ops decide <work-unit-id>`

Preview or publish a guarded Operations Lead decision.

```bash
python3 scripts/openclaw_company_ops.py ops decide WU-260606-001 --decision accept --dry-run
```

The default is dry-run. Use `--publish` only when the normal closeout criteria,
source evidence, and visibility/project requirements are satisfied.

### `/ops preflight`

Run foreground setup and readiness checks.

```bash
python3 scripts/openclaw_company_ops.py ops preflight --format json
```

This is read-only. It checks capacity and optional configured Project/Discord
readiness without granting scopes, creating resources, or mutating source
artifacts.

## Non-Goals

The `/ops` router is not a hidden orchestrator, protocol runtime, classifier,
background watcher, source of truth, Team Lead executor, or automatic closeout
path. It only maps owner-facing intent into existing foreground Company Ops
commands.

Native `/goal` remains reserved for the surrounding OpenClaw/Codex session goal
feature. Company Ops uses `protocol_capsule.mode: goal` inside Assignment
Packets, not the global `/goal` command.
