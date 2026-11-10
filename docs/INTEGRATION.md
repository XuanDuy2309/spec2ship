# Integration contracts (Phase 0 spike results)

Recorded 2026-11-09. Every item is marked **Verified** (observed directly), **Documented** (read in upstream docs,
not exercised) or **Assumption** (not confirmed; isolated so it is easy to change).

## Claude Code plugin / marketplace

| Item | Status | Detail |
|---|---|---|
| Claude Code version | Verified | 2.1.319 on Windows 10 |
| Plugin manifest `.claude-plugin/plugin.json` | Verified | `claude plugin validate .` passes |
| Marketplace manifest `.claude-plugin/marketplace.json` with `"source": "./"` (repo is its own marketplace, same layout as claude-code-harness) | Verified | validate passes |
| Auto-discovered `commands/`, `skills/<name>/SKILL.md`, `agents/`, `hooks/hooks.json` | Verified | clean `CLAUDE_CONFIG_DIR` marketplace install: 9 commands (listed as skills), 7 skills, 5 agents, 2 hooks; ~1k always-on tokens |
| Plugin command names are namespaced | Verified (live) | `/spec2ship:spec2ship-approve` resolved; bare `/spec2ship-approve` was passed to the model as plain text in a `--plugin-dir` session. Docs use the namespaced form |
| `disable-model-invocation: true` on the approve command | Verified (live) | the command was not in the model's available list; it ran when typed by the user. Also enforced by the PreToolUse hook (tested) |
| `${CLAUDE_PLUGIN_ROOT}` in command bodies and hook commands | Verified (live) | command ran `scripts/spec2ship.py approve`; hooks executed |
| UserPromptSubmit `{"decision":"block","reason":...}` | Verified (live) | `/claude-code-harness:harness-work all` blocked before any model turn after a scope edit |
| PreToolUse `hookSpecificOutput.permissionDecision: "deny"` | Documented; handler tested via stdin (direct and through `run-hook.sh` with bash) |
| Windows: hooks run under Git Bash; `MSYS_NO_PATHCONV=1` breaks `/c/...` paths for native Python | Verified (live failure, fixed with `cygpath -w`; launcher fails open) |

## claude-code-harness

Source inspected: installed plugin cache `claude-code-harness@claude-code-harness-marketplace` **4.12.11**
(skills `harness-plan`, `harness-work`, `harness-review`, `harness-sync`, `breezing`, `harness-loop`).

| Item | Status | Detail |
|---|---|---|
| Install | Verified | `/plugin marketplace add Chachamaru127/claude-code-harness`, plugin id `claude-code-harness@claude-code-harness-marketplace`, recorded in `~/.claude/plugins/installed_plugins.json` (`installPath`, `version`) |
| Plans.md v2 table | Verified (skills/harness-plan/SKILL.md, references/create.md) | `\| Task \| 内容 \| DoD \| Depends \| Status \|`; phase headings `## Phase N: name`; optional `Purpose:` line |
| Status markers | Verified | `cc:TODO`, `cc:WIP`, `cc:完了` (optionally `cc:完了 [7-char hash]`), `blocked`, `pm:依頼中`, `pm:確認済` |
| TDD / quality tags | Verified | `[tdd:required]`, `[tdd:skip:<reason>]`, `[feature:security]`, `[feature:a11y]`, `[bugfix:reproduce-first]`, `[skip:tdd]`, `[needs-spike]` |
| Plans.md location | Verified (go/cmd/harness/pre_compact.go, config template) | project root; `plansDirectory` in `.claude-code-harness.config.yaml` overrides |
| Spec precedence | Verified | Harness treats root `spec.md` as product contract (`spec.md > sub-spec > Plans.md`). Spec2Ship does **not** create or overwrite root `spec.md`; its section in Plans.md links `.spec2ship/planning/spec.md` as the approved sub-spec |
| Execution entry points | Verified (argument-hint) | `harness-work [all] [task-number\|range] ...`, `breezing`, `harness-loop`, `harness-review [code\|plan\|scope\|...]`, `harness-sync` |
| Harness guardrails | Verified (observed live) | Harness PreToolUse hook blocked a shell write of a `.env` fixture during development; Spec2Ship tests were changed instead of bypassing it |
| Plans.md written by Spec2Ship is parsed by Harness | **Assumption** | format matches the documented table; not yet exercised by running `/harness-work` on a handed-off section |

Adapter: `scripts/s2s/harness_adapter.py` (all Harness knowledge in one module). Compatibility policy: ≥ 4.0.0 is
accepted; versions other than `TESTED_VERSIONS` produce a warning.

## figma-mcp-go

Blueprint referenced `RamenSV/figma-mcp-go`. Its README (read 2026-11-09) instructs `npx -y @vkhanhqui/figma-mcp-go`
and links the Figma plugin `plugin.zip` from `vkhanhqui/figma-mcp-go` releases. The npm page (HTTP 403) and the
vkhanhqui GitHub repo (HTTP 451) could not be fetched in a browser-style request; the npm registry was then
queried directly with `npm view` (2026-11-10).

| Item | Status | Detail |
|---|---|---|
| Package metadata | Verified (`npm view`) | `@vkhanhqui/figma-mcp-go` latest **0.1.3**, license **MIT**, `engines.node >=18.0.0`, repo `github.com/vkhanhqui/figma-mcp-go`, bin `bin/run.js` (Node launcher for prebuilt Go binaries: darwin/linux/windows × amd64/arm64) |
| **Bundled in Spec2Ship** (0.2.0) | Verified (live) | plugin-root `.mcp.json` → `npx -y @vkhanhqui/figma-mcp-go@0.1.3`; in a `claude -p --plugin-dir` session Claude Code started it and exposed tools as **`mcp__plugin_spec2ship_figma-mcp-go__<tool>`**; `get_metadata` returned `plugin not connected` (Figma Desktop plugin not running) |
| Multiple instances | Verified (live probe of the 0.1.3 Windows binary) | first instance becomes LEADER listening on `127.0.0.1:1994`; later instances log `[node] became FOLLOWER` and ping the leader (`→ 200 healthy=true`). A user's own figma-mcp-go config and the bundled one therefore coexist |
| Local config on the test machine | Verified | `claude mcp get figma-mcp-go` → "Project config (shared via .mcp.json)", stdio, `npx -y @vkhanhqui/figma-mcp-go@latest`, defined in `~/.mcp.json` — i.e. Claude Code applies ancestor `.mcp.json` files; preflight now walks ancestors and warns that it is unpinned |
| No Figma token / REST API | Documented | README: "doesn't use the API at all" |
| Bridge | Documented + Verified failure mode | Figma Desktop → Plugins → Development → Import plugin from manifest → run plugin in the file. With the plugin not running, `get_metadata` returned the error **`plugin not connected`** (observed) |
| Open-file scope | Verified (tool schemas) | tools read the current document/page; no file-key argument. Spec2Ship compares the URL name slug with `get_metadata`'s file name and asks the user when uncertain |
| Node id format | Verified (tool schema) | colon format `4029:12345`, "never hyphens"; Spec2Ship converts URL `node-id=12-345` → `12:345` |
| Read tools used (schemas loaded in-session) | Verified | `get_metadata()`, `get_pages()`, `get_node(nodeId)`, `get_nodes_info`, `get_design_context(depth, detail, dedupe_components)`, `search_nodes(query, nodeId, types, limit)`, `scan_text_nodes(nodeId)`, `get_annotations(nodeId?)`, `get_document()` (current page only, can be large) |
| Write tools present (create_*, set_*, delete_* …) | Verified | Spec2Ship never calls them; the `figma-analyst` agent's tool allowlist excludes them |
| Successful capture with Figma Desktop running | **Not yet tested** | |

## BA parsing

| Item | Status |
|---|---|
| Markdown, DOCX via stdlib (zip/XML) | Verified (fixtures, EN + VI) |
| PDF via `pdftotext -layout` (poppler, found at `/mingw64/bin/pdftotext`) | Verified |
| PDF fallback `pypdf` | Code path present; pypdf not installed here → **untested** |
| PDF built-in extractor (uncompressed/Flate content streams, simple fonts) | Verified on fixture; CID/Identity-H fonts not supported (warning emitted) |
| Scanned PDF detection | Verified (fixture with no text layer → `OCR_REQUIRED`) |
| No network use by parsers | Verified by code review: no network imports in `scripts/s2s/` |
