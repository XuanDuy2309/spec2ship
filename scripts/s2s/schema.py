"""JSON Schema validation.

Uses the `jsonschema` package when installed; otherwise falls back to a small
built-in validator covering the subset of keywords Spec2Ship schemas use:
type, properties, required, additionalProperties, items, enum, const, pattern,
minLength, minItems, minimum, maximum, $ref (local #/$defs only).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import SCHEMA_DIR, read_json

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def load_schema(name: str) -> dict[str, Any]:
    return read_json(SCHEMA_DIR / f"{name}.schema.json")


def _is_type(value: Any, t: str) -> bool:
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[t])


def _builtin(value: Any, schema: dict, root: dict, path: str, errors: list[str]) -> None:
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            errors.append(f"{path}: unsupported $ref {ref}")
            return
        _builtin(value, root["$defs"][ref.split("/")[-1]], root, path, errors)
        return
    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_is_type(value, x) for x in types):
            errors.append(f"{path}: expected {t}, got {type(value).__name__}")
            return
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "items" in schema:
            for i, item in enumerate(value):
                _builtin(item, schema["items"], root, f"{path}[{i}]", errors)
    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                _builtin(v, props[k], root, f"{path}.{k}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property '{k}'")
            elif isinstance(schema.get("additionalProperties"), dict):
                _builtin(v, schema["additionalProperties"], root, f"{path}.{k}", errors)


def validate(value: Any, schema_name: str, force_builtin: bool = False) -> list[str]:
    schema = load_schema(schema_name)
    if not force_builtin:
        try:
            import jsonschema  # type: ignore

            validator_cls = jsonschema.validators.validator_for(schema)
            v = validator_cls(schema)
            out = []
            for e in sorted(v.iter_errors(value), key=lambda e: list(e.absolute_path)):
                loc = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path)
                out.append(f"{loc}: {e.message}")
            return out
        except ImportError:
            pass
    errors: list[str] = []
    _builtin(value, schema, schema, "$", errors)
    return errors


def validate_file(path: Path, schema_name: str) -> list[str]:
    return validate(read_json(path), schema_name)
