# Contributing

## Development setup

- Python 3.9+ (stdlib only at runtime; `jsonschema` is used when present, otherwise a built-in validator).
- Optional: `pdftotext` (poppler) or `pypdf` for PDF tests of the preferred extractor paths.
- Claude Code for `claude plugin validate .` and manual testing with `claude --plugin-dir .`.

## Tests

```bash
python -m unittest discover -s tests -t .        # unit, artifact validation, integration, smoke
claude plugin validate .                         # manifest / commands / skills / agents
python tests/fixtures/build_fixtures.py          # regenerate DOCX/PDF fixtures
```

Tests never touch your real Claude config: they use a temporary `CLAUDE_CONFIG_DIR` with a fake Harness install
and `SPEC2SHIP_MCP_SEARCH_STOP` to keep MCP-config discovery inside the temp dir.

## Rules

- Keep all Harness-specific knowledge in `scripts/s2s/harness_adapter.py`; update `TESTED_VERSIONS` and
  `docs/INTEGRATION.md` when re-verifying against a new Harness release.
- Do not add network access to helper scripts (a smoke test enforces this).
- Never weaken the evidence rules (no PASS without evidence; LLM review = REVIEWED).
- Every new feature needs tests; never document a feature as working unless a test or recorded manual check covers it.
- Update `CHANGELOG.md` (Keep a Changelog). Bump `version` in `plugin.json`, `marketplace.json` and
  `scripts/s2s/__init__.py` together (the smoke test checks they agree).
