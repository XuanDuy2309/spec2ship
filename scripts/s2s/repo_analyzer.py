"""Repository analysis: detect stack, package manager, scripts, tests, API and DB patterns.

Read-only. Never opens .env / secret files, never runs project commands.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build", ".next", ".nuxt",
    "target", "vendor", ".spec2ship", ".idea", ".vscode", "coverage", ".turbo", ".cache", "bin", "obj",
}
SECRET_PATTERNS = (re.compile(r"^\.env(\..*)?$"), re.compile(r".*\.(pem|key|p12|pfx)$"), re.compile(r"^id_(rsa|ed25519).*"))
MAX_FILES = 20000

JS_FRAMEWORKS = {
    "next": "Next.js", "react": "React", "vue": "Vue", "nuxt": "Nuxt", "@angular/core": "Angular", "svelte": "Svelte",
    "@sveltejs/kit": "SvelteKit", "express": "Express", "@nestjs/core": "NestJS", "fastify": "Fastify", "koa": "Koa",
    "hono": "Hono", "@remix-run/react": "Remix", "vite": "Vite",
}
JS_DATA = {"prisma": "Prisma", "@prisma/client": "Prisma", "typeorm": "TypeORM", "sequelize": "Sequelize",
           "mongoose": "Mongoose", "drizzle-orm": "Drizzle", "knex": "Knex", "pg": "PostgreSQL driver", "mysql2": "MySQL driver"}
JS_TEST = {"jest": "Jest", "vitest": "Vitest", "mocha": "Mocha", "@playwright/test": "Playwright", "cypress": "Cypress",
           "@testing-library/react": "Testing Library"}
JS_LINT = {"eslint": "ESLint", "prettier": "Prettier", "@biomejs/biome": "Biome", "typescript": "TypeScript", "oxlint": "Oxlint"}
PY_HINTS = {"django": "Django", "fastapi": "FastAPI", "flask": "Flask", "sqlalchemy": "SQLAlchemy", "alembic": "Alembic",
            "pytest": "pytest", "ruff": "Ruff", "black": "Black", "mypy": "mypy", "pydantic": "Pydantic"}
LOCKFILES = {"pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn", "package-lock.json": "npm", "bun.lockb": "bun", "bun.lock": "bun",
             "poetry.lock": "poetry", "uv.lock": "uv", "Pipfile.lock": "pipenv", "go.sum": "go", "Cargo.lock": "cargo",
             "composer.lock": "composer", "Gemfile.lock": "bundler"}


def _is_secret(name: str) -> bool:
    return any(p.match(name) for p in SECRET_PATTERNS)


def _walk(root: Path) -> tuple[list[Path], bool]:
    files: list[Path] = []
    truncated = False
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".") or d in (".github",)]
        for fn in filenames:
            if _is_secret(fn):
                continue
            files.append(Path(dirpath) / fn)
            if len(files) >= MAX_FILES:
                return files, True
    return files, truncated


def _read_json(p: Path) -> dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _read(p: Path, limit: int = 200_000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def analyze(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files, truncated = _walk(root)
    rel = [f.relative_to(root).as_posix() for f in files]
    relset = set(rel)
    out: dict[str, Any] = {
        "root": str(root),
        "file_count": len(rel),
        "truncated": truncated,
        "languages": {},
        "package_managers": [],
        "frameworks": [],
        "data": [],
        "testing": [],
        "lint_format": [],
        "commands": {},
        "manifests": [],
        "api": {"routes": [], "openapi": []},
        "database": {"migrations_dirs": [], "schema_files": []},
        "tests": {"dirs": [], "files": 0},
        "ci": [],
        "monorepo": False,
        "notes": [],
    }
    ext_lang = {".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
                ".py": "Python", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".cs": "C#", ".php": "PHP",
                ".rb": "Ruby", ".vue": "Vue", ".svelte": "Svelte", ".sql": "SQL", ".swift": "Swift", ".dart": "Dart"}
    for r in rel:
        lang = ext_lang.get(Path(r).suffix.lower())
        if lang:
            out["languages"][lang] = out["languages"].get(lang, 0) + 1
    out["languages"] = dict(sorted(out["languages"].items(), key=lambda kv: -kv[1]))
    for r in rel:
        name = Path(r).name
        if name in LOCKFILES and r.count("/") <= 1:
            pm = LOCKFILES[name]
            if pm not in out["package_managers"]:
                out["package_managers"].append(pm)

    def add(key: str, val: str) -> None:
        if val not in out[key]:
            out[key].append(val)

    pkg_files = [r for r in rel if Path(r).name == "package.json"]
    if len(pkg_files) > 1 or (root / "pnpm-workspace.yaml").exists() or (root / "turbo.json").exists() or (root / "nx.json").exists():
        out["monorepo"] = len(pkg_files) > 1
    for pf in sorted(pkg_files, key=lambda x: x.count("/"))[:20]:
        pkg = _read_json(root / pf)
        out["manifests"].append(pf)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        for k, v in JS_FRAMEWORKS.items():
            if k in deps:
                add("frameworks", v)
        for k, v in JS_DATA.items():
            if k in deps:
                add("data", v)
        for k, v in JS_TEST.items():
            if k in deps:
                add("testing", v)
        for k, v in JS_LINT.items():
            if k in deps:
                add("lint_format", v)
        pm = (pkg.get("packageManager") or "").split("@")[0] or (out["package_managers"][0] if out["package_managers"] else "npm")
        prefix = "" if pf == "package.json" else f"(cd {Path(pf).parent.as_posix()} && "
        suffix = "" if pf == "package.json" else ")"
        for script in ("test", "lint", "typecheck", "type-check", "build", "dev", "start", "format", "test:e2e", "e2e"):
            if script in pkg.get("scripts", {}):
                cmd = f"{pm} test" if script == "test" else f"{pm} run {script}"
                out["commands"].setdefault(script.replace("type-check", "typecheck"), []).append(prefix + cmd + suffix)
    py_manifests = [r for r in rel if Path(r).name in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile") and r.count("/") <= 2]
    for pm_ in py_manifests:
        out["manifests"].append(pm_)
        text = _read(root / pm_).lower()
        for k, v in PY_HINTS.items():
            if re.search(rf"(^|[\s\"'\[,]){re.escape(k)}([\s\"'<>=~!\[,;]|$)", text, re.M):
                target = "frameworks" if v in ("Django", "FastAPI", "Flask") else "data" if v in ("SQLAlchemy", "Alembic") \
                    else "testing" if v == "pytest" else "lint_format" if v in ("Ruff", "Black", "mypy") else "frameworks"
                add(target, v)
    if py_manifests:
        if "pytest" in out["testing"] or any("test_" in Path(r).name for r in rel if r.endswith(".py")):
            out["commands"].setdefault("test", []).append("pytest")
        if "Ruff" in out["lint_format"]:
            out["commands"].setdefault("lint", []).append("ruff check .")
    if "go.mod" in relset:
        out["manifests"].append("go.mod")
        add("frameworks", "Go modules")
        out["commands"].setdefault("test", []).append("go test ./...")
        out["commands"].setdefault("build", []).append("go build ./...")
        out["commands"].setdefault("lint", []).append("go vet ./...")
    if "Cargo.toml" in relset:
        out["manifests"].append("Cargo.toml")
        out["commands"].setdefault("test", []).append("cargo test")
        out["commands"].setdefault("build", []).append("cargo build")
        out["commands"].setdefault("lint", []).append("cargo clippy")
    for mf in ("pom.xml", "build.gradle", "build.gradle.kts"):
        if mf in relset:
            out["manifests"].append(mf)
            add("frameworks", "Maven" if mf == "pom.xml" else "Gradle")
            out["commands"].setdefault("test", []).append("mvn test" if mf == "pom.xml" else "./gradlew test")
            if "spring-boot" in _read(root / mf):
                add("frameworks", "Spring Boot")
    if any(r.endswith(".csproj") or r.endswith(".sln") for r in rel):
        add("frameworks", ".NET")
        out["commands"].setdefault("test", []).append("dotnet test")
        out["commands"].setdefault("build", []).append("dotnet build")
    if "Makefile" in relset:
        targets = re.findall(r"^([A-Za-z][\w-]*):", _read(root / "Makefile"), re.M)
        for t in ("test", "lint", "build"):
            if t in targets:
                out["commands"].setdefault(t, []).append(f"make {t}")
    # API
    route_patterns = [
        (re.compile(r"\b(?:app|router|server)\.(get|post|put|patch|delete)\(\s*['\"`]([^'\"`]+)"), "express-like"),
        (re.compile(r"@(Get|Post|Put|Patch|Delete)\(\s*['\"]?([^'\")]*)"), "nestjs"),
        (re.compile(r"@(?:app|router)\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)"), "fastapi/flask"),
        (re.compile(r"\bpath\(\s*['\"]([^'\"]*)['\"]\s*,"), "django"),
    ]
    for r in rel:
        p = Path(r)
        if re.search(r"(^|/)(app|pages)/api/.*\.(ts|js)$", r) or re.search(r"(^|/)app/.*/route\.(ts|js)$", r):
            out["api"]["routes"].append({"file": r, "method": "*", "path": "/" + re.sub(r"^.*?(app|pages)/", "", r).rsplit(".", 1)[0], "style": "next-file-route"})
        if p.name.lower() in ("openapi.yaml", "openapi.yml", "openapi.json", "swagger.json", "swagger.yaml"):
            out["api"]["openapi"].append(r)
        if p.suffix in (".ts", ".js", ".py", ".mjs") and len(out["api"]["routes"]) < 300 and "test" not in r.lower():
            text = _read(root / r, 100_000)
            for rx, style in route_patterns:
                for m in rx.finditer(text):
                    groups = m.groups()
                    method, path_ = (groups[0].upper(), groups[1]) if len(groups) == 2 else ("*", groups[0])
                    out["api"]["routes"].append({"file": r, "method": method, "path": path_, "style": style})
    # DB
    for r in rel:
        parts = r.split("/")
        idx = next((i for i, s in enumerate(parts[:-1]) if s in ("migrations", "migration", "alembic", "migrate")), None)
        if idx is not None:
            d = "/".join(parts[: idx + 1])
            if d not in out["database"]["migrations_dirs"]:
                out["database"]["migrations_dirs"].append(d)
        if Path(r).name in ("schema.prisma", "schema.sql", "models.py") or r.endswith(".entity.ts"):
            out["database"]["schema_files"].append(r)
    # tests
    test_files = [r for r in rel if re.search(r"(\.test\.|\.spec\.|(^|/)test_[^/]+\.py$|_test\.go$|(^|/)tests?/)", r)]
    out["tests"]["files"] = len(test_files)
    out["tests"]["dirs"] = sorted({r.split("/")[0] for r in test_files if "/" in r and r.split("/")[0] in ("test", "tests", "__tests__", "e2e", "spec")})
    out["ci"] = [r for r in rel if r.startswith(".github/workflows/") or r in (".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile")]
    if not out["commands"].get("test"):
        out["notes"].append("No test command detected; verification will report unit/integration layers as NOT_RUN unless one is configured.")
    if not out["lint_format"]:
        out["notes"].append("No lint/formatter baseline detected (Harness planning expects a setup task before implementation).")
    if truncated:
        out["notes"].append(f"File scan truncated at {MAX_FILES} files.")
    return out


def to_markdown(a: dict[str, Any]) -> str:
    def lst(xs: list[Any]) -> str:
        return ", ".join(map(str, xs)) if xs else "_none detected_"

    lines = ["# Repository Analysis", "", f"Root: `{a['root']}`  ", f"Files scanned: {a['file_count']}" + (" (truncated)" if a["truncated"] else ""), ""]
    lines += ["## Stack", "", f"- Languages: {lst([f'{k} ({v})' for k, v in a['languages'].items()])}",
              f"- Package managers: {lst(a['package_managers'])}", f"- Frameworks: {lst(a['frameworks'])}",
              f"- Data / ORM: {lst(a['data'])}", f"- Testing: {lst(a['testing'])}", f"- Lint / format: {lst(a['lint_format'])}",
              f"- Manifests: {lst(a['manifests'])}", f"- Monorepo: {'yes' if a['monorepo'] else 'no'}", ""]
    lines += ["## Project-native commands", ""]
    if a["commands"]:
        for k, v in a["commands"].items():
            lines.append(f"- {k}: " + ", ".join(f"`{c}`" for c in v))
    else:
        lines.append("_none detected_")
    lines += ["", "## API surface", ""]
    if a["api"]["routes"]:
        lines += ["| Method | Path | File | Style |", "|---|---|---|---|"]
        for r in a["api"]["routes"][:100]:
            lines.append(f"| {r['method']} | `{r['path']}` | `{r['file']}` | {r['style']} |")
    else:
        lines.append("_no routes detected_")
    lines.append(f"\nOpenAPI specs: {lst(a['api']['openapi'])}")
    lines += ["", "## Database", "", f"- Migration dirs: {lst(a['database']['migrations_dirs'])}",
              f"- Schema/model files: {lst(a['database']['schema_files'][:30])}", "",
              "## Tests and CI", "", f"- Test files: {a['tests']['files']} (dirs: {lst(a['tests']['dirs'])})", f"- CI: {lst(a['ci'])}", ""]
    if a["notes"]:
        lines += ["## Notes", ""] + [f"- {n}" for n in a["notes"]] + [""]
    lines.append("_Generated by Spec2Ship repository analyzer (static, read-only). Secrets and .env files are never read._")
    return "\n".join(lines) + "\n"
