---
description: Check Spec2Ship prerequisites (Python, PDF extractor, claude-code-harness, figma-mcp-go config and Figma Desktop bridge) and explain fixes
argument-hint: (no arguments)
---

# /spec2ship-setup

`S2S` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec2ship.py"` (use `python` on Windows if needed).

1. Run `S2S preflight` from the project root (results are saved to the run only when a run exists). Show every
   line, grouped OK / WARN / FAIL, with the suggested fix.
2. Check the Figma bridge yourself: call the figma-mcp-go `get_metadata` tool (e.g. `mcp__figma-mcp-go__get_metadata`).
   - Tool not available → the MCP server is not configured or not approved; show the `claude mcp add` fix from
     preflight and tell the developer to restart Claude Code / approve the project MCP server.
   - Error `plugin not connected` → Figma Desktop is closed or the figma-mcp-go plugin is not running. Steps:
     download `plugin.zip` from the figma-mcp-go releases page, Figma Desktop → Plugins → Development →
     Import plugin from manifest → select `manifest.json`, then run the plugin inside the design file.
   - Success → report the open file name and current page.
   If a run exists, record the outcome with `S2S figma-check ...` (see /spec2ship step 4).
3. Do **not** install anything, edit settings, or add MCP servers yourself. Print the exact commands for the
   developer to run, for example:
   - `/plugin marketplace add Chachamaru127/claude-code-harness` and
     `/plugin install claude-code-harness@claude-code-harness-marketplace`
   - `claude mcp add figma-mcp-go -s project -- npx -y @vkhanhqui/figma-mcp-go@<tested-version>`
4. Summarize: READY / READY WITH WARNINGS / BLOCKED, and the next command (`/spec2ship <figma-url> --ba <path>`).
