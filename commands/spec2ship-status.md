---
description: Show the current Spec2Ship run state, artifacts, approval, Harness progress, blockers and the next step
argument-hint: (no arguments)
---

# /spec2ship-status

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec2ship.py" status` (use `python` on Windows if needed) from the
project root and present it briefly:

- run id and workflow state
- artifacts present / missing
- approval: approved? still current (no edits since approval)?
- Harness: Plans.md path, task markers (TODO / WIP / done / blocked), drift status
- changed or missing BA inputs since the run started
- blockers
- the single recommended next command

Resuming is safe: every command re-checks prerequisites. Do not change anything in this command.
