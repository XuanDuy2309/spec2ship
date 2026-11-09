---
description: Generate or update the Spec2Ship specification, RTM and Harness-compatible task plan, then present it for developer approval
argument-hint: [change request]
---

# /spec2ship-plan

`S2S` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec2ship.py"`. Change request (optional): `$ARGUMENTS`.

1. `S2S status`. Requirements, Figma context and mapping must exist (otherwise run `/spec2ship-analyze`).
   If the run is already APPROVED/EXECUTION, a new plan **revokes the approval**: say so before changing anything,
   and run `S2S transition PLANNING --reason "<why>"`.
2. Apply the change request, if any, to the canonical JSON (`requirements.json`, `tasks.json`) — not to the
   generated Markdown views. Scope or behavior changes must be visible in the plan diff you present.
3. Follow the `fullstack-planning` skill to create/update `planning/tasks.json` and, when relevant,
   `planning/architecture.md`, `planning/api-contract.md`, `planning/database-impact.md`.
4. Run `S2S plan-review`. It validates everything, renders `planning/spec.md` (keeping developer edits — if it
   reports `preserved_user_edits`, merge needed changes from `spec.generated.md` by hand), renders the Harness
   `planning/Plans.md` preview and `reports/rtm.md`, and moves the run to PLAN_REVIEW. Fix ERRORs and re-run.
5. Present the plan (see /spec2ship step 9) including risks flagged for explicit review and blocking questions, then
   stop with:

   > To approve this exact plan, type: `/spec2ship:spec2ship-approve <plan_hash_short>`

Never approve on the developer's behalf and never start implementation here.
