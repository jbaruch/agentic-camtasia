#!/usr/bin/env python3
"""Check the pinned community schema, with explicit native-verified corrections.

Schema validity, editor acceptance, and rendered behavior are separate results.
The compatibility profile is restricted to its observed editor build and format.
Install jsonschema through the repository's verification extra or the documented
isolated uv invocation. Fetch downloads data only and never executes it.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterator

import jsonschema
from jsonschema.exceptions import SchemaError

from project import load, native_hazards, nonfinite_errors

UPSTREAM_COMMIT = "443a41e37cddb460c0aa6e046c951cb17f241bf3"
UPSTREAM_URL = (
    "https://raw.githubusercontent.com/grandmasteri/pycamtasia/"
    + UPSTREAM_COMMIT
    + "/src/camtasia/resources/camtasia-project-schema.json"
)
UPSTREAM_SHA256 = "e8df2fab865f9a42b953985c01a47bfc898da3641b50dc7d0af80af53794f08a"
PROFILE_FILE = Path(__file__).resolve().parent.parent / "assets/mac-2025.0.3-profile.json"
PROFILE_FILES = {
    "mac-2025.0.3": PROFILE_FILE,
    "mac-2026.2.4": PROFILE_FILE.with_name("mac-2026.2.4-profile.json"),
}
MAX_MESSAGE = 240


def read_document(path: Path) -> dict[str, Any]:
    return load(path)[0]


def fetch_schema(output: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--location", UPSTREAM_URL],
        capture_output=True,
        check=True,
    )
    if hashlib.sha256(result.stdout).hexdigest() != UPSTREAM_SHA256:
        raise ValueError(
            "download hash differs from the reviewed schema; keep the current baseline"
        )
    jsonschema.Draft7Validator.check_schema(json.loads(result.stdout))
    if output.exists() and output.read_bytes() != result.stdout:
        raise ValueError(f"{output} contains different data; choose another cache path")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result.stdout)
    return {"schema": str(output), "sha256": UPSTREAM_SHA256, "commit": UPSTREAM_COMMIT}


def descend(schema: dict[str, Any], path: list[str]) -> Any:
    value: Any = schema
    for part in path:
        value = value[part]
    return value


def apply_profile(schema: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(schema)
    for change in profile["changes"]:
        target = descend(result, change["path"])
        if change["operation"] == "optional":
            target.remove(change["value"])
        elif change["operation"] == "append-enum":
            if change["value"] not in target:
                target.append(change["value"])
        elif change["operation"] == "append-branch":
            if change["schema"] not in target:
                target.append(change["schema"])
        elif change["operation"] == "add-property":
            if change["name"] in target:
                raise ValueError(f"profile would replace an existing property: {change['name']}")
            target[change["name"]] = change["schema"]
        else:
            raise ValueError(f"unknown profile operation {change['operation']!r}")
    jsonschema.Draft7Validator.check_schema(result)
    return result


def error_leaves(error: Any) -> Iterator[Any]:
    children = error.context
    # A media union emits misleading failures for every other clip family.
    # Select the branch matching the instance's _type when the schema declares it.
    if children and isinstance(error.instance, dict):
        family = error.instance.get("_type")
        if family is None and "effectName" in error.instance:
            family = "effect"
        options = error.schema.get(error.validator, [])
        match = next(
            (
                i
                for i, option in enumerate(options)
                if family is not None and option.get("$ref", "").rsplit("/", 1)[-1] == family
            ),
            None,
        )
        if match is not None:
            children = [c for c in children if c.schema_path[0] == match]
    if not children:
        yield error
    else:
        for child in children:
            yield from error_leaves(child)


def errors_for(schema: dict[str, Any], doc: dict[str, Any]) -> list[dict[str, Any]]:
    errors = []
    for error in jsonschema.Draft7Validator(schema).iter_errors(doc):
        for leaf in error_leaves(error):
            path = "/" + "/".join(
                str(p).replace("~", "~0").replace("/", "~1") for p in leaf.absolute_path
            )
            errors.append({"path": path, "message": leaf.message[:MAX_MESSAGE]})
    return sorted(errors, key=lambda e: (e["path"], e["message"]))


def audit(
    doc: dict[str, Any], schema: dict[str, Any], profile: dict[str, Any] | None = None
) -> dict[str, Any]:
    raw_errors = errors_for(schema, doc)
    corrected_errors = raw_errors
    if profile is not None:
        match = profile["appliesTo"]
        if (
            doc.get("version") != match["formatVersion"]
            or doc.get("authoringClientName") != match["authoringClient"]
        ):
            raise ValueError(
                "compatibility profile does not match this document's editor build and format"
            )
        corrected_errors = errors_for(apply_profile(schema, profile), doc)
    hazards = native_hazards(doc) + nonfinite_errors(doc)
    return {
        "ok": not corrected_errors and not hazards,
        "formatVersion": doc.get("version"),
        "authoringClient": doc.get("authoringClientName"),
        "upstreamErrors": raw_errors,
        "profile": profile["id"] if profile else None,
        "errors": corrected_errors,
        "nativeCompatibilityErrors": hazards,
        "meaning": "Schema structure only; editor roundtrip and rendered behavior are separate checks.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--out", type=Path, required=True)
    check = sub.add_parser("check")
    check.add_argument("--schema", type=Path, required=True)
    check.add_argument("--profile", choices=sorted(PROFILE_FILES))
    check.add_argument("projects", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            print(json.dumps(fetch_schema(args.out)))
            return 0
        raw = args.schema.read_bytes()
        schema = json.loads(raw)
        jsonschema.Draft7Validator.check_schema(schema)
        profile = None
        if args.profile:
            if hashlib.sha256(raw).hexdigest() != UPSTREAM_SHA256:
                raise ValueError("profile requires the reviewed upstream schema hash; run fetch")
            profile = read_document(PROFILE_FILES[args.profile])
        reports = []
        for path in args.projects:
            report = audit(read_document(path), schema, profile)
            reports.append({"project": str(path), **report})
        print(
            json.dumps(
                {"ok": all(r["ok"] for r in reports), "projects": reports}, ensure_ascii=False
            )
        )
        return 0 if all(r["ok"] for r in reports) else 1
    except (
        OSError,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
        SchemaError,
    ) as exc:
        print(f"Schema audit: {exc}", file=sys.stderr)
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
