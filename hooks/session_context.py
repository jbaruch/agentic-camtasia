#!/usr/bin/env python3
"""Read-only Camtasia reminder, scoped to projects near the session cwd.

Only cwd and two directory levels are inspected. Hidden trees and common
dependency/build directories are excluded. No project contents are read.
This hook adds context; it does not intercept writes or enforce validation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

MAX_DEPTH = 2
SKIP = frozenset({"node_modules", "vendor", "dist", "build", "__pycache__"})


def has_project(root: Path, depth: int = MAX_DEPTH) -> bool:
    for entry in sorted(root.iterdir()):
        if entry.is_symlink() or entry.name.startswith(".") or entry.name in SKIP:
            continue
        if entry.suffix.lower() in (".cmproj", ".tscproj"):
            return True
        if depth and entry.is_dir() and has_project(entry, depth - 1):
            return True
    return root.suffix.lower() == ".cmproj"


def main() -> int:
    try:
        if not has_project(Path.cwd()):
            return 0
    except OSError as exc:
        print(
            f"Camtasia context scan incomplete: {exc}; use explicit project inspection.",
            file=sys.stderr,
        )
        return 0
    context = (
        "Camtasia project nearby. Use the camtasia-project skill before project JSON edits. "
        "Prefer staged JSON edits using verified feature contracts; use the editor to resolve "
        "unknown serialization or verify the changed result. "
        "Save and close the target before writes; preserve native effects and original media. "
        "Static validation is partial; verify changed features in the target editor. "
        "This reminder does not block tool calls."
    )
    if os.environ.get("CURSOR_VERSION"):
        print(json.dumps({"additional_context": context}))
    else:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": context,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
