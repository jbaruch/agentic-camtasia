from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
import session_context  # noqa: E402


class HookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_no_project_emits_nothing(self) -> None:
        output = io.StringIO()
        with patch.object(Path, "cwd", return_value=self.root), patch("sys.stdout", output):
            self.assertEqual(session_context.main(), 0)
        self.assertEqual(output.getvalue(), "")

    def test_discovers_bundle_in_output_without_reading_project(self) -> None:
        bundle = self.root / "output/My Film.cmproj"
        bundle.mkdir(parents=True)
        (bundle / "project.tscproj").write_text("not parsed by the hook")
        output = io.StringIO()
        with (
            patch.object(Path, "cwd", return_value=self.root),
            patch.dict("os.environ", {"CURSOR_VERSION": ""}),
            patch("sys.stdout", output),
        ):
            self.assertEqual(session_context.main(), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("camtasia-project", payload["hookSpecificOutput"]["additionalContext"])
        self.assertIn(
            "Prefer staged JSON edits", payload["hookSpecificOutput"]["additionalContext"]
        )
        self.assertEqual((bundle / "project.tscproj").read_text(), "not parsed by the hook")

    def test_cursor_receives_native_context_shape(self) -> None:
        (self.root / "film.cmproj").mkdir()
        output = io.StringIO()
        with (
            patch.object(Path, "cwd", return_value=self.root),
            patch.dict("os.environ", {"CURSOR_VERSION": "1"}),
            patch("sys.stdout", output),
        ):
            session_context.main()
        context = json.loads(output.getvalue())["additional_context"]
        self.assertIn("Prefer staged JSON edits", context)
        self.assertIn("verify the changed result", context)

    def test_does_not_follow_symlinks_or_dependency_trees(self) -> None:
        hidden = self.root / "node_modules/film.cmproj"
        hidden.mkdir(parents=True)
        (self.root / "linked.cmproj").symlink_to(hidden, target_is_directory=True)
        self.assertFalse(session_context.has_project(self.root))

    def test_unreadable_scan_is_visible_but_does_not_block_session(self) -> None:
        error = io.StringIO()
        with (
            patch.object(session_context, "has_project", side_effect=PermissionError("denied")),
            patch("sys.stderr", error),
        ):
            self.assertEqual(session_context.main(), 0)
        self.assertIn("scan incomplete", error.getvalue())


if __name__ == "__main__":
    unittest.main()
