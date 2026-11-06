from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_annotations import fixture, clip
import annotations
import project


def document():
    doc = fixture()
    definition = clip(doc)["def"]
    definition.update({"resize-behavior": "resizeText", "enable-ligatures": 1.0, "word-wrap": 1.0})
    return doc


class AnnotationLayoutTests(unittest.TestCase):
    def test_sizing_and_ligatures_change_only_requested_native_fields(self):
        doc = document()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        clip(expected)["def"].update({"resize-behavior": "resizeCallout", "enable-ligatures": 0.0})
        result = annotations.edit_annotation(
            doc,
            3,
            dict(
                schema_version=1,
                definition={"resize-behavior": "resizeCallout", "enable-ligatures": 0},
            ),
        )
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertIs(type(clip(result)["def"]["enable-ligatures"]), float)
        self.assertEqual(
            annotations.edit_annotation(
                result,
                3,
                dict(
                    schema_version=1,
                    definition={"resize-behavior": "resizeCallout", "enable-ligatures": 0},
                ),
            ),
            result,
        )

    def test_restore_preserves_native_reset_companions_and_rich_style_partitions(self):
        doc = document()
        clip(doc)["def"].update({"resize-behavior": "resizeCallout", "enable-ligatures": 0.0})
        clip(doc)["metadata"].update(
            {
                "default-callout-resize-behavior": "resizeText",
                "default-callout-enable-ligatures": "1",
            }
        )
        doc = annotations.edit_annotation(
            doc,
            3,
            dict(schema_version=2, rich_ranges=[dict(start=1, end=3, rich=dict(fontWeight=700))]),
        )
        expected = copy.deepcopy(doc)
        clip(expected)["def"].update({"resize-behavior": "resizeText", "enable-ligatures": 1.0})
        self.assertEqual(
            annotations.edit_annotation(
                doc,
                3,
                dict(
                    schema_version=2,
                    definition={"resize-behavior": "resizeText", "enable-ligatures": "1/1"},
                ),
            ),
            expected,
        )

    def test_layout_only_edits_keep_timed_rich_styles_and_independent_geometry(self):
        doc = document()
        frames = clip(doc)["def"]["textAttributes"]["keyframes"]
        frame = copy.deepcopy(frames[0])
        frame.update(time=2000, endTime=2000)
        for run in frame["value"]:
            if run["name"] == "fontSize":
                run["value"] = 32.0
        frames.append(frame)
        expected = copy.deepcopy(doc)
        clip(expected)["def"]["resize-behavior"] = "resizeCallout"
        self.assertEqual(
            annotations.edit_annotation(
                doc, 3, dict(schema_version=3, definition={"resize-behavior": "resizeCallout"})
            ),
            expected,
        )

    def test_flag_edit_preserves_static_typed_representation_and_refuses_animation(self):
        doc = document()
        p: dict[str, Any] = dict(
            type="double",
            defaultValue=1.0,
            interp="linr",
            uiHints={"opaque": 1},
            valueBounds={"minValue": 0, "maxValue": 1},
            opaque=["retain"],
        )
        clip(doc)["def"]["enable-ligatures"] = p
        expected = copy.deepcopy(doc)
        clip(expected)["def"]["enable-ligatures"]["defaultValue"] = 0.0
        self.assertEqual(
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"enable-ligatures": 0})
            ),
            expected,
        )
        p["keyframes"] = [dict(time=0, endTime=1000, duration=1000, value=0.0)]
        before = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"enable-ligatures": 0})
            )
        self.assertEqual(doc, before)

    def test_unsupported_choices_flags_and_missing_fields_refuse_atomically(self):
        for name, value in [
            ("resize-behavior", "none"),
            ("resize-behavior", 0),
            ("resize-behavior", True),
            ("enable-ligatures", -1),
            ("enable-ligatures", 2),
            ("enable-ligatures", "1/2"),
            ("enable-ligatures", False),
        ]:
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={name: value})
                )
            self.assertEqual(doc, before)
        for name, value in [("resize-behavior", "resizeCallout"), ("enable-ligatures", 0)]:
            doc = document()
            clip(doc)["def"].pop(name)
            before = copy.deepcopy(doc)
            with self.subTest(missing=name), self.assertRaisesRegex(ValueError, "capture"):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={name: value})
                )
            self.assertEqual(doc, before)
        doc = document()
        before = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            annotations.edit_annotation(
                doc,
                3,
                dict(
                    schema_version=1,
                    definition={"resize-behavior": "resizeCallout", "enable-ligatures": 2},
                ),
            )
        self.assertEqual(doc, before)

    def test_cli_candidate_repeat_and_input_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            settings = root / "settings.json"
            output = root / "candidate.json"
            source.write_bytes(project.encode_document(document()))
            before = source.read_bytes()
            settings.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        definition={"resize-behavior": "resizeCallout", "enable-ligatures": 0},
                    )
                )
            )
            args = [
                "set",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(settings),
                "--output",
                str(output),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(annotations.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            expected = document()
            clip(expected)["def"].update(
                {"resize-behavior": "resizeCallout", "enable-ligatures": 0.0}
            )
            self.assertEqual(project.load(output)[0], expected)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
