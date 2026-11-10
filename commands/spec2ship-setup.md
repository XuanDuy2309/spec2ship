---
description: Check Spec2Ship prerequisites (Python, PDF extractor, claude-code-harness, figma-mcp-go config and Figma Desktop bridge) and explain fixes
argument-hint: (no arguments)
---

# /spec2ship-setup

`S2S` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec2ship.py"` (use `python` on Windows if needed).

1. Run `S2S preflight` from the project root (results are saved to the run only when a run exists). Show every
   line, grouped OK / WARN / FAIL, with the suggested fix.
2. Check the Figma bridge yourself: call `mcp__plugin_spec2ship_figma-mcp-go__get_metadata` (Spec2Ship bundles the
   figma-mcp-go server; Claude Code starts it with the plugin — the developer does not need `claude mcp add`).
   - Tool not available → the bundled server failed to start: usually Node.js 18+/npx missing (see `node-runtime`
     in preflight) or no network for the first `npx` download. Check `/mcp`, fix, restart Claude Code.
   - Error `plugin not connected` → Figma Desktop is closed or the figma-mcp-go plugin is not running. Steps:
     download `plugin.zip` from the figma-mcp-go releases page, Figma Desktop → Plugins → Development →
     Import plugin from manifest → select `manifest.json`, then run the plugin inside the design file.
   - Success → report the open file name and current page.
   If a run exists, record the outcome with `S2S figma-check ...` (see /spec2ship step 4).
3. Do **not** install anything, edit settings, or add MCP servers yourself. Print the exact commands for the
   developer to run, for example:
   - `/plugin marketplace add Chachamaru127/claude-code-harness` and
     `/plugin install claude-code-harness@claude-code-harness-marketplace`
   - Node.js 18+ from https://nodejs.org if `node-runtime` failed (needed by the bundled figma-mcp-go server)
   If preflight reports `figma-mcp-duplicate`, the developer's own figma-mcp-go entry can stay (instances share one
   leader on 127.0.0.1:1994) or be removed; do not remove it yourself.
4. Summarize: READY / READY WITH WARNINGS / BLOCKED, and the next command (`/spec2ship <figma-url> --ba <path>`).
