"""Shared helpers: workspace paths, JSON IO, hashing."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = PLUGIN_ROOT / "schemas"
TEMPLATE_DIR = PLUGIN_ROOT / "templates"

DEFAULT_WORKSPACE = ".spec2ship"

WORKSPACE_DIRS = (
    "inputs",
    "analysis",
    "mappings",
    "planning",
    "execution",
    "verification",
    "reports",
)


class Spec2ShipError(Exception):
    """User-facing error; message is printed without a traceback."""


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    return _dt.date.today().isoformat()


def workspace_path(project_root: Path, workspace: str | None = None) -> Path:
    ws = workspace or os.environ.get("SPEC2SHIP_WORKSPACE") or DEFAULT_WORKSPACE
    p = Path(ws)
    if not p.is_absolute():
        p = project_root / p
    return p


def read_json(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Spec2ShipError(f"Missing file: {path}") from None
    except json.JSONDecodeError as e:
        raise Spec2ShipError(f"Invalid JSON in {path}: {e}") from None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
