---
name: fullstack-planning
description: Produce the Spec2Ship fullstack impact analysis and a Harness-compatible task plan (tasks.json) that respects the existing repository architecture. Use when generating or updating a Spec2Ship plan.
---

# Fullstack planning

Inputs: `requirements.json`, `figma-mapping.json`, `figma-context.json`, `repository-analysis.{json,md}`,
`repository-notes.md`. Output: `.spec2ship/planning/tasks.json` (schema `schemas/task.schema.json`), plus
`architecture.md`, `api-contract.md`, `database-impact.md` when those layers are affected.

## Impact analysis (write findings, do not impose a new architecture)

- **Frontend:** routes/pages, components (reuse existing ones and Figma components), states
  (loading/empty/error/success), forms and validation, responsive behavior, API dependencies.
- **Backend:** use cases, endpoints, DTOs, validation, authorization, error handling, transactions, logging.
- **API:** reuse existing endpoints before adding new ones (see detected routes / OpenAPI); request/response,
  pagination, filters, error contract, auth; mark breaking changes `risk: "breaking-api"`.
- **Database:** entities, relations, constraints, indexes, migrations, data lifecycle; mark destructive
  migrations (drop/rename column, type narrowing, data rewrite) `risk: "destructive-migration"`.
- **Repository:** follow detected stack, package manager, naming and folder conventions; never plan to rewrite
  unrelated code. Read representative files before deciding where code goes.

## tasks.json rules (map 1:1 to the Harness Plans.md v2 table)

- Phases numbered from 1 (the CLI renumbers to avoid collisions with existing Harness phases at handoff).
  Task ids `N.M` inside phase N. Typical order: setup → database → backend/API → frontend → tests.
- Every task lists `requirement_ids`. Tasks without requirements are allowed only for `setup|test|docs|infra`
  with `no_requirement_reason`. Every in-scope requirement must be covered by at least one task.
- `dod`: one verifiable Yes/No line using project-native commands (e.g. "`pnpm test customers` passes",
  "migration applies on a fresh dev DB"). Never "works well".
- `depends`: task ids only, no cycles. `criteria_ids`: acceptance criteria the task makes testable.
- `tags` use Harness markers: `tdd:required`, `tdd:skip:<reason>`, `feature:security`, `feature:a11y`,
  `bugfix:reproduce-first`, `skip:tdd`, `needs-spike`.
- If no lint/formatter baseline was detected and source code will change, add a setup task first (Harness planning
  expects this).
- Keep tasks small (one PR-sized change each) and within approved requirements only.

Then run `spec2ship.py plan-review`, which validates and renders `spec.md`, the Plans.md preview and the RTM.
