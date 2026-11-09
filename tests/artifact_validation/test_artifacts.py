import copy
import json
import unittest

from tests.helpers import FIXTURES
from s2s import artifacts, ba_parser, schema

RUN = FIXTURES / "run"


def load(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


IRS = {"customer-management.md": ba_parser.parse_document(FIXTURES / "ba" / "customer-management.md")}


class SchemaTests(unittest.TestCase):
    def test_fixtures_valid_both_validators(self):
        for name, sch in (("requirements.json", "requirement"), ("figma-context.json", "figma-context"),
                          ("figma-mapping.json", "figma-mapping"), ("tasks.json", "task")):
            for builtin in (False, True):
                self.assertEqual(schema.validate(load(name), sch, force_builtin=builtin), [], f"{name} builtin={builtin}")

    def test_invalid_detected_both_validators(self):
        reqs = load("requirements.json")
        reqs["requirements"][0]["id"] = "REQ-1"
        reqs["requirements"][0]["status"] = "done"
        del reqs["requirements"][1]["source"]
        for builtin in (False, True):
            errs = schema.validate(reqs, "requirement", force_builtin=builtin)
            self.assertGreaterEqual(len(errs), 3, (builtin, errs))

    def test_evidence_schema(self):
        ok = {"schema_version": "1.0", "results": [{"criterion_id": "AC-CUS-001-01", "status": "NOT_RUN", "method": "unit-test", "recorded_at": "x"}]}
        self.assertEqual(schema.validate(ok, "evidence"), [])
        bad = copy.deepcopy(ok)
        bad["results"][0]["status"] = "passed"
        self.assertTrue(schema.validate(bad, "evidence", force_builtin=True))


class CrossRefTests(unittest.TestCase):
    def _req_report(self, reqs):
        rep = artifacts.Report()
        artifacts.check_requirements(reqs, IRS, rep)
        return rep

    def test_fixture_requirements_trace_to_source(self):
        rep = self._req_report(load("requirements.json"))
        self.assertTrue(rep.ok, rep.errors)

    def test_hallucinated_quote_section_page(self):
        reqs = load("requirements.json")
        reqs["requirements"][0]["source"]["quote"] = "Search supports fuzzy matching on email"
        reqs["requirements"][1]["source"]["section"] = "9.9"
        reqs["requirements"][2]["source"]["page"] = 3
        reqs["requirements"][2]["source"]["block_ids"] = ["B9999"]
        rep = self._req_report(reqs)
        joined = "\n".join(rep.errors)
        self.assertIn("possible hallucination", joined)
        self.assertIn("section '9.9' not found", joined)
        self.assertIn("no page information", joined)
        self.assertIn("B9999", joined)

    def test_ac_naming_and_duplicates(self):
        reqs = load("requirements.json")
        reqs["requirements"][1]["acceptance_criteria"][0]["id"] = "AC-CUS-001-01"
        rep = self._req_report(reqs)
        self.assertTrue(any("must be named AC-CUS-002" in e for e in rep.errors))
        self.assertTrue(any("duplicate acceptance" in e for e in rep.errors))

    def test_unknown_document(self):
        reqs = load("requirements.json")
        reqs["requirements"][0]["source"]["document"] = "other.pdf"
        self.assertFalse(self._req_report(reqs).ok)

    def test_mapping_requires_captured_nodes(self):
        mp = load("figma-mapping.json")
        mp["mappings"][0]["node_id"] = "99:1"
        mp["mappings"][1]["requirement_id"] = "REQ-CUS-099"
        mp["unmapped_requirements"] = []
        mp["mappings"] = mp["mappings"][:2]
        rep = artifacts.Report()
        artifacts.check_figma_mapping(mp, load("requirements.json"), load("figma-context.json"), rep)
        self.assertTrue(any("99:1" in e for e in rep.errors))
        self.assertTrue(any("REQ-CUS-099" in e for e in rep.errors))
        self.assertTrue(any("REQ-CUS-003 affects the UI" in w for w in rep.warnings))

    def test_tasks_coverage_orphans_cycles(self):
        reqs = load("requirements.json")
        tasks = load("tasks.json")
        rep = artifacts.Report()
        artifacts.check_tasks(tasks, reqs, rep)
        self.assertTrue(rep.ok, rep.errors)
        t = copy.deepcopy(tasks)
        t["phases"][1]["tasks"] = t["phases"][1]["tasks"][:2]  # drop REQ-CUS-003 task
        t["phases"][0]["tasks"][0]["depends"] = ["2.2"]  # cycle 1.1 -> 2.2 -> 1.3 -> 1.1
        t["phases"][0]["tasks"].append({"id": "1.4", "title": "Refactor logger", "requirement_ids": [], "layer": "backend", "dod": "tests pass", "depends": []})
        t["phases"][0]["tasks"].append({"id": "1.5", "title": "Perf tuning", "requirement_ids": ["REQ-CUS-004"], "layer": "backend", "dod": "p95 < 1s", "depends": ["7.7"]})
        rep = artifacts.Report()
        artifacts.check_tasks(t, reqs, rep)
        joined = "\n".join(rep.errors)
        self.assertIn("REQ-CUS-003 is in scope but no task implements it", joined)
        self.assertIn("dependency cycle", joined)
        self.assertIn("1.4 has no requirement_ids (orphan)", joined)
        self.assertIn("REQ-CUS-004, which is deferred", joined)
        self.assertIn("unknown task 7.7", joined)

    def test_llm_review_cannot_pass(self):
        ver = {"schema_version": "1.0", "results": [
            {"criterion_id": "AC-CUS-001-01", "status": "PASS", "method": "llm-review", "evidence": {"note": "looks right"}, "recorded_at": "x"},
            {"criterion_id": "AC-CUS-001-02", "status": "PASS", "method": "unit-test", "recorded_at": "x"}]}
        rep = artifacts.Report()
        artifacts.check_verification(ver, load("requirements.json"), rep)
        self.assertTrue(any("LLM review alone" in e for e in rep.errors))
        self.assertTrue(any("PASS requires evidence" in e for e in rep.errors))


if __name__ == "__main__":
    unittest.main()
