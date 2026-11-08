from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import builtins
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import tomllib
from typing import Any
import unittest
from unittest.mock import patch

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.textTools import Tag
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTCollection, TTFont, newTable
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance
from test_captions import fixture
import font_resources as fonts
import project


def font_file(*, family="Fixture Handoff", bold=False, restricted=0, variable=False):
    style = "Bold" if bold else "Regular"
    ps = family.replace(" ", "") + "-" + style
    with patch("fontTools.fontBuilder.timestampNow", return_value=3400000000):
        builder = FontBuilder(1000)
    builder.setupGlyphOrder([".notdef", "A"])
    builder.setupCharacterMap({65: "A"})
    pen = TTGlyphPen(None)
    pen.moveTo((100, 0))
    pen.lineTo((300, 700))
    pen.lineTo((500, 0))
    pen.closePath()
    builder.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": pen.glyph()})
    builder.setupHorizontalMetrics({".notdef": (600, 0), "A": (600, 100)})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable(
        dict(
            familyName=family,
            styleName=style,
            fullName=family + " " + style,
            psName=ps,
            uniqueFontIdentifier=ps + "-fixture-1.0",
            version="Version 1.0",
            copyright="Fixed fixture copyright",
            licenseDescription="Fixed fixture redistribution notice",
        )
    )
    builder.setupOS2(
        usWeightClass=700 if bold else 400, fsSelection=32 if bold else 64, fsType=restricted
    )
    head: Any = builder.font["head"]
    head.macStyle = 1 if bold else 0
    builder.setupPost()
    if variable:
        table: Any = newTable("fvar")
        axis = Axis()
        axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue = Tag("wght"), 100, 400, 900
        axis.flags, axis.axisNameID = 0, 256
        instance = NamedInstance()
        instance.subfamilyNameID, instance.postscriptNameID, instance.flags = 257, 258, 0
        instance.coordinates = {"wght": 700}
        table.axes, table.instances = [axis], [instance]
        builder.font["fvar"] = table
        for nid, text in ((256, "Weight"), (257, "Named Bold"), (258, "FixtureHandoff-NamedBold")):
            builder.font["name"].setName(text, nid, 3, 1, 0x409)
    output = io.BytesIO()
    builder.font.save(output)
    builder.font.close()
    return output.getvalue()


class FontResourceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.source = self.root / "source.json"
        self.doc = fixture("audio")
        self.doc["timeline"]["captionAttributes"]["fontName"] = "Fixture Handoff"
        self.source.write_bytes(project.encode_document(self.doc))
        self.before = self.source.read_bytes()
        self.expected = project.digest(self.before)
        self.regular = self.root / "Regular.ttf"
        self.bold = self.root / "Bold.ttf"
        self.regular.write_bytes(font_file())
        self.bold.write_bytes(font_file(bold=True))
        self.notice = self.root / "COPYRIGHT.txt"
        self.notice.write_text("Fixed fixture copyright and distribution notice.\n")
        self.request = self.root / "spec.json"
        self.output = self.root / "handoff"
        self.spec: dict[str, Any] = dict(
            schema_version=1,
            redistribution_confirmed=True,
            fonts=[
                self.font_row(self.regular, "FixtureHandoff-Regular"),
                self.font_row(self.bold, "FixtureHandoff-Bold"),
            ],
            licenses=[
                dict(
                    id="fixture",
                    path=self.notice.name,
                    sha256=project.digest(self.notice.read_bytes()),
                )
            ],
        )
        self.closed = patch.object(project, "ensure_closed")
        self.closed.start()
        self.addCleanup(self.closed.stop)

    def font_row(self, path, *names) -> dict[str, Any]:
        return dict(
            path=path.name,
            sha256=project.digest(path.read_bytes()),
            postscript_names=list(names),
            license_id="fixture",
        )

    def stage(self, expected=None):
        self.request.write_text(json.dumps(self.spec))
        return fonts.stage_handoff(
            self.source, self.request, self.output, expected or self.expected
        )

    def manifest(self):
        return project.load(self.output / fonts.MANIFEST)[0]

    def test_static_face_identity_and_optional_parser_do_not_change_font_bytes(self):
        first = self.regular.read_bytes()
        result = fonts.font_faces(first)
        self.assertEqual(result[0]["postscriptName"], "FixtureHandoff-Regular")
        self.assertEqual(result[0]["family"], "Fixture Handoff")
        self.assertEqual(result[0]["weightClass"], 400)
        self.assertEqual(result[0]["embeddingFlags"], 0)
        self.assertEqual(result[0]["variableAxes"], [])
        self.assertEqual(fonts.font_faces(self.bold.read_bytes())[0]["weightClass"], 700)
        self.assertEqual(self.regular.read_bytes(), first)
        self.assertEqual(font_file(), first)

    def test_declared_parser_pin_and_dependency_free_inspection(self):
        manifest = Path(__file__).resolve().parents[1] / "pyproject.toml"
        dependencies = tomllib.loads(manifest.read_text())["project"]["optional-dependencies"]
        self.assertEqual(dependencies["fonts"], [fonts.FONTTOOLS_REQUIREMENT])
        self.assertIn(fonts.FONTTOOLS_REQUIREMENT, dependencies["verification"])
        real_import = builtins.__import__

        def without_parser(name, *args, **kwargs):
            if name == "fontTools.ttLib":
                raise ImportError("parser unavailable")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=without_parser):
            self.assertEqual(fonts.inspect_fonts(self.source, [])["projectSha256"], self.expected)
            with self.assertRaisesRegex(ValueError, fonts.FONTTOOLS_REQUIREMENT):
                fonts.inspect_fonts(self.source, [self.regular])

    def test_collection_and_named_variable_faces_preserve_physical_file_identity(self):
        collection = TTCollection()
        collection.fonts = [
            TTFont(io.BytesIO(self.regular.read_bytes()), recalcTimestamp=False),
            TTFont(io.BytesIO(self.bold.read_bytes()), recalcTimestamp=False),
        ]
        output = io.BytesIO()
        collection.save(output)
        collection.close()
        self.assertEqual(
            [f["postscriptName"] for f in fonts.font_faces(output.getvalue())],
            ["FixtureHandoff-Regular", "FixtureHandoff-Bold"],
        )
        raw = font_file(variable=True)
        result = fonts.font_faces(raw)[0]
        self.assertEqual(
            result["variableAxes"], [dict(tag="wght", minimum=100, default=400, maximum=900)]
        )
        self.assertEqual(result["namedInstances"][0]["postscriptName"], "FixtureHandoff-NamedBold")
        self.assertEqual(fonts.selected_faces([result], ["FixtureHandoff-NamedBold"]), [result])

    def test_inventory_separates_declarations_and_rtf_from_physical_resolution(self):
        self.doc["opaque"] = dict(name="fontName", value="Other Family", rangeStart=0, rangeEnd=3)
        self.doc["rtf"] = dict(text=r"{\rtf1\ansi sample}")
        self.source.write_bytes(project.encode_document(self.doc))
        report = fonts.inspect_fonts(self.source, [self.regular])
        self.assertFalse(report["completeFontClosure"])
        self.assertFalse(report["nativeVerified"])
        self.assertIn("Fixture Handoff", [d["fontName"] for d in report["fontDeclarations"]])
        self.assertEqual(report["unresolvedRTF"], ["/rtf/text"])
        self.assertEqual(
            report["fontFiles"][0]["sha256"], project.digest(self.regular.read_bytes())
        )

    def test_staging_keeps_whole_files_and_notices_independent_and_reruns_as_noop(self):
        report = self.stage()
        self.assertTrue(report["written"])
        self.assertFalse(report["nativeVerified"])
        self.assertFalse(report["completeFontClosure"])
        manifest = self.manifest()
        self.assertEqual(manifest["projectSha256"], self.expected)
        self.assertTrue(fonts.verify_handoff(self.output)["ok"])
        self.assertFalse(self.stage()["written"])
        for src, row in zip(
            [self.notice, self.regular, self.bold], [*manifest["licenses"], *manifest["fonts"]]
        ):
            target = self.output / row["relativePath"]
            self.assertEqual(target.name, src.name)
            self.assertEqual(target.read_bytes(), src.read_bytes())
            self.assertEqual(target.stat().st_nlink, 1)
            self.assertNotEqual(target.stat().st_ino, src.stat().st_ino)
        (self.output / manifest["fonts"][0]["relativePath"]).write_bytes(
            b"independent recipient edit"
        )
        self.assertEqual(self.regular.read_bytes(), font_file())
        self.assertEqual(self.source.read_bytes(), self.before)

    def test_stale_project_and_resource_hashes_refuse_without_output(self):
        with self.assertRaisesRegex(ValueError, "project changed"):
            self.stage(expected="0" * 64)
        for kind in ("fonts", "licenses"):
            original = self.spec[kind][0]["sha256"]
            self.spec[kind][0]["sha256"] = "0" * 64
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "changed"):
                self.stage()
            self.assertFalse(self.output.exists())
            self.spec[kind][0]["sha256"] = original

    def test_rights_license_associations_and_face_selection_require_explicit_matching_inputs(self):
        cases = []
        changed = copy.deepcopy(self.spec)
        changed["redistribution_confirmed"] = False
        cases.append(changed)
        changed = copy.deepcopy(self.spec)
        changed["schema_version"] = True
        cases.append(changed)
        changed = copy.deepcopy(self.spec)
        changed["licenses"] = []
        cases.append(changed)
        changed = copy.deepcopy(self.spec)
        changed["fonts"][0]["license_id"] = "absent"
        cases.append(changed)
        changed = copy.deepcopy(self.spec)
        changed["fonts"][0]["postscript_names"] = ["AbsentFace"]
        cases.append(changed)
        changed = copy.deepcopy(self.spec)
        changed["fonts"][0]["postscript_names"] *= 2
        cases.append(changed)
        for spec in cases:
            self.spec = spec
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                self.stage()
            self.assertFalse(self.output.exists())

    def test_restricted_faces_irrelevant_fonts_and_duplicate_physical_versions_refuse(self):
        self.regular.write_bytes(font_file(restricted=2))
        self.spec["fonts"][0] = self.font_row(self.regular, "FixtureHandoff-Regular")
        with self.assertRaisesRegex(ValueError, "restricted"):
            self.stage()
        self.regular.write_bytes(font_file(family="Unrelated"))
        self.spec["fonts"][0] = self.font_row(self.regular, "Unrelated-Regular")
        with self.assertRaisesRegex(ValueError, "related"):
            self.stage()
        self.regular.write_bytes(font_file())
        self.spec["fonts"][0] = self.font_row(self.regular, "FixtureHandoff-Regular")
        other = self.root / "OtherVersion.ttf"
        other.write_bytes(self.regular.read_bytes())
        self.spec["fonts"].append(self.font_row(other, "FixtureHandoff-Regular"))
        with self.assertRaisesRegex(ValueError, "one physical version"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_verify_refuses_changed_bytes_extra_files_links_and_unsafe_or_unknown_manifests(self):
        self.stage()
        manifest = self.manifest()
        path = self.output / fonts.MANIFEST
        for name in ("../outside.ttf", "/absolute.ttf", "C:/outside.ttf", "fonts\\outside.ttf"):
            candidate = copy.deepcopy(manifest)
            candidate["fonts"][0]["relativePath"] = name
            path.write_bytes(project.encode_document(candidate))
            with self.subTest(name=name), self.assertRaises(ValueError):
                fonts.verify_handoff(self.output)
        candidate = copy.deepcopy(manifest)
        candidate["schema_version"] = 2
        path.write_bytes(project.encode_document(candidate))
        with self.assertRaisesRegex(ValueError, "schema-1"):
            fonts.verify_handoff(self.output)
        path.write_bytes(project.encode_document(manifest))
        extra = self.output / "unexpected.bin"
        extra.write_bytes(b"do not ignore")
        with self.assertRaisesRegex(ValueError, "only independent"):
            fonts.verify_handoff(self.output)
        extra.unlink()
        original = self.output / manifest["fonts"][0]["relativePath"]
        original.unlink()
        original.symlink_to(self.regular)
        with self.assertRaisesRegex(ValueError, "linked/special"):
            fonts.verify_handoff(self.output)

    def test_unknown_selected_face_metadata_and_changed_font_refuse_verification(self):
        self.stage()
        manifest = self.manifest()
        manifest["fonts"][0]["postscriptNames"] = ["AbsentFace"]
        (self.output / fonts.MANIFEST).write_bytes(project.encode_document(manifest))
        with self.assertRaisesRegex(ValueError, "PostScript"):
            fonts.verify_handoff(self.output)
        manifest["fonts"][0]["postscriptNames"] = ["FixtureHandoff-Regular"]
        (self.output / fonts.MANIFEST).write_bytes(project.encode_document(manifest))
        (self.output / manifest["fonts"][0]["relativePath"]).write_bytes(b"modified")
        with self.assertRaisesRegex(ValueError, "content changed"):
            fonts.verify_handoff(self.output)

    def test_copy_and_publication_failures_preserve_originals_and_leave_no_partial_output(self):
        for target in ("copy_snapshot", "publish"):
            self.request.write_text(json.dumps(self.spec))
            boundary = (
                patch.object(fonts.bundles, "copy_snapshot", side_effect=OSError("disk full"))
                if target == "copy_snapshot"
                else patch.object(os, "replace", side_effect=OSError("publish refused"))
            )
            with boundary:
                with self.assertRaises(OSError):
                    fonts.stage_handoff(self.source, self.request, self.output, self.expected)
            self.assertFalse(self.output.exists())
            self.assertFalse(list(self.root.glob(".camtasia-fonts-*")))
            self.assertEqual(self.source.read_bytes(), self.before)
            self.assertEqual(self.regular.read_bytes(), font_file())

    def test_ownership_and_different_occupied_output_are_preserved(self):
        with patch.object(project, "ensure_closed", side_effect=ValueError("close project")):
            with self.assertRaisesRegex(ValueError, "close project"):
                self.stage()
        self.output.mkdir()
        kept = self.output / "owner.bin"
        kept.write_bytes(b"occupied directory")
        with self.assertRaises(ValueError):
            self.stage()
        self.assertEqual(kept.read_bytes(), b"occupied directory")
        self.assertFalse(list(self.root.glob(".camtasia-fonts-*")))

    def test_input_ancestors_and_project_descendants_refuse_without_changes(self):
        self.output = self.root
        with self.assertRaisesRegex(ValueError, "input directories"):
            self.stage()
        bundle = self.root / "source.cmproj"
        bundle.mkdir()
        (bundle / "project.tscproj").write_bytes(self.before)
        self.source = bundle
        self.output = bundle / "handoff"
        with self.assertRaisesRegex(ValueError, "outside the original"):
            self.stage()
        self.assertEqual((bundle / "project.tscproj").read_bytes(), self.before)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob(".camtasia-fonts-*")))

    def test_duplicate_physical_faces_cannot_be_added_by_editing_manifest(self):
        self.stage()
        manifest = self.manifest()
        row = copy.deepcopy(manifest["fonts"][0])
        row["relativePath"] = "fonts/extra/Regular.ttf"
        target = self.output / row["relativePath"]
        target.parent.mkdir()
        target.write_bytes(self.regular.read_bytes())
        manifest["fonts"].append(row)
        (self.output / fonts.MANIFEST).write_bytes(project.encode_document(manifest))
        with self.assertRaisesRegex(ValueError, "one physical version"):
            fonts.verify_handoff(self.output)

    def test_malformed_font_data_and_cli_errors_remain_visible(self):
        for raw in (b"not a font", b"\0\1\0\0broken"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                fonts.font_faces(raw)
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(
                fonts.main(["inspect", str(self.source), "--font", str(self.regular)]), 0
            )
        self.assertEqual(json.loads(stdout.getvalue())["owner"], fonts.OWNER)
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(fonts.main(["verify", str(self.root / "absent")]), 1)
        self.assertIn("nonsymlink", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
