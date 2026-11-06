from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotations import clip, fixture
import annotations
import project


def document():
    doc = fixture(rich=False)
    clip(doc)["def"] = {
        "kind": "TypeWinSVG",
        "shape": "",
        "style": "",
        "width": 200.5,
        "height": 100.25,
        "DrawTime": 1.0,
        "borderWidth": 3.0,
        "borderColorRed": 1.0,
        "borderColorGreen": 1.0,
        "borderColorBlue": 0.0,
        "xmlContent": '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L200 100"/></svg>',
    }
    clip(doc)["metadata"].update(
        {"default-callout-stroke-width": "3", "default-callout-stroke-color": "(255,255,0,255)"}
    )
    return doc


class AnnotationSketchTests(unittest.TestCase):
    def test_inspection_exposes_effective_drawing_companion_separately_from_definition(self):
        doc = document()
        clip(doc)["leftEdgeMods"][0]["duration"] = 2500
        entry = annotations.inventory(doc)[0]
        self.assertEqual(entry["leftEdgeMods"][0]["duration"], 2500)
        self.assertEqual(entry["definition"]["DrawTime"], 1.0)
        entry["leftEdgeMods"][0]["duration"] = 0
        self.assertEqual(clip(doc)["leftEdgeMods"][0]["duration"], 2500)

    def test_native_draw_time_changes_only_edge_duration_and_is_idempotent(self):
        for seconds, ticks in [(0, 0), ("5/2", 2500), (5, 5000)]:
            doc = document()
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            clip(expected)["leftEdgeMods"][0]["duration"] = ticks
            spec = dict(schema_version=1, draw_time=seconds)
            with self.subTest(seconds=seconds):
                result = annotations.edit_annotation(doc, 3, spec)
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(annotations.edit_annotation(result, 3, spec), result)

    def test_compound_stroke_and_timing_preserve_svg_geometry_fade_resets_and_audio(self):
        doc = document()
        expected = copy.deepcopy(doc)
        clip(expected)["leftEdgeMods"][0]["duration"] = 2500
        clip(expected)["def"].update(
            borderWidth=7.0, borderColorRed=0.0, borderColorGreen=128 / 255, borderColorBlue=1.0
        )
        result = annotations.edit_annotation(
            doc,
            3,
            dict(
                schema_version=3,
                draw_time="5/2",
                definition=dict(
                    borderWidth=7,
                    borderColorRed=0,
                    borderColorGreen="128/255",
                    borderColorBlue=1,
                ),
            ),
        )
        self.assertEqual(result, expected)

    def test_zero_stroke_and_static_typed_fields_retain_native_representation(self):
        doc = document()
        clip(doc)["def"]["borderWidth"] = dict(
            type="double", defaultValue=3.0, keyframes=[], opaque=["retain"]
        )
        expected = copy.deepcopy(doc)
        clip(expected)["def"]["borderWidth"]["defaultValue"] = 0.0
        self.assertEqual(
            annotations.edit_annotation(
                doc, 3, dict(schema_version=2, definition={"borderWidth": 0})
            ),
            expected,
        )

    def test_bad_times_and_stroke_values_leave_input_unchanged(self):
        for change in [
            {"draw_time": -1},
            {"draw_time": "5001/1000"},
            {"draw_time": "1/3000"},
            {"draw_time": True},
            {"definition": {"borderWidth": -1}},
            {"definition": {"borderWidth": False}},
            {"definition": {"borderColorRed": 1.01}},
            {"definition": {"borderColorBlue": -0.1}},
            {"definition": {"DrawTime": 2}},
        ]:
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 3, dict(schema_version=1, **change))
            self.assertEqual(doc, before)

    def test_missing_unfamiliar_duplicate_or_invalid_drawing_companions_refuse(self):
        valid = clip(document())["leftEdgeMods"]
        for mods in [
            None,
            [],
            valid * 2,
            [{**valid[0], "duration": True}],
            [{**valid[0], "duration": -1}],
            [{**valid[0], "duration": 6000}],
            [{**valid[0], "duration": "1000"}],
            [{**valid[0], "opaque": 1}],
            [{**valid[0], "group": "Other"}],
            [{**valid[0], "parameters": [{"name": "DrawTime", "func": "Other"}]}],
        ]:
            for change in [{"draw_time": 2}, {"definition": {"borderWidth": 7}}]:
                doc = document()
                clip(doc)["leftEdgeMods"] = mods
                before = copy.deepcopy(doc)
                with (
                    self.subTest(mods=mods, change=change),
                    self.assertRaisesRegex(ValueError, "drawing modifier"),
                ):
                    annotations.edit_annotation(doc, 3, dict(schema_version=1, **change))
                self.assertEqual(doc, before)

    def test_unobserved_owners_clocks_and_other_kinds_refuse(self):
        for modification in [
            {"mediaStart": 500},
            {"scalar": "1/2"},
            {"duration": 0},
        ]:
            doc = document()
            clip(doc).update(modification)
            with (
                self.subTest(modification=modification),
                self.assertRaisesRegex(ValueError, "root"),
            ):
                annotations.edit_annotation(doc, 3, dict(schema_version=1, draw_time=2))
        doc = document()
        node = copy.deepcopy(clip(doc))
        clip(doc).clear()
        clip(doc).update(id=9, _type="Group", tracks=[dict(medias=[node])])
        with self.assertRaisesRegex(ValueError, "root"):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"borderWidth": 7})
            )
        doc = document()
        clip(doc)["def"]["kind"] = "remix"
        with self.assertRaisesRegex(ValueError, "root"):
            annotations.edit_annotation(doc, 3, dict(schema_version=1, draw_time=2))
        with self.assertRaisesRegex(ValueError, "supported existing"):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"borderWidth": 7})
            )

    def test_missing_or_animated_stroke_refuses_without_partial_timing_update(self):
        for value in [
            None,
            dict(type="double", keyframes=[]),
            dict(type="double", defaultValue=3.0, keyframes=[dict(time=0, value=7)]),
        ]:
            doc = document()
            if value is None:
                del clip(doc)["def"]["borderWidth"]
            else:
                clip(doc)["def"]["borderWidth"] = value
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, draw_time=2, definition={"borderWidth": 7})
                )
            self.assertEqual(doc, before)

    def test_cli_exclusive_staging_reports_actual_change_without_writing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, spec, output = (
                root / name for name in ("source.json", "spec.json", "out.json")
            )
            data = project.encode_document(document())
            source.write_bytes(data)
            spec.write_text(json.dumps(dict(schema_version=1, draw_time="5/2")))
            args = [
                "set",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(spec),
                "--output",
                str(output),
            ]
            for written in (True, False):
                stdout = io.StringIO()
                with patch("sys.stdout", stdout):
                    self.assertEqual(annotations.main(args), 0)
                report = json.loads(stdout.getvalue())
                self.assertTrue(report["changed"])
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(clip(project.load(output)[0])["leftEdgeMods"][0]["duration"], 2500)
            self.assertEqual(source.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
