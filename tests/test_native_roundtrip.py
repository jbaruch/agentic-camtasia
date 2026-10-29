from __future__ import annotations

import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import native_roundtrip  # noqa: E402
import project  # noqa: E402


class NativeRoundtripTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / "Candidate with spaces.cmproj"
        self.bundle.mkdir()
        self.target = self.bundle / "project.tscproj"
        self.doc = {
            "version": "9.0",
            "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2025.0.3"},
            "width": 640,
            "height": 360,
            "editRate": 100,
            "timeline": {"sceneTrack": {"scenes": [{"csml": {"tracks": []}}]}},
        }
        self.raw = json.dumps(self.doc).encode()
        self.target.write_bytes(self.raw)
        self.app = self.make_editor("Camtasia 2025.app", "2025.0.3")
        self.health_report = self.editor_health(self.app)
        health = patch.object(
            native_roundtrip.native_health,
            "require_healthy",
            return_value=self.health_report,
        )
        health.start()
        self.addCleanup(health.stop)

    def make_editor(self, name: str, version: str) -> Path:
        app = Path(self.temp.name) / "Editors with spaces" / name
        executable = app / "Contents/MacOS/Camtasia"
        executable.parent.mkdir(parents=True)
        executable.write_text("not executable; metadata-only unit fixture")
        (app / "Contents/Info.plist").write_bytes(
            plistlib.dumps(
                {
                    "CFBundleIdentifier": "com.techsmith.camtasia",
                    "CFBundleExecutable": "Camtasia",
                    "CFBundleShortVersionString": version,
                }
            )
        )
        return app

    def editor_health(self, app: Path) -> dict:
        return {
            "ok": True,
            "privacyService": {"pid": 409},
            "editorPids": [731],
            "editorProcesses": [{"pid": 731, "executable": str(app / "Contents/MacOS/Camtasia")}],
        }

    def test_original_bytes_are_backed_up_before_native_execution(self) -> None:
        def native(args, **kwargs):
            self.assertEqual(args[-1], str(self.app.resolve()))
            backups = list(self.bundle.glob("*.before-native-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), self.raw)
            changed = dict(self.doc, title="Native save")
            self.target.write_text(json.dumps(changed))
            return subprocess.CompletedProcess(args, 0, str(self.bundle) + "\n", "")

        with (
            patch.object(project, "ensure_closed"),
            patch.object(native_roundtrip.subprocess, "run", side_effect=native),
        ):
            result = native_roundtrip.roundtrip(self.bundle)
        self.assertTrue(result["saveReopen"])
        self.assertFalse(result["renderVerified"])
        self.assertNotEqual(result["beforeSha256"], result["afterSha256"])
        self.assertEqual(result["editor"]["app"], str(self.app.resolve()))

    def test_native_failure_keeps_original_and_names_backup(self) -> None:
        result = subprocess.CompletedProcess([], 1, "", "editor rejected candidate")
        with (
            patch.object(project, "ensure_closed"),
            patch.object(native_roundtrip.subprocess, "run", return_value=result),
        ):
            with self.assertRaisesRegex(ValueError, "original JSON is at"):
                native_roundtrip.roundtrip(self.bundle)
        self.assertEqual(self.target.read_bytes(), self.raw)
        self.assertEqual(len(list(self.bundle.glob("*.before-native-*"))), 1)

    def test_live_project_is_refused_before_backup_or_automation(self) -> None:
        with (
            patch.object(project, "ensure_closed", side_effect=ValueError("open")),
            patch.object(native_roundtrip.subprocess, "run") as run,
        ):
            with self.assertRaisesRegex(ValueError, "open"):
                native_roundtrip.roundtrip(self.bundle)
        run.assert_not_called()
        self.assertEqual(list(self.bundle.glob("*.before-native-*")), [])

    def test_wrong_native_document_response_is_an_error(self) -> None:
        result = subprocess.CompletedProcess([], 0, "/another/project.cmproj\n", "")
        with (
            patch.object(project, "ensure_closed"),
            patch.object(native_roundtrip.subprocess, "run", return_value=result),
        ):
            with self.assertRaisesRegex(ValueError, "unexpected native response"):
                native_roundtrip.roundtrip(self.bundle)

    def test_unhealthy_desktop_is_refused_before_backup_and_automation(self) -> None:
        with (
            patch.object(project, "ensure_closed"),
            patch.object(
                native_roundtrip.native_health,
                "require_healthy",
                side_effect=ValueError("helpers still running"),
            ),
            patch.object(native_roundtrip.subprocess, "run") as run,
        ):
            with self.assertRaisesRegex(ValueError, "helpers still running"):
                native_roundtrip.roundtrip(self.bundle)
        run.assert_not_called()
        self.assertEqual(list(self.bundle.glob("*.before-native-*")), [])
        self.assertEqual(self.target.read_bytes(), self.raw)

    def test_post_save_instability_names_retained_original_backup(self) -> None:
        response = subprocess.CompletedProcess([], 0, str(self.bundle) + "\n", "")
        with (
            patch.object(project, "ensure_closed"),
            patch.object(
                native_roundtrip.native_health,
                "require_healthy",
                side_effect=[
                    self.health_report,
                    ValueError("privacy service restarted"),
                ],
            ),
            patch.object(native_roundtrip.subprocess, "run", return_value=response),
        ):
            with self.assertRaisesRegex(ValueError, "stability checks failed.*original JSON"):
                native_roundtrip.roundtrip(self.bundle)
        self.assertEqual(list(self.bundle.glob("*.before-native-*"))[0].read_bytes(), self.raw)

    def test_selection_follows_running_bundle_even_with_two_installed_versions(self) -> None:
        newer = self.make_editor("Camtasia 2026.app", "2026.2.4")
        document = dict(
            self.doc,
            version="10.0",
            authoringClientName={"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"},
        )
        selected = native_roundtrip.select_editor(document, self.editor_health(newer))
        self.assertEqual(selected["app"], str(newer.resolve()))
        self.assertEqual(selected["version"], "2026.2.4")
        with self.assertRaisesRegex(ValueError, "requested editor"):
            native_roundtrip.select_editor(document, self.editor_health(newer), self.app)

    def test_known_editor_with_mismatched_project_format_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "project format"):
            native_roundtrip.select_editor(dict(self.doc, version="10.0"), self.health_report)

    def test_wrong_build_or_missing_editor_is_refused_before_backup_or_native_calls(self) -> None:
        reports = [
            dict(self.health_report, editorProcesses=[]),
            self.editor_health(self.make_editor("Newer.app", "2026.2.4")),
        ]
        for report in reports:
            with (
                self.subTest(report=report),
                patch.object(project, "ensure_closed"),
                patch.object(
                    native_roundtrip.native_health, "require_healthy", return_value=report
                ),
                patch.object(native_roundtrip.subprocess, "run") as run,
            ):
                with self.assertRaises(ValueError):
                    native_roundtrip.roundtrip(self.bundle)
                run.assert_not_called()
                self.assertEqual(list(self.bundle.glob("*.before-native-*")), [])
                self.assertEqual(self.target.read_bytes(), self.raw)

    def test_unidentified_or_non_mac_projects_are_refused(self) -> None:
        for identity in [
            None,
            {"name": "Camtasia", "platform": "Windows", "version": "2025.0.3"},
            {"name": "Other", "platform": "Mac", "version": "2025.0.3"},
        ]:
            with (
                self.subTest(identity=identity),
                self.assertRaisesRegex(ValueError, "authoring build"),
            ):
                native_roundtrip.select_editor(
                    dict(self.doc, authoringClientName=identity), self.health_report
                )

    def test_wrong_app_identity_and_non_bundle_process_paths_are_refused(self) -> None:
        info = self.app / "Contents/Info.plist"
        data = plistlib.loads(info.read_bytes())
        data["CFBundleIdentifier"] = "other.app"
        info.write_bytes(plistlib.dumps(data))
        with self.assertRaisesRegex(ValueError, "verify"):
            native_roundtrip.select_editor(self.doc, self.health_report)
        with self.assertRaises(ValueError):
            native_roundtrip.select_editor(
                self.doc, {"editorProcesses": [{"pid": 731, "executable": str(self.target)}]}
            )

    def test_editor_restart_during_save_retains_the_original_backup(self) -> None:
        response = subprocess.CompletedProcess([], 0, str(self.bundle) + "\n", "")
        with (
            patch.object(project, "ensure_closed"),
            patch.object(
                native_roundtrip.native_health,
                "require_healthy",
                side_effect=[self.health_report, dict(self.health_report, editorPids=[732])],
            ),
            patch.object(native_roundtrip.subprocess, "run", return_value=response),
        ):
            with self.assertRaisesRegex(ValueError, "editor instance changed.*original JSON"):
                native_roundtrip.roundtrip(self.bundle)
        self.assertEqual(list(self.bundle.glob("*.before-native-*"))[0].read_bytes(), self.raw)

    def test_native_format_conversion_is_reported_instead_of_certified(self) -> None:
        def native(args, **kwargs):
            self.target.write_text(json.dumps(dict(self.doc, version="10.0")))
            return subprocess.CompletedProcess(args, 0, str(self.bundle) + "\n", "")

        with (
            patch.object(project, "ensure_closed"),
            patch.object(native_roundtrip.subprocess, "run", side_effect=native),
        ):
            with self.assertRaisesRegex(ValueError, "changed the editor/format identity"):
                native_roundtrip.roundtrip(self.bundle)
        self.assertEqual(list(self.bundle.glob("*.before-native-*"))[0].read_bytes(), self.raw)

    def test_invocation_timeout_names_the_retained_original(self) -> None:
        with (
            patch.object(project, "ensure_closed"),
            patch.object(
                native_roundtrip.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired("osascript", 60),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "did not complete.*original JSON is at"):
                native_roundtrip.roundtrip(self.bundle)
        self.assertEqual(list(self.bundle.glob("*.before-native-*"))[0].read_bytes(), self.raw)

    def test_unreadable_native_save_names_the_retained_original(self) -> None:
        def native(args, **kwargs):
            self.target.write_text('{"version":')
            return subprocess.CompletedProcess(args, 0, str(self.bundle) + "\n", "")

        with (
            patch.object(project, "ensure_closed"),
            patch.object(native_roundtrip.subprocess, "run", side_effect=native),
        ):
            with self.assertRaisesRegex(ValueError, "cannot read.*original JSON is at"):
                native_roundtrip.roundtrip(self.bundle)
        self.assertEqual(list(self.bundle.glob("*.before-native-*"))[0].read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main()
