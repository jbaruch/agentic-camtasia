from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_distribution  # noqa: E402


def planned(files: list[str]) -> str:
    return json.dumps({"ok": True, "result": {"valid": True, "files": files}})


class DistributionTests(unittest.TestCase):
    def test_generated_files_are_distinct_from_source_and_profile_files(self) -> None:
        source = [
            "agent-plugin.yaml",
            "rules/timing.md",
            "skills/edit/SKILL.md",
            "skills/edit/scripts/project.py",
            "skills/edit/scripts/native.applescript",
            "skills/edit/assets/profile.json",
            "hooks/session.py",
        ]
        generated = [
            "skills/edit/scripts/__pycache__/project.cpython-312.pyc",
            "skills/edit/.DS_Store",
            "skills/edit/scripts/project.PYC",
            "skills/edit/.pytest_cache/data.json",
        ]
        self.assertEqual(check_distribution.generated_paths(source), [])
        self.assertEqual(check_distribution.generated_paths(source + generated), sorted(generated))

    def test_unusable_registry_file_inventories_are_refused(self) -> None:
        for payload in [
            "not JSON",
            "[]",
            json.dumps({"ok": False}),
            planned([]),
            planned(["skills/edit/SKILL.md"]),
            json.dumps({"ok": True, "result": {"valid": True, "files": [123]}}),
        ]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                check_distribution.distribution_files(payload)

    def test_cli_accepts_the_actual_clean_registry_plan(self) -> None:
        files = ["agent-plugin.yaml", "skills/edit/SKILL.md", "skills/edit/scripts/project.py"]
        response = subprocess.CompletedProcess([], 0, planned(files), "")
        with (
            patch.object(check_distribution.subprocess, "run", return_value=response),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            self.assertEqual(check_distribution.main(["."]), 0)
        self.assertEqual(
            json.loads(output.getvalue()),
            {"ok": True, "distributionFiles": 3, "generatedFiles": []},
        )

    def test_cli_refuses_a_registry_plan_containing_bytecode(self) -> None:
        bytecode = "skills/edit/scripts/__pycache__/project.cpython-312.pyc"
        response = subprocess.CompletedProcess([], 0, planned(["agent-plugin.yaml", bytecode]), "")
        with (
            patch.object(check_distribution.subprocess, "run", return_value=response),
            patch("sys.stdout", new_callable=io.StringIO) as output,
            patch("sys.stderr", new_callable=io.StringIO) as errors,
        ):
            self.assertEqual(check_distribution.main(["."]), 1)
        self.assertEqual(json.loads(output.getvalue())["generatedFiles"], [bytecode])
        self.assertIn("Move generated cache files", errors.getvalue())

    def test_cli_reports_missing_failed_and_unreadable_registry_results(self) -> None:
        responses = [
            FileNotFoundError(),
            subprocess.CompletedProcess([], 1, "", "invalid skill"),
            subprocess.CompletedProcess([], 0, "not JSON", ""),
        ]
        for response in responses:
            with (
                self.subTest(response=response),
                patch("sys.stderr", new_callable=io.StringIO) as errors,
            ):
                mocked = (
                    patch.object(check_distribution.subprocess, "run", side_effect=response)
                    if isinstance(response, Exception)
                    else patch.object(check_distribution.subprocess, "run", return_value=response)
                )
                with mocked:
                    self.assertEqual(check_distribution.main(["."]), 1)
                self.assertTrue(errors.getvalue().strip())


if __name__ == "__main__":
    unittest.main()
