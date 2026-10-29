#!/usr/bin/env python3
"""Back up a closed candidate, then save/close/reopen it through Camtasia.

macOS only. Native save acceptance does not certify rendered behavior or absence
of an unsupported-feature warning. Continue through the editor's export checks.
The AppleScript touches only the document whose file URL matches the candidate.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
from typing import Any

import project
import native_health


def select_editor(
    document: dict[str, Any], health: dict[str, Any], requested: Path | None = None
) -> dict[str, Any]:
    """Resolve the sole running Mac editor without launching an application."""
    editors = health.get("editorProcesses")
    if not isinstance(editors, list) or len(editors) != 1:
        raise ValueError("open the intended Camtasia build as the sole editor, then retry")
    editor = editors[0]
    if (
        not isinstance(editor, dict)
        or type(editor.get("pid")) is not int
        or editor["pid"] <= 0
        or not isinstance(editor.get("executable"), str)
    ):
        raise ValueError("cannot identify the running editor; repeat the native health check")
    executable = Path(editor["executable"]).resolve(strict=True)
    if executable.name != "Camtasia" or executable.parent.name != "MacOS":
        raise ValueError("unexpected editor executable; open a native Camtasia Mac bundle")
    contents = executable.parent.parent
    application = contents.parent
    if contents.name != "Contents" or application.suffix.lower() != ".app":
        raise ValueError("cannot locate the editor bundle; open a native Camtasia Mac app")
    if requested is not None and requested.expanduser().resolve() != application:
        raise ValueError("the requested editor is not the running bundle; open that app first")
    info = plistlib.loads((contents / "Info.plist").read_bytes())
    if (
        not isinstance(info, dict)
        or info.get("CFBundleIdentifier") != "com.techsmith.camtasia"
        or info.get("CFBundleExecutable") != executable.name
        or not isinstance(info.get("CFBundleShortVersionString"), str)
    ):
        raise ValueError("cannot verify the running Camtasia identity; inspect its app bundle")
    identity = document.get("authoringClientName")
    if (
        not isinstance(identity, dict)
        or identity.get("name") != "Camtasia"
        or identity.get("platform") != "Mac"
        or identity.get("version") != info["CFBundleShortVersionString"]
    ):
        raise ValueError(
            "the running editor does not match the project's Mac authoring build; "
            "open the matching version or perform an explicit conversion in the editor"
        )
    signature = {key: identity[key] for key in ("name", "platform", "version")}
    for profile_path in (Path(__file__).resolve().parent.parent / "assets").glob("*-profile.json"):
        match = json.loads(profile_path.read_text())["appliesTo"]
        if (
            match["authoringClient"] == signature
            and document.get("version") != match["formatVersion"]
        ):
            raise ValueError(
                "the project format does not match this verified authoring build; "
                "use a same-build native template or convert explicitly in the editor"
            )
    return {"app": str(application), "pid": editor["pid"], "version": identity["version"]}


def roundtrip(path: Path, editor_app: Path | None = None) -> dict[str, Any]:
    path = path.resolve()
    target = project.project_file(path)
    before, raw = project.load(target)
    report = project.validate(before, target.parent)
    if not report["ok"]:
        raise ValueError(
            "candidate has structural or native compatibility errors; validate it first"
        )
    project.ensure_closed(target)
    health_before = native_health.require_healthy()
    editor = select_editor(before, health_before, editor_app)
    backup = target.with_name(f"{target.stem}.before-native-{project.digest(raw)}.tscproj")
    try:
        with backup.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if backup.read_bytes() != raw:
            raise ValueError(
                f"backup collision at {backup}; preserve that file and choose another candidate"
            )
    script = Path(__file__).with_suffix(".applescript")
    try:
        result = subprocess.run(
            ["osascript", str(script), str(path), editor["app"]],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(
            f"native invocation did not complete: {exc}; original JSON is at {backup}. "
            "Inspect the candidate in Camtasia before retrying"
        ) from exc
    if result.returncode:
        raise ValueError(
            f"native roundtrip failed: {result.stderr.strip()}; original JSON is at {backup}. "
            "Inspect the candidate's Camtasia dialog before retrying"
        )
    if Path(result.stdout.strip()).resolve() != path:
        raise ValueError(f"unexpected native response; inspect Camtasia and preserve {backup}")
    try:
        health_after = native_health.require_healthy(health_before["privacyService"]["pid"])
        if editor["pid"] not in health_after["editorPids"]:
            raise ValueError("the editor instance changed during native verification")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ValueError(
            f"native save returned but stability checks failed: {exc}; "
            f"stop editor work and preserve the original JSON at {backup}"
        ) from exc
    try:
        after, saved = project.load(target)
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"cannot read the native-saved candidate: {exc}; original JSON is at {backup}. "
            "Inspect the candidate in Camtasia before retrying"
        ) from exc
    if after.get("authoringClientName") != before.get("authoringClientName") or after.get(
        "version"
    ) != before.get("version"):
        raise ValueError(
            f"native save changed the editor/format identity; inspect the candidate and "
            f"preserve the original JSON at {backup}"
        )
    after_report = project.validate(after, target.parent)
    return {
        "ok": after_report["ok"],
        "candidate": str(path),
        "editor": editor,
        "backup": str(backup),
        "beforeSha256": project.digest(raw),
        "afterSha256": project.digest(saved),
        "saveReopen": True,
        "renderVerified": False,
        "nativeHealth": {"before": health_before, "after": health_after},
        "authoringClient": after.get("authoringClientName"),
        "validation": after_report,
        "next": "Check export warnings, render, and inspect the requested native behavior.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--editor-app", type=Path, help="Require this exact running Camtasia .app")
    args = parser.parse_args(argv)
    try:
        result = roundtrip(args.candidate, args.editor_app)
        print(json.dumps(result))
        return 0 if result["validation"]["ok"] else 1
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Native roundtrip: {exc}", file=sys.stderr)
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
