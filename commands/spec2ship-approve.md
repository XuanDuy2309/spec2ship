---
description: Developer-only — approve the reviewed Spec2Ship plan by its hash (Claude cannot invoke this)
argument-hint: <plan-hash> [--accept-open-questions]
disable-model-invocation: true
---

# /spec2ship:spec2ship-approve

The developer typed this command to approve a plan. Arguments: `$ARGUMENTS`.

`S2S` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec2ship.py"`.

1. If no hash was given, run `S2S status`, explain that approval needs the hash shown at plan review, and stop.
2. Run `S2S approve <hash> [--accept-open-questions]` exactly with the developer's arguments. Do not add
   `--accept-open-questions` unless the developer typed it. Do not retry with a different hash.
3. On error (hash mismatch, invalid artifacts, blocking questions, missing intent) show the message and the fix.
   Do not work around it.
4. On success, confirm who approved what (plan hash, time) and state the next step: `/spec2ship-work` hands the
   approved tasks to claude-code-harness. Do not start it automatically.
