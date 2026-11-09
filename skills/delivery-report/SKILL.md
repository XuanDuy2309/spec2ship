---
name: delivery-report
description: Present the Spec2Ship delivery report and RTM honestly — separate implemented, verified, blocked and deferred requirements with real check statuses. Use at the end of /spec2ship-verify or when the user asks for a delivery summary.
---

# Delivery report

1. Run `spec2ship.py report`. It regenerates `mappings/rtm.json`, `reports/rtm.md` and `reports/report.md` from
   canonical data (requirements, Harness Plans.md markers, verification evidence).
2. Present, in this order:
   - run id, state, who approved which plan hash and when, Harness ledger path;
   - requirements grouped: verified / implemented-not-verified / in progress / not started / blocked / deferred /
     rejected;
   - acceptance criteria counts by status (PASS, REVIEWED, FAIL, NOT_RUN);
   - project checks table with real commands and statuses;
   - traceability metrics (mapped to design, to tasks, with code evidence, covered by tests, orphan tasks);
   - blockers and recommended next actions.
3. Do not compute a single completion percentage. Do not upgrade REVIEWED or NOT_RUN to passed in prose.
4. Mention which artifacts the team may want to commit (`planning/spec.md`, `reports/rtm.md`, `reports/report.md`,
   `verification/verification.json`) versus intermediate files.
