---
description: Run project-native checks and acceptance verification, record evidence, and produce the RTM and delivery report
argument-hint: (no arguments)
---

# /spec2ship-verify

`S2S` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec2ship.py"`. Load the `implementation-verification` skill.

1. `S2S status`; require REVIEW or VERIFICATION with a current approval. If REVIEW, `S2S transition VERIFICATION`.
2. Read `analysis/repository-analysis.json` → `commands`. Run only project-native commands that exist
   (lint, typecheck, test, build). Never assume npm or a framework. Do not run deploy, migrations against real
   databases, or anything touching production. Save long output to `.spec2ship/verification/logs/<name>.log`.
   Record each with `S2S record-check --name ... --layer static|unit|integration|build --command "..." --exit-code N --status PASS|FAIL|NOT_RUN --log-file ...`.
   A layer with no command is `NOT_RUN` (or `NOT_APPLICABLE` with a reason) — never PASS.
3. For every acceptance criterion of every in-scope requirement, record exactly one current result:
   - automated test that exercises it and passed → `S2S record-evidence --criterion AC-... --status PASS --method unit-test|integration-test|e2e-test --file <test file> --test "<test name>"` (or `--command ... --exit-code 0`)
   - human-confirmed → `--method manual --note "<who verified what>"` only if the developer confirms it in chat
   - checked only by reading code → `--method llm-review --status REVIEWED`
   - failing → `--status FAIL`; cannot be checked → `NOT_RUN` or `BLOCKED` with `--note`.
   If a criterion lacks a test, you may propose adding one through Harness (`/spec2ship-work`), not directly.
4. `S2S report` → `reports/report.md` and `mappings/rtm.json`. Present the report: verified, implemented-not-verified,
   blocked, deferred listed separately; checks with real statuses; metrics (never a single % score).
5. If everything in scope is verified: `S2S transition COMPLETED`. If not, either go back to work
   (`S2S transition EXECUTION` — retry limit enforced) or `S2S transition BLOCKED --reason "..."` and ask the developer.
