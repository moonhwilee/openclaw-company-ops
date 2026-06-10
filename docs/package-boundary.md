# Package Boundary

Status: repo-local boundary contract

This repository is the Company Ops development workspace. It is not itself the
installable package root yet.

Until Phase 6 creates the installable layout, package work must treat this repo
as a source workspace with three different surfaces:

- Development surface: implementation, protocol docs, templates, hooks, tests,
  and setup notes used to build and verify Company Ops.
- Package source surface: the subset of files that should be copied or moved
  into the future plugin/package.
- Local state surface: current Work Unit evidence and machine-local state that
  must never be exported as reusable package content.

## Current Package Source Surface

The future public-v1 package/plugin should be assembled from these repo-local
surfaces, subject to Phase 6 manifest review:

- `scripts/`: supported foreground CLI and source-backed helper modules.
- `.codex/hooks/`: optional hook guard code and related configuration, if the
  package keeps the hook surface.
- `docs/protocols/`: Team Lead and recovery protocol references.
- `docs/templates/`: Assignment Packet, Evidence & Result Record, Operations
  Lead decision, Work Card, progress, and Team Playbook templates.
- `docs/architecture.md`, `docs/operations-manual.md`,
  `docs/setup-guide.md`, `docs/implementation-setup-guide.md`,
  `docs/capacity-policy.md`, `docs/company-dashboard-timing.md`,
  `docs/discord-event-visibility.md`, and
  `docs/role-persona-packages.md` after public-install sanitization.
- `README.md`, `LICENSE`, `.github/ISSUE_TEMPLATE/`, and small package-facing
  examples that do not include private owner context.

This list is a boundary guide, not a generated manifest. Phase 6 should turn it
into an explicit package manifest or export script and verify the resulting
layout from a clean install.

## Excluded From Package Export

These paths are local development or operating state and must not be included in
public-v1 package exports:

- `docs/work-units/WU-*/`: concrete Assignment Packets, claims, progress logs,
  visibility proof logs, evidence, decisions, and closeout stage artifacts.
- `docs/work-units/*-handoff-spec.json`: concrete handoff drafts.
- `docs/phase-*`, historical stabilization plans, and long realization plans
  unless a section is deliberately promoted into current package docs.
- Local runtime/cache/state directories such as `runtime/`, `state/`, `logs/`,
  `tmp/`, `.cache/`, `dist/`, and `build/`.
- Machine-local auth, environment, token, or private owner memory files.
- Live GitHub Project/Discord proof artifacts that are evidence for this repo's
  dogfood runs rather than reusable examples.

`docs/work-units/README.md` is included because it documents the local artifact
root. Concrete `WU-*` directories are excluded because they are per-run source
truth, not package instructions.

## Repo Cleanup Timing

Do not restructure the repo into a package layout before the current Company Ops
implementation is accepted. During the remaining implementation phase, keep
changes small:

1. Maintain this package boundary document.
2. Keep concrete Work Unit artifacts out of git and package exports.
3. Label docs as current, planning, or historical when ambiguity causes
   confusion.
4. Continue verifying the repo-local CLI and smoke tests in place.

After implementation acceptance, Phase 6 should create the actual clean package
root or export script, then prove it with a clean-install smoke.

## Completion Gate For Phase 6

Phase 6 packaging is not complete until all of these are true:

- A manifest or export script identifies every file in the installable surface.
- The exported package excludes concrete Work Unit artifacts and local state.
- A clean OpenClaw runtime can discover the bundled Company Ops skill/plugin.
- The packaged foreground CLI can run setup/preflight/smoke without relying on
  this development repo's chat memory.
- Team Lead and Operations Lead setup prompts receive the same packaged protocol
  docs, templates, and context-recovery package prompt.
