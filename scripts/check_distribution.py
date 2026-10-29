#!/usr/bin/env python3
"""Reject generated files selected by ACR's actual package-file planner.

ACR v1 recursively distributes every regular file in a declared skill tree;
Git ignore patterns do not filter local installs. GENERATED_DIRECTORIES,
GENERATED_SUFFIXES and GENERATED_NAMES define this package's cache-file guard.
Run after tests, immediately before packaging or disposable consumer installs.
Stdout is JSON; generated files or operational errors exit 1 with diagnostics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Any

GENERATED_DIRECTORIES = frozenset({"__pycache__", ".pytest_cache", ".ruff_cache"})
GENERATED_SUFFIXES = frozenset({".pyc", ".pyo", ".pyd"})
GENERATED_NAMES = frozenset({".DS_Store"})


def generated_paths(files: list[str]) -> list[str]:
    return sorted(
        name
        for name in files
        if any(part in GENERATED_DIRECTORIES for part in PurePosixPath(name).parts)
        or PurePosixPath(name).suffix.lower() in GENERATED_SUFFIXES
        or PurePosixPath(name).name in GENERATED_NAMES
    )


def distribution_files(stdout: str) -> list[str]:
    payload: Any = json.loads(stdout)
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise ValueError("ACR did not report successful validation")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("valid") is not True:
        raise ValueError("ACR did not return a valid package plan")
    files = result.get("files")
    if (
        not isinstance(files, list)
        or not all(isinstance(name, str) for name in files)
        or "agent-plugin.yaml" not in files
    ):
        raise ValueError("ACR did not return the expected distribution-file inventory")
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args(argv)
    try:
        result = subprocess.run(
            ["acr", "validate", str(args.root), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("Install the ACR CLI before checking the package distribution", file=sys.stderr)
        return 1
    if result.returncode:
        print(
            "ACR validation failed; fix the package before distributing it: "
            + (result.stderr or result.stdout).strip(),
            file=sys.stderr,
        )
        return 1
    try:
        files = distribution_files(result.stdout)
    except ValueError as exc:
        print(f"{exc}; check the ACR CLI's validate --json contract", file=sys.stderr)
        return 1
    generated = generated_paths(files)
    print(
        json.dumps(
            {"ok": not generated, "distributionFiles": len(files), "generatedFiles": generated}
        )
    )
    if generated:
        print(
            "Move generated cache files outside declared skill directories, then rerun the check. "
            "Use python -B or PYTHONDONTWRITEBYTECODE=1 when importing installed helpers.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
