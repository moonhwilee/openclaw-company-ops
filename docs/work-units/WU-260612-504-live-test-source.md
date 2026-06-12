# WU-260612-504 Live Test Source

Status: Source

## Purpose

Exercise a small goal-mode Work Unit after the P3-lite source-index merge.

## Goal

Create one small source-local live-test note under the Work Unit artifact
directory that explains, in plain language, how closeout should use
`closeout-source-index.json`.

## Required Checks

- The note must say the index is a source pointer map, not source truth.
- The note must say stale, missing, or mismatched index state requires direct
  source artifact inspection.
- The note must say the index must not make accept/revise/block judgments.
- Evidence must map every done criterion and verification criterion.

## Allowed Output

- `docs/work-units/WU-260612-504/p3-lite-operator-note.md`

## Non-goals

- Do not edit repo runtime code.
- Do not edit global docs.
- Do not commit or push.
