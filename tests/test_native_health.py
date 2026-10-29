from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import native_health  # noqa: E402


PROCESSES = "409 1 /System/Library/PrivateFrameworks/TCC.framework/Support/tccd\n731 1 /Test App/Camtasia.app/Contents/MacOS/Camtasia\n"
SERVICE = "system/com.apple.tccd.system = {\n\tstate = running\n\tpid = 409\n\tlast exit code = (never exited)\n\tresource coalition = {\n\t\tstate = active\n\t}\n\tproperties = exponential throttling\n}\n"


class NativeHealthTests(unittest.TestCase):
    def test_healthy_single_editor_and_service_are_accepted(self) -> None:
        report = native_health.assess(PROCESSES, SERVICE, 409)
        self.assertTrue(report["ok"])
        self.assertEqual(report["editorPids"], [731])
        self.assertEqual(
            report["editorProcesses"],
            [{"pid": 731, "executable": "/Test App/Camtasia.app/Contents/MacOS/Camtasia"}],
        )
        self.assertEqual(report["thumbnailerPids"], [])
        self.assertEqual(report["privacyService"]["state"], "running")

    def test_an_orphan_or_active_thumbnailer_blocks_another_operation(self) -> None:
        for parent in (1, 731):
            processes = PROCESSES + f"810 {parent} /Test App/CLThumbnailer\n"
            with self.subTest(parent=parent):
                report = native_health.assess(processes, SERVICE)
                self.assertFalse(report["ok"])
                self.assertEqual(report["thumbnailerPids"], [810])

    def test_a_helper_accumulation_is_refused(self) -> None:
        processes = PROCESSES + "".join(
            f"{pid} 1 /Test/CLThumbnailer\n" for pid in range(1000, 1273)
        )
        report = native_health.assess(processes, SERVICE)
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["thumbnailerPids"]), 273)

    def test_multiple_editor_instances_are_refused(self) -> None:
        report = native_health.assess(PROCESSES + "900 1 /Other/Camtasia\n", SERVICE)
        self.assertFalse(report["ok"])
        self.assertIn("Multiple Camtasia", report["problems"][0])

    def test_permission_service_failure_and_restart_are_refused(self) -> None:
        for service in (
            SERVICE.replace("state = running", "state = throttled"),
            SERVICE.replace("(never exited)", "9"),
        ):
            with self.subTest(service=service):
                self.assertFalse(native_health.assess(PROCESSES, service)["ok"])
        changed = native_health.assess(PROCESSES, SERVICE, 408)
        self.assertFalse(changed["ok"])
        self.assertIn("restarted", changed["problems"][0])

    def test_a_missing_or_mismatched_live_service_pid_is_refused(self) -> None:
        for processes in (
            "731 1 /Test/Camtasia\n",
            PROCESSES.replace("Support/tccd", "Support/other"),
        ):
            with self.subTest(processes=processes):
                self.assertFalse(native_health.assess(processes, SERVICE)["ok"])

    def test_malformed_observations_fail_closed(self) -> None:
        for processes in ("PID PPID COMMAND", "0 1 /Test/CLThumbnailer", "409 missing /Test/tccd"):
            with self.subTest(processes=processes), self.assertRaises(ValueError):
                native_health.assess(processes, SERVICE)
        for service in (
            "",
            SERVICE.replace("\tpid = 409\n", ""),
            SERVICE.replace("pid = 409", "pid = 0"),
        ):
            with self.subTest(service=service), self.assertRaises(ValueError):
                native_health.assess(PROCESSES, service)

    def test_clean_service_exit_history_is_accepted(self) -> None:
        self.assertTrue(
            native_health.assess(PROCESSES, SERVICE.replace("(never exited)", "0"))["ok"]
        )

    def test_collection_is_read_only_and_checks_commands(self) -> None:
        observations = [
            subprocess.CompletedProcess([], 0, PROCESSES, ""),
            subprocess.CompletedProcess([], 0, SERVICE, ""),
        ]
        with (
            patch.object(native_health.sys, "platform", "darwin"),
            patch.object(native_health.subprocess, "run", side_effect=observations) as run,
        ):
            self.assertTrue(native_health.require_healthy()["ok"])
        self.assertEqual(run.call_args_list[0].args[0], ["ps", "-axo", "pid=,ppid=,comm="])
        self.assertEqual(
            run.call_args_list[1].args[0], ["launchctl", "print", "system/com.apple.tccd.system"]
        )
        for call in run.call_args_list:
            self.assertTrue(call.kwargs["check"])
            self.assertEqual(call.kwargs["timeout"], 5)

    def test_other_platforms_never_invoke_native_commands(self) -> None:
        with (
            patch.object(native_health.sys, "platform", "linux"),
            patch.object(native_health.subprocess, "run") as run,
        ):
            with self.assertRaisesRegex(ValueError, "require macOS"):
                native_health.require_healthy()
        run.assert_not_called()

    def test_cli_failure_is_explicit_json_and_nonzero(self) -> None:
        output, errors = io.StringIO(), io.StringIO()
        with (
            patch.object(
                native_health, "require_healthy", side_effect=ValueError("helpers still running")
            ),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(errors),
        ):
            status = native_health.main([])
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(output.getvalue())["ok"])
        self.assertIn("helpers still running", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
