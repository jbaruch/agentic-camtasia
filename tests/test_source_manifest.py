from __future__ import annotations

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import project  # noqa: E402


class SourceManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bundle = self.root / "Film.cmproj"
        (self.bundle / "media").mkdir(parents=True)
        self.media = self.bundle / "media/日本語 media.bin"
        self.payload = b"native source retention\x00" * 70000
        self.media.write_bytes(self.payload)
        self.doc = {
            "version": "10.0",
            "sourceBin": [
                {"id": 3, "src": "./media/日本語 media.bin", "opaque": {"preserve": True}}
            ],
            "timeline": {},
            "opaque": {"src": "not a source"},
        }
        self.raw = project.encode_document(self.doc)

    def test_hashes_relative_unicode_source_without_mutation(self) -> None:
        original = copy.deepcopy(self.doc)
        report = project.source_manifest(self.doc, self.raw, self.bundle)
        self.assertTrue(report["ok"])
        self.assertTrue(report["allSourcesBundled"])
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["owner"], "camtasia-source-manifest")
        self.assertEqual(report["projectSha256"], hashlib.sha256(self.raw).hexdigest())
        source = report["sources"][0]
        self.assertEqual(source["sha256"], hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(source["sizeBytes"], len(self.payload))
        self.assertEqual(source["sourceId"], 3)
        self.assertEqual(source["path"], "/sourceBin/0/src")
        self.assertEqual(self.doc, original)
        self.assertEqual(self.media.read_bytes(), self.payload)

    def test_absolute_parent_escape_and_external_symlink_are_not_bundled(self) -> None:
        external = self.root / "outside.bin"
        external.write_bytes(b"external")
        (self.bundle / "media/link.bin").symlink_to(external)
        for stored in [str(self.media), "../outside.bin", "./media/link.bin"]:
            self.doc["sourceBin"][0]["src"] = stored
            with self.subTest(stored=stored):
                report = project.source_manifest(self.doc, self.raw, self.bundle)
                self.assertTrue(report["ok"])
                self.assertFalse(report["allSourcesBundled"])
                self.assertFalse(report["sources"][0]["bundled"])

    def test_missing_directory_url_and_foreign_path_never_gain_hashes(self) -> None:
        for stored, status in [
            ("missing.mp4", "missing"),
            ("media", "missing"),
            ("https://example.test/source.mp4", "unchecked"),
            ("file:///outside/source.mp4", "unchecked"),
            ("C:\\Media\\source.mp4", "unchecked"),
            ("\\\\server\\share\\source.mp4", "unchecked"),
        ]:
            self.doc["sourceBin"][0]["src"] = stored
            with self.subTest(stored=stored):
                report = project.source_manifest(self.doc, self.raw, self.bundle)
                self.assertFalse(report["ok"])
                self.assertFalse(report["allSourcesBundled"])
                self.assertEqual(report["sources"][0]["status"], status)
                self.assertIsNone(report["sources"][0]["sha256"])

    def test_empty_source_bin_and_logical_assets_have_separate_scope(self) -> None:
        doc = {
            "timeline": {
                "effectName": "DeviceFrameEffect",
                "parameters": {"deviceFrameSource": "Desktop_1.mp4"},
            }
        }
        report = project.source_manifest(doc, b"{}", self.bundle)
        self.assertTrue(report["ok"])
        self.assertTrue(report["allSourcesBundled"])
        self.assertEqual(report["sources"], [])
        self.assertEqual(report["assetReferences"][0]["reference"], "Desktop_1.mp4")
        self.assertIn("not complete native dependency", report["limits"][0])

    def test_invalid_source_shapes_and_identities_are_refused(self) -> None:
        for sources in [
            {},
            [None],
            [{"id": True, "src": "x"}],
            [{"id": 1, "src": ""}],
            [{"id": 1, "src": "bad\0path"}],
            [{"id": 1, "src": "x"}, {"id": 1, "src": "y"}],
        ]:
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                project.source_manifest({"sourceBin": sources}, b"{}", self.bundle)

    def test_file_change_during_hash_is_refused(self) -> None:
        before = self.media.stat()
        after = SimpleNamespace(
            st_dev=before.st_dev,
            st_ino=before.st_ino,
            st_size=before.st_size + 1,
            st_mtime_ns=before.st_mtime_ns,
            st_ctime_ns=before.st_ctime_ns,
        )
        with patch.object(os, "fstat", side_effect=[before, after]):
            with self.assertRaisesRegex(ValueError, "changed while hashing"):
                project.source_file_digest(self.media)

    def test_symlink_retarget_during_hash_is_refused(self) -> None:
        link = self.bundle / "media/link.bin"
        other = self.bundle / "media/other.bin"
        other.write_bytes(b"different")
        link.symlink_to(self.media)
        self.doc["sourceBin"][0]["src"] = "./media/link.bin"
        original = project.source_file_digest

        def changed(path: Path) -> dict:
            result = original(path)
            link.unlink()
            link.symlink_to(other)
            return result

        with patch.object(project, "source_file_digest", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "link changed while hashing"):
                project.source_manifest(self.doc, self.raw, self.bundle)

    def test_cli_uses_destination_root_and_reports_unresolved_sources(self) -> None:
        staged = self.root / "candidate.json"
        staged.write_bytes(self.raw)
        output = io.StringIO()
        with patch("sys.stdout", output):
            code = project.main(["source-manifest", str(staged), "--media-root", str(self.bundle)])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["allSourcesBundled"])
        output = io.StringIO()
        with patch("sys.stdout", output):
            code = project.main(["source-manifest", str(staged)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["sources"][0]["status"], "missing")
        self.assertEqual(staged.read_bytes(), self.raw)


if __name__ == "__main__":
    unittest.main()
