---
name: implementation-verification
description: Verify a Spec2Ship implementation with project-native checks and per-criterion evidence, never reporting unknown or LLM-only results as passed. Use in /spec2ship-verify and /spec2ship-review.
---

# Implementation verification

Layers: task completion (Harness markers) → code review → static checks → unit tests → integration/API tests →
build → acceptance criteria → traceability audit → optional visual check.

## Status vocabulary

`PASS` (automated check or developer-confirmed manual check with evidence), `REVIEWED` (LLM/code reading only),
`FAIL`, `BLOCKED`, `NOT_RUN`, `NOT_APPLICABLE`. The CLI refuses PASS without evidence, PASS with a non-zero exit
code, and converts LLM-review PASS to REVIEWED.

## Procedure

1. Commands come from `analysis/repository-analysis.json` (`commands.lint`, `typecheck`, `test`, `build`). If a
   command is missing, the layer is NOT_RUN — do not invent one. Ask the developer if a command is unclear.
2. Run checks with the Bash tool from the project root; keep logs under `.spec2ship/verification/logs/`.
   Never run deploys, production migrations, or commands needing secrets.
3. Map each acceptance criterion to the test(s) that exercise it: read the test code, confirm it asserts the
   criterion's `then`, and confirm the test ran and passed in this session's output. Record the file and test name.
4. A test that exists but was not run, or was skipped, is NOT_RUN. A flaky or failing test is FAIL.
5. Visual verification (optional): compare `get_screenshot` of the Figma node with the running UI only if the
   developer provides a running app URL; record `--method visual` as REVIEWED unless a deterministic visual test ran.
6. Traceability audit: `spec2ship.py report`, then check `metrics.unmapped_to_tasks`, `metrics.orphan_tasks`, and
   requirements implemented but not verified. List them explicitly.
