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


def document(kind="TypeWinBlur"):
    doc = fixture()
    definition = clip(doc)["def"]
    definition.clear()
    definition.update(
        kind=kind,
        shape="",
        style="",
        width=240.0,
        height=140.0,
        **{"corner-radius": 6.0, "opaque": ["keep"]},
    )
    defaults = {
        "TypeWinBlur": {"intensity": 0.8125, "blur-invert": 0.0},
        "TypeWinPixelate": {"intensity": 0.33},
        "TypeWinSpotlight": {"intensity": 0.5},
        "TypeWinHighlighter": {
            "fill-invert": 0.0,
            "fillColorRed": 0.0,
            "fillColorGreen": 1.0,
            "fillColorBlue": 0.0,
            "fill-color-opacity": 0.25,
        },
    }
    definition.update(defaults[kind])
    return doc


class AnnotationRegionTests(unittest.TestCase):
    def test_static_strength_on_each_native_region_kind_changes_only_its_definition_value(self):
        for kind, value in [
            ("TypeWinBlur", 0.4),
            ("TypeWinPixelate", 0.6),
            ("TypeWinSpotlight", 0.75),
        ]:
            doc = document(kind)
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            clip(expected)["def"]["intensity"] = value
            with self.subTest(kind=kind):
                result = annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={"intensity": value})
                )
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(
                    annotations.edit_annotation(
                        result, 3, dict(schema_version=1, definition={"intensity": value})
                    ),
                    result,
                )

    def test_both_inversion_controls_preserve_geometry_effects_resets_and_audio(self):
        for kind, name in [("TypeWinBlur", "blur-invert"), ("TypeWinHighlighter", "fill-invert")]:
            doc = document(kind)
            clip(doc)["metadata"]["default-callout-" + name] = "0"
            expected = copy.deepcopy(doc)
            clip(expected)["def"][name] = 1.0
            with self.subTest(kind=kind):
                self.assertEqual(
                    annotations.edit_annotation(
                        doc, 3, dict(schema_version=1, definition={name: 1})
                    ),
                    expected,
                )

    def test_highlight_rgb_uses_existing_legacy_names_without_inventing_aliases(self):
        doc = document("TypeWinHighlighter")
        expected = copy.deepcopy(doc)
        clip(expected)["def"].update(
            fillColorRed=1.0,
            fillColorGreen=128 / 255,
            fillColorBlue=0.0,
            **{"fill-color-opacity": 0.5, "fill-invert": 1.0},
        )
        result = annotations.edit_annotation(
            doc,
            3,
            dict(
                schema_version=2,
                definition={
                    "fillColorRed": 1,
                    "fillColorGreen": "128/255",
                    "fillColorBlue": 0,
                    "fill-color-opacity": 0.5,
                    "fill-invert": 1,
                },
            ),
        )
        self.assertEqual(result, expected)
        self.assertNotIn("fill-color-red", clip(result)["def"])
        with self.assertRaisesRegex(ValueError, "capture"):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"fill-color-red": 1})
            )

    def test_static_typed_strength_preserves_every_descriptor_and_opaque_field(self):
        doc = document("TypeWinSpotlight")
        p: dict[str, Any] = dict(
            type="double",
            defaultValue=0.5,
            interp="linr",
            uiHints={"unitType": 0},
            valueBounds={"minValue": 0.0, "maxValue": 1.0},
            opaque=["retain"],
            keyframes=[],
        )
        clip(doc)["def"]["intensity"] = p
        expected = copy.deepcopy(doc)
        clip(expected)["def"]["intensity"]["defaultValue"] = 0.75
        self.assertEqual(
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"intensity": "3/4"})
            ),
            expected,
        )
        p["keyframes"] = [dict(time=0, endTime=1000, duration=1000, value=0.25)]
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "animated"):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"intensity": 0.75})
            )
        self.assertEqual(doc, before)

    def test_regions_do_not_admit_generic_intensity_or_cross_kind_fields(self):
        for kind, name in [
            ("remix", "intensity"),
            ("TypeWinHighlighter", "intensity"),
            ("TypeWinPixelate", "blur-invert"),
            ("TypeWinBlur", "fill-invert"),
            ("TypeWinSpotlight", "fillColorRed"),
        ]:
            doc = document()
            clip(doc)["def"]["kind"] = kind
            clip(doc)["def"][name] = 0.5
            before = copy.deepcopy(doc)
            with (
                self.subTest(kind=kind, name=name),
                self.assertRaisesRegex(ValueError, "supported existing"),
            ):
                annotations.edit_annotation(doc, 3, dict(schema_version=1, definition={name: 0}))
            self.assertEqual(doc, before)

    def test_numeric_ranges_flags_and_missing_fields_refuse_without_partial_mutation(self):
        for kind, name, value in [
            ("TypeWinBlur", "intensity", -1),
            ("TypeWinPixelate", "intensity", 1.1),
            ("TypeWinSpotlight", "intensity", True),
            ("TypeWinHighlighter", "fillColorBlue", 2),
            ("TypeWinHighlighter", "fill-invert", 0.5),
            ("TypeWinBlur", "blur-invert", False),
        ]:
            doc = document(kind)
            before = copy.deepcopy(doc)
            with self.subTest(kind=kind, name=name, value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={name: value})
                )
            self.assertEqual(doc, before)
        doc = document()
        clip(doc)["def"].pop("intensity")
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "capture"):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"blur-invert": 1, "intensity": 0.4})
            )
        self.assertEqual(doc, before)
        doc = document("TypeWinHighlighter")
        before = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"fillColorRed": 1, "fillColorGreen": -1})
            )
        self.assertEqual(doc, before)

    def test_unknown_or_animated_structured_parameters_remain_unflattened(self):
        for value in (
            {"type": "double"},
            {"type": "point", "defaultValue": [0, 0, 0]},
            {"type": "double", "defaultValue": 0.5, "keyframes": "unknown"},
        ):
            doc = document("TypeWinSpotlight")
            clip(doc)["def"]["intensity"] = value
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={"intensity": 0.75})
                )
            self.assertEqual(doc, before)

    def test_cli_stages_native_unit_edits_repeats_and_keeps_input_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            settings = root / "spec.json"
            output = root / "candidate.json"
            source.write_bytes(project.encode_document(document()))
            before = source.read_bytes()
            settings.write_text(
                json.dumps(dict(schema_version=1, definition={"intensity": 0.4, "blur-invert": 1}))
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
                r = json.loads(stream.getvalue())
                self.assertEqual(r["written"], written)
                self.assertFalse(r["nativeVerified"])
            expected = document()
            clip(expected)["def"].update(intensity=0.4, **{"blur-invert": 1.0})
            self.assertEqual(project.load(output)[0], expected)
            self.assertEqual(source.read_bytes(), before)
            settings.write_text(
                json.dumps(dict(schema_version=1, definition={"intensity": 0.4, "blur-invert": 2}))
            )
            missing = root / "missing.json"
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(annotations.main(args[:-1] + [str(missing)]), 1)
            self.assertFalse(missing.exists())
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
