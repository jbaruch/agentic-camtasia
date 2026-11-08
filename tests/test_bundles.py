from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from test_captions import fixture
import bundles
import project


class BundleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.source = self.root / "Original.cmproj"
        (self.source / "media").mkdir(parents=True)
        (self.source / "empty").mkdir()
        (self.source / "media/source.wav").write_bytes(b"fixed audio source\x00" * 100)
        (self.source / "companion.bin").write_bytes(b"unknown companion\x00")
        (self.source / "companion.bin").chmod(0o640)
        self.doc = fixture("audio")
        self.doc["sourceBin"][0]["src"] = "./media/source.wav"
        self.output = self.root / "Candidate.cmproj"
        self.save()
        self.closed = patch.object(project, "ensure_closed")
        self.closed.start()
        self.addCleanup(self.closed.stop)

    def save(self):
        self.raw = project.encode_document(self.doc)
        (self.source / "project.tscproj").write_bytes(self.raw)
        self.expected = project.digest(self.raw)

    def stage(self, **changes):
        return bundles.stage_bundle(
            changes.get("source", self.source),
            changes.get("output", self.output),
            changes.get("expected", self.expected),
            changes.get("selected", [1]),
        )

    def external(self, folder="outside", content=b"external bytes"):
        parent = self.root / folder
        parent.mkdir()
        path = parent / "日本語 audio.wav"
        path.write_bytes(content)
        return path

    def test_complete_bundle_preserves_unknown_companions_modes_and_internal_references(self):
        before = bundles.tree(self.source)
        report = self.stage()
        self.assertTrue(report["written"])
        self.assertFalse(report["nativeVerified"])
        self.assertEqual(project.load(self.output)[0], self.doc)
        self.assertEqual(bundles.tree(self.output), before)
        self.assertEqual(bundles.tree(self.source), before)
        self.assertTrue(report["destination"]["allSourcesBundled"])
        for name in before[1]:
            self.assertNotEqual(
                (self.source / name).stat().st_ino, (self.output / name).stat().st_ino
            )
            self.assertEqual((self.output / name).stat().st_nlink, 1)

    def test_external_basename_collisions_get_distinct_relative_slots_without_changing_payload(
        self,
    ):
        first, second = self.external("one", b"first"), self.external("two", b"second")
        self.doc["sourceBin"][0]["src"] = str(first)
        other = copy.deepcopy(self.doc["sourceBin"][0])
        other.update(id=9, src=str(second), future={"retain": True})
        self.doc["sourceBin"].append(other)
        (self.source / "media-packed").mkdir()
        (self.source / "media-packed/retain.txt").write_bytes(b"do not replace")
        self.save()
        report = self.stage(selected=[1, 9])
        candidate = project.load(self.output)[0]
        expected = copy.deepcopy(self.doc)
        for entry in expected["sourceBin"]:
            entry["src"] = f"./media-packed-1/source-{entry['id']}/日本語 audio.wav"
        self.assertEqual(candidate, expected)
        self.assertEqual(
            [Path(self.output / e["src"]).read_bytes() for e in candidate["sourceBin"]],
            [b"first", b"second"],
        )
        self.assertEqual((self.output / "media-packed/retain.txt").read_bytes(), b"do not replace")
        self.assertEqual((self.source / "project.tscproj").read_bytes(), self.raw)
        self.assertTrue(report["destination"]["allSourcesBundled"])

    def test_external_symlinks_and_hardlinks_become_regular_independent_files(self):
        external = self.external()
        alias = external.with_name("linked.wav")
        os.link(external, alias)
        link = external.with_name("selected.wav")
        link.symlink_to(alias)
        self.doc["sourceBin"][0]["src"] = str(link)
        os.link(self.source / "companion.bin", self.source / "hard-companion.bin")
        self.save()
        inspected = bundles.inspect_bundle(self.source)[2]
        row = inspected["sources"]["sources"][0]
        self.assertTrue(row["symlink"])
        self.assertEqual(row["hardLinkCount"], 2)
        self.stage()
        entry = project.load(self.output)[0]["sourceBin"][0]
        copied = self.output / entry["src"]
        self.assertFalse(copied.is_symlink())
        self.assertEqual(copied.stat().st_nlink, 1)
        self.assertEqual(copied.name, "selected.wav")
        copied.write_bytes(b"independent edit")
        (self.output / "companion.bin").write_bytes(b"independent companion edit")
        self.assertEqual(external.read_bytes(), b"external bytes")
        self.assertEqual((self.source / "companion.bin").read_bytes(), b"unknown companion\x00")
        self.assertEqual(
            (self.output / "hard-companion.bin").read_bytes(), b"unknown companion\x00"
        )

    def test_identical_rerun_is_noop_but_different_or_aliased_outputs_refuse(self):
        self.stage()
        self.assertFalse(self.stage()["written"])
        (self.output / "extra").write_bytes(b"retain occupied output")
        before = bundles.tree(self.output)
        with self.assertRaisesRegex(ValueError, "different data"):
            self.stage()
        self.assertEqual(bundles.tree(self.output), before)
        for output in [self.source, self.source / "nested.cmproj"]:
            with self.subTest(output=output), self.assertRaises(ValueError):
                self.stage(output=output)
        linked = self.root / "Alias.cmproj"
        linked.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.stage(output=linked)
        self.assertEqual((self.source / "project.tscproj").read_bytes(), self.raw)

    def test_matching_output_with_a_hardlinked_companion_is_not_independent(self):
        self.stage()
        target = self.output / "companion.bin"
        target.unlink()
        os.link(self.source / "companion.bin", target)
        with self.assertRaisesRegex(ValueError, "hard-linked"):
            self.stage()
        self.assertEqual(target.read_bytes(), b"unknown companion\x00")

    def test_stale_hash_selection_and_unverified_identity_refuse_without_output(self):
        for changes in [
            dict(expected="0" * 64),
            dict(expected="invalid"),
            dict(selected=[]),
            dict(selected=[1, 1]),
            dict(selected=[True]),
            dict(selected=[2]),
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.stage(**changes)
            self.assertFalse(self.output.exists())
        self.doc["authoringClientName"]["version"] = "unverified"
        self.save()
        with self.assertRaisesRegex(ValueError, "verified Mac"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_missing_remote_and_foreign_sources_refuse_without_partial_output(self):
        for stored in ["absent.wav", "https://example.test/speech.wav", r"C:\Media\speech.wav"]:
            self.doc["sourceBin"][0]["src"] = stored
            self.save()
            with self.subTest(stored=stored), self.assertRaises(ValueError):
                self.stage()
            self.assertFalse(self.output.exists())
            self.assertFalse(list(self.root.glob(".camtasia-bundle-*")))

    def test_bundle_symlinks_special_files_fonts_and_application_resources_refuse(self):
        link = self.source / "alias"
        link.symlink_to(self.source / "companion.bin")
        with self.assertRaisesRegex(ValueError, "linked/special"):
            self.stage()
        link.unlink()
        os.mkfifo(link)
        with self.assertRaisesRegex(ValueError, "linked/special"):
            self.stage()
        link.unlink()
        for stored in [self.source / "private.otf", self.source / "Vendor.app/resource.bin"]:
            stored.parent.mkdir(exist_ok=True)
            stored.write_bytes(b"do not redistribute")
            with (
                self.subTest(stored=stored),
                self.assertRaisesRegex(ValueError, "physical fonts/application"),
            ):
                self.stage()
            stored.unlink()
        self.assertFalse(self.output.exists())

    def test_ownership_refusal_before_or_after_copy_leaves_inputs_and_no_partial_output(self):
        before = bundles.tree(self.source)
        for results in [
            [ValueError("save and close project")],
            [None, ValueError("new live handle")],
        ]:
            with patch.object(project, "ensure_closed", side_effect=results):
                with self.assertRaises(ValueError):
                    self.stage()
            self.assertEqual(bundles.tree(self.source), before)
            self.assertFalse(self.output.exists())
            self.assertFalse(list(self.root.glob(".camtasia-bundle-*")))

    def test_changed_companion_is_detected_and_owned_staging_is_cleaned(self):
        original = bundles.copy_snapshot

        def changed(source, output, expected):
            original(source, output, expected)
            if source.name == "companion.bin":
                source.write_bytes(b"simultaneous external edit")

        with patch.object(bundles, "copy_snapshot", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "changed"):
                self.stage()
        self.assertEqual(
            (self.source / "companion.bin").read_bytes(), b"simultaneous external edit"
        )
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob(".camtasia-bundle-*")))

    def test_copy_failure_does_not_publish_or_remove_an_occupied_output(self):
        self.output.mkdir()
        (self.output / "owner.bin").write_bytes(b"existing owner bytes")
        with patch.object(bundles, "copy_snapshot", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                self.stage()
        self.assertEqual((self.output / "owner.bin").read_bytes(), b"existing owner bytes")
        self.assertFalse(list(self.root.glob(".camtasia-bundle-*")))

    def test_publication_failure_removes_only_the_owned_empty_reservation(self):
        before = bundles.tree(self.source)
        with patch.object(os, "replace", side_effect=OSError("publish failed")):
            with self.assertRaisesRegex(OSError, "publish failed"):
                self.stage()
        self.assertEqual(bundles.tree(self.source), before)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob(".camtasia-bundle-*")))

    def test_unreadable_companion_directory_refuses_instead_of_silently_omitting_it(self):
        scan = os.scandir

        def unreadable(path):
            if Path(path) == self.source / "empty":
                raise PermissionError("cannot read companion directory")
            return scan(path)

        with patch.object(os, "scandir", side_effect=unreadable):
            with self.assertRaisesRegex(PermissionError, "companion directory"):
                self.stage()
        self.assertFalse(self.output.exists())

    def test_external_physical_font_and_app_resources_are_not_pulled_into_bundle(self):
        for name in ("private.otf", "Vendor.app/Contents/resource.bin"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"retain outside project")
            self.doc["sourceBin"][0]["src"] = str(path)
            self.save()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "physical fonts"):
                self.stage()
            self.assertEqual(path.read_bytes(), b"retain outside project")
            self.assertFalse(self.output.exists())

    def test_cli_reports_live_sources_and_stages_without_claiming_native_verification(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(bundles.main(["inspect", str(self.source)]), 0)
        report = json.loads(out.getvalue())
        self.assertEqual((report["schema_version"], report["owner"]), (1, "camtasia-bundles"))
        self.assertEqual(report["sources"]["sources"][0]["referenceKind"], "relative")
        self.assertEqual(report["companions"]["companion.bin"]["mode"], stat.S_IMODE(0o640))
        out, err = io.StringIO(), io.StringIO()
        args = [
            "stage",
            str(self.source),
            "--expected-sha256",
            self.expected,
            "--copy-source",
            "1",
            "--output",
            str(self.output),
        ]
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(bundles.main(args), 0, err.getvalue())
        self.assertFalse(json.loads(out.getvalue())["nativeVerified"])
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            self.assertEqual(bundles.main(["inspect", str(self.root / "missing.cmproj")]), 1)
        self.assertIn("select a saved", err.getvalue())


if __name__ == "__main__":
    unittest.main()
