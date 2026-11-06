from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotation_text_layout import document, leaf
import animations
import project


WHITE = {
    "kind": "remix",
    "shape": "shape-rectangle",
    "style": "basic",
    "corner-radius": 8.0,
    "fill-color-blue": 1.0,
    "fill-color-green": 1.0,
    "fill-color-red": 1.0,
    "fill-color-opacity": 1.0,
    "fill-style": "solid",
    "stroke-color-blue": 1.0,
    "stroke-color-green": 1.0,
    "stroke-color-red": 1.0,
    "stroke-color-opacity": 1.0,
    "stroke-width": 0.0,
    "stroke-style": "solid",
    "width": 240.0,
    "height": 180.0,
}
TARGETS = {
    "fill-color-red": 0.0,
    "fill-color-green": 0.501960784313725,
    "fill-color-opacity": 0.5,
    "stroke-color-blue": 0.0,
    "stroke-color-green": 0.250980392156863,
    "stroke-color-opacity": 0.75,
    "stroke-width": 12.0,
}


def fixture(depth=0):
    doc = document(depth)
    leaf(doc)["def"] = copy.deepcopy(WHITE)
    leaf(doc)["parameters"] = {
        "geometryCrop0": 0.0,
        "geometryCrop1": 0.0,
        "geometryCrop2": 0.0,
        "geometryCrop3": 0.0,
    }
    return doc


def request(**fields):
    return dict(schema_version=2, start=1, end=2, definition=TARGETS, **fields)


def native_frame(value, start=1000, end=2000):
    return dict(time=start, endTime=end, duration=end - start, value=value)


class RemixStyleAnimationTests(unittest.TestCase):
    def test_non_remix_owners_and_non_group_ancestors_refuse_style_edits(self):
        for scenario in ["image", "region", "stitched"]:
            doc = fixture(1 if scenario == "stitched" else 0)
            if scenario == "image":
                leaf(doc)["_type"] = "IMFile"
            elif scenario == "region":
                leaf(doc)["def"]["kind"] = "TypeWinHighlighter"
            else:
                project.scene_tracks(doc)[0][0]["medias"][0]["_type"] = "StitchedMedia"
            before = copy.deepcopy(doc)
            with self.subTest(scenario=scenario), self.assertRaisesRegex(ValueError, "remix"):
                animations.edit_interval(doc, 3, request())
            self.assertEqual(doc, before)

    def test_native_constant_nondefault_scale_companions_ease_and_restore_initial_scale(self):
        doc = animations.edit_interval(fixture(), 3, request())
        for name in ["scale0", "scale1"]:
            leaf(doc)["parameters"][name] = dict(
                type="double", defaultValue=0.9, keyframes=[native_frame(0.9)]
            )
        result = animations.edit_interval(
            doc, 3, dict(schema_version=1, start=1, end=2, values={}, easing="linear")
        )
        expected = copy.deepcopy(doc)
        leaf(expected)["animationTracks"]["visual"][0]["interp"] = "linr"
        for name in TARGETS:
            leaf(expected)["def"][name]["keyframes"][0]["interp"] = "linr"
        for name in ["scale0", "scale1"]:
            leaf(expected)["parameters"][name]["keyframes"][0]["interp"] = "linr"
        self.assertEqual(result, expected)
        expected = fixture()
        leaf(expected)["parameters"].update(scale0=0.9, scale1=0.9)
        self.assertEqual(animations.remove_interval(result, 3, 1, 2), expected)

    def test_native_fill_stroke_and_geometry_shape_with_fixed_expected_targets(self):
        doc = fixture()
        expected = copy.deepcopy(doc)
        for name, value in TARGETS.items():
            leaf(expected)["def"][name] = dict(
                type="double", defaultValue=WHITE[name], keyframes=[native_frame(value)]
            )
        leaf(expected)["parameters"]["translation0"] = dict(
            type="double", defaultValue=0.0, keyframes=[native_frame(60.0)]
        )
        leaf(expected)["animationTracks"]["visual"] = [dict(endTime=2000, duration=1000)]
        spec = request(values={"translation0": 60}, initial={"translation0": 0})
        result = animations.edit_interval(doc, 3, spec)
        self.assertEqual(result, expected)
        self.assertEqual(doc, fixture())
        self.assertEqual(animations.edit_interval(result, 3, spec), result)

    def test_ease_and_remove_restore_explicit_native_style_scalars_in_groups(self):
        for depth in [0, 1, 3]:
            doc = fixture(depth)
            original = copy.deepcopy(doc)
            result = animations.edit_interval(doc, 3, request())
            for easing, code in [
                ("auto", None),
                ("linear", "linr"),
                ("exponential", "eioe"),
                ("bounce", "bnce"),
                ("spring", "sprg"),
            ]:
                with self.subTest(depth=depth, easing=easing):
                    eased = animations.edit_interval(
                        result, 3, dict(schema_version=1, start=1, end=2, values={}, easing=easing)
                    )
                    expected = copy.deepcopy(result)
                    if code is not None:
                        leaf(expected)["animationTracks"]["visual"][0]["interp"] = code
                        for name in TARGETS:
                            leaf(expected)["def"][name]["keyframes"][0]["interp"] = code
                    self.assertEqual(eased, expected)
                    self.assertEqual(animations.remove_interval(eased, 3, 1, 2), original)
            self.assertEqual(doc, original)

    def test_trimmed_double_speed_group_uses_source_bounds_without_changing_ancestors(self):
        doc = fixture(2)
        leaf(doc).update(start=7000, mediaStart=3000, scalar="1/2")
        expected = copy.deepcopy(doc)
        for name, value in TARGETS.items():
            leaf(expected)["def"][name] = dict(
                type="double", defaultValue=WHITE[name], keyframes=[native_frame(value, 5000, 7000)]
            )
        leaf(expected)["animationTracks"]["visual"] = [dict(endTime=7000, duration=2000)]
        self.assertEqual(animations.edit_interval(doc, 3, request()), expected)

    def test_text_shape_fill_curves_preserve_timed_rich_and_coupled_text_outline(self):
        doc = document(1)
        definition = leaf(doc)["def"]
        definition.update({k: v for k, v in WHITE.items() if k not in ("shape", "style")})
        definition["text-stroke-width"] = 0.0
        later = copy.deepcopy(definition["textAttributes"]["keyframes"][0])
        later.update(time=2500, endTime=2500)
        definition["textAttributes"]["keyframes"].append(later)
        result = animations.edit_interval(
            doc,
            3,
            dict(
                schema_version=2,
                start=1,
                end=2,
                definition={"text-stroke-width": 5, "fill-color-opacity": 0.25},
            ),
        )
        eased = animations.edit_interval(
            result, 3, dict(schema_version=1, start=1, end=2, values={}, easing="linear")
        )
        self.assertEqual(leaf(eased)["def"]["textAttributes"], definition["textAttributes"])
        self.assertEqual(
            [
                leaf(eased)["def"][name]["keyframes"][0]["interp"]
                for name in ["text-stroke-width", "fill-color-opacity"]
            ],
            ["linr", "linr"],
        )
        self.assertEqual(animations.remove_interval(eased, 3, 1, 2), doc)

    def test_second_return_and_all_color_channels_remain_independent(self):
        doc = animations.edit_interval(fixture(), 3, request())
        spec = dict(
            schema_version=2,
            start=3,
            end=4,
            definition={"fill-color-blue": 0, "stroke-color-red": 0},
        )
        result = animations.edit_interval(doc, 3, spec)
        expected = copy.deepcopy(doc)
        for name in ["fill-color-blue", "stroke-color-red"]:
            leaf(expected)["def"][name] = dict(
                type="double", defaultValue=1.0, keyframes=[native_frame(0.0, 3000, 4000)]
            )
        leaf(expected)["animationTracks"]["visual"].append(dict(endTime=4000, duration=1000))
        self.assertEqual(result, expected)
        removed = animations.remove_interval(result, 3, 1, 2)
        expected = fixture()
        for name in ["fill-color-blue", "stroke-color-red"]:
            leaf(expected)["def"][name] = dict(
                type="double", defaultValue=1.0, keyframes=[native_frame(0.0, 3000, 4000)]
            )
        leaf(expected)["animationTracks"]["visual"] = [dict(endTime=4000, duration=1000)]
        self.assertEqual(removed, expected)

    def test_preserve_typed_style_bounds_opaque_frames_and_parameter_interpolation(self):
        doc = fixture()
        leaf(doc)["def"]["stroke-width"] = dict(
            type="double",
            defaultValue=0.0,
            interp="eioe",
            opaque=["retain"],
            valueBounds=dict(minValue=0.0, maxValue=100.0),
        )
        result = animations.edit_interval(doc, 3, request())
        leaf(result)["def"]["stroke-width"]["keyframes"][0]["opaque"] = ["frame"]
        changed = animations.edit_interval(
            result, 3, dict(schema_version=2, start=1, end=2, definition={"stroke-width": 20})
        )
        expected = copy.deepcopy(result)
        leaf(expected)["def"]["stroke-width"]["keyframes"][0]["value"] = 20.0
        self.assertEqual(changed, expected)
        removed = animations.remove_interval(changed, 3, 1, 2)
        self.assertEqual(removed, doc)

    def test_missing_wrong_typed_out_of_range_and_discrete_fields_refuse_atomically(self):
        for name, value in [
            ("stroke-width", -1),
            ("stroke-width", True),
            ("stroke-width", "nan"),
            ("fill-color-red", -0.01),
            ("fill-color-opacity", 1.01),
            ("stroke-color-green", False),
            ("stroke-color-opacity", 2),
            ("fill-color-alpha", 1),
            ("stroke-color-alpha", 1),
            ("corner-radius", 10),
            ("fill-style", "none"),
            ("stroke-style", "dash"),
        ]:
            doc = fixture()
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                animations.edit_interval(
                    doc, 3, dict(schema_version=2, start=1, end=2, definition={name: value})
                )
            self.assertEqual(doc, fixture())
        for value in [
            None,
            {"type": "int", "defaultValue": 1},
            {"type": "double"},
            {"type": "double", "defaultValue": 1, "keyframes": [native_frame(0.5, 1000, 1000)]},
        ]:
            doc = fixture()
            if value is None:
                del leaf(doc)["def"]["fill-color-opacity"]
            else:
                leaf(doc)["def"]["fill-color-opacity"] = value
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                animations.edit_interval(doc, 3, request())
            self.assertEqual(doc, before)

    def test_unknown_coupling_and_orphans_remain_refusals_for_shape_styles(self):
        doc = animations.edit_interval(fixture(), 3, request())
        leaf(doc)["def"]["corner-radius"] = dict(
            type="double", defaultValue=8, keyframes=[native_frame(30.0)]
        )
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "unknown definition"):
            animations.remove_interval(doc, 3, 1, 2)
        with self.assertRaisesRegex(ValueError, "unknown definition"):
            animations.edit_interval(
                doc, 3, dict(schema_version=1, start=1, end=2, values={}, easing="linear")
            )
        self.assertEqual(doc, before)
        del leaf(doc)["def"]["corner-radius"]
        del leaf(doc)["animationTracks"]["visual"]
        with self.assertRaisesRegex(ValueError, "orphaned"):
            animations.remove_interval(doc, 3, 1, 2)
        with self.assertRaisesRegex(ValueError, "orphaned"):
            animations.edit_interval(
                doc, 3, dict(schema_version=1, start=1, end=2, values={}), allow_empty=True
            )

    def test_cli_refusal_never_creates_a_candidate_or_changes_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source, spec, output = [
                Path(temp) / name for name in ["source.json", "spec.json", "output.json"]
            ]
            source.write_bytes(project.encode_document(fixture()))
            before = source.read_bytes()
            spec.write_text(
                json.dumps(dict(schema_version=2, start=1, end=2, definition={"stroke-width": -1}))
            )
            stream = io.StringIO()
            with patch("sys.stderr", stream):
                status = animations.main(
                    [
                        "set-interval",
                        str(source),
                        "--clip-id",
                        "3",
                        "--spec",
                        str(spec),
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertFalse(json.loads(stream.getvalue())["ok"])
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), before)
