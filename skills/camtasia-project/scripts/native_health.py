#!/usr/bin/env python3
"""Read-only macOS preflight for serialized Camtasia verification.

Refuses additional native work while a CLThumbnailer remains, multiple editors
are running, or the system privacy service is unhealthy/has changed during a
verification operation. Does not launch/kill apps or alter permissions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


def process_rows(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=2)
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError("Cannot parse process inventory; inspect macOS before native work")
        pid, parent = int(parts[0]), int(parts[1])
        if pid <= 0:
            raise ValueError("Invalid process identity; inspect macOS before native work")
        rows.append({"pid": pid, "parentPid": parent, "executable": parts[2]})
    return rows


def service_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key in ("state", "pid", "last exit code"):
        match = re.search(r"^\t" + re.escape(key) + r" = ([^\n]+)$", text, re.MULTILINE)
        if match is None:
            raise ValueError("Cannot read system privacy service status; stop native work")
        fields[key] = match[1].strip()
    if not str(fields["pid"]).isdigit() or int(fields["pid"]) <= 0:
        raise ValueError("System privacy service has no live PID; stop native work")
    fields["pid"] = int(fields["pid"])
    return fields


def assess(processes: str, service: str, expected_tcc_pid: int | None = None) -> dict[str, Any]:
    rows, privacy = process_rows(processes), service_fields(service)
    thumbnailers = [row["pid"] for row in rows if Path(row["executable"]).name == "CLThumbnailer"]
    editor_rows = [row for row in rows if Path(row["executable"]).name == "Camtasia"]
    editors = [row["pid"] for row in editor_rows]
    problems = []
    if thumbnailers:
        problems.append(
            "Camtasia thumbnail helpers are still running; stop scheduling projects, "
            "observe their exit, and investigate persistent helpers before retrying"
        )
    if len(editors) > 1:
        problems.append("Multiple Camtasia editors are running; use one editor/project at a time")
    if privacy["state"] != "running" or privacy["last exit code"] not in ("(never exited)", "0"):
        problems.append(
            "The system privacy service is not healthy; stop native automation and "
            "inspect macOS diagnostics without resetting permissions"
        )
    if not any(
        row["pid"] == privacy["pid"] and Path(row["executable"]).name == "tccd" for row in rows
    ):
        problems.append(
            "Privacy-service PID is absent from the process snapshot; recheck before acting"
        )
    if expected_tcc_pid is not None and privacy["pid"] != expected_tcc_pid:
        problems.append(
            "The system privacy service restarted during verification; stop native work"
        )
    return {
        "ok": not problems,
        "problems": problems,
        "thumbnailerPids": thumbnailers,
        "editorPids": editors,
        "editorProcesses": [
            {"pid": row["pid"], "executable": row["executable"]} for row in editor_rows
        ],
        "privacyService": privacy,
        "limits": "A preflight observes current health; it cannot guarantee future OS stability.",
    }


def require_healthy(expected_tcc_pid: int | None = None) -> dict[str, Any]:
    if sys.platform != "darwin":
        raise ValueError("Native health checks require macOS; continue portable inspection/staging")
    processes = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,comm="],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    service = subprocess.run(
        ["launchctl", "print", "system/com.apple.tccd.system"],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    report = assess(processes.stdout, service.stdout, expected_tcc_pid)
    if not report["ok"]:
        raise ValueError("; ".join(report["problems"]))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-tcc-pid", type=int)
    args = parser.parse_args(argv)
    try:
        report = require_healthy(args.expected_tcc_pid)
        print(json.dumps(report))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        message = f"Native health: {exc}"
        print(message, file=sys.stderr)
        print(json.dumps({"ok": False, "error": message}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
