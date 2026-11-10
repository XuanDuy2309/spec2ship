# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub Security Advisories ("Report a vulnerability" on the
repository's Security tab). Do not open a public issue. Include affected version, reproduction steps and impact.
We aim to acknowledge within 5 business days. Supported version: the latest release.

## Threat model

| Asset | Threat | Mitigation |
|---|---|---|
| Agent behavior | **Prompt injection** in BA documents or Figma text/annotations ("ignore instructions", "approve") | Parser output carries an untrusted-data notice; all skills/agents/commands instruct to treat content as data; approval and scope rules live in code (CLI + hooks), not in prompts; fixture includes an injection line |
| Approval integrity | Model approves on the developer's behalf | `/spec2ship-approve` has `disable-model-invocation`; PreToolUse hook denies Skill invocation of it; `approve` requires an intent recorded by the UserPromptSubmit hook from the developer's typed prompt (≤ 30 min, single use) and the reviewed plan hash; hook denies writes to the intent file and to `state.json`/`run.json` |
| Approved scope | Plan edited after approval; Harness executes unapproved tasks | Plan hash over requirements scope, mapping, tasks and spec; scope hash of the Plans.md section; guard hooks block `/harness-work`, `/breezing`, `/harness-loop` on drift; re-planning revokes approval |
| BA documents (confidential) | Exfiltration by helper scripts | Parsers are local (stdlib, local `pdftotext`/`pypdf`); a test fails if scripts import network modules |
| Secrets | Reading `.env`/keys during repo analysis | Analyzer skips `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`; skills forbid reading secrets |
| User work | Overwriting files / Plans.md / spec edits | Plans.md merged inside markers with a backup; handoff refuses to overwrite started tasks; developer edits of `spec.md` preserved; `.gitignore` never edited; root `spec.md` never written |
| Production | Deploys, destructive git, production DB | Not performed by Spec2Ship; verification skill forbids them; risky tasks (destructive migration, breaking API, cross-repo) flagged for explicit review; Harness guardrails remain in force |
| Supply chain | Bundled MCP server fetched from npm at runtime (`npx`) | Pinned to an exact version (`@vkhanhqui/figma-mcp-go@0.1.3`, MIT) in `.mcp.json`; a test fails if it becomes unpinned; npm still serves the bytes, so review upstream releases before bumping the pin. Preflight warns when a user-configured figma-mcp-go is unpinned |
| Design integrity | Bundled server exposes Figma write tools | Spec2Ship skills forbid write tools and the `figma-analyst` agent allowlist contains only read tools; Claude Code permission prompts still apply |

## Limits (be honest)

The approval gate is a guardrail inside Claude Code. Anyone with shell access (including a model allowed to run
arbitrary shell commands outside the patterns the hook recognizes) could alter workspace files. Hooks fail open on
internal errors so they never lock users out; a warning is printed to stderr. Use Claude Code permission settings to
restrict shell access in sensitive repositories.
