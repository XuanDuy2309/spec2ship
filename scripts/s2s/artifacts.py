"""Artifact validation: JSON Schema + cross-reference / traceability checks."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from .common import read_json
from .schema import validate

OUT_OF_SCOPE = {"deferred", "rejected"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").lower()
    return re.sub(r"\s+", " ", s).strip()


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, artifact: str, msg: str) -> None:
        self.errors.append(f"[{artifact}] {msg}")

    def warn(self, artifact: str, msg: str) -> None:
        self.warnings.append(f"[{artifact}] {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def load_ba_irs(ws: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    path = ws / "analysis" / "ba-normalized.json"
    if not path.exists():
        return out
    data = read_json(path)
    for doc in data.get("documents", []):
        out[doc["document"]] = doc
    return out


def check_requirements(reqs: dict[str, Any], irs: dict[str, dict[str, Any]], rep: Report) -> None:
    A = "requirements.json"
    for e in validate(reqs, "requirement"):
        rep.err(A, e)
    if any(e.startswith(f"[{A}]") for e in rep.errors):
        return
    seen: set[str] = set()
    seen_ac: set[str] = set()
    for r in reqs["requirements"]:
        rid = r["id"]
        if rid in seen:
            rep.err(A, f"duplicate requirement id {rid}")
        seen.add(rid)
        stem = rid[len("REQ-"):]
        for ac in r["acceptance_criteria"]:
            if not ac["id"].startswith(f"AC-{stem}-"):
                rep.err(A, f"{ac['id']} must be named AC-{stem}-NN to trace to {rid}")
            if ac["id"] in seen_ac:
                rep.err(A, f"duplicate acceptance criterion id {ac['id']}")
            seen_ac.add(ac["id"])
        if not r["acceptance_criteria"] and r["status"] not in OUT_OF_SCOPE:
            rep.warn(A, f"{rid} has no acceptance criteria; it cannot be verified")
        for q in r.get("ambiguities", []):
            if q["blocking"] and not q.get("resolution"):
                rep.warn(A, f"{rid} has unresolved blocking question {q['id']}: {q['question']}")
        _check_source(r, irs, rep)


def _check_source(r: dict[str, Any], irs: dict[str, dict[str, Any]], rep: Report) -> None:
    A = "requirements.json"
    src = r["source"]
    rid = r["id"]
    if not irs:
        rep.warn(A, f"{rid}: no ba-normalized.json; source reference not verified")
        return
    doc = irs.get(src["document"])
    if doc is None:
        rep.err(A, f"{rid}: source document '{src['document']}' was not parsed (known: {', '.join(irs)})")
        return
    blocks = doc["blocks"]
    if "page" in src:
        pages = doc.get("pages")
        if pages is None and not any("page" in b for b in blocks):
            rep.err(A, f"{rid}: '{src['document']}' has no page information; cite section/line instead")
        elif pages is not None and src["page"] > pages:
            rep.err(A, f"{rid}: page {src['page']} exceeds document page count {pages}")
        elif not any(b.get("page") == src["page"] for b in blocks):
            rep.warn(A, f"{rid}: no extracted text on page {src['page']}")
    if src.get("section"):
        want = _norm(src["section"])
        ok = any(
            _norm(b.get("section", "")) == want
            or _norm(b.get("section_title", "")) == want
            or (b["type"] == "heading" and want and want in _norm(b.get("text", "")))
            for b in blocks
        )
        if not ok:
            rep.err(A, f"{rid}: section '{src['section']}' not found in '{src['document']}'")
    ids = {b["id"] for b in blocks}
    for bid in src.get("block_ids", []):
        if bid not in ids:
            rep.err(A, f"{rid}: block {bid} does not exist in '{src['document']}'")
    if src.get("quote"):
        text = _norm(" ".join(b.get("text", "") for b in blocks))
        if _norm(src["quote"]) not in text:
            rep.err(A, f"{rid}: quoted text not found verbatim in '{src['document']}' (possible hallucination)")
    if "line" in src and doc["format"] == "markdown":
        if not any(b.get("line") == src["line"] for b in blocks):
            rep.warn(A, f"{rid}: line {src['line']} is not the start of an extracted block")


def check_figma_context(ctx: dict[str, Any], rep: Report) -> None:
    A = "figma-context.json"
    for e in validate(ctx, "figma-context"):
        rep.err(A, e)
    if any(e.startswith(f"[{A}]") for e in rep.errors):
        return
    if ctx["status"] == "captured" and not ctx["nodes"]:
        rep.err(A, "status is 'captured' but no nodes were recorded")
    if ctx["status"] == "unavailable":
        rep.warn(A, f"Figma context unavailable: {ctx.get('unavailable_reason', 'no reason given')}")
    match = (ctx.get("open_file") or {}).get("match")
    if match in ("low", "unknown"):
        rep.warn(A, "open Figma file was not confirmed to be the file in the URL; ask the user to confirm")


def check_figma_mapping(mp: dict[str, Any], reqs: dict[str, Any], ctx: dict[str, Any] | None, rep: Report) -> None:
    A = "figma-mapping.json"
    for e in validate(mp, "figma-mapping"):
        rep.err(A, e)
    if any(e.startswith(f"[{A}]") for e in rep.errors):
        return
    req_ids = {r["id"] for r in reqs.get("requirements", [])}
    node_ids = {n["id"] for n in (ctx or {}).get("nodes", [])}
    mapped = set()
    for m in mp["mappings"]:
        if m["requirement_id"] not in req_ids:
            rep.err(A, f"unknown requirement {m['requirement_id']}")
        if ctx is not None and m["node_id"] not in node_ids:
            rep.err(A, f"node {m['node_id']} is not in figma-context.json (mappings must cite captured nodes)")
        mapped.add(m["requirement_id"])
    declared = {u["requirement_id"] for u in mp.get("unmapped_requirements", [])}
    for r in reqs.get("requirements", []):
        needs_ui = r["type"] == "ui" or "frontend" in r.get("layers", [])
        if needs_ui and r["id"] not in mapped and r["id"] not in declared and r["status"] not in OUT_OF_SCOPE:
            rep.warn(A, f"{r['id']} affects the UI but has no Figma mapping and no unmapped reason")
    for c in mp.get("conflicts", []):
        rep.warn(A, f"BA/Figma conflict on {c['requirement_id']} / {c['node_id']}: {c['description']}")


def _cycle(graph: dict[str, list[str]]) -> list[str] | None:
    color: dict[str, int] = {}
    stack: list[str] = []

    def dfs(n: str) -> list[str] | None:
        color[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if color.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if color.get(m) is None:
                found = dfs(m)
                if found:
                    return found
        stack.pop()
        color[n] = 2
        return None

    for n in graph:
        if color.get(n) is None:
            found = dfs(n)
            if found:
                return found
    return None


def check_tasks(tasks: dict[str, Any], reqs: dict[str, Any], rep: Report) -> None:
    A = "tasks.json"
    for e in validate(tasks, "task"):
        rep.err(A, e)
    if any(e.startswith(f"[{A}]") for e in rep.errors):
        return
    req_by_id = {r["id"]: r for r in reqs.get("requirements", [])}
    ac_ids = {ac["id"] for r in req_by_id.values() for ac in r["acceptance_criteria"]}
    graph: dict[str, list[str]] = {}
    covered: set[str] = set()
    phase_numbers = set()
    for ph in tasks["phases"]:
        if ph["number"] in phase_numbers:
            rep.err(A, f"duplicate phase number {ph['number']}")
        phase_numbers.add(ph["number"])
        for t in ph["tasks"]:
            tid = t["id"]
            if tid in graph:
                rep.err(A, f"duplicate task id {tid}")
            if not tid.startswith(f"{ph['number']}."):
                rep.err(A, f"task {tid} must be numbered {ph['number']}.N inside phase {ph['number']}")
            graph[tid] = list(t["depends"])
            for rid in t["requirement_ids"]:
                if rid not in req_by_id:
                    rep.err(A, f"task {tid} references unknown requirement {rid}")
                elif req_by_id[rid]["status"] in OUT_OF_SCOPE:
                    rep.err(A, f"task {tid} implements {rid}, which is {req_by_id[rid]['status']} (out of approved scope)")
                covered.add(rid)
            if not t["requirement_ids"]:
                if t["layer"] not in ("setup", "test", "docs", "infra") or not t.get("no_requirement_reason"):
                    rep.err(A, f"task {tid} has no requirement_ids (orphan); add requirement ids or a no_requirement_reason for setup/test/docs/infra tasks")
            for cid in t.get("criteria_ids", []):
                if cid not in ac_ids:
                    rep.err(A, f"task {tid} references unknown acceptance criterion {cid}")
            if t.get("risk") in ("destructive-migration", "breaking-api", "cross-repo"):
                rep.warn(A, f"task {tid} is flagged '{t['risk']}' and needs explicit developer review")
    for tid, deps in graph.items():
        for d in deps:
            if d not in graph:
                rep.err(A, f"task {tid} depends on unknown task {d}")
    cyc = _cycle(graph)
    if cyc:
        rep.err(A, f"dependency cycle: {' -> '.join(cyc)}")
    for rid, r in req_by_id.items():
        if r["status"] not in OUT_OF_SCOPE and rid not in covered:
            rep.err(A, f"{rid} is in scope but no task implements it (mark it deferred/rejected or plan a task)")


def check_verification(ver: dict[str, Any], reqs: dict[str, Any], rep: Report) -> None:
    A = "verification.json"
    for e in validate(ver, "evidence"):
        rep.err(A, e)
    if any(e.startswith(f"[{A}]") for e in rep.errors):
        return
    ac_ids = {ac["id"] for r in reqs.get("requirements", []) for ac in r["acceptance_criteria"]}
    for res in ver["results"]:
        if res["criterion_id"] not in ac_ids:
            rep.err(A, f"evidence for unknown criterion {res['criterion_id']}")
        if res["method"] == "llm-review" and res["status"] == "PASS":
            rep.err(A, f"{res['criterion_id']}: LLM review alone cannot be PASS (use REVIEWED)")
        if res["status"] == "PASS" and not res.get("evidence"):
            rep.err(A, f"{res['criterion_id']}: PASS requires evidence")


def validate_workspace(ws: Path, stage: str = "auto") -> Report:
    """Validate every artifact that exists. stage='plan' requires planning inputs."""
    rep = Report()
    irs = load_ba_irs(ws)
    req_path = ws / "analysis" / "requirements.json"
    reqs: dict[str, Any] = {"requirements": []}
    if req_path.exists():
        reqs = read_json(req_path)
        check_requirements(reqs, irs, rep)
    elif stage in ("plan", "approve"):
        rep.err("requirements.json", "missing")
    ctx = None
    ctx_path = ws / "analysis" / "figma-context.json"
    if ctx_path.exists():
        ctx = read_json(ctx_path)
        check_figma_context(ctx, rep)
    elif stage in ("plan", "approve"):
        rep.err("figma-context.json", "missing (record status 'unavailable' with a reason if Figma could not be read)")
    mp_path = ws / "mappings" / "figma-mapping.json"
    if mp_path.exists() and reqs.get("requirements"):
        check_figma_mapping(read_json(mp_path), reqs, ctx, rep)
    elif stage in ("plan", "approve"):
        rep.err("figma-mapping.json", "missing")
    tasks_path = ws / "planning" / "tasks.json"
    if tasks_path.exists():
        check_tasks(read_json(tasks_path), reqs, rep)
    elif stage == "approve":
        rep.err("tasks.json", "missing")
    ver_path = ws / "verification" / "verification.json"
    if ver_path.exists():
        check_verification(read_json(ver_path), reqs, rep)
    return rep
