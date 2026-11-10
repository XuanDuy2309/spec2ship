# Spec2Ship

**BA documents + Figma design + your existing repo → an approved, traceable fullstack plan, executed by
[claude-code-harness](https://github.com/Chachamaru127/claude-code-harness), verified with evidence.**

Spec2Ship is a Claude Code plugin. It reads a business-analysis document (PDF, DOCX or Markdown, English or
Vietnamese) and a Figma design, analyzes your repository, and produces source-cited requirements, a
requirement ↔ design mapping, a specification, a Requirement Traceability Matrix (RTM) and a Harness `Plans.md`
task plan. **Nothing is implemented until a developer approves the exact plan.** Execution is delegated to
claude-code-harness; Spec2Ship then records review/test evidence and writes a delivery report that keeps
*implemented*, *verified*, *blocked* and *deferred* apart.

> Status: **0.2.0 preview — initial vertical slice.** Live Figma capture and Harness execution of a handed-off plan
> are not yet verified end-to-end. See [What is tested](#what-is-tested) and [Limitations](#limitations).

## Prerequisites

| Requirement | Why | Tested with |
|---|---|---|
| Claude Code | plugin host | 2.1.319 |
| Python ≥ 3.9 on PATH (`python3` or `python`) | local helper scripts (stdlib only) | 3.14.5 |
| [claude-code-harness](https://github.com/Chachamaru127/claude-code-harness) plugin | task ledger, Work, Review | 4.12.11 (≥ 4.0 accepted) |
| Node.js ≥ 18 with `npx` | runs the **bundled** figma-mcp-go MCP server | Node 24.16.0 |
| figma-mcp-go plugin in Figma Desktop (one-time import) | bridge between Figma Desktop and the MCP server | figma-mcp-go 0.1.3 |
| `pdftotext` (poppler) or `pip install pypdf` — optional | reliable PDF text extraction | poppler `pdftotext` (Git for Windows build) |
| `bash` | hook launcher | Git Bash on Windows |

## Install

```text
/plugin marketplace add Chachamaru127/claude-code-harness
/plugin install claude-code-harness@claude-code-harness-marketplace

/plugin marketplace add hthai1523/spec2ship        # this repository (it is its own marketplace)
/plugin install spec2ship@spec2ship-marketplace
```

Local checkout: `/plugin marketplace add /path/to/spec2ship`, or `claude --plugin-dir /path/to/spec2ship` for a single session.

**Figma: no MCP setup needed.** Spec2Ship bundles the figma-mcp-go MCP server (`.mcp.json`, pinned to
`@vkhanhqui/figma-mcp-go@0.1.3`, MIT); Claude Code starts it automatically when the plugin is enabled. Its tools
appear as `mcp__plugin_spec2ship_figma-mcp-go__*`. The first start downloads the package via `npx` (network needed
once).

One step cannot be bundled, because it lives inside Figma Desktop: download `plugin.zip` from
[figma-mcp-go releases](https://github.com/vkhanhqui/figma-mcp-go/releases), then in **Figma Desktop**
*Plugins → Development → Import plugin from manifest…* → `manifest.json` (once per machine), and run the plugin in
your design file whenever you use Spec2Ship.

Already configured figma-mcp-go yourself? It can stay: instances elect one leader on `127.0.0.1:1994` and the
others act as followers, so they do not conflict (verified with 0.1.3). You may remove your own entry.

Run `/spec2ship-setup` to check everything.

## Usage

```text
/spec2ship https://www.figma.com/design/FILE_KEY/customer-management?node-id=12-345 --ba docs/BA/customer-management.pdf
```

1. Preflight (Harness, Figma MCP + bridge, PDF extractor, git state).
2. BA parsing (local) → requirements with page/section/line citations, acceptance criteria, open questions.
3. Figma context (only relevant nodes) → requirement ↔ node mapping with evidence and confidence.
4. Repository analysis → stack, project-native commands, API routes, migrations, tests.
5. `spec.md`, `tasks.json`, Harness `Plans.md` preview and RTM → **stop for review**.
6. You type `/spec2ship:spec2ship-approve <plan-hash>` (Claude cannot do this for you).
7. `/spec2ship-work` hands the approved tasks to Harness (`/harness-work`, `/breezing`).
8. `/spec2ship-review`, `/spec2ship-verify` → evidence, RTM, `reports/report.md`.

Installed plugin commands are namespaced: type `/spec2ship:spec2ship-setup`, `/spec2ship:spec2ship-approve`, etc.
(the short forms below may also resolve when unambiguous; the approve command was verified only in namespaced form).

| Command | Purpose |
|---|---|
| `/spec2ship <figma-url> --ba <path>` | full workflow up to plan approval |
| `/spec2ship-setup` | dependency / integration checks with fixes |
| `/spec2ship-analyze [ba\|figma\|repo\|mapping]` | (re)run analysis parts |
| `/spec2ship-plan [change]` | generate/update spec, RTM, Harness plan; present for approval |
| `/spec2ship:spec2ship-approve <hash>` | developer-only approval of the reviewed plan |
| `/spec2ship-work [all\|task]` | hand off to Harness and run Harness Work |
| `/spec2ship-review` | Harness review + traceability review |
| `/spec2ship-verify` | project-native checks, per-criterion evidence, report |
| `/spec2ship-status` | state, artifacts, approval, Harness progress, next step |

## How the approval gate works

- `plan-review` computes a SHA-256 over requirements (scope), mapping, tasks and `spec.md`. You approve that hash.
- A `UserPromptSubmit` hook records your typed `/spec2ship:spec2ship-approve`; the `approve` step refuses without it, and a
  `PreToolUse` hook blocks Claude from invoking the approve command or writing the intent file.
- Handoff writes a marked section into Harness `Plans.md` (existing content preserved, backup kept). A hook blocks
  `/harness-work`, `/breezing` and `/harness-loop` if the approved task scope in `Plans.md` or the planning artifacts
  change afterwards (Harness status-marker updates are ignored).
- These are guardrails inside Claude Code, not a security boundary against a user with shell access.

## Artifacts (`.spec2ship/`)

`state.json`, `run.json`, `analysis/` (ba-normalized, requirements, figma-context, repository-analysis),
`mappings/` (figma-mapping, rtm, code-evidence), `planning/` (spec.md, tasks.json, Plans.md preview, architecture,
api-contract, database-impact), `verification/verification.json`, `reports/` (rtm.md, report.md).
Spec2Ship does not edit `.gitignore`: add `.spec2ship/` to keep intermediates out of Git, or commit
`planning/spec.md`, `reports/` and `verification/` deliberately. Override the location with `SPEC2SHIP_WORKSPACE`.

## Supported BA formats

| Format | Structure | Source references |
|---|---|---|
| Markdown | headings, lists, tables, links, code | section + line |
| DOCX | headings (styles/outline level), lists, tables, hyperlinks | section; page estimated from Word page-break markers |
| PDF (text) | numbered headings, paragraphs, lists, simple layout tables | page + section |
| PDF (scanned) | detected; run is blocked with an OCR notice (no OCR built in) | — |

## What is tested

`python -m unittest discover -s tests -t .` — unit, artifact-validation, integration and smoke tests (no network,
no model calls): parsers (EN/VI fixtures, scanned PDF, built-in PDF fallback), Figma URL handling, state machine,
schema + cross-reference validation (hallucinated citations, orphan tasks, cycles, coverage), Harness adapter
(render/renumber/merge/drift/detection), the full CLI vertical slice with the hook gate, repository analysis, and
plugin layout (64 tests). `claude plugin validate .` passes. Verified live in real Claude Code 2.1.319 sessions: clean
marketplace install; developer-typed `/spec2ship:spec2ship-approve <hash>` approving a plan through the hook;
handoff into a Plans.md alongside the installed Harness 4.12.11; and `/claude-code-harness:harness-work` being
blocked after the approved scope was edited. See [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Limitations

- The live Figma path was verified only up to the bridge check (`plugin not connected`); end-to-end design capture
  with Figma Desktop running has not been tested yet.
- Harness execution itself (`/harness-work` on a handed-off plan) has not been run end-to-end in a real session;
  the Plans.md format was verified against Harness 4.12.11 sources.
- Requirement extraction, mapping and planning quality depend on the model; the CLI validates structure and
  citations, not business correctness.
- PDF tables are detected heuristically from layout; complex tables may become paragraphs. No OCR.
- DOCX page numbers are estimates.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `[FAIL] harness` | install/enable claude-code-harness, restart Claude Code |
| `[FAIL] node-runtime` | install Node.js 18+ (bundled figma-mcp-go is started with `npx`), restart Claude Code |
| figma tools missing in `/mcp` | check Node/npx and network for the first `npx` download; restart Claude Code |
| `plugin not connected` | open Figma Desktop, open the file, run the figma-mcp-go plugin |
| `OCR_REQUIRED` | export a text PDF/DOCX/Markdown or OCR the PDF locally |
| `section '...' not found` / `possible hallucination` | the requirement's citation does not match the parsed BA; fix the citation |
| `Plan hash mismatch` | the plan changed after review; run `/spec2ship-plan` and approve the new hash |
| `No developer approval intent` | type `/spec2ship:spec2ship-approve <hash>` yourself (hooks must be enabled) |
| Harness Work blocked by Spec2Ship | approved scope in Plans.md changed; restore from `.spec2ship/execution/Plans.md.bak-*` or re-plan |

## Documentation

[Architecture](docs/ARCHITECTURE.md) · [Workflow](docs/WORKFLOW.md) · [Integration contracts](docs/INTEGRATION.md) ·
[Security & threat model](SECURITY.md) · [Product blueprint](docs/PRODUCT_BLUEPRINT.md) ·
[Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

## License

MIT — see [LICENSE](LICENSE).
